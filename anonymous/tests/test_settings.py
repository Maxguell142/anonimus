import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from anonymous.settings import SettingsError, SettingsStore


class FakeCredentialStore:
    def __init__(self):
        self.values = {}

    def get_password(self, service, username):
        return self.values.get((service, username))

    def set_password(self, service, username, password):
        self.values[(service, username)] = password

    def delete_password(self, service, username):
        del self.values[(service, username)]


class TestSettingsStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.path = Path(self.temp_dir.name) / "settings.json"
        self.credentials = FakeCredentialStore()
        self.store = SettingsStore(self.path, credential_store=self.credentials)

    def test_defaults_keep_existing_docker_mcp_and_offer_unconfigured_remote_backends(self):
        settings = self.store.load()

        self.assertEqual(settings["kali_backend"], "docker")
        self.assertTrue(settings["mcp_urls"]["docker"])
        self.assertEqual(settings["mcp_urls"]["cloud"], "")
        self.assertEqual(settings["mcp_urls"]["virtualbox"], "")
        self.assertEqual(settings["cloud_ssh"]["host"], "")
        self.assertEqual(settings["cloud_ssh"]["username"], "kali")
        self.assertEqual(settings["cloud_ssh"]["port"], 22)
        self.assertIn(settings["ai_provider"], ("ollama", "google"))

    def test_save_and_load_share_provider_backend_and_profile_preferences(self):
        settings = self.store.load()
        settings.update(
            ai_provider="google",
            kali_backend="cloud",
            user_name="Max",
        )
        settings["mcp_urls"]["cloud"] = "https://kali.example/mcp"
        settings["cloud_ssh"].update(
            host="kali.example",
            key_path="C:\\keys\\kali.pem",
        )

        self.store.save(settings)

        loaded = self.store.load()
        self.assertEqual(loaded["ai_provider"], "google")
        self.assertEqual(loaded["kali_backend"], "cloud")
        self.assertEqual(loaded["mcp_urls"]["cloud"], "https://kali.example/mcp")
        self.assertEqual(loaded["cloud_ssh"]["host"], "kali.example")
        self.assertEqual(loaded["cloud_ssh"]["key_path"], "C:\\keys\\kali.pem")
        self.assertEqual(loaded["user_name"], "Max")

    def test_rejects_unknown_backend_and_does_not_change_saved_settings(self):
        original = self.store.load()
        invalid = dict(original, kali_backend="arbitrary-shell")

        with self.assertRaises(SettingsError):
            self.store.save(invalid)

        self.assertEqual(self.store.load(), original)

    def test_rejects_malformed_mcp_url(self):
        settings = self.store.load()
        settings["mcp_urls"]["cloud"] = "not-a-url"

        with self.assertRaises(SettingsError):
            self.store.save(settings)

        self.assertFalse(self.path.exists())

    def test_rejects_unencrypted_remote_mcp_endpoint(self):
        settings = self.store.load()
        settings["mcp_urls"]["cloud"] = "http://kali.example/mcp"

        with self.assertRaises(SettingsError):
            self.store.save(settings)

    def test_rejects_unsafe_cloud_ssh_host_or_port(self):
        settings = self.store.load()
        settings["cloud_ssh"].update(host="host; whoami", port=22)
        with self.assertRaises(SettingsError):
            self.store.save(settings)

        settings["cloud_ssh"].update(host="kali.example", port=70000)
        with self.assertRaises(SettingsError):
            self.store.save(settings)

    def test_rejects_api_key_in_plaintext_settings(self):
        settings = self.store.load()
        settings["api_key"] = "synthetic-secret"

        with self.assertRaises(SettingsError):
            self.store.save(settings)

    def test_api_key_is_stored_in_credential_store_not_settings_file(self):
        self.store.save(self.store.load())
        self.store.set_api_key("synthetic-test-secret")

        self.assertEqual(self.store.get_api_key(), "synthetic-test-secret")
        persisted = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertNotIn("api_key", persisted)
        self.assertNotIn("synthetic-test-secret", json.dumps(persisted))

    def test_clearing_api_key_removes_it_from_the_credential_store(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
            self.store.set_api_key("synthetic-test-secret")
            self.store.set_api_key("")

            self.assertEqual(self.store.get_api_key(), "")

    def test_environment_key_remains_a_compatible_fallback(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "synthetic-env-secret"}):
            self.assertEqual(self.store.get_api_key(), "synthetic-env-secret")

    def test_corrupt_settings_are_reported_instead_of_silently_reset(self):
        self.path.write_text("{", encoding="utf-8")

        with self.assertRaises(SettingsError):
            self.store.load()


if __name__ == "__main__":
    unittest.main()
