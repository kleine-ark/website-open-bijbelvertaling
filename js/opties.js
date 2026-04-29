/* Open Vertaling — Vertalingsopties (parametrische rendering) */

const Opties = {
    STORAGE_KEY: 'sv2026_vertaalopties',

    DEFAULTS: {
        godsnaam: 'ov',          // 'ov' (JAHWEH/God JAHWEH) | 'klassiek' (HEERE/HEERE God) | 'jhwh' (יהוה)
        kolomLayout: 'naast',    // 'naast' (parallelle kolom) | 'eronder' (nieuwe regel onder OV2026)
    },

    state: {},

    init() {
        const saved = localStorage.getItem(this.STORAGE_KEY);
        try {
            this.state = saved ? { ...this.DEFAULTS, ...JSON.parse(saved) } : { ...this.DEFAULTS };
        } catch (e) {
            this.state = { ...this.DEFAULTS };
        }

        // Sync radio buttons
        document.querySelectorAll('[data-optie]').forEach(input => {
            const optie = input.dataset.optie;
            input.checked = this.state[optie] === input.value;
        });

        // Pas layout-class direct toe (geen re-render nodig — pure CSS)
        this.applyLayoutClass();

        // Listen to changes
        document.querySelectorAll('[data-optie]').forEach(input => {
            input.addEventListener('change', () => {
                if (input.checked) {
                    this.state[input.dataset.optie] = input.value;
                    this.save();
                    if (input.dataset.optie === 'kolomLayout') {
                        // Layout is puur CSS-toggle — geen re-render
                        this.applyLayoutClass();
                    } else {
                        this.applyToCurrentChapter();
                    }
                }
            });
        });
    },

    applyLayoutClass() {
        const content = document.getElementById('content');
        if (!content) return;
        content.classList.remove('layout-naast', 'layout-eronder');
        const mode = this.state.kolomLayout === 'eronder' ? 'eronder' : 'naast';
        content.classList.add('layout-' + mode);
    },

    save() {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.state));
    },

    /**
     * Transformeer een OV-tekst-fragment volgens de huidige opties.
     * Werkt op zowel platte tekst als HTML — we doen alleen tekst-vervangingen
     * en blijven van HTML-tags af.
     */
    transformOV(html) {
        if (!html) return html;
        let out = html;

        // === Godsnaam ===
        if (this.state.godsnaam === 'klassiek') {
            // Volgorde belangrijk: composiet eerst
            out = this._replaceOutsideTags(out, [
                [/\bGod JAHWEH\b/g, 'de HEERE God'],
                [/\bvan JAHWEH\b/g, 'van de HEERE'],
                [/\baan JAHWEH\b/g, 'aan de HEERE'],
                [/\bvoor JAHWEH\b/g, 'voor de HEERE'],
                [/\btot JAHWEH\b/g, 'tot de HEERE'],
                [/\bdoor JAHWEH\b/g, 'door de HEERE'],
                [/\bin JAHWEH\b/g, 'in de HEERE'],
                [/\bmet JAHWEH\b/g, 'met de HEERE'],
                [/\bbij JAHWEH\b/g, 'bij de HEERE'],
                [/\bJAHWEH van de legermachten\b/g, 'de HEERE der heirscharen'],
                [/\bJAHWEH\b/g, 'HEERE'],
            ]);
        } else if (this.state.godsnaam === 'jhwh') {
            out = this._replaceOutsideTags(out, [
                [/\bGod JAHWEH\b/g, 'God יהוה'],
                [/\bJAHWEH\b/g, 'יהוה'],
            ]);
        }
        // 'ov': geen transformatie

        return out;
    },

    /**
     * Pas regex-replacements toe alleen op tekstdelen, niet binnen HTML-tags.
     */
    _replaceOutsideTags(html, pairs) {
        const tokenRegex = /(<[^>]+>)|([^<]+)/g;
        let result = '';
        let m;
        while ((m = tokenRegex.exec(html)) !== null) {
            if (m[1]) {
                result += m[1];           // HTML tag: laat staan
            } else {
                let txt = m[2];
                for (const [re, repl] of pairs) {
                    txt = txt.replace(re, repl);
                }
                result += txt;
            }
        }
        return result;
    },

    /**
     * Re-render het huidige hoofdstuk zodat opties-veranderingen direct zichtbaar zijn.
     */
    applyToCurrentChapter() {
        if (typeof Navigation !== 'undefined' && Navigation.currentBook && Navigation.currentChapter) {
            App.renderChapter(Navigation.currentBook, Navigation.currentChapter);
        } else {
            location.reload();
        }
    },
};
