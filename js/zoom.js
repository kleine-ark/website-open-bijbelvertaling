/* Open Vertaling — mobiele zoomregeling.
 * Voegt een kleine zweefknop (− percentage +) toe waarmee je op mobiel/tablet
 * de hele pagina groter of kleiner maakt. De keuze wordt onthouden (localStorage).
 * Geladen via topnav.js, dus op elke pagina beschikbaar. Raakt de reader-JS niet. */
(function () {
    'use strict';
    var KEY = 'ov_zoom';
    var STEPS = [0.8, 0.9, 1.0, 1.1, 1.25, 1.4, 1.6];
    var BREAKPOINT = 900;   // alleen tonen op smallere schermen

    function clampIndex(i) { return Math.max(0, Math.min(STEPS.length - 1, i)); }

    function currentIndex() {
        var z = parseFloat(localStorage.getItem(KEY));
        if (!z) return 2; // 1.0
        var best = 2, bd = 9;
        for (var i = 0; i < STEPS.length; i++) {
            var d = Math.abs(STEPS[i] - z);
            if (d < bd) { bd = d; best = i; }
        }
        return best;
    }

    var idx = currentIndex();

    /* --- Toepassen, en nagaan of het echt gebeurd is -----------------------
       `zoom` is geen standaard-eigenschap. Chromium en Firefox schalen er alles
       mee, maar Safari past hem toe op de opmaak en laat de lettergrootte over
       aan zijn eigen automatische aanpassing. Op de iPad groeide daardoor wel de
       regelafstand maar niet de letter — een lezer die vergroot omdat hij het
       niet kan lezen, schiet daar niets mee op.

       De CSS zet die automatische aanpassing uit (text-size-adjust), wat het in
       de regel oplost. Blijkt de tekst tóch niet mee te schalen, dan meten we
       dat hier en schakelen we over op de terugval: --ov-zoom, waarmee de CSS de
       leestekst zelf vergroot. Meten in plaats van de browser herkennen: welke
       versie het wel of niet doet is niet te weten, of het gewerkt heeft wel. */

    function meetLetter() {
        var proef = document.createElement('span');
        proef.textContent = 'M';
        proef.style.cssText = 'position:absolute;left:-9999px;top:0;font-size:16px;';
        document.body.appendChild(proef);
        var h = proef.getBoundingClientRect().height;
        proef.remove();
        return h;
    }


    /* De terugval schaalt de leestekst zelf. Niet met vaste waarden in de CSS:
       de lettergrootte verschilt per schermbreedte (16 px op desktop, 19 op
       mobiel), en een vaste waarde zou op mobiel het verkeerde uitgangspunt
       nemen — dan vergroot 140% maar tot 118%. We lezen daarom per cel de
       natuurlijke grootte uit en bewaren die, zodat er niet op een al vergrote
       waarde wordt doorgerekend. */

    var huidigeSchaal = 1;

    function schaalTekst(z) {
        huidigeSchaal = z;
        var cellen = document.querySelectorAll('.verse-cell');
        var i, c;

        /* Eerst alles vrijmaken en pas daarna meten. In één doorgang meten en
           zetten gaat mis: een cel erft van zijn omgeving, en die is dan al
           vergroot door een eerdere ronde. De gemeten "natuurlijke" grootte is
           dan die van een al geschaalde cel, en 125% werd zo 116%. */
        var teMeten = [];
        for (i = 0; i < cellen.length; i++) {
            c = cellen[i];
            if (!c.dataset.ovBasis) { c.style.fontSize = ''; teMeten.push(c); }
        }
        for (i = 0; i < teMeten.length; i++) {
            teMeten[i].dataset.ovBasis = parseFloat(getComputedStyle(teMeten[i]).fontSize);
        }
        for (i = 0; i < cellen.length; i++) {
            c = cellen[i];
            var basis = parseFloat(c.dataset.ovBasis);
            c.style.fontSize = (z === 1 || !basis) ? '' : (basis * z) + 'px';
        }
    }

    /* De verzen worden opnieuw opgebouwd bij elk hoofdstuk; nieuwe cellen weten
       nog niets van de schaal. */
    function volgNieuweVerzen() {
        if (!window.MutationObserver) return;
        var houder = document.getElementById('verses-container') || document.body;
        new MutationObserver(function () {
            if (huidigeSchaal !== 1) schaalTekst(huidigeSchaal);
        }).observe(houder, { childList: true, subtree: true });
    }

    var terugvalNodig = null;   // nog niet gemeten

    function apply(z) {
        var wortel = document.documentElement;
        wortel.style.setProperty('--ov-zoom', z);

        if (terugvalNodig === true) {
            wortel.style.zoom = '';
            schaalTekst(z);
            return;
        }

        var voor = (terugvalNodig === null && z !== 1 && document.body) ? meetLetter() : null;
        wortel.style.zoom = (z === 1 ? '' : z);

        if (voor !== null) {
            var na = meetLetter();
            // schaalt de letter mee? dan is na/voor ongeveer z
            var gelukt = Math.abs((na / voor) - z) < 0.05 * z;
            terugvalNodig = !gelukt;
            if (terugvalNodig) {
                wortel.style.zoom = '';
                wortel.classList.add('ov-zoom-tekst');
                volgNieuweVerzen();
                schaalTekst(z);
            }
        }
    }

    /* --- Leespositie vasthouden bij zoomen ---------------------------------
       Schalen verandert de regelhoogte, waardoor dezelfde scrollpositie in
       pixels ineens een ander vers aanwijst. We onthouden daarom welk vers
       bovenaan staat en zetten dat na het schalen terug op dezelfde hoogte.
       Werkt op beide leesweergaven: app.js zet data-verse op .verse-row,
       lees.js op .verse-span. */

    function scrollHouder(el) {
        var p = el && el.parentElement;
        while (p && p !== document.body) {
            var s = getComputedStyle(p);
            if (/(auto|scroll)/.test(s.overflowY) && p.scrollHeight > p.clientHeight) return p;
            p = p.parentElement;
        }
        return document.scrollingElement || document.documentElement;
    }

    function leesAnker() {
        var elems = document.querySelectorAll('[data-verse]');
        for (var i = 0; i < elems.length; i++) {
            var r = elems[i].getBoundingClientRect();
            if (r.height > 0 && r.bottom > 0) return { el: elems[i], top: r.top };
        }
        return null;
    }

    function herstelAnker(anker) {
        if (!anker || !anker.el || !anker.el.isConnected) return;
        var verschil = anker.el.getBoundingClientRect().top - anker.top;
        if (Math.abs(verschil) < 1) return;
        scrollHouder(anker.el).scrollTop += verschil;
    }

    /* --- Plaatsing --------------------------------------------------------
       De vaste voetbalk op mobiel (#mobile-footer-nav) bevat de knoppen voor
       vorig/volgend hoofdstuk en de afspeelknop. De zweefknop moet daarboven
       blijven; naar opzij schuiven helpt niet, want de vrije gaten in die balk
       zijn smaller dan de zweefknop.

       Dit stond eerst in JavaScript: meet de balk, zet bottom navenant. Dat
       ging twee keer mis. De balk groeit van 56 naar 72 px zodra de
       afspeelknop verschijnt, en op een toestel met home-indicator komt daar
       de veilige zone nog bij — maar de meting draaide daarna niet opnieuw, en
       een verouderde waarde legt de knop precies op de pijl. Bovendien is
       innerHeight op iOS niet betrouwbaar terwijl de URL-balk in- en uitschuift.

       De hoogte van die balk staat gewoon in de CSS (10 px ondermarge plus de
       hoogste knop: 46 px normaal, 62 px met afspeelknop). Dan kan de afstand
       daar ook staan, en kan hij per definitie niet verouderen. */

    // Pas de opgeslagen zoom meteen toe (ook op desktop, zodat de keuze consistent is).
    apply(STEPS[idx]);

    function build() {
        if (document.getElementById('ov-zoom')) return;
        var wrap = document.createElement('div');
        wrap.id = 'ov-zoom';
        wrap.setAttribute('role', 'group');
        wrap.setAttribute('aria-label', 'Zoom');
        wrap.innerHTML =
            '<button type="button" class="ov-zoom-btn" id="ov-zoom-out" aria-label="Kleiner">−</button>' +
            '<button type="button" class="ov-zoom-lbl" id="ov-zoom-lbl" aria-label="Zoom terug naar 100%" title="Terug naar 100%">100%</button>' +
            '<button type="button" class="ov-zoom-btn" id="ov-zoom-in" aria-label="Groter">+</button>';
        document.body.appendChild(wrap);

        var lbl = wrap.querySelector('#ov-zoom-lbl');

        function refresh(bewaarPositie) {
            var anker = bewaarPositie ? leesAnker() : null;
            lbl.textContent = Math.round(STEPS[idx] * 100) + '%';
            apply(STEPS[idx]);
            if (STEPS[idx] === 1) localStorage.removeItem(KEY);
            else localStorage.setItem(KEY, STEPS[idx]);
            // herstelAnker leest getBoundingClientRect(), wat de layout meteen
            // laat herberekenen — geen requestAnimationFrame nodig. Dat is ook
            // beter: rAF vuurt niet op een achtergrondtab, waardoor de
            // leespositie daar zou blijven hangen.
            if (anker) herstelAnker(anker);
        }

        wrap.querySelector('#ov-zoom-out').addEventListener('click', function () { idx = clampIndex(idx - 1); refresh(true); });
        wrap.querySelector('#ov-zoom-in').addEventListener('click', function () { idx = clampIndex(idx + 1); refresh(true); });
        lbl.addEventListener('click', function () { idx = 2; refresh(true); });
        refresh(false);   // bij het opstarten is er nog geen leespositie om te bewaren

    }

    // Styles injecteren (self-contained, geen extra bestand)
    function styles() {
        if (document.getElementById('ov-zoom-css')) return;
        var s = document.createElement('style');
        s.id = 'ov-zoom-css';
        s.textContent =
            /* Rechtsonder, niet linksonder: links zit de knop voor het vorige
               hoofdstuk. 84px = 62px afspeelknop + 10px ondermarge van de balk
               + 12px lucht; env() vangt de home-indicator op. right:20px is
               dezelfde marge als de pijlen in de balk, zodat het één kolom is. */
            '#ov-zoom{position:fixed;right:20px;z-index:5000;display:none;' +
            'bottom:calc(84px + env(safe-area-inset-bottom, 0px));' +
            'align-items:center;gap:2px;background:rgba(20,46,66,0.92);border:1px solid rgba(203,164,73,0.5);' +
            'border-radius:22px;padding:3px;box-shadow:0 2px 10px rgba(0,0,0,0.3);backdrop-filter:blur(4px);}' +
            '#ov-zoom button{font-family:inherit;color:#fff;background:transparent;border:none;cursor:pointer;}' +
            '.ov-zoom-btn{width:34px;height:34px;border-radius:50%;font-size:20px;line-height:1;font-weight:600;}' +
            '.ov-zoom-btn:hover,.ov-zoom-btn:active{background:rgba(203,164,73,0.28);}' +
            '.ov-zoom-lbl{min-width:46px;height:34px;font-size:13px;font-weight:600;border-radius:17px;}' +
            '.ov-zoom-lbl:hover{background:rgba(203,164,73,0.2);}' +
            '@media (max-width:' + BREAKPOINT + 'px){#ov-zoom{display:flex;}}' +
            /* Zoom mag de vaste zweefknop niet zelf meeschalen tot buiten beeld:
               reset de zoom binnen de knop zelf. */
            '';
        document.head.appendChild(s);
    }

    function init() { styles(); build(); }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();
})();
