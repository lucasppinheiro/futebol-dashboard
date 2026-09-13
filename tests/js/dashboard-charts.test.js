const { JSDOM } = require('jsdom');
const fs = require('fs');
const path = require('path');

const chartsJs = fs.readFileSync(path.resolve(__dirname, '../../static/js/dashboard-charts.js'), 'utf-8');

function criarDOM({ comPartidas = true } = {}) {
    const dom = new JSDOM(
        `<!DOCTYPE html><html><body>
            <canvas id="chart-attack-defense"></canvas>
            <canvas id="chart-home-away"></canvas>
            <canvas id="chart-recent-form"></canvas>
            <canvas id="chart-goals-round"></canvas>
        </body></html>`,
        { runScripts: 'dangerously', pretendToBeVisual: true }
    );
    dom.window.document.querySelectorAll('canvas').forEach((canvas) => {
        canvas.getContext = () => ({ canvas });
    });
    dom.window.dadosClassificacao = [
        { time: 'Flamengo', sigla: 'FLA', pontos: 54, gols_pro: 51, gols_contra: 21, cor: '#E11D1D' },
        { time: 'Palmeiras', sigla: 'PAL', pontos: 53, gols_pro: 45, gols_contra: 21, cor: '#006437' }
    ];
    dom.window.dadosGraficos = comPartidas
        ? {
              mandos: [
                  { time: 'Flamengo', sigla: 'FLA', aproveitamento_casa: 72.2, aproveitamento_fora: 61.1 },
                  { time: 'Palmeiras', sigla: 'PAL', aproveitamento_casa: 69.4, aproveitamento_fora: 58.3 }
              ],
              forma: [
                  { time: 'Flamengo', sigla: 'FLA', pontos: 13, resultados: ['V', 'V', 'E', 'V', 'V'] },
                  { time: 'Palmeiras', sigla: 'PAL', pontos: 10, resultados: ['V', 'D', 'V', 'V', 'E'] }
              ],
              gols_por_rodada: [
                  { rodada: 1, gols: 24, jogos: 10, completa: true },
                  { rodada: 2, gols: 19, jogos: 9, completa: false }
              ]
          }
        : { mandos: [], forma: [], gols_por_rodada: [] };
    dom.window.Chart = function Chart(context, config) {
        dom.window.Chart.instances.push({ ...config, canvasId: context.canvas.id });
        return { update() {}, destroy() {}, options: config.options };
    };
    dom.window.Chart.instances = [];
    dom.window.Chart.defaults = { font: {} };
    return dom;
}

test('cria quatro leituras sem repetir a tabela de artilharia', () => {
    const dom = criarDOM();

    dom.window.eval(chartsJs);
    expect(dom.window.brasileiraoCharts.init()).toBe(true);

    expect(dom.window.Chart.instances.map((config) => config.canvasId)).toEqual([
        'chart-attack-defense',
        'chart-home-away',
        'chart-recent-form',
        'chart-goals-round'
    ]);
    expect(dom.window.Chart.instances.map((config) => config.type)).toEqual(['scatter', 'bar', 'bar', 'line']);
    expect(dom.window.Chart.instances[1].data.datasets.map((dataset) => dataset.label)).toEqual(['Casa', 'Fora']);
    expect(dom.window.Chart.instances[2].data.datasets[0].data).toEqual([13, 10]);
    expect(dom.window.Chart.instances[3].data.labels).toEqual(['R1', 'R2']);
    expect(dom.window.Chart.instances.some((config) => config.canvasId === 'chart-scorers')).toBe(false);
    expect(dom.window.Chart.defaults.font.family).toBe("'Inter', sans-serif");
    expect(dom.window.Chart.instances[0].options.scales.x.ticks.font.family).toBe("'Inter', sans-serif");
    dom.window.close();
});

test('mantem ataque e defesa disponível quando a agenda ainda não foi sincronizada', () => {
    const dom = criarDOM({ comPartidas: false });

    dom.window.eval(chartsJs);
    expect(dom.window.brasileiraoCharts.init()).toBe(true);

    expect(dom.window.Chart.instances.map((config) => config.canvasId)).toEqual(['chart-attack-defense']);
    expect(dom.window.Chart.instances[0].type).toBe('scatter');
    dom.window.close();
});

test('ignora atualização de classificação vazia sem remover gráficos já renderizados', () => {
    const dom = criarDOM();

    dom.window.eval(chartsJs);
    dom.window.brasileiraoCharts.init();

    expect(dom.window.brasileiraoCharts.updateClassificacao([])).toBe(false);
    expect(dom.window.Chart.instances).toHaveLength(4);
    dom.window.close();
});
