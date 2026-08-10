/* Centrale tekstweergave voor Bijbelcitaten binnen de website.
 *
 * Alle pagina's die OV-tekst buiten de hoofdlezer tonen, lezen via deze module
 * dezelfde opgeslagen weergave-instellingen. embed.js blijft de publieke
 * citaat-API en gebruikt deze module wanneer hij op openvertaling.nl draait. */
(function (global) {
    'use strict';

    function bool(value, fallback) {
        if (value === undefined || value === null || value === '') return fallback;
        if (typeof value === 'boolean') return value;
        return !/^(false|0|nee|no|uit)$/i.test(String(value));
    }

    function state() {
        if (global.Opties && global.Opties.state) return global.Opties.state;
        try {
            return JSON.parse(localStorage.getItem('sv2026_vertaalopties') || '{}');
        } catch (e) {
            return {};
        }
    }

    function citatenAan(overrides) {
        overrides = overrides || {};
        if (overrides.citaat !== undefined) return bool(overrides.citaat, true);
        var current = state();
        if (current.citaten !== undefined) return current.citaten !== 'uit';
        return localStorage.getItem('citaatopmaak') !== 'false';
    }

    function versnummersAan(overrides) {
        overrides = overrides || {};
        if (overrides.numbers !== undefined) return bool(overrides.numbers, true);
        return state().versnummers !== 'uit';
    }

    function transformeer(html, context, overrides) {
        overrides = overrides || {};
        context = context || {};
        if (overrides.godsnaam !== undefined || !global.Opties || !global.Opties.transformOV) {
            return html;
        }

        var output = global.Opties.transformOV(html, context.testament);
        if (global.Opties.markeerGeo) {
            output = global.Opties.markeerGeo(
                output, context.boek, context.hoofdstuk, context.vers
            );
        }
        if (global.Opties.rekenMaten) {
            output = global.Opties.rekenMaten(
                output, context.boek, context.hoofdstuk, context.vers
            );
        }
        if (global.Opties.rekenTijden) {
            output = global.Opties.rekenTijden(
                output, context.boek, context.hoofdstuk, context.vers, context.testament
            );
        }
        return output;
    }

    function pasDocumentToe() {
        if (!document.body) return;
        var current = state();
        document.body.classList.toggle('citaten-uit', !citatenAan());
        document.body.classList.toggle('hide-verse-numbers', current.versnummers === 'uit');
    }

    function lezerLink(ref) {
        var match = String(ref || '').trim().match(/^(\S+)\s+(\d+):(\d+)/);
        if (!match) return 'index.html#' + encodeURIComponent(String(ref || ''));
        return 'index.html#' + match[1].toLowerCase() + '/' + match[2] + '/' + match[3];
    }

    /* Eén DOM-template voor OV-tekst op alle naslagpagina's. De citaatinhoud
       blijft vrij van geneste links (Strong-knoppen blijven dus klikbaar); de
       tekstlink ernaast opent altijd de volledige lezer buiten een wiki-frame. */
    function renderNaslagtekst(container, ref, options) {
        options = options || {};
        if (!container) return Promise.reject(new Error('Naslagtekstcontainer ontbreekt'));

        container.textContent = '';
        var component = document.createElement('div');
        component.className = 'ov-naslagtekst' + (options.className ? ' ' + options.className : '');

        var link = document.createElement('a');
        link.className = 'ov-naslagtekst-link' + (options.linkClass ? ' ' + options.linkClass : '');
        link.href = lezerLink(ref);
        link.target = options.target === '_blank' ? '_blank' : '_top';
        if (link.target === '_blank') link.rel = 'noopener';
        link.textContent = options.linkLabel || String(ref || 'Open in de Bijbellezer');
        if (options.toonLink !== false) component.appendChild(link);

        var citation = document.createElement('div');
        citation.className = 'ov-naslagtekst-citaat osv-cite';
        citation.innerHTML = '<span class="osv-laden">…</span>';
        component.appendChild(citation);
        container.appendChild(component);

        if (!global.OSV || typeof global.OSV.cite !== 'function') {
            citation.innerHTML = '<span class="osv-fout">Deze tekst kon niet geladen worden.</span>';
            return Promise.reject(new Error('OV-citaatcomponent ontbreekt'));
        }

        var citeOptions = {};
        for (var key in options) citeOptions[key] = options[key];
        delete citeOptions.className;
        delete citeOptions.linkClass;
        delete citeOptions.linkLabel;
        delete citeOptions.target;
        delete citeOptions.toonLink;
        citeOptions.link = false;

        return global.OSV.cite(ref, citeOptions).then(function (resultaat) {
            citation.innerHTML = resultaat.html;
            if (!options.linkLabel) link.textContent = resultaat.label;
            return { component: component, citation: citation, link: link, resultaat: resultaat };
        }).catch(function (error) {
            citation.innerHTML = '<span class="osv-fout">Deze tekst kon niet geladen worden.</span>';
            throw error;
        });
    }

    global.OVTekstweergave = {
        state: state,
        citatenAan: citatenAan,
        versnummersAan: versnummersAan,
        transformeer: transformeer,
        pasDocumentToe: pasDocumentToe,
        lezerLink: lezerLink,
        renderNaslagtekst: renderNaslagtekst
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', pasDocumentToe);
    } else {
        pasDocumentToe();
    }
})(window);
