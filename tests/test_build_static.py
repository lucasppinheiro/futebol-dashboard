import json
import os
import re
import time

import build_static


def test_build_static_aplica_site_base_path(monkeypatch, tmp_path):
    dist_dir = tmp_path / "dist"
    monkeypatch.setattr(build_static, "DIST_DIR", dist_dir)

    build_static.build("/futebol-dashboard")

    index_html = (dist_dir / "index.html").read_text(encoding="utf-8")
    time_html = (dist_dir / "time" / "PAL" / "index.html").read_text(encoding="utf-8")
    not_found_html = (dist_dir / "404.html").read_text(encoding="utf-8")

    assert re.search(r'href="/futebol-dashboard/static/css/dashboard\.css\?v=[0-9a-f]+"', index_html)
    assert 'href="/futebol-dashboard/time/PAL/"' in index_html
    assert re.search(r'src="/futebol-dashboard/static/img/escudos/normalizados/CAP\.png\?v=[0-9a-f]+"', index_html)
    assert re.search(r'src="/futebol-dashboard/static/img/escudos/normalizados/PAL\.png\?v=[0-9a-f]+"', index_html)
    assert re.search(r'src="/futebol-dashboard/static/js/dashboard\.js\?v=[0-9a-f]+"', index_html)
    assert re.search(r'src="/futebol-dashboard/static/js/dashboard-charts\.js\?v=[0-9a-f]+"', index_html)
    assert 'window.siteBasePath = "/futebol-dashboard/"' in index_html
    assert "window.dadosPartidas" in index_html
    assert "window.escudoFallback" in index_html
    assert "concept-dock" not in index_html
    assert 'data-ui="brasileirao-dashboard"' in index_html
    assert 'class="site-header"' in index_html
    assert 'id="round-track"' in index_html
    assert "Dados atualizados em" in index_html
    assert "Classificação atual" in index_html
    dados = build_static.app_module.carregar_dados(permitir_refresh=False)
    assert f"rodadaAtual: {dados['info']['rodada_atual']}" in index_html
    assert f"rodadasTotal: {dados['info']['rodadas_total']}" in index_html
    assert "jogos mínimos" not in index_html
    assert "family=Inter" in index_html
    assert "family=Barlow+Condensed" not in index_html
    assert "family=IBM+Plex+Mono" not in index_html
    assert "family=Outfit" not in index_html
    assert "family=Source+Serif+4" not in index_html
    assert "family=Libre+Franklin" not in index_html
    for chart_id in ("chart-attack-defense", "chart-home-away", "chart-recent-form", "chart-goals-round"):
        assert f'id="{chart_id}"' in index_html
    assert 'id="chart-scorers"' not in index_html
    assert 'class="section-number"' not in index_html
    assert "O campeonato, rodada a rodada" not in index_html
    assert 'href="/futebol-dashboard/"' in time_html
    assert 'href="/futebol-dashboard/#classificacao"' in time_html
    assert (dist_dir / ".nojekyll").exists()
    assert "Página não encontrada" in not_found_html
    assert re.search(r'href="/futebol-dashboard/static/css/dashboard\.css\?v=[0-9a-f]+"', not_found_html)
    assert "family=Inter" in not_found_html
    assert "family=Inter" in time_html
    assert "family=Barlow+Condensed" not in not_found_html
    assert "family=IBM+Plex+Mono" not in time_html
    assert "family=Outfit" not in time_html
    assert "editorial-v2-production" not in not_found_html
    assert not (dist_dir / "prototipos").exists()
    assert not (dist_dir / "static" / "css" / "header-prototypes.css").exists()
    assert not (dist_dir / "static" / "js" / "header-prototypes.js").exists()
    assert (dist_dir / "robots.txt").exists()
    assert (dist_dir / "sitemap.xml").exists()
    assert not (dist_dir / "_redirects").exists()
    assert not (dist_dir / "static" / "css" / "style.css").exists()
    assert not (dist_dir / "static" / "css" / "matchday.css").exists()
    assert not (dist_dir / "static" / "css" / "editorial-header.css").exists()
    assert not (dist_dir / "static" / "js" / "main.js").exists()
    assert not (dist_dir / "static" / "js" / "charts.js").exists()
    assert not (dist_dir / "static" / "js" / "shared.js").exists()
    assert not (dist_dir / "static" / "js" / "time.js").exists()
    assert (dist_dir / "static" / "css" / "dashboard.css").exists()
    assert (dist_dir / "static" / "img" / "favicon.svg").exists()
    assert (dist_dir / "static" / "img" / "og-brasileirao.png").exists()
    cbf_dir = dist_dir / "static" / "img" / "escudos" / "cbf"
    cbf_assets = list(cbf_dir.glob("*.jpg"))
    assert len(cbf_assets) == 20
    assert all(asset.stat().st_size > 2_000 for asset in cbf_assets)
    assert (cbf_dir / "CAP.jpg").exists()
    normalizados_dir = dist_dir / "static" / "img" / "escudos" / "normalizados"
    escudos_normalizados = list(normalizados_dir.glob("*.png"))
    assert len(escudos_normalizados) == 20
    assert all(asset.read_bytes()[25] == 6 for asset in escudos_normalizados)  # PNG RGBA.

    health = json.loads((dist_dir / "api" / "health.json").read_text(encoding="utf-8"))
    partidas = json.loads((dist_dir / "api" / "partidas.json").read_text(encoding="utf-8"))
    classificacoes = json.loads((dist_dir / "api" / "classificacoes.json").read_text(encoding="utf-8"))
    assert partidas == dados["partidas"]
    assert classificacoes == dados["classificacao_por_rodada"]
    assert "Caderno da Rodada" not in index_html
    assert 'id="theme-toggle"' not in index_html
    assert health["dados_desatualizados"] is False
    assert health["dados_refresh_necessario"] == build_static.app_module.dados_dashboard_refresh_necessario(
        build_static.app_module.carregar_dados(permitir_refresh=False),
        fallback_mtime=build_static.Path(build_static.app_module.DATA_PATH).stat().st_mtime,
    )

    links = re.findall(r'href="/futebol-dashboard/([^"#?]*)"', index_html)
    for link in links:
        if not link:
            continue
        destino = dist_dir / link
        assert destino.exists() or (destino / "index.html").exists(), link


def test_build_static_usa_raiz_para_vercel(monkeypatch, tmp_path):
    dist_dir = tmp_path / "dist"
    monkeypatch.setattr(build_static, "DIST_DIR", dist_dir)
    monkeypatch.delenv("SITE_BASE_PATH", raising=False)
    monkeypatch.setenv("SITE_ORIGIN", "https://dashboard.example")

    build_static.build()

    index_html = (dist_dir / "index.html").read_text(encoding="utf-8")
    sitemap = (dist_dir / "sitemap.xml").read_text(encoding="utf-8")
    assert re.search(r'href="/static/css/dashboard\.css\?v=[0-9a-f]+"', index_html)
    assert 'href="/time/PAL/"' in index_html
    assert "https://dashboard.example/time/PAL/" in sitemap


def test_build_static_nao_tenta_refresh_com_snapshot_vencido(monkeypatch, tmp_path):
    data_path = tmp_path / "brasileirao.json"
    data_path.write_text(
        build_static.Path(build_static.app_module.DATA_PATH).read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    instante_vencido = time.time() - 7200
    os.utime(data_path, (instante_vencido, instante_vencido))

    dist_dir = tmp_path / "dist"
    monkeypatch.setattr(build_static, "DIST_DIR", dist_dir)
    monkeypatch.setattr(build_static.app_module, "DATA_PATH", str(data_path))
    monkeypatch.setenv("DATA_AUTO_REFRESH_HOURS", "1")
    monkeypatch.setattr(build_static.app_module, "_ultimo_refresh_automatico", 0.0, raising=False)

    tentativas_refresh = []
    monkeypatch.setattr(
        build_static.app_module,
        "_tentar_refresh_automatico",
        lambda: tentativas_refresh.append(True),
    )
    monkeypatch.setitem(build_static.app_module.app.config, "TESTING", False)
    build_static.app_module.limpar_cache()
    site_base_path_anterior = build_static.app_module.app.config.get("SITE_BASE_PATH")

    build_static.build("/futebol-dashboard")

    assert tentativas_refresh == []
    assert build_static.app_module.app.config.get("SITE_BASE_PATH") == site_base_path_anterior


def test_build_static_usa_public_url_e_escapa_sitemap(monkeypatch, tmp_path):
    dist_dir = tmp_path / "dist"
    monkeypatch.setattr(build_static, "DIST_DIR", dist_dir)
    chamadas = []

    def public_url(path=""):
        chamadas.append(path)
        if path:
            return f"https://dashboard.example/base/{path}?q=a&x=<unsafe>"
        return "https://dashboard.example/base/?q=a&x=<unsafe>"

    monkeypatch.setattr(build_static.app_module, "public_url", public_url, raising=False)

    build_static.build("/base")

    sitemap = (dist_dir / "sitemap.xml").read_text(encoding="utf-8")
    robots = (dist_dir / "robots.txt").read_text(encoding="utf-8")
    assert "https://dashboard.example/base/?q=a&amp;x=&lt;unsafe&gt;" in sitemap
    assert "https://dashboard.example/base/time/PAL/?q=a&amp;x=&lt;unsafe&gt;" in sitemap
    assert "Sitemap: https://dashboard.example/base/sitemap.xml?q=a&x=<unsafe>" in robots
    assert "" in chamadas
    assert "sitemap.xml" in chamadas
    assert "time/PAL/" in chamadas


def test_preview_editorial_usa_fundo_escuro_continuo():
    css = build_static.Path("static/css/header-prototypes.css").read_text(encoding="utf-8")
    template_v2 = build_static.Path("templates/prototipo-header-editorial-v2.html").read_text(encoding="utf-8")

    assert 'body class="prototype-page prototype-editorial-v2-page"' in template_v2
    assert re.search(
        r"body\.prototype-editorial-v2-page\s*\{(?P<body>.*?)\}",
        css,
        re.S,
    )
    toolbar = re.search(
        r"\.prototype-editorial-v2-page \.prototype-live-toolbar\s*\{(?P<body>.*?)\}",
        css,
        re.S,
    )
    assert toolbar and "background: var(--editorial-v2-green-deep);" in toolbar.group("body")
