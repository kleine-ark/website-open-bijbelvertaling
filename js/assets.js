/* Open Vertaling — publieke assetlocatie.
 *
 * Alle grote, extern opgeslagen bestanden lopen via deze resolver. Daardoor
 * werkt dezelfde URL in productie, in lokale ontwikkelservers en in de
 * desktop-app. Een toekomstige verhuizing verandert alleen de basis-URL hier.
 * Een host kan vóór dit script window.OV_ASSET_BASE_URL instellen.
 */
(function () {
    'use strict';

    var configuredBaseUrl = window.OV_ASSET_BASE_URL ||
        'https://kleineark.com/assets/openvertaling/';
    var baseUrl = configuredBaseUrl.endsWith('/')
        ? configuredBaseUrl
        : configuredBaseUrl + '/';

    window.OV_ASSETS = Object.freeze({
        baseUrl: baseUrl,
        url: function (path) {
            return new URL(path, baseUrl).href;
        }
    });
})();
