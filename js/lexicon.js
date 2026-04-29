/* Open Vertaling — Lexicon tooltip integratie */

const Lexicon = {
    currentTooltip: null,

    hoverTooltip: null,
    hoverTimeout: null,

    init() {
        // Klik: toon uitgebreide lexicon-entry
        document.addEventListener('click', (e) => {
            // Klik op grondtekst-woord
            const wordEl = e.target.closest('.strongs-word');
            if (wordEl) {
                e.stopPropagation();
                this.hideHover();
                this.showEntry(wordEl);
                return;
            }
            // Klik op inline Strong's nummer (blauw superscript)
            const inlineEl = e.target.closest('.strongs-inline');
            if (inlineEl) {
                e.stopPropagation();
                const strongs = inlineEl.textContent.trim();
                if (strongs) {
                    this.showEntryByStrongs(strongs, inlineEl);
                }
                return;
            }
            if (this.currentTooltip && !e.target.closest('.lexicon-tooltip')) {
                this.hideTooltip();
            }
        });

        // Hover: toon korte tooltip met woord + betekenis + highlight NL tekst
        document.addEventListener('mouseover', (e) => {
            const wordEl = e.target.closest('.strongs-word');
            if (wordEl && !this.currentTooltip) {
                clearTimeout(this.hoverTimeout);
                this.hoverTimeout = setTimeout(() => {
                    this.showHover(wordEl);
                    this.highlightVerseWord(wordEl);
                }, 200);
            }
        });
        document.addEventListener('mouseout', (e) => {
            const wordEl = e.target.closest('.strongs-word');
            if (wordEl) {
                clearTimeout(this.hoverTimeout);
                this.hideHover();
                this.clearHighlights();
            }
        });
    },

    showHover(wordEl) {
        this.hideHover();
        const strongs = wordEl.dataset.strongs;
        if (!strongs) return;

        const woord = wordEl.textContent;
        const transliteratie = wordEl.dataset.transliteratie || '';
        const gloss = wordEl.dataset.gloss || '';

        if (!transliteratie && !gloss) return;

        const tip = document.createElement('div');
        tip.className = 'word-hover-tooltip';
        tip.innerHTML = `<strong>${woord}</strong>` +
            (transliteratie ? ` <span class="wht-translit">${transliteratie}</span>` : '') +
            (gloss ? `<br><span class="wht-gloss">${gloss}</span>` : '') +
            `<br><span class="wht-strongs">${strongs}</span>`;

        document.body.appendChild(tip);
        this.hoverTooltip = tip;

        const rect = wordEl.getBoundingClientRect();
        let left = rect.left;
        let top = rect.top - tip.offsetHeight - 6;
        if (top < 5) top = rect.bottom + 6;
        if (left + tip.offsetWidth > window.innerWidth - 10) {
            left = window.innerWidth - tip.offsetWidth - 10;
        }
        tip.style.left = left + 'px';
        tip.style.top = top + 'px';
    },

    hideHover() {
        if (this.hoverTooltip) {
            this.hoverTooltip.remove();
            this.hoverTooltip = null;
        }
    },

    showEntry(wordEl) {
        this.hideTooltip();

        const strongs = wordEl.dataset.strongs;
        if (!strongs) return;

        let entry = null;
        let lexiconName = '';

        if (strongs.startsWith('H') && typeof bdbLexicon !== 'undefined') {
            entry = bdbLexicon[strongs];
            lexiconName = 'BDB Hebreeuws';
        } else if (strongs.startsWith('G') && typeof abbottSmithLexicon !== 'undefined') {
            entry = abbottSmithLexicon[strongs];
            lexiconName = 'Abbott-Smith Grieks';
        }

        if (!entry) return;

        const tooltip = document.createElement('div');
        tooltip.className = 'lexicon-tooltip';

        const gloss = entry.gloss || '';
        const woord = entry.woord || '';
        // Korte definitie: neem eerste 300 tekens
        let definitie = entry.definitie || '';
        if (definitie.length > 400) {
            definitie = definitie.substring(0, 400) + '...';
        }

        tooltip.innerHTML = `
            <div class="lexicon-header">
                <span class="lexicon-strongs">${strongs}</span>
                <span class="lexicon-source">${lexiconName}</span>
            </div>
            <div class="lexicon-word">${woord}</div>
            <div class="lexicon-gloss">${gloss}</div>
            <div class="lexicon-def">${definitie}</div>
            <div style="margin-top:8px;border-top:1px solid #eee;padding-top:6px;">
                <a href="#" style="color:var(--gold);font-size:12px;text-decoration:none;" onclick="event.preventDefault();document.getElementById('lexicon-modal').style.display='flex';document.getElementById('lexicon-search').value='${strongs}';document.getElementById('lexicon-search').dispatchEvent(new Event('input'));document.getElementById('lexicon-lang').value='${strongs.startsWith('H')?'hebrew':'greek'}';return false;">→ Open in lexicon</a>
            </div>
        `;

        document.body.appendChild(tooltip);
        this.currentTooltip = tooltip;

        // Positioneer bij het woord
        const rect = wordEl.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();

        let left = rect.left;
        let top = rect.bottom + 4;

        // Zorg dat tooltip binnen viewport blijft
        if (left + tooltipRect.width > window.innerWidth - 10) {
            left = window.innerWidth - tooltipRect.width - 10;
        }
        if (top + tooltipRect.height > window.innerHeight - 10) {
            top = rect.top - tooltipRect.height - 4;
        }

        tooltip.style.left = left + 'px';
        tooltip.style.top = top + 'px';
    },

    showEntryByStrongs(strongs, anchorEl) {
        this.hideTooltip();
        let entry = null;
        let lexiconName = '';

        if (strongs.startsWith('H') && typeof bdbLexicon !== 'undefined') {
            entry = bdbLexicon[strongs];
            lexiconName = 'BDB Hebreeuws';
        } else if (strongs.startsWith('G') && typeof abbottSmithLexicon !== 'undefined') {
            entry = abbottSmithLexicon[strongs];
            lexiconName = 'Abbott-Smith Grieks';
        }

        if (!entry) return;

        const gloss = entry.gloss || '';
        const woord = entry.woord || '';
        let definitie = entry.definitie || '';
        if (definitie.length > 400) definitie = definitie.substring(0, 400) + '...';

        const tooltip = document.createElement('div');
        tooltip.className = 'lexicon-tooltip';
        tooltip.innerHTML = `
            <div class="lexicon-header">
                <span class="lexicon-strongs">${strongs}</span>
                <span class="lexicon-source">${lexiconName}</span>
            </div>
            <div class="lexicon-word">${woord}</div>
            <div class="lexicon-gloss">${gloss}</div>
            <div class="lexicon-def">${definitie}</div>
            <div style="margin-top:8px;border-top:1px solid #eee;padding-top:6px;">
                <a href="#" style="color:var(--gold);font-size:12px;text-decoration:none;" onclick="event.preventDefault();document.getElementById('lexicon-modal').style.display='flex';document.getElementById('lexicon-search').value='${strongs}';document.getElementById('lexicon-search').dispatchEvent(new Event('input'));document.getElementById('lexicon-lang').value='${strongs.startsWith('H')?'hebrew':'greek'}';return false;">→ Open in lexicon</a>
            </div>
        `;

        document.body.appendChild(tooltip);
        this.currentTooltip = tooltip;

        const rect = anchorEl.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();
        let left = rect.left;
        let top = rect.bottom + 4;
        if (left + tooltipRect.width > window.innerWidth - 10) left = window.innerWidth - tooltipRect.width - 10;
        if (top + tooltipRect.height > window.innerHeight - 10) top = rect.top - tooltipRect.height - 4;
        tooltip.style.left = left + 'px';
        tooltip.style.top = top + 'px';
    },

    hideTooltip() {
        if (this.currentTooltip) {
            this.currentTooltip.remove();
            this.currentTooltip = null;
        }
    },

    // --- Grondtekst ↔ NL koppeling ---

    highlightVerseWord(wordEl) {
        // Vind de verse-row waar dit woord bij hoort
        const row = wordEl.closest('.verse-row');
        if (!row) return;

        const strongs = wordEl.dataset.strongs;
        const gloss = wordEl.dataset.gloss || '';
        if (!strongs && !gloss) return;

        // Highlight de hele vers-cellen met een subtiele achtergrond
        const cells1637 = row.querySelector('.col-1637');
        const cells2026 = row.querySelector('.col-2026');
        const cellsSV1888 = row.querySelector('.col-marginSV1888');

        // Markeer het actieve grondtekstwoord
        wordEl.classList.add('strongs-active');

        // Probeer het Nederlandse equivalent te markeren via de gloss
        if (gloss) {
            const glossWords = gloss.toLowerCase().split(/[,;/]\s*/);
            [cells1637, cells2026].forEach(cell => {
                if (!cell) return;
                const text = cell.textContent;
                // Zoek naar elk glosswoord in de Nederlandse tekst
                glossWords.forEach(gw => {
                    if (gw.length < 2) return;
                    const regex = new RegExp(`(${gw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
                    if (regex.test(text)) {
                        // Voeg een highlight-klasse toe aan de cel
                        cell.classList.add('strongs-verse-highlight');
                    }
                });
            });
        }

        // Highlight ook alle andere grondtekstwoorden met dezelfde Strong's in dit vers
        row.querySelectorAll(`.strongs-word[data-strongs="${strongs}"]`).forEach(el => {
            el.classList.add('strongs-active');
        });
    },

    clearHighlights() {
        document.querySelectorAll('.strongs-active').forEach(el => {
            el.classList.remove('strongs-active');
        });
        document.querySelectorAll('.strongs-verse-highlight').forEach(el => {
            el.classList.remove('strongs-verse-highlight');
        });
    }
};
