/* Open Vertaling — Leesversie */

const Lees = {
    manifest: null,
    bookCache: {},
    currentBook: null,
    currentChapter: null,
    selected: new Set(),
    lastClickedVerse: null,
    touchStartX: 0,

    // Traditionele bijbelverdeling
    BOOK_ORDER: {
        'Pentateuch': ['genesis', 'exodus', 'leviticus', 'numeri', 'deuteronomium'],
        'Historische boeken': ['jozua', 'richteren', 'ruth', '1samuel', '2samuel', '1koningen', '2koningen', '1kronieken', '2kronieken', 'ezra', 'nehemia', 'esther'],
        'Poetische boeken': ['job', 'psalmen', 'spreuken', 'prediker', 'hooglied'],
        'Grote profeten': ['jesaja', 'jeremia', 'klaagliederen', 'ezechiel', 'daniel'],
        'Kleine profeten': ['hosea', 'joel', 'amos', 'obadja', 'jona', 'micha', 'nahum', 'habakuk', 'zefanja', 'haggai', 'zacharia', 'maleachi'],
        'Evangelien': ['mattheus', 'markus', 'lukas', 'johannes'],
        'Handelingen': ['handelingen'],
        'Brieven van Paulus': ['romeinen', '1korinthiers', '2korinthiers', 'galaten', 'efeziers', 'filippenzen', 'kolossenzen', '1tessalonicensen', '2tessalonicensen', '1timotheus', '2timotheus', 'titus', 'filemon'],
        'Algemene brieven': ['hebreeen', 'jakobus', '1petrus', '2petrus', '1johannes', '2johannes', '3johannes', 'judas'],
        'Openbaring': ['openbaring'],
        'Apocriefen': ['tobit', 'judith', 'estherapocrief', 'boekderwijsheid', 'jezussirach', 'baruch', 'gebedvanazaria', 'gezangindevuuroven', 'susanna', 'belenddedraak', '1makkabeeen', '2makkabeeen', '3makkabeeen', '3ezra', '4ezra', 'gebedvanmanasse'],
    },

    async init() {
        this.manifest = await this.fetchJSON('/data/books.json');
        this.buildBookById();
        this.setupEventListeners();
        this.setupAudioPlayer();
        this.restoreDarkMode();
        this.handleHash();
        window.addEventListener('hashchange', () => this.handleHash());
    },

    buildBookById() {
        this.bookById = {};
        for (const b of this.manifest.books) {
            this.bookById[b.id] = b;
        }
    },

    async fetchJSON(url) {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`Fetch failed: ${url}`);
        return res.json();
    },

    async loadBook(bookId) {
        if (this.bookCache[bookId]) return this.bookCache[bookId];
        const data = await this.fetchJSON(`/data/${bookId}.json`);
        this.bookCache[bookId] = data;
        return data;
    },

    // === Navigation ===

    handleHash() {
        const hash = location.hash.slice(1);
        if (!hash) {
            location.hash = '#genesis/1';
            return;
        }
        const [bookId, chStr] = hash.split('/');
        const chapter = parseInt(chStr) || 1;
        this.navigate(bookId, chapter);
    },

    async navigate(bookId, chapter) {
        const book = await this.loadBook(bookId);
        if (!book) return;

        this.currentBook = bookId;
        this.currentChapter = chapter;
        this.clearSelection();

        // Update nav
        document.getElementById('nav-book-name').textContent = book.nameDutch || bookId;
        this.renderChapterButtons(book);
        this.renderChapter(book, chapter);

        // Audio-speler tonen/verbergen — bookId apart doorgeven (book.id niet altijd gezet)
        this.updateAudioPlayer(bookId, book, chapter);

        // AI-concept-banner tonen voor niet-geverifieerde hoofdstukken
        this._updateVerifiedBanner(bookId, chapter);

        // Scroll to top
        window.scrollTo(0, 0);

        // Als de hash een ?v=N bevat, scroll/highlight dat vers (search-navigatie).
        if (window.Search && /[?&]v=\d+/.test(location.hash)) {
            window.Search.handleVerseHash();
        }
    },

    // === Audio-speler in reader-footer ===
    // Hardcoded lijst van hoofdstukken met voorlezing (uitbreiden naarmate
    // er meer audio-bestanden in audio/{book}/{ch}.mp3 staan).
    AUDIO_AVAILABLE: {
        genesis: [1],
        johannes: [1],
    },

    VERIFIED_CHAPTERS: {
        genesis:    [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20],
        psalmen:    [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31],
        johannes:   'all',
        handelingen:[1,2,3,4,5,6,7,8],
        markus:     [1,2],
        romeinen:   [1,2,3,4],
        '1johannes':'all',
        '2johannes':'all',
        '3johannes':'all',
        gebedvanmanasse:'all',
        filemon:    'all',
        judas:      'all',
    },

    _isVerified(bookId, chapter) {
        const v = this.VERIFIED_CHAPTERS[bookId];
        if (!v) return false;
        if (v === 'all') return true;
        return Array.isArray(v) && v.includes(chapter);
    },

    _updateVerifiedBanner(bookId, chapter) {
        let banner = document.getElementById('ai-concept-banner');
        if (this._isVerified(bookId, chapter)) {
            if (banner) banner.style.display = 'none';
            return;
        }
        if (!banner) {
            banner = document.createElement('div');
            banner.id = 'ai-concept-banner';
            banner.className = 'ai-concept-banner';
            banner.innerHTML = '<strong>⚠ Let op:</strong> AI-wijzigingen. Concept. Nog geen menselijke controle plaatsgevonden — kans op nog niet opgeloste onjuistheden.';
            const versesEl = document.getElementById('verses');
            if (versesEl && versesEl.parentNode) versesEl.parentNode.insertBefore(banner, versesEl);
        }
        banner.style.display = 'block';
    },

    async updateAudioPlayer(bookId, book, chapter) {
        const audioEl = document.getElementById('audio-el');
        const playBtn = document.getElementById('audio-play-big');
        const label   = document.getElementById('reader-footer-label');
        if (!audioEl || !playBtn) return;

        if (label) label.textContent = `${(book && book.nameDutch) || bookId} ${chapter}`;
        try { audioEl.pause(); } catch (e) {}

        const list = this.AUDIO_AVAILABLE[bookId] || [];
        if (!list.includes(chapter)) {
            playBtn.classList.add('hidden');
            audioEl.removeAttribute('src');
            return;
        }
        audioEl.src = `audio/${bookId}/${chapter}.mp3`;
        playBtn.classList.remove('is-playing');
        playBtn.classList.remove('hidden');
    },

    setupAudioPlayer() {
        const audioEl = document.getElementById('audio-el');
        const playBtn = document.getElementById('audio-play-big');
        if (!audioEl || !playBtn) return;

        playBtn.addEventListener('click', () => {
            if (audioEl.paused) audioEl.play();
            else audioEl.pause();
        });
        audioEl.addEventListener('play', () => {
            playBtn.classList.add('is-playing');
            playBtn.setAttribute('aria-label', 'Pauzeer voorlezing');
        });
        audioEl.addEventListener('pause', () => {
            playBtn.classList.remove('is-playing');
            playBtn.setAttribute('aria-label', 'Speel voorlezing af');
        });
    },

    renderChapterButtons(book) {
        const container = document.getElementById('chapter-buttons');
        container.innerHTML = '';
        const chapters = book.chapters.map(c => c.number);
        for (const ch of chapters) {
            const btn = document.createElement('button');
            btn.textContent = ch;
            btn.classList.toggle('active', ch === this.currentChapter);
            btn.classList.toggle('unverified', !this._isVerified(this.currentBook, ch));
            btn.title = this._isVerified(this.currentBook, ch) ? '' : 'Concept — nog niet handmatig gecontroleerd';
            btn.addEventListener('click', () => {
                location.hash = `#${this.currentBook}/${ch}`;
            });
            container.appendChild(btn);
        }
    },

    renderChapter(book, chapterNum) {
        const chapter = book.chapters.find(c => c.number === chapterNum);
        if (!chapter) return;

        // Heading — concept-marker bij niet-geverifieerde hoofdstukken
        const headingEl = document.getElementById('chapter-heading');
        const isVerified = this._isVerified(this.currentBook, chapterNum);
        headingEl.textContent = `${book.nameDutch} ${chapterNum}`;
        headingEl.classList.toggle('chapter-unverified', !isVerified);
        if (!isVerified) {
            const tag = document.createElement('span');
            tag.className = 'chapter-concept-tag';
            tag.textContent = 'CONCEPT — NIET GECONTROLEERD';
            headingEl.appendChild(document.createTextNode(' '));
            headingEl.appendChild(tag);
        }

        // Book intro (only chapter 1)
        const introEl = document.getElementById('book-intro');
        if (chapterNum === 1 && book.bookIntro && book.bookIntro.text2026) {
            introEl.innerHTML = `
                <span class="book-intro-label">Boekinleiding</span>
                <div class="book-intro-text">${book.bookIntro.text2026}</div>`;
            introEl.classList.remove('hidden');
            introEl.classList.add('collapsed');
            introEl.onclick = () => introEl.classList.toggle('collapsed');
        } else {
            introEl.classList.add('hidden');
        }

        // Chapter intro
        const chIntroEl = document.getElementById('chapter-intro');
        const chIntro = chapter.chapterIntro;
        if (chIntro && typeof chIntro === 'object' && chIntro.text2026) {
            chIntroEl.textContent = chIntro.text2026;
            chIntroEl.style.display = '';
        } else {
            chIntroEl.style.display = 'none';
        }

        // Verses
        const versesEl = document.getElementById('verses');
        versesEl.innerHTML = '';
        for (const verse of chapter.verses) {
            const span = document.createElement('span');
            span.className = 'verse-span';
            span.dataset.verse = verse.number;

            // Verse number
            const num = document.createElement('span');
            num.className = 'verse-num';
            num.textContent = verse.number;
            num.addEventListener('click', (e) => this.handleVerseClick(e, verse.number));
            span.appendChild(num);

            // Verse text (use text2026_html which has god-speaks + note-markers)
            const textNode = document.createElement('span');
            textNode.className = 'verse-text';
            const html = verse.text2026_html || verse.text2026 || '';
            // Add Strong's word wrapping
            textNode.innerHTML = this.wrapWordsWithStrongs(html, verse.grondtekst);
            span.appendChild(textNode);

            // Space between verses
            span.appendChild(document.createTextNode(' '));

            versesEl.appendChild(span);
        }

        // Attach note-marker click handlers
        versesEl.querySelectorAll('.note-marker').forEach(marker => {
            marker.addEventListener('click', (e) => {
                e.preventDefault();
                const verseNum = parseInt(marker.closest('.verse-span')?.dataset.verse);
                const noteId = marker.dataset.note;
                this.showNotes(chapter, verseNum, noteId);
            });
        });
    },

    wrapWordsWithStrongs(html, grondtekst) {
        if (!grondtekst || grondtekst.length === 0) return html;

        // We can't easily map Hebrew/Greek words to Dutch words positionally.
        // Instead, store the grondtekst data on the verse-span and handle
        // Strong's lookup via a modal that shows all source words for the verse.
        // This is simpler and more reliable than per-word wrapping.
        return html;
    },

    // === Notes panel ===

    showNotes(chapter, verseNum, focusNoteId) {
        const verse = chapter.verses.find(v => v.number === verseNum);
        if (!verse || !verse.marginNotes) return;

        const panel = document.getElementById('notes-panel');
        const content = document.getElementById('notes-content');

        let notesHtml = `<div class="notes-verse-ref" style="font-weight:600;margin-bottom:8px;">Vers ${verseNum}</div>`;
        for (const note of verse.marginNotes) {
            const text2026 = note.text2026 || note.text1637 || '';
            if (!text2026) continue;
            const isActive = note.marker === focusNoteId ? ' style="background:var(--selected);padding:4px 6px;border-radius:4px;"' : '';
            notesHtml += `<div class="note-item"${isActive}>
                <span class="note-item-marker">${note.marker}</span>
                ${text2026}
            </div>`;
        }

        content.innerHTML = notesHtml;
        panel.classList.remove('hidden');
    },

    // === Verse selection & copy ===

    handleVerseClick(e, verseNum) {
        const key = String(verseNum);

        if (e.shiftKey && this.lastClickedVerse != null) {
            const start = Math.min(this.lastClickedVerse, verseNum);
            const end = Math.max(this.lastClickedVerse, verseNum);
            for (let i = start; i <= end; i++) this.selected.add(String(i));
        } else if (e.ctrlKey || e.metaKey) {
            if (this.selected.has(key)) this.selected.delete(key);
            else this.selected.add(key);
        } else {
            if (this.selected.has(key) && this.selected.size === 1) {
                this.selected.clear();
            } else {
                this.selected.clear();
                this.selected.add(key);
            }
        }
        this.lastClickedVerse = verseNum;
        this.updateSelection();
    },

    clearSelection() {
        this.selected.clear();
        this.lastClickedVerse = null;
        this.updateSelection();
    },

    updateSelection() {
        document.querySelectorAll('.verse-span').forEach(span => {
            span.classList.toggle('selected', this.selected.has(span.dataset.verse));
        });
        const toolbar = document.getElementById('copy-toolbar');
        const count = this.selected.size;
        if (count > 0) {
            document.getElementById('copy-count').textContent =
                `${count} vers${count > 1 ? 'en' : ''} geselecteerd`;
            toolbar.classList.add('visible');
        } else {
            toolbar.classList.remove('visible');
        }
    },

    getSelectedVerses() {
        const spans = [...document.querySelectorAll('.verse-span')];
        return spans.filter(s => this.selected.has(s.dataset.verse));
    },

    copyVerses(withFormatting) {
        const spans = this.getSelectedVerses();
        if (spans.length === 0) return;

        const items = spans.map(span => {
            const num = span.dataset.verse;
            const clone = span.querySelector('.verse-text').cloneNode(true);
            clone.querySelectorAll('.note-marker').forEach(m => m.remove());
            return { num, clone };
        });

        if (withFormatting) {
            const html = items.map(({ num, clone }) =>
                `<b>${num}</b> ${clone.innerHTML.trim()}`
            ).join('<br>\n');
            const plain = items.map(({ num, clone }) =>
                `${num} ${clone.textContent.trim()}`
            ).join('\n');

            navigator.clipboard.write([new ClipboardItem({
                'text/html': new Blob([html], { type: 'text/html' }),
                'text/plain': new Blob([plain], { type: 'text/plain' }),
            })]).then(() => this.showCopyFeedback('Gekopieerd met opmaak'));
        } else {
            const plain = items.map(({ num, clone }) =>
                `${num} ${clone.textContent.trim()}`
            ).join('\n');
            navigator.clipboard.writeText(plain)
                .then(() => this.showCopyFeedback('Gekopieerd'));
        }
    },

    showCopyFeedback(msg) {
        const el = document.getElementById('copy-count');
        const orig = el.textContent;
        el.textContent = msg;
        el.style.color = '#27ae60';
        setTimeout(() => { el.textContent = orig; el.style.color = ''; }, 1500);
    },

    // === Book selector ===

    openBookSelector() {
        const overlay = document.getElementById('book-selector');
        const list = document.getElementById('book-list');
        list.innerHTML = '';

        for (const [groupName, ids] of Object.entries(this.BOOK_ORDER)) {
            const books = ids.map(id => this.bookById[id]).filter(Boolean);
            if (books.length === 0) continue;

            const group = document.createElement('div');
            group.className = 'book-group';

            const label = document.createElement('div');
            label.className = 'book-group-label';
            label.textContent = groupName;
            group.appendChild(label);

            const items = document.createElement('div');
            items.className = 'book-group-items';
            for (const book of books) {
                const btn = document.createElement('button');
                btn.textContent = book.nameDutch;
                btn.classList.toggle('active', book.id === this.currentBook);
                btn.addEventListener('click', () => {
                    overlay.classList.add('hidden');
                    location.hash = `#${book.id}/1`;
                });
                items.appendChild(btn);
            }
            group.appendChild(items);
            list.appendChild(group);
        }

        overlay.classList.remove('hidden');
    },

    // === Search ===
    // Verplaatst naar js/search.js (Search-module). De /api/search backend-call
    // is verwijderd — de zoekfunctie is volledig client-side via search-index.json.

    // === Dark mode ===

    toggleDarkMode() {
        document.body.classList.toggle('dark');
        localStorage.setItem('lees_dark', document.body.classList.contains('dark'));
    },

    restoreDarkMode() {
        if (localStorage.getItem('lees_dark') === 'true') {
            document.body.classList.add('dark');
        }
    },

    // === Swipe (mobile) ===

    navigateRelative(offset) {
        const bookMeta = this.bookById[this.currentBook];
        if (!bookMeta) return;
        const chapters = bookMeta.chaptersIncluded;
        const idx = chapters.indexOf(this.currentChapter);
        const newIdx = idx + offset;
        if (newIdx >= 0 && newIdx < chapters.length) {
            location.hash = `#${this.currentBook}/${chapters[newIdx]}`;
        }
    },

    // === Event listeners ===

    setupEventListeners() {
        // Book selector
        document.getElementById('nav-book-btn').addEventListener('click', () => this.openBookSelector());
        document.querySelectorAll('.overlay-close').forEach(btn => {
            btn.addEventListener('click', () => btn.closest('.overlay').classList.add('hidden'));
        });

        // Chapter arrows (top nav)
        document.getElementById('prev-ch').addEventListener('click', () => this.navigateRelative(-1));
        document.getElementById('next-ch').addEventListener('click', () => this.navigateRelative(1));
        // Footer-nav (sticky bottom)
        const rfPrev = document.getElementById('rf-prev');
        const rfNext = document.getElementById('rf-next');
        if (rfPrev) rfPrev.addEventListener('click', () => this.navigateRelative(-1));
        if (rfNext) rfNext.addEventListener('click', () => this.navigateRelative(1));

        // Keyboard nav
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT') return;
            if (e.key === 'ArrowLeft') this.navigateRelative(-1);
            if (e.key === 'ArrowRight') this.navigateRelative(1);
        });

        // Copy toolbar
        document.getElementById('copy-formatted').addEventListener('click', () => this.copyVerses(true));
        document.getElementById('copy-plain').addEventListener('click', () => this.copyVerses(false));
        document.getElementById('copy-close').addEventListener('click', () => this.clearSelection());

        // Notes panel close
        document.querySelector('.notes-close').addEventListener('click', () => {
            document.getElementById('notes-panel').classList.add('hidden');
        });

        // Dark mode
        document.getElementById('dark-mode-toggle').addEventListener('click', () => this.toggleDarkMode());

        // Search wordt nu door js/search.js (Search-module) afgehandeld.
        // De #lees-search-trigger input opent de overlay; verdere logica zit
        // in Search.init() / Search.open(). Geen oude /api/search-call meer.

        // Mobile swipe
        document.addEventListener('touchstart', (e) => {
            this.touchStartX = e.touches[0].clientX;
        }, { passive: true });
        document.addEventListener('touchend', (e) => {
            const diff = e.changedTouches[0].clientX - this.touchStartX;
            if (Math.abs(diff) > 80) {
                this.navigateRelative(diff > 0 ? -1 : 1);
            }
        }, { passive: true });

        // Mobile nav tabs
        document.querySelectorAll('.mobile-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                const action = tab.dataset.tab;
                if (action === 'bijbel') this.openBookSelector();
                if (action === 'zoek') {
                    if (window.Search) window.Search.open();
                }
                if (action === 'instellingen') this.toggleDarkMode();
            });
        });

        // Close overlays on backdrop click
        document.querySelectorAll('.overlay').forEach(overlay => {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) overlay.classList.add('hidden');
            });
        });
    },
};

document.addEventListener('DOMContentLoaded', () => Lees.init());
