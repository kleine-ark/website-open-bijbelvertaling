/* Open Vertaling — gedeelde bovenbalk (shared nav).
 * Gebruik: plaats <nav id="topnav"></nav> in de body en laad dit script er direct na.
 * Injecteert de canonieke balk (merk, links, zoekbalk, thema-knop, auth-slot, hamburger)
 * en zet de actieve link op basis van de huidige pagina. Zo blijft de nav overal gelijk. */
(function () {
    var nav = document.getElementById('topnav');
    if (!nav) return;

    nav.innerHTML =
        '<div class="topnav-brand">Open Vertaling<span class="topnav-version"><a href="changelog.html" style="color:#cba449;text-decoration:none;">v0.21.6</a></span></div>' +
        '<div class="topnav-links" id="topnav-links">' +
            '<a href="over-ov.html">Over OV</a>' +
            '<a href="index.html#johannes/1">Tekst</a>' +
            '<a href="onderwerpen.html">Onderwerpen</a>' +
            '<a href="wiki.html">Wiki</a>' +
            '<a href="lexicon-viewer.html?taal=hebreeuws">Lexicon</a>' +
            '<a href="kaart.html">Kaart</a>' +
            '<a href="contact.html">Over ons</a>' +
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
})();
