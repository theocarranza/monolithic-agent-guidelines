"""Shared routing and conservative tool classification; no host-specific JSON."""
import hashlib
import json
from pathlib import Path
import re
import shlex

READ_TOOLS = {'Read', 'Glob', 'Grep', 'read_file', 'list_dir', 'search_query', 'view_image'}
SHELL_TOOLS = {'Bash', 'exec_command', 'shell', 'shell_command'}


def requirements(event, catalog):
    text = json.dumps(event.get('tool_input', {}), ensure_ascii=False) + ' ' + event.get('prompt', '')
    cwd = Path(event['cwd'])
    languages = set()
    if re.search(r'\bdart\b|\.dart\b', text, re.I) or (cwd / 'pubspec.yaml').is_file():
        languages.add('dart')
    if re.search(r'\btypescript\b|\.tsx?\b|\btsx?\b', text, re.I) or (cwd / 'package.json').is_file():
        languages.add('typescript')
    topic_ids = set()
    for pattern, identifier, language in [
        (r'\b(adapters?|data[ -]sources?|database|json|local[ -]storage|entry[ -]?points?|test[ -]dependencies|canonical[ -](flow|implementation)|workflows?)\b', 'shared/canonical-behavior', 'all'),
        (r'\b(task|async|concurrency)\b', 'dart/task', 'dart'),
        (r'\b(option|nullable|absence)\b', 'dart/option', 'dart'),
        (r'\b(either|failure|error)\b', 'dart/either', 'dart'),
        (r'\b(effect|clock|random|fake)\b', 'typescript/effects', 'typescript'),
        (r'\b(monoid|aggregation|aggregate)\b', 'typescript/monoids', 'typescript'),
    ]:
        if (language == 'all' or language in languages) and re.search(pattern, text, re.I):
            topic_ids.add(identifier)
    return [catalog.fetch(row['id']) for row in catalog.rows
            if (row['required'] == 'true' and (row['language'] == 'all' or row['language'] in languages))
            or row['id'] in topic_ids]


def fingerprint(documents):
    values = sorted((doc['id'], doc['version'], doc['sha256']) for doc in documents)
    return hashlib.sha256(json.dumps(values).encode()).hexdigest()


def internal_command(tool_input, root):
    """Only direct bundled read commands; never shell expressions."""
    command = tool_input.get('command', tool_input.get('cmd', '')) if isinstance(tool_input, dict) else ''
    if not isinstance(command, str) or re.search(r'[$`;&|><\n\r]', command):
        return False
    try:
        words = shlex.split(command)
    except ValueError:
        return False
    if len(words) < 3 or words[0] not in ('python', 'python3'):
        return False
    script = Path(words[1])
    if not script.is_absolute():
        return False
    return script == root / 'retrieval/query.py' and words[2] in ('catalog', 'find', 'fetch')


def guarded(event, root):
    name = event.get('tool_name', '')
    return name not in READ_TOOLS and not (name in SHELL_TOOLS and internal_command(event.get('tool_input'), root))


def potential_change(event, root):
    return guarded(event, root)
