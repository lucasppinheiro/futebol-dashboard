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

    const maxPts = Math.max(...todosClassificacao.map((time) => time.pontos));
    const maxGP = Math.max(...todosClassificacao.map((time) => time.gols_pro));
    const normalize = (value, max) => Math.round((value / max) * 100);

    const accent = timeData.cor || getCssVar('--brand-alt', '#52b7ff');
    const theme = getTheme();

    Chart.defaults.color = theme.label;
    Chart.defaults.font.family = "'Outfit', sans-serif";

    const chart = new Chart(el.getContext('2d'), {
        type: 'radar',
        data: {
            labels: ['Pontos', 'Vitórias', 'Gols pró', 'Aproveitamento', 'Saldo+50'],
            datasets: [{
                label: timeData.time,
                data: [
                    normalize(timeData.pontos, maxPts),
                    normalize(timeData.vitorias, 38),
                    normalize(timeData.gols_pro, maxGP),
                    timeData.aproveitamento,
                    Math.max(0, timeData.saldo + 50)
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
