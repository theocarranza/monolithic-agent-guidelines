"""Read real documents and temporary catalogs through the public retrieval API."""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class QueryTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((ROOT / 'retrieval/catalog.py').exists(), 'retrieval is not implemented')
        from retrieval.catalog import Catalog
        self.Catalog = Catalog
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'manifest.json').write_text(json.dumps({'schema_version': 1, 'version': 'test'}))
        self.fields = ['id', 'language', 'topic', 'title', 'path', 'provenance', 'read_when', 'required']
        self.document = '# Document\n\n## Parent\nparent\n### Child\nchild\n```md\n## Fake\n```\n## Other\nother\n'
        self.write_catalog()

    def write_catalog(self, **changes):
        path = self.root / 'nested/deep/doc.md'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.document)
        row = dict(zip(self.fields, ['dart/task', 'dart', 'task', 'Deferred Task', 'nested/deep/doc.md', 'adapted', 'async effects', 'false']))
        row.update(changes)
        with (self.root / 'catalog.tsv').open('w') as stream:
            writer = csv.DictWriter(stream, self.fields, delimiter='\t')
            writer.writeheader(); writer.writerow(row)

    def test_fetch_envelope_keeps_metadata_for_sections(self):
        result = self.Catalog(self.root).fetch('dart/task#parent')
        self.assertEqual(result['version'], 'test')
        self.assertEqual(result['id'], 'dart/task')
        self.assertEqual(result['provenance'], 'adapted')
        self.assertIn('### Child', result['content'])
        self.assertIn('## Fake', result['content'])
        self.assertNotIn('## Other', result['content'])
        self.assertEqual(result['sha256'], hashlib.sha256(self.document.encode()).hexdigest())
        self.assertEqual(result['content_sha256'], hashlib.sha256(result['content'].encode()).hexdigest())

    def test_fetch_child_and_whole_document(self):
        store = self.Catalog(self.root)
        self.assertEqual(store.fetch('dart/task')['content'], self.document)
        self.assertTrue(store.fetch('dart/task#child')['content'].startswith('### Child'))
        for key in ['missing', 'dart/task#missing', 'dart/task#fake']:
            with self.subTest(key=key), self.assertRaises(ValueError): store.fetch(key)

    def test_ambiguous_sections_are_rejected(self):
        self.document = '## Same\na\n## Same\nb\n'
        self.write_catalog()
        with self.assertRaises(ValueError): self.Catalog(self.root).fetch('dart/task#same')

    def test_find_is_deterministic_filtered_and_bounded(self):
        store = self.Catalog(self.root)
        self.assertEqual(store.find(['deferred'], 'dart')[0]['id'], 'dart/task')
        self.assertEqual(store.find(['deferred'], 'typescript'), [])
        self.assertEqual(store.find(['no-such-word']), [])
        self.assertLessEqual(len(store.find(['parent'])[0]['snippet']), 240)
        self.assertEqual(store.select('dart')[0]['read_when'], 'async effects')

    def test_catalog_rejects_escapes_and_symlinks(self):
        outside = self.root.parent / (self.root.name + '-outside.md')
        # Outside content need not exist: traversal is rejected before reading.
        for path in ['../' + outside.name, str(outside)]:
            self.write_catalog(path=path)
            with self.subTest(path=path), self.assertRaises(ValueError): self.Catalog(self.root)
        link = self.root / 'escape.md'
        link.symlink_to('/etc/passwd')
        self.write_catalog(path='escape.md')
        with self.assertRaises(ValueError): self.Catalog(self.root)

    def test_malformed_duplicate_and_missing_catalog_data(self):
        for field, value in [('required', 'perhaps'), ('id', ''), ('language', 'rust'), ('provenance', '')]:
            self.write_catalog(**{field: value})
            with self.subTest(field=field), self.assertRaises(ValueError): self.Catalog(self.root)
        self.write_catalog()
        catalog = self.root / 'catalog.tsv'
        catalog.write_text(catalog.read_text() + catalog.read_text().splitlines()[1] + '\n')
        with self.assertRaises(ValueError): self.Catalog(self.root)
        catalog.write_text('wrong\theader\n')
        with self.assertRaises(ValueError): self.Catalog(self.root)

    def test_real_store_has_required_language_guidance(self):
        store = self.Catalog(ROOT / 'knowledge')
        for language in ['dart', 'typescript']:
            rows = store.select(language)
            self.assertIn(language + '/guidelines', [r['id'] for r in rows])
        skill = (ROOT / 'skills/karpathy-guidelines/SKILL.md').read_text()
        core = store.fetch('core/principles')['content']
        self.assertEqual(core.strip(), skill[skill.index('## 1. Think Before Coding'):].split('\n<!-- reference-routing -->')[0].strip())
        for row in store.rows:
            self.assertTrue(store.fetch(row['id'])['content'].strip())

    def test_manifest_shapes_missing_files_and_fenced_pseudo_closers(self):
        manifest = self.root / 'manifest.json'
        for value in [[], None, {'schema_version': 2, 'version': 'test'}]:
            manifest.write_text(json.dumps(value))
            with self.subTest(value=value), self.assertRaises(ValueError): self.Catalog(self.root)
        manifest.write_text(json.dumps({'schema_version': 1, 'version': 'test'}))
        self.write_catalog(path='missing.md')
        with self.assertRaises(ValueError): self.Catalog(self.root)
        self.document = '## Real\n```md\n```not-a-close\n## Hidden\n```\nnot a heading\n## Last\nend\n'
        self.write_catalog()
        result = self.Catalog(self.root).fetch('dart/task#real')['content']
        self.assertIn('not a heading', result)
        with self.assertRaises(ValueError): self.Catalog(self.root).fetch('dart/task#hidden')

    def test_cli_success_no_match_and_error(self):
        def query(*args):
            return subprocess.run([sys.executable, str(ROOT / 'retrieval/query.py'), '--root', str(self.root), *args], text=True, capture_output=True)
        self.assertEqual(json.loads(query('catalog', '--language', 'dart').stdout)[0]['id'], 'dart/task')
        self.assertIn('content', json.loads(query('fetch', 'dart/task#parent').stdout))
        result = query('find', 'absent')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout), [])
        self.assertEqual(query('fetch', 'missing').returncode, 2)
        self.assertEqual(query('rebuild-catalog').returncode, 2)


if __name__ == '__main__': unittest.main()
