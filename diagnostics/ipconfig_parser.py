"""
Parses the output of `ipconfig /all` into a structured list of adapters.
Shared by network.py, dns_check.py, and dhcp_check.py so all three modules
agree on adapter state without duplicating parsing logic.
"""
import re
import subprocess


def get_ipconfig_all() -> str:
    """Runs `ipconfig /all` and returns its raw text output."""
    result = subprocess.run(
        ["ipconfig", "/all"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.stdout


# Matches lines like: "   IPv4 Address. . . . . . . . . . . : 192.168.1.5(Preferred)"
# Key excludes '.' so the run of dot-leaders isn't swallowed into the field name.
# The dot-leader length varies (padding to align labels), so match one-or-more.
_KV_LINE = re.compile(r"^\s*([A-Za-z0-9()\-/ ]+?)\s*(?:\.\s*)+:\s*(.*)$")

# Matches adapter header lines, e.g. "Ethernet adapter Ethernet:" or
# "Wireless LAN adapter Wi-Fi:" — these are NOT indented and end with ':'.
_ADAPTER_HEADER = re.compile(r"^\S.*adapter.*:\s*$", re.IGNORECASE)


def parse_ipconfig(output: str) -> list[dict]:
    """
    Returns a list of dicts: {"name": str, "fields": {key: [values...]}}
    Multi-value fields (like DNS Servers spanning multiple lines) are
    collected as a list under one key.
    """
    adapters = []
    current = None
    current_key = None

    for raw_line in output.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue

        if _ADAPTER_HEADER.match(line):
            if current is not None:
                adapters.append(current)
            current = {"name": line.strip().rstrip(":"), "fields": {}}
            current_key = None
            continue

        if current is None:
            continue  # skip the "Windows IP Configuration" preamble

        m = _KV_LINE.match(line)
        if m:
            key = m.group(1).strip()
            value = m.group(2).strip()
            current_key = key
            current["fields"].setdefault(key, [])
            if value:
                current["fields"][key].append(value)
        elif current_key:
            # Continuation line — e.g. a second DNS server on its own line
            value = line.strip()
            if value:
                current["fields"][current_key].append(value)

    if current is not None:
        adapters.append(current)

    return adapters


def active_adapters(adapters: list[dict]) -> list[dict]:
    """Filters to adapters that actually have an IPv4 address assigned."""
    return [a for a in adapters if a["fields"].get("IPv4 Address")]
