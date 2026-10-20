#!/usr/bin/env python3
"""Skip existing versions, then publish the unchanged built ZIP with official tcli."""
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
API = "https://thunderstore.io/api/experimental/"


def api(path, token, payload=None):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()
    request = Request(API + path, data=data, headers=headers)
    try:
        with urlopen(request, timeout=180) as response:
            return json.load(response)
    except HTTPError as exc:
        # Never print authenticated response bodies or signed upload URLs.
        raise RuntimeError(f"Thunderstore {path}: HTTP {exc.code}") from None


def publish(token, namespace, categories):
    if not token.strip():
        raise RuntimeError("Set the THUNDERSTORE_API_TOKEN GitHub Actions secret (repository Settings > Secrets and variables > Actions). No token was provided.")
    manifest = json.loads((ROOT / "manifest.json").read_text())
    name, version = manifest["name"], manifest["version_number"]
    package = ROOT / "dist" / f"{name}-{version}.zip"
    if not package.is_file():
        raise RuntimeError("Build the package before publishing.")
    lookup = f"package/{quote(namespace, safe='')}/{quote(name, safe='')}/{version}/"
    try:
        api(lookup, None)
    except RuntimeError as exc:
        if str(exc) == f"Thunderstore {lookup}: HTTP 403":
            raise RuntimeError("Thunderstore denied the version lookup (HTTP 403), before tcli ran. Check API access from the runner; this response does not establish whether the version exists.") from None
        if str(exc) != f"Thunderstore {lookup}: HTTP 404":
            raise
    else:
        print(f"{namespace}-{name}-{version} already exists; skipping upload.")
        return
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
    except (RuntimeError, URLError, KeyError, ValueError, OSError, subprocess.CalledProcessError) as exc:
        # URLError text can contain network details; tokens and signed URLs stay private.
        sys.exit(str(exc) if isinstance(exc, RuntimeError) else "Thunderstore publishing failed; check API connectivity and response format.")
