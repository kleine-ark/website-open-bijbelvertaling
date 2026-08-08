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
            var itemIndex = -1;
            if (gekozen) {
                for (var i = 0; i < d.items.length; i++) {
                    if (d.items[i].id === gekozen) {
                        item = d.items[i];
                        itemIndex = i;
                        break;
                    }
                }
            }
            if (item) { toonItem(d, item, itemIndex); } else { toonOverzicht(d); }
        })
        .catch(function () { houder.textContent = 'De gegevens konden niet geladen worden.'; });

    function toonOverzicht(d) {
        document.title = d.titel + ' — Open Vertaling';
        var h = '<h1>' + esc(d.titel) + '</h1>';
        if (d.intro) h += '<p class="ns-lead">' + esc(d.intro) + '</p>';
        h += '<div class="ns-rooster">';
        for (var i = 0; i < d.items.length; i++) {
            var it = d.items[i];
            h += '<a class="ns-kaart" href="?item=' + encodeURIComponent(it.id) + '">' +
                 (d.nummerType ? '<span class="ns-nummer">' + esc(d.nummerType) + ' ' + (i + 1) + '</span>' : '') +
                 '<span class="ns-kaart-naam">' + esc(it.naam) + '</span>' +
                 '<span class="ns-kaart-tal">' + it.verzen.length +
                 (it.verzen.length === 1 ? ' vindplaats' : ' vindplaatsen') + '</span></a>';
        }
        h += '</div>';
        houder.innerHTML = h;
    }

    function toonItem(d, it, itemIndex) {
        document.title = it.naam + ' — ' + d.titel + ' — Open Vertaling';
        var h = '<p class="ns-terug"><a href="' + location.pathname.split('/').pop() + '">&larr; ' +
                esc(d.titel) + '</a></p>';
        if (d.nummerType) {
            h += '<span class="ns-nummer">' + esc(d.nummerType) + ' ' + (itemIndex + 1) + '</span>';
        }
        h += '<h1>' + esc(it.naam) + '</h1>';
        h += '<p class="ns-beschrijving">' + esc(it.beschrijving) + '</p>';
        if (d.nummerType && it.tekstpassages) {
            h += '<section class="ns-volledige-tekst" aria-live="polite">' +
                 '<h2 class="ns-kop">Volledige tekst</h2>' +
                 '<p class="ns-tekstladen">De volledige tekst wordt geladen…</p></section>';
        }
        h += '<h2 class="ns-kop">Vindplaatsen in ' + esc(d.bron) + '</h2>';
        h += '<p class="ns-verzen">';
        for (var i = 0; i < it.verzen.length; i++) {
            h += versLink(d.bron, it.verzen[i]) + ' ';
        }
        h += '</p>';
        houder.innerHTML = h;

        if (d.nummerType && it.tekstpassages) laadVolledigeTekst(d, it);
    }

    function bundelPad(d, it) {
        var soort = d.nummerType === 'Lied' ? 'liederen' : 'gebeden';
        return 'data/naslag-teksten/' + soort + '/' + encodeURIComponent(it.id) + '.json';
    }

    function laadVolledigeTekst(d, it) {
        var container = houder.querySelector('.ns-volledige-tekst');
        fetch(bundelPad(d, it))
            .then(function (r) {
                if (!r.ok) throw new Error('tekstbundel ontbreekt');
                return r.json();
            })
            .then(function (bundle) { toonVolledigeTekst(container, bundle); })
            .catch(function () {
                container.innerHTML = '<h2 class="ns-kop">Volledige tekst</h2>' +
                    '<p class="ns-tekstfout">De volledige tekst kon niet geladen worden.</p>';
            });
    }

    function maakElement(tag, className, text) {
        var node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    }

    function toonVolledigeTekst(container, bundle) {
        container.textContent = '';
        container.appendChild(maakElement('h2', 'ns-kop', 'Volledige tekst'));

        var isPsalmen = bundle.id === 'de-psalmen';
        if (isPsalmen) {
            var sprongen = maakElement('nav', 'ns-psalm-sprongen');
            sprongen.setAttribute('aria-label', 'Ga naar een psalm');
            for (var psalm = 1; psalm <= 150; psalm++) {
                var link = maakElement('a', '', String(psalm));
                link.href = '#psalm-' + psalm;
                sprongen.appendChild(link);
            }
            container.appendChild(sprongen);
        }

        for (var p = 0; p < bundle.passages.length; p++) {
            var passage = bundle.passages[p];
            var passageNode = maakElement('section', 'ns-passage');
            passageNode.appendChild(maakElement('h3', '', passage.label));

            for (var s = 0; s < passage.sections.length; s++) {
                var section = passage.sections[s];
                if (isPsalmen || passage.sections.length > 1) {
                    var sectionTitle = isPsalmen
                        ? 'Psalm ' + section.hoofdstuk
                        : passage.label.split(':')[0] + ', hoofdstuk ' + section.hoofdstuk;
                    var sectionHeading = maakElement('h4', 'ns-sectie-kop', sectionTitle);
                    if (isPsalmen) sectionHeading.id = 'psalm-' + section.hoofdstuk;
                    passageNode.appendChild(sectionHeading);
                }

                for (var v = 0; v < section.verzen.length; v++) {
                    var vers = section.verzen[v];
                    var verseNode = maakElement('p', 'ns-tekstvers');
                    verseNode.appendChild(maakElement('sup', '', String(vers.nummer)));
                    verseNode.appendChild(document.createTextNode(' ' + vers.tekst));
                    passageNode.appendChild(verseNode);
                }
            }
            container.appendChild(passageNode);
        }

        if (bundle.tekstmelding) {
            container.appendChild(maakElement('p', 'ns-tekstmelding', bundle.tekstmelding));
        }
    }
})();
