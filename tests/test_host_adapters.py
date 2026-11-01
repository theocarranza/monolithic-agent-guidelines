"""Drive the shipped host executables through actual JSON stdin/stdout."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class HostTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / 'project with spaces'
        self.project.mkdir()
        self.env = {**os.environ, 'PLUGIN_DATA': str(self.root / 'plugin data')}
        self.key = None

    def call(self, host, event, **extra):
        script = ROOT / 'enforcement/adapters' / (host + '.py')
        self.assertTrue(script.exists(), 'host adapter is not implemented')
        payload = {'session_id': 'test-session', 'transcript_path': '/test/transcript', 'cwd': str(self.project), 'hook_event_name': event, **extra}
        result = subprocess.run([sys.executable, str(script)], input=json.dumps(payload), text=True, capture_output=True, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def pre(self, host, **extra):
        return self.call(host, 'PreToolUse', tool_name='Write', tool_input={'file_path': 'lib/main.dart'}, **extra)

    def verified(self, host):
        from enforcement.session_state import identity
        key = identity({'session_id': 'test-session', 'transcript_path': '/test/transcript', 'cwd': str(self.project)}, host)
        (self.project / '.monolithic-guidelines.json').write_text(json.dumps({'verification_commands': [[sys.executable, '-c', 'print("real checks passed")']]}))
        result = subprocess.run([sys.executable, str(ROOT / 'enforcement/verify.py'), '--key', key, '--cwd', str(self.project), '--host', host], text=True, capture_output=True, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_lifecycle_denial_retry_evidence_and_completion_both_hosts(self):
        for host in ['codex', 'claude']:
            with self.subTest(host=host):
                start = self.call(host, 'SessionStart', source='startup')
                self.assertIn('Think Before Coding', start['hookSpecificOutput']['additionalContext'])
                first = self.pre(host)['hookSpecificOutput']
                self.assertEqual(first['permissionDecision'], 'deny')
                self.assertIn('Strict functional Dart', first['permissionDecisionReason'])
                self.assertIn('sha256', first['permissionDecisionReason'])
                self.assertEqual(self.pre(host), {})
                self.call(host, 'PostToolUse', tool_name='Write', tool_input={'file_path': 'lib/main.dart'}, tool_response={'success': True})
                stop = self.call(host, 'Stop')
                self.assertEqual(stop['decision'], 'block')
                self.assertIn('enforcement/verify.py', stop['reason'])
                self.verified(host)
                self.assertEqual(self.call(host, 'Stop'), {})
                self.assertEqual(self.pre(host), {})
                self.assertEqual(self.call(host, 'Stop')['decision'], 'block')

    def test_verified_stop_finishes_task_and_does_not_warn_on_continuation(self):
        self.pre('codex'); self.pre('codex')
        self.assertEqual(self.call('codex', 'Stop')['decision'], 'block')
        self.verified('codex')
        self.assertEqual(self.call('codex', 'Stop', stop_hook_active=True), {})
        self.call('codex', 'UserPromptSubmit', prompt='Explain what changed without using tools.')
        self.assertEqual(self.call('codex', 'Stop'), {})

    def test_repeated_stop_allows_explicit_unverified_status_without_loop(self):
        self.pre('codex'); self.pre('codex')
        result = self.call('codex', 'Stop', stop_hook_active=True)
        self.assertNotIn('decision', result)
        self.assertIn('unverified', result['systemMessage'].lower())

    def test_new_prompt_resume_and_compaction_invalidate_receipts(self):
        for event, kwargs in [('UserPromptSubmit', {'prompt': 'TypeScript Task error'}), ('SessionStart', {'source': 'resume'}), ('PostCompact', {'trigger': 'auto'}), ('SessionStart', {'source': 'compact'})]:
            self.pre('codex'); self.pre('codex')
            self.call('codex', event, **kwargs)
            self.assertEqual(self.pre('codex')['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_prompt_and_tool_languages_accumulate(self):
        self.call('claude', 'UserPromptSubmit', prompt='Review TypeScript monoid and Dart Task')
        result = self.pre('claude')['hookSpecificOutput']['permissionDecisionReason']
        self.assertIn('typescript/monoids', result)
        self.assertIn('dart/task', result)

    def test_native_reads_and_exact_retrieval_do_not_need_checks(self):
        self.assertEqual(self.call('codex', 'PreToolUse', tool_name='Read', tool_input={'file_path': 'main.dart'}), {})
        self.assertEqual(self.call('codex', 'Stop'), {})
        command = 'python3 ' + shlex.quote(str(ROOT / 'retrieval/query.py')) + ' fetch core/principles'
        self.assertEqual(self.call('codex', 'PreToolUse', tool_name='Bash', tool_input={'command': command}), {})
        self.call('codex', 'PostToolUse', tool_name='Bash', tool_input={'command': command})
        self.assertEqual(self.call('codex', 'Stop'), {})

    def test_malformed_hook_input_produces_real_denial(self):
        for host in ['codex', 'claude']:
            script = ROOT / 'enforcement/adapters' / (host + '.py')
            self.assertTrue(script.exists(), 'host adapter is not implemented')
            result = subprocess.run([sys.executable, str(script)], input='not json', text=True, capture_output=True, env=self.env)
            self.assertEqual(result.returncode, 2)
            self.assertIn('guidance', result.stderr.lower())

    def test_store_changes_force_retrieval_even_without_a_version_bump(self):
        import shutil
        from unittest.mock import patch
        from enforcement.adapters import common
        from enforcement.session_state import StateStore
        fixture = self.root / 'plugin'
        shutil.copytree(ROOT / 'knowledge', fixture / 'knowledge')
        store = StateStore(self.root / 'isolated')
        event = {'session_id': 'update', 'cwd': str(self.project), 'hook_event_name': 'PreToolUse', 'tool_name': 'Write', 'tool_input': {'file_path': 'main.dart'}}
        with patch.object(common, 'ROOT', fixture):
            self.assertEqual(common.dispatch(event, 'codex', store)['hookSpecificOutput']['permissionDecision'], 'deny')
            self.assertEqual(common.dispatch(event, 'codex', store), {})
            source = fixture / 'knowledge/dart/guidelines.md'
            source.write_text(source.read_text() + '\nUpdated project contract.\n')
            result = common.dispatch(event, 'codex', store)['hookSpecificOutput']
            self.assertIn('Updated project contract', result['permissionDecisionReason'])
            self.assertNotIn('Reference {"id": "core/principles"', result['permissionDecisionReason'])
            event['hook_event_name'] = 'Stop'
            source.write_text(source.read_text() + '\nReview needs fresh guidance.\n')
            self.assertIn('Review needs fresh guidance', common.dispatch(event, 'codex', store)['reason'])

    def test_invalid_events_corrupt_state_and_stop_escape(self):
        from enforcement.adapters.common import dispatch
        from enforcement.session_state import StateStore, identity
        store = StateStore(self.root / 'isolated')
        with self.assertRaises(ValueError): dispatch([], 'codex', store)
        event = {'session_id': 'test-session', 'transcript_path': '/test/transcript', 'cwd': str(self.project)}
        self.pre('codex')
        key = identity(event, 'codex')
        (self.root / 'plugin data/codex' / (key + '.json')).write_text('broken')
        self.assertIn('unverified', self.call('codex', 'Stop', stop_hook_active=True)['systemMessage'])
        script = ROOT / 'enforcement/adapters/codex.py'
        result = subprocess.run([sys.executable, str(script)], input=json.dumps({**event, 'hook_event_name': 'PreToolUse'}), text=True, capture_output=True, env=self.env)
        self.assertEqual(result.returncode, 2)

    def test_failed_and_reconfigured_checks_do_not_satisfy_completion(self):
        from enforcement.session_state import identity
        self.pre('codex'); self.pre('codex')
        key = identity({'session_id': 'test-session', 'transcript_path': '/test/transcript', 'cwd': str(self.project)}, 'codex')
        config = self.project / '.monolithic-guidelines.json'
        config.write_text(json.dumps({'verification_commands': [[sys.executable, '-c', 'raise SystemExit(9)']]}))
        command = [sys.executable, str(ROOT / 'enforcement/verify.py'), '--key', key, '--cwd', str(self.project), '--host', 'codex']
        result = subprocess.run(command, text=True, capture_output=True, env=self.env)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.call('codex', 'Stop')['decision'], 'block')
        self.verified('codex')
        config.write_text(json.dumps({'verification_commands': [[sys.executable, '-c', 'print("new check")']]}))
        self.assertEqual(self.call('codex', 'Stop')['decision'], 'block')
        bad = subprocess.run([*command[:3], 'a' * 64, *command[4:]], text=True, capture_output=True, env=self.env)
        self.assertEqual(bad.returncode, 2)

    def test_importing_entrypoints_does_not_execute_hooks_or_queries(self):
        code = 'import enforcement.adapters.codex; import enforcement.adapters.claude; import retrieval.query'
        result = subprocess.run([sys.executable, '-c', code], cwd=ROOT, input='invalid hook input', text=True, capture_output=True, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '')
        self.assertFalse((self.root / 'plugin data').exists())

    def test_status_never_claims_host_trust_from_files(self):
        script = ROOT / 'enforcement/adapters/codex.py'
        self.assertTrue(script.exists(), 'host adapter is not implemented')
        result = subprocess.run([sys.executable, str(script), '--status'], text=True, capture_output=True, env=self.env)
        self.assertEqual(json.loads(result.stdout)['enforcement'], 'unverified')

    def test_compaction_and_resume_reload_accumulated_language_scope(self):
        for reset, extra in [('PostCompact', {}), ('SessionStart', {'source': 'resume'}), ('SessionStart', {'source': 'compact'})]:
            with self.subTest(reset=reset, extra=extra):
                self.call('codex', 'UserPromptSubmit', prompt='Change nested Dart Task error handling')
                self.pre('codex'); self.pre('codex')
                self.call('codex', reset, **extra)
                result = self.call('codex', 'PreToolUse', tool_name='Bash', tool_input={'command': 'pwd'})
                reason = result['hookSpecificOutput']['permissionDecisionReason']
                self.assertIn('dart/guidelines', reason)
                self.assertIn('dart/task', reason)
                self.assertIn('dart/either', reason)

    def test_malformed_nested_state_returns_blocking_error(self):
        from enforcement.session_state import identity
        key = identity({'session_id': 'test-session', 'transcript_path': '/test/transcript', 'cwd': str(self.project)}, 'codex')
        self.pre('codex'); self.pre('codex')
        path = self.root / 'plugin data/codex' / (key + '.json')
        original = json.loads(path.read_text())
        for changes in [{'scope': [None]}, {'receipts': {'core/principles': [7]}}, {'verification': {'generation': 1, 'epoch': 0, 'config': 'bad', 'results': [None]}}]:
            with self.subTest(changes=changes):
                path.write_text(json.dumps({**original, **changes}))
                script = ROOT / 'enforcement/adapters/codex.py'
                payload = {'session_id': 'test-session', 'transcript_path': '/test/transcript', 'cwd': str(self.project), 'hook_event_name': 'Stop'}
                result = subprocess.run([sys.executable, str(script)], input=json.dumps(payload), text=True, capture_output=True, env=self.env)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertNotIn('Traceback', result.stderr)

    def test_unconfigured_completion_reports_checks_and_unknown_events_are_ignored(self):
        self.pre('codex'); self.pre('codex')
        result = self.call('codex', 'Stop')
        self.assertEqual(result['decision'], 'block')
        self.assertIn('No project checks configured', result['reason'])
        self.assertEqual(self.call('codex', 'UnrecognizedEvent'), {})
        self.assertEqual(self.call('codex', 'PostCompact'), {})

    def test_completion_command_shares_state_without_hook_environment(self):
        self.pre('codex'); self.pre('codex')
        config = self.project / '.monolithic-guidelines.json'
        config.write_text(json.dumps({'verification_commands': [[sys.executable, '-c', 'print("check ran")']]}))
        stop = self.call('codex', 'Stop')
        command = stop['reason'].split('Run explicitly:\n', 1)[1].split('\n', 1)[0]
        self.assertIn('--state-dir', command)
        environment = {k: v for k, v in self.env.items() if k not in ('PLUGIN_DATA', 'CLAUDE_PLUGIN_DATA')}
        environment['XDG_STATE_HOME'] = str(self.root / 'unrelated state')
        result = subprocess.run(shlex.split(command), cwd=self.project, env=environment, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('check ran', result.stdout)
        self.assertEqual(self.call('codex', 'Stop'), {})
        self.assertFalse((self.root / 'unrelated state').exists())

    def test_explicit_missing_state_does_not_create_a_new_session(self):
        absent = self.root / 'absent state'
        script = ROOT / 'enforcement/verify.py'
        result = subprocess.run([sys.executable, str(script), '--key', 'a' * 64,
                                 '--cwd', str(self.project), '--host', 'codex', '--state-dir', str(absent)],
                                text=True, capture_output=True, env=self.env)
        self.assertEqual(result.returncode, 2)
        self.assertIn('No hook session state', result.stderr)
        self.assertFalse(absent.exists())

    @unittest.skipUnless(hasattr(os, 'geteuid') and os.geteuid() == 0 and any(int(line.split()[2]) > 65534 for line in Path('/proc/self/uid_map').read_text().splitlines()) and any(int(line.split()[2]) > 65534 for line in Path('/proc/self/gid_map').read_text().splitlines()), 'requires a mapped unprivileged UID/GID')
    def test_state_write_denial_preserves_gate_and_reports_narrow_grant(self):
        self.pre('codex'); self.pre('codex')
        (self.project / '.monolithic-guidelines.json').write_text(json.dumps({'verification_commands': [[sys.executable, '-c', 'print("check ran")']]}))
        stop = self.call('codex', 'Stop')
        command = stop['reason'].split('Run explicitly:\n', 1)[1].split('\n', 1)[0]
        state_dir = self.root / 'plugin data/codex'
        for directory in [self.root, self.project, state_dir.parent]:
            directory.chmod(0o755)
        for file in state_dir.iterdir():
            file.chmod(0o644)
        state_dir.chmod(0o555)
        result = subprocess.run(shlex.split(command), cwd=self.project, env=self.env,
                                user=65534, group=65534, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stderr)
        detail = json.loads(result.stderr)
        self.assertEqual(detail['state_directory'], str(state_dir))
        self.assertIn('--add-dir', detail['access_required'])
        self.assertNotIn('check ran', result.stdout)
        self.assertEqual(self.call('codex', 'Stop')['decision'], 'block')
        # Permit only this isolated state directory for the test user.
        for file in state_dir.iterdir():
            file.chown(65534, 65534)
        state_dir.chown(65534, 65534)
        state_dir.chmod(0o700)
        environment = {k: v for k, v in self.env.items() if k not in ('PLUGIN_DATA', 'CLAUDE_PLUGIN_DATA')}
        result = subprocess.run(shlex.split(command), cwd=self.project, env=environment,
                                user=65534, group=65534, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('check ran', result.stdout)
        self.assertEqual(self.call('codex', 'Stop'), {})

    def test_read_only_lock_failure_leaves_completion_blocked_until_access_is_available(self):
        import errno
        import io
        from contextlib import redirect_stderr, redirect_stdout
        from unittest.mock import patch
        from enforcement import verify
        self.pre('codex'); self.pre('codex')
        (self.project / '.monolithic-guidelines.json').write_text(json.dumps({'verification_commands': [[sys.executable, '-c', 'print("check ran")']]}))
        command = self.call('codex', 'Stop')['reason'].split('Run explicitly:\n', 1)[1].split('\n', 1)[0]
        args = shlex.split(command)[2:]
        for error_number in (errno.EROFS, errno.EACCES, errno.EPERM):
            error_output = io.StringIO()
            with patch('enforcement.session_state.os.open', side_effect=OSError(error_number, 'state write denied')), redirect_stderr(error_output):
                self.assertEqual(verify.main(args), 2)
            detail = json.loads(error_output.getvalue())
            self.assertEqual(detail['state_directory'], str(self.root / 'plugin data/codex'))
            self.assertIn('--add-dir', detail['access_required'])
            self.assertEqual(self.call('codex', 'Stop')['decision'], 'block')
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(verify.main(args), 0)
        self.assertIn('check ran', output.getvalue())
        self.assertEqual(self.call('codex', 'Stop'), {})

    def test_explicit_symlink_state_directory_is_refused(self):
        self.pre('codex'); self.pre('codex')
        (self.project / '.monolithic-guidelines.json').write_text(json.dumps({'verification_commands': [[sys.executable, '-c', 'pass']]}))
        command = self.call('codex', 'Stop')['reason'].split('Run explicitly:\n', 1)[1].split('\n', 1)[0]
        args = shlex.split(command)
        alias = self.root / 'alias'
        alias.symlink_to(self.root / 'plugin data/codex', target_is_directory=True)
        args[-1] = str(alias)
        result = subprocess.run(args, capture_output=True, text=True, env=self.env)
        self.assertEqual(result.returncode, 2)
        self.assertIn('symlink', result.stderr)


if __name__ == '__main__': unittest.main()
