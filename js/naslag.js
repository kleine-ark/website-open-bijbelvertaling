/* Open Vertaling — naslagpagina's (materialen, dieren, bomen en planten).
 *
 * Eén renderer voor drie pagina's: elke pagina zet data-naslag op <body> met
 * het pad naar zijn databestand. Zonder ?item= toont hij de hoofdpagina (alle
 * onderwerpen als kaarten); met ?item=goud de subpagina van dat onderwerp.
 * Zo bestaat er per onderwerp een eigen adres zonder tientallen losse
 * HTML-bestanden, en kan de inhoud per boek groeien door alleen het
 * databestand aan te vullen.
 *
 * Geen lookbehind of andere nieuwigheden: de ondergrens is iPadOS 15.4. */
(function () {
    'use strict';

    var houder = document.getElementById('naslag');
    if (!houder) return;
    var bron = document.body.getAttribute('data-naslag');
    if (!bron) return;

    function esc(s) {
        return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    /* Vindplaats -> koppeling naar de leestekst. Twee vormen:
       "12:6"           — boek-brede pagina; het boek komt uit d.bron
       "exodus 15:1"    — Bijbelbrede pagina (liederen, gebeden); het boek-id
                          staat vóór de spatie, zoals de mapnamen in data/
       target=_top zodat de lezer uit de wiki-iframe stapt in plaats van de
       Bijbel ín het kader te openen (site-in-site). */
    function versLink(boek, ref) {
        var doelBoek = boek.toLowerCase();
        var rest = ref;
        var i = ref.indexOf(' ');
        if (i > 0) {
            doelBoek = ref.slice(0, i).toLowerCase();
            rest = ref.slice(i + 1);
        }
        var toon = (i > 0)
            ? ref.charAt(0).toUpperCase() + ref.slice(1)   // "Exodus 15:1"
            : ref;
        return '<a class="ns-vers" target="_top" href="index.html#' + doelBoek +
               '/' + rest.split(':')[0] + '">' + esc(toon) + '</a>';
    }

    function itemParam() {
        var m = /[?&]item=([^&]+)/.exec(location.search);
        return m ? decodeURIComponent(m[1]) : null;
    }

    fetch(bron)
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (d) {
            if (!d) { houder.textContent = 'De gegevens konden niet geladen worden.'; return; }
            var gekozen = itemParam();
            var item = null;
            if (gekozen) {
                for (var i = 0; i < d.items.length; i++) {
                    if (d.items[i].id === gekozen) { item = d.items[i]; break; }
                }
            }
            if (item) { toonItem(d, item); } else { toonOverzicht(d); }
        })
        .catch(function () { houder.textContent = 'De gegevens konden niet geladen worden.'; });

    function toonOverzicht(d) {
        document.title = d.titel + ' — Open Vertaling';
        var h = '<h1>' + esc(d.titel) + '</h1>';
        h += '<p class="ns-lead">' + esc(d.intro) + '</p>';
        h += '<div class="ns-rooster">';
        for (var i = 0; i < d.items.length; i++) {
            var it = d.items[i];
            h += '<a class="ns-kaart" href="?item=' + encodeURIComponent(it.id) + '">' +
                 '<span class="ns-kaart-naam">' + esc(it.naam) + '</span>' +
                 '<span class="ns-kaart-tal">' + it.verzen.length +
                 (it.verzen.length === 1 ? ' vindplaats' : ' vindplaatsen') + '</span></a>';
        }
        h += '</div>';
        houder.innerHTML = h;
    }

    function toonItem(d, it) {
        document.title = it.naam + ' — ' + d.titel + ' — Open Vertaling';
        var h = '<p class="ns-terug"><a href="' + location.pathname.split('/').pop() + '">&larr; ' +
                esc(d.titel) + '</a></p>';
        h += '<h1>' + esc(it.naam) + '</h1>';
        h += '<p class="ns-beschrijving">' + esc(it.beschrijving) + '</p>';
        h += '<h2 class="ns-kop">Vindplaatsen in ' + esc(d.bron) + '</h2>';
        h += '<p class="ns-verzen">';
        for (var i = 0; i < it.verzen.length; i++) {
            h += versLink(d.bron, it.verzen[i]) + ' ';
        }
        h += '</p>';
        houder.innerHTML = h;
    }
})();
