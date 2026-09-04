(function () {
    'use strict';
    var body;
    var status;
    var search;
    var timer;
    var offset = 0;
    var pageSize = 50;
    var total = 0;

    function text(tag, value, className) {
        var element = document.createElement(tag);
        element.textContent = value == null ? '' : String(value);
        if (className) element.className = className;
        return element;
    }

    function showStatus(message, error) {
        status.textContent = message;
        status.classList.toggle('is-error', !!error);
    }

    async function saveRoles(user, checkboxes) {
        var roles = checkboxes.filter(function (checkbox) { return checkbox.checked; })
            .map(function (checkbox) { return checkbox.value; });
        checkboxes.forEach(function (checkbox) { checkbox.disabled = true; });
        try {
            await Collaboration.api('/users/' + encodeURIComponent(user.uid) + '/roles', {
                method: 'PATCH',
                body: JSON.stringify({ roles: roles })
            });
            showStatus('Rollen opgeslagen.', false);
            await Promise.all([loadUsers(), loadRoleEvents()]);
        } catch (error) {
            showStatus(error.message, true);
            checkboxes.forEach(function (checkbox) { checkbox.disabled = user.bootstrap; });
        }
    }

    function roleControl(user, role, label) {
        var wrap = document.createElement('label');
        wrap.className = 'role-control';
        var input = document.createElement('input');
        input.type = 'checkbox';
        input.value = role;
        input.checked = user.roles.indexOf(role) !== -1;
        input.disabled = user.bootstrap;
        wrap.append(input, document.createTextNode(' ' + label));
        return { wrap: wrap, input: input };
    }

    function renderUsers(users) {
        body.replaceChildren();
        users.forEach(function (user) {
            var row = document.createElement('tr');
            var account = document.createElement('td');
            var name = text('strong', user.displayName);
            var email = text('span', user.email, 'muted block');
            account.append(name, email);
            if (!user.registered) account.append(text('span', 'Nog niet aangemeld', 'badge pending'));

            var roleCell = document.createElement('td');
            var administrator = roleControl(user, 'administrator', 'Beheerder');
            var reviewer = roleControl(user, 'reviewer', 'Reviewer');
            var controls = [administrator.input, reviewer.input];
            controls.forEach(function (input) {
                input.addEventListener('change', function () { saveRoles(user, controls); });
            });
            roleCell.append(administrator.wrap, reviewer.wrap);
            if (user.bootstrap) roleCell.append(text('span', 'Vaste beheerder', 'muted block'));

            var lastSeen = document.createElement('td');
            lastSeen.textContent = user.registered
                ? new Date(user.lastSeenAt).toLocaleString('nl-NL')
                : '—';
            row.append(account, roleCell, lastSeen);
            body.appendChild(row);
        });
        if (!users.length) {
            var empty = document.createElement('tr');
            var cell = text('td', 'Geen accounts gevonden.', 'empty-state');
            cell.colSpan = 3;
            empty.appendChild(cell);
            body.appendChild(empty);
        }
        document.getElementById('users-prev').disabled = offset === 0;
        document.getElementById('users-next').disabled = offset + users.length >= total;
        document.getElementById('users-page').textContent = total
            ? (offset + 1) + '–' + Math.min(offset + users.length, total) + ' van ' + total
            : '0 resultaten';
    }

    async function loadUsers() {
        showStatus('Accounts laden…', false);
        try {
            var query = new URLSearchParams({
                q: search.value.trim(), offset: String(offset), limit: String(pageSize)
            });
            var payload = await Collaboration.api('/users?' + query.toString());
            total = payload.total;
            renderUsers(payload.items);
            showStatus(total + ' account(s)', false);
        } catch (error) {
            body.replaceChildren();
            showStatus(error.message, true);
        }
    }

    async function loadRoleEvents() {
        var eventBody = document.querySelector('#role-events-table tbody');
        try {
            var payload = await Collaboration.api('/role-events');
            eventBody.replaceChildren();
            payload.events.forEach(function (event) {
                var row = document.createElement('tr');
                var target = text('td', event.targetDisplayName);
                target.append(text('span', event.targetEmail, 'muted block'));
                var roles = event.roles.length ? event.roles.join(', ') : 'Geen rollen';
                var actor = text('td', event.actor.displayName || event.actor.email);
                actor.append(text('span', new Date(event.createdAt).toLocaleString('nl-NL'), 'muted block'));
                row.append(target, text('td', roles), actor);
                eventBody.appendChild(row);
            });
            if (!payload.events.length) {
                var empty = document.createElement('tr');
                var cell = text('td', 'Nog geen rolwijzigingen.', 'empty-state');
                cell.colSpan = 3;
                empty.appendChild(cell);
                eventBody.appendChild(empty);
            }
        } catch (error) {
            eventBody.replaceChildren();
            var failed = document.createElement('tr');
            var failedCell = text('td', 'Er is een fout opgetreden. Controleer het logboek.', 'empty-state');
            failedCell.colSpan = 3;
            failed.appendChild(failedCell);
            eventBody.appendChild(failed);
        }
    }

    function clearData() {
        body.replaceChildren();
        document.querySelector('#role-events-table tbody').replaceChildren();
        document.getElementById('users-page').textContent = '';
        document.getElementById('users-prev').disabled = true;
        document.getElementById('users-next').disabled = true;
    }

    function handleProfile(profile) {
        if (!profile) {
            showStatus('Log in met Google om deze pagina te gebruiken.', true);
            clearData();
            return;
        }
        if (profile.roles.indexOf('administrator') === -1) {
            showStatus('Deze pagina is alleen toegankelijk voor beheerders.', true);
            clearData();
            return;
        }
        Promise.all([loadUsers(), loadRoleEvents()]);
    }

    document.addEventListener('DOMContentLoaded', function () {
        body = document.querySelector('#users-table tbody');
        status = document.getElementById('users-status');
        search = document.getElementById('users-search');
        search.addEventListener('input', function () {
            clearTimeout(timer);
            timer = setTimeout(function () { offset = 0; loadUsers(); }, 250);
        });
        document.getElementById('users-prev').addEventListener('click', function () {
            offset = Math.max(0, offset - pageSize);
            loadUsers();
        });
        document.getElementById('users-next').addEventListener('click', function () {
            offset += pageSize;
            loadUsers();
        });
        Collaboration.onChange(handleProfile);
    });
})();
