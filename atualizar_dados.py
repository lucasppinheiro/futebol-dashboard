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
from gerar_dados import montar_info

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "brasileirao.json")


def atualizar(temporada: str = "2026") -> None:
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
        sys.exit(1)

    if not classificacao:
        logger.warning("API retornou classificacao vazia. Mantendo dados locais.")
        sys.exit(1)

    if not artilharia:
        logger.warning("API retornou artilharia vazia. Mantendo dados locais.")
        sys.exit(1)

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
        sys.exit(1)

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    logger.info("Dados atualizados em: %s", OUTPUT_FILE)
    logger.info("%d times | %d artilheiros", len(classificacao), len(artilharia))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Atualizar dados do Brasileirao via football-data.org")
    parser.add_argument("--temporada", default="2026", help="Temporada (ex: 2026)")
    args = parser.parse_args()
    atualizar(args.temporada)
