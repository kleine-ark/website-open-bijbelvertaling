/* Bouwt het boekje op: inhoudsopgave en een spread per passage.
 * De tekst zelf wordt in een volgende stap ingeladen.
 */
import {
    passageId, passageTitel, afbeeldingUrl, leesUrl, boekNamen, escapeHtml, spreadHtml,
} from './render.js';

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

async function start() {
    const [boeken, uitleg] = await Promise.all([
        haalJson(`${config.DATA_BASE}books.json`, { books: [] }),
        haalJson('data/uitleg.json', {}),
    ]);
    const namen = boekNamen(boeken);
    bouwInhoudsopgave(namen);
    bouwSpreads(namen, uitleg);
}

start();
