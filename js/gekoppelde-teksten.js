/* Gekoppelde Bijbelteksten voor de wiki.
 * De tekst zelf blijft uit embed.js komen; hier staan alleen presentatie,
 * luie belading en de bediening voor meer of minder context. */
(function (global) {
    'use strict';

    function refParts(ref) {
        var m = String(ref || '').trim().match(/^(\S+)\s+(\d+):(\d+)(?:\s*-\s*(\d+))?$/);
        if (!m) return null;
        return {
            boek: m[1].toLowerCase(),
            hoofdstuk: Number(m[2]),
            van: Number(m[3]),
            tot: Number(m[4] || m[3])
        };
    }

    function labelVoor(ref, parts, boeknamen) {
        if (!parts) return String(ref || 'Onbekende vindplaats');
        var boek = (boeknamen && boeknamen[parts.boek]) ||
            parts.boek.charAt(0).toUpperCase() + parts.boek.slice(1);
        return boek + ' ' + parts.hoofdstuk + ':' + parts.van +
            (parts.tot !== parts.van ? '-' + parts.tot : '');
    }

    function linkVoor(ref, parts) {
        if (!parts) return 'index.html#' + encodeURIComponent(String(ref || ''));
        return 'index.html#' + parts.boek + '/' + parts.hoofdstuk + '/' + parts.van;
    }

    function element(tag, className, tekst) {
        var node = document.createElement(tag);
        if (className) node.className = className;
        if (tekst !== undefined) node.textContent = tekst;
        return node;
    }

    function markeerVerzen(teksthouder, parts, metContext) {
        var verzen = teksthouder.querySelectorAll('.osv-vers');
        for (var i = 0; i < verzen.length; i++) {
            var nummer = verzen[i].querySelector('.osv-num');
            var isFocus = nummer && Number(nummer.textContent) >= parts.van &&
                Number(nummer.textContent) <= parts.tot;
            verzen[i].classList.add(isFocus ? 'focus-vers' : 'context-vers');
            if (!metContext && !isFocus) verzen[i].classList.add('gt-verborgen');
        }
    }

    function laad(item, metContext) {
        var parts = item._gtParts;
        var teksthouder = item.querySelector('.gt-vers-tekst');
        var plus = item.querySelector('.gt-plus');
        var min = item.querySelector('.gt-min');
        var verzoek = (item._gtVerzoek || 0) + 1;
        item._gtVerzoek = verzoek;

        teksthouder.innerHTML = '<span class="osv-laden">…</span>';
        if (!parts || !global.OSV || typeof global.OSV.cite !== 'function') {
            teksthouder.innerHTML = '<span class="osv-fout">Deze tekst kon niet geladen worden.</span>';
            plus.hidden = true;
            min.hidden = true;
            return Promise.resolve();
        }

        var van = metContext ? Math.max(1, parts.van - 2) : parts.van;
        var tot = metContext ? parts.tot + 2 : parts.tot;
        var citeRef = parts.boek + ' ' + parts.hoofdstuk + ':' + van +
            (tot !== van ? '-' + tot : '');

        return global.OSV.cite(citeRef, { link: false }).then(function (resultaat) {
            if (item._gtVerzoek !== verzoek) return;
            teksthouder.innerHTML = resultaat.html;
            markeerVerzen(teksthouder, parts, metContext);
            plus.hidden = metContext;
            min.hidden = !metContext;
            item.setAttribute('data-level', metContext ? '1' : '0');
        }).catch(function () {
            if (item._gtVerzoek !== verzoek) return;
            teksthouder.innerHTML = '<span class="osv-fout">Deze tekst kon niet geladen worden.</span>';
            plus.hidden = true;
            min.hidden = true;
        });
    }

    function maakItem(ref, opties) {
        var parts = refParts(ref);
        var item = element('li', 'gt-vers');
        item.setAttribute('data-ref', ref);
        item.setAttribute('data-level', '0');
        item._gtParts = parts;

        var kop = element('div', 'gt-vers-kop');
        var link = element('a', '', labelVoor(ref, parts, opties.boeknamen));
        link.href = linkVoor(ref, parts);
        link.target = '_top';
        kop.appendChild(link);

        var knoppen = element('span', 'gt-knoppen');
        var min = element('button', 'gt-min', '−');
        min.type = 'button';
        min.hidden = true;
        min.setAttribute('aria-label', 'Minder context');
        var plus = element('button', 'gt-plus', '+');
        plus.type = 'button';
        plus.setAttribute('aria-label', 'Meer context eromheen');
        knoppen.appendChild(min);
        knoppen.appendChild(plus);
        kop.appendChild(knoppen);
        item.appendChild(kop);

        var tekst = element('div', 'gt-vers-tekst osv-cite');
        tekst.innerHTML = '<span class="osv-laden">…</span>';
        item.appendChild(tekst);

        plus.addEventListener('click', function () { laad(item, true); });
        min.addEventListener('click', function () { laad(item, false); });
        return item;
    }

    function render(container, references, options) {
        options = options || {};
        if (!container) return;
        var oldMore = container.nextElementSibling;
        if (oldMore && oldMore.classList.contains('gt-meer-teksten')) oldMore.remove();
        container.textContent = '';
        var allReferences = references || [];
        var limit = options.compact ? (options.initialLimit || 8) : allReferences.length;
        references = allReferences.slice(0, limit);
        var items = [];
        for (var i = 0; i < (references || []).length; i++) {
            var item = maakItem(references[i], options);
            container.appendChild(item);
            items.push(item);
        }

        if (!('IntersectionObserver' in global) || !global.IntersectionObserver) {
            for (var j = 0; j < items.length; j++) laad(items[j], false);
            return;
        }

        var observer = new global.IntersectionObserver(function (entries) {
            for (var k = 0; k < entries.length; k++) {
                if (!entries[k].isIntersecting) continue;
                observer.unobserve(entries[k].target);
                laad(entries[k].target, false);
            }
        }, { rootMargin: '400px 0px' });
        for (var n = 0; n < items.length; n++) observer.observe(items[n]);

        if (allReferences.length > references.length) {
            var more = element('button', 'gt-meer-teksten', '+ meer teksten');
            more.type = 'button';
            more.setAttribute('aria-label', 'Meer teksten weergeven');
            more.addEventListener('click', function () {
                var expandedOptions = {};
                for (var key in options) expandedOptions[key] = options[key];
                expandedOptions.compact = false;
                render(container, allReferences, expandedOptions);
            });
            container.insertAdjacentElement('afterend', more);
        }
    }

    global.GekoppeldeTeksten = {
        render: render,
        refParts: refParts
    };
})(window);
