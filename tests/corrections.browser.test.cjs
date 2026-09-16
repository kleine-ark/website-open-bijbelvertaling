const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { startFixture } = require('./helpers/browser-fixture.cjs');
let fixture;
before(async () => { fixture = await startFixture(); });
after(async () => { await fixture.close(); });

test('ordinary and anonymous users cannot request, read or decide corrections', async () => {
    for (const who of [null, 'reader']) {
        const page = await fixture.pageAs(who);
        await page.goto(fixture.base + '/correcties.html');
        await page.waitForURL(url => url.pathname === '/index.html');
        assert.equal(await page.locator('[data-collaboration-link="corrections"]').count(), 0);
        const responses = await page.evaluate(async who => {
            const headers = { 'Content-Type': 'application/json' };
            if (who) headers.Authorization = 'Bearer ' + who;
            const prefix = '/api/collaboration/corrections';
            return Promise.all([[prefix, 'GET'], [prefix, 'POST'],
                [prefix + '/11111111-1111-1111-1111-111111111111/decision', 'POST']].map(async ([url, method]) =>
                (await fetch(url, { headers, method, ...(method === 'POST' ? { body: '{}' } : {}) })).status));
        }, who);
        assert.deepEqual(responses, [who ? 403 : 401, who ? 403 : 401, who ? 403 : 401]);
        await page.close();
    }
});

test('request → private operator proposal → return → accept, with identity and mobile checks', async () => {
    const page = await fixture.pageAs('reviewer');
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(fixture.base + '/index.html#genesis/1');
    const control = page.locator('[data-verification="text-verse:genesis/1/1"]');
    await control.waitFor();
    await control.getByRole('button', { name: 'Beoordelingsacties: Genesis 1:1', exact: true }).click();
    await control.getByRole('link', { name: 'Aanpassing aanvragen' }).click();
    await page.getByRole('heading', { name: 'Aanpassing aanvragen: Genesis 1:1' }).waitFor();
    const note = 'De woordkeuze moet worden nagekeken. <img src=x onerror="window.leaked=true">';
    await page.getByLabel('Reden voor de aanpassing').fill(note);
    await page.getByRole('button', { name: 'Aanvraag opslaan' }).click();
    await page.getByText('Aanvraag opgeslagen. Deze wacht op verwerking op verzoek.').waitFor();
    assert.equal(await page.locator('.correction-note img').count(), 0);
    const id = new URL(page.url()).searchParams.get('id');
    assert.ok(id);
    const task = await page.evaluate(async id => (await Collaboration.api('/corrections/' + id)).correction, id);
    assert.equal(JSON.stringify(task).includes('reviewer@example.test'), false);
    assert.equal(task.events[0].actor, undefined);
    const state = await page.evaluate(async () => (await Collaboration.api('/subject?type=text-chapter&id=genesis/1')).subject);
    assert.equal(state.status, 'correction-needed');

    function proposal(version, text) {
        const before = fs.readFileSync('data/genesis/1.json', 'utf8');
        const data = JSON.parse(before);
        data.verses[0].text2026 = text;
        data.verses[0].text2026_html = text;
        return fixture.propose({ id, version, summary: 'Voorstel voor de woordkeuze.', files: [
            { path: 'data/genesis/1.json', before, after: JSON.stringify(data, null, 2) + '\n' }
        ] });
    }
    proposal(task.version, 'Een eerste voorstel.');
    await page.reload();
    await page.getByRole('button', { name: 'Voorstel accepteren voor publicatie' }).waitFor();
    assert.match(await page.locator('.correction-diff').first().innerText(), /Een eerste voorstel/);
    await page.getByText('Ander voorstel aanvragen', { exact: true }).click();
    const returned = page.locator('details').filter({ has: page.getByText('Ander voorstel aanvragen', { exact: true }) });
    await returned.getByLabel('Reden', { exact: true }).fill('Behoud de oorspronkelijke betekenis.');
    await returned.getByRole('button', { name: 'Terugsturen met reden' }).click();
    await page.getByText('Besluit opgeslagen.', { exact: true }).waitFor();
    const revised = await page.evaluate(async id => (await Collaboration.api('/corrections/' + id)).correction, id);
    assert.equal(revised.status, 'requested');
    proposal(revised.version, 'Een tweede voorstel.');
    await page.reload();
    await page.getByRole('button', { name: 'Voorstel accepteren voor publicatie' }).click();
    await page.getByText('Voorstel geaccepteerd. Publicatie gebeurt op verzoek; dit is nog geen verificatie.').waitFor();
    assert.equal(await page.getByRole('button', { name: 'Voorstel accepteren voor publicatie' }).count(), 0);
    assert.match(await page.locator('#corrections-content').innerText(), /Wacht op publicatie/);
    assert.equal(fs.readFileSync('data/genesis/1.json', 'utf8').includes('Een tweede voorstel.'), false);

    await page.evaluate(() => setTestUser('admin'));
    await page.getByText('Taakgeschiedenis', { exact: true }).click();
    await page.locator('.correction-log').getByText('· Reviewer', { exact: false }).first().waitFor();
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: '/tmp/openvertaling-corrections-mobile.png', fullPage: true });
    await page.evaluate(() => setTestUser(null));
    await page.waitForURL(url => url.pathname === '/index.html');
    assert.equal(await page.locator('.correction-log').count(), 0);
    await page.close();
});

test('location request, close and list use the same reviewer workflow', async () => {
    const page = await fixture.pageAs('reviewer');
    await page.goto(fixture.base + '/plaats.html?plaats=' + fixture.locationId);
    await page.getByRole('link', { name: 'Aanpassing aanvragen' }).click();
    await page.getByLabel('Reden voor de aanpassing').fill('Controleer de coördinaten.');
    await page.getByRole('button', { name: 'Aanvraag opslaan' }).click();
    await page.getByText('Afsluiten zonder wijziging', { exact: true }).click();
    await page.getByLabel('Reden', { exact: true }).fill('De huidige bron bevestigt de coördinaten.');
    await page.getByRole('button', { name: 'Taak afsluiten' }).click();
    await page.getByText('Afgesloten zonder wijziging', { exact: true }).waitFor();
    await page.getByRole('link', { name: 'Alle correctietaken' }).click();
    await page.getByLabel('Status', { exact: true }).selectOption('closed');
    await page.getByRole('button', { name: 'Filteren' }).click();
    await page.getByText('1 correctietaak/taken', { exact: true }).waitFor();
    await page.close();
});
