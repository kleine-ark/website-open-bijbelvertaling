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
            '<h3>Over dit woordenboek — Brown-Driver-Briggs</h3>' +
            '<p>De Hebreeuwse en Aramese woorden komen uit het <strong>Brown-Driver-Briggs</strong> (BDB), voluit <em>A Hebrew and English Lexicon of the Old Testament</em> (1906). Het is het klassieke standaardwoordenboek van het Bijbels Hebreeuws, samengesteld door Francis Brown, Samuel Rolles Driver en Charles Augustus Briggs. BDB ordent de woorden per <strong>stam</strong> (de drie medeklinkers die de kern van een woord vormen) en geeft per woord uitvoerige betekenissen met de bijbehorende tekstplaatsen. Het is tot op vandaag een van de meest geraadpleegde Hebreeuwse lexicons.</p>' +
            '<p>De Engelse definities worden op deze site naar het Nederlands vertaald (in bewerking). BDB is <strong>publiek domein</strong>. Zie de pagina <a href="woordenboeken.html#bdb">De woordenboeken</a> voor de volledige bronvermelding.</p>' +
            '<p class="lex-landing-hint">Kies links een woord om de betekenis, de grondvorm en de tekstverwijzingen te zien.</p></div>',
        grieks:
            '<div class="lex-landing"><h2>Grieks — de taal van het Nieuwe Testament</h2>' +
            '<p>Het Nieuwe Testament is geschreven in het <strong>Koinè-Grieks</strong>, het algemene Grieks van de eerste eeuw. Grieks wordt van links naar rechts gelezen en heeft, anders dan het Hebreeuws, wél aparte klinkers.</p>' +
            '<ul><li>Het alfabet telt <strong>24 letters</strong>, elk met een eigen naam en getalswaarde.</li>' +
            '<li>De sigma heeft een aparte vorm (ς) aan het einde van een woord.</li>' +
            '<li>Accenten en spiritus (de tekentjes boven klinkers) geven klemtoon en een h-klank aan.</li></ul>' +
            '<h3>Het Griekse alfabet</h3>' + alfabet(GRC, 'grc') +
            '<h3>Over deze woordenboeken — TBESG &amp; Abbott-Smith</h3>' +
            '<p>De Griekse woorden worden hier uit <strong>twee woordenboeken</strong> naast elkaar getoond. <strong>TBESG</strong> (Translators Brief lexicon of Extended Strongs for Greek, 2018) is een modern, beknopt lexicon van Tyndale House (Cambridge) dat aan elk Strong-nummer een betekenis koppelt; het bouwt voort op het klassieke <strong>Abbott-Smith</strong> (<em>A Manual Greek Lexicon of the New Testament</em>, 1922). Zo zie je een moderne én een klassieke omschrijving van hetzelfde woord.</p>' +
            '<p>De definities worden naar het Nederlands vertaald (in bewerking). TBESG is beschikbaar onder <strong>CC BY 4.0</strong>, Abbott-Smith is <strong>publiek domein</strong>. Zie de pagina <a href="woordenboeken.html#tbesg">De woordenboeken</a> voor de volledige bronvermelding.</p>' +
            '<p class="lex-landing-hint">Kies links een woord om de betekenis en de tekstverwijzingen te zien.</p></div>',
        geez:
            '<div class="lex-landing"><h2>Ge’ez — klassiek Ethiopisch</h2>' +
            '<p>Ge’ez (klassiek Ethiopisch) is de taal waarin o.a. de boeken Henoch, Jubileeën en de Meqabyan-boeken volledig zijn overgeleverd, binnen de Ethiopisch-Orthodoxe traditie.</p>' +
            '<ul><li>Ge’ez gebruikt een eigen schrift (de <em>fidäl</em>): een <strong>abugida</strong> waarin elk teken een medeklinker + klinker weergeeft (ruim 200 tekens), in plaats van een los alfabet.</li>' +
            '<li>Het wordt van links naar rechts geschreven.</li></ul>' +
            '<h3>Twee bronnen in één tabblad</h3>' +
            '<p>Dit tabblad combineert twee dingen. Ten eerste de <strong>grondtekst-glossen</strong>: per Ge’ez-woord uit de Ethiopische boeken een korte Nederlandse betekenis en de tekstplaatsen waar het voorkomt (bron: Beta maṣāḥǝft). Ten tweede het volledige <strong>woordenboek van Dillmann</strong> (die lemmas herken je aan het nummer <em>DiL&nbsp;…</em>).</p>' +
            '<h3>Over het woordenboek — Dillmann (1865)</h3>' +
            '<p>Het klassieke <strong>Lexicon linguae aethiopicae</strong> van August Dillmann (1823–1894) is het standaardwoordenboek van het Ge’ez, met ruim 13.000 lemmas. De definities staan in het <strong>Latijn</strong> — de wetenschapstaal van die tijd; een Nederlandse vertaling volgt. De digitale editie is verzorgd door het TraCES-project en Beta maṣāḥǝft (Universiteit Hamburg) en is beschikbaar onder <strong>CC BY-NC-SA 4.0</strong>. Zie de pagina <a href="woordenboeken.html#dillmann">De woordenboeken</a> voor de volledige bronvermelding.</p>' +
            '<p class="lex-landing-hint">Kies links een woord om de betekenis en de tekstverwijzingen te zien, of zoek op een Ge’ez-woord.</p></div>',
        latijn:
            '<div class="lex-landing"><h2>Latijn — de taal van de Vulgaat</h2>' +
            '<p>Enkele boeken zijn niet in het Grieks bewaard gebleven maar in het <strong>Latijn</strong>, via de <em>Vulgaat</em> — de gezaghebbende Latijnse Bijbelvertaling die Hiëronymus rond 400 n.Chr. maakte. Het bekendste voorbeeld is <strong>4 Ezra</strong>, waarvan de oorspronkelijke Griekse tekst verloren is; de Latijnse traditie is daar de belangrijkste getuige.</p>' +
            '<h3>Over deze woordenlijst</h3>' +
            '<p>Hier staan <strong>grondtekst-glossen</strong>: per Latijns woord uit de tekst de vorm en een Nederlandse betekenis, zodat je woord voor woord kunt meelezen. Het is geen volledig woordenboek maar een hulp bij de tekst; de Nederlandse betekenissen zijn met AI-hulp samengesteld en nagekeken.</p>' +
            '<p class="lex-landing-hint">Kies links een woord om de betekenis te zien.</p></div>'
    };
})();
