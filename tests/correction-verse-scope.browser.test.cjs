const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const { startFixture } = require('./helpers/browser-fixture.cjs');
let fixture;
before(async () => { fixture = await startFixture(); });
after(async () => { await fixture.close(); });

test('a verse request leaves siblings verified and the chapter recovers after that verse is reviewed', async () => {
    const page = await fixture.pageAs('admin');
    await page.goto(fixture.base + '/index.html#genesis/3');
    const chapter = page.locator('#chapter-verification');
    await chapter.getByRole('button', { name: 'Geverifieerd: Genesis 3', exact: true }).waitFor();
    const original = await page.evaluate(async () => (await Collaboration.api('/subject?type=text-chapter&id=genesis/3')).subject.latestReview);
    const verse = page.locator('[data-verification="text-verse:genesis/3/1"]');
    const sibling = page.locator('[data-verification="text-verse:genesis/3/2"]');
    await verse.getByRole('button', { name: 'Beoordelingsacties: Genesis 3:1', exact: true }).click();
    await verse.getByRole('link', { name: 'Aanpassing aanvragen', exact: true }).click();
    await page.getByLabel('Reden voor de aanpassing').fill('Alleen dit vers controleren.');
    await page.getByRole('button', { name: 'Aanvraag opslaan' }).click();
    await page.getByText('Aanvraag opgeslagen. Deze wacht op verwerking op verzoek.').waitFor();
    const taskURL = page.url();
    await page.getByRole('link', { name: 'Open de inhoud', exact: true }).click();
    await chapter.getByRole('button', { name: 'Aanpassing nodig: Genesis 3', exact: true }).waitFor();
    await sibling.getByRole('button', { name: 'Geverifieerd: Genesis 3:2', exact: true }).waitFor();
    await page.goto(taskURL);
    await page.getByText('Afsluiten zonder wijziging', { exact: true }).click();
    await page.getByLabel('Reden', { exact: true }).fill('Test afgerond; vers opnieuw controleren.');
    await page.getByRole('button', { name: 'Taak afsluiten', exact: true }).click();
    await page.getByText('Besluit opgeslagen.', { exact: true }).waitFor();
    await page.getByRole('link', { name: 'Open de inhoud', exact: true }).click();
    await verse.getByRole('button', { name: 'Verifiëren: Genesis 3:1', exact: true }).click();
    await chapter.getByRole('button', { name: 'Geverifieerd: Genesis 3', exact: true }).waitFor();
    const restored = await page.evaluate(async () => (await Collaboration.api('/subject?type=text-chapter&id=genesis/3')).subject.latestReview);
    assert.deepEqual(restored, original);
    await sibling.getByRole('button', { name: 'Geverifieerd: Genesis 3:2', exact: true }).waitFor();
    await page.close();
});

test('history explicitly identifies the verses covered by a repaired chapter event', async () => {
    const page = await fixture.pageAs('admin');
    await page.route(url => url.pathname === '/api/collaboration/reviews', async route => {
        const response = await route.fetch();
        const data = await response.json();
        await route.fulfill({ json: { total: 1, items: [{ ...data.items[0],
            components: ['text'], verseScopes: { text: [6] }, label: 'Johannes 1', decision: 'revoked' }] } });
    });
    await page.goto(fixture.base + '/beoordelingsgeschiedenis.html');
    await page.getByText('de Bijbeltekst — vers 6', { exact: true }).waitFor();
    await page.close();
});
