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
    var historyLink;
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
            const stateLabel = { approved: 'Goedgekeurd', pending: 'Te beoordelen', 'correction-needed': 'Aanpassing nodig' };
            stateCell.append(element('span', stateLabel[subject.status], 'badge ' + subject.status));
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
            for (const task of subject.corrections) {
                const correction = element('a', 'Correctietaak: ' + ReviewComponents.correctionLabel(task), 'block');
                correction.href = 'correcties.html?id=' + task.id;
                actionCell.append(correction);
            }
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

    function resetAndLoad() {
        offset = 0;
        loadSubjects();
    }

    function clearData() {
        body.replaceChildren();
        document.getElementById('reviews-page').textContent = '';
        document.getElementById('reviews-prev').disabled = true;
        document.getElementById('reviews-next').disabled = true;
    }

    function handleProfile(profile, ready) {
        main.hidden = true;
        historyLink.hidden = true;
        clearData();
        if (!ready) return;
        if (!profile || profile.roles.indexOf('reviewer') === -1) {
            location.replace('index.html');
            return;
        }
        main.hidden = false;
        historyLink.hidden = !Collaboration.hasRole('administrator');
        loadSubjects();
    }

    document.addEventListener('DOMContentLoaded', function () {
        main = document.querySelector('.collaboration-main');
        body = document.querySelector('#reviews-table tbody');
        status = document.getElementById('reviews-status');
        search = document.getElementById('reviews-search');
        typeFilter = document.getElementById('reviews-type');
        statusFilter = document.getElementById('reviews-state');
        historyLink = document.getElementById('review-history-link');
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
        Collaboration.onChange(handleProfile);
    });
})();
