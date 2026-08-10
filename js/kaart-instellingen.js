(function () {
    'use strict';

    var opener = document.getElementById('kaart-instellingen-open');
    var paneel = document.getElementById('kaart-instellingen');
    var sluiter = document.getElementById('kaart-instellingen-sluit');
    if (!opener || !paneel || !sluiter) return;

    function openPaneel() {
        paneel.hidden = false;
        opener.setAttribute('aria-expanded', 'true');
        sluiter.focus();
    }

    function sluitPaneel(herstelFocus) {
        paneel.hidden = true;
        opener.setAttribute('aria-expanded', 'false');
        if (herstelFocus) opener.focus();
    }

    opener.addEventListener('click', function () {
        if (paneel.hidden) openPaneel();
        else sluitPaneel(true);
    });
    sluiter.addEventListener('click', function () { sluitPaneel(true); });
    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && !paneel.hidden) sluitPaneel(true);
    });
})();
