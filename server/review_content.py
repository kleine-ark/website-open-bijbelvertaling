"""Canonical review payloads shared by catalog generation and corrections."""
import hashlib
import json


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def text_review_payload(chapter):
    intro = chapter.get('chapterIntro') or {}
    if not isinstance(intro, dict) or not isinstance(chapter.get('verses'), list):
        raise ValueError('Invalid chapter structure')
    verses = []
    for verse in chapter['verses']:
        notes = verse.get('marginNotes') or []
        if not isinstance(notes, list):
            raise ValueError('Invalid margin notes')
        verses.append({
            'number': verse.get('number'), 'text2026': verse.get('text2026'),
            'text2026_html': verse.get('text2026_html'),
            'marginNotes': [{key: note.get(key) for key in ('marker', 'type', 'text2026')} for note in notes],
        })
    return {'number': chapter.get('number'), 'chapterIntro': {'text2026': intro.get('text2026')},
            'verses': verses}


def text_revision(chapter):
    return canonical_hash(text_review_payload(chapter))


def location_review_payload(feature):
    properties = dict(feature['properties'])
    properties.pop('humanReviewed', None)
    properties.pop('koppelingStatus', None)
    if 'refs' in properties:
        properties['refs'] = [{key: value for key, value in ref.items() if key != 'status'}
                              for ref in properties['refs']]
    return {'geometry': feature.get('geometry'), 'properties': properties}


def subject_payload(kind, identifier, document):
    if kind == 'text-chapter':
        return text_review_payload(document)
    if kind == 'text-verse':
        number = int(identifier.rsplit('/', 1)[1])
        matches = [v for v in text_review_payload(document)['verses'] if v['number'] == number]
    elif kind == 'location':
        matches = [location_review_payload(f) for f in document['features']
                   if f['properties']['id'] == identifier]
    else:
        raise ValueError('No correction adapter for subject type: ' + kind)
    if len(matches) != 1:
        raise ValueError('Subject must exist exactly once')
    return matches[0]
