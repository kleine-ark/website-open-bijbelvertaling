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

    global.OVTekstweergave = {
        state: state,
        citatenAan: citatenAan,
        versnummersAan: versnummersAan,
        transformeer: transformeer,
        pasDocumentToe: pasDocumentToe
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', pasDocumentToe);
    } else {
        pasDocumentToe();
    }
})(window);
