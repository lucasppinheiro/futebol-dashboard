from flask import Flask, render_template, jsonify
from typing import Any, Optional
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "brasileirao.json")

app = Flask(__name__)

_dados_cache: Optional[dict] = None


def carregar_dados() -> dict:
    global _dados_cache
    if _dados_cache is not None:
        return _dados_cache
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dados não encontrados em {DATA_PATH}. Execute: python gerar_dados.py")
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data: Any = json.load(f)
    _dados_cache = data
    return data


@app.route("/")
def index():
    dados = carregar_dados()
    return render_template("index.html", dados=dados)


@app.route("/api/classificacao")
def api_classificacao():
    dados = carregar_dados()
    return jsonify(dados["classificacao"])


@app.route("/api/artilharia")
def api_artilharia():
    dados = carregar_dados()
    return jsonify(dados["artilharia"])


@app.errorhandler(FileNotFoundError)
def dados_nao_encontrados(e: Exception):
    return (
        "<h1>Dados não encontrados</h1>"
        "<p>Execute no terminal: <code>python gerar_dados.py</code></p>"
        "<p>Depois inicie o servidor novamente com <code>python app.py</code></p>",
        503,
    )


if __name__ == "__main__":
    if not os.path.exists(DATA_PATH):
        from gerar_dados import gerar_dados
        gerar_dados()

    try:
        print("Futebol Dashboard rodando em http://localhost:5000")
    except UnicodeEncodeError:
        print("Futebol Dashboard rodando em http://localhost:5000")
    app.run(debug=True, port=5000, host="127.0.0.1", use_reloader=False)
