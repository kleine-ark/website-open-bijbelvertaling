/* Open Vertaling — gedeelde, bronvaste woordnummerweergave. */
(function (global) {
    'use strict';

    const FAMILIES = {
        H:   { lang: 'he',  direction: 'rtl', tokenClass: 'strongs-token-hebrew', label: 'Strong Hebreeuws' },
        G:   { lang: 'grc', direction: 'ltr', tokenClass: 'strongs-token-greek',  label: 'Strong Grieks' },
        OVL: { lang: 'la',  direction: 'ltr', tokenClass: 'strongs-token-latin',  label: 'Open Vertaling Latijn' },
        OVG: { lang: 'gez', direction: 'ltr', tokenClass: 'strongs-token-geez',   label: 'Open Vertaling Ge’ez' },
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

    global.OVWoordnummers = { FAMILIES, escapeHtml, familyOf, parse, renderAlignment };
})(typeof window !== 'undefined' ? window : this);
