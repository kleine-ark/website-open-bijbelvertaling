/* Open Vertaling — Service Worker
 *
 * Strategieën:
 *   - shell (HTML/CSS/JS): cache-first met background network-update
 *   - data (JSON): stale-while-revalidate — instant uit cache, vernieuwt op achtergrond
 *   - lexicon (grote JS): cache-first, geen revalidate (zelden gewijzigd)
 *
 * Versionering: bump VERSION bij elke deploy om alle caches te vernieuwen.
 */

const VERSION = '2026-05-14a';
const SHELL_CACHE   = `shell-${VERSION}`;
const DATA_CACHE    = `data-${VERSION}`;
const LEXICON_CACHE = `lexicon-${VERSION}`;

// Pre-cache: minimal kritieke files voor instant 1e bezoek
const PRECACHE_URLS = [
    '/',
    '/index.html',
    '/css/style.css',
    '/js/storage.js',
    '/js/data-loader.js',
    '/js/navigation.js',
    '/js/sidebar.js',
    '/js/app.js',
    '/js/opties.js',
    '/js/begrippen.js',
    '/js/references.js',
    '/js/lexicon.js',
    '/js/editor.js',
    '/js/export.js',
    '/js/column-resize.js',
    '/js/column-reorder.js',
    '/js/verse-select.js',
    '/js/highlight.js',
    '/js/tags.js',
    '/js/search.js',
    '/data/books.json',
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(SHELL_CACHE).then(cache =>
            // Per file proberen — als 1 faalt, geen volledige install-fail
            Promise.allSettled(PRECACHE_URLS.map(url =>
                cache.add(url).catch(err => console.warn('SW precache miss:', url, err))
            ))
        ).then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil((async () => {
        // Verwijder oude caches
        const keys = await caches.keys();
        await Promise.all(
            keys.filter(k => ![SHELL_CACHE, DATA_CACHE, LEXICON_CACHE].includes(k))
                .map(k => caches.delete(k))
        );
        await self.clients.claim();
    })());
});

self.addEventListener('fetch', (event) => {
    const req = event.request;
    if (req.method !== 'GET') return;

    const url = new URL(req.url);
    // Only handle same-origin
    if (url.origin !== self.location.origin) return;

    const path = url.pathname;

    // Lexicon (grote JS)
    if (path.endsWith('/js/hebreeuws-woordenboek.js') || path.endsWith('/js/grieks-woordenboek.js')) {
        event.respondWith(cacheFirst(req, LEXICON_CACHE));
        return;
    }

    // Data files (JSON in /data/)
    if (path.startsWith('/data/') && path.endsWith('.json')) {
        event.respondWith(staleWhileRevalidate(req, DATA_CACHE));
        return;
    }

    // Shell files (HTML, CSS, andere JS)
    if (path.endsWith('.html') || path.endsWith('.css') || path.endsWith('.js') || path === '/') {
        event.respondWith(cacheFirstWithRefresh(req, SHELL_CACHE));
        return;
    }

    // Fonts, images, alles anders: cache-first
    event.respondWith(cacheFirst(req, SHELL_CACHE));
});

/** Cache-first: gebruik cache, fetch alleen als miss. */
async function cacheFirst(req, cacheName) {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(req);
    if (cached) return cached;
    try {
        const resp = await fetch(req);
        if (resp.ok) cache.put(req, resp.clone());
        return resp;
    } catch (e) {
        return new Response('Offline en niet in cache', { status: 503 });
    }
}

/** Cache-first met background refresh. Gebruiker krijgt direct cached versie,
 *  cache wordt op achtergrond geüpdatet voor volgende bezoek. */
async function cacheFirstWithRefresh(req, cacheName) {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(req);
    const fetchPromise = fetch(req).then(resp => {
        if (resp.ok) cache.put(req, resp.clone());
        return resp;
    }).catch(() => cached || Response.error());
    return cached || fetchPromise;
}

/** Stale-while-revalidate: cached versie direct, fetch op achtergrond. */
async function staleWhileRevalidate(req, cacheName) {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(req);
    const fetchPromise = fetch(req).then(resp => {
        if (resp.ok) cache.put(req, resp.clone());
        return resp;
    }).catch(() => null);
    return cached || fetchPromise || new Response('Offline en niet in cache', { status: 503 });
}

// Message handler — voor cache-clear van app
self.addEventListener('message', (event) => {
    if (event.data === 'clearAllCaches') {
        event.waitUntil((async () => {
            const keys = await caches.keys();
            await Promise.all(keys.map(k => caches.delete(k)));
            self.clients.matchAll().then(clients =>
                clients.forEach(c => c.postMessage('cachesCleared'))
            );
        })());
    }
});
