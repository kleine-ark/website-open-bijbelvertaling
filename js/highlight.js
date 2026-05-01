/* Highlight — markeer hele verzen of losse woorden in OV2026-kolom in een van 4 kleuren */

const Highlight = {
    STORAGE_KEY: 'sv2026_highlights_v1',
    COLORS: ['magenta', 'lichtblauw', 'lichtgroen', 'lichtgeel'],
    LABELS: {
        magenta: 'Magenta',
        lichtblauw: 'Licht­blauw',
        lichtgroen: 'Licht­groen',
        lichtgeel: 'Licht­geel'
    },
    state: {},        // "bookId:ch:vs" -> { verse?: 'magenta', words?: [{text,color}] }
    palette: null,    // floating word-palette element
    lastSelection: null,  // { range, bookId, ch, vs, text }

    /* ===== persistence ===== */
    load() {
        try {
            const raw = localStorage.getItem(this.STORAGE_KEY);
            this.state = raw ? JSON.parse(raw) : {};
        } catch (e) {
            console.warn('Highlight load error:', e);
            this.state = {};
        }
    },

    save() {
        try {
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.state));
        } catch (e) {
            console.warn('Highlight save error:', e);
        }
    },

    keyFor(bookId, ch, vs) {
        return `${bookId}:${ch}:${vs}`;
    },

    /* ===== verse-level highlight ===== */
    setVerseColor(bookId, ch, vs, color) {
        const key = this.keyFor(bookId, ch, vs);
        if (!this.state[key]) this.state[key] = {};
        this.state[key].verse = color;
        this.save();
        this.applyVerseToRow(bookId, ch, vs);
    },

    clearVerse(bookId, ch, vs) {
        const key = this.keyFor(bookId, ch, vs);
        if (this.state[key]) {
            delete this.state[key].verse;
            if (!this.state[key].verse && (!this.state[key].words || this.state[key].words.length === 0)) {
                delete this.state[key];
            }
            this.save();
        }
        // strip classes
        const row = document.querySelector(`.verse-row[data-book="${bookId}"][data-chapter="${ch}"][data-verse="${vs}"]`);
        if (row) {
            this.COLORS.forEach(c => row.classList.remove(`hl-verse-${c}`));
        }
    },

    applyVerseToRow(bookId, ch, vs) {
        const row = document.querySelector(`.verse-row[data-book="${bookId}"][data-chapter="${ch}"][data-verse="${vs}"]`);
        if (!row) return;
        this.COLORS.forEach(c => row.classList.remove(`hl-verse-${c}`));
        const key = this.keyFor(bookId, ch, vs);
        const entry = this.state[key];
        if (entry && entry.verse && this.COLORS.includes(entry.verse)) {
            row.classList.add(`hl-verse-${entry.verse}`);
        }
    },

    /* ===== word-level highlight =====
     * Storage: { start, end, text, color } — start/end zijn char-offsets binnen
     * cell.textContent. Werkt ook over <sup>, <i>, <span> heen. `text` is
     * fallback voor oude entries en debug.
     */
    addWordHighlight(bookId, ch, vs, range, color) {
        const cell = this._cellFor(bookId, ch, vs);
        if (!cell || !range) return;
        const start = this._offsetInCell(cell, range.startContainer, range.startOffset);
        const end   = this._offsetInCell(cell, range.endContainer,   range.endOffset);
        if (start < 0 || end <= start) return;
        const text = range.toString();
        const key = this.keyFor(bookId, ch, vs);
        if (!this.state[key]) this.state[key] = {};
        if (!this.state[key].words) this.state[key].words = [];
        // Verwijder bestaande overlappende entries (zelfde range opnieuw kleuren = vervangen)
        this.state[key].words = this.state[key].words.filter(w => {
            const ws = w.start ?? -1, we = w.end ?? -1;
            if (ws < 0) return true; // legacy entries niet wegfilteren
            return we <= start || ws >= end; // niet-overlappend = behouden
        });
        this.state[key].words.push({ start, end, text, color });
        this.save();
        this.applyWordsToCell(bookId, ch, vs);
    },

    removeWordAt(bookId, ch, vs, offset) {
        const key = this.keyFor(bookId, ch, vs);
        const entry = this.state[key];
        if (!entry || !entry.words) return false;
        const before = entry.words.length;
        entry.words = entry.words.filter(w => {
            const s = w.start ?? -1, e = w.end ?? -1;
            if (s < 0) return true;
            return offset < s || offset >= e;
        });
        if (entry.words.length === before) return false;
        if (entry.words.length === 0 && !entry.verse) delete this.state[key];
        this.save();
        this.applyWordsToCell(bookId, ch, vs);
        return true;
    },

    clearWordHighlights(bookId, ch, vs) {
        const key = this.keyFor(bookId, ch, vs);
        if (this.state[key]) {
            delete this.state[key].words;
            if (!this.state[key].verse && (!this.state[key].words || this.state[key].words.length === 0)) {
                delete this.state[key];
            }
            this.save();
        }
        this.applyWordsToCell(bookId, ch, vs);
    },

    _cellFor(bookId, ch, vs) {
        return document.querySelector(
            `.verse-row[data-book="${bookId}"][data-chapter="${ch}"][data-verse="${vs}"] .col-2026`
        );
    },

    // Char-offset van (node, offset) binnen cell.textContent
    _offsetInCell(cell, node, off) {
        if (!cell.contains(node)) return -1;
        const walker = document.createTreeWalker(cell, NodeFilter.SHOW_TEXT, null);
        let pos = 0, n;
        while ((n = walker.nextNode())) {
            if (n === node) return pos + off;
            pos += n.nodeValue.length;
        }
        // node is geen text-node (bv. element) — gebruik element-positie
        if (node.nodeType === 1) {
            const r = document.createRange();
            r.selectNodeContents(cell);
            r.setEnd(node, off);
            return r.toString().length;
        }
        return -1;
    },

    // Range over [start, end) char-offsets binnen cell.textContent
    _rangeFromOffsets(cell, start, end) {
        const walker = document.createTreeWalker(cell, NodeFilter.SHOW_TEXT, null);
        let pos = 0, n;
        let startNode = null, startOff = 0, endNode = null, endOff = 0;
        while ((n = walker.nextNode())) {
            const len = n.nodeValue.length;
            if (startNode === null && pos + len > start) {
                startNode = n;
                startOff = start - pos;
            }
            if (startNode !== null && pos + len >= end) {
                endNode = n;
                endOff = end - pos;
                break;
            }
            pos += len;
        }
        if (!startNode || !endNode) return null;
        const range = document.createRange();
        range.setStart(startNode, startOff);
        range.setEnd(endNode, endOff);
        return range;
    },

    applyWordsToCell(bookId, ch, vs) {
        const cell = this._cellFor(bookId, ch, vs);
        if (!cell) return;
        // Strip bestaande word-marks (unwrap <mark> → text)
        cell.querySelectorAll('mark.hl-word').forEach(m => {
            const parent = m.parentNode;
            while (m.firstChild) parent.insertBefore(m.firstChild, m);
            parent.removeChild(m);
        });
        cell.normalize();

        const key = this.keyFor(bookId, ch, vs);
        const entry = this.state[key];
        if (!entry || !entry.words || entry.words.length === 0) return;

        for (const w of entry.words) {
            if (!this.COLORS.includes(w.color)) continue;
            const hasOffsets = (w.start != null) && (w.end != null) && w.end > w.start;
            const range = hasOffsets
                ? this._rangeFromOffsets(cell, w.start, w.end)
                : (w.text ? this._findRangeByText(cell, w.text) : null);
            if (!range) continue;
            this._wrapRangeMulti(range, w.color);
            cell.normalize();
        }
    },

    // Wrap een range die meerdere text-nodes/elementen kan overspannen.
    // Per text-node: knip exact stuk en wrap in eigen <mark>.
    _wrapRangeMulti(range, color) {
        const walker = document.createTreeWalker(range.commonAncestorContainer, NodeFilter.SHOW_TEXT, null);
        const nodes = [];
        let n;
        while ((n = walker.nextNode())) {
            if (range.intersectsNode(n)) nodes.push(n);
        }
        // Edge case: range zit binnen één text-node → walker pakt 'm niet vanaf commonAncestor=text
        if (nodes.length === 0 && range.startContainer === range.endContainer && range.startContainer.nodeType === 3) {
            nodes.push(range.startContainer);
        }
        for (const node of nodes) {
            const startOff = (node === range.startContainer) ? range.startOffset : 0;
            const endOff   = (node === range.endContainer)   ? range.endOffset   : node.nodeValue.length;
            if (startOff >= endOff) continue;
            // Skip als al binnen hl-word
            if (node.parentElement && node.parentElement.closest('mark.hl-word')) continue;
            const sub = document.createRange();
            sub.setStart(node, startOff);
            sub.setEnd(node, endOff);
            const mark = document.createElement('mark');
            mark.className = `hl-word hl-word-${color}`;
            mark.dataset.hlOffsetStart = String(startOff);
            try {
                sub.surroundContents(mark);
            } catch (e) {
                try {
                    const frag = sub.extractContents();
                    mark.appendChild(frag);
                    sub.insertNode(mark);
                } catch (e2) {
                    console.warn('hl wrap failed', e2);
                }
            }
        }
    },

    // Legacy fallback: zoek tekst over text-nodes heen
    _findRangeByText(cell, text) {
        const full = cell.textContent;
        const idx = full.indexOf(text);
        if (idx < 0) return null;
        return this._rangeFromOffsets(cell, idx, idx + text.length);
    },

    /* ===== applied to whole chapter render ===== */
    applyToChapter(bookId, chapterNum) {
        const rows = document.querySelectorAll(
            `.verse-row[data-book="${bookId}"][data-chapter="${chapterNum}"]`
        );
        rows.forEach(row => {
            const vs = row.dataset.verse;
            this.applyVerseToRow(bookId, chapterNum, vs);
            this.applyWordsToCell(bookId, chapterNum, vs);
        });
    },

    /* ===== floating word palette ===== */
    buildPalette() {
        if (this.palette) return this.palette;
        const pal = document.createElement('div');
        pal.id = 'word-hl-palette';
        pal.className = 'hl-palette hl-palette-float';
        pal.style.display = 'none';
        pal.innerHTML = this.COLORS.map(c =>
            `<button class="hl-color-btn hl-color-${c}" data-color="${c}" title="${this.LABELS[c]}"></button>`
        ).join('') + `<button class="hl-color-btn hl-clear" data-action="clear" title="Wissen">&times;</button>`;
        document.body.appendChild(pal);
        pal.addEventListener('mousedown', (e) => {
            // Voorkom dat mousedown op palette de selectie wist
            e.preventDefault();
        });
        pal.addEventListener('click', (e) => {
            const btn = e.target.closest('button');
            if (!btn) return;
            const color = btn.dataset.color;
            const action = btn.dataset.action;
            if (action === 'clear') {
                if (this.lastSelection) {
                    const { bookId, ch, vs } = this.lastSelection;
                    this.clearWordHighlights(bookId, ch, vs);
                }
            } else if (color && this.lastSelection) {
                const { bookId, ch, vs, range } = this.lastSelection;
                this.addWordHighlight(bookId, ch, vs, range, color);
            }
            this.hidePalette();
        });
        this.palette = pal;
        return pal;
    },

    showPaletteAt(rect) {
        const pal = this.buildPalette();
        pal.style.display = 'flex';
        // Plaats boven selectie
        const top = window.scrollY + rect.top - pal.offsetHeight - 8;
        const left = window.scrollX + rect.left + (rect.width / 2) - (pal.offsetWidth / 2);
        pal.style.top = `${Math.max(8, top)}px`;
        pal.style.left = `${Math.max(8, left)}px`;
    },

    hidePalette() {
        if (this.palette) this.palette.style.display = 'none';
        this.lastSelection = null;
    },

    handleMouseUp(e) {
        // Klik op palette zelf — negeren
        if (e.target.closest('#word-hl-palette')) return;

        setTimeout(() => {
            const sel = window.getSelection();
            if (!sel || sel.isCollapsed || sel.rangeCount === 0) {
                this.hidePalette();
                return;
            }
            const range = sel.getRangeAt(0);
            const text = sel.toString();
            if (!text.trim()) {
                this.hidePalette();
                return;
            }
            // Check: selectie geheel binnen één col-2026 cel?
            const startCell = (range.startContainer.nodeType === 1 ? range.startContainer : range.startContainer.parentElement)
                .closest('.col-2026');
            const endCell = (range.endContainer.nodeType === 1 ? range.endContainer : range.endContainer.parentElement)
                .closest('.col-2026');
            if (!startCell || startCell !== endCell) {
                this.hidePalette();
                return;
            }
            const row = startCell.closest('.verse-row');
            if (!row) {
                this.hidePalette();
                return;
            }
            this.lastSelection = {
                bookId: row.dataset.book,
                ch: parseInt(row.dataset.chapter, 10),
                vs: parseInt(row.dataset.verse, 10),
                text: text,
                range: range.cloneRange()
            };
            const rect = range.getBoundingClientRect();
            this.showPaletteAt(rect);
        }, 1);
    },

    // Klik op een gemarkeerd woord = die ene markering wissen.
    handleMarkClick(e) {
        const mark = e.target.closest('mark.hl-word');
        if (!mark) return;
        const cell = mark.closest('.col-2026');
        if (!cell) return;
        const row = mark.closest('.verse-row');
        if (!row) return;
        // Alleen wegklikken als er geen actieve tekstselectie is
        const sel = window.getSelection();
        if (sel && !sel.isCollapsed && sel.toString().trim().length > 0) return;
        e.preventDefault();
        e.stopPropagation();
        // Vind char-offset van deze mark binnen cell
        const offset = this._offsetInCell(cell, mark.firstChild || mark, 0);
        if (offset < 0) return;
        const bookId = row.dataset.book;
        const ch = parseInt(row.dataset.chapter, 10);
        const vs = parseInt(row.dataset.verse, 10);
        // Probeer eerst nieuwe-stijl (offset-based)
        const removed = this.removeWordAt(bookId, ch, vs, offset);
        if (!removed) {
            // Legacy: vind de matching word-entry op text en verwijder
            const text = mark.textContent;
            const key = this.keyFor(bookId, ch, vs);
            const entry = this.state[key];
            if (entry && entry.words) {
                const idx = entry.words.findIndex(w => (w.start == null) && w.text === text);
                if (idx >= 0) {
                    entry.words.splice(idx, 1);
                    if (entry.words.length === 0 && !entry.verse) delete this.state[key];
                    this.save();
                    this.applyWordsToCell(bookId, ch, vs);
                }
            }
        }
        this.hidePalette();
    },

    init() {
        this.load();
        // Mouseup wereldwijd: filter op col-2026 in handler
        document.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        // Klik op bestaande markering → die markering wissen (alleen zonder selectie)
        document.addEventListener('click', (e) => this.handleMarkClick(e));
        // Klik buiten palette → verbergen
        document.addEventListener('mousedown', (e) => {
            if (this.palette && this.palette.style.display !== 'none' &&
                !e.target.closest('#word-hl-palette')) {
                // Wacht op selectie-handling; verberg pas als geen nieuwe selectie volgt
                setTimeout(() => {
                    const sel = window.getSelection();
                    if (!sel || sel.isCollapsed) this.hidePalette();
                }, 50);
            }
        });
        // Sluit palette bij scroll
        window.addEventListener('scroll', () => {
            if (this.palette && this.palette.style.display !== 'none') this.hidePalette();
        }, { passive: true });
    }
};

document.addEventListener('DOMContentLoaded', () => Highlight.init());
