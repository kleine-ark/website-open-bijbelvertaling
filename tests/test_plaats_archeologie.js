const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const target = path.join(__dirname, '..', 'js', 'plaats-archeologie.js');

function renderer() {
    assert.ok(fs.existsSync(target), 'De gedeelde archeologiesectie ontbreekt.');
    return require(target);
}
function dossier(changes = {}) {
    return {
        onderzoeksstatus: 'archeologische-bron', siteNaam: 'Tel Voorbeeld',
        samenvatting: 'Een onderzochte stad.', koppelingAanPlaats: 'De site wordt met deze stad verbonden.',
        perioden: ['Bronstijd'],
        bevindingen: [{ tekst: 'Een stadsmuur is opgegraven.', bronIds: ['rapport'] }],
        beperkingen: ['De vondst bewijst geen specifieke gebeurtenis.'],
        bronnen: [{ id: 'rapport', titel: 'Opgravingsrapport', url: 'https://example.org/rapport',
                    organisatie: 'Onderzoeksinstituut', jaar: 2022 }],
        gecontroleerdOp: '2026-09-13', humanReviewed: false, ...changes
    };
}
test('een ononderzocht dossier blijft zichtbaar zonder archeologie te verzinnen', () => {
    const html = renderer().render({onderzoeksstatus:'nog-te-onderzoeken'});
    assert.match(html, /Archeologie/);
    assert.match(html, /Nog te onderzoeken/);
    assert.doesNotMatch(html, /geen archeologie|geen vondsten|Opgravingsrapport/);
});
test('een bevinding verwijst naar de juiste klikbare bron', () => {
    const html = renderer().render(dossier());
    assert.match(html, /Een stadsmuur is opgegraven/);
    assert.match(html, /href="#archeologie-bron-1"/);
    assert.match(html, /id="archeologie-bron-1"/);
    assert.match(html, /href="https:\/\/example.org\/rapport"/);
    assert.match(html, /Onderzoeksinstituut/);
    assert.match(html, /2022/);
    assert.match(html, /De vondst bewijst geen specifieke gebeurtenis/);
});
test('identificatieonderzoek wordt niet als opgegraven Bijbelse plaats gepresenteerd', () => {
    const html = renderer().render(dossier({onderzoeksstatus:'alleen-identificatie'}));
    assert.match(html, /Plaatsidentificatie/);
    assert.match(html, /niet over een bewezen opgravingslocatie/);
});
test('een record zonder menselijke controle zegt dat expliciet', () => {
    assert.match(renderer().render(dossier()), /Menselijke revisie staat nog open/);
});
test('voortgang telt daadwerkelijke dossiers los van de totale inventaris', () => {
    const html = renderer().render(null, { totaal:1269, onderzocht:10, metArcheologischeBron:9 });
    assert.match(html, /10 van 1\.269/);
    assert.match(html, /9 met archeologische bronnen/);
    assert.doesNotMatch(html, /1\.269 onderzocht/);
});
test('broninhoud en links kunnen geen scripts injecteren', () => {
    const html = renderer().render(dossier({
        siteNaam:'<img src=x>', samenvatting:'<script>x</script>',
        bronnen:[{id:'rapport',titel:'<b>titel</b>',url:'javascript:alert(1)',organisatie:'Instelling'}]
    }));
    assert.doesNotMatch(html, /<img|<script|href="javascript:/);
    assert.match(html, /&lt;script&gt;/);
});
test('ontbrekende archeologiegegevens melden een laadfout zonder onderzoek te veinzen', () => {
    const html = renderer().render(null, null, {unavailable:true});
    assert.match(html, /tijdelijk niet worden geladen/);
    assert.doesNotMatch(html, /Nog te onderzoeken/);
});

async function openPage(archeologieFails = false) {
    const html = fs.readFileSync(path.join(__dirname, '..', 'plaats.html'), 'utf8');
    const script = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]).find(s=>s.includes('var inhoud ='));
    const inhoud = {innerHTML:'', querySelector(){return {after(){}};}};
    const archInhoud = {innerHTML:''};
    const feature = {
        geometry:{coordinates:[35,32]}, properties:{id:'geo-test', naam:'Testplaats', type:'stad',
        zekerheid:'zeker', refs:[{boek:'johannes',hoofdstuk:2,vers:1,href:'index.html#johannes/2/1'}], bron:{}}
    };
    const context = vm.createContext({
        URL, URLSearchParams, OVPlaatsArcheologie: renderer(),
        document:{getElementById(id){return id === 'plaats-archeologie' ? archInhoud : inhoud;}, createElement(){return {};}},
        window:{location:{search:'?plaats=geo-test'}},
        async fetch(url){
            if(url.includes('geografie-archeologie')){
                if(archeologieFails === 'pending') return new Promise(()=>{});
                if(archeologieFails === 'malformed') return {ok:true,async json(){return {dossiers:{'geo-test':dossier({bronnen:[null]})}};}};
                if(archeologieFails) throw new Error('offline');
                return {ok:true,async json(){return {dossiers:{'geo-test':dossier()},metadata:{totaal:1,onderzocht:1,metArcheologischeBron:1}};}};
            }
            return {ok:true,async json(){return url.endsWith('.geojson')?{features:[feature]}:{books:[]};}};
        },
        Verification:{async loadJSON(url){return (await context.fetch(url)).json();}, mount(){}}
    });
    vm.runInContext(script, context);
    await new Promise(setImmediate);
    return archInhoud.innerHTML ? inhoud.innerHTML.replace(/(<div id="plaats-archeologie">)[\s\S]*?<\/div>/, '$1' + archInhoud.innerHTML + '</div>') : inhoud.innerHTML;
}
test('de echte plaatspagina laadt het dossier op canoniek ID naast alle verslinks', async () => {
    const html = await openPage();
    assert.match(html, /Een onderzochte stad/);
    assert.match(html, /href="index.html#johannes\/2\/1"/);
    assert.match(html, /Brongegevens/);
});
test('een archeologiefout laat de plaats en Bijbelverwijzingen bruikbaar', async () => {
    const html = await openPage(true);
    assert.match(html, /Testplaats/);
    assert.match(html, /href="index.html#johannes\/2\/1"/);
    assert.match(html, /tijdelijk niet worden geladen/);
});

test('een hangend optioneel verzoek houdt de basispagina niet tegen', async () => {
    const html = await openPage('pending');
    assert.match(html, /Testplaats/);
    assert.match(html, /href="index.html#johannes\/2\/1"/);
    assert.match(html, /Archeologiegegevens laden/);
});

test('een ongeldig archeologiedossier wist de basispagina niet', async () => {
    const html = await openPage('malformed');
    assert.match(html, /Testplaats/);
    assert.match(html, /href="index.html#johannes\/2\/1"/);
    assert.match(html, /tijdelijk niet worden geladen/);
});
