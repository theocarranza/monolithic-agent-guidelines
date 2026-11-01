"""Lifecycle guardrails shared by Codex and Claude command-hook adapters."""
import json
from pathlib import Path
import shlex
import sys

from enforcement.policy import guarded, potential_change, requirements
from enforcement.session_state import StateStore, identity, state_directory
from enforcement.verify import commands, config_digest
from retrieval.catalog import Catalog

ROOT = Path(__file__).resolve().parents[2]


def startup(root):
    query = 'python3 ' + shlex.quote(str(root / 'retrieval/query.py'))
    return (
        'Monolithic Agent Guidelines: Think Before Coding — expose assumptions; '
        'Simplicity First — build only what is needed; Surgical Changes — keep edits '
        'focused; Goal-Driven Execution — define success and verify it.\n'
        'Existing project requirements, permissions and explicit approval gates prevail. '
        'Before substantial planning, coding or review, fetch the full principles and '
        'relevant language/topic references. Reload after resume, compaction and scope changes.\n'
        + query + ' catalog\n' + query + ' fetch core/principles\n'
        'Hooks are guardrails, not proof of comprehension or a complete security boundary.'
    )


def context(event_name, text):
    return {'hookSpecificOutput': {'hookEventName': event_name, 'additionalContext': text}}


def deny(text):
    return {'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'deny',
                                   'permissionDecisionReason': text}}


def render(documents):
    return '\n\n'.join(
        'Reference ' + json.dumps({key: doc[key] for key in ['id', 'title', 'version', 'provenance', 'sha256']})
        + '\n' + doc['content'] for doc in documents)


def select(event, catalog, state):
    selected = {doc['id']: doc for doc in requirements(event, catalog)}
    for identifier in state.get('scope', []):
        selected[identifier] = catalog.fetch(identifier)
    state['scope'] = sorted(selected)
    return [selected[identifier] for identifier in sorted(selected)]


def refresh(documents, state):
    missing = [doc for doc in documents if state['receipts'].get(doc['id']) != [doc['version'], doc['sha256']]]
    if missing:
        state['verification'] = None
        for doc in missing:
            state['receipts'][doc['id']] = [doc['version'], doc['sha256']]
    return missing


def verifier_command(host, key, cwd, directory):
    return shlex.join(['python3', str(ROOT / 'enforcement/verify.py'), '--key', key,
                       '--cwd', cwd, '--host', host, '--state-dir', str(directory.resolve())])


def dispatch(event, host, store):
    if not isinstance(event, dict):
        raise ValueError('Expected a hook JSON object')
    key = identity(event, host)
    name = event.get('hook_event_name')
    cwd = str(Path(event['cwd']).resolve())
    with store.transaction(key) as state:
        state['workspace'] = cwd
        if name in ('SessionStart', 'PostCompact', 'UserPromptSubmit'):
            state['epoch'] += 1
            state['receipts'] = {}
            state['verification'] = None
            if name == 'UserPromptSubmit':
                state['scope'] = [doc['id'] for doc in requirements(event, Catalog(ROOT / 'knowledge'))]
            elif name == 'SessionStart' and event.get('source') not in ('resume', 'compact'):
                state['scope'] = []
            return {} if name == 'PostCompact' else context(name, startup(ROOT))
        if name == 'PreToolUse':
            if not guarded(event, ROOT):
                return {}
            missing = refresh(select(event, Catalog(ROOT / 'knowledge'), state), state)
            if missing:
                return deny('Required guidance follows. Read it, then retry the action. '
                            'This grants no additional permission.\n\n' + render(missing))
            # Invalidate before execution as well as afterwards: checks must not race edits.
            state['generation'] += 1
            state['dirty'] = True
            state['verification'] = None
            return {}
        if name == 'PostToolUse':
            if potential_change(event, ROOT):
                state['generation'] += 1
                state['dirty'] = True
                state['verification'] = None
            return {}
        if name == 'Stop' and state['dirty']:
            missing = refresh(select(event, Catalog(ROOT / 'knowledge'), state), state)
            evidence = state['verification']
            try:
                checks = commands(Path(cwd))
                success = (not missing and evidence and evidence.get('generation') == state['generation']
                           and evidence.get('epoch') == state['epoch']
                           and evidence.get('config') == config_digest(checks)
                           and evidence.get('results') and all(r.get('exit_code') == 0 for r in evidence['results']))
            except (OSError, ValueError) as error:
                success = False
                detail = str(error) + '\n'
            else:
                detail = ''
            if success:
                state['dirty'] = False
                return {}
            if event.get('stop_hook_active'):
                return {'systemMessage': 'Work remains unverified. Report the blocker and missing evidence; do not claim verified completion.'}
            if missing:
                return {'decision': 'block', 'reason': 'Reload guidance before completing.\n\n' + render(missing)}
            if not success:
                return {'decision': 'block', 'reason': detail + 'Verification evidence is missing, failed or stale. Run explicitly:\n'
                        + verifier_command(host, key, cwd, store.directory)
                        + '\nThe verifier needs write access only to ' + str(store.directory.resolve())
                        + '. If the sandbox denies access, request that narrow grant or restart local Codex with '
                        + shlex.join(['codex', '--add-dir', str(store.directory.resolve())])
                        + '. Never broaden sandbox permissions automatically.'
                        + '\nReport what the configured checks prove. Do not claim more.'}
        return {}


def main(host, argv=None):
    if (sys.argv[1:] if argv is None else argv) == ['--status']:
        print(json.dumps({'host': host, 'enforcement': 'unverified',
                          'reason': 'Installed hooks require host support, trust and a successful live smoke test.'}))
        return 0
    event = None
    try:
        event = json.load(sys.stdin)
        result = dispatch(event, host, StateStore(state_directory(host)))
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as error:
        message = 'Guidance hook could not establish its requirements: ' + str(error)
        if isinstance(event, dict) and event.get('hook_event_name') == 'Stop' and event.get('stop_hook_active'):
            print(json.dumps({'systemMessage': 'Work is unverified. ' + message}))
            return 0
        # Exit 2 is the documented blocking feedback path for both hosts.
        print(message, file=sys.stderr)
        return 2
