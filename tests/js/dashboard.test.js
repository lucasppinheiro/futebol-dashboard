const { JSDOM } = require('jsdom');
const fs = require('fs');
const path = require('path');

const dashboardJs = fs.readFileSync(path.resolve(__dirname, '../../static/js/dashboard.js'), 'utf-8');

function criarDOM(url = 'http://localhost/?rodada=2', prazoVerificacao = Date.now() + 60_000) {
    const dom = new JSDOM(
        `<!DOCTYPE html><html data-theme="light"><body>
            <nav><a class="edition-nav-link" href="#classificacao">Tabela</a><a class="edition-nav-link" href="#rodada">Rodada</a><a class="edition-nav-link" href="#desempenho">Desempenho</a></nav>
            <section id="classificacao">
                <strong id="standings-heading"></strong><span id="standings-source"></span>
                <p id="classificacao-unavailable" hidden></p>
                <span class="classification-update"></span>
                <p id="verification-warning" hidden data-deadline="${prazoVerificacao}"></p>
            </section>
            <section id="rodada" data-current-round="1" data-total-rounds="3">
                <button id="round-prev"></button><button id="round-next"></button>
                <button id="round-trigger" aria-expanded="false"><span id="round-trigger-label"></span></button>
                <div id="round-listbox" role="listbox" hidden>
                    <button class="round-option" data-round="1" role="option"></button>
                    <button class="round-option" data-round="2" role="option"></button>
                    <button class="round-option" data-round="3" role="option"></button>
                </div>
                <strong id="round-heading"></strong><span id="round-count"></span><button id="round-favorites" class="filter-btn" aria-pressed="false" hidden>Meus clubes</button>
                <button id="round-current" hidden></button><div id="round-track"></div><div id="round-empty" hidden><strong></strong><p></p></div><p id="round-announcement"></p>
            </section>
            <section id="desempenho"></section>
            <label>Busca <input id="search-classificacao"></label>
            <button class="filter-btn is-active" data-zona="todas" aria-pressed="true">Todas</button>
            <button class="filter-btn" data-zona="libertadores" aria-pressed="false">G4</button>
            <button class="filter-btn" data-zona="favoritos" aria-pressed="false">Favoritos</button>
            <span id="classificacao-count"></span><p id="classificacao-empty" hidden></p>
            <table id="tabela-classificacao"><thead><tr><th data-sort="pontos" tabindex="0">P</th></tr></thead><tbody>
                <tr id="initial-row" data-time="Flamengo" data-sigla="FLA" data-zona="libertadores" data-pontos="54"><td><button class="favorite-toggle" data-favorite="FLA" aria-pressed="false"></button><button class="row-expand" aria-expanded="false"></button><div class="mobile-campaign" hidden></div></td></tr>
                <tr data-time="Palmeiras" data-sigla="PAL" data-zona="neutra" data-pontos="53"><td><button class="favorite-toggle" data-favorite="PAL" aria-pressed="false"></button></td></tr>
            </tbody></table>
            <button id="cmp-quick-leaders"></button>
            <select id="cmp-time1"><option value=""></option><option value="FLA">Flamengo</option><option value="PAL">Palmeiras</option></select>
            <select id="cmp-time2"><option value=""></option><option value="FLA">Flamengo</option><option value="PAL">Palmeiras</option></select>
            <div id="cmp-result"></div>
        </body></html>`,
        { runScripts: 'dangerously', pretendToBeVisual: true, url }
    );
    dom.window.dadosClassificacao = [
        {
            sigla: 'FLA',
            time: 'Flamengo',
            escudo: '/fla.png',
            posicao: 1,
            pontos: 54,
            vitorias: 16,
            gols_pro: 51,
            gols_contra: 21,
            saldo: 30,
            aproveitamento: 69.2
        },
        {
            sigla: 'PAL',
            time: 'Palmeiras',
            escudo: '/pal.png',
            posicao: 2,
            pontos: 53,
            vitorias: 16,
            gols_pro: 45,
            gols_contra: 21,
            saldo: 24,
            aproveitamento: 68
        }
    ];
    dom.window.dadosPartidas = [
        {
            id: 2,
            rodada: 2,
            inicio_em: '2026-05-02T20:00:00Z',
            status: 'agendada',
            mandante: 'FLA',
            visitante: 'PAL',
            placar: { mandante: null, visitante: null }
        }
    ];
    dom.window.eval(dashboardJs);
    dom.window.document.dispatchEvent(new dom.window.Event('DOMContentLoaded'));
    return dom;
}

test('mostra o aviso quando o prazo de verificação vence após o build', () => {
    const dom = criarDOM(undefined, Date.now() - 1);
    expect(dom.window.document.getElementById('verification-warning').hidden).toBe(false);
    expect(dom.window.document.querySelector('.classification-update').classList.contains('is-stale')).toBe(true);
    dom.window.close();
});

describe('Linha da Rodada', () => {
    test('abre na rodada informada pela query string', () => {
        const dom = criarDOM();
        expect(dom.window.document.getElementById('round-heading').textContent).toContain('Rodada 2');
        expect(dom.window.document.querySelectorAll('.match-card')).toHaveLength(1);
        expect(dom.window.document.getElementById('round-trigger-label').textContent).toBe('Rodada 2 de 3');
        dom.window.close();
    });

    test('query invalida retorna para a rodada atual', () => {
        const dom = criarDOM('http://localhost/?rodada=99');
        expect(dom.window.document.getElementById('round-heading').textContent).toContain('Rodada 1');
        expect(dom.window.document.getElementById('round-empty').hidden).toBe(false);
        dom.window.close();
    });

    test('botao seguinte atualiza rodada e URL', () => {
        const dom = criarDOM('http://localhost/?rodada=1');
        dom.window.document.getElementById('round-next').click();
        expect(dom.window.location.search).toContain('rodada=2');
        expect(dom.window.document.querySelectorAll('.match-card')).toHaveLength(1);
        dom.window.close();
    });

    test('rodada selecionada altera os jogos sem substituir a classificação atual', () => {
        const dom = criarDOM('http://localhost/?rodada=1');
        dom.window.document.getElementById('round-next').click();

        const primeiraLinha = dom.window.document.querySelector('#tabela-classificacao tbody tr');
        expect(primeiraLinha.id).toBe('initial-row');
        expect(primeiraLinha.dataset.sigla).toBe('FLA');
        expect(primeiraLinha.dataset.pontos).toBe('54');
        dom.window.close();
    });

    test('mantém a tabela atual mesmo quando a rodada não possui histórico', () => {
        const dom = criarDOM('http://localhost/?rodada=3');

        expect(dom.window.document.querySelectorAll('#tabela-classificacao tbody tr')).toHaveLength(2);
        expect(dom.window.document.getElementById('classificacao-unavailable').hidden).toBe(true);
        dom.window.close();
    });

    test('hash legado de graficos aponta para desempenho', () => {
        const dom = criarDOM('http://localhost/#graficos');
        expect(dom.window.location.hash).toBe('#desempenho');
        dom.window.close();
    });

    test('lista de rodadas permite navegação por teclado', () => {
        const dom = criarDOM('http://localhost/?rodada=1');
        const trigger = dom.window.document.getElementById('round-trigger');
        trigger.click();
        const options = dom.window.document.querySelectorAll('.round-option');
        options[0].focus();
        options[0].dispatchEvent(new dom.window.KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true }));
        expect(dom.window.document.activeElement).toBe(options[1]);
        options[1].dispatchEvent(new dom.window.KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
        expect(dom.window.location.search).toContain('rodada=2');
        dom.window.close();
    });
});

describe('Interações preservadas', () => {
    test('preserva a tabela renderizada no servidor na carga inicial', () => {
        const dom = criarDOM('http://localhost/?rodada=1');
        expect(dom.window.document.getElementById('initial-row')).not.toBeNull();
        dom.window.close();
    });

    test('integra melhor ataque e melhor defesa sem repetir a liderança', () => {
        const dom = criarDOM('http://localhost/?rodada=1');
        const [dadosFlamengo, dadosPalmeiras] = dom.window.dadosClassificacao;
        const classification = [
            { ...dadosPalmeiras, posicao: 1, pontos: 13, vitorias: 4, saldo: 5 },
            { ...dadosFlamengo, posicao: 2, pontos: 12, vitorias: 4, saldo: 4 }
        ];

        dom.window.dispatchEvent(
            new dom.window.CustomEvent('brasileirao:classificacao', {
                detail: { classificacao: classification, rodada: 2 }
            })
        );

        const flamengo = dom.window.document.querySelector('tr[data-sigla="FLA"]');
        const palmeiras = dom.window.document.querySelector('tr[data-sigla="PAL"]');
        expect(palmeiras.querySelector('.club-achievement')).toBeNull();
        expect(flamengo.querySelectorAll('.metric-record-label')[0].textContent).toBe('Melhor ataque');
        expect(flamengo.querySelectorAll('.metric-record-label')[1].textContent).toBe('Melhor defesa');
        expect(palmeiras.querySelector('.metric-record-label').textContent).toBe('Melhor defesa');
        dom.window.close();
    });

    test('interface permanece clara e não cria controle de tema', () => {
        const dom = criarDOM();
        expect(dom.window.document.documentElement.dataset.theme).toBe('light');
        expect(dom.window.document.getElementById('theme-toggle')).toBeNull();
        dom.window.close();
    });

    test('busca, filtros, favoritos e estado vazio continuam funcionais', () => {
        const dom = criarDOM();
        const document = dom.window.document;
        document.querySelector('[data-favorite="FLA"]').click();
        expect(dom.window.localStorage.getItem('favoritos')).toBe('["FLA"]');
        document.querySelector('[data-zona="favoritos"]').click();
        expect(document.querySelector('tr[data-sigla="FLA"]').hidden).toBe(false);
        expect(document.querySelector('tr[data-sigla="PAL"]').hidden).toBe(true);
        document.querySelector('[data-zona="todas"]').click();
        const search = document.getElementById('search-classificacao');
        search.value = 'inexistente';
        search.dispatchEvent(new dom.window.Event('input', { bubbles: true }));
        expect(document.getElementById('classificacao-empty').hidden).toBe(false);
        dom.window.close();
    });

    test('comparador recupera seleção compartilhada e mantém a query da rodada', () => {
        const dom = criarDOM('http://localhost/?rodada=2&time1=FLA&time2=PAL#comparador');
        const document = dom.window.document;
        expect(document.getElementById('cmp-time1').value).toBe('FLA');
        expect(document.getElementById('cmp-time2').value).toBe('PAL');
        expect(document.getElementById('cmp-result').textContent).toContain('Flamengo');
        const second = document.getElementById('cmp-time2');
        second.dispatchEvent(new dom.window.Event('change'));
        expect(dom.window.location.search).toContain('rodada=2');
        expect(dom.window.location.search).toContain('time1=FLA');
        expect(dom.window.location.hash).toBe('#comparador');
        dom.window.close();
    });
});

test('volta à rodada atual e preserva a comparação na URL', () => {
    const dom = criarDOM('http://localhost/?rodada=2&time1=FLA&time2=PAL');
    const current = dom.window.document.getElementById('round-current');
    expect(current.hidden).toBe(false);
    current.click();
    expect(dom.window.document.getElementById('round-heading').textContent).toContain('Rodada 1');
    expect(current.hidden).toBe(true);
    expect(dom.window.location.search).not.toContain('rodada=');
    expect(dom.window.location.search).toContain('time1=FLA');
    dom.window.close();
});

test('compara automaticamente ao selecionar dois clubes diferentes', () => {
    const dom = criarDOM('http://localhost/?rodada=2');
    const document = dom.window.document;
    document.getElementById('cmp-time1').value = 'FLA';
    const second = document.getElementById('cmp-time2');
    second.value = 'PAL';
    second.dispatchEvent(new dom.window.Event('change'));
    expect(document.getElementById('cmp-result').textContent).toContain('Flamengo');
    expect(dom.window.location.search).toContain('time2=PAL');
    expect(dom.window.location.search).toContain('rodada=2');
    dom.window.close();
});

test('abre o comparador com apenas o clube da página selecionado', () => {
    const dom = criarDOM('http://localhost/?time1=PAL#comparador');
    const document = dom.window.document;

    expect(document.getElementById('cmp-time1').value).toBe('PAL');
    expect(document.getElementById('cmp-time2').value).toBe('');
    expect(document.querySelector('.compare-summary')).toBeNull();
    dom.window.close();
});

test('Meus clubes filtra os jogos e acompanha as alterações de favoritos', () => {
    const dom = criarDOM();
    const document = dom.window.document;
    const filter = document.getElementById('round-favorites');
    const favorite = document.querySelector('[data-favorite="FLA"]');
    const empty = document.getElementById('round-empty');
    dom.window.dadosPartidas.push({
        ...dom.window.dadosPartidas[0],
        id: 3,
        mandante: 'GRE',
        visitante: 'COR'
    });

    expect(filter.hidden).toBe(false);
    filter.click();
    expect(filter.getAttribute('aria-pressed')).toBe('true');
    expect(empty.textContent).toContain('Nenhum clube favorito');
    expect(document.querySelectorAll('#round-track .match-card')).toHaveLength(0);

    favorite.click();
    expect(empty.hidden).toBe(true);
    expect(document.querySelector('[data-match-id="2"]')).not.toBeNull();
    expect(document.querySelector('[data-match-id="3"]')).toBeNull();

    filter.click();
    expect(document.querySelectorAll('#round-track .match-card')).toHaveLength(2);
    dom.window.close();
});
