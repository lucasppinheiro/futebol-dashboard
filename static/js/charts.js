const { getCssVar } = window.dashboardShared;

function getChartTheme() {
    return {
        brand: getCssVar('--brand', '#18c17a'),
        brandAlt: getCssVar('--brand-alt', '#52b7ff'),
        warning: getCssVar('--warning', '#ffbf5f'),
        danger: getCssVar('--danger', '#ff6f61'),
        text: getCssVar('--chart-label', '#c1cde0'),
        grid: getCssVar('--chart-grid', 'rgba(181, 195, 216, 0.14)'),
        tooltipBg: getCssVar('--chart-tooltip-bg', '#102138'),
        tooltipBorder: getCssVar('--chart-tooltip-border', 'rgba(181, 195, 216, 0.18)')
    };
}

function configureDefaults() {
    if (typeof Chart === 'undefined') return false;
    const theme = getChartTheme();
    Chart.defaults.color = theme.text;
    Chart.defaults.borderColor = theme.grid;
    Chart.defaults.font.family = "'Outfit', sans-serif";
    Chart.defaults.font.weight = 500;
    return true;
}

function tooltipBase() {
    const theme = getChartTheme();
    return {
        backgroundColor: theme.tooltipBg,
        borderColor: theme.tooltipBorder,
        borderWidth: 1,
        padding: 12,
        cornerRadius: 12,
        titleColor: theme.text,
        bodyColor: theme.text
    };
}

function formatarNomeCurto(nome) {
    const partes = String(nome || '')
        .trim()
        .split(/\s+/)
        .filter(Boolean);
    if (partes.length <= 1) return partes[0] || '';
    const ultimo = partes[partes.length - 1];
    if (partes[0].length + ultimo.length <= 14) {
        return `${partes[0]} ${ultimo}`;
    }
    return `${partes[0]} ${ultimo.charAt(0)}.`;
}

const chartsRegistry = [];
let chartsInitialized = false;
let themeObserver = null;

function criarGraficoPontos(classificacao) {
    const top10 = classificacao.slice(0, 10).reverse();
    const el = document.getElementById('chartPontos');
    if (!el) return;

    const theme = getChartTheme();
    const chart = new Chart(el.getContext('2d'), {
        type: 'bar',
        data: {
            labels: top10.map((time) => time.sigla),
            datasets: [
                {
                    label: 'Pontos',
                    data: top10.map((time) => time.pontos),
                    backgroundColor: top10.map((_, index) => {
                        if (index >= 6) return theme.brand;
                        if (index >= 4) return theme.warning;
                        return theme.brandAlt;
                    }),
                    borderRadius: 10,
                    borderSkipped: false,
                    barPercentage: 0.72
                }
            ]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    ...tooltipBase(),
                    titleFont: { weight: 700 },
                    callbacks: {
                        title: (items) => top10[items[0].dataIndex].time,
                        label: (item) => `${item.raw} pontos`
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: theme.grid },
                    ticks: { stepSize: 10 }
                },
                y: { grid: { display: false } }
            }
        }
    });

    chartsRegistry.push({
        chart,
        updateTheme: (newTheme) => {
            chart.data.datasets[0].backgroundColor = top10.map((_, index) => {
                if (index >= 6) return newTheme.brand;
                if (index >= 4) return newTheme.warning;
                return newTheme.brandAlt;
            });
            chart.options.scales.x.grid.color = newTheme.grid;
            chart.options.plugins.tooltip = {
                ...tooltipBase(),
                titleFont: { weight: 700 },
                callbacks: {
                    title: (items) => top10[items[0].dataIndex].time,
                    label: (item) => `${item.raw} pontos`
                }
            };
        }
    });
}

function criarGraficoArtilheiros(artilharia) {
    const top10 = artilharia.slice(0, 10);
    const el = document.getElementById('chartArtilheiros');
    if (!el) return;

    const theme = getChartTheme();
    const chart = new Chart(el.getContext('2d'), {
        type: 'bar',
        data: {
            labels: top10.map((jogador) => formatarNomeCurto(jogador.jogador)),
            datasets: [
                {
                    label: 'Gols',
                    data: top10.map((jogador) => jogador.gols),
                    backgroundColor: top10.map((_, index) => {
                        if (index === 0) return theme.warning;
                        if (index <= 2) return theme.brandAlt;
                        return theme.brand;
                    }),
                    borderRadius: 10,
                    borderSkipped: false,
                    barPercentage: 0.68
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    ...tooltipBase(),
                    callbacks: {
                        title: (items) => {
                            const jogador = top10[items[0].dataIndex];
                            return `${jogador.jogador} (${jogador.sigla})`;
                        },
                        label: (item) => `${item.raw} gols`
                    }
                }
            },
            scales: {
                x: { grid: { display: false } },
                y: {
                    beginAtZero: true,
                    grid: { color: theme.grid }
                }
            }
        }
    });

    chartsRegistry.push({
        chart,
        updateTheme: (newTheme) => {
            chart.data.datasets[0].backgroundColor = top10.map((_, index) => {
                if (index === 0) return newTheme.warning;
                if (index <= 2) return newTheme.brandAlt;
                return newTheme.brand;
            });
            chart.options.scales.y.grid.color = newTheme.grid;
            chart.options.plugins.tooltip = {
                ...tooltipBase(),
                callbacks: {
                    title: (items) => {
                        const jogador = top10[items[0].dataIndex];
                        return `${jogador.jogador} (${jogador.sigla})`;
                    },
                    label: (item) => `${item.raw} gols`
                }
            };
        }
    });
}

function criarGraficoAproveitamento(classificacao) {
    const dados = [...classificacao]
        .sort((a, b) => b.aproveitamento - a.aproveitamento)
        .slice(0, 10)
        .reverse();

    const el = document.getElementById('chartAproveitamento');
    if (!el) return;

    const theme = getChartTheme();
    const chart = new Chart(el.getContext('2d'), {
        type: 'bar',
        data: {
            labels: dados.map((time) => time.sigla),
            datasets: [
                {
                    label: 'Aproveitamento %',
                    data: dados.map((time) => time.aproveitamento),
                    backgroundColor: dados.map((time) => {
                        if (time.aproveitamento >= 60) return theme.brand;
                        if (time.aproveitamento >= 45) return theme.warning;
                        return theme.danger;
                    }),
                    borderRadius: 10,
                    borderSkipped: false,
                    barPercentage: 0.72
                }
            ]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    ...tooltipBase(),
                    callbacks: {
                        title: (items) => dados[items[0].dataIndex].time,
                        label: (item) => `${item.raw}% de aproveitamento`
                    }
                }
            },
            scales: {
                x: {
                    max: 100,
                    grid: { color: theme.grid },
                    ticks: { callback: (value) => `${value}%` }
                },
                y: { grid: { display: false } }
            }
        }
    });

    chartsRegistry.push({
        chart,
        updateTheme: (newTheme) => {
            chart.data.datasets[0].backgroundColor = dados.map((time) => {
                if (time.aproveitamento >= 60) return newTheme.brand;
                if (time.aproveitamento >= 45) return newTheme.warning;
                return newTheme.danger;
            });
            chart.options.scales.x.grid.color = newTheme.grid;
            chart.options.plugins.tooltip = {
                ...tooltipBase(),
                callbacks: {
                    title: (items) => dados[items[0].dataIndex].time,
                    label: (item) => `${item.raw}% de aproveitamento`
                }
            };
        }
    });
}

function criarGraficoGolsComparativo(classificacao) {
    const top8 = classificacao.slice(0, 8);
    const el = document.getElementById('chartGolsComparativo');
    if (!el) return;

    const theme = getChartTheme();
    const chart = new Chart(el.getContext('2d'), {
        type: 'bar',
        data: {
            labels: top8.map((time) => time.sigla),
            datasets: [
                {
                    label: 'Gols pró',
                    data: top8.map((time) => time.gols_pro),
                    backgroundColor: theme.brand,
                    borderRadius: 6,
                    borderSkipped: false,
                    barPercentage: 0.7
                },
                {
                    label: 'Gols contra',
                    data: top8.map((time) => time.gols_contra),
                    backgroundColor: theme.danger,
                    borderRadius: 6,
                    borderSkipped: false,
                    barPercentage: 0.7
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        pointStyle: 'rectRounded',
                        padding: 18,
                        font: { size: 12, weight: 600 }
                    }
                },
                tooltip: {
                    ...tooltipBase(),
                    callbacks: {
                        title: (items) => top8[items[0].dataIndex].time
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 10 } }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: theme.grid }
                }
            }
        }
    });

    chartsRegistry.push({
        chart,
        updateTheme: (newTheme) => {
            chart.data.datasets[0].backgroundColor = newTheme.brand;
            chart.data.datasets[1].backgroundColor = newTheme.danger;
            chart.options.scales.y.grid.color = newTheme.grid;
            chart.options.plugins.tooltip = {
                ...tooltipBase(),
                callbacks: {
                    title: (items) => top8[items[0].dataIndex].time
                }
            };
        }
    });
}

function atualizarTemaGraficos() {
    if (typeof Chart === 'undefined') return;

    const theme = getChartTheme();
    Chart.defaults.color = theme.text;
    Chart.defaults.borderColor = theme.grid;

    chartsRegistry.forEach(({ chart, updateTheme }) => {
        updateTheme(theme);
        chart.update('none');
    });
}

function inicializarGraficos() {
    if (chartsInitialized) return true;
    if (!configureDefaults()) return false;
    if (typeof dadosClassificacao === 'undefined' || typeof dadosArtilharia === 'undefined') return false;
    if (!Array.isArray(dadosClassificacao) || !Array.isArray(dadosArtilharia)) return false;

    criarGraficoPontos(dadosClassificacao);
    criarGraficoArtilheiros(dadosArtilharia);
    criarGraficoAproveitamento(dadosClassificacao);
    criarGraficoGolsComparativo(dadosClassificacao);

    if (!themeObserver) {
        themeObserver = new MutationObserver(() => atualizarTemaGraficos());
        themeObserver.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['data-theme']
        });
    }

    chartsInitialized = true;
    return true;
}

window.dashboardCharts = {
    init: inicializarGraficos,
    isInitialized: () => chartsInitialized
};
