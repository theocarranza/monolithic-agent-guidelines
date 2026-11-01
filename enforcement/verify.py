#!/usr/bin/env python3
"""Explicitly run project checks and record actual, generation-bound evidence."""
import argparse
import errno
import shlex
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from enforcement.session_state import StateStore, state_directory


def commands(root):
    config = root / '.monolithic-guidelines.json'
    if config.exists():
        data = json.loads(config.read_text(encoding='utf-8'))
        checks = data.get('verification_commands') if isinstance(data, dict) else None
        if not isinstance(checks, list) or not checks or any(
                not isinstance(check, list) or not check or any(not isinstance(arg, str) or not arg for arg in check)
                for check in checks):
            raise ValueError('verification_commands must be a nonempty list of nonempty argument arrays')
        return checks
    result = subprocess.run(['git', '-C', str(root), 'rev-parse', '--show-toplevel'], capture_output=True, text=True)
    if result.returncode == 0:
        return [['git', 'diff', '--check']]
    raise ValueError('No project checks configured; add .monolithic-guidelines.json verification_commands')


def config_digest(checks):
    return hashlib.sha256(json.dumps(checks).encode()).hexdigest()


def run_checks(root, checks, timeout=300):
    results = []
    for command in checks:
        with tempfile.TemporaryFile() as output:
            try:
                code = subprocess.run(command, cwd=root, stdout=output, stderr=subprocess.STDOUT, timeout=timeout).returncode
            except subprocess.TimeoutExpired:
                code = 124
            except OSError as error:
                output.write(str(error).encode())
                code = 127
            output.seek(0, 2)
            output.seek(max(0, output.tell() - 4096))
            results.append({'command': command, 'exit_code': code, 'output': output.read().decode('utf-8', errors='replace')})
    return results


def record(store, key, root):
    with store.transaction(key, require_existing=True) as state:
        if state['workspace'] != str(root):
            raise ValueError('Verification requires the hook session workspace')
        before = (state['generation'], state['epoch'])
    checks = commands(root)
    results = run_checks(root, checks)
    with store.transaction(key, require_existing=True) as state:
        if before != (state['generation'], state['epoch']) or config_digest(commands(root)) != config_digest(checks):
            raise ValueError('Task, checks or files changed during verification; run again')
        state['verification'] = {'generation': before[0], 'epoch': before[1],
                                 'config': config_digest(checks), 'results': results}
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--key', required=True)
    parser.add_argument('--cwd', required=True, type=Path)
    parser.add_argument('--host', choices=['codex', 'claude'], required=True)
    parser.add_argument('--state-dir', type=Path, help='Exact host-specific state directory supplied by the hook')
    args = parser.parse_args(argv)
    directory = (args.state_dir or state_directory(args.host)).absolute()
    try:
        results = record(StateStore(directory), args.key, args.cwd.resolve())
        print(json.dumps({'results': results}, indent=2))
        return 0 if all(r['exit_code'] == 0 for r in results) else 1
    except (OSError, ValueError) as error:
        detail = {'error': str(error), 'state_directory': str(directory)}
        if isinstance(error, OSError) and error.errno in (errno.EROFS, errno.EACCES, errno.EPERM):
            detail['access_required'] = ('Request write access only to this state directory. For a local Codex session, '
                                         'restart with: ' + shlex.join(['codex', '--add-dir', str(directory)]) +
                                         '. Do not disable the sandbox or alter filesystem permissions.')
        print(json.dumps(detail), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
