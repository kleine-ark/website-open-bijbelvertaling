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
            const resp = await fetch(`data/begrippenlijst-${bookId}.json`);
            if (!resp.ok) {
                console.warn(`Geen begrippenlijst voor ${bookId}`);
                this.data = [];
                this.loaded = true;
                return;
            }
            this.data = await resp.json();
            this.buildLookup();
            await this.loadEncyclopedieMapping();
            this.loaded = true;
        } catch (e) {
            console.warn('Begrippenlijst laden mislukt:', e);
            this.data = [];
            this.loaded = true;
        }
    },

    buildLookup() {
        this.lookup = {};
        for (const item of this.data) {
            this.lookup[item.woord.toLowerCase()] = item;
            // Voeg ook alternatieve namen toe
            if (item.ook) {
                for (const alt of item.ook) {
                    this.lookup[alt.toLowerCase()] = item;
                }
            }
        }
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
                if (this.lookup[part.toLowerCase()]) {
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
        const item = this.lookup[word.toLowerCase()];
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
        document.getElementById('begrip-ref').textContent = item.ref ? `Eerste vermelding: ${item.ref}` : '';

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

    // Herlaad bij boekwissel
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
