const { JSDOM } = require('jsdom');
const fs = require('fs');
const path = require('path');

const sharedJs = fs.readFileSync(path.resolve(__dirname, '../../static/js/shared.js'), 'utf-8');
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
        <section id="classificacao" class="section active" role="tabpanel"></section>
        <section id="artilharia" class="section" role="tabpanel"></section>
        <section id="graficos" class="section" role="tabpanel"></section>
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
    dom.window.eval(sharedJs);
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
});
