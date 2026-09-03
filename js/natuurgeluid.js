/* Open Vertaling — natuurgeluid onder de voorlezing.
 *
 * Speelt een zachte laag met vogels en wind zolang de voorlezing loopt, en
 * stopt zodra die pauzeert. De laag volgt de hoofdspeler (#audio-el); hij
 * start dus nooit uit zichzelf.
 *
 * Herhaling: de eigenaar wil dat een herhaling pas na ongeveer tien minuten
 * hoorbaar wordt. Daarom worden de opnames aan elkaar geregen in een steeds
 * wisselende volgorde, met een korte overvloeier ertussen. Pas als de hele
 * reeks op is begint hij opnieuw — met genoeg materiaal duurt dat langer dan
 * de tien minuten die gevraagd zijn.
 *
 * Bronnen en licenties staan in data/natuurgeluiden.json; alles moet CC0
 * zijn, want de site is volledig publiek domein en de brondata wordt als
 * download aangeboden.
 *
 * Ontbreekt het databestand of zijn er geen opnames, dan doet deze module
 * niets. De site werkt dus gewoon zonder de geluidsbestanden.
 */
(function () {
    'use strict';

    var SLEUTEL = 'ov_natuurgeluid';         // 'aan' | 'uit'
    var SLEUTEL_VOL = 'ov_natuurgeluid_vol'; // 0..1
    var STANDAARD_VOL = 0.14;                // zacht; het gaat om de voorlezing
    var OVERVLOEI_MS = 2500;
    var MIN_ZONDER_HERHALING_S = 600;        // tien minuten

    var clips = null;      // [{bestand, titel, bron, licentie, seconden}]
    var volgorde = [];     // resterende indexen deze ronde
    var huidige = null;    // het spelende audio-element
    var volgende = null;   // voorgeladen element voor de overvloeier
    var timer = null;
    var actief = false;

    function aan() { return localStorage.getItem(SLEUTEL) === 'aan'; }
    function volume() {
        var v = parseFloat(localStorage.getItem(SLEUTEL_VOL));
        return (isFinite(v) && v >= 0 && v <= 1) ? v : STANDAARD_VOL;
    }

    /* Fisher-Yates; bewust niet met een vaste seed, zodat twee luistersessies
       niet dezelfde volgorde krijgen. */
    function schud(n) {
        var a = [];
        for (var i = 0; i < n; i++) a.push(i);
        for (var j = a.length - 1; j > 0; j--) {
            var k = Math.floor(Math.random() * (j + 1));
            var t = a[j]; a[j] = a[k]; a[k] = t;
        }
        return a;
    }

    function volgendeIndex() {
        if (!volgorde.length) volgorde = schud(clips.length);
        return volgorde.shift();
    }

    function maakElement(clip) {
        var el = new Audio(window.OV_ASSETS.url('audio/natuur/' + clip.bestand));
        el.preload = 'auto';
        el.volume = 0;
        return el;
    }

    /* Lineair vervagen. Geen Web Audio API: die vraagt op iOS een expliciete
       ontgrendeling en dat is hier de moeite niet waard. */
    function vervaag(el, van, naar, ms, klaar) {
        var stappen = Math.max(1, Math.round(ms / 50));
        var i = 0;
        var id = setInterval(function () {
            i++;
            var v = van + (naar - van) * (i / stappen);
            try { el.volume = Math.max(0, Math.min(1, v)); } catch (e) {}
            if (i >= stappen) {
                clearInterval(id);
                if (klaar) klaar();
            }
        }, 50);
        return id;
    }

    function speelVolgende() {
        if (!actief || !clips || !clips.length) return;
        var clip = clips[volgendeIndex()];
        var el = volgende || maakElement(clip);
        volgende = null;
        huidige = el;
        el.play().catch(function () { /* autoplay geweigerd; niet erg */ });
        vervaag(el, 0, volume(), OVERVLOEI_MS);

        // Overvloeien kort voor het einde, zodat er geen stilte valt.
        el.addEventListener('loadedmetadata', function () {
            var duur = el.duration;
            if (!isFinite(duur) || duur <= 0) return;
            var wachtMs = Math.max(1000, (duur * 1000) - OVERVLOEI_MS);
            clearTimeout(timer);
            timer = setTimeout(function () {
                if (!actief) return;
                var oud = el;
                vervaag(oud, oud.volume, 0, OVERVLOEI_MS, function () {
                    try { oud.pause(); oud.src = ''; } catch (e) {}
                });
                speelVolgende();
            }, wachtMs);
        });
        el.addEventListener('error', function () {
            // Ontbrekend bestand mag de voorlezing niet raken; probeer de volgende.
            if (actief) setTimeout(speelVolgende, 200);
        });
    }

    function start() {
        if (actief || !aan() || !clips || !clips.length) return;
        actief = true;
        speelVolgende();
    }

    function stop() {
        actief = false;
        clearTimeout(timer);
        [huidige, volgende].forEach(function (el) {
            if (!el) return;
            try { el.pause(); el.src = ''; } catch (e) {}
        });
        huidige = volgende = null;
    }

    function koppelAanSpeler() {
        var speler = document.getElementById('audio-el');
        if (!speler || speler._natuurGekoppeld) return;
        speler._natuurGekoppeld = true;
        speler.addEventListener('play', start);
        speler.addEventListener('pause', stop);
        speler.addEventListener('ended', stop);
        // Bij het verlaten van de pagina niets laten doorspelen.
        window.addEventListener('pagehide', stop);
        if (!speler.paused) start();
    }

    function laad() {
        fetch('data/natuurgeluiden.json')
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (d) {
                if (!d || !Array.isArray(d.clips) || !d.clips.length) return;
                clips = d.clips;
                volgorde = schud(clips.length);
                var totaal = clips.reduce(function (s, c) { return s + (c.seconden || 0); }, 0);
                if (totaal && totaal < MIN_ZONDER_HERHALING_S) {
                    console.info('[natuurgeluid] ' + Math.round(totaal / 60) +
                        ' min materiaal; herhaling is eerder hoorbaar dan de gewenste tien minuten.');
                }
                koppelAanSpeler();
            })
            .catch(function () { /* geen geluiden: module doet niets */ });
    }

    // Publiek haakje voor een instelling in het optiepaneel.
    window.OVNatuurgeluid = {
        aan: function () { localStorage.setItem(SLEUTEL, 'aan'); koppelAanSpeler(); start(); },
        uit: function () { localStorage.setItem(SLEUTEL, 'uit'); stop(); },
        staatAan: aan,
        volume: function (v) {
            if (v === undefined) return volume();
            localStorage.setItem(SLEUTEL_VOL, String(v));
            if (huidige) { try { huidige.volume = v; } catch (e) {} }
        },
        clips: function () { return clips ? clips.slice() : []; }
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', laad);
    } else {
        laad();
    }
})();
