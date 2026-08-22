import json
import re

import build_static


def test_build_static_aplica_site_base_path(monkeypatch, tmp_path):
    dist_dir = tmp_path / "dist"
    monkeypatch.setattr(build_static, "DIST_DIR", dist_dir)

    build_static.build("/futebol-dashboard")

    index_html = (dist_dir / "index.html").read_text(encoding="utf-8")
    time_html = (dist_dir / "time" / "PAL" / "index.html").read_text(encoding="utf-8")
    not_found_html = (dist_dir / "404.html").read_text(encoding="utf-8")

    assert re.search(r'href="/futebol-dashboard/static/css/style\.css\?v=[0-9a-f]+"', index_html)
    assert re.search(r'href="/futebol-dashboard/static/css/matchday\.css\?v=[0-9a-f]+"', index_html)
    assert re.search(r'href="/futebol-dashboard/static/css/editorial-header\.css\?v=[0-9a-f]+"', index_html)
    assert 'href="/futebol-dashboard/time/PAL/"' in index_html
    assert 'src="/futebol-dashboard/static/img/escudos/normalizados/CAP.png"' in index_html
    assert 'src="/futebol-dashboard/static/img/escudos/normalizados/PAL.png"' in index_html
    assert re.search(r'src="/futebol-dashboard/static/js/main\.js\?v=[0-9a-f]+"', index_html)
    assert 'class="scorer-podium-crest"\n                            width="30" height="30"' in index_html
    assert 'window.siteBasePath = "/futebol-dashboard/"' in index_html
    assert "escudo: normalizarUrlEscudo(time.escudo)" in index_html
    assert "window.escudoFallback" in index_html
    assert "concept-dock" not in index_html
    assert 'data-visual="matchday"' in index_html
    assert 'class="hero editorial-v2-production"' in index_html
    assert 'aria-valuetext="Rodada ' in index_html
    assert "Dados atualizados em" in index_html
    assert 'href="/futebol-dashboard/"' in time_html
    assert 'href="/futebol-dashboard/#classificacao"' in time_html
    assert (dist_dir / ".nojekyll").exists()
    assert "Página não encontrada" in not_found_html
    assert "editorial-v2-production" not in not_found_html
    assert not (dist_dir / "prototipos").exists()
    assert not (dist_dir / "static" / "css" / "header-prototypes.css").exists()
    assert not (dist_dir / "static" / "js" / "header-prototypes.js").exists()
    assert (dist_dir / "robots.txt").exists()
    assert (dist_dir / "sitemap.xml").exists()
    assert not (dist_dir / "_redirects").exists()
    assert (dist_dir / "static" / "css" / "matchday.css").exists()
    assert (dist_dir / "static" / "css" / "editorial-header.css").exists()
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
    assert health["dados_desatualizados"] == build_static.app_module._dados_estao_desatualizados(
        build_static.Path(build_static.app_module.DATA_PATH).stat().st_mtime
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
    assert re.search(r'href="/static/css/style\.css\?v=[0-9a-f]+"', index_html)
    assert 'href="/time/PAL/"' in index_html
    assert "https://dashboard.example/time/PAL/" in sitemap
