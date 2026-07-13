/* Open Staten Vertaling — Ge'ez-lexicon (Ethiopische boeken)
 *
 * Ge'ez (Ethiopisch/Fidäl) heeft geen Strong's-nummers, dus de gewone Strong's-
 * lexiconpopup werkt er niet voor. Deze module maakt Ge'ez-grondtekstwoorden
 * selecteerbaar: klik op een woord → popup met (a) het woord, (b) een Latijnse
 * transliteratie (deterministisch uit het Fidäl-syllabarium), en (c) opzoeklinks
 * naar online Ge'ez-woordenboeken (Dillmann/Beta maṣāḥǝft, Wiktionary).
 */
(function () {
    'use strict';

    // 34 basismedeklinkers van het Ethiopisch syllabarium, in Unicode-volgorde
    // (elk blok van 8 codepunten begint op U+1200 + n*8).
    const CONS = [
        'h', 'l', 'ḥ', 'm', 'ś', 'r', 's', 'š', 'q', 'q̈', 'b', 'v', 't', 'č', 'ḫ', 'n',
        'ñ', 'ʾ', 'k', 'ḵ', 'w', 'ʿ', 'z', 'ž', 'y', 'd', 'ǧ', 'g', 'ṭ', 'č̣', 'p̣', 'ṣ',
        'ṣ́', 'f', 'p'
    ];
    // Klinkerordes 1..7 (+ labiovelaar-varianten); order 6 (ǝ) = geen/zwakke klinker.
    const VOW = ['ä', 'u', 'i', 'a', 'e', '', 'o', 'wa'];

    function translitChar(ch) {
        const c = ch.codePointAt(0);
        // Ethiopisch hoofdblok U+1200–U+135A (syllaben)
        if (c >= 0x1200 && c <= 0x135A) {
            const idx = c - 0x1200;
            const cons = CONS[Math.floor(idx / 8)];
            const vow = VOW[idx % 8];
            if (cons === undefined) return ch;
            return cons + vow;
        }
        // Ethiopische woordscheider (፡) en leestekens → spatie/weglaten
        if (c === 0x1361) return ' ';
        if (c >= 0x1362 && c <= 0x1368) return '';
        return ch;
    }

    function transliterate(word) {
        let out = '';
        for (const ch of (word || '')) out += translitChar(ch);
        return out.replace(/\s+/g, ' ').trim();
    }

    let popupEl = null;
    function closePopup() { if (popupEl) { popupEl.remove(); popupEl = null; } }

    function showPopup(word, anchorEl) {
        closePopup();
        // Voorkeur: vooraf-berekende transliteratie uit de data (data-translit);
        // anders de client-side benadering.
        const tr = (anchorEl && anchorEl.dataset && anchorEl.dataset.translit) || transliterate(word);
        const q = encodeURIComponent(word);
        popupEl = document.createElement('div');
        popupEl.className = 'geez-lex-popup';
        popupEl.innerHTML =
            `<div class="geez-lex-word" lang="gez">${word}</div>` +
            (tr ? `<div class="geez-lex-translit">${tr}</div>` : '') +
            `<div class="geez-lex-links">` +
              `<a href="https://en.wiktionary.org/w/index.php?search=${q}" target="_blank" rel="noopener">Zoek in Wiktionary ↗</a>` +
              `<a href="https://betamasaheft.eu/Dillmann/" target="_blank" rel="noopener">Dillmann-lexicon (Beta maṣāḥǝft) ↗</a>` +
            `</div>`;
        document.body.appendChild(popupEl);
        // Positioneer onder het woord
        const r = anchorEl.getBoundingClientRect();
        const top = r.bottom + window.scrollY + 6;
        let left = r.left + window.scrollX;
        popupEl.style.top = top + 'px';
        popupEl.style.left = Math.min(left, window.scrollX + window.innerWidth - popupEl.offsetWidth - 12) + 'px';
    }

    // Globale klik-afhandeling: klik op een Ge'ez-woord toont de popup; klik elders sluit.
    document.addEventListener('click', function (e) {
        const w = e.target.closest && e.target.closest('.geez-word');
        if (w) {
            e.stopPropagation();
            showPopup(w.dataset.geez || w.textContent, w);
        } else if (popupEl && !(e.target.closest && e.target.closest('.geez-lex-popup'))) {
            closePopup();
        }
    });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closePopup(); });

    window.GeezLexicon = { transliterate: transliterate };
})();
