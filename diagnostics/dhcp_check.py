"""
DHCP module: reads DHCP enabled/disabled state, lease details, and detects
APIPA (169.254.x.x) addresses, which indicate the DHCP server was unreachable.
"""
from . import models
from .ipconfig_parser import get_ipconfig_all, parse_ipconfig, active_adapters


def run() -> list[models.DiagnosticResult]:
    results = []

    output = get_ipconfig_all()
    adapters = parse_ipconfig(output)
    active = active_adapters(adapters)

    if not active:
        results.append(models.DiagnosticResult(
            "DHCP", models.Status.WARNING, "No active adapters found."))
        return results

    for adapter in active:
        name = adapter["name"]
        fields = adapter["fields"]
        dhcp_enabled = fields.get("DHCP Enabled", ["No"])[0].strip().lower() == "yes"
        ip = fields.get("IPv4 Address", ["unknown"])[0]

        if not dhcp_enabled:
            results.append(models.DiagnosticResult(
                f"DHCP: {name}", models.Status.INFO,
                "Static IP configuration (DHCP disabled).",
                "Not necessarily a problem — informational only."))
            continue

        if ip.startswith("169.254."):
            results.append(models.DiagnosticResult(
                f"DHCP: {name}", models.Status.FAIL,
                "APIPA address detected — the DHCP server was not reachable.",
                ip))
            continue

        dhcp_server = fields.get("DHCP Server", ["(none reported)"])[0]
        lease_obtained = fields.get("Lease Obtained", ["unknown"])[0]
        lease_expires = fields.get("Lease Expires", ["unknown"])[0]

        results.append(models.DiagnosticResult(
            f"DHCP: {name}", models.Status.PASS,
            f"Lease active from server {dhcp_server}",
            f"Obtained: {lease_obtained} | Expires: {lease_expires}"))

    return results
