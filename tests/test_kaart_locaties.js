const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const helperPath = path.join(__dirname, '..', 'js', 'kaart-locaties.js');
const locaties = fs.existsSync(helperPath) ? require(helperPath) : {};
const runtime = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'data', 'geografie-runtime.geojson'), 'utf8')).features;
const fixtures = [
    { id: 'stad-a', naam: 'Én-Gedi', aliases: ['Engedi'], moderneNaam: 'Ein Gedi', type: 'stad-dorp', zekerheid: 'zeker', refs: [{ boek: 'jozua', hoofdstuk: 15 }] },
    { id: 'streek-b', naam: 'En-Gedi', aliases: ['Engedi'], moderneNaam: 'Ein Gedi', type: 'land-streek', zekerheid: 'onzeker', refs: [{ boek: 'hooglied', hoofdstuk: 1 }] },
    { id: 'leeg', naam: 'Los punt', zekerheid: 'waarschijnlijk', refs: [] }
];

test('naam, alias en moderne naam zijn accent- en koppeltekensonafhankelijk vindbaar', () => {
    assert.equal(typeof locaties.search, 'function');
    for (const query of ['en gedi', 'Engedi', 'EIN–GEDI']) {
        assert.deepEqual(locaties.search(fixtures, query, {}).matches.map(r => r.feature.id).sort(), ['stad-a', 'streek-b']);
    }
});

test('gelijknamige plaatsen blijven afzonderlijke resultaten met onderscheidende bronidentiteit', () => {
    const results = locaties.search(fixtures, 'Engedi', {}).matches;
    assert.equal(results.length, 2);
    assert.notEqual(results[0].detail, results[1].detail);
    assert.match(results[0].detail, /stad-a|streek-b/);
});

test('zoekresultaten respecteren boek, hoofdstuk en zekerheid en tellen treffers buiten het filter apart', () => {
    assert.deepEqual(locaties.search(fixtures, 'Engedi', { boek: 'jozua', hoofdstuk: 15 }).matches.map(r => r.feature.id), ['stad-a']);
    assert.equal(locaties.search(fixtures, 'Engedi', { boek: 'jozua', hoofdstuk: 14 }).outsideCount, 2);
    assert.equal(locaties.search(fixtures, 'Engedi', { boek: 'jozua', hoofdstuk: 14 }).matches.length, 0);
    assert.equal(locaties.search(fixtures, 'Engedi', { onzeker: false }).matches.length, 1);
    assert.equal(locaties.search(fixtures, 'Los punt', {}).matches.length, 1);
});

test('lege zoekopdrachten en ontbrekende optionele velden zijn veilig', () => {
    assert.deepEqual(locaties.search(fixtures, '  ', {}), { matches: [], outsideCount: 0, total: 0 });
    assert.equal(locaties.search([{}], 'iets', {}).total, 0);
});

test('zoeken doorloopt de volledige runtime en scheidt de twee Jericho-identificaties', () => {
    assert.equal(runtime.length, 1269);
    const results = locaties.search(runtime, 'Jericho', {}).matches;
    assert.ok(results.some(r => r.feature.properties.id === 'geo-jericho-1-231f80'));
    assert.ok(results.some(r => r.feature.properties.id === 'geo-jericho-2-af03fa'));
    assert.ok(locaties.search(runtime, 'Zophim', {}).matches.length > 0);
});

test('een exacte alias komt vóór een toevallige deelmatch met meer verwijzingen', () => {
    assert.equal(locaties.search(runtime, 'Enon', {}).matches[0].feature.properties.id, 'geo-aenon-112fe3');
});

test('de vier schaalniveaus schakelen op de grenzen 6, 9 en 12', () => {
    assert.deepEqual([5, 5.9, 6, 8.9, 9, 11.9, 12, 18].map(z => locaties.scale(z).id), ['overzicht', 'overzicht', 'regio', 'regio', 'omgeving', 'omgeving', 'detail', 'detail']);
});

test('gecureerde hoofdplaatsen krijgen voorrang boven alleen vermeldingsfrequentie', () => {
    const nazareth = runtime.find(f => f.properties.id === 'geo-nazareth-f5884f');
    const veelRefs = { id: 'kleine-plaats', naam: 'Kleine plaats', refs: Array(1000).fill({ boek: 'jozua', hoofdstuk: 1 }) };
    assert.ok(locaties.importance(nazareth, {}) > locaties.importance(veelRefs, {}));
    assert.equal(locaties.presentation(nazareth, 5, {}, false).label, true);
    assert.equal(locaties.presentation(fixtures[0], 5, {}, false).label, false);
    assert.ok(locaties.presentation(fixtures[0], 5, {}, false).radius < locaties.presentation(nazareth, 5, {}, false).radius);
    assert.equal(locaties.presentation(fixtures[0], 12, {}, false).label, true);
});

test('selectie krijgt labelvoorrang maar kan filters nooit omzeilen', () => {
    assert.equal(locaties.presentation(fixtures[1], 5, { onzeker: false }, true).visible, false);
    assert.equal(locaties.presentation(fixtures[0], 5, {}, true).label, true);
    assert.ok(locaties.compareFeatures(fixtures[0], fixtures[1], {}, 'stad-a') < 0);
});
