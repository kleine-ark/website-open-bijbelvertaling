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
        // Multi-entry support: lookup[word] is een ARRAY van entries (homoniemen).
        // caseLookup en lookup voor case-sensitive vs lowercase fallback (Geest vs geest).
        // Boek-specifieke entries staan vóór supplement-entries (eerst getoond in popup).
        this.lookup = {};       // lowercase -> [items]
        this.caseLookup = {};   // exacte case -> [items]
        const addEntry = (key, item, store) => {
            if (!store[key]) store[key] = [];
            // Voorkom dubbel inschuiven (zelfde object referentie)
            if (!store[key].includes(item)) store[key].push(item);
        };
        // Eerst boek-specifiek (krijgt prioriteit in popup-volgorde)
        for (const item of this.data || []) {
            addEntry(item.woord, item, this.caseLookup);
            addEntry(item.woord.toLowerCase(), item, this.lookup);
            if (item.ook) for (const alt of item.ook) {
                addEntry(alt, item, this.caseLookup);
                addEntry(alt.toLowerCase(), item, this.lookup);
            }
        }
        // Dan supplement (cross-boek) — wordt erachter aangevoegd
        for (const item of this.supplement || []) {
            addEntry(item.woord, item, this.caseLookup);
            addEntry(item.woord.toLowerCase(), item, this.lookup);
            if (item.ook) for (const alt of item.ook) {
                addEntry(alt, item, this.caseLookup);
                addEntry(alt.toLowerCase(), item, this.lookup);
            }
        }
    },

    // Vind ALLE begrippen voor een woord (voor homoniemen). Eerste = hoogste prioriteit.
    findItems(word) {
        if (this.caseLookup && this.caseLookup[word]) return this.caseLookup[word];
        return this.lookup[word.toLowerCase()] || [];
    },

    // Backward-compat: vind eerste begrip
    findItem(word) {
        const items = this.findItems(word);
        return items.length > 0 ? items[0] : null;
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
        const items = this.findItems(word);
        if (!items.length) return;
        const item = items[0];   // primair (= eerste, meestal boek-specifiek)

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

        // Multi-entry render: als er meer dan 1 begrip is, toon alle als genummerde definities
        const uitlegEl = document.getElementById('begrip-uitleg');
        if (items.length > 1) {
            uitlegEl.innerHTML = '';
            items.forEach((it, idx) => {
                const div = document.createElement('div');
                div.style.cssText = idx === 0 ? '' : 'margin-top:8px;padding-top:8px;border-top:1px dashed #e5e1d8;';
                const label = it.betekenis ? it.betekenis : (catLabels[it.categorie] || it.categorie);
                div.innerHTML = `<strong style="color:var(--teal);font-size:12px;text-transform:uppercase;letter-spacing:0.04em;">${idx+1}. ${label}</strong><br>${it.uitleg}`;
                uitlegEl.appendChild(div);
            });
        } else {
            uitlegEl.textContent = item.uitleg;
        }

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
