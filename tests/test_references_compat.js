/* Regressietest — js/references.js moet werken op Safari < 16.4.
 *
 * iPadOS 15.4 t/m 16.3 kent géén RegExp-lookbehind ((?<=...)). Stond die in de
 * verwijzings-regex, dan gooide new RegExp() een SyntaxError midden in de
 * verzen-renderlus van App.renderChapter() — met als gevolg dat kop en voet
 * (statische HTML) wél verschenen, maar de hele hoofdstuktekst niet.
 *
 * Draaien:  node tests/test_references_compat.js
 */

const fs = require('fs');
const path = require('path');

const SRC_PATH = path.join(__dirname, '..', 'js', 'references.js');
const src = fs.readFileSync(SRC_PATH, 'utf8');
const References = eval(src + '\n;References');

// Commentaar eruit: alleen echte code telt voor de compatibiliteitscheck,
// anders slaat de test aan op een toelichting die (?<=...) noemt.
const code = src
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/(^|[^:])\/\/.*$/gm, '$1');

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

console.log('references.js — Safari-compatibiliteit en gedrag\n');

// 1. Kern van de bug: geen lookbehind in het bronbestand.
check(
    'bevat geen RegExp-lookbehind (Safari < 16.4)',
    !/\(\?<[=!]/.test(code),
    'gevonden: ' + (code.match(/.*\(\?<[=!].*/) || [''])[0].trim()
);

// 2. Volledige boek-verwijzing blijft werken.
const volledig = References.linkify('Zie Gen. 1:1 hierover.', 'genesis', 1);
check(
    'volledige boek-verwijzing wordt gelinkt',
    volledig.includes('data-ref-book="genesis"') && volledig.includes('data-ref-ch="1"'),
    volledig
);

// 3. Verkorte verwijzing na komma blijft werken.
const verkort = References.linkify('Zie Ps. 89:12, 90:1 daarover.', 'psalmen', 1);
check(
    'verkorte verwijzing na komma wordt gelinkt',
    verkort.includes('data-ref-ch="90"') && verkort.includes('data-ref-vs="1"'),
    verkort
);

// 4. De scheidende komma mag niet uit de tekst verdwijnen.
check(
    'komma tussen twee verwijzingen blijft staan',
    /<\/a>,\s*<a/.test(verkort),
    verkort
);

// 5. Zonder voorafgaande komma géén verkorte link (oorspronkelijk gedrag).
const losStaand = References.linkify('In 5:6 staat iets.', 'genesis', 1);
check(
    'getal zonder voorafgaande komma wordt niet gelinkt',
    !losStaand.includes('ref-link'),
    losStaand
);

// 6. Fallback: linkify mag nooit gooien, ook niet als de regex onbouwbaar is.
//    Dan liever onopgemaakte tekst dan een lege pagina.
const bewaard = References.REF_REGEX;
References.REF_REGEX = { source: '(' };   // levert gegarandeerd een SyntaxError op
let fallbackOk = false;
let fallbackUit = '';
const warnBewaard = console.warn;
console.warn = () => {};              // de verwachte waarschuwing niet meelogen
try {
    fallbackUit = References.linkify('Zie Gen. 1:1 hierover.', 'genesis', 1);
    fallbackOk = fallbackUit === 'Zie Gen. 1:1 hierover.';
} catch (e) {
    fallbackUit = 'gooide: ' + e.message;
} finally {
    console.warn = warnBewaard;
}
References.REF_REGEX = bewaard;
check(
    'linkify valt terug op platte tekst i.p.v. te gooien',
    fallbackOk,
    fallbackUit
);

console.log('');
if (mislukt > 0) {
    console.log(`${mislukt} test(s) mislukt`);
    process.exit(1);
}
console.log('alle tests geslaagd');
