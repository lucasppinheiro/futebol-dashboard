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
});
