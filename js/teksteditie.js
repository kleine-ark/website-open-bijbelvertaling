/* Gedeelde teksteditie-laag voor OV en de genormaliseerde buitenlandse corpora. */
(function (global) {
    'use strict';
    const CODES = new Set(['nl-ov', 'nl-opv', 'fr-lsg1910', 'en-webbe', 'ar-vd', 'uk-ukrfb', 'de-luther1912', 'es-rv1909', 'pl-gdanska1881', 'tr-open-basic-nt']);
    const STORAGE_KEY = 'sv2026_vertaalopties';

    function storedCode() {
        try {
            const state = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
            return CODES.has(state.teksteditie) ? state.teksteditie : 'nl-ov';
        } catch (_) {
            return 'nl-ov';
        }
    }

    const TekstEditie = {
        _manifest: null,
        _manifestPromise: null,
        _cache: new Map(),
        code() {
            const fromUrl = new URL(location.href).searchParams.get('editie');
            return CODES.has(fromUrl) ? fromUrl : storedCode();
        },
        isDutch() { return this.code() === 'nl-ov'; },
        async manifest() {
            if (this._manifest) return this._manifest;
            if (!this._manifestPromise) {
                this._manifestPromise = Promise.all([
                    fetch('data/vertalingen/manifest.json')
                        .then(r => { if (!r.ok) throw new Error('Vertalingenmanifest ontbreekt'); return r.json(); }),
                    fetch('data/edities/manifest.json')
                        .then(r => { if (!r.ok) throw new Error('Editiesmanifest ontbreekt'); return r.json(); }),
                ]).then(([translations, editions]) => {
                    const generated = (translations.edities || []).map(item => ({
                        ...item,
                        dataRoot: item.dataRoot || `data/vertalingen/${item.code}`,
                    }));
                    const merged = { schema: 1, edities: generated.concat(editions.edities || []) };
                    merged.edities.forEach(item => CODES.add(item.code));
                    this._manifest = merged;
                    return merged;
                });
            }
            return this._manifestPromise;
        },
        async metadata(code) {
            code = code || this.code();
            if (code === 'nl-ov') return { code: 'nl-ov', naam: 'Open Vertaling', taal: 'nl', richting: 'ltr' };
            const manifest = await this.manifest();
            return manifest.edities.find(item => item.code === code) || null;
        },
        async loadChapter(bookId, chapter) {
            return this.loadChapterForEdition(this.code(), bookId, chapter);
        },
        async loadChapterForEdition(code, bookId, chapter) {
            const meta = await this.metadata(code);
            if (code === 'nl-ov') {
                const key = `${code}:${bookId}:${chapter}`;
                if (this._cache.has(key)) return this._cache.get(key);
                const response = await fetch(`data/${bookId}/${chapter}.json`);
                if (!response.ok) return { _unavailable: true, _translation: meta, boek: bookId, hoofdstuk: chapter };
                const result = await response.json();
                result._translation = meta;
                this._cache.set(key, result);
                return result;
            }
            const chapters = meta && meta.hoofdstukken && meta.hoofdstukken[bookId];
            if (!meta || !meta.boeken.includes(bookId) || (chapters && !chapters.includes(Number(chapter)))) {
                return { _unavailable: true, _translation: meta || { code, naam: code }, boek: bookId, hoofdstuk: chapter };
            }
            const key = `${code}:${bookId}:${chapter}`;
            if (this._cache.has(key)) return this._cache.get(key);
            const response = await fetch(`${meta.dataRoot}/${bookId}/${chapter}.json`);
            if (!response.ok) return { _unavailable: true, _translation: meta, boek: bookId, hoofdstuk: chapter };
            const normalized = await response.json();
            const result = this.chapterToReaderData(normalized, meta);
            this._cache.set(key, result);
            return result;
        },
        chapterToReaderData(chapter, meta) {
            return {
                schema: chapter.schema,
                editie: chapter.editie,
                boek: chapter.boek,
                number: chapter.hoofdstuk,
                _translation: meta,
                heading: chapter.kop,
                blokken: chapter.blokken || [],
                verses: (chapter.verzen || []).map(verse => ({
                    number: verse.nummer,
                    status: (verse.review && verse.review.status) || verse.status || 'external',
                    bron: verse.bron,
                    begrippen: verse.begrippen || [],
                    citaten: verse.citaten || [],
                    review: verse.review,
                    segmenten: verse.segmenten || [],
                    text1637: '', textSV1888: '',
                    text2026: verse.tekst,
                    text2026_html: verse.html || verse.tekst,
                    translationSegments: verse.segmenten || [],
                    marginNotes: (verse.voetnoten || []).map((note, index) => ({
                        marker: index + 1, type: 'footnote', text1637: '', text2026: note.tekst,
                    })),
                    crossReferences: verse.kruisverwijzingen || [],
                    grondtekst: [], phraseDiff: [],
                })),
            };
        },
        setCode(code) {
            code = CODES.has(code) ? code : 'nl-ov';
            const url = new URL(location.href);
            if (code === 'nl-ov') url.searchParams.delete('editie');
            else url.searchParams.set('editie', code);
            history.replaceState(history.state, '', url.pathname + url.search + url.hash);
            this._cache.clear();
            if (typeof DataLoader !== 'undefined' && DataLoader.invalidateAllChapters) DataLoader.invalidateAllChapters();
        },
    };

    global.TekstEditie = TekstEditie;
    global.addEventListener('storage', event => {
        if (event.key !== STORAGE_KEY) return;
        TekstEditie._cache.clear();
        if (typeof DataLoader !== 'undefined' && DataLoader.invalidateAllChapters) DataLoader.invalidateAllChapters();
        if (global.App && global.Navigation && Navigation.currentBook) {
            App.renderChapter(Navigation.currentBook, Navigation.currentChapter);
        }
    });
})(window);
