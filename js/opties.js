/* Open Vertaling — Vertalingsopties (parametrische rendering) */

const Opties = {
    STORAGE_KEY: 'sv2026_vertaalopties',

    DEFAULTS: {
        godsnaam: 'ov',          // 'ov' (JAHWEH) | 'klassiek' (HEERE) | 'jehovah' (Jehovah) | 'jhwh' (יהוה)
        heereNT: 'heere',        // NT-aanspreektitel (Kurios): 'heere' (OSV) | 'here' (Heere → Here)
        kolomLayout: 'naast',    // 'naast' (parallelle kolom) | 'eronder' (nieuwe regel onder OV2026)
        boekvolgorde: 'canoniek',// 'canoniek' | 'tenach' | 'chronologisch' | 'auteur' | 'lengte'
        versnummers: 'aan',      // 'aan' | 'uit'
        citaten: 'aan',          // 'aan' | 'uit' — citaatmarkering en sprekerkleuren
        otSheol: 'dodenrijk',    // 'dodenrijk' (OT-context, modern) | 'hel' (SV-traditioneel)
        thema: 'auto',           // 'auto' (systeem) | 'licht' | 'donker'
        arabischeNamen: 'uit',   // 'uit' (Nederlandse namen) | 'aan' (Musa, Ibrahim, Isa …) — alleen OV-tekst
        jezusNaam: 'nl',         // 'nl' (Jezus Christus) | 'hebreeuws' (Yeshua HaMashiach) | 'koranisch' (Isa) | 'arabisch' (Yasūʿ al-Masīḥ)
        geoMarkeren: 'uit',      // 'uit' | 'aan' — geografische locaties in de tekst markeren (Torah)
        maatstelsel: 'bijbels',  // 'bijbels' (el, efa, sikkel) | 'metrisch' (meter, liter, gram) | 'imperiaal' (voet, gallon, pond)
        getalweergave: 'woorden', // 'woorden' | 'cijfers' — zet aantallen vanaf 21 ook tussen haakjes in cijfers
        tijdrekening: 'bijbels', // 'bijbels' (de derde ure) | 'modern' (omstreeks negen uur 's ochtends)
        strongs: 'uit',          // 'uit' | 'aan' — bronvaste Strong-nummers bij grondtekstwoorden
        apocriefeBoeken: 'aan',
        ethiopischeBoeken: 'uit',
        teksteditie: 'nl-ov',    // actieve Bijbeltekst; de interface blijft Nederlands
        lettertype: 'klassiek',
        regelafstand: 'normaal',
    },

    state: {},

    // Vervang-paren voor Arabische namen ([regex, translit]); lui geladen uit data/namen-arabisch.json
    _arNamen: null,
    _geoData: {},            // per boek: { namen:{naam:{type}}, verzen:{"ch:vs":[substrings]} }
    _eenheden: null,         // omrekentabel + uitzonderingen; lui geladen uit data/eenheden.json
    _tijden: null,           // uren, nachtwaken en vaste tijdsfrasen; lui geladen uit data/tijden.json

    init() {
        if (this._initialized) return;
        this._initialized = true;
        const saved = localStorage.getItem(this.STORAGE_KEY);
        // Mobiele default: kolommen 'eronder' i.p.v. 'naast' — beter leesbaar op smal scherm
        const defaults = { ...this.DEFAULTS };
        if (window.innerWidth <= 768) defaults.kolomLayout = 'eronder';
        let savedState = {};
        try {
            savedState = saved ? JSON.parse(saved) : {};
            this.state = { ...defaults, ...savedState };
        } catch (e) {
            this.state = { ...defaults };
        }
        // Een geldige URL-keuze heeft in deze tab voorrang op de opslag.
        if (typeof TekstEditie !== 'undefined') this.state.teksteditie = TekstEditie.code();
        // Een oudere versie bewaarde citaatopmaak onder een losse sleutel.
        // Neem die eenmalig over zolang de centrale opties nog geen keuze bevatten.
        if (!Object.prototype.hasOwnProperty.call(savedState, 'citaten')) {
            const legacyCitaten = localStorage.getItem('citaatopmaak');
            if (legacyCitaten !== null) this.state.citaten = legacyCitaten === 'false' ? 'uit' : 'aan';
        }

        // Sync radio buttons + selects
        document.querySelectorAll('[data-optie]').forEach(input => {
            const optie = input.dataset.optie;
            if (input.type === 'range' && optie === 'regelafstand') {
                input.value = String({ compact: 0, normaal: 1, ruim: 2 }[this.state.regelafstand] ?? 1);
                this.updateRangeLabel(input);
            } else if (input.tagName === 'SELECT') {
                input.value = this.state[optie];
            } else {
                input.checked = this.state[optie] === input.value;
            }
        });

        // Pas layout-class direct toe (geen re-render nodig — pure CSS)
        this.applyLayoutClass();
        this.applyVerseNumbersClass();
        this.applyCitationsClass();
        this.applyThemeClass();
        this.applyReaderStyleClasses();

        // Arabische namen lui laden (en, indien al ingeschakeld, hoofdstuk herrenderen)
        this.ready = Promise.all([
            this.loadArabischeNamen(),
            this.loadGeoData(),
            this.loadEenheden(),
            this.loadTijden(),
        ]);

        // Klik op een gemarkeerde geografische locatie -> geografie-pagina (later: kaart/geodata)
        document.addEventListener('click', function (e) {
            var geo = e.target.closest && e.target.closest('.geo-locatie');
            if (geo) { window.location.href = 'geografie.html'; }
        });

        // Versnummers-checkbox (in 'Pagina & leeshulp') synchroniseren met state
        const vnCb = document.getElementById('toggle-versnummers');
        if (vnCb) vnCb.checked = this.state.versnummers !== 'uit';

        const alternatiefLettertype = document.getElementById('toggle-lettertype-alternatief');
        if (alternatiefLettertype) {
            alternatiefLettertype.checked = this.state.lettertype === 'rustig';
            alternatiefLettertype.addEventListener('change', () => {
                this.state.lettertype = alternatiefLettertype.checked ? 'rustig' : 'klassiek';
                this.save();
                this.applyReaderStyleClasses();
            });
        }

        // Topnav-knop voor 1-klik thema-wissel (donker ↔ licht)
        const themeBtn = document.getElementById('topnav-theme-toggle');
        if (themeBtn) {
            themeBtn.addEventListener('click', () => {
                const cur = document.documentElement.dataset.theme === 'donker' ? 'licht' : 'donker';
                this.state.thema = cur;
                this.save();
                this.applyThemeClass();
                document.querySelectorAll('[data-optie="thema"]').forEach(control => {
                    if (control.tagName === 'SELECT') control.value = cur;
                    else control.checked = (control.value === cur);
                });
            });
        }

        // Listen to changes
        document.querySelectorAll('[data-optie]').forEach(input => {
            input.addEventListener('change', () => {
                // Een checkbox moet ook op uitvinken reageren; radio's en selects
                // vuren alleen bij de nieuwe keuze.
                if (input.type === 'checkbox') {
                    this.state[input.dataset.optie] = input.checked ? input.value : 'uit';
                    this.save();
                    if (input.dataset.optie === 'apocriefeBoeken' || input.dataset.optie === 'ethiopischeBoeken') {
                        if (typeof Sidebar !== 'undefined' && Sidebar.renderTree) Sidebar.renderTree();
                        if (typeof Navigation !== 'undefined' && Navigation.renderBookNav) Navigation.renderBookNav();
                        return;
                    }
                    this.applyToCurrentChapter();
                    return;
                }
                if (input.type === 'range' && input.dataset.optie === 'regelafstand') {
                    this.state.regelafstand = ['compact', 'normaal', 'ruim'][Number(input.value)] || 'normaal';
                    this.updateRangeLabel(input);
                    this.save();
                    this.applyReaderStyleClasses();
                    return;
                }
                if (input.tagName === 'SELECT' || input.checked) {
                    this.state[input.dataset.optie] = input.value;
                    this.save();
                    const optie = input.dataset.optie;
                    if (optie === 'kolomLayout') {
                        this.applyLayoutClass();
                    } else if (optie === 'versnummers') {
                        // Pure CSS-toggle — geen re-render
                        this.applyVerseNumbersClass();
                    } else if (optie === 'citaten') {
                        this.applyCitationsClass();
                        this.applyToCurrentChapter();
                    } else if (optie === 'thema') {
                        this.applyThemeClass();
                    } else if (optie === 'lettertype' || optie === 'regelafstand') {
                        this.applyReaderStyleClasses();
                    } else if (optie === 'boekvolgorde' || optie === 'apocriefeBoeken' || optie === 'ethiopischeBoeken') {
                        // Sidebar + topnav opnieuw renderen, geen hoofdstuk-rerender
                        if (typeof Sidebar !== 'undefined' && Sidebar.renderTree) Sidebar.renderTree();
                        if (typeof Navigation !== 'undefined' && Navigation.renderBookNav) Navigation.renderBookNav();
                    } else if (optie === 'teksteditie') {
                        if (typeof TekstEditie !== 'undefined') TekstEditie.setCode(input.value);
                        this.applyToCurrentChapter();
                    } else {
                        this.applyToCurrentChapter();
                    }
                }
            });
        });
    },

    updateRangeLabel(input) {
        const label = document.getElementById(`${input.id}-value`);
        if (!label) return;
        label.textContent = ['Compact', 'Normaal', 'Ruim'][Number(input.value)] || 'Normaal';
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

    applyCitationsClass() {
        document.body.classList.toggle('citaten-uit', this.state.citaten === 'uit');
    },

    applyReaderStyleClasses() {
        const font = this.state.lettertype === 'rustig' ? 'rustig' : 'klassiek';
        const spacing = ['compact', 'normaal', 'ruim'].includes(this.state.regelafstand)
            ? this.state.regelafstand
            : 'normaal';
        document.body.classList.remove('reader-font-klassiek', 'reader-font-rustig');
        document.body.classList.remove(
            'reader-spacing-compact',
            'reader-spacing-normaal',
            'reader-spacing-ruim'
        );
        document.body.classList.add(`reader-font-${font}`, `reader-spacing-${spacing}`);
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
        window.dispatchEvent(new CustomEvent('ov:opties-gewijzigd', {
            detail: { state: { ...this.state } }
        }));
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

        // === Naam van Jezus ===
        // Vier keuzes. "Jezus Sirach" blijft altijd ongemoeid: dat is Ben Sira,
        // een andere persoon, en de boektitel hoort niet te wijzigen.
        //
        // De samenstelling "Jezus Christus" moet vóór de losse naam staan,
        // anders wordt eerst "Jezus" vervangen en blijft "Christus" los achter.
        var NAAMVORMEN = {
            hebreeuws: { vol: 'Yeshua HaMashiach', kort: 'Yeshua',
                         volHoofd: 'YESHUA HAMASHIACH', kortHoofd: 'YESHUA' },
            koranisch: { vol: 'Isa al-Masih', kort: 'Isa',
                         volHoofd: 'ISA AL-MASIH', kortHoofd: 'ISA' },
            arabisch:  { vol: 'Yasūʿ al-Masīḥ', kort: 'Yasūʿ',
                         volHoofd: 'YASŪʿ AL-MASĪḤ', kortHoofd: 'YASŪʿ' },
        };
        var vorm = NAAMVORMEN[this.state.jezusNaam];
        if (vorm) {
            out = this._replaceOutsideTags(out, [
                // De Statenvertaling zet de naam in hoofdletters waar hij
                // gegeven wordt (Mattheüs 1:21, 1:25). Dat blijft zo.
                [/\bJEZUS CHRISTUS\b/g, vorm.volHoofd],
                [/\bJezus Christus\b/g, vorm.vol],
                [/\bJEZUS\b/g, vorm.kortHoofd],
                [/\bJezus\b(?! Sirach)/g, vorm.kort],
            ]);
        }

        // === Arabische (islamitische) namen (optioneel) ===
        // Vervangt gevestigde bijbelse figuren/begrippen door hun Arabische naamvorm.
        // Alleen op de OV-tekst; historische kolommen blijven ongemoeid.
        if (this.state.arabischeNamen === 'aan' && this._arNamen) {
            out = this._replaceOutsideTags(out, this._arNamen);
        }

        // Aantallen blijven uitgeschreven en krijgen desgewenst een compact
        // cijferbeeld ernaast, bijvoorbeeld "drie (3)" of "... duizend (57.400)".
        out = this.toonGetalcijfers(out);

        return out;
    },

    /** Laad de Arabische-namen-tabel en bouw vervang-paren (whole-word). */
    loadArabischeNamen() {
        return fetch('data/namen-arabisch.json')
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

    /** Laad de geografische-locatie-data voor de vijf boeken van de Torah. */
    loadGeoData() {
        var boeken = ['genesis', 'exodus', 'leviticus', 'numeri', 'deuteronomium'];
        return Promise.all(boeken.map(function (boek) {
            return fetch('data/' + boek + '-geo.json')
                .then(function (r) { return r.ok ? r.json() : null; })
                .then(function (data) { return [boek, data]; });
        }))
            .then(resultaten => {
                resultaten.forEach(paar => {
                    if (paar[1] && paar[1].verzen) this._geoData[paar[0]] = paar[1];
                });
                if (this.state.geoMarkeren === 'aan' &&
                    typeof Navigation !== 'undefined' && Navigation.currentBook && Navigation.currentChapter &&
                    typeof App !== 'undefined' && App.renderChapter) {
                    App.renderChapter(Navigation.currentBook, Navigation.currentChapter);
                }
            })
            .catch(() => {});
    },

    /** Markeer geografische locaties in een OV-vers (buiten HTML-tags). */
    markeerGeo(html, book, ch, vnum) {
        if (this.state.geoMarkeren !== 'aan' || !this._geoData[book]) return html;
        var boekData = this._geoData[book];
        var locs = boekData.verzen[ch + ':' + vnum];
        if (!locs || !locs.length) return html;
        var namen = boekData.namen || {};
        var esc = function (s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); };
        var uniq = Object.keys(locs.reduce(function (a, l) { a[l] = 1; return a; }, {}))
            .sort(function (a, b) { return b.length - a.length; });
        var re = new RegExp('(' + uniq.map(esc).join('|') + ')', 'g');
        var tokenRegex = /(<[^>]+>)|([^<]+)/g, result = '', m;
        while ((m = tokenRegex.exec(html)) !== null) {
            if (m[1]) { result += m[1]; continue; }
            result += m[2].replace(re, function (mm) {
                var type = (namen[mm] && namen[mm].type) ? ' — ' + namen[mm].type : '';
                return '<span class="geo-locatie" data-geo="' + mm.replace(/"/g, '') + '" title="Geografische locatie' + type + '">' + mm + '</span>';
            });
        }
        return result;
    },

    // ===================================================================
    // Maten, inhoudsmaten en gewichten — omrekenen naar een modern stelsel
    // -------------------------------------------------------------------
    // Bij `maatstelsel: 'metrisch'` of `'imperiaal'` wordt de Bijbelse maat in
    // de OV-tekst VERVANGEN door de moderne ("driehonderd ellen" wordt
    // "ongeveer 133 meter"); het origineel blijft in het title-attribuut staan.
    // Bij 'bijbels' (de standaard) verandert er niets aan de tekst.
    //
    // Rekenwaarden, de schalen per stelsel, contextvarianten (de lange el van
    // Ezechiël 40-48) en alle uitzonderingen staan in data/eenheden.json, zodat
    // ze bij te werken zijn zonder deze code aan te raken. Er wordt uitsluitend
    // op tekst gewerkt: HTML-tags en nootcijfers (<sup>) blijven behouden, en
    // de brondata verandert niet.
    //
    // Let op: geen RegExp-lookbehind — Safari < 16.4 (iPadOS 15.4) kent die niet.
    // ===================================================================

    /** Laad de omrekentabel voor Bijbelse maten en gewichten. */
    loadEenheden() {
        return fetch('data/eenheden.json')
            .then(r => (r.ok ? r.json() : null))
            .then(d => {
                if (!d || !Array.isArray(d.eenheden)) return;
                this._eenheden = this._maatIndex(d);
                if (((this.state.maatstelsel && this.state.maatstelsel !== 'bijbels') ||
                    this.state.getalweergave === 'cijfers') &&
                    typeof Navigation !== 'undefined' && Navigation.currentBook && Navigation.currentChapter &&
                    typeof App !== 'undefined' && App.renderChapter) {
                    App.renderChapter(Navigation.currentBook, Navigation.currentChapter);
                }
            })
            .catch(() => {});
    },

    /**
     * Voeg na ondubbelzinnige uitgeschreven aantallen vanaf 21 een cijfernotatie toe.
     * Het onbeklemtoonde lidwoord "een" blijft ongemoeid; "één" is wel een getal.
     * De woorden blijven de eigenlijke vertaling; dit is uitsluitend leeshulp.
     */
    toonGetalcijfers(html) {
        if (!html || this.state.getalweergave !== 'cijfers' || !this._eenheden) return html;
        var E = this._eenheden;
        var proj = this._maatPlatteTekst(html);
        var plain = proj.plain, map = proj.map;
        var woordRe = /[A-Za-zÀ-ÖØ-öø-ÿ]+/g, woorden = [], m;
        while ((m = woordRe.exec(plain)) !== null) {
            woorden.push({ woord: m[0].toLowerCase(), start: m.index, eind: m.index + m[0].length });
        }

        var invoegingen = [], laatsteEind = -1;
        for (var i = 0; i < woorden.length; i++) {
            var eersteMorfemen = this._maatMorfemen(E, woorden[i].woord);
            if (eersteMorfemen === null || !eersteMorfemen.length) continue;

            var links = i, rechts = i;
            while (links > 0 && /^\s+$/.test(plain.slice(woorden[links - 1].eind, woorden[links].start)) &&
                this._maatMorfemen(E, woorden[links - 1].woord) !== null) links--;
            while (rechts + 1 < woorden.length && /^\s+$/.test(plain.slice(woorden[rechts].eind, woorden[rechts + 1].start)) &&
                this._maatMorfemen(E, woorden[rechts + 1].woord) !== null) rechts++;

            while (links <= rechts && E.scheiders.indexOf(woorden[links].woord) !== -1) links++;
            while (rechts >= links && E.scheiders.indexOf(woorden[rechts].woord) !== -1) rechts--;
            if (links > rechts) continue;

            // "een" en "ene" zijn doorgaans lidwoord/voornaamwoord. Alleen de
            // expliciet beklemtoonde schrijfwijze "één" krijgt zelfstandig (1).
            if (links === rechts && (woorden[links].woord === 'een' || woorden[links].woord === 'ene')) {
                i = rechts;
                continue;
            }

            var begin = woorden[links].start, eind = woorden[rechts].eind;
            if (begin < laatsteEind) continue;
            var parsed = this._maatUitTokens(E, woorden.slice(links, rechts + 1).map(function (x) { return x.woord; }));
            if (!parsed.expliciet || !isFinite(parsed.aantal) || parsed.aantal <= 20) continue;

            var cijfer = this._getalExactTekst(parsed.aantal);
            invoegingen.push({
                positie: map[eind - 1] + 1,
                html: ' <span class="getal-cijfer" aria-label="' + cijfer + '">(' + cijfer + ')</span>',
            });
            laatsteEind = eind;
            i = rechts;
        }

        for (var j = invoegingen.length - 1; j >= 0; j--) {
            var item = invoegingen[j];
            html = html.slice(0, item.positie) + item.html + html.slice(item.positie);
        }
        return html;
    },

    /** Exacte Nederlandse cijfernotatie voor een expliciet genoemd aantal. */
    _getalExactTekst(v) {
        var d = String(v).split('.');
        var geheel = d[0].replace(/\B(?=(\d{3})+(?!\d))/g, '.');
        return d.length > 1 ? geheel + ',' + d[1] : geheel;
    },

    /** Bouw eenmalig de zoekstructuren uit data/eenheden.json. */
    _maatIndex(d) {
        var opties = d.opties || {};
        var esc = function (s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); };
        var vormMap = {}, alleVormen = [];
        d.eenheden.forEach(function (eh) {
            if (eh.volgtOp) eh._volgtOpRe = new RegExp(eh.volgtOp);
            if (eh.volgtNiet) eh._volgtNietRe = new RegExp(eh.volgtNiet);
            if (eh.voorafNiet) eh._voorafNietRe = new RegExp(eh.voorafNiet);
            if (eh.ijkFrase && eh.ijkFrase.patroon) eh._ijkRe = new RegExp(eh.ijkFrase.patroon);
            // Voor "een el en een halve el": het herhaalde eenheidswoord hoort bij dezelfde maat
            eh._herhaalRe = new RegExp('^\\s+(?:' + (eh.vormen || []).map(esc).join('|') + ')(?![A-Za-zÀ-ÖØ-öø-ÿ])');
            (eh.vormen || []).forEach(function (v) {
                vormMap[v.toLowerCase()] = eh;
                alleVormen.push(v);
            });
        });
        // Langste vorm eerst, anders wint "el" van "ellen" en "maat" van "korenmaat"
        alleVormen.sort(function (a, b) { return b.length - a.length; });
        var koppels = d.koppels || [], malen = d.malen || [], alternatieven = d.alternatieven || [];
        // Morfemen om uitgeschreven getallen te ontleden ("vierhonderddrieëndertig")
        var morfemen = Object.keys(d.getallen || {})
            .concat(koppels, d.halven || [], malen, alternatieven)
            .sort(function (a, b) { return b.length - a.length; });
        return {
            vormMap: vormMap,
            vormRegex: new RegExp('(?:' + alleVormen.map(esc).join('|') + ')',
                opties.alleenKleineLetter === false ? 'gi' : 'g'),
            getallen: d.getallen || {},
            halven: d.halven || [],
            malen: malen,
            alternatieven: alternatieven,
            scheiders: koppels.concat(malen, alternatieven),
            morfemen: morfemen,
            breuken: d.breuken || {},
            stoffen: opties.stofadjectieven || {},
            stelsels: d.stelsels || {},
            uitzonderingen: d.uitzonderingen || [],
            implicieteMaten: d.implicieteMaten || [],
        };
    },

    /**
     * Vervang Bijbelse maten in een OV-vers door moderne eenheden.
     * Geeft de HTML ongewijzigd terug als het stelsel op 'bijbels' staat,
     * als de tabel nog niet geladen is, of als er niets te vervangen valt.
     */
    rekenMaten(html, book, ch, vnum) {
        var stelsel = this.state.maatstelsel;
        if (!html || !this._eenheden) return html;
        if (stelsel !== 'metrisch' && stelsel !== 'imperiaal') return html;
        var E = this._eenheden;
        if (!E.stelsels[stelsel]) return html;
        var proj = this._maatPlatteTekst(html);
        var plain = proj.plain, map = proj.map;
        var re = E.vormRegex, stukken = [], m, grens = 0;
        ch = +ch; vnum = +vnum;
        re.lastIndex = 0;
        while ((m = re.exec(plain)) !== null) {
            var start = m.index, eind = start + m[0].length;
            re.lastIndex = eind;
            // Randcontrole vangt Beth-el, Bath-sua, meetriet en rietstok af
            if (!this._maatVrijeRand(plain, start, eind)) continue;
            var eh = E.vormMap[m[0].toLowerCase()];
            if (!eh) continue;
            if (eh.alleenIn && !this._maatInBereik(eh.alleenIn, book, ch, vnum)) continue;
            if (this._maatUitgesloten(E, eh.id, book, ch, vnum)) continue;
            var na = plain.slice(eind);
            if (eh._volgtOpRe && !eh._volgtOpRe.test(na)) continue;
            if (eh._volgtNietRe && eh._volgtNietRe.test(na)) continue;

            // Contextvariant: Ezechiël 40-48 meet met de lange el, het NT met een lichter talent
            var waarde = eh.waarde, uitleg = eh.uitleg, slokOp = eh.slokOp;
            if (eh.context) {
                for (var c = 0; c < eh.context.length; c++) {
                    if (this._maatInBereik(eh.context[c].verzen, book, ch, vnum)) {
                        waarde = eh.context[c].waarde;
                        uitleg = eh.context[c].uitleg;
                        if (eh.context[c].slokOp) slokOp = eh.context[c].slokOp;
                        break;
                    }
                }
            }

            // "naar de sikkel van het heiligdom" is de ijkmaat zelf en geen hoeveelheid:
            // die tekst blijft staan, met alleen een uitleg in het title-attribuut.
            if (eh._ijkRe && eh._ijkRe.test(na)) {
                if (start < grens) continue;
                stukken.push({
                    van: map[start], tot: map[eind],
                    nieuw: '<span class="maat-ijk" title="' + this._maatAttr(eh.ijkFrase.uitleg) + '">' + m[0] + '</span>',
                });
                grens = eind;
                continue;
            }

            var g = this._maatAantalVoor(E, plain.slice(0, start));
            // "een el en een halve (el)" hoort bij dezelfde maat
            var half = /^[,;]?\s+en\s+(?:een|één|ene)\s+halve?n?(?![A-Za-zÀ-ÖØ-öø-ÿ])/.exec(na);
            if (half) {
                g.aantal += 0.5;
                g.alternatieven = null;
                g.expliciet = true;
                eind += half[0].length;
                var herhaald = eh._herhaalRe.exec(plain.slice(eind));
                if (herhaald) eind += herhaald[0].length;
                re.lastIndex = eind;
            }
            // "een talent pond zwaar": het naliggende woord hoort bij dezelfde maat
            if (slokOp) {
                var sm = new RegExp(slokOp).exec(plain.slice(eind));
                if (sm) { eind += sm[0].length; re.lastIndex = eind; }
            }
            // Zonder telwoord valt er niets te vervangen ("met de gomer maten",
            // "een schatting aan zilveren sikkels") — dan blijft de tekst staan.
            if (!g.expliciet) continue;
            if (g.start < grens) continue;
            // Definitiezinnen als "elke el van één el en een handbreed" (Ezechiël 40:5,
            // 43:13) blijven onaangeroerd — daar wordt de eenheid zelf omschreven.
            if (eh._voorafNietRe && eh._voorafNietRe.test(plain.slice(0, g.start))) continue;

            var getallen = g.alternatieven || [g.aantal], delen = [], bruikbaar = true;
            for (var q = 0; q < getallen.length; q++) {
                if (!isFinite(getallen[q]) || getallen[q] <= 0) { bruikbaar = false; break; }
                delen.push(this._maatFormatteer(getallen[q] * waarde, eh.grondEenheid, stelsel));
            }
            if (!bruikbaar || !delen.length) continue;

            // "twee of drie metreten" → "ongeveer 78 of 117 liter" (eenheid één keer)
            var zelfdeEenheid = delen.every(function (x) { return x.eenheid === delen[0].eenheid; });
            var getalTekst = zelfdeEenheid
                ? delen.map(function (x) { return x.getal; }).join(' of ') + ' ' + delen[0].eenheid
                : delen.map(function (x) { return x.getal + ' ' + x.eenheid; }).join(' of ');
            // Niet "ongeveer ongeveer": de tekst zegt het soms zelf al
            var alBenaderd = /(?:ongeveer|omtrent|circa|bijna|ruim)\s*$/.test(plain.slice(0, g.start));
            var nieuweTekst = (alBenaderd ? '' : 'ongeveer ') + getalTekst + (g.stof ? ' ' + g.stof : '');
            var origineel = plain.slice(g.start, eind);
            // Stond het telwoord aan het begin van een zin ("Één maatje tarwe"),
            // dan hoort de vervanging ook met een hoofdletter te beginnen.
            if (/^[A-ZÀ-ÖØ-Þ]/.test(origineel)) {
                nieuweTekst = nieuweTekst.charAt(0).toUpperCase() + nieuweTekst.slice(1);
            }
            // Nootcijfers en tags binnen het vervangen stuk mogen niet verdwijnen
            var behoud = this._maatBehoudTags(html.slice(map[g.start], map[eind]));
            stukken.push({
                van: map[g.start], tot: map[eind],
                nieuw: '<span class="maat-omgerekend" title="' +
                    this._maatAttr('Oorspronkelijk: ' + origineel + ' · ' + uitleg) + '">' + nieuweTekst + '</span>' + behoud,
            });
            grens = eind;
        }
        if (!stukken.length) return this._rekenImplicieteMaten(html, book, ch, vnum, stelsel, E);
        var uit = '', vorig = 0;
        for (var i = 0; i < stukken.length; i++) {
            if (stukken[i].van < vorig) continue;
            uit += html.slice(vorig, stukken[i].van) + stukken[i].nieuw;
            vorig = stukken[i].tot;
        }
        return this._rekenImplicieteMaten(uit + html.slice(vorig), book, ch, vnum, stelsel, E);
    },

    /**
     * Vul alleen expliciet geregistreerde, elliptische maten aan. Soms noemt
     * een vers de eenheid maar Ã©Ã©n keer (bijvoorbeeld: â€œzestig ellen â€¦
     * twintig in zijn breedteâ€). De bron blijft onaangeroerd; de tabel legt
     * per vers vast welk getal die eerder genoemde eenheid herhaalt.
     */
    _rekenImplicieteMaten(html, book, ch, vnum, stelsel, E) {
        var regels = E.implicieteMaten || [];
        for (var i = 0; i < regels.length; i++) {
            var regel = regels[i];
            if (!regel || !regel.zoek || !regel.eenheid || !regel.verzen ||
                !this._maatInBereik(regel.verzen, book, ch, vnum)) continue;
            var eh = E.vormMap[String(regel.eenheid).toLowerCase()];
            if (!eh || !isFinite(regel.aantal) || html.indexOf(regel.zoek) === -1) continue;
            var waarde = typeof regel.waarde === 'number' ? regel.waarde : eh.waarde;
            var deel = this._maatFormatteer(regel.aantal * waarde, eh.grondEenheid, stelsel);
            if (!deel) continue;
            var nieuw = 'ongeveer ' + deel.getal + ' ' + deel.eenheid;
            var origineel = regel.zoek + ' ' + (eh.enkelvoud || regel.eenheid);
            var titel = 'Oorspronkelijk: ' + origineel + ' Â· ' +
                (regel.uitleg || 'de eenheid is in deze zin uit de directe context aangevuld');
            html = html.replace(regel.zoek,
                '<span class="maat-omgerekend maat-impliciet" title="' +
                this._maatAttr(titel) + '">' + nieuw + '</span>');
        }
        return html;
    },

    /**
     * Projecteer HTML op platte tekst met een index-kaart terug naar de HTML.
     * Inhoud van <sup>…</sup> (de nootcijfers) telt niet mee, anders zou
     * "driehonderd<sup>37</sup> ellen" nooit als één getal + maat herkend worden.
     */
    _maatPlatteTekst(html) {
        var plain = '', map = [], i = 0, n = html.length;
        while (i < n) {
            if (html.charAt(i) === '<') {
                var gt = html.indexOf('>', i);
                if (gt === -1) { plain += html.charAt(i); map.push(i); i++; continue; }
                if (/^<sup[\s>]/i.test(html.slice(i, gt + 1))) {
                    var dicht = html.toLowerCase().indexOf('</sup>', gt);
                    i = dicht === -1 ? gt + 1 : dicht + 6;
                } else {
                    i = gt + 1;
                }
                continue;
            }
            plain += html.charAt(i); map.push(i); i++;
        }
        map.push(n);   // sluitpositie, zodat map[eind] altijd bestaat
        return { plain: plain, map: map };
    },

    /** Haal de tags en nootcijfers uit een HTML-stuk dat vervangen wordt. */
    _maatBehoudTags(fragment) {
        var uit = '', i = 0, n = fragment.length;
        while (i < n) {
            if (fragment.charAt(i) !== '<') { i++; continue; }
            var gt = fragment.indexOf('>', i);
            if (gt === -1) break;
            if (/^<sup[\s>]/i.test(fragment.slice(i, gt + 1))) {
                var dicht = fragment.toLowerCase().indexOf('</sup>', gt);
                var stop = dicht === -1 ? gt + 1 : dicht + 6;
                uit += fragment.slice(i, stop);
                i = stop;
            } else {
                uit += fragment.slice(i, gt + 1);
                i = gt + 1;
            }
        }
        return uit;
    },

    /** Staat het gevonden woord vrij, of plakt het aan een ander woord/koppelteken vast? */
    _maatVrijeRand(txt, start, eind) {
        var LETTER = /[0-9A-Za-zÀ-ÖØ-öø-ÿ'’\-]/;
        if (start > 0 && LETTER.test(txt.charAt(start - 1))) return false;
        if (eind < txt.length && LETTER.test(txt.charAt(eind))) return false;
        return true;
    },

    /**
     * Lees het uitgeschreven getal dat vóór een maat staat ("vier duizend en
     * vijfhonderd"). Geeft { aantal, alternatieven, expliciet, start, stof }:
     * `expliciet` is onwaar als er geen telwoord of breuk stond ("met de gomer"),
     * `start` is de plaats waar het te vervangen stuk begint.
     */
    _maatAantalVoor(E, voor) {
        var WOORD = /[A-Za-zÀ-ÖØ-öø-ÿ]+$/;
        var rest = voor.replace(/\s+$/, ''), tokens = [], posities = [], stof = null;
        while (true) {
            var w = WOORD.exec(rest);
            if (!w) break;
            var woord = w[0].toLowerCase();
            // Stofadjectief tussen telwoord en eenheid: "vijftig zilveren sikkels"
            if (!stof && !tokens.length && E.stoffen[woord]) {
                stof = E.stoffen[woord];
                rest = rest.slice(0, w.index).replace(/\s+$/, '');
                continue;
            }
            if (this._maatMorfemen(E, woord) === null) break;
            tokens.unshift(woord);
            posities.unshift(w.index);
            rest = rest.slice(0, w.index).replace(/\s+$/, '');
        }
        // Een losse "en" of "of" aan het begin hoort bij de zin, niet bij het getal
        while (tokens.length && E.scheiders.indexOf(tokens[0]) !== -1) {
            tokens.shift(); posities.shift();
        }
        var res = this._maatUitTokens(E, tokens);
        res.stof = stof;
        res.start = posities.length ? posities[0] : voor.length;
        // Breuk ervoor: "het tiende deel van een efa", "de helft van de sikkel".
        // Rangtelwoorden eisen het woord "deel", anders leest "de derde van zeven
        // ellen" (de derde kamer) ten onrechte als een derde van zeven ellen.
        var b = /(?:het|de|een|één)\s+(?:([A-Za-zÀ-ÖØ-öø-ÿ]+)\s+deel|(helft|vierendeel))\s+van(?:\s+(?:de|het|een|één|ene))?\s*$/.exec(rest);
        if (b) {
            var breuk = E.breuken[(b[1] || b[2]).toLowerCase()];
            if (typeof breuk === 'number') {
                res.aantal *= breuk;
                if (res.alternatieven) {
                    res.alternatieven = res.alternatieven.map(function (x) { return x * breuk; });
                }
                res.expliciet = true;
                res.start = b.index;
            }
        }
        return res;
    },

    /** Reken een rij getalwoorden om naar één getal ("vier duizend en vijfhonderd" → 4500). */
    _maatUitTokens(E, tokens) {
        // "twee of drie metreten" — twee mogelijkheden, allebei tonen
        for (var a = 0; a < tokens.length; a++) {
            if (E.alternatieven.indexOf(tokens[a]) !== -1) {
                var l = this._maatUitTokens(E, tokens.slice(0, a));
                var r = this._maatUitTokens(E, tokens.slice(a + 1));
                if (l.expliciet && r.expliciet) {
                    return { aantal: r.aantal, alternatieven: [l.aantal, r.aantal], expliciet: true };
                }
                return r;
            }
        }
        var factor = 1;
        if (tokens.length && E.halven.indexOf(tokens[tokens.length - 1]) !== -1) {
            factor = 0.5;                       // "een halve el", "een halven homer"
            tokens = tokens.slice(0, -1);
        }
        // "duizend maal duizend talenten" — vermenigvuldigen in plaats van optellen
        for (var k = 0; k < tokens.length; k++) {
            if (E.malen.indexOf(tokens[k]) !== -1) {
                var links = this._maatUitTokens(E, tokens.slice(0, k));
                var rechts = this._maatUitTokens(E, tokens.slice(k + 1));
                return {
                    aantal: links.aantal * rechts.aantal * factor,
                    expliciet: links.expliciet && rechts.expliciet,
                };
            }
        }
        var totaal = 0, huidig = 0, gezien = false;
        for (var i = 0; i < tokens.length; i++) {
            var delen = this._maatMorfemen(E, tokens[i]);
            if (delen === null) continue;
            for (var j = 0; j < delen.length; j++) {
                var v = delen[j];
                gezien = true;
                if (v === 100) huidig = (huidig || 1) * 100;
                else if (v === 1000) { totaal += (huidig || 1) * 1000; huidig = 0; }
                else huidig += v;
            }
        }
        totaal += huidig;
        if (!gezien) totaal = 1;                // "de gomer", "met de sikkel" → één eenheid
        return { aantal: totaal * factor, expliciet: gezien || factor !== 1 };
    },

    /**
     * Ontleed één woord in getalmorfemen. Geeft null als het geen getalwoord is;
     * "en"/"ën"/"of"/"halve" leveren een lege bijdrage maar zijn wél toegestaan.
     */
    _maatMorfemen(E, woord) {
        // Het bronbestand kan door oudere tooling met verkeerd gedecodeerde
        // UTF-8 binnenkomen. Normaliseer alleen de bekende beklemtoonde vorm
        // zodat "één" even betrouwbaar als "een" als getal wordt herkend.
        woord = String(woord).replace(/één/gi, 'een');
        var res = [], i = 0, n = woord.length;
        while (i < n) {
            var gevonden = null;
            for (var k = 0; k < E.morfemen.length; k++) {
                var mo = E.morfemen[k];
                if (woord.slice(i, i + mo.length) === mo) { gevonden = mo; break; }
            }
            if (!gevonden) return null;
            i += gevonden.length;
            if (typeof E.getallen[gevonden] === 'number') res.push(E.getallen[gevonden]);
        }
        return res;
    },

    /** Valt dit vers onder een uitzondering voor deze eenheid? */
    _maatUitgesloten(E, id, book, ch, vs) {
        for (var i = 0; i < E.uitzonderingen.length; i++) {
            var u = E.uitzonderingen[i];
            var raakt = !u.eenheden || u.eenheden.indexOf('*') !== -1 || u.eenheden.indexOf(id) !== -1;
            if (raakt && this._maatInBereik(u.verzen, book, ch, vs)) return true;
        }
        return false;
    },

    /** Vers-referenties: "genesis 25:4", "ezechiel 45:11-14", "ezechiel 40-48", "johannes 12". */
    _maatInBereik(lijst, book, ch, vs) {
        if (!lijst) return false;
        for (var i = 0; i < lijst.length; i++) {
            var ref = lijst[i], sp = ref.lastIndexOf(' ');
            if (sp === -1 || ref.slice(0, sp) !== book) continue;
            var rest = ref.slice(sp + 1), dp = rest.indexOf(':');
            if (dp === -1) {
                var hp = rest.split('-');
                var h1 = parseInt(hp[0], 10);
                var h2 = hp.length > 1 ? parseInt(hp[1], 10) : h1;
                if (ch >= h1 && ch <= h2) return true;
                continue;
            }
            if (parseInt(rest.slice(0, dp), 10) !== ch) continue;
            var vp = rest.slice(dp + 1).split('-');
            var v1 = parseInt(vp[0], 10);
            var v2 = vp.length > 1 ? parseInt(vp[1], 10) : v1;
            if (vs >= v1 && vs <= v2) return true;
        }
        return false;
    },

    /**
     * Kies binnen het gekozen stelsel de best leesbare eenheid en rond af.
     * De schalen (grens, factor, naam) staan in data/eenheden.json.
     */
    _maatFormatteer(w, grond, stelsel) {
        var schaal = (this._eenheden.stelsels[stelsel] || {})[grond] || [];
        for (var i = 0; i < schaal.length; i++) {
            var s = schaal[i];
            if (s.tot === undefined || w < s.tot || i === schaal.length - 1) {
                return { getal: this._maatGetalTekst(w * s.factor, s.stap), eenheid: s.naam };
            }
        }
        return { getal: this._maatGetalTekst(w), eenheid: '' };
    },

    /** Nederlandse getalnotatie: komma als decimaalteken, punt als duizendtal. */
    _maatGetalTekst(v, stap) {
        var x;
        if (stap && v >= 100) x = Math.round(v / stap) * stap;
        else if (v >= 1000) {
            // Grote getallen op drie significante cijfers; "1.162.357 gallon"
            // suggereert een precisie die er niet is.
            var orde = Math.pow(10, Math.floor(Math.log(v) / Math.LN10) - 2);
            x = Math.round(v / orde) * orde;
        }
        else if (v >= 10) x = Math.round(v);
        else if (v >= 1) x = Math.round(v * 10) / 10;
        else x = Math.round(v * 100) / 100;
        var d = String(x).split('.');
        // Alleen vooruitkijkende assertie — lookbehind is niet toegestaan (Safari < 16.4)
        var geheel = d[0].replace(/\B(?=(\d{3})+(?!\d))/g, '.');
        return d.length > 1 ? geheel + ',' + d[1] : geheel;
    },

    /** Maak een string veilig voor een HTML-attribuut. */
    _maatAttr(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    },

    // ===================================================================
    // Tijdsaanduidingen — omrekenen naar moderne kloktijd
    // -------------------------------------------------------------------
    // Bij `tijdrekening: 'modern'` wordt "het negende uur" in de OV-tekst
    // VERVANGEN door "ongeveer drie uur 's middags"; het origineel blijft in
    // het title-attribuut staan. Bij 'bijbels' (de standaard) verandert er
    // niets. De brondata in data/ blijft hoe dan ook ongemoeid — dit is een
    // weergave-optie, geen tekstwijziging.
    //
    // De Bijbelse dag loopt van zonsopgang tot zonsondergang en telt twaalf
    // uren, dus het eerste uur begint omstreeks zes uur 's ochtends. Het zijn
    // seizoensuren: 's zomers duurt een uur ruim zeventig minuten, 's winters
    // nog geen vijftig. Daarom staat er altijd "ongeveer" of "omstreeks" bij,
    // en daarom is er ook geen exactere weergave dan hele uren.
    //
    // Rekenwaarden, de nachtwaken (drie in het OT, vier in het NT) en de vaste
    // frasen staan in data/tijden.json, zodat ze bij te werken zijn zonder deze
    // code aan te raken.
    //
    // De hulpfuncties _maatPlatteTekst / _maatBehoudTags / _maatAttr /
    // _maatInBereik zijn niet maat-specifiek en worden hier hergebruikt: ze
    // lossen precies hetzelfde probleem op (tekst herkennen dwars door
    // nootcijfers en citaat-spans heen, zonder de HTML te beschadigen).
    //
    // Let op: geen RegExp-lookbehind — Safari < 16.4 (iPadOS 15.4) kent die niet.
    // ===================================================================

    /** Laad de omrekentabel voor Bijbelse tijdsaanduidingen. */
    loadTijden() {
        return fetch('data/tijden.json')
            .then(r => (r.ok ? r.json() : null))
            .then(d => {
                if (!d || !d.uren) return;
                this._tijden = this._tijdIndex(d);
                if (this.state.tijdrekening === 'modern' &&
                    typeof Navigation !== 'undefined' && Navigation.currentBook && Navigation.currentChapter &&
                    typeof App !== 'undefined' && App.renderChapter) {
                    App.renderChapter(Navigation.currentBook, Navigation.currentChapter);
                }
            })
            .catch(() => {});
    },

    /** Bouw eenmalig de zoekpatronen uit data/tijden.json. */
    _tijdIndex(d) {
        var LET = '[A-Za-zÀ-ÖØ-öø-ÿ]';
        var rangen = Object.keys(d.rangtelwoorden || {}).join('|');
        // "den nacht" (4 Baruch) naast "de nacht"; "overdag" naast "van de dag"
        var dagdeel = '(?:\\s+van\\s+(?:de|den|het)\\s+(?:nacht|dag)|\\s+in\\s+de\\s+nacht|\\s+overdag)?';
        var lidwoord = '(?:(?:het|den|de|dit|dat|die)\\s+)?';

        // Hoofdletter-ongevoelig: "Tussen de twee avonden zult u vlees eten"
        // (Exodus 16:12) staat aan het begin van de zin. De vervanging krijgt
        // die hoofdletter later terug.
        //
        // Het voorzetsel wordt meegenomen omdat "op het negende uur" in modern
        // Nederlands "omstreeks drie uur" wordt, niet "op ongeveer drie uur".
        var uurRe = new RegExp(
            '\\b(?:(ongeveer|omtrent|omstreeks|circa)\\s+)?(?:(op|om|te|ten|ter)\\s+)?' +
            lidwoord + '(' + rangen + ')' +
            '(?:\\s+en\\s+' + lidwoord + '(' + rangen + '))?' +
            '\\s+(?:uur|ure)(' + dagdeel + ')(?!' + LET + ')', 'gi');

        // "waak op!" is een oproep, geen nachtwake — die mag niet meegenomen worden
        var waakRe = new RegExp(
            '\\b(' + rangen + ')\\s+(?:nachtwake|nachtwaak|wake|waak)(?!\\s+op\\b)' +
            '(?:\\s+in\\s+de\\s+nacht)?(?!' + LET + ')', 'gi');

        var bouw = function (lijst) {
            return (lijst || []).map(function (f) {
                return {
                    id: f.id,
                    re: new RegExp('\\b(?:' + f.patroon + ')(?!' + LET + ')', 'gi'),
                    enkel: new RegExp('^(?:' + f.patroon + ')$', 'i'),
                    vervang: f.vervang,
                    uitleg: f.uitleg,
                    alleenIn: f.alleenIn,
                };
            });
        };

        return {
            rangtelwoorden: d.rangtelwoorden || {},
            uren: d.uren, uurUitleg: d.uurUitleg || {}, waken: d.waken || {},
            uurRe: uurRe, waakRe: waakRe,
            genoemdeWaken: bouw(d.genoemdeWaken),
            frases: bouw(d.frases),
            toelichtingen: bouw(d.toelichtingen),
        };
    },

    /**
     * Vervang Bijbelse tijdsaanduidingen in een OV-vers door moderne kloktijd.
     * Geeft de HTML ongewijzigd terug als de optie uit staat, als de tabel nog
     * niet geladen is, of als er niets te vervangen valt.
     */
    rekenTijden(html, book, ch, vnum, testament) {
        if (!html || !this._tijden) return html;
        if (this.state.tijdrekening !== 'modern') return html;
        var T = this._tijden, zelf = this;
        var proj = this._maatPlatteTekst(html);
        var plain = proj.plain, map = proj.map;
        var bezet = [], stukken = [];
        ch = +ch; vnum = +vnum;

        // Elke plaats wordt hooguit één keer aangepakt. De regels lopen in
        // volgorde van bepaald naar algemeen, zodat de losse toelichting op
        // "nachtwake" alleen overblijft waar géén rangtelwoord stond.
        function vrij(a, b) {
            for (var i = 0; i < bezet.length; i++) {
                if (a < bezet[i][1] && b > bezet[i][0]) return false;
            }
            return true;
        }
        function neem(a, b, klasse, tekst, titel) {
            bezet.push([a, b]);
            var binnen = html.slice(map[a], map[b]);
            var inhoud = tekst === null
                ? binnen                                        // tekst blijft staan, alleen een toelichting
                : tekst + zelf._maatBehoudTags(binnen);         // nootcijfers mogen niet verdwijnen
            stukken.push({
                van: map[a], tot: map[b],
                nieuw: '<span class="' + klasse + '" title="' + zelf._maatAttr(titel) + '">' + inhoud + '</span>',
            });
        }
        // Stond het origineel aan het begin van een zin, dan hoort de
        // vervanging ook met een hoofdletter te beginnen.
        function volgHoofdletter(origineel, nieuw) {
            return /^[A-ZÀ-ÖØ-Þ]/.test(origineel)
                ? nieuw.charAt(0).toUpperCase() + nieuw.slice(1) : nieuw;
        }

        // === Uren: "ongeveer het zesde uur", "tegen het derde uur in de nacht" ===
        var m;
        T.uurRe.lastIndex = 0;
        while ((m = T.uurRe.exec(plain)) !== null) {
            var start = m.index, eind = start + m[0].length;
            if (!vrij(start, eind)) continue;
            var snacht = /nacht/.test(m[5] || '');
            var tabel = T.uren[snacht ? 'nacht' : 'dag'];
            var e1 = tabel[String(T.rangtelwoorden[m[3].toLowerCase()])];
            var e2 = m[4] ? tabel[String(T.rangtelwoorden[m[4].toLowerCase()])] : null;
            if (!e1 || (m[4] && !e2)) continue;
            var tijd;
            if (e2) {
                // "het zesde en het negende uur" — het dagdeel hoeft maar één keer
                tijd = (!e1.los && !e2.los && e1.deel === e2.deel)
                    ? e1.getal + ' en ' + e2.getal + ' uur ' + e1.deel
                    : this._tijdTekst(e1) + ' en ' + this._tijdTekst(e2);
            } else {
                tijd = this._tijdTekst(e1);
            }
            // Met voorzetsel of "ongeveer" ervoor leest "omstreeks" beter;
            // zonder die aanloop hoort er alsnog een slag om de arm bij.
            var nieuw = ((m[1] || m[2]) ? 'omstreeks ' : 'ongeveer ') + tijd;
            neem(start, eind, 'tijd-omgerekend', volgHoofdletter(m[0], nieuw),
                 'Oorspronkelijk: ' + m[0] + ' · ' + (T.uurUitleg[snacht ? 'nacht' : 'dag'] || ''));
        }

        // === Nachtwaken met rangtelwoord: "ter vierde wake in de nacht" ===
        var schema = T.waken[testament === 'NT' ? 'nt' : 'ot'] || {};
        T.waakRe.lastIndex = 0;
        while ((m = T.waakRe.exec(plain)) !== null) {
            var wStart = m.index, wEind = wStart + m[0].length;
            if (!vrij(wStart, wEind)) continue;
            var nr = T.rangtelwoorden[m[1].toLowerCase()];
            var bereik = schema[String(nr)];
            if (!bereik) continue;                  // "vierde wake" bestaat niet in een driedeling
            neem(wStart, wEind, 'tijd-omgerekend',
                 volgHoofdletter(m[0], 'nachtwake ' + bereik),
                 'Oorspronkelijk: ' + m[0] + ' · ' + (schema.uitleg || ''));
        }

        // === Vaste frasen: morgenwake, middelste nachtwaak, tussen twee avonden ===
        var regels = T.genoemdeWaken.concat(T.frases);
        for (var r = 0; r < regels.length; r++) {
            var g = regels[r];
            if (g.alleenIn && !this._maatInBereik(g.alleenIn, book, ch, vnum)) continue;
            g.re.lastIndex = 0;
            while ((m = g.re.exec(plain)) !== null) {
                var fStart = m.index, fEind = fStart + m[0].length;
                if (!vrij(fStart, fEind)) continue;
                neem(fStart, fEind, 'tijd-omgerekend',
                     volgHoofdletter(m[0], m[0].replace(g.enkel, g.vervang)),
                     'Oorspronkelijk: ' + m[0] + ' · ' + (g.uitleg || ''));
            }
        }

        // === Alleen toelichten: het avondoffer blijft een offer, geen kloktijd ===
        for (var t = 0; t < T.toelichtingen.length; t++) {
            var u = T.toelichtingen[t];
            u.re.lastIndex = 0;
            while ((m = u.re.exec(plain)) !== null) {
                var tStart = m.index, tEind = tStart + m[0].length;
                if (!vrij(tStart, tEind)) continue;
                neem(tStart, tEind, 'tijd-toelichting', null, u.uitleg || '');
            }
        }

        if (!stukken.length) return html;
        stukken.sort(function (a, b) { return a.van - b.van; });
        var uit = '', vorig = 0;
        for (var i = 0; i < stukken.length; i++) {
            if (stukken[i].van < vorig) continue;
            uit += html.slice(vorig, stukken[i].van) + stukken[i].nieuw;
            vorig = stukken[i].tot;
        }
        return uit + html.slice(vorig);
    },

    /** Eén kloktijd uitschrijven; middernacht krijgt geen "uur" achter zich. */
    _tijdTekst(e) {
        return e.los ? e.los : (e.getal + ' uur ' + e.deel);
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
            // Naslag- en wikipagina's hebben geen hoofdstukrouter. Hun
            // citaten luisteren naar ov:opties-gewijzigd en worden daar via
            // de gedeelde tekstcomponent vernieuwd, zonder navigatie.
            if (typeof OVTekstweergave !== 'undefined' && OVTekstweergave.verversCitaten) {
                OVTekstweergave.verversCitaten(document);
            }
        }
    },
};

// Globaal beschikbaar maken: een top-level `const` komt niet op window terecht,
// terwijl mobile-nav.js en app.js (boekvolgorde, doorlopend lezen) `window.Opties`
// gebruiken. Zonder deze regel valt de boekvolgorde altijd terug op 'canoniek'.
if (typeof window !== 'undefined') window.Opties = Opties;
