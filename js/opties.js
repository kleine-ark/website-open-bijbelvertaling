/* Open Vertaling — Vertalingsopties (parametrische rendering) */

const Opties = {
    STORAGE_KEY: 'sv2026_vertaalopties',

    DEFAULTS: {
        godsnaam: 'ov',          // 'ov' (JAHWEH) | 'klassiek' (HEERE) | 'jehovah' (Jehovah) | 'jhwh' (יהוה)
        kolomLayout: 'naast',    // 'naast' (parallelle kolom) | 'eronder' (nieuwe regel onder OV2026)
    },

    state: {},

    init() {
        const saved = localStorage.getItem(this.STORAGE_KEY);
        // Mobiele default: kolommen 'eronder' i.p.v. 'naast' — beter leesbaar op smal scherm
        const defaults = { ...this.DEFAULTS };
        if (window.innerWidth <= 768) defaults.kolomLayout = 'eronder';
        try {
            this.state = saved ? { ...defaults, ...JSON.parse(saved) } : { ...defaults };
        } catch (e) {
            this.state = { ...defaults };
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
            // Volgorde belangrijk: composiet eerst, daarna prep+vocatief, daarna default
            out = this._replaceOutsideTags(out, [
                [/\bGod JAHWEH\b/g, 'de HEERE God'],
                [/\bJAHWEH van de legermachten\b/g, 'de HEERE der heirscharen'],
                // Voorzetsels: "op JAHWEH" → "op de HEERE"
                [/\b(op|van|aan|voor|tot|door|in|met|bij|over|onder|naast|achter|jegens|uit|na|sinds) JAHWEH\b/gi, '$1 de HEERE'],
                // Echte vocatief alleen na "O " of "o "
                [/\b([Oo]) JAHWEH\b/g, '$1 HEERE'],
                // JAHWEH! als uitroep blijft vocatief zonder "de"
                [/\bJAHWEH!/g, 'HEERE!'],
                // Begin van zin (na . ! ? of regel-begin): "De HEERE"
                [/(^|[.!?]\s+)JAHWEH\b/g, '$1De HEERE'],
                // Default mid-zin: "de HEERE"
                [/\bJAHWEH\b/g, 'de HEERE'],
                // Cleanup: "de de HEERE" → "de HEERE" (in geval voorzetsel ontbrak)
                [/\bde de HEERE\b/g, 'de HEERE'],
                [/\bDe de HEERE\b/g, 'De HEERE'],
            ]);
        } else if (this.state.godsnaam === 'jehovah') {
            out = this._replaceOutsideTags(out, [
                [/\bGod JAHWEH\b/g, 'God Jehovah'],
                [/\bJAHWEH\b/g, 'Jehovah'],
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
