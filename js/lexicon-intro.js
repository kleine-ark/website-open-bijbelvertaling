/* Landingspagina's per taal voor het woordenboek: een korte uitleg van de taal
 * en het alfabet, getoond zolang er nog geen woord gekozen is. */
(function () {
    'use strict';

    var HEB = [
        ['א', 'Alef', 'ʼ (stil)', '1', 'stille medeklinker / stemhebbende inzet'],
        ['ב', 'Bet', 'b / v', '2', 'met puntje (dagesj) b, anders v'],
        ['ג', 'Gimel', 'g', '3', ''],
        ['ד', 'Dalet', 'd', '4', ''],
        ['ה', 'He', 'h', '5', 'aan het woordeind vaak stil'],
        ['ו', 'Vav', 'w / v', '6', 'ook als klinker o/oe'],
        ['ז', 'Zayin', 'z', '7', ''],
        ['ח', 'Chet', 'ch', '8', 'harde keel-ch'],
        ['ט', 'Tet', 't', '9', 'nadrukkelijke t'],
        ['י', 'Jod', 'j', '10', 'ook als klinker i'],
        ['כ', 'Kaf', 'k / ch', '20', 'sloteind: ך'],
        ['ל', 'Lamed', 'l', '30', ''],
        ['מ', 'Mem', 'm', '40', 'sloteind: ם'],
        ['נ', 'Noen', 'n', '50', 'sloteind: ן'],
        ['ס', 'Samech', 's', '60', ''],
        ['ע', 'Ajin', 'ʻ (stil)', '70', 'stemhebbende keelklank'],
        ['פ', 'Pe', 'p / f', '80', 'sloteind: ף'],
        ['צ', 'Tsade', 'ts', '90', 'sloteind: ץ'],
        ['ק', 'Qof', 'k', '100', 'nadrukkelijke k'],
        ['ר', 'Resj', 'r', '200', ''],
        ['שׁ', 'Sjin / Sin', 'sj / s', '300', 'punt rechts = sj, links = s'],
        ['ת', 'Tav', 't', '400', '']
    ];
    var GRC = [
        ['Α α', 'Alfa', 'a', '1', ''], ['Β β', 'Bèta', 'b', '2', ''], ['Γ γ', 'Gamma', 'g', '3', ''],
        ['Δ δ', 'Delta', 'd', '4', ''], ['Ε ε', 'Epsilon', 'e (kort)', '5', ''], ['Ζ ζ', 'Zèta', 'z', '7', ''],
        ['Η η', 'Èta', 'e (lang)', '8', ''], ['Θ θ', 'Thèta', 'th', '9', ''], ['Ι ι', 'Jota', 'i', '10', ''],
        ['Κ κ', 'Kappa', 'k', '20', ''], ['Λ λ', 'Lambda', 'l', '30', ''], ['Μ μ', 'Mu', 'm', '40', ''],
        ['Ν ν', 'Nu', 'n', '50', ''], ['Ξ ξ', 'Xi', 'x', '60', ''], ['Ο ο', 'Omikron', 'o (kort)', '70', ''],
        ['Π π', 'Pi', 'p', '80', ''], ['Ρ ρ', 'Rho', 'r', '100', ''], ['Σ σ/ς', 'Sigma', 's', '200', 'ς aan woordeind'],
        ['Τ τ', 'Tau', 't', '300', ''], ['Υ υ', 'Upsilon', 'u / y', '400', ''], ['Φ φ', 'Phi', 'f', '500', ''],
        ['Χ χ', 'Chi', 'ch', '600', ''], ['Ψ ψ', 'Psi', 'ps', '700', ''], ['Ω ω', 'Omega', 'o (lang)', '800', '']
    ];

    function alfabet(rows, lang) {
        var h = '<table class="lex-alfabet"><thead><tr><th>Letter</th><th>Naam</th><th>Klank</th><th>Getal</th><th></th></tr></thead><tbody>';
        rows.forEach(function (r) {
            h += '<tr><td class="la-let" lang="' + lang + '">' + r[0] + '</td><td>' + r[1] + '</td><td>' + r[2] + '</td><td class="la-num">' + r[3] + '</td><td class="la-note">' + r[4] + '</td></tr>';
        });
        return h + '</tbody></table>';
    }

    window.LEX_LANDING = {
        hebreeuws:
            '<div class="lex-landing"><h2>Hebreeuws &amp; Aramees — de taal van het Oude Testament</h2>' +
            '<p>Het grootste deel van het Oude Testament is geschreven in het <strong>Bijbels Hebreeuws</strong>; enkele gedeelten (o.a. in Daniël en Ezra) in het nauw verwante <strong>Aramees</strong>. Hebreeuws wordt <strong>van rechts naar links</strong> gelezen en geschreven.</p>' +
            '<ul><li>Het alfabet telt <strong>22 medeklinkers</strong>; oorspronkelijk werden er geen klinkers geschreven.</li>' +
            '<li>De klinkers (de puntjes en streepjes onder en boven de letters) zijn later toegevoegd door de <em>masoreten</em> om de uitspraak vast te leggen.</li>' +
            '<li>Vijf letters hebben een aparte <strong>slotvorm</strong> aan het einde van een woord (ך ם ן ף ץ).</li>' +
            '<li>Elke letter heeft ook een <strong>getalswaarde</strong> — zo kon men met letters tellen.</li></ul>' +
            '<h3>Het Hebreeuwse alfabet</h3>' + alfabet(HEB, 'he') +
            '<p class="lex-landing-hint">Kies links een woord om de betekenis, de grondvorm en de tekstverwijzingen te zien.</p></div>',
        grieks:
            '<div class="lex-landing"><h2>Grieks — de taal van het Nieuwe Testament</h2>' +
            '<p>Het Nieuwe Testament is geschreven in het <strong>Koinè-Grieks</strong>, het algemene Grieks van de eerste eeuw. Grieks wordt van links naar rechts gelezen en heeft, anders dan het Hebreeuws, wél aparte klinkers.</p>' +
            '<ul><li>Het alfabet telt <strong>24 letters</strong>, elk met een eigen naam en getalswaarde.</li>' +
            '<li>De sigma heeft een aparte vorm (ς) aan het einde van een woord.</li>' +
            '<li>Accenten en spiritus (de tekentjes boven klinkers) geven klemtoon en een h-klank aan.</li></ul>' +
            '<h3>Het Griekse alfabet</h3>' + alfabet(GRC, 'grc') +
            '<p class="lex-landing-hint">Kies links een woord om de betekenis en de tekstverwijzingen te zien.</p></div>',
        geez:
            '<div class="lex-landing"><h2>Ge’ez — klassiek Ethiopisch</h2>' +
            '<p>Ge’ez (klassiek Ethiopisch) is de taal waarin o.a. de boeken Henoch, Jubileeën en de Meqabyan-boeken volledig zijn overgeleverd, binnen de Ethiopisch-Orthodoxe traditie.</p>' +
            '<ul><li>Ge’ez gebruikt een eigen schrift (de <em>fidäl</em>): een <strong>abugida</strong> waarin elk teken een medeklinker + klinker weergeeft (ruim 200 tekens), in plaats van een los alfabet.</li>' +
            '<li>Het wordt van links naar rechts geschreven.</li></ul>' +
            '<p class="lex-landing-hint">Kies links een woord om de betekenis en de tekstverwijzingen te zien.</p></div>',
        'geez-dillmann':
            '<div class="lex-landing"><h2>Dillmann — het Ge’ez-woordenboek (1865)</h2>' +
            '<p>Dit is het klassieke <strong>Lexicon linguae aethiopicae</strong> van August Dillmann (1865): het standaardwoordenboek van het Ge’ez, met ruim 13.000 lemmas. De definities staan in het <strong>Latijn</strong> (de wetenschapstaal van die tijd); een Nederlandse vertaling volgt.</p>' +
            '<p class="lex-landing-hint">Zoek links op een Ge’ez-woord of blader door de lemmas.</p></div>',
        latijn:
            '<div class="lex-landing"><h2>Latijn</h2>' +
            '<p>Latijnse grondtekst-glossen, o.a. bij 4 Ezra, dat niet in het Grieks maar in de Latijnse (Vulgaat-)traditie is bewaard.</p>' +
            '<p class="lex-landing-hint">Kies links een woord om de betekenis te zien.</p></div>'
    };
})();
