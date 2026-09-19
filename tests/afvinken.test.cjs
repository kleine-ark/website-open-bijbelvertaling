/* Hele hoofdstukken tegelijk afvinken: node --test tests/afvinken.test.cjs */
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
require('../js/review-components.js');
require('../js/herverificatie.js');

const { Herverificatie } = globalThis;
const bytes = text => new TextEncoder().encode(text);
const sha = text => createHash('sha256').update(text).digest('hex');

// Onderdelen zoals de API ze geeft: [status, needsReverification, present].
function hoofdstuk(id, onderdelen) {
    const components = {};
    for (const [key, [status, needsReverification, present = true]] of Object.entries(onderdelen)) {
        components[key] = { revision: 'rev-' + key + '-' + id, status, needsReverification, present };
    }
    const bron = '{"number":' + id.split('/')[1] + '}';
    const [boek, nummer] = id.split('/');
    return {
        type: 'text-chapter', id, revision: 'rev-' + id, label: boek + ' ' + nummer, href: 'index.html#' + id,
        source: 'data/' + id + '.json', status: components.text.status, needsReverification: components.text.needsReverification,
        metadata: { sourceHash: sha(bron), components }, components, bron,
    };
}

const nieuw = hoofdstuk('tobit/1', { text: ['pending', false], citations: ['pending', false], intro: ['pending', false],
    notes: ['approved', false, false] });
const opnieuw = hoofdstuk('tobit/2', { text: ['pending', true], citations: ['approved', false] });
const klaar = hoofdstuk('tobit/3', { text: ['approved', false], intro: ['approved', false] });
const correctie = hoofdstuk('tobit/4', { text: ['correction-needed', true] });

test('een heel hoofdstuk bevestigt elk aanwezig onderdeel dat nog open staat', () => {
    assert.deepEqual(Herverificatie.openOnderdelen(nieuw), ['text', 'citations', 'intro']);
    assert.deepEqual(Herverificatie.openOnderdelen(opnieuw), ['text']);
    assert.deepEqual(Herverificatie.openOnderdelen(klaar), []);
});

test('de stand van een hoofdstuk zegt wat afvinken ervoor betekent', () => {
    assert.equal(Herverificatie.stand(nieuw), 'nieuw');
    assert.equal(Herverificatie.stand(opnieuw), 'opnieuw');
    assert.equal(Herverificatie.stand(klaar), 'goedgekeurd');
    assert.equal(Herverificatie.stand(correctie), 'correctie');
});

test('een boek laden haalt precies dat boek op, in de volgorde van de hoofdstukken', async () => {
    const catalogus = [hoofdstuk('baruch/10', { text: ['pending', false] }), hoofdstuk('4baruch/1', { text: ['pending', false] }),
        hoofdstuk('baruch/2', { text: ['approved', false] }), hoofdstuk('baruch/1', { text: ['pending', true] })];
    const vragen = [];
    const items = await Herverificatie.laadBoek(async pad => {
        const vraag = new URLSearchParams(pad.split('?')[1]);
        vragen.push([pad.split('?')[0], vraag.get('type'), vraag.get('q'), vraag.get('status')]);
        const passend = catalogus.filter(item => item.id.includes(vraag.get('q')));
        const begin = Number(vraag.get('offset'));
        return { total: passend.length, items: passend.slice(begin, begin + Number(vraag.get('limit'))) };
    }, 'baruch');
    assert.deepEqual(vragen, [['/subjects', 'text-chapter', 'baruch/', null]]);
    assert.deepEqual(items.map(item => item.id), ['baruch/1', 'baruch/2', 'baruch/10']);
});

test('afvinken legt alle open onderdelen vast op hun huidige revisie', async () => {
    const verzoeken = [];
    const uitkomst = await Herverificatie.verifieer(nieuw, {
        bron: async () => bytes(nieuw.bron),
        api: async (pad, opties) => { verzoeken.push([pad, JSON.parse(opties.body)]); return { subject: {} }; },
    }, Herverificatie.openOnderdelen);
    assert.deepEqual(uitkomst, { id: 'tobit/1', ok: true });
    assert.deepEqual(verzoeken, [['/reviews', {
        subjectType: 'text-chapter', subjectId: 'tobit/1', revision: 'rev-tobit/1', sourceHash: nieuw.metadata.sourceHash,
        components: { text: 'rev-text-tobit/1', citations: 'rev-citations-tobit/1', intro: 'rev-intro-tobit/1' },
        decision: 'approved', note: '',
    }]]);
});

/* ---- De pagina, met een nagebootst scherm ---- */

function element(tag) {
    return {
        tag, children: [], hidden: false, disabled: false, checked: false, value: '', type: '', label: '',
        textContent: '', className: '', href: '', luisteraars: {},
        append(...nodes) { this.children.push(...nodes); },
        replaceChildren(...nodes) { this.children = nodes; },
        setAttribute(naam, waarde) { this[naam] = waarde; },
        addEventListener(type, handler) { this.luisteraars[type] = handler; },
        klik() { return this.luisteraars.click(); },
        wijzig() { return this.luisteraars.change(); },
        get tekst() { return [this.textContent, ...this.children.map(child => child.tekst)].join(' ').replace(/\s+/g, ' ').trim(); },
        vind(test) { return test(this) ? this : this.children.map(child => child.vind(test)).find(Boolean); },
        alle(test) { return [...(test(this) ? [this] : []), ...this.children.flatMap(child => child.alle(test))]; },
    };
}

function opstelling(catalogus, { zoek = '' } = {}) {
    const vast = {};
    for (const id of ['boek-afvinken-sectie', 'boek-keuze', 'boek-status', 'boek-lijst', 'boek-alles-aan', 'boek-afvinken']) {
        vast[id] = element(id);
    }
    const verzoeken = [];
    const Collaboration = {
        currentUser: { roles: ['reviewer'] },
        hasRole(role) { return !!this.currentUser && this.currentUser.roles.includes(role); },
        async api(pad, opties) {
            if (pad.startsWith('/subjects')) {
                const vraag = new URLSearchParams(pad.split('?')[1]);
                const passend = catalogus.filter(item => item.id.includes(vraag.get('q')));
                return { total: passend.length, items: passend };
            }
            const opdracht = JSON.parse(opties.body);
            verzoeken.push([opdracht.subjectId, Object.keys(opdracht.components)]);
            const item = catalogus.find(kandidaat => kandidaat.id === opdracht.subjectId);
            for (const onderdeel of Object.values(item.components)) { onderdeel.status = 'approved'; onderdeel.needsReverification = false; }
            return { subject: item };
        },
    };
    const pagina = Herverificatie.boekPagina({
        document: { getElementById: id => vast[id], createElement: element }, Collaboration, zoek,
        boeken: async () => [{ id: 'tobit', naam: 'Tobit', testament: 'Apocrief / deuterocanoniek' },
            { id: 'susanna', naam: 'Susanna', testament: 'Apocrief / deuterocanoniek' }],
        bron: async pad => bytes(catalogus.find(item => item.source === pad).bron),
    });
    return { vast, verzoeken, Collaboration, pagina };
}

const vakjes = vast => vast['boek-lijst'].alle(node => node.type === 'checkbox');

test('zonder reviewerrol blijft het afvinken verborgen', async () => {
    const { vast, Collaboration, pagina } = opstelling([nieuw]);
    Collaboration.currentUser = null;
    await pagina.toon(null, true);
    assert.equal(vast['boek-afvinken-sectie'].hidden, true);
});

test('een gekozen boek toont elk hoofdstuk met zijn stand, de open hoofdstukken al aangevinkt', async () => {
    const catalogus = [hoofdstuk('tobit/1', { text: ['pending', false], intro: ['pending', false] }),
        hoofdstuk('tobit/2', { text: ['pending', true] }), hoofdstuk('tobit/3', { text: ['approved', false] }),
        hoofdstuk('tobit/4', { text: ['correction-needed', true] })];
    const { vast, Collaboration, pagina } = opstelling(catalogus, { zoek: '?boek=tobit' });
    await pagina.toon(Collaboration.currentUser, true);
    assert.equal(vast['boek-afvinken-sectie'].hidden, false);
    assert.equal(vast['boek-keuze'].value, 'tobit');
    assert.deepEqual(vast['boek-keuze'].alle(node => node.tag === 'option').map(optie => optie.value), ['', 'tobit', 'susanna']);
    const lijst = vast['boek-lijst'].tekst;
    assert.match(lijst, /tobit 1 .*nog niet nagekeken/);
    assert.match(lijst, /tobit 2 .*opnieuw verifiëren/);
    assert.match(lijst, /tobit 3 .*goedgekeurd/);
    assert.match(lijst, /tobit 4 .*openstaande correctie/);
    assert.deepEqual(vakjes(vast).map(vakje => [vakje.checked, vakje.disabled]),
        [[true, false], [true, false], [true, true], [false, true]]);
    assert.match(vast['boek-afvinken'].textContent, /2 hoofdstukken afvinken/);
});

test('afvinken vraagt eerst bevestiging en keurt daarna alleen de aangevinkte hoofdstukken goed', async () => {
    const catalogus = [hoofdstuk('tobit/1', { text: ['pending', false], citations: ['pending', false] }),
        hoofdstuk('tobit/2', { text: ['pending', false] }), hoofdstuk('tobit/3', { text: ['pending', true] })];
    const { vast, verzoeken, Collaboration, pagina } = opstelling(catalogus, { zoek: '?boek=tobit' });
    await pagina.toon(Collaboration.currentUser, true);
    const [, tweede] = vakjes(vast);
    tweede.checked = false;
    await tweede.wijzig();
    const knop = vast['boek-afvinken'];
    assert.match(knop.textContent, /2 hoofdstukken afvinken/);
    await knop.klik();
    assert.match(knop.textContent, /Bevestig/);
    assert.match(knop.textContent, /nagelezen/);
    assert.deepEqual(verzoeken, []);
    await knop.klik();
    assert.deepEqual(verzoeken, [['tobit/1', ['text', 'citations']], ['tobit/3', ['text']]]);
    assert.match(vast['boek-status'].textContent, /2 hoofdstukken afgevinkt/);
    assert.match(vast['boek-lijst'].tekst, /tobit 1 .*✓ afgevinkt/);
    assert.deepEqual(vakjes(vast).map(vakje => vakje.disabled), [true, false, true]);
});

test('alles aanvinken zet elk open hoofdstuk aan', async () => {
    const catalogus = [hoofdstuk('tobit/1', { text: ['pending', false] }), hoofdstuk('tobit/2', { text: ['pending', false] })];
    const { vast, Collaboration, pagina } = opstelling(catalogus, { zoek: '?boek=tobit' });
    await pagina.toon(Collaboration.currentUser, true);
    for (const vakje of vakjes(vast)) { vakje.checked = false; await vakje.wijzig(); }
    assert.equal(vast['boek-afvinken'].disabled, true);
    await vast['boek-alles-aan'].klik();
    assert.deepEqual(vakjes(vast).map(vakje => vakje.checked), [true, true]);
    assert.match(vast['boek-afvinken'].textContent, /2 hoofdstukken afvinken/);
});

test('een ander boek kiezen laadt dat boek', async () => {
    const catalogus = [hoofdstuk('tobit/1', { text: ['pending', false] }), hoofdstuk('susanna/1', { text: ['pending', false] })];
    const { vast, Collaboration, pagina } = opstelling(catalogus);
    await pagina.toon(Collaboration.currentUser, true);
    assert.equal(vast['boek-lijst'].children.length, 0);
    vast['boek-keuze'].value = 'susanna';
    await vast['boek-keuze'].wijzig();
    assert.match(vast['boek-lijst'].tekst, /susanna 1/);
    assert.doesNotMatch(vast['boek-lijst'].tekst, /tobit/);
});

test('de pagina heeft de elementen voor het afvinken en Beoordelingen wijst erheen', () => {
    const fs = require('node:fs');
    const path = require('node:path');
    const html = fs.readFileSync(path.join(__dirname, '..', 'herverificatie.html'), 'utf8');
    for (const id of ['boek-afvinken-sectie', 'boek-keuze', 'boek-status', 'boek-lijst', 'boek-alles-aan', 'boek-afvinken']) {
        assert.match(html, new RegExp('id="' + id + '"'), id);
    }
    const beoordelingen = fs.readFileSync(path.join(__dirname, '..', 'beoordelingen.html'), 'utf8');
    assert.match(beoordelingen, /<a class="secondary-button" href="herverificatie\.html">Hoofdstukken afvinken<\/a>/);
});
