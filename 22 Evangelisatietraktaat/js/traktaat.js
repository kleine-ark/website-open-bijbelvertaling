/* Bouwt het boekje op: inhoudsopgave en een spread per passage.
 * De tekst zelf wordt in een volgende stap ingeladen.
 */
import {
    passageId, passageTitel, afbeeldingUrl, leesUrl, boekNamen, escapeHtml,
    spreadHtml, verzenHtml,
} from './render.js';
import { laadPassage } from './laden.js';

const config = window.TRAKTAAT_CONFIG;
const selectie = window.TRAKTAAT_SELECTIE || [];

async function haalJson(url, terugval) {
    try {
        const antwoord = await fetch(url);
        if (!antwoord.ok) return terugval;
        return await antwoord.json();
    } catch (e) {
        return terugval;
    }
}

function bouwInhoudsopgave(namen) {
    document.getElementById('inhoudsopgave').innerHTML = selectie.map(p =>
        `<a href="#${passageId(p)}">${escapeHtml(passageTitel(p, namen[p.boek] || p.boek))}</a>`
    ).join('');
}

function bouwSpreads(namen, uitleg) {
    document.getElementById('boekje').innerHTML = selectie.map(p => spreadHtml({
        id: passageId(p),
        titel: passageTitel(p, namen[p.boek] || p.boek),
        leesHref: leesUrl(config, p),
        afbeelding: afbeeldingUrl(config, p),
        uitleg: uitleg[passageId(p)],
    })).join('\n');
}

/* Laadt één passage en zet de verzen in zijn spread. */
async function vulTekst(passage, plek) {
    plek.innerHTML = '<p class="laden">Laden…</p>';
    // fetch als pijlfunctie doorgeven: los meegegeven raakt hij zijn binding
    // aan window kwijt en gooit de browser "Illegal invocation".
    const uit = await laadPassage(url => fetch(url), config, passage);
    if (uit.ok) {
        plek.innerHTML = verzenHtml(uit.verzen);
        return;
    }
    plek.innerHTML = `<p class="fout">${escapeHtml(uit.fout)}<button type="button">Opnieuw proberen</button></p>`;
    plek.querySelector('button').addEventListener('click', () => vulTekst(passage, plek));
}

/* Laat elke spread zijn tekst ophalen zodra hij in beeld komt. */
function bewaakSpreads() {
    const perId = {};
    selectie.forEach(p => { perId[passageId(p)] = p; });

    const kijker = new IntersectionObserver((waarnemingen) => {
        waarnemingen.forEach(w => {
            if (!w.isIntersecting) return;
            kijker.unobserve(w.target);
            vulTekst(perId[w.target.dataset.tekst], w.target);
        });
    }, { rootMargin: '600px 0px' });

    document.querySelectorAll('[data-tekst]').forEach(el => kijker.observe(el));
}

/* Toont een kader in plaats van een gebroken afbeelding. */
function bewaakAfbeeldingen() {
    document.querySelectorAll('.illustratie img').forEach(img => {
        img.addEventListener('error', () => {
            img.closest('.illustratie').classList.add('ontbreekt');
        });
    });
}

async function start() {
    const [boeken, uitleg] = await Promise.all([
        haalJson(`${config.DATA_BASE}books.json`, { books: [] }),
        haalJson('data/uitleg.json', {}),
    ]);
    const namen = boekNamen(boeken);
    bouwInhoudsopgave(namen);
    bouwSpreads(namen, uitleg);
    bewaakAfbeeldingen();
    bewaakSpreads();
}

start();
