const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const { startFixture } = require('./helpers/browser-fixture.cjs');
let fixture;
before(async () => { fixture = await startFixture(); });
after(async () => { await fixture.close(); });

async function requestPage(page, verse) {
    await page.goto(fixture.base + '/index.html#genesis/3');
    const control = page.locator('[data-verification="text-verse:genesis/3/' + verse + '"]');
    await control.getByRole('button', { name: 'Beoordelingsacties: Genesis 3:' + verse, exact: true }).click();
    await control.getByRole('link', { name: 'Aanpassing aanvragen', exact: true }).click();
    await page.getByLabel('Onderdeel', { exact: true }).waitFor();
}

test('request defaults to Bible text and warns only for that component', async () => {
    const page = await fixture.pageAs('reviewer');
    await requestPage(page, 1);
    assert.equal(await page.getByLabel('Onderdeel', { exact: true }).inputValue(), 'text');
    assert.equal(await page.getByLabel('Welk onderdeel moet worden aangepast?').isVisible(), false);
    await page.getByLabel('Reden voor de aanpassing').fill('Test alleen de Bijbeltekst.');
    await page.getByRole('button', { name: 'Aanvraag opslaan' }).click();
    await page.getByText('Onderdeel: de Bijbeltekst', { exact: true }).waitFor();
    await page.getByRole('link', { name: 'Open de inhoud', exact: true }).click();
    await page.locator('#ai-concept-banner:not([hidden])').waitFor();
    assert.equal(await page.locator('#ai-concept-banner').textContent(),
        'Let op: voor de Bijbeltekst is een aanpassing aangevraagd.');
    await page.close();
});

test('notes selection is saved; another component can be requested separately', async () => {
    const page = await fixture.pageAs('reviewer');
    await requestPage(page, 1);
    assert.equal(await page.getByRole('button', { name: 'Aanvraag opslaan' }).isDisabled(), true);
    await page.getByRole('link', { name: 'Open correctietaak' }).waitFor();
    await page.getByLabel('Onderdeel', { exact: true }).selectOption('notes');
    assert.equal(await page.getByRole('button', { name: 'Aanvraag opslaan' }).isEnabled(), true);
    await page.getByLabel('Reden voor de aanpassing').fill('Test de uitleg, niet de tekst.');
    await page.getByRole('button', { name: 'Aanvraag opslaan' }).click();
    await page.getByText('Onderdeel: de kanttekeningen', { exact: true }).waitFor();
    const task = await page.evaluate(async () => (await Collaboration.api('/corrections/' +
        new URL(location.href).searchParams.get('id'))).correction);
    assert.equal(task.component, 'notes');
    assert.equal(task.customTarget, '');
    await page.close();
});

test('custom target is required, safely displayed and retained in the list on mobile', async () => {
    const page = await fixture.pageAs('reviewer');
    await page.setViewportSize({ width: 390, height: 844 });
    await requestPage(page, 2);
    await page.getByLabel('Onderdeel', { exact: true }).selectOption('custom');
    await page.getByLabel('Reden voor de aanpassing').fill('Dit onderdeel moet worden nagekeken.');
    await page.getByRole('button', { name: 'Aanvraag opslaan' }).click();
    assert.equal(await page.getByLabel('Welk onderdeel moet worden aangepast?').evaluate(el => el.validity.valueMissing), true);
    const target = 'Woordkoppeling <img src=x onerror="window.leaked=true">';
    await page.getByLabel('Welk onderdeel moet worden aangepast?').fill(target);
    await page.screenshot({ path: '/tmp/openvertaling-correction-target-mobile.png', fullPage: true });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.getByRole('button', { name: 'Aanvraag opslaan' }).click();
    await page.getByText('Onderdeel: ' + target, { exact: true }).waitFor();
    assert.equal(await page.locator('.correction-scope img').count(), 0);
    await page.getByRole('link', { name: 'Alle correctietaken' }).click();
    await page.getByText('Onderdeel: ' + target, { exact: true }).waitFor();
    await page.close();
});
