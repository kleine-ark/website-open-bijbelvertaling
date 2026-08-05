/* Open Vertaling — gedeelde bovenbalk (shared nav).
 * Gebruik: plaats <nav id="topnav"></nav> in de body en laad dit script er direct na.
 * Injecteert de canonieke balk (merk, links, zoekbalk, thema-knop, auth-slot, hamburger)
 * en zet de actieve link op basis van de huidige pagina. Zo blijft de nav overal gelijk. */
(function () {
    var nav = document.getElementById('topnav');
    if (!nav) return;

    /* Ingebed in de wiki? Die laadt pagina's in een iframe, en dan verschijnt
       de hele site nóg een keer binnen zichzelf: een tweede bovenbalk, en bij
       acht pagina's ook een tweede documentatie-zijbalk. Binnen een iframe
       renderen we daarom geen navigatie en laden we de zweefknoppen niet. De
       markering op <html> laat de CSS de eigen zijbalk van de pagina en de
       lege balk verbergen. */
    var ingebed;
    try { ingebed = window.self !== window.top; }
    catch (e) { ingebed = true; }   // andere herkomst: dan zitten we zeker ingebed
    if (ingebed) {
        document.documentElement.classList.add('ov-ingebed');
        return;
    }

    nav.innerHTML =
        '<div class="topnav-brand">Open Vertaling<span class="topnav-version"><a href="changelog.html" style="color:#cba449;text-decoration:none;">v0.26.0</a></span></div>' +
        '<div class="topnav-links" id="topnav-links">' +
            '<a href="over-ov.html">Over OV</a>' +
            '<a href="index.html#johannes/1">Tekst</a>' +
            '<a href="onderwerpen.html">Onderwerpen</a>' +
            '<a href="wiki.html">Wiki</a>' +
            '<a href="lexicon-viewer.html?taal=hebreeuws">Woordenboek</a>' +
        '</div>' +
        '<input type="search" id="topnav-search-input" class="topnav-search-input" placeholder="Zoek in Gods Woord… (Ctrl+K)" autocomplete="off" aria-label="Zoeken in Gods Woord" onkeydown="if(event.key===\'Enter\'){var q=this.value.trim();if(q){location.href=\'index.html?q=\'+encodeURIComponent(q);}}">' +
        '<button class="topnav-theme" id="topnav-theme-toggle" title="Thema: licht/donker" aria-label="Wissel thema"><svg class="theme-icon-sun" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg><svg class="theme-icon-moon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg></button>' +
        '<div id="auth-slot" class="topnav-auth"></div>' +
        '<button class="topnav-hamburger" id="topnav-hamburger" onclick="document.getElementById(\'topnav-links\').classList.toggle(\'open\');this.classList.toggle(\'open\')" title="Menu" aria-label="Menu" aria-expanded="false"><span></span><span></span><span></span></button>';

    var page = (location.pathname.split('/').pop() || 'index.html');
    var isLex = page.indexOf('lexicon') === 0;
    var links = nav.querySelectorAll('.topnav-links a');
    for (var i = 0; i < links.length; i++) {
        var href = links[i].getAttribute('href') || '';
        var file = href.split('#')[0].split('?')[0];
        if (file === page || (isLex && href.indexOf('lexicon') === 0)) {
            links[i].classList.add('active');
        }
    }

    // Inlog-UI (auth-slot) vullen: laad de auth-scripts indien nog niet aanwezig,
    // in volgorde (config vóór auth), zodat de login-knop overal verschijnt en de balk niet verspringt.
    ['js/firebase-config.js', 'js/auth.js'].forEach(function (src) {
        var name = src.split('/').pop();
        if (document.querySelector('script[src$="' + name + '"]')) return;
        var s = document.createElement('script'); s.src = src; s.async = false;
        if (name === 'auth.js') {
            // auth.js init't normaal op DOMContentLoaded; dat is bij dynamisch laden al voorbij → zelf init'en.
            s.onload = function () { if (window.Auth && document.readyState !== 'loading') window.Auth.init(); };
        }
        document.head.appendChild(s);
    });

    // Mobiele zoomregeling (zweefknop −/+) — self-contained, op elke pagina.
    if (!document.querySelector('script[src$="zoom.js"]')) {
        var zs = document.createElement('script'); zs.src = 'js/zoom.js'; zs.async = false;
        document.head.appendChild(zs);
    }

    // Scherm aan houden — alleen waar daadwerkelijk gelezen wordt, niet op
    // contact- of overzichtspagina's waar niemand lang blijft.
    var leespagina = (page === 'index.html' || page === 'lees.html' || page === '');
    if (leespagina && !document.querySelector('script[src$="wake-lock.js"]')) {
        var ws = document.createElement('script'); ws.src = 'js/wake-lock.js'; ws.async = false;
        document.head.appendChild(ws);
    }

    // Natuurgeluid onder de voorlezing. Doet niets zolang er geen opnames in
    // data/natuurgeluiden.json staan, dus veilig om altijd te laden.
    if (leespagina && !document.querySelector('script[src$="natuurgeluid.js"]')) {
        var ns = document.createElement('script'); ns.src = 'js/natuurgeluid.js'; ns.async = false;
        document.head.appendChild(ns);
    }
})();
