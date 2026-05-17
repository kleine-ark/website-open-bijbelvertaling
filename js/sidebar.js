/* Open Vertaling — Sidebar boomnavigatie */

const Sidebar = {
    init() {
        this.setupToggle();
        this.setupRightToggle();
        this.setupMobileBackdrop();
        this.setupSearch();
    },

    isMobile() { return window.matchMedia('(max-width: 768px)').matches; },

    setupToggle() {
        const sidebar = document.getElementById('sidebar');
        const toggleBtn = document.getElementById('sidebar-toggle');
        const openBtn = document.getElementById('sidebar-open');
        if (!sidebar || !toggleBtn || !openBtn) return;

        const collapse = () => {
            sidebar.classList.remove('mobile-open');
            sidebar.classList.add('collapsed');
            openBtn.style.display = 'block';
            document.body.classList.toggle('drawer-open', this._anyDrawerOpen());
            if (!this.isMobile()) localStorage.setItem('sv2026_sidebarCollapsed', 'true');
        };

        const expand = () => {
            sidebar.classList.remove('collapsed');
            if (this.isMobile()) {
                sidebar.classList.add('mobile-open');
                this._closeRight();   // op mobile: andere drawer sluiten
                document.body.classList.add('drawer-open');
            } else {
                openBtn.style.display = 'none';
            }
            if (!this.isMobile()) localStorage.setItem('sv2026_sidebarCollapsed', 'false');
        };

        // Default state: desktop = open; mobile = collapsed
        if (this.isMobile()) {
            collapse();
        } else if (localStorage.getItem('sv2026_sidebarCollapsed') === 'true') {
            collapse();
        } else {
            openBtn.style.display = 'none';
        }

        toggleBtn.addEventListener('click', collapse);
        openBtn.addEventListener('click', expand);
    },

    setupRightToggle() {
        const r = document.getElementById('sidebar-right');
        const toggleBtn = document.getElementById('sidebar-right-toggle');
        const openBtn = document.getElementById('sidebar-right-open');
        if (!r || !toggleBtn || !openBtn) return;

        const collapse = () => {
            r.classList.remove('mobile-open');
            r.classList.add('collapsed');
            openBtn.style.display = 'block';
            document.body.classList.toggle('drawer-open', this._anyDrawerOpen());
            if (!this.isMobile()) localStorage.setItem('sv2026_sidebarRightCollapsed', 'true');
        };

        const expand = () => {
            r.classList.remove('collapsed');
            if (this.isMobile()) {
                r.classList.add('mobile-open');
                this._closeLeft();
                document.body.classList.add('drawer-open');
            } else {
                openBtn.style.display = 'none';
            }
            if (!this.isMobile()) localStorage.setItem('sv2026_sidebarRightCollapsed', 'false');
        };

        // Default state — bekijk eerst localStorage; daarna fallback naar
        // de class op het element zelf (HTML kan default 'collapsed' staan).
        const stored = localStorage.getItem('sv2026_sidebarRightCollapsed');
        const startsCollapsed = stored !== null
            ? stored === 'true'
            : r.classList.contains('collapsed');
        if (this.isMobile() || startsCollapsed) {
            collapse();
        } else {
            r.classList.remove('collapsed');
            openBtn.style.display = 'none';
        }

        toggleBtn.addEventListener('click', collapse);
        openBtn.addEventListener('click', expand);

        // Re-evaluate on resize
        window.addEventListener('resize', () => {
            if (this.isMobile()) {
                if (!r.classList.contains('mobile-open')) {
                    r.classList.add('collapsed');
                    openBtn.style.display = 'block';
                }
            } else {
                if (localStorage.getItem('sv2026_sidebarRightCollapsed') !== 'true') {
                    r.classList.remove('collapsed');
                    openBtn.style.display = 'none';
                }
            }
        });
    },

    setupMobileBackdrop() {
        const bd = document.getElementById('mobile-backdrop');
        if (!bd) return;
        bd.addEventListener('click', () => {
            this._closeLeft();
            this._closeRight();
        });
    },

    _closeLeft() {
        const s = document.getElementById('sidebar');
        const o = document.getElementById('sidebar-open');
        if (!s) return;
        s.classList.remove('mobile-open');
        s.classList.add('collapsed');
        if (o && this.isMobile()) o.style.display = 'block';
        document.body.classList.toggle('drawer-open', this._anyDrawerOpen());
    },
    _closeRight() {
        const r = document.getElementById('sidebar-right');
        const o = document.getElementById('sidebar-right-open');
        if (!r) return;
        r.classList.remove('mobile-open');
        r.classList.add('collapsed');
        if (o && this.isMobile()) o.style.display = 'block';
        document.body.classList.toggle('drawer-open', this._anyDrawerOpen());
    },
    _anyDrawerOpen() {
        return document.querySelector('#sidebar.mobile-open, #sidebar-right.mobile-open') !== null;
    },

    setupSearch() {
        const input = document.getElementById('book-search');
        input.addEventListener('input', () => {
            const q = input.value.toLowerCase().trim();
            document.querySelectorAll('.tree-book').forEach(book => {
                const name = book.dataset.name.toLowerCase();
                const match = !q || name.includes(q);
                book.style.display = match ? '' : 'none';
            });
            // Open alle groepen bij zoeken
            if (q) {
                document.querySelectorAll('.tree-group').forEach(g => g.classList.remove('collapsed'));
            }
        });
    },

    async renderTree() {
        const manifest = await DataLoader.loadManifest();
        const tree = document.getElementById('sidebar-tree');
        tree.innerHTML = '';

        // Boekvolgorde uit gebruikersopties (canoniek / tenach / chronologisch / auteur / lengte)
        const mode = (typeof Opties !== 'undefined' && Opties.state && Opties.state.boekvolgorde) || 'canoniek';
        const bookOrder = (typeof getBookOrderGroups === 'function')
            ? getBookOrderGroups(mode, manifest)
            : {
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

        // Maak een lookup van book id -> book object
        const bookById = {};
        for (const b of manifest.books) {
            bookById[b.id] = b;
        }

        const groups = Object.entries(bookOrder).map(([label, ids]) => ({
            label,
            books: ids.map(id => bookById[id]).filter(Boolean)
        }));

        // Voeg eventuele ontbrekende boeken toe aan de juiste groep
        const assignedIds = new Set(Object.values(bookOrder).flat());
        const unassigned = manifest.books.filter(b => !assignedIds.has(b.id));
        if (unassigned.length > 0) {
            groups.push({ label: 'Overig', books: unassigned });
        }

        for (const group of groups) {
            const books = group.books;
            if (books.length === 0) continue;

            const groupEl = document.createElement('div');
            groupEl.className = 'tree-group';

            const labelEl = document.createElement('div');
            labelEl.className = 'tree-group-label';
            labelEl.innerHTML = `<span class="arrow">▼</span> ${group.label} <span style="opacity:0.4;font-size:10px;">(${books.length})</span>`;
            labelEl.addEventListener('click', () => {
                groupEl.classList.toggle('collapsed');
            });
            groupEl.appendChild(labelEl);

            const booksContainer = document.createElement('div');
            booksContainer.className = 'tree-books';

            for (const book of books) {
                const bookEl = document.createElement('div');
                bookEl.className = 'tree-book collapsed'; // standaard ingeklapt
                bookEl.dataset.name = book.nameDutch;
                bookEl.dataset.bookId = book.id;

                const bookLabel = document.createElement('div');
                bookLabel.className = 'tree-book-label';
                bookLabel.innerHTML = `<span class="arrow">▼</span> ${book.nameDutch}`;
                bookLabel.addEventListener('click', (e) => {
                    // Toggle open/dicht
                    bookEl.classList.toggle('collapsed');
                    // Als net geopend, navigeer naar eerste hoofdstuk
                    if (!bookEl.classList.contains('collapsed') && book.chaptersIncluded.length > 0) {
                        location.hash = `#${book.id}/${book.chaptersIncluded[0]}`;
                    }
                });
                bookEl.appendChild(bookLabel);

                // Hoofdstuk-knoppen
                const chaptersEl = document.createElement('div');
                chaptersEl.className = 'tree-chapters';

                for (const ch of book.chaptersIncluded) {
                    const btn = document.createElement('button');
                    btn.className = 'tree-ch-btn';
                    const verified = App && App._isVerified ? App._isVerified(book.id, ch) : false;
                    if (!verified) {
                        btn.classList.add('unverified');
                        btn.title = 'Concept — nog niet handmatig gecontroleerd';
                    }
                    btn.textContent = ch;
                    btn.dataset.bookId = book.id;
                    btn.dataset.chapter = ch;
                    btn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        location.hash = `#${book.id}/${ch}`;
                    });
                    chaptersEl.appendChild(btn);
                }

                bookEl.appendChild(chaptersEl);
                booksContainer.appendChild(bookEl);
            }

            groupEl.appendChild(booksContainer);
            tree.appendChild(groupEl);
        }
    },

    updateActive(bookId, chapter) {
        // Boek-labels
        document.querySelectorAll('.tree-book-label').forEach(el => {
            const bookEl = el.parentElement;
            const isActive = bookEl.dataset.bookId === bookId;
            el.classList.toggle('active', isActive);
            // Open het actieve boek
            if (isActive) {
                bookEl.classList.remove('collapsed');
            }
        });

        // Hoofdstuk-knoppen
        document.querySelectorAll('.tree-ch-btn').forEach(btn => {
            const isActive = btn.dataset.bookId === bookId && parseInt(btn.dataset.chapter) === chapter;
            btn.classList.toggle('active', isActive);
        });

        // Scroll actief boek in view
        const activeLabel = document.querySelector('.tree-book-label.active');
        if (activeLabel) {
            activeLabel.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }
    },

    async markApprovedChapters(bookId) {
        const book = await DataLoader.loadBook(bookId);
        if (!book) return;

        for (const chapter of book.chapters) {
            if (chapter.verses.length > 0) {
                const allFinal = chapter.verses.every(v => v.status === 'final');
                if (allFinal) {
                    const btn = document.querySelector(`.tree-ch-btn[data-book-id="${bookId}"][data-chapter="${chapter.number}"]`);
                    if (btn) btn.classList.add('approved');
                }
            }
        }
    }
};
