import io
import os
import struct
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from anonymous.engines.ops.kali_forensics import (
    MAX_OUTPUT_CHARS,
    KaliForensicsEngine,
    kali_forensics_engine,
)


class TestKaliForensicsEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.evidence_dir = root / "Evidencias"
        self.results_dir = root / "Resultados"
        self.evidence_dir.mkdir()
        self.results_dir.mkdir()
        self.engine = KaliForensicsEngine()
        self.engine.evidence_dir = self.evidence_dir
        self.engine.results_dir = self.results_dir

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_hash_uses_only_fixed_commands_and_saves_report(self):
        evidence = self.evidence_dir / "sample.E01"
        evidence.write_bytes(b"synthetic evidence")
        self.engine.status = lambda: {
            "connected": True,
            "evidence_read_only": True,
            "container": "kali-forensics",
            "state": "running",
            "detail": "ready",
        }
        with patch.object(
            self.engine,
            "_run_docker",
            side_effect=[
                CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout="abc  /evidencias/sample.E01",
                    stderr="",
                ),
                CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout="def  /evidencias/sample.E01",
                    stderr="",
                ),
            ],
        ) as run:
            result = self.engine.analyze("hash", "sample.E01")

        self.assertTrue(result["ok"])
        self.assertEqual(run.call_count, 2)
        self.assertTrue(all(call.kwargs.get("timeout") == 120 for call in run.call_args_list))
        self.assertIn("sample.E01", Path(result["report"]).read_text(encoding="utf-8"))
        self.assertEqual(len(list(self.results_dir.glob("*.hashes.txt"))), 1)

    def test_filename_rejects_paths_and_options(self):
        for filename in ("../sample.E01", r"..\sample.E01", "-e"):
            with self.subTest(filename=filename):
                with self.assertRaises(ValueError):
                    self.engine._validate_filename(filename)

    def test_status_requires_the_configured_evidence_bind_mount_to_be_read_only(self):
        source = sorted(self.engine._expected_evidence_mount_sources())[0]
        with patch.object(
            self.engine,
            "_run_docker",
            return_value=CompletedProcess(
                args=[],
                returncode=0,
                stdout=f"running|{source}|false",
                stderr="",
            ),
        ):
            status = self.engine.status()

        self.assertTrue(status["connected"])
        self.assertTrue(status["evidence_read_only"])

    def test_status_rejects_writable_or_unexpected_evidence_mounts(self):
        expected_source = sorted(self.engine._expected_evidence_mount_sources())[0]
        for mount_status in (
            f"{expected_source}|true",
            "/unrelated/evidence|false",
            "",
        ):
            with self.subTest(mount_status=mount_status), patch.object(
                self.engine,
                "_run_docker",
                return_value=CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout=f"running|{mount_status}",
                    stderr="",
                ),
            ):
                status = self.engine.status()

            self.assertFalse(status["connected"])
            self.assertFalse(status["evidence_read_only"])

    def test_docker_output_is_bounded_and_truncation_is_reported(self):
        process = unittest.mock.Mock()
        process.stdout = io.BytesIO(b"x" * (MAX_OUTPUT_CHARS + 1))
        process.stderr = io.BytesIO(b"")
        process.wait.return_value = 0
        with (
            patch.object(self.engine._docker, "_docker_executable", return_value="docker"),
            patch.object(self.engine, "_docker_environment", return_value={}),
            patch(
                "anonymous.engines.ops.kali_forensics.subprocess.Popen",
                return_value=process,
            ) as popen,
        ):
            result = self.engine._run_docker(["inspect", "kali-forensics"])

        self.assertEqual(len(result.stdout.split("\n[Salida truncada")[0]), MAX_OUTPUT_CHARS)
        self.assertIn("Salida truncada", result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(process.stdout.closed)
        self.assertTrue(process.stderr.closed)
        self.assertNotIn("shell", popen.call_args.kwargs)

    def test_docker_timeout_kills_child_process_and_propagates_timeout(self):
        process = unittest.mock.Mock()
        process.stdout = io.BytesIO(b"")
        process.stderr = io.BytesIO(b"")
        process.wait.side_effect = [
            subprocess.TimeoutExpired(cmd="docker", timeout=1),
            -9,
        ]
        with (
            patch.object(self.engine._docker, "_docker_executable", return_value="docker"),
            patch.object(self.engine, "_docker_environment", return_value={}),
            patch(
                "anonymous.engines.ops.kali_forensics.subprocess.Popen",
                return_value=process,
            ),
        ):
            with self.assertRaises(subprocess.TimeoutExpired):
                self.engine._run_docker(["exec", "kali-forensics", "file"], timeout=1)

        process.kill.assert_called_once_with()
        self.assertEqual(process.wait.call_count, 2)

    def test_each_supported_operation_invokes_only_its_fixed_read_only_tool(self):
        evidence = self.evidence_dir / "sample.E01"
        original_content = b"synthetic evidence"
        evidence.write_bytes(original_content)
        self.engine.status = lambda: {
            "connected": True,
            "evidence_read_only": True,
            "container": "kali-forensics",
            "state": "running",
            "detail": "ready",
        }
        cases = (
            ("identify", "sample.E01", ["file", "--", "/evidencias/sample.E01"]),
            (
                "metadata",
                "sample.E01",
                [
                    "exiftool",
                    "-s",
                    "-FileName",
                    "-FileType",
                    "-MIMEType",
                    "-FileSize",
                    "/evidencias/sample.E01",
                ],
            ),
            ("partitions", "sample.E01", ["mmls", "/evidencias/sample.E01"]),
            ("ewf-info", "sample.E01", ["ewfinfo", "/evidencias/sample.E01"]),
            ("ewf-verify", "sample.E01", ["ewfverify", "/evidencias/sample.E01"]),
            ("files", "sample.E01", ["fls", "-p", "/evidencias/sample.E01"]),
            ("binwalk", "sample.E01", ["binwalk", "/evidencias/sample.E01"]),
        )

        for operation, filename, expected_command in cases:
            with self.subTest(operation=operation), patch.object(
                self.engine,
                "_run_docker",
                return_value=CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout="read-only result",
                    stderr="",
                ),
            ) as run:
                result = self.engine.analyze(operation, filename)

            self.assertTrue(result["ok"])
            self.assertEqual(
                run.call_args.args[0],
                ["exec", "kali-forensics", *expected_command],
            )
            self.assertEqual(evidence.read_bytes(), original_content)

        self.assertEqual(
            {path.name for path in self.results_dir.iterdir()},
            set(),
            "Read-only analyses must not create output files.",
        )

    def test_shell_metacharacters_are_passed_as_a_single_argument(self):
        evidence = self.evidence_dir / "x; whoami"
        evidence.write_bytes(b"synthetic evidence")
        self.engine.status = lambda: {
            "connected": True,
            "evidence_read_only": True,
            "container": "kali-forensics",
            "state": "running",
            "detail": "ready",
        }
        with patch.object(
            self.engine,
            "_run_docker",
            return_value=CompletedProcess(
                args=[],
                returncode=0,
                stdout="ASCII text",
                stderr="",
            ),
        ) as run:
            result = self.engine.analyze("identify", "x; whoami")

        self.assertTrue(result["ok"])
        self.assertIn("/evidencias/x; whoami", run.call_args.args[0])

    def test_analysis_is_refused_when_evidence_mount_is_not_verified_read_only(self):
        evidence = self.evidence_dir / "sample.txt"
        evidence.write_text("synthetic evidence", encoding="utf-8")
        self.engine.status = lambda: {
            "connected": False,
            "evidence_read_only": False,
            "container": "kali-forensics",
            "state": "running",
            "detail": "Evidencias no está montada en solo lectura.",
        }
        with patch.object(self.engine, "_run_docker") as run:
            result = self.engine.analyze("identify", "sample.txt")

        self.assertFalse(result["ok"])
        self.assertIn("solo lectura", result["message"])
        run.assert_not_called()

    def test_symlink_cannot_escape_evidence_directory(self):
        outside = Path(self.temp_dir.name) / "outside.E01"
        outside.write_bytes(b"not evidence")
        link = self.evidence_dir / "linked.E01"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("El sistema no permite crear enlaces simbólicos sin privilegios.")

        with self.assertRaises(ValueError):
            self.engine._evidence_path("linked.E01")

    def test_unknown_operation_is_rejected_without_docker(self):
        result = self.engine.analyze("shell", "sample.E01")

        self.assertFalse(result["ok"])
        self.assertIn("kali forensic tools", result["message"])

    def test_start_requires_confirmation(self):
        result = self.engine.start_container()

        self.assertEqual(result["type"], "confirmation_required")
        self.assertEqual(result["pending_message"], "kali start")

    def test_stop_requires_confirmation(self):
        result = self.engine.stop_container()

        self.assertEqual(result["type"], "confirmation_required")
        self.assertEqual(result["pending_message"], "kali stop")


@unittest.skipUnless(
    os.getenv("ANONYMOUS_KALI_LIVE_TESTS") == "1",
    "Set ANONYMOUS_KALI_LIVE_TESTS=1 to run against Docker and a temporary evidence fixture.",
)
class TestKaliForensicsLive(unittest.TestCase):
    def test_fls_lists_a_file_from_synthetic_fat12_image(self):
        status = kali_forensics_engine.status()
        if not status["connected"] or not status["evidence_read_only"]:
            self.skipTest(f"Kali with read-only evidence mount is unavailable: {status['detail']}")

        filename = f"anonymous-live-fls-{uuid4().hex}.img"
        image_path = kali_forensics_engine.evidence_dir / filename
        image = bytearray(2880 * 512)
        boot = memoryview(image)[:512]
        boot[0:3] = b"\xeb\x3c\x90"
        boot[3:11] = b"MSDOS5.0"
        struct.pack_into("<HBHBHHBHHHII", boot, 11, 512, 1, 1, 2, 224, 2880, 0xF0, 9, 18, 2, 0, 0)
        boot[36] = 0
        boot[38] = 0x29
        struct.pack_into("<I", boot, 39, 0x1234ABCD)
        boot[43:54] = b"ANON TEST  "
        boot[54:62] = b"FAT12   "
        boot[510:512] = b"\x55\xaa"

        fat = bytearray(9 * 512)
        fat[0:3] = b"\xf0\xff\xff"
        fat[3] = 0xff
        fat[4] = (fat[4] & 0xF0) | 0x0F
        image[512:512 + len(fat)] = fat
        image[10 * 512:10 * 512 + len(fat)] = fat

        directory_entry = bytearray(32)
        directory_entry[0:8] = b"CASE    "
        directory_entry[8:11] = b"TXT"
        directory_entry[11] = 0x20
        contents = b"Synthetic FAT12 forensic fixture\n"
        struct.pack_into("<H", directory_entry, 26, 2)
        struct.pack_into("<I", directory_entry, 28, len(contents))
        image[19 * 512:19 * 512 + 32] = directory_entry
        image[33 * 512:33 * 512 + len(contents)] = contents

        try:
            image_path.write_bytes(image)
            result = kali_forensics_engine.analyze("files", filename)
            self.assertTrue(result["ok"], result["message"])
            self.assertIn("CASE.TXT", result["output"])
        finally:
            image_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
