"""Installer selection, ownership, native command contracts and read-only preview."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InstallerTests(unittest.TestCase):
    def setUp(self):
        script = ROOT / 'scripts/install_hosts.py'
        self.assertTrue(script.exists(), 'multi-host installer is missing')
        spec = importlib.util.spec_from_file_location('installer', script)
        self.module = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.module)
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / 'home'; self.home.mkdir()
        self.calls = []

    def runner(self, args):
        self.calls.append(args)
        if args[:4] == ['codex', 'plugin', 'marketplace', 'list']:
            data = {'marketplaces': []}
        elif args[:3] == ['codex', 'plugin', 'list']:
            data = {'installed': [{'pluginId': self.module.CODEX_ID, 'version': '1.4.1', 'enabled': True}]}
        elif args[:3] == ['claude', 'plugin', 'list']:
            data = [{'id': self.module.CLAUDE_ID, 'version': '1.4.1', 'enabled': True}]
        elif args[:4] == ['claude', 'plugin', 'marketplace', 'list']:
            data = []
        else:
            data = {}
        return subprocess.CompletedProcess(args, 0, stdout=json.dumps(data), stderr='')

    def test_selected_cursor_installs_complete_portable_references_only(self):
        result = self.module.install(ROOT, self.home, ['cursor'], which=lambda _: None, runner=self.runner)
        target = self.home / '.cursor/plugins/local/monolithic-agent-guidelines'
        self.assertEqual(result['installed'], ['cursor'])
        self.assertTrue((target / 'skills/karpathy-guidelines/SKILL.md').is_file())
        self.assertTrue((target / 'knowledge/core/principles.md').is_file())
        self.assertTrue((target / 'plugin.json').is_file())
        self.assertFalse((target / 'skills/setup').exists())
        manifest = json.loads((target / 'plugin.json').read_text())
        self.assertNotIn('hooks', manifest)
        self.assertNotIn('extensions', manifest)
        self.assertFalse((self.home / '.codex').exists())
        self.assertEqual(self.calls, [])
        self.module.install(ROOT, self.home, ['cursor'], which=lambda _: None, runner=self.runner)

    def test_all_detects_available_hosts_and_reports_missing(self):
        result = self.module.install(ROOT, self.home, ['all'], which=lambda name: '/bin/'+name if name in ['codex', 'cursor'] else None, runner=self.runner)
        self.assertEqual(result['installed'], ['codex', 'cursor'])
        self.assertIn('claude', result['unavailable'])
        self.assertFalse(any(args[0] == 'claude' for args in self.calls))

    def test_multiple_explicit_hosts_and_isolated_marketplace_identity(self):
        result = self.module.install(ROOT, self.home, ['codex,claude'], which=lambda name: name, runner=self.runner)
        self.assertEqual(result['installed'], ['codex', 'claude'])
        root = Path(result['package'])
        self.assertEqual(json.loads((root / '.claude-plugin/marketplace.json').read_text())['name'], 'monolithic-agent-guidelines')
        self.assertTrue(any(args[:4] == ['claude', 'plugin', 'install', self.module.CLAUDE_ID] for args in self.calls))
        self.assertFalse(any('remove' in args or 'uninstall' in args for args in self.calls))

    def test_dry_run_does_not_write_or_execute(self):
        before = list(self.home.iterdir())
        result = self.module.install(ROOT, self.home, ['codex'], which=lambda name: name, runner=self.runner, dry_run=True)
        self.assertEqual(result['planned'], ['codex'])
        self.assertEqual(list(self.home.iterdir()), before)
        self.assertEqual(self.calls, [])

    def test_explicit_missing_or_unknown_host_fails_before_writes(self):
        for hosts in [['codex'], ['unknown'], ['all,cursor']]:
            with self.subTest(hosts=hosts), self.assertRaises(ValueError):
                self.module.install(ROOT, self.home, hosts, which=lambda _: None, runner=self.runner)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_unowned_or_edited_cursor_destination_is_preserved(self):
        target = self.home / '.cursor/plugins/local/monolithic-agent-guidelines'
        target.mkdir(parents=True); (target / 'user.txt').write_text('keep')
        with self.assertRaisesRegex(ValueError, 'unowned'):
            self.module.install(ROOT, self.home, ['cursor'], which=lambda _: None, runner=self.runner)
        self.assertEqual((target / 'user.txt').read_text(), 'keep')

    def test_owned_edits_and_symlink_targets_are_refused(self):
        result = self.module.install(ROOT, self.home, ['cursor'], which=lambda _: None, runner=self.runner)
        target = self.home / '.cursor/plugins/local/monolithic-agent-guidelines'
        (target / 'plugin.json').write_text('user edit')
        with self.assertRaisesRegex(ValueError, 'modified'):
            self.module.install(ROOT, self.home, ['cursor'], which=lambda _: None, runner=self.runner)
        self.assertEqual((target / 'plugin.json').read_text(), 'user edit')
        link_home = self.home / 'alias'; link_home.symlink_to(self.home, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.module.install(ROOT, link_home, ['cursor'], which=lambda _: None, runner=self.runner)


    def test_marketplace_refresh_preserves_foreign_registration(self):
        package = self.home / 'releases/1.4.1'
        for location, allowed in [(self.module.REPOSITORY + '.git', True),
                                  ('https://github.com/someone/another-repo', False)]:
            self.calls.clear()
            def client(args):
                self.calls.append(args)
                return subprocess.CompletedProcess(args, 0, stdout=json.dumps([
                    {'name': self.module.NAME, 'source': {'source': location}}]), stderr='')
            if allowed:
                self.module.marketplace(client, 'codex', package, self.home / 'releases')
                self.assertEqual([args[3] for args in self.calls], ['list', 'remove', 'add'])
            else:
                with self.assertRaisesRegex(ValueError, 'another source'):
                    self.module.marketplace(client, 'claude', package, self.home / 'releases')
                self.assertEqual(len(self.calls), 1)

    def test_native_install_failure_and_wrong_version_are_reported(self):
        def failing(args):
            raise subprocess.CalledProcessError(1, args, stderr='native install failed')
        with self.assertRaises(subprocess.CalledProcessError):
            self.module.install(ROOT, self.home, ['codex'], which=lambda _: 'codex', runner=failing)
        def wrong_version(args):
            result = self.runner(args)
            if args[:3] == ['codex', 'plugin', 'list']:
                result.stdout = json.dumps({'installed': []})
            return result
        with self.assertRaisesRegex(ValueError, 'requested plugin version'):
            self.module.install(ROOT, self.home, ['codex'], which=lambda _: 'codex', runner=wrong_version)

    def test_no_detected_hosts_and_local_shell_preview(self):
        with self.assertRaisesRegex(ValueError, 'No supported local hosts'):
            self.module.install(ROOT, self.home, ['all'], which=lambda _: None)
        import os
        result = subprocess.run(['bash', str(ROOT / 'install.sh'), '--host', 'cursor', '--dry-run'],
                                env={**os.environ, 'HOME': str(self.home)}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['planned'], ['cursor'])
        self.assertEqual(list(self.home.iterdir()), [])



    def test_managed_file_preservation_for_corrupt_records_and_unexpected_files(self):
        target = self.home / 'owned'
        self.module.write_owned(target, {'file.txt': b'original'})
        marker = target / self.module.MARKER
        original = marker.read_text()
        marker.write_text('[]')
        with self.assertRaisesRegex(ValueError, 'ownership'):
            self.module.write_owned(target, {'file.txt': b'new'})
        marker.write_text(original)
        (target / 'extra.txt').write_text('keep')
        with self.assertRaisesRegex(ValueError, 'unowned'):
            self.module.write_owned(target, {'file.txt': b'new'})
        self.assertEqual((target / 'extra.txt').read_text(), 'keep')
        self.assertEqual((target / 'file.txt').read_text(), 'original')
        other = self.home / 'stale'
        self.module.write_owned(other, {'old.txt': b'keep'})
        with self.assertRaisesRegex(ValueError, 'never deletes'):
            self.module.write_owned(other, {})
        self.assertEqual((other / 'old.txt').read_text(), 'keep')

    def test_existing_marketplace_same_release_needs_no_refresh(self):
        package = self.home / 'releases/1.4.1'
        def client(args):
            self.calls.append(args)
            return subprocess.CompletedProcess(args, 0, stdout=json.dumps({'marketplaces': [
                {'name': self.module.NAME, 'marketplaceSource': {'source': str(package)}}]}))
        self.module.marketplace(client, 'codex', package, self.home / 'releases')
        self.assertEqual(len(self.calls), 1)

    def test_installer_command_reports_missing_client_without_writes(self):
        from unittest.mock import patch
        from io import StringIO
        output = StringIO()
        with patch.object(self.module.Path, 'home', return_value=self.home), patch.object(self.module, 'install', side_effect=ValueError('missing client')), patch('sys.stderr', output):
            self.assertEqual(self.module.main(['--host', 'codex']), 1)
        self.assertEqual(json.loads(output.getvalue())['error'], 'missing client')
        self.assertEqual(list(self.home.iterdir()), [])



    def test_symlink_package_inputs_and_destination_are_rejected(self):
        source = self.home / 'source'; source.mkdir()
        (source / 'hooks').symlink_to(ROOT / 'hooks', target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink package source'):
            self.module.package_files(source)
        other = self.home / 'other'; (other / 'hooks').mkdir(parents=True)
        (other / 'hooks/link.json').symlink_to(ROOT / 'hooks/codex.json')
        with self.assertRaisesRegex(ValueError, 'symlink package input'):
            self.module.package_files(other)
        target = self.home / 'linked'; target.symlink_to(other, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink installation target'):
            self.module.write_owned(target, {'new.txt': b'no'})
        self.assertFalse((other / 'new.txt').exists())

    def test_invalid_release_version_is_rejected_before_copy(self):
        source = self.home / 'source'; source.mkdir()
        (source / 'plugin.json').write_text(json.dumps({'version': '../outside'}))
        with self.assertRaisesRegex(ValueError, 'Invalid package version'):
            self.module.install(source, self.home, ['cursor'], which=lambda _: None)
        self.assertFalse((self.home / '.cursor').exists())

    def test_client_error_detail_is_preserved(self):
        import sys
        from unittest.mock import patch
        from io import StringIO
        with self.assertRaises(subprocess.CalledProcessError) as failure:
            self.module.run([sys.executable, '-c', 'import sys; print("client refused", file=sys.stderr); sys.exit(3)'])
        output = StringIO()
        with patch.object(self.module, 'install', side_effect=failure.exception), patch('sys.stderr', output):
            self.assertEqual(self.module.main(['--host', 'codex']), 1)
        self.assertEqual(json.loads(output.getvalue())['detail'].strip(), 'client refused')


if __name__ == '__main__': unittest.main()
