"""License distribution regressions for the standalone experimental ZIP."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from unittest.mock import patch

import package_skill

HERE = Path(__file__).resolve().parent
OLD = HERE / "dist" / "wangbin-estimate-calculator-0.1.0-technical-candidate.zip"
OLD_SHA = "ab28889f1a126c45a508d9c593d618cac3689256985f8df2694e197911b09991"


class LicensePackageTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(dir=os.environ["POC_SCRATCH"])
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.committed = subprocess.run(
            ["git", "show", "HEAD:" + package_skill.LICENSE_GIT_PATH],
            cwd=HERE, capture_output=True, check=True).stdout

    def test_exact_license_and_immutable_old_candidate(self):
        before = hashlib.sha256(OLD.read_bytes()).hexdigest()
        self.assertEqual(before, OLD_SHA)
        facts = package_skill.build(self.root)
        self.assertEqual(set(facts["members"]), {
            "wangbin-estimate-calculator/" + x for x in package_skill.MEMBERS})
        with zipfile.ZipFile(facts["archive"]) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(archive.read("wangbin-estimate-calculator/LICENSE"), self.committed)
        self.assertEqual(hashlib.sha256(OLD.read_bytes()).hexdigest(), OLD_SHA)
        self.assertEqual(package_skill.build(self.root), facts)

    def test_tampered_preview_license_refused_without_archive(self):
        preview = self.root / "skill-preview"
        shutil.copytree(package_skill.SKILL, preview)
        (preview / "LICENSE").write_bytes(b"not the original license\n")
        with patch.object(package_skill, "SKILL", preview):
            with self.assertRaisesRegex(ValueError, "Skill LICENSE differs"):
                package_skill.build(self.root / "dist")
        self.assertFalse((self.root / "dist").exists())

    def test_existing_corrupt_archive_refused_not_overwritten(self):
        output = self.root / "dist"
        output.mkdir()
        archive = output / "wangbin-estimate-calculator-0.1.0-licensefix1.zip"
        archive.write_bytes(b"preserve this existing artifact")
        with self.assertRaises(zipfile.BadZipFile):
            package_skill.build(output)
        self.assertEqual(archive.read_bytes(), b"preserve this existing artifact")


if __name__ == "__main__":
    unittest.main()
