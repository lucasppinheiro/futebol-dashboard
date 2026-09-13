document.addEventListener('DOMContentLoaded', () => {
    const root = document.documentElement;
    const tabs = document.querySelectorAll('.tab-btn');
    const sections = document.querySelectorAll('.section');
    const chartsSection = document.getElementById('graficos');
    const chartsStatus = document.getElementById('charts-status');
    const escudoFallback = window.escudoFallback;
    const safeStorage = (() => {
        try {
            return window.localStorage;
        } catch {
            return null;
        }
    })();
    const seletoresDeEscudo = [
        '.time-escudo',
        '.scorer-escudo',
        '.scorer-podium-crest',
        '.hero-escudo',
        '.cmp-picker-escudo',
        '.cmp-picker-current-escudo',
        '.cmp-summary-escudo',
        '.cmp-radar-escudo'
    ].join(', ');

    function aplicarFallbackEscudo(img) {
        if (!escudoFallback || img.dataset.fallbackAplicado === 'true') return;

        img.dataset.fallbackAplicado = 'true';
        img.src = escudoFallback;
    }

    document.addEventListener(
        'error',
        (event) => {
            const elemento = event.target;
            if (elemento instanceof HTMLImageElement && elemento.matches(seletoresDeEscudo)) {
                aplicarFallbackEscudo(elemento);
            }
        },
        true
    );

    document.querySelectorAll(seletoresDeEscudo).forEach((img) => {
        if (img.complete && img.naturalWidth === 0) aplicarFallbackEscudo(img);
    });

    function setChartsStatus(message, state = '') {
        if (!chartsStatus) return;

        chartsStatus.textContent = message || '';
        chartsStatus.hidden = !message;
        chartsStatus.classList.remove('charts-state-loading', 'charts-state-error');
        if (state) chartsStatus.classList.add(`charts-state-${state}`);
        if (chartsSection) {
            chartsSection.classList.toggle('charts-unavailable', state === 'error');
            chartsSection.classList.toggle('charts-ready', !message);
        }
    }

    function isSafeImageUrl(value) {
        if (typeof value !== 'string' || !value.trim()) return false;
        const candidate = value.trim();
        if (candidate.startsWith('//')) return false;
        if (/^data:image\/(?:png|gif|jpe?g|webp|avif);/i.test(candidate)) return true;

        try {
            const url = new URL(candidate, document.baseURI);
            return url.protocol === 'http:' || url.protocol === 'https:';
        } catch {
            return false;
        }
    }

    function appendSafeImage(container, source, className, alt = '') {
        if (!isSafeImageUrl(source)) return null;

        const image = document.createElement('img');
        image.src = source;
        image.alt = alt;
        image.className = className;
        container.appendChild(image);
        return image;
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

    function getChartsUnavailableMessage() {
        const semDados =
            typeof dadosClassificacao !== 'undefined' &&
            typeof dadosArtilharia !== 'undefined' &&
            Array.isArray(dadosClassificacao) &&
            Array.isArray(dadosArtilharia) &&
            (!dadosClassificacao.length || !dadosArtilharia.length);

        return semDados
            ? 'Ainda não há dados suficientes para exibir os gráficos. Consulte a classificação e a artilharia.'
            : 'Os gráficos interativos estão indisponíveis. Consulte os resumos textuais desta seção.';
    }

    function ensureChartsInitialized(targetId) {
        if (targetId !== 'graficos' || !chartsSection) return;

        if (window.dashboardCharts?.isInitialized()) {
            chartsSection.setAttribute('aria-busy', 'false');
            setChartsStatus('');
            return;
        }

        chartsSection.setAttribute('aria-busy', 'true');
        setChartsStatus('Carregando gráficos.', 'loading');

        if (!window.dashboardCharts || typeof window.dashboardCharts.init !== 'function') {
            chartsSection.setAttribute('aria-busy', 'false');
            setChartsStatus(getChartsUnavailableMessage(), 'error');
            return;
        }

        let ok;
        try {
            ok = window.dashboardCharts.init();
        } catch {
            ok = false;
        }
        chartsSection.setAttribute('aria-busy', 'false');
        setChartsStatus(ok ? '' : getChartsUnavailableMessage(), ok ? '' : 'error');
    }

    function ativarSecao(targetId, options = {}) {
        const { updateHash = true, alignSection = false } = options;
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

        if (alignSection) {
            const alignPageStart = () => window.scrollTo({ top: 0, behavior: 'auto' });
            alignPageStart();
            requestAnimationFrame(alignPageStart);
            setTimeout(alignPageStart, 80);
            setTimeout(alignPageStart, 240);
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
            ativarSecao(hash, { updateHash: false, alignSection: true });
        } else {
            const activeTab = document.querySelector('.tab-btn.active');
            if (activeTab) ensureChartsInitialized(activeTab.dataset.section);
        }

        window.addEventListener('hashchange', () => {
            const nextHash = window.location.hash.replace('#', '');
            if (sectionIds.has(nextHash)) {
                ativarSecao(nextHash, { updateHash: false, alignSection: true });
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
        if (!safeStorage) return [];
        try {
            const raw = safeStorage.getItem(key);
            if (!raw) return [];
            const parsed = JSON.parse(raw);
            return Array.isArray(parsed) ? parsed : [];
        } catch {
            try {
                safeStorage.removeItem(key);
            } catch {
                return [];
            }
            return [];
        }
    }

    const favoritos = readStoredArray('favoritos');

    function salvarFavoritos() {
        if (!safeStorage) return;
        try {
            safeStorage.setItem('favoritos', JSON.stringify(favoritos));
        } catch {
            // Favoritos continuam funcionando durante a sessão quando o armazenamento está indisponível.
        }
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
            filterBtns.forEach((item) => {
                item.classList.remove('active');
                item.setAttribute('aria-pressed', 'false');
            });
            btn.classList.add('active');
            btn.setAttribute('aria-pressed', 'true');
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

    root.setAttribute('data-theme', 'light');
    try {
        safeStorage?.removeItem('athletic-table-theme');
    } catch {
        // O tema claro continua ativo mesmo sem armazenamento local.
    }

    document.querySelectorAll('[data-count]').forEach((element) => {
        const target = parseInt(element.dataset.count, 10);
        if (Number.isNaN(target)) return;

        const original = element.textContent || '';
        const suffix = original.replace(/^\s*[\d.+-]+\s*/, '').trim();
        element.textContent = suffix ? `${target} ${suffix}` : `${target}`;
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
    const cmpQuickLeaders = document.getElementById('cmp-quick-leaders');

    if (cmpBtn && cmpSelect1 && cmpSelect2 && cmpResult) {
        let chartComparador = null;

        function getRadarTheme() {
            return {
                grid: getCssVar('--chart-grid', 'rgba(181, 195, 216, 0.14)'),
                label: getCssVar('--chart-label', '#c1cde0'),
                primary: getCssVar('--chart-primary', '#6ebc83'),
                secondary: getCssVar('--chart-secondary', '#65716c')
            };
        }

        function atualizarEstadoComparador() {
            const invalido = !cmpSelect1.value || !cmpSelect2.value || cmpSelect1.value === cmpSelect2.value;
            cmpBtn.disabled = invalido;
        }

        function fecharPicker(picker) {
            picker.classList.remove('open');
            const button = picker.querySelector('.cmp-picker-button');
            if (button) button.setAttribute('aria-expanded', 'false');
            const listbox = picker.querySelector('[role="listbox"]');
            if (listbox) {
                listbox.hidden = true;
                listbox.removeAttribute('aria-activedescendant');
            }
        }

        function fecharPickers(excecao = null) {
            document.querySelectorAll('.cmp-picker.open').forEach((picker) => {
                if (picker === excecao) return;
                fecharPicker(picker);
            });
        }

        function atualizarVisualPicker(select) {
            const picker = document.querySelector(`.cmp-picker[data-select="${select.id}"]`);
            if (!picker) return;

            const button = picker.querySelector('.cmp-picker-button');
            const options = Array.from(picker.querySelectorAll('.cmp-picker-option'));
            const selectedOption = options.find((option) => option.dataset.value === select.value);
            const currentId = select.id === 'cmp-time1' ? 'cmp-time1-current' : 'cmp-time2-current';

            options.forEach((option) => {
                option.setAttribute('aria-selected', String(option === selectedOption));
            });

            if (!button) return;
            button.replaceChildren();

            if (!selectedOption) {
                const placeholder = document.createElement('span');
                placeholder.id = currentId;
                placeholder.className = 'cmp-picker-placeholder';
                placeholder.textContent = select.id === 'cmp-time1' ? 'Selecione o 1º time' : 'Selecione o 2º time';
                button.appendChild(placeholder);
                return;
            }

            const escudo = selectedOption.querySelector('img');
            if (escudo) appendSafeImage(button, escudo.getAttribute('src'), 'cmp-picker-current-escudo');

            const nome = document.createElement('span');
            nome.id = currentId;
            nome.textContent = selectedOption.textContent.trim();
            button.appendChild(nome);
        }

        function selecionarPickerOption(select, option) {
            select.value = option.dataset.value || '';
            select.dispatchEvent(new Event('change', { bubbles: true }));
            fecharPickers();
        }

        document.querySelectorAll('.cmp-picker').forEach((picker) => {
            const select = document.getElementById(picker.dataset.select);
            const button = picker.querySelector('.cmp-picker-button');
            const options = Array.from(picker.querySelectorAll('.cmp-picker-option'));
            const listbox = picker.querySelector('[role="listbox"]');
            if (!select || !button || !options.length) return;

            if (listbox) {
                if (!listbox.id) listbox.id = `${select.id}-listbox`;
                button.setAttribute('aria-controls', listbox.id);
                listbox.hidden = true;
                listbox.tabIndex = -1;
            }

            options.forEach((option, index) => {
                if (!option.id) option.id = `${select.id}-option-${option.dataset.value || index}`;
                option.tabIndex = -1;
            });

            const abrirPicker = () => {
                const jaAberto = picker.classList.contains('open');
                fecharPickers(picker);
                picker.classList.toggle('open', !jaAberto);
                button.setAttribute('aria-expanded', String(!jaAberto));
                if (listbox) listbox.hidden = jaAberto;
            };

            const focarOption = (option) => {
                picker.classList.add('open');
                button.setAttribute('aria-expanded', 'true');
                if (listbox) listbox.hidden = false;
                option.focus();
            };

            button.addEventListener('click', abrirPicker);
            button.addEventListener('keydown', (event) => {
                if (event.key === 'Escape') {
                    event.preventDefault();
                    fecharPickers();
                    return;
                }
                if (!['ArrowDown', 'Enter', ' '].includes(event.key)) return;
                event.preventDefault();
                const selectedOption = options.find((option) => option.dataset.value === select.value);
                focarOption(selectedOption || options[0]);
            });

            options.forEach((option, index) => {
                option.addEventListener('click', () => {
                    selecionarPickerOption(select, option);
                    button.focus();
                });

                option.addEventListener('focus', () => {
                    if (listbox) listbox.setAttribute('aria-activedescendant', option.id);
                });

                option.addEventListener('keydown', (event) => {
                    if (event.key === 'Escape') {
                        event.preventDefault();
                        fecharPickers();
                        button.focus();
                    }

                    if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        selecionarPickerOption(select, option);
                        button.focus();
                    }

                    if (event.key === 'ArrowDown') {
                        event.preventDefault();
                        options[Math.min(index + 1, options.length - 1)].focus();
                    }

                    if (event.key === 'ArrowUp') {
                        event.preventDefault();
                        options[Math.max(index - 1, 0)].focus();
                    }

                    if (event.key === 'Home') {
                        event.preventDefault();
                        options[0].focus();
                    }

                    if (event.key === 'End') {
                        event.preventDefault();
                        options[options.length - 1].focus();
                    }
                });
            });

            picker.addEventListener('focusout', (event) => {
                if (event.relatedTarget && picker.contains(event.relatedTarget)) return;
                window.setTimeout(() => {
                    if (!picker.contains(document.activeElement)) fecharPicker(picker);
                }, 0);
            });

            select.addEventListener('change', () => atualizarVisualPicker(select));
            atualizarVisualPicker(select);
        });

        document.addEventListener('click', (event) => {
            if (event.target.closest('.cmp-picker')) return;
            fecharPickers();
        });

        cmpSelect1.addEventListener('change', atualizarEstadoComparador);
        cmpSelect2.addEventListener('change', atualizarEstadoComparador);
        atualizarEstadoComparador();

        if (cmpQuickLeaders && typeof dadosClassificacao !== 'undefined' && dadosClassificacao.length >= 2) {
            cmpQuickLeaders.addEventListener('click', () => {
                cmpSelect1.value = dadosClassificacao[0].sigla;
                cmpSelect2.value = dadosClassificacao[1].sigla;
                cmpSelect1.dispatchEvent(new Event('change', { bubbles: true }));
                cmpSelect2.dispatchEvent(new Event('change', { bubbles: true }));
                cmpBtn.click();
            });
        }

        const observer = new MutationObserver(() => {
            if (!chartComparador) return;
            const theme = getRadarTheme();
            chartComparador.options.scales.r.grid.color = theme.grid;
            chartComparador.options.scales.r.pointLabels.color = theme.label;
            chartComparador.data.datasets[0].borderColor = theme.primary;
            chartComparador.data.datasets[0].backgroundColor = hexToRgba(theme.primary, 0.16);
            chartComparador.data.datasets[1].borderColor = theme.secondary;
            chartComparador.data.datasets[1].backgroundColor = hexToRgba(theme.secondary, 0.12);
            chartComparador.update('none');
        });
        observer.observe(root, { attributes: true, attributeFilter: ['data-theme'] });

        cmpBtn.addEventListener('click', () => {
            const s1 = cmpSelect1.value;
            const s2 = cmpSelect2.value;

            if (!s1 || !s2 || s1 === s2) {
                const aviso = document.createElement('p');
                aviso.className = 'cmp-aviso';
                aviso.textContent = 'Selecione dois times diferentes.';
                cmpResult.replaceChildren(aviso);
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

            const createElement = (tag, className = '', text = '') => {
                const element = document.createElement(tag);
                if (className) element.className = className;
                if (text) element.textContent = text;
                return element;
            };

            const summary = createElement('div', 'cmp-summary');
            const createSummaryTeam = (time) => {
                const team = createElement('div', 'cmp-summary-team');
                appendSafeImage(team, time.escudo, 'cmp-summary-escudo');
                team.appendChild(createElement('strong', '', time.time));
                team.appendChild(createElement('span', '', `${time.posicao}º lugar · ${time.pontos} pontos`));
                return team;
            };

            summary.appendChild(createSummaryTeam(t1));
            summary.appendChild(createElement('div', 'cmp-summary-divider', 'vs'));
            summary.appendChild(createSummaryTeam(t2));

            const grid = createElement('div', 'cmp-grid');

            campos.forEach((campo) => {
                const v1 = t1[campo.k];
                const v2 = t2[campo.k];
                const better1 = campo.inv ? v1 < v2 : v1 > v2;
                const better2 = campo.inv ? v2 < v1 : v2 > v1;
                const suffix = campo.k === 'aproveitamento' ? '%' : '';

                grid.appendChild(createElement('div', `cmp-val ${better1 ? 'cmp-win' : ''}`, `${v1}${suffix}`));
                grid.appendChild(createElement('div', 'cmp-label', campo.label));
                grid.appendChild(createElement('div', `cmp-val ${better2 ? 'cmp-win' : ''}`, `${v2}${suffix}`));
            });

            const radarCard = createElement('div', 'cmp-radar-card');
            const radarHeader = createElement('div', 'cmp-radar-header');
            const radarIntro = createElement('div');
            radarIntro.appendChild(createElement('h3', '', 'Perfil de desempenho'));
            radarIntro.appendChild(
                createElement(
                    'p',
                    '',
                    'Escala normalizada da Série A para comparar força geral, produção ofensiva e consistência.'
                )
            );

            const radarLegend = createElement('div', 'cmp-radar-legend');
            radarLegend.setAttribute('aria-label', 'Legenda do radar');
            const createLegendItem = (time, keyClass) => {
                const item = createElement('span');
                const key = createElement('span', `cmp-radar-key ${keyClass}`);
                key.setAttribute('aria-hidden', 'true');
                item.appendChild(key);
                appendSafeImage(item, time.escudo, 'cmp-radar-escudo');
                item.appendChild(document.createTextNode(time.time || ''));
                return item;
            };
            radarLegend.appendChild(createLegendItem(t1, 'cmp-radar-key-a'));
            radarLegend.appendChild(createLegendItem(t2, 'cmp-radar-key-b'));
            radarHeader.appendChild(radarIntro);
            radarHeader.appendChild(radarLegend);

            const chartBody = createElement('div', 'chart-body chart-body-detail');
            chartBody.setAttribute('aria-busy', 'true');
            const radarCanvas = createElement('canvas');
            radarCanvas.id = 'chartRadarCmp';
            radarCanvas.setAttribute('role', 'img');
            radarCanvas.setAttribute('aria-label', 'Radar comparativo entre os clubes selecionados');
            chartBody.appendChild(radarCanvas);
            const radarStatus = createElement(
                'p',
                'charts-state charts-state-error',
                'O radar comparativo está indisponível no momento.'
            );
            radarStatus.id = 'cmp-radar-status';
            radarStatus.setAttribute('role', 'status');
            radarStatus.setAttribute('aria-live', 'polite');
            radarStatus.textContent = 'Carregando radar comparativo.';
            radarStatus.classList.remove('charts-state-error');
            radarStatus.classList.add('charts-state-loading');
            radarStatus.hidden = false;
            chartBody.appendChild(radarStatus);

            radarCard.appendChild(radarHeader);
            radarCard.appendChild(chartBody);
            cmpResult.replaceChildren(summary, grid, radarCard);

            if (typeof Chart !== 'undefined') {
                const radarEl = document.getElementById('chartRadarCmp');
                if (!radarEl) return;

                const theme = getRadarTheme();
                const pontosSerie = dadosClassificacao.map((time) => time.pontos);
                const vitoriasSerie = dadosClassificacao.map((time) => time.vitorias);
                const golsProSerie = dadosClassificacao.map((time) => time.gols_pro);
                const aproveitamentoSerie = dadosClassificacao.map((time) => time.aproveitamento);
                const saldoSerie = dadosClassificacao.map((time) => time.saldo);

                const colorA = theme.primary;
                const colorB = theme.secondary;

                try {
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
                                    borderWidth: 2,
                                    pointRadius: 2,
                                    pointHoverRadius: 4
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
                                    backgroundColor: hexToRgba(colorB, 0.12),
                                    borderWidth: 2,
                                    pointRadius: 2,
                                    pointHoverRadius: 4
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
                                    display: false
                                }
                            }
                        }
                    });
                    chartBody.setAttribute('aria-busy', 'false');
                    radarStatus.hidden = true;
                } catch {
                    chartBody.setAttribute('aria-busy', 'false');
                    chartBody.classList.add('charts-unavailable');
                    radarStatus.textContent = 'O radar comparativo está indisponível no momento.';
                    radarStatus.classList.remove('charts-state-loading');
                    radarStatus.classList.add('charts-state-error');
                    radarStatus.hidden = false;
                }
            } else {
                chartBody.setAttribute('aria-busy', 'false');
                chartBody.classList.add('charts-unavailable');
                radarStatus.textContent = 'O radar comparativo está indisponível no momento.';
                radarStatus.classList.remove('charts-state-loading');
                radarStatus.classList.add('charts-state-error');
                radarStatus.hidden = false;
            }
        });
    }

    aplicarFiltros();
});
