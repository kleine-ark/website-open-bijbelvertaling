/* Tests voor de verwijzingspopup en de grondwoorden in kanttekeningen.
 *
 * Draaien:  node tests/test_verwijzing_popup.js
 */

const fs = require('fs');
const path = require('path');

const pad = naam => path.join(__dirname, '..', 'js', naam);
const References = eval(fs.readFileSync(pad('references.js'), 'utf8') + '\n;References');
const VerwijzingPopup = require(pad('verwijzing-popup.js'));
const NootGrondwoorden = require(pad('noot-grondwoorden.js'));

let mislukt = 0;
function check(naam, conditie, detail) {
    if (conditie) {
        console.log(`  ok   ${naam}`);
    } else {
        mislukt++;
        console.log(`  FOUT ${naam}`);
        if (detail !== undefined) console.log(`       ${detail}`);
    }
}

console.log('verwijzingspopup en grondwoorden\n');

// --- Safari 15.4: geen lookbehind in de nieuwe bestanden ---
for (const naam of ['verwijzing-popup.js', 'noot-grondwoorden.js']) {
    const code = fs.readFileSync(pad(naam), 'utf8').replace(/\/\*[\s\S]*?\*\//g, '');
    check(`${naam} bevat geen RegExp-lookbehind`, !/\(\?<[=!]/.test(code));
}

// --- references.js: het laatste vers van een reeks gaat mee ---
const bereik = References.linkify('Spr. 8:22-23 en Ps. 90:2.', 'genesis', 1);
check('reeks met streepje krijgt data-ref-tot', bereik.includes('data-ref-vs="22" data-ref-tot="23"'), bereik);
check('los vers krijgt geen data-ref-tot', /data-ref-vs="2"(?! data-ref-tot)/.test(bereik), bereik);
const opsomming = References.linkify('Zie Spr. 8:22,23 hierover.', 'genesis', 1);
check('opsomming met komma krijgt data-ref-tot', opsomming.includes('data-ref-tot="23"'), opsomming);
const verkort = References.linkify('Ps. 33:6, 89:12-14.', 'genesis', 1);
check('verkorte verwijzing met reeks krijgt data-ref-tot', verkort.includes('data-ref-ch="89" data-ref-vs="12" data-ref-tot="14"'), verkort);

// --- popup: tekst uit het hoofdstuk ---
const { kaleTekst, verzen, label, MAX_VERZEN } = VerwijzingPopup._intern;
check('nummertjes, opmaak en entiteiten verdwijnen uit de verstekst',
    kaleTekst('En God<sup class="note-marker" data-note="10">10</sup> zei: <span class="god-speaks"><i>Daar zij licht!</i></span> &amp; meer')
        === 'En God zei: Daar zij licht! & meer');

const hoofdstuk = { verses: Array.from({ length: 12 }, (_, i) => ({ number: i + 1, text2026_html: `vers ${i + 1}` })) };
const twee = verzen(hoofdstuk, 22 - 20, 23 - 20);
check('een reeks levert precies die verzen', twee.verzen.map(v => v.nummer).join(',') === '2,3' && !twee.ingekort, JSON.stringify(twee));
const lang = verzen(hoofdstuk, 2, 12);
check(`een lange reeks wordt na ${MAX_VERZEN} verzen afgekapt`, lang.verzen.length === MAX_VERZEN && lang.ingekort, JSON.stringify(lang));
check('een niet-bestaand vers levert niets', verzen(hoofdstuk, 99, null).verzen.length === 0);
check('zonder hoofdstukdata geen fout', verzen(null, 1, 3).verzen.length === 0);
check('kop met reeks', label('Spreuken', 8, 22, 23) === 'Spreuken 8:22-23');
check('kop zonder vers', label('Genesis', 20, null, null) === 'Genesis 20');

// --- grondwoorden ---
check('klinkertekens en scheidingstekens tellen niet mee',
    NootGrondwoorden.normaliseer('בְּ/צַלְמֵ֖/נוּ') === NootGrondwoorden.normaliseer('בְּצַלְמֵנוּ'));
check('Griekse accenten en slot-sigma tellen niet mee',
    NootGrondwoorden.normaliseer('λόγος') === NootGrondwoorden.normaliseer('λογοσ'));
check('voorvoegselnummers vallen weg', NootGrondwoorden.nummerVan('H9003 H7225') === 'H7225');
check('twee echte nummers is geen koppeling', NootGrondwoorden.nummerVan('H1254 H7225') === null);

const vers26 = { grondtekst: [
    { woord: 'וַ/יֹּ֣אמֶר', strongs: 'H559' },
    { woord: 'בְּ/צַלְמֵ֖/נוּ', strongs: 'H6754' },
] };
const gelinkt = NootGrondwoorden.link('Hebr. betsalmenu (בְּצַלְמֵנוּ), in ons beeld.', vers26);
check('grondwoord uit de grondtekst van het vers wordt een woordenboekknop',
    gelinkt.includes('class="strongs-inline grondwoord-link" data-strongs="H6754"') && gelinkt.includes('>בְּצַלְמֵנוּ</button>'), gelinkt);
const lemma = NootGrondwoorden.link('Hebr. raqia (רָקִיעַ), van raqa (רָקַע).', { grondtekst: [{ woord: 'רָקִ֖יעַ', strongs: 'H7549' }] });
check('woord dat in het vers staat wel, lemma dat er niet staat niet',
    lemma.includes('data-strongs="H7549"') && lemma.includes('(רָקַע)'), lemma);
const dubbel = NootGrondwoorden.link('Hebr. (אֵת)', { grondtekst: [{ woord: 'אֵת', strongs: 'H853' }, { woord: 'אֵת', strongs: 'H854' }] });
check('vorm met twee nummers in hetzelfde vers blijft tekst', !dubbel.includes('<button'), dubbel);
check('zonder grondtekst blijft de noot ongewijzigd', NootGrondwoorden.link('Hebr. (אָב)', {}) === 'Hebr. (אָב)');
const naLinkify = NootGrondwoorden.link(References.linkify('Hebr. (בְּצַלְמֵנוּ); zie Gen. 5:1.', 'genesis', 1), vers26);
check('werkt ook op tekst waar al verwijzingslinks in staan',
    naLinkify.includes('data-strongs="H6754"') && naLinkify.includes('data-ref-book="genesis" data-ref-ch="5"'), naLinkify);

console.log(mislukt ? `\n${mislukt} test(s) mislukt` : '\nalles in orde');
process.exit(mislukt ? 1 : 0);
