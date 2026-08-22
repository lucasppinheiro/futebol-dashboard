"""
Busca dados atualizados do Brasileirao e grava em data/brasileirao.json.

Uso:
    python atualizar_dados.py
    python atualizar_dados.py --temporada 2026

Fonte padrao: CBF. Fallback opcional: football-data.org com FOOTBALL_DATA_TOKEN.
Fallback: se a API falhar, mantem os dados locais existentes.
"""

import argparse
import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from api_client import (
    buscar_artilharia,
    buscar_artilharia_cbf,
    buscar_classificacao,
    buscar_classificacao_cbf,
)
from dados_schema import validar_dados_dashboard
from env_config import carregar_env_local
from gerar_dados import montar_info
from temporada import temporada_brasileirao_atual

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "brasileirao.json")


carregar_env_local()


def _escrever_json_atomico(destino: str | Path, dados: object) -> None:
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destino.parent,
            prefix=f".{destino.name}.",
            suffix=".tmp",
            delete=False,
        ) as arquivo:
            temporario = Path(arquivo.name)
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
            arquivo.write("\n")
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(temporario, destino)
    finally:
        if temporario and temporario.exists():
            temporario.unlink()


def _buscar_dados(temporada: str) -> tuple[list[dict], list[dict], str]:
    fonte = os.environ.get("DATA_SOURCE", "cbf").strip().lower()
    if fonte == "football-data":
        return buscar_classificacao(temporada), buscar_artilharia(temporada), "football-data.org"

    try:
        return buscar_classificacao_cbf(temporada), buscar_artilharia_cbf(temporada), "CBF"
    except Exception as e:
        logger.warning("Falha ao buscar dados da CBF: %s", e)
        logger.info("Tentando fallback via football-data.org...")
        return buscar_classificacao(temporada), buscar_artilharia(temporada), "football-data.org"


def _timestamp_atualizacao(dados_base: dict) -> str:
    existentes: dict | None = None
    try:
        with open(OUTPUT_FILE, encoding="utf-8") as arquivo:
            carregados = json.load(arquivo)
            if isinstance(carregados, dict):
                existentes = carregados
    except (OSError, json.JSONDecodeError):
        existentes = None

    blocos_competicao = ("classificacao", "artilharia", "info")
    dados_inalterados = existentes is not None and all(
        existentes.get(bloco) == dados_base[bloco] for bloco in blocos_competicao
    )

    if dados_inalterados:
        valor_salvo = existentes.get("dados_atualizados_em")
        if isinstance(valor_salvo, str) and valor_salvo:
            return valor_salvo
        try:
            return datetime.fromtimestamp(os.path.getmtime(OUTPUT_FILE), tz=timezone.utc).isoformat()
        except OSError:
            pass

    return datetime.now(timezone.utc).isoformat()


def atualizar(temporada: str | None = None) -> None:
    temporada = temporada or temporada_brasileirao_atual()
    logger.info("Buscando dados da temporada %s...", temporada)

    try:
        classificacao, artilharia, fonte = _buscar_dados(temporada)
    except Exception as e:
        logger.error("Erro ao buscar dados: %s", e)
        if os.path.exists(OUTPUT_FILE):
            logger.info("Mantendo dados locais existentes.")
        else:
            logger.warning("Nenhum dado local disponivel. Execute 'python gerar_dados.py' para usar dados estaticos.")
        raise

    if not classificacao:
        raise ValueError("API retornou classificacao vazia. Mantendo dados locais.")

    if not artilharia:
        raise ValueError("API retornou artilharia vazia. Mantendo dados locais.")

    dados_base = {
        "classificacao": classificacao,
        "artilharia": artilharia,
        "info": montar_info(classificacao, artilharia, temporada),
    }
    dados = {
        "classificacao": dados_base["classificacao"],
        "artilharia": dados_base["artilharia"],
        "dados_atualizados_em": _timestamp_atualizacao(dados_base),
        "info": dados_base["info"],
    }

    try:
        validar_dados_dashboard(dados)
    except Exception as e:
        logger.error("Dados da API falharam na validacao: %s", e)
        logger.info("Mantendo dados locais existentes.")
        raise

    _escrever_json_atomico(OUTPUT_FILE, dados)

    logger.info("Dados atualizados em: %s", OUTPUT_FILE)
    logger.info("Fonte: %s", fonte)
    logger.info("%d times | %d artilheiros", len(classificacao), len(artilharia))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Atualizar dados do Brasileirao")
    parser.add_argument("--temporada", default=None, help="Temporada (ex: 2026). Padrao: ano atual.")
    args = parser.parse_args()
    try:
        atualizar(args.temporada)
    except Exception as exc:
        raise SystemExit(1) from exc
