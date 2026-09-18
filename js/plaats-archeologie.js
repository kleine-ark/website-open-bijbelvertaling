(function (root, factory) {
    var api = factory();
    if (typeof module === 'object' && module.exports) module.exports = api;
    else root.OVPlaatsArcheologie = api;
}(typeof globalThis !== 'undefined' ? globalThis : this, function () {
    'use strict';
    var labels = {
        'nog-te-onderzoeken': 'Nog te onderzoeken',
        'archeologische-bron': 'Archeologische bronnen beschikbaar',
        'alleen-identificatie': 'Plaatsidentificatie',
        'regionale-context': 'Archeologie van de omgeving',
        'geen-passende-bron-gevonden': 'Nog geen passende bron gevonden'
    };
    function esc(value) {
        return String(value == null ? '' : value).replace(/[&<>"']/g, function (c) {
            return {'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c];
        });
    }
    function list(value) { return Array.isArray(value) ? value : []; }
    function safeUrl(value) {
        try { var url = new URL(value); return url.protocol === 'https:' ? url.href : ''; }
        catch (e) { return ''; }
    }
    function progress(metadata) {
        if (!metadata || !Number.isFinite(metadata.totaal) || !Number.isFinite(metadata.onderzocht)) return '';
        return '<p class="archeologie-voortgang">Onderzoeksvoortgang: ' + metadata.onderzocht.toLocaleString('nl-NL') +
            ' van ' + metadata.totaal.toLocaleString('nl-NL') + ' plaatsdossiers voorzien van brononderzoek' +
            (Number.isFinite(metadata.metArcheologischeBron) ? '; ' + metadata.metArcheologischeBron.toLocaleString('nl-NL') + ' met archeologische bronnen' : '') +
            '. De overige dossiers staan nog open.</p>';
    }
    function render(dossier, metadata, options) {
        var start = '<section class="archeologie" aria-labelledby="archeologie-titel"><h2 id="archeologie-titel">Archeologie</h2>';
        if (options && options.unavailable) return start + '<p>De archeologiegegevens konden tijdelijk niet worden geladen. De plaatsgegevens en tekstverwijzingen blijven beschikbaar.</p></section>';
        var d = dossier || {}, status = d.onderzoeksstatus || 'nog-te-onderzoeken';
        var html = start + '<p class="archeologie-status">' + esc(labels[status] || labels['nog-te-onderzoeken']) + '</p>';
        if (!labels[status] || status === 'nog-te-onderzoeken') {
            return html + '<p>Voor deze plaats moet nog gericht archeologisch brononderzoek worden gedaan. De geografische bron hieronder onderbouwt de plaatsidentificatie, niet automatisch archeologische vondsten.</p>' + progress(metadata) + '</section>';
        }
        if (status === 'alleen-identificatie') html += '<p class="archeologie-kanttekening">Dit dossier gaat over de plaatsidentificatie, niet over een bewezen opgravingslocatie.</p>';
        if (status === 'regionale-context') html += '<p class="archeologie-kanttekening">Deze bronnen beschrijven de omgeving. Ze bevestigen niet de precieze ligging van deze Bijbelse plaats.</p>';
        if (d.siteNaam) html += '<h3>' + esc(d.siteNaam) + '</h3>';
        if (d.samenvatting) html += '<p>' + esc(d.samenvatting) + '</p>';
        if (d.koppelingAanPlaats) html += '<p><strong>Koppeling aan deze plaats.</strong> ' + esc(d.koppelingAanPlaats) + '</p>';
        if (list(d.perioden).length) html += '<p><strong>Perioden:</strong> ' + d.perioden.map(esc).join(' · ') + '</p>';
        var sources = list(d.bronnen), numbers = Object.create(null);
        sources.forEach(function (source, index) { numbers[source.id] = index + 1; });
        if (list(d.bevindingen).length) html += '<h3>Wat de bronnen beschrijven</h3><ul class="archeologie-bevindingen">' + d.bevindingen.map(function (finding) {
            return '<li>' + esc(finding.tekst) + ' ' + list(finding.bronIds).map(function (id) {
                var number = numbers[id];
                return number ? '<a class="archeologie-citaat" href="#archeologie-bron-' + number + '" aria-label="Bron ' + number + '">[' + number + ']</a>' : '';
            }).join(' ') + '</li>';
        }).join('') + '</ul>';
        if (list(d.beperkingen).length) html += '<h3>Wat onzeker blijft</h3><ul>' + d.beperkingen.map(function (text) { return '<li>' + esc(text) + '</li>'; }).join('') + '</ul>';
        if (sources.length) html += '<h3>Archeologische en historische bronnen</h3><ol class="archeologie-bronnen">' + sources.map(function (source, index) {
            var url = safeUrl(source.url);
            return '<li id="archeologie-bron-' + (index + 1) + '">' +
                (url ? '<a href="' + esc(url) + '" target="_blank" rel="noopener noreferrer">' + esc(source.titel) + ' ↗</a>' : esc(source.titel)) +
                '<span class="archeologie-bronmeta">' + esc(source.organisatie) + (source.jaar ? ' · ' + esc(source.jaar) : '') + '</span></li>';
        }).join('') + '</ol>';
        html += '<p class="archeologie-revisie">' + (d.gecontroleerdOp ? 'Brononderzoek: ' + esc(d.gecontroleerdOp) + '. ' : '') +
            (d.humanReviewed === true ? 'Menselijk gereviseerd.' : 'Menselijke revisie staat nog open.') + '</p>';
        return html + progress(metadata) + '</section>';
    }
    return { render: render };
}));
