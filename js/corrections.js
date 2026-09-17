/* Private correction queue. No automatic AI execution or publication. */
(function () {
    'use strict';
    const ERROR = 'Er is een fout opgetreden. Controleer het logboek.';
    const labels = {
        requested: 'Wacht op verwerking', proposed: 'Voorstel beoordelen', accepted: 'Wacht op publicatie',
        applied: 'Gepubliceerd — opnieuw verifiëren', closed: 'Afgesloten zonder wijziging'
    };
    const events = { requested: 'Aanpassing aangevraagd', proposed: 'Voorstel toegevoegd',
        accept: 'Voorstel geaccepteerd', return: 'Nieuw voorstel gevraagd', rebased: 'Aanvraag vernieuwd',
        close: 'Afgesloten zonder wijziging', applied: 'Wijziging gepubliceerd',
        'scope-migrated': 'Onderdeel van de aanvraag vastgelegd' };
    let main, content, status, generation = 0;

    function el(tag, text, className) {
        const node = document.createElement(tag);
        if (text !== undefined) node.textContent = text;
        if (className) node.className = className;
        return node;
    }
    function link(text, href) { const node = el('a', text); node.href = href; return node; }
    function button(text, action, primary = false) {
        const node = el('button', text, primary ? 'primary-button' : 'secondary-button');
        node.type = 'button';
        node.addEventListener('click', action);
        return node;
    }
    function show(message, error = false) {
        status.textContent = message;
        status.classList.toggle('is-error', error);
    }
    function failure(error, current) {
        console.error('[corrections]', error);
        if (current !== generation) return;
        show(error.status === 409 ? 'De taak of gegevens zijn gewijzigd. Ververs de pagina en beoordeel opnieuw.' : ERROR, true);
    }
    function noteForm(label, submitLabel, onSubmit) {
        const form = el('form', undefined, 'correction-form');
        const wrapper = el('label', label);
        const note = el('textarea');
        note.required = true;
        note.maxLength = 2000;
        note.name = 'reason';
        wrapper.append(note);
        const submit = el('button', submitLabel, 'primary-button');
        submit.type = 'submit';
        form.append(wrapper, submit);
        form.addEventListener('submit', async event => {
            event.preventDefault();
            if (!note.value.trim()) { note.setCustomValidity('Vul een reden in.'); note.reportValidity(); return; }
            submit.disabled = true;
            try { await onSubmit(note.value.trim()); } finally { submit.disabled = false; }
        });
        note.addEventListener('input', () => note.setCustomValidity(''));
        return form;
    }

    function targetFields(subject, form) {
        const fields = el('div', undefined, 'correction-target');
        const label = el('label', 'Onderdeel');
        const select = el('select');
        select.name = 'component'; select.id = 'correction-component'; label.htmlFor = select.id;
        for (const key of Object.keys(subject.components)) {
            const name = ReviewComponents.labels[key].replace(/^de /, '');
            select.append(new Option(name[0].toUpperCase() + name.slice(1), key));
        }
        select.append(new Option('Anders — zelf omschrijven', 'custom'));
        select.value = subject.type.startsWith('text-') ? 'text' : 'content';
        const customLabel = el('label', 'Welk onderdeel moet worden aangepast?');
        const custom = el('input');
        custom.type = 'text'; custom.name = 'customTarget'; custom.maxLength = 200;
        customLabel.append(custom);
        const explanation = el('p', 'Bij een eigen onderdeel trekken we niet automatisch de verificatie van de Bijbeltekst of andere onderdelen in.');
        const existing = el('p', undefined, 'correction-warning');
        function update() {
            const isCustom = select.value === 'custom';
            customLabel.hidden = explanation.hidden = !isCustom;
            custom.required = isCustom;
            custom.disabled = !isCustom;
            custom.setCustomValidity('');
            existing.replaceChildren();
            const task = subject.corrections.find(task => task.component === select.value);
            existing.hidden = !task;
            form.querySelector('[type="submit"]').disabled = !!task;
            if (task) existing.append('Voor dit onderdeel staat al een aanvraag open. ',
                link('Open correctietaak', 'correcties.html?id=' + task.id));
        }
        select.addEventListener('change', update);
        custom.addEventListener('input', () => custom.setCustomValidity(
            custom.value.trim() ? '' : 'Omschrijf het onderdeel.'));
        fields.append(label, select, customLabel, explanation, existing);
        form.prepend(fields);
        update();
        return () => ({ component: select.value, customTarget: select.value === 'custom' ? custom.value.trim() : '' });
    }

    async function createForm(params, current) {
        const query = new URLSearchParams({ type: params.get('type'), id: params.get('subject') });
        const { subject } = await Collaboration.api('/subject?' + query);
        if (current !== generation) return;
        const card = el('section', undefined, 'correction-card');
        card.append(el('h2', 'Aanpassing aanvragen: ' + subject.label), link('Open de inhoud', subject.href));
        if (subject.revision !== params.get('revision') || subject.metadata.sourceHash !== params.get('sourceHash')) {
            card.append(el('p', 'De gegevens zijn gewijzigd. Open de inhoud opnieuw en vraag daar de aanpassing aan.', 'correction-warning'));
        } else {
            card.append(el('p', 'Beschrijf wat er fout is. Voeg eventueel een voorgestelde tekst of bron toe.'));
            const form = noteForm('Reden voor de aanpassing', 'Aanvraag opslaan', async reason => {
                try {
                    const payload = await Collaboration.api('/corrections', { method: 'POST', body: JSON.stringify({
                        subjectType: subject.type, subjectId: subject.id, revision: subject.revision,
                        sourceHash: subject.metadata.sourceHash, reason, ...target()
                    }) });
                    if (current !== generation) return;
                    history.replaceState(null, '', 'correcties.html?id=' + payload.correction.id);
                    renderTask(payload.correction);
                    show('Aanvraag opgeslagen. Deze wacht op verwerking op verzoek.');
                } catch (error) { failure(error, current); }
            });
            const target = targetFields(subject, form);
            card.append(form);
        }
        content.append(card);
        show('');
    }

    function flatten(value, prefix = '', result = {}) {
        if (value !== null && typeof value === 'object') {
            const entries = Object.entries(value);
            if (!entries.length) result[prefix] = JSON.stringify(value);
            for (const [key, item] of entries) flatten(item, prefix ? prefix + ' / ' + key : key, result);
        } else result[prefix] = value === null ? '—' : String(value);
        return result;
    }
    function difference(before, after, markup = false) {
        const oldFields = flatten(before), newFields = flatten(after);
        const table = el('table', undefined, 'collaboration-table correction-diff');
        const head = el('tr');
        ['Veld', 'Oorspronkelijk', 'Voorstel'].forEach(name => head.append(el('th', name)));
        const thead = el('thead'); thead.append(head); table.append(thead);
        const body = el('tbody');
        for (const key of new Set([...Object.keys(oldFields), ...Object.keys(newFields)])) {
            if (oldFields[key] === newFields[key]) continue;
            if (key.includes('text2026_html') !== markup) continue;
            const row = el('tr');
            const field = key.replace('text2026_html', 'Opmaak (HTML)').replace('text2026', 'Tekst')
                .replace('verses', 'Verzen').replace('marginNotes', 'Kanttekeningen').replace('chapterIntro', 'Inleiding');
            row.append(el('td', field), el('td', oldFields[key] ?? '—', 'before'), el('td', newFields[key] ?? '—', 'after'));
            body.append(row);
        }
        table.append(body);
        return body.children.length ? table : null;
    }
    function proposalCard(proposal, latest) {
        const card = el(latest ? 'section' : 'details', undefined, 'correction-card');
        card.append(el(latest ? 'h2' : 'summary', (latest ? 'Wijzigingsvoorstel' : 'Eerder voorstel') + ' · versie ' + proposal.version),
            el('p', proposal.summary));
        card.append(difference(proposal.before, proposal.after) || el('p', 'De wijziging betreft de opmaak.'));
        const markup = difference(proposal.before, proposal.after, true);
        if (markup) {
            const details = el('details');
            details.append(el('summary', 'Opmaakverschillen bekijken'), markup);
            card.append(details);
        }
        const files = el('details', undefined, 'correction-files');
        files.append(el('summary', 'Alle bestandswijzigingen (' + proposal.diffs.length + ')'));
        for (const file of proposal.diffs) {
            const detail = el('details');
            detail.append(el('summary', file.path), el('pre', file.diff || 'Alleen de JSON-opmaak wijzigt.'));
            files.append(detail);
        }
        card.append(files);
        return card;
    }

    async function decide(task, action, note = '') {
        const current = generation;
        content.querySelectorAll('button').forEach(node => { node.disabled = true; });
        try {
            const result = await Collaboration.api('/corrections/' + task.id + '/decision', {
                method: 'POST', body: JSON.stringify({ version: task.version, action, note })
            });
            if (current !== generation) return;
            renderTask(result.correction);
            show(action === 'accept' ? 'Voorstel geaccepteerd. Publicatie gebeurt op verzoek; dit is nog geen verificatie.' : 'Besluit opgeslagen.');
        } catch (error) { failure(error, current); }
        finally { if (current === generation) content.querySelectorAll('button').forEach(node => { node.disabled = false; }); }
    }
    function decisionForm(task, action, label, submit) {
        const details = el('details', undefined, 'correction-card');
        details.append(el('summary', label), noteForm('Reden', submit, note => decide(task, action, note)));
        return details;
    }
    function renderTask(task) {
        content.replaceChildren();
        const nav = el('div', undefined, 'correction-actions');
        nav.append(link('Alle correctietaken', 'correcties.html'), link('Open de inhoud', task.href));
        const card = el('section', undefined, 'correction-card');
        card.append(el('h2', task.label), el('p', labels[task.status]),
            el('p', 'Onderdeel: ' + ReviewComponents.correctionLabel(task), 'correction-scope'), el('h3', 'Reden van de aanvraag'),
            el('p', task.reason, 'correction-note'));
        if (task.stale) card.append(el('p', 'De brondata is intussen gewijzigd. Laat de aanvraag opnieuw verwerken voor de huidige versie.', 'correction-warning'));
        const snapshot = el('details');
        snapshot.append(el('summary', 'Inhoud bij de aanvraag'), el('pre', JSON.stringify(task.before, null, 2), 'correction-snapshot'));
        card.append(snapshot);
        content.append(nav, card);
        for (const proposal of task.proposals) {
            content.append(proposalCard(proposal, task.status !== 'requested' && task.status !== 'closed'
                && proposal.id === task.proposal.id));
        }
        if (task.status === 'proposed' && !task.stale) {
            content.append(button('Voorstel accepteren voor publicatie', () => decide(task, 'accept'), true));
        }
        if (task.status === 'proposed') {
            content.append(decisionForm(task, 'return', 'Ander voorstel aanvragen', 'Terugsturen met reden'));
        }
        if (task.stale) content.append(decisionForm(task, 'rebase', 'Opnieuw aanvragen voor de huidige versie', 'Aanvraag vernieuwen'));
        if (['requested', 'proposed'].includes(task.status) || task.stale) {
            content.append(decisionForm(task, 'close', 'Afsluiten zonder wijziging', 'Taak afsluiten'));
        }
        if (task.status === 'accepted' && !task.stale) {
            content.append(el('p', 'Dit voorstel wacht op publicatie op verzoek. Na publicatie kan de nieuwe versie worden geverifieerd.', 'correction-warning'));
        }
        if (task.status === 'applied') content.append(link('Lees en verifieer de gepubliceerde inhoud', task.href));
        const history = el('details', undefined, 'correction-card');
        history.append(el('summary', 'Taakgeschiedenis'));
        const list = el('ol', undefined, 'correction-log');
        for (const event of task.events) {
            const item = el('li', events[event.kind] + ' · ' + new Date(event.createdAt).toLocaleString('nl-NL'));
            if (event.actor) item.append(el('span', ' · ' + event.actor.displayName));
            if (event.note) item.append(el('p', event.note, 'correction-note'));
            list.append(item);
        }
        history.append(list); content.append(history);
    }

    async function renderList(params, current) {
        const offset = Math.max(0, Number(params.get('offset')) || 0);
        const toolbar = el('form', undefined, 'collaboration-toolbar');
        const searchLabel = el('label', 'Zoeken');
        const search = el('input'); search.type = 'search'; search.name = 'q'; search.value = params.get('q') || '';
        searchLabel.append(search);
        const filterLabel = el('label', 'Status');
        const filter = el('select'); filter.name = 'status'; filter.id = 'correction-state';
        filterLabel.htmlFor = filter.id;
        filter.append(new Option('Alle statussen', ''));
        Object.entries(labels).forEach(([key, text]) => filter.append(new Option(text, key)));
        filter.value = params.get('status') || '';
        const filterWrap = el('div'); filterWrap.append(filterLabel, filter);
        const submit = el('button', 'Filteren', 'secondary-button'); submit.type = 'submit';
        toolbar.append(searchLabel, filterWrap, submit); content.append(toolbar);
        const query = new URLSearchParams({ status: filter.value, q: search.value, offset: String(offset), limit: '50' });
        const result = await Collaboration.api('/corrections?' + query);
        if (current !== generation) return;
        for (const task of result.items) {
            const card = el('article', undefined, 'correction-card');
            const title = el('h2'); title.append(link(task.label, 'correcties.html?id=' + task.id));
            card.append(title, el('p', 'Onderdeel: ' + ReviewComponents.correctionLabel(task), 'correction-scope'),
                el('p', labels[task.status] + (task.stale ? ' · Bron gewijzigd' : '')), el('p', task.reason));
            content.append(card);
        }
        const pagination = el('nav', undefined, 'correction-actions');
        for (const [name, next] of [['Vorige', offset - 50], ['Volgende', offset + 50]]) {
            if (next < 0 || next >= result.total) continue;
            const page = new URLSearchParams(query); page.set('offset', next); page.delete('limit');
            pagination.append(link(name, 'correcties.html?' + page));
        }
        content.append(pagination);
        show(result.total ? result.total + ' correctietaak/taken' : 'Geen correctietaken gevonden.');
    }

    async function load(profile, ready) {
        const current = ++generation;
        main.hidden = true; content.replaceChildren(); show('');
        if (!ready) return;
        if (!profile || !Collaboration.hasRole('reviewer')) { location.replace('index.html'); return; }
        main.hidden = false; show('Laden…');
        const params = new URLSearchParams(location.search);
        try {
            if (params.has('id')) {
                const result = await Collaboration.api('/corrections/' + encodeURIComponent(params.get('id')));
                if (current !== generation) return;
                renderTask(result.correction); show('');
            } else if (params.has('subject')) await createForm(params, current);
            else await renderList(params, current);
        } catch (error) { failure(error, current); }
    }
    document.addEventListener('DOMContentLoaded', () => {
        main = document.querySelector('.collaboration-main');
        content = document.getElementById('corrections-content');
        status = document.getElementById('corrections-status');
        Collaboration.onChange(load);
    });
})();
