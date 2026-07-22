/* Open Vertaling — localStorage persistentie */

const Storage = {
    PREFIX: 'sv2026_',

    getEdits(bookId) {
        const raw = localStorage.getItem(this.PREFIX + bookId);
        return raw ? JSON.parse(raw) : null;
    },

    saveVerse(bookId, chapter, verseNum, data) {
        const edits = this.getEdits(bookId) || {};
        edits[`${chapter}:${verseNum}`] = data;
        localStorage.setItem(this.PREFIX + bookId, JSON.stringify(edits));
    },

    exportAll() {
        const result = {};
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key.startsWith(this.PREFIX)) {
                result[key.slice(this.PREFIX.length)] = JSON.parse(localStorage.getItem(key));
            }
        }
        return result;
    },

    importEdits(data) {
        for (const [bookId, edits] of Object.entries(data)) {
            localStorage.setItem(this.PREFIX + bookId, JSON.stringify(edits));
        }
    },

    clearAll() {
        const keys = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key.startsWith(this.PREFIX)) keys.push(key);
        }
        keys.forEach(k => localStorage.removeItem(k));
    }
};
