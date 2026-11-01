"""Optional real-client discovery test; uses a disposable CODEX_HOME, without a model."""
import argparse
import json
import os
from pathlib import Path
import queue
import signal
import subprocess
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = 'monolithic-agent-guidelines@monolithic-agent-guidelines'


def check(binary):
    with tempfile.TemporaryDirectory(prefix='guidelines-codex-') as temporary:
        fixture = Path(temporary)
        home = fixture / 'home'; home.mkdir()
        project = fixture / 'project'; project.mkdir()
        (home / 'config.toml').write_text(
            '[features]\nremote_plugin = false\napps = false\n'
            '[projects.' + json.dumps(str(project)) + ']\ntrust_level = "trusted"\n')
        env = {**os.environ, 'CODEX_HOME': str(home)}
        for arguments in [['plugin', 'marketplace', 'add', str(ROOT), '--json'],
                          ['plugin', 'add', PLUGIN, '--json']]:
            subprocess.run([binary, *arguments], env=env, cwd=project, capture_output=True, text=True,
                           timeout=20, check=True)
        with (fixture / 'stderr.log').open('w') as log:
            process = subprocess.Popen([binary, 'app-server', '--stdio'], env=env, cwd=project,
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=log, text=True, start_new_session=True)
            responses = queue.Queue()
            def read_output():
                for line in process.stdout:
                    responses.put(json.loads(line))
            reader = threading.Thread(target=read_output, daemon=True)
            reader.start()
            def rpc(identifier, method, params):
                process.stdin.write(json.dumps({'id': identifier, 'method': method, 'params': params}) + '\n')
                process.stdin.flush()
                while True:
                    item = responses.get(timeout=20)
                    if item.get('id') == identifier:
                        if 'error' in item:
                            raise RuntimeError(item['error'])
                        return item['result']
            try:
                initialized = rpc(1, 'initialize', {'clientInfo': {'name': 'guidelines_test', 'version': '1.0'},
                                                   'capabilities': {'experimentalApi': True}})
                process.stdin.write('{"method":"initialized","params":{}}\n')
                process.stdin.flush()
                result = rpc(2, 'hooks/list', {'cwds': [str(project)]})['data'][0]
                hooks = [hook for hook in result['hooks'] if hook.get('pluginId') == PLUGIN]
                expected = {'sessionStart', 'userPromptSubmit', 'preToolUse', 'postToolUse', 'stop', 'postCompact'}
                assert {hook['eventName'] for hook in hooks} == expected, hooks
                assert all(hook['enabled'] and hook['trustStatus'] == 'untrusted' for hook in hooks), hooks
                assert not result['errors'], result['errors']
                for hook in hooks:
                    assert Path(hook['sourcePath']).is_file(), hook
                return {'client': initialized['userAgent'], 'hooks': sorted(expected),
                        'trust': 'untrusted (expected)', 'errors': result['errors'],
                        'live_execution': 'not tested'}
            finally:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
                process.stdin.close()
                reader.join(timeout=5)
                process.stdout.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('codex_binary', help='Absolute path to the Codex executable')
    print(json.dumps(check(parser.parse_args().codex_binary), indent=2))
