/* Statenvertaling 2026 — Navigatie */

const Navigation = {
    currentBook: null,
    currentChapter: null,

    init() {
        window.addEventListener('hashchange', () => this.handleHash());
    },

    async renderBookNav() {
        const manifest = await DataLoader.loadManifest();
        const nav = document.getElementById('book-nav');
        nav.innerHTML = '';
        nav.className = 'nav-bar book-nav-grouped';

        // Traditionele bijbelverdeling
        const bookOrder = {
            'Pentateuch': ['genesis', 'exodus', 'leviticus', 'numeri', 'deuteronomium'],
            'Historische boeken': ['jozua', 'richteren', 'ruth', '1samuel', '2samuel', '1koningen', '2koningen', '1kronieken', '2kronieken', 'ezra', 'nehemia', 'esther'],
            'Poëtische boeken': ['job', 'psalmen', 'spreuken', 'prediker', 'hooglied'],
            'Grote profeten': ['jesaja', 'jeremia', 'klaagliederen', 'ezechiel', 'daniel'],
            'Kleine profeten': ['hosea', 'joel', 'amos', 'obadja', 'jona', 'micha', 'nahum', 'habakuk', 'zefanja', 'haggai', 'zacharia', 'maleachi'],
            'Apocriefen': ['3ezra', '4ezra', 'tobit', 'judith', 'boekderwijsheid', 'jezussirach', 'baruch', 'estherapocrief', 'gebedvanazaria', 'gezangindevuuroven', 'susanna', 'belenddedraak', 'gebedvanmanasse', '1makkabeeen', '2makkabeeen', '3makkabeeen'],
            'Evangeliën': ['mattheus', 'markus', 'lukas', 'johannes'],
            'Handelingen': ['handelingen'],
            'Brieven van Paulus': ['romeinen', '1korinthiers', '2korinthiers', 'galaten', 'efeziers', 'filippenzen', 'kolossenzen', '1tessalonicensen', '2tessalonicensen', '1timotheus', '2timotheus', 'titus', 'filemon'],
            'Algemene brieven': ['hebreeen', 'jakobus', '1petrus', '2petrus', '1johannes', '2johannes', '3johannes', 'judas'],
            'Openbaring': ['openbaring'],
        };

        const bookById = {};
        for (const b of manifest.books) bookById[b.id] = b;

        const addGroup = (label, books) => {
            if (books.length === 0) return;
            const group = document.createElement('div');
            group.className = 'nav-group';
            const lbl = document.createElement('span');
            lbl.className = 'nav-group-label';
            lbl.textContent = label;
            group.appendChild(lbl);
            for (const book of books) {
                const btn = document.createElement('button');
                btn.textContent = book.nameDutch;
                btn.dataset.bookId = book.id;
                btn.addEventListener('click', () => {
                    const firstCh = book.chaptersIncluded[0];
                    location.hash = `#${book.id}/${firstCh}`;
                });
                group.appendChild(btn);
            }
            nav.appendChild(group);
        };

        for (const [label, ids] of Object.entries(bookOrder)) {
            const books = ids.map(id => bookById[id]).filter(Boolean);
            addGroup(label, books);
        }
        // Eventuele ontbrekende boeken
        const assignedIds = new Set(Object.values(bookOrder).flat());
        const unassigned = manifest.books.filter(b => !assignedIds.has(b.id));
        if (unassigned.length > 0) addGroup('Overig', unassigned);
    },

    async renderChapterNav(bookId) {
        const manifest = await DataLoader.loadManifest();
        const bookMeta = manifest.books.find(b => b.id === bookId);
        if (!bookMeta) return;

        const nav = document.getElementById('chapter-nav');
        nav.innerHTML = '';
        nav.className = 'nav-bar';

        // Laad boekdata om status per hoofdstuk te bepalen
        const book = await DataLoader.loadBook(bookId);

        for (const ch of bookMeta.chaptersIncluded) {
            const btn = document.createElement('button');
            btn.textContent = ch;
            btn.dataset.chapter = ch;
            btn.addEventListener('click', () => {
                location.hash = `#${bookId}/${ch}`;
            });

            // Groen kleuren als alle verzen "final" zijn
            if (book) {
                const chapter = book.chapters.find(c => c.number === ch);
                if (chapter && chapter.verses.length > 0) {
                    const allFinal = chapter.verses.every(v => v.status === 'final');
                    if (allFinal) btn.classList.add('chapter-approved');
                }
            }

            nav.appendChild(btn);
        }
    },

    updateActiveButtons() {
        // Book buttons
        document.querySelectorAll('#book-nav button').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.bookId === this.currentBook);
        });
        // Chapter buttons
        document.querySelectorAll('#chapter-nav button').forEach(btn => {
            btn.classList.toggle('active', parseInt(btn.dataset.chapter) === this.currentChapter);
        });
    },

    async handleHash() {
        const hash = location.hash.slice(1); // verwijder #
        if (!hash) {
            // Default: eerste boek, eerste hoofdstuk
            const manifest = await DataLoader.loadManifest();
            if (manifest.books.length > 0) {
                const first = manifest.books[0];
                location.hash = `#${first.id}/${first.chaptersIncluded[0]}`;
            }
            return;
        }

        const parts = hash.split('/');
        const bookId = parts[0];
        const chapter = parseInt(parts[1]) || 1;

        if (bookId !== this.currentBook) {
            this.currentBook = bookId;
            await this.renderChapterNav(bookId);
        }
        this.currentChapter = chapter;
        this.updateActiveButtons();

        // Synchroniseer sidebar
        if (typeof Sidebar !== 'undefined') {
            Sidebar.updateActive(bookId, chapter);
            Sidebar.markApprovedChapters(bookId);
        }

        // Laad en render het hoofdstuk
        await App.renderChapter(bookId, chapter);

        // Scroll naar boven bij navigatie
        window.scrollTo(0, 0);
    },

    navigateRelative(offset) {
        if (!this.currentBook) return;
        const chapterBtns = document.querySelectorAll('#chapter-nav button');
        const chapters = Array.from(chapterBtns).map(b => parseInt(b.dataset.chapter));
        const idx = chapters.indexOf(this.currentChapter);
        const newIdx = idx + offset;
        if (newIdx >= 0 && newIdx < chapters.length) {
            location.hash = `#${this.currentBook}/${chapters[newIdx]}`;
        }
    }
};
