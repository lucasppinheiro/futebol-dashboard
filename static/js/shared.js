(function () {
    const root = document.documentElement;
    const safeStorage = (() => {
        try {
            return window.localStorage;
        } catch {
            return null;
        }
    })();

    function getMediaQueryMatch(query) {
        if (typeof window.matchMedia !== 'function') return false;
        return window.matchMedia(query).matches;
    }

    function getCssVar(name, fallback) {
        const value = getComputedStyle(root).getPropertyValue(name).trim();
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

        const intValue = parseInt(full, 16);
        const r = (intValue >> 16) & 255;
        const g = (intValue >> 8) & 255;
        const b = intValue & 255;
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    function normalizarRadar(valor, valores, options = {}) {
        const { invert = false } = options;
        const numeros = valores.map((item) => Number(item) || 0);
        const minimo = Math.min(...numeros);
        const maximo = Math.max(...numeros);
        if (maximo === minimo) return 100;

        let proporcao = ((Number(valor) || 0) - minimo) / (maximo - minimo);
        if (invert) proporcao = 1 - proporcao;
        return Math.round(Math.max(0, Math.min(1, proporcao)) * 100);
    }

    function getRadarTheme() {
        return {
            grid: getCssVar('--chart-grid', 'rgba(181, 195, 216, 0.14)'),
            label: getCssVar('--chart-label', '#c1cde0'),
            brandAlt: getCssVar('--brand-alt', '#52b7ff'),
            danger: getCssVar('--danger', '#ff6f61')
        };
    }

    const RADAR_LABELS = ['Pontos', 'Vitórias', 'Gols pró', 'Aproveitamento', 'Saldo'];

    function radarDataset(time, classificacao) {
        const series = {
            pontos: classificacao.map((item) => item.pontos),
            vitorias: classificacao.map((item) => item.vitorias),
            gols_pro: classificacao.map((item) => item.gols_pro),
            aproveitamento: classificacao.map((item) => item.aproveitamento),
            saldo: classificacao.map((item) => item.saldo)
        };
        return [
            normalizarRadar(time.pontos, series.pontos),
            normalizarRadar(time.vitorias, series.vitorias),
            normalizarRadar(time.gols_pro, series.gols_pro),
            normalizarRadar(time.aproveitamento, series.aproveitamento),
            normalizarRadar(time.saldo, series.saldo)
        ];
    }

    function criarRadarChart(canvas, datasets, options = {}) {
        const { legend = false } = options;
        const theme = getRadarTheme();

        return new Chart(canvas.getContext('2d'), {
            type: 'radar',
            data: { labels: RADAR_LABELS, datasets },
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
                plugins: {
                    legend: legend
                        ? {
                              labels: {
                                  color: theme.label,
                                  font: { family: "'Outfit', sans-serif", weight: 600 }
                              }
                          }
                        : { display: false }
                }
            }
        });
    }

    function observarTemaRadar(getChart) {
        const observer = new MutationObserver(() => {
            const chart = getChart();
            if (!chart) return;
            const theme = getRadarTheme();
            chart.options.scales.r.grid.color = theme.grid;
            chart.options.scales.r.pointLabels.color = theme.label;
            if (chart.options.plugins.legend && chart.options.plugins.legend.labels) {
                chart.options.plugins.legend.labels.color = theme.label;
            }
            chart.update('none');
        });
        observer.observe(root, { attributes: true, attributeFilter: ['data-theme'] });
        return observer;
    }

    function annotateResponsiveTables() {
        document.querySelectorAll('.data-table').forEach((table) => {
            const headers = Array.from(table.querySelectorAll('thead th')).map((header) => header.textContent.trim());

            table.querySelectorAll('tbody tr').forEach((row) => {
                row.querySelectorAll('td').forEach((cell, index) => {
                    if (!cell.dataset.label && headers[index]) {
                        cell.dataset.label = headers[index];
                    }
                });
            });
        });
    }

    function initPageBasics() {
        annotateResponsiveTables();

        const themeToggle = document.getElementById('theme-toggle');

        function atualizarCopiaTema(tema) {
            if (!themeToggle) return;
            const label = tema === 'light' ? 'Mudar para modo escuro' : 'Mudar para modo claro';
            themeToggle.setAttribute('aria-label', label);
            themeToggle.setAttribute('title', label);
        }

        function setTheme(tema) {
            root.setAttribute('data-theme', tema);
            try {
                safeStorage?.setItem('theme', tema);
            } catch {
                // O tema continua aplicado mesmo quando o armazenamento está indisponível.
            }
            atualizarCopiaTema(tema);
        }

        const savedTheme = (() => {
            try {
                return safeStorage?.getItem('theme') || null;
            } catch {
                return null;
            }
        })();
        if (savedTheme) {
            setTheme(savedTheme);
        } else if (getMediaQueryMatch('(prefers-color-scheme: light)')) {
            setTheme('light');
        } else {
            atualizarCopiaTema(root.getAttribute('data-theme') || 'dark');
        }

        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                const atual = root.getAttribute('data-theme');
                setTheme(atual === 'light' ? 'dark' : 'light');
            });
        }

        document.querySelectorAll('[data-count]').forEach((element) => {
            const target = parseInt(element.dataset.count, 10);
            if (Number.isNaN(target)) return;

            const original = element.textContent || '';
            const suffix = original.replace(/^\s*[\d.+-]+\s*/, '').trim();
            element.textContent = suffix ? `${target} ${suffix}` : `${target}`;
        });
    }

    document.addEventListener('DOMContentLoaded', initPageBasics);

    window.dashboardShared = {
        getMediaQueryMatch,
        getCssVar,
        hexToRgba,
        normalizarRadar,
        getRadarTheme,
        radarDataset,
        criarRadarChart,
        observarTemaRadar,
        annotateResponsiveTables,
        initPageBasics
    };
})();
