#!/usr/bin/env python3
"""Publish the unchanged built ZIP with official tcli."""
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent


def publish(token, namespace, categories):
    if not token.strip():
        raise RuntimeError("Set the THUNDERSTORE_API_TOKEN secret in the prod GitHub Actions environment. No token was provided.")
    manifest = json.loads((ROOT / "manifest.json").read_text())
    name, version = manifest["name"], manifest["version_number"]
    package = ROOT / "dist" / f"{name}-{version}.zip"
    if not package.is_file():
        raise RuntimeError("Build the package before publishing.")
    # Only orchestration remains here: tcli owns all authenticated upload requests.
    # JSON strings/arrays are valid TOML values and safely escape variable input.
    with tempfile.TemporaryDirectory(prefix="thunderstore-") as directory:
        config_path = Path(directory) / "thunderstore.toml"
        config_path.write_text(
            '[config]\nschemaVersion = "0.0.1"\n'
            '[package]\n'
            f'namespace = {json.dumps(namespace)}\n'
            f'name = {json.dumps(name)}\n'
            f'versionNumber = {json.dumps(version)}\n'
            '[build]\noutdir = "dist"\n'
            '[publish]\nrepository = "https://thunderstore.io"\ncommunities = ["valheim"]\n'
            '[publish.categories]\n'
            f'valheim = {json.dumps(categories)}\n'
        )
        env = os.environ.copy()
        env["TCLI_AUTH_TOKEN"] = token
        subprocess.run([
            "tcli", "publish", "--config-path", str(config_path),
            "--file", str(package),
        ], cwd=ROOT, env=env, check=True)
    print(f"Published {namespace}-{name}-{version} to Thunderstore.")


if __name__ == "__main__":
    try:
        publish(os.environ.get("THUNDERSTORE_API_TOKEN", ""),
                os.environ.get("THUNDERSTORE_NAMESPACE", "Jolene"),
                [c.strip() for c in os.environ.get("THUNDERSTORE_CATEGORIES", "modpacks").split(",") if c.strip()])
    except subprocess.CalledProcessError as exc:
        # tcli inherits stdout/stderr so its actual diagnostics remain visible.
        sys.exit(exc.returncode)
    except (RuntimeError, KeyError, ValueError, OSError) as exc:
        sys.exit(str(exc) if isinstance(exc, RuntimeError) else "Could not prepare Thunderstore publishing; check the manifest, built ZIP, and tcli installation.")
