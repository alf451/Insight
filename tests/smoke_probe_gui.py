"""Manual smoke test: build the Probe GUI, pump a few events, close it.
Not part of the pytest suite (Tkinter GUI construction needs a real display) —
run manually with: py tests/smoke_probe_gui.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "probe"))

import tkinter as tk

from insight_probe.app import ProbeApp

root = tk.Tk()
app = ProbeApp(root)
root.update()
root.update()
print("Probe GUI constructed and pumped OK")
app._on_close()
print("Probe GUI closed cleanly")
