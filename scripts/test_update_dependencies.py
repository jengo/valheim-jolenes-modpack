#!/usr/bin/env python3
"""Offline dependency-updater tests; no live API requests."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import update_dependencies as updater


def package(namespace, name, version='1.10.0', **extra):
    return dict(full_name=f'{namespace}-{name}', is_deprecated=False,
                latest={'version_number': version, 'is_active': True}, **extra)


class UpgradeTests(unittest.TestCase):
    def test_numeric_upgrade_preserves_other_fields_and_order(self):
        manifest = {'version_number': '1.0.10', 'dependencies': ['A-One-1.9.0', 'B-Two-2.0.0']}
        result, changes = updater.upgrade(manifest, lambda n, p: package(n, p))
        self.assertEqual(result['dependencies'], ['A-One-1.10.0', 'B-Two-2.0.0'])
        self.assertEqual(result['version_number'], '1.0.10')
        self.assertEqual(manifest['dependencies'][0], 'A-One-1.9.0')
        self.assertEqual(changes, [('A-One', '1.9.0', '1.10.0')])

    def test_invalid_dependencies_fail_before_requests(self):
        for deps in [[], ['bad'], ['A-One-1.0.0', 'A-One-2.0.0']]:
            with self.subTest(deps=deps), self.assertRaises(ValueError):
                updater.upgrade({'dependencies': deps}, lambda *args: self.fail('Unexpected request'))

    def test_bad_api_responses_rejected(self):
        responses = [None, package('Wrong', 'Name'),
                     {'full_name': 'A-One', 'is_deprecated': True},
                     {'full_name': 'A-One', 'is_deprecated': False, 'latest': {'is_active': False}},
                     package('A', 'One', 'invalid')]
        for response in responses:
            with self.subTest(response=response), self.assertRaises(ValueError):
                updater.upgrade({'dependencies': ['A-One-1.0.0']}, lambda *args: response)

    def run_main(self, path, *args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return updater.main(['--manifest', str(path), *args])

    def test_dry_run_and_atomic_update(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'manifest.json'
            original = '{"version_number": "1.0.10", "dependencies": ["A-One-1.0.0"], "name": "Pack"}'
            path.write_text(original)
            with patch.object(updater, 'fetch_package', return_value=package('A', 'One')):
                self.assertEqual(self.run_main(path, '--dry-run'), 0)
                self.assertEqual(path.read_text(), original)
                self.assertFalse((path.parent / 'CHANGELOG.md').exists())
                self.assertEqual(self.run_main(path), 0)
            self.assertEqual((path.parent / 'CHANGELOG.md').read_text(), '## 1.1.0\n- Update A-One from 1.0.0 to 1.10.0.\n')
            self.assertEqual(json.loads(path.read_text()), {'version_number': '1.1.0', 'dependencies': ['A-One-1.10.0'], 'name': 'Pack'})

    def test_lookup_failure_leaves_original_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'manifest.json'
            original = '{"version_number": "1.0.10", "dependencies": ["A-One-1.0.0", "B-Two-1.0.0"]}\n'
            path.write_text(original)
            def fetch(n, p):
                if n == 'B':
                    raise ValueError('HTTP 429')
                return package(n, p)
            with patch.object(updater, 'upgrade', side_effect=lambda m: real_upgrade(m, fetch)):
                self.assertEqual(self.run_main(path), 1)
            self.assertEqual(path.read_text(), original)

    def test_no_updates_leaves_both_files_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'manifest.json'
            original = '{"version_number":"2.7.9","dependencies":["A-One-1.10.0"]}'
            path.write_text(original)
            notes = path.parent / 'CHANGELOG.md'
            notes.write_text('# Changelog\n\n## 2.7.9\n- Existing.\n')
            old_notes = notes.read_bytes()
            with patch.object(updater, 'fetch_package', return_value=package('A', 'One')):
                self.assertEqual(self.run_main(path), 0)
            self.assertEqual(path.read_text(), original)
            self.assertEqual(notes.read_bytes(), old_notes)

    def test_minor_bump_changelog_preservation_and_rerun(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'manifest.json'
            path.write_text('{"version_number":"2.7.9","dependencies":["A-One-1.0.0"]}')
            notes = path.parent / 'CHANGELOG.md'
            notes.write_text('# Changelog\n\n## 2.7.9\n- Existing.\n')
            with patch.object(updater, 'fetch_package', return_value=package('A', 'One')):
                self.assertEqual(self.run_main(path), 0)
                self.assertEqual(json.loads(path.read_text())['version_number'], '2.8.0')
                self.assertEqual(notes.read_text(), '# Changelog\n\n## 2.8.0\n- Update A-One from 1.0.0 to 1.10.0.\n\n## 2.7.9\n- Existing.\n')
                snapshot = (path.read_bytes(), notes.read_bytes())
                self.assertEqual(self.run_main(path), 0)
                self.assertEqual((path.read_bytes(), notes.read_bytes()), snapshot)

    def test_invalid_version_or_duplicate_changelog_does_not_write(self):
        for version, changelog in [('invalid', ''), ('1.0.10', '## 1.1.0\n- Existing.\n')]:
            with self.subTest(version=version), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'manifest.json'
                path.write_text(json.dumps({'version_number': version, 'dependencies': ['A-One-1.0.0']}))
                notes = path.parent / 'CHANGELOG.md'
                notes.write_text(changelog)
                snapshot = (path.read_bytes(), notes.read_bytes())
                with patch.object(updater, 'fetch_package', return_value=package('A', 'One')):
                    self.assertEqual(self.run_main(path), 1)
                self.assertEqual((path.read_bytes(), notes.read_bytes()), snapshot)

    def test_second_write_failure_rolls_back_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'manifest.json'
            path.write_text('{"version_number":"1.0.10","dependencies":["A-One-1.0.0"]}')
            notes = path.parent / 'CHANGELOG.md'
            notes.write_text('## 1.0.10\n- Existing.\n')
            snapshot = (path.read_bytes(), notes.read_bytes())
            real_replace = updater.os.replace
            def fail_changelog(src, dst):
                if dst == notes:
                    raise OSError('Simulated changelog write failure')
                return real_replace(src, dst)
            with patch.object(updater, 'fetch_package', return_value=package('A', 'One')), patch.object(updater.os, 'replace', side_effect=fail_changelog):
                self.assertEqual(self.run_main(path), 1)
            self.assertEqual((path.read_bytes(), notes.read_bytes()), snapshot)
            self.assertEqual(sorted(p.name for p in path.parent.iterdir()), ['CHANGELOG.md', 'manifest.json'])


real_upgrade = updater.upgrade
if __name__ == '__main__':
    unittest.main()
