const { JSDOM } = require('jsdom');
const fs = require('fs');
const path = require('path');

const sharedJs = fs.readFileSync(path.resolve(__dirname, '../../static/js/shared.js'), 'utf-8');

function criarShared() {
    const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
        runScripts: 'dangerously',
        pretendToBeVisual: true
    });
    dom.window.eval(sharedJs);
    return dom.window.dashboardShared;
}

describe('dashboardShared.hexToRgba', () => {
    const shared = criarShared();

    test('converte hex de 6 digitos', () => {
        expect(shared.hexToRgba('#006437', 0.5)).toBe('rgba(0, 100, 55, 0.5)');
    });

    test('expande hex de 3 digitos', () => {
        expect(shared.hexToRgba('#abc', 1)).toBe('rgba(170, 187, 204, 1)');
    });

    test('entrada invalida usa fallback', () => {
        expect(shared.hexToRgba('vermelho', 0.2)).toBe('rgba(82, 183, 255, 0.2)');
    });

    test('null e undefined usam fallback sem quebrar', () => {
        expect(shared.hexToRgba(null, 0.2)).toBe('rgba(82, 183, 255, 0.2)');
        expect(shared.hexToRgba(undefined, 0.2)).toBe('rgba(82, 183, 255, 0.2)');
    });
});

describe('dashboardShared.normalizarRadar', () => {
    const shared = criarShared();

    test('normaliza entre 0 e 100', () => {
        expect(shared.normalizarRadar(10, [0, 10])).toBe(100);
        expect(shared.normalizarRadar(0, [0, 10])).toBe(0);
        expect(shared.normalizarRadar(5, [0, 10])).toBe(50);
    });

    test('serie constante retorna 100', () => {
        expect(shared.normalizarRadar(7, [7, 7, 7])).toBe(100);
    });

    test('opcao invert espelha a escala', () => {
        expect(shared.normalizarRadar(0, [0, 10], { invert: true })).toBe(100);
        expect(shared.normalizarRadar(10, [0, 10], { invert: true })).toBe(0);
    });

    test('valores nao numericos viram 0', () => {
        expect(shared.normalizarRadar('x', [0, 10])).toBe(0);
    });
});

describe('dashboardShared.radarDataset', () => {
    const shared = criarShared();

    test('gera as 5 metricas normalizadas na ordem dos labels', () => {
        const classificacao = [
            { pontos: 79, vitorias: 23, gols_pro: 78, aproveitamento: 69.3, saldo: 51 },
            { pontos: 17, vitorias: 2, gols_pro: 28, aproveitamento: 14.9, saldo: -47 }
        ];
        expect(shared.radarDataset(classificacao[0], classificacao)).toEqual([100, 100, 100, 100, 100]);
        expect(shared.radarDataset(classificacao[1], classificacao)).toEqual([0, 0, 0, 0, 0]);
    });
});

describe('dashboardShared.getCssVar', () => {
    const shared = criarShared();

    test('retorna fallback quando variavel nao definida', () => {
        expect(shared.getCssVar('--nao-existe', '#123456')).toBe('#123456');
    });
});
