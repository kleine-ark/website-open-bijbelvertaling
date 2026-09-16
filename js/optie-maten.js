/* Bijbelse maten, gewichten en getalnotatie — gedeeld door de leesopties. */
const OptieMaten = {
    // ===================================================================
    // Maten, inhoudsmaten en gewichten — omrekenen naar een modern stelsel
    // -------------------------------------------------------------------
    // Bij `maatstelsel: 'metrisch'` of `'imperiaal'` blijft de Bijbelse maat in
    // de OV-tekst staan en volgt de moderne waarde tussen haakjes
    // ("driehonderd ellen (ongeveer 133 meter)").
    // Bij 'bijbels' verandert er niets aan de tekst. Standaard staat de optie
    // op 'metrisch' (zie Opties.DEFAULTS).
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
            while (links > 0 && this._getalSluitAan(E, plain, woorden, links - 1) &&
                this._maatMorfemen(E, woorden[links - 1].woord) !== null) links--;
            while (rechts + 1 < woorden.length && this._getalSluitAan(E, plain, woorden, rechts) &&
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

    /**
     * Horen twee opeenvolgende telwoorden bij hetzelfde getal?
     * Normaal staat er alleen witruimte tussen, maar de Statenvertaling zet
     * geregeld een komma achter de duizendtallen: "vijfduizend,
     * vierhonderdennegenenzestig" (3 Ezra 2:14) en "twee duizend, honderd
     * twee en zeventig" (Nehemia 7:8) zijn elk één getal. Volgt er na de
     * komma een koppelwoord, dan begint juist een nieuw getal — 1 Kronieken
     * 21:5 telt "vierhonderd duizend, en zeventig duizend" apart — en dan
     * blijven het er twee.
     */
    _getalSluitAan(E, plain, woorden, index) {
        var gat = plain.slice(woorden[index].eind, woorden[index + 1].start);
        if (/^\s+$/.test(gat)) return true;
        return /^,\s+$/.test(gat) &&
            /duizend$/.test(woorden[index].woord) &&
            E.scheiders.indexOf(woorden[index + 1].woord) === -1;
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
            // Nootcijfers en tags binnen het vervangen stuk mogen niet verdwijnen.
            // Staat het stuk HTML op zichzelf, dan gaat het in zijn geheel mee en
            // blijft het cijferbeeld op zijn plaats staan: "vijf en twintig (25)
            // ellen (ongeveer 13 meter)". Is de opmaak halverwege geopend, dan
            // blijft het bij de platte tekst met de tags erachter, want een halve
            // tag mag niet in de nieuwe span terechtkomen.
            var fragment = html.slice(map[g.start], map[eind]);
            var heel = this._maatHeelFragment(fragment);
            var behoud = heel ? '' : this._maatBehoudTags(fragment);
            stukken.push({
                van: map[g.start], tot: map[eind],
                nieuw: '<span class="maat-omgerekend" title="' +
                    this._maatAttr(uitleg) + '">' + (heel ? fragment : origineel) +
                    ' (' + nieuweTekst + ')</span>' + behoud,
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
     * een vers de eenheid maar één keer (bijvoorbeeld: “zestig ellen …
     * twintig in zijn breedte”). De bron blijft onaangeroerd; de tabel legt
     * per vers vast welk getal die eerder genoemde eenheid herhaalt.
     */
    _rekenImplicieteMaten(html, book, ch, vnum, stelsel, E) {
        var regels = E.implicieteMaten || [], zelf = this;
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
            var titel = 'Oorspronkelijk: ' + origineel + ' · ' +
                (regel.uitleg || 'de eenheid is in deze zin uit de directe context aangevuld');
            // Het cijferbeeld van toonGetalcijfers staat direct achter het
            // telwoord; de aangevulde maat hoort daarachter en niet ertussen.
            var zoekRe = new RegExp(this._maatEscape(regel.zoek) +
                '(\\s*<span[^>]*\\bgetal-cijfer\\b[^>]*>[^<]*<\\/span>)?');
            html = html.replace(zoekRe, function (heel) {
                return '<span class="maat-omgerekend maat-impliciet" title="' +
                    zelf._maatAttr(titel) + '">' + heel + ' (' + nieuw + ')</span>';
            });
        }
        return html;
    },

    /**
     * Projecteer HTML op platte tekst met een index-kaart terug naar de HTML.
     * Inhoud van <sup>…</sup> (de nootcijfers) telt niet mee, anders zou
     * "driehonderd<sup>37</sup> ellen" nooit als één getal + maat herkend worden.
     * Om dezelfde reden telt het cijferbeeld van toonGetalcijfers niet mee.
     * Dat komt tussen het telwoord en de maat te staan ("vijf en twintig
     * (25) ellen"), en zonder deze uitzondering zou juist vanaf eenentwintig
     * geen enkele maat meer omgerekend worden.
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
                } else if (/^<span[^>]*\bgetal-cijfer\b/i.test(html.slice(i, gt + 1))) {
                    var dichtCijfer = html.toLowerCase().indexOf('</span>', gt);
                    i = dichtCijfer === -1 ? gt + 1 : dichtCijfer + 7;
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

    /** Maak een zoekstring veilig voor gebruik in een RegExp. */
    _maatEscape(tekst) {
        return String(tekst).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    },

    /**
     * Staat dit stuk HTML op zichzelf, zonder halverwege geopende opmaak?
     * Alleen dan mag het in zijn geheel in een nieuwe span gezet worden.
     */
    _maatHeelFragment(fragment) {
        var stapel = [], re = /<(\/?)([A-Za-z][A-Za-z0-9]*)[^>]*?(\/?)>/g, m;
        while ((m = re.exec(fragment)) !== null) {
            if (m[3] === '/' || /^(br|img|hr|input|meta|link)$/i.test(m[2])) continue;
            if (m[1] === '/') {
                if (!stapel.length || stapel.pop() !== m[2].toLowerCase()) return false;
            } else {
                stapel.push(m[2].toLowerCase());
            }
        }
        return stapel.length === 0;
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
            // Eindigt een telwoord op een koppelwoord, dan is het een meervoud
            // en geen getal: "de duizenden van de hemel" (4 Ezra 13:3). Het losse
            // woord "en" blijft wel een koppeling tussen twee telwoorden.
            else if (i === n && res.length && E.scheiders.indexOf(gevonden) !== -1) return null;
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

};
window.OptieMaten = OptieMaten;
