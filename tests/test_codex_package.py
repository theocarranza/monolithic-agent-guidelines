"""Generated Codex distribution must preserve runtime files without portable classification."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((ROOT / 'scripts/build_codex_package.py').is_file(), 'Codex package builder is missing')
        spec = importlib.util.spec_from_file_location('builder', ROOT / 'scripts/build_codex_package.py')
        self.builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.builder)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in self.builder.DIRECTORIES:
            shutil.copytree(ROOT / name, self.root / name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for name in self.builder.FILES:
            shutil.copyfile(ROOT / name, self.root / name)

    def test_generated_distribution_has_same_runtime_and_no_portable_manifest(self):
        self.builder.build(self.root)
        target = self.root / 'dist/codex'
        self.assertFalse((target / 'plugin.json').exists())
        manifest = json.loads((target / '.codex-plugin/plugin.json').read_text())
        self.assertEqual(manifest['hooks'], './hooks/codex.json')
        self.assertEqual((target / 'enforcement/adapters/common.py').read_bytes(), (self.root / 'enforcement/adapters/common.py').read_bytes())
        result = subprocess.run([sys.executable, str(target / 'retrieval/query.py'), 'fetch', 'dart/task'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['id'], 'dart/task')
        self.builder.build(self.root, check=True)

    def test_check_reports_stale_missing_and_unexpected_files_without_writing(self):
        with self.assertRaisesRegex(ValueError, 'out of date'):
            self.builder.build(self.root, check=True)
        self.builder.build(self.root)
        source = self.root / 'knowledge/core/principles.md'
        source.write_text(source.read_text() + '\nChanged\n')
        with self.assertRaisesRegex(ValueError, 'out of date'):
            self.builder.build(self.root, check=True)
        self.builder.build(self.root)
        extra = self.root / 'dist/codex/plugin.json'
        extra.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Unexpected'):
            self.builder.build(self.root, check=True)
        self.assertEqual(extra.read_text(), '{}')
        with self.assertRaisesRegex(ValueError, 'Unexpected'):
            self.builder.build(self.root)

    def test_generated_distribution_ignores_bytecode_and_rejects_symlinks(self):
        cache = self.root / 'retrieval/__pycache__'
        cache.mkdir(exist_ok=True)
        (cache / 'junk.pyc').write_bytes(b'cache')
        self.builder.build(self.root)
        self.assertFalse((self.root / 'dist/codex/retrieval/__pycache__').exists())
        (self.root / 'retrieval/escape.py').symlink_to(self.root / 'README.md')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.builder.build(self.root)

    def test_committed_distribution_is_current_and_marketplace_selects_it(self):
        self.builder.build(ROOT, check=True)
        catalog = json.loads((ROOT / '.agents/plugins/marketplace.json').read_text())
        self.assertEqual(catalog['plugins'][0]['source']['path'], './dist/codex')

    def test_cli_preview_detects_drift_and_build_repairs_it(self):
        from contextlib import redirect_stderr
        import io
        # Same executable code, with its source location rooted in this fixture.
        self.builder.__file__ = str(self.root / 'scripts/build_codex_package.py')
        errors = io.StringIO()
        with redirect_stderr(errors):
            self.assertEqual(self.builder.main(['--check']), 1)
        self.assertIn('out of date', errors.getvalue())
        self.assertFalse((self.root / 'dist/codex').exists())
        self.assertEqual(self.builder.main([]), 0)
        self.assertEqual(self.builder.main(['--check']), 0)

    def test_output_directory_symlink_is_refused(self):
        outside = self.root / 'outside'; outside.mkdir()
        (self.root / 'dist').mkdir()
        (self.root / 'dist/codex').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.builder.build(self.root)
        self.assertEqual(list(outside.iterdir()), [])

    def test_top_level_input_directory_symlink_is_refused(self):
        original = self.root / 'knowledge'
        external = self.root / 'external-knowledge'
        original.rename(external)
        original.symlink_to(external, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.builder.build(self.root)

    def test_dangling_portable_manifest_is_not_accepted_by_check(self):
        self.builder.build(self.root)
        (self.root / 'dist/codex/plugin.json').symlink_to(self.root / 'missing')
        with self.assertRaisesRegex(ValueError, 'Unexpected|symlink'):
            self.builder.build(self.root, check=True)

    def test_parent_output_symlink_is_refused(self):
        outside = self.root / 'outside'; outside.mkdir()
        (self.root / 'dist').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.builder.build(self.root)
        self.assertEqual(list(outside.iterdir()), [])

    def test_command_line_check_verifies_committed_output(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/build_codex_package.py'), '--check'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__': unittest.main()
