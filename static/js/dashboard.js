(function () {
    'use strict';

    const STATUS_LABELS = {
        agendada: 'Agendado',
        em_andamento: 'Em andamento',
        intervalo: 'Intervalo',
        encerrada: 'Encerrado',
        adiada: 'Adiado',
        suspensa: 'Suspenso',
        cancelada: 'Cancelado'
    };

    function safeStorage() {
        try {
            return window.localStorage;
        } catch {
            return null;
        }
    }

    function normalizarRodada(value, fallback, total) {
        const parsed = Number.parseInt(value, 10);
        return Number.isInteger(parsed) && parsed >= 1 && parsed <= total ? parsed : fallback;
    }

    function siteUrl(path = '') {
        const base = window.siteBasePath || '/';
        return `${base.endsWith('/') ? base : `${base}/`}${String(path).replace(/^\/+/, '')}`;
    }

    function urlEscudo(path) {
        if (!path || /^(?:https?:|data:)/.test(path)) return path || '';
        return siteUrl(path);
    }

    function criar(tag, className = '', text = '') {
        const element = document.createElement(tag);
        if (className) element.className = className;
        if (text !== '') element.textContent = text;
        return element;
    }

    function formatarHorario(value) {
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return { data: 'A confirmar', hora: '--:--' };
        return {
            data: new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: 'short', timeZone: 'America/Sao_Paulo' })
                .format(date)
                .replace('.', ''),
            hora: new Intl.DateTimeFormat('pt-BR', {
                hour: '2-digit',
                minute: '2-digit',
                hour12: false,
                timeZone: 'America/Sao_Paulo'
            }).format(date)
        };
    }

    function timesMap() {
        const times = [...(window.dadosClassificacaoAtual || []), ...(window.dadosClassificacao || [])];
        return new Map(times.map((time) => [time.sigla, time]));
    }

    function criarImagem(time, className = '') {
        if (!time?.escudo) return null;
        const image = criar('img', className);
        image.src = urlEscudo(time.escudo);
        image.alt = '';
        image.width = 32;
        image.height = 32;
        image.loading = 'lazy';
        image.decoding = 'async';
        return image;
    }

    function criarTimePartida(partida, lado, mapa) {
        const sigla = partida[lado];
        const time = mapa.get(sigla) || { sigla, time: sigla, escudo: '' };
        const link = criar('a', 'match-team');
        link.href = siteUrl(`time/${sigla}/`);
        link.appendChild(criar('span', '', time.time));
        const image = criarImagem(time);
        if (image) link.appendChild(image);
        const valor = partida.placar?.[lado] ?? '—';
        link.appendChild(criar('b', '', String(valor)));
        return link;
    }

    function criarCartaoPartida(partida, mapa = timesMap()) {
        const card = criar('article', `match-card status-${partida.status}`);
        card.dataset.matchId = String(partida.id);
        card.setAttribute('role', 'listitem');
        const horario = formatarHorario(partida.inicio_em);
        const header = criar('header');
        header.append(
            criar('span', '', `${horario.data} · ${horario.hora}`),
            criar('strong', '', STATUS_LABELS[partida.status] || 'A confirmar')
        );
        card.append(header, criarTimePartida(partida, 'mandante', mapa), criarTimePartida(partida, 'visitante', mapa));
        return card;
    }

    function atualizarQuery(changes, hash) {
        const url = new URL(window.location.href);
        Object.entries(changes).forEach(([key, value]) => {
            if (value === null || value === undefined || value === '') url.searchParams.delete(key);
            else url.searchParams.set(key, String(value));
        });
        if (hash !== undefined) url.hash = hash;
        window.history.replaceState({}, '', `${url.pathname}${url.search}${url.hash}`);
    }

    function initNavigation() {
        if (window.location.hash === '#graficos') atualizarQuery({}, '#desempenho');
        const links = Array.from(document.querySelectorAll('.edition-nav-link'));
        const sections = links.map((link) => document.querySelector(link.getAttribute('href'))).filter(Boolean);
        if (!('IntersectionObserver' in window) || !sections.length) return;
        const visibleSections = new Map();
        const activateSection = (section) => {
            links.forEach((link) => link.classList.toggle('is-active', link.getAttribute('href') === `#${section.id}`));
        };
        const requestedSection = sections.find((section) => `#${section.id}` === window.location.hash);
        if (sections.includes(requestedSection)) activateSection(requestedSection);
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) visibleSections.set(entry.target.id, entry);
                    else visibleSections.delete(entry.target.id);
                });
                const activationLine = window.innerHeight * 0.25;
                const visible = Array.from(visibleSections.values()).sort((a, b) => {
                    const distanceA = Math.abs(a.target.getBoundingClientRect().top - activationLine);
                    const distanceB = Math.abs(b.target.getBoundingClientRect().top - activationLine);
                    return distanceA - distanceB || b.intersectionRatio - a.intersectionRatio;
                })[0];
                if (!visible) return;
                activateSection(visible.target);
            },
            { rootMargin: '-25% 0px -60% 0px', threshold: [0.05, 0.25, 0.5] }
        );
        sections.forEach((section) => observer.observe(section));
    }

    function initImages() {
        document.addEventListener(
            'error',
            (event) => {
                const image = event.target;
                if (!(image instanceof HTMLImageElement) || image.dataset.fallback === 'true' || !window.escudoFallback)
                    return;
                image.dataset.fallback = 'true';
                image.src = window.escudoFallback;
            },
            true
        );
    }

    function zonaDoClube(posicao) {
        if (posicao <= 4) return 'libertadores';
        if (posicao === 5) return 'pre-libertadores';
        if (posicao <= 11) return 'sulamericana';
        if (posicao >= 17) return 'rebaixamento';
        return 'neutra';
    }

    function destaquesDaClassificacao(classificacao) {
        if (!classificacao.length) return { ataques: new Set(), defesas: new Set() };
        const golsPro = Math.max(...classificacao.map((clube) => clube.gols_pro));
        const golsContra = Math.min(...classificacao.map((clube) => clube.gols_contra));
        return {
            ataques: new Set(classificacao.filter((clube) => clube.gols_pro === golsPro).map((clube) => clube.sigla)),
            defesas: new Set(
                classificacao.filter((clube) => clube.gols_contra === golsContra).map((clube) => clube.sigla)
            )
        };
    }

    function criarLinhaClassificacao(clube, destaques = { ataques: new Set(), defesas: new Set() }) {
        const row = criar('tr');
        const values = {
            time: clube.time,
            sigla: clube.sigla,
            zona: zonaDoClube(Number(clube.posicao)),
            posicao: clube.posicao,
            pontos: clube.pontos,
            jogos: clube.jogos,
            vitorias: clube.vitorias,
            empates: clube.empates,
            derrotas: clube.derrotas,
            gols_pro: clube.gols_pro,
            gols_contra: clube.gols_contra,
            saldo: clube.saldo
        };
        Object.entries(values).forEach(([key, value]) => {
            row.dataset[key] = String(value ?? '');
        });

        const position = criar('td', 'col-pos');
        position.appendChild(criar('span', 'rank-mark', String(clube.posicao)));

        const teamCell = criar('td', 'col-team');
        const favorite = criar('button', 'favorite-toggle');
        favorite.type = 'button';
        favorite.dataset.favorite = clube.sigla;
        favorite.setAttribute('aria-label', `Favoritar ${clube.time}`);
        favorite.setAttribute('aria-pressed', 'false');
        favorite.innerHTML =
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2L3 9.6l6.2-.9Z"></path></svg>';

        const link = criar('a', 'club-cell');
        link.href = siteUrl(`time/${clube.sigla}/`);
        const image = criarImagem(clube);
        if (image) link.appendChild(image);
        const identity = criar('span');
        identity.append(criar('strong', '', clube.time), criar('small', '', `${clube.sigla} · ${clube.estado}`));
        link.appendChild(identity);

        const expand = criar('button', 'row-expand');
        expand.type = 'button';
        expand.setAttribute('aria-expanded', 'false');
        expand.setAttribute('aria-label', `Ver campanha de ${clube.time}`);
        expand.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m7 10 5 5 5-5"></path></svg>';
        const campaign = criar('div', 'mobile-campaign');
        campaign.hidden = true;
        [
            [clube.vitorias, 'Vitórias'],
            [clube.empates, 'Empates'],
            [clube.derrotas, 'Derrotas'],
            [clube.gols_pro, 'Gols pró', destaques.ataques.has(clube.sigla) ? 'Melhor ataque' : ''],
            [clube.gols_contra, 'Gols contra', destaques.defesas.has(clube.sigla) ? 'Melhor defesa' : ''],
            [`${clube.aproveitamento}%`, 'Aproveitamento']
        ].forEach(([value, label, record]) => {
            const item = criar('span');
            item.append(criar('b', '', String(value)), document.createTextNode(label));
            if (record) item.appendChild(criar('em', 'mobile-record-label', record));
            campaign.appendChild(item);
        });
        teamCell.append(favorite, link, expand, campaign);

        const points = criar('td', 'col-points');
        points.appendChild(criar('strong', '', String(clube.pontos)));
        const cell = (value, className = '') => criar('td', className, String(value ?? 0));
        const recordCell = (value, label, active) => {
            const result = criar('td', `col-secondary${active ? ' is-record' : ''}`);
            result.appendChild(criar('span', 'metric-value', String(value ?? 0)));
            if (active) result.appendChild(criar('small', 'metric-record-label', label));
            return result;
        };
        const saldo = Number(clube.saldo || 0);
        row.append(
            position,
            teamCell,
            points,
            cell(clube.jogos),
            cell(clube.vitorias, 'col-secondary'),
            cell(clube.empates, 'col-secondary'),
            cell(clube.derrotas, 'col-secondary'),
            recordCell(clube.gols_pro, 'Melhor ataque', destaques.ataques.has(clube.sigla)),
            recordCell(clube.gols_contra, 'Melhor defesa', destaques.defesas.has(clube.sigla)),
            cell(`${saldo > 0 ? '+' : ''}${saldo}`, 'col-saldo')
        );
        return row;
    }

    function initTable() {
        const tbody = document.querySelector('#tabela-classificacao tbody');
        if (!tbody) return;
        const tableWrap = document.getElementById('standings-table-wrap') || tbody.closest('.table-scroll');
        const unavailable = document.getElementById('classificacao-unavailable');
        const heading = document.getElementById('standings-heading');
        const source = document.getElementById('standings-source');
        const search = document.getElementById('search-classificacao');
        const filters = Array.from(document.querySelectorAll('.filter-btn'));
        const count = document.getElementById('classificacao-count');
        const empty = document.getElementById('classificacao-empty');
        const storage = safeStorage();
        let favorites = [];
        let clubs = window.dadosClassificacao || [];
        let zone = 'todas';
        let sortKey = null;
        let ascending = true;

        try {
            const parsed = JSON.parse(storage?.getItem('favoritos') || '[]');
            favorites = Array.isArray(parsed) ? parsed : [];
        } catch {
            try {
                storage?.removeItem('favoritos');
            } catch {
                // A tabela segue funcional sem persistência.
            }
        }

        function apply() {
            const term = (search?.value || '').trim().toLocaleLowerCase('pt-BR');
            let visible = 0;
            tbody.querySelectorAll('tr').forEach((row) => {
                const matchesText =
                    !term || `${row.dataset.time} ${row.dataset.sigla}`.toLocaleLowerCase('pt-BR').includes(term);
                const matchesZone = zone === 'todas' || zone === 'favoritos' || row.dataset.zona === zone;
                const matchesFavorite = zone !== 'favoritos' || favorites.includes(row.dataset.sigla);
                row.hidden = !(matchesText && matchesZone && matchesFavorite);
                if (!row.hidden) visible += 1;
            });
            if (count)
                count.textContent = clubs.length
                    ? `${visible} ${visible === 1 ? 'clube exibido' : 'clubes exibidos'}`
                    : 'Histórico indisponível';
            if (empty) empty.hidden = !clubs.length || visible !== 0;
        }

        function sortRows() {
            if (!sortKey) return;
            Array.from(tbody.querySelectorAll('tr'))
                .sort((a, b) => {
                    const left = a.dataset[sortKey] || '';
                    const right = b.dataset[sortKey] || '';
                    const result =
                        sortKey === 'time' ? left.localeCompare(right, 'pt-BR') : Number(left) - Number(right);
                    return ascending ? result : -result;
                })
                .forEach((row) => tbody.appendChild(row));
        }

        function bindRows() {
            tbody.querySelectorAll('.favorite-toggle').forEach((button) => {
                const sigla = button.dataset.favorite;
                const sync = () => {
                    const active = favorites.includes(sigla);
                    button.classList.toggle('is-active', active);
                    button.setAttribute('aria-pressed', String(active));
                };
                sync();
                button.addEventListener('click', () => {
                    favorites = favorites.includes(sigla)
                        ? favorites.filter((item) => item !== sigla)
                        : [...favorites, sigla];
                    try {
                        storage?.setItem('favoritos', JSON.stringify(favorites));
                    } catch {
                        // Favoritos continuam ativos nesta sessão.
                    }
                    sync();
                    apply();
                });
            });
            tbody.querySelectorAll('.row-expand').forEach((button) => {
                button.addEventListener('click', () => {
                    const details = button.parentElement?.querySelector('.mobile-campaign');
                    if (!details) return;
                    const open = details.hidden;
                    details.hidden = !open;
                    button.setAttribute('aria-expanded', String(open));
                });
            });
        }

        function updateChartAlternative(data) {
            const alternative = document.getElementById('attack-defense-data');
            if (alternative) {
                alternative.replaceChildren(
                    ...data.map((club) =>
                        criar('li', '', `${club.time}: ${club.gols_pro} gols pró e ${club.gols_contra} gols contra.`)
                    )
                );
            }
        }

        function render(data, rodada) {
            clubs = Array.isArray(data) ? data : [];
            window.dadosClassificacao = clubs;
            if (heading) heading.textContent = `Tabela após a Rodada ${rodada}`;
            if (source) {
                source.textContent = clubs.length
                    ? rodada === Number(window.dashboardConfig?.rodadaAtual)
                        ? 'CBF · classificação atual'
                        : 'football-data.org · histórico'
                    : 'Histórico ainda não sincronizado';
            }
            const available = clubs.length > 0;
            if (tableWrap) tableWrap.hidden = !available;
            if (unavailable) unavailable.hidden = available;
            if (search) search.disabled = !available;
            filters.forEach((button) => {
                button.disabled = !available;
            });
            const destaques = destaquesDaClassificacao(clubs);
            tbody.replaceChildren(...clubs.map((clube) => criarLinhaClassificacao(clube, destaques)));
            if (available) {
                updateChartAlternative(clubs);
                bindRows();
                sortRows();
            }
            apply();
        }

        search?.addEventListener('input', apply);
        filters.forEach((button) => {
            button.addEventListener('click', () => {
                zone = button.dataset.zona || 'todas';
                filters.forEach((item) => {
                    const active = item === button;
                    item.classList.toggle('is-active', active);
                    item.setAttribute('aria-pressed', String(active));
                });
                apply();
            });
        });
        document.querySelectorAll('#tabela-classificacao th[data-sort]').forEach((header) => {
            header.setAttribute('aria-sort', 'none');
            const sort = () => {
                const key = header.dataset.sort;
                ascending = sortKey === key ? !ascending : key === 'time';
                sortKey = key;
                document
                    .querySelectorAll('#tabela-classificacao th[data-sort]')
                    .forEach((item) =>
                        item.setAttribute(
                            'aria-sort',
                            item === header ? (ascending ? 'ascending' : 'descending') : 'none'
                        )
                    );
                sortRows();
                apply();
            };
            header.addEventListener('click', sort);
            header.addEventListener('keydown', (event) => {
                if (!['Enter', ' '].includes(event.key)) return;
                event.preventDefault();
                sort();
            });
        });
        window.addEventListener('brasileirao:classificacao', (event) =>
            render(event.detail.classificacao, event.detail.rodada)
        );
        bindRows();
        apply();
    }

    function initComparator() {
        const first = document.getElementById('cmp-time1');
        const second = document.getElementById('cmp-time2');
        const button = document.getElementById('cmp-btn');
        const quick = document.getElementById('cmp-quick-leaders');
        const result = document.getElementById('cmp-result');
        if (!first || !second || !button || !result) return;
        let clubs = window.dadosClassificacao || [];

        function valid() {
            const ok = Boolean(
                clubs.length &&
                first.value &&
                second.value &&
                first.value !== second.value &&
                clubs.some((club) => club.sigla === first.value) &&
                clubs.some((club) => club.sigla === second.value)
            );
            button.disabled = !ok;
            return ok;
        }

        function render(updateUrl = true) {
            if (!valid()) return;
            const left = clubs.find((club) => club.sigla === first.value);
            const right = clubs.find((club) => club.sigla === second.value);
            if (!left || !right) return;
            const summary = criar('div', 'compare-summary');
            const team = (club) => {
                const element = criar('div', 'compare-team');
                const image = criarImagem(club);
                if (image) element.appendChild(image);
                element.append(
                    criar('strong', '', club.time),
                    criar('span', '', `${club.posicao}º lugar · ${club.pontos} pontos`)
                );
                return element;
            };
            summary.append(team(left), criar('span', '', '×'), team(right));
            const metrics = criar('div', 'compare-metrics');
            [
                ['Pontos', 'pontos', false],
                ['Vitórias', 'vitorias', false],
                ['Gols pró', 'gols_pro', false],
                ['Gols contra', 'gols_contra', true],
                ['Saldo', 'saldo', false],
                ['Aproveitamento', 'aproveitamento', false]
            ].forEach(([label, key, inverse]) => {
                const row = criar('div', 'compare-metric');
                const leftWins = inverse ? left[key] < right[key] : left[key] > right[key];
                const rightWins = inverse ? right[key] < left[key] : right[key] > left[key];
                const suffix = key === 'aproveitamento' ? '%' : '';
                row.append(
                    criar('b', leftWins ? 'is-best' : '', `${left[key]}${suffix}`),
                    criar('span', '', label),
                    criar('b', rightWins ? 'is-best' : '', `${right[key]}${suffix}`)
                );
                metrics.appendChild(row);
            });
            result.replaceChildren(summary, metrics);
            if (updateUrl) atualizarQuery({ time1: left.sigla, time2: right.sigla }, '#comparador');
        }

        first.addEventListener('change', valid);
        second.addEventListener('change', valid);
        button.addEventListener('click', () => render(true));
        quick?.addEventListener('click', () => {
            if (clubs.length < 2) return;
            first.value = clubs[0].sigla;
            second.value = clubs[1].sigla;
            valid();
            render(true);
        });
        window.addEventListener('brasileirao:classificacao', (event) => {
            clubs = event.detail.classificacao || [];
            if (!clubs.length) {
                button.disabled = true;
                result.replaceChildren(
                    criar('p', '', 'O comparador ficará disponível quando o histórico desta rodada for sincronizado.')
                );
                return;
            }
            if (valid() && result.querySelector('.compare-summary')) render(false);
        });

        const params = new URL(window.location.href).searchParams;
        const queryFirst = params.get('time1');
        const querySecond = params.get('time2');
        if (
            clubs.some((club) => club.sigla === queryFirst) &&
            clubs.some((club) => club.sigla === querySecond) &&
            queryFirst !== querySecond
        ) {
            first.value = queryFirst;
            second.value = querySecond;
            render(false);
        } else valid();
    }

    function initCharts() {
        const status = document.getElementById('charts-status');
        const section = document.getElementById('desempenho');
        if (!section) return;
        let ultimaClassificacao = window.dadosClassificacao || [];
        let carregando = null;
        const update = (classificacao) => {
            ultimaClassificacao = classificacao || [];
            if (typeof window.Chart === 'undefined') return;
            try {
                const ok = window.brasileiraoCharts?.updateClassificacao(ultimaClassificacao);
                if (status) {
                    status.hidden = Boolean(ok);
                    status.textContent = ok
                        ? ''
                        : 'Os gráficos ficam disponíveis quando a classificação da rodada é sincronizada.';
                }
            } catch {
                if (status) {
                    status.hidden = false;
                    status.textContent =
                        'As visualizações interativas estão indisponíveis. Os resumos textuais permanecem acessíveis.';
                }
            }
        };

        const iniciar = () => {
            try {
                window.dadosClassificacao = ultimaClassificacao;
                const ok = window.brasileiraoCharts?.init();
                if (status) {
                    status.hidden = Boolean(ok);
                    status.textContent = ok
                        ? ''
                        : 'O mapa fica disponível quando a classificação da rodada é sincronizada.';
                }
            } catch {
                if (status) {
                    status.hidden = false;
                    status.textContent =
                        'As visualizações interativas estão indisponíveis. Os resumos textuais permanecem acessíveis.';
                }
            }
        };

        const carregar = () => {
            if (typeof window.Chart !== 'undefined') {
                iniciar();
                return;
            }
            if (carregando || !window.chartJsUrl) return;
            const script = document.createElement('script');
            script.src = window.chartJsUrl;
            script.async = true;
            carregando = script;
            script.addEventListener('load', iniciar, { once: true });
            script.addEventListener(
                'error',
                () => {
                    if (status) {
                        status.hidden = false;
                        status.textContent =
                            'As visualizações interativas estão indisponíveis. Os resumos textuais permanecem acessíveis.';
                    }
                },
                { once: true }
            );
            document.head.appendChild(script);
        };

        if ('IntersectionObserver' in window) {
            const observer = new IntersectionObserver(
                (entries) => {
                    if (!entries.some((entry) => entry.isIntersecting)) return;
                    observer.disconnect();
                    carregar();
                },
                { rootMargin: '400px 0px' }
            );
            observer.observe(section);
        } else carregar();
        window.addEventListener('brasileirao:classificacao', (event) => update(event.detail.classificacao));
    }

    function initRodadas() {
        const controller = document.querySelector('[data-round-controller]') || document.getElementById('rodada');
        const track = document.getElementById('round-track');
        if (!controller || !track) return;
        const total = Number(controller.dataset.totalRounds || window.dashboardConfig?.rodadasTotal || 38);
        const fallback = normalizarRodada(
            window.dashboardConfig?.rodadaInicial || controller.dataset.currentRound,
            Number(window.dashboardConfig?.rodadaAtual || 1),
            total
        );
        const params = new URL(window.location.href).searchParams;
        let atual = normalizarRodada(params.get('rodada'), fallback, total);
        const heading = document.getElementById('round-heading');
        const count = document.getElementById('round-count');
        const empty = document.getElementById('round-empty');
        const announcement = document.getElementById('round-announcement');
        const prev = document.getElementById('round-prev');
        const next = document.getElementById('round-next');
        const trigger = document.getElementById('round-trigger');
        const triggerLabel = document.getElementById('round-trigger-label');
        const listbox = document.getElementById('round-listbox');
        const options = Array.from(document.querySelectorAll('.round-option'));
        const progress = document.getElementById('season-progress-bar');
        const progressRoot = progress?.parentElement;

        function fecharLista() {
            if (!listbox || !trigger) return;
            listbox.hidden = true;
            trigger.setAttribute('aria-expanded', 'false');
        }

        function render(rodada, { updateUrl = false, announce = false, dispatch = true } = {}) {
            atual = normalizarRodada(rodada, atual, total);
            const partidas = (window.dadosPartidas || []).filter((partida) => Number(partida.rodada) === atual);
            const classificacao =
                window.classificacoesPorRodada?.[String(atual)] ||
                (atual === Number(window.dashboardConfig?.rodadaAtual) ? window.dadosClassificacaoAtual : null);
            const mapa = timesMap();
            track.replaceChildren(...partidas.map((partida) => criarCartaoPartida(partida, mapa)));
            if (heading) heading.textContent = `Jogos da Rodada ${atual}`;
            if (count) count.textContent = `${partidas.length} ${partidas.length === 1 ? 'confronto' : 'confrontos'}`;
            if (empty) empty.hidden = partidas.length > 0;
            if (triggerLabel) triggerLabel.textContent = `Rodada ${atual}`;
            if (prev) prev.disabled = atual <= 1;
            if (next) next.disabled = atual >= total;
            options.forEach((option) =>
                option.setAttribute('aria-selected', String(Number(option.dataset.round) === atual))
            );
            if (progress) progress.style.setProperty('--season-progress', `${(atual / total) * 100}%`);
            if (progressRoot) progressRoot.setAttribute('aria-valuenow', String(atual));
            if (updateUrl) atualizarQuery({ rodada: atual });
            if (announce && announcement) {
                announcement.textContent = `Rodada ${atual}. ${partidas.length} ${partidas.length === 1 ? 'confronto' : 'confrontos'}.`;
            }
            if (dispatch) {
                window.dispatchEvent(
                    new CustomEvent('brasileirao:rodada', {
                        detail: {
                            rodada: atual,
                            classificacao: Array.isArray(classificacao) ? classificacao : null,
                            partidas
                        }
                    })
                );
            }
        }

        trigger?.addEventListener('click', () => {
            if (!listbox) return;
            const open = listbox.hidden;
            listbox.hidden = !open;
            trigger.setAttribute('aria-expanded', String(open));
            if (open) options.find((option) => Number(option.dataset.round) === atual)?.focus();
        });
        options.forEach((option, index) => {
            option.addEventListener('click', () => {
                render(option.dataset.round, { updateUrl: true, announce: true });
                fecharLista();
                trigger?.focus();
            });
            option.addEventListener('keydown', (event) => {
                if (event.key === 'Escape') {
                    event.preventDefault();
                    fecharLista();
                    trigger?.focus();
                } else if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
                    event.preventDefault();
                    const direction = event.key === 'ArrowDown' ? 1 : -1;
                    options[(index + direction + options.length) % options.length].focus();
                } else if (event.key === 'Home' || event.key === 'End') {
                    event.preventDefault();
                    options[event.key === 'Home' ? 0 : options.length - 1].focus();
                } else if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    option.click();
                }
            });
        });
        prev?.addEventListener('click', () => render(atual - 1, { updateUrl: true, announce: true }));
        next?.addEventListener('click', () => render(atual + 1, { updateUrl: true, announce: true }));
        document.addEventListener('click', (event) => {
            if (!event.target.closest('.round-picker')) fecharLista();
        });
        render(atual, { dispatch: atual !== Number(controller.dataset.currentRound) });
    }

    function init() {
        if (document.documentElement.dataset.dashboardReady === 'true') return;
        document.documentElement.dataset.dashboardReady = 'true';
        initNavigation();
        initImages();
        initTable();
        initComparator();
        initCharts();
        initRodadas();
    }

    window.brasileiraoDashboard = { init, normalizarRodada, criarCartaoPartida, criarLinhaClassificacao };
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();
})();
