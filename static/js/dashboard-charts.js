(function () {
    'use strict';

    const instances = [];
    let attackChart = null;
    let initialized = false;

    function css(name, fallback) {
        const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
        return value || fallback;
    }

    function theme() {
        return {
            ink: css('--chart-label', '#4f5c56'),
            grid: css('--chart-grid', 'rgba(19, 56, 46, .1)'),
            pitch: css('--pitch', '#0b684d'),
            signal: css('--signal', '#ffd044'),
            link: css('--link', '#2459b8'),
            surface: css('--chart-surface', '#ffffff')
        };
    }

    function animationDuration() {
        return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ? 0 : 220;
    }

    function tooltipOptions(colors) {
        return {
            backgroundColor: colors.surface,
            titleColor: colors.ink,
            bodyColor: colors.ink,
            borderColor: colors.grid,
            borderWidth: 1,
            padding: 12,
            displayColors: false,
            titleFont: { family: "'Inter', sans-serif", size: 13, weight: 700 },
            bodyFont: { family: "'Inter', sans-serif", size: 12 }
        };
    }

    function axis(colors, { grid = true } = {}) {
        return {
            border: { display: false },
            grid: { color: grid ? colors.grid : 'transparent' },
            ticks: { color: colors.ink, font: { family: "'Inter', sans-serif", size: 10 } }
        };
    }

    function createAttackDefense(canvas, classificacao, colors) {
        const data = classificacao.map((club) => {
            const jogos = Math.max(1, Number(club.jogos || 0));
            return {
                x: Number((Number(club.gols_pro || 0) / jogos).toFixed(2)),
                y: Number((Number(club.gols_contra || 0) / jogos).toFixed(2)),
                club: club.time,
                sigla: club.sigla,
                pontos: club.pontos,
                color: club.cor
            };
        });
        return new Chart(canvas.getContext('2d'), {
            type: 'scatter',
            data: {
                datasets: [
                    {
                        label: 'Clubes',
                        data,
                        pointRadius: (context) => 5 + Math.max(0, Number(context.raw?.pontos || 0)) / 24,
                        pointHoverRadius: 9,
                        backgroundColor: data.map((club) => club.color || colors.pitch),
                        borderColor: colors.surface,
                        borderWidth: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: animationDuration() },
                scales: {
                    x: {
                        ...axis(colors),
                        title: { display: true, text: 'Gols marcados por jogo', color: colors.ink }
                    },
                    y: {
                        ...axis(colors),
                        reverse: true,
                        title: { display: true, text: 'Gols sofridos por jogo · menos é melhor', color: colors.ink }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        ...tooltipOptions(colors),
                        callbacks: {
                            title: (items) => items[0]?.raw?.club || '',
                            label: (item) => `${item.raw.x.toFixed(2)} pró · ${item.raw.y.toFixed(2)} contra por jogo`
                        }
                    }
                }
            }
        });
    }

    function createRecentForm(canvas, forma, colors) {
        return new Chart(canvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: forma.map((item) => item.sigla),
                datasets: [
                    {
                        label: 'Pontos nos últimos cinco jogos',
                        data: forma.map((item) => item.pontos),
                        backgroundColor: forma.map((item) => (item.pontos >= 10 ? colors.pitch : colors.link)),
                        borderWidth: 0,
                        barThickness: 10
                    }
                ]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: animationDuration() },
                scales: {
                    x: { ...axis(colors), beginAtZero: true, max: 15, ticks: { ...axis(colors).ticks, stepSize: 3 } },
                    y: axis(colors, { grid: false })
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        ...tooltipOptions(colors),
                        callbacks: {
                            title: (items) => forma[items[0]?.dataIndex]?.time || '',
                            label: (item) => {
                                const club = forma[item.dataIndex];
                                return `${club.pontos} de ${club.jogos * 3} pts · ${club.resultados.join(' · ')}`;
                            }
                        }
                    }
                }
            }
        });
    }

    function createGoalsByRound(canvas, rodadas, colors) {
        return new Chart(canvas.getContext('2d'), {
            type: 'line',
            data: {
                labels: rodadas.map((item) => `R${item.rodada}`),
                datasets: [
                    {
                        label: 'Gols',
                        data: rodadas.map((item) => item.gols),
                        borderColor: colors.pitch,
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 7,
                        pointBackgroundColor: rodadas.map((item) => (item.completa ? colors.pitch : colors.signal)),
                        pointBorderColor: colors.surface,
                        pointBorderWidth: 2,
                        tension: 0.28
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: animationDuration() },
                scales: {
                    x: {
                        ...axis(colors, { grid: false }),
                        ticks: { ...axis(colors).ticks, maxRotation: 0, autoSkip: true }
                    },
                    y: { ...axis(colors), beginAtZero: true, ticks: { ...axis(colors).ticks, precision: 0 } }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        ...tooltipOptions(colors),
                        callbacks: {
                            title: (items) => `Rodada ${rodadas[items[0]?.dataIndex]?.rodada || ''}`,
                            label: (item) => {
                                const rodada = rodadas[item.dataIndex];
                                return `${rodada.gols} gols em ${rodada.jogos} jogos${rodada.completa ? '' : ' · parcial'}`;
                            }
                        }
                    }
                }
            }
        });
    }

    function updateTheme() {
        const colors = theme();
        instances.forEach((chart) => {
            if (!chart?.options?.scales) return;
            Object.values(chart.options.scales).forEach((scale) => {
                if (scale.grid && scale.grid.color !== 'transparent') scale.grid.color = colors.grid;
                if (scale.ticks) scale.ticks.color = colors.ink;
                if (scale.title) scale.title.color = colors.ink;
            });
            chart.update('none');
        });
    }

    function updateClassificacao(classificacao) {
        if (typeof Chart === 'undefined' || !Array.isArray(classificacao) || !classificacao.length) return false;
        const canvas = document.getElementById('chart-attack-defense');
        if (!canvas) return false;
        const index = instances.indexOf(attackChart);
        if (index >= 0) instances.splice(index, 1);
        attackChart?.destroy();
        attackChart = createAttackDefense(canvas, classificacao, theme());
        instances.unshift(attackChart);
        initialized = true;
        return true;
    }

    function init() {
        if (initialized) return true;
        if (typeof Chart === 'undefined') return false;
        const classificacao = window.dadosClassificacao || [];
        const graficos = window.dadosGraficos || {};
        const colors = theme();
        Chart.defaults.font.family = "'Inter', sans-serif";

        const attack = document.getElementById('chart-attack-defense');
        const recentForm = document.getElementById('chart-recent-form');
        const goalsRound = document.getElementById('chart-goals-round');
        if (attack && Array.isArray(classificacao) && classificacao.length) {
            attackChart = createAttackDefense(attack, classificacao, colors);
            instances.push(attackChart);
        }
        if (recentForm && Array.isArray(graficos.forma) && graficos.forma.length) {
            instances.push(createRecentForm(recentForm, graficos.forma, colors));
        }
        if (goalsRound && Array.isArray(graficos.gols_por_rodada) && graficos.gols_por_rodada.length) {
            instances.push(createGoalsByRound(goalsRound, graficos.gols_por_rodada, colors));
        }
        initialized = instances.length > 0;
        return initialized;
    }

    window.brasileiraoCharts = { init, updateTheme, updateClassificacao, isInitialized: () => initialized };
})();
