const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;

test.beforeEach(async ({ page }) => {
    await page.route('https://fonts.googleapis.com/**', (route) =>
        route.fulfill({ contentType: 'text/css', body: '' })
    );
    await page.route('https://fonts.gstatic.com/**', (route) => route.fulfill({ body: '' }));
    await page.route('https://cdn.jsdelivr.net/**', (route) =>
        route.fulfill({ contentType: 'application/javascript', body: '' })
    );
});

const viewports = [
    { name: 'desktop', width: 1440, height: 900 },
    { name: 'tablet', width: 1024, height: 768 },
    { name: 'mobile', width: 390, height: 844 },
    { name: 'mobile-small', width: 320, height: 568 }
];

for (const viewport of viewports) {
    for (const theme of ['light']) {
        test(`${viewport.name} em tema claro não transborda e passa WCAG AA`, async ({ page }) => {
            await page.setViewportSize(viewport);
            await page.addInitScript((selectedTheme) => localStorage.setItem('theme', selectedTheme), theme);
            await page.goto('/');
            await expect(page.locator('#standings-heading')).toContainText('Classificação atual');
            await expect(page.locator('html')).toHaveAttribute('data-theme', theme);

            const overflow = await page.evaluate(() => ({
                viewport: {
                    innerWidth,
                    clientWidth: document.documentElement.clientWidth,
                    bodyWidth: document.body.clientWidth
                },
                delta: document.documentElement.scrollWidth - document.documentElement.clientWidth,
                offenders: Array.from(document.querySelectorAll('body *'))
                    .map((element) => {
                        const box = element.getBoundingClientRect();
                        return {
                            selector: `${element.tagName.toLowerCase()}.${element.className || ''}`,
                            left: box.left,
                            right: box.right,
                            width: box.width
                        };
                    })
                    .filter((box) => box.left < -1 || box.right > document.documentElement.clientWidth + 1)
                    .sort((a, b) => Math.max(b.right - innerWidth, -b.left) - Math.max(a.right - innerWidth, -a.left))
                    .slice(0, 12)
            }));
            expect(
                overflow.delta,
                JSON.stringify({ viewport: overflow.viewport, offenders: overflow.offenders })
            ).toBeLessThanOrEqual(1);

            if (viewport.width <= 720) {
                const visibleColumns = await page
                    .locator('.standings-table thead th')
                    .evaluateAll((headers) =>
                        headers
                            .filter((header) => getComputedStyle(header).display !== 'none')
                            .map((header) => header.textContent.trim())
                    );
                expect(visibleColumns).toEqual(['#', 'Clube', 'P', 'J', 'SG']);
                for (const selector of ['.favorite-toggle', '.row-expand']) {
                    const target = await page.locator(selector).first().boundingBox();
                    expect(target.width).toBeGreaterThanOrEqual(44);
                    expect(target.height).toBeGreaterThanOrEqual(44);
                }
            }

            const sections = page.locator('.edition-section');
            for (let index = 0; index < (await sections.count()); index += 1) {
                await sections.nth(index).scrollIntoViewIfNeeded();
            }
            await page.evaluate(() => window.scrollTo(0, 0));

            const accessibility = await new AxeBuilder({ page })
                .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
                .analyze();
            expect(accessibility.violations).toEqual([]);
        });
    }
}

test('fluxo principal preserva rodada, favoritos, filtros e comparador compartilhável', async ({ page }) => {
    const consoleErrors = [];
    page.on('console', (message) => {
        if (message.type() === 'error') consoleErrors.push(message.text());
    });
    await page.goto('/?rodada=26');

    await page.locator('#round-next').click();
    await expect(page).toHaveURL(/rodada=27/);

    await page.locator('.favorite-toggle').first().click();
    await page.locator('[data-zona="favoritos"]').click();
    await expect(page.locator('#classificacao-count')).toHaveText('1 clube exibido');
    await page.locator('[data-zona="todas"]').click();

    await page.locator('#cmp-time1').selectOption('FLA');
    await page.locator('#cmp-time2').selectOption('PAL');
    await page.locator('#cmp-btn').click();
    await expect(page).toHaveURL(/time1=FLA/);
    await expect(page).toHaveURL(/time2=PAL/);
    await expect(page).toHaveURL(/#comparador$/);
    await expect(page.locator('#cmp-result')).toContainText('Flamengo');

    expect(consoleErrors).toEqual([]);
});

test('seletor de rodadas funciona por teclado e página de clube mantém o percurso', async ({ page }) => {
    await page.goto('/');
    await page.locator('#round-trigger').focus();
    await page.keyboard.press('Enter');
    await page.locator('.round-option').first().focus();
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('Enter');
    await expect(page).toHaveURL(/rodada=2/);

    await page.goto('/time/FLA/');
    await expect(page.locator('h1')).toHaveText('Flamengo');
    await expect(page.getByText('Último jogo', { exact: true })).toBeVisible();
    await expect(page.getByText('Próximo jogo', { exact: true })).toBeVisible();
    await expect(page.getByRole('link', { name: /Comparar Flamengo/ })).toHaveAttribute('href', /time1=FLA/);
    const accessibility = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
        .analyze();
    expect(accessibility.violations).toEqual([]);
});

test('sistema visual usa tipografia esportiva, cabeçalho verde e comparador claro', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/');

    const visual = await page.locator('body').evaluate(() => {
        const masthead = document.querySelector('.header-row');
        const heroTitle = document.querySelector('#standings-heading');
        const section = document.querySelector('.edition-section');
        const sectionTitle = document.querySelector('#round-heading');
        const comparison = document.querySelector('.compare-edition');
        const header = document.querySelector('.site-header');
        return {
            mastheadHeight: masthead.getBoundingClientRect().height,
            heroSize: Number.parseFloat(getComputedStyle(heroTitle).fontSize),
            sectionPadding: Number.parseFloat(getComputedStyle(section).paddingTop),
            sectionTitleFamily: getComputedStyle(sectionTitle).fontFamily,
            bodyFamily: getComputedStyle(document.body).fontFamily,
            headerBackground: getComputedStyle(header).backgroundColor,
            comparisonBackground: getComputedStyle(comparison).backgroundColor,
            bodyBackground: getComputedStyle(document.body).backgroundColor,
            decorativeNumbers: document.querySelectorAll('.section-number, .rail-index').length
        };
    });

    expect(visual.mastheadHeight).toBeLessThanOrEqual(76);
    expect(visual.heroSize).toBeLessThanOrEqual(44);
    expect(visual.sectionPadding).toBeLessThanOrEqual(64);
    expect(visual.sectionTitleFamily).toContain('Inter');
    expect(visual.bodyFamily).toContain('Inter');
    expect(visual.headerBackground).toBe('rgb(7, 82, 62)');
    expect(visual.comparisonBackground).toBe(visual.bodyBackground);
    expect(visual.decorativeNumbers).toBe(0);
});

test('navegação fixa acompanha a seção de gráficos durante a rolagem', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 629 });
    await page.goto('/#desempenho');
    await page.evaluate(() => window.scrollTo(0, document.querySelector('#desempenho').offsetTop + 500));

    await expect(page.locator('.edition-nav-link[href="#desempenho"]')).toHaveClass(/is-active/);
    await expect(page.locator('.edition-nav-link[href="#artilharia"]')).not.toHaveClass(/is-active/);
});
