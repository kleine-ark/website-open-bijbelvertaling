/* Open Vertaling — interactieve stamboom (stamboom.html).
 *
 * Leest data/stamboom.json (gemaakt door scripts/build_stamboom.py) en tekent
 * daar een VERTICALE, uitklapbare boom van: Adam bovenaan, de generaties naar
 * beneden, broers en zussen naast elkaar. Slepen en zoomen met muis én
 * aanraking.
 *
 * Waarom hij zo compact begint
 * ----------------------------
 * Van Adam tot Jezus liggen 64 generaties. Ze alle 64 als losse rij tekenen
 * levert een tekening van ruim tweeduizend pixels hoog op waarin niemand meer
 * iets terugvindt. Daarom twee ingrepen:
 *
 *   1. RECHTE STUKKEN WORDEN SAMENGEVOUWEN. Grote delen van de boom vertakken
 *      niet: Genesis 5 en 11 en de koningen van Juda zijn lange kettingen van
 *      vader op zoon. Zo'n keten wordt één schakel-vakje
 *      ("Seth › … › Lamech · 8 gen.") dat opengaat bij aantikken. Onderbroken
 *      wordt hij alleen bij een ANKER (Adam, Noach, Sem, Abraham, Izak, Jakob,
 *      Juda, David, Jechonia, Zerubbabel, Jozef, Jezus — zie
 *      scripts/build_stamboom.py) of bij iemand van wie de zijtak openstaat.
 *   2. ZIJTAKKEN STAAN DICHT. Van iemand op de hoofdlijn is standaard alleen de
 *      zoon zichtbaar die de lijn voortzet; de rest zit achter een telbadge
 *      ("+12"). Wat openstaat wordt onthouden in de URL en in localStorage,
 *      zodat een gedeelde link hetzelfde toont.
 *
 * Zo begint de boom op 18 rijen die in hun geheel op een telefoonscherm passen.
 *
 * Bewust zonder externe bibliotheken en zonder taalfeatures van na Safari 15.4
 * (dus geen lookbehind, geen Object.groupBy, geen container queries): de site
 * moet het op een iPad met iPadOS 15.4 blijven doen.
 */
(function () {
    'use strict';

    // ── Maatvoering ───────────────────────────────────────────────────────
    var DOOS_H = 22;           // hoogte van elk vakje (alle rijen even hoog)
    var V_GAP = 8;             // ruimte tussen twee generatierijen
    var RIJ = DOOS_H + V_GAP;  // verticale stap per rij
    var H_GAP = 14;            // ruimte tussen twee vakjes naast elkaar
    var PAD = 9;               // binnenmarge links/rechts in een vakje
    var MAX_B = 250, MIN_B = 62;
    var MIN_K = 0.06, MAX_K = 3;

    var FONT_NAAM = '11.5px "Fira Sans", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';
    var FONT_BIJ = '10px "Fira Sans", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';
    var FONT_BADGE = '600 9px "Fira Sans", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';

    var OPSLAG = 'sv2026_stamboom';

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
    var spineKindVan = {};      // id -> kind dat de hoofdlijn voortzet
    var gekozen = null;         // id van de geopende persoonskaart
    var view = { x: 0, y: 0, k: 1 };
    var gEl = null;             // <g> waarop de transform staat
    var plaats = {};            // id (of 'keten:'+id) -> {x, y}
    var laatsteBox = null;      // omhullende rechthoek van de tekening
    var aangeraakt = false;     // heeft de gebruiker zelf al verschoven/gezoomd?

    // ── Hulp ──────────────────────────────────────────────────────────────

    function esc(s) {
        return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

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
        if (!meetCtx) return String(tekst).length * (parseFloat(font) * 0.55);
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
                inKeten = true;      // uitgevouwen: elke schakel een eigen rij
            }
        } else if (!isVlak(id)) {
            inKeten = false;         // einde van de uitgevouwen keten
        }
        var kids = zichtbareKinderen(id), uit = [];
        for (var i = 0; i < kids.length; i++) uit.push(maakKnoop(kids[i], inKeten));
        return { soort: 'persoon', id: id, kinderen: uit };
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
        var o = { badge: '', badgeB: 0 };
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
            var n = verborgen(dn.id);
            if (n > 0) o.badge = '+' + n;
            o.titel = p.naam + (o.bij ? ' ' + o.bij : '');
        }
        o.naamB = breed(o.naam, FONT_NAAM);
        o.bijB = o.bij ? breed(o.bij, FONT_BIJ) : 0;
        o.badgeB = o.badge ? breed(o.badge, FONT_BADGE) + 10 : 0;
        var w = PAD + o.naamB + (o.bij ? 5 + o.bijB : 0) + (o.badge ? 6 + o.badgeB : 0) + PAD;
        if (w > MAX_B) {
            var ruimte = MAX_B - 2 * PAD - (o.badge ? 6 + o.badgeB : 0);
            if (o.bij) {
                o.bij = inkorten(o.bij, Math.max(24, ruimte - o.naamB - 5), FONT_BIJ);
                o.bijB = breed(o.bij, FONT_BIJ);
                ruimte -= o.bijB + 5;
            }
            o.naam = inkorten(o.naam, Math.max(30, ruimte), FONT_NAAM);
            o.naamB = breed(o.naam, FONT_NAAM);
            w = PAD + o.naamB + (o.bij ? 5 + o.bijB : 0) + (o.badge ? 6 + o.badgeB : 0) + PAD;
        }
        o.w = Math.max(MIN_B, Math.min(MAX_B, Math.ceil(w)));
        dn.opmaak = o;
        return o;
    }

    // ── Ordening ──────────────────────────────────────────────────────────

    function meetBlok(dn) {
        dn.w = opmaak(dn).w;
        var n = dn.kinderen.length;
        if (!n) { dn.blok = dn.w; return dn.blok; }
        var som = 0;
        for (var i = 0; i < n; i++) som += meetBlok(dn.kinderen[i]);
        som += H_GAP * (n - 1);
        dn.blok = Math.max(dn.w, som);
        return dn.blok;
    }

    function plaatsBlok(dn, links, rij) {
        dn.y = rij * RIJ;
        var n = dn.kinderen.length, i;
        if (!n) { dn.cx = links + dn.blok / 2; return; }
        var totaal = 0;
        for (i = 0; i < n; i++) totaal += dn.kinderen[i].blok;
        totaal += H_GAP * (n - 1);
        var x = links + (dn.blok - totaal) / 2;
        for (i = 0; i < n; i++) {
            plaatsBlok(dn.kinderen[i], x, rij + 1);
            x += dn.kinderen[i].blok + H_GAP;
        }
        dn.cx = (dn.kinderen[0].cx + dn.kinderen[n - 1].cx) / 2;
    }

    function alleKnopen(wortel) {
        var uit = [], stapel = [wortel];
        while (stapel.length) {
            var dn = stapel.pop();
            uit.push(dn);
            for (var i = 0; i < dn.kinderen.length; i++) stapel.push(dn.kinderen[i]);
        }
        return uit;
    }

    // ── Tekenen ───────────────────────────────────────────────────────────

    function opHoofdlijn(dn) {
        if (dn.soort === 'keten') return true;
        var p = persoon(dn.id);
        return !!(p && p.hoofdlijn);
    }

    function tekenKnoop(dn) {
        var o = opmaak(dn);
        var bx = dn.cx - dn.w / 2, by = dn.y;
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
        s.push('<g class="' + kl + '"' + sleutel + '><title>' + esc(o.titel) + '</title>');
        s.push('<rect class="sb-doos" x="' + bx.toFixed(1) + '" y="' + by + '" width="' + dn.w +
               '" height="' + DOOS_H + '" rx="4"/>');
        var tx = bx + PAD, ty = by + 15;
        s.push('<text class="sb-naam" x="' + tx.toFixed(1) + '" y="' + ty + '">' + esc(o.naam) + '</text>');
        if (o.bij) {
            s.push('<text class="sb-bij" x="' + (tx + o.naamB + 5).toFixed(1) + '" y="' + ty + '">' +
                   esc(o.bij) + '</text>');
        }
        s.push('</g>');
        if (o.badge) {
            var kx = bx + dn.w - PAD - o.badgeB;
            var attr = dn.soort === 'keten'
                ? ' data-keten="' + esc(dn.id) + '"'
                : ' data-klap="' + esc(dn.id) + '"';
            s.push('<g class="sb-badge' + (dn.soort === 'keten' ? ' is-keten' : '') + '"' + attr + '>' +
                   '<rect x="' + kx.toFixed(1) + '" y="' + (by + 5) + '" width="' + o.badgeB.toFixed(1) +
                   '" height="12" rx="6"/>' +
                   '<text x="' + (kx + o.badgeB / 2).toFixed(1) + '" y="' + (by + 14) +
                   '" text-anchor="middle">' + esc(o.badge) + '</text></g>');
        }
        return s.join('');
    }

    function teken() {
        var wortel = maakKnoop(DATA.wortel, false);
        meetBlok(wortel);
        plaatsBlok(wortel, 0, 0);
        var knopen = alleKnopen(wortel);

        var s = [], i, j;
        var minX = 1e9, maxX = -1e9, maxY = -1e9;
        plaats = {};

        // Verbindingslijnen eerst, zodat de vakjes erbovenop komen te liggen.
        for (i = 0; i < knopen.length; i++) {
            var dn = knopen[i];
            for (j = 0; j < dn.kinderen.length; j++) {
                var kd = dn.kinderen[j];
                var y1 = dn.y + DOOS_H, my = y1 + V_GAP / 2;
                var kl = 'sb-lijn';
                if (opHoofdlijn(dn) && opHoofdlijn(kd)) kl += ' is-lijn';
                if (kd.soort === 'persoon' && persoon(kd.id).viaMoeder) kl += ' is-via';
                s.push('<path class="' + kl + '" d="M' + dn.cx.toFixed(1) + ' ' + y1 +
                       'V' + my + 'H' + kd.cx.toFixed(1) + 'V' + kd.y + '"/>');
            }
        }

        for (i = 0; i < knopen.length; i++) {
            var n = knopen[i];
            s.push(tekenKnoop(n));
            var bx = n.cx - n.w / 2;
            if (bx < minX) minX = bx;
            if (bx + n.w > maxX) maxX = bx + n.w;
            if (n.y + DOOS_H > maxY) maxY = n.y + DOOS_H;
            var mid = { x: n.cx, y: n.y + DOOS_H / 2 };
            if (n.soort === 'keten') {
                plaats['keten:' + n.id] = mid;
                for (j = 0; j < n.ids.length; j++) plaats[n.ids[j]] = mid;
            } else {
                plaats[n.id] = mid;
            }
        }

        laatsteBox = { x: minX - 10, y: -10, w: (maxX - minX) + 20, h: maxY + 20 };

        var laden = document.getElementById('sb-laden');
        if (laden && laden.parentNode) laden.parentNode.removeChild(laden);
        var oud = canvas.querySelector('svg');
        if (oud) canvas.removeChild(oud);
        var houder = document.createElement('div');
        houder.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" aria-label="Stamboom van Adam tot Jezus">' +
                           '<g id="sb-g">' + s.join('') + '</g></svg>';
        canvas.insertBefore(houder.firstChild, canvas.firstChild);
        gEl = document.getElementById('sb-g');
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

    function zoomKnop(f) {
        var m = maat();
        aangeraakt = true;
        zoomNaar(view.k * f, m.b / 2, m.h / 2);
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

    function passend(maxSchaal) {
        if (!laatsteBox) return;
        var m = maat();
        var k = Math.min(m.b / laatsteBox.w, m.h / laatsteBox.h);
        view.k = klem(k, MIN_K, maxSchaal || MAX_K);
        view.x = (m.b - laatsteBox.w * view.k) / 2 - laatsteBox.x * view.k;
        view.y = (m.h - laatsteBox.h * view.k) / 2 - laatsteBox.y * view.k;
        pasToe();
    }

    function beginBeeld() {
        // De ingeklapte boom hoort in zijn geheel in beeld te staan. Past hij
        // ruim, dan mag hij tot 1,4× opgeschaald worden zodat hij op een groot
        // scherm niet als postzegel middenin blijft staan.
        passend(1.4);
    }

    // ── Muis ──────────────────────────────────────────────────────────────

    var sleep = null, raakteBezig = false, verplaatst = 0;

    canvas.addEventListener('mousedown', function (e) {
        if (raakteBezig || e.button !== 0) return;
        sleep = { x: e.clientX, y: e.clientY, vx: view.x, vy: view.y };
        verplaatst = 0;
        canvas.classList.add('sb-sleept');
    });
    window.addEventListener('mousemove', function (e) {
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
        sleep = null;
        canvas.classList.remove('sb-sleept');
    });

    canvas.addEventListener('wheel', function (e) {
        e.preventDefault();
        var m = maat();
        // Eén sprong per gebeurtenis begrenzen: sommige trackpads sturen enorme
        // deltaY-waarden en de boom zou dan wegschieten.
        var f = klem(Math.pow(0.9982, e.deltaY * (e.deltaMode === 1 ? 16 : 1)), 0.6, 1.6);
        aangeraakt = true;
        zoomNaar(view.k * f, e.clientX - m.l, e.clientY - m.t);
        verbergHint();
    }, { passive: false });

    // ── Aanraking ─────────────────────────────────────────────────────────

    var raak = null;

    function afstand(t) {
        var dx = t[0].clientX - t[1].clientX, dy = t[0].clientY - t[1].clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }

    canvas.addEventListener('touchstart', function (e) {
        raakteBezig = true;
        var t = e.touches;
        if (t.length === 1) {
            raak = { soort: 1, x: t[0].clientX, y: t[0].clientY, vx: view.x, vy: view.y };
            verplaatst = 0;
        } else if (t.length >= 2) {
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
        if (raak.soort === 1 && t.length === 1) {
            var dx = t[0].clientX - raak.x, dy = t[0].clientY - raak.y;
            verplaatst = Math.max(verplaatst, Math.abs(dx) + Math.abs(dy));
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
        if (e.touches && e.touches.length === 0) {
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

    /** Vouwt precies genoeg open om deze persoon als eigen rij te tonen. */
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
    knop('sb-alles', function () { alles(true); teken(); passend(); aangeraakt = true; bewaar(); });
    knop('sb-passend', function () { aangeraakt = true; passend(); });
    knop('sb-in', function () { zoomKnop(1.25); });
    knop('sb-uit', function () { zoomKnop(0.8); });

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
