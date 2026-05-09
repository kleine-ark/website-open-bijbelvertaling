/* Verse Select — Selecteer meerdere verzen en kopieer met/zonder opmaak */

const VerseSelect = {
    selected: new Set(),
    lastClicked: null,

    init() {
        // Kopieer-toolbar toevoegen aan DOM
        const toolbar = document.createElement('div');
        toolbar.id = 'copy-toolbar';
        const HL_COLORS = ['magenta', 'lichtblauw', 'lichtgroen', 'lichtgeel'];
        const HL_LABELS = { magenta: 'Magenta', lichtblauw: 'Lichtblauw', lichtgroen: 'Lichtgroen', lichtgeel: 'Lichtgeel' };
        const paletteHtml = `<div class="hl-palette hl-palette-toolbar" id="verse-hl-palette">
            ${HL_COLORS.map(c => `<button class="hl-color-btn hl-color-${c}" data-hl-color="${c}" title="Markeer ${HL_LABELS[c]}"></button>`).join('')}
            <button class="hl-color-btn hl-clear" data-hl-action="clear" title="Wis markering">&times;</button>
        </div>`;
        toolbar.innerHTML = `
            <span id="copy-count"></span>
            <button id="copy-formatted" title="Kopieer met versnummers, opmaak en Godscitaten">Met opmaak</button>
            <button id="copy-plain" title="Kopieer als platte tekst">Zonder opmaak</button>
            ${paletteHtml}
            <button id="copy-close" title="Deselecteer alles">&times;</button>
        `;
        document.body.appendChild(toolbar);

        document.getElementById('copy-formatted').addEventListener('click', () => this.copy(true));
        document.getElementById('copy-plain').addEventListener('click', () => this.copy(false));
        document.getElementById('copy-close').addEventListener('click', () => this.clearAll());

        // Highlight-palet voor geselecteerde verzen
        document.getElementById('verse-hl-palette').addEventListener('click', (e) => {
            const btn = e.target.closest('button.hl-color-btn');
            if (!btn) return;
            const color = btn.dataset.hlColor;
            const action = btn.dataset.hlAction;
            const rows = this.getSelectedRows();
            if (rows.length === 0 || typeof Highlight === 'undefined') return;
            for (const row of rows) {
                const bookId = row.dataset.book;
                const ch = parseInt(row.dataset.chapter, 10);
                const vs = parseInt(row.dataset.verse, 10);
                if (action === 'clear') {
                    Highlight.clearVerse(bookId, ch, vs);
                } else if (color) {
                    Highlight.setVerseColor(bookId, ch, vs, color);
                }
            }
        });

        // Luister naar klikken op versnummers (legacy: highlight-toggle e.d.)
        document.getElementById('verses-container').addEventListener('click', (e) => {
            const num = e.target.closest('.verse-num');
            if (!num) return;
            const row = num.closest('.verse-row');
            if (!row) return;

            const verseKey = row.dataset.verse;

            if (e.shiftKey && this.lastClicked) {
                this.selectRange(this.lastClicked, verseKey);
            } else if (e.ctrlKey || e.metaKey) {
                this.toggle(verseKey);
            } else {
                if (this.selected.has(verseKey) && this.selected.size === 1) {
                    this.clearAll();
                } else {
                    this.clearAll();
                    this.select(verseKey);
                }
            }
            this.lastClicked = verseKey;
            this.updateUI();
        });

        // NIEUW: klik op de OV2026 tekst-cel selecteert de tekst browser-native
        // (zodat Ctrl+C werkt) + toont copy-toolbar onderin.
        // Drag-select (>5px) wordt gerespecteerd voor sub-selectie van een woord/zin.
        let downX = 0, downY = 0;
        const versesContainer = document.getElementById('verses-container');
        versesContainer.addEventListener('pointerdown', (e) => {
            downX = e.clientX; downY = e.clientY;
        });
        versesContainer.addEventListener('pointerup', (e) => {
            // Skip als klik op interactief sub-element
            if (e.target.closest('.note-marker, .strongs-inline, a, .begrip-link, .verse-num, button')) return;
            const cell = e.target.closest('.col-2026');
            if (!cell) return;
            const row = cell.closest('.verse-row');
            if (!row) return;
            const moved = Math.hypot(e.clientX - downX, e.clientY - downY);
            if (moved > 5) return; // user is drag-selecting
            const verseKey = row.dataset.verse;
            this.toggle(verseKey);
            this._syncBrowserSelectionToSelected();
            this.updateUI();
        });

        // selectionchange-driven toolbar — luistert op browser-native selectie
        // binnen #verses-container, ongeacht hoe die ontstond (klik of drag).
        this._setupSelectionToolbar();
    },

    // Synchroniseer browser-native Selection met de this.selected set.
    // Probeer addRange per geselecteerde vers (Firefox toont dat als losse
    // highlights; Chrome rendert alleen de eerste range — visueel valt
    // .verse-row.verse-selected dat alsnog op via de CSS class).
    _syncBrowserSelectionToSelected() {
        const sel = window.getSelection();
        if (!sel) return;
        sel.removeAllRanges();
        const keys = [...this.selected];
        for (const key of keys) {
            const row = document.querySelector(`.verse-row[data-verse="${key}"]`);
            if (!row) continue;
            const cell = row.querySelector('.col-2026');
            if (!cell) continue;
            const range = document.createRange();
            range.selectNodeContents(cell);
            try { sel.addRange(range); } catch (e) { /* sommige browsers limiteren range-count */ }
        }
    },

    _setupSelectionToolbar() {
        let timer = null;
        document.addEventListener('selectionchange', () => {
            clearTimeout(timer);
            timer = setTimeout(() => this._handleSelectionChange(), 80);
        });
        // mousedown op toolbar mag selectie niet wissen
        const tb = document.getElementById('copy-toolbar');
        if (tb) tb.addEventListener('mousedown', (e) => e.preventDefault());
    },

    _handleSelectionChange() {
        const sel = window.getSelection();
        const tb = document.getElementById('copy-toolbar');
        if (!tb) return;
        // Als er via klik al verzen geselecteerd zijn (this.selected),
        // laat updateUI dat afhandelen — niet overrulen vanuit selectionchange.
        if (this.selected.size > 0) { tb.classList.add('visible'); return; }
        if (!sel || sel.rangeCount === 0 || !sel.toString().trim()) {
            tb.classList.remove('visible');
            return;
        }
        const versesContainer = document.getElementById('verses-container');
        const range = sel.getRangeAt(0);
        if (!versesContainer || !versesContainer.contains(range.commonAncestorContainer)) return;
        // Drag-selectie → toon "X tekens geselecteerd"
        const cnt = document.getElementById('copy-count');
        if (cnt) cnt.textContent = `${sel.toString().length} tekens geselecteerd`;
        tb.classList.add('visible');
    },

    select(key) {
        this.selected.add(key);
        const row = document.querySelector(`.verse-row[data-verse="${key}"]`);
        if (row) row.classList.add('verse-selected');
    },

    deselect(key) {
        this.selected.delete(key);
        const row = document.querySelector(`.verse-row[data-verse="${key}"]`);
        if (row) row.classList.remove('verse-selected');
    },

    toggle(key) {
        if (this.selected.has(key)) {
            this.deselect(key);
        } else {
            this.select(key);
        }
    },

    selectRange(fromKey, toKey) {
        const rows = [...document.querySelectorAll('.verse-row')];
        const fromIdx = rows.findIndex(r => r.dataset.verse === fromKey);
        const toIdx = rows.findIndex(r => r.dataset.verse === toKey);
        if (fromIdx < 0 || toIdx < 0) return;

        const start = Math.min(fromIdx, toIdx);
        const end = Math.max(fromIdx, toIdx);
        for (let i = start; i <= end; i++) {
            this.select(rows[i].dataset.verse);
        }
    },

    clearAll() {
        document.querySelectorAll('.verse-row.verse-selected').forEach(r => r.classList.remove('verse-selected'));
        this.selected.clear();
        this.updateUI();
    },

    updateUI() {
        const toolbar = document.getElementById('copy-toolbar');
        const count = this.selected.size;
        if (count > 0) {
            // Bouw "Boek H:V[-W of ,X]" label
            const nums = [...this.selected].map(n => parseInt(n)).filter(n => !isNaN(n)).sort((a,b) => a-b);
            const bookEl = document.getElementById('chapter-title');
            let bookName = '';
            if (bookEl) {
                const clone = bookEl.cloneNode(true);
                clone.querySelectorAll('.chapter-concept-tag').forEach(t => t.remove());
                bookName = clone.textContent.trim();
            }
            let ref;
            if (nums.length === 1) ref = `${bookName}:${nums[0]}`;
            else if (nums.every((n,i) => i===0 || n === nums[i-1]+1))
                ref = `${bookName}:${nums[0]}-${nums[nums.length-1]}`;
            else
                ref = `${bookName}:${nums.join(',')}`;
            document.getElementById('copy-count').textContent = `${ref} (${count} vers${count > 1 ? 'en' : ''})`;
            toolbar.classList.add('visible');
        } else {
            toolbar.classList.remove('visible');
        }
    },

    getSelectedRows() {
        // Geordend op positie in de DOM
        const rows = [...document.querySelectorAll('.verse-row')];
        return rows.filter(r => this.selected.has(r.dataset.verse));
    },

    copy(withFormatting) {
        const rows = this.getSelectedRows();
        if (rows.length === 0) return;

        // Welke kolom is de OV2026 kolom?
        const col2026 = rows.map(row => {
            const num = row.querySelector('.verse-num')?.textContent?.trim() || '';
            const cell = row.querySelector('.col-2026');
            return { num, cell };
        });

        if (withFormatting) {
            // HTML: versnummers vet, god-speaks rood+cursief
            const htmlParts = col2026.map(({ num, cell }) => {
                // Kloon de cel inhoud maar strip contenteditable artefacten
                const clone = cell.cloneNode(true);
                // Verwijder note-markers voor kopieer
                clone.querySelectorAll('.note-marker').forEach(m => m.remove());
                clone.querySelectorAll('.strongs-inline').forEach(m => m.remove());
                const inner = clone.innerHTML.trim();
                return `<b>${num}</b> ${inner}`;
            });
            const html = htmlParts.join('<br>\n');

            // Platte tekst als fallback
            const plain = col2026.map(({ num, cell }) => {
                const clone = cell.cloneNode(true);
                clone.querySelectorAll('.note-marker').forEach(m => m.remove());
                clone.querySelectorAll('.strongs-inline').forEach(m => m.remove());
                return `${num} ${clone.textContent.trim()}`;
            }).join('\n');

            const blob = new Blob([html], { type: 'text/html' });
            const blobPlain = new Blob([plain], { type: 'text/plain' });
            navigator.clipboard.write([
                new ClipboardItem({
                    'text/html': blob,
                    'text/plain': blobPlain
                })
            ]).then(() => this.showCopied('Met opmaak gekopieerd!'));
        } else {
            // Platte tekst
            const plain = col2026.map(({ num, cell }) => {
                const clone = cell.cloneNode(true);
                clone.querySelectorAll('.note-marker').forEach(m => m.remove());
                clone.querySelectorAll('.strongs-inline').forEach(m => m.remove());
                return `${num} ${clone.textContent.trim()}`;
            }).join('\n');

            navigator.clipboard.writeText(plain)
                .then(() => this.showCopied('Zonder opmaak gekopieerd!'));
        }
    },

    showCopied(msg) {
        const toolbar = document.getElementById('copy-toolbar');
        const countEl = document.getElementById('copy-count');
        const orig = countEl.textContent;
        countEl.textContent = msg;
        countEl.style.color = '#27ae60';
        setTimeout(() => {
            countEl.textContent = orig;
            countEl.style.color = '';
        }, 1500);
    }
};

document.addEventListener('DOMContentLoaded', () => VerseSelect.init());
