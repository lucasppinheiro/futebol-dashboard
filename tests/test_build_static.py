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
    assert not (dist_dir / "_redirects").exists()
