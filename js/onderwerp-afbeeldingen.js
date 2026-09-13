/* Illustraties voor de onderwerpkaarten en detailweergave. */
var OnderwerpAfbeeldingen = (function () {
    'use strict';
    var beschikbaar = new Set('schepping bekering gods-leiding geloof gebed zonde verbond karakter-jezus evangelisatie gebedshouding apostelen-vandaag tucht-gemeente jezus-is-god misbruik-verkrachting-en-incest rijkdom-armoede jahweh-schepping huwelijk lhbtq liefde-algemeen liefde-man-vrouw waarheid-en-levensgevaar valse-profetie kinderoffers waarzeggerij werk-en-vlijt engelen volk-ammon volk-edom volk-midian volk-moab reuzen ziekte-van-jahweh opvoeding-kinderen bouwen vloek-op-voorwerpen jezus-in-het-ot huisinwijding zegeningen vervloekingen beloften bijbelse-feesten afgoden almacht-van-god zaaien-en-oogsten vruchtbaarheid-en-onvruchtbaarheid dubbelhartigheid wijn doop-door-onderdompeling vakmanschap straf-in-dit-leven verloren-bijbelse-bronnen boze-geesten demonen-en-duivelen vader-spreekt zoon-spreekt geest-spreekt'.split(' '));
    function pad(id) {
        return beschikbaar.has(id) ? 'images/wiki/onderwerpen/' + (id === 'wijn' ? 'wijn-v2' : id) + '.webp' : null;
    }
    return {
        pad: pad,
        html: function (id) {
            var src = pad(id);
            return src ? '<img class="ond-card-beeld" src="' + src + '" alt="" loading="lazy" width="640" height="640" style="display:block;width:100%;height:auto;border-radius:9px;margin-bottom:14px">' : '';
        },
        detail: function (beeld, id, naam) {
            var src = pad(id);
            beeld.hidden = !src;
            beeld.alt = naam || '';
            if (src) beeld.src = src;
            else beeld.removeAttribute('src');
        }
    };
}());
