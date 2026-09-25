"""
IT Support Diagnostic Tool (Python / Tkinter edition)

Run with:  python main.py
No third-party packages required — standard library only.

Each check (Network / DNS / DHCP / Printer) runs independently on its own
button, in a background thread so the UI never freezes. Results from every
run are appended to a shared table, newest at the bottom.
"""
import datetime
import platform
import queue
import threading
import tkinter as tk
from tkinter import ttk

from diagnostics import models, network, dns_check, dhcp_check, printer_check


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("IT Support Diagnostic Tool")
        self.geometry("900x600")
        self.minsize(700, 400)

        self.result_queue: "queue.Queue[tuple]" = queue.Queue()
        self.buttons: dict[str, tk.Button] = {}

        self._build_ui()
        self.after(100, self._poll_queue)

        if platform.system() != "Windows":
            self._add_result(models.DiagnosticResult(
                "Platform", models.Status.WARNING,
                "This tool relies on Windows-only commands (ipconfig, PowerShell, ping -n).",
                "Checks will likely fail or behave differently on this OS."))

    def _build_ui(self):
        title = tk.Label(self, text="IT Support Diagnostic Tool", font=("Segoe UI", 16, "bold"))
        title.pack(anchor="w", padx=15, pady=(15, 5))

        btn_frame = tk.Frame(self)
        btn_frame.pack(anchor="w", padx=15, pady=(0, 10))

        module_specs = [
            ("Check Network", network.run),
            ("Check DNS", dns_check.run),
            ("Check DHCP", dhcp_check.run),
            ("Check Printer", printer_check.run),
        ]
        for label, func in module_specs:
            btn = tk.Button(btn_frame, text=label, width=16,
                             command=lambda f=func, l=label: self._run_module(f, l))
            btn.pack(side="left", padx=(0, 8))
            self.buttons[label] = btn

        clear_btn = tk.Button(btn_frame, text="Clear Results", width=14, command=self._clear)
        clear_btn.pack(side="left", padx=(20, 0))

        columns = ("status", "check", "message", "details")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        self.tree.heading("status", text="")
        self.tree.heading("check", text="Check")
        self.tree.heading("message", text="Result")
        self.tree.heading("details", text="Details")
        self.tree.column("status", width=32, anchor="center", stretch=False)
        self.tree.column("check", width=220)
        self.tree.column("message", width=280)
        self.tree.column("details", width=320)
        self.tree.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        scrollbar = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.tree.tag_configure(models.Status.PASS.value, foreground="#1a7f37")
        self.tree.tag_configure(models.Status.WARNING.value, foreground="#b08800")
        self.tree.tag_configure(models.Status.FAIL.value, foreground="#c1121f")
        self.tree.tag_configure(models.Status.INFO.value, foreground="#555555")

        self.status_label = tk.Label(self, text="Ready. Click a check above to run it.",
                                      fg="gray", anchor="w")
        self.status_label.pack(fill="x", padx=15, pady=(0, 10))

    def _run_module(self, func, label):
        self.buttons[label].config(state="disabled")
        self.status_label.config(text=f"Running {label}...")
        threading.Thread(target=self._worker, args=(func, label), daemon=True).start()

    def _worker(self, func, label):
        try:
            results = func()
            self.result_queue.put(("done", label, results, None))
        except Exception as e:  # noqa: BLE001 - surface any unexpected error to the UI
            self.result_queue.put(("error", label, None, str(e)))

    def _poll_queue(self):
        try:
            while True:
                kind, label, results, error = self.result_queue.get_nowait()
                if kind == "done":
                    self._add_result(models.DiagnosticResult(
                        f"\u2014 {label} \u2014", models.Status.INFO,
                        f"Run at {datetime.datetime.now().strftime('%H:%M:%S')}"))
                    for r in results:
                        self._add_result(r)
                    self.status_label.config(text=f"{label} complete.")
                else:
                    self._add_result(models.DiagnosticResult(
                        label, models.Status.FAIL, "Module crashed unexpectedly.", error))
                    self.status_label.config(text=f"{label} failed.")
                self.buttons[label].config(state="normal")
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    def _add_result(self, result: models.DiagnosticResult):
        self.tree.insert("", "end",
                          values=(result.symbol, result.check_name, result.message, result.details),
                          tags=(result.status.value,))
        children = self.tree.get_children()
        if children:
            self.tree.see(children[-1])

    def _clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.status_label.config(text="Ready. Click a check above to run it.")


if __name__ == "__main__":
    app = App()
    app.mainloop()
