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
        function refresh() {
            lbl.textContent = Math.round(STEPS[idx] * 100) + '%';
            apply(STEPS[idx]);
            if (STEPS[idx] === 1) localStorage.removeItem(KEY);
            else localStorage.setItem(KEY, STEPS[idx]);
        }
        wrap.querySelector('#ov-zoom-out').addEventListener('click', function () { idx = clampIndex(idx - 1); refresh(); });
        wrap.querySelector('#ov-zoom-in').addEventListener('click', function () { idx = clampIndex(idx + 1); refresh(); });
        lbl.addEventListener('click', function () { idx = 2; refresh(); });
        refresh();
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
