/* Klein i18n-fundament. De bediening blijft in fase 1 Nederlands. */
(function (global) {
    'use strict';
    const fallback = {
        'edition.label': 'Bijbeltekst',
        'edition.unavailable': '{boek} is niet beschikbaar in {editie}.',
        'edition.openDutch': 'Open dit boek in Open Vertaling',
        'edition.invalid': 'De gekozen Bijbeltekst bestaat niet; Open Vertaling wordt gebruikt.',
    };
    const I18n = {
        locale: 'nl',
        messages: { ...fallback },
        ready: fetch('i18n/nl.json').then(r => r.ok ? r.json() : {}).then(data => {
            Object.assign(I18n.messages, data || {});
            return I18n;
        }).catch(() => I18n),
        t(key, variables) {
            let value = this.messages[key] || fallback[key] || '';
            for (const [name, replacement] of Object.entries(variables || {})) {
                value = value.replaceAll(`{${name}}`, String(replacement));
            }
            return value;
        },
    };
    global.I18n = I18n;
})(window);
