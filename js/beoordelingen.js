(function () {
    'use strict';
    var body;
    var main;
    var status;
    var search;
    var typeFilter;
    var statusFilter;
    var offset = 0;
    var pageSize = 50;
    var total = 0;
    var eventOffset = 0;
    var eventTotal = 0;
    var eventPageSize = 100;
    var timer;

    function element(tag, value, className) {
        var node = document.createElement(tag);
        if (value != null) node.textContent = String(value);
        if (className) node.className = className;
        return node;
    }

    function showStatus(message, error) {
        status.textContent = message;
        status.classList.toggle('is-error', !!error);
    }

    function actorLabel(review) {
        if (!review) return '—';
        if (review.actor.kind === 'historical-import') return 'Onbekend (geïmporteerd)';
        return review.actor.displayName || review.actor.email || 'Onbekend';
    }

    async function decide(subject, decision, note, button) {
        button.disabled = true;
        try {
            await Collaboration.api('/reviews', {
                method: 'POST',
                body: JSON.stringify({
                    subjectType: subject.type,
                    subjectId: subject.id,
                    revision: subject.revision,
                    decision: decision,
                    note: note.value.trim()
                })
            });
            showStatus(decision === 'approved' ? 'Goedkeuring opgeslagen.' : 'Goedkeuring ingetrokken.', false);
            eventOffset = 0;
            await Promise.all([loadSubjects(), loadEvents()]);
        } catch (error) {
            showStatus(error.message, true);
            button.disabled = false;
        }
    }

    function renderSubjects(items) {
        body.replaceChildren();
        items.forEach(function (subject) {
            var row = document.createElement('tr');
            var subjectCell = document.createElement('td');
            var link = element('a', subject.label);
            link.href = subject.href;
            subjectCell.append(link, element('span', subject.id, 'muted block'));

            var typeCell = element('td', subject.typeLabel);
            var stateCell = document.createElement('td');
            stateCell.append(element('span', subject.status === 'approved' ? 'Goedgekeurd' : 'Te beoordelen', 'badge ' + subject.status));
            if (subject.latestReview) {
                stateCell.append(
                    element('span', actorLabel(subject.latestReview), 'block'),
                    element('span', new Date(subject.latestReview.createdAt).toLocaleString('nl-NL'), 'muted block')
                );
            }

            var actionCell = document.createElement('td');
            var note = document.createElement('input');
            note.type = 'text';
            note.maxLength = 2000;
            note.placeholder = 'Toelichting (optioneel)';
            note.className = 'review-note';
            var button = element('button', subject.status === 'approved' ? 'Intrekken' : 'Goedkeuren');
            button.type = 'button';
            button.className = subject.status === 'approved' ? 'secondary-button' : 'primary-button';
            button.addEventListener('click', function () {
                decide(subject, subject.status === 'approved' ? 'revoked' : 'approved', note, button);
            });
            actionCell.append(note, button);
            row.append(subjectCell, typeCell, stateCell, actionCell);
            body.appendChild(row);
        });
        if (!items.length) {
            var empty = document.createElement('tr');
            var cell = element('td', 'Geen reviewonderwerpen gevonden.', 'empty-state');
            cell.colSpan = 4;
            empty.appendChild(cell);
            body.appendChild(empty);
        }
        document.getElementById('reviews-prev').disabled = offset === 0;
        document.getElementById('reviews-next').disabled = offset + items.length >= total;
        document.getElementById('reviews-page').textContent = total
            ? (offset + 1) + '–' + Math.min(offset + items.length, total) + ' van ' + total
            : '0 resultaten';
    }

    async function loadSubjects() {
        var query = new URLSearchParams({
            q: search.value.trim(),
            type: typeFilter.value,
            status: statusFilter.value,
            offset: String(offset),
            limit: String(pageSize)
        });
        showStatus('Reviewgegevens laden…', false);
        try {
            var payload = await Collaboration.api('/subjects?' + query.toString());
            total = payload.total;
            var selectedType = typeFilter.value;
            typeFilter.replaceChildren(new Option('Alle gegevens', ''));
            payload.types.forEach(function (type) {
                typeFilter.appendChild(new Option(type.label, type.id));
            });
            typeFilter.value = selectedType;
            renderSubjects(payload.items);
            showStatus(total + ' onderwerp(en)', false);
        } catch (error) {
            body.replaceChildren();
            showStatus(error.message, true);
        }
    }

    async function loadEvents() {
        var eventBody = document.querySelector('#review-events-table tbody');
        try {
            var payload = await Collaboration.api(
                '/reviews?offset=' + eventOffset + '&limit=' + eventPageSize
            );
            eventBody.replaceChildren();
            eventTotal = payload.total;
            payload.items.forEach(function (review) {
                var row = document.createElement('tr');
                var subject = element('td', review.label);
                subject.append(element('span', review.subjectType + ' · ' + review.subjectId, 'muted block'));
                var decision = element('td', review.decision === 'approved' ? 'Goedgekeurd' : 'Ingetrokken');
                var actor = element('td', actorLabel(review));
                actor.append(element('span', new Date(review.createdAt).toLocaleString('nl-NL'), 'muted block'));
                row.append(subject, decision, actor, element('td', review.note || '—'));
                eventBody.appendChild(row);
            });
            if (!payload.items.length) {
                var empty = document.createElement('tr');
                var cell = element('td', 'Nog geen beslissingen.', 'empty-state');
                cell.colSpan = 4;
                empty.appendChild(cell);
                eventBody.appendChild(empty);
            }
            document.getElementById('review-events-prev').disabled = eventOffset === 0;
            document.getElementById('review-events-next').disabled =
                eventOffset + payload.items.length >= eventTotal;
            document.getElementById('review-events-page').textContent = eventTotal
                ? (eventOffset + 1) + '–' + Math.min(eventOffset + payload.items.length, eventTotal) + ' van ' + eventTotal
                : '0 gebeurtenissen';
        } catch (error) {
            eventBody.replaceChildren();
            var failed = document.createElement('tr');
            var failedCell = element('td', 'Er is een fout opgetreden. Controleer het logboek.', 'empty-state');
            failedCell.colSpan = 4;
            failed.appendChild(failedCell);
            eventBody.appendChild(failed);
            document.getElementById('review-events-prev').disabled = true;
            document.getElementById('review-events-next').disabled = true;
        }
    }

    function resetAndLoad() {
        offset = 0;
        loadSubjects();
    }

    function clearData() {
        body.replaceChildren();
        document.querySelector('#review-events-table tbody').replaceChildren();
        document.getElementById('reviews-page').textContent = '';
        document.getElementById('reviews-prev').disabled = true;
        document.getElementById('reviews-next').disabled = true;
        document.getElementById('review-events-page').textContent = '';
        document.getElementById('review-events-prev').disabled = true;
        document.getElementById('review-events-next').disabled = true;
    }

    function handleProfile(profile, ready) {
        if (!ready) return;
        if (!profile || profile.roles.indexOf('reviewer') === -1) {
            main.hidden = true;
            clearData();
            location.replace('index.html');
            return;
        }
        main.hidden = false;
        Promise.all([loadSubjects(), loadEvents()]);
    }

    document.addEventListener('DOMContentLoaded', function () {
        main = document.querySelector('.collaboration-main');
        body = document.querySelector('#reviews-table tbody');
        status = document.getElementById('reviews-status');
        search = document.getElementById('reviews-search');
        typeFilter = document.getElementById('reviews-type');
        statusFilter = document.getElementById('reviews-state');
        search.addEventListener('input', function () {
            clearTimeout(timer);
            timer = setTimeout(resetAndLoad, 250);
        });
        typeFilter.addEventListener('change', resetAndLoad);
        statusFilter.addEventListener('change', resetAndLoad);
        document.getElementById('reviews-prev').addEventListener('click', function () {
            offset = Math.max(0, offset - pageSize);
            loadSubjects();
        });
        document.getElementById('reviews-next').addEventListener('click', function () {
            offset += pageSize;
            loadSubjects();
        });
        document.getElementById('review-events-prev').addEventListener('click', function () {
            eventOffset = Math.max(0, eventOffset - eventPageSize);
            loadEvents();
        });
        document.getElementById('review-events-next').addEventListener('click', function () {
            eventOffset += eventPageSize;
            loadEvents();
        });
        Collaboration.onChange(handleProfile);
    });
})();
