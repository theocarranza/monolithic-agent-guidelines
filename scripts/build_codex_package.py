#!/usr/bin/env python3
"""Generate the legacy Codex package from the authoritative repository files."""
import argparse
from pathlib import Path
import sys

DIRECTORIES = ('.codex-plugin', 'skills', 'knowledge', 'retrieval', 'enforcement', 'hooks', '.cursor')
FILES = ('README.md', 'README.zh.md', 'CLAUDE.md', 'CURSOR.md', 'EXAMPLES.md', 'CODEX.md', 'HOOKS.md', 'CHANGELOG.md')


def build(root, check=False):
    root = Path(root)
    target = root / 'dist/codex'
    sources = [root / name for name in FILES]
    for directory in DIRECTORIES:
        if (root / directory).is_symlink():
            raise ValueError('Refusing symlink package input directory')
        sources.extend(path for path in (root / directory).rglob('*')
                       if '__pycache__' not in path.parts and path.suffix != '.pyc'
                       and (path.is_file() or path.is_symlink()))
    if any(path.is_symlink() for path in sources) or target.is_symlink():
        raise ValueError('Refusing symlink package inputs or output')
    expected = {path.relative_to(root): path.read_bytes() for path in sources}
    actual = {path.relative_to(target) for path in target.rglob('*') if path.is_file() or path.is_symlink()}
    unexpected = actual - expected.keys()
    if unexpected:
        raise ValueError('Unexpected generated files; review manually: ' + ', '.join(map(str, sorted(unexpected))))
    for relative, content in expected.items():
        destination = target / relative
        if destination.is_symlink() or any(parent.is_symlink() for parent in destination.parents):
            raise ValueError('Refusing symlink package output')
        if check:
            if not destination.is_file() or destination.read_bytes() != content:
                raise ValueError('Codex package is out of date: ' + str(relative))
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Verify committed output without writing')
    args = parser.parse_args(argv)
    try:
        build(Path(__file__).resolve().parents[1], check=args.check)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
