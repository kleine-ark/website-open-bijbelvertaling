/* Het ophalen van een hoofdstuk uit de OSV-data.
 * fetchFn wordt meegegeven zodat deze laag testbaar is zonder netwerk.
 */
import { dataUrl } from './render.js';

export function verzenInBereik(verzen, bereik) {
    if (!bereik) return verzen;
    const [eerste, laatste] = bereik;
    return verzen.filter(v => v.number >= eerste && v.number <= laatste);
}

export async function laadPassage(fetchFn, config, passage) {
    const url = dataUrl(config, passage);
    try {
        const antwoord = await fetchFn(url);
        if (!antwoord.ok) {
            return { ok: false, fout: `Ophalen mislukt (${antwoord.status})` };
        }
        const hoofdstuk = await antwoord.json();
        return { ok: true, verzen: verzenInBereik(hoofdstuk.verses, passage.verzen) };
    } catch (e) {
        return { ok: false, fout: `Ophalen mislukt: ${e.message}` };
    }
}
