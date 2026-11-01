#!/usr/bin/env python3
"""Read-only catalog → find → fetch. No network or session-state writes."""
import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from retrieval.catalog import Catalog


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1] / 'knowledge')
    commands = parser.add_subparsers(dest='command', required=True)
    catalog = commands.add_parser('catalog')
    find = commands.add_parser('find')
    fetch = commands.add_parser('fetch')
    for command in (catalog, find):
        command.add_argument('--language', choices=['dart', 'typescript'])
    find.add_argument('terms', nargs='+')
    fetch.add_argument('reference')
    args = parser.parse_args(argv)
    try:
        store = Catalog(args.root)
        if args.command == 'fetch':
            result = store.fetch(args.reference)
        elif args.command == 'find':
            result = store.find(args.terms, args.language)
        else:
            result = store.select(args.language)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if args.command == 'find' and not result else 0
    except (OSError, ValueError) as error:
        print(json.dumps({'error': str(error)}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
