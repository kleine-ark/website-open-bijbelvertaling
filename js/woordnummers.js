/* Open Vertaling — gedeelde, bronvaste woordnummerweergave. */
(function (global) {
    'use strict';

    const FAMILIES = {
        H:   { lang: 'he',  direction: 'rtl', tokenClass: 'strongs-token-hebrew', label: 'Strong Hebreeuws' },
        G:   { lang: 'grc', direction: 'ltr', tokenClass: 'strongs-token-greek',  label: 'Strong Grieks' },
        OVL: { lang: 'la',  direction: 'ltr', tokenClass: 'strongs-token-latin',  label: 'Open Vertaling Latijn' },
        OVG: { lang: 'gez', direction: 'ltr', tokenClass: 'strongs-token-geez',   label: 'Ge’ez-woordnummer' },
    };

    function escapeHtml(value) {
        return String(value == null ? '' : value)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    function familyOf(number) {
        if (/^OVL\d+$/.test(number)) return 'OVL';
        if (/^OVG\d+$/.test(number)) return 'OVG';
        if (/^H\d+[A-Za-z]?$/.test(number)) return 'H';
        if (/^G\d+[A-Za-z]?$/.test(number)) return 'G';
        return null;
    }

    function parse(value) {
        const matches = String(value || '').match(/(?:OVL|OVG)\d+|[HG]\d+[A-Za-z]?/g) || [];
        return [...new Set(matches)].filter(number => familyOf(number));
    }

    function parseSequence(value) {
        const matches = String(value || '').match(/(?:OVL|OVG)\d+|[HG]\d+[A-Za-z]?/g) || [];
        return matches.filter(number => familyOf(number));
    }

    function visibleNumber(number) {
        return String(number || '').replace(/^(?:OVL|OVG|[HG])/, '');
    }

    function renderAlignment(groundText) {
        if (!Array.isArray(groundText)) return '';
        let firstFamily = null;
        const tokens = groundText.map(word => {
            if (!word || typeof word !== 'object') return '';
            const numbers = parse(word.strongs);
            if (!numbers.length) return '';
            const family = familyOf(numbers[0]);
            const descriptor = FAMILIES[family];
            if (!firstFamily) firstFamily = family;
            const sourceWord = escapeHtml(word.woord || '');
            const transliteration = escapeHtml(word.transliteratie || word.translit || word.lemma || '');
            const gloss = escapeHtml(word.gloss || word.betekenis || '');
            const links = numbers.map(number => {
                const safeNumber = escapeHtml(number);
                const label = `Open woordenboekbetekenis van ${number}${word.woord ? ` bij ${word.woord}` : ''}`;
                return `<button type="button" class="strongs-inline" data-strongs="${safeNumber}" data-source-word="${sourceWord}" data-transliteratie="${transliteration}" data-gloss="${gloss}" aria-label="${escapeHtml(label)}">&lt;${safeNumber}&gt;</button>`;
            }).join('');
            return `<span class="strongs-token ${descriptor.tokenClass}"><span class="strongs-source-word" lang="${descriptor.lang}">${sourceWord}</span>${links}</span>`;
        }).filter(Boolean).join(' ');
        if (!tokens) return '';
        const descriptor = FAMILIES[firstFamily] || FAMILIES.G;
        const directionClass = descriptor.direction === 'ltr' ? ' strongs-alignment-ltr' : ' strongs-alignment-rtl';
        return `<span class="strongs-alignment${directionClass}" aria-label="Woordnummers bij de grondtekst">${tokens}</span>`;
    }

    function escapeRegExp(value) {
        return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    function inlineButtons(mapping) {
        const numbers = Array.isArray(mapping.strongs)
            ? mapping.strongs.flatMap(parseSequence)
            : parse(mapping.strongs);
        const sourceWords = mapping.bronwoorden || [];
        const transliterations = mapping.transliteraties || [];
        const glosses = mapping.glossen || [];
        const tvmCodes = mapping.tvm || [];
        const alignmentStatus = mapping.status
            ? ` data-alignment-status="${escapeHtml(mapping.status)}"`
            : '';
        return numbers.map((number, index) => {
            const safeNumber = escapeHtml(number);
            const sourceWord = escapeHtml(sourceWords[index] || sourceWords[0] || '');
            const transliteration = escapeHtml(transliterations[index] || transliterations[0] || '');
            const gloss = escapeHtml(glosses[index] || glosses[0] || '');
            const visible = escapeHtml(visibleNumber(number));
            const tvm = parseSequence(tvmCodes[index] || '')[0] || '';
            const safeTvm = escapeHtml(tvm);
            const visibleTvm = tvm ? `(${escapeHtml(visibleNumber(tvm))})` : '';
            const tvmAttribute = tvm ? ` data-tvm="${safeTvm}"` : '';
            return `<button type="button" class="strongs-inline" data-strongs="${safeNumber}"${tvmAttribute} data-source-word="${sourceWord}" data-transliteratie="${transliteration}" data-gloss="${gloss}"${alignmentStatus} aria-label="Open woordenboekbetekenis van ${safeNumber}${tvm ? `, tijdcode ${safeTvm}` : ''}">&lt;${visible}&gt;${visibleTvm}</button>`;
        }).join('');
    }

    function renderInline(html, mappings) {
        if (!Array.isArray(mappings) || !mappings.length || typeof document === 'undefined') {
            return String(html || '');
        }
        const template = document.createElement('template');
        template.innerHTML = String(html || '');

        // Plaats eerst de langste Nederlandse woordgroep. Zo kan een korter
        // anker (bijvoorbeeld "en ziende") de tekstknoop van een langere
        // gecontroleerde koppeling ("ziende hen volgen") niet voortijdig
        // opsplitsen.
        [...mappings].sort((left, right) => {
            const leftTarget = String(left?.tekst || left?.anker || '');
            const rightTarget = String(right?.tekst || right?.anker || '');
            return rightTarget.length - leftTarget.length;
        }).forEach(mapping => {
            if (!mapping || (mapping.reviewstatus && !['handmatig_gecontroleerd', 'automatisch_hoog_vertrouwen'].includes(mapping.reviewstatus))) return;
            const target = String(mapping.tekst || mapping.anker || '');
            const occurrence = Math.max(1, Number(mapping.voorkomen) || 1);
            const buttons = inlineButtons(mapping);
            if (!target || !buttons) return;

            const matcher = new RegExp(`(^|[^\\p{L}\\p{N}])(${escapeRegExp(target)})(?=$|[^\\p{L}\\p{N}])`, 'giu');
            const walker = document.createTreeWalker(template.content, NodeFilter.SHOW_TEXT, {
                acceptNode(node) {
                    const parent = node.parentElement;
                    return (!parent || !parent.closest('button, sup, script, style'))
                        ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
                }
            });
            const nodes = [];
            let flattened = '';
            let current;
            while ((current = walker.nextNode())) {
                const start = flattened.length;
                flattened += current.data;
                nodes.push({ node: current, start, end: flattened.length });
            }
            let seen = 0;
            matcher.lastIndex = 0;
            let match;
            while ((match = matcher.exec(flattened))) {
                seen += 1;
                if (seen !== occurrence) continue;
                const absoluteStart = match.index + match[1].length;
                const absoluteEnd = absoluteStart + match[2].length;
                const before = !mapping.tekst && mapping.plaats === 'voor';
                const absolutePosition = before ? absoluteStart : absoluteEnd;
                const boundary = nodes.find((entry, index) => (
                    absolutePosition < entry.end
                    || (absolutePosition === entry.end && (before || index === nodes.length - 1))
                ));
                if (!boundary) return;
                const offset = Math.max(0, Math.min(boundary.node.length, absolutePosition - boundary.start));
                const tail = boundary.node.splitText(offset);
                const holder = document.createElement('template');
                holder.innerHTML = buttons;
                tail.parentNode.insertBefore(holder.content, tail);
                return;
            }
        });
        return template.innerHTML;
    }

    const mappingCache = {};

    async function loadBookMappings(bookId, base) {
        const prefix = String(base || '').replace(/\/$/, '');
        const key = `${prefix}:${bookId}`;
        if (!mappingCache[key]) {
            mappingCache[key] = fetch(`${prefix}/data/woordnummers-inline/${bookId}.json`)
                .then(response => response.ok ? response.json() : null)
                .catch(() => null);
        }
        return mappingCache[key];
    }

    function mergeChapterMappings(chapter, mappingBook, chapterNumber) {
        if (!chapter || !mappingBook || !mappingBook.chapters) return chapter;
        const external = mappingBook.chapters[String(chapterNumber)] || {};
        for (const verse of chapter.verses || []) {
            const generated = external[String(verse.number)] || [];
            if (!generated.length) continue;
            const merged = new Map();
            [...generated, ...(verse.woordnummers || [])].forEach(mapping => {
                const strongs = Array.isArray(mapping.strongs)
                    ? mapping.strongs.join('|')
                    : String(mapping.strongs || '');
                const key = `${String(mapping.tekst || '').toLocaleLowerCase('nl')}#${String(mapping.anker || '').toLocaleLowerCase('nl')}#${mapping.voorkomen || 1}#${strongs}`;
                merged.set(key, mapping);
            });
            verse.woordnummers = [...merged.values()];
        }
        return chapter;
    }

    global.OVWoordnummers = {
        FAMILIES, escapeHtml, familyOf, parse, renderAlignment, renderInline,
        loadBookMappings, mergeChapterMappings
    };
})(typeof window !== 'undefined' ? window : this);
