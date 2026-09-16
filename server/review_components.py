"""Independent review fingerprints. Keep extraction identical to review-components.js."""
import re
from review_content import canonical_hash

LABELS = {'text': 'de Bijbeltekst', 'notes': 'de kanttekeningen',
          'markers': 'de nootnummers', 'citations': 'de citaatopmaak',
          'layout': 'de overige tekstopmaak', 'intro': 'de hoofdstukinleiding',
          'content': 'de inhoud'}
MARKER = re.compile(r'<sup\b[^>]*\bclass="note-marker"[^>]*>.*?</sup>', re.S)
TAG = re.compile(r'<[^>]*>')
CITATION = re.compile(r'\bclass="(?:direct-speech|[a-z]+-speaks)"')


def normalized(text):
    return re.sub(r'\s+', ' ', text or '').strip()


def position(html):
    # UTF-16 code units, also used by the browser (including supplementary characters).
    return len(normalized(TAG.sub('', html)).encode('utf-16-le')) // 2


def verse_components(verse):
    html = verse.get('text2026_html') or verse.get('text2026') or ''
    markers = [[position(MARKER.sub('', html[:match.start()])), match.group()]
               for match in MARKER.finditer(html)]
    html = MARKER.sub('', html)
    citations, layout, stack = [], [], []
    for match in TAG.finditer(html):
        tag = match.group()
        if tag.startswith('</'):
            citation = stack.pop() if stack else False
        else:
            citation = bool(CITATION.search(tag)) or (tag == '<i>' and any(stack))
            if not tag.endswith('/>'):
                stack.append(citation)
        (citations if citation else layout).append([position(html[:match.start()]), tag])
    return {
        'text': [normalized(verse.get('text2026')), normalized(TAG.sub('', html))],
        'notes': [{key: note.get(key) for key in ('marker', 'type', 'text2026')}
                  for note in (verse.get('marginNotes') or [])],
        'markers': markers, 'citations': citations, 'layout': layout,
    }


def component_payloads(kind, payload):
    if kind == 'text-verse':
        return verse_components(payload)
    if kind != 'text-chapter':
        return {'content': payload}
    verses = [(v['number'], verse_components(v)) for v in payload['verses']]
    result = {key: [[number, components[key]] for number, components in verses]
              for key in ('text', 'notes', 'markers', 'citations', 'layout')}
    result['intro'] = (payload.get('chapterIntro') or {}).get('text2026') or ''
    return result


def component_metadata(kind, payload):
    components = component_payloads(kind, payload)
    result = {key: {'revision': canonical_hash(value), 'present': (
        any(bool(item[1]) for item in value) if kind == 'text-chapter' and key != 'intro'
        else bool(value))} for key, value in components.items()}
    if kind == 'text-chapter':
        for key in result:
            if key != 'intro':
                result[key]['members'] = {str(number): canonical_hash(value) for number, value in components[key]}
    return result
