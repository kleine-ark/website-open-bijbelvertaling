/* Verse Select — Selecteer meerdere verzen en kopieer met/zonder opmaak */

const VerseSelect = {
    selected: new Set(),
    lastClicked: null,

    init() {
        // Kopieer-toolbar toevoegen aan DOM
        const toolbar = document.createElement('div');
        toolbar.id = 'copy-toolbar';
        toolbar.innerHTML = `
            <span id="copy-count"></span>
            <button id="copy-formatted" title="Kopieer met versnummers, opmaak en Godscitaten">Met opmaak</button>
            <button id="copy-plain" title="Kopieer als platte tekst">Zonder opmaak</button>
            <button id="copy-close" title="Deselecteer alles">&times;</button>
        `;
        document.body.appendChild(toolbar);

        document.getElementById('copy-formatted').addEventListener('click', () => this.copy(true));
        document.getElementById('copy-plain').addEventListener('click', () => this.copy(false));
        document.getElementById('copy-close').addEventListener('click', () => this.clearAll());

        // Luister naar klikken op versnummers
        document.getElementById('verses-container').addEventListener('click', (e) => {
            const num = e.target.closest('.verse-num');
            if (!num) return;
            const row = num.closest('.verse-row');
            if (!row) return;

            const verseKey = row.dataset.verse;

            if (e.shiftKey && this.lastClicked) {
                // Shift+klik: selecteer bereik
                this.selectRange(this.lastClicked, verseKey);
            } else if (e.ctrlKey || e.metaKey) {
                // Ctrl/Cmd+klik: toggle
                this.toggle(verseKey);
            } else {
                // Gewone klik: als al geselecteerd, deselecteer. Anders selecteer alleen deze.
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
            document.getElementById('copy-count').textContent = `${count} vers${count > 1 ? 'en' : ''} geselecteerd`;
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
