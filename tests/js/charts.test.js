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
        { posicao: 1, time: "Flamengo", sigla: "FLA", pontos: 79, aproveitamento: 69.3, gols_pro: 78, gols_contra: 27 },
        { posicao: 2, time: "Palmeiras", sigla: "PAL", pontos: 76, aproveitamento: 66.7, gols_pro: 66, gols_contra: 33 },
        { posicao: 3, time: "Cruzeiro", sigla: "CRU", pontos: 70, aproveitamento: 61.4, gols_pro: 55, gols_contra: 31 },
    ];

    const artilharia = [
        { jogador: "Kaio Jorge", time: "Cruzeiro", sigla: "CRU", gols: 21 },
        { jogador: "Arrascaeta", time: "Flamengo", sigla: "FLA", gols: 18 },
    ];

    const vc = new VirtualConsole();

    const html = `<!DOCTYPE html><html><body>${canvasHtml}</body></html>`;
    const dom = new JSDOM(html, {
        runScripts: 'dangerously',
        pretendToBeVisual: true,
        virtualConsole: vc,
    });

    if (comCanvas) {
        dom.window.document.querySelectorAll('canvas').forEach(c => {
            c.getContext = () => ({});
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
                Chart._instances.push({ ctx, config });
            };
            Chart.defaults = { color: '', borderColor: '', font: { family: '', weight: 0 } };
        `);
    }

    dom.window.eval(chartsJs);

    // charts.js tenta auto-inicializar; como o DOM já completou o load,
    // o else-branch do readyState chama inicializarGraficos() imediatamente.
    // Se por timing não rodou, chamamos explicitamente.
    if (comChart && dom.window.Chart && (!dom.window.Chart._instances || dom.window.Chart._instances.length === 0)) {
        dom.window.eval('inicializarGraficos()');
    }

    return dom;
}

describe('Inicializacao de graficos', () => {
    test('cria 4 graficos quando tudo esta presente', () => {
        const dom = criarDOM();
        const instancias = dom.window.Chart._instances || [];
        expect(instancias).toHaveLength(4);
        dom.window.close();
    });

    test('nao quebra sem Chart definido', () => {
        expect(() => {
            const dom = criarDOM({ comChart: false });
            dom.window.close();
        }).not.toThrow();
    });

    test('nao quebra sem dados globais', () => {
        expect(() => {
            const dom = criarDOM({ comDados: false });
            dom.window.close();
        }).not.toThrow();
    });

    test('nao quebra sem canvas no DOM', () => {
        expect(() => {
            const dom = criarDOM({ comCanvas: false });
            dom.window.close();
        }).not.toThrow();
    });

    test('nao quebra com dados vazios', () => {
        const dom = criarDOM({ comDados: false, comChart: true });
        dom.window.eval('var dadosClassificacao = []; var dadosArtilharia = [];');
        expect(() => {
            dom.window.eval('inicializarGraficos()');
        }).not.toThrow();
        dom.window.close();
    });

    test('tipo do grafico de pontos e bar horizontal', () => {
        const dom = criarDOM();
        const instancias = dom.window.Chart._instances;
        const pontosChart = instancias[0];
        expect(pontosChart.config.type).toBe('bar');
        expect(pontosChart.config.options.indexAxis).toBe('y');
        dom.window.close();
    });
});
