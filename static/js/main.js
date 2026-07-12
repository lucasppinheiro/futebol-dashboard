document.addEventListener('DOMContentLoaded', () => {
    const root = document.documentElement;
    const getMediaQueryMatch = (query) => {
        if (typeof window.matchMedia !== 'function') return false;
        return window.matchMedia(query).matches;
    };
    const prefersReducedMotion = getMediaQueryMatch('(prefers-reduced-motion: reduce)');
    const tabs = document.querySelectorAll('.tab-btn');
    const sections = document.querySelectorAll('.section');
    const chartsSection = document.getElementById('graficos');
    const chartsStatus = document.getElementById('charts-status');

    function setChartsStatus(message) {
        if (chartsStatus) chartsStatus.textContent = message;
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

    function ensureChartsInitialized(targetId) {
        if (targetId !== 'graficos' || !chartsSection || !window.dashboardCharts) return;

        if (window.dashboardCharts.isInitialized()) {
            chartsSection.setAttribute('aria-busy', 'false');
            return;
        }

        chartsSection.setAttribute('aria-busy', 'true');
        setChartsStatus('Carregando gráficos.');

        const ok = window.dashboardCharts.init();
        chartsSection.setAttribute('aria-busy', 'false');
        setChartsStatus(ok ? 'Gráficos carregados.' : 'Não foi possível carregar os gráficos.');
    }

    function ativarSecao(targetId, options = {}) {
        const { updateHash = true } = options;
        const panel = document.getElementById(targetId);
        if (!panel) return;

        tabs.forEach((tab) => {
            const isActive = tab.dataset.section === targetId;
            tab.classList.toggle('active', isActive);
            tab.setAttribute('aria-selected', String(isActive));
            tab.tabIndex = isActive ? 0 : -1;
        });

        sections.forEach((section) => {
            section.classList.toggle('active', section.id === targetId);
        });

        ensureChartsInitialized(targetId);

        if (updateHash && window.location.hash !== `#${targetId}`) {
            history.replaceState(null, '', `#${targetId}`);
        }
    }

    tabs.forEach((tab, index) => {
        tab.tabIndex = tab.classList.contains('active') ? 0 : -1;

        tab.addEventListener('click', () => ativarSecao(tab.dataset.section));
        tab.addEventListener('keydown', (event) => {
            if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;

            event.preventDefault();

            let nextIndex = index;
            if (event.key === 'ArrowRight') nextIndex = (index + 1) % tabs.length;
            if (event.key === 'ArrowLeft') nextIndex = (index - 1 + tabs.length) % tabs.length;
            if (event.key === 'Home') nextIndex = 0;
            if (event.key === 'End') nextIndex = tabs.length - 1;

            const nextTab = tabs[nextIndex];
            if (!nextTab) return;

            nextTab.focus();
            ativarSecao(nextTab.dataset.section);
        });
    });

    if (tabs.length > 0) {
        const sectionIds = new Set(Array.from(sections).map((section) => section.id));
        const hash = window.location.hash.replace('#', '');
        if (hash && sectionIds.has(hash)) {
            ativarSecao(hash, { updateHash: false });
        } else {
            const activeTab = document.querySelector('.tab-btn.active');
            if (activeTab) ensureChartsInitialized(activeTab.dataset.section);
        }

        window.addEventListener('hashchange', () => {
            const nextHash = window.location.hash.replace('#', '');
            if (sectionIds.has(nextHash)) {
                ativarSecao(nextHash, { updateHash: false });
            }
        });
    }

    annotateResponsiveTables();

    const searchInput = document.getElementById('search-classificacao');
    const filterBtns = document.querySelectorAll('.filter-btn');
    const tabelaBody = document.querySelector('#tabela-classificacao tbody');
    const countLabel = document.getElementById('classificacao-count');
    const emptyState = document.getElementById('classificacao-empty');
    let filtroZonaAtivo = 'todas';

    function readStoredArray(key) {
        try {
            const raw = localStorage.getItem(key);
            if (!raw) return [];
            const parsed = JSON.parse(raw);
            return Array.isArray(parsed) ? parsed : [];
        } catch {
            localStorage.removeItem(key);
            return [];
        }
    }

    const favoritos = readStoredArray('favoritos');

    function salvarFavoritos() {
        localStorage.setItem('favoritos', JSON.stringify(favoritos));
    }

    function isFavorito(sigla) {
        return favoritos.includes(sigla);
    }

    function toggleFavorito(sigla) {
        const idx = favoritos.indexOf(sigla);
        if (idx >= 0) favoritos.splice(idx, 1);
        else favoritos.push(sigla);
        salvarFavoritos();
    }

    if (tabelaBody) {
        tabelaBody.querySelectorAll('tr').forEach((row) => {
            const sigla = row.dataset.sigla;
            const tdTime = row.querySelector('.col-time');
            if (!sigla || !tdTime) return;

            const star = document.createElement('button');
            const ativo = isFavorito(sigla);
            star.className = 'fav-btn' + (ativo ? ' active' : '');
            star.innerHTML = ativo ? '&#9733;' : '&#9734;';
            star.setAttribute('type', 'button');
            star.setAttribute('aria-label', 'Favoritar ' + (row.dataset.time || sigla));
            star.setAttribute('aria-pressed', String(ativo));

            star.addEventListener('click', (event) => {
                event.preventDefault();
                event.stopPropagation();
                toggleFavorito(sigla);

                const agoraAtivo = isFavorito(sigla);
                star.classList.toggle('active', agoraAtivo);
                star.innerHTML = agoraAtivo ? '&#9733;' : '&#9734;';
                star.setAttribute('aria-pressed', String(agoraAtivo));
                row.classList.toggle('favorito', agoraAtivo);
                aplicarFiltros();
            });

            tdTime.insertBefore(star, tdTime.firstChild);
            row.classList.toggle('favorito', ativo);
        });
    }

    function aplicarFiltros() {
        if (!tabelaBody) return;

        const termo = (searchInput ? searchInput.value : '').toLowerCase().trim();
        const rows = tabelaBody.querySelectorAll('tr');
        let visiveis = 0;

        rows.forEach((row) => {
            const nome = (row.dataset.time || '').toLowerCase();
            const sigla = (row.dataset.sigla || '').toLowerCase();
            const zona = row.dataset.zona || '';

            const matchBusca = !termo || nome.includes(termo) || sigla.includes(termo);
            const matchZona =
                filtroZonaAtivo === 'todas' || filtroZonaAtivo === 'favoritos' || zona === filtroZonaAtivo;
            const matchFav = filtroZonaAtivo !== 'favoritos' || isFavorito((row.dataset.sigla || '').toUpperCase());
            const mostrar = matchBusca && matchZona && matchFav;

            row.hidden = !mostrar;
            if (mostrar) visiveis += 1;
        });

        if (countLabel) {
            countLabel.textContent = `${visiveis} ${visiveis === 1 ? 'clube exibido' : 'clubes exibidos'}`;
        }

        if (emptyState) {
            emptyState.hidden = visiveis !== 0;
        }
    }

    if (searchInput) {
        searchInput.addEventListener('input', aplicarFiltros);
    }

    filterBtns.forEach((btn) => {
        btn.addEventListener('click', () => {
            filterBtns.forEach((item) => item.classList.remove('active'));
            btn.classList.add('active');
            filtroZonaAtivo = btn.dataset.zona;
            aplicarFiltros();
        });
    });

    const sortHeaders = document.querySelectorAll('#tabela-classificacao th[data-sort]');
    let sortCol = null;
    let sortAsc = true;

    sortHeaders.forEach((header) => header.setAttribute('aria-sort', 'none'));

    sortHeaders.forEach((th) => {
        th.tabIndex = 0;

        function ordenarColuna() {
            const col = th.dataset.sort;
            if (!tabelaBody || !col) return;

            if (sortCol === col) {
                sortAsc = !sortAsc;
            } else {
                sortCol = col;
                sortAsc = col === 'time';
            }

            sortHeaders.forEach((header) => {
                header.classList.remove('sort-asc', 'sort-desc');
                header.setAttribute('aria-sort', 'none');
            });

            th.classList.add(sortAsc ? 'sort-asc' : 'sort-desc');
            th.setAttribute('aria-sort', sortAsc ? 'ascending' : 'descending');

            const rows = Array.from(tabelaBody.querySelectorAll('tr'));
            rows.sort((a, b) => {
                let va = a.dataset[col] || '';
                let vb = b.dataset[col] || '';

                if (col !== 'time') {
                    va = parseFloat(va) || 0;
                    vb = parseFloat(vb) || 0;
                    return sortAsc ? va - vb : vb - va;
                }

                return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
            });

            rows.forEach((row) => tabelaBody.appendChild(row));
        }

        th.addEventListener('click', ordenarColuna);
        th.addEventListener('keydown', (event) => {
            if (event.key !== 'Enter' && event.key !== ' ') return;
            event.preventDefault();
            ordenarColuna();
        });
    });

    const themeToggle = document.getElementById('theme-toggle');

    function atualizarCopiaTema(tema) {
        if (!themeToggle) return;
        const label = tema === 'light' ? 'Mudar para modo escuro' : 'Mudar para modo claro';
        themeToggle.setAttribute('aria-label', label);
        themeToggle.setAttribute('title', label);
    }

    function setTheme(tema) {
        root.setAttribute('data-theme', tema);
        localStorage.setItem('theme', tema);
        atualizarCopiaTema(tema);
    }

    const savedTheme = localStorage.getItem('theme');
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

        if (prefersReducedMotion) {
            element.textContent = suffix ? `${target} ${suffix}` : `${target}`;
            return;
        }

        const duration = 900;
        const start = performance.now();

        function step(now) {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const value = Math.round(target * eased);
            element.textContent = suffix ? `${value} ${suffix}` : `${value}`;
            if (progress < 1) requestAnimationFrame(step);
        }

        requestAnimationFrame(step);
    });

    function getCssVar(name, fallback) {
        const value = getComputedStyle(root).getPropertyValue(name).trim();
        return value || fallback;
    }

    function hexToRgba(hex, alpha) {
        const normalized = hex.replace('#', '');
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

    const cmpSelect1 = document.getElementById('cmp-time1');
    const cmpSelect2 = document.getElementById('cmp-time2');
    const cmpBtn = document.getElementById('cmp-btn');
    const cmpResult = document.getElementById('cmp-result');

    if (cmpBtn && cmpSelect1 && cmpSelect2 && cmpResult) {
        let chartComparador = null;

        function getRadarTheme() {
            return {
                grid: getCssVar('--chart-grid', 'rgba(181, 195, 216, 0.14)'),
                label: getCssVar('--chart-label', '#c1cde0'),
                brandAlt: getCssVar('--brand-alt', '#52b7ff'),
                danger: getCssVar('--danger', '#ff6f61')
            };
        }

        function atualizarEstadoComparador() {
            const invalido = !cmpSelect1.value || !cmpSelect2.value || cmpSelect1.value === cmpSelect2.value;
            cmpBtn.disabled = invalido;
        }

        cmpSelect1.addEventListener('change', atualizarEstadoComparador);
        cmpSelect2.addEventListener('change', atualizarEstadoComparador);
        atualizarEstadoComparador();

        const observer = new MutationObserver(() => {
            if (!chartComparador) return;
            const theme = getRadarTheme();
            chartComparador.options.scales.r.grid.color = theme.grid;
            chartComparador.options.scales.r.pointLabels.color = theme.label;
            chartComparador.options.plugins.legend.labels.color = theme.label;
            chartComparador.update('none');
        });
        observer.observe(root, { attributes: true, attributeFilter: ['data-theme'] });

        cmpBtn.addEventListener('click', () => {
            const s1 = cmpSelect1.value;
            const s2 = cmpSelect2.value;

            if (!s1 || !s2 || s1 === s2) {
                cmpResult.innerHTML = '<p class="cmp-aviso">Selecione dois times diferentes.</p>';
                if (chartComparador) {
                    chartComparador.destroy();
                    chartComparador = null;
                }
                atualizarEstadoComparador();
                return;
            }

            if (typeof dadosClassificacao === 'undefined') return;

            const t1 = dadosClassificacao.find((time) => time.sigla === s1);
            const t2 = dadosClassificacao.find((time) => time.sigla === s2);
            if (!t1 || !t2) return;

            if (chartComparador) {
                chartComparador.destroy();
                chartComparador = null;
            }

            const campos = [
                { label: 'Posição', k: 'posicao', inv: true },
                { label: 'Pontos', k: 'pontos' },
                { label: 'Vitórias', k: 'vitorias' },
                { label: 'Empates', k: 'empates' },
                { label: 'Derrotas', k: 'derrotas', inv: true },
                { label: 'Gols pró', k: 'gols_pro' },
                { label: 'Gols contra', k: 'gols_contra', inv: true },
                { label: 'Saldo', k: 'saldo' },
                { label: 'Aproveitamento', k: 'aproveitamento' }
            ];

            let html = `
                <div class="cmp-summary">
                    <div class="cmp-summary-team">
                        <strong>${t1.time}</strong>
                        <span>${t1.posicao}º lugar · ${t1.pontos} pontos</span>
                    </div>
                    <div class="cmp-summary-divider">vs</div>
                    <div class="cmp-summary-team">
                        <strong>${t2.time}</strong>
                        <span>${t2.posicao}º lugar · ${t2.pontos} pontos</span>
                    </div>
                </div>
                <div class="cmp-grid">
                    <div class="cmp-header">${t1.time}</div>
                    <div class="cmp-header cmp-label-center">métrica</div>
                    <div class="cmp-header">${t2.time}</div>
            `;

            campos.forEach((campo) => {
                const v1 = t1[campo.k];
                const v2 = t2[campo.k];
                const better1 = campo.inv ? v1 < v2 : v1 > v2;
                const better2 = campo.inv ? v2 < v1 : v2 > v1;
                const suffix = campo.k === 'aproveitamento' ? '%' : '';

                html += `
                    <div class="cmp-val ${better1 ? 'cmp-win' : ''}">${v1}${suffix}</div>
                    <div class="cmp-label">${campo.label}</div>
                    <div class="cmp-val ${better2 ? 'cmp-win' : ''}">${v2}${suffix}</div>
                `;
            });

            html += `
                </div>
                <div class="chart-body chart-body-detail">
                    <canvas id="chartRadarCmp" aria-label="Radar comparativo entre os clubes selecionados"></canvas>
                </div>
            `;

            cmpResult.innerHTML = html;

            if (typeof Chart !== 'undefined') {
                const radarEl = document.getElementById('chartRadarCmp');
                if (!radarEl) return;

                const theme = getRadarTheme();
                const pontosSerie = dadosClassificacao.map((time) => time.pontos);
                const vitoriasSerie = dadosClassificacao.map((time) => time.vitorias);
                const golsProSerie = dadosClassificacao.map((time) => time.gols_pro);
                const aproveitamentoSerie = dadosClassificacao.map((time) => time.aproveitamento);
                const saldoSerie = dadosClassificacao.map((time) => time.saldo);

                const colorA = t1.cor || theme.brandAlt;
                const colorB = t2.cor || theme.danger;

                chartComparador = new Chart(radarEl.getContext('2d'), {
                    type: 'radar',
                    data: {
                        labels: ['Pontos', 'Vitórias', 'Gols pró', 'Aproveitamento', 'Saldo'],
                        datasets: [
                            {
                                label: t1.time,
                                data: [
                                    normalizarRadar(t1.pontos, pontosSerie),
                                    normalizarRadar(t1.vitorias, vitoriasSerie),
                                    normalizarRadar(t1.gols_pro, golsProSerie),
                                    normalizarRadar(t1.aproveitamento, aproveitamentoSerie),
                                    normalizarRadar(t1.saldo, saldoSerie)
                                ],
                                borderColor: colorA,
                                backgroundColor: hexToRgba(colorA, 0.16),
                                pointRadius: 3
                            },
                            {
                                label: t2.time,
                                data: [
                                    normalizarRadar(t2.pontos, pontosSerie),
                                    normalizarRadar(t2.vitorias, vitoriasSerie),
                                    normalizarRadar(t2.gols_pro, golsProSerie),
                                    normalizarRadar(t2.aproveitamento, aproveitamentoSerie),
                                    normalizarRadar(t2.saldo, saldoSerie)
                                ],
                                borderColor: colorB,
                                backgroundColor: hexToRgba(colorB, 0.16),
                                pointRadius: 3
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
                        plugins: {
                            legend: {
                                labels: {
                                    color: theme.label,
                                    font: { family: "'Outfit', sans-serif", weight: 600 }
                                }
                            }
                        }
                    }
                });
            }
        });
    }

    aplicarFiltros();
});
