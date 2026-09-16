#!/usr/bin/env python3
"""Freeze independently reproducible component fingerprints for pre-component reviews.

Git is used only when producing this versioned migration, never by the API.
--audit-host checks every existing remote review, without changing remote data.
"""
import argparse
import json
import sqlite3
import subprocess
import sys
import itertools
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))
from review_content import canonical_hash, subject_payload
from review_components import component_metadata


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def generate(audit_host=None, database=None):
    targets, commits = set(), set()
    for name in ('review-history-v1.json', 'review-history-v2.json'):
        history = json.loads((ROOT / 'migrations' / name).read_text())
        commits.add(history['sourceCommit'])
        targets.update((i['type'], i['id'], i['revision']) for i in history['subjects'])
    if audit_host:
        command = "python3 -c \"import sqlite3,json;db=sqlite3.connect('file:/var/lib/openvertaling-collaboration/collaboration.sqlite3?mode=ro',uri=True);print(json.dumps(db.execute('SELECT DISTINCT subject_type,subject_id,revision FROM review_events').fetchall()))\""
        targets.update(map(tuple, json.loads(subprocess.check_output([
            'ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', audit_host, command]))))
    if database:
        with sqlite3.connect('file:' + str(Path(database).resolve()) + '?mode=ro', uri=True) as db:
            targets.update(db.execute('SELECT DISTINCT subject_type,subject_id,revision FROM review_events'))
    result = []
    output = ROOT / 'migrations/review-components-v1.json'
    frozen = json.loads(output.read_text())['subjects'] if output.exists() else []
    previous = {(i['type'], i['id'], i['revision']): i['sourceCommit'] for i in frozen}
    targets.update(previous)
    sources = {}
    for kind, identifier, revision in targets:
        source = ('data/geografie-runtime.geojson' if kind == 'location'
                  else 'data/' + '/'.join(identifier.split('/')[:2]) + '.json')
        sources.setdefault(source, set()).add((kind, identifier, revision))
    for source, missing in sorted(sources.items()):
        candidates = [previous[t] for t in sorted(missing) if t in previous]
        candidates += ['HEAD', '7b4038e207824ec0b47c31052767def38cdaf4c9', *sorted(commits)]
        def older():
            yield from git('log', '--format=%H', '--all', '--', source).decode().splitlines()
        seen = set()
        for commit in itertools.chain(candidates, older()):
            if commit in seen:
                continue
            seen.add(commit)
            exists = subprocess.run(['git', 'cat-file', '-e', commit + ':' + source], cwd=ROOT,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if exists.returncode:
                continue
            document = json.loads(git('show', commit + ':' + source))
            for target in sorted(missing):
                kind, identifier, revision = target
                payload = subject_payload(kind, identifier, document)
                if canonical_hash(payload) != revision:
                    continue
                result.append({'type': kind, 'id': identifier, 'revision': revision,
                               'sourceCommit': commit if commit != 'HEAD' else git('rev-parse', 'HEAD').decode().strip(),
                               'metadata': {'components': component_metadata(kind, payload)}})
                missing.remove(target)
            if not missing:
                break
        if missing:
            raise RuntimeError('Cannot reconstruct reviewed content: ' + repr(missing))
    result.sort(key=lambda i: (i['type'], i['id'], i['revision']))
    output.write_text(json.dumps({'schemaVersion': 1, 'subjects': result}, ensure_ascii=False,
                                separators=(',', ':')) + '\n')
    print(f'{len(targets)} reviewed revisions reconstructed and covered: {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit-host')
    parser.add_argument('--database')
    args = parser.parse_args()
    generate(args.audit_host, args.database)
