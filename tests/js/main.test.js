const { JSDOM } = require('jsdom');
const fs = require('fs');
const path = require('path');

const mainJs = fs.readFileSync(path.resolve(__dirname, '../../static/js/main.js'), 'utf-8');

function criarDOM(setupWindow) {
    const html = `
    <!DOCTYPE html>
    <html>
    <body>
        <div class="nav-pills" role="tablist">
            <button class="tab-btn active" data-section="classificacao"
                role="tab" aria-selected="true" aria-controls="classificacao" id="tab-classificacao">
                Classificacao
            </button>
            <button class="tab-btn" data-section="artilharia"
                role="tab" aria-selected="false" aria-controls="artilharia" id="tab-artilharia">
                Artilharia
            </button>
            <button class="tab-btn" data-section="graficos"
                role="tab" aria-selected="false" aria-controls="graficos" id="tab-graficos">
                Graficos
            </button>
        </div>
        <section id="classificacao" class="section active" role="tabpanel">
            <div class="filter-group">
                <button class="filter-btn active" data-zona="todas" aria-pressed="true">Todas</button>
                <button class="filter-btn" data-zona="libertadores" aria-pressed="false">Libertadores</button>
            </div>
            <span id="classificacao-count"></span>
            <p id="classificacao-empty" hidden></p>
            <table id="tabela-classificacao"><tbody>
                <tr data-time="Palmeiras" data-sigla="PAL" data-zona="libertadores">
                    <td class="col-time"><span>Palmeiras</span></td>
                </tr>
            </tbody></table>
        </section>
        <section id="artilharia" class="section" role="tabpanel"></section>
        <section id="graficos" class="section" role="tabpanel">
            <p id="charts-status" class="charts-state" role="status" aria-live="polite" hidden></p>
        </section>
    </body>
    </html>`;

    const dom = new JSDOM(html, {
        runScripts: 'dangerously',
        pretendToBeVisual: true,
        url: 'http://localhost/'
    });
    if (typeof setupWindow === 'function') {
        setupWindow(dom.window);
    }
    dom.window.eval(mainJs);
    return dom;
}

describe('Navegacao por abas', () => {
    let dom, document;

    beforeEach(() => {
        dom = criarDOM();
        document = dom.window.document;
    });

    afterEach(() => {
        dom.window.close();
    });

    test('aba classificacao esta ativa por padrao', () => {
        const tab = document.getElementById('tab-classificacao');
        const panel = document.getElementById('classificacao');
        expect(tab.classList.contains('active')).toBe(true);
        expect(tab.getAttribute('aria-selected')).toBe('true');
        expect(panel.classList.contains('active')).toBe(true);
    });

    test('clicar em artilharia ativa a aba correta', () => {
        const tabArtilharia = document.getElementById('tab-artilharia');
        tabArtilharia.click();

        expect(tabArtilharia.classList.contains('active')).toBe(true);
        expect(tabArtilharia.getAttribute('aria-selected')).toBe('true');
        expect(document.getElementById('artilharia').classList.contains('active')).toBe(true);

        const tabClassificacao = document.getElementById('tab-classificacao');
        expect(tabClassificacao.classList.contains('active')).toBe(false);
        expect(tabClassificacao.getAttribute('aria-selected')).toBe('false');
        expect(document.getElementById('classificacao').classList.contains('active')).toBe(false);
    });

    test('clicar em graficos ativa a aba correta', () => {
        const tabGraficos = document.getElementById('tab-graficos');
        tabGraficos.click();

        expect(tabGraficos.classList.contains('active')).toBe(true);
        expect(document.getElementById('graficos').classList.contains('active')).toBe(true);
        expect(document.getElementById('classificacao').classList.contains('active')).toBe(false);
        expect(document.getElementById('artilharia').classList.contains('active')).toBe(false);
    });

    test('apenas uma aba fica ativa por vez', () => {
        const tabs = document.querySelectorAll('.tab-btn');
        const sections = document.querySelectorAll('.section');

        tabs[2].click();
        const ativas = [...tabs].filter((t) => t.classList.contains('active'));
        const secAtivas = [...sections].filter((s) => s.classList.contains('active'));

        expect(ativas).toHaveLength(1);
        expect(secAtivas).toHaveLength(1);
    });

    test('data-section invalido nao quebra', () => {
        const btn = document.createElement('button');
        btn.classList.add('tab-btn');
        btn.dataset.section = 'secao_inexistente';
        btn.setAttribute('role', 'tab');
        btn.setAttribute('aria-selected', 'false');
        document.querySelector('.nav-pills').appendChild(btn);

        expect(() => btn.click()).not.toThrow();
    });

    test('favoritos invalido no localStorage nao quebra a inicializacao', () => {
        const domLocal = criarDOM((window) => {
            window.localStorage.setItem('favoritos', '{invalido');
        });
        const documentLocal = domLocal.window.document;

        expect(documentLocal.getElementById('tab-classificacao').classList.contains('active')).toBe(true);

        domLocal.window.close();
    });

    test('filtro ativo atualiza aria-pressed', () => {
        const filtros = document.querySelectorAll('.filter-btn');
        filtros[1].click();

        expect(filtros[0].getAttribute('aria-pressed')).toBe('false');
        expect(filtros[1].getAttribute('aria-pressed')).toBe('true');
    });
});

describe('Atalho do comparador', () => {
    test('compara lider e vice-lider com um clique', () => {
        const dom = new JSDOM(
            `<!DOCTYPE html><html><body>
                <select id="cmp-time1"><option value=""></option><option value="PAL">Palmeiras</option></select>
                <select id="cmp-time2"><option value=""></option><option value="FLA">Flamengo</option></select>
                <button id="cmp-btn" disabled>Comparar</button>
                <button id="cmp-quick-leaders">Comparar líder e vice-líder</button>
                <div id="cmp-result"></div>
            </body></html>`,
            { runScripts: 'dangerously', pretendToBeVisual: true, url: 'http://localhost/' }
        );
        dom.window.dadosClassificacao = [
            {
                sigla: 'PAL',
                time: 'Palmeiras',
                posicao: 1,
                pontos: 48,
                vitorias: 14,
                empates: 6,
                derrotas: 2,
                gols_pro: 38,
                gols_contra: 16,
                saldo: 22,
                aproveitamento: 72.7,
                escudo: ''
            },
            {
                sigla: 'FLA',
                time: 'Flamengo',
                posicao: 2,
                pontos: 42,
                vitorias: 12,
                empates: 6,
                derrotas: 3,
                gols_pro: 39,
                gols_contra: 18,
                saldo: 21,
                aproveitamento: 66.7,
                escudo: ''
            }
        ];
        dom.window.eval(mainJs);
        dom.window.document.dispatchEvent(new dom.window.Event('DOMContentLoaded'));

        dom.window.document.getElementById('cmp-quick-leaders').click();

        expect(dom.window.document.getElementById('cmp-time1').value).toBe('PAL');
        expect(dom.window.document.getElementById('cmp-time2').value).toBe('FLA');
        expect(dom.window.document.getElementById('cmp-result').textContent).toContain('Palmeiras');
        expect(dom.window.document.getElementById('cmp-result').textContent).toContain('Flamengo');

        dom.window.close();
    });

    test('exibe estado visivel quando os graficos nao estao disponiveis', async () => {
        const dom = criarDOM();
        await new Promise((resolve) => setTimeout(resolve, 0));
        const tabGraficos = dom.window.document.getElementById('tab-graficos');
        const status = dom.window.document.getElementById('charts-status');

        tabGraficos.click();

        expect(status.hidden).toBe(false);
        expect(status.textContent).toContain('indisponíveis');
        expect(dom.window.document.getElementById('graficos').getAttribute('aria-busy')).toBe('false');
        dom.window.close();
    });

    test('preserva texto de clube e ignora escudo com protocolo inseguro', () => {
        const dom = new JSDOM(
            `<!DOCTYPE html><html><body>
                <select id="cmp-time1"><option value=""></option><option value="BAD">A</option></select>
                <select id="cmp-time2"><option value=""></option><option value="SAFE">B</option></select>
                <button id="cmp-btn" disabled>Comparar</button>
                <button id="cmp-quick-leaders">Comparar líder e vice-líder</button>
                <div id="cmp-result"></div>
            </body></html>`,
            { runScripts: 'dangerously', pretendToBeVisual: true, url: 'http://localhost/' }
        );
        dom.window.dadosClassificacao = [
            {
                sigla: 'BAD',
                time: '<img src=x onerror=window.__injetado=true>',
                posicao: 1,
                pontos: 48,
                vitorias: 14,
                empates: 6,
                derrotas: 2,
                gols_pro: 38,
                gols_contra: 16,
                saldo: 22,
                aproveitamento: 72.7,
                escudo: 'javascript:window.__injetado=true'
            },
            {
                sigla: 'SAFE',
                time: 'Flamengo',
                posicao: 2,
                pontos: 42,
                vitorias: 12,
                empates: 6,
                derrotas: 3,
                gols_pro: 39,
                gols_contra: 18,
                saldo: 21,
                aproveitamento: 66.7,
                escudo: ''
            }
        ];
        dom.window.eval(mainJs);
        dom.window.document.dispatchEvent(new dom.window.Event('DOMContentLoaded'));

        dom.window.document.getElementById('cmp-quick-leaders').click();

        const result = dom.window.document.getElementById('cmp-result');
        expect(result.textContent).toContain('<img src=x onerror=window.__injetado=true>');
        expect(result.querySelector('img')).toBeNull();
        expect(dom.window.__injetado).toBeUndefined();
        dom.window.close();
    });

    test('associa o picker customizado ao listbox e alterna hidden com foco', () => {
        const dom = new JSDOM(
            `<!DOCTYPE html><html><body>
                <select id="cmp-time1"><option value=""></option><option value="PAL">Palmeiras</option></select>
                <select id="cmp-time2"><option value=""></option><option value="FLA">Flamengo</option></select>
                <button id="cmp-btn" disabled>Comparar</button>
                <div class="cmp-picker" data-select="cmp-time1">
                    <button type="button" class="cmp-picker-button" aria-haspopup="listbox" aria-expanded="false">
                        <span id="cmp-time1-current">Selecione</span>
                    </button>
                    <div id="cmp-time1-listbox" class="cmp-picker-list" role="listbox">
                        <button id="cmp-time1-option-PAL" type="button" class="cmp-picker-option" role="option" data-value="PAL" aria-selected="false">Palmeiras</button>
                    </div>
                </div>
                <div class="cmp-picker" data-select="cmp-time2">
                    <button type="button" class="cmp-picker-button" aria-haspopup="listbox" aria-expanded="false">
                        <span id="cmp-time2-current">Selecione</span>
                    </button>
                    <div id="cmp-time2-listbox" class="cmp-picker-list" role="listbox">
                        <button id="cmp-time2-option-FLA" type="button" class="cmp-picker-option" role="option" data-value="FLA" aria-selected="false">Flamengo</button>
                    </div>
                </div>
                <div id="cmp-result"></div>
            </body></html>`,
            { runScripts: 'dangerously', pretendToBeVisual: true, url: 'http://localhost/' }
        );
        dom.window.eval(mainJs);
        dom.window.document.dispatchEvent(new dom.window.Event('DOMContentLoaded'));

        const picker = dom.window.document.querySelector('.cmp-picker');
        const button = picker.querySelector('.cmp-picker-button');
        const listbox = picker.querySelector('[role="listbox"]');
        const option = picker.querySelector('[role="option"]');

        expect(button.getAttribute('aria-controls')).toBe('cmp-time1-listbox');
        expect(listbox.hidden).toBe(true);
        expect(listbox.tabIndex).toBe(-1);
        expect(listbox.getAttribute('tabindex')).toBe('-1');
        button.click();
        expect(listbox.hidden).toBe(false);
        expect(button.getAttribute('aria-expanded')).toBe('true');

        option.dispatchEvent(new dom.window.Event('focus'));
        expect(listbox.getAttribute('aria-activedescendant')).toBe('cmp-time1-option-PAL');

        option.dispatchEvent(new dom.window.KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
        expect(listbox.hidden).toBe(true);
        expect(button.getAttribute('aria-expanded')).toBe('false');
        dom.window.close();
    });

    test('mantem o segundo picker aberto quando o primeiro perde foco antes do clique', async () => {
        const dom = new JSDOM(
            `<!DOCTYPE html><html><body>
                <select id="cmp-time1"><option value=""></option><option value="PAL">Palmeiras</option></select>
                <select id="cmp-time2"><option value=""></option><option value="FLA">Flamengo</option></select>
                <button id="cmp-btn" disabled>Comparar</button>
                <div class="cmp-picker" data-select="cmp-time1">
                    <button type="button" class="cmp-picker-button" aria-haspopup="listbox" aria-expanded="false">Time 1</button>
                    <div id="cmp-time1-listbox" class="cmp-picker-list" role="listbox">
                        <button id="cmp-time1-option-PAL" type="button" class="cmp-picker-option" role="option" data-value="PAL">Palmeiras</button>
                    </div>
                </div>
                <div class="cmp-picker" data-select="cmp-time2">
                    <button type="button" class="cmp-picker-button" aria-haspopup="listbox" aria-expanded="false">Time 2</button>
                    <div id="cmp-time2-listbox" class="cmp-picker-list" role="listbox">
                        <button id="cmp-time2-option-FLA" type="button" class="cmp-picker-option" role="option" data-value="FLA">Flamengo</button>
                    </div>
                </div>
                <div id="cmp-result"></div>
            </body></html>`,
            { runScripts: 'dangerously', pretendToBeVisual: true, url: 'http://localhost/' }
        );
        const ready = new Promise((resolve) => {
            dom.window.document.addEventListener('DOMContentLoaded', resolve, { once: true });
        });
        dom.window.eval(mainJs);
        await ready;

        const pickers = dom.window.document.querySelectorAll('.cmp-picker');
        const picker1 = pickers[0];
        const picker2 = pickers[1];
        const option1 = picker1.querySelector('[role="option"]');
        const button2 = picker2.querySelector('.cmp-picker-button');
        const listbox1 = picker1.querySelector('[role="listbox"]');
        const listbox2 = picker2.querySelector('[role="listbox"]');

        picker1.querySelector('.cmp-picker-button').click();
        option1.focus();
        button2.focus();
        button2.click();

        await new Promise((resolve) => dom.window.setTimeout(resolve, 0));

        expect(picker1.classList.contains('open')).toBe(false);
        expect(listbox1.hidden).toBe(true);
        expect(picker2.classList.contains('open')).toBe(true);
        expect(button2.getAttribute('aria-expanded')).toBe('true');
        expect(listbox2.hidden).toBe(false);
        dom.window.close();
    });
});
