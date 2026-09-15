const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'wiki-overzicht.html'), 'utf8');
const cards = [...html.matchAll(/<a class="wo-kaart"[\s\S]*?<img src="([^"]+)"[\s\S]*?<h3>([\s\S]*?)<\/h3>/g)];
const expected = ['Onderwerpen', 'Woordenboek', 'Voedsel', 'Afgoden &amp; machten', 'Muziekinstrumenten', 'Drukversie'];

for (const title of expected) {
    const card = cards.find(match => match[2].trim() === title);
    assert.ok(card, `${title}: hoofdcategorie heeft een kaart`);
    assert.match(card[1], /\.webp$/);
    assert.ok(fs.existsSync(path.join(root, card[1])), `${title}: afbeelding bestaat`);
}

const sources = cards.map(card => card[1]);
assert.equal(new Set(sources).size, sources.length, 'iedere hoofdcategorie gebruikt een eigen afbeelding');
console.log(`${cards.length} hoofdcategorieën hebben elk een unieke, bestaande afbeelding`);
