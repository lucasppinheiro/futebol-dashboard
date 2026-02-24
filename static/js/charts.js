const CORES = {
    green: '#10b981',
    greenLight: '#34d399',
    blue: '#3b82f6',
    blueLight: '#60a5fa',
    orange: '#f59e0b',
    red: '#ef4444',
    redLight: '#f87171',
    purple: '#8b5cf6',
    text: '#94a3b8',
    grid: 'rgba(255, 255, 255, 0.04)',
    bg: '#1a1f35',
};

Chart.defaults.color = CORES.text;
Chart.defaults.borderColor = CORES.grid;
Chart.defaults.font.family = "'Outfit', sans-serif";
Chart.defaults.font.weight = 500;

function criarGraficoPontos() {
    const top10 = dadosClassificacao.slice(0, 10).reverse();
    const ctx = document.getElementById('chartPontos').getContext('2d');

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: top10.map(t => t.sigla),
            datasets: [{
                label: 'Pontos',
                data: top10.map(t => t.pontos),
                backgroundColor: top10.map((_, i) => {
                    if (i >= 6) return CORES.blue;
                    if (i >= 4) return CORES.orange;
                    return CORES.green;
                }),
                borderRadius: 8,
                borderSkipped: false,
                barPercentage: 0.7,
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1e293b',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    titleFont: { weight: 700 },
                    padding: 12,
                    cornerRadius: 10,
                    callbacks: {
                        title: (items) => top10[items[0].dataIndex].time,
                        label: (item) => `${item.raw} pontos`
                    }
                }
            },
            scales: {
                x: { grid: { color: CORES.grid }, ticks: { stepSize: 10 } },
                y: { grid: { display: false } }
            }
        }
    });
}

function criarGraficoArtilheiros() {
    const top10 = dadosArtilharia.slice(0, 10);
    const ctx = document.getElementById('chartArtilheiros').getContext('2d');

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: top10.map(j => j.jogador.split(' ')[0]),
            datasets: [{
                label: 'Gols',
                data: top10.map(j => j.gols),
                backgroundColor: top10.map((_, i) => {
                    if (i === 0) return CORES.orange;
                    if (i <= 2) return 'rgba(245, 158, 11, 0.6)';
                    return CORES.green;
                }),
                borderRadius: 8,
                borderSkipped: false,
                barPercentage: 0.65,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1e293b',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 10,
                    callbacks: {
                        title: (items) => {
                            const j = top10[items[0].dataIndex];
                            return `${j.jogador} (${j.sigla})`;
                        },
                        label: (item) => `${item.raw} gols`
                    }
                }
            },
            scales: {
                x: { grid: { display: false } },
                y: { grid: { color: CORES.grid }, beginAtZero: true }
            }
        }
    });
}

function criarGraficoAproveitamento() {
    const dados = [...dadosClassificacao]
        .sort((a, b) => b.aproveitamento - a.aproveitamento)
        .slice(0, 10)
        .reverse();
    const ctx = document.getElementById('chartAproveitamento').getContext('2d');

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dados.map(t => t.sigla),
            datasets: [{
                label: 'Aproveitamento %',
                data: dados.map(t => t.aproveitamento),
                backgroundColor: dados.map(t => {
                    if (t.aproveitamento >= 60) return CORES.green;
                    if (t.aproveitamento >= 45) return CORES.orange;
                    return CORES.red;
                }),
                borderRadius: 8,
                borderSkipped: false,
                barPercentage: 0.7,
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1e293b',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 10,
                    callbacks: {
                        title: (items) => dados[items[0].dataIndex].time,
                        label: (item) => `${item.raw}% de aproveitamento`
                    }
                }
            },
            scales: {
                x: { grid: { color: CORES.grid }, max: 100, ticks: { callback: v => v + '%' } },
                y: { grid: { display: false } }
            }
        }
    });
}

function criarGraficoGolsComparativo() {
    const dados = dadosClassificacao;
    const ctx = document.getElementById('chartGolsComparativo').getContext('2d');

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dados.map(t => t.sigla),
            datasets: [
                {
                    label: 'Gols Pró',
                    data: dados.map(t => t.gols_pro),
                    backgroundColor: CORES.greenLight,
                    borderRadius: 4,
                    borderSkipped: false,
                    barPercentage: 0.7,
                },
                {
                    label: 'Gols Contra',
                    data: dados.map(t => t.gols_contra),
                    backgroundColor: CORES.redLight,
                    borderRadius: 4,
                    borderSkipped: false,
                    barPercentage: 0.7,
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
                        padding: 20,
                        font: { size: 12, weight: 600 }
                    }
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 10,
                    callbacks: {
                        title: (items) => dados[items[0].dataIndex].time
                    }
                }
            },
            scales: {
                x: { grid: { display: false }, ticks: { font: { size: 10 } } },
                y: { grid: { color: CORES.grid }, beginAtZero: true }
            }
        }
    });
}

function inicializarGraficos() {
    if (typeof dadosClassificacao === 'undefined' || typeof dadosArtilharia === 'undefined') return;
    if (!Array.isArray(dadosClassificacao) || !Array.isArray(dadosArtilharia)) return;
    if (!document.getElementById('chartPontos')) return;

    criarGraficoPontos();
    criarGraficoArtilheiros();
    criarGraficoAproveitamento();
    criarGraficoGolsComparativo();
}

document.addEventListener('DOMContentLoaded', inicializarGraficos);
