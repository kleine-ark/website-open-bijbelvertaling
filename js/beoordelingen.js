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
    var eventRequest = 0;
    var historyDialog;
    var historyButton;
    var eventStatus;
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
                    element('span', Collaboration.reviewActorLabel(subject.latestReview), 'block'),
                    element('span', Collaboration.reviewDateLabel(subject.latestReview), 'muted block')
                );
            }

            var actionCell = document.createElement('td');
            var open = element('a', 'Open de inhoud');
            open.href = subject.href;
            actionCell.append(open);
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
        var requestedUser = Collaboration.currentUser;
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
            if (Collaboration.currentUser !== requestedUser) return;
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
            console.error('[collaboration]', error);
            showStatus('Er is een fout opgetreden. Controleer het logboek.', true);
        }
    }

    async function loadEvents() {
        if (!historyDialog.open || !Collaboration.hasRole('administrator')) return;
        var request = ++eventRequest;
        var requestedUser = Collaboration.currentUser;
        var eventBody = document.querySelector('#review-events-table tbody');
        eventStatus.textContent = 'Beoordelingsgeschiedenis laden…';
        eventStatus.classList.remove('is-error');
        document.getElementById('review-events-prev').disabled = true;
        document.getElementById('review-events-next').disabled = true;
        try {
            var payload = await Collaboration.api(
                '/reviews?offset=' + eventOffset + '&limit=' + eventPageSize
            );
            if (request !== eventRequest || Collaboration.currentUser !== requestedUser || !historyDialog.open) return;
            eventBody.replaceChildren();
            eventTotal = payload.total;
            payload.items.forEach(function (review) {
                var row = document.createElement('tr');
                var subject = element('td', review.label);
                subject.append(element('span', review.subjectType + ' · ' + review.subjectId, 'muted block'));
                var decision = element('td', review.decision === 'approved' ? 'Goedgekeurd' : 'Ingetrokken');
                var actor = element('td', Collaboration.reviewActorLabel(review));
                actor.append(element('span', Collaboration.reviewDateLabel(review), 'muted block'));
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
            eventStatus.textContent = '';
            document.querySelector('.review-history-body').scrollTop = 0;
        } catch (error) {
            console.error('[collaboration]', error);
            if (request !== eventRequest || Collaboration.currentUser !== requestedUser || !historyDialog.open) return;
            eventBody.replaceChildren();
            eventStatus.textContent = 'Er is een fout opgetreden. Controleer het logboek.';
            eventStatus.classList.add('is-error');
            document.getElementById('review-events-page').textContent = '';
        }
    }

    function resetAndLoad() {
        offset = 0;
        loadSubjects();
    }

    function clearData() {
        body.replaceChildren();
        document.getElementById('reviews-page').textContent = '';
        document.getElementById('reviews-prev').disabled = true;
        document.getElementById('reviews-next').disabled = true;
        clearEvents();
    }

    function clearEvents() {
        eventRequest++;
        eventOffset = 0;
        eventTotal = 0;
        document.querySelector('#review-events-table tbody').replaceChildren();
        eventStatus.textContent = '';
        eventStatus.classList.remove('is-error');
        document.getElementById('review-events-page').textContent = '';
        document.getElementById('review-events-prev').disabled = true;
        document.getElementById('review-events-next').disabled = true;
    }

    function handleProfile(profile, ready) {
        main.hidden = true;
        historyButton.hidden = true;
        if (historyDialog.open) historyDialog.close();
        clearData();
        if (!ready) return;
        if (!profile || profile.roles.indexOf('reviewer') === -1) {
            location.replace('index.html');
            return;
        }
        main.hidden = false;
        historyButton.hidden = !Collaboration.hasRole('administrator');
        loadSubjects();
    }

    document.addEventListener('DOMContentLoaded', function () {
        main = document.querySelector('.collaboration-main');
        body = document.querySelector('#reviews-table tbody');
        status = document.getElementById('reviews-status');
        search = document.getElementById('reviews-search');
        typeFilter = document.getElementById('reviews-type');
        statusFilter = document.getElementById('reviews-state');
        historyDialog = document.getElementById('review-history');
        historyButton = document.getElementById('review-history-open');
        eventStatus = document.getElementById('review-events-status');
        historyButton.addEventListener('click', function () {
            historyDialog.showModal();
            loadEvents();
        });
        document.getElementById('review-history-close').addEventListener('click', function () {
            historyDialog.close();
        });
        historyDialog.addEventListener('close', clearEvents);
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
