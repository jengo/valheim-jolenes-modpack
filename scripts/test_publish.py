"""Exercise publishing without sending any network requests."""
import unittest
from unittest.mock import patch, MagicMock

import publish


class PublishingTests(unittest.TestCase):
    def test_existing_version_does_not_upload(self):
        with patch.object(publish, "api", return_value={}) as api:
            publish.publish("secret", "Jolene", ["modpacks"])
        self.assertEqual(api.call_count, 1)

    def test_api_failure_does_not_trigger_upload(self):
        with patch.object(publish, "api", side_effect=RuntimeError("HTTP 503")) as api:
            with self.assertRaises(RuntimeError):
                publish.publish("secret", "Jolene", ["modpacks"])
        self.assertEqual(api.call_count, 1)

    def test_upload_then_submit(self):
        calls = []

        def api(path, token, payload=None):
            calls.append((path, token, payload))
            if path.startswith("package/"):
                raise RuntimeError(f"Thunderstore {path}: HTTP 404")
            if path == "usermedia/initiate-upload/":
                return {"user_media": {"uuid": "test-id"}, "upload_urls": [
                    {"url": "https://storage.example/part", "offset": 0,
                     "length": 12, "part_number": 1}]}
            return {}

        response = MagicMock()
        response.__enter__.return_value.headers = {"ETag": '"etag"'}
        with patch.object(publish, "api", side_effect=api), patch.object(
            publish, "urlopen", return_value=response
        ) as storage:
            publish.publish("secret", "Jolene", ["modpacks"])
        request = storage.call_args.args[0]
        self.assertEqual(request.method, "PUT")
        self.assertFalse(request.has_header("Authorization"))
        self.assertEqual(calls[-2][0], "usermedia/test-id/finish-upload/")
        self.assertEqual(calls[-1][0], "submission/submit/")
        self.assertEqual(calls[-1][2]["author_name"], "Jolene")
        self.assertEqual(calls[-1][2]["community_categories"], {"valheim": ["modpacks"]})


if __name__ == "__main__":
    unittest.main()
