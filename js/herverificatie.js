/* Opnieuw verifiëren na een tekstwijziging.
 *
 * Een goedkeuring hoort bij één versie van de tekst. Wijzigt een principe de
 * tekst, dan vervalt ze en vraagt het hoofdstuk om een nieuwe verificatie. Deze
 * pagina zet die hoofdstukken bij elkaar, zodat een reviewer ze onder de eigen
 * naam opnieuw kan bevestigen. Hoofdstukken die nooit zijn nagekeken horen hier
 * niet: die vragen om een eerste controle in de lezer. */
(function (global) {
    'use strict';

    function vervallenOnderdelen(item) {
        return Object.keys(item.components).filter(key => item.components[key].needsReverification);
    }

    function openCorrectie(item) {
        return vervallenOnderdelen(item).some(key => item.components[key].status === 'correction-needed');
    }

    function kandidaten(items) {
        return items.filter(item => item.type === 'text-chapter' && vervallenOnderdelen(item).length && !openCorrectie(item));
    }

    function geblokkeerd(items) {
        return items.filter(item => item.type === 'text-chapter' && openCorrectie(item));
    }

    function opdracht(item, sourceHash) {
        return {
            subjectType: item.type, subjectId: item.id, revision: item.revision, sourceHash,
            components: Object.fromEntries(vervallenOnderdelen(item).map(key => [key, item.components[key].revision])),
            decision: 'approved', note: '',
        };
    }

    async function bronHash(bytes) {
        const digest = await global.crypto.subtle.digest('SHA-256', bytes);
        return Array.from(new Uint8Array(digest), n => n.toString(16).padStart(2, '0')).join('');
    }

    async function verifieer(item, deps) {
        try {
            // Dezelfde toets als in de lezer: bevestigd wordt wat nu gepubliceerd is.
            const sourceHash = await bronHash(await deps.bron(item.source));
            if (sourceHash !== item.metadata.sourceHash) {
                return { id: item.id, ok: false, melding: 'De gepubliceerde tekst is gewijzigd. Herlaad deze pagina.' };
            }
            await deps.api('/reviews', { method: 'POST', body: JSON.stringify(opdracht(item, sourceHash)) });
            return { id: item.id, ok: true };
        } catch (error) {
            return { id: item.id, ok: false, melding: error && error.status === 409
                ? 'De gegevens zijn gewijzigd. Herlaad deze pagina en probeer het opnieuw.'
                : 'Vastleggen is niet gelukt. Probeer het later opnieuw.' };
        }
    }

    async function alles(items, deps, voortgang) {
        const uitkomsten = [];
        for (const item of items) {
            const uitkomst = await verifieer(item, deps);
            uitkomsten.push(uitkomst);
            if (voortgang) voortgang(uitkomst);
        }
        return uitkomsten;
    }

    async function laad(api) {
        const items = [];
        // De API filtert op de status van de Bijbeltekst; een open correctie heeft een eigen status.
        for (const status of ['pending', 'correction-needed']) {
            for (let offset = 0, total = 1; offset < total; offset += 100) {
                const pagina = await api('/subjects?' + new URLSearchParams({
                    type: 'text-chapter', status, offset: String(offset), limit: '100',
                }));
                total = pagina.total;
                items.push(...pagina.items);
            }
        }
        return { kandidaten: kandidaten(items), geblokkeerd: geblokkeerd(items) };
    }

    function pagina(deps) {
        const { document, Collaboration, ReviewComponents } = deps;
        const main = document.querySelector('main');
        const status = document.getElementById('herverificatie-status');
        const allesKnop = document.getElementById('herverificatie-alles');
        const lijst = document.getElementById('herverificatie-lijst');
        const toegang = { bron: deps.bron, api: (pad, opties) => Collaboration.api(pad, opties) };
        let open = [];
        let gewapend = false;
        let generatie = 0;

        function maak(tag, tekst, className) {
            const node = document.createElement(tag);
            if (tekst) node.textContent = tekst;
            if (className) node.className = className;
            return node;
        }

        function aantal(n) {
            return n + (n === 1 ? ' hoofdstuk' : ' hoofdstukken');
        }

        function werkKnopBij() {
            allesKnop.hidden = !open.length;
            allesKnop.disabled = false;
            allesKnop.textContent = gewapend ? 'Bevestig: ' + aantal(open.length) + ' opnieuw verifiëren'
                : 'Alles opnieuw verifiëren (' + open.length + ')';
        }

        function rij(item) {
            const regel = maak('li');
            const link = maak('a', item.label);
            link.href = item.href;
            const knop = maak('button', 'Opnieuw verifiëren', 'secondary-button');
            knop.type = 'button';
            const uitkomst = maak('span', '', 'review-note');
            regel.append(link, maak('span', ' — ' + ReviewComponents.join(vervallenOnderdelen(item)) + ' '), knop, uitkomst);
            knop.addEventListener('click', async () => {
                knop.disabled = true;
                toonUitkomst(item, await verifieer(item, toegang));
                werkKnopBij();
            });
            item.rij = { knop, uitkomst };
            return regel;
        }

        function toonUitkomst(item, uitkomst) {
            item.rij.uitkomst.textContent = uitkomst.ok ? ' ✓ geverifieerd' : ' ' + uitkomst.melding;
            item.rij.knop.hidden = uitkomst.ok;
            item.rij.knop.disabled = false;
            if (uitkomst.ok) open = open.filter(ander => ander !== item);
        }

        allesKnop.addEventListener('click', async () => {
            if (!gewapend) {
                gewapend = true;
                werkKnopBij();
                return;
            }
            gewapend = false;
            allesKnop.disabled = true;
            const werk = open.slice();
            const uitkomsten = await alles(werk, toegang, uitkomst => {
                toonUitkomst(werk.find(item => item.id === uitkomst.id), uitkomst);
                status.textContent = 'Bezig: ' + (werk.length - open.length) + ' van ' + werk.length + '…';
            });
            const gelukt = uitkomsten.filter(uitkomst => uitkomst.ok).length;
            status.textContent = aantal(gelukt) + ' opnieuw geverifieerd'
                + (gelukt < werk.length ? '; ' + (werk.length - gelukt) + ' niet gelukt, zie de lijst.' : '.');
            werkKnopBij();
        });

        async function toon(profile, ready) {
            const huidige = ++generatie;
            open = [];
            gewapend = false;
            lijst.replaceChildren();
            allesKnop.hidden = true;
            main.hidden = false;
            if (!ready) { status.textContent = 'Laden…'; return; }
            if (!profile || !Collaboration.hasRole('reviewer')) {
                status.textContent = 'Log in met een account dat mag verifiëren om deze pagina te gebruiken.';
                return;
            }
            status.textContent = 'Laden…';
            let stand;
            try {
                stand = await laad(toegang.api);
            } catch (error) {
                if (huidige === generatie) status.textContent = 'De lijst kon niet worden geladen. Herlaad om het opnieuw te proberen.';
                return;
            }
            if (huidige !== generatie) return;
            open = stand.kandidaten;
            status.textContent = open.length
                ? aantal(open.length) + (open.length === 1 ? ' wacht' : ' wachten') + ' op een nieuwe verificatie.'
                : 'Er wachten geen hoofdstukken op een nieuwe verificatie.';
            const rijen = maak('ul', '', 'herverificatie-rijen');
            rijen.append(...open.map(rij));
            lijst.append(rijen);
            if (stand.geblokkeerd.length) {
                const blok = maak('ul', '', 'herverificatie-rijen');
                blok.append(...stand.geblokkeerd.map(item => {
                    const regel = maak('li');
                    const link = maak('a', item.label);
                    link.href = item.href;
                    regel.append(link, maak('span', ' — heeft een openstaande correctie; die gaat voor.'));
                    return regel;
                }));
                lijst.append(maak('h2', 'Eerst een correctie afhandelen'), blok);
            }
            werkKnopBij();
        }

        return { toon };
    }

    global.Herverificatie = { kandidaten, geblokkeerd, opdracht, verifieer, alles, laad, pagina };

    // De login-module laadt uitgesteld; pas bij DOMContentLoaded bestaat Collaboration.
    if (global.document) global.document.addEventListener('DOMContentLoaded', () => {
        if (!global.document.getElementById('herverificatie-lijst')) return;
        const scherm = pagina({
            document: global.document, Collaboration: global.Collaboration, ReviewComponents: global.ReviewComponents,
            bron: async pad => {
                const antwoord = await fetch(pad, { cache: 'no-store' });
                if (!antwoord.ok) throw new Error('Bron niet beschikbaar');
                return new Uint8Array(await antwoord.arrayBuffer());
            },
        });
        global.Collaboration.onChange((profile, ready) => scherm.toon(profile, ready));
    });
})(typeof window === 'undefined' ? globalThis : window);
