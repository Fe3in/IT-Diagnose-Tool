# IT Support Diagnostic Tool (Python Edition)

Same tool as the C#/WPF version, rebuilt in Python + Tkinter. No third-party
packages, no build step — just Python's standard library.

## Requirements

- **Windows** (the checks shell out to `ipconfig`, `ping`, and PowerShell,
  which are Windows-specific).
- **Python 3.10+** (uses the `list[dict]` type-hint syntax). If you're on an
  older Python, remove the `from __future__ import annotations`-style hints
  or upgrade — 3.10+ is recommended anyway.

Check your Python version:
```
python --version
```
If you don't have Python, install it from https://python.org — during setup,
tick "Add python.exe to PATH".

## How to run

From the `ITDiagToolPy` folder:
```
python main.py
```
That's it — a window opens with four buttons. No `pip install` needed.

## Project structure

```
ITDiagToolPy/
├── main.py                      # Tkinter UI — one button per module
└── diagnostics/
    ├── models.py                 # DiagnosticResult + Status (Pass/Warning/Fail/Info)
    ├── ipconfig_parser.py        # shared parser for `ipconfig /all`
    ├── network.py                # adapters, IP, gateway, ping checks
    ├── dns_check.py               # DNS servers, resolution test, port 53 check
    ├── dhcp_check.py              # DHCP lease status, APIPA detection
    └── printer_check.py           # spooler status, printer states (via PowerShell)
```

<img width="1122" height="789" alt="image" src="https://github.com/user-attachments/assets/d76a715b-0e03-4c95-9b98-79c20c77c191" />


## What each module checks

- **Network**: active adapters + IPv4, default gateway, ping to gateway,
  ping to 8.8.8.8 (internet reachability).
- **DNS**: configured DNS servers (parsed from `ipconfig /all`), resolution
  test against known-good hostnames, TCP/53 reachability per DNS server.
- **DHCP**: DHCP enabled/disabled per adapter, lease server/times, detects
  APIPA (169.254.x.x) addresses as a failure.
- **Printer**: Print Spooler service status (via `Get-Service`), installed
  printers and their status (via `Get-Printer`).

## Design pattern

Every module is just a function `run() -> list[DiagnosticResult]` — no
classes or interfaces needed in Python for this. `main.py` maps one button
to one module function, runs it on a background thread (so the window
doesn't freeze while `ipconfig`/`ping`/PowerShell execute), and appends
results to the shared table. Modules never call each other, so one failing
doesn't affect the rest.

## Extending it

To add a new check (e.g. firewall status):
1. Create `diagnostics/firewall_check.py` with a `run()` function that
   returns a list of `DiagnosticResult` objects (see any existing module
   for the pattern).
2. Import it in `main.py` and add one line to `module_specs` in `_build_ui`:
   ```python
   ("Check Firewall", firewall_check.run),
   ```
   That's the entire integration — no other wiring needed.

## Known TODOs (good next learning steps)

- DHCP: parse `Lease Expires` into a real datetime and warn when a lease is
  close to expiring.
- Printer: enumerate stuck print jobs (`Get-PrintJob`) and offer to clear them.
- Add a "Run All" button that fires every module in sequence.
- Add an "Export Results" button that writes the table to a `.txt`/`.csv`
  file for attaching to support tickets.
- Package as a standalone `.exe` with `pyinstaller` so it can run on a
  machine without Python installed: `pyinstaller --onefile --windowed main.py`
