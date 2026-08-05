/* Feedback-tool — de lezer selecteert tekst, klikt 💬 in het zwevende palet,
 * vult een suggestie in en verstuurt. De melding gaat rechtstreeks per mail.
 *
 * Geen inloggen vereist: dat is een drempel die alleen maar minder feedback
 * oplevert. Wie wél is ingelogd stuurt zijn naam automatisch mee.
 */

const Feedback = {
    /* Meldingen gaan rechtstreeks per mail via FormSubmit. Bewust geen
       Firestore: dat vroeg inloggen van de bezoeker én beveiligingsregels in
       de Firebase Console, terwijl het doel simpelweg is dat de melding
       aankomt. Inloggen blijft wel bestaan voor persoonlijke instellingen en
       markeringen; wie is ingelogd stuurt zijn naam automatisch mee.

       Het adres staat hier nog voluit. FormSubmit geeft na de eerste
       bevestiging een sleutel van de vorm /ajax/a1b2c3…; vervang die hier,
       dan staat het mailadres niet meer in de broncode en kunnen spambots
       het niet oogsten. */
    FORM_ENDPOINT: 'https://formsubmit.co/ajax/maartenvroegindeweij@gmail.com',
    MAIL_TERUGVAL: 'maartenvroegindeweij@gmail.com',
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
        setTimeout(() => m.querySelector('#fb-suggestion').focus(), 30);
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

        // Eén verzendweg: rechtstreeks per mail. De veldnamen met een
        // onderstreep zijn instellingen van FormSubmit zelf en komen niet in
        // de mail terecht.
        let ok = false;
        try {
            const r = await fetch(this.FORM_ENDPOINT, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                body: JSON.stringify({
                    _subject: `Opmerking bij ${payload.ref}`,
                    _template: 'table',
                    _captcha: 'false',
                    Vers: payload.ref,
                    'Geselecteerde tekst': payload.selected || '(geen selectie)',
                    Suggestie: payload.suggestion,
                    Van: payload.user.name + (payload.user.email ? ' <' + payload.user.email + '>' : ''),
                    Datum: payload.datum,
                    Browser: payload.userAgent
                })
            });
            const j = await r.json().catch(() => ({}));
            ok = r.ok && String(j.success) === 'true';
            if (!ok) console.warn('[Feedback] FormSubmit antwoordde:', r.status, j);
        } catch (e) {
            console.warn('[Feedback] versturen mislukt:', e);
        }

        if (ok) {
            status.textContent = 'Bedankt! Je opmerking is verstuurd.';
            setTimeout(() => this.close(), 1600);
        } else {
            const subject = `[OSV opmerking] ${payload.ref}`;
            const body =
                `Vers: ${payload.ref}\n` +
                `Geselecteerde tekst:\n  "${payload.selected}"\n\n` +
                `Suggestie:\n${payload.suggestion}\n`;
            const mailto = `mailto:${this.MAIL_TERUGVAL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
            status.innerHTML = 'Online versturen mislukt. <a href="' + mailto + '" style="color:var(--gold);font-weight:600;">Klik hier om via je mailprogramma te versturen</a>.';
            sendBtn.disabled = false;
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => Feedback.init(), 100);
});
window.Feedback = Feedback;
