/* stats-inject.js — vult alle aantallen op de site vanuit één bron: data/stats.json
 *
 * Gebruik in HTML:  <span data-stat="verses_total">37.235</span>
 *   - data-stat="key"            → vult de waarde (met NL-duizendscheiding voor getallen)
 *   - data-stat="key" data-stat-format="raw"  → zonder duizendscheiding
 *   - data-stat="key" data-stat-suffix="%"    → voegt suffix toe
 *
 * Zo staan op GEEN enkele pagina nog handmatige aantallen die kunnen afwijken.
 */
(function () {
    function nl(n) {
        return (typeof n === 'number') ? n.toLocaleString('nl-NL') : n;
    }
    function esc(s) {
        return String(s).replace(/[&<>"]/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
        });
    }
    var BADGE_STYLE = 'display:inline-block;background:#d1fae5;color:#065f46;border:1px solid #6ee7b7;padding:5px 12px;border-radius:6px;font-size:13px;font-weight:600;margin:0 8px 6px 0;';
    function apply(stats) {
        document.querySelectorAll('[data-stat]').forEach(function (el) {
            var key = el.getAttribute('data-stat');
            if (!(key in stats)) return;
            var val = stats[key];
            var fmt = el.getAttribute('data-stat-format');
            var text = (fmt === 'raw') ? String(val) : nl(val);
            var suffix = el.getAttribute('data-stat-suffix');
            if (suffix) text += suffix;
            el.textContent = text;
        });
        // Lijsten (bv. de nagekeken-boeken-badges): <ul data-stat-list="verified_books">
        document.querySelectorAll('[data-stat-list]').forEach(function (el) {
            var key = el.getAttribute('data-stat-list');
            if (!Array.isArray(stats[key])) return;
            el.innerHTML = stats[key].map(function (name) {
                return '<li style="' + BADGE_STYLE + '">✓ ' + esc(name) + '</li>';
            }).join('');
        });
    }
    function init() {
        fetch('data/stats.json', { cache: 'no-cache' })
            .then(function (r) { return r.json(); })
            .then(apply)
            .catch(function (e) { console.warn('[stats] kon stats.json niet laden:', e); });
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
