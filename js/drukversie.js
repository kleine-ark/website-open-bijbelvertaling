/* Drukversie — een zelf samengestelde uitgave, pagina voor pagina opgemaakt.
 *
 * De tekst loopt door precies dezelfde bewerking als in de lezer: Opties.
 * transformOV, markeerGeo, rekenMaten en rekenTijden, in die volgorde. Dat is
 * geen keuze uit gemak maar uit noodzaak — zou deze pagina zijn eigen omzetting
 * doen, dan zou de drukproef stilletjes iets anders laten zien dan de site, en
 * juist dat verschil valt op papier niet meer te herstellen.
 *
 * Die omzetters laden hun tabellen lui en geven de tekst ongewijzigd terug
 * zolang die er niet zijn. Op de leespagina valt dat niet op, want daar wordt
 * na het laden opnieuw gerenderd; hier zou een lezer een uitgave afdrukken
 * waarin de maten stilzwijgend onomgerekend zijn gebleven. Vandaar dat alles
 * wat nodig is vóór het opmaken wordt binnengehaald.
 *
 * Opmaken gebeurt door te meten. Er bestaat geen manier om vooraf te weten waar
 * een pagina vol is, dus vullen we een blad tot het overloopt, halen het laatste
 * blok er weer af en beginnen een nieuw blad. Bij twee kolommen loopt een blad
 * niet in de hoogte over maar in de breedte — de tekst maakt een derde kolom
 * naast de tweede — en daarom wordt op allebei gemeten.
 *
 * De hele Bijbel is ruim eenendertigduizend verzen. Dat in een keer opmaken
 * duurt te lang en levert een pagina op die niet meer reageert, dus gaat het
 * per honderd bladen, met een knop voor de volgende ronde.
 */
(function () {
    'use strict';

    var PAGINAS_PER_RONDE = 100;

    var Druk = {
        boeken: null,
        gekozen: new Set(),
        /* De opdracht die nog te doen is: een vlakke lijst hoofdstukken. */
        wachtrij: [],
        klaar: 0,
        paginaNr: 0,
        bezig: false,
        perikopen: null,
        platen: null,           // boek-id -> hoofdstukken met een plaat

        /* Bladmaten in millimeters. De marge volgt de breedte in plaats van een
           vaste maat per formaat, anders staat een zakbijbel met de marge van
           een A4 op zijn kop. De factoren komen overeen met wat A4 en A5
           hiervoor hadden. */
        FORMATEN: {
            letter: [216, 279], a4: [210, 297], b5: [176, 250], royaal: [156, 234],
            a5: [148, 210], hand: [130, 190], zak: [115, 170], a6: [105, 148]
        },
        boekStart: {},          // boek-id -> eerste bladnummer, voor de inhoudsopgave

        VOORWOORD:
            'De Open Vertaling neemt de Statenvertaling van 1888 als basistekst. Verouderde ' +
            'naamvallen, werkwoordsvormen en woorden zijn vervangen door hedendaags Nederlands, ' +
            'maar de zinsbouw is gelaten zoals hij stond. Wie een zin herschrijft omdat hij hem ' +
            'mooier vindt is aan het vertalen en niet aan het herzien.\n\n' +
            'Elke wijziging loopt via een genummerd principe, zodat op elke plaats na te gaan is ' +
            'waaróm daar iets anders staat dan in 1888. Die principes staan openbaar op ' +
            'openvertaling.nl, met hun vindplaatsen erbij.\n\n' +
            'Deze uitgave is samengesteld met de drukversie op de website. De keuzes die u daar ' +
            'maakte — de Godsnaam, de maten, de namen, de opmaak — staan in deze afdruk vast; ' +
            'op de website kan elke lezer ze zelf anders zetten.',

        /* De leesopties die op een gedrukte uitgave van toepassing zijn. De
           overige — thema, kolomindeling, Strong-nummers — gaan over het scherm
           en horen hier niet thuis. */
        LEESOPTIES: [
            ['godsnaam', 'Godsnaam', [['ov', 'JAHWEH'], ['klassiek', 'de HEERE'],
                ['jehovah', 'Jehovah'], ['jhwh', 'יהוה']]],
            ['heereNT', 'Aanspreektitel in het NT', [['heere', 'Heere'], ['here', 'Here']]],
            ['jezusNaam', 'Naam van Jezus', [['nl', 'Jezus Christus'], ['hebreeuws', 'Yeshua HaMashiach'],
                ['koranisch', 'Isa'], ['arabisch', 'Yasūʿ al-Masīḥ']]],
            ['arabischeNamen', 'Arabische naamvormen', [['uit', 'Nederlands'], ['aan', 'Musa, Ibrahim, Isa']]],
            ['otSheol', 'Sheol in het OT', [['dodenrijk', 'dodenrijk'], ['hel', 'hel']]],
            ['maatstelsel', 'Maten en gewichten', [['bijbels', 'bijbels'], ['metrisch', 'metrisch'],
                ['imperiaal', 'imperiaal']]],
            ['tijdrekening', 'Tijdsaanduidingen', [['bijbels', 'de derde ure'], ['modern', 'omgerekend']]],
            ['getalweergave', 'Getallen', [['woorden', 'in woorden'], ['cijfers', 'met cijfers erbij']]],
            ['citaten', 'Citaatopmaak', [['aan', 'aan'], ['uit', 'uit']]],
            ['geoMarkeren', 'Plaatsnamen markeren', [['uit', 'uit'], ['aan', 'aan (Tora)']]],
            ['boekvolgorde', 'Boekvolgorde', [['canoniek', 'canoniek'], ['tenach', 'Tenach'],
                ['orthodox', 'Septuaginta'], ['ethiopisch', 'Ethiopisch'],
                ['chronologisch', 'chronologisch'], ['auteur', 'op auteur'], ['lengte', 'op lengte']]]
        ],

        /* Tien voorbeelduitgaven. Elk recept zet niet alleen welke boeken erin
           gaan, maar ook het papier, de kolommen, de volgorde en het omslag --
           anders is een uitgave niet meer dan een selectievakje, terwijl het
           juist die combinatie is die een boek zijn karakter geeft. Alles blijft
           daarna met de hand bij te stellen. */
        UITGAVEN: {
            alles: {
                boeken: 'westers', volgorde: 'canoniek', omslag: '01-klassiek',
                ondertitel: 'Open Vertaling',
                velden: { 'dv-formaat': 'a5', 'dv-kolommen': '2', 'dv-marge': 'normaal',
                          'dv-notities': 'geen', 'dv-versregels': false }
            },
            ot: {
                boeken: 'ot', volgorde: 'canoniek', omslag: '03-bergen-regenboog',
                ondertitel: 'Het Oude Testament',
                velden: { 'dv-formaat': 'a5', 'dv-kolommen': '2', 'dv-marge': 'normaal',
                          'dv-notities': 'geen', 'dv-versregels': false }
            },
            nt: {
                boeken: 'nt', volgorde: 'canoniek', omslag: '04-rivier-zonsopkomst',
                ondertitel: 'Het Nieuwe Testament',
                velden: { 'dv-formaat': 'hand', 'dv-kolommen': '2', 'dv-marge': 'normaal',
                          'dv-notities': 'geen', 'dv-versregels': false }
            },
            'taurat-injil': {
                boeken: ['genesis', 'johannes'], volgorde: 'canoniek', omslag: '02-paradijstuin',
                ondertitel: 'Taurat en Injil',
                velden: { 'dv-formaat': 'a5', 'dv-kolommen': '1', 'dv-marge': 'ruim',
                          'dv-notities': 'geen', 'dv-versregels': true }
            },
            tora: {
                boeken: ['genesis', 'exodus', 'leviticus', 'numeri', 'deuteronomium'],
                volgorde: 'tenach', omslag: '05-bloemenweide', ondertitel: 'De Tora',
                velden: { 'dv-formaat': 'a5', 'dv-kolommen': '2', 'dv-marge': 'normaal',
                          'dv-notities': 'geen', 'dv-versregels': false }
            },
            evangelien: {
                boeken: ['mattheus', 'markus', 'lukas', 'johannes'],
                volgorde: 'canoniek', omslag: '04-rivier-zonsopkomst',
                ondertitel: 'De vier Evangelien',
                velden: { 'dv-formaat': 'a6', 'dv-kolommen': '1', 'dv-marge': 'krap',
                          'dv-notities': 'geen', 'dv-versregels': false }
            },
            'psalmen-spreuken': {
                boeken: ['psalmen', 'spreuken'], volgorde: 'canoniek', omslag: '05-bloemenweide',
                ondertitel: 'Psalmen en Spreuken',
                velden: { 'dv-formaat': 'zak', 'dv-kolommen': '1', 'dv-marge': 'krap',
                          'dv-notities': 'geen', 'dv-versregels': true }
            },
            ethiopisch: {
                boeken: 'alles', volgorde: 'ethiopisch', omslag: '06-sober-nachtblauw',
                ondertitel: 'Ethiopische canon',
                velden: { 'dv-formaat': 'b5', 'dv-kolommen': '2', 'dv-marge': 'normaal',
                          'dv-notities': 'geen', 'dv-versregels': false }
            },
            orthodox: {
                boeken: 'westers', volgorde: 'orthodox', omslag: '06-sober-nachtblauw',
                ondertitel: 'Naar de Septuaginta',
                velden: { 'dv-formaat': 'b5', 'dv-kolommen': '2', 'dv-marge': 'normaal',
                          'dv-notities': 'geen', 'dv-versregels': false }
            },
            bijschrijf: {
                boeken: 'westers', volgorde: 'canoniek', omslag: '01-klassiek',
                ondertitel: 'Bijschrijfbijbel',
                velden: { 'dv-formaat': 'a4', 'dv-kolommen': '1', 'dv-marge': 'krap',
                          'dv-notities': 'zij', 'dv-notitiemaat': '60', 'dv-lijntjes': true,
                          'dv-versregels': false }
            }
        },

        async init() {
            var manifest = await DataLoader.loadManifest();
            this.boeken = (manifest && manifest.books) || [];
            // Eigen staat, los van wat de lezer op de site heeft ingesteld: een
            // drukproef hoort de voorkeuren van de lezer niet te overschrijven.
            Opties.state = Object.assign({}, Opties.DEFAULTS);
            // In de lezer bepalen deze twee of de apocriefen en de Ethiopische
            // boeken in de zijbalk staan. Hier doen de vinkjes bij "Wat erin
            // komt" dat werk; stonden ze uit, dan liet getFlatBookOrder de
            // Ethiopische boeken weg en verdwenen ze stil uit de Ethiopische
            // uitgave, ook al waren ze aangevinkt.
            Opties.state.apocriefeBoeken = 'aan';
            Opties.state.ethiopischeBoeken = 'aan';
            Opties._initialized = true;
            document.getElementById('dv-voorwoord-tekst').value = this.VOORWOORD;
            this.vulBoekenlijst();
            this.vulLeesopties();
            this.bindPaneel();
            this.kiesUitgave('alles');
            this.pasInstellingenToe();
            // kiesUitgave heeft zojuist een uitgestelde opmaak ingepland; die
            // hoeft niet ook nog eens boven op deze eerste.
            clearTimeout(this._wachtOpRust);
            this.bouw();
        },

        boekenPerTestament() {
            var groepen = [['OT', 'Oude Testament'], ['NT', 'Nieuwe Testament'],
                ['AP', 'Apocriefen'], ['ET', 'Ethiopische boeken']];
            var uit = [];
            groepen.forEach(function (g) {
                var lijst = this.boeken.filter(function (b) { return b.testament === g[0]; });
                if (lijst.length) uit.push([g[1], lijst]);
            }, this);
            return uit;
        },

        vulBoekenlijst() {
            var houder = document.getElementById('dv-boekenlijst');
            var html = '';
            this.boekenPerTestament().forEach(function (groep) {
                html += '<h3>' + groep[0] + '</h3>';
                groep[1].forEach(function (b) {
                    html += '<label><input type="checkbox" value="' + b.id + '"> ' +
                        b.nameDutch + '</label>';
                });
            });
            houder.innerHTML = html;
            houder.addEventListener('change', function (e) {
                if (e.target.type !== 'checkbox') return;
                if (e.target.checked) this.gekozen.add(e.target.value);
                else this.gekozen.delete(e.target.value);
                document.getElementById('dv-uitgave').value = 'eigen';
                this.werkTellingBij();
            }.bind(this));
        },

        vulLeesopties() {
            var houder = document.getElementById('dv-leesopties');
            var html = '';
            this.LEESOPTIES.forEach(function (o) {
                html += '<label class="dv-veld"><span>' + o[1] + '</span><select data-leesoptie="' +
                    o[0] + '">';
                o[2].forEach(function (keuze) {
                    var gekozen = Opties.DEFAULTS[o[0]] === keuze[0] ? ' selected' : '';
                    html += '<option value="' + keuze[0] + '"' + gekozen + '>' + keuze[1] + '</option>';
                });
                html += '</select></label>';
            });
            houder.innerHTML = html;
            houder.addEventListener('change', function (e) {
                var sleutel = e.target.getAttribute('data-leesoptie');
                if (!sleutel) return;
                Opties.state[sleutel] = e.target.value;
                this.meldWijziging();
            }.bind(this));
        },

        /* Welke boeken horen bij een recept: een lijst met namen, of een van de
           korte aanduidingen. 'westers' is alles behalve de Ethiopische boeken;
           'alles' is werkelijk alles, alle achtentachtig. */
        boekenVoor(spec) {
            if (Array.isArray(spec)) return spec.slice();
            var boeken = this.boeken;
            if (spec === 'alles') return boeken.map(function (b) { return b.id; });
            if (spec === 'westers') {
                return boeken.filter(function (b) { return b.testament !== 'ET'; })
                    .map(function (b) { return b.id; });
            }
            var t = String(spec).toUpperCase();
            return boeken.filter(function (b) { return b.testament === t; })
                .map(function (b) { return b.id; });
        },

        kiesUitgave(keuze) {
            var recept = this.UITGAVEN[keuze];
            if (!recept) return;        // 'eigen' laat de aangevinkte boeken staan
            var ids = this.boekenVoor(recept.boeken);

            Object.keys(recept.velden || {}).forEach(function (id) {
                var el = document.getElementById(id);
                if (!el) return;
                if (el.type === 'checkbox') el.checked = !!recept.velden[id];
                else el.value = recept.velden[id];
            });
            if (recept.volgorde) {
                Opties.state.boekvolgorde = recept.volgorde;
                var keuzelijst = document.querySelector('[data-leesoptie="boekvolgorde"]');
                if (keuzelijst) keuzelijst.value = recept.volgorde;
            }
            if (recept.omslag !== undefined) document.getElementById('dv-omslag').value = recept.omslag;
            if (recept.titel) document.getElementById('dv-titel').value = recept.titel;
            if (recept.ondertitel) document.getElementById('dv-ondertitel').value = recept.ondertitel;
            this.pasInstellingenToe();

            this.gekozen = new Set(ids);
            document.querySelectorAll('#dv-boekenlijst input').forEach(function (c) {
                c.checked = this.gekozen.has(c.value);
            }, this);
            this.werkTellingBij();
        },

        werkTellingBij() {
            var n = this.gekozen.size;
            document.getElementById('dv-boeken-telling').textContent =
                '— ' + n + (n === 1 ? ' boek' : ' boeken');
            this.meldWijziging();
        },

        /* Een wijziging wordt meteen doorgevoerd. Dat kan omdat er per ronde maar
           honderd bladen worden opgemaakt: opnieuw beginnen kost een paar tellen,
           en dat weegt niet op tegen een knop die je bij elke keuze moet
           aanklikken. Wat er al voorbij die honderd lag gaat wel verloren -- dat
           moet u opnieuw ophalen met "Volgende honderd pagina's".
           Het uitstel vangt het slepen aan een schuifregelaar op; anders zou elke
           tussenstand een hele opmaak in gang zetten. */
        meldWijziging() {
            var self = this;
            clearTimeout(this._wachtOpRust);
            if (!this.boeken) return;       // de eerste opmaak wacht op books.json
            this.zetStatus('Bezig met opnieuw opmaken…');
            this._wachtOpRust = setTimeout(function () {
                // Loopt er nog een ronde, dan wacht de nieuwe keuze tot die af is;
                // bouw() zou hem anders zonder meer laten vallen.
                if (self.bezig) { self._opnieuw = true; return; }
                self.bouw();
            }, 350);
        },

        /* Titel, ondertitel en de tekst van het voorwoord raken de bladspiegel
           niet: daarvoor hoeft alleen het voorwerk opnieuw. */
        werkVoorwerkBij() {
            if (!document.getElementById('dv-paginas').children.length) return;
            this.bouwVoorwerk();
        },

        zetStatus(tekst) { document.getElementById('dv-status').textContent = tekst; },

        bindPaneel() {
            var self = this;
            document.getElementById('dv-uitgave').addEventListener('change', function () {
                self.kiesUitgave(this.value);
                if (this.value !== 'eigen') document.getElementById('dv-boeken-details').open = false;
            });
            // Deze keuzes veranderen de bladspiegel: de opmaak moet opnieuw.
            ['dv-formaat', 'dv-breedte-mm', 'dv-hoogte-mm', 'dv-kolommen', 'dv-marge',
             'dv-letter', 'dv-grootte', 'dv-interlinie', 'dv-notities', 'dv-notitiemaat',
             'dv-tussenkopjes', 'dv-inleiding', 'dv-platen', 'dv-kanttekeningen',
             'dv-versnummers', 'dv-versregels', 'dv-sierletter', 'dv-kopregel'].forEach(function (id) {
                document.getElementById(id).addEventListener('input', function () {
                    self.pasInstellingenToe();
                    self.meldWijziging();
                });
            });
            // Deze niet: alleen het voorwerk of de lijntjes veranderen.
            ['dv-lijntjes', 'dv-lijnafstand', 'dv-cover', 'dv-omslag', 'dv-titel', 'dv-ondertitel', 'dv-voorwoord',
             'dv-voorwoord-tekst', 'dv-inhoudsopgave'].forEach(function (id) {
                document.getElementById(id).addEventListener('input', function () {
                    self.pasInstellingenToe();
                    self.werkVoorwerkBij();
                });
            });
            document.getElementById('dv-bouw').addEventListener('click', function () { self.bouw(); });
            document.getElementById('dv-print').addEventListener('click', function () { window.print(); });
            document.getElementById('dv-verder-knop').addEventListener('click', function () {
                self.rendeerRonde();
            });
        },

        /* Paneel -> CSS-variabelen en kenmerken op body. De maten staan in
           millimeters omdat een blad op het scherm even groot hoort te zijn als
           op papier. */
        pasInstellingenToe() {
            var b = document.body, s = b.style;
            var formaat = document.getElementById('dv-formaat').value;
            var marge = document.getElementById('dv-marge').value;
            var maat = this.FORMATEN[formaat];
            if (!maat) {
                maat = [+document.getElementById('dv-breedte-mm').value || 148,
                        +document.getElementById('dv-hoogte-mm').value || 210];
            } else {
                document.getElementById('dv-breedte-mm').value = maat[0];
                document.getElementById('dv-hoogte-mm').value = maat[1];
            }
            b.dataset.formaat = formaat;
            this.bladmaat = maat;
            s.setProperty('--dv-breedte', maat[0] + 'mm');
            s.setProperty('--dv-hoogte', maat[1] + 'mm');

            var m = Math.round(maat[0] * {krap: 0.050, normaal: 0.072, ruim: 0.100}[marge]);
            // Boven en onder moet de kopregel er nog bij kunnen; zonder kopregel
            // mag de tekst dichter naar de snijrand toe.
            var kopregel = document.getElementById('dv-kopregel').checked;
            var v = Math.max(m, kopregel ? 11 : 6);
            s.setProperty('--dv-marge-boven', v + 'mm');
            s.setProperty('--dv-marge-onder', v + 'mm');
            s.setProperty('--dv-marge-binnen', m + 'mm');
            s.setProperty('--dv-marge-buiten', m + 'mm');

            // De notitieruimte komt niet uit de marge maar uit het tekstblok:
            // zij zit aan de buitenkant, waar de hand bij kan zonder over de rug
            // te schrijven, of onderaan over de hele breedte.
            var waar = document.getElementById('dv-notities').value;
            var maat = document.getElementById('dv-notitiemaat').value + 'mm';
            s.setProperty('--dv-notitie-zij', waar === 'zij' ? maat : '0mm');
            s.setProperty('--dv-notitie-onder', waar === 'onder' ? maat : '0mm');
            document.getElementById('dv-notitiemaat-uit').textContent =
                document.getElementById('dv-notitiemaat').value + ' mm';
            b.dataset.notities = waar;
            // De lijntjes staan los van de regelafstand van de tekst: met de hand
            // schrijf je grover dan een zetter zet, en onderaan wil je er meer.
            var lijn = document.getElementById('dv-lijnafstand').value;
            s.setProperty('--dv-lijnafstand', lijn + 'mm');
            document.getElementById('dv-lijnafstand-uit').textContent = lijn + ' mm';

            s.setProperty('--dv-kolommen', document.getElementById('dv-kolommen').value);
            s.setProperty('--dv-grootte', (document.getElementById('dv-grootte').value / 10) + 'pt');
            s.setProperty('--dv-interlinie', document.getElementById('dv-interlinie').value / 100);

            b.dataset.marge = marge;
            b.dataset.letter = document.getElementById('dv-letter').value;
            b.dataset.lijntjes = document.getElementById('dv-lijntjes').checked ? 'aan' : 'uit';
            b.dataset.versnummers = document.getElementById('dv-versnummers').checked ? 'aan' : 'uit';
            b.dataset.versregels = document.getElementById('dv-versregels').checked ? 'aan' : 'uit';
            b.dataset.sierletter = document.getElementById('dv-sierletter').checked ? 'aan' : 'uit';
            b.dataset.kopregel = document.getElementById('dv-kopregel').checked ? 'aan' : 'uit';
            b.dataset.cover = document.getElementById('dv-cover').checked ? 'aan' : 'uit';
            b.dataset.voorwoord = document.getElementById('dv-voorwoord').checked ? 'aan' : 'uit';

            document.getElementById('dv-grootte-uit').textContent =
                (document.getElementById('dv-grootte').value / 10).toFixed(1).replace('.', ',') + ' pt';
            document.getElementById('dv-interlinie-uit').textContent =
                (document.getElementById('dv-interlinie').value / 100).toFixed(2).replace('.', ',');

            // De printer moet hetzelfde papier krijgen als het scherm laat zien.
            var regel = document.getElementById('dv-page-rule');
            if (!regel) {
                regel = document.createElement('style');
                regel.id = 'dv-page-rule';
                document.head.appendChild(regel);
            }
            regel.textContent = '@page { size: ' + maat[0] + 'mm ' + maat[1] + 'mm; margin: 0; }';
        },

        /* De tabellen die de omzetters nodig hebben. Zonder deze stap zouden
           maten, tijden en namen ongemerkt onvertaald blijven. */
        async laadTabellen() {
            var werk = [];
            var st = Opties.state;
            if (st.maatstelsel !== 'bijbels' || st.getalweergave === 'cijfers') werk.push(Opties.loadEenheden());
            if (st.tijdrekening === 'modern') werk.push(Opties.loadTijden());
            if (st.arabischeNamen === 'aan') werk.push(Opties.loadArabischeNamen());
            if (st.geoMarkeren === 'aan') werk.push(Opties.loadGeoData());
            if (document.getElementById('dv-tussenkopjes').checked && !this.perikopen) {
                werk.push(fetch('data/pericopen.json')
                    .then(function (r) { return r.ok ? r.json() : {}; })
                    .then(function (d) { Druk.perikopen = d; })
                    .catch(function () { Druk.perikopen = {}; }));
            }
            if (document.getElementById('dv-platen').checked && !this.platen) {
                werk.push(fetch('data/illustraties.json')
                    .then(function (r) { return r.ok ? r.json() : {}; })
                    .then(function (d) { Druk.platen = d; })
                    .catch(function () { Druk.platen = { map: '', platen: {} }; }));
            }
            if (werk.length) await Promise.all(werk);
        },

        async bouw() {
            if (this.bezig) return;
            if (!this.gekozen.size) { this.zetStatus('Kies eerst ten minste één boek.'); return; }
            document.getElementById('dv-leeg').hidden = true;
            document.getElementById('dv-paginas').innerHTML = '';
            document.getElementById('dv-verder').hidden = true;
            this.paginaNr = 0;
            this.klaar = 0;
            this.boekStart = {};
            this.zetStatus('Tabellen laden…');
            await this.laadTabellen();

            // Boekvolgorde volgens de gekozen ordening, beperkt tot de selectie.
            var volgorde;
            try {
                volgorde = getFlatBookOrder(Opties.state.boekvolgorde, { books: this.boeken });
            } catch (e) {
                volgorde = this.boeken.map(function (b) { return b.id; });
            }
            var perId = {};
            this.boeken.forEach(function (b) { perId[b.id] = b; });
            this.boekPerId = perId;
            this.volgordeIds = volgorde.filter(function (id) { return this.gekozen.has(id); }, this);

            this.wachtrij = [];
            volgorde.forEach(function (id) {
                if (!this.gekozen.has(id)) return;
                var boek = perId[id];
                if (!boek) return;
                (boek.chaptersIncluded || []).forEach(function (ch, i) {
                    this.wachtrij.push({ boek: boek, hoofdstuk: ch, eerste: i === 0 });
                }, this);
            }, this);

            await this.rendeerRonde();
        },

        async rendeerRonde() {
            if (this.bezig) return;
            this.bezig = true;
            var knop = document.getElementById('dv-verder-knop');
            knop.disabled = true;
            document.getElementById('dv-verder').hidden = true;

            var houder = document.getElementById('dv-paginas');
            var start = this.paginaNr;
            var pagina = this.nieuwePagina(houder);
            var inhoud = pagina.querySelector('.dv-inhoud');

            while (this.klaar < this.wachtrij.length && (this.paginaNr - start) < PAGINAS_PER_RONDE) {
                var taak = this.wachtrij[this.klaar];
                this.zetStatus('Bezig: ' + taak.boek.nameDutch + ' ' + taak.hoofdstuk +
                    ' — ' + this.paginaNr + ' bladen');
                var blokken = await this.blokkenVoorHoofdstuk(taak);

                // Een plaat vult de onderste helft van het blad. Staat er al
                // tekst op, dan begint het hoofdstuk op een nieuw blad: anders
                // zou de plaat een halfvolle bladzijde doormidden snijden.
                var plaat = this.plaatVoor(taak);
                if (plaat) {
                    if (inhoud.children.length) {
                        pagina = this.nieuwePagina(houder, taak.boek);
                        inhoud = pagina.querySelector('.dv-inhoud');
                    }
                    this.zetPlaat(pagina, plaat);
                }

                for (var i = 0; i < blokken.length; i++) {
                    inhoud.appendChild(blokken[i]);
                    if (this.looptOver(inhoud)) {
                        inhoud.removeChild(blokken[i]);
                        // Een leeg blad zou een blok opleveren dat nergens past;
                        // dan blijft het staan waar het staat.
                        if (!inhoud.children.length) { inhoud.appendChild(blokken[i]); continue; }
                        pagina = this.nieuwePagina(houder, taak.boek);
                        inhoud = pagina.querySelector('.dv-inhoud');
                        inhoud.appendChild(blokken[i]);
                        if ((this.paginaNr - start) >= PAGINAS_PER_RONDE) break;
                    }
                    this.zetBereik(pagina, taak.boek, taak.hoofdstuk);
                }
                this.klaar++;
                // De pagina moet tussendoor kunnen tekenen, anders lijkt hij vast te zitten.
                await new Promise(function (r) { setTimeout(r, 0); });
            }

            // Het voorwerk wordt na elke ronde opnieuw gemaakt: de
            // inhoudsopgave kent alleen de boeken die al opgemaakt zijn.
            this.bouwVoorwerk();

            this.bezig = false;
            knop.disabled = false;
            var rest = this.wachtrij.length - this.klaar;
            if (rest > 0) {
                document.getElementById('dv-verder').hidden = false;
                document.getElementById('dv-verder-tekst').textContent =
                    this.paginaNr + ' bladen opgemaakt. Er staan nog ' + rest +
                    (rest === 1 ? ' hoofdstuk' : ' hoofdstukken') + ' in de wachtrij.';
                this.zetStatus(this.paginaNr + ' bladen klaar, ' + rest + ' hoofdstukken te gaan.');
            } else {
                this.zetStatus('Klaar: ' + this.paginaNr + ' bladen.');
            }

            if (this._opnieuw) { this._opnieuw = false; this.bouw(); }
        },

        /* Het voorwerk komt vooraan maar wordt achteraf gemaakt: pas als de
           bladen er liggen is bekend op welke bladzijde elk boek begint. Dat is
           ook de reden dat het voorwerk zijn eigen nummering krijgt in Romeinse
           cijfers -- zou het meetellen, dan zou de inhoudsopgave zichzelf
           verschuiven zodra hij een blad langer werd. */
        romeins(n) {
            var tabel = [[10, 'x'], [9, 'ix'], [5, 'v'], [4, 'iv'], [1, 'i']], uit = '';
            tabel.forEach(function (p) { while (n >= p[0]) { uit += p[1]; n -= p[0]; } });
            return uit;
        },

        voorwerkPagina(klasse) {
            var p = document.createElement('div');
            p.className = 'dv-pagina dv-voorwerk ' + klasse;
            p.dataset.kolommen = '1';
            p.innerHTML = '<div class="dv-inhoud"></div><div class="dv-voet"><span></span></div>';
            return p;
        },

        bouwVoorwerk() {
            var houder = document.getElementById('dv-paginas');
            houder.querySelectorAll('.dv-voorwerk').forEach(function (p) { p.remove(); });
            var bladen = [];

            if (document.getElementById('dv-cover').checked) {
                var titel = document.getElementById('dv-titel').value.trim() || 'Open Vertaling';
                var onder = document.getElementById('dv-ondertitel').value.trim() ||
                    this.omschrijvingVanSelectie();
                var c = this.voorwerkPagina('dv-cover');
                // De omslagontwerpen staan er zonder tekst: GODS WOORD en
                // OPEN VERTALING worden hier als echte letters gezet, niet als
                // onderdeel van het beeld. Zo blijft de titel scherp en
                // aanpasbaar, en kan de drukker hem als vector overnemen.
                var omslag = document.getElementById('dv-omslag').value;
                if (omslag) {
                    c.classList.add('dv-cover-beeld');
                    c.style.backgroundImage =
                        'url("images/covers/gods-woord/web/' + omslag + '.webp")';
                }
                c.querySelector('.dv-inhoud').innerHTML =
                    '<div class="dv-cover-blok">' +
                    '<h1>' + this.tekstVeilig(titel) + '</h1>' +
                    (onder ? '<p class="dv-cover-onder">' + this.tekstVeilig(onder) + '</p>' : '') +
                    '<p class="dv-cover-voet">openvertaling.nl</p></div>';
                bladen.push(c);
            }

            if (document.getElementById('dv-voorwoord').checked) {
                var tekst = document.getElementById('dv-voorwoord-tekst').value.trim();
                if (tekst) {
                    var v = this.voorwerkPagina('dv-voorwoordblad');
                    v.querySelector('.dv-inhoud').innerHTML =
                        '<h2 class="dv-voorwerk-kop">Voorwoord</h2>' +
                        tekst.split(/\n{2,}/).map(function (a) {
                            return '<p class="dv-voorwoord-alinea">' + Druk.tekstVeilig(a) + '</p>';
                        }).join('');
                    bladen.push(v);
                }
            }

            if (document.getElementById('dv-inhoudsopgave').checked) {
                var regels = [];
                (this.volgordeIds || []).forEach(function (id) {
                    if (!this.boekStart[id]) return;   // nog niet opgemaakt
                    var boek = this.boekPerId[id];
                    regels.push('<li><span class="dv-io-naam">' + this.tekstVeilig(boek.nameDutch) +
                        '</span><span class="dv-io-punten"></span><span class="dv-io-nr">' +
                        this.boekStart[id] + '</span></li>');
                }, this);
                if (regels.length) {
                    var i = this.voorwerkPagina('dv-inhoudsblad');
                    i.querySelector('.dv-inhoud').innerHTML =
                        '<h2 class="dv-voorwerk-kop">Inhoud</h2><ul class="dv-io">' +
                        regels.join('') + '</ul>';
                    bladen.push(i);
                }
            }

            // achterstevoren invoegen, zodat de volgorde klopt
            for (var n = bladen.length - 1; n >= 0; n--) houder.insertBefore(bladen[n], houder.firstChild);
            bladen.forEach(function (blad, idx) {
                var voet = blad.querySelector('.dv-voet span');
                if (voet) voet.textContent = Druk.romeins(idx + 1);
                blad.classList.toggle('dv-links', (idx + 1) % 2 === 0);
            });
        },

        omschrijvingVanSelectie() {
            var keuze = document.getElementById('dv-uitgave');
            var label = keuze.options[keuze.selectedIndex].textContent;
            if (keuze.value === 'eigen') {
                var n = this.gekozen.size;
                return n === 1 ? this.boekPerId[[...this.gekozen][0]].nameDutch
                               : n + ' boeken';
            }
            // "Taurat & Injil — Genesis en Johannes" -> alleen het deel na de streep
            var streep = label.indexOf('—');
            return streep > 0 ? label.slice(streep + 1).trim() : label;
        },

        tekstVeilig(s) {
            return String(s).replace(/[&<>]/g, function (c) {
                return { '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c];
            });
        },

        /* De platen staan in data/illustraties.json: per boek de hoofdstukken die
           er een hebben, plus de map en de extensie. Ontbreekt het bestand of
           het hoofdstuk, dan gebeurt er niets -- de opmaak mag niet afhangen van
           beeldmateriaal dat er nog niet is. */
        plaatVoor(taak) {
            if (!document.getElementById('dv-platen').checked) return null;
            var bron = this.platen;
            if (!bron || !bron.platen) return null;
            var lijst = bron.platen[taak.boek.id];
            var naam = lijst && lijst[String(taak.hoofdstuk)];
            return naam ? (bron.map || '') + naam : null;
        },

        zetPlaat(pagina, bron) {
            pagina.classList.add('dv-met-plaat');
            var f = document.createElement('figure');
            f.className = 'dv-plaat';
            f.innerHTML = '<img src="' + bron + '" alt="">';
            // Ontbreekt het bestand, dan krijgt het blad zijn volle hoogte terug.
            f.firstChild.addEventListener('error', function () {
                pagina.classList.remove('dv-met-plaat');
                f.remove();
            });
            pagina.appendChild(f);
        },

        nieuwePagina(houder, boek) {
            this.paginaNr++;
            var p = document.createElement('div');
            p.className = 'dv-pagina' + (this.paginaNr % 2 === 0 ? ' dv-links' : '');
            p.dataset.kolommen = document.getElementById('dv-kolommen').value;
            p.innerHTML =
                '<div class="dv-kop"><span></span><span></span></div>' +
                '<div class="dv-inhoud"></div>' +
                '<div class="dv-voet"><span>' + this.paginaNr + '</span></div>';
            houder.appendChild(p);
            if (boek) this.zetBereik(p, boek, null);
            return p;
        },

        /* De kopregel van een bijbel noemt waar je bent, niet wie hem uitgeeft:
           links de boeknaam, rechts het hoofdstukbereik dat op het blad staat.
           Het bereik groeit mee terwijl het blad zich vult. */
        zetBereik(pagina, boek, hoofdstuk) {
            if (boek) {
                pagina._boek = boek;
                if (!this.boekStart[boek.id]) this.boekStart[boek.id] = this.paginaNr;
            }
            if (hoofdstuk != null) {
                if (pagina._hsVan == null) pagina._hsVan = hoofdstuk;
                pagina._hsTot = hoofdstuk;
            }
            var kop = pagina.querySelector('.dv-kop');
            if (!kop || !pagina._boek) return;
            var bereik = '';
            if (pagina._hsVan != null) {
                bereik = '' + pagina._hsVan +
                    (pagina._hsTot !== pagina._hsVan ? '–' + pagina._hsTot : '');
            }
            kop.children[0].textContent = pagina._boek.nameDutch;
            kop.children[1].textContent = bereik;
        },

        /* Een blad loopt bij een kolom in de hoogte over en bij twee kolommen in
           de breedte, want de tekst maakt dan een kolom naast de laatste. */
        looptOver(inhoud) {
            return inhoud.scrollHeight > inhoud.clientHeight + 1 ||
                   inhoud.scrollWidth > inhoud.clientWidth + 1;
        },

        async blokkenVoorHoofdstuk(taak) {
            var data = await DataLoader.loadChapter(taak.boek.id, taak.hoofdstuk);
            var blokken = [];
            var testament = taak.boek.testament;

            if (taak.eerste) {
                var t = document.createElement('h2');
                t.className = 'dv-boektitel';
                t.textContent = taak.boek.nameDutch;
                blokken.push(t);
            }
            var h = document.createElement('h3');
            h.className = 'dv-hoofdstuk';
            h.textContent = taak.boek.nameDutch + ' ' + taak.hoofdstuk;
            blokken.push(h);

            // Tussenkopjes staan per vers in data/pericopen.json en gaan door
            // dezelfde omzetting als de tekst, anders zou een kopje "de HEERE"
            // zeggen boven een stuk waar JAHWEH staat.
            var koppen = {};
            if (document.getElementById('dv-tussenkopjes').checked && this.perikopen) {
                (this.perikopen[taak.boek.id] || []).forEach(function (p) {
                    if (p.c === taak.hoofdstuk) koppen[p.v] = p.t;
                });
            }

            if (document.getElementById('dv-inleiding').checked && data && data.chapterIntro) {
                var intro = data.chapterIntro.text2026 || data.chapterIntro.textSV1888 ||
                    data.chapterIntro.text1637;
                if (intro) {
                    var p = document.createElement('p');
                    p.className = 'dv-inleiding';
                    p.innerHTML = this.schoon(intro);
                    blokken.push(p);
                }
            }

            var verzen = ((data && data.verses) || []).filter(function (v) { return v && v.number; });
            var noten = [];
            var sierletter = document.getElementById('dv-sierletter').checked;

            // Elk vers is een eigen element, ook bij doorlopende tekst. Zou een
            // heel hoofdstuk in één alinea staan, dan valt het niet te breken en
            // loopt elk blad over -- de eerste opzet leverde zo bladen op met
            // alleen een kopje erop. Of de verzen naast elkaar of onder elkaar
            // komen bepaalt de CSS, niet de opbouw.
            verzen.forEach(function (v, idx) {
                if (koppen[v.number]) {
                    var k = document.createElement('h4');
                    k.className = 'dv-tussenkop';
                    k.innerHTML = Opties.transformOV
                        ? Opties.transformOV(koppen[v.number], testament) : koppen[v.number];
                    blokken.push(k);
                }
                var tekst = v.text2026_html || v.text2026 || '';
                tekst = this.bewerk(tekst, taak.boek.id, taak.hoofdstuk, v.number, testament);
                tekst = this.schoon(tekst);
                if (sierletter && idx === 0) tekst = this.metSierletter(tekst);

                var r = document.createElement('span');
                r.className = 'dv-vers';
                r.innerHTML = '<span class="dv-versnr">' + v.number + '</span>' + tekst + ' ';
                blokken.push(r);
                if (document.getElementById('dv-kanttekeningen').checked) {
                    (v.marginNotes || []).forEach(function (n) {
                        var nt = n.text2026 || n.textSV1888;
                        if (nt) noten.push([taak.hoofdstuk + ':' + v.number, n.marker, nt]);
                    });
                }
            }, this);

            if (noten.length) {
                var blok = document.createElement('div');
                blok.className = 'dv-noten';
                blok.innerHTML = noten.map(function (n) {
                    return '<p class="dv-noot"><b>' + n[0] + '</b> ' +
                        Druk.schoon(String(n[2])) + '</p>';
                }).join('');
                blokken.push(blok);
            }
            return blokken;
        },

        /* Dezelfde keten als de lezer, in dezelfde volgorde. */
        bewerk(html, boekId, hs, vs, testament) {
            if (Opties.transformOV) html = Opties.transformOV(html, testament);
            if (Opties.markeerGeo) html = Opties.markeerGeo(html, boekId, hs, vs);
            if (Opties.rekenMaten) html = Opties.rekenMaten(html, boekId, hs, vs);
            if (Opties.rekenTijden) html = Opties.rekenTijden(html, boekId, hs, vs, testament);
            return html;
        },

        /* Nootmarkeringen en woordnummers horen niet in een drukproef; de
           citaatopmaak blijft, want die is een keuze in het paneel. */
        schoon(html) {
            return String(html)
                .replace(/<sup class="note-marker"[^>]*>.*?<\/sup>/g, '')
                .replace(/<span class="strongs[^"]*"[^>]*>.*?<\/span>/g, '')
                .replace(/\s{2,}/g, ' ')
                .trim();
        },

        metSierletter(html) {
            return html.replace(/([A-Za-zÀ-ÖØ-öø-ÿ])/, function (m) {
                return '<span class="dv-sierletter">' + m + '</span>';
            });
        }
    };

    window.Druk = Druk;
    document.addEventListener('DOMContentLoaded', function () {
        Druk.init().catch(function (e) {
            console.error(e);
            Druk.zetStatus('Er ging iets mis bij het laden: ' + e.message);
        });
    });
})();
