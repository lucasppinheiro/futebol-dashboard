import json
import logging
import math
import os
import re
import secrets
import threading
import time
import traceback
from typing import Any

from flask import Flask, jsonify, render_template, request

from dados_schema import DadosInvalidosError, validar_dados_dashboard
from env_config import carregar_env_local
from normalizacao import normalizar_dados_dashboard
from temporada import temporada_brasileirao_atual

carregar_env_local()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.environ.get("DATA_PATH", os.path.join(BASE_DIR, "data", "brasileirao.json"))
_ABSOLUTE_URL_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def normalizar_site_base_path(base_path: str | None) -> str:
    valor = (base_path or "").strip()
    if not valor or valor == "/":
        return ""
    return "/" + valor.strip("/")


app = Flask(__name__)
app.config["SITE_BASE_PATH"] = normalizar_site_base_path(os.environ.get("SITE_BASE_PATH"))


def site_url(path: str = "") -> str:
    base_path = normalizar_site_base_path(app.config.get("SITE_BASE_PATH"))
    destino = (path or "").strip()

    if not destino:
        return f"{base_path}/" if base_path else "/"

    if _ABSOLUTE_URL_RE.match(destino) or destino.startswith("//"):
        return destino

    if destino.startswith("#"):
        raiz = f"{base_path}/" if base_path else "/"
        return f"{raiz}{destino}"

    destino_normalizado = destino.lstrip("/")
    url = f"{base_path}/{destino_normalizado}" if base_path else f"/{destino_normalizado}"
    if destino.endswith("/") and not url.endswith("/"):
        url = f"{url}/"
    return url


app.jinja_env.globals["site_url"] = site_url

_dados_cache: dict | None = None
_dados_mtime: float = 0.0
_ultimo_refresh_automatico: float = 0.0
_cache_lock = threading.Lock()
_refresh_lock = threading.Lock()
_refresh_thread: threading.Thread | None = None


def limpar_cache() -> None:
    """Limpa o cache de dados."""
    global _dados_cache, _dados_mtime
    with _cache_lock:
        _dados_cache = None
        _dados_mtime = 0.0


def _ler_numero_env(nome: str, padrao: float) -> float:
    bruto = (os.environ.get(nome) or "").strip()
    if not bruto:
        return padrao
    try:
        valor = float(bruto)
    except ValueError:
        logger.warning("Valor invalido em %s=%r. Usando padrao %s.", nome, bruto, padrao)
        return padrao
    if not math.isfinite(valor):
        logger.warning("Valor invalido em %s=%r. Usando padrao %s.", nome, bruto, padrao)
        return padrao
    return valor


def _refresh_automatico_horas() -> float:
    return max(0.0, _ler_numero_env("DATA_AUTO_REFRESH_HOURS", 6.0))


def _refresh_automatico_cooldown_segundos() -> float:
    minutos = max(0.0, _ler_numero_env("DATA_AUTO_REFRESH_COOLDOWN_MINUTES", 15.0))
    return minutos * 60.0


def _token_football_data_disponivel() -> bool:
    return bool((os.environ.get("FOOTBALL_DATA_TOKEN") or "").strip())


def dados_estao_desatualizados(mtime: float) -> bool:
    horas = _refresh_automatico_horas()
    if horas <= 0:
        return False
    idade_segundos = max(0.0, time.time() - mtime)
    return idade_segundos >= horas * 3600.0


def _pode_tentar_refresh_automatico() -> bool:
    global _ultimo_refresh_automatico
    cooldown = _refresh_automatico_cooldown_segundos()
    if cooldown <= 0:
        return True
    return _ultimo_refresh_automatico == 0.0 or (time.time() - _ultimo_refresh_automatico) >= cooldown


def _executar_refresh_automatico() -> None:
    try:
        from atualizar_dados import atualizar

        atualizar(temporada_brasileirao_atual())
        limpar_cache()
        logger.info("Refresh automatico concluido com sucesso.")
    except Exception as e:
        logger.warning("Refresh automatico falhou. Mantendo cache local atual: %s", e)
    finally:
        _refresh_lock.release()


def _tentar_refresh_automatico() -> None:
    global _ultimo_refresh_automatico, _refresh_thread

    if app.config.get("TESTING"):
        return

    if not _token_football_data_disponivel() or not _pode_tentar_refresh_automatico():
        return

    if os.path.exists(DATA_PATH):
        mtime = os.path.getmtime(DATA_PATH)
        if not dados_estao_desatualizados(mtime):
            return
        if not _refresh_lock.acquire(blocking=False):
            return
        logger.info("Dados locais estao desatualizados. Iniciando refresh automatico em background.")
        _ultimo_refresh_automatico = time.time()
        # O request atual serve o dado antigo imediatamente; a rede roda fora dele.
        _refresh_thread = threading.Thread(target=_executar_refresh_automatico, daemon=True, name="refresh-dados")
        _refresh_thread.start()
        return

    # Sem arquivo local nao ha o que servir: o refresh sincrono e o unico caminho.
    if not _refresh_lock.acquire(blocking=False):
        return
    logger.info("Arquivo de dados nao existe. Tentando gerar dados atualizados automaticamente.")
    _ultimo_refresh_automatico = time.time()
    _executar_refresh_automatico()


def carregar_dados() -> dict[str, Any]:
    global _dados_cache, _dados_mtime

    _tentar_refresh_automatico()

    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dados nao encontrados em {DATA_PATH}. Execute: python gerar_dados.py")

    mtime = os.path.getmtime(DATA_PATH)
    with _cache_lock:
        if _dados_cache is not None and mtime == _dados_mtime:
            return _dados_cache

        with open(DATA_PATH, encoding="utf-8") as f:
            data: Any = json.load(f)

        normalizar_dados_dashboard(data)
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
    clube = next((t for t in dados["classificacao"] if t["sigla"] == sigla_upper), None)
    if not clube:
        if _is_api_request():
            return jsonify({"erro": f"Time '{sigla}' nao encontrado", "codigo": "TIME_NAO_ENCONTRADO"}), 404
        return f"<h1>Time nao encontrado</h1><p>Sigla '{sigla}' nao existe na classificacao.</p>", 404
    artilheiros_time = [j for j in dados["artilharia"] if j["sigla"] == sigla_upper]
    return render_template("time.html", time=clube, artilheiros=artilheiros_time, dados=dados)


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

        atualizar(temporada_brasileirao_atual())
        limpar_cache()
        return jsonify({"status": "ok", "mensagem": "Dados atualizados com sucesso"})
    except (OSError, ConnectionError, ValueError) as e:
        logger.error("Falha ao atualizar dados: %s", e)
        return jsonify({"erro": f"Falha ao atualizar dados: {e}", "codigo": "ATUALIZACAO_FALHOU"}), 500
    except Exception as e:
        logger.error("Erro inesperado ao atualizar dados: %s\n%s", e, traceback.format_exc())
        return jsonify({"erro": "Falha inesperada ao atualizar dados", "codigo": "ATUALIZACAO_FALHOU"}), 500


@app.route("/api/health")
def api_health():
    """Endpoint de health check."""
    status = {"status": "ok", "versao": "1.0.0"}
    try:
        mtime = os.path.getmtime(DATA_PATH)
        from datetime import datetime, timezone

        status["dados_atualizados_em"] = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
        status["dados_desatualizados"] = dados_estao_desatualizados(mtime)
    except OSError:
        status["dados_atualizados_em"] = None
        status["dados_desatualizados"] = True
    status["refresh_automatico"] = _token_football_data_disponivel() and _refresh_automatico_horas() > 0
    status["temporada_padrao"] = temporada_brasileirao_atual()
    return jsonify(status)


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

    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", "5000"))

    logger.info("Futebol Dashboard rodando em http://%s:%d", host, port)
    app.run(debug=debug, port=port, host=host, use_reloader=False)
