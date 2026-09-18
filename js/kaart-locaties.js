(function (root, factory) {
    'use strict';
    var api = factory();
    if (typeof module === 'object' && module.exports) module.exports = api;
    else root.KaartLocaties = api;
}(typeof globalThis !== 'undefined' ? globalThis : this, function () {
    'use strict';

    // Voorrang volgt bronidentiteit: gelijknamige plaatsen worden niet samengevoegd.
    var HOOFDPLAATSEN = {
        'geo-jerusalem-15257a': 1200,
        'geo-nazareth-f5884f': 1000,
        'geo-bethlehem-1-112427': 1000,
        'geo-jericho-1-231f80': 1000,
        'geo-capernaum-f2161c': 1000,
        'geo-babylon-1-217d18': 1000,
        'geo-antioch-1-e41ab4': 1000,
        'geo-hebron-85151a': 1000,
        'geo-damascus-69c1d4': 1000,
        'geo-rome-fc8e7a': 1000,
        'geo-egypt-f301ca': 850,
        'geo-canaan-581f0c': 850,
        'geo-assyria-3d1321': 850,
        'geo-babylonia-8394b8': 850,
        'geo-galilee-1-9cf1e8': 850,
        'geo-judea-1-149f13': 850,
        'geo-samaria-2-282dce': 850,
        'geo-jordan-e686c9': 850,
        'geo-euphrates-62dec4': 850,
        'geo-nile-012705': 850,
        'geo-sea-of-galilee-562fcc': 850
    };
    var TYPEN = { 'stad-dorp': 'Stad of dorp', 'land-streek': 'Land of streek', 'rivier-water': 'Rivier of water', 'dal-vlakte': 'Dal of vlakte', berg: 'Berg', eiland: 'Eiland', plaats: 'Plaats' };

    function properties(feature) {
        return feature && (typeof feature.getProperties === 'function' ? feature.getProperties() : feature.properties || feature) || {};
    }

    function normalize(value) {
        return String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('nl').replace(/[^\p{L}\p{N}]+/gu, ' ').trim();
    }

    function matchingRefs(feature, filters) {
        var f = filters || {};
        return (properties(feature).refs || []).filter(function (ref) {
            return (!f.boek || ref.boek === f.boek) && (!f.hoofdstuk || Number(ref.hoofdstuk) === Number(f.hoofdstuk));
        });
    }

    function matchesFilter(feature, filters) {
        var f = filters || {}, p = properties(feature);
        var zekerheid = ['zeker', 'waarschijnlijk'].indexOf(p.zekerheid) >= 0 ? p.zekerheid : 'onzeker';
        return f[zekerheid] !== false && ((!f.boek && !f.hoofdstuk) || matchingRefs(feature, f).length > 0);
    }

    function importance(feature, filters) {
        var p = properties(feature), f = filters || {};
        var breed = /^(land|streek|regio|land-streek|rivier|zee|meer|rivier-water)$/.test(p.type || '');
        var frequentie = Math.min(150, (p.refs || []).length * 3);
        var relevantie = f.boek || f.hoofdstuk ? Math.min(180, matchingRefs(feature, f).length * 30) : 0;
        return (HOOFDPLAATSEN[p.id] || 0) + (breed ? 35 : 0) + frequentie + relevantie;
    }

    function scale(zoom) {
        var id = zoom < 6 ? 'overzicht' : zoom < 9 ? 'regio' : zoom < 12 ? 'omgeving' : 'detail';
        return { id: id, label: { overzicht: 'Overzicht', regio: 'Regio', omgeving: 'Omgeving', detail: 'Detail' }[id], hint: id === 'detail' ? 'Namen krijgen ruimte waar dat past' : 'Inzoomen toont meer namen' };
    }

    function presentation(feature, zoom, filters, selected) {
        var niveau = scale(zoom).id, score = importance(feature, filters), major = score >= 800;
        var visible = matchesFilter(feature, filters);
        var label = selected || niveau === 'detail' || (niveau === 'omgeving' && score >= 6) || (niveau === 'regio' && score >= 90) || major;
        var radius = selected ? 8 : niveau === 'overzicht' ? (major ? 4 : 1.6) : niveau === 'regio' ? (major ? 5 : 2.4) : niveau === 'omgeving' ? (major ? 5.5 : 3.4) : 4.5;
        return { visible: visible, label: visible && label, radius: radius, priority: selected && visible ? 10000 : score, major: major };
    }

    function compareFeatures(a, b, filters, selectedId) {
        var pa = properties(a), pb = properties(b);
        var sa = pa.id === selectedId && matchesFilter(a, filters), sb = pb.id === selectedId && matchesFilter(b, filters);
        return Number(sb) - Number(sa) || importance(b, filters) - importance(a, filters) || String(pa.id || '').localeCompare(String(pb.id || ''));
    }

    function search(features, query, filters, options) {
        var needle = normalize(query), matches = [], outsideCount = 0;
        if (!needle) return { matches: [], outsideCount: 0, total: 0 };
        var compact = needle.replace(/ /g, '');
        (features || []).forEach(function (feature) {
            var p = properties(feature), naam = normalize(p.naam);
            var terms = [p.naam, p.moderneNaam].concat(p.aliases || []).map(normalize);
            if (!terms.some(function (term) { return term.indexOf(needle) >= 0 || term.replace(/ /g, '').indexOf(compact) >= 0; })) return;
            if (!matchesFilter(feature, filters)) { outsideCount++; return; }
            var bronId = (p.bron || {}).ancientId || p.id || 'bron onbekend';
            var detail = [TYPEN[p.type] || p.type || 'Plaats', p.moderneNaam, 'Bron ' + bronId].filter(Boolean).join(' · ');
            var exact = terms.some(function (term) { return term === needle || term.replace(/ /g, '') === compact; });
            var begintMet = terms.some(function (term) { return term.indexOf(needle) === 0; });
            matches.push({ feature: feature, label: p.naam || p.moderneNaam || p.id, detail: detail, rank: naam === needle ? 0 : exact ? 1 : naam.indexOf(needle) === 0 ? 2 : begintMet ? 3 : 4 });
        });
        matches.sort(function (a, b) { return a.rank - b.rank || compareFeatures(a.feature, b.feature, filters); });
        var total = matches.length;
        var limit = options && Number.isFinite(options.limit) ? Math.max(1, options.limit) : 8;
        return { matches: matches.slice(0, limit).map(function (match) { return { feature: match.feature, label: match.label, detail: match.detail }; }), outsideCount: outsideCount, total: total };
    }

    return { normalize: normalize, matchingRefs: matchingRefs, matchesFilter: matchesFilter, importance: importance, scale: scale, presentation: presentation, compareFeatures: compareFeatures, search: search };
}));
