const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'onderwerpen.html'), 'utf8');
const context = {};
vm.createContext(context);
const helper = path.join(root, 'js/onderwerp-afbeeldingen.js');
if (fs.existsSync(helper)) vm.runInContext(fs.readFileSync(helper, 'utf8'), context);
vm.runInContext(html.match(/function kaartHTML\(tag\) \{[\s\S]*?(?=        function toonGrid)/)[0], context);
for (const id of ['schepping', 'wijn']) {
  const card = context.kaartHTML({id, naam: id, verzen: []});
  const source = card.match(/<img[^>]+src="([^"]+)"/);
  assert.ok(source, `${id}: kaart bevat een afbeelding`);
  assert.ok(fs.existsSync(path.join(root, source[1])), `${id}: afbeelding bestaat`);
  if (id === 'wijn') assert.ok(source[1].endsWith('wijn-v2.webp'));
}
assert.ok(!context.kaartHTML({id: 'nieuw-onderwerp', verzen: []}).includes('<img'));
assert.ok(html.includes('id="ond-detail-beeld"'));
console.log('Onderwerpkaarten, detailbeeld en veilige ontbrekende afbeelding: geslaagd');
