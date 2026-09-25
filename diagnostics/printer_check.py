"""
Printer module: Print Spooler service status and installed printers'
online/offline state, queried via PowerShell (Get-Service / Get-Printer).
"""
import json
import subprocess

from . import models


def _run_powershell(cmd: str):
    """Returns (stdout, stderr) from a PowerShell command."""
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", cmd],
        capture_output=True,
        text=True,
        timeout=15,
    )
    return result.stdout.strip(), result.stderr.strip()


def run() -> list[models.DiagnosticResult]:
    results = []

    # 1. Print Spooler service status
    out, err = _run_powershell("Get-Service -Name Spooler | Select-Object -ExpandProperty Status")
    if out:
        status = out.strip()
        if status.lower() == "running":
            results.append(models.DiagnosticResult("Print Spooler Service", models.Status.PASS, "Running"))
        else:
            results.append(models.DiagnosticResult(
                "Print Spooler Service", models.Status.FAIL,
                f"Not running (status: {status})",
                "Most printer issues start here — try restarting the Spooler service."))
    else:
        results.append(models.DiagnosticResult(
            "Print Spooler Service", models.Status.FAIL,
            "Could not query service status.", err))

    # 2. Installed printers and their reported status
    out, err = _run_powershell(
        "Get-Printer | Select-Object Name, PrinterStatus | ConvertTo-Json -Compress")
    if out:
        try:
            data = json.loads(out)
            if isinstance(data, dict):
                data = [data]
            if not data:
                results.append(models.DiagnosticResult(
                    "Installed Printers", models.Status.WARNING, "No printers found on this system."))
            for p in data:
                name = p.get("Name", "Unknown printer")
                pstatus = str(p.get("PrinterStatus", "Unknown"))
                if pstatus.lower() in ("offline", "error", "paperout", "paper jam"):
                    results.append(models.DiagnosticResult(
                        f"Printer: {name}", models.Status.WARNING, f"Status: {pstatus}"))
                else:
                    results.append(models.DiagnosticResult(
                        f"Printer: {name}", models.Status.PASS, f"Status: {pstatus}"))
        except json.JSONDecodeError:
            results.append(models.DiagnosticResult(
                "Installed Printers", models.Status.WARNING,
                "Could not parse printer data.", out))
    else:
        results.append(models.DiagnosticResult(
            "Installed Printers", models.Status.FAIL,
            "Could not query printers.", err))

    return results
