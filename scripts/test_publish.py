"""Exercise CLI orchestration without publishing or making network requests."""
import subprocess
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

import publish


class PublishingTests(unittest.TestCase):
    def test_cli_receives_existing_zip_config_and_environment_token(self):
        def run(args, **kwargs):
            self.assertEqual(args[:3], ['tcli', 'publish', '--config-path'])
            config = tomllib.loads(Path(args[3]).read_text())
            self.assertEqual(config['package']['namespace'], 'Jolene')
            self.assertEqual(config['publish']['communities'], ['valheim'])
            self.assertEqual(config['publish']['categories']['valheim'], ['modpacks', 'qol'])
            manifest = publish.json.loads((publish.ROOT / 'manifest.json').read_text())
            self.assertEqual(config['package']['versionNumber'], manifest['version_number'])
            self.assertEqual(args[4], '--file')
            self.assertEqual(Path(args[5]).name, f"{manifest['name']}-{manifest['version_number']}.zip")
            self.assertTrue(Path(args[5]).is_file())
            self.assertEqual(kwargs['env']['TCLI_AUTH_TOKEN'], 'secret')
            self.assertNotIn('secret', ' '.join(args) + Path(args[3]).read_text())
            self.assertTrue(kwargs['check'])
        with patch.object(publish.subprocess, 'run', side_effect=run) as cli:
            publish.publish('secret', 'Jolene', ['modpacks', 'qol'])
        cli.assert_called_once()
        self.assertFalse(Path(cli.call_args.args[0][3]).exists())

    def test_missing_token_does_not_invoke_cli(self):
        with patch.object(publish.subprocess, 'run') as run:
            for token in ('', '   '):
                with self.assertRaisesRegex(RuntimeError, 'THUNDERSTORE_API_TOKEN'):
                    publish.publish(token, 'Jolene', ['modpacks'])
        run.assert_not_called()

    def test_no_python_network_preflight(self):
        with patch('socket.create_connection', side_effect=AssertionError('Python must not make network requests')), patch.object(publish.subprocess, 'run') as cli:
            publish.publish('secret', 'Jolene', ['modpacks'])
        cli.assert_called_once()

    def test_missing_package_does_not_invoke_cli(self):
        with patch.object(publish.Path, 'is_file', return_value=False), patch.object(publish.subprocess, 'run') as cli:
            with self.assertRaisesRegex(RuntimeError, 'Build the package'):
                publish.publish('secret', 'Jolene', ['modpacks'])
        cli.assert_not_called()

    def test_cli_failure_propagates(self):
        with patch.object(publish.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'tcli')):
            with self.assertRaises(subprocess.CalledProcessError):
                publish.publish('secret', 'Jolene', ['modpacks'])


if __name__ == '__main__':
    unittest.main()
