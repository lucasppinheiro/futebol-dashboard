document.addEventListener('DOMContentLoaded', () => {
    if (typeof Chart === 'undefined' || typeof timeData === 'undefined') return;

    const el = document.getElementById('chartRadarTime');
    if (!el) return;

    function getCssVar(name, fallback) {
        const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
        return value || fallback;
    }

    function hexToRgba(hex, alpha) {
        const normalized = (hex || '').replace('#', '');
        if (![3, 6].includes(normalized.length)) return `rgba(82, 183, 255, ${alpha})`;

        const full = normalized.length === 3
            ? normalized.split('').map((char) => char + char).join('')
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

    const chart = new Chart(el.getContext('2d'), {
        type: 'radar',
        data: {
            labels: ['Pontos', 'Vitórias', 'Gols pró', 'Aproveitamento', 'Saldo'],
            datasets: [{
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
            }]
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
