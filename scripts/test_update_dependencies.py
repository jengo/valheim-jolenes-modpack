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
            original = '{"dependencies": ["A-One-1.0.0"], "name": "Pack"}'
            path.write_text(original)
            with patch.object(updater, 'fetch_package', return_value=package('A', 'One')):
                self.assertEqual(self.run_main(path, '--dry-run'), 0)
                self.assertEqual(path.read_text(), original)
                self.assertEqual(self.run_main(path), 0)
            self.assertEqual(json.loads(path.read_text()), {'dependencies': ['A-One-1.10.0'], 'name': 'Pack'})

    def test_lookup_failure_leaves_original_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'manifest.json'
            original = '{"dependencies": ["A-One-1.0.0", "B-Two-1.0.0"]}\n'
            path.write_text(original)
            def fetch(n, p):
                if n == 'B':
                    raise ValueError('HTTP 429')
                return package(n, p)
            with patch.object(updater, 'upgrade', side_effect=lambda m: real_upgrade(m, fetch)):
                self.assertEqual(self.run_main(path), 1)
            self.assertEqual(path.read_text(), original)


real_upgrade = updater.upgrade
if __name__ == '__main__':
    unittest.main()
