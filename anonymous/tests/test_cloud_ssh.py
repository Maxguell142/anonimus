import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from anonymous.engines.ops.kali_ssh import KaliSshTransport


class TestKaliSshTransport(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        root = Path(self.temp_dir.name)
        self.key_path = root / "kali.pem"
        self.known_hosts = root / "known_hosts"
        self.key_path.write_text("synthetic key placeholder", encoding="utf-8")
        self.known_hosts.write_text("192.0.2.10 ssh-ed25519 synthetic-host-key\n", encoding="utf-8")
        self.transport = KaliSshTransport(
            {
                "host": "192.0.2.10",
                "username": "kali",
                "port": 22,
                "key_path": str(self.key_path),
                "known_hosts": str(self.known_hosts),
            }
        )

    def test_health_check_uses_pinned_host_key_and_batch_ssh(self):
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="ANONYMOUS_KALI_SSH_OK\n",
            stderr="",
        )
        with patch("anonymous.engines.ops.kali_ssh.shutil.which", return_value="ssh.exe"), patch(
            "anonymous.engines.ops.kali_ssh.subprocess.run",
            return_value=completed,
        ) as run:
            result = self.transport.health_check()

        args, kwargs = run.call_args
        command = args[0]
        self.assertTrue(result["healthy"])
        self.assertIn("StrictHostKeyChecking=yes", command)
        self.assertIn(f"UserKnownHostsFile={self.known_hosts}", command)
        self.assertIn("BatchMode=yes", command)
        self.assertEqual(command[-2], "kali@192.0.2.10")
        self.assertEqual(command[-1], "printf ANONYMOUS_KALI_SSH_OK")
        self.assertFalse(kwargs["shell"])

    def test_missing_known_hosts_fails_without_connecting_or_trusting_new_host(self):
        self.transport.connection["known_hosts"] = str(self.known_hosts.with_name("missing_hosts"))

        with patch("anonymous.engines.ops.kali_ssh.subprocess.run") as run:
            result = self.transport.health_check()

        self.assertFalse(result["healthy"])
        self.assertIn("known_hosts", result["detail"])
        run.assert_not_called()

    def test_missing_private_key_fails_without_connecting(self):
        self.transport.connection["key_path"] = str(self.key_path.with_name("missing.pem"))

        with patch("anonymous.engines.ops.kali_ssh.subprocess.run") as run:
            result = self.transport.health_check()

        self.assertFalse(result["healthy"])
        self.assertIn("clave SSH", result["detail"])
        run.assert_not_called()

    def test_discovery_runs_only_the_fixed_nmap_host_discovery_command(self):
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="Nmap done: 2 IP addresses (1 host up)",
            stderr="",
        )
        with patch("anonymous.engines.ops.kali_ssh.shutil.which", return_value="ssh.exe"), patch(
            "anonymous.engines.ops.kali_ssh.subprocess.run",
            return_value=completed,
        ) as run:
            result = self.transport.discover_network("192.168.10.0/24")

        command = run.call_args.args[0]
        self.assertTrue(result["ok"])
        self.assertEqual(
            command[-1],
            "nmap -sn -n --reason 192.168.10.0/24",
        )
        self.assertFalse(run.call_args.kwargs["shell"])

    def test_discovery_rejects_non_private_or_broad_ranges_without_ssh(self):
        with patch("anonymous.engines.ops.kali_ssh.subprocess.run") as run:
            public = self.transport.discover_network("8.8.8.0/24")
            broad = self.transport.discover_network("10.0.0.0/8")

        self.assertFalse(public["ok"])
        self.assertFalse(broad["ok"])
        run.assert_not_called()

    def test_arbitrary_remote_command_is_rejected(self):
        with self.assertRaises(ValueError):
            self.transport._run("whoami")


if __name__ == "__main__":
    unittest.main()
