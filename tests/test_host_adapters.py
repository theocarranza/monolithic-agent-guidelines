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

    def test_canonical_behavior_guidance_delivered_from_prompt_then_retry_allowed(self):
        for host in ['codex', 'claude']:
            with self.subTest(host=host):
                self.call(host, 'UserPromptSubmit', prompt='Use database and JSON adapters for the same workflow')
                first = self.call(host, 'PreToolUse', tool_name='Bash', tool_input={'command': 'pwd'})
                output = first['hookSpecificOutput']
                self.assertEqual(output['permissionDecision'], 'deny')
                self.assertIn('"id": "shared/canonical-behavior"', output['permissionDecisionReason'])
                self.assertEqual(self.call(host, 'PreToolUse', tool_name='Bash', tool_input={'command': 'pwd'}), {})
                self.assertEqual(self.call(host, 'Stop'), {})


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
                payload = {'session_id': 'test-session', 'transcript_path': '/test/transcript', 'cwd': str(self.project), 'hook_event_name': 'PreToolUse', 'tool_name': 'Write', 'tool_input': {'file_path': 'main.dart'}}
                result = subprocess.run([sys.executable, str(script)], input=json.dumps(payload), text=True, capture_output=True, env=self.env)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertNotIn('Traceback', result.stderr)


    def test_pwd_gate_retry_and_completion_need_no_verifier_both_hosts(self):
        from enforcement.session_state import identity
        for host in ['codex', 'claude']:
            with self.subTest(host=host):
                self.call(host, 'SessionStart', source='startup')
                self.call(host, 'UserPromptSubmit', prompt='Run pwd without modifying files')
                first = self.call(host, 'PreToolUse', tool_name='Bash', tool_input={'command': 'pwd'})
                self.assertEqual(first['hookSpecificOutput']['permissionDecision'], 'deny')
                self.assertIn('core/principles', first['hookSpecificOutput']['permissionDecisionReason'])
                self.assertNotIn('verify.py', first['hookSpecificOutput']['permissionDecisionReason'])
                self.assertEqual(self.call(host, 'PreToolUse', tool_name='Bash', tool_input={'command': 'pwd'}), {})
                result = subprocess.run(['pwd'], cwd=self.project, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout.strip(), str(self.project))
                key = identity({'session_id': 'test-session', 'transcript_path': '/test/transcript', 'cwd': str(self.project)}, host)
                record = self.root / 'plugin data' / host / (key + '.json')
                before = record.read_bytes()
                self.assertEqual(self.call(host, 'PostToolUse', tool_name='Bash', tool_input={'command': 'pwd'}), {})
                self.assertEqual(self.call(host, 'Stop'), {})
                self.assertEqual(record.read_bytes(), before)
                self.assertEqual(list(self.project.iterdir()), [])

    def test_retired_events_do_not_read_or_write_even_corrupt_legacy_state(self):
        self.pre('codex')
        state = next((self.root / 'plugin data/codex').glob('*.json'))
        state.write_text('broken old completion record')
        for event in ['Stop', 'PostToolUse', 'UnrecognizedEvent']:
            self.assertEqual(self.call('codex', event), {})
        self.assertEqual(state.read_text(), 'broken old completion record')

    def test_default_registrations_only_handle_guidance(self):
        for path, expected in [('hooks/codex.json', {'SessionStart', 'UserPromptSubmit', 'PreToolUse', 'PostCompact'}),
                               ('hooks/hooks.json', {'SessionStart', 'UserPromptSubmit', 'PreToolUse'})]:
            events = json.loads((ROOT / path).read_text())['hooks']
            self.assertEqual(set(events), expected)


if __name__ == '__main__': unittest.main()
