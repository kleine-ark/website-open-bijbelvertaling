(function () {
    function esc(s) { return (s == null ? '' : String(s)).replace(/[&<>"]/g, function (c) { return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]; }); }
    function q(name) { var m = location.search.match(new RegExp('[?&]' + name + '=([^&]+)')); return m ? decodeURIComponent(m[1]) : null; }

    // Taal van de grondtekst per boek (voor de getranscribeerde tekst).
    var _HEB = {genesis:1,exodus:1,leviticus:1,numeri:1,deuteronomium:1,jozua:1,richteren:1,ruth:1,'1samuel':1,'2samuel':1,'1koningen':1,'2koningen':1,'1kronieken':1,'2kronieken':1,ezra:1,nehemia:1,esther:1,job:1,psalmen:1,spreuken:1,prediker:1,hooglied:1,jesaja:1,jeremia:1,klaagliederen:1,ezechiel:1,daniel:1,hosea:1,joel:1,amos:1,obadja:1,jona:1,micha:1,nahum:1,habakuk:1,zefanja:1,haggai:1,zacharia:1,maleachi:1};
    var _GEZ = {henoch:1,jubileeen:1,'4baruch':1,'1meqabyan':1,'2meqabyan':1,'3meqabyan':1};
    var _AUTEUR = {"genesis": "Mozes (traditioneel)", "exodus": "Mozes (traditioneel)", "leviticus": "Mozes (traditioneel)", "numeri": "Mozes (traditioneel)", "deuteronomium": "Mozes (traditioneel)", "jozua": "Anoniem (deuteronomistische geschiedschrijving)", "richteren": "Anoniem (deuteronomistische geschiedschrijving)", "ruth": "Anoniem (deuteronomistische geschiedschrijving)", "1samuel": "Anoniem (deuteronomistische geschiedschrijving)", "2samuel": "Anoniem (deuteronomistische geschiedschrijving)", "1koningen": "Anoniem (deuteronomistische geschiedschrijving)", "2koningen": "Anoniem (deuteronomistische geschiedschrijving)", "1kronieken": "De Kroniekschrijver", "2kronieken": "De Kroniekschrijver", "ezra": "De Kroniekschrijver", "nehemia": "De Kroniekschrijver", "esther": "Anoniem", "job": "Anoniem", "psalmen": "David en andere psalmisten", "spreuken": "Salomo (traditioneel)", "hooglied": "Salomo (traditioneel)", "prediker": "Salomo — 'de Prediker' (traditioneel)", "klaagliederen": "Jeremia (traditioneel)", "jesaja": "De profeet Jesaja", "jeremia": "De profeet Jeremia", "ezechiel": "De profeet Ezechiël", "daniel": "De profeet Daniël", "hosea": "De profeet Hosea", "joel": "De profeet Joël", "amos": "De profeet Amos", "obadja": "De profeet Obadja", "jona": "De profeet Jona", "micha": "De profeet Micha", "nahum": "De profeet Nahum", "habakuk": "De profeet Habakuk", "zefanja": "De profeet Zefanja", "haggai": "De profeet Haggaï", "zacharia": "De profeet Zacharia", "maleachi": "De profeet Maleachi", "mattheus": "De apostel Mattheüs (traditioneel)", "markus": "Johannes Markus (traditioneel)", "lukas": "Lukas", "handelingen": "Lukas", "johannes": "De apostel Johannes (traditioneel)", "romeinen": "De apostel Paulus", "1korinthiers": "De apostel Paulus", "2korinthiers": "De apostel Paulus", "galaten": "De apostel Paulus", "efeziers": "De apostel Paulus", "filippenzen": "De apostel Paulus", "kolossenzen": "De apostel Paulus", "1tessalonicensen": "De apostel Paulus", "2tessalonicensen": "De apostel Paulus", "1timotheus": "De apostel Paulus", "2timotheus": "De apostel Paulus", "titus": "De apostel Paulus", "filemon": "De apostel Paulus", "hebreeen": "Anoniem", "jakobus": "Jakobus", "1petrus": "De apostel Petrus (traditioneel)", "2petrus": "De apostel Petrus (traditioneel)", "1johannes": "De apostel Johannes (traditioneel)", "2johannes": "De apostel Johannes (traditioneel)", "3johannes": "De apostel Johannes (traditioneel)", "judas": "Judas", "openbaring": "De apostel Johannes (traditioneel)", "3ezra": "Anoniem / traditioneel toegeschreven", "4ezra": "Anoniem / traditioneel toegeschreven", "tobit": "Anoniem / traditioneel toegeschreven", "judith": "Anoniem / traditioneel toegeschreven", "boekderwijsheid": "Anoniem / traditioneel toegeschreven", "jezussirach": "Anoniem / traditioneel toegeschreven", "baruch": "Anoniem / traditioneel toegeschreven", "estherapocrief": "Anoniem / traditioneel toegeschreven", "gebedvanazaria": "Anoniem / traditioneel toegeschreven", "gezangindevuuroven": "Anoniem / traditioneel toegeschreven", "susanna": "Anoniem / traditioneel toegeschreven", "belenddedraak": "Anoniem / traditioneel toegeschreven", "gebedvanmanasse": "Anoniem / traditioneel toegeschreven", "1makkabeeen": "Anoniem / traditioneel toegeschreven", "2makkabeeen": "Anoniem / traditioneel toegeschreven", "3makkabeeen": "Anoniem / traditioneel toegeschreven", "henoch": "Toegeschreven aan Henoch (pseudepigraaf)", "jubileeen": "Anoniem (2e eeuw v.Chr.)", "4baruch": "Anoniem", "1meqabyan": "Anoniem (Ethiopische traditie)", "2meqabyan": "Anoniem (Ethiopische traditie)", "3meqabyan": "Anoniem (Ethiopische traditie)"};

    function jaarLabel(y){ return y<0 ? Math.abs(y)+' v.Chr.' : y+' n.Chr.'; }
    function renderVerseWitnesses(boekId){
        var el=document.getElementById('verse-witnesses'); if(!el) return;
        fetch('data/verse-witnesses.json').then(function(r){return r.json();}).then(function(vw){
            var e=(vw.boeken||{})[boekId]; if(!e||!e.origineel){el.style.display='none';return;}
            var h='<p style="font-size:13px;color:var(--teal);">Voor elk vers: het oudste handschrift in de oorspronkelijke taal, en het oudste \u00fcberhaupt (inclusief de Griekse Septuaginta).</p>';
            h+='<div class="vw-default"><div><span class="vw-lbl">Origineel (Hebreeuws/Grieks)</span><br><strong>'+esc(e.origineel.naam)+'</strong> \u2014 '+esc(jaarLabel(e.origineel.jaar))+'</div>';
            if(e.alle && (e.alle.ms!==e.origineel.ms)) h+='<div><span class="vw-lbl">Oudste \u00fcberhaupt</span><br><strong>'+esc(e.alle.naam)+'</strong> \u2014 '+esc(jaarLabel(e.alle.jaar))+'</div>';
            h+='</div>';
            h+='<p class="vw-note">Dit geldt voor (vrijwel) alle verzen van dit boek. De volledige codices dekken het hele boek; waar een ouder fragment bewaard is, staat dat hieronder.</p>';
            var exk=Object.keys(e.uitzonderingen||{});
            if(exk.length){
                var grp={};
                exk.forEach(function(k){var o=e.uitzonderingen[k].origineel||e.uitzonderingen[k].alle;if(!o)return;if(!grp[o.ms])grp[o.ms]={naam:o.naam,jaar:o.jaar,verzen:[]};grp[o.ms].verzen.push(k);});
                var ids=Object.keys(grp).sort(function(a,b){return grp[a].jaar-grp[b].jaar;});
                h+='<h3 class="vw-h3">Ouder bewaard \u2014 specifieke verzen</h3><ul class="vw-list">';
                ids.forEach(function(m){var g=grp[m];h+='<li><strong>'+esc(g.naam)+'</strong> ('+esc(jaarLabel(g.jaar))+'): '+g.verzen.map(esc).join(', ')+'</li>';});
                h+='</ul>';
            }
            el.innerHTML=h;
        }).catch(function(){el.style.display='none';});
    }
    function grondtaal(bid){ if(_HEB[bid])return 'he'; if(_GEZ[bid])return 'gez'; if(bid==='4ezra')return 'la'; return 'grc'; }
    // Toon hoofdstuk 1 (eerste verzen) in de grondtekst + vertaling, als geen fragment dat al doet.
    function renderDefaultGrondtekst(boekId, lang, containerId){
        var container=document.getElementById(containerId); if(!container) return;
        var isHeb=lang==='he';
        var taalNaam=isHeb?'Hebreeuwse':lang==='grc'?'Griekse':lang==='gez'?'Ge\u2019ez-':lang==='la'?'Latijnse':'';
        fetch('data/'+boekId+'/1.json').then(function(r){return r.json();}).then(function(d){
            var verses=(d.verses||[]).filter(function(v){return v.number<=6;});
            if(!verses.length){container.style.display='none';return;}
            var h='<p style="font-size:13px;color:var(--teal);">De '+taalNaam+' grondtekst en de Nederlandse vertaling van de eerste verzen.</p>';
            var any=false;
            verses.forEach(function(v){
                var src=(v.grondtekst||[]).map(function(w){return w.woord;}).join(' ');
                if(src)any=true;
                h+='<div class="frag-verse"><span class="frag-num">vers '+v.number+'</span>'+
                   (src?'<div class="frag-src" lang="'+lang+'"'+(isHeb?' dir="rtl"':'')+'>'+esc(src)+'</div>':'')+
                   '<div class="frag-nl">'+esc(v.text2026||'')+'</div></div>';
            });
            if(!any){container.style.display='none';return;}
            container.innerHTML=h;
        }).catch(function(){container.style.display='none';});
    }


    var PERSONEN = {};
    var MANS = {}, BOEKEN = {}, BOOKS = [], DATING = {};
    function bkName(id) { var b = BOOKS.find(function (x) { return x.id === id; }); return b ? b.nameDutch : id; }

    // Ontdekker als interne link (opent een beknopte bio-popup) i.p.v. een externe link.
    function personLink(ms) {
        var g = ms.gevonden || {};
        if (!g.wie) return null;
        if (ms.persoon && PERSONEN[ms.persoon]) {
            return '<a class="persoon-link" data-persoon="' + esc(ms.persoon) + '" role="button" tabindex="0">' + esc(g.wie) + '</a>';
        }
        return esc(g.wie);
    }

    function card(ms, isOudste, withLink) {
        var g = ms.gevonden || {};
        var wie = personLink(ms);
        var vind = wie ? ('door ' + wie + (g.jaar ? ' (' + esc(g.jaar) + ')' : '') + (g.plaats ? ', ' + esc(g.plaats) : ''))
                       : (g.hoe ? '' : (g.jaar ? esc(g.jaar) : '—'));
        var facts = '<ul class="ms-facts">';
        facts += '<li><strong>Bevindt zich:</strong> ' + esc(ms.bewaarplaats || '—') + '</li>';
        if (ms.bevat) facts += '<li><strong>Bevat:</strong> ' + esc(ms.bevat) + '</li>';
        facts += '<li><strong>Gevonden/verworven:</strong> ' + (vind ? vind + '. ' : '') + esc(g.hoe || '') + '</li>';
        if (ms.bewijs && ms.bewijs.url) facts += '<li class="ms-bewijs"><strong>Bewijs:</strong> <a href="' + esc(ms.bewijs.url) + '" target="_blank" rel="noopener">' + esc(ms.bewijs.tekst) + '</a></li>';
        if (ms.digitaal && ms.digitaal.length) {
            facts += '<li class="ms-digitaal"><strong>Online te bekijken:</strong> ' +
                ms.digitaal.map(function (dgl) { return '<a href="' + esc(dgl.url) + '" target="_blank" rel="noopener">' + esc(dgl.label) + '</a>'; }).join(' &nbsp;·&nbsp; ') + '</li>';
        }
        facts += '</ul>';
        var fig = ms.afbeelding ? ('<figure class="codex-photo">' +
            '<img class="codex-scan" src="' + esc(ms.afbeelding) + '" alt="' + esc(ms.bijschrift || ms.naam) + '" title="Klik om de scan te vergroten" loading="lazy">' +
            '<figcaption>' + esc(ms.bijschrift || '') + '<br><span class="scan-hint">🔍 klik om te vergroten</span> · <a href="' + esc(ms.commons) + '" target="_blank" rel="noopener">Wikimedia</a> (' + esc(ms.licentie || 'bron') + ')</figcaption></figure>') : '';
        // Handschrift-naam is altijd een link naar de eigen detailpagina.
        var naamHtml = ms.id
            ? '<a href="handschriften.html?ms=' + encodeURIComponent(ms.id) + '">' + esc(ms.naam) + '</a>'
            : esc(ms.naam);
        return '<div class="codex-card' + (isOudste ? ' oudste' : '') + '">' + fig +
            (isOudste ? '<span class="codex-badge">Oudste bewaarde tekst</span><br>' : '') +
            '<h4>' + naamHtml + (ms.bijnaam ? ' <span class="bijnaam">' + esc(ms.bijnaam) + '</span>' : '') + '</h4>' +
            '<div class="meta">' + esc(ms.datering || '') + (ms.bewaarplaats ? ' · ' + esc(ms.bewaarplaats) : '') + '</div>' +
            '<p>' + esc(ms.beschrijving || '') + '</p>' + facts +
            (withLink && ms.id ? '<p class="ms-detail-link"><a href="handschriften.html?ms=' + encodeURIComponent(ms.id) + '">Volledige gegevens, tekst &amp; tekstvarianten ›</a></p>' : '') +
            '</div>';
    }

    function sumCard(label, ms, cls) {
        var naamHtml = ms.id ? '<a href="handschriften.html?ms=' + encodeURIComponent(ms.id) + '">' + esc(ms.naam) + '</a>' : esc(ms.naam);
        return '<div class="sum-card ' + cls + '"><div class="sum-label">' + esc(label) + '</div>' +
            '<div class="sum-name">' + naamHtml + (ms.bijnaam ? ' <span style="font-weight:400;color:var(--teal);font-size:12px;">' + esc(ms.bijnaam) + '</span>' : '') + '</div>' +
            '<div class="sum-meta">' + esc(ms.datering || '') + (ms.bevat ? ' · ' + esc(ms.bevat) : '') + '</div></div>';
    }

    // Beknopte bio-popup (intern) met één externe link.
    function closePopup() { var p = document.getElementById('persoon-popup'); if (p) p.remove(); document.removeEventListener('click', outside, true); }
    function outside(e) { var p = document.getElementById('persoon-popup'); if (p && !p.contains(e.target) && !(e.target.classList && e.target.classList.contains('persoon-link'))) closePopup(); }
    function showPopup(link) {
        closePopup();
        var pid = link.getAttribute('data-persoon'); var per = PERSONEN[pid]; if (!per) return;
        var pop = document.createElement('div');
        pop.id = 'persoon-popup'; pop.className = 'persoon-popup';
        pop.innerHTML = '<h5>' + esc(per.naam) + '</h5>' + (per.jaren ? '<div class="pp-jaren">' + esc(per.jaren) + '</div>' : '') +
            '<div>' + esc(per.bio) + '</div>' +
            (per.wikipedia ? '<div class="pp-more">Meer: <a href="' + esc(per.wikipedia) + '" target="_blank" rel="noopener">Wikipedia →</a></div>' : '');
        document.body.appendChild(pop);
        var r = link.getBoundingClientRect();
        var top = r.bottom + 6, left = Math.min(r.left, window.innerWidth - pop.offsetWidth - 12);
        if (top + pop.offsetHeight > window.innerHeight - 8) top = Math.max(8, r.top - pop.offsetHeight - 6);
        pop.style.top = top + 'px'; pop.style.left = Math.max(8, left) + 'px';
        setTimeout(function () { document.addEventListener('click', outside, true); }, 0);
    }
    document.addEventListener('click', function (e) {
        var l = e.target.closest ? e.target.closest('.persoon-link') : null;
        if (l) { e.preventDefault(); e.stopPropagation(); showPopup(l); }
    });

    // Scan-lightbox: klik op een handschrift-scan om 'm groot te bekijken.
    var lb = document.createElement('div');
    lb.id = 'scan-lightbox';
    lb.innerHTML = '<button class="sl-close" aria-label="Sluiten">×</button><img alt=""><div class="sl-cap"></div>';
    document.body.appendChild(lb);
    function closeLb() { lb.classList.remove('open'); }
    lb.addEventListener('click', closeLb);
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeLb(); });
    document.addEventListener('click', function (e) {
        var img = e.target.closest ? e.target.closest('.codex-scan') : null;
        if (!img) return;
        lb.querySelector('img').src = img.getAttribute('src');
        lb.querySelector('.sl-cap').textContent = img.getAttribute('alt') || '';
        lb.classList.add('open');
    });

    // Render de grondtekst (Hebreeuws/Grieks) + Nederlandse vertaling van een fragment.
    function renderFragmentText(ms, containerId) {
        var tf = ms.tekstfragment; if (!tf) return;
        var container = document.getElementById(containerId || 'fragment-tekst'); if (!container) return;
        var lang = tf.lang || 'grc';
        var isHeb = lang === 'he';
        var taalNaam = isHeb ? 'Hebreeuwse' : lang === 'grc' ? 'Griekse' : lang === 'la' ? 'Latijnse' : '';
        var chs = {}; (tf.blokken || []).forEach(function (b) { chs[b.hoofdstuk] = true; });
        var jobs = Object.keys(chs).map(function (ch) {
            return fetch('data/' + tf.boek + '/' + ch + '.json').then(function (r) { return r.json(); }).then(function (d) { return { ch: ch, d: d }; });
        });
        Promise.all(jobs).then(function (loaded) {
            var byCh = {}; loaded.forEach(function (x) { byCh[x.ch] = x.d; });
            var h = '<h3 class="frag-kop">📜 Lees de tekst van dit handschrift — ' + esc(tf.verwijzing) + '</h3>' +
                '<p style="font-size:13px;color:var(--teal);">De ' + taalNaam + ' grondtekst en de Nederlandse vertaling, vers voor vers.</p>';
            (tf.blokken || []).forEach(function (b) {
                var d = byCh[b.hoofdstuk]; if (!d) return;
                b.nummers.forEach(function (n) {
                    var v = (d.verses || []).find(function (x) { return x.number === n; }); if (!v) return;
                    var src = (v.grondtekst || []).map(function (w) { return w.woord; }).join(' ');
                    h += '<div class="frag-verse"><span class="frag-num">' + esc(b.label) + ' : ' + n + '</span>' +
                        (src ? '<div class="frag-src" lang="' + lang + '"' + (isHeb ? ' dir="rtl"' : '') + '>' + esc(src) + '</div>' : '') +
                        '<div class="frag-nl">' + esc(v.text2026 || '') + '</div></div>';
                });
            });
            if (tf.verschillen) h += '<div class="principle-box" style="background:rgba(203,164,73,0.08);margin-top:12px;"><strong>Over dit handschrift:</strong> ' + esc(tf.verschillen) + '</div>';
            container.innerHTML = h;
        }).catch(function (e) { console.error(e); });
    }

    // === Detailpagina van één handschrift (?ms=<id>) ===
    function renderMsDetail(id) {
        var el = document.getElementById('ms-page');
        var ms = MANS[id];
        if (!ms) { el.innerHTML = '<h1>Onbekend handschrift</h1><p><a href="handschriften.html">← Alle handschriften</a></p>'; return; }
        var getuigeVoor = [];
        Object.keys(BOEKEN).forEach(function (bid) {
            var bk = BOEKEN[bid];
            var volFirst = bk.oudsteVolledig || (bk.volledig && bk.volledig[0]);
            if (bk.oudsteFragment === id) getuigeVoor.push({ bid: bid, rol: 'oudste bewaarde tekst' });
            else if (volFirst === id) getuigeVoor.push({ bid: bid, rol: 'oudste volledige versie' });
            else if ((bk.fragmenten || []).indexOf(id) >= 0 || (bk.volledig || []).indexOf(id) >= 0) getuigeVoor.push({ bid: bid, rol: 'tekstgetuige' });
        });
        var h = '<p style="font-size:13px;"><a href="handschriften.html">← Alle handschriften</a></p>';
        h += '<h1>' + esc(ms.naam) + '</h1>';
        h += '<p class="subtitle">' + esc(ms.bijnaam || '') + (ms.siglum ? ' · ' + esc(ms.siglum) : '') + '</p>';
        h += card(ms, false);
        if (getuigeVoor.length) {
            h += '<h2>Voor welke boeken</h2><ul>';
            getuigeVoor.forEach(function (g) { h += '<li><a href="handschriften/' + encodeURIComponent(g.bid) + '.html' + '">' + esc(bkName(g.bid)) + '</a> — ' + esc(g.rol) + '</li>'; });
            h += '</ul>';
        }
        // Betrokken personen (klikbaar naar korte biografie-popup)
        var betrok = (ms.betrokkenen || []).filter(function (pid) { return PERSONEN[pid]; });
        if (betrok.length) {
            h += '<h2>Betrokken personen</h2><ul class="ms-personen">';
            betrok.forEach(function (pid) {
                var per = PERSONEN[pid];
                h += '<li><a class="persoon-link" data-persoon="' + esc(pid) + '" role="button" tabindex="0">' + esc(per.naam) + '</a>' +
                    (per.jaren ? ' <span class="mini-meta">(' + esc(per.jaren) + ')</span>' : '') +
                    (per.bio ? ' — ' + esc(per.bio.split('. ')[0]) + '.' : '') + '</li>';
            });
            h += '</ul>';
        }
        if (ms.tekstfragment) h += '<div id="fragment-tekst"></div>';
        if (ms.varianten && ms.varianten.length) {
            h += '<h2>Tekstvarianten</h2><div class="ms-table-wrap"><table class="ms-table"><thead><tr><th>Plaats</th><th>Lezing van dit handschrift</th><th>Gangbare tekst</th><th>Toelichting</th></tr></thead><tbody>';
            ms.varianten.forEach(function (v) {
                h += '<tr><td>' + esc(v.verwijzing || '') + '</td><td lang="grc">' + esc(v.lezing || '') + '</td><td lang="grc">' + esc(v.standaard || '') + '</td><td>' + esc(v.toelichting || '') + '</td></tr>';
            });
            h += '</tbody></table></div>';
        }
        h += '<h2>Bronvermelding</h2><p style="font-size:12.5px;color:var(--teal);">Foto van <a href="' + esc(ms.commons || 'https://commons.wikimedia.org/') + '" target="_blank" rel="noopener">Wikimedia Commons</a> (' + esc(ms.licentie || 'bron') + '). Datering en toeschrijving volgen de gangbare tekstkritische literatuur.</p>';
        el.innerHTML = h;
        document.title = ms.naam + ' — Handschriften — Open Vertaling';
        if (ms.tekstfragment) renderFragmentText(ms);
    }

    // === Index van alle handschriften ===
    function renderIndex() {
        var el = document.getElementById('ms-page');
        var ids = Object.keys(MANS);
        function mini(list) {
            return '<ul class="ms-index">' + list.map(function (id) {
                var m = MANS[id];
                return '<li><a href="handschriften.html?ms=' + encodeURIComponent(id) + '">' + esc(m.naam) + '</a>' +
                    (m.bijnaam ? ' <span class="mini-bij">' + esc(m.bijnaam) + '</span>' : '') +
                    '<span class="mini-meta">' + esc(m.datering || '') + (m.bevat ? ' · ' + esc(m.bevat) : (m.bewaarplaats ? ' · ' + esc(m.bewaarplaats) : '')) + '</span></li>';
            }).join('') + '</ul>';
        }
        var frags = ids.filter(function (id) { return MANS[id].type === 'fragment'; });
        var vols = ids.filter(function (id) { return MANS[id].type === 'volledig'; });
        var rest = ids.filter(function (id) { return frags.indexOf(id) < 0 && vols.indexOf(id) < 0; });
        var h = '<h1>Handschriften</h1><p class="subtitle">de centrale opslag van handschriften van Gods Woord — tekst, vindgeschiedenis, citaties en varianten</p>';
        h += '<div class="principle-box">Elk handschrift heeft een eigen pagina met foto/scan, datering, vindgeschiedenis, dekking en (waar bekend) de tekst met tekstvarianten. Deze gegevens staan los van de leesweergave. Per boek is er ook een <a href="handschriften.html?boek=johannes">boekpagina</a> en het <a href="grondteksten.html#codices">codex-overzicht</a>.</div>';
        if (frags.length) h += '<h2>Fragmenten &amp; papyri</h2>' + mini(frags);
        if (vols.length) h += '<h2>Volledige handschriften (codices)</h2>' + mini(vols);
        if (rest.length) h += '<h2>Overige</h2>' + mini(rest);
        var boeken = Object.keys(BOEKEN);
        if (boeken.length) h += '<h2>Per boek</h2><p>' + boeken.map(function (bid) { return '<a href="handschriften/' + encodeURIComponent(bid) + '.html' + '">' + esc(bkName(bid)) + '</a>'; }).join(' &nbsp;·&nbsp; ') + '</p>';
        el.innerHTML = h;
        document.title = 'Handschriften — Open Vertaling';
    }

    Promise.all([
        fetch('data/manuscripts.json').then(function (r) { return r.json(); }),
        fetch('data/books.json').then(function (r) { return r.json(); }).catch(function () { return { books: [] }; }),
        fetch('data/book-dating.json').then(function (r) { return r.json(); }).catch(function () { return {}; })
    ]).then(function (res) {
        var data = res[0], books = res[1], dating = res[2];
        PERSONEN = data.personen || {};
        MANS = data.manuscripten || {}; BOEKEN = data.boeken || {}; BOOKS = (books.books || []); DATING = dating || {};
        Object.keys(MANS).forEach(function (k) { if (MANS[k] && !MANS[k].id) MANS[k].id = k; });
        var el = document.getElementById('ms-page');

        // Detailpagina van één handschrift
        var msId = q('ms');
        if (msId) { renderMsDetail(msId); return; }

        var boekId = window.HS_BOOK || q('boek');
        // Geen boek gekozen → index van alle handschriften
        if (!boekId) { renderIndex(); return; }

        var M = MANS, B = BOEKEN;
        var bkLookup = function (id) { return BOOKS.find(function (b) { return b.id === id; }); };
        // Onbekend boek → index
        if (!bkLookup(boekId)) { renderIndex(); return; }

        // Boek bestaat maar heeft (nog) geen uitgebreide handschrift-data → minimale pagina
        if (!B[boekId]) {
            var bk0 = bkLookup(boekId), d0 = dating && dating[boekId];
            var h = '<h1>Handschriften van ' + esc(bk0.nameDutch) + '</h1>';
            if (d0) {
                var pp = [];
                if (d0.schrijftijdKort || d0.schrijftijd) pp.push('Schrijftijd: ' + esc(d0.schrijftijdKort || d0.schrijftijd));
                var oj0 = d0.oudsteDatum || d0.oudsteHandschrift;
                if (oj0) pp.push('Oudste handschrift: ' + esc(String(oj0).split(' (')[0]));
                if (pp.length) h += '<div class="dating-line">📜 ' + pp.join(' &nbsp;·&nbsp; ') + '</div>';
            }
            h += '<div class="principle-box">Voor dit boek is nog geen uitgebreide handschrift-pagina met foto’s gemaakt. ' +
                'De belangrijkste tekstgetuigen staan wel in de <a href="grondteksten.html?boek=' + encodeURIComponent(boekId) + '">grondtekst-tabel</a>, ' +
                'en de codices met foto’s in het <a href="grondteksten.html#codices">codex-overzicht</a>.</div>';
            h += '<p>→ Lees ' + esc(bk0.nameDutch) + ' in de tekst: <a href="index.html#' + encodeURIComponent(boekId) + '/1">' + esc(bk0.nameDutch) + ' 1</a></p>';
            el.innerHTML = h;
            document.title = 'Handschriften van ' + bk0.nameDutch + ' — Open Vertaling';
            return;
        }

        var boek = B[boekId];
        var bk = (books.books || []).find(function (b) { return b.id === boekId; });
        var naam = bk ? bk.nameDutch : boekId;
        var d = dating && dating[boekId];

        var html = '<h1>Handschriften van ' + esc(naam) + '</h1>';
        html += '<p class="subtitle">het oudste fragment, de vindgeschiedenis en de originele scans</p>';
        if (d) {
            var parts = [];
            if (d.schrijftijdKort || d.schrijftijd) parts.push('Schrijftijd: ' + esc(d.schrijftijdKort || d.schrijftijd));
            var oudsteJaar = d.oudsteDatum || d.oudsteHandschrift;
            if (oudsteJaar) parts.push('Oudste handschrift: ' + esc(String(oudsteJaar).split(' (')[0]));
            if (parts.length) html += '<div class="dating-line">📜 ' + parts.join(' &nbsp;·&nbsp; ') + '</div>';
        if (_AUTEUR[boekId]) html += '<p class="boek-auteur"><strong>Traditionele auteur:</strong> ' + esc(_AUTEUR[boekId]) + '</p>';
        }
        var oudste = boek.oudsteFragment;
        var oudsteVol = boek.oudsteVolledig || (boek.volledig && boek.volledig[0]);
        var sum = '';
        if (oudste && M[oudste]) sum += sumCard('Oudste fragment', M[oudste], 'frag');
        if (oudsteVol && M[oudsteVol]) sum += sumCard('Oudste volledige versie', M[oudsteVol], 'vol');
        if (sum) html += '<div class="ms-summary">' + sum + '</div>';

        if (boek.intro) html += '<div class="principle-box">' + esc(boek.intro) + '</div>';

        if (oudste && M[oudste]) {
            html += '<h2>Oudste bewaarde tekst</h2>' + card(M[oudste], true, true) + '<div class="frag-tekst" id="fragment-tekst-' + esc(oudste) + '"></div>';
        }
        var frags = (boek.fragmenten || []).filter(function (id) { return id !== oudste && M[id]; });
        if (frags.length) {
            html += '<h2>Andere vroege fragmenten</h2>';
            frags.forEach(function (id) { html += card(M[id], false, true) + '<div class="frag-tekst" id="fragment-tekst-' + esc(id) + '"></div>'; });
        }
        var vol = (boek.volledig || []).filter(function (id) { return M[id]; });
        if (vol.length) {
            html += '<h2>Volledige handschriften</h2>';
            vol.forEach(function (id) { html += card(M[id], false, true); });
        }
        if (boek.tekstgetuigen) html += '<p style="font-size:13px;color:var(--teal);"><strong>Tekstgetuigen totaal:</strong> ' + esc(boek.tekstgetuigen) + '</p>';

        // Optioneel: feitenoverzicht van specifieke hoofdstukken (bv. de Ismaël-hoofdstukken in Genesis)
        if (boek.ismaelHoofdstukken) {
            var ih = boek.ismaelHoofdstukken;
            html += '<h2>' + esc(ih.titel) + '</h2>';
            html += '<p style="font-size:13px;color:var(--teal);">' + esc(ih.intro) + '</p>';
            html += '<div class="ms-table-wrap"><table class="ms-table"><thead><tr><th>Hoofdstuk</th><th>Onderwerp</th><th>Oudste bewaarde handschrift</th></tr></thead><tbody>';
            (ih.rijen || []).forEach(function (r) {
                html += '<tr><td><strong>' + esc(r.h) + '</strong></td><td>' + esc(r.onderwerp) + '</td><td>' + esc(r.oudste) + '</td></tr>';
            });
            html += '</tbody></table></div>';
            if (ih.bron) html += '<p style="font-size:11.5px;color:#999;">' + esc(ih.bron) + '</p>';
        }

        // Getranscribeerde grondtekst (hoofdstuk 1) als geen handschrift al tekst toont
        var _anyFrag = (oudste && M[oudste] && M[oudste].tekstfragment) || frags.some(function(id){return M[id]&&M[id].tekstfragment;});
        if (!_anyFrag) {
            html += '<h2>Lees de grondtekst — ' + esc(naam) + ' 1</h2>';
            html += '<div class="frag-tekst" id="fragment-tekst-default"></div>';
        }
        html += '<h2>Oudste handschrift per vers</h2><div id="verse-witnesses"><p style="color:var(--teal);font-size:13px;">Laden\u2026</p></div>';
        html += '<h2>Bronvermelding</h2>' +
            '<p style="font-size:12.5px;color:var(--teal);">De foto’s van de handschriften komen van ' +
            '<a href="https://commons.wikimedia.org/" target="_blank" rel="noopener">Wikimedia Commons</a> en behoren tot het publieke domein; klik op een foto voor de bronpagina en de hoge-resolutie scan. ' +
            'Datering en toeschrijving volgen de gangbare tekstkritische literatuur (o.a. Aland, Metzger). ' +
            'Zie ook het <a href="grondteksten.html#codices">codex-overzicht</a> en de <a href="grondteksten.html?boek=' + encodeURIComponent(boekId) + '">grondtekst-tabel</a>.</p>';
        html += '<p style="margin-top:14px;">→ Lees ' + esc(naam) + ' in de tekst: <a href="index.html#' + encodeURIComponent(boek.leesInReader || boekId) + '/1">' + esc(naam) + ' 1</a></p>';

        el.innerHTML = html;
        document.title = 'Handschriften van ' + naam + ' — Open Vertaling';
        if (oudste && M[oudste]) renderFragmentText(M[oudste], 'fragment-tekst-' + oudste);
        frags.forEach(function (id) { if (M[id].tekstfragment) renderFragmentText(M[id], 'fragment-tekst-' + id); });
        if (!_anyFrag) renderDefaultGrondtekst(boekId, grondtaal(boekId), 'fragment-tekst-default');
        renderVerseWitnesses(boekId);
    }).catch(function (e) {
        document.getElementById('ms-page').innerHTML = '<p style="color:#c0392b">Kon de handschrift-gegevens niet laden.</p>';
        console.error(e);
    });
})();
