/* Open Vertaling — naslagpagina's (materialen, dieren, bomen en planten,
 * personen en muziekinstrumenten).
 *
 * Eén renderer voor alle naslagpagina's: elke pagina zet data-naslag op <body> met
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
        var m = /[?&](?:persoon|item)=([^&]+)/.exec(location.search);
        return m ? decodeURIComponent(m[1]) : null;
    }

    fetch(bron)
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (d) {
            if (!d) { houder.textContent = 'De gegevens konden niet geladen worden.'; return; }
            var gekozen = itemParam();
            var collectie = d.personen || d.items || [];
            var item = null;
            var itemIndex = -1;
            if (gekozen) {
                for (var i = 0; i < collectie.length; i++) {
                    if (collectie[i].id === gekozen) {
                        item = collectie[i];
                        itemIndex = i;
                        break;
                    }
                }
            }
            if (item) { toonItem(d, item, itemIndex); } else { toonOverzicht(d); }
        })
        .catch(function () { houder.textContent = 'De gegevens konden niet geladen worden.'; });

    function overzichtPassage(it) {
        if (it.overzichtLabel) return it.overzichtLabel;
        var labels = [];
        for (var i = 0; i < it.tekstpassages.length; i++) {
            labels.push(it.tekstpassages[i].label);
        }
        return labels.join(' · ');
    }

    function overzichtHoofdstukken(it) {
        var hoofdstukken = [];
        var gezien = {};
        for (var i = 0; i < it.tekstpassages.length; i++) {
            var passage = it.tekstpassages[i];
            var label = passage.label || ((passage.boekNaam || passage.boek) + ' ' + passage.hoofdstuk);
            var hoofdstuk = label.split(':')[0];
            if (!gezien[hoofdstuk]) {
                gezien[hoofdstuk] = true;
                hoofdstukken.push(hoofdstuk);
            }
        }
        return hoofdstukken.join(' · ');
    }

    function toonOverzicht(d) {
        document.title = d.titel + ' — Open Vertaling';
        var h = '<h1>' + esc(d.titel) + '</h1>';
        if (d.intro) h += '<p class="ns-lead">' + esc(d.intro) + '</p>';
        var items = (d.personen || d.items || []).slice();
        if (!d.nummerType) {
            items.sort(function (a, b) {
                var byName = a.naam.localeCompare(b.naam, 'nl', { sensitivity: 'base' });
                return byName || a.id.localeCompare(b.id, 'nl');
            });
            h += '<label class="ns-zoek-label" for="ns-zoeken">Zoeken in ' +
                 esc(d.titel.toLowerCase()) + '</label>' +
                 '<input id="ns-zoeken" class="ns-zoeken" type="search" ' +
                 'autocomplete="off" placeholder="Typ een naam of begrip">' +
                 '<p id="ns-zoek-status" class="ns-zoek-status" aria-live="polite"></p>';
        }
        h += '<div class="ns-rooster">';
        for (var i = 0; i < items.length; i++) {
            var it = items[i];
            var zoekTekst = d.personen
                ? [it.naam, it.onderscheiding || ''].join(' ')
                : [it.naam, it.beschrijving || '', it.gebruik || '', it.onderscheiding || ''].join(' ');
            h += '<a class="ns-kaart' + (d.titel === 'Dieren in de Bijbel' ? ' ns-kaart--dieren' : '') + '" data-zoektekst="' + esc(zoekTekst) + '" href="?' + (d.personen ? 'persoon' : 'item') + '=' + encodeURIComponent(it.id) + '">' +
                 (it.afbeelding ? '<img class="ns-kaart-beeld" src="' + esc(it.afbeelding) + '" alt="' + esc(it.naam) + '" loading="lazy" width="640" height="640">' : '') +
                 (d.nummerType ? '<span class="ns-nummer">' + esc(d.nummerType) + ' ' + (i + 1) + '</span>' : '') +
                 '<span class="ns-kaart-naam">' + esc(it.naam) + '</span>' +
                 (it.beschrijving ? '<span class="ns-kaart-beschrijving">' + esc(eersteZin(it.beschrijving)) + '</span>' : '') +
                 (it.onderscheiding ? '<span class="ns-kaart-onderscheiding">' + esc(it.onderscheiding) + '</span>' : '') +
                 (it.gebruik ? '<span class="ns-type">' + esc(it.gebruik) + '</span>' : '') +
                 (d.nummerType === 'Lied' ? '<span class="ns-kaart-passage">' + esc(overzichtPassage(it)) + '</span>' :
                 d.nummerType === 'Gebed' ? '<span class="ns-kaart-passage">' + esc(overzichtHoofdstukken(it)) + '</span>' :
                 '<span class="ns-kaart-tal">' + it.verzen.length +
                 (it.verzen.length === 1 ? ' vindplaats' : ' vindplaatsen') + '</span>') + '</a>';
        }
        h += '</div>';
        houder.innerHTML = h;

        var search = document.getElementById('ns-zoeken');
        if (search) {
            var cards = houder.querySelectorAll('.ns-kaart');
            var status = document.getElementById('ns-zoek-status');
            search.addEventListener('input', function () {
                var query = search.value.toLocaleLowerCase('nl').trim();
                var visible = 0;
                for (var c = 0; c < cards.length; c++) {
                    var match = !query || cards[c].getAttribute('data-zoektekst').toLocaleLowerCase('nl').indexOf(query) >= 0;
                    cards[c].hidden = !match;
                    if (match) visible++;
                }
                status.textContent = query ? visible + (visible === 1 ? ' resultaat' : ' resultaten') : '';
            });
        }
    }

    function toonItem(d, it, itemIndex) {
        document.title = it.naam + ' — ' + d.titel + ' — Open Vertaling';
        var h = '<p class="ns-terug"><a href="' + location.pathname.split('/').pop() + '">&larr; ' +
                esc(d.titel) + '</a></p>';
        if (d.nummerType) {
            h += '<span class="ns-nummer">' + esc(d.nummerType) + ' ' + (itemIndex + 1) + '</span>';
        }
        h += '<h1>' + esc(it.naam) + '</h1>';
        if (it.afbeelding) {
            h += '<img class="ns-detail-beeld" src="' + esc(it.afbeelding) + '" alt="' +
                 esc(it.naam) + '" width="640" height="640">';
        }
        if (it.gebruik) {
            h += '<span class="ns-type ns-type-detail">' + esc(it.gebruik) + '</span>';
        }
        if (it.onderscheiding) {
            h += '<p class="ns-onderscheiding">' + esc(it.onderscheiding) + '</p>';
        }
        h += '<p class="ns-beschrijving">' + esc(it.beschrijving) + '</p>';
        if (d.titel === 'Materialen in de Bijbel' || d.titel === 'Dieren in de Bijbel' || it.wikipedia) {
            h += '<p class="ns-externe-bron"><a href="' + esc(wikipediaUrl(it)) +
                '" target="_blank" rel="noopener noreferrer">Lees meer op Wikipedia <span aria-hidden="true">↗</span></a></p>';
        }
        if (it.naamvormen && it.naamvormen.length > 1) {
            h += '<p class="ns-naamvormen"><strong>Naamvormen:</strong> ' +
                 esc(it.naamvormen.join(' · ')) + '</p>';
        }
        if (it.stamvader) h += stamvaderHtml(it.stamvader);
        if (it.kaart) h += volkenKaartHtml(it.kaart);
        if (d.relaties) h += familieHtml(d, it);
        if (d.nummerType && it.tekstpassages) {
            h += '<section class="ns-volledige-tekst" aria-live="polite">' +
                 '<h2 class="ns-kop">Volledige tekst</h2>' +
                 '<p class="ns-tekstladen">De volledige tekst wordt geladen…</p></section>';
        }
        if (d.nummerType === 'Gebed') {
            h += '<h2 class="ns-kop">Vindplaatsen in ' + esc(d.bron) + '</h2>';
            h += '<p class="ns-verzen">';
            for (var i = 0; i < it.verzen.length; i++) {
                h += versLink(d.bron, it.verzen[i]) + ' ';
            }
            h += '</p>';
        } else if (!d.nummerType) {
            h += '<h2 class="ns-kop">Teksten in ' + esc(d.bron) + '</h2>';
            h += '<ol id="naslag-gekoppelde-teksten" class="gt-lijst"></ol>';
        }
        houder.innerHTML = h;

        if (d.nummerType && it.tekstpassages) laadVolledigeTekst(d, it);
        if (!d.nummerType && globalThis.GekoppeldeTeksten) {
            var refs = [];
            for (var r = 0; r < it.verzen.length; r++) {
                refs.push(it.verzen[r].indexOf(' ') > 0
                    ? it.verzen[r]
                    : (d.bronId || d.bron.toLowerCase()) + ' ' + it.verzen[r]);
            }
            globalThis.GekoppeldeTeksten.render(
                document.getElementById('naslag-gekoppelde-teksten'),
                refs,
                { compact: true, initialLimit: 8, boeknamen: d.boeknamen || (function () {
                    var namen = {};
                    namen[d.bronId || d.bron.toLowerCase()] = d.bron;
                    return namen;
                })() }
            );
        }
    }

    function stamvaderHtml(stamvader) {
        var ref = String(stamvader.ref || '');
        var parts = ref.split(' ');
        var boek = parts[0] || '';
        var cv = (parts[1] || '').split(':');
        var refLink = 'index.html#' + boek + '/' + (cv[0] || '') + '/' + (cv[1] || '');
        return '<section class="vn-stamvader" aria-labelledby="vn-stamvader-kop">' +
            '<div class="vn-stamvader-tak" aria-hidden="true"><span></span></div>' +
            '<div><span class="vn-label">Stamvader</span>' +
            '<h2 id="vn-stamvader-kop">' + esc(stamvader.naam) + '</h2>' +
            '<p>' + esc(stamvader.relatie) +
            (stamvader.betekenis ? '; de naam betekent ‘' + esc(stamvader.betekenis) + '’' : '') + '.</p>' +
            '<div class="vn-stamvader-links">' +
            '<a target="_top" href="' + refLink + '">' + esc(ref) + '</a>' +
            (stamvader.persoonLink ? '<a target="_top" href="' + esc(stamvader.persoonLink) + '">Persoonspagina</a>' : '') +
            '</div></div></section>';
    }

    function volkenKaartHtml(kaart) {
        return '<a class="vn-kaart" target="_top" href="' + esc(kaart.link) + '" aria-label="Bekijk ' +
            esc(kaart.plaats) + ' op de interactieve kaart">' +
            '<span class="vn-kaart-beeld" aria-hidden="true">' +
            '<svg viewBox="0 0 420 190" role="img">' +
            '<path class="vn-water" d="M151 0 C144 42 161 64 153 100 C148 126 157 145 150 190" />' +
            '<ellipse class="vn-zee" cx="150" cy="151" rx="14" ry="27" />' +
            '<path class="vn-gebied" d="M177 37 C224 20 298 38 328 76 C310 122 269 153 199 149 C173 116 168 76 177 37 Z" />' +
            '<circle class="vn-marker-ring" cx="254" cy="83" r="11" />' +
            '<circle class="vn-marker" cx="254" cy="83" r="5" />' +
            '<text class="vn-rabba" x="272" y="88">Rabba</text>' +
            '<text class="vn-jordaan" x="126" y="83" transform="rotate(-83 126 83)">Jordaan</text>' +
            '<text class="vn-ammon" x="230" y="126">AMMON</text>' +
            '</svg></span>' +
            '<span class="vn-kaart-info"><span class="vn-label">Woongebied</span>' +
            '<strong>' + esc(kaart.gebied) + '</strong>' +
            '<span>' + esc(kaart.plaats) + ' — ' + esc(kaart.moderneNaam) + '</span>' +
            '<small>' + esc(kaart.toelichting) + '</small>' +
            '<span class="vn-kaart-cta">Bekijk op de kaart →</span></span></a>';
    }

    function familieHtml(d, it) {
        var people = d.personen || [];
        var byId = {};
        for (var p = 0; p < people.length; p++) byId[people[p].id] = people[p];
        var rows = [];
        for (var r = 0; r < d.relaties.length; r++) {
            var rel = d.relaties[r];
            if (rel.van !== it.id && rel.naar !== it.id) continue;
            var otherId = rel.van === it.id ? rel.naar : rel.van;
            if (!byId[otherId]) continue;
            var label = rel.type;
            if (rel.type === 'vader' || rel.type === 'moeder') {
                label = rel.naar === it.id ? rel.type : 'kind';
            }
            rows.push('<li><span class="ps-relatie-type">' + esc(label) + '</span> ' +
                '<a href="?persoon=' + encodeURIComponent(otherId) + '">' +
                esc(byId[otherId].naam) + '</a>' +
                (rel.refs && rel.refs.length ? ' <span class="ps-relatie-ref">' + esc(rel.refs.join(' · ')) + '</span>' : '') +
                '</li>');
        }
        if (!rows.length) return '';
        return '<section class="ps-familie"><h2 class="ns-kop">Familie en stamboom</h2><ul>' +
               rows.join('') + '</ul><p><a href="stamboom.html">Bekijk de stambomen</a></p></section>';
    }

    function bundelPad(d, it) {
        var soort = d.nummerType === 'Lied' ? 'liederen' : 'gebeden';
        return 'data/naslag-teksten/' + soort + '/' + encodeURIComponent(it.id) + '.json';
    }

    function laadVolledigeTekst(d, it) {
        var container = houder.querySelector('.ns-volledige-tekst');
        if ((d.nummerType === 'Lied' || d.nummerType === 'Gebed') &&
            globalThis.OVTekstweergave &&
            typeof globalThis.OVTekstweergave.renderNaslagtekst === 'function') {
            if (d.nummerType === 'Gebed') {
                laadGebedtekstUitCitaten(container, it);
            } else if (globalThis.GekoppeldeTeksten &&
                       typeof globalThis.GekoppeldeTeksten.render === 'function') {
                laadLiedtekstMetBediening(container, it);
            } else {
                laadLiedtekstUitCitaten(container, it);
            }
            return;
        }
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

    function eersteZin(tekst) {
        var match = String(tekst || '').match(/^.*?[.!?](?:\s|$)/);
        return match ? match[0].trim() : String(tekst || '').trim();
    }

    function wikipediaUrl(item) {
        if (item.wikipedia) return item.wikipedia;
        return 'https://nl.wikipedia.org/w/index.php?search=' + encodeURIComponent(item.naam);
    }

    /* Liederen gebruiken dezelfde gekoppelde-tekstencomponent als de overige
       wiki-pagina's. Daardoor krijgt een volledig lied ook de vertrouwde
       tekstlink en +/−-bediening voor context buiten het lied. */
    function laadLiedtekstMetBediening(container, it) {
        container.textContent = '';
        container.appendChild(maakElement('h2', 'ns-kop', 'Volledige tekst'));
        var passages = it.tekstpassages || [];
        for (var i = 0; i < passages.length; i++) {
            var passage = passages[i];
            var passageNode = maakElement('section', 'ns-passage ns-liedcitaat');
            passageNode.appendChild(maakElement('h3', '', passage.label));
            var lijst = maakElement('ol', 'gt-lijst ns-liedtekst');
            passageNode.appendChild(lijst);
            container.appendChild(passageNode);

            var ref = passage.boek + ' ' + passage.hoofdstuk + ':' + passage.van +
                (passage.tot !== passage.van ? '-' + passage.tot : '');
            globalThis.GekoppeldeTeksten.render(lijst, [ref], { compact: false });

            /* De centrale component maakt de link direct; het lied levert de
               redactionele boeknaam en bereik als leesbaar opschrift. */
            var link = lijst.querySelector('.gt-vers-kop > a');
            if (link) link.textContent = passage.label;
        }
    }

    function laadLiedtekstUitCitaten(container, it) {
        container.textContent = '';
        container.appendChild(maakElement('h2', 'ns-kop', 'Volledige tekst'));
        var passages = it.tekstpassages || [];
        var taken = passages.map(function (passage) {
            var passageNode = maakElement('section', 'ns-passage ns-liedcitaat');
            passageNode.appendChild(maakElement('h3', '', passage.label));
            var citaat = maakElement('div', 'ns-liedtekst');
            citaat.innerHTML = '<span class="osv-laden">…</span>';
            passageNode.appendChild(citaat);
            container.appendChild(passageNode);

            var ref = passage.boek + ' ' + passage.hoofdstuk + ':' + passage.van +
                (passage.tot !== passage.van ? '-' + passage.tot : '');
            return globalThis.OVTekstweergave.renderNaslagtekst(citaat, ref, {
                linkLabel: passage.label,
                target: '_top'
            });
        });
        Promise.all(taken).catch(function () {
            container.innerHTML = '<h2 class="ns-kop">Volledige tekst</h2>' +
                '<p class="ns-tekstfout">De volledige tekst kon niet geladen worden.</p>';
        });
    }

    function laadGebedtekstUitCitaten(container, it) {
        container.textContent = '';
        container.appendChild(maakElement('h2', 'ns-kop', 'Volledige tekst'));
        var passages = it.tekstpassages || [];
        var taken = [];
        passages.forEach(function (passage) {
            var passageNode = maakElement('section', 'ns-passage ns-gebedcitaat');
            passageNode.appendChild(maakElement('h3', '', passage.label));
            container.appendChild(passageNode);
            for (var nummer = passage.van; nummer <= passage.tot; nummer++) {
                (function (versnummer) {
                    var verseNode = maakElement('p', 'ns-tekstvers');
                    passageNode.appendChild(verseNode);
                    var ref = passage.boek + ' ' + passage.hoofdstuk + ':' + versnummer;
                    taken.push(globalThis.OVTekstweergave.renderNaslagtekst(verseNode, ref, {
                        linkClass: 'ns-tekstvers-link',
                        target: '_top'
                    }));
                })(nummer);
            }
        });
        Promise.all(taken).catch(function () {
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

        for (var p = 0; p < bundle.passages.length; p++) {
            var passage = bundle.passages[p];
            var passageNode = maakElement('section', 'ns-passage');
            passageNode.appendChild(maakElement('h3', '', passage.label));

            for (var s = 0; s < passage.sections.length; s++) {
                var section = passage.sections[s];
                if (passage.sections.length > 1) {
                    var sectionTitle = passage.label.split(':')[0] + ', hoofdstuk ' + section.hoofdstuk;
                    var sectionHeading = maakElement('h4', 'ns-sectie-kop', sectionTitle);
                    passageNode.appendChild(sectionHeading);
                }

                for (var v = 0; v < section.verzen.length; v++) {
                    var vers = section.verzen[v];
                    var verseNode = maakElement('p', 'ns-tekstvers');
                    var textNode = verseNode;
                    if (bundle.nummerType === 'Gebed' && section.boek) {
                        textNode = maakElement('a', 'ns-tekstvers-link');
                        textNode.href = 'index.html#' + section.boek + '/' +
                            section.hoofdstuk + '/' + vers.nummer;
                        textNode.target = '_top';
                        verseNode.appendChild(textNode);
                    }
                    textNode.appendChild(maakElement('sup', '', String(vers.nummer)));
                    textNode.appendChild(document.createTextNode(' ' + vers.tekst));
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
