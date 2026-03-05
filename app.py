from flask import Flask, render_template, jsonify, request
from typing import Any
import json
import os
import secrets

from dados_schema import validar_dados_dashboard, DadosInvalidosError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.environ.get("DATA_PATH", os.path.join(BASE_DIR, "data", "brasileirao.json"))

app = Flask(__name__)

_dados_cache: dict | None = None
_dados_mtime: float = 0.0


def limpar_cache() -> None:
    """Limpa o cache de dados."""
    global _dados_cache, _dados_mtime
    _dados_cache = None
    _dados_mtime = 0.0


def carregar_dados() -> dict[str, Any]:
    global _dados_cache, _dados_mtime

    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dados nao encontrados em {DATA_PATH}. Execute: python gerar_dados.py")

    mtime = os.path.getmtime(DATA_PATH)
    if _dados_cache is not None and mtime == _dados_mtime:
        return _dados_cache

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data: Any = json.load(f)

    validar_dados_dashboard(data)
    _dados_cache = data
    _dados_mtime = mtime
    return data


def _is_api_request() -> bool:
    return request.path.startswith("/api/")


@app.route("/")
def index():
    dados = carregar_dados()
    return render_template("index.html", dados=dados)


@app.route("/time/<sigla>")
def detalhe_time(sigla: str):
    dados = carregar_dados()
    sigla_upper = sigla.upper()
    time = next((t for t in dados["classificacao"] if t["sigla"] == sigla_upper), None)
    if not time:
        if _is_api_request():
            return jsonify({"erro": f"Time '{sigla}' nao encontrado", "codigo": "TIME_NAO_ENCONTRADO"}), 404
        return f"<h1>Time nao encontrado</h1><p>Sigla '{sigla}' nao existe na classificacao.</p>", 404
    artilheiros_time = [j for j in dados["artilharia"] if j["sigla"] == sigla_upper]
    return render_template("time.html", time=time, artilheiros=artilheiros_time, dados=dados)


@app.route("/api/classificacao")
def api_classificacao():
    dados = carregar_dados()
    return jsonify(dados["classificacao"])


@app.route("/api/artilharia")
def api_artilharia():
    dados = carregar_dados()
    return jsonify(dados["artilharia"])


@app.route("/api/atualizar", methods=["POST"])
def api_atualizar():
    token = (os.environ.get("API_UPDATE_TOKEN") or "").strip()
    if not token:
        return jsonify({"erro": "Endpoint nao configurado", "codigo": "NAO_CONFIGURADO"}), 501
    auth = (request.headers.get("Authorization") or "").strip()
    if not secrets.compare_digest(auth, f"Bearer {token}"):
        return jsonify({"erro": "Nao autorizado", "codigo": "NAO_AUTORIZADO"}), 403

    try:
        from atualizar_dados import atualizar
        atualizar()
        limpar_cache()
        return jsonify({"status": "ok", "mensagem": "Dados atualizados com sucesso"})
    except Exception:
        return jsonify({"erro": "Falha ao atualizar dados", "codigo": "ATUALIZACAO_FALHOU"}), 500


@app.errorhandler(FileNotFoundError)
def erro_arquivo_nao_encontrado(e: Exception):
    if _is_api_request():
        return jsonify({"erro": str(e), "codigo": "DADOS_NAO_ENCONTRADOS"}), 503
    return (
        "<h1>Dados nao encontrados</h1>"
        "<p>Execute no terminal: <code>python gerar_dados.py</code></p>"
        "<p>Depois inicie o servidor novamente com <code>python app.py</code></p>",
        503,
    )


@app.errorhandler(json.JSONDecodeError)
def erro_json_invalido(e: Exception):
    if _is_api_request():
        return jsonify({"erro": "Arquivo de dados com JSON invalido", "codigo": "JSON_INVALIDO"}), 500
    return "<h1>Erro nos dados</h1><p>O arquivo de dados esta corrompido.</p>", 500


@app.errorhandler(DadosInvalidosError)
def erro_dados_invalidos(e: Exception):
    if _is_api_request():
        return jsonify({"erro": str(e), "codigo": "DADOS_INVALIDOS"}), 500
    return f"<h1>Dados invalidos</h1><p>{e}</p>", 500


@app.errorhandler(KeyError)
def erro_chave_ausente(e: Exception):
    if _is_api_request():
        return jsonify({"erro": f"Chave ausente: {e}", "codigo": "CHAVE_AUSENTE"}), 500
    return f"<h1>Erro interno</h1><p>Chave ausente nos dados: {e}</p>", 500


if __name__ == "__main__":
    if not os.path.exists(DATA_PATH):
        from gerar_dados import gerar_dados
        gerar_dados()
    
    limpar_cache()

    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", "5000"))

    print(f"Futebol Dashboard rodando em http://{host}:{port}")
    app.run(debug=debug, port=port, host=host, use_reloader=False)
