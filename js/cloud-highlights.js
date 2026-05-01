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

            // Last-writer-wins op het hele state-object. Anders wordt
            // een lokale verwijdering "geresurrecteerd" door per-key
            // union-merge (cloud heeft entry, local niet → terug erin).
            // Eerste-keer login (lokaal nog niets) → adopteer cloud.
            const localHasAny = Object.keys(Highlight.state).some(k => k !== '_meta');
            const adoptCloud = !localHasAny || cloudTs > localTs;

            if (adoptCloud) {
                Highlight.state = JSON.parse(JSON.stringify(cloudState));
                if (!Highlight.state._meta) Highlight.state._meta = {};
                Highlight.state._meta.lastLocalEdit = cloudTs;
                try {
                    localStorage.setItem(Highlight.STORAGE_KEY, JSON.stringify(Highlight.state));
                } catch (e) { console.warn(e); }
                // Markeer als reeds gepusht zodat we niet onmiddellijk weer pushen
                this.lastPushedJSON = JSON.stringify(Highlight.state);
                this._reRenderCurrent();
            } else {
                // Local is gelijk of nieuwer → push local naar cloud (overschrijft)
                await this.pushNow();
            }
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
