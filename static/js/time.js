document.addEventListener('DOMContentLoaded', () => {
    if (typeof Chart === 'undefined' || typeof timeData === 'undefined') return;

    const el = document.getElementById('chartRadarTime');
    if (!el) return;

    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = "'Outfit', sans-serif";

    const maxPts = Math.max(...todosClassificacao.map(t => t.pontos));
    const maxGP = Math.max(...todosClassificacao.map(t => t.gols_pro));
    const normalize = (v, max) => Math.round((v / max) * 100);

    const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
    const gridColor = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
    const labelColor = isDark ? '#94a3b8' : '#475569';

    const chart = new Chart(el.getContext('2d'), {
        type: 'radar',
        data: {
            labels: ['Pontos', 'Vitórias', 'Gols Pro', 'Aproveit.', 'Saldo+50'],
            datasets: [{
                label: timeData.time,
                data: [
                    normalize(timeData.pontos, maxPts),
                    normalize(timeData.vitorias, 38),
                    normalize(timeData.gols_pro, maxGP),
                    timeData.aproveitamento,
                    Math.max(0, timeData.saldo + 50)
                ],
                borderColor: timeData.cor || '#3b82f6',
                backgroundColor: (timeData.cor || '#3b82f6') + '26',
                pointRadius: 4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    grid: { color: gridColor },
                    pointLabels: { color: labelColor },
                    ticks: { display: false }
                }
            },
            plugins: { legend: { display: false } }
        }
    });


    const observer = new MutationObserver(() => {
        const dark = document.documentElement.getAttribute('data-theme') !== 'light';
        const gc = dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
        const lc = dark ? '#94a3b8' : '#475569';
        chart.options.scales.r.grid.color = gc;
        chart.options.scales.r.pointLabels.color = lc;
        chart.update('none');
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
});
