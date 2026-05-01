/* Open Vertaling — Mobiele navigatie (≤768px)
 *
 * Vervangt de sidebar-driehoekjes op mobiel door:
 *   - boek-dropdown (links)  → kies boek (gegroepeerd OT/NT/Apocrief)
 *   - hoofdstuk-dropdown (midden) → kies hoofdstuk
 *   - opties-knop (rechts) → opent #sidebar-right als drawer
 *   - footer met ◀ vorig | "Boek X / Y" | volgend ▶
 *
 * Desktop (>768px) blijft ongewijzigd: CSS verbergt deze elementen.
 */

const MobileNav = {
    inited: false,
    booksByGroup: null,         // [{label, books: [...]}]
    bookById: null,             // id -> book meta

    isMobile() { return window.matchMedia('(max-width: 768px)').matches; },

    BOOK_GROUPS: [
        ['Pentateuch', ['genesis', 'exodus', 'leviticus', 'numeri', 'deuteronomium']],
        ['Historische boeken', ['jozua','richteren','ruth','1samuel','2samuel','1koningen','2koningen','1kronieken','2kronieken','ezra','nehemia','esther']],
        ['Poëtische boeken', ['job','psalmen','spreuken','prediker','hooglied']],
        ['Grote profeten', ['jesaja','jeremia','klaagliederen','ezechiel','daniel']],
        ['Kleine profeten', ['hosea','joel','amos','obadja','jona','micha','nahum','habakuk','zefanja','haggai','zacharia','maleachi']],
        ['Apocriefen', ['3ezra','4ezra','tobit','judith','boekderwijsheid','jezussirach','baruch','estherapocrief','gebedvanazaria','gezangindevuuroven','susanna','belenddedraak','gebedvanmanasse','1makkabeeen','2makkabeeen','3makkabeeen']],
        ['Evangeliën', ['mattheus','markus','lukas','johannes']],
        ['Handelingen', ['handelingen']],
        ['Brieven van Paulus', ['romeinen','1korinthiers','2korinthiers','galaten','efeziers','filippenzen','kolossenzen','1tessalonicensen','2tessalonicensen','1timotheus','2timotheus','titus','filemon']],
        ['Algemene brieven', ['hebreeen','jakobus','1petrus','2petrus','1johannes','2johannes','3johannes','judas']],
        ['Openbaring', ['openbaring']],
    ],

    pickerMode: null,           // 'books' | 'chapters'
    pickerBookId: null,         // boek waarvoor we hoofdstukken tonen

    async init() {
        if (this.inited) return;
        this.inited = true;

        const bookBtn = document.getElementById('mobile-book-btn');
        const optBtn  = document.getElementById('mobile-opties-btn');
        if (!bookBtn || !optBtn) return;

        // Manifest preloaden voor naam-mapping
        const manifest = await DataLoader.loadManifest();
        this.bookById = {};
        for (const b of manifest.books) this.bookById[b.id] = b;

        // Boek+hoofdstuk-knop opent altijd boek-overlay (kies boek → kies hoofdstuk)
        bookBtn.addEventListener('click', () => this.openPicker('books'));

        // Begrippen aan/uit toggle
        const begrBtn = document.getElementById('mobile-begrippen-btn');
        if (begrBtn) {
            begrBtn.addEventListener('click', () => {
                const on = !begrBtn.classList.contains('is-on');
                begrBtn.classList.toggle('is-on', on);
                begrBtn.setAttribute('aria-pressed', on ? 'true' : 'false');
                // Sync met desktop-checkboxen
                const cb1 = document.getElementById('toggle-begrippen');
                const cb2 = document.getElementById('quick-begrippen');
                if (cb1) cb1.checked = on;
                if (cb2) cb2.checked = on;
                if (window.Begrippen) Begrippen.toggle(on);
            });
        }

        // Overlay-controls
        document.getElementById('mp-close').addEventListener('click', () => this.closePicker());
        document.getElementById('mp-back').addEventListener('click', () => {
            if (this.pickerMode === 'chapters') this.openPicker('books');
            else this.closePicker();
        });

        // Opties-knop opent rechter sidebar als drawer
        optBtn.addEventListener('click', () => this._openOpties());

        // Reageer op hash-veranderingen
        window.addEventListener('hashchange', () => this.syncFromState());
        setTimeout(() => this.syncFromState(), 50);
    },

    openPicker(mode, bookId = null) {
        const overlay = document.getElementById('mobile-picker');
        const body    = document.getElementById('mp-body');
        const title   = document.getElementById('mp-title');
        const back    = document.getElementById('mp-back');
        if (!overlay || !body) return;
        this.pickerMode = mode;
        body.innerHTML = '';
        if (mode === 'books') {
            title.textContent = 'Kies een bijbelboek';
            back.classList.add('hidden');
            this._renderBooks(body);
        } else {
            const book = this.bookById[bookId];
            if (!book) return;
            this.pickerBookId = bookId;
            title.textContent = `${book.nameDutch} — kies hoofdstuk`;
            back.classList.remove('hidden');
            this._renderChapters(body, book);
        }
        overlay.classList.remove('hidden');
        overlay.setAttribute('aria-hidden', 'false');
        // Body-scroll blokkeren
        document.body.style.overflow = 'hidden';
    },

    closePicker() {
        const overlay = document.getElementById('mobile-picker');
        if (overlay) {
            overlay.classList.add('hidden');
            overlay.setAttribute('aria-hidden', 'true');
        }
        document.body.style.overflow = '';
        this.pickerMode = null;
    },

    _renderBooks(body) {
        const currentBook = Navigation.currentBook;
        for (const [label, ids] of this.BOOK_GROUPS) {
            const books = ids.map(id => this.bookById[id]).filter(Boolean);
            if (!books.length) continue;
            const grp = document.createElement('div');
            grp.className = 'mp-group';
            const lbl = document.createElement('div');
            lbl.className = 'mp-group-label';
            lbl.textContent = label;
            grp.appendChild(lbl);
            const list = document.createElement('div');
            list.className = 'mp-list';
            for (const b of books) {
                const item = document.createElement('button');
                item.type = 'button';
                item.className = 'mp-item' + (b.id === currentBook ? ' active' : '');
                item.textContent = b.nameDutch;
                item.addEventListener('click', () => {
                    const chapters = b.chaptersIncluded || [];
                    if (chapters.length === 1) {
                        // 1-hoofdstuk-boek: direct navigeren, picker dicht
                        location.hash = `#${b.id}/${chapters[0]}`;
                        this.closePicker();
                        setTimeout(() => this.syncFromState(), 80);
                    } else {
                        // Meerdere hoofdstukken: door naar hoofdstuk-keuze
                        this.openPicker('chapters', b.id);
                    }
                });
                list.appendChild(item);
            }
            grp.appendChild(list);
            body.appendChild(grp);
        }
    },

    _renderChapters(body, book) {
        const currentChapter = Navigation.currentChapter;
        const sameBook = (book.id === Navigation.currentBook);
        const list = document.createElement('div');
        list.className = 'mp-list mp-chapters';
        for (const ch of book.chaptersIncluded) {
            const item = document.createElement('button');
            item.type = 'button';
            item.className = 'mp-item' + (sameBook && ch === currentChapter ? ' active' : '');
            item.textContent = ch;
            item.addEventListener('click', () => {
                // Direct het topbar-label updaten zodat het niet de oude waarde
                // toont terwijl Navigation nog moet bijwerken via hashchange.
                const bookLbl = document.querySelector('#mobile-book-btn .mp-label');
                if (bookLbl) bookLbl.textContent = `${book.nameDutch} ${ch}`;
                location.hash = `#${book.id}/${ch}`;
                this.closePicker();
                // Backup: sync na korte delay (na Navigation hashchange handler)
                setTimeout(() => this.syncFromState(), 80);
            });
            list.appendChild(item);
        }
        body.appendChild(list);
    },

    async _populateBooks(sel) {
        const manifest = await DataLoader.loadManifest();

        // Hergebruik dezelfde groep-volgorde als sidebar/Navigation
        const bookOrder = {
            'Pentateuch': ['genesis', 'exodus', 'leviticus', 'numeri', 'deuteronomium'],
            'Historische boeken': ['jozua','richteren','ruth','1samuel','2samuel','1koningen','2koningen','1kronieken','2kronieken','ezra','nehemia','esther'],
            'Poëtische boeken': ['job','psalmen','spreuken','prediker','hooglied'],
            'Grote profeten': ['jesaja','jeremia','klaagliederen','ezechiel','daniel'],
            'Kleine profeten': ['hosea','joel','amos','obadja','jona','micha','nahum','habakuk','zefanja','haggai','zacharia','maleachi'],
            'Apocriefen': ['3ezra','4ezra','tobit','judith','boekderwijsheid','jezussirach','baruch','estherapocrief','gebedvanazaria','gezangindevuuroven','susanna','belenddedraak','gebedvanmanasse','1makkabeeen','2makkabeeen','3makkabeeen'],
            'Evangeliën': ['mattheus','markus','lukas','johannes'],
            'Handelingen': ['handelingen'],
            'Brieven van Paulus': ['romeinen','1korinthiers','2korinthiers','galaten','efeziers','filippenzen','kolossenzen','1tessalonicensen','2tessalonicensen','1timotheus','2timotheus','titus','filemon'],
            'Algemene brieven': ['hebreeen','jakobus','1petrus','2petrus','1johannes','2johannes','3johannes','judas'],
            'Openbaring': ['openbaring'],
        };

        this.bookById = {};
        for (const b of manifest.books) this.bookById[b.id] = b;

        sel.innerHTML = '';
        // placeholder
        const ph = document.createElement('option');
        ph.value = '';
        ph.textContent = 'Kies boek…';
        ph.disabled = true;
        ph.selected = true;
        sel.appendChild(ph);

        for (const [label, ids] of Object.entries(bookOrder)) {
            const books = ids.map(id => this.bookById[id]).filter(Boolean);
            if (books.length === 0) continue;
            const og = document.createElement('optgroup');
            og.label = label;
            for (const b of books) {
                const o = document.createElement('option');
                o.value = b.id;
                o.textContent = b.nameDutch;
                og.appendChild(o);
            }
            sel.appendChild(og);
        }
        // Eventuele ontbrekende boeken
        const assigned = new Set(Object.values(bookOrder).flat());
        const rest = manifest.books.filter(b => !assigned.has(b.id));
        if (rest.length > 0) {
            const og = document.createElement('optgroup');
            og.label = 'Overig';
            for (const b of rest) {
                const o = document.createElement('option');
                o.value = b.id;
                o.textContent = b.nameDutch;
                og.appendChild(o);
            }
            sel.appendChild(og);
        }
    },

    _populateChapters(bookId, currentChapter) {
        const sel = document.getElementById('mobile-chapter-select');
        if (!sel) return;
        const book = this.bookById && this.bookById[bookId];
        if (!book) { sel.innerHTML = ''; return; }
        sel.innerHTML = '';
        for (const ch of book.chaptersIncluded) {
            const o = document.createElement('option');
            o.value = ch;
            o.textContent = ch;
            if (ch === currentChapter) o.selected = true;
            sel.appendChild(o);
        }
    },

    syncFromState() {
        if (!this.bookById) return;
        const bookId = Navigation.currentBook;
        const ch = Navigation.currentChapter;
        if (!bookId) return;
        const book = this.bookById[bookId];

        // Knop-label updaten — combineer boek + hoofdstuk in één label
        const bookLbl = document.querySelector('#mobile-book-btn .mp-label');
        if (bookLbl && book) bookLbl.textContent = `${book.nameDutch} ${ch}`;

        // Footer-label "Boek X / Y"
        const label = document.getElementById('mobile-chapter-label');
        if (label && book) {
            const total = book.chaptersIncluded.length;
            label.textContent = `${book.nameDutch} ${ch} / ${total}`;
        }

        // Disable prev/next aan de uiteinden
        const prev = document.getElementById('mobile-prev-btn');
        const next = document.getElementById('mobile-next-btn');
        if (book && prev && next) {
            const idx = book.chaptersIncluded.indexOf(ch);
            prev.disabled = (idx <= 0);
            next.disabled = (idx < 0 || idx >= book.chaptersIncluded.length - 1);
        }
    },

    _openOpties() {
        // Mimic Sidebar's expand-rechts pad: voeg mobile-open toe + drawer-open op body
        const r = document.getElementById('sidebar-right');
        if (!r) return;
        r.classList.remove('collapsed');
        r.classList.add('mobile-open');
        document.body.classList.add('drawer-open');
        // Sluit links indien open
        const s = document.getElementById('sidebar');
        if (s) { s.classList.remove('mobile-open'); s.classList.add('collapsed'); }
    },
};

document.addEventListener('DOMContentLoaded', () => {
    // Wacht een tick zodat App.init() en Navigation.init() klaar zijn met manifest-laden
    setTimeout(() => MobileNav.init(), 0);
});
