#!/usr/bin/env python3
"""Install user-scoped packages into selected supported local agent hosts."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_codex_package import DIRECTORIES, FILES

NAME = 'monolithic-agent-guidelines'
REPOSITORY = 'https://github.com/theocarranza/monolithic-agent-guidelines'
CODEX_ID = NAME + '@' + NAME
CLAUDE_ID = 'andrej-karpathy-skills@' + NAME
MARKER = '.monolithic-agent-guidelines-install.json'
HOSTS = ('codex', 'claude', 'cursor')


def run(args):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=120)


def selected_hosts(requested, home, which):
    requested = list(dict.fromkeys(host for value in requested for host in value.split(',')))
    if not requested or any(host not in (*HOSTS, 'all') for host in requested) or ('all' in requested and len(requested) != 1):
        raise ValueError('Use --host all or select codex, claude, cursor (repeatable or comma-separated)')
    available = {host: bool(which(host)) for host in HOSTS}
    available['cursor'] = available['cursor'] or bool(which('cursor-agent')) or (home / '.cursor').is_dir()
    if requested == ['all']:
        selected = [host for host in HOSTS if available[host]]
        unavailable = [host for host in HOSTS if not available[host]]
        if not selected:
            raise ValueError('No supported local hosts found; install a client or explicitly select --host cursor')
        return selected, unavailable
    missing = [host for host in requested if host != 'cursor' and not available[host]]
    if missing:
        raise ValueError('Required client command is unavailable: ' + ', '.join(missing))
    return [host for host in HOSTS if host in requested], []


def package_files(source):
    paths = [source / name for name in (*FILES, 'plugin.json')]
    for name in (*DIRECTORIES, '.agents', '.claude-plugin', 'dist/codex'):
        directory = source / name
        if directory.is_symlink():
            raise ValueError('Refusing symlink package source: ' + str(directory))
        paths.extend(path for path in directory.rglob('*') if '__pycache__' not in path.parts
                     and path.suffix != '.pyc' and (path.is_file() or path.is_symlink()))
    if any(path.is_symlink() for path in paths):
        raise ValueError('Refusing symlink package input')
    files = {str(path.relative_to(source)): path.read_bytes() for path in paths}
    marketplace = json.loads(files['.claude-plugin/marketplace.json'])
    marketplace['name'] = NAME
    marketplace['id'] = NAME
    files['.claude-plugin/marketplace.json'] = (json.dumps(marketplace, indent=2) + '\n').encode()
    return files


def write_owned(target, files):
    if target.is_symlink() or any(parent.is_symlink() for parent in target.parents):
        raise ValueError('Refusing symlink installation target: ' + str(target))
    manifest = {path: hashlib.sha256(content).hexdigest() for path, content in files.items()}
    marker = target / MARKER
    if target.exists():
        if not marker.is_file() or marker.is_symlink():
            raise ValueError('Refusing unowned installation directory: ' + str(target))
        previous = json.loads(marker.read_text())
        if not isinstance(previous, dict) or previous.get('owner') != REPOSITORY or previous.get('schema') != 1 or not isinstance(previous.get('files'), dict):
            raise ValueError('Invalid installation ownership record: ' + str(target))
        actual = {str(path.relative_to(target)) for path in target.rglob('*') if path.is_file() or path.is_symlink()}
        if actual != set(previous['files']) | {MARKER}:
            raise ValueError('Installation contains modified or unowned files: ' + str(target))
        for path, digest in previous['files'].items():
            file = target / path
            if Path(path).is_absolute() or '..' in Path(path).parts or file.is_symlink() or any(parent.is_symlink() for parent in file.parents) or hashlib.sha256(file.read_bytes()).hexdigest() != digest:
                raise ValueError('Installation was modified; preserve/reconcile it manually: ' + str(file))
        if set(previous['files']) - set(files):
            raise ValueError('Old managed files require manual review; installer never deletes files')
    # Preflight paths before writing any part of this package.
    for path in files:
        file = target / path
        if file.is_symlink() or any(parent.is_symlink() for parent in file.parents):
            raise ValueError('Refusing symlink installation output: ' + str(file))
    target.mkdir(parents=True, exist_ok=True)
    for path, content in files.items():
        file = target / path
        file.parent.mkdir(parents=True, exist_ok=True)
        if not file.is_file() or file.read_bytes() != content:
            file.write_bytes(content)
    marker.write_text(json.dumps({'schema': 1, 'owner': REPOSITORY, 'files': manifest}, indent=2) + '\n')


def marketplace(runner, client, package, release_base):
    raw = json.loads(runner([client, 'plugin', 'marketplace', 'list', '--json']).stdout)
    entries = raw.get('marketplaces', []) if isinstance(raw, dict) else raw
    existing = next((entry for entry in entries if entry.get('name') == NAME), None)
    if existing:
        source = existing.get('marketplaceSource', existing.get('source', {}))
        location = source.get('source', source.get('path', source.get('url', ''))) if isinstance(source, dict) else source
        location = str(location)
        if location == str(package):
            return
        local = Path(location)
        owned_local = local.is_absolute() and release_base in local.parents and (local / MARKER).is_file()
        owned_git = location.removesuffix('.git') == REPOSITORY
        if not (owned_local or owned_git):
            raise ValueError('Existing marketplace uses another source; refusing to replace it: ' + location)
        # Native host removal refreshes only this owned marketplace registration;
        # do not remove installed plugin data or user instruction files.
        runner([client, 'plugin', 'marketplace', 'remove', NAME])
    runner([client, 'plugin', 'marketplace', 'add', str(package)])


def install(source, home, requested, which=shutil.which, runner=run, dry_run=False):
    source, home = Path(source).absolute(), Path(home).absolute()
    if home.is_symlink() or source.is_symlink():
        raise ValueError('Refusing symlink source or home')
    hosts, unavailable = selected_hosts(requested, home, which)
    version = json.loads((source / 'plugin.json').read_text())['version']
    if not isinstance(version, str) or not version or any(part in version for part in ('/', '\\', '..')):
        raise ValueError('Invalid package version')
    release_base = home / '.local/share' / NAME / 'releases'
    package = release_base / version
    result = {'version': version, 'package': str(package), 'installed': [], 'planned': hosts, 'unavailable': unavailable,
              'manual': ['ChatGPT installation, hook trust, persistent instruction setup'], 'scope': 'user'}
    if dry_run:
        return result
    files = package_files(source)
    # Check Cursor's destination before invoking host commands.
    cursor = home / '.cursor/plugins/local' / NAME
    cursor_files = {path: content for path, content in files.items()
                    if path in FILES or path == 'plugin.json' or path.startswith(('skills/karpathy-guidelines/', 'knowledge/', 'retrieval/'))}
    cursor_manifest = json.loads(cursor_files['plugin.json'])
    cursor_manifest.pop('hooks', None)
    cursor_manifest.pop('extensions', None)
    cursor_files['plugin.json'] = (json.dumps(cursor_manifest, indent=2) + '\n').encode()
    if 'cursor' in hosts:
        write_owned(cursor, cursor_files)
    write_owned(package, files)
    for host in hosts:
        if host in ('codex', 'claude'):
            marketplace(runner, host, package, release_base)
            identifier = CODEX_ID if host == 'codex' else CLAUDE_ID
            command = [host, 'plugin', 'add' if host == 'codex' else 'install', identifier]
            runner(command if host == 'codex' else command + ['--scope', 'user'])
            raw = json.loads(runner([host, 'plugin', 'list', '--json']).stdout)
            installed = raw.get('installed', raw.get('plugins', [])) if isinstance(raw, dict) else raw
            if not any(entry.get('pluginId', entry.get('id')) == identifier and entry.get('version') == version
                       and entry.get('enabled', True) for entry in installed):
                raise ValueError(host + ' did not report the requested plugin version as installed')
        result['installed'].append(host)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', action='append', help='all, codex, claude, cursor; repeat or use commas')
    parser.add_argument('--dry-run', action='store_true', help='Show detected targets without writing or invoking clients')
    args = parser.parse_args(argv)
    try:
        print(json.dumps(install(Path(__file__).resolve().parents[1], Path.home(), args.host or ['all'], dry_run=args.dry_run), indent=2))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        detail = error.stderr if isinstance(error, subprocess.CalledProcessError) else None
        print(json.dumps({'error': str(error), 'detail': detail, 'note': 'Installation stopped; already completed host steps may remain.'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
