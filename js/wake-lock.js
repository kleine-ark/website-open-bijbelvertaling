/* Open Vertaling — scherm aan houden tijdens het lezen.
 *
 * Gebruikt de Screen Wake Lock API. Die kent Safari pas vanaf 16.4; op oudere
 * iPads valt dit stil terug op niets-doen (het scherm dimt dan gewoon zoals
 * het systeem wil). Bewust geen alternatieve truc met een verborgen video:
 * dat kost doorlopend accu en is elders in deze codebase niet nodig gebleken.
 *
 * Geladen via topnav.js, alleen op de leespagina's.
 */
(function () {
    'use strict';

    if (!('wakeLock' in navigator)) return;

    var lock = null;
    var gewenst = true;

    function pak() {
        if (!gewenst || lock || document.visibilityState !== 'visible') return;
        navigator.wakeLock.request('screen').then(function (l) {
            lock = l;
            // Het systeem kan de lock zelf loslaten (batterijbesparing, gesprek);
            // dan moet onze verwijzing ook leeg, anders pakken we hem nooit terug.
            l.addEventListener('release', function () { lock = null; });
        }).catch(function () {
            lock = null;   // geweigerd (bijv. accu bijna leeg) — niet erg
        });
    }

    function los() {
        if (!lock) return;
        var l = lock;
        lock = null;
        try { l.release(); } catch (e) { /* al vrijgegeven */ }
    }

    // De lock gaat verloren zodra het tabblad naar de achtergrond gaat;
    // bij terugkeer opnieuw aanvragen.
    document.addEventListener('visibilitychange', function () {
        if (document.visibilityState === 'visible') pak();
        else los();
    });

    window.addEventListener('pagehide', los);

    // Publiek haakje, zodat een instelling dit later kan uitzetten.
    window.OVWakeLock = {
        aan: function () { gewenst = true; pak(); },
        uit: function () { gewenst = false; los(); },
        actief: function () { return !!lock; }
    };

    pak();
})();
