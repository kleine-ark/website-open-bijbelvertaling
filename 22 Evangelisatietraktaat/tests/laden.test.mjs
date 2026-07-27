import test from 'node:test';
import assert from 'node:assert/strict';
import { verzenInBereik, laadPassage } from '../js/laden.js';

const config = { DATA_BASE: '../data/' };

const hoofdstuk = {
    number: 1,
    verses: [
        { number: 1, text2026: 'een' },
        { number: 2, text2026: 'twee' },
        { number: 3, text2026: 'drie' },
    ],
};

function nepFetch(antwoord) {
    return async () => antwoord;
}

test('verzenInBereik zonder bereik geeft alle verzen', () => {
    assert.equal(verzenInBereik(hoofdstuk.verses, undefined).length, 3);
});

test('verzenInBereik filtert inclusief begin en eind', () => {
    const uit = verzenInBereik(hoofdstuk.verses, [2, 3]);
    assert.deepEqual(uit.map(v => v.number), [2, 3]);
});

test('laadPassage geeft de gefilterde verzen bij een goed antwoord', async () => {
    const fetchFn = nepFetch({ ok: true, json: async () => hoofdstuk });
    const uit = await laadPassage(fetchFn, config, { boek: 'genesis', hoofdstuk: 1, verzen: [2, 2] });
    assert.equal(uit.ok, true);
    assert.deepEqual(uit.verzen.map(v => v.number), [2]);
});

test('laadPassage vraagt de juiste url op', async () => {
    let gevraagd = null;
    const fetchFn = async (url) => { gevraagd = url; return { ok: true, json: async () => hoofdstuk }; };
    await laadPassage(fetchFn, config, { boek: 'jona', hoofdstuk: 2 });
    assert.equal(gevraagd, '../data/jona/2.json');
});

test('laadPassage meldt een http-fout', async () => {
    const fetchFn = nepFetch({ ok: false, status: 404 });
    const uit = await laadPassage(fetchFn, config, { boek: 'genesis', hoofdstuk: 1 });
    assert.equal(uit.ok, false);
    assert.match(uit.fout, /404/);
});

test('laadPassage meldt een netwerkfout', async () => {
    const fetchFn = async () => { throw new Error('offline'); };
    const uit = await laadPassage(fetchFn, config, { boek: 'genesis', hoofdstuk: 1 });
    assert.equal(uit.ok, false);
    assert.match(uit.fout, /offline/);
});

test('laadPassage meldt een fout als het antwoord geen verzen bevat', async () => {
    const fetchFn = nepFetch({ ok: true, json: async () => ({ boodschap: 'geen hoofdstuk' }) });
    const uit = await laadPassage(fetchFn, config, { boek: 'genesis', hoofdstuk: 1 });
    assert.equal(uit.ok, false);
    assert.match(uit.fout, /verzen/i);
});
