/* Open Vertaling — interactieve stamboom (stamboom.html).
 *
 * Leest data/stamboom.json (gemaakt door scripts/build_stamboom.py) en tekent
 * daar een VERTICALE boom van: Adam bovenaan, de generaties naar beneden.
 * Slepen en zoomen met muis én aanraking; losse namen kunnen met de hand
 * verplaatst worden.
 *
 * Waarom een INGESPRONGEN indeling
 * --------------------------------
 * De eerste opzet zette broers en zussen náást elkaar, zoals een gewone
 * stamboom. Dat werkt zolang alles dichtstaat, maar met 367 zichtbare namen
 * liep de tekening op tot ruim 19.000 pixels breed: horizontaal slepen over
 * twintig schermbreedtes. De breedte werd bepaald door het aantal broers en
 * zussen, en dat groeit onbeheersbaar.
 *
 * Daarom staat de boom nu als een REGISTER: kinderen onder hun ouder, elk
 * vertakkingsniveau een klein stukje naar rechts ingesprongen, met een dunne
 * verbindingslijn (de "rail") die van de ouder naar beneden loopt en bij elk
 * kind een streepje naar binnen maakt. De breedte hangt nu af van de diepte
 * van de VERTAKKING en niet meer van het aantal namen: van Adam tot Jezus zijn
 * er hoogstens 19 vertakkingsniveaus, dus 19 × 26 px inspringing.
 *
 * Twee bijzonderheden:
 *
 *   - EEN RECHTE AFSTAMMING SPRINGT NIET IN. Heeft iemand maar één zichtbaar
 *     kind, dan staat dat kind recht onder hem. Zo blijft de ingeklapte boom
 *     één smalle kolom die op een telefoon van 390 px past, en leest een
 *     rechte lijn van vader op zoon als één doorlopende streep.
 *   - BROERS EN ZUSSEN ZONDER NAKOMELINGEN LOPEN TERUG, zoals tekst afbreekt.
 *     De twintig kinderen van David of de dertien van Joktan vullen anders
 *     twintig regels; nu staan ze met een paar naast elkaar binnen een vaste
 *     regelbreedte. Alleen namen die zelf geen kinderen hebben doen mee, zodat
 *     nooit onduidelijk wordt wie van wie afstamt.
 *
 * De twee inklap-mechanismen van de eerste opzet blijven:
 *
 *   1. RECHTE STUKKEN WORDEN SAMENGEVOUWEN. Genesis 5 en 11 en de koningen van
 *      Juda zijn lange kettingen van vader op zoon. Zo'n keten wordt één
 *      schakel-vakje ("Seth › … › Lamech · 8 gen.") dat opengaat bij aantikken.
 *      Onderbroken wordt hij alleen bij een ANKER (Adam, Noach, Sem, Abraham,
 *      Izak, Jakob, Juda, David, Jechonia, Zerubbabel, Jozef, Jezus) of bij
 *      iemand van wie de zijtak openstaat.
 *   2. ZIJTAKKEN STAAN DICHT. Van iemand op de hoofdlijn is standaard alleen de
 *      zoon zichtbaar die de lijn voortzet; de rest zit achter een telbadge
 *      ("+12"). Wat openstaat wordt onthouden in de URL en in localStorage,
 *      zodat een gedeelde link hetzelfde toont.
 *
 * Bewust zonder externe bibliotheken: alles wat hier nodig is — verschuiven,
 * zoomen, knijpen, een eigen indeling — staat in een paar honderd regels, en
 * een tekenbibliotheek zou daar alleen gewicht en een tweede browserondergrens
 * aan toevoegen. Ook geen taalfeatures van na Safari 15.4 (dus geen lookbehind,
 * geen Object.groupBy, geen container queries): de site moet het op een iPad
 * met iPadOS 15.4 blijven doen.
 */
(function () {
    'use strict';

    // ── Maatvoering ───────────────────────────────────────────────────────
    // Ruimer dan een schema: leesbaarheid gaat hier boven compactheid.
    var DOOS_H = 26;           // hoogte van elk vakje (alle regels even hoog)
    var V_GAP = 7;             // ruimte tussen twee regels
    var RIJ = DOOS_H + V_GAP;  // verticale stap per regel
    var H_GAP = 16;            // ruimte tussen twee vakjes op dezelfde regel
    var INSPRING = 26;         // inspringing per vertakkingsniveau
    var RAIL = 12;             // afstand van de verbindingslijn tot de linkerrand
    var STROOM_B = 520;        // maximale regelbreedte voor teruglopende namen
    var PAD = 11;              // binnenmarge links/rechts in een vakje
    var BASIS = 18;            // basislijn van de tekst binnen het vakje
    var MAX_B = 260, MIN_B = 66;
    var MIN_K = 0.04, MAX_K = 3;

    var SERIF = '"EB Garamond", Garamond, Cambria, "Times New Roman", Georgia, serif';
    var SANS = '"Fira Sans", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';
    var FONT_NAAM = '15px ' + SERIF;
    var FONT_ANKER = '600 15px ' + SERIF;   // ankers staan vet; apart meten
    var FONT_BIJ = 'italic 12.5px ' + SERIF;
    var FONT_BADGE = '600 9.5px ' + SANS;

    var OPSLAG = 'sv2026_stamboom';
    var OPSLAG_VERZET = 'sv2026_stamboom_verzet';

    var canvas = document.getElementById('sb-canvas');
    var kaart = document.getElementById('sb-kaart');
    var hint = document.getElementById('sb-hint');
    var zoekVeld = document.getElementById('sb-zoek');
    var trefLijst = document.getElementById('sb-tref');
    if (!canvas) return;

    var DATA = null;            // hele JSON
    var P = null;               // personen (id -> object)
    var takOpen = {};           // id -> true: ook de zijtakken van deze persoon tonen
    var ketenOpen = {};         // begin-id van een keten -> true: keten uitgevouwen
    var verzet = {};            // sleutel -> {dx, dy}: met de hand verplaatst
    var spineKindVan = {};      // id -> kind dat de hoofdlijn voortzet
    var gekozen = null;         // id van de geopende persoonskaart
    var view = { x: 0, y: 0, k: 1 };
    var gEl = null;             // <g> waarop de transform staat
    var lijnLaag = null, knoopLaag = null;
    var plaats = {};            // id (of 'keten:'+id) -> {x, y}
    var knoopVan = {};          // sleutel -> weergaveknoop
    var ouderVan = {};          // sleutel -> weergaveknoop van de ouder
    var elVan = {};             // sleutel -> <g> in de tekening
    var lijnEl = {};            // sleutel -> {gewoon, lijn, via} <path>
    var laatsteBox = null;      // omhullende rechthoek van de tekening
    var aangeraakt = false;     // heeft de gebruiker zelf al verschoven/gezoomd?

    var SVGNS = 'http://www.w3.org/2000/svg';

    // ── Hulp ──────────────────────────────────────────────────────────────

    function esc(s) {
        return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function f(n) { return Math.round(n * 10) / 10; }

    // Combinerende accenttekens (U+0300–U+036F), als patroon opgeschreven zodat
    // deze regel zelf geen losse accenttekens bevat.
    var ACCENTEN = new RegExp('[\\u0300-\\u036f]', 'g');

    function plat(s) {
        var t = String(s).toLowerCase();
        if (t.normalize) t = t.normalize('NFD').replace(ACCENTEN, '');
        return t;
    }

    function klem(v, min, max) { return v < min ? min : (v > max ? max : v); }

    function persoon(id) { return (P && P[id]) ? P[id] : null; }

    var meetCtx;
    function breed(tekst, font) {
        if (meetCtx === undefined) {
            var c = document.createElement('canvas');
            meetCtx = (c && c.getContext) ? c.getContext('2d') : null;
        }
        if (!meetCtx) return String(tekst).length * (parseFloat(font) * 0.5);
        meetCtx.font = font;
        return meetCtx.measureText(String(tekst)).width;
    }

    function inkorten(tekst, max, font) {
        if (breed(tekst, font) <= max) return tekst;
        var t = String(tekst);
        while (t.length > 1 && breed(t + '…', font) > max) t = t.slice(0, -1);
        return t + '…';
    }

    // ── Structuur van de hoofdlijn ────────────────────────────────────────

    function bepaalSpineKinderen() {
        spineKindVan = {};
        for (var id in P) {
            var p = P[id];
            if (!p.hoofdlijn || !p.kinderen) continue;
            for (var i = 0; i < p.kinderen.length; i++) {
                if (P[p.kinderen[i]] && P[p.kinderen[i]].hoofdlijn) {
                    spineKindVan[id] = p.kinderen[i];
                    break;
                }
            }
        }
    }

    function spineKind(id) { return spineKindVan[id] || null; }

    function zichtbareKinderen(id) {
        var p = persoon(id);
        if (!p || !p.kinderen || !p.kinderen.length) return [];
        if (takOpen[id]) return p.kinderen;
        var sk = spineKind(id);
        return sk ? [sk] : [];
    }

    function verborgen(id) {
        var p = persoon(id);
        if (!p || !p.kinderen) return 0;
        return p.kinderen.length - zichtbareKinderen(id).length;
    }

    /** Vlak = mag in een samengevouwen keten verdwijnen. */
    function isVlak(id) {
        var p = persoon(id);
        return !!(p && p.hoofdlijn && !p.anker && !takOpen[id] && spineKind(id));
    }

    function ketenBegin(id) {
        var s = id;
        while (isVlak(s)) {
            var o = persoon(s).ouder;
            if (!o || !isVlak(o) || spineKind(o) !== s) break;
            s = o;
        }
        return s;
    }

    // ── Weergaveboom ──────────────────────────────────────────────────────
    // Elk weergaveknooppunt is óf één persoon óf een samengevouwen keten.

    function maakKnoop(id, inKeten) {
        if (!inKeten) {
            var run = [], cur = id;
            while (isVlak(cur)) { run.push(cur); cur = spineKind(cur); }
            if (run.length >= 2) {
                if (!ketenOpen[run[0]]) {
                    return { soort: 'keten', id: run[0], ids: run, kinderen: [maakKnoop(cur, false)] };
                }
                inKeten = true;      // uitgevouwen: elke schakel een eigen regel
            }
        } else if (!isVlak(id)) {
            inKeten = false;         // einde van de uitgevouwen keten
        }
        var kids = zichtbareKinderen(id), uit = [];
        for (var i = 0; i < kids.length; i++) uit.push(maakKnoop(kids[i], inKeten));
        return { soort: 'persoon', id: id, kinderen: uit };
    }

    function sleutelVan(dn) { return dn.soort === 'keten' ? 'keten:' + dn.id : dn.id; }

    /** Kinderloos = mag met broers en zussen op één teruglopende regel staan.
     *  Iemand met kinderen — ook als die dichtstaan — krijgt altijd een eigen
     *  regel, anders is niet meer te zien wie van wie afstamt. */
    function isKinderloos(dn) {
        if (dn.soort === 'keten' || dn.kinderen.length) return false;
        var p = persoon(dn.id);
        return !(p && p.kinderen && p.kinderen.length);
    }

    // ── Opmaak van één vakje ──────────────────────────────────────────────

    function partnerTekst(p) {
        if (!p.partners || !p.partners.length) return '';
        var namen = [];
        for (var i = 0; i < p.partners.length && i < 2; i++) {
            var q = persoon(p.partners[i]);
            if (q) namen.push(q.naam);
        }
        if (!namen.length) return '';
        var rest = p.partners.length - namen.length;
        return '× ' + namen.join(', ') + (rest > 0 ? ' +' + rest : '');
    }

    function opmaak(dn) {
        if (dn.opmaak) return dn.opmaak;
        var o = { badge: '', badgeB: 0, font: FONT_NAAM };
        if (dn.soort === 'keten') {
            var namen = [];
            for (var i = 0; i < dn.ids.length; i++) namen.push(persoon(dn.ids[i]).naam);
            o.naam = namen[0] + ' › … › ' + namen[namen.length - 1];
            o.bij = '';
            o.badge = dn.ids.length + ' gen.';
            o.titel = namen.join(' › ') + ' — klik om uit te vouwen';
        } else {
            var p = persoon(dn.id);
            o.naam = p.naam;
            o.bij = partnerTekst(p);
            if (p.anker) o.font = FONT_ANKER;
            // De badge is ook de knop. Zolang er iets verborgen is toont hij
            // hoeveel; staat de tak open, dan moet er een knop blijven staan om
            // hem weer dicht te doen. Anders kun je een tak wel openen maar
            // nooit meer sluiten, en groeit de boom alleen maar.
            var n = verborgen(dn.id);
            if (n > 0) {
                o.badge = '+' + n;
                o.titel = p.naam + (o.bij ? ' ' + o.bij : '') + ' — klik om ' + n +
                          (n === 1 ? ' tak' : ' takken') + ' te tonen';
            } else if (takOpen[dn.id] && p.kinderen && p.kinderen.length) {
                o.badge = '−';
                o.titel = p.naam + (o.bij ? ' ' + o.bij : '') + ' — klik om hier dicht te klappen';
            } else {
                o.titel = p.naam + (o.bij ? ' ' + o.bij : '');
            }
        }
        o.naamB = breed(o.naam, o.font);
        o.bijB = o.bij ? breed(o.bij, FONT_BIJ) : 0;
        o.badgeB = o.badge ? breed(o.badge, FONT_BADGE) + 11 : 0;
        var w = PAD + o.naamB + (o.bij ? 6 + o.bijB : 0) + (o.badge ? 7 + o.badgeB : 0) + PAD;
        if (w > MAX_B) {
            var ruimte = MAX_B - 2 * PAD - (o.badge ? 7 + o.badgeB : 0);
            if (o.bij) {
                o.bij = inkorten(o.bij, Math.max(26, ruimte - o.naamB - 6), FONT_BIJ);
                o.bijB = breed(o.bij, FONT_BIJ);
                ruimte -= o.bijB + 6;
            }
            o.naam = inkorten(o.naam, Math.max(34, ruimte), o.font);
            o.naamB = breed(o.naam, o.font);
            w = PAD + o.naamB + (o.bij ? 6 + o.bijB : 0) + (o.badge ? 7 + o.badgeB : 0) + PAD;
        }
        o.w = Math.max(MIN_B, Math.min(MAX_B, Math.ceil(w)));
        dn.opmaak = o;
        return o;
    }

    // ── Ordening: het ingesprongen register ───────────────────────────────
    //
    // plaatsKnoop zet de knoop op (x, y) en daaronder zijn kinderen, en geeft
    // terug op welke hoogte de volgende regel begint. dn.regels bewaart per
    // knoop welke kinderen op welke regel terechtkwamen; het tekenen van de
    // verbindingslijnen leest dat weer uit.

    function plaatsRegel(regel, x, y) {
        for (var i = 0; i < regel.length; i++) {
            regel[i].x = x;
            regel[i].y = y;
            x += regel[i].w + H_GAP;
        }
    }

    // `alleen` zegt of deze knoop het enige zichtbare kind van zijn ouder is.
    // Dat bepaalt of zijn eigen kind zonder inspringen recht eronder mag: dat
    // is de hoofdlijn. Staat de knoop tussen broers en zussen, dan moet zijn
    // kind wél inspringen, anders komt het op dezelfde hoogte als zijn ooms en
    // tantes te staan. Zo leek Henoch, de zoon van Kaïn, een vierde kind van
    // Adam: onder Adam las de lijst Kaïn, Henoch, Abel, Seth.
    function plaatsKnoop(dn, x, y, alleen) {
        dn.w = opmaak(dn).w;
        dn.x = x;
        dn.y = y;
        dn.regels = [];
        var kids = dn.kinderen, n = kids.length;
        var cy = y + RIJ;
        if (!n) return cy;

        // Eén zichtbaar kind = rechte afstamming: recht eronder, niet inspringen.
        dn.recht = (n === 1) && alleen !== false;
        var kx = dn.recht ? x : x + INSPRING;

        var i = 0;
        while (i < n) {
            // Zoek een aaneengesloten reeks kinderloze broers en zussen. Die
            // mogen teruglopen; de volgorde van geboorte blijft daarbij intact.
            var j = i;
            while (j < n && isKinderloos(kids[j])) j++;
            if (j - i >= 2) {
                var regel = [], breedte = 0;
                for (var q = i; q < j; q++) {
                    var kn = kids[q];
                    kn.w = opmaak(kn).w;
                    var erbij = regel.length ? H_GAP + kn.w : kn.w;
                    if (regel.length && breedte + erbij > STROOM_B) {
                        plaatsRegel(regel, kx, cy);
                        dn.regels.push(regel);
                        cy += RIJ;
                        regel = []; breedte = 0; erbij = kn.w;
                    }
                    regel.push(kn);
                    breedte += erbij;
                }
                if (regel.length) {
                    plaatsRegel(regel, kx, cy);
                    dn.regels.push(regel);
                    cy += RIJ;
                }
                i = j;
            } else {
                dn.regels.push([kids[i]]);
                cy = plaatsKnoop(kids[i], kx, cy, n === 1);
                i++;
            }
        }
        return cy;
    }

    function alleKnopen(wortel) {
        var uit = [], stapel = [wortel];
        while (stapel.length) {
            var dn = stapel.pop();
            uit.push(dn);
            for (var i = dn.kinderen.length - 1; i >= 0; i--) stapel.push(dn.kinderen[i]);
        }
        return uit;
    }

    // ── Verbindingslijnen ─────────────────────────────────────────────────

    function opHoofdlijn(dn) {
        if (dn.soort === 'keten') return true;
        var p = persoon(dn.id);
        return !!(p && p.hoofdlijn);
    }

    function lijnSoort(dn, kd) {
        if (kd.soort === 'persoon' && persoon(kd.id).viaMoeder) return 'via';
        if (opHoofdlijn(dn) && opHoofdlijn(kd)) return 'lijn';
        return 'gewoon';
    }

    /** De padstukken die onder één ouder horen, per lijnsoort. De rail — de
     *  lange verticale streep langs een hele zijtak — staat apart, zodat hij
     *  lichter getekend kan worden dan de streepjes naar de kinderen zelf.
     *  Bij een opengeklapte boom lopen sommige rails duizenden pixels door. */
    function lijnPaden(dn) {
        var uit = { rail: '', gewoon: '', lijn: '', via: '' };
        var regels = dn.regels;
        if (!regels || !regels.length) return uit;
        var railX = dn.px + RAIL;
        var onder = dn.py + DOOS_H;
        var i, j;

        // Rechte afstamming: één streep recht naar beneden.
        if (dn.recht && regels.length === 1 && regels[0].length === 1 &&
            Math.abs(regels[0][0].px - dn.px) < 0.5) {
            var kd = regels[0][0];
            uit[lijnSoort(dn, kd)] += 'M' + f(railX) + ' ' + f(onder) + 'V' + f(kd.py);
            return uit;
        }

        // Vertakking: een rail langs de linkerkant met een streepje per regel.
        var hoog = onder, laag = onder;
        for (i = 0; i < regels.length; i++) {
            var my = regels[i][0].py + DOOS_H / 2;
            if (my < hoog) hoog = my;
            if (my > laag) laag = my;
        }
        uit.rail += 'M' + f(railX) + ' ' + f(hoog) + 'V' + f(laag);
        for (i = 0; i < regels.length; i++) {
            var regel = regels[i];
            var y = regel[0].py + DOOS_H / 2;
            uit[lijnSoort(dn, regel[0])] += 'M' + f(railX) + ' ' + f(y) + 'H' + f(regel[0].px);
            // Teruggelopen broers en zussen: een dunne draad door de tussenruimte.
            for (j = 1; j < regel.length; j++) {
                var a = regel[j - 1], b = regel[j];
                uit[lijnSoort(dn, b)] += 'M' + f(a.px + a.w) + ' ' + f(a.py + DOOS_H / 2) +
                                         'L' + f(b.px) + ' ' + f(b.py + DOOS_H / 2);
            }
        }
        return uit;
    }

    var LIJN_KLASSE = {
        rail: 'sb-lijn is-rail', gewoon: 'sb-lijn',
        lijn: 'sb-lijn is-lijn', via: 'sb-lijn is-via'
    };

    /** Werkt de lijnen van één ouder bij zonder de hele tekening te herbouwen. */
    function hertekenLijnen(dn) {
        if (!lijnLaag) return;
        var sl = sleutelVan(dn);
        var paden = lijnPaden(dn);
        var set = lijnEl[sl] || (lijnEl[sl] = {});
        for (var soort in paden) {
            var d = paden[soort];
            var el = set[soort];
            if (!el) {
                if (!d) continue;
                el = document.createElementNS(SVGNS, 'path');
                el.setAttribute('class', LIJN_KLASSE[soort]);
                el.setAttribute('data-van', sl);
                el.setAttribute('data-stijl', soort);
                lijnLaag.appendChild(el);
                set[soort] = el;
            }
            el.setAttribute('d', d);
        }
    }

    // ── Tekenen ───────────────────────────────────────────────────────────

    function tekenKnoop(dn) {
        var o = opmaak(dn);
        var s = [], kl = 'sb-node', sleutel;
        if (dn.soort === 'keten') {
            kl += ' is-keten';
            sleutel = ' data-keten="' + esc(dn.id) + '"';
        } else {
            var p = persoon(dn.id);
            if (p.geslacht === 'v') kl += ' is-vrouw';
            if (p.soort === 'volk') kl += ' is-volk';
            if (p.hoofdlijn) kl += ' is-lijn';
            if (p.anker) kl += ' is-anker';
            if (dn.id === gekozen) kl += ' is-gekozen';
            sleutel = ' data-id="' + esc(dn.id) + '"';
        }
        s.push('<g class="' + kl + '" transform="translate(' + f(dn.px) + ' ' + f(dn.py) + ')"' +
               sleutel + '><title>' + esc(o.titel) + '</title>');
        s.push('<rect class="sb-doos" x="0" y="0" width="' + dn.w +
               '" height="' + DOOS_H + '" rx="3"/>');
        s.push('<text class="sb-naam" x="' + PAD + '" y="' + BASIS + '">' + esc(o.naam) + '</text>');
        if (o.bij) {
            s.push('<text class="sb-bij" x="' + f(PAD + o.naamB + 6) + '" y="' + BASIS + '">' +
                   esc(o.bij) + '</text>');
        }
        if (o.badge) {
            var kx = dn.w - PAD - o.badgeB;
            var attr = dn.soort === 'keten'
                ? ' data-keten="' + esc(dn.id) + '"'
                : ' data-klap="' + esc(dn.id) + '"';
            s.push('<g class="sb-badge' + (dn.soort === 'keten' ? ' is-keten' : '') + '"' + attr + '>' +
                   '<rect x="' + f(kx) + '" y="' + ((DOOS_H - 14) / 2) + '" width="' + f(o.badgeB) +
                   '" height="14" rx="7"/>' +
                   '<text x="' + f(kx + o.badgeB / 2) + '" y="' + ((DOOS_H - 14) / 2 + 10) +
                   '" text-anchor="middle">' + esc(o.badge) + '</text></g>');
        }
        s.push('</g>');
        return s.join('');
    }

    function teken() {
        var wortel = maakKnoop(DATA.wortel, false);
        plaatsKnoop(wortel, 0, 0);
        var knopen = alleKnopen(wortel);

        var i, j, dn;
        knoopVan = {}; ouderVan = {}; elVan = {}; lijnEl = {}; plaats = {};

        // Handmatig verplaatste knopen: het verzet bovenop de indeling leggen.
        for (i = 0; i < knopen.length; i++) {
            dn = knopen[i];
            var sl = sleutelVan(dn);
            knoopVan[sl] = dn;
            var v = verzet[sl];
            dn.px = dn.x + (v ? v.dx : 0);
            dn.py = dn.y + (v ? v.dy : 0);
            for (j = 0; j < dn.kinderen.length; j++) {
                ouderVan[sleutelVan(dn.kinderen[j])] = dn;
            }
        }

        var lijnen = [], vakjes = [];
        var minX = 1e9, maxX = -1e9, minY = 1e9, maxY = -1e9;

        for (i = 0; i < knopen.length; i++) {
            dn = knopen[i];
            var paden = lijnPaden(dn);
            var sleutel = sleutelVan(dn);
            for (var soort in paden) {
                if (!paden[soort]) continue;
                lijnen.push('<path class="' + LIJN_KLASSE[soort] + '" data-van="' + esc(sleutel) +
                            '" data-stijl="' + soort + '" d="' + paden[soort] + '"/>');
            }
            vakjes.push(tekenKnoop(dn));

            if (dn.px < minX) minX = dn.px;
            if (dn.px + dn.w > maxX) maxX = dn.px + dn.w;
            if (dn.py < minY) minY = dn.py;
            if (dn.py + DOOS_H > maxY) maxY = dn.py + DOOS_H;

            var mid = { x: dn.px + dn.w / 2, y: dn.py + DOOS_H / 2 };
            if (dn.soort === 'keten') {
                plaats['keten:' + dn.id] = mid;
                for (j = 0; j < dn.ids.length; j++) plaats[dn.ids[j]] = mid;
            } else {
                plaats[dn.id] = mid;
            }
        }

        laatsteBox = { x: minX - 12, y: minY - 12, w: (maxX - minX) + 24, h: (maxY - minY) + 24 };

        var laden = document.getElementById('sb-laden');
        if (laden && laden.parentNode) laden.parentNode.removeChild(laden);
        var oud = canvas.querySelector('svg');
        if (oud) canvas.removeChild(oud);
        var houder = document.createElement('div');
        houder.innerHTML = '<svg xmlns="' + SVGNS + '" aria-label="Stamboom van Adam tot Jezus">' +
                           '<g id="sb-g"><g id="sb-lijnen">' + lijnen.join('') +
                           '</g><g id="sb-knopen">' + vakjes.join('') + '</g></g></svg>';
        canvas.insertBefore(houder.firstChild, canvas.firstChild);
        gEl = document.getElementById('sb-g');
        lijnLaag = document.getElementById('sb-lijnen');
        knoopLaag = document.getElementById('sb-knopen');

        // Verwijzingen bewaren, zodat één verplaatste naam niet de hele
        // tekening opnieuw hoeft te laten opbouwen.
        var ps = lijnLaag.childNodes;
        for (i = 0; i < ps.length; i++) {
            var van = ps[i].getAttribute('data-van');
            (lijnEl[van] || (lijnEl[van] = {}))[ps[i].getAttribute('data-stijl')] = ps[i];
        }
        var gs = knoopLaag.childNodes;
        for (i = 0; i < gs.length && i < knopen.length; i++) elVan[sleutelVan(knopen[i])] = gs[i];

        toonHerstel();
        pasToe();
    }

    function pasToe() {
        if (gEl) {
            gEl.setAttribute('transform', 'translate(' + view.x.toFixed(2) + ' ' +
                view.y.toFixed(2) + ') scale(' + view.k.toFixed(4) + ')');
        }
    }

    // Handvat om vanaf de console de werkelijke tekengrootte te kunnen meten.
    window.sbAfmeting = function () {
        return laatsteBox ? { breedte: laatsteBox.w, hoogte: laatsteBox.h, schaal: view.k } : null;
    };

    // ── Beeld verplaatsen ─────────────────────────────────────────────────

    function maat() {
        var r = canvas.getBoundingClientRect();
        return { b: r.width, h: r.height, l: r.left, t: r.top };
    }

    function zoomNaar(k, cx, cy) {
        var nk = klem(k, MIN_K, MAX_K);
        if (nk === view.k) return;
        view.x = cx - (cx - view.x) * (nk / view.k);
        view.y = cy - (cy - view.y) * (nk / view.k);
        view.k = nk;
        pasToe();
    }

    function zoomKnop(fac) {
        var m = maat();
        aangeraakt = true;
        zoomNaar(view.k * fac, m.b / 2, m.h / 2);
    }

    function centreerOp(id, minK) {
        var pl = plaats[id];
        if (!pl) return;
        var m = maat();
        if (minK && view.k < minK) view.k = klem(minK, MIN_K, MAX_K);
        view.x = m.b / 2 - pl.x * view.k;
        view.y = m.h / 2 - pl.y * view.k;
        pasToe();
    }

    /** maxSchaal begrenst het inzoomen; opBreedte houdt de BREEDTE leidend.
     *
     *  Een register is hoog en smal. Alles in één keer passend maken levert bij
     *  een opengeklapte boom een streepje van negentig pixels op waar niets meer
     *  in te lezen valt. Met opBreedte wordt daarom nooit verder uitgezoomd dan
     *  de breedte vraagt (en nooit onder ware grootte als de breedte al past);
     *  verticaal scrolt de lezer mee, met Adam bovenaan. Scheelt het in de
     *  hoogte maar een randje, dan komt dat randje er alsnog bij. */
    function passend(maxSchaal, opBreedte) {
        if (!laatsteBox) return;
        var m = maat();
        var kb = m.b / laatsteBox.w, kh = m.h / laatsteBox.h;
        var k = Math.min(kb, kh, maxSchaal || MAX_K);
        if (opBreedte) {
            var bodem = Math.min(kb, 1);
            if (k < bodem) k = (kh >= bodem * 0.9) ? kh : bodem;
        }
        view.k = klem(k, MIN_K, maxSchaal || MAX_K);
        view.x = (m.b - laatsteBox.w * view.k) / 2 - laatsteBox.x * view.k;
        var hoogte = laatsteBox.h * view.k;
        if (hoogte > m.h) view.y = 12 - laatsteBox.y * view.k;   // bovenaan beginnen
        else view.y = (m.h - hoogte) / 2 - laatsteBox.y * view.k;
        pasToe();
    }

    function beginBeeld() {
        // De ingeklapte boom hoort in zijn geheel in beeld te staan. Past hij
        // ruim, dan mag hij tot 1,4× opgeschaald worden; past hij alleen in de
        // breedte, dan blijft hij op ware grootte staan met Adam bovenaan.
        passend(1.4, true);
    }

    // ── Knopen met de hand verplaatsen ────────────────────────────────────

    function leesVerzet() {
        try {
            var s = localStorage.getItem(OPSLAG_VERZET);
            var o = s ? JSON.parse(s) : null;
            if (o && typeof o === 'object') verzet = o;
        } catch (e) { /* privémodus */ }
    }

    function bewaarVerzet() {
        try {
            if (heeftVerzet()) localStorage.setItem(OPSLAG_VERZET, JSON.stringify(verzet));
            else localStorage.removeItem(OPSLAG_VERZET);
        } catch (e) { /* privémodus */ }
    }

    function heeftVerzet() { for (var k in verzet) { if (verzet[k]) return true; } return false; }

    function toonHerstel() {
        var el = document.getElementById('sb-herschik');
        if (el) el.hidden = !heeftVerzet();
    }

    function zetVerzet(sl, dx, dy) {
        verzet[sl] = { dx: Math.round(dx * 10) / 10, dy: Math.round(dy * 10) / 10 };
        var dn = knoopVan[sl];
        if (!dn) return;
        dn.px = dn.x + verzet[sl].dx;
        dn.py = dn.y + verzet[sl].dy;
        var el = elVan[sl];
        if (el) el.setAttribute('transform', 'translate(' + f(dn.px) + ' ' + f(dn.py) + ')');
        var mid = { x: dn.px + dn.w / 2, y: dn.py + DOOS_H / 2 };
        plaats[sl] = mid;
        if (dn.soort === 'keten') {
            for (var i = 0; i < dn.ids.length; i++) plaats[dn.ids[i]] = mid;
        } else {
            plaats[dn.id] = mid;
        }
        hertekenLijnen(dn);
        var ou = ouderVan[sl];
        if (ou) hertekenLijnen(ou);
    }

    function herschik() {
        verzet = {};
        bewaarVerzet();
        teken();
        aangeraakt = true;
    }

    /** Geeft de sleutel van de knoop onder een aangeraakt element, of null.
     *  Een tik op de telbadge telt niet als vastpakken: die klapt open. */
    function knoopOnder(el) {
        while (el && el !== canvas) {
            if (el.getAttribute) {
                var kl = el.getAttribute('class');
                if (kl && kl.indexOf('sb-badge') > -1) return null;
                if (kl && kl.indexOf('sb-node') > -1) {
                    var id = el.getAttribute('data-id');
                    if (id) return id;
                    var kt = el.getAttribute('data-keten');
                    if (kt) return 'keten:' + kt;
                    return null;
                }
            }
            el = el.parentNode;
        }
        return null;
    }

    var sleepKnoop = null;

    function beginKnoopSleep(sl, cx, cy) {
        var oud = verzet[sl] || { dx: 0, dy: 0 };
        sleepKnoop = { sl: sl, x: cx, y: cy, dx0: oud.dx, dy0: oud.dy, actief: false };
    }

    function knoopSleepStap(cx, cy) {
        if (!sleepKnoop) return;
        if (!sleepKnoop.actief) {
            sleepKnoop.actief = true;
            var el = elVan[sleepKnoop.sl];
            if (el) el.setAttribute('class', el.getAttribute('class') + ' is-pakt');
        }
        zetVerzet(sleepKnoop.sl,
            sleepKnoop.dx0 + (cx - sleepKnoop.x) / view.k,
            sleepKnoop.dy0 + (cy - sleepKnoop.y) / view.k);
    }

    function eindKnoopSleep() {
        if (!sleepKnoop) return;
        if (sleepKnoop.actief) {
            var el = elVan[sleepKnoop.sl];
            if (el) el.setAttribute('class', el.getAttribute('class').replace(/ is-pakt/, ''));
            bewaarVerzet();
            toonHerstel();
            aangeraakt = true;
        }
        sleepKnoop = null;
    }

    // ── Muis ──────────────────────────────────────────────────────────────

    var sleep = null, raakteBezig = false, verplaatst = 0;

    canvas.addEventListener('mousedown', function (e) {
        if (raakteBezig || e.button !== 0) return;
        verplaatst = 0;
        var sl = knoopOnder(e.target);
        if (sl) { beginKnoopSleep(sl, e.clientX, e.clientY); return; }
        sleep = { x: e.clientX, y: e.clientY, vx: view.x, vy: view.y };
        canvas.classList.add('sb-sleept');
    });
    window.addEventListener('mousemove', function (e) {
        if (sleepKnoop) {
            var ax = e.clientX - sleepKnoop.x, ay = e.clientY - sleepKnoop.y;
            verplaatst = Math.max(verplaatst, Math.abs(ax) + Math.abs(ay));
            if (!sleepKnoop.actief && verplaatst < 5) return;
            knoopSleepStap(e.clientX, e.clientY);
            verbergHint();
            return;
        }
        if (!sleep) return;
        var dx = e.clientX - sleep.x, dy = e.clientY - sleep.y;
        verplaatst = Math.max(verplaatst, Math.abs(dx) + Math.abs(dy));
        view.x = sleep.vx + dx;
        view.y = sleep.vy + dy;
        aangeraakt = true;
        pasToe();
        verbergHint();
    });
    window.addEventListener('mouseup', function () {
        eindKnoopSleep();
        sleep = null;
        canvas.classList.remove('sb-sleept');
    });

    canvas.addEventListener('wheel', function (e) {
        e.preventDefault();
        var m = maat();
        // Eén sprong per gebeurtenis begrenzen: sommige trackpads sturen enorme
        // deltaY-waarden en de boom zou dan wegschieten.
        var fac = klem(Math.pow(0.9982, e.deltaY * (e.deltaMode === 1 ? 16 : 1)), 0.6, 1.6);
        aangeraakt = true;
        zoomNaar(view.k * fac, e.clientX - m.l, e.clientY - m.t);
        verbergHint();
    }, { passive: false });

    // ── Aanraking ─────────────────────────────────────────────────────────
    //
    // Eén vinger verschuift het beeld. Wie een naam wil verplaatsen houdt hem
    // even vast: na een halve seconde stilstaan pakt de vinger de naam op.

    var raak = null, pakTimer = null;

    function afstand(t) {
        var dx = t[0].clientX - t[1].clientX, dy = t[0].clientY - t[1].clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }

    function stopPakTimer() {
        if (pakTimer) { clearTimeout(pakTimer); pakTimer = null; }
    }

    canvas.addEventListener('touchstart', function (e) {
        raakteBezig = true;
        stopPakTimer();
        var t = e.touches;
        if (t.length === 1) {
            raak = { soort: 1, x: t[0].clientX, y: t[0].clientY, vx: view.x, vy: view.y };
            verplaatst = 0;
            var sl = knoopOnder(e.target);
            if (sl) {
                var cx = t[0].clientX, cy = t[0].clientY;
                pakTimer = setTimeout(function () {
                    pakTimer = null;
                    if (verplaatst > 8) return;
                    // Het kleine beetje verschuiving van het beeld terugdraaien.
                    view.x = raak.vx; view.y = raak.vy;
                    pasToe();
                    beginKnoopSleep(sl, cx, cy);
                    knoopSleepStap(cx, cy);
                    verbergHint();
                }, 450);
            }
        } else if (t.length >= 2) {
            eindKnoopSleep();
            var m = maat();
            raak = {
                soort: 2, d: afstand(t), k: view.k,
                cx: (t[0].clientX + t[1].clientX) / 2 - m.l,
                cy: (t[0].clientY + t[1].clientY) / 2 - m.t,
                mx: (t[0].clientX + t[1].clientX) / 2,
                my: (t[0].clientY + t[1].clientY) / 2,
                vx: view.x, vy: view.y
            };
            verplaatst = 99;
        }
    }, { passive: true });

    canvas.addEventListener('touchmove', function (e) {
        if (!raak) return;
        e.preventDefault();
        var t = e.touches;
        if (sleepKnoop && t.length === 1) {
            knoopSleepStap(t[0].clientX, t[0].clientY);
            verplaatst = 99;
            return;
        }
        if (raak.soort === 1 && t.length === 1) {
            var dx = t[0].clientX - raak.x, dy = t[0].clientY - raak.y;
            verplaatst = Math.max(verplaatst, Math.abs(dx) + Math.abs(dy));
            if (verplaatst > 8) stopPakTimer();
            view.x = raak.vx + dx;
            view.y = raak.vy + dy;
            aangeraakt = true;
            pasToe();
        } else if (raak.soort === 2 && t.length >= 2) {
            var d = afstand(t);
            if (raak.d > 0) {
                var nk = klem(raak.k * (d / raak.d), MIN_K, MAX_K);
                var mx = (t[0].clientX + t[1].clientX) / 2;
                var my = (t[0].clientY + t[1].clientY) / 2;
                // Schalen om het knijppunt én meebewegen met twee vingers.
                view.x = raak.cx - (raak.cx - raak.vx) * (nk / raak.k) + (mx - raak.mx);
                view.y = raak.cy - (raak.cy - raak.vy) * (nk / raak.k) + (my - raak.my);
                view.k = nk;
                aangeraakt = true;
                pasToe();
            }
        }
        verbergHint();
    }, { passive: false });

    function raakEinde(e) {
        stopPakTimer();
        if (e.touches && e.touches.length === 0) {
            eindKnoopSleep();
            raak = null;
            setTimeout(function () { raakteBezig = false; }, 350);
        } else if (e.touches && e.touches.length === 1 && raak && raak.soort === 2) {
            raak = { soort: 1, x: e.touches[0].clientX, y: e.touches[0].clientY, vx: view.x, vy: view.y };
        }
    }
    canvas.addEventListener('touchend', raakEinde, { passive: true });
    canvas.addEventListener('touchcancel', raakEinde, { passive: true });

    // Safari's eigen knijpgebaar uitschakelen binnen het tekenvlak.
    canvas.addEventListener('gesturestart', function (e) { e.preventDefault(); });
    canvas.addEventListener('gesturechange', function (e) { e.preventDefault(); });

    function verbergHint() { if (hint) hint.classList.add('weg'); }

    // ── Klikken in de boom ────────────────────────────────────────────────

    function attribuutOmhoog(el, naam) {
        while (el && el !== canvas) {
            if (el.getAttribute) {
                var v = el.getAttribute(naam);
                if (v) return v;
            }
            el = el.parentNode;
        }
        return null;
    }

    /** Tekent opnieuw en houdt het aangeklikte punt op zijn plek in beeld. */
    function hertekenRond(sleutel) {
        var was = plaats[sleutel];
        var scherm = was ? { x: was.x * view.k + view.x, y: was.y * view.k + view.y } : null;
        teken();
        if (scherm && plaats[sleutel]) {
            view.x = scherm.x - plaats[sleutel].x * view.k;
            view.y = scherm.y - plaats[sleutel].y * view.k;
            aangeraakt = true;
            pasToe();
        }
        bewaar();
    }

    canvas.addEventListener('click', function (e) {
        if (verplaatst > 6) return;              // dit was slepen, geen tik
        var ket = attribuutOmhoog(e.target, 'data-keten');
        if (ket) {
            ketenOpen[ket] = !ketenOpen[ket];
            hertekenRond(ketenOpen[ket] ? ket : 'keten:' + ket);
            verbergHint();
            return;
        }
        var klap = attribuutOmhoog(e.target, 'data-klap');
        if (klap) {
            takOpen[klap] = !takOpen[klap];
            hertekenRond(klap);
            verbergHint();
            return;
        }
        var id = attribuutOmhoog(e.target, 'data-id');
        if (id) { toonKaart(id); verbergHint(); }
    });

    // ── Persoonskaart ─────────────────────────────────────────────────────

    function link(id) {
        var p = persoon(id);
        if (!p) return '';
        return '<button type="button" class="sb-ga" data-go="' + esc(id) + '">' + esc(p.naam) + '</button>';
    }

    function lijst(ids) {
        var uit = [];
        for (var i = 0; i < ids.length; i++) {
            var l = link(ids[i]);
            if (l) uit.push(l);
        }
        return uit.join(', ');
    }

    function toonKaart(id) {
        var p = persoon(id);
        if (!p) return;
        gekozen = id;
        var h = [];
        h.push('<button type="button" class="sb-sluit" id="sb-sluit" aria-label="Sluiten">×</button>');
        h.push('<h2>' + esc(p.naam) + '</h2>');

        var meta = [];
        if (typeof p.generatie === 'number') meta.push('generatie ' + p.generatie);
        if (p.ookGenoemd && p.ookGenoemd.length) meta.push('ook: ' + esc(p.ookGenoemd.join(', ')));
        if (p.soort === 'volk') meta.push('volk, geen persoon');
        h.push('<p class="sb-gen">' + meta.join(' · ') + '</p>');

        if (p.opmerking) h.push('<p class="sb-opm">' + esc(p.opmerking) + '</p>');

        if (p.vader) h.push('<p class="sb-rel"><b>Vader</b> ' + link(p.vader) + '</p>');
        if (p.moeder) h.push('<p class="sb-rel"><b>Moeder</b> ' + link(p.moeder) + '</p>');
        if (!p.vader && !p.moeder && p.ouder) {
            h.push('<p class="sb-rel"><b>Uit het geslacht van</b> ' + link(p.ouder) + '</p>');
        }
        if (p.partners && p.partners.length) {
            h.push('<p class="sb-rel"><b>' + (p.geslacht === 'v' ? 'Man' : 'Vrouw(en)') + '</b> ' +
                   lijst(p.partners) + '</p>');
        }
        if (p.kinderen && p.kinderen.length) {
            h.push('<p class="sb-rel"><b>Kinderen (' + p.kinderen.length + ')</b> ' +
                   lijst(p.kinderen) + '</p>');
        }

        if (p.verzen && p.verzen.length) {
            h.push('<h3>In de tekst</h3>');
            for (var i = 0; i < p.verzen.length; i++) {
                var v = p.verzen[i];
                var href = 'index.html#' + encodeURIComponent(v.boek) + '/' + v.hoofdstuk + '/' + v.vers;
                h.push('<div class="sb-vers"><a class="sb-ref" href="' + href + '">' +
                       esc(v.boekNaam) + ' ' + v.hoofdstuk + ':' + v.vers +
                       ' →</a><p>' + esc(v.tekst) + '</p></div>');
            }
        }

        kaart.innerHTML = h.join('');
        kaart.hidden = false;
        kaart.scrollTop = 0;
        teken();
        bewaar();
    }

    function sluitKaart() {
        kaart.hidden = true;
        gekozen = null;
        teken();
        bewaar();
    }

    kaart.addEventListener('click', function (e) {
        var t = e.target;
        if (t && t.id === 'sb-sluit') { sluitKaart(); return; }
        var go = t && t.getAttribute ? t.getAttribute('data-go') : null;
        if (go) gaNaar(go);
    });

    /** Vouwt precies genoeg open om deze persoon als eigen regel te tonen. */
    function maakZichtbaar(id) {
        var pad = [], p = persoon(id);
        while (p) { pad.unshift(p.id); p = p.ouder ? persoon(p.ouder) : null; }
        for (var i = 0; i < pad.length - 1; i++) {
            if (spineKind(pad[i]) !== pad[i + 1]) takOpen[pad[i]] = true;
        }
        if (isVlak(id)) ketenOpen[ketenBegin(id)] = true;
    }

    function gaNaar(id) {
        if (!persoon(id)) return;
        maakZichtbaar(id);
        toonKaart(id);
        aangeraakt = true;
        centreerOp(id, 0.8);
    }

    // ── Zoeken ────────────────────────────────────────────────────────────

    function zoek(term) {
        var t = plat(term).trim();
        if (t.length < 1) return [];
        var uit = [];
        for (var id in P) {
            var p = P[id];
            var namen = [p.naam].concat(p.ookGenoemd || []);
            var raakt = false, exact = false;
            for (var i = 0; i < namen.length; i++) {
                var n = plat(namen[i]);
                if (n.indexOf(t) === 0) { raakt = true; exact = true; break; }
                if (n.indexOf(t) > -1) raakt = true;
            }
            if (raakt) uit.push({ id: id, p: p, exact: exact });
        }
        uit.sort(function (a, b) {
            if (a.exact !== b.exact) return a.exact ? -1 : 1;
            if (a.p.naam !== b.p.naam) return a.p.naam < b.p.naam ? -1 : 1;
            return (a.p.generatie || 0) - (b.p.generatie || 0);
        });
        return uit.slice(0, 12);
    }

    function toonTreffers(lijstje) {
        if (!lijstje.length) { trefLijst.hidden = true; trefLijst.innerHTML = ''; return; }
        var h = [];
        for (var i = 0; i < lijstje.length; i++) {
            var p = lijstje[i].p;
            var bij = [];
            if (p.ouder && persoon(p.ouder)) bij.push('kind van ' + persoon(p.ouder).naam);
            else if (p.partners && p.partners.length && persoon(p.partners[0])) {
                bij.push('vrouw van ' + persoon(p.partners[0]).naam);
            }
            if (typeof p.generatie === 'number') bij.push('gen. ' + p.generatie);
            h.push('<button type="button" data-go="' + esc(p.id) + '">' + esc(p.naam) +
                   ' <span class="sb-tref-bij">' + esc(bij.join(' · ')) + '</span></button>');
        }
        trefLijst.innerHTML = h.join('');
        trefLijst.hidden = false;
    }

    zoekVeld.addEventListener('input', function () { toonTreffers(zoek(zoekVeld.value)); });
    zoekVeld.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') { trefLijst.hidden = true; zoekVeld.blur(); }
        if (e.key === 'Enter') {
            var r = zoek(zoekVeld.value);
            if (r.length) { gaNaar(r[0].id); trefLijst.hidden = true; zoekVeld.blur(); }
        }
    });
    trefLijst.addEventListener('click', function (e) {
        var el = e.target;
        while (el && el !== trefLijst && !(el.getAttribute && el.getAttribute('data-go'))) el = el.parentNode;
        var go = el && el.getAttribute ? el.getAttribute('data-go') : null;
        if (go) { gaNaar(go); trefLijst.hidden = true; zoekVeld.blur(); }
    });
    document.addEventListener('click', function (e) {
        var el = e.target;
        while (el) {
            if (el.className === 'sb-zoek') return;
            el = el.parentNode;
        }
        trefLijst.hidden = true;
    });

    // ── Toestand bewaren (URL + localStorage) ─────────────────────────────

    var stilBewaren = false;

    function sleutels(o) {
        var uit = [];
        for (var k in o) if (o[k]) uit.push(k);
        uit.sort();
        return uit;
    }

    function bewaar() {
        if (stilBewaren) return;
        var t = sleutels(takOpen), k = sleutels(ketenOpen);
        var delen = [];
        if (gekozen) delen.push('p=' + gekozen);
        if (t.length) delen.push('t=' + t.join(','));
        if (k.length) delen.push('k=' + k.join(','));
        var h = delen.length ? '#' + delen.join('&') : '';
        try {
            if (window.history && history.replaceState) {
                history.replaceState(null, '', location.pathname + location.search + h);
            }
        } catch (e) { /* file:// of oude browser — niet erg */ }
        try {
            localStorage.setItem(OPSLAG, JSON.stringify({ p: gekozen, t: t, k: k }));
        } catch (e2) { /* privémodus */ }
    }

    function leesToestand() {
        var h = (location.hash || '').replace(/^#/, '');
        if (h) {
            if (h.indexOf('=') === -1) return { p: persoon(h) ? h : null, t: [], k: [] };
            var uit = { p: null, t: [], k: [] };
            var stukken = h.split('&');
            for (var i = 0; i < stukken.length; i++) {
                var d = stukken[i].split('=');
                var v = decodeURIComponent(d[1] || '');
                if (d[0] === 'p') uit.p = v;
                else if (d[0] === 't') uit.t = v ? v.split(',') : [];
                else if (d[0] === 'k') uit.k = v ? v.split(',') : [];
            }
            return uit;
        }
        try {
            var s = localStorage.getItem(OPSLAG);
            if (s) return JSON.parse(s);
        } catch (e) { /* niets */ }
        return null;
    }

    function pasToestandToe(st) {
        takOpen = {}; ketenOpen = {};
        if (!st) return false;
        var i;
        for (i = 0; st.t && i < st.t.length; i++) if (persoon(st.t[i])) takOpen[st.t[i]] = true;
        for (i = 0; st.k && i < st.k.length; i++) if (persoon(st.k[i])) ketenOpen[st.k[i]] = true;
        return !!(st.p && persoon(st.p));
    }

    // ── Werkbalk ──────────────────────────────────────────────────────────

    function knop(id, fn) {
        var el = document.getElementById(id);
        if (el) el.addEventListener('click', fn);
    }

    function alles(aan) {
        takOpen = {}; ketenOpen = {};
        if (!aan) return;
        for (var id in P) {
            if (P[id].kinderen && P[id].kinderen.length) takOpen[id] = true;
            if (P[id].hoofdlijn) ketenOpen[id] = true;
        }
    }

    knop('sb-hoofdlijn', function () {
        alles(false);
        gekozen = null;
        kaart.hidden = true;
        teken();
        beginBeeld();
        aangeraakt = false;
        bewaar();
    });
    knop('sb-alles', function () { alles(true); teken(); beginBeeld(); aangeraakt = true; bewaar(); });
    knop('sb-passend', function () { aangeraakt = true; passend(); });
    knop('sb-in', function () { zoomKnop(1.25); });
    knop('sb-uit', function () { zoomKnop(0.8); });
    knop('sb-herschik', herschik);

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && !kaart.hidden) sluitKaart();
    });

    var wachtMaat = null;
    window.addEventListener('resize', function () {
        if (wachtMaat) clearTimeout(wachtMaat);
        wachtMaat = setTimeout(function () {
            if (aangeraakt) pasToe(); else beginBeeld();
        }, 150);
    });

    // ── Starten ───────────────────────────────────────────────────────────

    var SPRONGEN = ['noach', 'abram', 'jakob', 'juda', 'david', 'jezus'];

    function bouwSprongen() {
        var el = document.getElementById('sb-sprong');
        if (!el) return;
        var h = [];
        for (var i = 0; i < SPRONGEN.length; i++) {
            var p = persoon(SPRONGEN[i]);
            if (p) h.push('<button type="button" data-go="' + esc(p.id) + '">' + esc(p.naam) + '</button>');
        }
        el.innerHTML = h.join('');
        el.addEventListener('click', function (e) {
            var go = e.target && e.target.getAttribute ? e.target.getAttribute('data-go') : null;
            if (go) gaNaar(go);
        });
    }

    function start(json) {
        DATA = json;
        P = json.personen;
        bepaalSpineKinderen();
        bouwSprongen();
        leesVerzet();

        var st = leesToestand();
        var heeftPersoon = pasToestandToe(st);
        teken();
        beginBeeld();
        if (heeftPersoon) gaNaar(st.p);

        window.addEventListener('hashchange', function () {
            var s = leesToestand();
            if (!s) return;
            stilBewaren = true;
            var pp = pasToestandToe(s);
            teken();
            if (pp) gaNaar(s.p); else beginBeeld();
            stilBewaren = false;
        });

        // De webfont laadt later dan dit script: breedtes opnieuw meten zodra
        // hij er is, anders staan de vakjes op de maten van het reservelettertype.
        if (document.fonts && document.fonts.ready && document.fonts.ready.then) {
            document.fonts.ready.then(function () {
                meetCtx = undefined;
                var vast = aangeraakt;
                teken();
                if (!vast) beginBeeld();
            })['catch'](function () { /* niets */ });
        }
    }

    function mislukt(reden) {
        var laden = document.getElementById('sb-laden');
        if (laden) laden.textContent = 'De stamboom kon niet geladen worden (' + reden + ').';
    }

    if (window.fetch) {
        fetch('data/stamboom.json').then(function (r) {
            if (!r.ok) throw new Error(r.status);
            return r.json();
        }).then(start)['catch'](function (err) { mislukt(String((err && err.message) || err)); });
    } else {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', 'data/stamboom.json', true);
        xhr.onload = function () {
            if (xhr.status >= 200 && xhr.status < 300) start(JSON.parse(xhr.responseText));
            else mislukt('fout ' + xhr.status);
        };
        xhr.onerror = function () { mislukt('netwerkfout'); };
        xhr.send();
    }
})();
