const { JSDOM, VirtualConsole } = require('jsdom');
const fs = require('fs');
const path = require('path');

const timeJs = fs.readFileSync(path.resolve(__dirname, '../../static/js/time.js'), 'utf-8');

const todosClassificacao = [
    { time: 'Flamengo', pontos: 79, vitorias: 23, gols_pro: 78, aproveitamento: 69.3, saldo: 51 },
    { time: 'Palmeiras', pontos: 76, vitorias: 22, gols_pro: 66, aproveitamento: 66.7, saldo: 33 },
    { time: 'Remo', pontos: 17, vitorias: 2, gols_pro: 28, aproveitamento: 14.9, saldo: -47 }
];

function criarDOM(opcoes = {}) {
    const {
        comCanvas = true,
        comChart = true,
        comTimeData = true,
        timeData = todosClassificacao[0],
        classificacao = todosClassificacao
    } = opcoes;

    const canvasHtml = comCanvas ? '<canvas id="chartRadarTime"></canvas>' : '';
    const dom = new JSDOM(`<!DOCTYPE html><html><body>${canvasHtml}</body></html>`, {
        runScripts: 'dangerously',
        pretendToBeVisual: true,
        virtualConsole: new VirtualConsole()
    });

    if (comCanvas) {
        dom.window.document.querySelectorAll('canvas').forEach((canvas) => {
            canvas.getContext = () => ({});
        });
    }

    if (comTimeData) {
        dom.window.eval(`var timeData = ${JSON.stringify(timeData)};`);
        dom.window.eval(`var todosClassificacao = ${JSON.stringify(classificacao)};`);
    }

    if (comChart) {
        dom.window.eval(`
            var Chart = function(ctx, config) {
                Chart._instances = Chart._instances || [];
                const instance = { ctx, config, options: config.options, update: function() {} };
                Chart._instances.push(instance);
                return instance;
            };
            Chart.defaults = { color: '', font: { family: '' } };
        `);
    }

    dom.window.eval(timeJs);
    return dom;
}

// DOMContentLoaded do jsdom dispara em macrotask; aguarda um tick para o
// listener de time.js executar antes das assercoes.
async function criarDOMPronto(opcoes = {}) {
    const dom = criarDOM(opcoes);
    await new Promise((resolve) => setTimeout(resolve, 0));
    return dom;
}

describe('Radar da pagina do time', () => {
    test('cria radar com valores normalizados (lider 100, lanterna 0)', async () => {
        const dom = await criarDOMPronto();
        const instancias = dom.window.Chart._instances || [];
        expect(instancias).toHaveLength(1);

        const dataset = instancias[0].config.data.datasets[0];
        // Flamengo lidera todas as series do fixture
        expect(dataset.data).toEqual([100, 100, 100, 100, 100]);
        dom.window.close();
    });

    test('lanterna normaliza para 0 em todas as series', async () => {
        const dom = await criarDOMPronto({ timeData: todosClassificacao[2] });
        const dataset = dom.window.Chart._instances[0].config.data.datasets[0];
        expect(dataset.data).toEqual([0, 0, 0, 0, 0]);
        dom.window.close();
    });

    test('serie com valores iguais normaliza para 100', async () => {
        const empatados = [
            { time: 'A', pontos: 10, vitorias: 3, gols_pro: 9, aproveitamento: 55.6, saldo: 1 },
            { time: 'B', pontos: 10, vitorias: 3, gols_pro: 9, aproveitamento: 55.6, saldo: 1 }
        ];
        const dom = await criarDOMPronto({ timeData: empatados[0], classificacao: empatados });
        const dataset = dom.window.Chart._instances[0].config.data.datasets[0];
        expect(dataset.data).toEqual([100, 100, 100, 100, 100]);
        dom.window.close();
    });

    test('hexToRgba converte hex de 6 digitos da cor do time', async () => {
        const dom = await criarDOMPronto({ timeData: { ...todosClassificacao[0], cor: '#006437' } });
        const dataset = dom.window.Chart._instances[0].config.data.datasets[0];
        expect(dataset.backgroundColor).toBe('rgba(0, 100, 55, 0.18)');
        expect(dataset.borderColor).toBe('#006437');
        dom.window.close();
    });

    test('hexToRgba expande hex de 3 digitos', async () => {
        const dom = await criarDOMPronto({ timeData: { ...todosClassificacao[0], cor: '#abc' } });
        const dataset = dom.window.Chart._instances[0].config.data.datasets[0];
        expect(dataset.backgroundColor).toBe('rgba(170, 187, 204, 0.18)');
        dom.window.close();
    });

    test('hex invalido usa fallback', async () => {
        const dom = await criarDOMPronto({ timeData: { ...todosClassificacao[0], cor: 'vermelho' } });
        const dataset = dom.window.Chart._instances[0].config.data.datasets[0];
        expect(dataset.backgroundColor).toBe('rgba(82, 183, 255, 0.18)');
        dom.window.close();
    });

    test('sem canvas nao instancia Chart', async () => {
        const dom = await criarDOMPronto({ comCanvas: false });
        expect(dom.window.Chart._instances || []).toHaveLength(0);
        dom.window.close();
    });

    test('sem Chart definido nao quebra', () => {
        expect(() => {
            const dom = criarDOM({ comChart: false });
            dom.window.close();
        }).not.toThrow();
    });

    test('sem timeData definido nao quebra', () => {
        expect(() => {
            const dom = criarDOM({ comTimeData: false });
            dom.window.close();
        }).not.toThrow();
    });
});
