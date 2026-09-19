/* Open Vertaling — Leesversie */

const Lees = {
    // Parallelle vertalingen (optioneel te tonen onder elk vers)
    PARALLEL: [
        { key: 'arabisch', dir: 'arabisch', label: 'ع', lang: 'ar', rtl: true, ls: 'toonArabisch', btn: 'arabisch-toggle' },
        { key: 'kjv', dir: 'kjv', label: 'KJV', lang: 'en', rtl: false, ls: 'toonKJV', btn: 'kjv-toggle' },
    ],
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
        'Ethiopische boeken (buiten de canon)': ['henoch', 'jubileeen', '1meqabyan', '2meqabyan', '3meqabyan', '4baruch'],
    },

    async init() {
        await Lees._laadVerified();   // vóór het renderen van de boekenlijst
        this.manifest = await this.fetchJSON('/data/books.json');
        this.buildBookById();
        this.setupEventListeners();
        if (typeof References !== 'undefined') References.init();
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
        const res = await fetch(url, { cache: 'no-cache' });
        if (!res.ok) throw new Error(`Fetch failed: ${url}`);
        return res.json();
    },

    async loadBook(bookId) {
        if (this.bookCache[bookId]) return this.bookCache[bookId];
        const data = await this.fetchJSON(`/data/${bookId}.json`);
        this.bookCache[bookId] = data;
        return data;
    },

    // Per-hoofdstuk JSON laden — verzen zitten sinds de chapter-split (Phase 1)
    // niet meer in /data/{bookId}.json maar in /data/{bookId}/{ch}.json.
    async loadChapter(bookId, chapter) {
        const key = `${bookId}/${chapter}`;
        this.chapterCache = this.chapterCache || {};
        if (this.chapterCache[key]) return this.chapterCache[key];
        const data = await Verification.loadJSON(`/data/${bookId}/${chapter}.json`);
        if (window.CitatieUit) window.CitatieUit.hoofdstuk(data, bookId);
        if (window.OVWoordnummers) {
            const mappings = await window.OVWoordnummers.loadBookMappings(bookId);
            window.OVWoordnummers.mergeChapterMappings(data, mappings, chapter);
        }
        this.chapterCache[key] = data;
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
        await this.renderChapter(book, chapter);

        // Audio-speler tonen/verbergen — bookId apart doorgeven (book.id niet altijd gezet)
        this.updateAudioPlayer(bookId, book, chapter);

        // AI-concept-banner tonen voor niet-geverifieerde hoofdstukken
        this._updateVerifiedBanner(bookId, chapter);
        // Waarschuwing boven apocriefe boeken (de Ethiopische boeken hebben er geen)
        this._updateEthiopicBanner(book);
        // Datering (schrijftijd + oudste handschrift) bovenin
        this._updateDatingBox(book);

        // Scroll to top
        window.scrollTo(0, 0);

        // Als de hash een ?v=N bevat, scroll/highlight dat vers (search-navigatie).
        if (window.Search && /[?&]v=\d+/.test(location.hash)) {
            window.Search.handleVerseHash();
        }
    },

    // === Audio-speler in reader-footer ===
    // AUDIO_AVAILABLE leeft in js/audio-available.js (window.AUDIO_AVAILABLE) —
    // niet hier definieren. Wordt door de TTS-rollout-script bijgewerkt.

    // Zie app.js: live accountgebonden beslissingen uit de API.
    VERIFIED_CHAPTERS: {},
    _verifiedGeladen: null,

    _laadVerified() {
        return Verification.loadChapters(Lees);
    },

    _isVerified(bookId, chapter) {
        return Verification.chapterVerified(Lees, bookId, chapter);
    },

    // Boek-niveau: is élk hoofdstuk in dit boek nagekeken?
    // - array met evenveel entries als het boek hoofdstukken heeft → ja
    // - geen entry of korter array → nee (= deels of niet nagekeken)
    _isBookFullyVerified(book) {
        if (!book) return false;
        const v = this.VERIFIED_CHAPTERS[book.id];
        if (!v) return false;
        const total = (book.chaptersIncluded || []).length;
        return total > 0 && v.length >= total;
    },

    _updateVerifiedBanner(bookId, chapter) {
        VerificationDisplay.banner(bookId, chapter, true);
    },

    ...LeesRenderer,

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
            // references.js declareert `const References`; dat is geen eigenschap van window.
            let tekst = typeof References !== 'undefined'
                ? References.linkify(text2026, this.currentBook, this.currentChapter) : text2026;
            if (window.NootGrondwoorden) tekst = NootGrondwoorden.link(tekst, verse);
            notesHtml += `<div class="note-item"${isActive}>
                <span class="note-item-marker">${note.marker}</span>
                ${tekst}
            </div>`;
        }

        content.innerHTML = notesHtml;
        panel.classList.remove('hidden');
        Verification.notes(content, this.currentBook, this.currentChapter, verseNum);
    },

    // === Tekst-selectie-driven toolbar ===
    // Luistert naar browser-native selectie binnen #verses; toont onderbalk met
    // Delen / Kopiëren / Met opmaak / Op afbeelding zolang er tekst geselecteerd is.

    _setupSelectionListener() {
        if (this._selListenerSet) return;
        this._selListenerSet = true;
        // Debounce zodat we niet bij elke micro-update herrenderen
        let timer = null;
        document.addEventListener('selectionchange', () => {
            clearTimeout(timer);
            timer = setTimeout(() => this._handleSelectionChange(), 80);
        });
    },

    _handleSelectionChange() {
        const sel = window.getSelection();
        if (!sel) return;
        const text = sel.toString().trim();
        const toolbar = document.getElementById('copy-toolbar');
        if (!toolbar) return;
        // Selectie moet binnen #verses zitten
        if (!text || sel.rangeCount === 0) {
            toolbar.classList.remove('visible');
            return;
        }
        const range = sel.getRangeAt(0);
        const versesEl = document.getElementById('verses');
        if (!versesEl || !versesEl.contains(range.commonAncestorContainer)) {
            toolbar.classList.remove('visible');
            return;
        }
        // Bepaal welke verzen de selectie raakt en bouw label
        const versNums = this._getSelectedVerseNumbers(range);
        const ref = this._buildRefFromNums(versNums);
        const cnt = document.getElementById('copy-count');
        if (cnt) cnt.textContent = ref ? `${ref} geselecteerd` : `${text.length} tekens geselecteerd`;
        toolbar.classList.add('visible');
    },

    _getSelectedVerseNumbers(range) {
        const versSpans = document.querySelectorAll('.verse-span');
        const nums = [];
        versSpans.forEach(span => {
            // Een vers raakt de range als zijn DOM-positie overlapt
            if (range.intersectsNode && range.intersectsNode(span)) {
                const n = parseInt(span.dataset.verse);
                if (!isNaN(n)) nums.push(n);
            }
        });
        return nums.sort((a,b) => a - b);
    },

    _buildRefFromNums(nums) {
        if (!nums || nums.length === 0) return '';
        const book = this.bookById?.[this.currentBook];
        const name = (book && book.nameDutch) || this.currentBook;
        if (nums.length === 1) return `${name} ${this.currentChapter}:${nums[0]}`;
        const range = nums.every((n,i) => i === 0 || n === nums[i-1]+1);
        if (range) return `${name} ${this.currentChapter}:${nums[0]}-${nums[nums.length-1]}`;
        return `${name} ${this.currentChapter}:${nums.join(',')}`;
    },

    _getSelectionData() {
        const sel = window.getSelection();
        if (!sel || !sel.toString().trim()) return null;
        const range = sel.getRangeAt(0);
        const versNums = this._getSelectedVerseNumbers(range);
        const ref = this._buildRefFromNums(versNums);
        // Plain text: directe sel.toString() — clean up note-marker artefacten
        const plain = sel.toString().replace(/\s+/g, ' ').trim();
        // HTML met opmaak: clone DocumentFragment en strip note-markers
        const frag = range.cloneContents();
        frag.querySelectorAll('.note-marker, .strongs-alignment').forEach(m => m.remove());
        const div = document.createElement('div');
        div.appendChild(frag);
        const html = div.innerHTML.trim();
        return { plain, html, ref, versNums };
    },

    // === Toolbar acties — werken op de huidige browser-selectie ===

    copyPlain() {
        const data = this._getSelectionData();
        if (!data) return;
        const text = data.ref ? `${data.plain}\n\n— ${data.ref}` : data.plain;
        navigator.clipboard.writeText(text).then(() => this.showCopyFeedback('Gekopieerd'));
    },

    copyFormatted() {
        const data = this._getSelectionData();
        if (!data) return;
        const html = data.ref
            ? `${data.html}<br><br><em>— ${data.ref}</em>`
            : data.html;
        const plain = data.ref ? `${data.plain}\n\n— ${data.ref}` : data.plain;
        if (window.ClipboardItem) {
            navigator.clipboard.write([new ClipboardItem({
                'text/html': new Blob([html], { type: 'text/html' }),
                'text/plain': new Blob([plain], { type: 'text/plain' }),
            })]).then(() => this.showCopyFeedback('Gekopieerd met opmaak'));
        } else {
            navigator.clipboard.writeText(plain).then(() => this.showCopyFeedback('Gekopieerd'));
        }
    },

    async shareSelection() {
        const data = this._getSelectionData();
        if (!data) return;
        const text = data.ref
            ? `${data.plain}\n\n— ${data.ref} (Open Vertaling)`
            : data.plain;
        if (navigator.share) {
            try {
                await navigator.share({ title: data.ref || 'Open Vertaling', text, url: location.href });
                return;
            } catch (e) { if (e.name === 'AbortError') return; }
        }
        navigator.clipboard.writeText(text).then(() => this.showCopyFeedback('Gekopieerd (delen niet ondersteund)'));
    },

    selectionAsImage() {
        const data = this._getSelectionData();
        if (!data) return;
        // Render op canvas — zelfde stijl als versAsImage maar met een vrije tekst-block
        const canvas = document.getElementById('vers-image-canvas');
        const W = 1200, PAD = 80;
        canvas.width = W;
        canvas.height = 1600;
        const ctx = canvas.getContext('2d');
        const grad = ctx.createLinearGradient(0, 0, 0, canvas.height);
        grad.addColorStop(0, '#f8f4ec'); grad.addColorStop(1, '#ede4d0');
        ctx.fillStyle = grad; ctx.fillRect(0, 0, W, canvas.height);
        ctx.fillStyle = '#cba449'; ctx.fillRect(0, 0, 8, canvas.height);
        ctx.fillStyle = '#142e42';
        ctx.font = '36px Georgia, "EB Garamond", serif';
        ctx.textBaseline = 'top';

        const wrap = (text, maxW, lineH, x, y) => {
            const words = text.split(' ');
            let line = '';
            for (const word of words) {
                const test = line ? line + ' ' + word : word;
                if (ctx.measureText(test).width > maxW && line) {
                    ctx.fillText(line, x, y); y += lineH; line = word;
                } else line = test;
            }
            if (line) { ctx.fillText(line, x, y); y += lineH; }
            return y;
        };
        let y = PAD;
        y = wrap(data.plain, W - PAD * 2, 50, PAD, y) + 30;
        if (data.ref) {
            ctx.font = 'italic 26px Georgia, serif'; ctx.fillStyle = '#5a7a8a';
            ctx.fillText(`— ${data.ref}`, PAD, y); y += 38;
        }
        ctx.font = '18px "Fira Sans", sans-serif'; ctx.fillStyle = '#999';
        ctx.fillText('Open Vertaling · openvertaling.nl', PAD, y); y += 30;

        const finalH = Math.max(y + PAD, 400);
        const tmp = document.createElement('canvas');
        tmp.width = W; tmp.height = finalH;
        tmp.getContext('2d').drawImage(canvas, 0, 0);
        canvas.width = W; canvas.height = finalH;
        canvas.getContext('2d').drawImage(tmp, 0, 0);
        document.getElementById('vers-image-modal').classList.remove('hidden');
    },

    // === Verse selection & copy (oude vers-nummer-klik handler — blijft werken) ===

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
            // Maak ook een browser-native tekst-selectie van de geselecteerde verzen,
            // zodat de gebruiker direct Ctrl+C kan gebruiken.
            this._applyNativeTextSelection();
        } else {
            toolbar.classList.remove('visible');
            // Wis browser-selectie als alle verzen gedeselecteerd zijn
            const sel = window.getSelection && window.getSelection();
            if (sel) sel.removeAllRanges();
        }
    },

    _applyNativeTextSelection() {
        const spans = this.getSelectedVerses();
        if (spans.length === 0) return;
        const sel = window.getSelection && window.getSelection();
        if (!sel) return;
        sel.removeAllRanges();
        // Range over de eerste t/m laatste vers-span (gesorteerd op DOM-volgorde)
        const range = document.createRange();
        const first = spans[0];
        const last = spans[spans.length - 1];
        const firstText = first.querySelector('.verse-text');
        const lastText = last.querySelector('.verse-text');
        if (!firstText || !lastText) return;
        range.setStartBefore(firstText);
        range.setEndAfter(lastText);
        sel.addRange(range);
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

    // Bouw een leesbare ref-string ("Genesis 1:1" of "Genesis 1:1-3" of "Genesis 1:1, 3, 5")
    _buildRef() {
        const book = this.bookById?.[this.currentBook];
        const name = (book && book.nameDutch) || this.currentBook;
        const nums = [...this.selected].map(n => parseInt(n)).sort((a,b) => a-b);
        if (nums.length === 0) return `${name} ${this.currentChapter}`;
        // Detecteer aaneensluitende reeks
        let isRange = nums.length > 1 && nums.every((n, i) => i === 0 || n === nums[i-1] + 1);
        if (isRange) return `${name} ${this.currentChapter}:${nums[0]}-${nums[nums.length-1]}`;
        if (nums.length === 1) return `${name} ${this.currentChapter}:${nums[0]}`;
        return `${name} ${this.currentChapter}:${nums.join(', ')}`;
    },

    // Web Share API — werkt vooral op mobiel; valt terug op kopiëren-naar-klembord
    async shareVerses() {
        const spans = this.getSelectedVerses();
        if (spans.length === 0) return;
        const text = spans.map(span => {
            const num = span.dataset.verse;
            const clone = span.querySelector('.verse-text').cloneNode(true);
            clone.querySelectorAll('.note-marker, .strongs-alignment').forEach(m => m.remove());
            return `${num} ${clone.textContent.trim()}`;
        }).join('\n');
        const ref = this._buildRef();
        const fullText = `${text}\n\n— ${ref} (Open Vertaling)`;
        if (navigator.share) {
            try {
                await navigator.share({ title: ref, text: fullText, url: location.href });
                return;
            } catch (e) { /* user cancelled, valt door naar fallback */
                if (e.name === 'AbortError') return;
            }
        }
        // Fallback: kopieer naar klembord
        try {
            await navigator.clipboard.writeText(fullText);
            this.showCopyFeedback('Tekst naar klembord (delen niet ondersteund)');
        } catch {
            alert('Delen niet ondersteund in deze browser.');
        }
    },

    // Render geselecteerde verzen op een canvas met perkament-achtergrond
    versAsImage() {
        const spans = this.getSelectedVerses();
        if (spans.length === 0) return;
        const ref = this._buildRef();
        const verses = spans.map(span => ({
            num: span.dataset.verse,
            text: (() => {
                const c = span.querySelector('.verse-text').cloneNode(true);
                c.querySelectorAll('.note-marker, .strongs-alignment').forEach(m => m.remove());
                return c.textContent.trim().replace(/\s+/g, ' ');
            })(),
        }));

        const canvas = document.getElementById('vers-image-canvas');
        const W = 1200, PAD = 80;
        canvas.width = W;
        // Hoogte berekenen na render met dummy

        const ctx = canvas.getContext('2d');
        // Voorlopig grote hoogte; trim later
        canvas.height = 1600;

        // Achtergrond: warme perkament-gradient met goud-accent
        const grad = ctx.createLinearGradient(0, 0, 0, canvas.height);
        grad.addColorStop(0, '#f8f4ec');
        grad.addColorStop(1, '#ede4d0');
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, W, canvas.height);

        // Linker goud-band
        ctx.fillStyle = '#cba449';
        ctx.fillRect(0, 0, 8, canvas.height);

        // Tekst-stijl
        ctx.fillStyle = '#142e42';
        ctx.font = '36px Georgia, "EB Garamond", serif';
        ctx.textBaseline = 'top';

        const wrap = (text, maxW, lineH, x, y) => {
            const words = text.split(' ');
            let line = '';
            for (const word of words) {
                const test = line ? line + ' ' + word : word;
                if (ctx.measureText(test).width > maxW && line) {
                    ctx.fillText(line, x, y);
                    y += lineH;
                    line = word;
                } else {
                    line = test;
                }
            }
            if (line) { ctx.fillText(line, x, y); y += lineH; }
            return y;
        };

        let y = PAD;
        const maxW = W - PAD * 2;
        const lineH = 50;

        for (const { num, text } of verses) {
            // Versnummer in goud
            ctx.font = 'bold 28px Georgia, serif';
            ctx.fillStyle = '#cba449';
            ctx.fillText(num, PAD, y + 6);
            // Tekst in donker
            ctx.font = '36px Georgia, "EB Garamond", serif';
            ctx.fillStyle = '#142e42';
            y = wrap(text, maxW - 60, lineH, PAD + 60, y);
            y += 18;
        }
        y += 20;

        // Reference + branding onderin
        ctx.font = 'italic 26px Georgia, serif';
        ctx.fillStyle = '#5a7a8a';
        ctx.fillText(`— ${ref}`, PAD, y);
        y += 38;
        ctx.font = '18px "Fira Sans", sans-serif';
        ctx.fillStyle = '#999';
        ctx.fillText('Open Vertaling · openvertaling.nl', PAD, y);
        y += 30;

        // Trim canvas naar werkelijke hoogte
        const finalH = Math.max(y + PAD, 400);
        const tmp = document.createElement('canvas');
        tmp.width = W;
        tmp.height = finalH;
        tmp.getContext('2d').drawImage(canvas, 0, 0);
        canvas.width = W;
        canvas.height = finalH;
        canvas.getContext('2d').drawImage(tmp, 0, 0);

        // Toon modal
        document.getElementById('vers-image-modal').classList.remove('hidden');
    },

    downloadVersImage() {
        const canvas = document.getElementById('vers-image-canvas');
        const ref = this._buildRef().replace(/[^a-zA-Z0-9-]+/g, '_');
        const link = document.createElement('a');
        link.download = `${ref}.png`;
        link.href = canvas.toDataURL('image/png');
        link.click();
    },

    async shareVersImage() {
        const canvas = document.getElementById('vers-image-canvas');
        const ref = this._buildRef();
        canvas.toBlob(async (blob) => {
            if (navigator.share && navigator.canShare && navigator.canShare({ files: [new File([blob], 'vers.png', { type: 'image/png' })] })) {
                try {
                    await navigator.share({
                        title: ref,
                        files: [new File([blob], `${ref}.png`, { type: 'image/png' })],
                    });
                } catch (e) { /* user cancelled */ }
            } else {
                this.downloadVersImage();
            }
        }, 'image/png');
    },

    // === Book selector ===

    /** De hoofdstukknoppen van één boek, voor onder dat boek in de boekkeuze. */
    _bookChapterGrid(book, overlay) {
        const grid = document.createElement('div');
        grid.className = 'book-chapters';
        for (const ch of book.chaptersIncluded) {
            const knop = document.createElement('button');
            knop.textContent = ch;
            knop.setAttribute('aria-label', `${book.nameDutch} ${ch}`);
            if (ch === this.currentChapter) {
                knop.classList.add('active');
                knop.setAttribute('aria-current', 'page');
            }
            knop.addEventListener('click', () => {
                overlay.classList.add('hidden');
                location.hash = `#${book.id}/${ch}`;
            });
            grid.appendChild(knop);
        }
        return grid;
    },

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

            // Apocriefen en Ethiopische boeken: klikbare kop, standaard
            // ingeklapt. Samen zijn het bijna dertig boeken, en wie de canon
            // zoekt moet daar niet eerst langs. Staat het geopende boek er wel
            // in, dan klapt de groep open, anders zie je niet waar je bent.
            if (groupName === 'Apocriefen' || groupName === 'Ethiopische boeken (buiten de canon)') {
                group.classList.add('book-group-collapsible');
                if (!ids.includes(this.currentBook)) group.classList.add('collapsed');
                label.style.cursor = 'pointer';
                label.addEventListener('click', () => group.classList.toggle('collapsed'));
            }

            const items = document.createElement('div');
            items.className = 'book-group-items';
            for (const book of books) {
                const btn = document.createElement('button');
                btn.textContent = book.nameDutch;
                btn.classList.toggle('active', book.id === this.currentBook);
                if (!this._isBookFullyVerified(book)) {
                    btn.classList.add('book-unverified');
                    btn.title = 'Bevat hoofdstukken die nog niet vers-voor-vers zijn nagekeken';
                    const flag = document.createElement('span');
                    flag.className = 'book-flag-unverified';
                    flag.textContent = '⚠';
                    flag.setAttribute('aria-hidden', 'true');
                    btn.appendChild(flag);
                }
                if (book.id === this.currentBook && book.chaptersIncluded.length > 1) {
                    // Het geopende boek staat meteen opengeklapt: elk hoofdstuk
                    // is dan met één tik te bereiken, zonder eerst naar
                    // hoofdstuk 1 te springen. Nog eens tikken klapt het dicht.
                    const chapters = this._bookChapterGrid(book, overlay);
                    btn.setAttribute('aria-expanded', 'true');
                    btn.addEventListener('click', () => {
                        chapters.hidden = !chapters.hidden;
                        btn.setAttribute('aria-expanded', String(!chapters.hidden));
                    });
                    items.appendChild(btn);
                    items.appendChild(chapters);
                } else {
                    btn.addEventListener('click', () => {
                        overlay.classList.add('hidden');
                        location.hash = `#${book.id}/1`;
                    });
                    items.appendChild(btn);
                }
            }
            group.appendChild(items);
            list.appendChild(group);
        }

        overlay.classList.remove('hidden');
        const actief = list.querySelector('.book-group-items button.active');
        if (actief) requestAnimationFrame(() => actief.scrollIntoView({ block: 'center' }));
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

        // Copy toolbar — Delen / Kopiëren / Met opmaak / Op afbeelding
        // Werkt op browser-native tekst-selectie (drag/long-press → toolbar verschijnt onderin)
        this._setupSelectionListener();
        // mousedown op de toolbar mag de selectie niet wissen (anders is de selectie weg
        // tegen de tijd dat het click-event aankomt)
        const toolbar = document.getElementById('copy-toolbar');
        if (toolbar) toolbar.addEventListener('mousedown', (e) => e.preventDefault());
        document.getElementById('vers-share').addEventListener('click', () => this.shareSelection());
        document.getElementById('copy-plain').addEventListener('click', () => this.copyPlain());
        document.getElementById('copy-formatted').addEventListener('click', () => this.copyFormatted());
        document.getElementById('vers-image').addEventListener('click', () => this.selectionAsImage());
        document.getElementById('copy-close').addEventListener('click', () => {
            const sel = window.getSelection(); if (sel) sel.removeAllRanges();
            document.getElementById('copy-toolbar').classList.remove('visible');
        });

        // Image-modal
        document.getElementById('vers-image-download').addEventListener('click', () => this.downloadVersImage());
        document.getElementById('vers-image-share').addEventListener('click', () => this.shareVersImage());
        document.getElementById('vers-image-close').addEventListener('click', () => {
            document.getElementById('vers-image-modal').classList.add('hidden');
        });
        document.getElementById('vers-image-modal').addEventListener('click', (e) => {
            if (e.target.id === 'vers-image-modal') {
                document.getElementById('vers-image-modal').classList.add('hidden');
            }
        });

        // Notes panel close
        document.querySelector('.notes-close').addEventListener('click', () => {
            document.getElementById('notes-panel').classList.add('hidden');
        });
        // Op mobiel bedekt het notenpaneel de tekst: wie een verwijzing volgt, wil die tekst zien.
        document.getElementById('notes-panel').addEventListener('click', (e) => {
            if (e.target.closest('.ref-link') && window.matchMedia('(max-width: 768px)').matches) {
                document.getElementById('notes-panel').classList.add('hidden');
            }
        });

        // Dark mode
        document.getElementById('dark-mode-toggle').addEventListener('click', () => this.toggleDarkMode());
        (function (self) {
            Lees.PARALLEL.forEach(function (cfg) {
                var btn = document.getElementById(cfg.btn);
                if (!btn) return;
                if (localStorage.getItem(cfg.ls) === '1') btn.classList.add('on');
                btn.addEventListener('click', function () {
                    var on = localStorage.getItem(cfg.ls) === '1';
                    localStorage.setItem(cfg.ls, on ? '0' : '1');
                    btn.classList.toggle('on', !on);
                    if (self._bookObj && self.currentChapter) self.renderChapter(self._bookObj, self.currentChapter);
                });
            });
        })(this);

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
