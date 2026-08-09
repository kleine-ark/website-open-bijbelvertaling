/* ============================================================================
 * OSV Citaat-bibliotheek  (embed.js)
 * Embed citaten uit de Open Vertaling op deze én op andere websites.
 *
 * ÉÉN BRON: de tekst wordt live van openvertaling.nl geladen — er wordt geen
 * kopie gemaakt. Wijzigt de OSV, dan wijzigt het citaat overal mee. De bron
 * verwijst altijd terug naar openvertaling.nl.
 *
 * Gebruik (HTML, auto):
 *   <script src="https://openvertaling.nl/embed.js" defer></script>
 *   <span data-osv="johannes 3:16"></span>
 *   <div  data-osv="psalmen 23:1-4" data-osv-godsnaam="klassiek" data-osv-numbers="true"></div>
 *
 * Opties (als data-osv-… attributen of in OSV.cite(ref, opts)):
 *   numbers   true|false   versnummers tonen          (standaard true)
 *   citaat    true|false   citaatopmaak (rood=God enz.)(standaard true)
 *   link      true|false   bronverwijzing tonen        (standaard true)
 *   godsnaam  ov|klassiek|jehovah|jhwh                 (standaard ov = JAHWEH)
 *
 * Via JavaScript:
 *   OSV.cite('johannes 3:16', {numbers:false}).then(r => el.innerHTML = r.html);
 * ========================================================================== */
(function (global) {
  'use strict';

  var SITE = 'https://openvertaling.nl';
  var script = document.currentScript;

  function inferBase() {
    if (script && script.dataset && script.dataset.base) return script.dataset.base.replace(/\/$/, '');
    if (global.OSV_BASE) return String(global.OSV_BASE).replace(/\/$/, '');
    try {
      var h = location.hostname;
      if (h === 'openvertaling.nl' || h.endsWith('.openvertaling.nl') ||
          h === 'localhost' || h === '127.0.0.1') return '';
    } catch (e) {}
    return SITE; // extern: laad van productie
  }
  var BASE = inferBase();

  var chapterCache = {};
  var booksPromise = null;

  function loadBooks() {
    if (!booksPromise) {
      booksPromise = fetch(BASE + '/data/books.json')
        .then(function (r) { return r.json(); })
        .then(function (d) {
          var m = {};
          (d.books || []).forEach(function (b) { m[b.id] = b; });
          return m;
        })
        .catch(function () { return {}; });
    }
    return booksPromise;
  }

  function loadChapter(book, ch) {
    var key = book + '/' + ch;
    if (!chapterCache[key]) {
      chapterCache[key] = fetch(BASE + '/data/' + book + '/' + ch + '.json')
        .then(function (r) { if (!r.ok) throw new Error('niet gevonden'); return r.json(); });
    }
    return chapterCache[key];
  }

  function parseRef(ref) {
    var m = String(ref || '').trim().match(/^(\S+)\s+(\d+):(\d+)(?:\s*-\s*(\d+))?$/);
    if (!m) return null;
    return { book: m[1].toLowerCase(), chapter: +m[2], from: +m[3], to: +(m[4] || m[3]) };
  }

  /* Godsnaam-transform (zoals js/opties.js), alleen buiten HTML-tags */
  function replaceOutsideTags(html, pairs) {
    var re = /(<[^>]+>)|([^<]+)/g, out = '', m;
    while ((m = re.exec(html)) !== null) {
      if (m[1]) { out += m[1]; }
      else {
        var txt = m[2];
        for (var i = 0; i < pairs.length; i++) txt = txt.replace(pairs[i][0], pairs[i][1]);
        out += txt;
      }
    }
    return out;
  }
  function applyGodsnaam(html, mode) {
    if (mode === 'klassiek') {
      return replaceOutsideTags(html, [
        [/\bGod JAHWEH\b/g, 'de HEERE God'],
        [/\bJAHWEH van de legermachten\b/g, 'de HEERE der heirscharen'],
        [/\b(op|van|aan|voor|tot|door|in|met|bij|over|onder|naast|achter|jegens|uit|na|sinds) JAHWEH\b/gi, '$1 de HEERE'],
        [/\b([Oo]) JAHWEH\b/g, '$1 HEERE'],
        [/\bJAHWEH!/g, 'HEERE!'],
        [/(^|[.!?]\s+)JAHWEH\b/g, '$1De HEERE'],
        [/\bJAHWEH\b/g, 'de HEERE'],
        [/\bde de HEERE\b/g, 'de HEERE'],
        [/\bDe de HEERE\b/g, 'De HEERE'],
      ]);
    } else if (mode === 'jehovah') {
      return replaceOutsideTags(html, [[/\bGod JAHWEH\b/g, 'God Jehovah'], [/\bJAHWEH\b/g, 'Jehovah']]);
    } else if (mode === 'jhwh') {
      return replaceOutsideTags(html, [[/\bGod JAHWEH\b/g, 'God יהוה'], [/\bJAHWEH\b/g, 'יהוה']]);
    }
    return html;
  }

  function bool(v, def) {
    if (v === undefined || v === null || v === '') return def;
    if (typeof v === 'boolean') return v;
    return !/^(false|0|nee|no|uit)$/i.test(String(v));
  }

  /* Hoofd-API: levert {html, plain, ref, label, url} voor een referentie */
  function cite(ref, opts) {
    opts = opts || {};
    var globalOptions = typeof Opties !== 'undefined' && Opties.state;
    var numbersDefault = globalOptions ? globalOptions.versnummers !== 'uit' : true;
    var numbers = bool(opts.numbers, numbersDefault);
    var citaat = bool(opts.citaat, true);
    var showLink = bool(opts.link, true);
    var gods = opts.godsnaam || 'ov';

    var p = parseRef(ref);
    if (!p) return Promise.reject(new Error('Ongeldige referentie: ' + ref));

    var optionsReady = typeof Opties !== 'undefined' && Opties.ready
      ? Opties.ready : Promise.resolve();
    return Promise.all([loadChapter(p.book, p.chapter), loadBooks(), optionsReady]).then(function (res) {
      var data = res[0], books = res[1], book = books[p.book] || {};
      var name = book.nameDutch || p.book;
      var picked = (data.verses || []).filter(function (v) { return v.number >= p.from && v.number <= p.to; });
      if (!picked.length) throw new Error('Vers niet gevonden: ' + ref);

      var parts = picked.map(function (v) {
        var body = citaat ? (v.text2026_html || v.text2026 || '') : (v.text2026 || '');
        if (!citaat) body = escapeHtml(body);
        if (typeof Opties !== 'undefined' && Opties.transformOV && opts.godsnaam === undefined) {
          body = Opties.transformOV(body, book.testament);
          if (Opties.markeerGeo) body = Opties.markeerGeo(body, p.book, p.chapter, v.number);
          if (Opties.rekenMaten) body = Opties.rekenMaten(body, p.book, p.chapter, v.number);
          if (Opties.rekenTijden) body = Opties.rekenTijden(body, p.book, p.chapter, v.number, book.testament);
        } else {
          body = applyGodsnaam(body, gods);
        }
        var num = numbers ? '<sup class="osv-num">' + v.number + '</sup> ' : '';
        return '<span class="osv-vers">' + num + body + '</span>';
      });

      var label = name + ' ' + p.chapter + ':' + p.from + (p.to !== p.from ? '-' + p.to : '');
      var url = SITE + '/index.html#' + p.book + '/' + p.chapter;
      var linkHtml = showLink
        ? '<a class="osv-bron" href="' + url + '" target="_blank" rel="noopener">— ' + label +
          ' <span class="osv-merk">(Open Vertaling)</span></a>'
        : '';
      var html = '<span class="osv-tekst">' + parts.join(' ') + '</span>' + linkHtml;

      var plain = picked.map(function (v) {
        var t = v.text2026 || '';
        if (typeof Opties !== 'undefined' && Opties.transformOV && opts.godsnaam === undefined) {
          t = Opties.transformOV(t, book.testament);
          if (Opties.rekenMaten) t = Opties.rekenMaten(t, p.book, p.chapter, v.number);
          if (Opties.rekenTijden) t = Opties.rekenTijden(t, p.book, p.chapter, v.number, book.testament);
        } else {
          t = applyGodsnaam(t, gods);
        }
        return (numbers ? v.number + ' ' : '') + t;
      }).join(' ');

      return { html: html, plain: plain, ref: ref, label: label, url: url };
    });
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]; });
  }

  function renderEl(el) {
    if (el.getAttribute('data-osv-done') === '1') return;
    el.setAttribute('data-osv-done', '1');
    var ref = el.getAttribute('data-osv');
    var opts = {
      numbers: el.getAttribute('data-osv-numbers'),
      citaat: el.getAttribute('data-osv-citaat'),
      link: el.getAttribute('data-osv-link'),
      godsnaam: el.getAttribute('data-osv-godsnaam') || undefined
    };
    el.classList.add('osv-cite');
    el.innerHTML = '<span class="osv-laden">…</span>';
    cite(ref, opts).then(function (r) { el.innerHTML = r.html; })
      .catch(function (e) { el.innerHTML = '<span class="osv-fout">[' + (ref || '') + ' niet gevonden]</span>'; });
  }

  function renderAll(root) {
    (root || document).querySelectorAll('[data-osv]:not([data-osv-done="1"])').forEach(renderEl);
  }

  /* Scoped CSS injecteren (werkt ook op externe sites) */
  function injectCss() {
    if (document.getElementById('osv-embed-css')) return;
    var css =
      '.osv-cite{font-family:Georgia,"Times New Roman",serif;line-height:1.6;color:inherit;}' +
      '.osv-cite .osv-num{font-size:.7em;font-weight:700;color:#cba449;vertical-align:super;margin-right:1px;}' +
      '.osv-cite .osv-vers{}' +
      '.osv-cite .god-speaks{color:#c0392b;font-style:italic;}' +
      '.osv-cite .direct-speech{font-style:italic;}' +
      '.osv-cite .direct-speech::before{content:"\\00ab";}.osv-cite .direct-speech::after{content:"\\00bb";}' +
      '.osv-cite .devil-speaks{color:#b8860b;font-style:italic;}' +
      '.osv-cite .angel-speaks{color:#1d4ed8;font-style:italic;}' +
      '.osv-cite .note-marker,.osv-cite .strongs-inline{display:none;}' +
      '.osv-cite .osv-bron{display:block;margin-top:.4em;font-family:system-ui,sans-serif;font-size:.8em;color:#7a6a3a;text-decoration:none;}' +
      '.osv-cite .osv-bron:hover{text-decoration:underline;}' +
      '.osv-cite .osv-merk{opacity:.75;}' +
      '.osv-cite .osv-laden{opacity:.5;}' +
      '.osv-cite .osv-fout{color:#999;font-style:italic;font-size:.9em;}' +
      '@media (prefers-color-scheme:dark){.osv-cite .god-speaks{color:#ff7a6c;}.osv-cite .angel-speaks{color:#7ab0ff;}.osv-cite .osv-bron{color:#cba449;}}';
    var s = document.createElement('style');
    s.id = 'osv-embed-css';
    s.textContent = css;
    document.head.appendChild(s);
  }

  var OSV = {
    cite: cite,
    render: renderEl,
    renderAll: renderAll,
    base: BASE,
    site: SITE,
    _loadChapter: loadChapter
  };
  global.OSV = OSV;

  injectCss();
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { renderAll(); });
  } else {
    renderAll();
  }
})(typeof window !== 'undefined' ? window : this);
