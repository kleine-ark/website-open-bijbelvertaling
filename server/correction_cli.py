#!/usr/bin/env python3
"""Explicit operator bridge: export → prepare → propose → human acceptance → apply.

Server commands use the existing private database through SSH. Local commands
operate on a worktree. This tool never calls an AI provider or publishes a site.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from correction_files import MAX_ARTIFACT_BYTES, apply_bundle, validate_files


def read_artifact(name):
    if name == '-':
        raw = sys.stdin.buffer.read(MAX_ARTIFACT_BYTES + 1)
    else:
        with Path(name).open('rb') as stream:
            raw = stream.read(MAX_ARTIFACT_BYTES + 1)
    if len(raw) > MAX_ARTIFACT_BYTES:
        raise ValueError('Artifact exceeds 16 MiB')
    return json.loads(raw)


def prepare(root, bundle, identifier, summary, base):
    if bundle.get('schemaVersion') != 1:
        raise ValueError('Unsupported task export')
    tasks = [task for task in bundle['items'] if task['id'] == identifier]
    if len(tasks) != 1 or tasks[0]['status'] != 'requested' or tasks[0]['stale']:
        raise ValueError('Expected one current requested task')
    root = Path(root).resolve(strict=True)

    def git(*arguments):
        return subprocess.check_output(['git', '-C', str(root), *arguments])

    revision = git('rev-parse', '--verify', base + '^{commit}').decode().strip()
    if git('ls-files', '--others', '--exclude-standard', '-z'):
        raise ValueError('Untracked files must not be silently left out of a proposal')
    names = git('diff', '--name-only', '-z', revision).decode().split('\0')
    files = [{'path': name, 'before': git('show', revision + ':' + name).decode('utf-8'),
              'after': (root / name).read_bytes().decode('utf-8')} for name in names if name]
    validate_files(root, files, expected='after')
    if tasks[0]['source'] not in {item['path'] for item in files}:
        raise ValueError('The subject source must be included')
    return {'id': identifier, 'version': tasks[0]['version'], 'summary': summary, 'files': files}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    export = commands.add_parser('export', help='Private operator: export tasks without identities')
    export.add_argument('--status', default='requested', choices=['requested', 'proposed', 'accepted', 'applied', 'closed'])
    export.add_argument('--id', default='')
    proposal = commands.add_parser('propose', help='Private operator: record a proposal, without applying it')
    proposal.add_argument('--input', default='-')
    build = commands.add_parser('prepare', help='Local: bundle existing changed data files from a worktree')
    build.add_argument('--input', required=True, help='Exported task bundle')
    build.add_argument('--id', required=True)
    build.add_argument('--summary', required=True)
    build.add_argument('--root', type=Path, required=True)
    build.add_argument('--base', default='HEAD')
    apply = commands.add_parser('apply', help='Local: apply an accepted bundle; do not publish or verify')
    apply.add_argument('--input', required=True)
    apply.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        result = prepare(args.root, read_artifact(args.input), args.id, args.summary, args.base)
    elif args.command == 'apply':
        result = {'changed': apply_bundle(args.root, read_artifact(args.input))}
    else:
        # Load the exact same configuration/migration/catalog code as the API.
        from collaboration_api import configured_app
        app = configured_app()
        service = app['corrections']
        service.reconcile()
        if args.command == 'export':
            result = service.export(args.status, args.id)
        else:
            result = service.propose(read_artifact(args.input))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    # Exported requests and reasons belong in private files, not the webroot.
    os.umask(0o077)
    main()
