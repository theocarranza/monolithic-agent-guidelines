"""Private Linux session state, locked across processes and replaced atomically."""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


def identity(event, host):
    if not isinstance(event.get('session_id'), str) or not event['session_id'] or not isinstance(event.get('cwd'), str):
        raise ValueError('Hook requires a session_id and cwd')
    fields = [host, event['session_id'], str(Path(event['cwd']).resolve()), event.get('agent_id'), event.get('transcript_path')]
    return hashlib.sha256(json.dumps(fields).encode()).hexdigest()


def empty_state():
    return {'schema': 1, 'generation': 0, 'epoch': 0, 'receipts': {}, 'dirty': False,
            'verification': None, 'workspace': None}


def valid_evidence(evidence):
    return (evidence is None or isinstance(evidence, dict)
            and type(evidence.get('generation')) is int and evidence['generation'] >= 0
            and type(evidence.get('epoch')) is int and evidence['epoch'] >= 0
            and isinstance(evidence.get('config'), str)
            and isinstance(evidence.get('results'), list) and bool(evidence['results'])
            and all(isinstance(result, dict) and type(result.get('exit_code')) is int
                    and isinstance(result.get('command'), list) and bool(result['command'])
                    and all(isinstance(arg, str) and arg for arg in result['command'])
                    and isinstance(result.get('output'), str) for result in evidence['results']))


def valid(state):
    return (isinstance(state, dict) and state.get('schema') == 1
            and type(state.get('generation')) is int and state['generation'] >= 0
            and type(state.get('epoch')) is int and state['epoch'] >= 0
            and isinstance(state.get('receipts'), dict) and type(state.get('dirty')) is bool
            and all(isinstance(key, str) and isinstance(value, list) and len(value) == 2
                    and all(isinstance(part, str) and part for part in value)
                    for key, value in state['receipts'].items())
            and isinstance(state.get('scope', []), list)
            and all(isinstance(identifier, str) and identifier for identifier in state.get('scope', []))
            and valid_evidence(state.get('verification'))
            and (state.get('workspace') is None or isinstance(state['workspace'], str)))


class StateStore:
    def __init__(self, directory):
        self.directory = Path(directory)

    @contextmanager
    def transaction(self, key, require_existing=False):
        if not re.fullmatch('[0-9a-f]{64}', key):
            raise ValueError('Invalid session state key')
        if self.directory.is_symlink():
            raise ValueError('Refusing symlink state directory')
        path = self.directory / (key + '.json')
        if require_existing and not path.is_file():
            raise ValueError('No hook session state at ' + str(path) + '; use the current hook-supplied verifier command')
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        lock = self.directory / (key + '.lock')
        descriptor = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, 'r+') as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            if path.is_symlink():
                raise ValueError('Refusing symlink session state')
            if require_existing and not path.is_file():
                raise ValueError('No hook session state at ' + str(path) + '; it disappeared while waiting for its lock')
            state = json.loads(path.read_text(encoding='utf-8')) if path.exists() else empty_state()
            if not valid(state):
                raise ValueError('Invalid session state; use a new session or resolve state manually')
            yield state
            descriptor, temporary = tempfile.mkstemp(prefix=key + '.', dir=self.directory)
            with os.fdopen(descriptor, 'w', encoding='utf-8') as output:
                json.dump(state, output, ensure_ascii=False)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, path)


def state_directory(host):
    data = os.environ.get('PLUGIN_DATA') or os.environ.get('CLAUDE_PLUGIN_DATA')
    base = Path(data) if data else Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state'))) / 'monolithic-agent-guidelines'
    return base / host
