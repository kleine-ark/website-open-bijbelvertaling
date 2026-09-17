/* Content fingerprints shared with server/review_components.py. No account data. */
(function (global) {
    'use strict';
    const labels = { text: 'de Bijbeltekst', notes: 'de kanttekeningen', markers: 'de nootnummers',
        citations: 'de citaatopmaak', layout: 'de overige tekstopmaak', intro: 'de hoofdstukinleiding', content: 'de inhoud' };
    const markerPattern = /<sup\b[^>]*\bclass="note-marker"[^>]*>.*?<\/sup>/gs;
    const tagPattern = /<[^>]*>/g;
    const normalized = text => (text || '').replace(/\s+/g, ' ').trim();
    const position = html => normalized(html.replace(tagPattern, '')).length;

    function verseComponents(verse) {
        let html = verse.text2026_html || verse.text2026 || '';
        const markers = [...html.matchAll(markerPattern)].map(match =>
            [position(html.slice(0, match.index).replace(markerPattern, '')), match[0]]);
        html = html.replace(markerPattern, '');
        const citations = [], layout = [], stack = [];
        for (const match of html.matchAll(tagPattern)) {
            const tag = match[0];
            let citation;
            if (tag.startsWith('</')) citation = stack.length ? stack.pop() : false;
            else {
                citation = /\bclass="(?:direct-speech|[a-z]+-speaks)"/.test(tag) || (tag === '<i>' && stack.some(Boolean));
                if (!tag.endsWith('/>')) stack.push(citation);
            }
            (citation ? citations : layout).push([position(html.slice(0, match.index)), tag]);
        }
        return { text: [normalized(verse.text2026), normalized(html.replace(tagPattern, ''))],
            notes: (verse.marginNotes || []).map(note => Object.fromEntries(
                ['marker', 'type', 'text2026'].map(key => [key, note[key] ?? null]))), markers, citations, layout };
    }

    function payloads(kind, payload) {
        if (kind === 'text-verse') return verseComponents(payload);
        if (kind !== 'text-chapter') return { content: payload };
        const verses = payload.verses.map(v => [v.number, verseComponents(v)]);
        const result = Object.fromEntries(['text', 'notes', 'markers', 'citations', 'layout'].map(key =>
            [key, verses.map(([number, components]) => [number, components[key]])]));
        result.intro = payload.chapterIntro?.text2026 || '';
        return result;
    }

    function canonical(value) {
        if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
        if (value && typeof value === 'object') return '{' + Object.keys(value).sort()
            .map(key => JSON.stringify(key) + ':' + canonical(value[key])).join(',') + '}';
        return JSON.stringify(value);
    }

    async function revisions(kind, payload) {
        return Object.fromEntries(await Promise.all(Object.entries(payloads(kind, payload)).map(async ([key, value]) => {
            const bytes = new TextEncoder().encode(canonical(value));
            const hash = await crypto.subtle.digest('SHA-256', bytes);
            return [key, [...new Uint8Array(hash)].map(n => n.toString(16).padStart(2, '0')).join('')];
        })));
    }

    function join(keys) {
        return new Intl.ListFormat('nl', { style: 'long', type: 'conjunction' }).format(keys.map(key => labels[key]));
    }

    function warning(parts) {
        const groups = { changed: [], pending: [], correction: [], stale: [], local: [] };
        for (const [key, part] of Object.entries(parts)) {
            if (part.local) groups.local.push(key);
            else if (part.stale) groups.stale.push(key);
            else if (part.status === 'correction-needed') groups.correction.push(key);
            else if (part.status !== 'approved') groups[part.needsReverification ? 'changed' : 'pending'].push(key);
        }
        const sentences = [];
        if (groups.local.length) sentences.push('lokale bewerkingen aan ' + join(groups.local) + ' zijn niet geverifieerd.');
        if (groups.changed.length) sentences.push(join(groups.changed) +
            (groups.changed.length === 1 && !['notes', 'markers'].includes(groups.changed[0]) ? ' is' : ' zijn') +
            ' gewijzigd sinds de laatste verificatie en nog niet opnieuw gecontroleerd.');
        if (groups.pending.length) sentences.push(join(groups.pending) +
            (groups.pending.length === 1 && !['notes', 'markers'].includes(groups.pending[0]) ? ' is' : ' zijn') +
            ' nog niet geverifieerd.');
        if (groups.correction.length) sentences.push('voor ' + join(groups.correction) + ' is een aanpassing aangevraagd.');
        if (groups.stale.length) sentences.push('de getoonde versie van ' + join(groups.stale) +
            ' wijkt af van de actuele versie. Herlaad om de verificatiestatus te controleren.');
        return sentences.length ? 'Let op: ' + sentences.join(' ') : '';
    }

    const correctionLabel = task => task.component === 'custom' ? task.customTarget : labels[task.component];
    global.ReviewComponents = { labels, payloads, revisions, join, warning, correctionLabel };
})(typeof window === 'undefined' ? globalThis : window);
