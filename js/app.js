/* Open Staten Vertaling — Hoofdapplicatie */

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
    // AUDIO_AVAILABLE leeft in js/audio-available.js (window.AUDIO_AVAILABLE) —
    // niet hier definieren. Wordt door de TTS-rollout-script bijgewerkt.

    // Hoofdstukken die handmatig vers-voor-vers zijn nagelopen.
    // Voor andere hoofdstukken: AI-concept-banner tonen.
    VERIFIED_CHAPTERS: {
        genesis:    [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20],
        psalmen:    'all',
        johannes:   'all',
        handelingen:[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16],
        markus:     [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16],
        romeinen:   [1,2,3,4],
        '1johannes':'all',
        '2johannes':'all',
        '3johannes':'all',
        efeziers:   'all',
        gebedvanmanasse:'all',
        filemon:    'all',
        judas:      'all',
        baruch:     'all',
        jakobus:    'all',
        '1makkabeeen': 'all',
        susanna:    'all',
        ezra:       'all',
        filippenzen:'all',
        titus:      'all',
        kolossenzen:'all',
        mattheus:   'all',
        lukas:      [1,2,3,4,5,6,7,8,9,10,11],
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
        const scrubMob = document.getElementById('audio-scrubber-mobile');
        const audioEl = document.getElementById('audio-el');
        // Containers ook hide-en zodat ze geen ruimte innemen op hoofdstukken zonder audio
        const chfCenter = playBtn ? playBtn.closest('.chf-center') : null;
        const mfnAudio = playMob ? playMob.closest('.mfn-audio') : null;
        const voiceBtn = document.getElementById('audio-voice');
        const voiceMob = document.getElementById('audio-voice-mobile');
        if (!audioEl) return;
        try { audioEl.pause(); } catch (e) {}

        // Onthoud huidig hoofdstuk voor de stem-toggle
        App._audioBookId = bookId;
        App._audioChapter = chapter;

        const ov = window.OV_AUDIO;
        const show = !!(ov && ov.available(bookId, chapter));
        const setHidden = (el, hide) => { if (el) el.classList.toggle('hidden', hide); };
        setHidden(playBtn, !show);
        setHidden(playMob, !show);
        setHidden(speedBtn, !show);
        setHidden(speedMob, !show);
        setHidden(scrubWrap, !show);
        setHidden(scrubMob, !show);
        setHidden(chfCenter, !show);
        setHidden(mfnAudio, !show);
        setHidden(voiceBtn, !show);
        setHidden(voiceMob, !show);
        if (!show) { audioEl.removeAttribute('src'); App._autoplayNext = false; return; }
        audioEl.src = ov.src(bookId, chapter);
        // Auto-doorspelen: na 'ended' navigeren we naar het volgende hoofdstuk;
        // zodra dat fragment geladen is, meteen verder afspelen.
        if (App._autoplayNext) {
            App._autoplayNext = false;
            audioEl.addEventListener('loadedmetadata', function once() {
                audioEl.removeEventListener('loadedmetadata', once);
                App._announceThenPlay(audioEl, chapter);
            });
        }
        if (voiceBtn) voiceBtn.textContent = ov.label();
        if (voiceMob) voiceMob.textContent = ov.label();
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

    // Kondig "Hoofdstuk N" aan en start daarna de voorlezing.
    // Voorkeur: een vooraf gegenereerde clip in DEZELFDE stem
    // (audio/_announce/{m|v}/{n}.mp3). Niet aanwezig → browser-spraak als fallback.
    _announceThenPlay(audioEl, chapter) {
        const start = () => { try { audioEl.play().catch(() => {}); } catch (e) {} };
        if (chapter == null) { start(); return; }
        const voice = (window.OV_AUDIO && OV_AUDIO.getVoice) ? OV_AUDIO.getVoice() : 'v';
        let done = false;
        const once = (fn) => { if (!done) { done = true; fn(); } };
        try {
            const clip = new Audio(`audio/_announce/${voice}/${chapter}.mp3`);
            clip.addEventListener('ended', () => once(start));
            clip.addEventListener('error', () => once(() => App._announceTTS(chapter, start)));
            clip.play().catch(() => once(() => App._announceTTS(chapter, start)));
        } catch (e) {
            once(() => App._announceTTS(chapter, start));
        }
    },

    // Fallback: spreek "Hoofdstuk N" uit via de browser-spraak, dan callback.
    _announceTTS(chapter, then) {
        let started = false;
        const go = () => { if (!started) { started = true; then(); } };
        try {
            const synth = window.speechSynthesis;
            if (synth && window.SpeechSynthesisUtterance) {
                const u = new SpeechSynthesisUtterance('Hoofdstuk ' + chapter);
                u.lang = 'nl-NL'; u.rate = 0.95;
                u.onend = go; u.onerror = go;
                synth.cancel(); synth.speak(u);
                setTimeout(go, 2500);
                return;
            }
        } catch (e) {}
        go();
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
        // Einde hoofdstuk → automatisch doorspelen naar het volgende hoofdstuk
        // (navigeert ook over de boekgrens; _updateAudioPlayer start het fragment).
        audioEl.addEventListener('ended', () => {
            App._autoplayNext = true;
            if (typeof Navigation !== 'undefined' && Navigation.navigateRelative) {
                Navigation.navigateRelative(1);
            }
        });

        // === Meescrollen met de voorlezing ===
        // Geen vers-timestamps in de MP3 → positie schatten op tekstlengte per vers.
        let scrollMap = null, lastScrollIdx = -1, userScrollAt = 0;
        const buildScrollMap = () => {
            const rows = Array.from(document.querySelectorAll('#content .verse-row'));
            let cum = 0;
            scrollMap = rows.map(r => {
                const len = ((r.textContent || '').trim().length) || 1;
                const start = cum; cum += len;
                return { row: r, end: cum };
            });
            scrollMap._total = cum || 1;
            lastScrollIdx = -1;
        };
        audioEl.addEventListener('play', buildScrollMap);
        // Handmatig scrollen pauzeert het meescrollen ~6s (zodat je rustig kunt lezen)
        ['wheel', 'touchmove'].forEach(ev =>
            window.addEventListener(ev, () => { userScrollAt = Date.now(); }, { passive: true }));
        audioEl.addEventListener('timeupdate', () => {
            if (audioEl.paused || !audioEl.duration || !scrollMap || !scrollMap.length) return;
            if (Date.now() - userScrollAt < 6000) return;
            const pos = (audioEl.currentTime / audioEl.duration) * scrollMap._total;
            let idx = scrollMap.findIndex(v => pos < v.end);
            if (idx < 0) idx = scrollMap.length - 1;
            if (idx !== lastScrollIdx) {
                lastScrollIdx = idx;
                const row = scrollMap[idx].row;
                if (row) row.scrollIntoView({ block: 'center', behavior: 'smooth' });
            }
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

        // Stem-toggle (man/vrouw): wissel bron, behoud positie + afspeelstatus
        const voiceBtn = document.getElementById('audio-voice');
        const voiceMob = document.getElementById('audio-voice-mobile');
        const toggleVoice = () => {
            const ov = window.OV_AUDIO;
            if (!ov || App._audioBookId == null) return;
            const wasPlaying = !audioEl.paused;
            const pos = audioEl.currentTime || 0;
            ov.toggleVoice();
            const lbl = ov.label();
            if (voiceBtn) voiceBtn.textContent = lbl;
            if (voiceMob) voiceMob.textContent = lbl;
            // Opties-radio's synchroniseren
            document.querySelectorAll('input[name="opt-stem"]').forEach(r => { r.checked = (r.value === ov.getVoice()); });
            audioEl.src = ov.src(App._audioBookId, App._audioChapter);
            audioEl.addEventListener('loadedmetadata', function once() {
                audioEl.removeEventListener('loadedmetadata', once);
                try { audioEl.currentTime = Math.min(pos, audioEl.duration || pos); } catch (e) {}
                if (wasPlaying) audioEl.play();
            });
        };
        if (voiceBtn) voiceBtn.addEventListener('click', toggleVoice);
        if (voiceMob) voiceMob.addEventListener('click', toggleVoice);

        // Scrubber: doorspoelen + tijd-display (desktop + mobiel)
        const scrubbers = [document.getElementById('audio-scrubber'),
                           document.getElementById('audio-scrubber-mobile')].filter(Boolean);
        if (scrubbers.length) {
            audioEl.addEventListener('loadedmetadata', () => {
                scrubbers.forEach(s => { s.max = audioEl.duration || 0; });
                if (totEl) totEl.textContent = fmt(audioEl.duration);
            });
            audioEl.addEventListener('timeupdate', () => {
                scrubbers.forEach(s => { if (!s._dragging) s.value = audioEl.currentTime; });
                if (curEl) curEl.textContent = fmt(audioEl.currentTime);
            });
            scrubbers.forEach(s => {
                s.addEventListener('input', () => {
                    s._dragging = true;
                    if (curEl) curEl.textContent = fmt(parseFloat(s.value));
                });
                s.addEventListener('change', () => {
                    audioEl.currentTime = parseFloat(s.value);
                    s._dragging = false;
                });
            });
        }

        // === Opties-paneel: stem (man/vrouw) + afspeelsnelheid ===
        const storedSpeed = parseFloat(localStorage.getItem('ov_speed')) || 1;
        audioEl.playbackRate = storedSpeed;
        // Opgeslagen snelheid opnieuw toepassen bij elk nieuw fragment
        audioEl.addEventListener('loadedmetadata', () => {
            audioEl.playbackRate = parseFloat(localStorage.getItem('ov_speed')) || 1;
        });
        // Stem opnieuw laden met behoud van positie + status
        const reloadVoice = () => {
            const ov = window.OV_AUDIO;
            if (!ov || App._audioBookId == null) return;
            const wasPlaying = !audioEl.paused;
            const pos = audioEl.currentTime || 0;
            audioEl.src = ov.src(App._audioBookId, App._audioChapter);
            const lbl = ov.label();
            if (voiceBtn) voiceBtn.textContent = lbl;
            if (voiceMob) voiceMob.textContent = lbl;
            audioEl.addEventListener('loadedmetadata', function once() {
                audioEl.removeEventListener('loadedmetadata', once);
                try { audioEl.currentTime = Math.min(pos, audioEl.duration || pos); } catch (e) {}
                if (wasPlaying) audioEl.play();
            });
        };
        const ovHelper = window.OV_AUDIO;
        document.querySelectorAll('input[name="opt-stem"]').forEach(r => {
            if (ovHelper) r.checked = (r.value === ovHelper.getVoice());
            r.addEventListener('change', () => {
                if (!r.checked || !window.OV_AUDIO) return;
                window.OV_AUDIO.setVoice(r.value);
                reloadVoice();
            });
        });
        const speedSel = document.getElementById('opt-audio-speed');
        if (speedSel) {
            speedSel.value = String(storedSpeed);
            speedSel.addEventListener('change', () => {
                const sp = parseFloat(speedSel.value) || 1;
                localStorage.setItem('ov_speed', String(sp));
                audioEl.playbackRate = sp;
                const lbl = sp + '×';
                if (speedBtn) speedBtn.textContent = lbl;
                if (speedMob) speedMob.textContent = lbl;
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

    async renderChapter(bookId, chapterNum, opts = {}) {
        const append = !!opts.append;    // doorlopend-lezen: hoofdstuk onderaan toevoegen
        const prepend = !!opts.prepend;  // doorlopend-lezen: hoofdstuk bovenaan toevoegen
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
        // Boeknaam onthouden (gebruikt door scroll-spy bij doorlopend lezen)
        App._contNames = App._contNames || {};
        App._contNames[bookId] = book.nameDutch;

        if (!append && !prepend) {
        // Titel — concept-marker bij niet-geverifieerde hoofdstukken
        App._setTitle(bookId, chapterNum);
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

        // Hoofdstukinleiding wordt nu INLINE in de tekstkolom getoond (zie hieronder),
        // niet meer in een apart frame.
        const introFrame = document.getElementById('chapter-intro');
        if (introFrame) introFrame.style.display = 'none';
        }  // einde if(!append): bovenstaande chrome alleen bij normaal renderen

        // Pericoop-kopjes (NBG-stijl indeling, eigen koppen) — eenmalig laden
        if (App._pericopen === undefined) {
            App._pericopen = null;
            try { App._pericopen = await (await fetch('data/pericopen.json')).json(); }
            catch (e) { App._pericopen = {}; }
        }
        const pericMap = {};
        for (const p of ((App._pericopen && App._pericopen[bookId]) || [])) {
            if (p.c === chapterNum) pericMap[p.v] = p.t;
        }

        // Verzen renderen
        const container = document.getElementById('verses-container');
        // sink = waar de nieuwe nodes heen gaan. Bij prepend bouwen we eerst in een
        // fragment, en plaatsen dat daarna bovenaan (met scroll-compensatie).
        const sink = prepend ? document.createDocumentFragment() : container;
        if (!append && !prepend) {
            container.innerHTML = '';
        }
        if (append || prepend) {
            // Doorlopend lezen: scheidingskop voor het toegevoegde hoofdstuk
            const sep = document.createElement('div');
            sep.className = 'chapter-separator';
            sep.textContent = `${book.nameDutch} ${chapterNum}`;
            sep.dataset.book = bookId;
            sep.dataset.chapter = chapterNum;
            sink.appendChild(sep);
        }

        // Hoofdstukinleiding inline in de tekstkolom (onder de hoofdstukkop),
        // zichtbaar via instelling (body.show-chapter-intro)
        if (chapter.chapterIntro && (chapter.chapterIntro.text2026 || chapter.chapterIntro.text1637)) {
            const intro = document.createElement('div');
            intro.className = 'chapter-intro-inline';
            intro.dataset.book = bookId;
            intro.dataset.chapter = chapterNum;
            intro.textContent = chapter.chapterIntro.text2026 || chapter.chapterIntro.text1637;
            sink.appendChild(intro);
        }

        for (const verse of chapter.verses) {
            // Pericoop-kop vóór dit vers?
            if (pericMap[verse.number]) {
                const h = document.createElement('div');
                h.className = 'pericope-heading';
                h.textContent = pericMap[verse.number];
                sink.appendChild(h);
            }
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
                    // Apocriefen hebben geen Strong's — toon dan lemma als subtext (of niets)
                    const strongs = w.strongs || '';
                    const subText = strongs || w.lemma || '';
                    const dataAttr = strongs ? ` data-strongs="${strongs}"` : '';
                    const subHtml = subText ? `<br><span class="strongs-sub">${subText}</span>` : '';
                    return `<span class="strongs-word"${dataAttr} data-transliteratie="${translit}" data-gloss="${gloss}">${w.woord}${subHtml}</span>`;
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

            // Open Staten Vertaling: gebruik text2026_html (met inline nootcijfers) als die er is,
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

            sink.appendChild(row);
            Editor.attachVerseListeners(row, bookId, chapterNum, verse.number);
            // Rechtermuisknop op versnummer = tag toevoegen
            row.querySelector('.verse-num').addEventListener('contextmenu', (e) => {
                e.preventDefault();
                if (typeof Tags !== 'undefined') {
                    Tags.showAddTagPopup(bookId, chapterNum, verse.number, e.target);
                }
            });
        }

        // Doorlopend lezen: prepend-fragment bovenaan plaatsen met scroll-compensatie
        // zodat de leespositie niet verspringt.
        if (prepend) {
            const scroller = App._getScroller();
            const prevH = scroller ? scroller.scrollHeight : 0;
            const prevTop = scroller ? scroller.scrollTop : 0;
            container.insertBefore(sink, container.firstChild);
            if (scroller) scroller.scrollTop = prevTop + (scroller.scrollHeight - prevH);
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
        // Versierde initiaal (drop-cap) op het eerste vers
        App._applyDropcap();
        // Doorlopend lezen: sentinel/observer beheren
        App._afterRenderContinuous(append, prepend);
    },

    // Scroll naar een specifiek vers en selecteer/markeer het (bv. vanaf Onderwerpen)
    focusVerse(bookId, ch, vs) {
        let tries = 0;
        const tryFocus = () => {
            const row = document.querySelector(`.verse-row[data-book="${bookId}"][data-chapter="${ch}"][data-verse="${vs}"]`)
                     || document.querySelector(`.verse-row[data-verse="${vs}"]`);
            if (!row) {
                if (tries++ < 20) { setTimeout(tryFocus, 80); } else { window.scrollTo(0, 0); }
                return;
            }
            row.scrollIntoView({ behavior: 'smooth', block: 'center' });
            try {
                if (window.VerseSelect && VerseSelect._key) {
                    VerseSelect.clearAll();
                    VerseSelect.select(VerseSelect._key(row));
                    VerseSelect.lastClicked = VerseSelect._key(row);
                    VerseSelect.updateUI();
                } else {
                    row.classList.add('verse-selected');
                }
            } catch (e) {}
            row.classList.add('verse-flash');
            setTimeout(() => row.classList.remove('verse-flash'), 1700);
        };
        setTimeout(tryFocus, 60);
    },

    // Hoofdstuktitel (met concept-marker) zetten — gedeeld door render + scroll-spy
    _setTitle(bookId, chapterNum) {
        const titleEl = document.getElementById('chapter-title');
        if (!titleEl) return;
        const name = (App._contNames && App._contNames[bookId]) || bookId;
        const verified = App._isVerified(bookId, chapterNum);
        titleEl.textContent = `${name} ${chapterNum}`;
        titleEl.classList.toggle('chapter-unverified', !verified);
        if (!verified) {
            const tag = document.createElement('span');
            tag.className = 'chapter-concept-tag';
            tag.textContent = 'CONCEPT — NIET GECONTROLEERD';
            titleEl.appendChild(document.createTextNode(' '));
            titleEl.appendChild(tag);
        }
    },

    // Bepaal het scrollbare element (document of #content)
    _getScroller() {
        const c = document.getElementById('content');
        if (c && c.scrollHeight > c.clientHeight + 5) return c;
        return document.scrollingElement || document.documentElement;
    },

    // === Doorlopend lezen (lazy-load hoofdstukken bij omhoog/omlaag scrollen) ===
    _afterRenderContinuous(append, prepend) {
        const container = document.getElementById('verses-container');
        if (!container) return;
        const on = localStorage.getItem('doorlopend') === 'true';
        document.body.classList.toggle('doorlopend-aan', on);
        let bottom = document.getElementById('continuous-sentinel');
        let top = document.getElementById('continuous-sentinel-top');
        if (!on) {
            if (bottom) bottom.remove();
            if (top) top.remove();
            if (App._contObserver) { App._contObserver.disconnect(); App._contObserver = null; }
            return;
        }
        App._setupScrollSpy();
        if (!append && !prepend) {
            App._contLast = { bookId: Navigation.currentBook, chapterNum: Navigation.currentChapter };
            App._contFirst = { bookId: Navigation.currentBook, chapterNum: Navigation.currentChapter };
            App._contLoading = false;
        }
        if (!bottom) { bottom = document.createElement('div'); bottom.id = 'continuous-sentinel'; bottom.style.height = '1px'; }
        if (!top) { top = document.createElement('div'); top.id = 'continuous-sentinel-top'; top.style.height = '1px'; }
        container.appendChild(bottom);                       // altijd onderaan
        container.insertBefore(top, container.firstChild);   // altijd bovenaan
        if (!App._contObserver) {
            App._contObserver = new IntersectionObserver((entries) => {
                for (const e of entries) {
                    if (!e.isIntersecting) continue;
                    if (e.target.id === 'continuous-sentinel-top') App._loadPrevContinuous();
                    else App._loadNextContinuous();
                }
            }, { rootMargin: '600px 0px' });
        } else {
            App._contObserver.disconnect();
        }
        App._contObserver.observe(bottom);
        App._contObserver.observe(top);
    },

    async _loadNextContinuous() {
        if (App._contLoading || localStorage.getItem('doorlopend') !== 'true') return;
        const last = App._contLast;
        if (!last) return;
        App._contLoading = true;
        try {
            const manifest = await DataLoader.loadManifest();
            const mode = (window.Opties && Opties.state && Opties.state.boekvolgorde) || 'canoniek';
            const orderIds = (typeof getFlatBookOrder === 'function')
                ? getFlatBookOrder(mode, manifest) : manifest.books.map(b => b.id);
            const byId = Object.fromEntries(manifest.books.map(b => [b.id, b]));
            const cur = byId[last.bookId];
            const chs = (cur && cur.chaptersIncluded) || [];
            const idx = chs.indexOf(last.chapterNum);
            let nextBook = null, nextCh = null;
            if (idx >= 0 && idx < chs.length - 1) {
                nextBook = last.bookId; nextCh = chs[idx + 1];
            } else {
                const bi = orderIds.indexOf(last.bookId);
                const nb = (bi >= 0 && bi < orderIds.length - 1) ? byId[orderIds[bi + 1]] : null;
                if (nb && nb.chaptersIncluded && nb.chaptersIncluded.length) {
                    nextBook = nb.id; nextCh = nb.chaptersIncluded[0];
                }
            }
            if (nextCh != null) {
                await App.renderChapter(nextBook, nextCh, { append: true });
                App._contLast = { bookId: nextBook, chapterNum: nextCh };
            }
        } catch (e) { console.warn('[doorlopend] laden volgende hoofdstuk faalde:', e); }
        App._contLoading = false;
    },

    async _loadPrevContinuous() {
        if (App._contLoading || localStorage.getItem('doorlopend') !== 'true') return;
        const first = App._contFirst;
        if (!first) return;
        App._contLoading = true;
        try {
            const manifest = await DataLoader.loadManifest();
            const mode = (window.Opties && Opties.state && Opties.state.boekvolgorde) || 'canoniek';
            const orderIds = (typeof getFlatBookOrder === 'function')
                ? getFlatBookOrder(mode, manifest) : manifest.books.map(b => b.id);
            const byId = Object.fromEntries(manifest.books.map(b => [b.id, b]));
            const cur = byId[first.bookId];
            const chs = (cur && cur.chaptersIncluded) || [];
            const idx = chs.indexOf(first.chapterNum);
            let prevBook = null, prevCh = null;
            if (idx > 0) {
                prevBook = first.bookId; prevCh = chs[idx - 1];
            } else {
                const bi = orderIds.indexOf(first.bookId);
                const pb = (bi > 0) ? byId[orderIds[bi - 1]] : null;
                if (pb && pb.chaptersIncluded && pb.chaptersIncluded.length) {
                    prevBook = pb.id; prevCh = pb.chaptersIncluded[pb.chaptersIncluded.length - 1];
                }
            }
            if (prevCh != null) {
                await App.renderChapter(prevBook, prevCh, { prepend: true });
                App._contFirst = { bookId: prevBook, chapterNum: prevCh };
            }
        } catch (e) { console.warn('[doorlopend] vorige hoofdstuk laden faalde:', e); }
        App._contLoading = false;
    },

    // Scroll-spy: werk de hoofdstuktitel bovenaan (en de URL) bij naar het
    // hoofdstuk dat momenteel boven in beeld staat — alleen bij doorlopend lezen.
    _setupScrollSpy() {
        if (App._scrollSpyWired) return;
        App._scrollSpyWired = true;
        let ticking = false;
        const onScroll = () => {
            if (localStorage.getItem('doorlopend') !== 'true') return;
            if (ticking) return;
            ticking = true;
            requestAnimationFrame(() => { ticking = false; App._updateTitleFromScroll(); });
        };
        window.addEventListener('scroll', onScroll, { passive: true });
        const sc = document.getElementById('content');
        if (sc) sc.addEventListener('scroll', onScroll, { passive: true });
    },

    _updateTitleFromScroll() {
        const rows = document.querySelectorAll('#verses-container .verse-row');
        if (!rows.length) return;
        const threshold = 140;   // net onder de sticky bovenbalk
        let cur = null;
        for (const r of rows) {
            const rect = r.getBoundingClientRect();
            if (rect.bottom > threshold) { cur = r; break; }
        }
        if (!cur) cur = rows[rows.length - 1];
        const bookId = cur.dataset.book;
        const ch = parseInt(cur.dataset.chapter, 10);
        if (!bookId || !ch) return;
        if (App._spyBook === bookId && App._spyChapter === ch) return;
        App._spyBook = bookId; App._spyChapter = ch;
        App._setTitle(bookId, ch);
        // footer-label + interne navigatiepointers meenemen (voor vorige/volgende)
        if (typeof Navigation !== 'undefined') {
            Navigation.currentBook = bookId;
            Navigation.currentChapter = ch;
        }
        try { history.replaceState(null, '', `#${bookId}/${ch}`); } catch (e) {}
    },

    /* Zet de eerste ECHTE letter van het eerste vers in een <span class="dropcap">.
     * Slaat leidende aanhalingstekens, note-markers (sup) en citaat-spans over,
     * zodat bij een citaat niet het aanhalingsteken wordt vergroot maar de letter. */
    _applyDropcap() {
        const container = document.getElementById('verses-container');
        if (!container) return;
        // Verwijder oude dropcap (bij hervertonen)
        const old = container.querySelector('.dropcap');
        if (old) old.replaceWith(...old.childNodes);
        const firstRow = container.querySelector('.verse-row');
        if (!firstRow) return;
        const cell = firstRow.querySelector('.col-2026');
        if (!cell) return;
        // Loop door tekstnodes (in document-volgorde) en zoek de eerste letter.
        const walker = document.createTreeWalker(cell, NodeFilter.SHOW_TEXT, {
            acceptNode(node) {
                // Sla note-markers (sup) over
                if (node.parentElement && node.parentElement.closest('sup')) return NodeFilter.FILTER_REJECT;
                return NodeFilter.FILTER_ACCEPT;
            }
        });
        let node;
        while ((node = walker.nextNode())) {
            const m = node.nodeValue.match(/[A-Za-zÀ-ÿ]/);
            if (!m) continue;
            const idx = node.nodeValue.indexOf(m[0]);
            // Split: tekst vóór de letter blijft, letter wordt dropcap, rest erna blijft
            const after = node.splitText(idx);          // after begint met de letter
            const letter = after.nodeValue[0];
            const rest = after.splitText(1);            // rest = na de letter
            const span = document.createElement('span');
            span.className = 'dropcap';
            span.textContent = letter;
            after.replaceWith(span);                     // vervang de losse letter-node
            break;
        }
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

        // Defaults: 1637, 2026, margin1637, margin2026 aan; rest uit.
        // Mobiel zonder opgeslagen voorkeur: alleen OSV (2026), geen verschillen.
        if (!visibility) {
            visibility = {};
            const isMobile = window.matchMedia && window.matchMedia('(max-width: 768px)').matches;
            this.ALL_COLS.forEach(col => {
                if (isMobile) {
                    visibility[col] = (col === '2026');   // alleen OSV, geen verschillen/kanttekeningen
                } else {
                    const cb = document.querySelector(`[data-toggle-col="${col}"]`);
                    visibility[col] = cb ? cb.checked : false;
                }
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
