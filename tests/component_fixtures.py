"""Synthetic fingerprints for store tests which deliberately do not load corpus data."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
from review_content import canonical_hash


def fingerprint_catalog(catalog):
    catalog['schemaVersion'] = 3
    catalog['componentHistory'] = []
    for item in catalog['subjects'] + catalog['historicalSubjects']:
        keys = (['text', 'notes', 'markers', 'citations', 'layout', 'intro'] if item['type'] == 'text-chapter'
                else ['text', 'notes', 'markers', 'citations', 'layout'] if item['type'] == 'text-verse'
                else ['content'])
        item['metadata'] = dict(item.get('metadata', {}))
        item['metadata']['components'] = {
            key: {'revision': item['revision'], 'present': True} for key in keys}
        if item['type'] == 'text-chapter':
            for key in keys:
                if key != 'intro':
                    item['metadata']['components'][key]['members'] = {
                        child['id'].rsplit('/', 1)[1]: child['revision'] for child in catalog['subjects']
                        if child['type'] == 'text-verse' and child['id'].startswith(item['id'] + '/')}
    data = dict(catalog)
    data.pop('catalogRevision', None)
    return canonical_hash(data)
