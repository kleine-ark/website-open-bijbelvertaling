/* Feedback-tool — gebruiker selecteert tekst, klikt 💬 in floating palette,
 * vult suggestie in, verzendt → Firestore (collectie `feedback`) +
 * POST /api/feedback (server.py mailt door naar maartenvroegindeweij@gmail.com).
 */

const Feedback = {
    SERVER_ENDPOINT: '/api/feedback',
    modal: null,
    pending: null,  // { bookId, ch, vs, text }

    init() {
        this._extendPalette();
        // Rechtermuisknop op col-2026 → feedback voor huidige selectie
        document.addEventListener('contextmenu', (e) => {
            const cell = e.target.closest && e.target.closest('.col-2026');
            if (!cell) return;
            const sel = window.getSelection();
            if (!sel || sel.isCollapsed) return;
            const text = sel.toString().trim();
            if (!text) return;
            const row = cell.closest('.verse-row');
            if (!row) return;
            e.preventDefault();
            this.open({
                bookId: row.dataset.book,
                ch: parseInt(row.dataset.chapter, 10),
                vs: parseInt(row.dataset.verse, 10),
                text
            });
            if (window.Highlight) Highlight.hidePalette();
        });
    },

    /* ===== Palette knop toevoegen ===== */
    _extendPalette() {
        if (!window.Highlight) return;
        const origBuild = Highlight.buildPalette.bind(Highlight);
        Highlight.buildPalette = () => {
            const pal = origBuild();
            if (pal && !pal.querySelector('.hl-feedback-btn')) {
                const btn = document.createElement('button');
                btn.className = 'hl-color-btn hl-feedback-btn';
                btn.title = 'Feedback / suggestie';
                btn.textContent = '💬';
                btn.style.background = 'transparent';
                btn.style.borderColor = 'rgba(255,255,255,0.55)';
                btn.style.fontSize = '13px';
                btn.style.lineHeight = '18px';
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (Highlight.lastSelection) {
                        const s = Highlight.lastSelection;
                        this.open({ bookId: s.bookId, ch: s.ch, vs: s.vs, text: s.text });
                    }
                    Highlight.hidePalette();
                });
                pal.appendChild(btn);
            }
            return pal;
        };
    },

    /* ===== Modal ===== */
    _ensureModal() {
        if (this.modal) return this.modal;
        const wrap = document.createElement('div');
        wrap.id = 'feedback-modal';
        wrap.className = 'feedback-modal hidden';
        wrap.innerHTML = `
            <div class="feedback-modal-backdrop"></div>
            <div class="feedback-modal-dialog" role="dialog" aria-modal="true" aria-labelledby="fb-title">
                <h3 id="fb-title">Feedback / suggestie</h3>
                <p class="fb-ref"></p>
                <blockquote class="fb-quote"></blockquote>
                <label for="fb-suggestion">Jouw suggestie of opmerking</label>
                <textarea id="fb-suggestion" rows="5" placeholder="Bijv.: 'voorgesteld als — voorgedragen als'..."></textarea>
                <div class="fb-actions">
                    <button class="fb-cancel" type="button">Annuleren</button>
                    <button class="fb-send"   type="button">Verzenden</button>
                </div>
                <p class="fb-status" aria-live="polite"></p>
            </div>`;
        document.body.appendChild(wrap);
        wrap.querySelector('.feedback-modal-backdrop').addEventListener('click', () => this.close());
        wrap.querySelector('.fb-cancel').addEventListener('click', () => this.close());
        wrap.querySelector('.fb-send').addEventListener('click', () => this.send());
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !this.modal.classList.contains('hidden')) this.close();
        });
        this.modal = wrap;
        return wrap;
    },

    open(sel) {
        this.pending = sel;
        const m = this._ensureModal();
        const refLabel = `${sel.bookId} ${sel.ch}:${sel.vs}`;
        m.querySelector('.fb-ref').textContent = refLabel;
        m.querySelector('.fb-quote').textContent = sel.text;
        m.querySelector('#fb-suggestion').value = '';
        m.querySelector('.fb-status').textContent = '';
        m.querySelector('.fb-send').disabled = false;
        m.classList.remove('hidden');
        this._toonLoginStatus();
        setTimeout(() => m.querySelector('#fb-suggestion').focus(), 30);
    },

    /* Zonder login komt de melding nergens aan: Firestore weigert het schrijven
       (permission-denied) en er is geen server-endpoint op een statische site.
       Vraag dus vooraf om inloggen, in plaats van pas na het verzenden te
       melden dat het mislukt is. */
    _toonLoginStatus() {
        var m = this.modal;
        if (!m) return;
        var status = m.querySelector('.fb-status');
        var send = m.querySelector('.fb-send');
        var ingelogd = !!(window.Auth && window.Auth.currentUser);

        if (ingelogd) {
            send.disabled = false;
            status.textContent = '';
            return;
        }
        send.disabled = true;
        status.innerHTML = 'Log eerst in, dan komt uw suggestie bij ons terecht. ' +
            '<button type="button" class="fb-login" style="background:var(--navy,#142e42);' +
            'color:#fff;border:2px solid var(--gold,#cba449);border-radius:5px;' +
            'padding:5px 14px;font:inherit;font-weight:600;cursor:pointer;margin-left:6px;">' +
            'Inloggen met Google</button>';
        var knop = status.querySelector('.fb-login');
        if (knop) {
            knop.addEventListener('click', function () {
                status.textContent = 'Bezig met inloggen…';
                if (window.Auth && window.Auth.login) window.Auth.login();
            });
        }
        // Na een geslaagde login (ook na de redirect op mobiel) de knop vrijgeven.
        if (window.Auth && window.Auth.onChange && !this._loginGekoppeld) {
            this._loginGekoppeld = true;
            var zelf = this;
            window.Auth.onChange(function () {
                if (zelf.modal && !zelf.modal.classList.contains('hidden')) zelf._toonLoginStatus();
            });
        }
    },

    close() {
        if (this.modal) this.modal.classList.add('hidden');
        this.pending = null;
    },

    async send() {
        if (!this.pending) return;
        const m = this.modal;
        const txt = m.querySelector('#fb-suggestion').value.trim();
        if (!txt) {
            m.querySelector('.fb-status').textContent = 'Vul eerst een suggestie in.';
            return;
        }
        const sendBtn = m.querySelector('.fb-send');
        sendBtn.disabled = true;
        const status = m.querySelector('.fb-status');
        status.textContent = 'Verzenden…';

        const user = (window.Auth && window.Auth.currentUser) || null;
        const payload = {
            user: user ? {
                uid: user.uid,
                name: user.displayName || '',
                email: user.email || ''
            } : { uid: null, name: 'anoniem', email: '' },
            ref: `${this.pending.bookId} ${this.pending.ch}:${this.pending.vs}`,
            book: this.pending.bookId,
            chapter: this.pending.ch,
            verse: this.pending.vs,
            selected: this.pending.text,
            suggestion: txt,
            datum: new Date().toISOString(),
            userAgent: navigator.userAgent
        };

        const tasks = [];

        // 1) Firestore (indien ingelogd & beschikbaar)
        if (window._fb && window._fb.db && user) {
            tasks.push((async () => {
                try {
                    const { collection, addDoc, serverTimestamp } = window._fb.fsMod;
                    await addDoc(collection(window._fb.db, 'feedback'), {
                        ...payload,
                        createdAt: serverTimestamp()
                    });
                    return 'firestore-ok';
                } catch (e) {
                    console.warn('[Feedback] Firestore failed:', e);
                    // permission-denied betekent dat de beveiligingsregels het
                    // schrijven blokkeren, niet dat de verbinding stuk is. Zie
                    // firestore.rules in de repo; die moet in de Console staan.
                    if (e && e.code === 'permission-denied') return 'firestore-geweigerd';
                    return 'firestore-fail';
                }
            })());
        }

        // 2) server.py /api/feedback (mail + log)
        tasks.push((async () => {
            try {
                const r = await fetch(this.SERVER_ENDPOINT, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (!r.ok) return 'server-fail-' + r.status;
                const j = await r.json().catch(() => ({}));
                return j.mail === true ? 'server-mailed' : 'server-logged';
            } catch (e) {
                console.warn('[Feedback] server failed:', e);
                return 'server-fail';
            }
        })());

        const results = await Promise.all(tasks);
        const ok = results.some(r => r && r.indexOf('fail') === -1);
        if (ok) {
            status.textContent = 'Bedankt! Je opmerking is verstuurd.';
            setTimeout(() => this.close(), 1600);
        } else {
            const subject = `[OSV opmerking] ${payload.ref}`;
            const body =
                `Vers: ${payload.ref}\n` +
                `Geselecteerde tekst:\n  "${payload.selected}"\n\n` +
                `Suggestie:\n${payload.suggestion}\n`;
            const mailto = `mailto:algemeen3bm@gmail.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
            status.innerHTML = 'Online versturen mislukt. <a href="' + mailto + '" style="color:var(--gold);font-weight:600;">Klik hier om via je mailprogramma te versturen</a>.';
            sendBtn.disabled = false;
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => Feedback.init(), 100);
});
window.Feedback = Feedback;
