"""
Busca dados atualizados do Brasileirao via football-data.org e grava em data/brasileirao.json.

Uso:
    python atualizar_dados.py
    python atualizar_dados.py --temporada 2026

Requer: FOOTBALL_DATA_TOKEN definida como variavel de ambiente.
Fallback: se a API falhar, mantem os dados locais existentes.
"""

import argparse
import json
import logging
import os
import sys

from api_client import buscar_classificacao, buscar_artilharia
from dados_schema import validar_dados_dashboard
from env_config import carregar_env_local
from gerar_dados import montar_info
from temporada import temporada_brasileirao_atual

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "brasileirao.json")


carregar_env_local()


def atualizar(temporada: str | None = None) -> None:
    temporada = temporada or temporada_brasileirao_atual()
    logger.info("Buscando dados da temporada %s via football-data.org...", temporada)

    try:
        classificacao = buscar_classificacao(temporada)
        artilharia = buscar_artilharia(temporada)
    except Exception as e:
        logger.error("Erro ao buscar dados da API: %s", e)
        if os.path.exists(OUTPUT_FILE):
            logger.info("Mantendo dados locais existentes.")
        else:
            logger.warning("Nenhum dado local disponivel. Execute 'python gerar_dados.py' para usar dados estaticos.")
        raise

    if not classificacao:
        raise ValueError("API retornou classificacao vazia. Mantendo dados locais.")

    if not artilharia:
        raise ValueError("API retornou artilharia vazia. Mantendo dados locais.")

    dados = {
        "classificacao": classificacao,
        "artilharia": artilharia,
        "info": montar_info(classificacao, artilharia, temporada),
    }

    try:
        validar_dados_dashboard(dados)
    except Exception as e:
        logger.error("Dados da API falharam na validacao: %s", e)
        logger.info("Mantendo dados locais existentes.")
        raise

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    logger.info("Dados atualizados em: %s", OUTPUT_FILE)
    logger.info("%d times | %d artilheiros", len(classificacao), len(artilharia))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Atualizar dados do Brasileirao via football-data.org")
    parser.add_argument("--temporada", default=None, help="Temporada (ex: 2026). Padrao: ano atual.")
    args = parser.parse_args()
    try:
        atualizar(args.temporada)
    except Exception:
        raise SystemExit(1)
