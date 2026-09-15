const { test } = require('node:test');
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const root = resolve(__dirname, '..');

test('every site navigation page loads the single theme module early, without inline copies', () => {
    const files = execFileSync('git', ['ls-files', '-z', '*.html'], { cwd: root, encoding: 'utf8' }).split('\0').filter(Boolean);
    let checked = 0;
    for (const file of files) {
        const html = readFileSync(resolve(root, file), 'utf8');
        if (!/src=["'][^"']*topnav\.js(?:\?[^"']*)?["']/.test(html) && !html.includes('/js/theme.js')) continue;
        checked++;
        const tags = [...html.matchAll(/<script\b[^>]*\bsrc=["']\/js\/theme\.js["'][^>]*><\/script>/g)];
        assert.equal(tags.length, 1, file);
        assert.ok(tags[0].index < html.indexOf('</head>'), file);
        const style = html.match(/<style\b|<link\b[^>]*rel=["']stylesheet["']/i);
        if (style) assert.ok(tags[0].index < style.index, file + ': theme must precede styles');
        assert.doesNotMatch(tags[0][0], /\b(?:defer|async)\b/, file);
        assert.doesNotMatch(html, /prefers-color-scheme/, file);
        assert.doesNotMatch(html, /getElementById\(['"]topnav-theme-toggle['"]\)/, file);
    }
    assert.ok(checked > 100);
});

test('direct option-script consumers load the extracted numeric module first', () => {
    const files = execFileSync('git', ['ls-files', '-z', '*.html'], { cwd: root, encoding: 'utf8' }).split('\0').filter(Boolean);
    for (const file of files) {
        const html = readFileSync(resolve(root, file), 'utf8');
        const options = html.indexOf('<script src="js/opties.js');
        if (options === -1) continue;
        const units = html.indexOf('<script src="js/optie-maten.js"></script>');
        assert.ok(units !== -1 && units < options, file);
    }
    for (const file of ['js/opties.js', 'js/optie-maten.js', 'js/theme.js']) {
        assert.ok(readFileSync(resolve(root, file), 'utf8').split('\n').length < 1000, file);
    }
});

test('theme resolution and theme-button handling have no duplicated options implementation', () => {
    const options = readFileSync(resolve(root, 'js/opties.js'), 'utf8');
    assert.doesNotMatch(options, /prefers-color-scheme|applyThemeClass|topnav-theme-toggle/);
    for (const file of ['js/cloud-opties.js', 'js/global-options-host.js']) {
        assert.doesNotMatch(readFileSync(resolve(root, file), 'utf8'), /applyThemeClass/);
    }
});
