"""
Network module: active adapters, IPv4/gateway config, ping to gateway,
and ping to a public host to confirm internet reachability.
"""
import re
import subprocess

from . import models
from .ipconfig_parser import get_ipconfig_all, parse_ipconfig, active_adapters


def _ping(host: str, timeout_ms: int = 2000):
    """Returns (success: bool, round_trip_ms: str|None, raw_output: str)."""
    try:
        result = subprocess.run(
            ["ping", "-n", "1", "-w", str(timeout_ms), host],
            capture_output=True,
            text=True,
            timeout=(timeout_ms / 1000) + 3,
        )
        output = result.stdout
        success = "TTL=" in output or "TTL =" in output
        m = re.search(r"time[=<]\s*(\d+)\s*ms", output, re.IGNORECASE)
        rtt = m.group(1) if m else None
        return success, rtt, output
    except Exception as e:
        return False, None, str(e)


def run() -> list[models.DiagnosticResult]:
    results = []

    output = get_ipconfig_all()
    adapters = parse_ipconfig(output)
    active = active_adapters(adapters)

    if not active:
        results.append(models.DiagnosticResult(
            "Network Adapter",
            models.Status.FAIL,
            "No active network adapters with an IPv4 address were found.",
            "All adapters are either disabled, disconnected, or have no IP."))
        return results

    for adapter in active:
        ip = adapter["fields"].get("IPv4 Address", ["unknown"])[0]
        results.append(models.DiagnosticResult(
            f"Adapter: {adapter['name']}",
            models.Status.PASS,
            f"IPv4: {ip}"))

    gw_adapter = next((a for a in active if a["fields"].get("Default Gateway")), None)
    gateway_ip = None

    if gw_adapter:
        gateway_ip = gw_adapter["fields"]["Default Gateway"][0]
        results.append(models.DiagnosticResult("Default Gateway", models.Status.PASS, gateway_ip))
    else:
        results.append(models.DiagnosticResult(
            "Default Gateway",
            models.Status.WARNING,
            "No default gateway found on any active adapter.",
            "Expected on isolated networks, but will block internet checks."))

    if gateway_ip:
        ok, rtt, raw = _ping(gateway_ip)
        if ok:
            results.append(models.DiagnosticResult(
                "Ping Gateway", models.Status.PASS,
                f"Reachable ({rtt} ms)" if rtt else "Reachable"))
        else:
            results.append(models.DiagnosticResult(
                "Ping Gateway", models.Status.FAIL,
                "Unreachable",
                "Check cabling/Wi-Fi or the gateway device itself."))

    ok, rtt, raw = _ping("8.8.8.8")
    if ok:
        results.append(models.DiagnosticResult(
            "Ping Internet (8.8.8.8)", models.Status.PASS,
            f"Reachable ({rtt} ms)" if rtt else "Reachable"))
    else:
        results.append(models.DiagnosticResult(
            "Ping Internet (8.8.8.8)", models.Status.FAIL,
            "Unreachable",
            "No internet connectivity, or ICMP is blocked upstream."))

    return results
