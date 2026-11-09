"""Bounded catalog and archive regression checks; never rewrite the registered ZIP."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
from io import StringIO

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('contract_packager', ROOT / 'tooling/package_contract_return.py')
if SPEC is None or SPEC.loader is None:
    raise RuntimeError('packager source unavailable')
packager = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packager)
CANDIDATE = f'dist/{packager.NAME}-0.1.5-skill-candidate.zip'


class CatalogCandidateTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(dir=ROOT / 'dist')
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        (self.root / 'products').mkdir()
        (self.root / 'dist').mkdir()
        self.catalog = json.loads((ROOT / 'products/catalog.json').read_text(encoding='utf-8'))
        shutil.copyfile(ROOT / CANDIDATE, self.root / CANDIDATE)
        shutil.copyfile(ROOT / 'requirements.txt', self.root / 'requirements.txt')
        self.root_patch = patch.object(packager, 'ROOT', self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.save_catalog()

    def save_catalog(self):
        (self.root / 'products/catalog.json').write_text(json.dumps(self.catalog), encoding='utf-8')

    def test_real_candidate_and_source(self):
        source = packager.validate()
        result = packager.verify(self.root / CANDIDATE, source)
        self.assertEqual(result['zip_sha256'], self.catalog['products'][0]['versions'][-1]['sha256'])
        self.assertEqual(len(result['members']), 3)

    def test_wrong_catalog_hash(self):
        self.catalog['products'][0]['versions'][-1]['sha256'] = '0' * 64
        self.save_catalog()
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            packager.validate()

    def test_wrong_catalog_path(self):
        self.catalog['products'][0]['versions'][-1]['candidate'] = 'dist/wrong.zip'
        self.save_catalog()
        with self.assertRaisesRegex(ValueError, 'candidate path mismatch'):
            packager.validate()

    def test_historical_candidate_or_hash_rejected(self):
        for field in ('candidate', 'sha256', 'published_at'):
            with self.subTest(field=field):
                original = copy.deepcopy(self.catalog)
                self.catalog['products'][0]['versions'][0][field] = 'not-unknown'
                self.save_catalog()
                with self.assertRaisesRegex(ValueError, 'historical candidate'):
                    packager.validate()
                self.catalog = original

    def test_tampered_archive_rejected(self):
        path = self.root / CANDIDATE
        with path.open('ab') as out:
            out.write(b'tamper')
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            packager.validate()

    def test_unpublished_gate(self):
        for field, value in (('published_at', '2026-01-01'), ('review_status', 'PASS'), ('status', 'PUBLISHED')):
            with self.subTest(field=field):
                original = copy.deepcopy(self.catalog)
                self.catalog['products'][0][field] = value
                self.save_catalog()
                with self.assertRaisesRegex(ValueError, 'publication or review'):
                    packager.validate()
                self.catalog = original
        self.catalog['products'][0]['versions'][-1]['published_at'] = '2026-01-01'
        self.save_catalog()
        with self.assertRaisesRegex(ValueError, 'publication or review'):
            packager.validate()

    def test_verify_wrong_output_path_rejected_even_if_bytes_match(self):
        other = self.root / 'dist/copy.zip'
        shutil.copyfile(self.root / CANDIDATE, other)
        with patch.object(sys, 'argv', ['package_contract_return.py', 'verify', '--output', str(other)]):
            with redirect_stdout(StringIO()):
                with self.assertRaisesRegex(ValueError, 'not the registered candidate'):
                    packager.main()

    def test_negative_cli_exit_codes(self):
        # Exercise the actual CLI with only ROOT redirected to isolated ignored fixtures.
        script = (
            'import importlib.util, pathlib, sys; '
            'spec=importlib.util.spec_from_file_location("packager", sys.argv[1]); '
            'm=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); '
            'm.ROOT=pathlib.Path(sys.argv[2]); sys.argv=["packager", "validate"]; m.main()'
        )
        entry = self.catalog['products'][0]
        for field, value in (('sha256', '0' * 64), ('candidate', 'dist/wrong.zip')):
            with self.subTest(field=field):
                old = entry['versions'][-1][field]
                entry['versions'][-1][field] = value
                self.save_catalog()
                result = subprocess.run([sys.executable, '-B', '-c', script,
                                         str(ROOT / 'tooling/package_contract_return.py'), str(self.root)],
                                        capture_output=True, text=True, check=False)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                entry['versions'][-1][field] = old
        entry['versions'][0]['candidate'] = 'dist/old.zip'
        self.save_catalog()
        result = subprocess.run([sys.executable, '-B', '-c', script,
                                 str(ROOT / 'tooling/package_contract_return.py'), str(self.root)],
                                capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0, result.stdout)


if __name__ == '__main__':
    unittest.main()
