const { test } = require('node:test');
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const { readFileSync } = require('node:fs');
require('../js/review-components.js');

test('Python and browser component fingerprints agree for every published chapter', async () => {
    const corpus = JSON.parse(execFileSync('python3', ['-c', `
import sys,json
from pathlib import Path
sys.path.insert(0,'server')
from review_components import component_metadata
result=[]
for book in json.loads(Path('data/books.json').read_text())['books']:
    for number in book['chaptersIncluded']:
        path=Path('data')/book['id']/(str(number)+'.json')
        parts=component_metadata('text-chapter',json.loads(path.read_text()))
        result.append([str(path),{key:part['revision'] for key,part in parts.items()}])
print(json.dumps(result))
`], { encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 }));
    for (const [path, expected] of corpus) {
        const actual = await ReviewComponents.revisions('text-chapter', JSON.parse(readFileSync(path)));
        assert.deepEqual(actual, expected, path);
    }
});

test('warnings name only unapproved components without assuming AI authorship', () => {
    const changed = { status: 'pending', needsReverification: true };
    assert.equal(ReviewComponents.warning({ text: { status: 'approved' }, notes: changed, markers: changed }),
        'Let op: de kanttekeningen en de nootnummers zijn gewijzigd sinds de laatste verificatie en nog niet opnieuw gecontroleerd.');
    assert.equal(ReviewComponents.warning({ text: { status: 'approved' } }), '');
    assert.equal(ReviewComponents.warning({ intro: { status: 'pending' } }),
        'Let op: de hoofdstukinleiding is nog niet geverifieerd.');
});
