(function () {
    'use strict';
    var main;
    var body;
    var status;
    var previous;
    var next;
    var page;
    var offset = 0;
    var pageSize = 100;
    var requestGeneration = 0;

    function element(tag, value, className) {
        var node = document.createElement(tag);
        node.textContent = value;
        if (className) node.className = className;
        return node;
    }

    async function loadEvents() {
        if (!Collaboration.hasRole('administrator')) return;
        var request = ++requestGeneration;
        var requestedUser = Collaboration.currentUser;
        body.replaceChildren();
        page.textContent = '';
        status.textContent = 'Beoordelingsgeschiedenis laden…';
        status.classList.remove('is-error');
        previous.disabled = true;
        next.disabled = true;
        try {
            var payload = await Collaboration.api('/reviews?offset=' + offset + '&limit=' + pageSize);
            if (request !== requestGeneration || Collaboration.currentUser !== requestedUser) return;
            payload.items.forEach(function (review) {
                var row = document.createElement('tr');
                var subject = element('td', review.label);
                subject.append(element('span', review.subjectType + ' · ' + review.subjectId, 'muted block'));
                const componentLabels = review.components.map(key => ReviewComponents.join([key]) +
                    (review.verseScopes[key] ? ' — ' + (review.verseScopes[key].length === 1 ? 'vers ' : 'verzen ') +
                        review.verseScopes[key].join(', ') : ''));
                subject.append(element('span', review.components.length ? componentLabels.join('; ')
                    : 'Geen onderdelen meer van toepassing', 'muted block'));
                var decision = element('td', review.components.length
                    ? (review.decision === 'approved' ? 'Goedgekeurd' : 'Ingetrokken') : 'Hersteld');
                var actor = element('td', Collaboration.reviewActorLabel(review));
                actor.append(element('span', Collaboration.reviewDateLabel(review), 'muted block'));
                row.append(subject, decision, actor, element('td', review.note || '—'));
                body.appendChild(row);
            });
            if (!payload.items.length) {
                var empty = document.createElement('tr');
                var cell = element('td', 'Nog geen beslissingen.', 'empty-state');
                cell.colSpan = 4;
                empty.appendChild(cell);
                body.appendChild(empty);
            }
            previous.disabled = offset === 0;
            next.disabled = offset + payload.items.length >= payload.total;
            page.textContent = payload.total
                ? (offset + 1) + '–' + Math.min(offset + payload.items.length, payload.total) + ' van ' + payload.total
                : '0 gebeurtenissen';
            status.textContent = '';
        } catch (error) {
            console.error('[collaboration]', error);
            if (request !== requestGeneration || Collaboration.currentUser !== requestedUser) return;
            body.replaceChildren();
            status.textContent = 'Er is een fout opgetreden. Controleer het logboek.';
            status.classList.add('is-error');
        }
    }

    function handleProfile(profile, ready) {
        main.hidden = true;
        requestGeneration++;
        offset = 0;
        body.replaceChildren();
        status.textContent = '';
        status.classList.remove('is-error');
        page.textContent = '';
        previous.disabled = true;
        next.disabled = true;
        if (!ready) return;
        if (!profile || profile.roles.indexOf('administrator') === -1) {
            location.replace('index.html');
            return;
        }
        main.hidden = false;
        loadEvents();
    }

    document.addEventListener('DOMContentLoaded', function () {
        main = document.querySelector('.collaboration-main');
        body = document.querySelector('#review-events-table tbody');
        status = document.getElementById('review-events-status');
        previous = document.getElementById('review-events-prev');
        next = document.getElementById('review-events-next');
        page = document.getElementById('review-events-page');
        previous.addEventListener('click', function () {
            offset -= pageSize;
            loadEvents();
        });
        next.addEventListener('click', function () {
            offset += pageSize;
            loadEvents();
        });
        Collaboration.onChange(handleProfile);
    });
})();
