/* Opnieuw verifiëren na een tekstwijziging: node --test tests/herverificatie.test.cjs */
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
require('../js/herverificatie.js');

const { Herverificatie } = globalThis;
const bytes = text => new TextEncoder().encode(text);
const sha = text => createHash('sha256').update(text).digest('hex');

function hoofdstuk(id, onderdelen, extra = {}) {
    const components = {};
    for (const [key, [status, needsReverification]] of Object.entries(onderdelen)) {
        components[key] = { revision: 'rev-' + key + '-' + id, status, needsReverification };
    }
    const bron = '{"number":' + id.split('/')[1] + '}';
    return {
        type: 'text-chapter', id, revision: 'rev-' + id, label: id, href: 'index.html#' + id,
        source: 'data/' + id + '.json', status: components.text.status,
        needsReverification: components.text.needsReverification,
        metadata: { sourceHash: sha(bron), components }, components, bron, ...extra,
    };
}

const vervallen = hoofdstuk('markus/4', { text: ['pending', true], markers: ['pending', true], notes: ['approved', false] });
const nooitBekeken = hoofdstuk('tobit/1', { text: ['pending', false], notes: ['pending', false] });
const goedgekeurd = hoofdstuk('markus/5', { text: ['approved', false], notes: ['approved', false] });
const metCorrectie = hoofdstuk('jona/4', { text: ['correction-needed', true], notes: ['approved', false] });

test('alleen hoofdstukken waarvan een eerdere goedkeuring is vervallen komen in aanmerking', () => {
    const gekozen = Herverificatie.kandidaten([vervallen, nooitBekeken, goedgekeurd, metCorrectie]);
    assert.deepEqual(gekozen.map(item => item.id), ['markus/4']);
});

test('een hoofdstuk met een openstaande correctie wordt apart gemeld en niet aangeboden', () => {
    const geblokkeerd = Herverificatie.geblokkeerd([vervallen, nooitBekeken, goedgekeurd, metCorrectie]);
    assert.deepEqual(geblokkeerd.map(item => item.id), ['jona/4']);
});

test('de opdracht bevestigt alleen de vervallen onderdelen, op hun huidige revisie', () => {
    assert.deepEqual(Herverificatie.opdracht(vervallen, vervallen.metadata.sourceHash), {
        subjectType: 'text-chapter', subjectId: 'markus/4', revision: 'rev-markus/4',
        sourceHash: vervallen.metadata.sourceHash,
        components: { text: 'rev-text-markus/4', markers: 'rev-markers-markus/4' },
        decision: 'approved', note: '',
    });
});

test('verifiëren leest het gepubliceerde bestand en legt de goedkeuring vast', async () => {
    const verzoeken = [];
    const uitkomst = await Herverificatie.verifieer(vervallen, {
        bron: async pad => { assert.equal(pad, 'data/markus/4.json'); return bytes(vervallen.bron); },
        api: async (pad, opties) => { verzoeken.push([pad, opties.method, JSON.parse(opties.body)]); return { subject: {} }; },
    });
    assert.deepEqual(uitkomst, { id: 'markus/4', ok: true });
    assert.equal(verzoeken.length, 1);
    assert.deepEqual(verzoeken[0].slice(0, 2), ['/reviews', 'POST']);
    assert.deepEqual(verzoeken[0][2], Herverificatie.opdracht(vervallen, vervallen.metadata.sourceHash));
});

test('wijkt het gepubliceerde bestand af van de catalogus, dan wordt er niets vastgelegd', async () => {
    let vastgelegd = 0;
    const uitkomst = await Herverificatie.verifieer(vervallen, {
        bron: async () => bytes('{"number":4,"later":"gewijzigd"}'),
        api: async () => { vastgelegd++; },
    });
    assert.equal(vastgelegd, 0);
    assert.equal(uitkomst.ok, false);
    assert.match(uitkomst.melding, /gewijzigd/i);
});

test('laden haalt alle wachtende hoofdstukken op, ook voorbij de eerste honderd', async () => {
    const wachtend = [vervallen, nooitBekeken, metCorrectie];
    for (let n = 1; n <= 120; n++) wachtend.push(hoofdstuk('psalmen/' + n, { text: ['pending', n === 119] }));
    const opgevraagd = [];
    const stand = await Herverificatie.laad(async pad => {
        const vraag = new URLSearchParams(pad.split('?')[1]);
        opgevraagd.push(pad.split('?')[0] + ' ' + vraag.get('type') + ' ' + vraag.get('status') + ' ' + vraag.get('offset'));
        // Zoals de API: het filter kijkt naar de status van de Bijbeltekst.
        const passend = wachtend.filter(item => item.status === vraag.get('status'));
        const begin = Number(vraag.get('offset'));
        return { total: passend.length, items: passend.slice(begin, begin + Number(vraag.get('limit'))) };
    });
    assert.deepEqual(opgevraagd, ['/subjects text-chapter pending 0', '/subjects text-chapter pending 100',
        '/subjects text-chapter correction-needed 0']);
    assert.deepEqual(stand.kandidaten.map(item => item.id), ['markus/4', 'psalmen/119']);
    assert.deepEqual(stand.geblokkeerd.map(item => item.id), ['jona/4']);
});

test('een geweigerde goedkeuring houdt de rest niet tegen', async () => {
    const tweede = hoofdstuk('lukas/11', { text: ['pending', true] });
    const voortgang = [];
    const uitkomsten = await Herverificatie.alles([vervallen, tweede], {
        bron: async pad => bytes(pad === 'data/markus/4.json' ? vervallen.bron : tweede.bron),
        api: async (_pad, opties) => {
            if (JSON.parse(opties.body).subjectId === 'markus/4') throw Object.assign(new Error('conflict'), { status: 409 });
            return { subject: {} };
        },
    }, uitkomst => voortgang.push(uitkomst.id));
    assert.deepEqual(uitkomsten.map(u => [u.id, u.ok]), [['markus/4', false], ['lukas/11', true]]);
    assert.match(uitkomsten[0].melding, /herlaad/i);
    assert.deepEqual(voortgang, ['markus/4', 'lukas/11']);
});

/* ---- De pagina, met een nagebootst scherm ---- */
require('../js/review-components.js');

function scherm() {
    function element(tag) {
        return {
            tag, children: [], hidden: false, disabled: false, textContent: '', className: '', href: '', luisteraars: {},
            append(...nodes) { this.children.push(...nodes); },
            replaceChildren(...nodes) { this.children = nodes; },
            addEventListener(type, handler) { this.luisteraars[type] = handler; },
            klik() { return this.luisteraars.click(); },
            get tekst() { return [this.textContent, ...this.children.map(child => child.tekst)].join(' ').replace(/\s+/g, ' ').trim(); },
            vind(test) { return test(this) ? this : this.children.map(child => child.vind(test)).find(Boolean); },
        };
    }
    const vast = { main: element('main'), 'herverificatie-status': element('p'), 'herverificatie-alles': element('button'),
        'herverificatie-lijst': element('section') };
    vast.main.hidden = true;
    return { vast, document: { querySelector: () => vast.main, getElementById: id => vast[id], createElement: element } };
}

function opstelling(items) {
    const { vast, document } = scherm();
    const verzoeken = [];
    const Collaboration = {
        currentUser: null,
        hasRole(role) { return !!this.currentUser && this.currentUser.roles.includes(role); },
        async api(pad, opties) {
            verzoeken.push([pad.split('?')[0], opties ? JSON.parse(opties.body).subjectId : null]);
            if (pad.startsWith('/subjects')) {
                const vraag = new URLSearchParams(pad.split('?')[1]);
                const passend = items.filter(item => item.status === vraag.get('status'));
                return { total: passend.length, items: passend };
            }
            const item = items.find(kandidaat => kandidaat.id === JSON.parse(opties.body).subjectId);
            for (const onderdeel of Object.values(item.components)) { onderdeel.status = 'approved'; onderdeel.needsReverification = false; }
            item.status = 'approved';
            return { subject: item };
        },
    };
    const pagina = Herverificatie.pagina({ document, Collaboration, ReviewComponents: globalThis.ReviewComponents,
        bron: async pad => bytes(items.find(item => item.source === pad).bron) });
    return { vast, verzoeken, Collaboration, pagina };
}

test('zonder reviewerrol wordt er niets opgevraagd en staat er hoe het wel kan', async () => {
    const { vast, verzoeken, pagina } = opstelling([vervallen]);
    await pagina.toon(null, true);
    assert.equal(vast.main.hidden, false);
    assert.match(vast['herverificatie-status'].textContent, /log in/i);
    assert.equal(vast['herverificatie-alles'].hidden, true);
    assert.deepEqual(verzoeken, []);
});

test('een reviewer ziet de vervallen hoofdstukken met hun onderdelen en één knop voor alles', async () => {
    const tweede = hoofdstuk('lukas/11', { text: ['pending', true] }, { label: 'Lukas 11' });
    const { vast, Collaboration, pagina } = opstelling([{ ...vervallen, label: 'Markus 4' }, tweede, nooitBekeken, metCorrectie]);
    Collaboration.currentUser = { roles: ['reviewer'] };
    await pagina.toon(Collaboration.currentUser, true);
    const lijst = vast['herverificatie-lijst'].tekst;
    assert.match(lijst, /Markus 4/);
    assert.match(lijst, /de Bijbeltekst en de nootnummers/);
    assert.match(lijst, /Lukas 11/);
    assert.doesNotMatch(lijst, /tobit/i);
    assert.match(lijst, /jona\/4.*openstaande correctie/i);
    assert.equal(vast['herverificatie-alles'].hidden, false);
    assert.match(vast['herverificatie-alles'].textContent, /Alles opnieuw verifiëren \(2\)/);
    assert.equal(vast['herverificatie-lijst'].vind(node => node.tag === 'a' && node.textContent === 'Markus 4').href, 'index.html#markus/4');
});

test('de knop voor alles vraagt eerst om bevestiging en legt daarna elke goedkeuring vast', async () => {
    const eerste = hoofdstuk('markus/4', { text: ['pending', true] }, { label: 'Markus 4' });
    const tweede = hoofdstuk('lukas/11', { text: ['pending', true] }, { label: 'Lukas 11' });
    const { vast, verzoeken, Collaboration, pagina } = opstelling([eerste, tweede]);
    Collaboration.currentUser = { roles: ['reviewer'] };
    await pagina.toon(Collaboration.currentUser, true);
    const knop = vast['herverificatie-alles'];
    await knop.klik();
    assert.match(knop.textContent, /Bevestig/);
    assert.deepEqual(verzoeken.filter(([pad]) => pad === '/reviews'), []);
    await knop.klik();
    assert.deepEqual(verzoeken.filter(([pad]) => pad === '/reviews'), [['/reviews', 'markus/4'], ['/reviews', 'lukas/11']]);
    assert.match(vast['herverificatie-status'].textContent, /2 hoofdstukken opnieuw geverifieerd/);
    assert.equal(knop.hidden, true);
});

test('de pagina start de login op, blijft buiten zoekmachines en biedt wat het script nodig heeft', () => {
    const html = require('node:fs').readFileSync(require('node:path').join(__dirname, '..', 'herverificatie.html'), 'utf8');
    assert.match(html, /<script type="module" src="\/js\/auth-bootstrap\.js"><\/script>/);
    assert.match(html, /<meta name="robots" content="noindex,nofollow">/);
    assert.match(html, /<main class="collaboration-main" hidden>/);
    for (const id of ['herverificatie-status', 'herverificatie-alles', 'herverificatie-lijst']) assert.match(html, new RegExp('id="' + id + '"'));
    assert.ok(html.indexOf('js/review-components.js') < html.indexOf('js/herverificatie.js'), 'de onderdelen moeten vóór het paginascript laden');
    assert.match(html, /href="beoordelingen\.html"/);
});

test('de pagina Beoordelingen wijst reviewers de weg naar het afvinken en opnieuw verifiëren', () => {
    const html = require('node:fs').readFileSync(require('node:path').join(__dirname, '..', 'beoordelingen.html'), 'utf8');
    assert.match(html, /<a class="secondary-button" href="herverificatie\.html">Hoofdstukken afvinken<\/a>/);
});
