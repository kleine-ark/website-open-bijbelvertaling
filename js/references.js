/* Open Vertaling — Bijbelverwijzingen klikbaar maken */

const References = {
    // Mapping van afkortingen naar boek-ID (webapp) en volledige naam
    BOOK_MAP: {
        // Genesis
        'gen': 'genesis', 'genes': 'genesis', 'genesis': 'genesis',
        // Exodus
        'ex': 'exodus', 'exod': 'exodus', 'exodus': 'exodus',
        // Leviticus
        'lev': 'leviticus', 'levit': 'leviticus', 'leviticus': 'leviticus',
        // Numeri
        'num': 'numeri', 'numer': 'numeri', 'numeri': 'numeri',
        // Deuteronomium
        'deut': 'deuteronomium', 'deuteronomium': 'deuteronomium',
        // Jozua
        'joz': 'jozua', 'jos': 'jozua', 'jozua': 'jozua',
        // Richteren
        'richt': 'richteren', 'richteren': 'richteren',
        // Ruth
        'ruth': 'ruth',
        // 1/2 Samuel
        '1 sam': '1samuel', '1 samuel': '1samuel', '2 sam': '2samuel', '2 samuel': '2samuel',
        // 1/2 Koningen
        '1 kon': '1koningen', '1 koningen': '1koningen', '1 reg': '1koningen',
        '2 kon': '2koningen', '2 koningen': '2koningen', '2 reg': '2koningen',
        // 1/2 Kronieken
        '1 kron': '1kronieken', '1 kronieken': '1kronieken',
        '2 kron': '2kronieken', '2 kronieken': '2kronieken',
        // Ezra, Nehemia, Esther
        'ezra': 'esther', 'neh': 'nehemia', 'esth': 'esther', 'esther': 'esther',
        // Job
        'job': 'job', 'iob': 'job',
        // Psalmen
        'ps': 'psalmen', 'psal': 'psalmen', 'psalm': 'psalmen', 'psalmen': 'psalmen',
        // Spreuken
        'spr': 'spreuken', 'prov': 'spreuken', 'spreuken': 'spreuken',
        // Prediker
        'pred': 'prediker', 'prediker': 'prediker',
        // Hooglied
        'hoogl': 'hooglied', 'hooglied': 'hooglied',
        // Jesaja
        'jes': 'jesaja', 'jesa': 'jesaja', 'jesaja': 'jesaja',
        // Jeremia
        'jer': 'jeremia', 'jeremia': 'jeremia',
        // Klaagliederen
        'klaagl': 'klaagliederen',
        // Ezechiël
        'ezech': 'ezechiel', 'ez': 'ezechiel',
        // Daniël
        'dan': 'daniel',
        // Hosea
        'hos': 'hosea', 'hosea': 'hosea',
        // Joël
        'joel': 'joel', 'joël': 'joel',
        // Amos
        'amos': 'amos',
        // Obadja
        'obadja': 'obadja', 'obad': 'obadja',
        // Jona
        'jona': 'jona',
        // Micha
        'micha': 'micha', 'mich': 'micha',
        // Nahum
        'nah': 'nahum', 'nahum': 'nahum',
        // Habakuk
        'hab': 'habakuk',
        // Zefanja
        'zef': 'zefanja',
        // Haggaï
        'hagg': 'haggai', 'hag': 'haggai',
        // Zacharia
        'zach': 'zacharia', 'zacharia': 'zacharia',
        // Maleachi
        'mal': 'maleachi', 'maleachi': 'maleachi',
        // Mattheüs
        'matt': 'mattheus', 'matth': 'mattheus', 'mat': 'mattheus',
        // Markus
        'mark': 'markus', 'marc': 'markus', 'markus': 'markus',
        // Lukas
        'luk': 'lukas', 'luc': 'lukas', 'lukas': 'lukas',
        // Johannes
        'joh': 'johannes', 'johannes': 'johannes',
        // Handelingen
        'hand': 'handelingen', 'handelingen': 'handelingen', 'act': 'handelingen',
        // Romeinen
        'rom': 'romeinen', 'romeinen': 'romeinen',
        // 1/2 Korinthe
        '1 kor': '1korinthe', '1 cor': '1korinthe',
        '2 kor': '2korinthe', '2 cor': '2korinthe',
        // Galaten
        'gal': 'galaten',
        // Efeziërs
        'ef': 'efeziers', 'efez': 'efeziers',
        // Filippenzen
        'fil': 'filippenzen', 'filipp': 'filippenzen',
        // Kolossenzen
        'kol': 'kolossenzen', 'col': 'kolossenzen', 'coloss': 'kolossenzen',
        // 1/2 Thessalonicenzen
        '1 thess': '1thessalonicenzen', '2 thess': '2thessalonicenzen',
        // 1/2 Timotheüs
        '1 tim': '1timotheus', '2 tim': '2timotheus',
        // Titus
        'tit': 'titus',
        // Filemon
        'filem': 'filemon',
        // Hebreeën
        'hebr': 'hebreeen', 'heb': 'hebreeen',
        // Jakobus
        'jak': 'jakobus', 'jac': 'jakobus', 'jakobus': 'jakobus',
        // 1/2 Petrus
        '1 petr': '1petrus', '1 pet': '1petrus',
        '2 petr': '2petrus', '2 pet': '2petrus',
        // 1/2/3 Johannes
        '1 joh': '1johannes', '2 joh': '2johannes', '3 joh': '3johannes',
        // Judas
        'jud': 'judas', 'judas': 'judas',
        // Openbaring
        'openb': 'openbaring', 'openbaring': 'openbaring', 'apoc': 'openbaring',
        // Wijsheid (apocrief)
        'wijsh': 'wijsheid', 'wijsheid': 'wijsheid',
        // Oude SV-afkortingen
        'genes': 'genesis', 'deuter': 'deuteronomium',
        'iohan': 'johannes', 'iohan.': 'johannes',
        'hfdst': null, // "hfdst." is geen boek
    },

    // Regex voor Bijbelverwijzingen
    // Match patronen als: "Gen. 2:1", "Ps. 90:2-3", "1 Kor. 16:2", "vers 21"
    // Punt na boekafkorting is OPTIONEEL: "Job 38:4" matcht ook (fix: bug zonder punt)
    REF_REGEX: /\b((?:[123]\s)?(?:Genesis|Exodus|Leviticus|Numeri|Deuteronomium|Deuter|Genes|Jozua|Richteren|Samuel|Koningen|Kronieken|Esther|Psalmen|Psalm|Psal|Spreuken|Prediker|Hooglied|Hoogl|Jesaja|Jesa|Jeremia|Klaagl|Ezechiel|Ezech|Daniel|Hosea|Obadja|Obad|Micha|Mich|Nahum|Habakuk|Zefanja|Haggai|Hagg|Zacharia|Zach|Maleachi|Mattheus|Matth|Markus|Marcus|Lukas|Lucas|Iohan|Iohannes|Johannes|Handelingen|Romeinen|Korinthe|Korinthiers|Korinthen|Galaten|Efeziers|Filippenzen|Filipp|Kolossenzen|Coloss|Thessalonicenzen|Thess|Timotheus|Filemon|Filem|Hebreeen|Jakobus|Petrus|Judas|Openbaring|Apoc|Wijsheid|Wijsh|Gen|Ex|Exod|Lev|Levit|Num|Numer|Deut|Joz|Jos|Richt|Ruth|Sam|Kon|Reg|Kron|Ezra|Neh|Esth|Job|Iob|Ps|Spr|Prov|Pred|Jes|Jer|Ez|Dan|Hos|Joel|Joël|Amos|Jona|Nah|Hab|Zef|Hag|Mal|Matt|Mat|Mark|Marc|Luk|Luc|Joh|Hand|Act|Rom|Kor|Cor|Gal|Ef|Efez|Fil|Kol|Col|Tim|Tit|Hebr|Heb|Jak|Jac|Petr|Pet|Jud|Openb))\.?\s+(\d+)(?::(\d+(?:[,-]\d+)*))?/gi,

    // Regex voor "vers X" verwijzingen (binnen hetzelfde hoofdstuk)
    VERSE_REF_REGEX: /\bvers\s+(\d+(?:\s*(?:,|en)\s*\d+)*)/gi,

    /**
     * Maak verwijzingen in tekst klikbaar.
     * @param {string} text - De tekst met verwijzingen
     * @param {string} currentBookId - Huidig boek (voor "vers X" refs)
     * @param {number} currentChapter - Huidig hoofdstuk
     * @returns {string} HTML met klikbare links
     */
    linkify(text, currentBookId, currentChapter) {
        if (!text) return text;

        // Eerst: "vers X" verwijzingen
        let result = text.replace(this.VERSE_REF_REGEX, (match, verses) => {
            const firstVerse = parseInt(verses);
            const hash = `#${currentBookId}/${currentChapter}`;
            return `<a class="ref-link" href="${hash}" data-ref-book="${currentBookId}" data-ref-ch="${currentChapter}" data-ref-vs="${firstVerse}" title="${match}">${match}</a>`;
        });

        // Dan: boek-verwijzingen + verkorte verwijzingen in ÉÉN pass
        // (zodat lastBookId correct per-positie wordt bijgehouden, niet
        // pas aan het einde van alle full-refs zoals voorheen — fix bug
        // waarbij "89:12" na "Ps." onbedoeld aan laatste boek werd gekoppeld)
        let lastBookId = currentBookId || '';
        // Combinerende regex: óf volledige boek-ref, óf verkorte "ch:vs"
        // verkorte vorm vereist voorafgaand komma (lookbehind) en niet binnen HTML-tag
        const fullRefSrc = this.REF_REGEX.source;
        const combinedRegex = new RegExp(
            fullRefSrc + '|(?<=,\\s*)(\\d+):(\\d+(?:[,-]\\d+)*)(?![^<]*>)',
            'gi'
        );

        result = result.replace(combinedRegex, (match, bookAbbr, chapter, verses, shortCh, shortVs) => {
            // Volledige boek-ref?
            if (bookAbbr) {
                const key = bookAbbr.toLowerCase().replace(/\.$/, '').replace(/\s+/g, ' ');
                const bookId = this.BOOK_MAP[key];
                if (!bookId) return match;

                lastBookId = bookId;
                const ch = parseInt(chapter);
                const hash = `#${bookId}/${ch}`;
                const vs = verses ? parseInt(verses) : null;

                return `<a class="ref-link" href="${hash}" data-ref-book="${bookId}" data-ref-ch="${ch}"${vs ? ` data-ref-vs="${vs}"` : ''} title="${match}">${match}</a>`;
            }
            // Verkorte ref (ch:vs zonder boek)
            if (shortCh) {
                if (!lastBookId) return match;
                const ch = parseInt(shortCh);
                const vs = shortVs ? parseInt(shortVs) : null;
                const hash = `#${lastBookId}/${ch}`;
                return `<a class="ref-link" href="${hash}" data-ref-book="${lastBookId}" data-ref-ch="${ch}"${vs ? ` data-ref-vs="${vs}"` : ''} title="${lastBookId} ${match}">${match}</a>`;
            }
            return match;
        });

        return result;
    },

    /**
     * Voeg click handlers toe voor ref-links (event delegation).
     */
    init() {
        document.addEventListener('click', (e) => {
            const link = e.target.closest('.ref-link');
            if (!link) return;

            e.preventDefault();

            const bookId = link.dataset.refBook;
            const ch = parseInt(link.dataset.refCh);
            const vs = link.dataset.refVs ? parseInt(link.dataset.refVs) : null;

            // Navigeer naar het boek/hoofdstuk
            location.hash = `#${bookId}/${ch}`;

            // Na navigatie: scroll naar vers
            if (vs) {
                setTimeout(() => {
                    const verseRow = document.querySelector(`.verse-row[data-verse="${vs}"]`);
                    if (verseRow) {
                        verseRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        verseRow.classList.add('ref-highlight');
                        setTimeout(() => verseRow.classList.remove('ref-highlight'), 2000);
                    }
                }, 300);
            }
        });
    }
};
