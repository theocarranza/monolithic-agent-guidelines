"""Policy, isolation, concurrent state and actual verification processes."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class EnforcementTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((ROOT / 'enforcement/policy.py').exists(), 'policy is not implemented')
        from enforcement import policy, session_state, verify
        self.policy, self.session_state, self.verify = policy, session_state, verify
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / 'project with spaces'
        self.project.mkdir()
        self.store = session_state.StateStore(self.root / 'state')
        self.event = {'session_id': 'a/../../b', 'cwd': str(self.project), 'hook_event_name': 'PreToolUse', 'tool_name': 'Write', 'tool_input': {'file_path': 'lib/main.dart'}}

    def test_routing_mixed_languages_and_topic_boundaries(self):
        from retrieval.catalog import Catalog
        catalog = Catalog(ROOT / 'knowledge')
        event = {**self.event, 'tool_input': {'command': 'edit lib/a.dart web/b.ts Task Option Either monoid'}}
        ids = [doc['id'] for doc in self.policy.requirements(event, catalog)]
        for identifier in ['core/principles', 'dart/guidelines', 'typescript/guidelines', 'dart/task', 'dart/option', 'dart/either', 'typescript/monoids']:
            self.assertIn(identifier, ids)
        self.assertNotIn('dart/task', [d['id'] for d in self.policy.requirements({**self.event, 'tool_input': {'command': 'multitasking'}}, catalog)])

    def test_workspace_manifests_route_shell_work(self):
        from retrieval.catalog import Catalog
        (self.project / 'pubspec.yaml').write_text('name: demo')
        (self.project / 'package.json').write_text('{}')
        event = {**self.event, 'tool_input': {}}
        ids = [doc['id'] for doc in self.policy.requirements(event, Catalog(ROOT / 'knowledge'))]
        self.assertIn('dart/guidelines', ids)
        self.assertIn('typescript/guidelines', ids)

    def test_fingerprint_detects_content_not_only_version(self):
        self.assertNotEqual(self.policy.fingerprint([{'id': 'a', 'sha256': '1', 'version': '1'}]), self.policy.fingerprint([{'id': 'a', 'sha256': '2', 'version': '1'}]))

    def test_query_exemption_is_exact_and_does_not_accept_shell_injection(self):
        import shlex
        path = shlex.quote(str(ROOT / 'retrieval/query.py'))
        for command in [f'python3 {path} fetch core/principles', f'python3 {path} catalog --language dart']:
            self.assertTrue(self.policy.internal_command({'command': command}, ROOT))
        for command in [f'python3 {path} fetch core/principles; touch x', f'python3 {path} fetch "$(touch x)"', 'python3 /tmp/query.py fetch core/principles', 'python3 retrieval/query.py fetch x >file']:
            self.assertFalse(self.policy.internal_command({'command': command}, ROOT), command)

    def test_identity_isolates_host_session_agent_transcript_and_workspace(self):
        key = self.session_state.identity(self.event, 'codex')
        self.assertRegex(key, '^[0-9a-f]{64}$')
        for extra in [{'session_id': 'different'}, {'agent_id': 'child'}, {'transcript_path': '/other'}, {'cwd': '/other'}]:
            self.assertNotEqual(key, self.session_state.identity({**self.event, **extra}, 'codex'))
        self.assertNotEqual(key, self.session_state.identity(self.event, 'claude'))
        with self.assertRaises(ValueError): self.session_state.identity({}, 'codex')

    def test_atomic_private_state_and_serialized_updates(self):
        key = self.session_state.identity(self.event, 'codex')
        def increment(_):
            with self.store.transaction(key) as state: state['generation'] += 1
        with ThreadPoolExecutor(max_workers=4) as pool: list(pool.map(increment, range(20)))
        with self.store.transaction(key) as state: self.assertEqual(state['generation'], 20)
        self.assertEqual((self.root / 'state' / (key + '.json')).stat().st_mode & 0o777, 0o600)
        with self.assertRaises(ValueError):
            with self.store.transaction('../escape'): pass

    def test_corrupt_state_and_symlinks_never_count_as_success(self):
        key = self.session_state.identity(self.event, 'codex')
        with self.store.transaction(key): pass
        file = self.root / 'state' / (key + '.json')
        for data in ['not json', '{}', '{"schema":1,"generation":-1}', '[]']:
            file.write_text(data)
            with self.subTest(data=data), self.assertRaises(ValueError):
                with self.store.transaction(key): pass
        other = 'f' * 64
        (self.root / 'state' / (other + '.json')).symlink_to(file)
        with self.assertRaises((OSError, ValueError)):
            with self.store.transaction(other): pass

    def test_check_config_and_actual_exit_codes(self):
        config = self.project / '.monolithic-guidelines.json'
        config.write_text(json.dumps({'verification_commands': [[sys.executable, '-c', 'print("passed")'], [sys.executable, '-c', 'raise SystemExit(7)']]}))
        commands = self.verify.commands(self.project)
        results = self.verify.run_checks(self.project, commands)
        self.assertEqual([r['exit_code'] for r in results], [0, 7])
        self.assertIn('passed', results[0]['output'])
        self.assertEqual(self.verify.run_checks(self.project, [['/nonexistent-program']])[0]['exit_code'], 127)
        result = self.verify.run_checks(self.project, [[sys.executable, '-c', 'import time; time.sleep(2)']], timeout=0.01)
        self.assertEqual(result[0]['exit_code'], 124)

    def test_check_config_rejects_empty_commands_and_no_implicit_shell(self):
        config = self.project / '.monolithic-guidelines.json'
        for value in [[], ['echo hello'], [[]], [['']], [[1]]]:
            config.write_text(json.dumps({'verification_commands': value}))
            with self.subTest(value=value), self.assertRaises(ValueError): self.verify.commands(self.project)
        config.write_text(json.dumps({'verification_commands': [[sys.executable, '-c', 'import sys; print(sys.argv[1])', '$(touch nope)']]}))
        result = self.verify.run_checks(self.project, self.verify.commands(self.project))
        self.assertIn('$(touch nope)', result[0]['output'])
        self.assertFalse((self.project / 'nope').exists())

    def test_non_object_verification_config_is_a_controlled_error(self):
        config = self.project / '.monolithic-guidelines.json'
        for value in [[], None, 'checks']:
            config.write_text(json.dumps(value))
            with self.subTest(value=value), self.assertRaises(ValueError): self.verify.commands(self.project)

    def test_record_rejects_wrong_workspace_and_concurrent_edits(self):
        key = self.session_state.identity(self.event, 'codex')
        config = self.project / '.monolithic-guidelines.json'
        config.write_text(json.dumps({'verification_commands': [[sys.executable, '-c', 'pass']]}))
        with self.assertRaises(ValueError): self.verify.record(self.store, key, self.project)
        with self.store.transaction(key) as state: state['workspace'] = '/unrelated/workspace'
        with self.assertRaisesRegex(ValueError, 'hook session workspace'): self.verify.record(self.store, key, self.project)
        with self.store.transaction(key) as state: state['workspace'] = str(self.project)
        code = ("import sys; sys.path.insert(0, " + repr(str(ROOT)) + "); "
                "from enforcement.session_state import StateStore; "
                "store=StateStore(" + repr(str(self.root / 'state')) + "); "
                "transaction=store.transaction(" + repr(key) + "); "
                "state=transaction.__enter__(); state['generation'] += 1; transaction.__exit__(None,None,None)")
        config.write_text(json.dumps({'verification_commands': [[sys.executable, '-c', code]]}))
        with self.assertRaisesRegex(ValueError, 'changed during verification'): self.verify.record(self.store, key, self.project)
        with self.store.transaction(key) as state: self.assertIsNone(state['verification'])

    def test_symlink_state_root_is_rejected(self):
        actual = self.root / 'actual'; actual.mkdir()
        link = self.root / 'linked'; link.symlink_to(actual, target_is_directory=True)
        store = self.session_state.StateStore(link)
        with self.assertRaises(ValueError):
            with store.transaction('a' * 64): pass

    def test_command_parser_handles_malformed_and_relative_commands(self):
        for value in [{'command': "python3 'unterminated"}, {'command': 'echo hi'}, {'command': 'python3 retrieval/query.py fetch x'}, {'command': None}, 'not an object']:
            self.assertFalse(self.policy.internal_command(value, ROOT))

    def test_unconfigured_non_git_refuses_and_git_fallback_is_explicit(self):
        with self.assertRaises(ValueError): self.verify.commands(self.project)
        subprocess.run(['git', 'init', '-q', str(self.project)], check=True)
        self.assertEqual(self.verify.commands(self.project), [['git', 'diff', '--check']])

    def test_verification_does_not_recreate_state_removed_while_waiting_for_lock(self):
        from unittest.mock import patch
        key = self.session_state.identity(self.event, 'codex')
        with self.store.transaction(key):
            pass
        path = self.store.directory / (key + '.json')
        moved = self.store.directory / 'moved-record.json'
        original_lock = self.session_state.fcntl.flock
        def acquire_then_move(descriptor, operation):
            original_lock(descriptor, operation)
            path.rename(moved)
        with patch('enforcement.session_state.fcntl.flock', side_effect=acquire_then_move):
            with self.assertRaisesRegex(ValueError, 'disappeared'):
                with self.store.transaction(key, require_existing=True):
                    self.fail('Missing state must not be yielded')
        self.assertFalse(path.exists())
        self.assertTrue(moved.is_file())


if __name__ == '__main__': unittest.main()
