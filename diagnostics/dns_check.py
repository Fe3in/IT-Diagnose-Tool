"""
DNS module: reads configured DNS servers from ipconfig, resolves known-good
hostnames via the system resolver, and checks TCP/53 reachability of each
configured DNS server.
"""
import socket
import time

from . import models
from .ipconfig_parser import get_ipconfig_all, parse_ipconfig

TEST_HOSTNAMES = ["www.google.com", "www.microsoft.com"]


def run() -> list[models.DiagnosticResult]:
    results = []

    output = get_ipconfig_all()
    adapters = parse_ipconfig(output)

    dns_servers = []
    for adapter in adapters:
        for server in adapter["fields"].get("DNS Servers", []):
            if server not in dns_servers:
                dns_servers.append(server)

    if not dns_servers:
        results.append(models.DiagnosticResult(
            "Configured DNS Servers", models.Status.WARNING,
            "No DNS servers found in the current configuration.",
            "This usually means DHCP hasn't handed out DNS settings."))
    else:
        results.append(models.DiagnosticResult(
            "Configured DNS Servers", models.Status.PASS, ", ".join(dns_servers)))

    for hostname in TEST_HOSTNAMES:
        start = time.time()
        try:
            addr = socket.gethostbyname(hostname)
            elapsed_ms = int((time.time() - start) * 1000)
            results.append(models.DiagnosticResult(
                f"Resolve {hostname}", models.Status.PASS,
                f"Resolved in {elapsed_ms} ms", addr))
        except socket.gaierror as e:
            results.append(models.DiagnosticResult(
                f"Resolve {hostname}", models.Status.FAIL,
                "Resolution failed.", str(e)))

    for server in dns_servers:
        try:
            sock = socket.create_connection((server, 53), timeout=1.5)
            sock.close()
            results.append(models.DiagnosticResult(
                f"DNS Server {server} Port 53", models.Status.PASS,
                "Reachable (TCP/53 open)"))
        except Exception:
            results.append(models.DiagnosticResult(
                f"DNS Server {server} Port 53", models.Status.WARNING,
                "Could not confirm TCP/53 is open.",
                "Some DNS servers only answer on UDP/53 — treat as informational."))

    return results
