/* Auth — Google-login via Firebase
 *
 * Werkt graceful zonder Firebase-config: knop blijft verborgen, alle
 * andere features blijven werken (localStorage-mode).
 */

(function () {
// Guard: sommige pagina's laden auth.js statisch, topnav.js injecteert het ook
// dynamisch. Zonder deze check gaf dat "Identifier 'Auth' has already been declared"
// (en op Safari/WebKit kan zo'n dubbele const de scriptuitvoering stoppen).
if (window.Auth) return;
const Auth = {
    app: null,
    auth: null,
    db: null,
    currentUser: null,
    stateResolved: false,
    initializing: false,
    listeners: [],   // (user|null, stateResolved) => void
    CACHE_KEY: 'osv_auth_cache',

    onChange(cb) {
        this.listeners.push(cb);
        // Roep direct aan met huidige status
        try { cb(this.currentUser, this.stateResolved); } catch (e) { console.warn(e); }
    },

    notify() {
        this.listeners.forEach(cb => {
            try { cb(this.currentUser, this.stateResolved); } catch (e) { console.warn(e); }
        });
    },

    saveCache(user) {
        try {
            if (user) {
                localStorage.setItem(this.CACHE_KEY, JSON.stringify({
                    displayName: user.displayName || null,
                    photoURL: user.photoURL || null,
                    email: user.email || null
                }));
            } else {
                localStorage.removeItem(this.CACHE_KEY);
            }
        } catch (e) { /* localStorage geweigerd — niet kritiek */ }
    },

    loadCache() {
        try {
            const raw = localStorage.getItem(this.CACHE_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch (e) { return null; }
    },

    async init() {
        if (this.initializing || this.stateResolved) return;
        this.initializing = true;
        // Instant render vanuit cache zodat de naam direct verschijnt
        // i.p.v. te wachten op Firebase-CDN + onAuthStateChanged round-trip.
        const cached = this.loadCache();
        if (cached) this.renderButton(cached);

        if (!window.firebaseEnabled) {
            console.info('[Auth] Firebase niet geconfigureerd — login uitgeschakeld.');
            if (!cached) this.renderButton(null);
            this.stateResolved = true;
            this.notify();
            return;
        }
        try {
            // Lazy-load Firebase via CDN (modular SDK v10)
            const [{ initializeApp }, authMod, fsMod] = await Promise.all([
                import('https://www.gstatic.com/firebasejs/10.13.0/firebase-app.js'),
                import('https://www.gstatic.com/firebasejs/10.13.0/firebase-auth.js'),
                import('https://www.gstatic.com/firebasejs/10.13.0/firebase-firestore.js')
            ]);
            this.app = initializeApp(window.firebaseConfig);
            this.auth = authMod.getAuth(this.app);
            this.db   = fsMod.getFirestore(this.app);
            // Expose Firebase modules voor andere modules
            window._fb = {
                app: this.app,
                auth: this.auth,
                db: this.db,
                authMod, fsMod
            };
            authMod.onAuthStateChanged(this.auth, (user) => {
                this.currentUser = user;
                this.stateResolved = true;
                this.saveCache(user);
                this.renderButton(user);
                this.notify();
            });
            // Rond een eventuele redirect-login af (mobiel gebruikt redirect i.p.v. popup)
            if (authMod.getRedirectResult) {
                authMod.getRedirectResult(this.auth).catch((e) => {
                    if (e && e.code && e.code !== 'auth/no-auth-event') {
                        console.warn('[Auth] redirect-result:', e.code);
                    }
                });
            }
        } catch (e) {
            console.warn('[Auth] kon Firebase niet laden:', e);
            if (!cached) this.renderButton(null);
            this.stateResolved = true;
            this.notify();
        }
    },

    async login() {
        if (!this.auth) return;
        const { GoogleAuthProvider, signInWithPopup, signInWithRedirect } = window._fb.authMod;
        const provider = new GoogleAuthProvider();
        // Mobiel/touch: popups worden vaak geblokkeerd of afgebroken
        // (auth/cancelled-popup-request) → gebruik de redirect-flow.
        const useRedirect = window.matchMedia && window.matchMedia('(max-width: 768px)').matches;
        try {
            if (useRedirect && signInWithRedirect) {
                await signInWithRedirect(this.auth, provider);
                return;
            }
            await signInWithPopup(this.auth, provider);
        } catch (e) {
            // Benigne: dubbel-trigger of door gebruiker gesloten popup → niet storen.
            if (e && (e.code === 'auth/cancelled-popup-request' || e.code === 'auth/popup-closed-by-user')) {
                console.info('[Auth] login geannuleerd:', e.code);
                return;
            }
            // Popup geblokkeerd → val terug op redirect.
            if (e && e.code === 'auth/popup-blocked' && signInWithRedirect) {
                try { await signInWithRedirect(this.auth, provider); return; } catch (e2) { e = e2; }
            }
            console.warn('[Auth] login afgebroken:', e);
            alert('Inloggen mislukt. Controleer het logboek.');
        }
    },

    async logout() {
        if (!this.auth) return;
        const { signOut } = window._fb.authMod;
        try { await signOut(this.auth); } catch (e) { console.warn(e); }
    },

    /* ===== UI ===== */
    renderButton(user) {
        const slot = document.getElementById('auth-slot');
        if (!slot) return;
        if (!window.firebaseEnabled) {
            slot.innerHTML = '';
            slot.style.display = 'none';
            return;
        }
        slot.style.display = '';
        slot.replaceChildren();
        if (!user) {
            const button = document.createElement('button');
            button.className = 'auth-btn auth-login';
            button.title = 'Login met Google';
            button.innerHTML = '<svg width="14" height="14" viewBox="0 0 18 18" aria-hidden="true"><path fill="#fff" d="M17.64 9.2c0-.64-.06-1.25-.17-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.92c1.71-1.57 2.68-3.89 2.68-6.62z"/><path fill="#fff" opacity=".85" d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.92-2.26c-.81.54-1.84.86-3.04.86-2.34 0-4.32-1.58-5.03-3.7H.92v2.34A9 9 0 0 0 9 18z"/><path fill="#fff" opacity=".7" d="M3.97 10.71A5.41 5.41 0 0 1 3.68 9c0-.59.1-1.17.29-1.71V4.95H.92A9 9 0 0 0 0 9c0 1.45.35 2.82.92 4.05l3.05-2.34z"/><path fill="#fff" opacity=".55" d="M9 3.58c1.32 0 2.51.45 3.44 1.35l2.58-2.58C13.46.89 11.43 0 9 0A9 9 0 0 0 .92 4.95l3.05 2.34C4.68 5.16 6.66 3.58 9 3.58z"/></svg><span>Login</span>';
            button.addEventListener('click', () => this.login());
            slot.appendChild(button);
            return;
        }
        const wrap = document.createElement('div');
        wrap.className = 'auth-user';
        wrap.title = user.email || '';
        if (user.photoURL) {
            const photo = document.createElement('img');
            photo.src = user.photoURL;
            photo.alt = '';
            photo.className = 'auth-avatar';
            wrap.appendChild(photo);
        } else {
            const fallback = document.createElement('span');
            fallback.className = 'auth-avatar auth-avatar-fallback';
            fallback.textContent = (user.displayName || user.email || '?')[0].toUpperCase();
            wrap.appendChild(fallback);
        }
        const name = document.createElement('span');
        name.className = 'auth-name';
        name.textContent = (user.displayName || user.email || 'Ingelogd').split(' ')[0];
        const logout = document.createElement('button');
        logout.className = 'auth-btn auth-logout';
        logout.title = 'Uitloggen';
        logout.textContent = '↪';
        logout.addEventListener('click', () => this.logout());
        wrap.append(name, logout);
        slot.appendChild(wrap);
    }
};

document.addEventListener('DOMContentLoaded', () => Auth.init());
window.Auth = Auth;
})();
