/* Open Vertaling — Hebreeuwse en Griekse woorden in kanttekeningen klikbaar maken.
 *
 * Een kanttekening noemt vaak het grondwoord: "Hebr. betsalmenu (בְּצַלְמֵנוּ),
 * in ons beeld." Staat dat woord ook in de grondtekst van hetzelfde vers, dan
 * is het Strongsnummer bekend. Het woord wordt dan een knop met de klasse
 * strongs-inline, zodat de bestaande klikafhandeling in lexicon.js het
 * woordenboekartikel opent, net als bij de Strongsnummers in de tekst.
 *
 * Alleen een exacte overeenkomst telt, na het weglaten van klinkertekens,
 * accenten en de scheidingstekens van de grondtekstlaag. Een verbogen vorm, een
 * lemma dat niet in het vers staat, of een vorm die in hetzelfde vers bij twee
 * verschillende nummers hoort, blijft gewone tekst:
 * scripts/grondwoorden_in_noten.py zet die op een werklijst.
 *
 * Geen lookbehind: de site moet werken op iPadOS 15.4.
 */
(function (global) {
    'use strict';

    const HEBREEUWS = /[א-תװ-ײ][֑-ׇא-תװ-״]*/g;
    const GRIEKS = /[Ͱ-Ͽἀ-῿][̀-ͯͰ-Ͽἀ-῿]*/g;
    const NUMMERS = /(?:OVL|OVG)\d+|[HG]\d+[A-Za-z]?/g;

    function normaliseer(woord) {
        return String(woord || '').normalize('NFD')
            .replace(/[֑-ׇ̀-ͯ]/g, '')
            .replace(/[\/־\sʹ͵;·]/g, '')
            .toLowerCase()
            .replace(/ς/g, 'σ');
    }

    /** Het ene Strongsnummer van een grondtekstwoord, of null.
     *  De extra nummers vanaf H9000 staan voor voorvoegsels en achtervoegsels. */
    function nummerVan(strongs) {
        const nummers = (String(strongs || '').match(NUMMERS) || [])
            .filter(n => !(n.charAt(0) === 'H' && parseInt(n.slice(1), 10) >= 9000));
        const uniek = nummers.filter((n, i) => nummers.indexOf(n) === i);
        return uniek.length === 1 ? uniek[0] : null;
    }

    /** Genormaliseerde vorm -> Strongsnummer voor de grondtekst van een vers.
     *  Een vorm die bij verschillende nummers hoort, valt af. */
    function indexVan(vers) {
        const index = new Map();
        const dubbelzinnig = new Set();
        ((vers && vers.grondtekst) || []).forEach(woord => {
            if (!woord || typeof woord !== 'object' || !woord.woord) return;
            const vorm = normaliseer(woord.woord);
            const nummer = nummerVan(woord.strongs);
            if (!vorm || !nummer) return;
            if (index.has(vorm) && index.get(vorm) !== nummer) dubbelzinnig.add(vorm);
            else index.set(vorm, nummer);
        });
        dubbelzinnig.forEach(vorm => index.delete(vorm));
        return index;
    }

    function link(html, vers) {
        const index = indexVan(vers);
        if (!index.size) return html;
        const vervang = (woord) => {
            const nummer = index.get(normaliseer(woord));
            if (!nummer) return woord;
            const hebreeuws = nummer.charAt(0) === 'H';
            return `<button type="button" class="strongs-inline grondwoord-link" data-strongs="${nummer}"`
                + ` lang="${hebreeuws ? 'he' : 'grc'}"${hebreeuws ? ' dir="rtl"' : ''}`
                + ` title="Woordenboek ${nummer}">${woord}</button>`;
        };
        return String(html == null ? '' : html).replace(HEBREEUWS, vervang).replace(GRIEKS, vervang);
    }

    const NootGrondwoorden = { normaliseer, nummerVan, indexVan, link };
    global.NootGrondwoorden = NootGrondwoorden;
    if (typeof module !== 'undefined' && module.exports) module.exports = NootGrondwoorden;
})(typeof window !== 'undefined' ? window : globalThis);
