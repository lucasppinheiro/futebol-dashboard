const fs = require('fs');
const { defineConfig } = require('@playwright/test');

const chromeWindows = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const executablePath =
    process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || (fs.existsSync(chromeWindows) ? chromeWindows : undefined);
module.exports = defineConfig({
    testDir: './tests/e2e',
    globalSetup: require.resolve('./tests/e2e/global-setup'),
    timeout: 30_000,
    expect: { timeout: 5_000 },
    fullyParallel: false,
    workers: 1,
    reporter: 'line',
    use: {
        baseURL: 'http://127.0.0.1:5179',
        browserName: 'chromium',
        headless: true,
        reducedMotion: 'reduce',
        launchOptions: executablePath ? { executablePath } : {},
        screenshot: 'only-on-failure',
        trace: 'retain-on-failure'
    }
});
