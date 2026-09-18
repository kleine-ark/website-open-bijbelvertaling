/* Echte serviceworker-fetchrouter met een geheugen-cache en gecontroleerd netwerk.
 * Uitvoeren: node --test tests/test_serviceworker_geojson.js
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'sw.js'), 'utf8');
const origin = 'https://example.test';

function serviceworker() {
    const handlers = new Map(), buckets = new Map();
    let networkBody = 'eerste versie', offline = false, fetchCount = 0;
    let httpCacheBody;
    const caches = {
        async open(name) {
            if (!buckets.has(name)) buckets.set(name, new Map());
            const entries = buckets.get(name);
            return {
                async match(request) { return entries.get(request.url)?.clone(); },
                async put(request, response) { entries.set(request.url, response.clone()); }
            };
        }
    };
    const context = vm.createContext({
        URL, Response, console, caches,
        self: { location: { origin }, addEventListener(type, handler) { handlers.set(type, handler); } },
        async fetch(_request, options) {
            fetchCount++;
            if (offline) throw new Error('Netwerk niet beschikbaar');
            // no-cache herbevestigt bij de server, no-store slaat de HTTP-cache helemaal over.
            if (httpCacheBody !== undefined && options?.cache !== 'no-cache' && options?.cache !== 'no-store') {
                return new Response(httpCacheBody, { status: 200 });
            }
            return new Response(networkBody, { status: 200 });
        }
    });
    vm.runInContext(source, context, { filename: 'sw.js' });
    return {
        netwerk(body) { networkBody = body; offline = false; },
        httpCache(body) { httpCacheBody = body; },
        offline() { offline = true; },
        get fetchCount() { return fetchCount; },
        async seed(cacheName, requestPath, body) {
            const cache = await caches.open(vm.runInContext(cacheName, context));
            await cache.put(new Request(origin + requestPath), new Response(body));
        },
        async request(requestPath) {
            let response;
            handlers.get('fetch')({
                request: new Request(origin + requestPath),
                respondWith(promise) { response = promise; }
            });
            assert.ok(response, 'De serviceworker moet deze lokale GET afhandelen');
            return response;
        }
    };
}

test('GeoJSON haalt meteen nieuwe gegevens op ondanks een oude shell-cache', async () => {
    const sw = serviceworker();
    await sw.seed('SHELL_CACHE', '/data/geografie-runtime.geojson', 'verouderde kaartpunten');
    sw.netwerk('bijgewerkte kaartpunten');
    const response = await sw.request('/data/geografie-runtime.geojson');
    assert.equal(await response.text(), 'bijgewerkte kaartpunten');
    assert.equal(sw.fetchCount, 1);
});

for (const suffix of ['.geojson', '.json']) {
    test(suffix + ' haalt online de actuele gegevens op, ook bij een nog verse browser-HTTPcache', async () => {
        const sw = serviceworker();
        sw.httpCache('verouderde HTTP-cache');
        sw.netwerk('actuele gegevens');
        assert.equal(await (await sw.request('/data/plaatsen' + suffix)).text(), 'actuele gegevens');
        sw.offline();
        assert.equal(await (await sw.request('/data/plaatsen' + suffix)).text(), 'actuele gegevens');
    });

    test(suffix + ' ververst online en bewaart de nieuwste versie voor offline gebruik', async () => {
        const sw = serviceworker();
        const requestPath = '/data/plaatsen' + suffix + '?taal=nl';
        sw.netwerk('eerste versie');
        assert.equal(await (await sw.request(requestPath)).text(), 'eerste versie');
        sw.netwerk('nieuwste versie');
        assert.equal(await (await sw.request(requestPath)).text(), 'nieuwste versie');
        sw.offline();
        assert.equal(await (await sw.request(requestPath)).text(), 'nieuwste versie');
        assert.equal(sw.fetchCount, 3);
    });
}

test('GeoJSON valt offline terug op de bestaande data-cache', async () => {
    const sw = serviceworker();
    await sw.seed('DATA_CACHE', '/data/geografie-runtime.geojson', 'bewaarde kaartpunten');
    sw.offline();
    const response = await sw.request('/data/geografie-runtime.geojson');
    assert.equal(response.status, 200);
    assert.equal(await response.text(), 'bewaarde kaartpunten');
});

test('HTML haalt online de actuele versie op, ook bij een nog verse browser-HTTPcache', async () => {
    const sw = serviceworker();
    sw.httpCache('verse HTML uit browsercache');
    sw.netwerk('actuele HTML op de server');
    assert.equal(await (await sw.request('/kaart.html')).text(), 'actuele HTML op de server');
});

test('GeoJSON zonder netwerk of cache meldt dat de gegevens niet beschikbaar zijn', async () => {
    const sw = serviceworker();
    sw.offline();
    const response = await sw.request('/data/geografie-runtime.geojson');
    assert.equal(response.status, 503);
});

test('afbeeldingen behouden de bestaande cache-first strategie', async () => {
    const sw = serviceworker();
    await sw.seed('SHELL_CACHE', '/images/kaart.webp', 'bewaarde afbeelding');
    sw.netwerk('andere afbeelding');
    assert.equal(await (await sw.request('/images/kaart.webp')).text(), 'bewaarde afbeelding');
    assert.equal(sw.fetchCount, 0);
});
