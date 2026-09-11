/* Citaatopmaak die bewaard blijft maar niet gepubliceerd wordt.
 *
 * In de grote profeten is de citatie uitgezet: de spans (god-speaks,
 * direct-speech, angel-speaks, devil-speaks) blijven in data/<boek>/*.json
 * staan, maar de Open Vertaling toont ze niet. Het werk dat erin zit gaat zo
 * niet verloren; weer aanzetten is het boek uit BOEKEN halen.
 *
 * Werkt op het geladen hoofdstuk, vóór het renderen, zodat leesweergave,
 * parallelweergave, drukversie, kopiëren en export allemaal dezelfde tekst
 * zien. De editor slaat alleen text2026 op, nooit text2026_html, dus de
 * bewaarde opmaak kan hierdoor niet overschreven worden.
 */
(function (global) {
    'use strict';

    var BOEKEN = { jesaja: true, jeremia: true, ezechiel: true };
    var SPRAAK = 'span.god-speaks, span.direct-speech, span.angel-speaks, span.devil-speaks';

    function ontdoe(html) {
        if (!html || html.indexOf('speaks') < 0 && html.indexOf('direct-speech') < 0) return html;
        var t = document.createElement('template');
        t.innerHTML = html;
        var spans = t.content.querySelectorAll(SPRAAK);
        for (var i = 0; i < spans.length; i++) {
            var el = spans[i];
            // <span class="god-speaks"><i>…</i></span>: de <i> hoort bij de
            // span en gaat mee weg; wat erin staat blijft.
            var inhoud = (el.childNodes.length === 1 && el.firstChild.nodeName === 'I') ? el.firstChild : el;
            var ouder = el.parentNode;
            while (inhoud.firstChild) ouder.insertBefore(inhoud.firstChild, el);
            ouder.removeChild(el);
        }
        return t.innerHTML;
    }

    global.CitatieUit = {
        geldt: function (bookId) { return BOEKEN[bookId] === true; },
        ontdoe: ontdoe,
        hoofdstuk: function (ch, bookId) {
            if (!ch || BOEKEN[bookId] !== true || !ch.verses) return ch;
            for (var i = 0; i < ch.verses.length; i++) {
                var v = ch.verses[i];
                if (v && v.text2026_html) v.text2026_html = ontdoe(v.text2026_html);
            }
            return ch;
        }
    };
})(window);
