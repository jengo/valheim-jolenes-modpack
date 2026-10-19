#!/usr/bin/env python3
"""Publish the built package using Thunderstore's usermedia/submission API."""
import json
import os
from pathlib import Path
import sys
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
    manifest = json.loads((ROOT / "manifest.json").read_text())
    name, version = manifest["name"], manifest["version_number"]
    package = ROOT / "dist" / f"{name}-{version}.zip"
    if not package.is_file():
        raise RuntimeError("Build the package before publishing.")
    lookup = f"package/{quote(namespace, safe='')}/{quote(name, safe='')}/{version}/"
    try:
        api(lookup, None)
    except RuntimeError as exc:
        if str(exc) != f"Thunderstore {lookup}: HTTP 404":
            raise
    else:
        print(f"{namespace}-{name}-{version} already exists; skipping upload.")
        return
    if not token:
        raise RuntimeError("Set the THUNDERSTORE_API_TOKEN GitHub Actions secret.")
    upload = api("usermedia/initiate-upload/", token, {
        "filename": package.name, "file_size_bytes": package.stat().st_size,
    })
    uuid = upload["user_media"]["uuid"]
    parts = []
    try:
        with package.open("rb") as source:
            for part in upload["upload_urls"]:
                source.seek(part["offset"])
                data = source.read(part["length"])
                if len(data) != part["length"]:
                    raise RuntimeError("Upload part extends past package size.")
                # Signed storage URLs authorize themselves; do not send the API token.
                request = Request(part["url"], data=data, method="PUT")
                try:
                    with urlopen(request, timeout=180) as response:
                        etag = response.headers["ETag"]
                        if not etag:
                            raise RuntimeError("Storage upload did not return an ETag.")
                except (HTTPError, URLError):
                    raise RuntimeError("Thunderstore storage upload failed.") from None
                parts.append({"ETag": etag, "PartNumber": part["part_number"]})
        api(f"usermedia/{uuid}/finish-upload/", token, {"parts": parts})
    except Exception:
        try:
            api(f"usermedia/{uuid}/abort-upload/", token, {})
        except Exception:
            pass
        raise
    api("submission/submit/", token, {
        "author_name": namespace,
        "communities": ["valheim"],
        "has_nsfw_content": False,
        "upload_uuid": uuid,
        "community_categories": {"valheim": categories},
    })
    print(f"Published {namespace}-{name}-{version} to Thunderstore.")


if __name__ == "__main__":
    try:
        publish(os.environ.get("THUNDERSTORE_API_TOKEN", ""),
                os.environ.get("THUNDERSTORE_NAMESPACE", "Jolene"),
                [c.strip() for c in os.environ.get("THUNDERSTORE_CATEGORIES", "modpacks").split(",") if c.strip()])
    except (RuntimeError, URLError, KeyError, ValueError, OSError) as exc:
        # URLError text can contain network details; tokens and signed URLs stay private.
        sys.exit(str(exc) if isinstance(exc, RuntimeError) else "Thunderstore publishing failed; check API connectivity and response format.")
