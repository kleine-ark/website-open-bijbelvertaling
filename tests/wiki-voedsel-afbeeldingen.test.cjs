const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const cp = require('node:child_process');
const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'js/naslag.js'), 'utf8');
const data = JSON.parse(cp.execFileSync('git', ['show', 'origin/main:data/naslag-voedsel.json'], {cwd: root, encoding: 'utf8'}));
async function render(search) {
    const holder = {innerHTML: ''};
    const context = {
        document: {getElementById: id => id === 'naslag' ? holder : null, body: {getAttribute: () => 'data/naslag-voedsel.json'}},
        location: {search, pathname: '/voedsel.html'},
        fetch: async () => ({ok: true, json: async () => structuredClone(data)})
    };
    vm.runInNewContext(source, context);
    await new Promise(resolve => setImmediate(resolve));
    assert.ok(!holder.innerHTML.includes('undefined'));
    return holder.innerHTML;
}
(async () => {
    const overview = await render('');
    const images = [...overview.matchAll(/<img[^>]+src="([^"]+)"/g)];
    assert.equal(images.length, 11);
    images.forEach(image => assert.ok(fs.existsSync(path.resolve(root, image[1])), image[1]));
    const detail = await render('?item=brood');
    assert.ok(detail.includes('class="ns-detail-beeld"'));
    assert.ok(detail.includes('images/wiki/voedsel/brood.webp'));
    console.log('Voedsel: 11 bestaande afbeeldingen gekoppeld; kaart- en detailrenderer geslaagd');
})().catch(error => {console.error(error); process.exitCode = 1;});
