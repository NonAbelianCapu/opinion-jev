"""Collect every saved run into one HTML page: results/spread/rumor.html."""

import json
from pathlib import Path

from jevsim.viz import write_html

runs = []
for f in sorted(Path("results/spread").glob("*_g*_r*.json")):
    run = json.loads(f.read_text())
    run["scenario"].setdefault("name", f.name.split("_")[0])
    runs.append(run)
print(write_html(runs, "results/spread/rumor.html"), f"({len(runs)} runs)")
