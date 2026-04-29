/* Statenvertaling 2026 — Data laden en mergen */

const DataLoader = {
    cache: {},
    manifest: null,

    async loadManifest() {
        if (this.manifest) return this.manifest;
        const resp = await fetch('data/books.json?v=' + Date.now());
        this.manifest = await resp.json();
        return this.manifest;
    },

    async loadBook(bookId) {
        if (this.cache[bookId]) return this.cache[bookId];

        const manifest = await this.loadManifest();
        const bookMeta = manifest.books.find(b => b.id === bookId);
        if (!bookMeta) return null;

        const resp = await fetch(`data/${bookMeta.file}?v=` + Date.now());
        const data = await resp.json();

        // Merge localStorage edits
        const edits = Storage.getEdits(bookId);
        if (edits) this.mergeEdits(data, edits);

        this.cache[bookId] = data;
        return data;
    },

    mergeEdits(bookData, edits) {
        for (const [key, edit] of Object.entries(edits)) {
            const [ch, vs] = key.split(':').map(Number);
            const chapter = bookData.chapters.find(c => c.number === ch);
            if (!chapter) continue;
            const verse = chapter.verses.find(v => v.number === vs);
            if (!verse) continue;

            // Kanttekeningen hertaald apart mergen
            if (edit.marginNotes && verse.marginNotes) {
                for (const [idx, text2026] of Object.entries(edit.marginNotes)) {
                    if (verse.marginNotes[parseInt(idx)]) {
                        verse.marginNotes[parseInt(idx)].text2026 = text2026;
                    }
                }
                const rest = { ...edit };
                delete rest.marginNotes;
                Object.assign(verse, rest);
            } else {
                Object.assign(verse, edit);
            }
        }
    },

    invalidateCache(bookId) {
        delete this.cache[bookId];
    }
};
