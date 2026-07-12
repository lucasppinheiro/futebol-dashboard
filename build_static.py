import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from flask import render_template

import app as app_module


BASE_DIR = Path(__file__).resolve().parent
DIST_DIR = BASE_DIR / "dist"
STATIC_DIR = BASE_DIR / "static"


def _render(url: str, template: str, **context: object) -> str:
    with app_module.app.test_request_context(url):
        return render_template(template, **context)


def _copiar_estaticos() -> None:
    destino = DIST_DIR / "static"
    if destino.exists():
        shutil.rmtree(destino)
    shutil.copytree(STATIC_DIR, destino)


def _escrever_arquivo(rel_path: str, conteudo: str) -> None:
    destino = DIST_DIR / rel_path
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(conteudo, encoding="utf-8")


def _escrever_json(rel_path: str, payload: object) -> None:
    destino = DIST_DIR / rel_path
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _resolver_site_base_path(site_base_path: str | None = None) -> str:
    if site_base_path is not None:
        return app_module.normalizar_site_base_path(site_base_path)

    configurado = os.environ.get("SITE_BASE_PATH")
    if configurado is not None:
        return app_module.normalizar_site_base_path(configurado)

    return ""


def build(site_base_path: str | None = None) -> None:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    resolved_site_base_path = _resolver_site_base_path(site_base_path)
    previous_site_base_path = app_module.app.config.get("SITE_BASE_PATH", "")
    app_module.app.config["SITE_BASE_PATH"] = resolved_site_base_path

    app_module.limpar_cache()
    try:
        dados = app_module.carregar_dados()

        _copiar_estaticos()
        _escrever_arquivo(".nojekyll", "")
        index_html = _render("/", "index.html", dados=dados)
        _escrever_arquivo("index.html", index_html)
        _escrever_arquivo("404.html", index_html)

        for time in dados["classificacao"]:
            artilheiros = [j for j in dados["artilharia"] if j["sigla"] == time["sigla"]]
            html = _render(f"/time/{time['sigla']}/", "time.html", time=time, artilheiros=artilheiros, dados=dados)
            _escrever_arquivo(f"time/{time['sigla']}/index.html", html)

        _escrever_json("api/classificacao.json", dados["classificacao"])
        _escrever_json("api/artilharia.json", dados["artilharia"])

        try:
            mtime = Path(app_module.DATA_PATH).stat().st_mtime
            atualizado_em = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
            dados_desatualizados = app_module.dados_estao_desatualizados(mtime)
        except OSError:
            atualizado_em = None
            dados_desatualizados = True

        _escrever_json(
            "api/health.json",
            {
                "status": "ok",
                "versao": "1.0.0",
                "dados_atualizados_em": atualizado_em,
                "dados_desatualizados": dados_desatualizados,
                "refresh_automatico": False,
                "temporada_padrao": dados["info"]["temporada"],
            },
        )
        site_root = (os.environ.get("SITE_ORIGIN") or "https://futebol-dashboard.vercel.app").rstrip("/") + "/"
        _escrever_arquivo("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {site_root}sitemap.xml\n")
        urls = [site_root] + [f"{site_root}time/{time['sigla']}/" for time in dados["classificacao"]]
        sitemap = "\n".join(f"  <url><loc>{url}</loc></url>" for url in urls)
        _escrever_arquivo(
            "sitemap.xml",
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{sitemap}\n</urlset>\n',
        )
    finally:
        app_module.app.config["SITE_BASE_PATH"] = previous_site_base_path


if __name__ == "__main__":
    build()
