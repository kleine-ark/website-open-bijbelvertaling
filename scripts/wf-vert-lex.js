export const meta = {
  name: 'vertaal-latijn-geez',
  description: 'Vertaal Latijnse (Lewis & Short) of Ge\'ez (Dillmann) woordenboekdefinities naar het Nederlands',
  phases: [{ title: 'Vertalen' }],
}
let a = args
if (typeof a === 'string') { try { a = JSON.parse(a) } catch (e) { a = {} } }
const dir = a.dir, prefix = a.prefix, mode = a.mode
const indices = Array.isArray(a.indices) ? a.indices : []
const BASE = '/home/maarten/Documents/GitHub/website-open-bijbelvertaling/data/lexicon-nl/_work/' + dir
log(`${indices.length} chunks (${mode})`)

function prompt(nnn) {
  const src = `${BASE}/${prefix}-src-${nnn}.json`
  const out = `${BASE}/${prefix}-out-${nnn}.json`
  if (mode === 'lat') {
    return `Je bent vertaler van een Latijns woordenboek (Lewis & Short). Lees ${src} — een object { sleutel: { woord, betekenis, definitie } }; "definitie" is Engelse woordenboektekst met wat HTML.
Vertaal per sleutel de ENGELSE inhoud naar natuurlijk Nederlands. Behoud alle HTML-tags (<b>, <i> enz.). Laat Latijnse citaatwoorden, afkortingen en Bijbel-/auteursverwijzingen ongewijzigd.
Schrijf met Write ALLEEN dit JSON naar ${out}: { sleutel: { "betekenisNl":"<korte NL-betekenis>", "definitieNl":"<NL-vertaling van definitie>" }, … } — exact dezelfde sleutels.
Antwoord kort met: done ${nnn}.`
  }
  return `Je bent vertaler van het Ge'ez-woordenboek van Dillmann. Lees ${src} — een object { nummer: { woord, betekenis, definitie } }. De "definitie" is in het LATIJN (met soms Franse/Engelse glossen), met HTML: <span class="dl-sense">, <i class="dl-tr">…</i> (vertaalglossen), <gez>…</gez> (Ge'ez-tekst) en <span class="dl-ref" …>…</span> (Bijbelverwijzingen).
Vertaal de LATIJNSE (en Franse/Engelse) inhoud naar natuurlijk Nederlands. STRIKT:
1. Wijzig NOOIT tekst binnen <gez>…</gez> — kopieer die byte-identiek; zelfde aantal <gez>-tags.
2. Behoud ALLE HTML-tags en attributen exact (ook <span class="dl-ref" data-cref=… data-loc=…>).
3. Vertaal de tekst in <i class="dl-tr">…</i> en de losse Latijnse woorden naar Nederlands.
Schrijf met Write ALLEEN dit JSON naar ${out}: { nummer: { "glossNl":"<korte NL-betekenis>", "definitieNl":"<NL-vertaling, zelfde HTML-structuur>" }, … } — exact dezelfde nummers.
Antwoord kort met: done ${nnn}.`
}

const res = await pipeline(indices, (i) => {
  const nnn = String(i).padStart(3, '0')
  return agent(prompt(nnn), { label: `${prefix}-${nnn}`, phase: 'Vertalen', model: 'sonnet', agentType: 'general-purpose' }).then(r => ({ i, ok: !!r }))
})
log(`klaar: ${res.filter(Boolean).length}/${indices.length}`)
return { done: res.filter(Boolean).length, total: indices.length }
