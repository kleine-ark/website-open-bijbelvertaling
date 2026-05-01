/* Cloud-highlights — sync layer tussen Highlight.state (localStorage)
 *  en Firestore: users/{uid}/highlights (single document).
 *
 * Strategie:
 *  - Bij login: pull cloud-state, merge per vers met laatste-wint-timestamp
 *  - Daarna: elke save() in Highlight wordt gedebouncedin Firestore opgeslagen
 *  - Bij logout: stop syncing; localStorage blijft authoritative
 */

const CloudHighlights = {
    SAVE_DEBOUNCE_MS: 1500,
    enabled: false,
    uid: null,
    docRef: null,
    saveTimer: null,
    lastPushedJSON: null,

    init() {
        if (!window.Auth || !window.Highlight) return;
        // Wrap Highlight.save: roep cloud-sync na elke lokale save
        const origSave = Highlight.save.bind(Highlight);
        Highlight.save = () => {
            origSave();
            this._touchTimestamps();
            this.scheduleSave();
        };

        Auth.onChange((user) => {
            if (user) this.attach(user);
            else      this.detach();
        });
    },

    _touchTimestamps() {
        // Voeg ts toe aan alle entries die geen timestamp hebben (na lokale wijziging
        // weten we niet welke entry net wijzigde — dus pak de _meta hash i.p.v. per-entry).
        // Lichtgewicht: bewaar 1 globale ts in state._meta
        Highlight.state._meta = Highlight.state._meta || {};
        Highlight.state._meta.lastLocalEdit = Date.now();
    },

    async attach(user) {
        if (!window._fb || !window._fb.db) return;
        this.uid = user.uid;
        const { doc } = window._fb.fsMod;
        this.docRef = doc(window._fb.db, 'users', this.uid, 'data', 'highlights');
        this.enabled = true;
        await this.pullAndMerge();
    },

    detach() {
        this.enabled = false;
        this.uid = null;
        this.docRef = null;
        if (this.saveTimer) { clearTimeout(this.saveTimer); this.saveTimer = null; }
    },

    async pullAndMerge() {
        if (!this.docRef) return;
        try {
            const { getDoc } = window._fb.fsMod;
            const snap = await getDoc(this.docRef);
            if (!snap.exists()) {
                // Geen cloud-state — push huidige local
                await this.pushNow();
                return;
            }
            const cloud = snap.data() || {};
            const cloudState = cloud.state || {};
            const cloudTs = (cloudState._meta && cloudState._meta.lastLocalEdit) || 0;
            const localTs = (Highlight.state._meta && Highlight.state._meta.lastLocalEdit) || 0;

            // Per-vers merge: laatste-wint op grof niveau (cloud vs local)
            // Voor verzen die slechts in 1 bron bestaan: behoud beide.
            const merged = {};
            const allKeys = new Set([...Object.keys(cloudState), ...Object.keys(Highlight.state)]);
            allKeys.forEach(k => {
                if (k === '_meta') return;
                const c = cloudState[k];
                const l = Highlight.state[k];
                if (c && !l) merged[k] = c;
                else if (l && !c) merged[k] = l;
                else if (c && l) merged[k] = (cloudTs > localTs) ? c : l;
            });
            merged._meta = { lastLocalEdit: Math.max(cloudTs, localTs) };

            Highlight.state = merged;
            // Schrijf merged naar localStorage zonder cloud-loop te triggeren
            try {
                localStorage.setItem(Highlight.STORAGE_KEY, JSON.stringify(merged));
            } catch (e) { console.warn(e); }

            // Re-render huidig hoofdstuk indien zichtbaar
            this._reRenderCurrent();

            // Push merged terug naar cloud (consistent state)
            await this.pushNow();
        } catch (e) {
            console.warn('[CloudHighlights] pull failed:', e);
        }
    },

    _reRenderCurrent() {
        try {
            const rows = document.querySelectorAll('.verse-row[data-book][data-chapter]');
            const seen = new Set();
            rows.forEach(r => {
                const k = `${r.dataset.book}|${r.dataset.chapter}`;
                if (seen.has(k)) return;
                seen.add(k);
                Highlight.applyToChapter(r.dataset.book, parseInt(r.dataset.chapter, 10));
            });
        } catch (e) { console.warn(e); }
    },

    scheduleSave() {
        if (!this.enabled || !this.docRef) return;
        if (this.saveTimer) clearTimeout(this.saveTimer);
        this.saveTimer = setTimeout(() => this.pushNow(), this.SAVE_DEBOUNCE_MS);
    },

    async pushNow() {
        if (!this.enabled || !this.docRef) return;
        try {
            const { setDoc } = window._fb.fsMod;
            const payload = {
                state: Highlight.state,
                updatedAt: Date.now()
            };
            const json = JSON.stringify(payload.state);
            if (json === this.lastPushedJSON) return;
            await setDoc(this.docRef, payload);
            this.lastPushedJSON = json;
        } catch (e) {
            console.warn('[CloudHighlights] push failed:', e);
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    // Wacht tot Highlight + Auth ge­ïnitialiseerd zijn
    setTimeout(() => CloudHighlights.init(), 200);
});
window.CloudHighlights = CloudHighlights;
