"""Validated catalog and deterministic, read-only local retrieval."""
import csv
import hashlib
import json
from pathlib import Path

from retrieval.sections import section

FIELDS = ['id', 'language', 'topic', 'title', 'path', 'provenance', 'read_when', 'required']


class Catalog:
    def __init__(self, root):
        self.root = Path(root).resolve()
        manifest = json.loads((self.root / 'manifest.json').read_text(encoding='utf-8'))
        if not isinstance(manifest, dict) or manifest.get('schema_version') != 1 or not isinstance(manifest.get('version'), str):
            raise ValueError('Unsupported knowledge manifest')
        self.version = manifest['version']
        with (self.root / 'catalog.tsv').open(encoding='utf-8', newline='') as stream:
            reader = csv.DictReader(stream, delimiter='\t')
            if reader.fieldnames != FIELDS:
                raise ValueError('Invalid catalog columns')
            self.rows = list(reader)
        seen = set()
        for row in self.rows:
            if set(row) != set(FIELDS) or not all(isinstance(v, str) and v.strip() for v in row.values()):
                raise ValueError('Incomplete catalog row')
            if row['id'] in seen or row['required'] not in ('true', 'false') or row['language'] not in ('all', 'dart', 'typescript'):
                raise ValueError('Invalid or duplicate catalog row: ' + row['id'])
            seen.add(row['id'])
            self.path(row)

    def path(self, row):
        relative = Path(row['path'])
        target = (self.root / relative).resolve()
        if relative.is_absolute() or '..' in relative.parts or self.root not in target.parents:
            raise ValueError('Catalog path escapes knowledge root')
        if not target.is_file():
            raise ValueError('Missing knowledge file: ' + row['path'])
        return target

    def select(self, language=None):
        return [dict(row) for row in self.rows if language is None or row['language'] in ('all', language)]

    def fetch(self, reference):
        identifier, separator, name = reference.partition('#')
        row = next((r for r in self.rows if r['id'] == identifier), None)
        if row is None:
            raise ValueError('Unknown reference: ' + identifier)
        data = self.path(row).read_bytes()
        text = data.decode('utf-8')
        content = section(text, name) if separator else text
        return {**row, 'version': self.version, 'sha256': hashlib.sha256(data).hexdigest(),
                'section': name if separator else None,
                'content_sha256': hashlib.sha256(content.encode()).hexdigest(), 'content': content}

    def find(self, terms, language=None):
        terms = sorted(set(t.lower() for t in terms if t.strip()))
        hits = []
        for row in self.select(language):
            text = self.fetch(row['id'])['content']
            haystack = (' '.join(row.values()) + '\n' + text).lower()
            matched = [term for term in terms if term in haystack]
            if not matched:
                continue
            score = len(matched) + 2 * sum(term in row['title'].lower() for term in matched)
            positions = [text.lower().find(term) for term in matched if term in text.lower()]
            start = max(0, min(positions, default=0) - 40)
            hits.append({'id': row['id'], 'path': row['path'], 'matched_terms': matched,
                         'score': score, 'snippet': text[start:start + 240]})
        return sorted(hits, key=lambda h: (-h['score'], h['id']))[:12]
