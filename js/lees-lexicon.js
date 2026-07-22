/* Open Vertaling Leesversie — Lexicon & Strong's */

const LeesLexicon = {
    hebrewLoaded: false,
    greekLoaded: false,
    hebrewData: null,
    greekData: null,

    async ensureLoaded(lang) {
        if (lang === 'hebrew' && !this.hebrewLoaded) {
            // The lexicon files define global arrays
            await this.loadScript('/js/hebreeuws-woordenboek.js');
            this.hebrewData = typeof hebreeuwsWoordenboek !== 'undefined' ? hebreeuwsWoordenboek : [];
            this.hebrewLoaded = true;
        }
        if (lang === 'greek' && !this.greekLoaded) {
            await this.loadScript('/js/grieks-woordenboek.js');
            this.greekData = typeof grieksWoordenboek !== 'undefined' ? grieksWoordenboek : [];
            this.greekLoaded = true;
        }
    },

    loadScript(src) {
        return new Promise((resolve, reject) => {
            if (document.querySelector(`script[src="${src}"]`)) { resolve(); return; }
            const s = document.createElement('script');
            s.src = src;
            s.onload = resolve;
            s.onerror = reject;
            document.head.appendChild(s);
        });
    },

    lookup(strongs) {
        if (!strongs) return null;
        const isHebrew = strongs.startsWith('H');
        const data = isHebrew ? this.hebrewData : this.greekData;
        if (!data) return null;

        const num = strongs.replace(/^[HG]/, '');
        return data.find(entry =>
            entry.strongs === strongs ||
            entry.strongs === num ||
            entry.nummer === strongs ||
            entry.nummer === num
        ) || null;
    },

    async showPopover(strongs, word, anchorEl) {
        const lang = strongs.startsWith('H') ? 'hebrew' : 'greek';
        await this.ensureLoaded(lang);

        const entry = this.lookup(strongs);
        const popover = document.getElementById('strongs-popover');

        document.getElementById('popover-word').textContent = word || strongs;
        document.getElementById('popover-strongs').textContent = strongs;
        document.getElementById('popover-gloss').textContent =
            entry ? (entry.gloss || entry.korte_definitie || entry.definitie || '').substring(0, 120) : 'Niet gevonden';

        // Position near the anchor
        const rect = anchorEl.getBoundingClientRect();
        popover.style.left = `${rect.left + window.scrollX}px`;
        popover.style.top = `${rect.bottom + window.scrollY + 4}px`;
        popover.classList.remove('hidden');

        // "More" button
        document.getElementById('popover-more').onclick = () => {
            popover.classList.add('hidden');
            this.showFullEntry(strongs, word, entry);
        };

        // Close on outside click
        const closeHandler = (e) => {
            if (!popover.contains(e.target) && e.target !== anchorEl) {
                popover.classList.add('hidden');
                document.removeEventListener('click', closeHandler);
            }
        };
        setTimeout(() => document.addEventListener('click', closeHandler), 10);
    },

    showFullEntry(strongs, word, entry) {
        const modal = document.getElementById('lexicon-modal');
        const title = document.getElementById('lexicon-title');
        const body = document.getElementById('lexicon-body');

        title.textContent = `${strongs} — Lexicon`;

        if (!entry) {
            body.innerHTML = `<p>Geen lexicon-entry gevonden voor ${strongs}.</p>`;
        } else {
            body.innerHTML = `
                <div class="lex-word">${entry.woord || entry.lemma || word || ''}</div>
                <div class="lex-strongs">${strongs} ${entry.transliteratie || ''}</div>
                <div class="lex-def">${entry.definitie || entry.gloss || ''}</div>
            `;
        }

        modal.classList.remove('hidden');
    },

    // Show all source words for a verse
    showVerseWords(verse) {
        if (!verse.grondtekst || verse.grondtekst.length === 0) return;

        const modal = document.getElementById('lexicon-modal');
        const title = document.getElementById('lexicon-title');
        const body = document.getElementById('lexicon-body');

        title.textContent = `Grondtekst — vers ${verse.number}`;

        const rows = verse.grondtekst.map(g => {
            const s = g.strongs || '';
            return `<tr style="cursor:pointer" data-strongs="${s}" data-word="${g.woord || ''}">
                <td style="font-size:20px;padding:4px 12px 4px 0">${g.woord || ''}</td>
                <td style="color:var(--text-muted);padding:4px 12px 4px 0;font-size:13px">${s}</td>
                <td style="font-size:13px">${g.gloss || ''}</td>
            </tr>`;
        }).join('');

        body.innerHTML = `<table style="width:100%;border-collapse:collapse">${rows}</table>`;

        // Click row to show full entry
        body.querySelectorAll('tr[data-strongs]').forEach(tr => {
            tr.addEventListener('click', () => {
                const strongs = tr.dataset.strongs;
                const word = tr.dataset.word;
                if (strongs) this.showPopover(strongs, word, tr);
            });
        });

        modal.classList.remove('hidden');
    },
};

// Integrate with Lees: add verse-level Strong's button
document.addEventListener('DOMContentLoaded', () => {
    // Add double-click handler on verses to show grondtekst
    document.getElementById('verses')?.addEventListener('dblclick', async (e) => {
        const verseSpan = e.target.closest('.verse-span');
        if (!verseSpan) return;
        const verseNum = parseInt(verseSpan.dataset.verse);
        if (!Lees.currentBook) return;

        const book = Lees.bookCache[Lees.currentBook];
        if (!book) return;
        const chapter = book.chapters.find(c => c.number === Lees.currentChapter);
        if (!chapter) return;
        const verse = chapter.verses.find(v => v.number === verseNum);
        if (!verse) return;

        LeesLexicon.showVerseWords(verse);
    });
});
