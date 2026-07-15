/* Open Staten Vertaling — chunk-audio speler
 * ------------------------------------------------------------------
 * Speelt een hoofdstuk af uit LOSSE audio-segmenten (chunks) op basis van een
 * manifest, zodat godsnaam (HEERE/JAHWEH/Jehova), kopjes en de boekaankondiging
 * optioneel zijn. Zie docs/superpowers/specs/2026-07-15-chunked-audio-design.md.
 *
 * Volledig achterwaarts compatibel: is er voor een hoofdstuk geen manifest, dan
 * geeft load() null terug en valt de aanroeper terug op de losse-MP3-speler.
 *
 * Deze module raakt window.AUDIO_AVAILABLE NIET aan (die leeft in
 * js/audio-available.js en wordt door de TTS-sessie beheerd).
 */
(function () {
    'use strict';

    var BASE = 'audio';

    function manifestUrl(bookId, chapter, voice) {
        return BASE + '/' + bookId + '/' + chapter + '/' + voice + '/manifest.json';
    }
    function segUrl(bookId, chapter, voice, file) {
        return BASE + '/' + bookId + '/' + chapter + '/' + voice + '/' + file;
    }

    // Standaardinstellingen; lezer-voorkeuren komen uit localStorage.
    function defaultSettings() {
        var s = { divineName: 'heere', headings: false, announce: true };
        try {
            var raw = localStorage.getItem('sv2026_audioChunkOpts');
            if (raw) { var o = JSON.parse(raw); for (var k in o) if (o[k] !== undefined) s[k] = o[k]; }
        } catch (e) {}
        return s;
    }
    function saveSettings(s) {
        try { localStorage.setItem('sv2026_audioChunkOpts', JSON.stringify(s)); } catch (e) {}
    }

    /* Haal het manifest op. Retourneert het geparste object of null (geen chunks). */
    function load(bookId, chapter, voice) {
        return fetch(manifestUrl(bookId, chapter, voice))
            .then(function (r) { return r.ok ? r.json() : null; })
            .catch(function () { return null; });
    }

    /* Zuivere functie: bouw de afspeellijst uit het manifest + instellingen.
     * Elk item: { type, verse?, src, dur, text? }. Eenvoudig te unit-testen. */
    function buildPlaylist(manifest, settings) {
        var s = settings || defaultSettings();
        var out = [];
        var segs = (manifest && manifest.segments) || [];
        for (var i = 0; i < segs.length; i++) {
            var seg = segs[i];
            if (seg.type === 'intro') {
                if (s.announce !== false) out.push({ type: 'intro', src: seg.file, dur: seg.dur || 0 });
            } else if (seg.type === 'heading') {
                if (s.headings) out.push({ type: 'heading', afterVerse: seg.afterVerse, src: seg.file, dur: seg.dur || 0, text: seg.text });
            } else if (seg.type === 'verse') {
                if (seg.divineName) {
                    var key = (s.divineName || 'heere');
                    var vfile = (seg.variants && (seg.variants[key] || seg.variants.heere));
                    var vdur = (seg.dur && typeof seg.dur === 'object') ? (seg.dur[key] || seg.dur.heere || 0) : (seg.dur || 0);
                    if (vfile) out.push({ type: 'verse', verse: seg.verse, src: vfile, dur: vdur, divineName: true });
                } else {
                    out.push({ type: 'verse', verse: seg.verse, src: seg.file, dur: seg.dur || 0 });
                }
            }
        }
        return out;
    }

    function totalDuration(playlist) {
        var t = 0;
        for (var i = 0; i < playlist.length; i++) t += (playlist[i].dur || 0);
        return t;
    }

    /* Controller die één <audio>-element door de afspeellijst stuurt.
     * callbacks: { onVerse(n), onPlay(), onPause(), onEnded(), onTime(elapsed,total) } */
    function createController(audioEl, manifest, settings, callbacks) {
        var cb = callbacks || {};
        var s = settings || defaultSettings();
        var bookId = manifest.book, chapter = manifest.chapter, voice = manifest.voice;
        var playlist = buildPlaylist(manifest, s);
        var idx = 0;
        var destroyed = false;
        var priorDur = 0; // som van dur van reeds afgespeelde segmenten

        function srcFor(item) { return segUrl(bookId, chapter, voice, item.src); }

        function loadIndex(i, autoplay) {
            if (i < 0 || i >= playlist.length) return;
            idx = i;
            priorDur = 0;
            for (var k = 0; k < i; k++) priorDur += (playlist[k].dur || 0);
            var item = playlist[i];
            audioEl.src = srcFor(item);
            audioEl.load();
            if (item.type === 'verse' && cb.onVerse) cb.onVerse(item.verse);
            if (autoplay) audioEl.play().catch(function () {});
        }

        function onEnded() {
            if (destroyed) return;
            if (idx < playlist.length - 1) loadIndex(idx + 1, true);
            else if (cb.onEnded) cb.onEnded();
        }
        function onTime() {
            if (cb.onTime) cb.onTime(priorDur + (audioEl.currentTime || 0), totalDuration(playlist));
        }
        function onPlay() { if (cb.onPlay) cb.onPlay(); }
        function onPause() { if (cb.onPause) cb.onPause(); }

        audioEl.addEventListener('ended', onEnded);
        audioEl.addEventListener('timeupdate', onTime);
        audioEl.addEventListener('play', onPlay);
        audioEl.addEventListener('pause', onPause);

        loadIndex(0, false);

        return {
            play: function () { audioEl.play().catch(function () {}); },
            pause: function () { audioEl.pause(); },
            isPlaying: function () { return !audioEl.paused; },
            currentVerse: function () { var it = playlist[idx]; return it ? it.verse : null; },
            /* Spring naar het segment dat vers N voorleest. */
            seekToVerse: function (n) {
                for (var i = 0; i < playlist.length; i++) {
                    if (playlist[i].type === 'verse' && playlist[i].verse === n) { loadIndex(i, !audioEl.paused); return true; }
                }
                return false;
            },
            /* Pas instellingen toe (godsnaam/kopjes/intro) zonder de plek te verliezen. */
            setSettings: function (newSettings) {
                var curVerse = (playlist[idx] && playlist[idx].verse) || null;
                var wasPlaying = !audioEl.paused;
                s = newSettings; saveSettings(s);
                playlist = buildPlaylist(manifest, s);
                var target = 0;
                if (curVerse != null) {
                    for (var i = 0; i < playlist.length; i++) {
                        if (playlist[i].type === 'verse' && playlist[i].verse >= curVerse) { target = i; break; }
                    }
                }
                loadIndex(target, wasPlaying);
            },
            playlist: function () { return playlist.slice(); },
            totalDuration: function () { return totalDuration(playlist); },
            destroy: function () {
                destroyed = true;
                audioEl.removeEventListener('ended', onEnded);
                audioEl.removeEventListener('timeupdate', onTime);
                audioEl.removeEventListener('play', onPlay);
                audioEl.removeEventListener('pause', onPause);
            }
        };
    }

    window.ChunkedAudio = {
        load: load,
        buildPlaylist: buildPlaylist,
        totalDuration: totalDuration,
        createController: createController,
        defaultSettings: defaultSettings,
        saveSettings: saveSettings,
        _manifestUrl: manifestUrl
    };
})();
