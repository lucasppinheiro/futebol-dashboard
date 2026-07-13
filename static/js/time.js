document.addEventListener('DOMContentLoaded', () => {
    if (typeof Chart === 'undefined' || typeof timeData === 'undefined') return;

    const el = document.getElementById('chartRadarTime');
    if (!el) return;

    const { getCssVar, hexToRgba, getRadarTheme, radarDataset, criarRadarChart, observarTemaRadar } =
        window.dashboardShared;

    const accent = timeData.cor || getCssVar('--brand-alt', '#52b7ff');
    const theme = getRadarTheme();

    Chart.defaults.color = theme.label;
    Chart.defaults.font.family = "'Outfit', sans-serif";

    const chart = criarRadarChart(el, [
        {
            label: timeData.time,
            data: radarDataset(timeData, todosClassificacao),
            borderColor: accent,
            backgroundColor: hexToRgba(accent, 0.18),
            pointRadius: 4
        }
    ]);

    observarTemaRadar(() => chart);
});
