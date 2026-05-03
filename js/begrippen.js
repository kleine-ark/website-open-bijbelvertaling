/* Begrippenlijst — klikbare woorden met popup uitleg */

const Begrippen = {
    data: null,
    loaded: false,
    active: false,
    lookup: {},  // woord (lowercase) -> begrip object
    encyclopedieMapping: null,  // NL woord -> EN key voor encyclopedie

    async ensureLoaded() {
        if (this.loaded) return;
        try {
            // Bepaal welk boek geladen is
            const bookId = Navigation?.currentBook || 'genesis';
            // Laad PARALLEL: boek-specifieke lijst + cross-boek encyclopedie-supplement
            const [bookResp, supplResp] = await Promise.all([
                fetch(`data/begrippenlijst-${bookId}.json`),
                fetch('data/encyclopedie_nl_begrippen.json'),
            ]);
            this.data = bookResp.ok ? await bookResp.json() : [];
            this.supplement = supplResp.ok ? await supplResp.json() : [];
            this.buildLookup();
            await this.loadEncyclopedieMapping();
            this.loaded = true;
        } catch (e) {
            console.warn('Begrippenlijst laden mislukt:', e);
            this.data = [];
            this.supplement = [];
            this.loaded = true;
        }
    },

    buildLookup() {
        // Twee niveaus: caseLookup (exacte case voor woorden waar dat ertoe doet,
        // bv. 'Geest' = Heilige Geest vs 'geest' = nieuwe mens) en lookup (lowercase fallback).
        this.lookup = {};
        this.caseLookup = {};
        // Eerst supplement (cross-boek)
        for (const item of this.supplement || []) {
            this.caseLookup[item.woord] = item;
            this.lookup[item.woord.toLowerCase()] = item;
            if (item.ook) for (const alt of item.ook) {
                this.caseLookup[alt] = item;
                this.lookup[alt.toLowerCase()] = item;
            }
        }
        // Dan boek-specifiek (overschrijft supplement)
        for (const item of this.data || []) {
            this.caseLookup[item.woord] = item;
            this.lookup[item.woord.toLowerCase()] = item;
            if (item.ook) for (const alt of item.ook) {
                this.caseLookup[alt] = item;
                this.lookup[alt.toLowerCase()] = item;
            }
        }
    },

    // Vind een begrip met case-sensitive prioriteit, fallback naar lowercase
    findItem(word) {
        if (this.caseLookup && this.caseLookup[word]) return this.caseLookup[word];
        return this.lookup[word.toLowerCase()] || null;
    },

    async loadEncyclopedieMapping() {
        if (this.encyclopedieMapping) return;
        try {
            const resp = await fetch('data/encyclopedie-mapping.json');
            if (resp.ok) {
                this.encyclopedieMapping = await resp.json();
            } else {
                this.encyclopedieMapping = {};
            }
        } catch (e) {
            console.warn('Encyclopedie-mapping laden mislukt:', e);
            this.encyclopedieMapping = {};
        }
    },

    async toggle(on) {
        this.active = on;
        if (on) {
            await this.ensureLoaded();
            this.highlightWords();
        } else {
            this.removeHighlights();
            this.hidePopover();
        }
    },

    highlightWords() {
        if (!this.data || this.data.length === 0) return;

        // Bouw een regex van alle bekende woorden (langste eerst)
        const words = Object.keys(this.lookup).sort((a, b) => b.length - a.length);
        if (words.length === 0) return;

        // Verwerk elke verse-cell col-2026
        const cells = document.querySelectorAll('.col-2026');
        cells.forEach(cell => {
            if (cell.dataset.begrippenApplied) return;
            this.wrapWordsInCell(cell, words);
            cell.dataset.begrippenApplied = 'true';
        });
    },

    wrapWordsInCell(cell, words) {
        // Loop door alle text nodes in de cel
        const walker = document.createTreeWalker(cell, NodeFilter.SHOW_TEXT);
        const textNodes = [];
        while (walker.nextNode()) textNodes.push(walker.currentNode);

        for (const node of textNodes) {
            const text = node.textContent;
            if (!text.trim()) continue;

            // Check of er bekende woorden in zitten
            let hasMatch = false;
            for (const w of words) {
                const regex = new RegExp(`\\b${w}\\b`, 'i');
                if (regex.test(text)) {
                    hasMatch = true;
                    break;
                }
            }
            if (!hasMatch) continue;

            // Bouw een pattern van alle woorden
            const escaped = words.map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
            const pattern = new RegExp(`\\b(${escaped.join('|')})\\b`, 'gi');

            const parts = text.split(pattern);
            if (parts.length <= 1) continue;

            const frag = document.createDocumentFragment();
            for (const part of parts) {
                if (this.findItem(part)) {
                    const span = document.createElement('span');
                    span.className = 'begrip-link';
                    span.textContent = part;
                    span.addEventListener('click', (e) => {
                        e.stopPropagation();
                        this.showPopover(part, e.target);
                    });
                    frag.appendChild(span);
                } else {
                    frag.appendChild(document.createTextNode(part));
                }
            }
            node.parentNode.replaceChild(frag, node);
        }
    },

    removeHighlights() {
        document.querySelectorAll('.begrip-link').forEach(span => {
            const text = document.createTextNode(span.textContent);
            span.parentNode.replaceChild(text, span);
        });
        document.querySelectorAll('.col-2026').forEach(cell => {
            delete cell.dataset.begrippenApplied;
        });
    },

    showPopover(word, anchorEl) {
        const item = this.findItem(word);
        if (!item) return;

        const pop = document.getElementById('begrip-popover');
        document.getElementById('begrip-woord').textContent = item.woord;

        const catLabels = {
            'persoon': 'Persoon',
            'plaats': 'Plaats',
            'volk': 'Volk',
            'begrip': 'Begrip',
            'overig': 'Overig'
        };
        document.getElementById('begrip-cat').textContent = catLabels[item.categorie] || item.categorie;
        document.getElementById('begrip-uitleg').textContent = item.uitleg;
        // Klikbare ref (geen "Eerste vermelding" label meer)
        const refEl = document.getElementById('begrip-ref');
        if (item.ref) {
            refEl.innerHTML = `<a href="#" class="begrip-ref-link" data-ref="${item.ref}">${item.ref}</a>`;
            const a = refEl.querySelector('a');
            a.onclick = (e) => { e.preventDefault(); this.gotoRef(item.ref); };
        } else {
            refEl.textContent = '';
        }

        // Encyclopedie link
        const encLink = document.getElementById('begrip-encyclopedie');
        const mapping = this.encyclopedieMapping || {};
        const enKey = mapping[item.woord];
        if (enKey) {
            encLink.href = `begrippen.html#${encodeURIComponent(enKey)}`;
            encLink.textContent = 'Lees meer in encyclopedie \u2192';
            encLink.style.display = 'block';
        } else {
            encLink.href = `begrippen.html#${encodeURIComponent(item.woord)}`;
            encLink.textContent = 'Zoek in encyclopedie \u2192';
            encLink.style.display = 'block';
        }

        const rect = anchorEl.getBoundingClientRect();
        pop.style.left = Math.min(rect.left + window.scrollX, window.innerWidth - 370) + 'px';
        pop.style.top = (rect.bottom + window.scrollY + 6) + 'px';
        pop.style.display = 'block';

        const close = (e) => {
            if (!pop.contains(e.target) && e.target !== anchorEl) {
                pop.style.display = 'none';
                document.removeEventListener('click', close);
            }
        };
        setTimeout(() => document.addEventListener('click', close), 10);
    },

    hidePopover() {
        document.getElementById('begrip-popover').style.display = 'none';
    },

    /** Navigate naar de vers-ref. Sluit popover. */
    gotoRef(ref) {
        const m = ref.match(/^([123]\s)?([A-Za-zé]+)\.?\s+(\d+)(?::(\d+))?/);
        if (!m) return;
        const prefix = (m[1] || '').trim();
        const book = m[2].toLowerCase();
        const ch = m[3];
        const SLUG = {
            gen:'genesis',ex:'exodus',lev:'leviticus',num:'numeri',deut:'deuteronomium',
            joz:'jozua',richt:'richteren',ruth:'ruth',
            '1 sam':'1samuel','2 sam':'2samuel','1 kon':'1koningen','2 kon':'2koningen',
            '1 kron':'1kronieken','2 kron':'2kronieken',ezra:'ezra',neh:'nehemia',esth:'esther',
            job:'job',ps:'psalmen',psa:'psalmen',psalm:'psalmen',
            spr:'spreuken',pred:'prediker',hoogl:'hooglied',
            jes:'jesaja',jer:'jeremia',klaagl:'klaagliederen',ezech:'ezechiel',ez:'ezechiel',
            dan:'daniel',hos:'hosea',joel:'joel','joël':'joel',amos:'amos',obad:'obadja',
            jona:'jona',micha:'micha',mi:'micha',nah:'nahum',hab:'habakuk',zef:'zefanja',
            hag:'haggai',hagg:'haggai',zach:'zacharia',mal:'maleachi',
            mat:'mattheus',matt:'mattheus',mt:'mattheus',mark:'markus',mk:'markus',
            luk:'lukas',lk:'lukas',luc:'lukas',joh:'johannes',hand:'handelingen',rom:'romeinen',
            '1 kor':'1korinthiers','2 kor':'2korinthiers',gal:'galaten',ef:'efeziers',
            fil:'filippenzen',filip:'filippenzen',kol:'kolossenzen',
            '1 tess':'1tessalonicensen','2 tess':'2tessalonicensen',
            '1 tim':'1timotheus','2 tim':'2timotheus',tit:'titus',filem:'filemon',
            hebr:'hebreeen',heb:'hebreeen',jak:'jakobus',
            '1 petr':'1petrus','2 petr':'2petrus',
            '1 joh':'1johannes','2 joh':'2johannes','3 joh':'3johannes',
            jud:'judas',op:'openbaring',openb:'openbaring',
        };
        const key = (prefix ? prefix + ' ' : '') + book;
        const slug = SLUG[key] || SLUG[book];
        if (!slug) return;
        this.hidePopover();
        location.hash = `#${slug}/${ch}`;
    },

    // Herlaad bij boekwissel — supplement caching behouden
    async reload(bookId) {
        this.loaded = false;
        this.data = null;
        this.lookup = {};
        this.removeHighlights();
        if (this.active) {
            await this.ensureLoaded();
            this.highlightWords();
        }
    }
};
