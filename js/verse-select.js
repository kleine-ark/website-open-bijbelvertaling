/* Verse Select — Selecteer meerdere verzen en kopieer met/zonder opmaak */

const VerseSelect = {
    selected: new Set(),
    lastClicked: null,

    init() {
        // Kopieer-toolbar toevoegen aan DOM
        const toolbar = document.createElement('div');
        toolbar.id = 'copy-toolbar';
        const shareIcon = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.6" y1="13.5" x2="15.4" y2="17.5"/><line x1="15.4" y1="6.5" x2="8.6" y2="10.5"/></svg>';
        const imgIcon = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>';
        toolbar.innerHTML = `
            <span id="copy-count"></span>
            <button id="vers-share" title="Delen via systeem">${shareIcon} Delen</button>
            <button id="copy-plain" title="Kopieer als platte tekst">Tekst kopiëren</button>
            <button id="copy-formatted" title="Kopieer met versnummers, opmaak en Godscitaten">Kopiëren met opmaak</button>
            <button id="vers-image" title="Maak afbeelding met de tekst">${imgIcon} Op afbeelding</button>
            <button id="copy-close" title="Deselecteer alles">&times;</button>
        `;
        document.body.appendChild(toolbar);

        document.getElementById('vers-share').addEventListener('click', () => this.share());
        document.getElementById('copy-plain').addEventListener('click', () => this.copy(false));
        document.getElementById('copy-formatted').addEventListener('click', () => this.copy(true));
        document.getElementById('vers-image').addEventListener('click', () => this.asImage());
        document.getElementById('copy-close').addEventListener('click', () => this.clearAll());

        // Luister naar klikken op versnummers (legacy: highlight-toggle e.d.)
        document.getElementById('verses-container').addEventListener('click', (e) => {
            const num = e.target.closest('.verse-num');
            if (!num) return;
            const row = num.closest('.verse-row');
            if (!row) return;

            const verseKey = row.dataset.verse;

            if (e.shiftKey && this.lastClicked) {
                this.selectRange(this.lastClicked, verseKey);
            } else if (e.ctrlKey || e.metaKey) {
                this.toggle(verseKey);
            } else {
                if (this.selected.has(verseKey) && this.selected.size === 1) {
                    this.clearAll();
                } else {
                    this.clearAll();
                    this.select(verseKey);
                }
            }
            this.lastClicked = verseKey;
            this.updateUI();
        });

        // NIEUW: klik op de OV2026 tekst-cel selecteert de tekst browser-native
        // (zodat Ctrl+C werkt) + toont copy-toolbar onderin.
        // Drag-select (>5px) wordt gerespecteerd voor sub-selectie van een woord/zin.
        let downX = 0, downY = 0;
        const versesContainer = document.getElementById('verses-container');
        versesContainer.addEventListener('pointerdown', (e) => {
            downX = e.clientX; downY = e.clientY;
        });
        versesContainer.addEventListener('pointerup', (e) => {
            // Skip als klik op interactief sub-element
            if (e.target.closest('.note-marker, .strongs-inline, a, .begrip-link, .verse-num, button')) return;
            const cell = e.target.closest('.col-2026');
            if (!cell) return;
            const row = cell.closest('.verse-row');
            if (!row) return;
            const moved = Math.hypot(e.clientX - downX, e.clientY - downY);
            if (moved > 5) return; // user is drag-selecting
            const verseKey = row.dataset.verse;
            this.toggle(verseKey);
            this._syncBrowserSelectionToSelected();
            this.updateUI();
        });

        // selectionchange-driven toolbar — luistert op browser-native selectie
        // binnen #verses-container, ongeacht hoe die ontstond (klik of drag).
        this._setupSelectionToolbar();
    },

    // Synchroniseer browser-native Selection met de this.selected set.
    // Probeer addRange per geselecteerde vers (Firefox toont dat als losse
    // highlights; Chrome rendert alleen de eerste range — visueel valt
    // .verse-row.verse-selected dat alsnog op via de CSS class).
    _syncBrowserSelectionToSelected() {
        const sel = window.getSelection();
        if (!sel) return;
        sel.removeAllRanges();
        const keys = [...this.selected];
        for (const key of keys) {
            const row = document.querySelector(`.verse-row[data-verse="${key}"]`);
            if (!row) continue;
            const cell = row.querySelector('.col-2026');
            if (!cell) continue;
            const range = document.createRange();
            range.selectNodeContents(cell);
            try { sel.addRange(range); } catch (e) { /* sommige browsers limiteren range-count */ }
        }
    },

    _setupSelectionToolbar() {
        let timer = null;
        document.addEventListener('selectionchange', () => {
            clearTimeout(timer);
            timer = setTimeout(() => this._handleSelectionChange(), 80);
        });
        // mousedown op toolbar mag selectie niet wissen
        const tb = document.getElementById('copy-toolbar');
        if (tb) tb.addEventListener('mousedown', (e) => e.preventDefault());
    },

    _handleSelectionChange() {
        const sel = window.getSelection();
        const tb = document.getElementById('copy-toolbar');
        if (!tb) return;
        // Als er via klik al verzen geselecteerd zijn (this.selected),
        // laat updateUI dat afhandelen — niet overrulen vanuit selectionchange.
        if (this.selected.size > 0) { tb.classList.add('visible'); return; }
        if (!sel || sel.rangeCount === 0 || !sel.toString().trim()) {
            tb.classList.remove('visible');
            return;
        }
        const versesContainer = document.getElementById('verses-container');
        const range = sel.getRangeAt(0);
        if (!versesContainer || !versesContainer.contains(range.commonAncestorContainer)) return;
        // Drag-selectie → toon "X tekens geselecteerd"
        const cnt = document.getElementById('copy-count');
        if (cnt) cnt.textContent = `${sel.toString().length} tekens geselecteerd`;
        tb.classList.add('visible');
    },

    select(key) {
        this.selected.add(key);
        const row = document.querySelector(`.verse-row[data-verse="${key}"]`);
        if (row) row.classList.add('verse-selected');
    },

    deselect(key) {
        this.selected.delete(key);
        const row = document.querySelector(`.verse-row[data-verse="${key}"]`);
        if (row) row.classList.remove('verse-selected');
    },

    toggle(key) {
        if (this.selected.has(key)) {
            this.deselect(key);
        } else {
            this.select(key);
        }
    },

    selectRange(fromKey, toKey) {
        const rows = [...document.querySelectorAll('.verse-row')];
        const fromIdx = rows.findIndex(r => r.dataset.verse === fromKey);
        const toIdx = rows.findIndex(r => r.dataset.verse === toKey);
        if (fromIdx < 0 || toIdx < 0) return;

        const start = Math.min(fromIdx, toIdx);
        const end = Math.max(fromIdx, toIdx);
        for (let i = start; i <= end; i++) {
            this.select(rows[i].dataset.verse);
        }
    },

    clearAll() {
        document.querySelectorAll('.verse-row.verse-selected').forEach(r => r.classList.remove('verse-selected'));
        this.selected.clear();
        this.updateUI();
    },

    updateUI() {
        const toolbar = document.getElementById('copy-toolbar');
        const count = this.selected.size;
        if (count > 0) {
            // Bouw "Boek H:V[-W of ,X]" label
            const nums = [...this.selected].map(n => parseInt(n)).filter(n => !isNaN(n)).sort((a,b) => a-b);
            const bookEl = document.getElementById('chapter-title');
            let bookName = '';
            if (bookEl) {
                const clone = bookEl.cloneNode(true);
                clone.querySelectorAll('.chapter-concept-tag').forEach(t => t.remove());
                bookName = clone.textContent.trim();
            }
            let ref;
            if (nums.length === 1) ref = `${bookName}:${nums[0]}`;
            else if (nums.every((n,i) => i===0 || n === nums[i-1]+1))
                ref = `${bookName}:${nums[0]}-${nums[nums.length-1]}`;
            else
                ref = `${bookName}:${nums.join(',')}`;
            document.getElementById('copy-count').textContent = `${ref} (${count} vers${count > 1 ? 'en' : ''})`;
            toolbar.classList.add('visible');
        } else {
            toolbar.classList.remove('visible');
        }
    },

    getSelectedRows() {
        // Geordend op positie in de DOM
        const rows = [...document.querySelectorAll('.verse-row')];
        return rows.filter(r => this.selected.has(r.dataset.verse));
    },

    copy(withFormatting) {
        const rows = this.getSelectedRows();
        if (rows.length === 0) return;

        // Welke kolom is de OV2026 kolom?
        const col2026 = rows.map(row => {
            const num = row.querySelector('.verse-num')?.textContent?.trim() || '';
            const cell = row.querySelector('.col-2026');
            return { num, cell };
        });

        if (withFormatting) {
            // HTML: versnummers superscript-vet, god-speaks rood+cursief met
            // aanhalingstekens, direct-speech cursief met aanhalingstekens.
            // CSS classes worden vertaald naar inline styles zodat ze in Word/
            // Mail/Outlook ook werken (die hebben onze stylesheet niet).
            const htmlParts = col2026.map(({ num, cell }) => {
                const clone = cell.cloneNode(true);
                clone.querySelectorAll('.note-marker').forEach(m => m.remove());
                clone.querySelectorAll('.strongs-inline').forEach(m => m.remove());
                // god-speaks → rode cursief tekst met „..." aanhalingstekens
                clone.querySelectorAll('.god-speaks').forEach(span => {
                    const inner = span.innerHTML;
                    const wrap = document.createElement('span');
                    wrap.setAttribute('style', 'color:#c0392b;');
                    wrap.innerHTML = '„' + inner + '”';
                    span.replaceWith(wrap);
                });
                // direct-speech → cursief met „..." aanhalingstekens
                clone.querySelectorAll('.direct-speech').forEach(span => {
                    const inner = span.innerHTML;
                    const wrap = document.createElement('em');
                    wrap.innerHTML = '„' + inner + '”';
                    span.replaceWith(wrap);
                });
                // Versnummer in superscript (i.p.v. <b> dat hele tekst vet maakt)
                return `<sup style="font-weight:600;">${num}</sup> ${clone.innerHTML.trim()}`;
            });
            const html = '<div style="font-family:Georgia,serif;line-height:1.6;">' + htmlParts.join('<br>\n') + '</div>';

            // Platte tekst als fallback
            const plain = col2026.map(({ num, cell }) => {
                const clone = cell.cloneNode(true);
                clone.querySelectorAll('.note-marker').forEach(m => m.remove());
                clone.querySelectorAll('.strongs-inline').forEach(m => m.remove());
                return `${num} ${clone.textContent.trim()}`;
            }).join('\n');

            const blob = new Blob([html], { type: 'text/html' });
            const blobPlain = new Blob([plain], { type: 'text/plain' });
            navigator.clipboard.write([
                new ClipboardItem({
                    'text/html': blob,
                    'text/plain': blobPlain
                })
            ]).then(() => this.showCopied('Met opmaak gekopieerd!'));
        } else {
            // Platte tekst
            const plain = col2026.map(({ num, cell }) => {
                const clone = cell.cloneNode(true);
                clone.querySelectorAll('.note-marker').forEach(m => m.remove());
                clone.querySelectorAll('.strongs-inline').forEach(m => m.remove());
                return `${num} ${clone.textContent.trim()}`;
            }).join('\n');

            navigator.clipboard.writeText(plain)
                .then(() => this.showCopied('Zonder opmaak gekopieerd!'));
        }
    },

    _buildRefAndText() {
        const rows = this.getSelectedRows();
        if (rows.length === 0) return null;
        const items = rows.map(row => {
            const num = row.dataset.verse;
            const cell = row.querySelector('.col-2026');
            const clone = cell ? cell.cloneNode(true) : null;
            if (clone) clone.querySelectorAll('.note-marker, .strongs-inline').forEach(m => m.remove());
            return { num, text: clone ? clone.textContent.trim().replace(/\s+/g,' ') : '', html: clone ? clone.innerHTML.trim() : '' };
        });
        // Build ref
        const nums = items.map(i => parseInt(i.num)).sort((a,b) => a-b);
        const bookEl = document.getElementById('chapter-title');
        let bookName = '';
        if (bookEl) {
            const c = bookEl.cloneNode(true);
            c.querySelectorAll('.chapter-concept-tag').forEach(t => t.remove());
            bookName = c.textContent.trim();
        }
        let ref;
        if (nums.length === 1) ref = `${bookName}:${nums[0]}`;
        else if (nums.every((n,i) => i===0 || n === nums[i-1]+1))
            ref = `${bookName}:${nums[0]}-${nums[nums.length-1]}`;
        else ref = `${bookName}:${nums.join(',')}`;
        const plain = items.map(i => `${i.num} ${i.text}`).join('\n');
        const html = items.map(i => `<b>${i.num}</b> ${i.html}`).join('<br>\n');
        return { ref, plain, html, nums, items };
    },

    async share() {
        const data = this._buildRefAndText();
        if (!data) return;
        const text = `${data.plain}\n\n— ${data.ref} (Open Staten Vertaling)`;
        if (navigator.share) {
            try { await navigator.share({ title: data.ref, text, url: location.href }); return; }
            catch (e) { if (e.name === 'AbortError') return; }
        }
        navigator.clipboard.writeText(text).then(() => this.showCopied('Tekst naar klembord (delen niet ondersteund)'));
    },

    asImage() {
        const data = this._buildRefAndText();
        if (!data) return;
        // Bouw modal als die nog niet bestaat
        let modal = document.getElementById('vers-image-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'vers-image-modal';
            modal.style.cssText = 'position:fixed;inset:0;background:rgba(20,46,66,0.7);display:none;align-items:center;justify-content:center;z-index:1000;padding:20px;';
            modal.innerHTML = `
                <div style="background:#fff;border-radius:8px;padding:18px;max-width:680px;width:92vw;max-height:92vh;overflow:auto;display:flex;flex-direction:column;align-items:center;gap:12px;">
                    <canvas id="vers-image-canvas" style="max-width:100%;height:auto;border:1px solid #e5e1d8;border-radius:6px;background:#f8f6f2;"></canvas>
                    <div style="display:flex;gap:10px;flex-wrap:wrap;justify-content:center;">
                        <button id="vers-image-download" style="background:#cba449;color:#fff;border:none;padding:9px 18px;border-radius:5px;font-weight:600;cursor:pointer;">Download als PNG</button>
                        <button id="vers-image-share" style="background:#142e42;color:#fff;border:none;padding:9px 18px;border-radius:5px;font-weight:600;cursor:pointer;">Delen</button>
                        <button id="vers-image-close" style="background:#eee;color:#333;border:none;padding:9px 18px;border-radius:5px;font-weight:600;cursor:pointer;">Sluiten</button>
                    </div>
                </div>`;
            document.body.appendChild(modal);
            modal.addEventListener('click', (e) => { if (e.target === modal) modal.style.display = 'none'; });
            document.getElementById('vers-image-close').addEventListener('click', () => modal.style.display = 'none');
            document.getElementById('vers-image-download').addEventListener('click', () => {
                const canvas = document.getElementById('vers-image-canvas');
                const a = document.createElement('a');
                a.download = (this._lastRef || 'vers').replace(/[^a-zA-Z0-9-]+/g, '_') + '.png';
                a.href = canvas.toDataURL('image/png');
                a.click();
            });
            document.getElementById('vers-image-share').addEventListener('click', () => {
                const canvas = document.getElementById('vers-image-canvas');
                canvas.toBlob(async (blob) => {
                    if (navigator.share && navigator.canShare && navigator.canShare({ files: [new File([blob],'vers.png',{type:'image/png'})] })) {
                        try { await navigator.share({ title: this._lastRef, files: [new File([blob], 'vers.png', { type: 'image/png' })] }); } catch (e) {}
                    } else {
                        const a = document.createElement('a'); a.download = 'vers.png'; a.href = canvas.toDataURL('image/png'); a.click();
                    }
                }, 'image/png');
            });
        }
        this._lastRef = data.ref;
        // Render canvas
        const canvas = document.getElementById('vers-image-canvas');
        const W = 1200, PAD = 80;
        canvas.width = W; canvas.height = 1600;
        const ctx = canvas.getContext('2d');
        const grad = ctx.createLinearGradient(0,0,0,canvas.height);
        grad.addColorStop(0,'#f8f4ec'); grad.addColorStop(1,'#ede4d0');
        ctx.fillStyle = grad; ctx.fillRect(0,0,W,canvas.height);
        ctx.fillStyle = '#cba449'; ctx.fillRect(0,0,8,canvas.height);
        ctx.textBaseline = 'top';
        const wrap = (text,maxW,lineH,x,y) => {
            const words = text.split(' '); let line = '';
            for (const w of words) {
                const test = line ? line+' '+w : w;
                if (ctx.measureText(test).width > maxW && line) { ctx.fillText(line,x,y); y += lineH; line = w; }
                else line = test;
            }
            if (line) { ctx.fillText(line,x,y); y += lineH; }
            return y;
        };
        let y = PAD;
        for (const it of data.items) {
            ctx.font = 'bold 28px Georgia, serif'; ctx.fillStyle = '#cba449';
            ctx.fillText(it.num, PAD, y + 6);
            ctx.font = '36px Georgia, "EB Garamond", serif'; ctx.fillStyle = '#142e42';
            y = wrap(it.text, W - PAD*2 - 60, 50, PAD + 60, y);
            y += 18;
        }
        y += 20;
        ctx.font = 'italic 26px Georgia, serif'; ctx.fillStyle = '#5a7a8a';
        ctx.fillText(`— ${data.ref}`, PAD, y); y += 38;
        ctx.font = '18px "Fira Sans", sans-serif'; ctx.fillStyle = '#999';
        ctx.fillText('Open Staten Vertaling · openvertaling.nl', PAD, y); y += 30;
        const finalH = Math.max(y + PAD, 400);
        const tmp = document.createElement('canvas'); tmp.width = W; tmp.height = finalH;
        tmp.getContext('2d').drawImage(canvas, 0, 0);
        canvas.width = W; canvas.height = finalH;
        canvas.getContext('2d').drawImage(tmp, 0, 0);
        modal.style.display = 'flex';
    },

    showCopied(msg) {
        const toolbar = document.getElementById('copy-toolbar');
        const countEl = document.getElementById('copy-count');
        const orig = countEl.textContent;
        countEl.textContent = msg;
        countEl.style.color = '#27ae60';
        setTimeout(() => {
            countEl.textContent = orig;
            countEl.style.color = '';
        }, 1500);
    }
};

document.addEventListener('DOMContentLoaded', () => VerseSelect.init());
