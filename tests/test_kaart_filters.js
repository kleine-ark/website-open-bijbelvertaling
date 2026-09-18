/* Gedragsregressies voor kaartfilters en plaatsselectie, zonder kaarttegels of browser.
 * Uitvoeren: node --test tests/test_kaart_filters.js
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '..', 'kaart.html'), 'utf8');
const filterCode = html.slice(html.indexOf('        var boekSelect ='), html.indexOf('        Promise.all(['));
const selectieCode = html.slice(html.indexOf('            var feats ='), html.indexOf('        }).catch(function (e)'));
const instellingenCode = fs.readFileSync(path.join(__dirname, '..', 'js', 'kaart-instellingen.js'), 'utf8');

function openKaart(query, options = {}) {
    const url = new URL('https://example.test/kaart.html' + query);
    let actiefElement;
    const documentHandlers = {};
    function element() {
        return { value: '', checked: true, hidden: true, disabled: false, style: { display: 'none' }, handlers: {}, attributes: {}, children: [],
            addEventListener(type, handler) { this.handlers[type] = handler; },
            setAttribute(name, value) { this.attributes[name] = String(value); },
            removeAttribute(name) { delete this.attributes[name]; },
            appendChild(child) { this.children.push(child); }, replaceChildren() { this.children = []; },
            querySelectorAll() { return this.children; }, scrollIntoView() {}, focus() { actiefElement = this; }, contains(target) { return this === target || this.children.includes(target); }
        };
    }
    const elementen = {};
    const verificaties = [];
    for (const id of ['f-boek', 'f-hoofdstuk', 'f-zeker', 'f-waarschijnlijk', 'f-onzeker', 'telling', 'popup', 'popup-content', 'kaart-zoek', 'kaart-zoekveld', 'kaart-zoek-wis', 'kaart-zoek-resultaten', 'kaart-zoek-status', 'kaart-zoek-paneel', 'kaart-zoek-alles', 'kaart-schaal', 'kaart-schaal-hint', 'kaart-instellingen-open', 'kaart-instellingen', 'kaart-instellingen-sluit']) {
        elementen[id] = element();
    }
    elementen['f-boek'].value = url.searchParams.get('boek') || '';
    elementen['f-hoofdstuk'].value = url.searchParams.get('hoofdstuk') || '';
    actiefElement = elementen['kaart-zoekveld'];
    const features = [
        { id: 'geo-abarim', naam: 'Abarim', zekerheid: 'zeker', refs: [
            { boek: 'numeri', hoofdstuk: 27, vers: 12, ref: 'numeri 27:12', href: 'index.html#numeri/27/12' },
            { boek: 'numeri', hoofdstuk: 33, vers: 47, ref: 'numeri 33:47', href: 'index.html#numeri/33/47' }
        ] },
        { id: 'geo-betlehem', legacyIds: ['geo-legacy-bethlehem'], naam: 'Betlehem', zekerheid: 'zeker', refs: [
            { boek: 'mattheus', hoofdstuk: 2, vers: 1, ref: 'mattheus 2:1', href: 'index.html#mattheus/2/1' }
        ] },
        { id: 'geo-ararat', naam: 'Ararat', zekerheid: 'onzeker', refs: [
            { boek: 'genesis', hoofdstuk: 8, vers: 4, ref: 'genesis 8:4', href: 'index.html#genesis/8/4' }
        ] },
        { id: 'geo-sinai', naam: 'Sinai', zekerheid: 'onzeker', refs: [
            { boek: 'numeri', hoofdstuk: 10, vers: 12, ref: 'numeri 10:12', href: 'index.html#numeri/10/12' }
        ] }
    ].map((properties, index) => ({
        properties,
        get(key) { return this.properties[key]; },
        getProperties() { return this.properties; },
        setStyle(style) { this.style = style; },
        getGeometry() { return { getCoordinates() { return [index, index]; } }; }
    }));
    const overlay = { position: undefined, setPosition(position) { this.position = position; }, panIntoView() {} };
    const map = {
        handlers: {}, hit: null, animations: [], size: [1280, 569],
        on(type, handler) { this.handlers[type] = handler; },
        forEachFeatureAtPixel(_pixel, callback) { return this.hit && callback(this.hit); },
        getSize() { return this.size; },
        getView() { return { animate(animation, callback) { map.lastAnimation = animation; map.animations.push(callback); if (!options.deferAnimations && callback) callback(true); }, fit(extent) { map.lastExtent = Array.from(extent); }, getZoom() { return 5; }, on() {} }; }
    };
    const helperPath = path.join(__dirname, '..', 'js', 'kaart-locaties.js');
    const KaartLocaties = fs.existsSync(helperPath) ? require(helperPath) : undefined;
    const context = vm.createContext({
        URL, URLSearchParams, KaartLocaties,
        document: { getElementById(id) { return elementen[id]; }, createElement() { return element(); },
            addEventListener(type, handler) { (documentHandlers[type] ||= []).push(handler); }, get activeElement() { return actiefElement; } },
        window: { location: { href: url.href, search: url.search }, matchMedia() { return { matches: true }; } },
        history: { replaceState(_state, _title, destination) { context.lastUrl = destination; } },
        vectorSource: { forEachFeature(callback) { features.forEach(callback); }, getFeatures() { return features; }, addFeatures() {}, getExtent() { return [-99, -99, 99, 99]; } },
        vectorLayer: { changed() {} }, labelLayer: { changed() {} }, geselecteerdePlaats: null,
        ol: {
            extent: { boundingExtent(coordinates) { return [Math.min(...coordinates.map(c => c[0])), Math.min(...coordinates.map(c => c[1])), Math.max(...coordinates.map(c => c[0])), Math.max(...coordinates.map(c => c[1]))]; } },
            style: { Style: class { constructor(options) { this.options = options; } } },
            format: { GeoJSON: class { readFeatures() { return features; } } }
        },
        markerStyle() { return { options: { image: 'geselecteerde-markering' } }; },
        esc: value => String(value || ''), prettyRef: value => value, refHref: value => value,
        overlay, map, res: [{}],
        Verification: { mount(parent, type, id, opties) { verificaties.push({ parent, type, id, opties }); } }
    });
    vm.runInContext(instellingenCode, context, { filename: 'js/kaart-instellingen.js' });
    vm.runInContext(filterCode + selectieCode, context, { filename: 'kaart.html' });
    return {
        elementen, features, overlay, context, map, verificaties,
        filter() { vm.runInContext('pasFilterToe()', context); },
        zoek(waarde) { elementen['kaart-zoekveld'].focus(); elementen['kaart-zoekveld'].value = waarde; elementen['kaart-zoekveld'].handlers.input?.(); },
        toets(key) {
            const event = new Event('keydown', { bubbles: true, cancelable: true });
            Object.defineProperty(event, 'key', { value: key });
            actiefElement.handlers.keydown?.(event);
            if (!event.cancelBubble) (documentHandlers.keydown || []).forEach(handler => handler(event));
        },
        klik(id) { map.hit = features.find(feature => feature.get('id') === id); map.handlers.singleclick({ pixel: [0, 0] }); }
    };
}

function zichtbareNamen(kaart) {
    return kaart.features.filter(feature => !feature.style || feature.style.options.image).map(feature => feature.get('naam'));
}

test('een gedeelde plaats buiten het boekfilter blijft verborgen', () => {
    const kaart = openKaart('?plaats=geo-abarim&boek=mattheus&hoofdstuk=2');
    assert.deepEqual(zichtbareNamen(kaart), ['Betlehem']);
    assert.equal(kaart.elementen.telling.textContent, '1 plaatsen');
});

test('een gedeelde plaats buiten het hoofdstukfilter blijft verborgen', () => {
    const kaart = openKaart('?plaats=geo-abarim&boek=numeri&hoofdstuk=10');
    assert.deepEqual(zichtbareNamen(kaart), ['Sinai']);
    assert.equal(kaart.elementen.telling.textContent, '1 plaatsen');
});

test('een passende gedeelde plaats blijft zichtbaar en gemarkeerd', () => {
    const kaart = openKaart('?plaats=geo-abarim&boek=numeri&hoofdstuk=27');
    assert.deepEqual(zichtbareNamen(kaart), ['Abarim']);
    assert.equal(kaart.context.geselecteerdePlaats, kaart.features[0]);
});

test('een popup met oude verwijzingen sluit na wijziging van het hoofdstukfilter', () => {
    const kaart = openKaart('?boek=numeri&hoofdstuk=27');
    kaart.klik('geo-abarim');
    assert.equal(kaart.elementen.popup.style.display, '');
    assert.match(kaart.elementen['popup-content'].innerHTML, /numeri\/27\/12/);
    kaart.elementen['f-hoofdstuk'].value = '33';
    kaart.filter();
    assert.equal(kaart.elementen.popup.style.display, 'none');
    assert.equal(kaart.overlay.position, undefined);
    kaart.klik('geo-abarim');
    assert.match(kaart.elementen['popup-content'].innerHTML, /numeri\/33\/47/);
    assert.doesNotMatch(kaart.elementen['popup-content'].innerHTML, /numeri\/27\/12/);
});

test('een geopende plaats toont de verificatie voor die plaats', () => {
    const kaart = openKaart('');
    kaart.klik('geo-abarim');
    assert.equal(kaart.verificaties.length, 1);
    assert.equal(kaart.verificaties[0].parent, kaart.elementen['popup-content']);
    assert.equal(kaart.verificaties[0].type, 'location');
    assert.equal(kaart.verificaties[0].id, 'geo-abarim');
});

test('uitschakelen van een onzekerheidsklasse verbergt ook de open popup', () => {
    const kaart = openKaart('');
    kaart.klik('geo-ararat');
    kaart.elementen['f-onzeker'].checked = false;
    kaart.elementen['f-onzeker'].handlers.change();
    assert.deepEqual(zichtbareNamen(kaart), ['Abarim', 'Betlehem']);
    assert.equal(kaart.elementen.popup.style.display, 'none');
    assert.equal(kaart.overlay.position, undefined);
});

test('een expliciete oude plaats-id selecteert het canonieke punt en behoudt canonieke bronlinks', () => {
    const kaart = openKaart('?plaats=geo-legacy-bethlehem&boek=mattheus&hoofdstuk=2');
    assert.equal(kaart.context.geselecteerdePlaats, kaart.features[1]);
    kaart.klik('geo-betlehem');
    assert.match(kaart.elementen['popup-content'].innerHTML, /href="plaats\.html\?plaats=geo-betlehem"/);
    assert.doesNotMatch(kaart.elementen['popup-content'].innerHTML, /geo-legacy-bethlehem/);
});

test('een oude plaats-id mag de actieve boekfilter niet omzeilen', () => {
    const kaart = openKaart('?plaats=geo-legacy-bethlehem&boek=numeri&hoofdstuk=27');
    assert.deepEqual(zichtbareNamen(kaart), ['Abarim']);
});

test('een oude plaats-id zonder expliciete koppeling selecteert geen ander punt', () => {
    const kaart = openKaart('?plaats=geo-legacy-ararat');
    assert.equal(kaart.context.geselecteerdePlaats, null);
});

test('een boekfilter past het beginbeeld uitsluitend om passende punten', () => {
    const kaart = openKaart('?boek=numeri&hoofdstuk=27');
    assert.deepEqual(kaart.map.lastExtent, [0, 0, 0, 0]);
});

test('zoeken met het toetsenbord selecteert het punt, opent de popup en zoomt in', () => {
    const kaart = openKaart('');
    kaart.zoek('Betlehem');
    assert.equal(kaart.elementen['kaart-zoekveld'].attributes['aria-expanded'], 'true');
    kaart.toets('ArrowDown');
    kaart.toets('Enter');
    assert.equal(kaart.context.geselecteerdePlaats, kaart.features[1]);
    assert.equal(kaart.elementen.popup.style.display, '');
    assert.match(kaart.elementen['popup-content'].innerHTML, /geo-betlehem/);
    assert.equal(kaart.map.lastAnimation.zoom, 12);
    assert.equal(kaart.elementen['kaart-zoekveld'].attributes['aria-expanded'], 'false');
});

test('buiten het filter zoeken vraagt expliciet filters wissen voordat selectie mogelijk is', () => {
    const kaart = openKaart('?boek=numeri&hoofdstuk=27');
    kaart.zoek('Betlehem');
    assert.equal(kaart.elementen['kaart-zoek-alles'].hidden, false);
    kaart.toets('Enter');
    assert.equal(kaart.context.geselecteerdePlaats, null);
    assert.deepEqual(zichtbareNamen(kaart), ['Abarim']);
    kaart.elementen['kaart-zoek-alles'].handlers.click();
    assert.equal(kaart.elementen['f-boek'].value, '');
    assert.equal(kaart.elementen['f-hoofdstuk'].value, '');
    kaart.toets('ArrowDown');
    kaart.toets('Enter');
    assert.equal(kaart.context.geselecteerdePlaats, kaart.features[1]);
});

test('Escape sluit suggesties en wissen verwijdert de selectie zonder de filters te veranderen', () => {
    const kaart = openKaart('?boek=numeri');
    kaart.zoek('Abarim');
    kaart.toets('Escape');
    assert.equal(kaart.elementen['kaart-zoekveld'].attributes['aria-expanded'], 'false');
    kaart.zoek('Abarim');
    kaart.toets('ArrowDown');
    kaart.toets('Enter');
    kaart.elementen['kaart-zoek-wis'].handlers.click();
    assert.equal(kaart.elementen['kaart-zoekveld'].value, '');
    assert.equal(kaart.context.geselecteerdePlaats, null);
    assert.equal(kaart.elementen['f-boek'].value, 'numeri');
});

test('pijl omhoog zonder actieve suggestie begint bij het laatste resultaat', () => {
    const kaart = openKaart('');
    kaart.zoek('a');
    kaart.toets('ArrowUp');
    kaart.toets('Enter');
    assert.equal(kaart.context.geselecteerdePlaats, kaart.features[3]);
});

test('filterwijziging ververst open suggesties voordat Enter een oude treffer kan kiezen', () => {
    const kaart = openKaart('');
    kaart.zoek('Ararat');
    kaart.elementen['f-onzeker'].checked = false;
    kaart.filter();
    kaart.toets('Enter');
    assert.equal(kaart.context.geselecteerdePlaats, null);
    assert.equal(kaart.elementen['kaart-zoek-resultaten'].children.length, 0);
    assert.equal(kaart.elementen['kaart-zoek-alles'].hidden, false);
});

test('Escape sluit eerst de suggesties met behoud van focus en daarna pas de instellingen', () => {
    const kaart = openKaart('');
    kaart.elementen['kaart-instellingen-open'].handlers.click();
    assert.equal(kaart.elementen['kaart-instellingen'].hidden, false);
    kaart.zoek('Abarim');
    kaart.toets('Escape');
    assert.equal(kaart.elementen['kaart-zoek-paneel'].hidden, true);
    assert.equal(kaart.elementen['kaart-instellingen'].hidden, false);
    assert.equal(kaart.context.document.activeElement, kaart.elementen['kaart-zoekveld']);
    kaart.toets('Escape');
    assert.equal(kaart.elementen['kaart-instellingen'].hidden, true);
    assert.equal(kaart.context.document.activeElement, kaart.elementen['kaart-instellingen-open']);
});

test('de zoekpopup wordt pas na het inzoomen geplaatst zodat automatisch pannen behouden blijft', () => {
    const kaart = openKaart('', { deferAnimations: true });
    kaart.zoek('Betlehem');
    kaart.toets('Enter');
    assert.equal(kaart.elementen.popup.style.display, 'none');
    assert.equal(kaart.overlay.position, undefined);
    kaart.map.animations[0](true);
    assert.equal(kaart.elementen.popup.style.display, '');
    assert.deepEqual(kaart.overlay.position, [1, 1]);
});

test('een gewiste selectie krijgt geen popup door een late zoomcallback', () => {
    const kaart = openKaart('', { deferAnimations: true });
    kaart.zoek('Betlehem');
    kaart.toets('Enter');
    kaart.elementen['kaart-zoek-wis'].handlers.click();
    assert.equal(typeof kaart.map.animations[0], 'function');
    kaart.map.animations[0](true);
    assert.equal(kaart.elementen.popup.style.display, 'none');
    assert.equal(kaart.overlay.position, undefined);
});

test('de popupinhoud blijft scrollbaar binnen een lage mobiele kaartviewport', () => {
    const kaart = openKaart('');
    kaart.map.size = [360, 220];
    kaart.klik('geo-abarim');
    assert.ok(parseFloat(kaart.elementen['popup-content'].style.maxHeight) < 180);
    assert.ok(parseFloat(kaart.elementen['popup-content'].style.maxHeight) > 0);
});
