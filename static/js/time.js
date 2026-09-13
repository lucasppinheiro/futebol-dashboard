document.addEventListener('DOMContentLoaded', () => {
    const radarSection = document.getElementById('time-radar-section');
    const status = document.getElementById('time-radar-status');
    const el = document.getElementById('chartRadarTime');

    const setStatus = (message, state) => {
        if (!status) return;
        const resolvedState = state || (message ? 'error' : '');
        status.textContent = message || '';
        status.hidden = !message;
        status.classList.remove('charts-state-loading', 'charts-state-error');
        if (resolvedState) status.classList.add(`charts-state-${resolvedState}`);
        radarSection.classList.toggle('charts-unavailable', Boolean(message) && resolvedState === 'error');
        radarSection.classList.toggle('charts-ready', !message);
    };

    if (!radarSection) return;
    radarSection.setAttribute('aria-busy', 'true');

    if (typeof Chart === 'undefined') {
        radarSection.setAttribute('aria-busy', 'false');
        setStatus('O radar interativo está indisponível no momento. Consulte os indicadores de desempenho da página.');
        return;
    }

    if (
        typeof timeData === 'undefined' ||
        !el ||
        typeof todosClassificacao === 'undefined' ||
        !Array.isArray(todosClassificacao) ||
        todosClassificacao.length === 0
    ) {
        radarSection.setAttribute('aria-busy', 'false');
        setStatus('Não foi possível carregar os dados do radar. Consulte os indicadores de desempenho da página.');
        return;
    }

    function getCssVar(name, fallback) {
        const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
        return value || fallback;
    }

    function hexToRgba(hex, alpha) {
        const normalized = (hex || '').replace('#', '');
        if (![3, 6].includes(normalized.length)) return `rgba(82, 183, 255, ${alpha})`;

        const full =
            normalized.length === 3
                ? normalized
                      .split('')
                      .map((char) => char + char)
                      .join('')
                : normalized;

        const value = parseInt(full, 16);
        const r = (value >> 16) & 255;
        const g = (value >> 8) & 255;
        const b = value & 255;
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    function getTheme() {
        return {
            grid: getCssVar('--chart-grid', 'rgba(181, 195, 216, 0.14)'),
            label: getCssVar('--chart-label', '#c1cde0'),
            brandAlt: getCssVar('--brand-alt', '#52b7ff')
        };
    }

    function normalizarRadar(valor, valores) {
        const numeros = valores.map((item) => Number(item) || 0);
        const minimo = Math.min(...numeros);
        const maximo = Math.max(...numeros);
        if (maximo === minimo) return 100;
        const proporcao = ((Number(valor) || 0) - minimo) / (maximo - minimo);
        return Math.round(Math.max(0, Math.min(1, proporcao)) * 100);
    }

    const pontosSerie = todosClassificacao.map((time) => time.pontos);
    const vitoriasSerie = todosClassificacao.map((time) => time.vitorias);
    const golsProSerie = todosClassificacao.map((time) => time.gols_pro);
    const aproveitamentoSerie = todosClassificacao.map((time) => time.aproveitamento);
    const saldoSerie = todosClassificacao.map((time) => time.saldo);

    const accent = timeData.cor || getCssVar('--brand-alt', '#52b7ff');
    const theme = getTheme();

    Chart.defaults.color = theme.label;
    Chart.defaults.font.family = "'Outfit', sans-serif";

    let chart;
    try {
        chart = new Chart(el.getContext('2d'), {
            type: 'radar',
            data: {
                labels: ['Pontos', 'Vitórias', 'Gols pró', 'Aproveitamento', 'Saldo'],
                datasets: [
                    {
                        label: timeData.time,
                        data: [
                            normalizarRadar(timeData.pontos, pontosSerie),
                            normalizarRadar(timeData.vitorias, vitoriasSerie),
                            normalizarRadar(timeData.gols_pro, golsProSerie),
                            normalizarRadar(timeData.aproveitamento, aproveitamentoSerie),
                            normalizarRadar(timeData.saldo, saldoSerie)
                        ],
                        borderColor: accent,
                        backgroundColor: hexToRgba(accent, 0.18),
                        pointRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: theme.grid },
                        pointLabels: { color: theme.label },
                        ticks: { display: false }
                    }
                },
                plugins: { legend: { display: false } }
            }
        });
    } catch {
        radarSection.setAttribute('aria-busy', 'false');
        setStatus('O radar interativo está indisponível no momento. Consulte os indicadores de desempenho da página.');
        return;
    }

    radarSection.setAttribute('aria-busy', 'false');
    setStatus('');

    const observer = new MutationObserver(() => {
        const nextTheme = getTheme();
        chart.options.scales.r.grid.color = nextTheme.grid;
        chart.options.scales.r.pointLabels.color = nextTheme.label;
        chart.update('none');
    });

    observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-theme']
    });
});
