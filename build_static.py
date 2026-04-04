import json
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


def build() -> None:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    app_module.limpar_cache()
    dados = app_module.carregar_dados()

    _copiar_estaticos()
    _escrever_arquivo("index.html", _render("/", "index.html", dados=dados))

    for time in dados["classificacao"]:
        artilheiros = [j for j in dados["artilharia"] if j["sigla"] == time["sigla"]]
        html = _render(f"/time/{time['sigla']}", "time.html", time=time, artilheiros=artilheiros, dados=dados)
        _escrever_arquivo(f"time/{time['sigla']}/index.html", html)

    _escrever_json("api/classificacao.json", dados["classificacao"])
    _escrever_json("api/artilharia.json", dados["artilharia"])

    try:
        mtime = Path(app_module.DATA_PATH).stat().st_mtime
        atualizado_em = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
    except OSError:
        atualizado_em = None

    _escrever_json(
        "api/health.json",
        {
            "status": "ok",
            "versao": "1.0.0",
            "dados_atualizados_em": atualizado_em,
            "dados_desatualizados": False,
            "refresh_automatico": False,
            "temporada_padrao": dados["info"]["temporada"],
        },
    )

    _escrever_arquivo(
        "_redirects",
        "\n".join(
            [
                "/api/classificacao /api/classificacao.json 200",
                "/api/artilharia /api/artilharia.json 200",
                "/api/health /api/health.json 200",
                "",
            ]
        ),
    )


if __name__ == "__main__":
    build()
