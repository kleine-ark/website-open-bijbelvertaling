/* Statenvertaling 2026 — Editor (contenteditable + auto-save) */

const Editor = {
    activeTooltip: null,
    activeDropdown: null,

    init() {
        // Sluit tooltips/dropdowns bij klik buiten
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.note-tooltip')) this.hideTooltip();
            if (!e.target.closest('.status-dropdown') && !e.target.closest('.verse-num')) {
                this.hideStatusDropdown();
            }
        });

        // Ctrl+S om op te slaan
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                this.saveAll();
            }
            // Ctrl+← en Ctrl+→ voor navigatie
            if (e.ctrlKey && e.key === 'ArrowLeft') {
                e.preventDefault();
                Navigation.navigateRelative(-1);
            }
            if (e.ctrlKey && e.key === 'ArrowRight') {
                e.preventDefault();
                Navigation.navigateRelative(1);
            }
        });
    },

    attachVerseListeners(row, bookId, chapterNum, verseNum) {
        // Auto-save bij blur (vers-cellen)
        const editables = row.querySelectorAll('.col-2026[contenteditable="true"], .col-opmerkingen[contenteditable="true"], .col-notes[contenteditable="true"]');
        editables.forEach(cell => {
            cell.addEventListener('blur', () => {
                this.saveVerse(row, bookId, chapterNum, verseNum);
            });
        });

        // Auto-save kanttekeningen hertaald bij blur
        row.querySelectorAll('.margin-note-edit').forEach(span => {
            span.addEventListener('blur', () => {
                this.saveMarginNote(bookId, chapterNum, verseNum, span);
            });
        });

        // Nootmarker klik
        row.querySelectorAll('.note-marker').forEach(marker => {
            marker.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showNoteTooltip(e.target, bookId, chapterNum, verseNum);
            });
        });

        // Status klik op versnummer
        const numCell = row.querySelector('.verse-num');
        if (numCell) {
            numCell.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showStatusDropdown(e.target, row, bookId, chapterNum, verseNum);
            });
        }
    },

    saveVerse(row, bookId, chapterNum, verseNum) {
        const text2026 = row.querySelector('.col-2026')?.innerText?.trim() || '';
        const opmerkingen = row.querySelector('.col-opmerkingen')?.innerText?.trim() || '';
        const aandachtspunten = row.querySelector('.col-notes')?.innerText?.trim() || '';
        const status = row.dataset.status || 'empty';

        Storage.saveVerse(bookId, chapterNum, verseNum, {
            text2026,
            opmerkingen,
            aandachtspunten,
            status
        });

        // Update cache
        if (DataLoader.cache[bookId]) {
            const ch = DataLoader.cache[bookId].chapters.find(c => c.number === chapterNum);
            if (ch) {
                const v = ch.verses.find(v => v.number === verseNum);
                if (v) {
                    v.text2026 = text2026;
                    v.opmerkingen = opmerkingen;
                    v.aandachtspunten = aandachtspunten;
                    v.status = status;
                }
            }
        }
    },

    saveMarginNote(bookId, chapterNum, verseNum, span) {
        const noteIndex = parseInt(span.dataset.noteIndex);
        const text2026 = span.innerText.trim();

        // Update cache
        if (DataLoader.cache[bookId]) {
            const ch = DataLoader.cache[bookId].chapters.find(c => c.number === chapterNum);
            if (ch) {
                const v = ch.verses.find(v => v.number === verseNum);
                if (v && v.marginNotes && v.marginNotes[noteIndex]) {
                    v.marginNotes[noteIndex].text2026 = text2026;
                }
            }
        }

        // Sla op via Storage
        const edits = Storage.getEdits(bookId) || {};
        const key = `${chapterNum}:${verseNum}`;
        if (!edits[key]) edits[key] = {};
        if (!edits[key].marginNotes) edits[key].marginNotes = {};
        edits[key].marginNotes[noteIndex] = text2026;
        localStorage.setItem(Storage.PREFIX + bookId, JSON.stringify(edits));
    },

    saveAll() {
        document.querySelectorAll('.verse-row').forEach(row => {
            const bookId = row.dataset.book;
            const ch = parseInt(row.dataset.chapter);
            const vs = parseInt(row.dataset.verse);
            this.saveVerse(row, bookId, ch, vs);
        });
        App.updateProgress();
    },

    showNoteTooltip(marker, bookId, chapterNum, verseNum) {
        this.hideTooltip();

        const noteId = marker.dataset.note;
        const book = DataLoader.cache[bookId];
        if (!book) return;

        const chapter = book.chapters.find(c => c.number === chapterNum);
        if (!chapter) return;
        const verse = chapter.verses.find(v => v.number === verseNum);
        if (!verse) return;

        const note = verse.marginNotes.find(n => n.marker === noteId);
        if (!note) return;

        const tooltip = document.createElement('div');
        tooltip.className = 'note-tooltip';
        const linkedText1637 = References.linkify(note.text1637, bookId, chapterNum);
        const linkedText2026 = note.text2026 ? References.linkify(note.text2026, bookId, chapterNum) : '';
        // Toon hertaalde tekst als hoofdtekst, 1637 als ondertekst
        const mainText = linkedText2026 || linkedText1637;
        tooltip.innerHTML = `
            <div class="note-type">${note.type === 'crossref' ? 'Kruisverwijzing' : 'Kanttekening'}</div>
            <div class="note-label">Noot ${note.marker}</div>
            <div>${mainText}</div>
            ${linkedText2026 && linkedText1637 ? `<div style="margin-top:8px;padding-top:8px;border-top:1px solid #eee;font-size:11px;color:#888;"><em>1637:</em> ${linkedText1637}</div>` : ''}
        `;

        document.body.appendChild(tooltip);

        // Positioneer bij de marker
        const rect = marker.getBoundingClientRect();
        tooltip.style.top = (rect.bottom + 8) + 'px';
        tooltip.style.left = Math.min(rect.left, window.innerWidth - 420) + 'px';

        this.activeTooltip = tooltip;
    },

    hideTooltip() {
        if (this.activeTooltip) {
            this.activeTooltip.remove();
            this.activeTooltip = null;
        }
    },

    showStatusDropdown(target, row, bookId, chapterNum, verseNum) {
        this.hideStatusDropdown();

        const dropdown = document.createElement('div');
        dropdown.className = 'status-dropdown';

        const statuses = [
            { value: 'empty', label: 'Leeg' },
            { value: 'draft', label: 'Concept' },
            { value: 'review', label: 'Review' },
            { value: 'final', label: 'Definitief' },
        ];

        for (const s of statuses) {
            const btn = document.createElement('button');
            btn.className = `s-${s.value}`;
            btn.textContent = s.label;
            btn.addEventListener('click', () => {
                row.dataset.status = s.value;
                this.saveVerse(row, bookId, chapterNum, verseNum);
                this.hideStatusDropdown();
                App.updateProgress();
            });
            dropdown.appendChild(btn);
        }

        document.body.appendChild(dropdown);

        const rect = target.getBoundingClientRect();
        dropdown.style.position = 'fixed';
        dropdown.style.top = (rect.bottom + 4) + 'px';
        dropdown.style.left = rect.left + 'px';

        this.activeDropdown = dropdown;
    },

    hideStatusDropdown() {
        if (this.activeDropdown) {
            this.activeDropdown.remove();
            this.activeDropdown = null;
        }
    }
};
