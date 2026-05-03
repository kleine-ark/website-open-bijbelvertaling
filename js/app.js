/* Open Vertaling — Hoofdapplicatie */

const App = {
    // Alle kolom-keys in volgorde (num is altijd zichtbaar)
    ALL_COLS: ['1637', 'margin1637', 'sv1888', 'marginSV1888', '2026', 'margin2026', 'hebrew', 'diff', 'noteDiff'],

    /**
     * Voeg Strong's nummers inline toe aan de OV2026 tekst.
     * Strategie: wijs elk grondtekst-woord sequentieel toe aan de
     * woorden in de Nederlandse tekst. HTML-tags worden overgeslagen.
     * Grondtekst-entries zonder strongs worden overgeslagen.
     */
    addInlineStrongs(htmlText, grondtekst) {
        if (!htmlText || !grondtekst || grondtekst.length === 0) return htmlText;

        // Verzamel Strong's nummers in volgorde (sla lege/particle-only over)
        const strongsEntries = grondtekst.filter(w => w.strongs);

        // Splits de HTML-tekst in tokens: HTML-tags vs tekst-segmenten
        // We matchen HTML tags, of runs van niet-tag tekst
        const tokenRegex = /(<[^>]+>)|([^<]+)/g;
        let match;
        const tokens = [];
        while ((match = tokenRegex.exec(htmlText)) !== null) {
            if (match[1]) {
                // HTML tag — bewaar ongewijzigd
                tokens.push({ type: 'tag', value: match[1] });
            } else if (match[2]) {
                // Tekst segment
                tokens.push({ type: 'text', value: match[2] });
            }
        }

        // Loop door teksttokens en splits in woorden; wijs Strong's toe
        let strongsIdx = 0;
        const result = [];

        for (const token of tokens) {
            if (token.type === 'tag') {
                result.push(token.value);
                continue;
            }
            // Splits tekst in woorden en niet-woord stukken (spaties, leestekens)
            const parts = token.value.split(/(\s+)/);
            for (const part of parts) {
                // Check of dit een echt woord is (bevat minstens één letter)
                if (/[a-zA-ZàáâãäåèéêëìíîïòóôõöùúûüýÿæœÀ-ÖØ-öø-ÿ]/.test(part) && strongsIdx < strongsEntries.length) {
                    const entry = strongsEntries[strongsIdx];
                    const title = entry.gloss ? entry.gloss.replace(/[〔〕]/g, '') : entry.woord || '';
                    result.push(part + `<sup class="strongs-inline" title="${title}">${entry.strongs}</sup>`);
                    strongsIdx++;
                } else {
                    result.push(part);
                }
            }
        }

        return result.join('');
    },
    // Kolom-breedtes: gelijk verdeeld
    // Hoofdstukken met voorlezing-audio (audio/{book}/{ch}.mp3)
    AUDIO_AVAILABLE: {
        genesis: [1],
        johannes: [1],
    },

    // Hoofdstukken die handmatig vers-voor-vers zijn nagelopen.
    // Voor andere hoofdstukken: AI-concept-banner tonen.
    VERIFIED_CHAPTERS: {
        genesis:    [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20],
        psalmen:    [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30],
        johannes:   'all',
        handelingen:[1,2,3,4,5,6,7,8],
        romeinen:   [1],
        filemon:    'all',
        judas:      'all',
    },

    _isVerified(bookId, chapter) {
        const v = App.VERIFIED_CHAPTERS[bookId];
        if (!v) return false;
        if (v === 'all') return true;
        return Array.isArray(v) && v.includes(chapter);
    },

    _updateVerifiedBanner(bookId, chapter) {
        let banner = document.getElementById('ai-concept-banner');
        if (App._isVerified(bookId, chapter)) {
            if (banner) banner.style.display = 'none';
            return;
        }
        if (!banner) {
            banner = document.createElement('div');
            banner.id = 'ai-concept-banner';
            banner.className = 'ai-concept-banner';
            banner.innerHTML = '<strong>⚠ Let op:</strong> AI-wijzigingen. Concept. Nog geen menselijke controle plaatsgevonden — kans op nog niet opgeloste onjuistheden.';
            const container = document.getElementById('verses-container');
            if (container && container.parentNode) container.parentNode.insertBefore(banner, container);
        }
        banner.style.display = 'block';
    },

    _updateAudioPlayer(bookId, chapter) {
        const playBtn = document.getElementById('audio-play-big');
        const playMob = document.getElementById('audio-play-mobile');
        const speedBtn = document.getElementById('audio-speed');
        const speedMob = document.getElementById('audio-speed-mobile');
        const scrubWrap = document.getElementById('audio-scrubber-wrap');
        const audioEl = document.getElementById('audio-el');
        if (!audioEl) return;
        try { audioEl.pause(); } catch (e) {}
        const list = App.AUDIO_AVAILABLE[bookId] || [];
        const show = list.includes(chapter);
        const setHidden = (el, hide) => { if (el) el.classList.toggle('hidden', hide); };
        setHidden(playBtn, !show);
        setHidden(playMob, !show);
        setHidden(speedBtn, !show);
        setHidden(speedMob, !show);
        setHidden(scrubWrap, !show);
        if (!show) { audioEl.removeAttribute('src'); return; }
        audioEl.src = `audio/${bookId}/${chapter}.mp3`;
        if (playBtn) playBtn.classList.remove('is-playing');
        if (playMob) playMob.classList.remove('is-playing');
        // Reset scrubber
        const scrubber = document.getElementById('audio-scrubber');
        const cur = document.getElementById('audio-time-cur');
        const tot = document.getElementById('audio-time-tot');
        if (scrubber) scrubber.value = 0;
        if (cur) cur.textContent = '0:00';
        if (tot) tot.textContent = '0:00';
    },

    _setupAudioPlayer() {
        const audioEl = document.getElementById('audio-el');
        const playBtn = document.getElementById('audio-play-big');
        const playMob = document.getElementById('audio-play-mobile');
        const speedBtn = document.getElementById('audio-speed');
        const speedMob = document.getElementById('audio-speed-mobile');
        const scrubber = document.getElementById('audio-scrubber');
        const curEl = document.getElementById('audio-time-cur');
        const totEl = document.getElementById('audio-time-tot');
        if (!audioEl || (!playBtn && !playMob)) return;
        if (audioEl._wired) return;
        audioEl._wired = true;

        const fmt = (sec) => {
            if (!isFinite(sec) || sec < 0) return '0:00';
            const m = Math.floor(sec / 60), s = Math.floor(sec % 60);
            return `${m}:${s.toString().padStart(2, '0')}`;
        };

        // Play / pause — beide knoppen (desktop + mobile) wirelinen
        const togglePlay = () => {
            if (audioEl.paused) audioEl.play();
            else audioEl.pause();
        };
        if (playBtn) playBtn.addEventListener('click', togglePlay);
        if (playMob) playMob.addEventListener('click', togglePlay);
        audioEl.addEventListener('play', () => {
            if (playBtn) playBtn.classList.add('is-playing');
            if (playMob) playMob.classList.add('is-playing');
        });
        audioEl.addEventListener('pause', () => {
            if (playBtn) playBtn.classList.remove('is-playing');
            if (playMob) playMob.classList.remove('is-playing');
        });

        // Snelheid: 1× → 1.25× → 1.5× → 2× → 0.75× → 1× (gedeeld tussen desktop + mobile)
        const cycle = [1, 1.25, 1.5, 2, 0.75];
        let idx = 0;
        const cycleSpeed = () => {
            idx = (idx + 1) % cycle.length;
            audioEl.playbackRate = cycle[idx];
            const lbl = cycle[idx] + '×';
            if (speedBtn) speedBtn.textContent = lbl;
            if (speedMob) speedMob.textContent = lbl;
        };
        if (speedBtn) speedBtn.addEventListener('click', cycleSpeed);
        if (speedMob) speedMob.addEventListener('click', cycleSpeed);

        // Scrubber: doorspoelen + tijd-display
        if (scrubber) {
            audioEl.addEventListener('loadedmetadata', () => {
                scrubber.max = audioEl.duration || 0;
                if (totEl) totEl.textContent = fmt(audioEl.duration);
            });
            audioEl.addEventListener('timeupdate', () => {
                if (!scrubber._dragging) {
                    scrubber.value = audioEl.currentTime;
                    if (curEl) curEl.textContent = fmt(audioEl.currentTime);
                }
            });
            scrubber.addEventListener('input', () => {
                scrubber._dragging = true;
                if (curEl) curEl.textContent = fmt(parseFloat(scrubber.value));
            });
            scrubber.addEventListener('change', () => {
                audioEl.currentTime = parseFloat(scrubber.value);
                scrubber._dragging = false;
            });
        }
    },

    COL_WIDTHS: {
        // minmax(0, 1fr) i.p.v. '1fr' zodat lange content een kolom niet
        // breder duwt dan zijn helft — bij 2 zichtbare kolommen wordt het echt 50/50.
        '1637': 'minmax(0, 1fr)', 'margin1637': 'minmax(0, 1fr)',
        'sv1888': 'minmax(0, 1fr)', 'marginSV1888': 'minmax(0, 1fr)',
        '2026': 'minmax(0, 1fr)', 'margin2026': 'minmax(0, 1fr)',
        'nbg51': 'minmax(0, 1fr)', 'hsv': 'minmax(0, 1fr)',
        'hebrew': 'minmax(0, 1fr)', 'diff': 'minmax(0, 1fr)', 'noteDiff': 'minmax(0, 1fr)'
    },

    async init() {
        Navigation.init();
        Editor.init();
        Lexicon.init();
        References.init();
        this.initColumnToggles();
        ColumnReorder.init();
        ColumnResize.init();
        Sidebar.init();

        await Navigation.renderBookNav();
        await Sidebar.renderTree();

        // Audio play-knop in chapter-footer wirelinen
        App._setupAudioPlayer();

        // Strong's toggle (optioneel — checkbox is verwijderd uit Opties)
        const strongsCb = document.getElementById('toggle-strongs');
        if (strongsCb) {
            strongsCb.addEventListener('change', () => {
                if (Navigation.currentBook && Navigation.currentChapter) {
                    App.renderChapter(Navigation.currentBook, Navigation.currentChapter);
                }
            });
        }
        // Begrippen-default: als checkbox checked is bij load → meteen activeren
        setTimeout(() => {
            const begrCb = document.getElementById('toggle-begrippen') || document.getElementById('quick-begrippen');
            if (begrCb && begrCb.checked && window.Begrippen) {
                Begrippen.toggle(true);
            }
        }, 200);

        // Toolbar knoppen
        document.getElementById('btn-save').addEventListener('click', () => Editor.saveAll());
        document.getElementById('btn-export').addEventListener('click', () => {
            if (Navigation.currentBook) {
                ExportImport.exportBook(Navigation.currentBook);
            }
        });
        document.getElementById('btn-export-edits').addEventListener('click', () => {
            ExportImport.exportAllEdits();
        });
        document.getElementById('btn-import').addEventListener('click', () => {
            ExportImport.importEdits();
        });
        document.getElementById('btn-approve').addEventListener('click', () => {
            if (!Navigation.currentBook || !Navigation.currentChapter) {
                alert('Selecteer eerst een hoofdstuk.');
                return;
            }
            const book = DataLoader.cache[Navigation.currentBook];
            const name = book ? book.nameDutch : Navigation.currentBook;
            if (confirm(`Weet u zeker dat u ${name} ${Navigation.currentChapter} als definitief wilt goedkeuren?\n\nAlle verzen worden op status "definitief" gezet en het hoofdstuk wordt als JSON gedownload.`)) {
                ExportImport.approveChapter(Navigation.currentBook, Navigation.currentChapter);
            }
        });
        document.getElementById('btn-reset').addEventListener('click', () => {
            if (confirm('Weet u zeker dat u alle lokale bewerkingen wilt wissen? De data wordt opnieuw geladen vanuit de JSON-bestanden.')) {
                Storage.clearAll();
                DataLoader.cache = {};
                location.reload();
            }
        });

        // Laad vanuit URL hash of default
        if (location.hash) {
            await Navigation.handleHash();
        } else {
            // Trigger default
            Navigation.handleHash();
        }
    },

    async renderChapter(bookId, chapterNum) {
        // Manifest (klein) + chapter (klein) parallel
        const [book, chapter] = await Promise.all([
            DataLoader.loadBook(bookId),                      // bouwt lazy book-object
            DataLoader.loadChapter(bookId, chapterNum),       // alleen huidige chapter
        ]);
        if (!book) {
            document.getElementById('verses-container').innerHTML = '<p>Boek niet gevonden.</p>';
            return;
        }
        if (!chapter) {
            document.getElementById('verses-container').innerHTML = '<p>Hoofdstuk niet gevonden.</p>';
            return;
        }
        // Pre-fetch buurchapters bij idle (volgende klik = instant)
        DataLoader.prefetchAdjacent(bookId, chapterNum);

        // Titel
        document.getElementById('chapter-title').textContent =
            `${book.nameDutch} ${chapterNum}`;
        // Chapter-footer label (sticky onderaan)
        const chfLabel = document.getElementById('chapter-footer-label');
        if (chfLabel) {
            const total = (book.chapters && book.chapters.length) || (book.chaptersIncluded && book.chaptersIncluded.length) || 0;
            chfLabel.textContent = total ? `${book.nameDutch} ${chapterNum} / ${total}` : `${book.nameDutch} ${chapterNum}`;
        }
        // Audio play-knop tonen voor hoofdstukken met voorlezing
        App._updateAudioPlayer(bookId, chapterNum);
        // AI-concept-banner tonen voor niet-geverifieerde hoofdstukken
        App._updateVerifiedBanner(bookId, chapterNum);

        // Boekinleiding (alleen bij hoofdstuk 1)
        const bookIntroEl = document.getElementById('book-intro');
        if (chapterNum === 1 && book.bookIntro) {
            const introText = book.bookIntro.text2026 || book.bookIntro.text1637 || '';
            if (introText) {
                bookIntroEl.innerHTML = '<span class="book-intro-label">Boekinleiding:</span>' + introText;
                bookIntroEl.style.display = 'block';
                bookIntroEl.classList.remove('expanded');
                bookIntroEl.onclick = () => bookIntroEl.classList.toggle('expanded');
            } else {
                bookIntroEl.style.display = 'none';
            }
        } else {
            bookIntroEl.style.display = 'none';
        }

        // Hoofdstuk inleiding
        const introEl = document.getElementById('chapter-intro');
        if (chapter.chapterIntro && (chapter.chapterIntro.text2026 || chapter.chapterIntro.text1637)) {
            introEl.textContent = chapter.chapterIntro.text2026 || chapter.chapterIntro.text1637;
            introEl.style.display = 'block';
            introEl.classList.remove('expanded');
            introEl.onclick = () => introEl.classList.toggle('expanded');
        } else {
            introEl.style.display = 'none';
        }

        // Verzen renderen
        const container = document.getElementById('verses-container');
        container.innerHTML = '';

        for (const verse of chapter.verses) {
            const row = document.createElement('div');
            row.className = 'verse-row';
            row.dataset.status = verse.status || 'empty';
            row.dataset.book = bookId;
            row.dataset.chapter = chapterNum;
            row.dataset.verse = verse.number;

            // Hebreeuws/Grieks kolom — klikbare woorden met Strong's
            const showStrongs = document.getElementById('toggle-strongs') && document.getElementById('toggle-strongs').checked;
            let hebrewHtml;
            if (verse.grondtekst && verse.grondtekst.length > 0) {
                const words = verse.grondtekst.map(w => {
                    const translit = w.transliteratie || '';
                    const gloss = w.gloss || '';
                    return `<span class="strongs-word" data-strongs="${w.strongs}" data-transliteratie="${translit}" data-gloss="${gloss}">${w.woord}<br><span class="strongs-sub">${w.strongs}</span></span>`;
                }).join(' ');
                hebrewHtml = `<span class="hebrew-text">${words}</span>`;
                if (verse.hebrewMeaning) {
                    hebrewHtml += `<span class="hebrew-meaning">${verse.hebrewMeaning}</span>`;
                }
            } else if (verse.hebrew) {
                hebrewHtml = `<span class="hebrew-text">${verse.hebrew}</span><span class="hebrew-meaning">${verse.hebrewMeaning || ''}</span>`;
            } else {
                hebrewHtml = '<span style="color:#bbb;font-style:italic;direction:ltr;font-size:12px">—</span>';
            }

            // Open Vertaling: gebruik text2026_html (met inline nootcijfers) als die er is,
            // anders text2026 of textHerzien als platte tekst
            let openVertaling = verse.text2026_html || verse.text2026 || verse.textHerzien || '';
            // Pas vertalingsopties toe (Godsnaam etc.) — alleen tekst, niet HTML-tags
            if (typeof Opties !== 'undefined') openVertaling = Opties.transformOV(openVertaling);

            // Strong's nummers inline bij SV1888 en OV tekst
            let sv1888Text = verse.textSV1888_html || verse.textSV1888 || '';
            if (showStrongs && verse.grondtekst && verse.grondtekst.length > 0) {
                // OV2026: voeg Strong's nummers inline toe na elk woord
                openVertaling = this.addInlineStrongs(openVertaling, verse.grondtekst);

                // SV1888: toon Strong's als rij onder de tekst (bestaand gedrag)
                const strongsList = verse.grondtekst
                    .filter(w => w.strongs)
                    .map(w => {
                        const title = w.gloss ? w.gloss.replace(/[〔〕]/g, '') : w.woord || '';
                        return `<span class="strongs-inline" title="${title}">${w.strongs}</span>`;
                    })
                    .join(' ');
                if (strongsList) {
                    sv1888Text += `<div class="strongs-row">${strongsList}</div>`;
                }
            }

            // Diff-kolom: toon phrase-level wijzigingen als "oud → nieuw"
            let diffHtml = '';
            if (verse.phraseDiff && verse.phraseDiff.length > 0) {
                diffHtml = verse.phraseDiff.map(d => {
                    const badge = d.principe ? `<a class="principe-badge cat-${d.principe[0]}" href="principes.html#${d.principe}" title="${d.principe}">${d.principe}</a>` : '';
                    const escOld = (d.old || '').replace(/'/g, "\\'");
                    const escNew = (d.new || '').replace(/'/g, "\\'");
                    const escPrincipe = (d.principe || '').replace(/'/g, "\\'");
                    const undoBtn = `<button class="undo-diff-btn" title="Uitzondering maken" onclick="undoDiff('${bookId}', ${chapterNum}, ${verse.number}, '${escPrincipe}', '${escOld}', '${escNew}')">✕</button>`;
                    if (d.old && d.new) {
                        return `<span class="diff-change">${badge}${undoBtn}<span class="diff-old">${d.old}</span> → <span class="diff-new">${d.new}</span></span>`;
                    } else if (d.new) {
                        return `<span class="diff-added">${badge}${undoBtn}+ ${d.new}</span>`;
                    } else if (d.old) {
                        return `<span class="diff-removed">${badge}${undoBtn}− ${d.old}</span>`;
                    }
                    return '';
                }).join('');
            }

            // Kanttekeningen 1637 (alleen-lezen)
            let margin1637Html = '';
            if (verse.marginNotes && verse.marginNotes.length > 0) {
                margin1637Html = verse.marginNotes.map(n =>
                    `<div class="note-item"><span class="note-marker-label">${n.marker}</span><span class="note-type-label">${n.type === 'crossref' ? 'kruisverw.' : ''}</span> ${References.linkify(n.text1637, bookId, chapterNum)}</div>`
                ).join('');
            } else {
                margin1637Html = '<span style="color:#bbb;font-style:italic;font-size:12px">—</span>';
            }

            // Kanttekeningen hertaald (bewerkbaar per noot)
            let margin2026Html = '';
            if (verse.marginNotes && verse.marginNotes.length > 0) {
                margin2026Html = verse.marginNotes.map((n, i) => {
                    const linkedText = n.text2026 ? References.linkify(n.text2026, bookId, chapterNum) : '';
                    return `<div class="note-item"><span class="note-marker-label">${n.marker}</span> <span class="margin-note-edit">${linkedText}</span></div>`;
                }).join('');
            } else {
                margin2026Html = '<span style="color:#bbb;font-style:italic;font-size:12px">—</span>';
            }

            // SV2000.net kanttekeningen (alleen-lezen)
            let marginSV1888Html = '';
            if (verse.marginNotes && verse.marginNotes.length > 0) {
                const sv2000Notes = verse.marginNotes.filter(n => n.textSV1888);
                if (sv2000Notes.length > 0) {
                    marginSV1888Html = sv2000Notes.map(n =>
                        `<div class="note-item"><span class="note-marker-label">${n.marker}</span> ${n.textSV1888}</div>`
                    ).join('');
                } else {
                    marginSV1888Html = '<span style="color:#bbb;font-style:italic;font-size:12px">—</span>';
                }
            } else {
                marginSV1888Html = '<span style="color:#bbb;font-style:italic;font-size:12px">—</span>';
            }

            // Kanttekening diff (SV1888 vs OV2026)
            let noteDiffHtml = '';
            if (verse.marginNotes && verse.marginNotes.length > 0) {
                const noteDiffs = verse.marginNotes.filter(n => n.noteDiff && n.noteDiff.length > 0);
                if (noteDiffs.length > 0) {
                    noteDiffHtml = noteDiffs.map(n => {
                        const changes = n.noteDiff.map(d => {
                            const badge = d.principe ? `<a class="principe-badge cat-${d.principe[0]}" href="principes.html#${d.principe}" title="${d.principe}">${d.principe}</a>` : '';
                            if (d.old && d.new) {
                                return `<span class="diff-change">${badge}<span class="diff-old">${d.old}</span> → <span class="diff-new">${d.new}</span></span>`;
                            } else if (d.new) {
                                return `<span class="diff-added">${badge}+ ${d.new}</span>`;
                            } else if (d.old) {
                                return `<span class="diff-removed">${badge}− ${d.old}</span>`;
                            }
                            return '';
                        }).join(' ');
                        return `<div class="note-item"><span class="note-marker-label">${n.marker}</span> ${changes}</div>`;
                    }).join('');
                }
            }

            row.innerHTML = `
                <div class="verse-num" data-col="num" title="Klik voor status">${verse.number}</div>
                <div class="verse-cell col-1637" data-col="1637">${verse.text1637_html || verse.text1637}</div>
                <div class="verse-cell col-margin1637" data-col="margin1637">${margin1637Html}</div>
                <div class="verse-cell col-sv1888" data-col="sv1888">${sv1888Text}</div>
                <div class="verse-cell col-marginSV1888" data-col="marginSV1888">${marginSV1888Html}</div>
                <div class="verse-cell col-2026" data-col="2026">${openVertaling}</div>
                <div class="verse-cell col-margin2026" data-col="margin2026">${margin2026Html}</div>
                <div class="verse-cell col-hebrew" data-col="hebrew">${hebrewHtml}</div>
                <div class="verse-cell col-diff" data-col="diff">${diffHtml}</div>
                <div class="verse-cell col-noteDiff" data-col="noteDiff">${noteDiffHtml}</div>
            `;

            container.appendChild(row);
            Editor.attachVerseListeners(row, bookId, chapterNum, verse.number);
            // Rechtermuisknop op versnummer = tag toevoegen
            row.querySelector('.verse-num').addEventListener('contextmenu', (e) => {
                e.preventDefault();
                if (typeof Tags !== 'undefined') {
                    Tags.showAddTagPopup(bookId, chapterNum, verse.number, e.target);
                }
            });
        }

        this.updateProgress();
        this.updateGrid();
        // Pas kolomvolgorde toe op nieuwe rijen
        if (typeof ColumnReorder !== 'undefined') ColumnReorder.reorderDOM();
        if (typeof updateStickyOffset === 'function') updateStickyOffset();
        // Tags tonen bij verzen
        if (typeof Tags !== 'undefined') Tags.renderTagsForChapter(bookId, chapterNum);
        // Begrippen herladen bij boekwisseling — eerst checkbox-state synchroniseren
        if (typeof Begrippen !== 'undefined') {
            const begrCb = document.getElementById('toggle-begrippen') || document.getElementById('quick-begrippen');
            if (begrCb && begrCb.checked) Begrippen.active = true;
            Begrippen.reload(bookId);
        }
        // Highlights toepassen op nieuwe rijen
        if (typeof Highlight !== 'undefined') Highlight.applyToChapter(bookId, chapterNum);
    },

    updateProgress() {
        const rows = document.querySelectorAll('.verse-row');
        if (rows.length === 0) return;

        let counts = { empty: 0, draft: 0, review: 0, final: 0 };
        rows.forEach(r => {
            const s = r.dataset.status || 'empty';
            if (counts[s] !== undefined) counts[s]++;
        });

        const total = rows.length;
        const done = counts.final;
        const pct = Math.round((done / total) * 100);

        document.getElementById('progress-fill').style.width = pct + '%';
        document.getElementById('progress-text').textContent =
            `${done}/${total} definitief (${counts.draft} concept, ${counts.review} review)`;
    },

    // === Kolom-toggle logica ===
    initColumnToggles() {
        const content = document.getElementById('content');
        const saved = localStorage.getItem('sv2026_columnVisibility');
        let visibility = saved ? JSON.parse(saved) : null;

        // Defaults: 1637, 2026, margin1637, margin2026 aan; rest uit
        if (!visibility) {
            visibility = {};
            this.ALL_COLS.forEach(col => {
                const cb = document.querySelector(`[data-toggle-col="${col}"]`);
                visibility[col] = cb ? cb.checked : false;
            });
        }

        // Pas checkboxes en classes toe
        this.ALL_COLS.forEach(col => {
            const cb = document.querySelector(`[data-toggle-col="${col}"]`);
            if (!cb) return;
            const visible = visibility[col] !== undefined ? visibility[col] : cb.checked;
            cb.checked = visible;
            content.classList.toggle(`hide-${col}`, !visible);
        });

        this.updateGrid();

        // Luister naar veranderingen
        // Luister op zowel oude topbar-wrapper als nieuwe rechter sidebar
        document.addEventListener('change', (e) => {
            const cb = e.target;
            if (!cb.dataset || !cb.dataset.toggleCol) return;
            const col = cb.dataset.toggleCol;
            content.classList.toggle(`hide-${col}`, !cb.checked);

            // Sla op
            const vis = {};
            this.ALL_COLS.forEach(c => {
                const box = document.querySelector(`[data-toggle-col="${c}"]`);
                vis[c] = box ? box.checked : false;
            });
            localStorage.setItem('sv2026_columnVisibility', JSON.stringify(vis));

            this.updateGrid();
            updateStickyOffset();
        });
    },

    updateGrid() {
        // Check leesmodus: alleen OV2026 aan
        const content = document.getElementById('content');
        const activeCols = this.ALL_COLS.filter(col => {
            const cb = document.querySelector(`[data-toggle-col="${col}"]`);
            return cb && cb.checked;
        });
        // Leesmodus: altijd aan (geen lelijke tabelstructuur)
        if (content) content.classList.add('reading-mode');

        // Gebruik ColumnResize als die geladen is (heeft custom widths)
        if (typeof ColumnResize !== 'undefined') {
            ColumnResize.applyWidths();
            ColumnResize.addResizeHandles();
            return;
        }
        // Fallback: standaard breedtes
        const parts = ['40px'];
        this.ALL_COLS.forEach(col => {
            const cb = document.querySelector(`[data-toggle-col="${col}"]`);
            if (cb && cb.checked) {
                parts.push(this.COL_WIDTHS[col] || '1fr');
            }
        });
        const template = parts.join(' ');

        const headers = document.querySelector('.column-headers');
        if (headers) headers.style.gridTemplateColumns = template;

        document.querySelectorAll('.verse-row').forEach(row => {
            row.style.gridTemplateColumns = template;
        });
    }
};

// Stel column-headers sticky offset in op basis van header-hoogte
function updateStickyOffset() {
    const topnav = document.getElementById('topnav');
    const header = document.getElementById('app-header');
    const topbar = document.getElementById('content-topbar');
    const colHeaders = document.querySelector('.column-headers');
    const navH = topnav ? topnav.offsetHeight : 0;
    if (header) header.style.top = navH + 'px';
    const headerH = header ? header.offsetHeight : 0;
    // app-header is leeg op tekstpagina → vaak height 0
    if (topbar) topbar.style.top = (navH + headerH) + 'px';
    if (colHeaders) {
        const topbarH = topbar ? topbar.offsetHeight : 0;
        colHeaders.style.top = (navH + headerH + topbarH) + 'px';
    }
}

// Uitzondering: wijziging ongedaan maken via server
async function undoDiff(boek, hoofdstuk, vers, principe, oud, nieuw) {
    if (!confirm(`Wijziging "${oud} → ${nieuw}" ongedaan maken?`)) return;
    const resp = await fetch('/api/uitzondering', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({boek, hoofdstuk, vers, principe, oud, nieuw, actie: 'undo'})
    });
    if (resp.ok) {
        // Cache wissen zodat data opnieuw geladen wordt
        if (typeof DataLoader !== 'undefined') delete DataLoader.cache[boek];
        location.reload();
    } else {
        alert('Fout bij ongedaan maken van wijziging.');
    }
}

// Start de applicatie
document.addEventListener('DOMContentLoaded', () => {
    App.init();
    if (typeof Opties !== 'undefined') Opties.init();
    setTimeout(updateStickyOffset, 100);
    window.addEventListener('resize', updateStickyOffset);

    // Sluit dropdown bij klik buiten
    document.addEventListener('click', (e) => {
        const wrapper = document.getElementById('column-toggles-wrapper');
        if (wrapper && !wrapper.contains(e.target)) {
            document.getElementById('columns-dropdown')?.classList.remove('open');
        }
    });
});

// Hamburger menu: sluit bij klik buiten
document.addEventListener('click', (e) => {
    const links = document.getElementById('topnav-links');
    const hamburger = document.getElementById('topnav-hamburger');
    if (!links || !hamburger) return;
    if (!links.contains(e.target) && !hamburger.contains(e.target)) {
        links.classList.remove('open');
        hamburger.classList.remove('open');
    }
});
