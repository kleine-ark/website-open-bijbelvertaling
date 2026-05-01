/* Auth — Google-login via Firebase
 *
 * Werkt graceful zonder Firebase-config: knop blijft verborgen, alle
 * andere features blijven werken (localStorage-mode).
 */

const Auth = {
    app: null,
    auth: null,
    db: null,
    currentUser: null,
    listeners: [],   // (user|null) => void

    onChange(cb) {
        this.listeners.push(cb);
        // Roep direct aan met huidige status
        try { cb(this.currentUser); } catch (e) { console.warn(e); }
    },

    notify() {
        this.listeners.forEach(cb => {
            try { cb(this.currentUser); } catch (e) { console.warn(e); }
        });
    },

    async init() {
        if (!window.firebaseEnabled) {
            console.info('[Auth] Firebase niet geconfigureerd — login uitgeschakeld.');
            this.renderButton(null);
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
                this.renderButton(user);
                this.notify();
            });
        } catch (e) {
            console.warn('[Auth] kon Firebase niet laden:', e);
            this.renderButton(null);
        }
    },

    async login() {
        if (!this.auth) return;
        const { GoogleAuthProvider, signInWithPopup } = window._fb.authMod;
        const provider = new GoogleAuthProvider();
        try {
            await signInWithPopup(this.auth, provider);
        } catch (e) {
            console.warn('[Auth] login afgebroken:', e);
            alert('Inloggen mislukt: ' + (e.message || e.code || 'onbekend'));
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
        if (!user) {
            slot.innerHTML = `<button class="auth-btn auth-login" title="Login met Google">
                <svg width="14" height="14" viewBox="0 0 18 18" aria-hidden="true"><path fill="#fff" d="M17.64 9.2c0-.64-.06-1.25-.17-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.92c1.71-1.57 2.68-3.89 2.68-6.62z"/><path fill="#fff" opacity=".85" d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.92-2.26c-.81.54-1.84.86-3.04.86-2.34 0-4.32-1.58-5.03-3.7H.92v2.34A9 9 0 0 0 9 18z"/><path fill="#fff" opacity=".7" d="M3.97 10.71A5.41 5.41 0 0 1 3.68 9c0-.59.1-1.17.29-1.71V4.95H.92A9 9 0 0 0 0 9c0 1.45.35 2.82.92 4.05l3.05-2.34z"/><path fill="#fff" opacity=".55" d="M9 3.58c1.32 0 2.51.45 3.44 1.35l2.58-2.58C13.46.89 11.43 0 9 0A9 9 0 0 0 .92 4.95l3.05 2.34C4.68 5.16 6.66 3.58 9 3.58z"/></svg>
                <span>Login</span>
            </button>`;
            slot.querySelector('button').addEventListener('click', () => this.login());
        } else {
            const photo = user.photoURL ? `<img src="${user.photoURL}" alt="" class="auth-avatar">`
                                        : `<span class="auth-avatar auth-avatar-fallback">${(user.displayName||user.email||'?')[0].toUpperCase()}</span>`;
            const name = (user.displayName || user.email || 'Ingelogd').split(' ')[0];
            slot.innerHTML = `
                <div class="auth-user" title="${user.email||''}">
                    ${photo}
                    <span class="auth-name">${name}</span>
                    <button class="auth-btn auth-logout" title="Uitloggen">↪</button>
                </div>`;
            slot.querySelector('.auth-logout').addEventListener('click', () => this.logout());
        }
    }
};

document.addEventListener('DOMContentLoaded', () => Auth.init());
window.Auth = Auth;
