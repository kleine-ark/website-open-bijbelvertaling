/* Verbind de gegenereerde tijdsvindplaatsen met de tabellen op de wiki. */
(function () {
    'use strict';

    var rijen = document.querySelectorAll('[data-tijdgroep]');
    if (!rijen.length || !window.GekoppeldeTeksten) return;

    Promise.all([
        fetch('data/naslag-tijdsaanduidingen.json').then(function (r) {
            if (!r.ok) throw new Error('tijdsvindplaatsen ontbreken');
            return r.json();
        }),
        fetch('data/books.json').then(function (r) {
            if (!r.ok) throw new Error('boeknamen ontbreken');
            return r.json();
        })
    ]).then(function (resultaten) {
        var index = resultaten[0];
        var boeken = resultaten[1].books || [];
        var boeknamen = {};
        for (var b = 0; b < boeken.length; b++) {
            boeknamen[boeken[b].id] = boeken[b].nameDutch;
        }

        for (var i = 0; i < rijen.length; i++) {
            verbindRij(rijen[i], index.groepen || {}, boeknamen);
        }
    }).catch(function () {
        /* De tabellen en hun handmatig leesbare samenvattingen blijven staan. */
    });

    function verbindRij(rij, groepen, boeknamen) {
        var hoofdgroep = rij.getAttribute('data-tijdgroep');
        var groepsnamen = (rij.getAttribute('data-tijdgroepen') || hoofdgroep).split(/\s+/);
        var refs = [];
        for (var g = 0; g < groepsnamen.length; g++) {
            var groepRefs = groepen[groepsnamen[g]] || [];
            for (var r = 0; r < groepRefs.length; r++) {
                if (refs.indexOf(groepRefs[r]) === -1) refs.push(groepRefs[r]);
            }
        }

        werkAantalBij(rij, refs.length);
        if (!refs.length) return;

        var detail = document.createElement('tr');
        detail.className = 'gt-detail-rij';
        detail.setAttribute('data-voor', hoofdgroep);
        var cel = document.createElement('td');
        cel.className = 'gt-detail-cel';
        cel.colSpan = Math.max(1, rij.cells.length);
        var lijst = document.createElement('ol');
        lijst.className = 'gt-lijst';
        cel.appendChild(lijst);
        detail.appendChild(cel);
        rij.parentNode.insertBefore(detail, rij.nextSibling);

        window.GekoppeldeTeksten.render(lijst, refs, { boeknamen: boeknamen });
    }

    function werkAantalBij(rij, aantal) {
        var laatsteCel = rij.cells[rij.cells.length - 1];
        if (!laatsteCel) return;
        var teller = laatsteCel.querySelector('.me-tel');
        if (!aantal) {
            if (teller) teller.parentNode.removeChild(teller);
            return;
        }
        if (!teller) {
            laatsteCel.appendChild(document.createTextNode(' '));
            teller = document.createElement('span');
            teller.className = 'me-tel';
            laatsteCel.appendChild(teller);
        }
        teller.textContent = aantal + '×';
    }
})();
