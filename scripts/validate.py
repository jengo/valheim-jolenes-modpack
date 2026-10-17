#!/usr/bin/env python3
"""Offline Thunderstore manifest and repository sanity checks."""
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def main():
    errors = []
    try:
        m = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    except Exception as exc:
        sys.exit(f"Invalid manifest.json: {exc}")
    required = {"name", "version_number", "website_url", "description", "dependencies"}
    if set(m) != required:
        errors.append(f"manifest fields must be exactly {sorted(required)}")
    if not isinstance(m.get("name"), str) or not re.fullmatch(r"[A-Za-z0-9_]{1,128}", m["name"]):
        errors.append("name must contain 1-128 letters, numbers, or underscores")
    if not isinstance(m.get("version_number"), str) or not re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", m["version_number"]):
        errors.append("version_number must be Major.Minor.Patch")
    if not isinstance(m.get("website_url"), str) or (m["website_url"] and not re.match(r"^https?://", m["website_url"])):
        errors.append("website_url must be empty or HTTP(S)")
    if not isinstance(m.get("description"), str) or not (1 <= len(m["description"]) <= 250):
        errors.append("description must contain 1-250 characters")
    deps = m.get("dependencies")
    if not isinstance(deps, list) or not deps:
        errors.append("dependencies must be a non-empty array")
    else:
        for dep in deps:
            if not isinstance(dep, str) or not re.fullmatch(r"[A-Za-z0-9_]+-[A-Za-z0-9_]+-\d+\.\d+\.\d+", dep):
                errors.append(f"invalid dependency: {dep!r}")
        if len(deps) != len(set(deps)):
            errors.append("duplicate dependencies")
        if any("SlotLock" in d for d in deps):
            errors.append("standalone SlotLock must not be a dependency")
    for file in ("README.md", "icon.png"):
        if not (ROOT / file).is_file():
            errors.append(f"missing {file}")
    icon = ROOT / "icon.png"
    if icon.is_file():
        b = icon.read_bytes()
        if len(b) < 24 or b[:8] != b"\x89PNG\r\n\x1a\n" or struct.unpack(">II", b[16:24]) != (256, 256):
            errors.append("icon.png must be a 256x256 PNG")
    cfg = ROOT / "config/seneaL.valheim.ui.cfg"
    if not cfg.is_file() or "MaxSlots = 32" not in cfg.read_text() or "Slots = 32" not in cfg.read_text():
        errors.append("expected 32-slot SeneaL config")
    if errors:
        print("Manifest/package validation failed:")
        for e in errors: print(" - " + e)
        return 1
    print("Manifest and package source validation passed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
