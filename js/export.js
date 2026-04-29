/* Statenvertaling 2026 — Export en Import */

const ExportImport = {
    exportBook(bookId) {
        const book = DataLoader.cache[bookId];
        if (!book) return;

        const blob = new Blob([JSON.stringify(book, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${bookId}.json`;
        a.click();
        URL.revokeObjectURL(url);
    },

    exportAllEdits() {
        const edits = Storage.exportAll();
        if (Object.keys(edits).length === 0) {
            alert('Geen bewerkingen om te exporteren.');
            return;
        }
        const blob = new Blob([JSON.stringify(edits, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'sv2026_edits.json';
        a.click();
        URL.revokeObjectURL(url);
    },

    async approveChapter(bookId, chapterNum) {
        const book = DataLoader.cache[bookId];
        if (!book) {
            alert('Boek niet geladen.');
            return;
        }

        const chapter = book.chapters.find(c => c.number === chapterNum);
        if (!chapter) {
            alert('Hoofdstuk niet gevonden.');
            return;
        }

        const now = new Date().toISOString().slice(0, 19);
        const dateStr = now.slice(0, 10);

        const definitief = {
            bookId: book.id,
            bookName: book.nameDutch,
            chapter: chapterNum,
            approvedAt: now,
            verses: chapter.verses.map(v => ({
                number: v.number,
                ref: v.ref,
                text1637: v.text1637,
                text2026: v.text2026 || '',
                text2026_html: v.text2026_html || '',
                marginNotes: v.marginNotes || [],
                grondtekst: v.grondtekst || [],
                hsv: v.hsv || '',
                nbg51: v.nbg51 || '',
                aandachtspunten: v.aandachtspunten || '',
                status: 'final'
            }))
        };

        // Download als JSON
        const blob = new Blob([JSON.stringify(definitief, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `definitief_${bookId}_h${chapterNum}_${dateStr}.json`;
        a.click();
        URL.revokeObjectURL(url);

        // Zet alle verzen op status 'final'
        for (const verse of chapter.verses) {
            verse.status = 'final';
            Storage.saveVerse(bookId, chapterNum, verse.number, {
                text2026: verse.text2026 || '',
                aandachtspunten: verse.aandachtspunten || '',
                status: 'final'
            });
        }

        // Update UI
        document.querySelectorAll('.verse-row').forEach(row => {
            row.dataset.status = 'final';
        });
        App.updateProgress();

        // Hoofdstukknop groen kleuren
        const chBtn = document.querySelector(`#chapter-nav button[data-chapter="${chapterNum}"]`);
        if (chBtn) chBtn.classList.add('chapter-approved');
    },

    async importEdits() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        input.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const text = await file.text();
            const data = JSON.parse(text);

            // Detecteer of het een edits-bestand is of een boek-bestand
            if (data.id && data.chapters) {
                // Het is een volledig boek-bestand: extraheer edits
                const edits = {};
                for (const ch of data.chapters) {
                    for (const v of ch.verses) {
                        if (v.text2026 || v.aandachtspunten || v.status !== 'empty') {
                            edits[`${ch.number}:${v.number}`] = {
                                text2026: v.text2026 || '',
                                aandachtspunten: v.aandachtspunten || '',
                                status: v.status || 'empty'
                            };
                        }
                    }
                }
                Storage.importEdits({ [data.id]: edits });
                DataLoader.invalidateCache(data.id);
            } else {
                // Het is een edits-bestand
                Storage.importEdits(data);
                // Invalidate alle caches
                for (const bookId of Object.keys(data)) {
                    DataLoader.invalidateCache(bookId);
                }
            }

            // Herlaad huidige weergave
            if (Navigation.currentBook && Navigation.currentChapter) {
                await App.renderChapter(Navigation.currentBook, Navigation.currentChapter);
            }
            alert('Bewerkingen geïmporteerd!');
        });
        input.click();
    }
};
