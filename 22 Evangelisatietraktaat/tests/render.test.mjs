import test from 'node:test';
import assert from 'node:assert/strict';
import {
    passageId, passageTitel, dataUrl, afbeeldingUrl, leesUrl,
    boekNamen, escapeHtml, verzenHtml, uitlegHtml, spreadHtml,
} from '../js/render.js';

const config = {
    DATA_BASE: '../data/',
    IMG_BASE: '../images/chapters/',
    LEES_BASE: '../lees.html',
};

test('passageId koppelt boek en hoofdstuk', () => {
    assert.equal(passageId({ boek: 'genesis', hoofdstuk: 1 }), 'genesis_1');
    assert.equal(passageId({ boek: '1koningen', hoofdstuk: 8 }), '1koningen_8');
});

test('passageTitel zonder versbereik is boek en hoofdstuk', () => {
    assert.equal(passageTitel({ boek: 'genesis', hoofdstuk: 1 }, 'Genesis'), 'Genesis 1');
});

test('passageTitel met versbereik toont de verzen', () => {
    assert.equal(
        passageTitel({ boek: 'jesaja', hoofdstuk: 5, verzen: [1, 24] }, 'Jesaja'),
        'Jesaja 5:1-24',
    );
});

test('passageTitel gebruikt een eigen titel als die er is', () => {
    assert.equal(
        passageTitel({ boek: 'gebedvanmanasse', hoofdstuk: 1, titel: 'Gebed van Manasse' }, 'Gebed van Manasse'),
        'Gebed van Manasse',
    );
});

test('urls worden uit de config opgebouwd', () => {
    const p = { boek: 'genesis', hoofdstuk: 1 };
    assert.equal(dataUrl(config, p), '../data/genesis/1.json');
    assert.equal(afbeeldingUrl(config, p), '../images/chapters/genesis_1.jpg');
    assert.equal(leesUrl(config, p), '../lees.html#genesis/1');
});

test('boekNamen maakt een tabel van id naar Nederlandse naam', () => {
    const namen = boekNamen({ books: [
        { id: 'genesis', nameDutch: 'Genesis' },
        { id: '1koningen', nameDutch: '1 Koningen' },
    ] });
    assert.equal(namen['1koningen'], '1 Koningen');
});

test('escapeHtml maakt tekst veilig', () => {
    assert.equal(escapeHtml('<b>&amp;</b>'), '&lt;b&gt;&amp;amp;&lt;/b&gt;');
    assert.equal(escapeHtml('gewone tekst'), 'gewone tekst');
});

test('verzenHtml zet versnummer en tekst om', () => {
    const html = verzenHtml([
        { number: 1, text2026: 'In het begin schiep God de hemel en de aarde.' },
        { number: 2, text2026: 'De aarde nu was woest & leeg.' },
    ]);
    assert.match(html, /<span class="versnr">1<\/span>/);
    assert.match(html, /In het begin schiep God/);
    assert.match(html, /woest &amp; leeg/);
    assert.equal((html.match(/class="vers"/g) || []).length, 2);
});

test('uitlegHtml valt terug op "Uitleg volgt"', () => {
    assert.match(uitlegHtml(''), /Uitleg volgt/);
    assert.match(uitlegHtml(undefined), /Uitleg volgt/);
    assert.match(uitlegHtml('God is de Maker'), /God is de Maker/);
    assert.doesNotMatch(uitlegHtml('God is de Maker'), /Uitleg volgt/);
});

test('spreadHtml bevat kop, link, afbeelding en een lege tekstplek', () => {
    const html = spreadHtml({
        id: 'genesis_1',
        titel: 'Genesis 1',
        leesHref: '../lees.html#genesis/1',
        afbeelding: '../images/chapters/genesis_1.jpg',
        uitleg: '',
    });
    assert.match(html, /id="genesis_1"/);
    assert.match(html, /href="\.\.\/lees\.html#genesis\/1"/);
    assert.match(html, /Genesis 1/);
    assert.match(html, /src="\.\.\/images\/chapters\/genesis_1\.jpg"/);
    assert.match(html, /data-tekst="genesis_1"/);
    assert.match(html, /Uitleg volgt/);
});
