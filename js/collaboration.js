/* Gedeelde client voor accounts, rollen en beoordelingen. */
(function () {
    'use strict';
    if (window.Collaboration) return;

    var listeners = [];
    var initialized = false;

    function emit(profile) {
        listeners.slice().forEach(function (listener) {
            try { listener(profile); } catch (error) { console.warn('[Collaboration] listener mislukt'); }
        });
        window.dispatchEvent(new CustomEvent('ov:collaboration-ready', { detail: profile }));
    }

    async function token(forceRefresh) {
        var user = window.Auth && window.Auth.currentUser;
        if (!user) throw new Error('AUTH_REQUIRED');
        return user.getIdToken(!!forceRefresh);
    }

    async function request(path, options, retry) {
        options = options || {};
        var headers = new Headers(options.headers || {});
        headers.set('Authorization', 'Bearer ' + await token(false));
        if (options.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
        var response = await fetch('/api/collaboration' + path, Object.assign({}, options, { headers: headers }));
        if (response.status === 401 && retry !== false) {
            headers.set('Authorization', 'Bearer ' + await token(true));
            response = await fetch('/api/collaboration' + path, Object.assign({}, options, { headers: headers }));
        }
        var payload = await response.json().catch(function () { return {}; });
        if (!response.ok) {
            var error = new Error(payload.error || 'Er is een fout opgetreden. Controleer het logboek.');
            error.status = response.status;
            throw error;
        }
        return payload;
    }

    function setNavigation(profile) {
        var links = document.getElementById('topnav-links');
        if (!links) return;
        ['review', 'users'].forEach(function (name) {
            var old = links.querySelector('[data-collaboration-link="' + name + '"]');
            if (old) old.remove();
        });
        if (!profile) return;
        if (profile.roles.indexOf('reviewer') !== -1) {
            var reviews = document.createElement('a');
            reviews.href = 'beoordelingen.html';
            reviews.dataset.collaborationLink = 'review';
            reviews.textContent = 'Beoordelingen';
            if (location.pathname.endsWith('/beoordelingen.html')) reviews.classList.add('active');
            links.appendChild(reviews);
        }
        if (profile.roles.indexOf('administrator') !== -1) {
            var users = document.createElement('a');
            users.href = 'gebruikers.html';
            users.dataset.collaborationLink = 'users';
            users.textContent = 'Gebruikers';
            if (location.pathname.endsWith('/gebruikers.html')) users.classList.add('active');
            links.appendChild(users);
        }
    }

    async function synchronize(user) {
        if (!user) {
            Collaboration.currentUser = null;
            setNavigation(null);
            emit(null);
            return;
        }
        try {
            var payload = await request('/session', { method: 'POST', body: '{}' });
            Collaboration.currentUser = payload.user;
            setNavigation(payload.user);
            emit(payload.user);
        } catch (error) {
            Collaboration.currentUser = null;
            setNavigation(null);
            console.warn('[Collaboration] sessie kon niet worden geladen');
            emit(null);
        }
    }

    var Collaboration = {
        currentUser: null,

        init: function () {
            if (initialized || !window.Auth) return;
            initialized = true;
            window.Auth.onChange(synchronize);
        },

        onChange: function (listener) {
            listeners.push(listener);
            listener(this.currentUser);
        },

        hasRole: function (role) {
            return !!this.currentUser && this.currentUser.roles.indexOf(role) !== -1;
        },

        api: function (path, options) {
            return request(path, options);
        }
    };

    window.Collaboration = Collaboration;
    if (window.Auth) Collaboration.init();
    else document.addEventListener('DOMContentLoaded', function () { Collaboration.init(); });
})();
