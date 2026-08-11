/* Open Vertaling — Lexicon tooltip integratie */

const Lexicon = {
    currentTooltip: null,
    lastTrigger: null,

    hoverTooltip: null,
    hoverTimeout: null,

    // Nederlandse vertaal-overlay (glossNl/definitieNl), lui geladen per taal
    _nl: { hebrew: null, greek: null },
    async ensureNl(lang) {
        if (this._nl[lang]) return this._nl[lang];
        const url = lang === 'hebrew' ? '/data/lexicon-nl/bdb-nl.json' : '/data/lexicon-nl/abbott-nl.json';
        try {
            const r = await fetch(url);
            this._nl[lang] = r.ok ? await r.json() : {};
        } catch (e) { this._nl[lang] = {}; }
        return this._nl[lang];
    },

    init() {
        if (this._initialized) return;
        this._initialized = true;
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
                const strongs = inlineEl.dataset.strongs || inlineEl.textContent.trim().replace(/[<>]/g, '');
                if (strongs) {
                    this.showEntryByStrongs(strongs, inlineEl);
                }
                return;
            }
            if (this.currentTooltip && !e.target.closest('.lexicon-tooltip, .strongs-sheet-panel')) {
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

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.currentTooltip) {
                e.preventDefault();
                this.hideTooltip(true);
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

    async showEntry(wordEl) {
        const strongs = wordEl.dataset.strongs;
        if (!strongs) return;
        return this.showEntryByStrongs(strongs, wordEl);
    },

    async showEntryByStrongs(strongs, anchorEl) {
        this.hideTooltip();

        const family = window.OVWoordnummers
            ? window.OVWoordnummers.familyOf(strongs)
            : (/^H\d+[A-Za-z]?$/.test(strongs) ? 'H' : (/^G\d+[A-Za-z]?$/.test(strongs) ? 'G' : null));
        if (!family) return;

        // Lazy-load lexicon indien nog niet geladen
        if ((family === 'H' || family === 'G') && window.LexiconLoader) {
            await window.LexiconLoader.ensureLoaded(family === 'H' ? 'hebrew' : 'greek');
        }

        let entry = null;
        let lexiconName = '';
        let fullLink = '';

        if (family === 'H') {
            lexiconName = 'BDB Hebreeuws';
            fullLink = `lexicon-viewer.html?entry=${encodeURIComponent(strongs)}`;
            if (typeof bdbLexicon !== 'undefined') entry = bdbLexicon[strongs];
        } else if (family === 'G') {
            lexiconName = 'Abbott-Smith Grieks';
            fullLink = `lexicon-viewer.html?entry=${encodeURIComponent(strongs)}`;
            if (typeof abbottSmithLexicon !== 'undefined') entry = abbottSmithLexicon[strongs];
        } else if (family === 'OVL') {
            entry = {};
            lexiconName = 'Lewis & Short Latijn';
            fullLink = `lexicon-viewer.html?taal=latijn&zoek=${encodeURIComponent(strongs)}`;
        } else if (family === 'OVG') {
            entry = {};
            lexiconName = 'Dillmann Ge’ez';
            fullLink = `lexicon-viewer.html?taal=geez&zoek=${encodeURIComponent(strongs)}`;
        }

        // Een nummer blijft bruikbaar wanneer een lexiconartikel nog ontbreekt:
        // toon de brongegevens en bied de volledige woordenboekzoeking aan.
        if (!entry) entry = {};

        const nl = (family === 'H' || family === 'G')
            ? await this.ensureNl(family === 'H' ? 'hebrew' : 'greek') : {};
        const t = nl[strongs] || {};

        const gloss = t.glossNl || t.samenvattingNl || anchorEl.dataset.gloss || entry.gloss || '';
        const woord = anchorEl.dataset.sourceWord || entry.woord || '';
        const transliteratie = anchorEl.dataset.transliteratie || entry.translit || entry.transliteratie || '';
        const definitie = t.definitieNl || entry.definitie ||
            (gloss ? `Betekenis in deze bronkoppeling: ${gloss}.` : 'Voor dit woordnummer is nog geen lokale woordenboekdefinitie beschikbaar.');
        if (!fullLink) fullLink = `lexicon-viewer.html?entry=${encodeURIComponent(strongs)}`;

        const sheet = document.createElement('div');
        sheet.id = 'strongs-sheet';
        sheet.className = 'strongs-sheet';
        sheet.setAttribute('role', 'dialog');
        sheet.setAttribute('aria-modal', 'true');
        sheet.setAttribute('aria-labelledby', 'strongs-sheet-number');
        sheet.innerHTML = `
            <section class="strongs-sheet-panel">
                <div class="strongs-sheet-handle" aria-hidden="true"></div>
                <header class="strongs-sheet-header">
                    <div>
                        <span id="strongs-sheet-number" class="lexicon-strongs">${this.escapeHtml(strongs)}</span>
                        <span class="lexicon-source">${this.escapeHtml(lexiconName)}</span>
                    </div>
                    <button type="button" class="strongs-sheet-close" aria-label="Woordenboek sluiten">×</button>
                </header>
                <div class="strongs-sheet-content">
                    <div id="strongs-sheet-word" class="lexicon-word">${this.escapeHtml(woord)}</div>
                    ${transliteratie ? `<div class="strongs-sheet-transliteration">${this.escapeHtml(transliteratie)}</div>` : ''}
                    <div class="lexicon-gloss">${this.escapeHtml(gloss)}</div>
                    <div id="strongs-sheet-definition" class="lexicon-def">${this.sanitizeDefinition(definitie)}</div>
                    <a id="strongs-sheet-full-link" class="strongs-sheet-full-link" href="${this.escapeHtml(fullLink)}">Volledig woordenboekartikel openen →</a>
                </div>
            </section>`;

        sheet.addEventListener('click', (event) => {
            if (event.target === sheet) this.hideTooltip(true);
        });
        sheet.addEventListener('keydown', (event) => {
            if (event.key !== 'Tab') return;
            const focusable = [...sheet.querySelectorAll('button:not([disabled]), a[href]')];
            if (!focusable.length) return;
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            if (event.shiftKey && document.activeElement === first) {
                event.preventDefault();
                last.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
                event.preventDefault();
                first.focus();
            }
        });
        sheet.querySelector('.strongs-sheet-close').addEventListener('click', () => this.hideTooltip(true));
        document.body.appendChild(sheet);
        document.body.classList.add('strongs-sheet-open');
        this.currentTooltip = sheet;
        this.lastTrigger = anchorEl;
        sheet.querySelector('.strongs-sheet-close').focus();
    },

    escapeHtml(value) {
        const span = document.createElement('span');
        span.textContent = String(value == null ? '' : value);
        return span.innerHTML;
    },

    sanitizeDefinition(html) {
        const template = document.createElement('template');
        template.innerHTML = String(html || 'Geen woordenboekdefinitie beschikbaar.');
        const allowed = new Set(['B', 'STRONG', 'I', 'EM', 'BR', 'P', 'DIV', 'UL', 'OL', 'LI', 'SUP', 'SUB', 'SPAN']);
        [...template.content.querySelectorAll('*')].forEach(node => {
            if (!allowed.has(node.tagName)) {
                node.replaceWith(...node.childNodes);
                return;
            }
            [...node.attributes].forEach(attribute => node.removeAttribute(attribute.name));
        });
        return template.innerHTML;
    },

    hideTooltip(restoreFocus = false) {
        if (this.currentTooltip) {
            this.currentTooltip.remove();
            this.currentTooltip = null;
        }
        document.body.classList.remove('strongs-sheet-open');
        if (restoreFocus && this.lastTrigger && this.lastTrigger.isConnected) {
            this.lastTrigger.focus();
        }
        this.lastTrigger = null;
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

if (typeof window !== 'undefined') window.Lexicon = Lexicon;
