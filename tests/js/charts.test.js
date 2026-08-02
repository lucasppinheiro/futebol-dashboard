const { JSDOM, VirtualConsole } = require('jsdom');
const fs = require('fs');
const path = require('path');

const chartsJs = fs.readFileSync(path.resolve(__dirname, '../../static/js/charts.js'), 'utf-8');

function criarDOM(opcoes = {}) {
    const { comCanvas = true, comDados = true, comChart = true } = opcoes;

    let canvasHtml = '';
    if (comCanvas) {
        canvasHtml = `
            <canvas id="chartPontos"></canvas>
            <canvas id="chartArtilheiros"></canvas>
            <canvas id="chartAproveitamento"></canvas>
            <canvas id="chartGolsComparativo"></canvas>
        `;
    }

    const classificacao = [
        { posicao: 1, time: 'Flamengo', sigla: 'FLA', pontos: 79, aproveitamento: 69.3, gols_pro: 78, gols_contra: 27 },
        {
            posicao: 2,
            time: 'Palmeiras',
            sigla: 'PAL',
            pontos: 76,
            aproveitamento: 66.7,
            gols_pro: 66,
            gols_contra: 33
        },
        { posicao: 3, time: 'Cruzeiro', sigla: 'CRU', pontos: 70, aproveitamento: 61.4, gols_pro: 55, gols_contra: 31 }
    ];

    const artilharia = [
        { jogador: 'Kaio Jorge', time: 'Cruzeiro', sigla: 'CRU', gols: 21 },
        { jogador: 'Arrascaeta', time: 'Flamengo', sigla: 'FLA', gols: 18 }
    ];

    const vc = new VirtualConsole();

    const html = `<!DOCTYPE html><html><body>${canvasHtml}</body></html>`;
    const dom = new JSDOM(html, {
        runScripts: 'dangerously',
        pretendToBeVisual: true,
        virtualConsole: vc
    });

    if (comCanvas) {
        dom.window.document.querySelectorAll('canvas').forEach((canvas) => {
            canvas.getContext = () => ({});
        });
    }

    if (comDados) {
        dom.window.eval(`var dadosClassificacao = ${JSON.stringify(classificacao)};`);
        dom.window.eval(`var dadosArtilharia = ${JSON.stringify(artilharia)};`);
    }

    if (comChart) {
        dom.window.eval(`
            var Chart = function(ctx, config) {
                Chart._instances = Chart._instances || [];
                const instance = {
                    ctx,
                    config,
                    data: config.data,
                    options: config.options,
                    update: function() {},
                    destroy: function() {}
                };
                Chart._instances.push(instance);
                return instance;
            };
            Chart.defaults = { color: '', borderColor: '', font: { family: '', weight: 0 } };
        `);
    }

    dom.window.eval(chartsJs);
    return dom;
}

describe('Inicializacao de graficos sob demanda', () => {
    test('nao cria graficos automaticamente ao carregar o script', () => {
        const dom = criarDOM();
        expect(dom.window.Chart._instances || []).toHaveLength(0);
        expect(dom.window.dashboardCharts.isInitialized()).toBe(false);
        dom.window.close();
    });

    test('cria 4 graficos quando init e chamado', () => {
        const dom = criarDOM();
        dom.window.dashboardCharts.init();
        const instancias = dom.window.Chart._instances || [];
        expect(instancias).toHaveLength(4);
        expect(dom.window.dashboardCharts.isInitialized()).toBe(true);
        dom.window.close();
    });

    test('nao duplica graficos ao chamar init duas vezes', () => {
        const dom = criarDOM();
        dom.window.dashboardCharts.init();
        dom.window.dashboardCharts.init();
        const instancias = dom.window.Chart._instances || [];
        expect(instancias).toHaveLength(4);
        dom.window.close();
    });

    test('nao quebra sem Chart definido', () => {
        expect(() => {
            const dom = criarDOM({ comChart: false });
            dom.window.dashboardCharts.init();
            dom.window.close();
        }).not.toThrow();
    });

    test('nao quebra sem dados globais', () => {
        expect(() => {
            const dom = criarDOM({ comDados: false });
            dom.window.dashboardCharts.init();
            dom.window.close();
        }).not.toThrow();
    });

    test('nao quebra sem canvas no DOM', () => {
        expect(() => {
            const dom = criarDOM({ comCanvas: false });
            dom.window.dashboardCharts.init();
            dom.window.close();
        }).not.toThrow();
    });

    test('tipo do grafico de pontos e bar horizontal', () => {
        const dom = criarDOM();
        dom.window.dashboardCharts.init();
        const instancias = dom.window.Chart._instances;
        const pontosChart = instancias[0];
        expect(pontosChart.config.type).toBe('bar');
        expect(pontosChart.config.options.indexAxis).toBe('y');
        dom.window.close();
    });
});
