/* Review scope follows the content actually displayed, not hidden additions. */
(function () {
    'use strict';
    function visible(node) {
        return node.getClientRects().length > 0 && getComputedStyle(node).visibility !== 'hidden';
    }

    function keys(control) {
        if (control.onlyComponents) return control.onlyComponents;
        if (!control.type.startsWith('text-')) return ['content'];
        const [book, chapter, verse] = control.id.split('/');
        const selector = control.reader ? '#verses .verse-span'
            : '.verse-row[data-book="' + book + '"][data-chapter="' + chapter + '"]';
        const rows = [...document.querySelectorAll(selector + (verse ? '[data-verse="' + verse + '"]' : ''))];
        const shown = selector => rows.some(row => [...row.querySelectorAll(selector)].some(visible));
        const text = shown('.col-2026, .verse-text, .col-diff');
        const citations = shown('.col-2026 .direct-speech, .col-2026 [class$="-speaks"], .verse-text .direct-speech, .verse-text [class$="-speaks"]');
        const scope = { text, notes: shown('.col-margin2026, .col-noteDiff'),
            markers: shown('.col-2026 .note-marker, .verse-text .note-marker'),
            citations: citations && !document.body.classList.contains('citaten-uit'), layout: text,
            intro: !verse && [...document.querySelectorAll(control.reader ? '#chapter-intro'
                : '.chapter-intro-inline[data-book="' + book + '"][data-chapter="' + chapter + '"]')].some(visible) };
        return Object.keys(scope).filter(key => scope[key] && (control.state.components[key].present
            || control.revisions[key] !== control.state.components[key].revision));
    }

    function parts(control) {
        return Object.fromEntries(keys(control).map(key => [key, { ...control.state.components[key],
            stale: control.revisions ? control.revisions[key] !== control.state.components[key].revision
                : control.sourceHash !== control.state.metadata.sourceHash }]));
    }

    function banner(book, chapter, reader = false) {
        const message = Verification.warning(book, chapter);
        let node = document.getElementById('ai-concept-banner');
        if (!message) { if (node) node.hidden = true; return; }
        if (!node) {
            node = document.createElement('div');
            node.id = 'ai-concept-banner';
            node.className = 'ai-concept-banner';
            node.setAttribute('role', 'status');
            document.getElementById(reader ? 'verses' : 'verses-container').before(node);
        }
        node.textContent = message;
        node.hidden = false;
    }

    function watch(update) {
        let queued = false;
        const changed = () => {
            if (queued) return;
            queued = true;
            requestAnimationFrame(() => { queued = false; update(); });
        };
        const observer = new MutationObserver(changed);
        observer.observe(document.body, { attributes: true, attributeFilter: ['class'] });
        const content = document.getElementById('content');
        if (content) observer.observe(content, { attributes: true, attributeFilter: ['class', 'style'] });
        document.addEventListener('change', changed);
        window.addEventListener('resize', changed);
    }

    function title(node, text, verified) {
        node.textContent = text;
        node.classList.toggle('chapter-unverified', !verified);
        if (!verified) {
            const tag = document.createElement('span');
            tag.className = 'chapter-concept-tag';
            tag.textContent = 'BIJBELTEKST — NOG NIET GEVERIFIEERD';
            node.append(document.createTextNode(' '), tag);
        }
    }

    function readerTitle(app, book, chapter) {
        Verification.heading(book, chapter);
        const node = document.getElementById('chapter-title');
        const name = app._contNames?.[book] || book;
        title(node, `${name} ${chapter}`, app._isVerified(book, chapter) || !Verification.textVisible(book, chapter));
    }

    window.VerificationDisplay = { keys, parts, banner, watch, title, readerTitle };
})();
