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

    function apply(z) {
        // 'zoom' schaalt de volledige pagina; ondersteund in moderne mobiele browsers
        // (iOS Safari, Chrome). Fallback via transform is onnodig voor deze doelgroep.
        document.documentElement.style.zoom = (z === 1 ? '' : z);
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
       De vaste voetbalk op mobiel (#mobile-footer-nav, 72 px hoog) bevat de
       knoppen voor vorig/volgend hoofdstuk en de afspeelknop. De zweefknop
       stond daar bovenop. Naar rechts schuiven helpt niet — de vrije gaten in
       die balk zijn smaller dan de zweefknop — dus zetten we hem erbovenop. */

    function positioneer() {
        var wrap = document.getElementById('ov-zoom');
        if (!wrap) return;
        var ruimte = 12;
        var balk = document.getElementById('mobile-footer-nav');
        if (balk) {
            var st = getComputedStyle(balk);
            if (st.display !== 'none' && st.visibility !== 'hidden' && st.position === 'fixed') {
                var r = balk.getBoundingClientRect();
                if (r.height > 0 && r.bottom >= window.innerHeight - 2) ruimte = Math.round(r.height) + 12;
            }
        }
        wrap.style.bottom = ruimte + 'px';
    }

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
            positioneer();
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

        // De voetbalk komt soms pas later in de DOM en verandert van hoogte
        // zodra de audiospeler verschijnt — dus opnieuw plaatsen bij elke wijziging.
        function koppelBalk() {
            positioneer();
            var balk = document.getElementById('mobile-footer-nav');
            if (balk && window.ResizeObserver && !balk._ovZoomWatch) {
                balk._ovZoomWatch = new ResizeObserver(positioneer);
                balk._ovZoomWatch.observe(balk);
            }
        }
        window.addEventListener('resize', positioneer);
        window.addEventListener('orientationchange', positioneer);
        window.addEventListener('load', koppelBalk);
        koppelBalk();
    }

    // Styles injecteren (self-contained, geen extra bestand)
    function styles() {
        if (document.getElementById('ov-zoom-css')) return;
        var s = document.createElement('style');
        s.id = 'ov-zoom-css';
        s.textContent =
            '#ov-zoom{position:fixed;left:10px;bottom:12px;z-index:5000;display:none;' +
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
