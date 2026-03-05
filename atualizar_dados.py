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
import os
import sys

from api_client import buscar_classificacao, buscar_artilharia
from dados_schema import validar_dados_dashboard
from gerar_dados import montar_info

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "brasileirao.json")


def atualizar(temporada: str = "2026") -> None:
    print(f"Buscando dados da temporada {temporada} via football-data.org...")

    try:
        classificacao = buscar_classificacao(temporada)
        artilharia = buscar_artilharia(temporada)
    except Exception as e:
        print(f"Erro ao buscar dados da API: {e}")
        if os.path.exists(OUTPUT_FILE):
            print("Mantendo dados locais existentes.")
        else:
            print("Nenhum dado local disponivel. Execute 'python gerar_dados.py' para usar dados estaticos.")
        sys.exit(1)

    if not classificacao:
        print("API retornou classificacao vazia. Mantendo dados locais.")
        sys.exit(1)

    if not artilharia:
        print("API retornou artilharia vazia. Mantendo dados locais.")
        sys.exit(1)

    dados = {
        "classificacao": classificacao,
        "artilharia": artilharia,
        "info": montar_info(classificacao, artilharia, temporada),
    }

    try:
        validar_dados_dashboard(dados)
    except Exception as e:
        print(f"Dados da API falharam na validacao: {e}")
        print("Mantendo dados locais existentes.")
        sys.exit(1)

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    print(f"Dados atualizados em: {OUTPUT_FILE}")
    print(f"{len(classificacao)} times | {len(artilharia)} artilheiros")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Atualizar dados do Brasileirao via football-data.org")
    parser.add_argument("--temporada", default="2026", help="Temporada (ex: 2026)")
    args = parser.parse_args()
    atualizar(args.temporada)
