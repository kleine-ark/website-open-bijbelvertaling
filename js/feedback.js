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
    savedRange: null,
    savedScroll: null,

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
                <div class="fb-types" aria-label="Voeg een categorie toe">
                    <span class="fb-types-label">Voeg categorie toe</span>
                    <button type="button" class="fb-type-chip" data-prefix="Citatie">Citatie</button>
                    <button type="button" class="fb-type-chip" data-prefix="Principe">Principe</button>
                    <button type="button" class="fb-type-chip" data-prefix="Spelling en grammatica">Spelling en grammatica</button>
                    <button type="button" class="fb-type-chip" data-prefix="Oude woorden vervangen">Oude woorden</button>
                    <button type="button" class="fb-type-chip" data-prefix="Woord is niet volgens principe vervangen">Principe niet toegepast</button>
                    <button type="button" class="fb-type-chip" data-prefix="Tag onderwerp">Onderwerptag</button>
                </div>
                <label for="fb-suggestion">Jouw suggestie of opmerking</label>
                <textarea id="fb-suggestion" rows="5" placeholder="Bijv.: 'voorgesteld als — voorgedragen als'..."></textarea>
                <p class="fb-status" aria-live="polite"></p>
                <div class="fb-actions">
                    <button class="fb-cancel" type="button">Annuleren</button>
                    <button class="fb-send"   type="button">Verzenden</button>
                </div>
            </div>`;
        document.body.appendChild(wrap);
        wrap.querySelector('.feedback-modal-backdrop').addEventListener('click', () => this.close());
        wrap.querySelector('.fb-cancel').addEventListener('click', () => this.close());
        wrap.querySelector('.fb-send').addEventListener('click', () => this.send());
        wrap.querySelectorAll('.fb-type-chip').forEach(button => {
            button.addEventListener('click', () => this.insertCategory(button.dataset.prefix));
        });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !this.modal.classList.contains('hidden')) this.close();
        });
        this.modal = wrap;
        return wrap;
    },

    /* Op een telefoon krimpt het zichtbare deel van het scherm als het
       toetsenbord opengaat, maar een position:fixed element blijft staan waar
       het stond. Zo verdween de knoppenrij onder het toetsenbord: typen ging
       wel, verzenden niet. visualViewport is het enige dat weet hoeveel er nog
       over is; daar hangen we de onderkant en de maximale hoogte aan op.

       Waar visualViewport ontbreekt vallen de CSS-variabelen terug op hun
       standaardwaarde en staat de kaart gewoon onderaan het venster. */
    _volgToetsenbord() {
        const vv = window.visualViewport;
        if (!vv) return;
        if (!this._pasViewport) {
            this._pasViewport = () => {
                if (!this.modal || this.modal.classList.contains('hidden')) return;
                const onder = Math.max(0, window.innerHeight - vv.height - vv.offsetTop);
                this.modal.style.setProperty('--fb-onder', onder + 'px');
                this.modal.style.setProperty('--fb-hoogte', vv.height + 'px');
            };
            vv.addEventListener('resize', this._pasViewport);
            vv.addEventListener('scroll', this._pasViewport);
        }
        this._pasViewport();
    },

    /* De bevestiging staat onderin en niet in de kaart, omdat de kaart al dicht
       is tegen de tijd dat Google antwoordt. Bij mislukken hangt er een knop
       aan: de ingetypte tekst is niet weg, die komt er dan weer in te staan. */
    _melding(tekst, actie) {
        let el = document.getElementById('fb-toast');
        if (!el) {
            el = document.createElement('div');
            el.id = 'fb-toast';
            el.className = 'fb-toast';
            el.setAttribute('role', 'status');
            el.setAttribute('aria-live', 'polite');
            document.body.appendChild(el);
        }
        clearTimeout(this._meldingTijd);
        el.replaceChildren(document.createTextNode(tekst));
        el.classList.toggle('fb-toast-fout', !!actie);
        if (actie) {
            const knop = document.createElement('button');
            knop.type = 'button';
            knop.className = 'fb-toast-knop';
            knop.textContent = actie.label;
            knop.addEventListener('click', () => {
                el.classList.remove('zichtbaar');
                actie.doe();
            });
            el.appendChild(knop);
        }
        el.classList.add('zichtbaar');
        this._meldingTijd = setTimeout(() => el.classList.remove('zichtbaar'), actie ? 9000 : 3200);
    },

    open(sel) {
        this.pending = sel;
        const selection = window.getSelection && window.getSelection();
        this.savedRange = selection && selection.rangeCount ? selection.getRangeAt(0).cloneRange() : null;
        this.savedScroll = { x: window.scrollX, y: window.scrollY };
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
        this._volgToetsenbord();
        setTimeout(() => m.querySelector('#fb-suggestion').focus(), 30);
    },


    close() {
        if (this.modal) {
            const field = this.modal.querySelector('#fb-suggestion');
            if (field) field.blur();
        }
        if (this.modal) this.modal.classList.add('hidden');
        this.pending = null;
        if (this.savedRange && window.getSelection) {
            try {
                const selection = window.getSelection();
                selection.removeAllRanges();
                selection.addRange(this.savedRange);
            } catch (_) { /* De tekst kan intussen opnieuw zijn opgebouwd. */ }
        }
        if (this.savedScroll) window.scrollTo(this.savedScroll.x, this.savedScroll.y);
        this.savedRange = null;
        this.savedScroll = null;
    },

    insertCategory(label) {
        const field = this.modal && this.modal.querySelector('#fb-suggestion');
        if (!field || !label) return;
        const prefix = `[${label}] `;
        if (!field.value.startsWith(prefix)) field.value = prefix + field.value;
        field.setSelectionRange(prefix.length, prefix.length);
        field.focus({ preventScroll: true });
    },

    send() {
        if (!this.pending) return;
        const m = this.modal;
        const txt = m.querySelector('#fb-suggestion').value.trim();
        if (!txt) {
            m.querySelector('.fb-status').textContent = 'Vul eerst een suggestie in.';
            return;
        }
        const user = (window.Auth && window.Auth.currentUser) || null;
        const opdracht = {
            ref: this.pending.ref || `${this.pending.bookId} ${this.pending.ch}:${this.pending.vs}`,
            selectie: this.pending.text || '',
            suggestie: txt,
            van: (user && user.displayName) || 'anoniem',
            selectiegegevens: this.pending
        };
        // De kaart gaat dicht vóór het versturen. Wachten op Google levert de
        // lezer niets op — met no-cors is het antwoord toch niet uit te lezen —
        // en houdt hem ondertussen wel van de tekst af. De uitslag komt onderin.
        this.close();
        this._verstuur(opdracht);
    },

    async _verstuur(o) {
        // Wat we van no-cors terugkrijgen is een leeg antwoord; de status is
        // niet uit te lezen. Wat het wél zegt: als fetch niet afketst, is het
        // verzoek de deur uit. Dat is precies de fout die de lezer kan
        // verhelpen (geen verbinding); een fout aan Google's kant kan hij toch
        // niet oplossen. Daarom hangt de bevestiging aan het afketsen.
        const v = this.FORMULIER_VELDEN;
        const velden = new URLSearchParams();
        velden.append(v.vers, o.ref);
        velden.append(v.selectie, o.selectie);
        velden.append(v.suggestie, o.suggestie);
        velden.append(v.van, o.van);
        try {
            await fetch(this.FORMULIER, { method: 'POST', mode: 'no-cors', body: velden });
            this._melding('Bedankt! Je opmerking is verstuurd.');
        } catch (e) {
            console.warn('[Feedback] versturen mislukt:', e);
            this._melding('Versturen mislukt — er lijkt geen verbinding te zijn.', {
                label: 'Opnieuw',
                doe: () => {
                    this.open(o.selectiegegevens);
                    this.modal.querySelector('#fb-suggestion').value = o.suggestie;
                }
            });
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => Feedback.init(), 100);
});
window.Feedback = Feedback;
