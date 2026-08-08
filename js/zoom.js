/* Open Vertaling — gedeelde zoomtoestand.
 * Past de opgeslagen tekstschaal toe en biedt een kleine interface aan het
 * optiespaneel. De bediening zelf staat in Leesvoorkeuren. */
(function () {
    'use strict';
    var KEY = 'ov_zoom';
    var STEPS = [0.8, 0.9, 1.0, 1.1, 1.25, 1.4, 1.6];

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
        /* Ook de perikoopkopjes: die staan búiten de verscellen (het zijn
           broertjes van de versrijen) en bleven op de iPad dus op de
           basisgrootte staan terwijl de tekst eromheen meegroeide. */
        var cellen = document.querySelectorAll('.verse-cell, .pericope-heading');
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

    var listeners = [];

    function notify() {
        var value = STEPS[idx];
        listeners.slice().forEach(function (listener) { listener(value); });
    }

    function refresh(bewaarPositie) {
        var anker = bewaarPositie ? leesAnker() : null;
        var value = STEPS[idx];
        apply(value);
        if (value === 1) localStorage.removeItem(KEY);
        else localStorage.setItem(KEY, value);
        if (anker) herstelAnker(anker);
        notify();
    }

    function nearestIndex(value) {
        var wanted = parseFloat(value);
        if (!wanted) return 2;
        var best = 2;
        var distance = Infinity;
        for (var i = 0; i < STEPS.length; i++) {
            var nextDistance = Math.abs(STEPS[i] - wanted);
            if (nextDistance < distance) { distance = nextDistance; best = i; }
        }
        return best;
    }

    window.OVZoom = {
        get: function () { return STEPS[idx]; },
        set: function (value) { idx = nearestIndex(value); refresh(true); },
        step: function (delta) { idx = clampIndex(idx + (delta < 0 ? -1 : 1)); refresh(true); },
        reset: function () { idx = 2; refresh(true); },
        subscribe: function (listener) {
            if (typeof listener !== 'function') return function () {};
            listeners.push(listener);
            listener(STEPS[idx]);
            return function () {
                listeners = listeners.filter(function (candidate) { return candidate !== listener; });
            };
        },
    };

    refresh(false);
    window.dispatchEvent(new CustomEvent('ovzoomready'));
})();
