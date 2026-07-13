import json
import re

import build_static


def test_build_static_aplica_site_base_path(monkeypatch, tmp_path):
    dist_dir = tmp_path / "dist"
    monkeypatch.setattr(build_static, "DIST_DIR", dist_dir)

    build_static.build("/futebol-dashboard")

    index_html = (dist_dir / "index.html").read_text(encoding="utf-8")
    time_html = (dist_dir / "time" / "PAL" / "index.html").read_text(encoding="utf-8")

    assert 'href="/futebol-dashboard/static/css/style.css"' in index_html
    assert 'href="/futebol-dashboard/time/PAL/"' in index_html
    assert 'src="/futebol-dashboard/static/js/main.js"' in index_html
    assert 'href="/futebol-dashboard/"' in time_html
    assert 'href="/futebol-dashboard/#classificacao"' in time_html
    assert (dist_dir / ".nojekyll").exists()
    assert (dist_dir / "404.html").exists()
    assert (dist_dir / "robots.txt").exists()
    assert (dist_dir / "sitemap.xml").exists()
    assert not (dist_dir / "_redirects").exists()

    pagina_404 = (dist_dir / "404.html").read_text(encoding="utf-8")
    assert "Página não encontrada" in pagina_404
    assert "tabela-classificacao" not in pagina_404
    assert 'href="/futebol-dashboard/"' in pagina_404

    classificacao_json = json.loads((dist_dir / "api" / "classificacao.json").read_text(encoding="utf-8"))
    artilharia_json = json.loads((dist_dir / "api" / "artilharia.json").read_text(encoding="utf-8"))
    assert len(classificacao_json) == 20
    assert artilharia_json and {"jogador", "time", "sigla", "gols"}.issubset(artilharia_json[0].keys())

    health = json.loads((dist_dir / "api" / "health.json").read_text(encoding="utf-8"))
    assert health["dados_desatualizados"] == build_static.app_module.dados_estao_desatualizados(
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
    assert 'href="/static/css/style.css"' in index_html
    assert 'href="/time/PAL/"' in index_html
    assert "https://dashboard.example/time/PAL/" in sitemap
