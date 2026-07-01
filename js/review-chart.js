/* review-chart.js — toont de nakijkvoortgang per week met de verwachte (geprojecteerde)
 * lijn en de verwachte einddatum. Leest data/review-history.json (datum → nagekeken
 * verzen) + data/stats.json (verses_total). Tekent een responsieve SVG.
 * Container: <div id="review-chart"></div>
 */
(function () {
    var NL_M = ['jan', 'feb', 'mrt', 'apr', 'mei', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'dec'];
    var NL_MV = ['januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli', 'augustus', 'september', 'oktober', 'november', 'december'];

    function init() {
        var el = document.getElementById('review-chart');
        if (!el) return;
        Promise.all([
            fetch('data/review-history.json', { cache: 'no-cache' }).then(function (r) { return r.json(); }),
            fetch('data/stats.json', { cache: 'no-cache' }).then(function (r) { return r.json(); })
        ]).then(function (res) { draw(el, res[0], res[1]); })
          .catch(function (e) { console.warn('[review-chart]', e); });
    }

    function draw(el, hist, stats) {
        var pts = Object.keys(hist).sort().map(function (d) {
            return { t: new Date(d + 'T00:00:00'), v: hist[d] };
        });
        if (pts.length < 2) return;
        var total = stats.verses_total || pts[pts.length - 1].v;

        // Lineaire trend (kleinste kwadraten) over de historie → verzen/dag
        var t0ord = pts[0].t.getTime() / 86400000;
        var xs = pts.map(function (p) { return p.t.getTime() / 86400000 - t0ord; });
        var ys = pts.map(function (p) { return p.v; });
        var n = xs.length, sx = 0, sy = 0, sxx = 0, sxy = 0;
        for (var i = 0; i < n; i++) { sx += xs[i]; sy += ys[i]; sxx += xs[i] * xs[i]; sxy += xs[i] * ys[i]; }
        var slope = (n * sxy - sx * sy) / (n * sxx - sx * sx); // verzen/dag
        var last = pts[pts.length - 1];
        var lastOrd = last.t.getTime() / 86400000;
        var etaOrd = slope > 0 ? lastOrd + (total - last.v) / slope : lastOrd;
        var etaDate = new Date(etaOrd * 86400000);

        // Domein
        var xMin = pts[0].t.getTime(), xMax = etaDate.getTime();
        if (xMax <= xMin) xMax = xMin + 86400000 * 30;
        var W = 720, H = 260, mL = 52, mR = 16, mT = 16, mB = 34;
        var px0 = mL, px1 = W - mR, py0 = mT, py1 = H - mB;
        function X(ms) { return px0 + (ms - xMin) / (xMax - xMin) * (px1 - px0); }
        function Y(v) { return py1 - (v / total) * (py1 - py0); }

        var s = [];
        s.push('<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Nakijkvoortgang per week met verwachte lijn">');

        // Y-gridlijnen + labels (0,25,50,75,100%)
        for (var q = 0; q <= 4; q++) {
            var vy = total * q / 4, yy = Y(vy);
            s.push('<line x1="' + px0 + '" y1="' + yy + '" x2="' + px1 + '" y2="' + yy + '" stroke="var(--border,#e5e1d8)" stroke-width="1"' + (q === 4 ? ' stroke-dasharray="4 3"' : '') + '/>');
            s.push('<text x="' + (px0 - 6) + '" y="' + (yy + 4) + '" text-anchor="end" font-size="11" fill="#888">' + (q * 25) + '%</text>');
        }
        // Doel-label (100% = verses_total)
        s.push('<text x="' + px1 + '" y="' + (Y(total) - 5) + '" text-anchor="end" font-size="11" fill="#5cb85c">100% · ' + total.toLocaleString('nl-NL') + ' verzen</text>');

        // X-as maand-ticks
        var d = new Date(xMin); d.setDate(1);
        while (d.getTime() <= xMax) {
            var xx = X(d.getTime());
            if (xx >= px0 - 1 && xx <= px1 + 1) {
                s.push('<line x1="' + xx + '" y1="' + py0 + '" x2="' + xx + '" y2="' + py1 + '" stroke="var(--border,#e5e1d8)" stroke-width="1" stroke-dasharray="2 4" opacity="0.6"/>');
                s.push('<text x="' + xx + '" y="' + (py1 + 16) + '" text-anchor="middle" font-size="10" fill="#888">' + NL_M[d.getMonth()] + '</text>');
            }
            d.setMonth(d.getMonth() + 1);
        }

        // Verwachte (geprojecteerde) lijn: van eerste punt langs trend tot ETA op 100%
        var trendY0 = Y(slope * (xMin / 86400000 - t0ord) + (sy / n - slope * (sx / n)));
        s.push('<line x1="' + X(xMin) + '" y1="' + trendY0 + '" x2="' + X(etaDate.getTime()) + '" y2="' + Y(total) + '" stroke="#cba449" stroke-width="2" stroke-dasharray="6 4" opacity="0.8"/>');

        // Werkelijke voortgang (cumulatief)
        var poly = pts.map(function (p) { return X(p.t.getTime()) + ',' + Y(p.v); }).join(' ');
        s.push('<polyline points="' + poly + '" fill="none" stroke="var(--text-primary,#142e42)" stroke-width="2.5"/>');
        pts.forEach(function (p) { s.push('<circle cx="' + X(p.t.getTime()) + '" cy="' + Y(p.v) + '" r="3" fill="var(--text-primary,#142e42)"/>'); });

        // ETA-marker
        var ex = X(etaDate.getTime()), ey = Y(total);
        s.push('<circle cx="' + ex + '" cy="' + ey + '" r="4.5" fill="#5cb85c"/>');
        var lbl = etaDate.getDate() + ' ' + NL_MV[etaDate.getMonth()] + ' ' + etaDate.getFullYear();
        s.push('<text x="' + (ex - 8) + '" y="' + (ey + 16) + '" text-anchor="end" font-size="11" font-weight="600" fill="#2e7d32">⚑ ' + lbl + '</text>');

        s.push('</svg>');

        // Legenda
        s.push('<div style="display:flex;gap:18px;flex-wrap:wrap;font-size:12px;color:#666;margin-top:6px;">' +
            '<span><span style="display:inline-block;width:14px;height:3px;background:#142e42;vertical-align:middle;"></span> werkelijke voortgang</span>' +
            '<span><span style="display:inline-block;width:14px;height:0;border-top:2px dashed #cba449;vertical-align:middle;"></span> verwachte lijn</span>' +
            '<span><span style="color:#5cb85c;">⚑</span> verwachte afronding</span>' +
            '</div>');

        el.innerHTML = s.join('');
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();
})();
