/* Open Vertaling — aangezette kolommen bovenaan de tekst.
 *
 * Wie naast de Bijbeltekst een kolom aanzet (kanttekeningen, SV 1888, de
 * grondtalen, een parallelle editie), krijgt die kolom hier als knopje met een
 * minteken. Eén tik en de kolom is weer weg, zonder het Weergave-paneel te
 * openen en de juiste schakelaar te zoeken. Staan er meer kolommen aan, dan
 * haalt "Alleen de Bijbeltekst" ze in één keer allemaal weg.
 *
 * De knopjes bedienen de bestaande schakelaars in het paneel, zodat opslaan,
 * het kolommenraster en de spiegels onder "Meest gebruikt" gewoon meelopen.
 * Geen lookbehind of andere nieuwigheden: de ondergrens is iPadOS 15.4. */
(function () {
    'use strict';

    const houder = document.getElementById('kolom-chips');
    if (!houder) return;

    const SCHAKELAARS = 'input[data-toggle-col], input[data-parallel-editie]';

    function naamVan(input) {
        const rij = input.closest('label');
        if (!rij) return input.dataset.toggleCol || input.dataset.parallelEditie || '';
        const kop = rij.querySelector('strong');
        const tekst = (kop ? kop.textContent : rij.textContent).replace(/\s+/g, ' ').trim();
        return tekst.replace(/ als kolom$/, '');
    }

    function aangezet() {
        const gezien = new Set();
        const kolommen = [];
        document.querySelectorAll(SCHAKELAARS).forEach(input => {
            if (!input.checked || input.closest('.option-mirror')) return;
            const sleutel = input.dataset.toggleCol
                ? 'kolom:' + input.dataset.toggleCol
                : 'editie:' + input.dataset.parallelEditie;
            // De Bijbeltekst zelf is geen extra kolom en blijft altijd staan.
            if (sleutel === 'kolom:2026' || gezien.has(sleutel)) return;
            gezien.add(sleutel);
            kolommen.push({ input, naam: naamVan(input) });
        });
        return kolommen;
    }

    function zetUit(input) {
        if (!input.checked) return;
        input.checked = false;
        input.dispatchEvent(new Event('change', { bubbles: true }));
        if (window.OptionsPanel && typeof window.OptionsPanel.syncOptionMirrors === 'function') {
            window.OptionsPanel.syncOptionMirrors();
        }
    }

    function knop(tekst, klasse, label, bijKlik) {
        const el = document.createElement('button');
        el.type = 'button';
        el.className = klasse;
        el.setAttribute('aria-label', label);
        el.title = label;
        const woord = document.createElement('span');
        woord.textContent = tekst;
        el.appendChild(woord);
        el.addEventListener('click', bijKlik);
        return el;
    }

    function teken() {
        const kolommen = aangezet();
        houder.textContent = '';
        houder.hidden = kolommen.length === 0;
        kolommen.forEach(({ input, naam }) => {
            const el = knop(naam, 'kolom-chip', naam + ' weghalen', () => zetUit(input));
            const min = document.createElement('span');
            min.className = 'kolom-chip-min';
            min.setAttribute('aria-hidden', 'true');
            min.textContent = '−';
            el.appendChild(min);
            houder.appendChild(el);
        });
        if (kolommen.length > 1) {
            houder.appendChild(knop('Alleen de Bijbeltekst', 'kolom-chip kolom-chip-alles',
                'Alle extra kolommen weghalen',
                () => kolommen.forEach(({ input }) => zetUit(input))));
        }
    }

    document.addEventListener('change', e => {
        if (e.target && e.target.matches && e.target.matches(SCHAKELAARS)) teken();
    });
    window.addEventListener('ov:opties-gewijzigd', teken);

    // Bij het laden zet de app de bewaarde kolommen terug zonder change-event;
    // de hide-klassen op #content veranderen dan wel. Daar kijken we naar.
    const content = document.getElementById('content');
    if (content && typeof MutationObserver === 'function') {
        new MutationObserver(teken).observe(content, { attributes: true, attributeFilter: ['class'] });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', teken);
    } else {
        teken();
    }
})();
