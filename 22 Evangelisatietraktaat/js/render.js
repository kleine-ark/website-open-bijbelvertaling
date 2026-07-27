/* Pure functies voor het traktaat: gegevens in, string uit.
 * Geen DOM, geen fetch — daardoor testbaar met `node --test`.
 */

export function passageId(passage) {
    return `${passage.boek}_${passage.hoofdstuk}`;
}

export function passageTitel(passage, boekNaam) {
    if (passage.titel) return passage.titel;
    const kop = `${boekNaam} ${passage.hoofdstuk}`;
    if (!passage.verzen) return kop;
    return `${kop}:${passage.verzen[0]}-${passage.verzen[1]}`;
}

export function dataUrl(config, passage) {
    return `${config.DATA_BASE}${passage.boek}/${passage.hoofdstuk}.json`;
}

export function afbeeldingUrl(config, passage) {
    return `${config.IMG_BASE}${passageId(passage)}.jpg`;
}

export function leesUrl(config, passage) {
    return `${config.LEES_BASE}#${passage.boek}/${passage.hoofdstuk}`;
}

export function boekNamen(boeksJson) {
    const namen = {};
    (boeksJson.books || []).forEach(b => { namen[b.id] = b.nameDutch; });
    return namen;
}

export function escapeHtml(tekst) {
    return String(tekst ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

export function verzenHtml(verzen) {
    return verzen.map(v =>
        `<p class="vers"><span class="versnr">${v.number}</span> ${escapeHtml(v.text2026)}</p>`
    ).join('\n');
}

export function uitlegHtml(uitleg) {
    if (!uitleg) return '<p class="uitleg leeg">Uitleg volgt</p>';
    return `<p class="uitleg">${escapeHtml(uitleg)}</p>`;
}

export function spreadHtml({ id, titel, leesHref, afbeelding, uitleg }) {
    return `<section class="spread" id="${id}">
  <div class="pagina tekst">
    <h2><a href="${leesHref}">${escapeHtml(titel)}</a></h2>
    <div class="verzen" data-tekst="${id}"><p class="laden">Laden…</p></div>
  </div>
  <div class="pagina beeld">
    <figure class="illustratie">
      <img src="${afbeelding}" alt="${escapeHtml(titel)}" loading="lazy">
      <figcaption>${escapeHtml(titel)}</figcaption>
    </figure>
    ${uitlegHtml(uitleg)}
  </div>
</section>`;
}
