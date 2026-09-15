/* Open Vertaling — de tekst van een Bijbelverwijzing als popup bij aanwijzen.
 *
 * Kanttekeningen verwijzen voortdurend naar andere plaatsen ("Ps. 90:2, Spr.
 * 8:22-23"). Wie met de muis over zo'n verwijzing gaat, ziet de verstekst in
 * een kleine popup, zonder het hoofdstuk te verlaten. Klikken springt nog
 * steeds naar de plaats; dat regelt references.js.
 *
 * Alleen op een apparaat met een muis. Op een touchscreen bestaat aanwijzen
 * niet, en daar blijft tikken gewoon navigeren.
 *
 * Geen lookbehind en geen recente API's: de site moet werken op iPadOS 15.4.
 */
(function (global) {
    'use strict';

    const MAX_VERZEN = 6;
    const TOON_NA_MS = 250;
    const VERBERG_NA_MS = 150;

    function escapeHtml(tekst) {
        return String(tekst == null ? '' : tekst)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    /** De leesbare tekst van een vers: zonder nummertjes, opmaak en entiteiten. */
    function kaleTekst(html) {
        return String(html || '')
            .replace(/<sup\b[^>]*>[\s\S]*?<\/sup>/gi, '')
            .replace(/<[^>]+>/g, '')
            .replace(/&nbsp;/g, ' ').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
            .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&')
            .replace(/\s+/g, ' ')
            .trim();
    }

    /** Verzen van..tot uit een hoofdstuk, hoogstens MAX_VERZEN. */
    function verzen(hoofdstuk, van, tot) {
        const lijst = (hoofdstuk && hoofdstuk.verses) || [];
        const gevraagdTot = tot && tot > van ? tot : van;
        const eind = Math.min(gevraagdTot, van + MAX_VERZEN - 1);
        const uit = [];
        lijst.forEach(vers => {
            const nummer = Number(vers.number);
            if (nummer < van || nummer > eind) return;
            const tekst = kaleTekst(vers.text2026_html || vers.text2026 || vers.textSV1888 || '');
            if (tekst) uit.push({ nummer, tekst });
        });
        return { verzen: uit, ingekort: gevraagdTot > eind };
    }

    function label(boeknaam, hoofdstuk, van, tot) {
        if (!van) return `${boeknaam} ${hoofdstuk}`;
        return `${boeknaam} ${hoofdstuk}:${van}${tot && tot > van ? `-${tot}` : ''}`;
    }

    let boeknamen = null;
    function laadBoeknamen() {
        if (!boeknamen) {
            boeknamen = fetch('data/books.json')
                .then(r => (r.ok ? r.json() : { books: [] }))
                .then(data => {
                    const namen = {};
                    (data.books || []).forEach(b => { namen[b.id] = b.nameDutch || b.name || b.id; });
                    return namen;
                })
                .catch(() => ({}));
        }
        return boeknamen;
    }

    const hoofdstukken = new Map();
    function laadHoofdstuk(boek, nummer) {
        // In de hoofdapp volgt DataLoader de gekozen teksteditie en heeft hij een eigen cache.
        if (global.DataLoader && typeof global.DataLoader.loadChapter === 'function') {
            return Promise.resolve(global.DataLoader.loadChapter(boek, nummer)).catch(() => null);
        }
        const sleutel = `${boek}/${nummer}`;
        if (!hoofdstukken.has(sleutel)) {
            hoofdstukken.set(sleutel, fetch(`data/${boek}/${nummer}.json`)
                .then(r => (r.ok ? r.json() : null))
                .catch(() => null));
        }
        return hoofdstukken.get(sleutel);
    }

    const VerwijzingPopup = {
        el: null,
        huidige: null,
        volgnummer: 0,
        toonTimer: null,
        verbergTimer: null,

        heeftMuis() {
            return !!(global.matchMedia && global.matchMedia('(hover: hover) and (pointer: fine)').matches);
        },

        init() {
            if (this._klaar || typeof document === 'undefined') return;
            this._klaar = true;

            document.addEventListener('mouseover', (e) => {
                const doel = e.target;
                const link = doel && doel.closest ? doel.closest('.ref-link') : null;
                if (link) {
                    this.planToon(link);
                } else if (this.el && this.el.contains(doel)) {
                    clearTimeout(this.verbergTimer);
                }
            });
            document.addEventListener('mouseout', (e) => {
                const doel = e.target;
                const link = doel && doel.closest ? doel.closest('.ref-link') : null;
                const uitPopup = this.el && this.el.contains(doel);
                if (!link && !uitPopup) return;
                const naar = e.relatedTarget;
                if (naar && ((link && link.contains(naar)) || (this.el && this.el.contains(naar)))) return;
                clearTimeout(this.toonTimer);
                clearTimeout(this.verbergTimer);
                this.verbergTimer = setTimeout(() => this.verberg(), VERBERG_NA_MS);
            });
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') this.verberg();
            });
            // Wie klikt, gaat naar de plaats; de popup hoort daar niet mee te reizen.
            document.addEventListener('click', (e) => {
                if (e.target && e.target.closest && e.target.closest('.ref-link')) this.verberg();
            }, true);
            // Capture, zodat ook scrollen in het notenpaneel de popup sluit.
            global.addEventListener('scroll', () => this.verberg(), true);
        },

        planToon(link) {
            if (!this.heeftMuis()) return;
            clearTimeout(this.verbergTimer);
            if (this.huidige === link && this.el && this.el.style.display !== 'none') return;
            clearTimeout(this.toonTimer);
            this.toonTimer = setTimeout(() => this.toon(link), TOON_NA_MS);
        },

        async toon(link) {
            const boek = link.dataset.refBook;
            const hoofdstuk = parseInt(link.dataset.refCh, 10);
            const van = link.dataset.refVs ? parseInt(link.dataset.refVs, 10) : null;
            const tot = link.dataset.refTot ? parseInt(link.dataset.refTot, 10) : null;
            if (!boek || !hoofdstuk) return;

            const nummer = ++this.volgnummer;
            this.huidige = link;
            const el = this.element();
            el.innerHTML = '<div class="vp-laden">Tekst laden…</div>';
            el.style.display = 'block';
            this.plaats(link);

            const [namen, data] = await Promise.all([laadBoeknamen(), laadHoofdstuk(boek, hoofdstuk)]);
            if (nummer !== this.volgnummer || this.huidige !== link) return;

            const gevonden = van ? verzen(data, van, tot) : verzen(data, 1, 3);
            const kop = escapeHtml(label(namen[boek] || boek, hoofdstuk, van, tot));
            const tekst = gevonden.verzen.length
                ? gevonden.verzen.map(v => `<span class="vp-vers"><sup>${v.nummer}</sup>${escapeHtml(v.tekst)}</span>`).join(' ')
                    + (gevonden.ingekort ? ' …' : '')
                : '<em>Deze tekst is niet gevonden.</em>';
            el.innerHTML = `<div class="vp-kop">${kop}</div><div class="vp-tekst">${tekst}</div>`
                + '<div class="vp-hint">Klik om erheen te gaan</div>';
            this.plaats(link);
        },

        element() {
            if (!this.el) {
                this.el = document.createElement('div');
                this.el.className = 'verwijzing-popup';
                this.el.setAttribute('role', 'tooltip');
                this.el.style.display = 'none';
                document.body.appendChild(this.el);
            }
            return this.el;
        },

        plaats(link) {
            const el = this.el;
            const rand = 8;
            const r = link.getBoundingClientRect();
            const breedte = el.offsetWidth;
            const hoogte = el.offsetHeight;
            let links = Math.max(rand, Math.min(r.left, global.innerWidth - breedte - rand));
            let boven = r.bottom + 6;
            if (boven + hoogte > global.innerHeight - rand && r.top - hoogte - 6 > rand) {
                boven = r.top - hoogte - 6;
            }
            el.style.left = `${links}px`;
            el.style.top = `${boven}px`;
        },

        verberg() {
            clearTimeout(this.toonTimer);
            clearTimeout(this.verbergTimer);
            this.huidige = null;
            this.volgnummer++;
            if (this.el) this.el.style.display = 'none';
        },
    };

    VerwijzingPopup._intern = { kaleTekst, verzen, label, MAX_VERZEN };
    global.VerwijzingPopup = VerwijzingPopup;
    if (typeof module !== 'undefined' && module.exports) module.exports = VerwijzingPopup;

    if (typeof document !== 'undefined') {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => VerwijzingPopup.init());
        } else {
            VerwijzingPopup.init();
        }
    }
})(typeof window !== 'undefined' ? window : globalThis);
