#!/usr/bin/env python3
"""Create a ZIP with Thunderstore files at its root."""
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
subprocess.run([sys.executable, str(ROOT / "scripts/validate.py")], check=True)
m = json.loads((ROOT / "manifest.json").read_text())
out = ROOT / "dist" / f"{m['name']}-{m['version_number']}.zip"
out.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for filename in ("manifest.json", "README.md", "CHANGELOG.md", "icon.png"):
        z.write(ROOT / filename, filename)
    for path in sorted((ROOT / "config").rglob("*")):
        if path.is_file():
            z.write(path, path.relative_to(ROOT).as_posix())
print(out)
