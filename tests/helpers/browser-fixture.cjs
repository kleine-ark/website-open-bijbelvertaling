const { spawn, execFileSync } = require('node:child_process');
const { chromium } = require('playwright');
const { once } = require('node:events');

async function startFixture() {
    const server = spawn('python3', ['-B', 'tests/serve_verification_fixture.py']);
    server.stderr.on('data', () => {});
    const [data] = await once(server.stdout, 'data');
    const config = JSON.parse(String(data));
    const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome', headless: true });
    async function pageAs(who) {
        // Routing deliberately controls in-flight responses; worker behavior has its own tests.
        const page = await browser.newPage({ serviceWorkers: 'block' });
        await page.route('https://**', route => route.abort());
        await page.route('**/js/firebase-config.js', route => route.fulfill({ contentType: 'text/javascript', body: 'window.firebaseEnabled = true;' }));
        await page.route('**/js/auth.js', route => route.fulfill({ contentType: 'text/javascript', body: '' }));
        for (const file of ['cloud-opties', 'cloud-highlights']) {
            await page.route('**/js/' + file + '.js', route => route.fulfill({ contentType: 'text/javascript', body: '' }));
        }
        await page.addInitScript(user => {
            let listeners = [];
            window.Auth = {
                currentUser: null, stateResolved: true, init() {},
                onChange(callback) { listeners.push(callback); callback(this.currentUser, true); },
            };
            window.setTestUser = name => {
                Auth.currentUser = name ? { uid: name, getIdToken: async () => name } : null;
                listeners.forEach(callback => callback(Auth.currentUser, true));
            };
            setTestUser(user);
            localStorage.setItem('doorlopend', 'false');
        }, who);
        return page;
    }

    return {
        browser, pageAs, base: 'http://127.0.0.1:' + config.port, locationId: config.location,
        propose(payload) {
            return JSON.parse(execFileSync('python3', ['server/correction_cli.py', 'propose'], {
                input: JSON.stringify(payload), encoding: 'utf8',
                env: { ...process.env, OV_COLLABORATION_DB: config.database,
                    OV_REVIEW_CATALOG: config.catalog, OV_CONTENT_ROOT: process.cwd() },
            }));
        },
        async close() {
            await browser.close();
            if (server.exitCode === null) { server.kill(); await once(server, 'exit'); }
        },
    };
}
module.exports = { startFixture };
