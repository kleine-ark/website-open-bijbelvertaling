/* Open Vertaling — Vertalingsopties (parametrische rendering) */

const Opties = {
    STORAGE_KEY: 'sv2026_vertaalopties',

    DEFAULTS: {
        godsnaam: 'ov',          // 'ov' (JAHWEH) | 'klassiek' (HEERE) | 'jehovah' (Jehovah) | 'jhwh' (יהוה)
        heereNT: 'heere',        // NT-aanspreektitel (Kurios): 'heere' (OSV) | 'here' (Heere → Here)
        kolomLayout: 'naast',    // 'naast' (parallelle kolom) | 'eronder' (nieuwe regel onder OV2026)
        boekvolgorde: 'canoniek',// 'canoniek' | 'tenach' | 'chronologisch' | 'auteur' | 'lengte'
        versnummers: 'aan',      // 'aan' | 'uit'
        otSheol: 'dodenrijk',    // 'dodenrijk' (OT-context, modern) | 'hel' (SV-traditioneel)
        thema: 'auto',           // 'auto' (systeem) | 'licht' | 'donker'
        arabischeNamen: 'uit',   // 'uit' (Nederlandse namen) | 'aan' (Musa, Ibrahim, Isa …) — alleen OV-tekst
    },

    state: {},

    // Vervang-paren voor Arabische namen ([regex, translit]); lui geladen uit data/namen-arabisch.json
    _arNamen: null,

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

        // Sync radio buttons + selects
        document.querySelectorAll('[data-optie]').forEach(input => {
            const optie = input.dataset.optie;
            if (input.tagName === 'SELECT') {
                input.value = this.state[optie];
            } else {
                input.checked = this.state[optie] === input.value;
            }
        });

        // Pas layout-class direct toe (geen re-render nodig — pure CSS)
        this.applyLayoutClass();
        this.applyVerseNumbersClass();
        this.applyThemeClass();

        // Arabische namen lui laden (en, indien al ingeschakeld, hoofdstuk herrenderen)
        this.loadArabischeNamen();

        // Versnummers-checkbox (in 'Pagina & leeshulp') synchroniseren met state
        const vnCb = document.getElementById('toggle-versnummers');
        if (vnCb) vnCb.checked = this.state.versnummers !== 'uit';

        // Topnav-knop voor 1-klik thema-wissel (donker ↔ licht)
        const themeBtn = document.getElementById('topnav-theme-toggle');
        if (themeBtn) {
            themeBtn.addEventListener('click', () => {
                const cur = document.documentElement.dataset.theme === 'donker' ? 'licht' : 'donker';
                this.state.thema = cur;
                this.save();
                this.applyThemeClass();
                document.querySelectorAll('input[data-optie="thema"]').forEach(r => {
                    r.checked = (r.value === cur);
                });
            });
        }

        // Listen to changes
        document.querySelectorAll('[data-optie]').forEach(input => {
            input.addEventListener('change', () => {
                if (input.tagName === 'SELECT' || input.checked) {
                    this.state[input.dataset.optie] = input.value;
                    this.save();
                    const optie = input.dataset.optie;
                    if (optie === 'kolomLayout') {
                        this.applyLayoutClass();
                    } else if (optie === 'versnummers') {
                        // Pure CSS-toggle — geen re-render
                        this.applyVerseNumbersClass();
                    } else if (optie === 'thema') {
                        this.applyThemeClass();
                    } else if (optie === 'boekvolgorde') {
                        // Sidebar + topnav opnieuw renderen, geen hoofdstuk-rerender
                        if (typeof Sidebar !== 'undefined' && Sidebar.renderTree) Sidebar.renderTree();
                        if (typeof Navigation !== 'undefined' && Navigation.renderBookNav) Navigation.renderBookNav();
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

    applyVerseNumbersClass() {
        // Toggle een class op <body> zodat CSS de versnummers kan verbergen.
        document.body.classList.toggle('hide-verse-numbers', this.state.versnummers === 'uit');
    },

    applyThemeClass() {
        // Zet data-theme op <html>. 'auto' = volg systeem-voorkeur, anders expliciet.
        const root = document.documentElement;
        const choice = this.state.thema;
        if (choice === 'donker') {
            root.setAttribute('data-theme', 'donker');
        } else if (choice === 'licht') {
            root.setAttribute('data-theme', 'licht');
        } else {
            const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
            root.setAttribute('data-theme', prefersDark ? 'donker' : 'licht');
        }
    },

    save() {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.state));
    },

    /**
     * Transformeer een OV-tekst-fragment volgens de huidige opties.
     * Werkt op zowel platte tekst als HTML — we doen alleen tekst-vervangingen
     * en blijven van HTML-tags af.
     */
    transformOV(html, testament) {
        if (!html) return html;
        let out = html;

        // === Heere → Here (alleen NT; Kurios) ===
        // In het NT is "Heere" de weergave van het Griekse κύριος (Kurios). Optioneel
        // tonen we de modernere vorm "Here". Hoofdletter-"HEERE" (OT-Godsnaam) blijft ongemoeid.
        if (testament === 'NT' && this.state.heereNT === 'here') {
            out = this._replaceOutsideTags(out, [
                [/\bHeere/g, 'Here'],   // vangt ook "Heeren" → "Heren"
            ]);
        }

        // === OT-Sheol: dodenrijk → hel (optioneel) ===
        if (this.state.otSheol === 'hel') {
            out = this._replaceOutsideTags(out, [
                [/\bdodenrijk\b/g, 'hel'],
                [/\bDodenrijk\b/g, 'Hel'],
            ]);
        }

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

        // === Arabische (islamitische) namen (optioneel) ===
        // Vervangt gevestigde bijbelse figuren/begrippen door hun Arabische naamvorm.
        // Alleen op de OV-tekst; historische kolommen blijven ongemoeid.
        if (this.state.arabischeNamen === 'aan' && this._arNamen) {
            out = this._replaceOutsideTags(out, this._arNamen);
        }

        return out;
    },

    /** Laad de Arabische-namen-tabel en bouw vervang-paren (whole-word). */
    loadArabischeNamen() {
        fetch('data/namen-arabisch.json')
            .then(r => (r.ok ? r.json() : null))
            .then(d => {
                if (!d || !Array.isArray(d.namen)) return;
                const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                const pairs = [];
                d.namen.forEach(n => {
                    if (!n.translit) return;
                    [n.nl].concat(n.varianten || []).forEach(f => {
                        if (f) pairs.push([new RegExp('\\b' + esc(f) + '\\b', 'g'), n.translit]);
                    });
                });
                this._arNamen = pairs;
                // Als de optie al aan stond: alleen her-renderen als er al een hoofdstuk staat.
                // NOOIT location.reload() hier (zou een herlaad-lus bij het opstarten geven).
                if (this.state.arabischeNamen === 'aan' &&
                    typeof Navigation !== 'undefined' && Navigation.currentBook && Navigation.currentChapter &&
                    typeof App !== 'undefined' && App.renderChapter) {
                    App.renderChapter(Navigation.currentBook, Navigation.currentChapter);
                }
            })
            .catch(() => {});
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

// Globaal beschikbaar maken: een top-level `const` komt niet op window terecht,
// terwijl mobile-nav.js en app.js (boekvolgorde, doorlopend lezen) `window.Opties`
// gebruiken. Zonder deze regel valt de boekvolgorde altijd terug op 'canoniek'.
if (typeof window !== 'undefined') window.Opties = Opties;
