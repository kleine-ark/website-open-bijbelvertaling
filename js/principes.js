/**
 * Wijzigingsprincipes — overzichtspagina
 * Laadt principes en scant boek-JSON bestanden voor toepassingen.
 */
(function() {
    'use strict';

    const CATEGORY_ORDER = ['Naamvallen', 'Aanspreekvormen', 'Godsnamen', 'Werkwoordsvormen', 'Verouderde woorden', 'Spelling', 'Overig'];

    let principesData = [];
    let booksData = [];
    // Cache: principe-ID -> [{bookId, bookName, chapter, verse, old, new}]
    let versenCache = {};
    // Count per principe (pre-counted from scan)
    let countPerPrincipe = {};

    async function init() {
        try {
            // Laad alleen 2 kleine files: principes-definities + pre-computed counts/verses
            // (was: 82 boek-JSONs van ~1MB elk = 80+ MB)
            const [principesResp, dataResp] = await Promise.all([
                fetch('data/wijzigingsprincipes.json'),
                fetch('data/principes-data.json'),
            ]);
            const principesJson = await principesResp.json();
            const data = await dataResp.json();

            principesData = principesJson.principes || [];
            countPerPrincipe = data.counts || {};

            // Convert pre-computed verses naar oude formaat voor render
            for (const [pid, list] of Object.entries(data.verses || {})) {
                versenCache[pid] = list.map(e => ({
                    bookId: e.b, bookName: e.n, chapter: e.c, verse: e.v,
                    old: e.o, new: e.x, text: '',
                }));
            }

            render();

            if (window.location.hash) {
                const targetId = window.location.hash.slice(1);
                expandPrincipe(targetId);
            }
        } catch (err) {
            document.getElementById('principes-container').innerHTML =
                `<div class="loading-msg" style="color:#b91c1c">Fout bij laden: ${err.message}</div>`;
        }
    }

    function processBookData(book, data) {
        if (!data.chapters) return;
        for (const ch of data.chapters) {
            if (!ch.verses) continue;
            for (const v of ch.verses) {
                if (!v.phraseDiff || !v.phraseDiff.length) continue;
                for (const d of v.phraseDiff) {
                    if (!d.principe) continue;
                    const pid = d.principe;
                    if (!countPerPrincipe[pid]) countPerPrincipe[pid] = 0;
                    countPerPrincipe[pid]++;

                    // Store in cache
                    if (!versenCache[pid]) versenCache[pid] = [];
                    versenCache[pid].push({
                        bookId: book.id,
                        bookName: book.nameDutch,
                        chapter: ch.number,
                        verse: v.number,
                        old: d.old,
                        new: d.new,
                        text: v.text2026 || ''
                    });
                }
            }
        }
    }

    function render() {
        const container = document.getElementById('principes-container');
        container.innerHTML = '';

        // Totaal aantal wijzigingen bovenaan
        const totalChanges = Object.values(countPerPrincipe).reduce((a, b) => a + b, 0);
        const totalPrincipes = principesData.length;
        const TOTAL_DIFFS = 71052; // van laatste diff-regen
        const pct = Math.round(100 * totalChanges / TOTAL_DIFFS);
        const losse = TOTAL_DIFFS - totalChanges;
        const summary = document.createElement('div');
        summary.style.cssText = 'background:#f8f6f2;border-left:3px solid #cba449;border-radius:0 8px 8px 0;padding:16px 20px;margin-bottom:24px;font-size:15px;line-height:1.6;';
        summary.innerHTML = `<strong>${TOTAL_DIFFS.toLocaleString('nl-NL')}</strong> tekstwijzigingen tussen SV1888 en de OSV. Daarvan is <strong>${totalChanges.toLocaleString('nl-NL')}</strong> (${pct}%) via een van de <strong>${totalPrincipes}</strong> principes geregeld; <strong>${losse.toLocaleString('nl-NL')}</strong> zijn losse, vers-specifieke correcties.`;
        container.appendChild(summary);

        // Group by category
        const grouped = {};
        for (const p of principesData) {
            const cat = p.categorie;
            if (!grouped[cat]) grouped[cat] = [];
            grouped[cat].push(p);
        }

        for (const cat of CATEGORY_ORDER) {
            const items = grouped[cat];
            if (!items || items.length === 0) continue;

            const section = document.createElement('div');
            const h2 = document.createElement('h2');
            h2.textContent = cat;
            section.appendChild(h2);

            for (const p of items) {
                const card = createPrincipeCard(p);
                section.appendChild(card);
            }

            container.appendChild(section);
        }
    }

    function createPrincipeCard(p) {
        const card = document.createElement('div');
        card.className = 'principe-card';
        card.id = p.id;

        const catLetter = p.id[0];
        const count = countPerPrincipe[p.id] || 0;

        // Header
        const header = document.createElement('div');
        header.className = 'principe-header';
        header.innerHTML = `
            <span class="expand-icon">&#9654;</span>
            <span class="principe-badge cat-${catLetter}">${p.id}</span>
            <span class="principe-change">
                <span class="old">${escHtml(p.oud)}</span>
                <span class="arrow">&rarr;</span>
                <span class="new">${escHtml(p.nieuw)}</span>
            </span>
            <span class="principe-toelichting">${escHtml(p.toelichting)}</span>
            <span class="principe-count">${count} ${count === 1 ? 'toepassing' : 'toepassingen'}</span>
        `;

        header.addEventListener('click', () => {
            card.classList.toggle('expanded');
            if (card.classList.contains('expanded')) {
                loadVerzen(p.id, card);
            }
        });

        card.appendChild(header);

        // Verzen container (hidden until expanded)
        const verzenDiv = document.createElement('div');
        verzenDiv.className = 'principe-verzen';
        card.appendChild(verzenDiv);

        return card;
    }

    function loadVerzen(principeId, card) {
        const verzenDiv = card.querySelector('.principe-verzen');
        const items = versenCache[principeId] || [];

        if (items.length === 0) {
            verzenDiv.innerHTML = '<div style="font-size:13px;color:#999;padding:8px 0;">Geen toepassingen gevonden. Draai eerst het diff-script met principe-koppeling.</div>';
            return;
        }

        // Only render if not already rendered
        if (verzenDiv.dataset.rendered) return;
        verzenDiv.dataset.rendered = '1';

        // Limit display to first 200, with message if more
        const displayItems = items.slice(0, 200);
        let html = displayItems.map(item => {
            const ref = `${item.bookName} ${item.chapter}:${item.verse}`;
            const href = `/#${item.bookId}/${item.chapter}`;
            const undoId = `${item.bookId}_${item.chapter}_${item.verse}_${principeId}`;
            const isUndone = isException(item.bookId, item.chapter, item.verse, principeId);
            const undoClass = isUndone ? 'undo-btn undone' : 'undo-btn';
            const undoLabel = isUndone ? 'Hersteld' : 'Uitzondering';
            const versText = item.text ? `<div class="vers-tekst" style="font-size:12px;color:#555;margin-top:2px;font-style:italic;">${escHtml(item.text)}</div>` : '';
            return `<div class="vers-item${isUndone ? ' vers-undone' : ''}">
                <a class="vers-ref" href="${href}" target="_blank">${escHtml(ref)}</a>
                <span class="vers-diff"><span class="diff-old">${escHtml(item.old)}</span> &rarr; <span class="diff-new">${escHtml(item.new)}</span></span>
                <button class="${undoClass}" data-book="${item.bookId}" data-ch="${item.chapter}" data-vs="${item.verse}" data-principe="${principeId}" onclick="toggleException(this)">${undoLabel}</button>
                ${versText}
            </div>`;
        }).join('');

        if (items.length > 200) {
            html += `<div style="font-size:12px;color:#999;padding:8px 0;text-align:center;">... en ${items.length - 200} meer</div>`;
        }

        verzenDiv.innerHTML = html;
    }

    function expandPrincipe(id) {
        const card = document.getElementById(id);
        if (card) {
            card.classList.add('expanded');
            loadVerzen(id, card);
            card.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    function escHtml(s) {
        if (!s) return '';
        return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    // Uitzonderingen uit localStorage
    function getExceptions() {
        try {
            return JSON.parse(localStorage.getItem('ov_uitzonderingen') || '[]');
        } catch(e) { return []; }
    }

    function saveExceptions(exceptions) {
        localStorage.setItem('ov_uitzonderingen', JSON.stringify(exceptions));
    }

    function isException(boek, hoofdstuk, vers, principe) {
        const exceptions = getExceptions();
        return exceptions.some(e => e.boek === boek && e.hoofdstuk === hoofdstuk && e.vers === vers && e.principe === principe);
    }

    // Maak toggleException globaal beschikbaar
    window.toggleException = function(btn) {
        const boek = btn.dataset.book;
        const hoofdstuk = parseInt(btn.dataset.ch);
        const vers = parseInt(btn.dataset.vs);
        const principe = btn.dataset.principe;

        let exceptions = getExceptions();
        const idx = exceptions.findIndex(e => e.boek === boek && e.hoofdstuk === hoofdstuk && e.vers === vers && e.principe === principe);

        if (idx >= 0) {
            // Was al uitzondering — verwijder
            exceptions.splice(idx, 1);
            btn.textContent = 'Uitzondering';
            btn.classList.remove('undone');
            btn.closest('.vers-item').classList.remove('vers-undone');
        } else {
            // Maak uitzondering
            exceptions.push({
                boek: boek,
                hoofdstuk: hoofdstuk,
                vers: vers,
                principe: principe,
                datum: new Date().toISOString().slice(0, 10)
            });
            btn.textContent = 'Hersteld';
            btn.classList.add('undone');
            btn.closest('.vers-item').classList.add('vers-undone');
        }

        saveExceptions(exceptions);
    };

    // Init on load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
