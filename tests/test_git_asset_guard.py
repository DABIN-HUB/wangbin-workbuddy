"""Focused regression checks for the team new-asset CI entry."""
import importlib.util
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "tooling" / "git_asset_guard.py"
spec = importlib.util.spec_from_file_location("git_asset_guard", SCRIPT)
assert spec is not None and spec.loader is not None
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class GitAssetGuardTests(TestCase):
    def test_necessary_fixed_inputs_and_sources(self):
        for path, blob in [
            ("tests/fixtures/case.expected.json", b'{"expected":"PASS"}'),
            ("tests/fixtures/sample.docx", b"PK\x03\x04fixture"),
            ("tests/fixtures/fixed-input.zip", b"PK\x03\x04fixture"),
            ("packages/skills/wangbin-example/examples/fictional-case.expected.json", b"{}"),
            ("packages/skills/wangbin-example/SKILL.md", b"# Skill\n"),
        ]:
            with self.subTest(path=path):
                self.assertEqual([], guard.reasons(path, blob))

    def test_generated_assets_and_credential_names(self):
        paths = [
            "packages/skills/example/dist/candidate.zip",
            "packages/skills/example/dist/candidate.zip.sha256",
            "packages/skills/example/candidate.zip.manifest.json",
            "reports/run-42/actual.json",
            "reports/run-42/result.json",
            "tooling/__pycache__/module.pyc",
            "services/.venv/lib/config.py",
            "tests/.pytest_cache/v/cache/nodeids",
            "config/.env.production",
            "config/service-credentials.json",
            "keys/signing.pem",
        ]
        for path in paths:
            with self.subTest(path=path):
                self.assertTrue(guard.reasons(path, b"placeholder"))
                with patch.object(guard, "additions", return_value=[path]), patch.object(guard, "git", return_value=b"placeholder"):
                    self.assertEqual(1, guard.main(["--base", guard.BASELINE]))

    def test_large_results_and_fixture_limit(self):
        self.assertTrue(guard.reasons("reports/metrics.json", b"a" * (guard.MAX_SOURCE + 1)))
        self.assertEqual([], guard.reasons("tests/fixtures/necessary.docx", b"a" * (guard.MAX_SOURCE + 1)))
        self.assertTrue(guard.reasons("tests/fixtures/too-large.zip", b"a" * (guard.MAX_FIXTURE + 1)))

    def test_secret_content_and_nonzero_exit(self):
        # Compose the test token so the test source itself is not flagged by content scanning.
        blob = b"api_" + b"key = 'not-a-real-test-value'"
        self.assertIn("possible credential content", guard.reasons("src/config.py", blob))
        with patch.object(guard, "additions", return_value=["src/config.py"]), patch.object(guard, "git", return_value=blob):
            self.assertEqual(1, guard.main(["--staged"]))
        self.assertIn("possible credential content", guard.reasons("docs/key.txt", b"-----BEGIN RSA " + b"PRIVATE KEY-----"))

    def test_fail_closed_wrong_baseline(self):
        with patch.object(guard, "git", side_effect=ValueError("unrelated")):
            self.assertEqual(2, guard.main(["--base", "deadbeef"]))


if __name__ == "__main__":
    main()
