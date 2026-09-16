"""Data-only proposal artifacts; no shell patches or AI code are executed."""
import json
import os
import tempfile
from pathlib import Path, PurePosixPath

MAX_ARTIFACT_BYTES = 16 * 1024 * 1024
FORBIDDEN = {'data/review-catalog.json', 'data/verified-chapters.json',
             'data/opmerkingen-bron.json', 'data/feedback-log.json'}


def data_path(root, name):
    if not isinstance(name, str):
        raise ValueError('Invalid data path')
    path = PurePosixPath(name)
    if (not name.startswith('data/') or path.suffix not in ('.json', '.geojson')
            or any(part.startswith('.') for part in path.parts) or str(path) != name
            or name in FORBIDDEN):
        raise ValueError('Only existing public data files may be changed: ' + name)
    root = Path(root).resolve(strict=True)
    target = root / name
    if target.resolve(strict=True) != target or not target.is_file():
        raise ValueError('Symlinks and missing files cannot be changed')
    return target


def validate_files(root, files, expected='before'):
    if not isinstance(files, list) or not files or len(files) > 100:
        raise ValueError('Expected 1–100 changed files')
    if len(json.dumps(files, ensure_ascii=False).encode()) > MAX_ARTIFACT_BYTES:
        raise ValueError('Proposal is too large')
    seen = set()
    for item in files:
        if not isinstance(item, dict) or set(item) != {'path', 'before', 'after'}:
            raise ValueError('Invalid file record')
        target = data_path(root, item['path'])
        if item['path'] in seen:
            raise ValueError('Duplicate path')
        seen.add(item['path'])
        for key in ('before', 'after'):
            if not isinstance(item[key], str):
                raise ValueError('Expected UTF-8 file contents')
            json.loads(item[key], parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))
        if item['before'] == item['after']:
            raise ValueError('Unchanged file in proposal')
        if expected and target.read_bytes() != item[expected].encode('utf-8'):
            raise ValueError('File differs from reviewed version: ' + item['path'])
    return files


def replace_file(path, content):
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix='.correction-')
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(content.encode('utf-8'))
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def apply_bundle(root, bundle):
    if bundle.get('schemaVersion') != 1 or not isinstance(bundle.get('items'), list):
        raise ValueError('Unsupported correction bundle')
    files = []
    for task in bundle['items']:
        if task['status'] != 'accepted' or task['stale']:
            raise ValueError('Only accepted, current proposals can be applied')
        files.extend(task['proposal']['files'])
    if not files:
        return []
    # Check the complete batch first. Overlapping files need separate publication.
    validate_files(root, files)
    changed = []
    try:
        for item in files:
            path = data_path(root, item['path'])
            replace_file(path, item['after'])
            changed.append(item)
    except BaseException:
        for item in reversed(changed):
            replace_file(data_path(root, item['path']), item['before'])
        raise
    return [item['path'] for item in changed]
