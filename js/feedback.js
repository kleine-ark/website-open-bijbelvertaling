/* Feedback-tool — de lezer selecteert tekst, klikt 💬 in het zwevende palet,
 * vult een suggestie in en verstuurt.
 *
 * Geen inloggen vereist: dat is een drempel die alleen maar minder feedback
 * oplevert. Wie wél is ingelogd stuurt zijn naam automatisch mee.
 */

const Feedback = {
    /* De melding gaat naar een Google Formulier, dat uit zichzelf naar zijn
       gekoppelde spreadsheet schrijft. Eén weg, verder niets: geen mail, geen
       Firestore. Dat laatste vroeg inloggen van de bezoeker én
       beveiligingsregels in de console, terwijl het doel simpelweg is dat de
       melding aankomt. Inloggen blijft wel bestaan voor persoonlijke
       instellingen en markeringen.

       De veldnummers komen uit het formulier zelf; scripts/formulier_velden.py
       leest ze eruit. Zie docs/opmerkingen-in-google-sheet.md.

       Het mailadres van een inzender gaat hier bewust niet heen: de sheet is
       als CSV gepubliceerd en dus openbaar. Alleen de naam die iemand zelf
       invulde gaat mee. */
    FORMULIER: 'https://docs.google.com/forms/d/e/1FAIpQLSc7XXjzq7eA-QtJoAcJaXX5tlVodKhQ54JMdCQ6_SvkxMccWA/formResponse',
    FORMULIER_VELDEN: {
        vers:      'entry.1027694877',
        selectie:  'entry.644152872',
        suggestie: 'entry.758123662',
        van:       'entry.745198439'
    },
    modal: null,
    pending: null,  // { bookId, ch, vs, ref?, text }

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
        const refLabel = sel.ref || `${sel.bookId} ${sel.ch}:${sel.vs}`;
        m.querySelector('.fb-ref').textContent = refLabel;
        const quote = m.querySelector('.fb-quote');
        quote.replaceChildren();
        String(sel.text || '').split('\n').forEach((line, index) => {
            if (index > 0) quote.appendChild(document.createElement('br'));
            quote.appendChild(document.createTextNode(line));
        });
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
            ref: this.pending.ref || `${this.pending.bookId} ${this.pending.ch}:${this.pending.vs}`,
            book: this.pending.bookId,
            chapter: this.pending.ch,
            verse: this.pending.vs,
            selected: this.pending.text,
            suggestion: txt,
            datum: new Date().toISOString(),
            userAgent: navigator.userAgent
        };

        // Eén verzendweg: het Google Formulier, dat naar zijn eigen
        // spreadsheet schrijft.
        //
        // Wat we van no-cors terugkrijgen is een leeg antwoord — de status is
        // niet uit te lezen. Wat het wél zegt: als fetch niet afketst, is het
        // verzoek de deur uit. Dat is precies de fout die de lezer kan
        // verhelpen (geen verbinding); een fout aan Google's kant kan hij toch
        // niet oplossen. Daarom hangt de bevestiging aan het afketsen.
        let ok = false;
        try {
            const v = this.FORMULIER_VELDEN;
            const velden = new URLSearchParams();
            velden.append(v.vers, payload.ref || '');
            velden.append(v.selectie, payload.selected || '');
            velden.append(v.suggestie, payload.suggestion || '');
            velden.append(v.van, payload.user.name || 'anoniem');
            await fetch(this.FORMULIER, { method: 'POST', mode: 'no-cors', body: velden });
            ok = true;
        } catch (e) {
            console.warn('[Feedback] versturen mislukt:', e);
        }

        if (ok) {
            status.textContent = 'Bedankt! Je opmerking is verstuurd.';
            setTimeout(() => this.close(), 1600);
        } else {
            // De ingevulde tekst blijft staan en de knop gaat weer aan, zodat
            // opnieuw proberen niets kost.
            status.textContent = 'Versturen mislukt — er lijkt geen verbinding te zijn. Probeer het zo nog eens.';
            sendBtn.disabled = false;
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => Feedback.init(), 100);
});
window.Feedback = Feedback;
