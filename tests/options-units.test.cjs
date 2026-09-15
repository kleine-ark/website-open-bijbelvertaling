const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const vm = require('node:vm');
const root = resolve(__dirname, '..');

function options() {
    const context = vm.createContext({ window: {} });
    for (const file of ['js/optie-maten.js', 'js/opties.js']) {
        vm.runInContext(readFileSync(resolve(root, file), 'utf8'), context);
    }
    const current = context.window.Opties;
    current.state = { ...current.DEFAULTS };
    current._eenheden = current._maatIndex(JSON.parse(readFileSync(resolve(root, 'data/eenheden.json'), 'utf8')));
    current._tijden = current._tijdIndex(JSON.parse(readFileSync(resolve(root, 'data/tijden.json'), 'utf8')));
    return current;
}

test('extracted number formatting preserves small numbers and marks composite numbers', () => {
    const current = options();
    current.state.getalweergave = 'cijfers';
    assert.equal(current.toonGetalcijfers('<i>twaalf</i> stammen'), '<i>twaalf</i> stammen');
    assert.doesNotMatch(current.toonGetalcijfers('drie dagen en twintig nachten, maar een mens'), /getal-cijfer/);
    assert.match(current.toonGetalcijfers('twintig en een stammen'), /\(21\)<\/span>/);
    assert.match(current.toonGetalcijfers('zeven en vijftig duizend en vierhonderd'), /\(57\.400\)<\/span>/);
    assert.equal(current.toonGetalcijfers('met de duizenden van de hemel'), 'met de duizenden van de hemel');
});

test('extracted measurement helpers preserve default text and support metric conversion', () => {
    const current = options();
    assert.equal(current.rekenMaten('een dagreis', '1koningen', 19, 4), 'een dagreis');
    current.state.maatstelsel = 'metrisch';
    assert.match(current.rekenMaten('een dagreis', '1koningen', 19, 4), /ongeveer 35 km/);
});

test('time conversion still shares the extracted text and range helpers', () => {
    const current = options();
    assert.equal(current.rekenTijden('het negende uur', 'mattheus', 27, 45, 'NT'), 'het negende uur');
    current.state.tijdrekening = 'modern';
    assert.match(current.rekenTijden('het negende uur', 'mattheus', 27, 45, 'NT'), /drie uur/);
});
