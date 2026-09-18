/* Voer de echte bronrenderer uit: node --test tests/test_plaats_bronnen.js */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '..', 'plaats.html'), 'utf8');
const renderer = html.slice(html.indexOf('        var inhoud ='), html.indexOf('        Promise.all(['));
const plaatsScript = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(match => match[1]).find(script => script.includes('var inhoud ='));

async function openPlaats(plaats, properties = {}) {
    const inhoud = { innerHTML: '', querySelector() { return { after() {} }; } };
    const feature = {
        geometry: { coordinates: [35.2, 31.7] },
        properties: {
            id: 'geo-betlehem', legacyIds: ['geo-legacy-bethlehem'], naam: 'Betlehem',
            type: 'stad', zekerheid: 'zeker', refs: [], ...properties
        }
    };
    const context = vm.createContext({
        URL, URLSearchParams,
        document: { getElementById() { return inhoud; }, createElement() { return {}; } },
        window: { location: { search: '?plaats=' + encodeURIComponent(plaats) } },
        async fetch(url) {
            return { ok: true, async json() { return url.endsWith('.geojson') ? { features: [feature] } : { books: [] }; } };
        },
        Verification: { async loadJSON(url) { return (await context.fetch(url)).json(); }, mount() {} }
    });
    vm.runInContext(plaatsScript, context, { filename: 'plaats.html' });
    await new Promise(setImmediate);
    return inhoud.innerHTML;
}

function renderBron(overrides = {}) {
    const inhoud = { innerHTML: '' };
    const feature = {
        geometry: { coordinates: [35.7152, 31.7539] },
        properties: {
            id: 'geo-abarim', naam: 'Abarim', type: 'berg', zekerheid: 'onzeker',
            refs: Array.from({ length: 15 }, (_, i) => ({
                boek: 'numeri', hoofdstuk: 33, vers: i + 1,
                href: 'index.html#numeri/33/' + (i + 1), status: 'needs-human-review'
            })),
            bron: {
                dataset: 'Geografische brondataset',
                url: 'https://www.openbible.info/geo/ancient/aa8275b',
                datasetUrl: 'https://github.com/openbibleinfo/Bible-Geocoding-Data',
                ancientId: 'aa8275b', modernId: 'm207993', identificationId: 'i123456',
                onderbouwing: 'Abarim, een gebergte', score: 242.5,
                scoreType: 'time_total × best_time_score / 1000',
                ...overrides
            }
        }
    };
    const context = vm.createContext({ URL, document: { getElementById() { return inhoud; } }, feature });
    vm.runInContext(renderer + '\ndetail(feature);', context, { filename: 'plaats.html' });
    return inhoud.innerHTML;
}

test('de directe plaatsbron en algemene dataset zijn afzonderlijk bereikbaar', () => {
    const rendered = renderBron();
    assert.match(rendered, /href="https:\/\/www\.openbible\.info\/geo\/ancient\/aa8275b"[^>]*>Bron openen/);
    assert.match(rendered, /href="https:\/\/github\.com\/openbibleinfo\/Bible-Geocoding-Data"[^>]*>Dataset openen/);
    assert.match(rendered, /Moderne locatie-id: m207993/);
    assert.match(rendered, /Identificatie-id: i123456/);
});

test('bronweging is zichtbaar met methode en niet als zekerheidspercentage', () => {
    const rendered = renderBron();
    assert.match(rendered, /Bronweging: 242,5/);
    assert.match(rendered, /time_total × best_time_score \/ 1000/);
    assert.match(rendered, /geen kanspercentage/);
    assert.doesNotMatch(rendered, /242[,.]5\s*%/);
});

test('alternatieven tonen hun eigen bronweging en kaartpunt', () => {
    const rendered = renderBron({ alternatieven: [{
        modernId: 'm654321', onderbouwing: 'Alternatieve heuvel', score: 125,
        lat: 31.5, lon: 35.25
    }] });
    assert.match(rendered, /Alternatieve identificaties/);
    assert.match(rendered, /Alternatieve heuvel/);
    assert.match(rendered, /m654321/);
    assert.match(rendered, /Bronweging: 125/);
    assert.match(rendered, /31\.50000, 35\.25000/);
});

test('regiopunten en een andere bronvoorkeur worden expliciet toegelicht', () => {
    const rendered = renderBron({ puntType: 'region', voorkeursInterpretatie: 'Onbekende locatie heeft de hoogste bronweging.' });
    assert.match(rendered, /region/);
    assert.match(rendered, /representatief punt/);
    assert.match(rendered, /Onbekende locatie heeft de hoogste bronweging\./);
});

test('broninhoud blijft tekst en onveilige bronlinks worden niet klikbaar', () => {
    const rendered = renderBron({
        url: 'javascript:alert(1)', datasetUrl: 'data:text/html,test',
        onderbouwing: '<script>onveilig</script>',
        alternatieven: [{ modernId: 'm1', onderbouwing: '<img src=x>', score: 0 }]
    });
    assert.doesNotMatch(rendered, /href="(?:javascript|data):/);
    assert.doesNotMatch(rendered, /<script>|<img/);
    assert.match(rendered, /&lt;script&gt;onveilig&lt;\/script&gt;/);
    assert.match(rendered, /&lt;img src=x&gt;/);
    assert.match(rendered, /Bronweging: 0/);
});

test('bronverrijking behoudt alle verslinks en werkt zonder optionele bronvelden', () => {
    const rendered = renderBron({ datasetUrl: undefined, identificationId: undefined, score: undefined, scoreType: undefined });
    assert.equal((rendered.match(/href="index\.html#numeri\/33\//g) || []).length, 15);
    assert.doesNotMatch(rendered, /undefined|NaN|Bronweging:/);
});

test('een expliciete oude plaats-id opent de bronpagina met een canonieke kaartlink', async () => {
    const rendered = await openPlaats('geo-legacy-bethlehem');
    assert.match(rendered, /<h1>Betlehem<\/h1>/);
    assert.match(rendered, /href="kaart\.html\?plaats=geo-betlehem"/);
    assert.doesNotMatch(rendered, /geo-legacy-bethlehem/);
});

test('de huidige plaats-id blijft werken zonder legacyIds', async () => {
    const rendered = await openPlaats('geo-betlehem', { legacyIds: undefined });
    assert.match(rendered, /<h1>Betlehem<\/h1>/);
});

for (const naam of ['Pella', 'Persepolis', 'Petra', 'Cus', 'Sion']) {
    test('geen impliciete oude-id-koppeling voor ' + naam, async () => {
        const slug = naam.toLowerCase();
        const rendered = await openPlaats('geo-legacy-' + slug, { id: 'geo-' + slug, naam, legacyIds: [] });
        assert.match(rendered, /Deze plaats is niet gevonden/);
    });
}
