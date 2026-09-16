const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { startFixture } = require('./helpers/browser-fixture.cjs');
let fixture;
before(async () => { fixture = await startFixture(); });
after(async () => { await fixture.close(); });

async function changedPage(change, reader = 'index.html', user = null) {
    const chapter = JSON.parse(readFileSync('data/genesis/3.json'));
    change(chapter);
    const raw = fixture.publishChapter(3, chapter);
    const page = await fixture.pageAs(user);
    await page.route('**/data/genesis/3.json', route => route.fulfill({ body: raw, contentType: 'application/json' }));
    await page.goto(fixture.base + '/' + reader + '#genesis/3');
    await page.locator('#chapter-verification button').first().waitFor();
    return page;
}

async function visibleBanner(page) {
    return page.locator('#ai-concept-banner').evaluateAll(nodes =>
        nodes.filter(n => !n.hidden && getComputedStyle(n).display !== 'none').map(n => n.textContent).join(''));
}

async function options(page, notes, markers, citations = true) {
    await page.evaluate(({ notes, markers, citations }) => {
        document.getElementById('content').classList.toggle('hide-margin2026', !notes);
        document.body.classList.toggle('kt-popup-mode', markers);
        document.body.classList.toggle('citaten-uit', !citations);
    }, { notes, markers, citations });
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
}

test('hidden notes and markers do not warn or invalidate the text; visible warnings name both', async () => {
    const page = await changedPage(chapter => {
        const verse = chapter.verses[0];
        verse.marginNotes[0].text2026 += ' Aangepast.';
        verse.text2026_html = verse.text2026_html.replace('data-note="1">1', 'data-note="1">a');
    });
    await options(page, false, false);
    assert.equal(await visibleBanner(page), '');
    assert.equal(await page.locator('.chapter-concept-tag').count(), 0);
    assert.equal(await page.locator('.col-2026 .note-marker').first().isVisible(), false);
    await options(page, false, true);
    assert.equal(await page.locator('.col-2026 .note-marker').first().isVisible(), true);
    assert.match(await visibleBanner(page), /de nootnummers zijn gewijzigd/);
    assert.doesNotMatch(await visibleBanner(page), /kanttekeningen|Bijbeltekst|AI-wijzigingen/);
    await options(page, true, true);
    assert.match(await visibleBanner(page), /de kanttekeningen en de nootnummers zijn gewijzigd/);
    await options(page, false, false);
    assert.equal(await visibleBanner(page), '');
    await page.close();
});

test('citation-only changes warn only while citation formatting is on', async () => {
    const page = await changedPage(chapter => {
        chapter.verses[0].text2026_html = chapter.verses[0].text2026_html.replace('devil-speaks', 'god-speaks');
    });
    await options(page, false, false);
    assert.match(await visibleBanner(page), /de citaatopmaak is gewijzigd/);
    await options(page, false, false, false);
    assert.equal(await visibleBanner(page), '');
    assert.equal(await page.locator('.chapter-concept-tag').count(), 0);
    await page.close();
});

test('a note popup checks that verse, including an unchanged verse in an otherwise changed chapter', async () => {
    for (const reader of ['index.html', 'lees.html']) {
        const page = await changedPage(chapter => {
            chapter.verses[0].marginNotes[0].text2026 += ' Gewijzigd.';
        }, reader);
        if (reader === 'index.html') await options(page, false, true);
        assert.equal(await visibleBanner(page), '');
        const rows = reader === 'index.html' ? '.verse-row' : '.verse-span';
        const markers = reader === 'index.html' ? '.col-2026 .note-marker' : '.verse-text .note-marker';
        const popup = reader === 'index.html' ? '.note-tooltip' : '#notes-content';
        await page.locator(rows + '[data-verse="1"] ' + markers).first().click();
        await page.locator(popup + ' .verification-component-warning').waitFor();
        assert.match(await page.locator(popup).innerText(), /de kanttekeningen zijn gewijzigd/);
        if (reader === 'index.html') await page.locator('#chapter-title').click();
        await page.locator(rows + '[data-verse="4"] ' + markers).first().click();
        await page.locator(popup + ' [data-verification="text-verse:genesis/3/4"] button').waitFor();
        assert.doesNotMatch(await page.locator(popup).innerText(), /zijn gewijzigd|nog niet geverifieerd/);
        await page.close();
    }
});

test('verification records only visible parts, without approving hidden changed notes', async () => {
    const page = await changedPage(chapter => {
        chapter.verses[0].text2026 += ' Tekstwijziging.';
        chapter.verses[0].text2026_html += ' Tekstwijziging.';
        chapter.verses[0].marginNotes[0].text2026 += ' Nootwijziging.';
    }, 'index.html', 'admin');
    await options(page, false, false);
    const posted = page.waitForRequest(request => request.method() === 'POST' && request.url().endsWith('/reviews'));
    await page.locator('#chapter-verification > span > button').first().click();
    const payload = (await posted).postDataJSON();
    assert.ok(payload.components.text);
    assert.equal('notes' in payload.components, false);
    await page.locator('#chapter-verification').getByText('Verificatie opgeslagen.', { exact: true }).waitFor();
    assert.equal(await visibleBanner(page), '');
    await options(page, true, false);
    assert.match(await visibleBanner(page), /kanttekeningen/);
    assert.doesNotMatch(await visibleBanner(page), /Bijbeltekst/);
    await page.close();
});

test('hidden local note edits and a hidden Bible text do not produce a text warning', async () => {
    const page = await changedPage(chapter => {
        chapter.verses[0].text2026 += ' Veranderd.';
        chapter.verses[0].text2026_html += ' Veranderd.';
    });
    await page.evaluate(() => {
        Storage.saveVerse('genesis', 3, 1, { marginNotes: { 0: 'Lokale noot' } });
        document.getElementById('content').classList.add('hide-2026', 'hide-diff', 'hide-margin2026');
    });
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    assert.equal(await visibleBanner(page), '');
    assert.equal(await page.locator('.chapter-concept-tag').count(), 0);
    await page.close();
});

test('the main reader popup fits a narrow viewport and shows the clicked verse notes', async () => {
    const page = await changedPage(() => {});
    await page.setViewportSize({ width: 390, height: 844 });
    await options(page, false, true);
    await page.locator('.verse-row[data-verse="1"] .col-2026 .note-marker').first().click();
    await page.locator('.note-tooltip .ov-verification button').waitFor();
    const box = await page.locator('.note-tooltip').boundingBox();
    assert.ok(box.x >= 0 && box.x + box.width <= 390);
    assert.ok(box.y >= 0 && box.y + box.height <= 844);
    assert.equal(await page.locator('.note-tooltip .note-popup-item').count(), 3);
    assert.match(await page.locator('.note-tooltip').innerText(), /Noot 1/);
    await page.close();
});
