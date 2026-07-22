/* Open Vertaling — Data laden (per-chapter, na chapter-split refactor) */

const DataLoader = {
    manifest: null,                 // books.json (boeken-overzicht)
    bookManifestCache: {},          // bookId -> book-manifest (zonder verzen)
    chapterCache: {},               // `${bookId}:${ch}` -> chapter-data
    cache: {},                      // bookId -> 'pseudo full book' (voor backwards-compat)
    MAX_CHAPTERS_CACHED: 30,
    _chapterCacheOrder: [],         // LRU

    async loadManifest() {
        if (this.manifest) return this.manifest;
        const resp = await fetch('data/books.json');
        this.manifest = await resp.json();
        return this.manifest;
    },

    /** Laadt het boek-manifest (klein, ~5KB): bookIntro + lijst chapters [{number, verseCount}]. */
    async loadBookManifest(bookId) {
        if (this.bookManifestCache[bookId]) return this.bookManifestCache[bookId];
        const m = await this.loadManifest();
        const bookMeta = m.books.find(b => b.id === bookId);
        if (!bookMeta) return null;
        const resp = await fetch(`data/${bookMeta.file}`);
        const bm = await resp.json();
        this.bookManifestCache[bookId] = bm;
        return bm;
    },

    /** Laadt 1 hoofdstuk en merget localStorage-edits. */
    async loadChapter(bookId, chapterNum) {
        const key = `${bookId}:${chapterNum}`;
        if (this.chapterCache[key]) {
            // bump LRU
            const idx = this._chapterCacheOrder.indexOf(key);
            if (idx >= 0) this._chapterCacheOrder.splice(idx, 1);
            this._chapterCacheOrder.push(key);
            return this.chapterCache[key];
        }
        const resp = await fetch(`data/${bookId}/${chapterNum}.json`);
        if (!resp.ok) return null;
        const ch = await resp.json();

        // Merge localStorage edits voor deze chapter
        const edits = (typeof Storage !== 'undefined') ? Storage.getEdits(bookId) : null;
        if (edits) this._mergeChapterEdits(ch, edits, chapterNum);

        this.chapterCache[key] = ch;
        this._chapterCacheOrder.push(key);
        this._evictOld();
        return ch;
    },

    /** Backward-compat: bouwt 'oude' formaat dict {chapters: [...]} maar laadt LAZY.
     *  Voor code die nog zoekt via book.chapters.find(...) — die werkt mits de chapter al gecached is.
     *  Voor de hoofd-render-flow gebruiken we direct loadChapter().
     */
    async loadBook(bookId) {
        if (this.cache[bookId]) return this.cache[bookId];
        const bm = await this.loadBookManifest(bookId);
        if (!bm) return null;
        // Bouw lazy chapters-array: alleen number gevuld; verses worden ingevuld bij loadChapter
        const lazyChapters = (bm.chapters || []).map(c => ({
            number: c.number,
            verseCount: c.verseCount,
            verses: [],   // leeg — code die .length checkt werkt; status-checks krijgen 'false'
            _lazy: true,
        }));
        const book = { ...bm, chapters: lazyChapters };
        this.cache[bookId] = book;
        return book;
    },

    /** Pre-fetch buurchapters bij idle — geeft instant volgende-chapter klik. */
    prefetchAdjacent(bookId, chapterNum) {
        const fn = () => {
            [chapterNum - 1, chapterNum + 1].forEach(n => {
                if (n >= 1) {
                    const key = `${bookId}:${n}`;
                    if (!this.chapterCache[key]) {
                        this.loadChapter(bookId, n).catch(() => {});
                    }
                }
            });
        };
        if ('requestIdleCallback' in window) {
            requestIdleCallback(fn, { timeout: 2000 });
        } else {
            setTimeout(fn, 500);
        }
    },

    _mergeChapterEdits(chapter, edits, chapterNum) {
        for (const [key, edit] of Object.entries(edits)) {
            const [ch, vs] = key.split(':').map(Number);
            if (ch !== chapterNum) continue;
            const verse = (chapter.verses || []).find(v => v.number === vs);
            if (!verse) continue;
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

    _evictOld() {
        while (this._chapterCacheOrder.length > this.MAX_CHAPTERS_CACHED) {
            const oldest = this._chapterCacheOrder.shift();
            delete this.chapterCache[oldest];
        }
    },

    invalidateCache(bookId) {
        delete this.cache[bookId];
        delete this.bookManifestCache[bookId];
        // chapter-cache for this book
        for (const key of [...this._chapterCacheOrder]) {
            if (key.startsWith(bookId + ':')) {
                const idx = this._chapterCacheOrder.indexOf(key);
                if (idx >= 0) this._chapterCacheOrder.splice(idx, 1);
                delete this.chapterCache[key];
            }
        }
    }
};
