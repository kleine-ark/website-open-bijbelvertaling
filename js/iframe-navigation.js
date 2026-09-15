/* Relatieve documentatielinks openen buiten het wiki-frame.
 * Naslagpagina's houden querylinks binnen hun eigen document.
 */
(function () {
    if (window.self === window.top) return;
    const preserveQuery = document.currentScript.hasAttribute('data-preserve-query');
    document.body.classList.add('in-iframe');
    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('a[href]').forEach(function (link) {
            const href = link.getAttribute('href');
            if (href && !href.startsWith('#') && !href.startsWith('mailto:') &&
                !href.startsWith('http') && !href.startsWith('javascript:') &&
                !(preserveQuery && href.startsWith('?'))) {
                link.target = '_top';
            }
        });
    });
})();
