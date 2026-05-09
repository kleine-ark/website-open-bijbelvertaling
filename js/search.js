/* Open Vertaling — Bijbeltekst-zoekfunctie
 *
 * Pure client-side. Laadt data/search-index.json lazy bij eerste open.
 * Substring-match (case-insensitive) op text2026 (fallback SV1888).
 * Categorie-filters bovenin. Resultaat: navigeert naar #book/chapter
 * en markeert het vers tijdelijk geel (.search-highlight).
 *
 * Werkt op zowel index.html (kolomtabel met .verse-row[data-verse=N])
 * als lees.html (lopende tekst met .verse-span[data-verse=N]).
 *
 * Globale API:
 *   Search.init(opts)  — wires up UI (idempotent)
 *   Search.open()      — toont overlay
 *   Search.close()     — verbergt overlay
 */

(function (global) {
    'use strict';

    const INDEX_URL = 'data/search-index.json';
    const MAX_RESULTS = 100;
    const DEBOUNCE_MS = 300;
    const HIGHLIGHT_MS = 3000;

    // Categorie-definities: ID, label, en welke boek-IDs erin zitten.
    // Default-state is "alles aan".
    const CATEGORIES = [
        { id: 'pentateuch', label: 'Pentateuch', books: ['genesis', 'exodus', 'leviticus', 'numeri', 'deuteronomium'] },
        { id: 'historisch', label: 'Historisch', books: ['jozua', 'richteren', 'ruth', '1samuel', '2samuel', '1koningen', '2koningen', '1kronieken', '2kronieken', 'ezra', 'nehemia', 'esther'] },
        { id: 'poetisch', label: 'Poëtisch', books: ['job', 'psalmen', 'spreuken', 'prediker', 'hooglied'] },
        { id: 'grote_profeten', label: 'Grote profeten', books: ['jesaja', 'jeremia', 'klaagliederen', 'ezechiel', 'daniel'] },
        { id: 'kleine_profeten', label: 'Kleine profeten', books: ['hosea', 'joel', 'amos', 'obadja', 'jona', 'micha', 'nahum', 'habakuk', 'zefanja', 'haggai', 'zacharia', 'maleachi'] },
        { id: 'apocriefen', label: 'Apocriefen', books: ['tobit', 'judith', 'estherapocrief', 'boekderwijsheid', 'jezussirach', 'baruch', 'gebedvanazaria', 'gezangindevuuroven', 'susanna', 'belenddedraak', '1makkabeeen', '2makkabeeen', '3makkabeeen', '3ezra', '4ezra', 'gebedvanmanasse'] },
        { id: 'evangelien', label: 'Evangeliën', books: ['mattheus', 'markus', 'lukas', 'johannes'] },
        { id: 'handelingen', label: 'Handelingen', books: ['handelingen'] },
        { id: 'brieven', label: 'Brieven', books: ['romeinen', '1korinthiers', '2korinthiers', 'galaten', 'efeziers', 'filippenzen', 'kolossenzen', '1tessalonicensen', '2tessalonicensen', '1timotheus', '2timotheus', 'titus', 'filemon', 'hebreeen', 'jakobus', '1petrus', '2petrus', '1johannes', '2johannes', '3johannes', 'judas'] },
        { id: 'openbaring', label: 'Openbaring', books: ['openbaring'] },
    ];

    // Canonieke boek-volgorde uit CATEGORIES (Pentateuch → Openbaring)
    function bookOrderMap() {
        const o = {};
        let i = 0;
        for (const cat of CATEGORIES) {
            for (const b of cat.books) o[b] = i++;
        }
        return o;
    }
    const BOOK_ORDER = bookOrderMap();

    function bookCategoryMap() {
        const m = {};
        for (const cat of CATEGORIES) {
            for (const b of cat.books) m[b] = cat.id;
        }
        return m;
    }
    const BOOK_TO_CAT = bookCategoryMap();

    function capitalize(s) {
        if (!s) return s;
        return s.charAt(0).toUpperCase() + s.slice(1);
    }

    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function escapeRegex(str) {
        return String(str).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    const Search = {
        index: null,                // Array<{b,c,v,t}> of null (niet geladen)
        indexLoading: null,         // Promise of null
        bookNames: {},              // bookId -> display name (uit books.json)
        enabledCategories: null,    // Set<categoryId> — null = alles
        debounceTimer: null,
        rootEl: null,
        inputEl: null,
        resultsEl: null,
        catEls: null,
        baseUrl: '',                // optionele prefix voor links
        leesMode: false,            // true voor lees.html (gebruikt lees.html als bestemming)

        async init(opts) {
            opts = opts || {};
            this.leesMode = !!opts.leesMode;

            // Books.json voor display-namen (best-effort, niet kritisch).
            this._loadBookNames().catch(() => {});

            // Bouw of herbouw overlay-DOM in de pagina.
            this._buildOverlay();
            this._wireTriggers();
            this._wireKeyboard();
            return this;
        },

        async _loadBookNames() {
            try {
                const resp = await fetch('data/books.json');
                if (!resp.ok) return;
                const data = await resp.json();
                for (const b of (data.books || [])) {
                    if (b.id) this.bookNames[b.id] = b.nameDutch || capitalize(b.id);
                }
            } catch (e) { /* fallback naar capitalize */ }
        },

        bookName(id) {
            return this.bookNames[id] || capitalize(id);
        },

        async _ensureIndex() {
            if (this.index) return this.index;
            if (this.indexLoading) return this.indexLoading;
            this.indexLoading = (async () => {
                const resp = await fetch(INDEX_URL);
                if (!resp.ok) throw new Error('Search-index laden mislukt: ' + resp.status);
                const data = await resp.json();
                // Pre-bereken lowercased text om herhaalde toLowerCase te voorkomen
                for (const e of data) e._tl = e.t.toLowerCase();
                this.index = data;
                return data;
            })();
            return this.indexLoading;
        },

        _buildOverlay() {
            // Verwijder eventuele oude overlay (van vorige init of oude markup)
            const old = document.getElementById('search-overlay');
            if (old) old.remove();

            const overlay = document.createElement('div');
            overlay.id = 'search-overlay';
            overlay.className = 'search-overlay hidden';
            overlay.setAttribute('aria-hidden', 'true');
            overlay.innerHTML = this._overlayHTML();
            document.body.appendChild(overlay);

            this.rootEl = overlay;
            this.inputEl = overlay.querySelector('#search-input');
            this.resultsEl = overlay.querySelector('#search-results');
            this.catEls = overlay.querySelectorAll('.search-cat-cb');

            // Sluiten via backdrop of close-knop
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) this.close();
            });
            const closeBtn = overlay.querySelector('.search-close');
            if (closeBtn) closeBtn.addEventListener('click', () => this.close());

            // Input: debounced render
            this.inputEl.addEventListener('input', () => {
                clearTimeout(this.debounceTimer);
                this.debounceTimer = setTimeout(() => this._render(), DEBOUNCE_MS);
            });

            // Categorie-checkboxes
            this.catEls.forEach(cb => {
                cb.addEventListener('change', () => this._render());
            });
            const selAll = overlay.querySelector('.search-cat-all');
            const selNone = overlay.querySelector('.search-cat-none');
            if (selAll) selAll.addEventListener('click', (e) => {
                e.preventDefault();
                this.catEls.forEach(cb => { cb.checked = true; });
                this._render();
            });
            if (selNone) selNone.addEventListener('click', (e) => {
                e.preventDefault();
                this.catEls.forEach(cb => { cb.checked = false; });
                this._render();
            });

            // Klik op resultaat: navigeer
            this.resultsEl.addEventListener('click', (e) => {
                const item = e.target.closest('.search-result');
                if (!item || !item.dataset.book) return;
                this._goTo(item.dataset.book, parseInt(item.dataset.ch, 10), parseInt(item.dataset.verse, 10));
            });
        },

        _overlayHTML() {
            const cats = CATEGORIES.map(c =>
                `<label class="search-cat"><input type="checkbox" class="search-cat-cb" data-cat="${c.id}" checked> ${escapeHtml(c.label)}</label>`
            ).join('');
            return `
                <div class="search-panel" role="dialog" aria-label="Zoeken in Gods Woord">
                    <div class="search-header">
                        <input type="text" id="search-input" placeholder="Zoek in Gods Woord..." autocomplete="off" autofocus>
                        <button class="search-close" aria-label="Sluiten" title="Sluiten">&times;</button>
                    </div>
                    <div class="search-categories">
                        ${cats}
                        <span class="search-cat-actions">
                            <a href="#" class="search-cat-all">alles</a> ·
                            <a href="#" class="search-cat-none">geen</a>
                        </span>
                    </div>
                    <div id="search-results" class="search-results" role="listbox"></div>
                </div>
            `;
        },

        _wireTriggers() {
            // Bestaande topnav-search-knop in index.html: vervang inline onclick
            // door directe binding. We voegen een extra handler toe; de oude
            // toggle van .hidden blijft functioneel.
            document.querySelectorAll('.topnav-search').forEach(btn => {
                btn.onclick = null;
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.open();
                });
            });
            // Lees.html: bestaande #search-input is door _buildOverlay verwijderd?
            // Nee, die zit in lees.html zelf. We laten 'm bestaan en gebruiken
            // 'm als trigger: focus → open overlay, met query overgenomen.
            const headerInput = document.getElementById('lees-search-trigger');
            if (headerInput) {
                headerInput.addEventListener('focus', () => this.open());
                headerInput.addEventListener('click', () => this.open());
            }
            // Brede zoekbalk in topnav van index.html — focus/typen opent overlay,
            // tekst wordt overgenomen in de overlay-input.
            const topnavInput = document.getElementById('topnav-search-input');
            if (topnavInput) {
                const openWithQuery = () => {
                    this.open();
                    if (this.inputEl && topnavInput.value) {
                        this.inputEl.value = topnavInput.value;
                        topnavInput.value = '';
                        this._render();
                    }
                };
                topnavInput.addEventListener('focus', () => this.open());
                topnavInput.addEventListener('click', () => this.open());
                topnavInput.addEventListener('input', openWithQuery);
            }
        },

        _wireKeyboard() {
            document.addEventListener('keydown', (e) => {
                // Cmd/Ctrl+K opent zoek
                if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                    e.preventDefault();
                    this.open();
                    return;
                }
                if (e.key === 'Escape' && this.rootEl && !this.rootEl.classList.contains('hidden')) {
                    this.close();
                }
                // "/" opent zoek (alleen buiten input-velden)
                if (e.key === '/' && !['INPUT', 'TEXTAREA'].includes((e.target.tagName || ''))) {
                    e.preventDefault();
                    this.open();
                }
            });
        },

        open() {
            if (!this.rootEl) return;
            this.rootEl.classList.remove('hidden');
            this.rootEl.setAttribute('aria-hidden', 'false');
            // Index lazy laden in achtergrond (toont placeholder zolang nog niet klaar)
            this._ensureIndex().then(() => {
                if (this.inputEl && this.inputEl.value.trim()) this._render();
                else this._renderPlaceholder('Type een woord om te zoeken in alle boeken van Gods Woord.');
            }).catch(err => {
                this._renderPlaceholder('Kon de zoek-index niet laden: ' + err.message);
            });
            setTimeout(() => this.inputEl && this.inputEl.focus(), 0);
            if (!this.inputEl.value.trim()) {
                this._renderPlaceholder(this.index
                    ? 'Type een woord om te zoeken in alle boeken van Gods Woord.'
                    : 'Index laden…');
            }
        },

        close() {
            if (!this.rootEl) return;
            this.rootEl.classList.add('hidden');
            this.rootEl.setAttribute('aria-hidden', 'true');
        },

        _renderPlaceholder(msg) {
            if (this.resultsEl) this.resultsEl.innerHTML = `<div class="search-empty">${escapeHtml(msg)}</div>`;
        },

        _activeCategories() {
            const active = new Set();
            this.catEls.forEach(cb => { if (cb.checked) active.add(cb.dataset.cat); });
            return active;
        },

        _render() {
            if (!this.index) {
                this._renderPlaceholder('Index laden…');
                return;
            }
            const q = (this.inputEl.value || '').trim();
            if (q.length < 2) {
                this._renderPlaceholder('Type minimaal 2 tekens.');
                return;
            }

            const ql = q.toLowerCase();
            const cats = this._activeCategories();
            const allMatches = [];

            for (let i = 0; i < this.index.length; i++) {
                const e = this.index[i];
                const cat = BOOK_TO_CAT[e.b];
                if (cat && !cats.has(cat)) continue;
                if (!cat && cats.size === 0) continue; // unknown book + nothing selected
                if (e._tl.indexOf(ql) === -1) continue;
                allMatches.push(e);
            }
            const totalMatches = allMatches.length;

            // Sorteer op canonieke boek-volgorde (Mattheüs vóór Markus etc.),
            // dan op hoofdstuk + vers.
            allMatches.sort((a, b) => {
                const oa = BOOK_ORDER[a.b] ?? 999;
                const ob = BOOK_ORDER[b.b] ?? 999;
                if (oa !== ob) return oa - ob;
                if (a.c !== b.c) return a.c - b.c;
                return a.v - b.v;
            });
            const results = allMatches.slice(0, MAX_RESULTS);

            if (totalMatches === 0) {
                this._renderPlaceholder(`Geen resultaten voor "${escapeHtml(q)}".`);
                return;
            }

            const re = new RegExp(escapeRegex(q), 'gi');
            const html = results.map(e => {
                const ref = `${this.bookName(e.b)} ${e.c}:${e.v}`;
                const text = escapeHtml(e.t);
                const highlighted = text.replace(re, m => `<mark>${m}</mark>`);
                // Snippet: probeer rond de match te trimmen voor lange verzen
                const snippet = this._snippet(highlighted, q);
                return `<div class="search-result" data-book="${escapeHtml(e.b)}" data-ch="${e.c}" data-verse="${e.v}" role="option" tabindex="0">
                    <div class="search-result-ref">${escapeHtml(ref)}</div>
                    <div class="search-result-text">${snippet}</div>
                </div>`;
            }).join('');

            const more = totalMatches > MAX_RESULTS
                ? `<div class="search-more">+ ${totalMatches - MAX_RESULTS} meer resultaten — verfijn je zoekopdracht</div>`
                : `<div class="search-more">${totalMatches} resultaat${totalMatches === 1 ? '' : 'en'}</div>`;

            this.resultsEl.innerHTML = html + more;
        },

        _snippet(highlightedHtml, q) {
            // Werkt op de gehighlighte string. Voor zeer lange verzen knippen
            // we rond de eerste <mark> heen voor leesbaarheid.
            const MAX = 220;
            if (highlightedHtml.length <= MAX) return highlightedHtml;
            const idx = highlightedHtml.indexOf('<mark>');
            if (idx < 0) return highlightedHtml.slice(0, MAX) + '…';
            const start = Math.max(0, idx - 60);
            const end = Math.min(highlightedHtml.length, idx + MAX - 60);
            const prefix = start > 0 ? '…' : '';
            const suffix = end < highlightedHtml.length ? '…' : '';
            // Pas op om geen tag in tweeën te knippen — schuif startgrens vooruit
            // tot na de laatste '>' voor onze startpositie als dat nodig is.
            let s = highlightedHtml.slice(start, end);
            // Repareer mogelijk afgekapte open <mark>: als er een </mark> is
            // zonder voorafgaande <mark>, plaats er een tag voor.
            if (s.indexOf('</mark>') !== -1 && s.lastIndexOf('<mark>') < s.indexOf('</mark>')) {
                s = '<mark>' + s;
            }
            // Onafgesloten <mark>: voeg sluiter toe
            const opens = (s.match(/<mark>/g) || []).length;
            const closes = (s.match(/<\/mark>/g) || []).length;
            if (opens > closes) s += '</mark>';
            return prefix + s + suffix;
        },

        _goTo(bookId, chapter, verse) {
            this.close();
            // Bouw hash. We gebruiken `?v=N` — beide pagina-types kunnen dat
            // parsen, en het bestaande hashchange in app.js/lees.js negeert
            // de querystring.
            const newHash = `#${bookId}/${chapter}?v=${verse}`;

            // Als we al op de juiste pagina + boek/hoofdstuk zitten: scroll meteen.
            const currentHash = location.hash.replace(/^#/, '').split('?')[0];
            if (currentHash === `${bookId}/${chapter}`) {
                // Force re-trigger via assignment niet nodig; gewoon scroll.
                this._scrollAndHighlight(verse);
                // Update hash zodat de query bewaard blijft (zonder scroll-jump)
                history.replaceState(null, '', newHash);
                return;
            }
            // Anders: nieuwe hash, en wacht tot pagina hoofdstuk gerenderd heeft.
            location.hash = newHash;
            // Probeer de target-versel periodiek te vinden (max 3s)
            this._scrollAndHighlightWhenReady(verse, 30);
        },

        _scrollAndHighlightWhenReady(verseNum, maxAttempts) {
            let attempts = 0;
            const tryIt = () => {
                attempts++;
                const found = this._findVerseEl(verseNum);
                if (found) {
                    this._scrollAndHighlight(verseNum);
                    return;
                }
                if (attempts < maxAttempts) {
                    setTimeout(tryIt, 100);
                }
            };
            // Eerste poging na een korte vertraging zodat hashchange-handler kan draaien
            setTimeout(tryIt, 80);
        },

        _findVerseEl(verseNum) {
            const sel = String(verseNum);
            // Algemeen: eerste element met data-verse=N (zowel .verse-row in
            // index.html als .verse-span in lees.html).
            return document.querySelector(`[data-verse="${sel}"]`);
        },

        _scrollAndHighlight(verseNum) {
            const el = this._findVerseEl(verseNum);
            if (!el) return;
            // Scroll het element naar het midden van de viewport
            try {
                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            } catch (e) {
                el.scrollIntoView();
            }
            // Markeer alle bijbehorende cellen (in tabel-layout meerdere) of de span (lees.html)
            const sel = String(verseNum);
            const targets = document.querySelectorAll(`[data-verse="${sel}"]`);
            targets.forEach(t => t.classList.add('search-highlight'));
            setTimeout(() => {
                targets.forEach(t => t.classList.remove('search-highlight'));
            }, HIGHLIGHT_MS);
        },

        // Aangeroepen door pagina's na initiële render: parse `?v=N` in hash
        // en spring naar dat vers als aanwezig.
        handleVerseHash() {
            const m = location.hash.match(/[?&]v=(\d+)/);
            if (!m) return;
            const v = parseInt(m[1], 10);
            this._scrollAndHighlightWhenReady(v, 30);
        },
    };

    global.Search = Search;
})(window);
