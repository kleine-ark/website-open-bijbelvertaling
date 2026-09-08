/* Open Vertaling — Hoofdapplicatie */

const App = {
    // Alle kolom-keys in volgorde (num is altijd zichtbaar)
    ALL_COLS: ['1637', 'margin1637', 'sv1888', 'marginSV1888', '2026', 'margin2026', 'hebrew', 'diff', 'noteDiff'],

    _escapeStrongHtml(value) {
        return String(value == null ? '' : value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    },

    renderStrongLinks(html, woordnummers) {
        return window.OVWoordnummers ? window.OVWoordnummers.renderInline(html, woordnummers) : html;
    },
    // AUDIO_AVAILABLE leeft in js/audio-available.js (window.AUDIO_AVAILABLE) —
    // niet hier definieren. Wordt door de TTS-rollout-script bijgewerkt.

    // Hoofdstukken die handmatig vers-voor-vers zijn nagelopen.
    // Voor andere hoofdstukken: AI-concept-banner tonen.
    // Nagekeken hoofdstukken staan in data/verified-chapters.json, zodat app.js,
    // lees.js en de bouwscripts allemaal uit dezelfde bron putten. Stond eerder
    // als kopie in twee JS-bestanden, wat vroeg of laat uit elkaar loopt.
    VERIFIED_CHAPTERS: {},
    _verifiedGeladen: null,

    /** Laad de nagekeken-lijst eenmalig. Faalt dit, dan geldt alles als NIET
     *  nagekeken, zodat de waarschuwingsbanner verschijnt. Nooit andersom: een
     *  storing mag geen onnagekeken tekst zonder waarschuwing tonen. */
    _laadVerified() {
        if (!App._verifiedGeladen) {
            App._verifiedGeladen = fetch('data/verified-chapters.json')
                .then(r => (r.ok ? r.json() : {}))
                .then(d => { App.VERIFIED_CHAPTERS = d || {}; })
                .catch(() => { App.VERIFIED_CHAPTERS = {}; });
        }
        return App._verifiedGeladen;
    },

    _isVerified(bookId, chapter) {
        if (typeof TekstEditie !== 'undefined' && TekstEditie.code() !== 'nl-ov') return false;
        const v = App.VERIFIED_CHAPTERS[bookId];
        if (!v) return false;
        if (v === 'all') return true;
        return Array.isArray(v) && v.includes(chapter);
    },

    _updateVerifiedBanner(bookId, chapter) {
        let banner = document.getElementById('ai-concept-banner');
        if (typeof TekstEditie !== 'undefined' && TekstEditie.code() !== 'nl-ov') {
            if (banner) banner.style.display = 'none';
            return;
        }
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

    _resetUnavailableChapterChrome(book, bookId, chapter) {
        App._contNames = App._contNames || {};
        App._contNames[bookId] = book.nameDutch;
        App._setTitle(bookId, chapter);
        App._updateVerifiedBanner(bookId, chapter);
        App._updateEthiopicBanner(null);

        const dating = document.getElementById('book-dating');
        if (dating) dating.style.display = 'none';
        ['book-intro', 'chapter-intro'].forEach(id => {
            const element = document.getElementById(id);
            if (element) element.style.display = 'none';
        });
    },

    async _updateDatingBox(book, renderGeneration) {
        if (App._bookDating === undefined) {
            App._bookDating = null;
            App._bookDatingLoading = (async () => {
                try { App._bookDating = await (await fetch('data/book-dating.json')).json(); }
                catch (e) { App._bookDating = {}; }
                finally { App._bookDatingLoading = null; }
            })();
        }
        if (App._bookDatingLoading) await App._bookDatingLoading;
        if (renderGeneration !== App._chapterChromeGeneration) return;

        const d = App._bookDating && App._bookDating[book.id];
        let box = document.getElementById('book-dating');
        if (!box) {
            box = document.createElement('div');
            box.id = 'book-dating';
            box.className = 'book-dating';
            const container = document.getElementById('verses-container');
            if (container && container.parentNode) container.parentNode.insertBefore(box, container);
        }
        const handschriftenUrl = `handschriften/${encodeURIComponent(book.id)}.html`;
        const handschriftenTitel = 'Open de handschriftenpagina met oudste fragment, vindgeschiedenis en scans';
        const parts = [];
        if (d && (d.schrijftijdKort || d.schrijftijd)) parts.push(`<a class="dating-link" href="${handschriftenUrl}" title="${handschriftenTitel}"><span class="dating-label">Schrijftijd:</span> ${d.schrijftijdKort || d.schrijftijd}</a>`);
        // Alleen het jaartal van het oudste handschrift tonen (geen siglum/nummer); details staan op de handschriftenpagina.
        const oudsteJaar = d && (d.oudsteDatum || d.oudsteHandschrift);
        if (oudsteJaar) parts.push(`<a class="dating-link" href="${handschriftenUrl}" title="${handschriftenTitel}"><span class="dating-label">Oudste handschrift:</span> ${String(oudsteJaar).split(' (')[0]}</a>`);
        box.innerHTML = '<img class="dating-icon" src="images/iconen/instellingen/oudste-handschrift.png" alt="" aria-hidden="true">' + parts.join(' &nbsp;·&nbsp; ');
        box.style.display = 'block';
    },

    _updateEthiopicBanner(book) {
        const isEth = book && (book.testament === 'ET' || (window.ETHIOPIC_BOOKS && window.ETHIOPIC_BOOKS.includes(book.id)));
        const isApoc = book && book.testament === 'AP';
        let banner = document.getElementById('ethiopic-banner');
        if (!isEth && !isApoc) { if (banner) banner.style.display = 'none'; return; }
        if (!banner) {
            banner = document.createElement('div');
            banner.id = 'ethiopic-banner';
            banner.className = 'ethiopic-banner';
            const container = document.getElementById('verses-container');
            if (container && container.parentNode) container.parentNode.insertBefore(banner, container);
        }
        banner.innerHTML = isEth
            ? '<strong>⚠ Buiten-canoniek boek (Ethiopisch-orthodoxe traditie).</strong> ' +
              'Dit boek is géén onderdeel van de canon van Gods Woord en hoort niet tot de Statenvertaling-canon. ' +
              'De vertaling is in bewerking en de Ge’ez-grondtekst wordt slechts gedeeltelijk (per beschikbaar hoofdstuk) getoond.'
            : '<strong>⚠ Apocrief boek - geen onderdeel van de canon van Gods Woord</strong>';
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
        const isOpenVertaling = typeof TekstEditie === 'undefined' || TekstEditie.code() === 'nl-ov';
        const show = !!(isOpenVertaling && ov && ov.available(bookId, chapter));
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
        if (playBtn) playBtn.classList.remove('is-playing');
        if (playMob) playMob.classList.remove('is-playing');
        const scrubber = document.getElementById('audio-scrubber');
        const cur = document.getElementById('audio-time-cur');
        const tot = document.getElementById('audio-time-tot');
        if (scrubber) scrubber.value = 0;
        if (cur) cur.textContent = '0:00';
        if (tot) tot.textContent = '0:00';
        if (!show) {
            audioEl.removeAttribute('src');
            try { audioEl.load(); } catch (e) {}
            App._autoplayNext = false;
            return;
        }
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
        const _curVoice = () => (window.OV_AUDIO && OV_AUDIO.getVoice) ? OV_AUDIO.getVoice() : 'v';
        audioEl.addEventListener('play', () => {
            if (playBtn) playBtn.classList.add('is-playing');
            if (playMob) playMob.classList.add('is-playing');
            // Tijdsbestand laden voor exacte versmarkering tijdens het voorlezen
            if (App._audioBookId != null) App._loadAudioTiming(App._audioBookId, App._audioChapter, _curVoice());
        });
        audioEl.addEventListener('pause', () => {
            if (playBtn) playBtn.classList.remove('is-playing');
            if (playMob) playMob.classList.remove('is-playing');
            App._clearVerseFocus();
        });
        // Einde hoofdstuk → automatisch doorspelen naar het volgende hoofdstuk
        // (navigeert ook over de boekgrens; _updateAudioPlayer start het fragment).
        audioEl.addEventListener('ended', () => {
            App._clearVerseFocus();
            App._autoplayNext = true;
            if (typeof Navigation !== 'undefined' && Navigation.navigateRelative) {
                Navigation.navigateRelative(1);
            }
        });

        // === Versmarkering + meescrollen met de voorlezing ===
        // Strikt gekoppeld aan het SPELENDE hoofdstuk (App._audioBookId/_audioChapter):
        // exact via het per-vers tijdsbestand, anders een schatting BINNEN dit
        // hoofdstuk. Zo kan de markering nooit naar een ánder hoofdstuk wegspringen
        // wanneer er meerdere hoofdstukken tegelijk geladen zijn (doorlopend lezen).
        // Handmatig scrollen pauzeert het meescrollen ~6s.
        App._userScrollAt = App._userScrollAt || 0;
        if (!App._userScrollWired) {
            App._userScrollWired = true;
            ['wheel', 'touchmove'].forEach(ev =>
                window.addEventListener(ev, () => { App._userScrollAt = Date.now(); }, { passive: true }));
        }
        audioEl.addEventListener('timeupdate', () => {
            if (audioEl.paused || App._audioBookId == null) return;
            App._followAudio(App._audioBookId, App._audioChapter, _curVoice(),
                             audioEl.currentTime, audioEl.duration);
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
        // Eerst de nagekeken-lijst, want sidebar.js, mobile-nav.js en de
        // hoofdstukknoppen lezen die synchroon. Renderen ze eerder, dan lijkt
        // alles concept te zijn.
        await App._laadVerified();
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

    _opvSpeakerClass(type) {
        if (type === 'god' || type === 'spirit') return 'god-speaks';
        if (type === 'angel') return 'angel-speaks';
        return 'direct-speech';
    },

    _appendOpvSegments(target, verse) {
        const segments = Array.isArray(verse.segmenten) ? verse.segmenten : [];
        if (!segments.length) {
            target.appendChild(document.createTextNode(verse.text2026 || ''));
            return;
        }

        const segmentIndex = new Map(segments.map((segment, index) => [segment.id, index]));
        const conceptsBySegment = new Map();
        for (const concept of (verse.begrippen || [])) {
            for (const segmentId of (concept.segmenten || [])) {
                if (!conceptsBySegment.has(segmentId)) conceptsBySegment.set(segmentId, concept.conceptId);
            }
        }

        const openings = new Map();
        for (const citation of (verse.citaten || [])) {
            const start = segmentIndex.get(citation.startSegment);
            const end = segmentIndex.get(citation.endSegment);
            if (start == null || end == null || end < start) continue;
            const interval = { citation, start, end };
            if (!openings.has(start)) openings.set(start, []);
            openings.get(start).push(interval);
        }
        openings.forEach(items => items.sort((left, right) => right.end - left.end));

        const stack = [];
        let current = target;
        segments.forEach((segment, index) => {
            for (const interval of (openings.get(index) || [])) {
                const citation = interval.citation;
                const speaker = citation.spreker || {};
                const wrapper = document.createElement('span');
                wrapper.classList.add('opv-citation', App._opvSpeakerClass(speaker.type));
                wrapper.dataset.opvCitation = citation.id || '';
                wrapper.dataset.opvCitationSemantic = citation.semanticId || '';
                wrapper.dataset.opvSpeaker = speaker.id || '';
                wrapper.dataset.opvSpeakerType = speaker.type || '';
                if (speaker.naam) wrapper.setAttribute('aria-label', `Woorden van ${speaker.naam}`);
                current.appendChild(wrapper);
                stack.push({ element: wrapper, end: interval.end });
                current = wrapper;
            }

            const conceptId = conceptsBySegment.get(segment.id);
            const segmentNode = document.createElement(conceptId ? 'button' : 'span');
            segmentNode.dataset.opvSegment = segment.id || '';
            if (conceptId) {
                segmentNode.type = 'button';
                segmentNode.className = 'opv-concept';
                segmentNode.dataset.opvConcept = conceptId;
                segmentNode.setAttribute('aria-expanded', 'false');
                segmentNode.setAttribute('aria-controls', 'opv-concept-dialog');
                segmentNode.setAttribute('aria-label', `${segment.tekst || ''} — toon uitleg`);
                segmentNode.tabIndex = App._opvConceptsEnabled === false ? -1 : 0;
                segmentNode.classList.toggle('opv-concept-disabled', App._opvConceptsEnabled === false);
                segmentNode.setAttribute('aria-disabled', App._opvConceptsEnabled === false ? 'true' : 'false');
                segmentNode.addEventListener('click', event => {
                    event.stopPropagation();
                    if (!segmentNode.classList.contains('opv-concept-disabled')) {
                        App._openOpvConcept(segmentNode);
                    }
                });
            }
            segmentNode.textContent = segment.tekst || '';
            current.appendChild(segmentNode);

            while (stack.length && stack[stack.length - 1].end === index) {
                stack.pop();
                current = stack.length ? stack[stack.length - 1].element : target;
            }
        });
    },

    _createOpvVerse(verse, book, bookId, chapterNum, parallelEditions) {
        const row = document.createElement('span');
        row.className = 'verse-row opv-verse';
        row.classList.toggle('opv-verse--parallel', parallelEditions.length > 0);
        row.dataset.status = verse.status || 'empty';
        row.dataset.book = bookId;
        row.dataset.chapter = chapterNum;
        row.dataset.verse = verse.number;

        const anchor = document.createElement('a');
        anchor.className = 'verse-num opv-verse-anchor';
        anchor.dataset.col = 'num';
        anchor.href = `#${bookId}/${chapterNum}/${verse.number}`;
        anchor.textContent = String(verse.number);
        anchor.title = `${book.nameDutch} ${chapterNum}:${verse.number}`;
        anchor.setAttribute('aria-label', `${book.nameDutch} ${chapterNum} vers ${verse.number}`);
        const hideNumbers = window.Opties && Opties.state && Opties.state.versnummers === 'uit';
        anchor.tabIndex = hideNumbers ? -1 : 0;
        anchor.setAttribute('aria-hidden', hideNumbers ? 'true' : 'false');
        anchor.addEventListener('contextmenu', event => {
            event.preventDefault();
            if (typeof Tags !== 'undefined') {
                Tags.showAddTagPopup(bookId, chapterNum, verse.number, anchor);
            }
        });

        const cell = document.createElement('span');
        cell.className = 'verse-cell col-2026 opv-verse-text';
        cell.dataset.col = '2026';
        cell.lang = 'nl';
        cell.dir = 'ltr';

        if (parallelEditions.length) {
            const comparison = document.createElement('span');
            comparison.className = 'edition-comparison opv-edition-comparison';
            comparison.dataset.layout = (window.Opties && Opties.state.kolomLayout === 'eronder') ? 'eronder' : 'naast';
            comparison.style.setProperty('--edition-count', String(parallelEditions.length + 1));

            const primary = document.createElement('span');
            primary.className = 'parallel-edition primary-edition';
            primary.dataset.editie = 'nl-opv';
            primary.dataset.editionLabel = 'Open Parafrase Vertaling (proef)';
            primary.lang = 'nl';
            App._appendOpvSegments(primary, verse);
            comparison.appendChild(primary);

            for (const item of parallelEditions) {
                const parallelVerse = item.verses.get(Number(verse.number));
                if (!parallelVerse) continue;
                const meta = item.meta || { naam: item.code, taal: '', richting: 'ltr' };
                const parallel = document.createElement('span');
                parallel.className = 'parallel-edition';
                parallel.dataset.editie = item.code;
                parallel.dataset.editionLabel = meta.naam || item.code;
                parallel.lang = meta.taal || '';
                parallel.dir = meta.richting === 'rtl' ? 'rtl' : 'ltr';
                parallel.textContent = parallelVerse.text2026 || parallelVerse.textHerzien || '';
                comparison.appendChild(parallel);
            }
            cell.appendChild(comparison);
        } else {
            App._appendOpvSegments(cell, verse);
        }

        row.append(anchor, cell);
        return row;
    },

    _renderOpvReadingFlow(
        chapter, book, bookId, chapterNum, sink, parallelEditions, labelledBy = 'chapter-title'
    ) {
        const flow = document.createElement('article');
        flow.className = 'opv-reading-flow';
        flow.dataset.editie = 'nl-opv';
        flow.dataset.book = bookId;
        flow.dataset.chapter = chapterNum;
        flow.lang = 'nl';
        flow.setAttribute('aria-labelledby', labelledBy);

        const verses = new Map((chapter.verses || []).map(verse => [Number(verse.number), verse]));
        const rendered = new Set();
        for (const block of (chapter.blokken || [])) {
            const passage = document.createElement('section');
            passage.className = 'opv-passage';
            passage.dataset.blockId = block.id || '';
            passage.dataset.range = `${block.vanaf}-${block.tot}`;
            passage.dataset.from = block.vanaf;
            passage.dataset.to = block.tot;

            const title = document.createElement('h3');
            title.className = 'opv-passage-title';
            title.textContent = block.kop || '';
            passage.appendChild(title);

            const passageText = document.createElement('div');
            passageText.className = 'opv-passage-text';
            for (let number = Number(block.vanaf); number <= Number(block.tot); number += 1) {
                const verse = verses.get(number);
                if (!verse || rendered.has(number)) continue;
                if (passageText.childNodes.length) passageText.appendChild(document.createTextNode(' '));
                passageText.appendChild(App._createOpvVerse(
                    verse, book, bookId, chapterNum, parallelEditions
                ));
                rendered.add(number);
            }
            passage.appendChild(passageText);
            flow.appendChild(passage);
        }
        sink.appendChild(flow);
    },

    _beginNavigationRequest(bookId, chapterNum) {
        const request = {
            id: (App._navigationRequestSequence = (App._navigationRequestSequence || 0) + 1),
            bookId,
            chapterNum: Number(chapterNum),
        };
        App._navigationRequest = request;
        return request;
    },

    _isCurrentNavigationRequest(request) {
        return !!request && App._navigationRequest === request;
    },

    _isCurrentRenderOwner(owner) {
        const edition = (typeof TekstEditie === 'undefined') ? 'nl-ov' : TekstEditie.code();
        return !!owner && App._renderOwner === owner && owner.editionCode === edition &&
            owner.navigationRequest === (App._navigationRequest || null);
    },

    _isCurrentContinuousOwner(owner) {
        if (!owner || App._continuousOwner !== owner ||
            !App._isCurrentRenderOwner(owner.renderOwner) ||
            localStorage.getItem('doorlopend') !== 'true') return false;
        const boundary = owner.direction === 'next' ? App._contLast : App._contFirst;
        return !!boundary && boundary.bookId === owner.edge.bookId &&
            Number(boundary.chapterNum) === Number(owner.edge.chapterNum);
    },

    _ensureOpvConceptDialog() {
        let dialog = document.getElementById('opv-concept-dialog');
        if (dialog) return dialog;
        dialog = document.createElement('dialog');
        dialog.id = 'opv-concept-dialog';
        dialog.className = 'opv-concept-dialog';
        dialog.tabIndex = -1;
        dialog.setAttribute('aria-labelledby', 'opv-concept-title');

        const content = document.createElement('div');
        content.className = 'opv-concept-dialog-content';
        const eyebrow = document.createElement('p');
        eyebrow.className = 'opv-concept-eyebrow';
        eyebrow.textContent = 'Begrip bij de tekst';
        const title = document.createElement('h2');
        title.id = 'opv-concept-title';
        title.className = 'opv-concept-title';
        const explanation = document.createElement('p');
        explanation.className = 'opv-concept-explanation';
        const close = document.createElement('button');
        close.type = 'button';
        close.className = 'opv-concept-close';
        close.textContent = 'Sluiten';
        close.addEventListener('click', () => App._closeOpvConcept(true));
        content.append(eyebrow, title, explanation, close);
        dialog.appendChild(content);
        dialog.addEventListener('click', event => {
            if (event.target === dialog) App._closeOpvConcept(true);
        });
        dialog.addEventListener('cancel', event => {
            event.preventDefault();
            App._closeOpvConcept(true);
        });
        dialog.addEventListener('keydown', event => {
            if (event.key !== 'Tab' || !dialog.open) return;
            const focusable = [...dialog.querySelectorAll(
                'a[href], button:not([disabled]), input:not([disabled]), ' +
                'select:not([disabled]), textarea:not([disabled]), ' +
                '[tabindex]:not([tabindex="-1"])'
            )].filter(element => !element.hidden &&
                element.getAttribute('aria-hidden') !== 'true' &&
                element.getClientRects().length > 0);
            if (!focusable.length) {
                event.preventDefault();
                dialog.focus();
                return;
            }
            if (focusable.length === 1) {
                event.preventDefault();
                focusable[0].focus();
                return;
            }
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            const active = document.activeElement;
            if (event.shiftKey && (active === first || !dialog.contains(active))) {
                event.preventDefault();
                last.focus();
            } else if (!event.shiftKey && (active === last || !dialog.contains(active))) {
                event.preventDefault();
                first.focus();
            }
        });
        dialog.addEventListener('close', () => {
            App._resetOpvConceptState(App._opvRestoreConceptFocus);
        });
        document.body.appendChild(dialog);
        return dialog;
    },

    _loadOpvConcepts() {
        if (!App._opvConceptsPromise) {
            App._opvConceptsPromise = fetch('data/edities/opv/concepten.json')
                .then(response => {
                    if (!response.ok) throw new Error('OPV-begrippenregister ontbreekt');
                    return response.json();
                })
                .then(data => new Map((data.concepten || []).map(item => [item.id, item])))
                .catch(error => {
                    App._opvConceptsPromise = null;
                    console.warn('[OPV] Begrippenregister laden mislukt:', error);
                    return new Map();
                });
        }
        return App._opvConceptsPromise;
    },

    async _openOpvConcept(trigger) {
        const renderOwner = App._renderOwner;
        if (!renderOwner || !renderOwner.committed ||
            !App._isCurrentRenderOwner(renderOwner)) return;
        const generation = App._opvViewGeneration;
        const concepts = await App._loadOpvConcepts();
        if (generation !== App._opvViewGeneration || renderOwner !== App._renderOwner ||
            !renderOwner.committed || !App._isCurrentRenderOwner(renderOwner) ||
            !trigger.isConnected ||
            !trigger.closest('[data-editie="nl-opv"]') ||
            trigger.classList.contains('opv-concept-disabled')) return;
        const concept = concepts.get(trigger.dataset.opvConcept);
        if (!concept) return;

        App._closeOpvConcept(false);
        const dialog = App._ensureOpvConceptDialog();
        dialog.querySelector('.opv-concept-title').textContent = concept.label || '';
        dialog.querySelector('.opv-concept-explanation').textContent = concept.uitleg || '';
        App._opvConceptTrigger = trigger;
        trigger.setAttribute('aria-expanded', 'true');
        if (typeof dialog.showModal === 'function') dialog.showModal();
        else dialog.setAttribute('open', '');
        dialog.querySelector('.opv-concept-close').focus();
    },

    _closeOpvConcept(restoreFocus) {
        const dialog = document.getElementById('opv-concept-dialog');
        const trigger = App._opvConceptTrigger;
        App._resetOpvConceptState(false);
        if (dialog && dialog.open && typeof dialog.close === 'function') dialog.close();
        else if (dialog && dialog.open) {
            dialog.removeAttribute('open');
            dialog.dispatchEvent(new Event('close'));
        }
        if (restoreFocus && trigger && trigger.isConnected) trigger.focus();
    },

    _resetOpvConceptState(restoreFocus) {
        const trigger = App._opvConceptTrigger;
        if (trigger) trigger.setAttribute('aria-expanded', 'false');
        App._opvConceptTrigger = null;
        App._opvRestoreConceptFocus = false;
        if (restoreFocus && trigger && trigger.isConnected) trigger.focus();
    },

    _setOpvConceptsEnabled(enabled) {
        App._opvConceptsEnabled = !!enabled;
        document.body.classList.toggle('opv-concepts-uit', !enabled);
        document.querySelectorAll('[data-opv-concept]').forEach(trigger => {
            trigger.tabIndex = enabled ? 0 : -1;
            trigger.classList.toggle('opv-concept-disabled', !enabled);
            trigger.setAttribute('aria-disabled', enabled ? 'false' : 'true');
        });
        if (!enabled) App._closeOpvConcept(false);
    },

    _finishChapterRender(bookId, chapterNum, append, prepend) {
        this.updateProgress();
        this.updateGrid();
        if (typeof ColumnReorder !== 'undefined') ColumnReorder.reorderDOM();
        if (typeof updateStickyOffset === 'function') updateStickyOffset();
        if (typeof Tags !== 'undefined') Tags.renderTagsForChapter(bookId, chapterNum);
        if (typeof Begrippen !== 'undefined') {
            const begrCb = document.getElementById('toggle-begrippen') || document.getElementById('quick-begrippen');
            if (begrCb && begrCb.checked) Begrippen.active = true;
            Begrippen.reload(bookId);
        }
        if (typeof Highlight !== 'undefined') Highlight.applyToChapter(bookId, chapterNum);
        App._applyDropcap();
        if (typeof Opties !== 'undefined') Opties.applyVerseNumbersClass();
        App._afterRenderContinuous(append, prepend, bookId, chapterNum);
        App._clearVerseFocus();
    },

    async renderChapter(bookId, chapterNum, opts = {}) {
        const append = !!opts.append;    // doorlopend-lezen: hoofdstuk onderaan toevoegen
        const prepend = !!opts.prepend;  // doorlopend-lezen: hoofdstuk bovenaan toevoegen
        const updatesChapterChrome = !append && !prepend;
        const requestedEditionCode = (typeof TekstEditie === 'undefined') ? 'nl-ov' : TekstEditie.code();
        let renderOwner = opts.owner || null;
        let ownsRender;
        if (updatesChapterChrome) {
            renderOwner = {
                id: (App._renderOwnerSequence = (App._renderOwnerSequence || 0) + 1),
                editionCode: requestedEditionCode,
                bookId,
                chapterNum: Number(chapterNum),
                navigationRequest: App._navigationRequest || null,
                committed: false,
            };
            App._renderOwner = renderOwner;
            App._continuousOwner = null;
            App._contLoading = false;
            App._opvViewGeneration = (App._opvViewGeneration || 0) + 1;
            App._closeOpvConcept(false);
            ownsRender = () => App._isCurrentRenderOwner(renderOwner);
        } else if (renderOwner) {
            ownsRender = () => App._isCurrentContinuousOwner(renderOwner);
        } else {
            const parentOwner = App._renderOwner;
            const parentGeneration = App._renderOwnerSequence || 0;
            ownsRender = () => App._renderOwner === parentOwner &&
                (App._renderOwnerSequence || 0) === parentGeneration &&
                ((typeof TekstEditie === 'undefined') ? 'nl-ov' : TekstEditie.code()) === requestedEditionCode;
        }
        if (!ownsRender()) return false;
        const renderGeneration = updatesChapterChrome
            ? (App._chapterChromeGeneration = (App._chapterChromeGeneration || 0) + 1)
            : App._chapterChromeGeneration;
        if (typeof TekstEditie === 'undefined' || TekstEditie.code() === 'nl-ov') {
            await App._laadVerified();   // banner mag niet op verouderde info draaien
            if (!ownsRender()) return false;
        }
        // Manifest (klein) + chapter (klein) parallel
        const [book, chapter] = await Promise.all([
            DataLoader.loadBook(bookId),                      // bouwt lazy book-object
            DataLoader.loadChapter(bookId, chapterNum),       // alleen huidige chapter
        ]);
        if (!ownsRender()) return false;
        if (!book) {
            document.getElementById('verses-container').innerHTML = '<p>Boek niet gevonden.</p>';
            return;
        }
        if (!chapter) {
            document.getElementById('verses-container').innerHTML = '<p>Hoofdstuk niet gevonden.</p>';
            return;
        }
        if (chapter._unavailable) {
            if (append || prepend) return false;
            App._updateAudioPlayer(bookId, chapterNum);
            App._resetUnavailableChapterChrome(book, bookId, chapterNum);
            const meta = chapter._translation || { code: 'nl-ov', naam: 'Open Vertaling' };
            const message = (typeof I18n !== 'undefined')
                ? I18n.t('edition.unavailable', { boek: book.nameDutch, editie: meta.naam })
                : `${book.nameDutch} is niet beschikbaar in ${meta.naam}.`;
            const action = (typeof I18n !== 'undefined') ? I18n.t('edition.openDutch') : 'Open dit boek in Open Vertaling';
            const href = `${location.pathname}?editie=nl-ov#${bookId}/${chapterNum}`;
            document.getElementById('verses-container').innerHTML =
                `<section class="translation-unavailable"><p>${App._escapeStrongHtml(message)}</p>` +
                `<a href="${App._escapeStrongHtml(href)}">${App._escapeStrongHtml(action)}</a></section>`;
            return;
        }
        const translationMeta = chapter._translation || null;
        const isExternalTranslation = !!translationMeta;
        const primaryEditionCode = translationMeta ? translationMeta.code : 'nl-ov';
        if (primaryEditionCode !== requestedEditionCode) return false;
        const configuredParallels = (typeof Opties !== 'undefined' && Array.isArray(Opties.state.parallelEdities))
            ? Opties.state.parallelEdities.filter(code => code !== primaryEditionCode).slice(0, 3)
            : [];
        const parallelEditions = [];
        const unavailableParallelNames = [];
        if (typeof TekstEditie !== 'undefined') {
            const loadedParallels = await Promise.all(configuredParallels.map(async code => {
                const parallelChapter = await TekstEditie.loadChapterForEdition(code, bookId, chapterNum);
                if (!parallelChapter || parallelChapter._unavailable) {
                    const missingMeta = parallelChapter && parallelChapter._translation;
                    unavailableParallelNames.push(missingMeta ? missingMeta.naam : code);
                    return null;
                }
                const meta = parallelChapter._translation || await TekstEditie.metadata(code);
                return {
                    code,
                    meta,
                    verses: new Map((parallelChapter.verses || []).map(item => [Number(item.number), item])),
                };
            }));
            parallelEditions.push(...loadedParallels.filter(Boolean));
        }
        if (!ownsRender()) return false;

        // Pericoop-kopjes (NBG-stijl indeling, eigen koppen) — eenmalig laden
        if (App._pericopen === undefined) {
            App._pericopen = null;
            App._pericopenPromise = fetch('data/pericopen.json')
                .then(response => response.json())
                .then(data => { App._pericopen = data || {}; })
                .catch(() => { App._pericopen = {}; })
                .finally(() => { App._pericopenPromise = null; });
        }
        if (App._pericopenPromise) await App._pericopenPromise;
        if (!ownsRender()) return false;

        // Vanaf hier publiceert alleen de nog actuele render naar DOM en app-state.
        if (updatesChapterChrome) App._closeOpvConcept(false);
        App._currentPrimaryEditionCode = primaryEditionCode;
        DataLoader.prefetchAdjacent(bookId, chapterNum);
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
        App._updateEthiopicBanner(book);
        App._updateDatingBox(book, renderGeneration);

        // Boek- en hoofdstukinleiding worden nu INLINE in de tekstkolom getoond
        // (zie hieronder), niet meer in een apart frame.
        const bookIntroEl = document.getElementById('book-intro');
        if (bookIntroEl) bookIntroEl.style.display = 'none';
        const introFrame = document.getElementById('chapter-intro');
        if (introFrame) introFrame.style.display = 'none';
        }  // einde if(!append): bovenstaande chrome alleen bij normaal renderen

        const pericMap = {};
        for (const p of (isExternalTranslation ? [] : ((App._pericopen && App._pericopen[bookId]) || []))) {
            if (p.c === chapterNum) pericMap[p.v] = p.t;
        }

        // Verzen renderen
        const container = document.getElementById('verses-container');
        // sink = waar de nieuwe nodes heen gaan. Bij prepend bouwen we eerst in een
        // fragment, en plaatsen dat daarna bovenaan (met scroll-compensatie).
        const sink = prepend ? document.createDocumentFragment() : container;
        if (!append && !prepend) {
            container.innerHTML = '';
            if (unavailableParallelNames.length) {
                const unavailable = document.createElement('div');
                unavailable.className = 'parallel-editions-unavailable';
                unavailable.textContent = `Niet beschikbaar voor dit hoofdstuk: ${unavailableParallelNames.join(', ')}.`;
                container.appendChild(unavailable);
            }
        }
        let opvChapterHeadingId = 'chapter-title';
        if ((append || prepend) && primaryEditionCode === 'nl-opv') {
            container.querySelectorAll(
                '.opv-reading-flow[aria-labelledby="chapter-title"]'
            ).forEach(existingFlow => {
                const existingBook = existingFlow.dataset.book;
                const existingChapter = existingFlow.dataset.chapter;
                const headingId = `opv-chapter-heading-${existingBook}-${existingChapter}`;
                let heading = document.getElementById(headingId);
                if (!heading) {
                    heading = document.createElement('h2');
                    heading.id = headingId;
                    heading.className = 'opv-continuous-heading';
                    const bookName = (App._contNames && App._contNames[existingBook]) || existingBook;
                    heading.textContent = `${bookName} ${existingChapter}`;
                    existingFlow.before(heading);
                }
                existingFlow.setAttribute('aria-labelledby', headingId);
            });
        }
        if (append || prepend) {
            // Doorlopend lezen: scheidingskop voor het toegevoegde hoofdstuk
            const isOpvChapter = primaryEditionCode === 'nl-opv';
            const sep = document.createElement(isOpvChapter ? 'h2' : 'div');
            sep.className = 'chapter-separator';
            sep.textContent = `${book.nameDutch} ${chapterNum}`;
            sep.dataset.book = bookId;
            sep.dataset.chapter = chapterNum;
            if (isOpvChapter) {
                opvChapterHeadingId = `opv-chapter-heading-${bookId}-${chapterNum}`;
                sep.id = opvChapterHeadingId;
            }
            sink.appendChild(sep);
        }

        // Boekinleiding inline in de tekstkolom (alleen bij hoofdstuk 1, onder de
        // hoofdstukkop), zichtbaar via instelling (body.show-book-intro)
        if (!isExternalTranslation && chapterNum === 1 && book.bookIntro && (book.bookIntro.text2026 || book.bookIntro.text1637)) {
            const bIntro = document.createElement('div');
            bIntro.className = 'book-intro-inline';
            bIntro.dataset.book = bookId;
            bIntro.innerHTML = '<span class="book-intro-label">Boekinleiding:</span> ' +
                (book.bookIntro.text2026 || book.bookIntro.text1637);
            sink.appendChild(bIntro);
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

        if (primaryEditionCode === 'nl-opv') {
            App._renderOpvReadingFlow(
                chapter, book, bookId, chapterNum, sink, parallelEditions,
                opvChapterHeadingId
            );
            if (prepend) {
                const scroller = App._getScroller();
                const prevH = scroller ? scroller.scrollHeight : 0;
                const prevTop = scroller ? scroller.scrollTop : 0;
                container.insertBefore(sink, container.firstChild);
                if (scroller) scroller.scrollTop = prevTop + (scroller.scrollHeight - prevH);
            }
            if (updatesChapterChrome) renderOwner.committed = true;
            App._finishChapterRender(bookId, chapterNum, append, prepend);
            return true;
        }

        for (const verse of chapter.verses) {
            // Pericoop-kop vóór dit vers?
            if (pericMap[verse.number]) {
                const h = document.createElement('div');
                h.className = 'pericope-heading';
                // Pas vertalingsopties (Godsnaam) ook op de kop toe, zodat de
                // perikoopkopjes synchroon lopen met de tekst (JAHWEH/HEERE/…).
                const pTitle = pericMap[verse.number];
                if (typeof Opties !== 'undefined' && Opties.transformOV) {
                    h.innerHTML = Opties.transformOV(pTitle, book.testament);
                } else {
                    h.textContent = pTitle;
                }
                sink.appendChild(h);
            }
            const row = document.createElement('div');
            row.className = 'verse-row';
            // Statuskleur volgt de enige bron (VERIFIED_CHAPTERS): een nagekeken hoofdstuk
            // toont 'final' (groen), anders de redactionele status van het vers zelf.
            row.dataset.status = primaryEditionCode === 'nl-ov' && App._isVerified(bookId, chapterNum)
                ? 'final'
                : (verse.status || 'empty');
            row.dataset.book = bookId;
            row.dataset.chapter = chapterNum;
            row.dataset.verse = verse.number;

            // Hebreeuws/Grieks kolom — klikbare woorden met Strong's
            const showStrongs = typeof Opties !== 'undefined' && Opties.state.strongs === 'aan';
            let hebrewHtml;
            const isGeez = book.testament === 'ET';
            if (verse.grondtekst && verse.grondtekst.length > 0) {
                const words = verse.grondtekst.map(w => {
                    const translit = w.transliteratie || '';
                    const gloss = w.gloss || '';
                    // Apocriefen hebben geen Strong's — toon dan lemma als subtext (of niets)
                    const strongs = w.strongs || '';
                    const subText = strongs || w.lemma || '';
                    const dataAttr = strongs ? ` data-strongs="${strongs}"` : '';
                    const subHtml = subText ? `<br><span class="strongs-sub">${subText}</span>` : '';
                    const attr = v => String(v == null ? '' : v).replace(/"/g, '&quot;');
                    // Ge'ez heeft geen Strong's → eigen OV-strongs (OVG, uit Dillmann); klikbaar via geez-word
                    if (isGeez) {
                        const ovg = w.strongs ? `<br><span class="strongs-sub ov-strongs">${attr(w.strongs)}</span>` : '';
                        return `<span class="strongs-word geez-word" data-geez="${attr(w.woord)}" data-translit="${attr(translit)}" data-betekenis="${attr(w.betekenis)}" data-strongs="${attr(w.strongs || '')}">${w.woord}${ovg}</span>`;
                    }
                    // Latijn (4 Ezra) heeft geen Strong's → eigen OV-strongs (OVL, uit Lewis & Short)
                    if (bookId === '4ezra') {
                        const ovl = w.strongs ? `<br><span class="strongs-sub ov-strongs">${attr(w.strongs)}</span>` : '';
                        return `<span class="strongs-word latin-word" data-lemma="${attr(w.lemma)}" data-betekenis="${attr(w.betekenis)}" data-strongs="${attr(w.strongs || '')}">${w.woord}${ovl}</span>`;
                    }
                    return `<span class="strongs-word"${dataAttr} data-transliteratie="${translit}" data-gloss="${gloss}">${w.woord}${subHtml}</span>`;
                }).join(' ');
                // Schrift-richting/taal per grondtekst: Hebreeuws (OT) = RTL; Grieks
                // (NT + apocriefen) en Ge'ez (Ethiopisch) = LTR; 4 Ezra = Latijn.
                const t = book.testament;
                let langAttr = '';
                if (bookId === '4ezra') langAttr = ' lang="la"';
                else if (t === 'ET') langAttr = ' lang="gez"';
                else if (t === 'NT' || t === 'AP') langAttr = ' lang="grc"';
                hebrewHtml = `<span class="hebrew-text"${langAttr}>${words}</span>`;
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
            if (!isExternalTranslation && typeof Opties !== 'undefined') openVertaling = Opties.transformOV(openVertaling, book.testament);
            // Optioneel: geografische locaties markeren (nu Genesis)
            if (!isExternalTranslation && typeof Opties !== 'undefined' && Opties.markeerGeo) openVertaling = Opties.markeerGeo(openVertaling, bookId, chapterNum, verse.number);
            // Optioneel: Bijbelse maten vervangen door metrisch of imperiaal
            if (!isExternalTranslation && typeof Opties !== 'undefined' && Opties.rekenMaten) openVertaling = Opties.rekenMaten(openVertaling, bookId, chapterNum, verse.number);
            // Optioneel: "het negende uur" vervangen door moderne kloktijd.
            // Het testament bepaalt of de nacht drie of vier waken telt.
            if (!isExternalTranslation && typeof Opties !== 'undefined' && Opties.rekenTijden) openVertaling = Opties.rekenTijden(openVertaling, bookId, chapterNum, verse.number, book.testament);

            // Alleen gecontroleerde koppelingen staan inline in de Nederlandse OV-tekst.
            // Nooit een extra grondtekstregel: de lezer ziet uitsluitend aanklikbare nummers
            // direct na het Nederlandse woord waarop de koppeling betrekking heeft.
            let sv1888Text = verse.textSV1888_html || verse.textSV1888 || '';
            if (showStrongs && verse.woordnummers && verse.woordnummers.length > 0) {
                openVertaling = this.renderStrongLinks(openVertaling, verse.woordnummers);
            }

            // Diff-kolom: toon phrase-level wijzigingen als "oud → nieuw"
            let diffHtml = '';
            if (verse.phraseDiff && verse.phraseDiff.length > 0) {
                diffHtml = verse.phraseDiff.map(d => {
                    // Sommige geïmporteerde revisies dragen meerdere principes als array.
                    // De leesweergave mag daardoor nooit vóór de initiaal-rendering afbreken.
                    const principe = Array.isArray(d.principe)
                        ? (d.principe[0] || '')
                        : String(d.principe || '');
                    const badge = principe ? `<a class="principe-badge cat-${principe[0]}" href="principes.html#${principe}" title="${principe}">${principe}</a>` : '';
                    const escOld = (d.old || '').replace(/'/g, "\\'");
                    const escNew = (d.new || '').replace(/'/g, "\\'");
                    const escPrincipe = principe.replace(/'/g, "\\'");
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

            let editionTextHtml = openVertaling;
            if (parallelEditions.length) {
                const primaryName = translationMeta ? translationMeta.naam : 'Open Vertaling';
                const layout = (typeof Opties !== 'undefined' && Opties.state.kolomLayout === 'eronder') ? 'eronder' : 'naast';
                const parallelHtml = parallelEditions.map(item => {
                    const parallelVerse = item.verses.get(Number(verse.number));
                    if (!parallelVerse) return '';
                    const text = parallelVerse.text2026_html || parallelVerse.text2026 || '';
                    const meta = item.meta || { naam: item.code, taal: '', richting: 'ltr' };
                    const safeTextOnly = item.code === 'nl-opv';
                    return `<section class="parallel-edition" data-editie="${App._escapeStrongHtml(item.code)}" data-edition-label="${App._escapeStrongHtml(meta.naam)}" lang="${App._escapeStrongHtml(meta.taal || '')}" dir="${meta.richting === 'rtl' ? 'rtl' : 'ltr'}"${safeTextOnly ? ' data-opv-parallel-text="true"' : ''}>${safeTextOnly ? '' : text}</section>`;
                }).join('');
                editionTextHtml = `<div class="edition-comparison" data-layout="${layout}" style="--edition-count:${parallelEditions.length + 1}">` +
                    `<section class="parallel-edition primary-edition" data-editie="${App._escapeStrongHtml(primaryEditionCode)}" data-edition-label="${App._escapeStrongHtml(primaryName)}">${openVertaling}</section>` +
                    parallelHtml + '</div>';
            }

            row.innerHTML = `
                <div class="verse-num" data-col="num" title="Klik voor status">${verse.number}</div>
                <div class="verse-cell col-1637" data-col="1637">${verse.text1637_html || verse.text1637}</div>
                <div class="verse-cell col-margin1637" data-col="margin1637">${margin1637Html}</div>
                <div class="verse-cell col-sv1888" data-col="sv1888">${sv1888Text}</div>
                <div class="verse-cell col-marginSV1888" data-col="marginSV1888">${marginSV1888Html}</div>
                <div class="verse-cell col-2026" data-col="2026"${translationMeta ? ` lang="${App._escapeStrongHtml(translationMeta.taal)}" dir="${translationMeta.richting === 'rtl' ? 'rtl' : 'ltr'}"` : ''}>${editionTextHtml}</div>
                <div class="verse-cell col-margin2026" data-col="margin2026">${margin2026Html}</div>
                <div class="verse-cell col-hebrew" data-col="hebrew">${hebrewHtml}</div>
                <div class="verse-cell col-diff" data-col="diff">${diffHtml}</div>
                <div class="verse-cell col-noteDiff" data-col="noteDiff">${noteDiffHtml}</div>
            `;

            for (const item of parallelEditions) {
                if (item.code !== 'nl-opv') continue;
                const parallelVerse = item.verses.get(Number(verse.number));
                const parallel = row.querySelector('.parallel-edition[data-editie="nl-opv"]');
                if (parallel && parallelVerse) {
                    App._appendOpvSegments(parallel, parallelVerse);
                }
            }

            sink.appendChild(row);
            if (!isExternalTranslation) Editor.attachVerseListeners(row, bookId, chapterNum, verse.number);
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

        if (updatesChapterChrome) renderOwner.committed = true;
        App._finishChapterRender(bookId, chapterNum, append, prepend);
        return true;
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
            const reducedOpvMotion = row.classList.contains('opv-verse') &&
                window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            row.scrollIntoView({ behavior: reducedOpvMotion ? 'auto' : 'smooth', block: 'center' });
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
            if (!reducedOpvMotion) {
                row.classList.add('verse-flash');
                setTimeout(() => row.classList.remove('verse-flash'), 1700);
            }
        };
        setTimeout(tryFocus, 60);
    },

    // Hoofdstuktitel (met concept-marker) zetten — gedeeld door render + scroll-spy
    _setTitle(bookId, chapterNum) {
        const titleEl = document.getElementById('chapter-title');
        if (!titleEl) return;
        const name = (App._contNames && App._contNames[bookId]) || bookId;
        const isOpenVertaling = typeof TekstEditie === 'undefined' || TekstEditie.code() === 'nl-ov';
        const verified = App._isVerified(bookId, chapterNum);
        titleEl.textContent = `${name} ${chapterNum}`;
        titleEl.classList.toggle('chapter-unverified', isOpenVertaling && !verified);
        if (isOpenVertaling && !verified) {
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
    _afterRenderContinuous(append, prepend, bookId, chapterNum) {
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
            App._contLast = { bookId, chapterNum: Number(chapterNum) };
            App._contFirst = { bookId, chapterNum: Number(chapterNum) };
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
        const last = App._contLast && { ...App._contLast };
        const renderOwner = App._renderOwner;
        if (!last || !renderOwner || !renderOwner.committed ||
            !App._isCurrentRenderOwner(renderOwner)) return;
        const owner = {
            id: (App._continuousOwnerSequence = (App._continuousOwnerSequence || 0) + 1),
            direction: 'next',
            editionCode: renderOwner.editionCode,
            edge: last,
            renderOwner,
        };
        App._continuousOwner = owner;
        App._contLoading = true;
        try {
            const manifest = await DataLoader.loadManifest();
            if (!App._isCurrentContinuousOwner(owner)) return;
            const mode = (window.Opties && Opties.state && Opties.state.boekvolgorde) || 'canoniek';
            const orderIds = (typeof getFlatBookOrder === 'function')
                ? getFlatBookOrder(mode, manifest) : manifest.books.map(b => b.id);
            const byId = Object.fromEntries(manifest.books.map(b => [b.id, b]));
            const cur = byId[last.bookId];
            const primaryOpv = typeof TekstEditie !== 'undefined' && TekstEditie.code() === 'nl-opv';
            let chs = (cur && cur.chaptersIncluded) || [];
            if (primaryOpv) {
                const meta = await TekstEditie.metadata('nl-opv');
                if (!App._isCurrentContinuousOwner(owner)) return;
                chs = (meta && meta.gepubliceerdeHoofdstukken &&
                    meta.gepubliceerdeHoofdstukken[last.bookId]) || [];
            }
            const idx = chs.indexOf(last.chapterNum);
            let nextBook = null, nextCh = null;
            if (idx >= 0 && idx < chs.length - 1) {
                nextBook = last.bookId; nextCh = chs[idx + 1];
            } else if (!primaryOpv) {
                const bi = orderIds.indexOf(last.bookId);
                const nb = (bi >= 0 && bi < orderIds.length - 1) ? byId[orderIds[bi + 1]] : null;
                if (nb && nb.chaptersIncluded && nb.chaptersIncluded.length) {
                    nextBook = nb.id; nextCh = nb.chaptersIncluded[0];
                }
            }
            if (nextCh != null) {
                const rendered = await App.renderChapter(nextBook, nextCh, { append: true, owner });
                if (rendered !== false && App._isCurrentContinuousOwner(owner)) {
                    App._contLast = { bookId: nextBook, chapterNum: nextCh };
                }
            }
        } catch (e) { console.warn('[doorlopend] laden volgende hoofdstuk faalde:', e); }
        finally {
            if (App._continuousOwner === owner) {
                App._continuousOwner = null;
                App._contLoading = false;
            }
        }
    },

    async _loadPrevContinuous() {
        if (App._contLoading || localStorage.getItem('doorlopend') !== 'true') return;
        const first = App._contFirst && { ...App._contFirst };
        const renderOwner = App._renderOwner;
        if (!first || !renderOwner || !renderOwner.committed ||
            !App._isCurrentRenderOwner(renderOwner)) return;
        const owner = {
            id: (App._continuousOwnerSequence = (App._continuousOwnerSequence || 0) + 1),
            direction: 'previous',
            editionCode: renderOwner.editionCode,
            edge: first,
            renderOwner,
        };
        App._continuousOwner = owner;
        App._contLoading = true;
        try {
            const manifest = await DataLoader.loadManifest();
            if (!App._isCurrentContinuousOwner(owner)) return;
            const mode = (window.Opties && Opties.state && Opties.state.boekvolgorde) || 'canoniek';
            const orderIds = (typeof getFlatBookOrder === 'function')
                ? getFlatBookOrder(mode, manifest) : manifest.books.map(b => b.id);
            const byId = Object.fromEntries(manifest.books.map(b => [b.id, b]));
            const cur = byId[first.bookId];
            const primaryOpv = typeof TekstEditie !== 'undefined' && TekstEditie.code() === 'nl-opv';
            let chs = (cur && cur.chaptersIncluded) || [];
            if (primaryOpv) {
                const meta = await TekstEditie.metadata('nl-opv');
                if (!App._isCurrentContinuousOwner(owner)) return;
                chs = (meta && meta.gepubliceerdeHoofdstukken &&
                    meta.gepubliceerdeHoofdstukken[first.bookId]) || [];
            }
            const idx = chs.indexOf(first.chapterNum);
            let prevBook = null, prevCh = null;
            if (idx > 0) {
                prevBook = first.bookId; prevCh = chs[idx - 1];
            } else if (!primaryOpv) {
                const bi = orderIds.indexOf(first.bookId);
                const pb = (bi > 0) ? byId[orderIds[bi - 1]] : null;
                if (pb && pb.chaptersIncluded && pb.chaptersIncluded.length) {
                    prevBook = pb.id; prevCh = pb.chaptersIncluded[pb.chaptersIncluded.length - 1];
                }
            }
            if (prevCh != null) {
                const rendered = await App.renderChapter(prevBook, prevCh, { prepend: true, owner });
                if (rendered !== false && App._isCurrentContinuousOwner(owner)) {
                    App._contFirst = { bookId: prevBook, chapterNum: prevCh };
                }
            }
        } catch (e) { console.warn('[doorlopend] vorige hoofdstuk laden faalde:', e); }
        finally {
            if (App._continuousOwner === owner) {
                App._continuousOwner = null;
                App._contLoading = false;
            }
        }
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
        // replaceState vuurt geen 'hashchange' → mobiele topbalk-knop zelf bijwerken,
        // anders blijft die het oude hoofdstuk tonen tijdens doorlopend scrollen.
        if (typeof MobileNav !== 'undefined' && MobileNav.syncFromState) {
            try { MobileNav.syncFromState(); } catch (e) {}
        }
        // Harde koppeling audio ↔ scrollpositie: de voorleesspeler volgt het
        // hoofdstuk dat in beeld is. Alleen wanneer er NIET wordt afgespeeld —
        // tijdens het voorlezen scrollt de tekst zelf mee, dan niet resetten.
        const audioEl = document.getElementById('audio-el');
        if (!audioEl || audioEl.paused) App._updateAudioPlayer(bookId, ch);
    },

    // === Versmarkering tijdens voorlezen ===
    // De markering verschijnt ALLEEN tijdens audio-voorlezen en staat exact op het
    // vers dat klinkt — op basis van een per-vers tijdsbestand
    // (data/audio-timing/{boek}/{hfdst}-{m|v}.json: [{v,t}], t = starttijd in sec).
    // Is er geen tijdsbestand, dan tonen we NIETS (liever geen markering dan een gok).
    _clearVerseFocus() {
        if (App._focusedRow) { App._focusedRow.classList.remove('verse-focus'); App._focusedRow = null; }
    },

    async _loadAudioTiming(bookId, ch, voice) {
        const key = `${bookId}/${ch}-${voice}`;
        App._timingCache = App._timingCache || {};
        if (key in App._timingCache) return App._timingCache[key];
        let data = null;
        try {
            const r = await fetch(`data/audio-timing/${bookId}/${ch}-${voice}.json`);
            if (r.ok) {
                const j = await r.json();
                const arr = Array.isArray(j) ? j : (j.verses || []);
                data = arr.map(x => ({ v: x.v != null ? x.v : x.verse, t: x.t != null ? x.t : x.start }))
                          .filter(x => x.v != null && x.t != null)
                          .sort((a, b) => a.t - b.t);
                if (!data.length) data = null;
            }
        } catch (e) { data = null; }
        App._timingCache[key] = data;
        return data;
    },

    // Bepaal het versnummer dat NU klinkt, binnen het opgegeven (spelende) hoofdstuk.
    // Exact via tijdsbestand; anders een schatting op tekstlengte BINNEN dit hoofdstuk.
    _currentAudioVerse(bookId, ch, voice, t, duration) {
        const timing = App._timingCache && App._timingCache[`${bookId}/${ch}-${voice}`];
        if (timing && timing.length) {
            let cur = timing[0].v;
            for (const seg of timing) { if (t >= seg.t) cur = seg.v; else break; }
            return cur;
        }
        // Fallback (nog geen tijdsbestand): schat BINNEN dit hoofdstuk, nooit erbuiten.
        if (!duration) return null;
        const rows = Array.from(document.querySelectorAll(
            `#verses-container .verse-row[data-book="${bookId}"][data-chapter="${ch}"]`));
        if (!rows.length) return null;
        let cum = 0;
        const map = rows.map(r => { cum += ((r.textContent || '').trim().length) || 1; return { v: parseInt(r.dataset.verse, 10), end: cum }; });
        const pos = (t / duration) * cum;
        for (const m of map) { if (pos < m.end) return m.v; }
        return map[map.length - 1].v;
    },

    // Markeer (en scroll naar) het vers dat klinkt — strikt binnen het spelende
    // hoofdstuk, dus geen wegspringen naar een ander hoofdstuk in doorlopend lezen.
    _followAudio(bookId, ch, voice, t, duration) {
        const cur = App._currentAudioVerse(bookId, ch, voice, t, duration);
        if (cur == null) return;
        const row = document.querySelector(
            `#verses-container .verse-row[data-book="${bookId}"][data-chapter="${ch}"][data-verse="${cur}"]`);
        if (!row || row === App._focusedRow) return;
        if (App._focusedRow) App._focusedRow.classList.remove('verse-focus');
        row.classList.add('verse-focus');
        App._focusedRow = row;
        // Meescrollen, tenzij de gebruiker net handmatig scrolde (~6s rust).
        if (!App._userScrollAt || (Date.now() - App._userScrollAt > 6000)) {
            const reducedOpvMotion = row.classList.contains('opv-verse') &&
                window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            try { row.scrollIntoView({ block: 'center', behavior: reducedOpvMotion ? 'auto' : 'smooth' }); } catch (e) {}
        }
    },

    /* Zet de eerste ECHTE letter van het eerste vers in een <span class="dropcap">.
     * Slaat leidende aanhalingstekens, note-markers (sup) en citaat-spans over,
     * zodat bij een citaat niet het aanhalingsteken wordt vergroot maar de letter. */
    _applyDropcap() {
        const container = document.getElementById('verses-container');
        if (!container) return;
        // Verwijder oude dropcaps (bij hervertonen)
        container.querySelectorAll('.dropcap').forEach(d => {
            d.replaceWith(document.createTextNode(d.dataset.letter || d.textContent));
        });
        // Drop-cap op het EERSTE vers van ELK hoofdstuk (ook in doorlopend lezen,
        // waar meerdere hoofdstukken na elkaar staan).
        const firstVerseRows = container.querySelectorAll('.verse-row[data-verse="1"]');
        const rows = firstVerseRows.length ? firstVerseRows : (container.querySelector('.verse-row') ? [container.querySelector('.verse-row')] : []);
        rows.forEach(row => {
            const cell = row.querySelector('.col-2026');
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
                const after = node.splitText(idx);          // after begint met de letter
                const letter = after.nodeValue[0];
                after.splitText(1);                         // rest = na de letter
                const span = document.createElement('span');
                span.textContent = letter;
                span.dataset.letter = letter;
                if (/^[A-Za-z]$/.test(letter)) {
                    const assetLetter = letter.toUpperCase();
                    span.className = 'dropcap dropcap--penkrul';
                    span.style.setProperty('--dropcap-shape',
                        `url("/images/initialen/vrije-penkrul/${assetLetter}.svg")`);
                    const licht = document.createElement('img');
                    licht.className = 'dropcap-image dropcap-image--light';
                    licht.src = `/images/initialen/vrije-penkrul/${assetLetter}.svg`;
                    licht.alt = '';
                    licht.setAttribute('aria-hidden', 'true');
                    const donker = document.createElement('img');
                    donker.className = 'dropcap-image dropcap-image--dark';
                    donker.src = `/images/initialen/vrije-penkrul/donker/${assetLetter}.svg`;
                    donker.alt = '';
                    donker.hidden = true;
                    donker.setAttribute('aria-hidden', 'true');
                    span.append(licht, donker);
                } else {
                    // Voor letters buiten A–Z blijft de leesbare typografische initiaal staan.
                    span.className = 'dropcap dropcap--fallback';
                }
                after.replaceWith(span);                     // vervang de losse letter-node
                break;
            }
        });
    },

    updateProgress() {
        const rows = document.querySelectorAll('.verse-row');
        if (rows.length === 0) return;

        const opvRows = Array.from(rows).filter(row => row.classList.contains('opv-verse'));
        if (opvRows.length) {
            const counts = {
                concept: 0,
                bron_gecontroleerd: 0,
                taal_gecontroleerd: 0,
                definitief: 0,
            };
            opvRows.forEach(row => {
                const status = row.dataset.status || 'concept';
                if (counts[status] !== undefined) counts[status]++;
            });
            const total = opvRows.length;
            const done = counts.definitief;
            const pct = Math.round((done / total) * 100);
            document.getElementById('progress-fill').style.width = pct + '%';
            document.getElementById('progress-text').textContent =
                `${done}/${total} definitief (${counts.concept} concept, ` +
                `${counts.bron_gecontroleerd} bron gecontroleerd, ` +
                `${counts.taal_gecontroleerd} taal gecontroleerd)`;
            return;
        }

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

// Globaal beschikbaar maken (zoals window.Opties) — handig voor o.a. navigation.js en tests.
if (typeof window !== 'undefined') window.App = App;
