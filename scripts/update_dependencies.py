#!/usr/bin/env python3
"""Upgrade manifest dependencies using Thunderstore's public API (stdlib only)."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
DEPENDENCY = re.compile(r"([A-Za-z0-9_]+)-([A-Za-z0-9_]+)-(\d+\.\d+\.\d+)")
VERSION = re.compile(r"\d+\.\d+\.\d+")
API = "https://thunderstore.io/api/experimental/package"


def version_tuple(value):
    if not isinstance(value, str) or not VERSION.fullmatch(value):
        raise ValueError(f"Invalid version: {value!r}")
    return tuple(map(int, value.split('.')))


def fetch_package(namespace, name):
    url = f"{API}/{namespace}/{name}/"
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "Jolenes-Modpack-Dependency-Updater/1.0"})
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as exc:
        raise ValueError(f"{namespace}-{name}: HTTP {exc.code} from Thunderstore") from exc
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        raise ValueError(f"{namespace}-{name}: API lookup failed: {exc}") from exc


def upgrade(manifest, fetch=None):
    """Return updated direct dependencies and changes; never mutate the input."""
    if fetch is None:
        fetch = fetch_package
    dependencies = manifest.get('dependencies')
    if not isinstance(dependencies, list) or not dependencies:
        raise ValueError('manifest dependencies must be a non-empty list')
    parsed = []
    seen = set()
    for dependency in dependencies:
        match = DEPENDENCY.fullmatch(dependency) if isinstance(dependency, str) else None
        if not match:
            raise ValueError(f"Invalid dependency: {dependency!r}")
        namespace, name, current = match.groups()
        package_id = f"{namespace}-{name}"
        if package_id in seen:
            raise ValueError(f"Duplicate package: {package_id}")
        seen.add(package_id)
        parsed.append((namespace, name, current, dependency))
    updated, changes = [], []
    for namespace, name, current, dependency in parsed:
        package_id = f"{namespace}-{name}"
        package = fetch(namespace, name)
        if not isinstance(package, dict) or package.get('full_name') != package_id:
            raise ValueError(f"{package_id}: unexpected API package identity")
        if package.get('is_deprecated') is not False:
            raise ValueError(f"{package_id}: deprecated package or missing deprecation status; review manually")
        latest = package.get('latest')
        if not isinstance(latest, dict) or latest.get('is_active') is not True:
            raise ValueError(f"{package_id}: no active latest release")
        version = latest.get('version_number')
        if version_tuple(version) > version_tuple(current):
            updated.append(f"{package_id}-{version}")
            changes.append((package_id, current, version))
        else:
            updated.append(dependency)  # Never downgrade a pinned version.
    return dict(manifest, dependencies=updated), changes


def write_manifest(path, manifest):
    """Replace atomically so a failed write cannot leave a partial manifest."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(manifest, handle, indent=2, ensure_ascii=False)
            handle.write('\n')
        temporary.chmod(path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true', help='Show upgrades without changing files')
    parser.add_argument('--manifest', type=Path, default=ROOT / 'manifest.json', help='Manifest to update (default: repository manifest.json)')
    args = parser.parse_args(argv)
    try:
        original = args.manifest.read_text(encoding='utf-8')
        manifest = json.loads(original)
        if not isinstance(manifest, dict):
            raise ValueError('manifest must be a JSON object')
        updated, changes = upgrade(manifest)
        for package, before, after in changes:
            print(f"{package}: {before} -> {after}")
        if not changes:
            print('No dependency upgrades available. Manifest unchanged.')
        elif args.dry_run:
            print(f"Dry run: {len(changes)} upgrade(s); manifest unchanged.")
        else:
            if args.manifest.read_text(encoding='utf-8') != original:
                raise ValueError('manifest changed during API lookups; rerun to avoid overwriting edits')
            write_manifest(args.manifest, updated)
            print(f"Updated {len(changes)} dependency version(s) in {args.manifest}.")
            print('Review mod compatibility and configs before building a new release.')
        return 0
    except (OSError, ValueError) as exc:
        print(f"Upgrade failed: {exc}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
