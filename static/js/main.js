document.addEventListener('DOMContentLoaded', () => {

    const tabs = document.querySelectorAll('.tab-btn');
    const sections = document.querySelectorAll('.section');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.dataset.section;
            const panel = document.getElementById(target);
            if (!panel) return;

            tabs.forEach(t => {
                t.classList.remove('active');
                t.setAttribute('aria-selected', 'false');
            });
            sections.forEach(s => s.classList.remove('active'));

            tab.classList.add('active');
            tab.setAttribute('aria-selected', 'true');
            panel.classList.add('active');
        });
    });

    const searchInput = document.getElementById('search-classificacao');
    const filterBtns = document.querySelectorAll('.filter-btn');
    const tabelaBody = document.querySelector('#classificacao .data-table tbody');
    let filtroZonaAtivo = 'todas';

    function aplicarFiltros() {
        if (!tabelaBody) return;
        const termo = (searchInput ? searchInput.value : '').toLowerCase().trim();
        const rows = tabelaBody.querySelectorAll('tr');

        rows.forEach(row => {
            const nome = (row.dataset.time || '').toLowerCase();
            const sigla = (row.dataset.sigla || '').toLowerCase();
            const zona = row.dataset.zona || '';

            const matchBusca = !termo || nome.includes(termo) || sigla.includes(termo);
            const matchZona = filtroZonaAtivo === 'todas' || zona === filtroZonaAtivo;

            row.style.display = (matchBusca && matchZona) ? '' : 'none';
        });
    }

    if (searchInput) {
        searchInput.addEventListener('input', aplicarFiltros);
    }

    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filtroZonaAtivo = btn.dataset.zona;
            aplicarFiltros();
        });
    });

    const sortHeaders = document.querySelectorAll('.data-table th[data-sort]');
    let sortCol = null;
    let sortAsc = true;

    sortHeaders.forEach(th => {
        th.style.cursor = 'pointer';
        th.addEventListener('click', () => {
            const col = th.dataset.sort;
            if (sortCol === col) {
                sortAsc = !sortAsc;
            } else {
                sortCol = col;
                sortAsc = col === 'time';
            }

            sortHeaders.forEach(h => {
                h.classList.remove('sort-asc', 'sort-desc');
            });
            th.classList.add(sortAsc ? 'sort-asc' : 'sort-desc');

            if (!tabelaBody) return;
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

            rows.forEach(r => tabelaBody.appendChild(r));
        });
    });

    const themeToggle = document.getElementById('theme-toggle');

    function setTheme(tema) {
        document.documentElement.setAttribute('data-theme', tema);
        localStorage.setItem('theme', tema);
        if (themeToggle) {
            themeToggle.setAttribute('aria-label', tema === 'light' ? 'Mudar para modo escuro' : 'Mudar para modo claro');
        }
    }

    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        setTheme(savedTheme);
    } else if (window.matchMedia('(prefers-color-scheme: light)').matches) {
        setTheme('light');
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const atual = document.documentElement.getAttribute('data-theme');
            setTheme(atual === 'light' ? 'dark' : 'light');
        });
    }

    document.querySelectorAll('[data-count]').forEach(el => {
        const target = parseInt(el.dataset.count, 10);
        if (isNaN(target)) return;
        const duration = 1200;
        const start = performance.now();
        const original = el.textContent;
        const suffix = original.trim().replace(/^\d+\s*/, '').trim();

        function step(now) {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = Math.round(eased * target) + (suffix ? ' ' + suffix : '');
            if (progress < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
    });

    const cmpSelect1 = document.getElementById('cmp-time1');
    const cmpSelect2 = document.getElementById('cmp-time2');
    const cmpBtn = document.getElementById('cmp-btn');
    const cmpResult = document.getElementById('cmp-result');

    if (cmpBtn && cmpSelect1 && cmpSelect2 && cmpResult) {
        let chartComparador = null;

        cmpBtn.addEventListener('click', () => {
            const s1 = cmpSelect1.value;
            const s2 = cmpSelect2.value;
            if (!s1 || !s2 || s1 === s2) {
                cmpResult.innerHTML = '<p class="cmp-aviso">Selecione dois times diferentes.</p>';
                if (chartComparador) {
                    chartComparador.destroy();
                    chartComparador = null;
                }
                return;
            }

            if (typeof dadosClassificacao === 'undefined') return;
            const t1 = dadosClassificacao.find(t => t.sigla === s1);
            const t2 = dadosClassificacao.find(t => t.sigla === s2);
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
                { label: 'Gols Pro', k: 'gols_pro' },
                { label: 'Gols Contra', k: 'gols_contra', inv: true },
                { label: 'Saldo', k: 'saldo' },
                { label: 'Aproveitamento', k: 'aproveitamento' },
            ];

            let html = `<div class="cmp-grid">
                <div class="cmp-header">${t1.time}</div>
                <div class="cmp-header cmp-label-center">vs</div>
                <div class="cmp-header">${t2.time}</div>`;

            campos.forEach(c => {
                const v1 = t1[c.k];
                const v2 = t2[c.k];
                const better1 = c.inv ? v1 < v2 : v1 > v2;
                const better2 = c.inv ? v2 < v1 : v2 > v1;
                const sfx = c.k === 'aproveitamento' ? '%' : '';
                html += `
                    <div class="cmp-val ${better1 ? 'cmp-win' : ''}">${v1}${sfx}</div>
                    <div class="cmp-label">${c.label}</div>
                    <div class="cmp-val ${better2 ? 'cmp-win' : ''}">${v2}${sfx}</div>`;
            });
            html += '</div>';

            html += '<canvas id="chartRadarCmp" style="max-height:320px;margin-top:20px"></canvas>';
            cmpResult.innerHTML = html;

            if (typeof Chart !== 'undefined') {
                const radarEl = document.getElementById('chartRadarCmp');
                if (radarEl) {
                    const normalize = (val, max) => Math.round((val / max) * 100);
                    const maxPts = Math.max(...dadosClassificacao.map(t => t.pontos));
                    const maxGP = Math.max(...dadosClassificacao.map(t => t.gols_pro));
                    const labels = ['Pontos', 'Vitórias', 'Gols Pro', 'Aproveit.', 'Saldo+50'];
                    const d1 = [normalize(t1.pontos, maxPts), normalize(t1.vitorias, 38), normalize(t1.gols_pro, maxGP), t1.aproveitamento, Math.max(0, t1.saldo + 50)];
                    const d2 = [normalize(t2.pontos, maxPts), normalize(t2.vitorias, 38), normalize(t2.gols_pro, maxGP), t2.aproveitamento, Math.max(0, t2.saldo + 50)];

                    chartComparador = new Chart(radarEl.getContext('2d'), {
                        type: 'radar',
                        data: {
                            labels,
                            datasets: [
                                { label: t1.time, data: d1, borderColor: t1.cor || '#3b82f6', backgroundColor: 'rgba(59,130,246,0.15)', pointRadius: 3 },
                                { label: t2.time, data: d2, borderColor: t2.cor || '#ef4444', backgroundColor: 'rgba(239,68,68,0.15)', pointRadius: 3 },
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: { r: { beginAtZero: true, max: 100, grid: { color: 'rgba(255,255,255,0.06)' }, pointLabels: { color: '#94a3b8' }, ticks: { display: false } } },
                            plugins: { legend: { labels: { color: '#94a3b8', font: { family: "'Outfit',sans-serif" } } } }
                        }
                    });
                }
            }
        });
    }
});
