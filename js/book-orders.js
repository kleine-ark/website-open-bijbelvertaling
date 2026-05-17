/* Open Vertaling — Boek-orderings
 *
 * Centrale definitie van alle ondersteunde boek-orderings.
 * Elke ordering is een object met groep-labels als keys en book-id arrays als values.
 * Gebruikt door Sidebar.renderTree() en Navigation.renderBookNav().
 */

const BookOrders = {

    // === Canoniek (Statenvertaling / Westerse Christelijke canon) ===
    // Pentateuch → historisch → poëtisch → profeten → apocriefen → NT
    canoniek: {
        label: 'Canoniek (SV)',
        groups: {
            'Pentateuch': ['genesis', 'exodus', 'leviticus', 'numeri', 'deuteronomium'],
            'Historische boeken': ['jozua', 'richteren', 'ruth', '1samuel', '2samuel', '1koningen', '2koningen', '1kronieken', '2kronieken', 'ezra', 'nehemia', 'esther'],
            'Poëtische boeken': ['job', 'psalmen', 'spreuken', 'prediker', 'hooglied'],
            'Grote profeten': ['jesaja', 'jeremia', 'klaagliederen', 'ezechiel', 'daniel'],
            'Kleine profeten': ['hosea', 'joel', 'amos', 'obadja', 'jona', 'micha', 'nahum', 'habakuk', 'zefanja', 'haggai', 'zacharia', 'maleachi'],
            'Apocriefen': ['3ezra', '4ezra', 'tobit', 'judith', 'boekderwijsheid', 'jezussirach', 'baruch', 'estherapocrief', 'gebedvanazaria', 'gezangindevuuroven', 'susanna', 'belenddedraak', 'gebedvanmanasse', '1makkabeeen', '2makkabeeen', '3makkabeeen'],
            'Evangeliën': ['mattheus', 'markus', 'lukas', 'johannes'],
            'Handelingen': ['handelingen'],
            'Brieven van Paulus': ['romeinen', '1korinthiers', '2korinthiers', 'galaten', 'efeziers', 'filippenzen', 'kolossenzen', '1tessalonicensen', '2tessalonicensen', '1timotheus', '2timotheus', 'titus', 'filemon'],
            'Algemene brieven': ['hebreeen', 'jakobus', '1petrus', '2petrus', '1johannes', '2johannes', '3johannes', 'judas'],
            'Openbaring': ['openbaring'],
        }
    },

    // === Joodse Tenach (TNK) ===
    // Torah → Nevi'im (vroege+late+twaalf) → Ketuvim (incl. 5 megillot)
    // Eindigt met 2 Kronieken — apocriefen + NT volgen daarna in westerse volgorde
    tenach: {
        label: 'Joodse Tenach',
        groups: {
            'Torah (Wet)': ['genesis', 'exodus', 'leviticus', 'numeri', 'deuteronomium'],
            'Vroege Profeten': ['jozua', 'richteren', '1samuel', '2samuel', '1koningen', '2koningen'],
            'Late Profeten': ['jesaja', 'jeremia', 'ezechiel'],
            'De Twaalf (kleine profeten)': ['hosea', 'joel', 'amos', 'obadja', 'jona', 'micha', 'nahum', 'habakuk', 'zefanja', 'haggai', 'zacharia', 'maleachi'],
            'Geschriften — poëtisch': ['psalmen', 'spreuken', 'job'],
            'Geschriften — Megillot (5 rollen)': ['hooglied', 'ruth', 'klaagliederen', 'prediker', 'esther'],
            'Geschriften — overig': ['daniel', 'ezra', 'nehemia', '1kronieken', '2kronieken'],
            'Apocriefen': ['3ezra', '4ezra', 'tobit', 'judith', 'boekderwijsheid', 'jezussirach', 'baruch', 'estherapocrief', 'gebedvanazaria', 'gezangindevuuroven', 'susanna', 'belenddedraak', 'gebedvanmanasse', '1makkabeeen', '2makkabeeen', '3makkabeeen'],
            'Nieuwe Testament': ['mattheus', 'markus', 'lukas', 'johannes', 'handelingen', 'romeinen', '1korinthiers', '2korinthiers', 'galaten', 'efeziers', 'filippenzen', 'kolossenzen', '1tessalonicensen', '2tessalonicensen', '1timotheus', '2timotheus', 'titus', 'filemon', 'hebreeen', 'jakobus', '1petrus', '2petrus', '1johannes', '2johannes', '3johannes', 'judas', 'openbaring'],
        }
    },

    // === Chronologisch (gebeurtenissen-tijdlijn) ===
    // Op basis van wanneer de gebeurtenissen plaatsvonden (niet schrijftijd).
    // Globale ordening; sommige boeken gelijktijdig — vrije keuze in plaatsing.
    chronologisch: {
        label: 'Chronologisch',
        groups: {
            'Oer-geschiedenis (Gen 1-11)': ['genesis'],
            'Patriarchen + Job': ['job'],
            'Exodus & woestijnreis': ['exodus', 'leviticus', 'numeri', 'deuteronomium'],
            'Verovering & Richters': ['jozua', 'richteren', 'ruth'],
            'Koningstijd vroeg (Saul, David)': ['1samuel', '2samuel', 'psalmen'],
            'Koningstijd (Salomo, scheuring, profeten)': ['1koningen', 'spreuken', 'prediker', 'hooglied', 'jona', 'amos', 'hosea', 'jesaja', 'micha'],
            'Vóór de ballingschap': ['2koningen', '1kronieken', '2kronieken', 'nahum', 'zefanja', 'habakuk', 'jeremia', 'klaagliederen'],
            'Ballingschap': ['ezechiel', 'daniel', 'obadja', 'joel'],
            'Na de ballingschap': ['ezra', 'haggai', 'zacharia', 'esther', 'nehemia', 'maleachi'],
            'Intertestamentaire periode (apocriefen)': ['3ezra', '4ezra', 'tobit', 'judith', 'boekderwijsheid', 'jezussirach', 'baruch', 'estherapocrief', 'gebedvanazaria', 'gezangindevuuroven', 'susanna', 'belenddedraak', 'gebedvanmanasse', '1makkabeeen', '2makkabeeen', '3makkabeeen'],
            'Evangeliën (leven Jezus)': ['mattheus', 'markus', 'lukas', 'johannes'],
            'Vroege kerk + Paulus-brieven': ['handelingen', 'galaten', '1tessalonicensen', '2tessalonicensen', '1korinthiers', '2korinthiers', 'romeinen', 'jakobus', 'efeziers', 'kolossenzen', 'filemon', 'filippenzen', '1timotheus', 'titus', '2timotheus', '1petrus', '2petrus', 'hebreeen', 'judas'],
            'Johannes-geschriften': ['1johannes', '2johannes', '3johannes', 'openbaring'],
        }
    },

    // === Op auteur / traditie ===
    auteur: {
        label: 'Op auteur',
        groups: {
            'Mozes (Pentateuch)': ['genesis', 'exodus', 'leviticus', 'numeri', 'deuteronomium'],
            'Anoniem-historisch (DtrH)': ['jozua', 'richteren', 'ruth', '1samuel', '2samuel', '1koningen', '2koningen'],
            'Kroniekschrijver': ['1kronieken', '2kronieken', 'ezra', 'nehemia', 'esther'],
            'David & andere psalmisten': ['psalmen'],
            'Salomo (wijsheid)': ['spreuken', 'prediker', 'hooglied'],
            'Job (anoniem)': ['job'],
            'Klaagliederen (Jeremia)': ['klaagliederen'],
            'Profeten (elk eigen auteur)': ['jesaja', 'jeremia', 'ezechiel', 'daniel', 'hosea', 'joel', 'amos', 'obadja', 'jona', 'micha', 'nahum', 'habakuk', 'zefanja', 'haggai', 'zacharia', 'maleachi'],
            'Apocriefen (diverse auteurs)': ['3ezra', '4ezra', 'tobit', 'judith', 'boekderwijsheid', 'jezussirach', 'baruch', 'estherapocrief', 'gebedvanazaria', 'gezangindevuuroven', 'susanna', 'belenddedraak', 'gebedvanmanasse', '1makkabeeen', '2makkabeeen', '3makkabeeen'],
            'Mattheüs': ['mattheus'],
            'Markus': ['markus'],
            'Lukas (Lk + Hd)': ['lukas', 'handelingen'],
            'Johannes (Ev + brieven + Openb)': ['johannes', '1johannes', '2johannes', '3johannes', 'openbaring'],
            'Paulus': ['romeinen', '1korinthiers', '2korinthiers', 'galaten', 'efeziers', 'filippenzen', 'kolossenzen', '1tessalonicensen', '2tessalonicensen', '1timotheus', '2timotheus', 'titus', 'filemon'],
            'Hebreeën (anoniem)': ['hebreeen'],
            'Jakobus': ['jakobus'],
            'Petrus': ['1petrus', '2petrus'],
            'Judas': ['judas'],
        }
    },

    // === Op lengte (aantal hoofdstukken — groot naar klein) ===
    // Volgorde wordt dynamisch berekend in getGroups() o.b.v. manifest.
    lengte: {
        label: 'Op lengte',
        groups: null,  // dynamisch
        dynamic: 'lengte',
    },
};

/**
 * Geef de groepen voor een gegeven ordering.
 * Voor dynamische orderings (lengte) wordt het manifest gebruikt.
 *
 * @param {string} mode - ordering-key uit BookOrders
 * @param {object} manifest - { books: [...] } met chaptersIncluded per boek
 * @returns {Object<string, string[]>}  groepen → array van book-ids
 */
function getBookOrderGroups(mode, manifest) {
    const ordering = BookOrders[mode] || BookOrders.canoniek;

    if (ordering.dynamic === 'lengte') {
        // Sorteer alle boeken op aantal hoofdstukken (groot → klein), per categorie
        const buckets = {
            'Zeer lang (≥40 hfdst)': [],
            'Lang (20–39 hfdst)': [],
            'Middel (10–19 hfdst)': [],
            'Kort (4–9 hfdst)': [],
            'Zeer kort (1–3 hfdst)': [],
        };
        const sorted = [...manifest.books].sort((a, b) => (b.totalChapters || 0) - (a.totalChapters || 0));
        for (const b of sorted) {
            const n = b.totalChapters || (b.chaptersIncluded ? b.chaptersIncluded.length : 0);
            if (n >= 40) buckets['Zeer lang (≥40 hfdst)'].push(b.id);
            else if (n >= 20) buckets['Lang (20–39 hfdst)'].push(b.id);
            else if (n >= 10) buckets['Middel (10–19 hfdst)'].push(b.id);
            else if (n >= 4) buckets['Kort (4–9 hfdst)'].push(b.id);
            else buckets['Zeer kort (1–3 hfdst)'].push(b.id);
        }
        return buckets;
    }

    return ordering.groups;
}

/**
 * Geef een flat-list van alle book-ids in volgorde voor de gekozen ordening.
 * Voegt boeken toe die nog niet in een groep zitten als 'Overig'.
 */
function getFlatBookOrder(mode, manifest) {
    const groups = getBookOrderGroups(mode, manifest);
    const allIds = new Set(manifest.books.map(b => b.id));
    const ordered = [];
    const seen = new Set();
    for (const ids of Object.values(groups)) {
        for (const id of ids) {
            if (allIds.has(id) && !seen.has(id)) {
                ordered.push(id);
                seen.add(id);
            }
        }
    }
    // Voeg ontbrekende toe in manifest-volgorde
    for (const b of manifest.books) {
        if (!seen.has(b.id)) {
            ordered.push(b.id);
            seen.add(b.id);
        }
    }
    return ordered;
}

// Expose globally
if (typeof window !== 'undefined') {
    window.BookOrders = BookOrders;
    window.getBookOrderGroups = getBookOrderGroups;
    window.getFlatBookOrder = getFlatBookOrder;
}
