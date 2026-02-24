import json
import os
from typing import Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "brasileirao.json")


def gerar_classificacao() -> list[dict[str, Any]]:
    dados_reais: list[dict[str, Any]] = [
        {"posicao": 1,  "time": "Flamengo",            "sigla": "FLA", "estado": "RJ", "cor": "#E11D1D", "jogos": 38, "vitorias": 23, "empates": 10, "derrotas": 5,  "gols_pro": 78, "gols_contra": 27},
        {"posicao": 2,  "time": "Palmeiras",            "sigla": "PAL", "estado": "SP", "cor": "#006437", "jogos": 38, "vitorias": 23, "empates": 7,  "derrotas": 8,  "gols_pro": 66, "gols_contra": 33},
        {"posicao": 3,  "time": "Cruzeiro",             "sigla": "CRU", "estado": "MG", "cor": "#003DA5", "jogos": 38, "vitorias": 19, "empates": 13, "derrotas": 6,  "gols_pro": 55, "gols_contra": 31},
        {"posicao": 4,  "time": "Mirassol",             "sigla": "MIR", "estado": "SP", "cor": "#FFD700", "jogos": 38, "vitorias": 18, "empates": 13, "derrotas": 7,  "gols_pro": 63, "gols_contra": 39},
        {"posicao": 5,  "time": "Fluminense",           "sigla": "FLU", "estado": "RJ", "cor": "#7B0023", "jogos": 38, "vitorias": 19, "empates": 7,  "derrotas": 12, "gols_pro": 50, "gols_contra": 39},
        {"posicao": 6,  "time": "Botafogo",             "sigla": "BOT", "estado": "RJ", "cor": "#1a1a2e", "jogos": 38, "vitorias": 17, "empates": 12, "derrotas": 9,  "gols_pro": 58, "gols_contra": 38},
        {"posicao": 7,  "time": "Bahia",                "sigla": "BAH", "estado": "BA", "cor": "#004A99", "jogos": 38, "vitorias": 17, "empates": 9,  "derrotas": 12, "gols_pro": 50, "gols_contra": 46},
        {"posicao": 8,  "time": "São Paulo",            "sigla": "SAO", "estado": "SP", "cor": "#FF0000", "jogos": 38, "vitorias": 14, "empates": 9,  "derrotas": 15, "gols_pro": 43, "gols_contra": 47},
        {"posicao": 9,  "time": "Grêmio",               "sigla": "GRE", "estado": "RS", "cor": "#0080C8", "jogos": 38, "vitorias": 13, "empates": 10, "derrotas": 15, "gols_pro": 47, "gols_contra": 50},
        {"posicao": 10, "time": "Red Bull Bragantino",   "sigla": "BRA", "estado": "SP", "cor": "#E30613", "jogos": 38, "vitorias": 14, "empates": 6,  "derrotas": 18, "gols_pro": 45, "gols_contra": 57},
        {"posicao": 11, "time": "Atlético-MG",          "sigla": "CAM", "estado": "MG", "cor": "#1a1a2e", "jogos": 38, "vitorias": 12, "empates": 12, "derrotas": 14, "gols_pro": 43, "gols_contra": 44},
        {"posicao": 12, "time": "Santos",               "sigla": "SAN", "estado": "SP", "cor": "#1a1a2e", "jogos": 38, "vitorias": 12, "empates": 11, "derrotas": 15, "gols_pro": 45, "gols_contra": 50},
        {"posicao": 13, "time": "Corinthians",          "sigla": "COR", "estado": "SP", "cor": "#1a1a2e", "jogos": 38, "vitorias": 12, "empates": 11, "derrotas": 15, "gols_pro": 42, "gols_contra": 47},
        {"posicao": 14, "time": "Vasco da Gama",        "sigla": "VAS", "estado": "RJ", "cor": "#1a1a2e", "jogos": 38, "vitorias": 13, "empates": 6,  "derrotas": 19, "gols_pro": 55, "gols_contra": 60},
        {"posicao": 15, "time": "Vitória",              "sigla": "VIT", "estado": "BA", "cor": "#E11D1D", "jogos": 38, "vitorias": 11, "empates": 12, "derrotas": 15, "gols_pro": 35, "gols_contra": 52},
        {"posicao": 16, "time": "Internacional",        "sigla": "INT", "estado": "RS", "cor": "#E30613", "jogos": 38, "vitorias": 11, "empates": 11, "derrotas": 16, "gols_pro": 44, "gols_contra": 57},
        {"posicao": 17, "time": "Ceará",                "sigla": "CEA", "estado": "CE", "cor": "#1a1a2e", "jogos": 38, "vitorias": 11, "empates": 10, "derrotas": 17, "gols_pro": 34, "gols_contra": 40},
        {"posicao": 18, "time": "Fortaleza",            "sigla": "FOR", "estado": "CE", "cor": "#004A99", "jogos": 38, "vitorias": 11, "empates": 10, "derrotas": 17, "gols_pro": 43, "gols_contra": 58},
        {"posicao": 19, "time": "Juventude",            "sigla": "JUV", "estado": "RS", "cor": "#006633", "jogos": 38, "vitorias": 9,  "empates": 8,  "derrotas": 21, "gols_pro": 35, "gols_contra": 69},
        {"posicao": 20, "time": "Sport",                "sigla": "SPO", "estado": "PE", "cor": "#E30613", "jogos": 38, "vitorias": 2,  "empates": 11, "derrotas": 25, "gols_pro": 28, "gols_contra": 75},
    ]

    for time in dados_reais:
        vitorias: int = time["vitorias"]
        empates: int = time["empates"]
        jogos: int = time["jogos"]
        gols_pro: int = time["gols_pro"]
        gols_contra: int = time["gols_contra"]
        pontos = vitorias * 3 + empates
        time["saldo"] = gols_pro - gols_contra
        time["pontos"] = pontos
        time["aproveitamento"] = round(pontos / (jogos * 3) * 100, 1)

    return dados_reais


def gerar_artilharia() -> list:
    artilheiros = [
        {"jogador": "Kaio Jorge",       "time": "Cruzeiro",            "sigla": "CRU", "posicao": "Atacante", "gols": 21},
        {"jogador": "Arrascaeta",       "time": "Flamengo",            "sigla": "FLA", "posicao": "Meia",     "gols": 18},
        {"jogador": "Vitor Roque",      "time": "Palmeiras",           "sigla": "PAL", "posicao": "Atacante", "gols": 16},
        {"jogador": "Pablo Vegetti",    "time": "Vasco da Gama",       "sigla": "VAS", "posicao": "Atacante", "gols": 14},
        {"jogador": "Rayan",            "time": "Vasco da Gama",       "sigla": "VAS", "posicao": "Atacante", "gols": 14},
        {"jogador": "Reinaldo",         "time": "Mirassol",            "sigla": "MIR", "posicao": "Lateral",  "gols": 13},
        {"jogador": "Pedro",            "time": "Flamengo",            "sigla": "FLA", "posicao": "Atacante", "gols": 12},
        {"jogador": "Carlos Vinícius",  "time": "Grêmio",              "sigla": "GRE", "posicao": "Atacante", "gols": 12},
        {"jogador": "Flaco López",      "time": "Palmeiras",           "sigla": "PAL", "posicao": "Atacante", "gols": 12},
        {"jogador": "Willian José",     "time": "Bahia",               "sigla": "BAH", "posicao": "Atacante", "gols": 11},
        {"jogador": "Pedro Raúl",       "time": "Ceará",               "sigla": "CEA", "posicao": "Atacante", "gols": 11},
        {"jogador": "Alan Patrick",     "time": "Internacional",       "sigla": "INT", "posicao": "Meia",     "gols": 11},
        {"jogador": "Yuri Alberto",     "time": "Corinthians",         "sigla": "COR", "posicao": "Atacante", "gols": 10},
        {"jogador": "Jhon Jhon",        "time": "Red Bull Bragantino", "sigla": "BRA", "posicao": "Meia",     "gols": 10},
        {"jogador": "Álvaro Barreal",   "time": "Santos",              "sigla": "SAN", "posicao": "Meia",     "gols": 9},
        {"jogador": "Luciano",          "time": "São Paulo",           "sigla": "SAO", "posicao": "Atacante", "gols": 9},
        {"jogador": "Renato Kayzer",    "time": "Vitória",             "sigla": "VIT", "posicao": "Atacante", "gols": 9},
        {"jogador": "Hulk",             "time": "Atlético-MG",         "sigla": "CAM", "posicao": "Atacante", "gols": 8},
        {"jogador": "Bruno Henrique",   "time": "Flamengo",            "sigla": "FLA", "posicao": "Atacante", "gols": 8},
        {"jogador": "Gabriel Taliari",  "time": "Juventude",           "sigla": "JUV", "posicao": "Atacante", "gols": 8},
    ]

    return artilheiros


def gerar_dados() -> None:
    classificacao = gerar_classificacao()
    artilharia = gerar_artilharia()
    campeao = classificacao[0]["time"]
    campeao_pts = classificacao[0]["pontos"]
    artilheiro_nome = artilharia[0]["jogador"]
    artilheiro_gols = artilharia[0]["gols"]

    dados = {
        "classificacao": classificacao,
        "artilharia": artilharia,
        "info": {
            "campeonato": "Brasileirão Série A",
            "temporada": "2025",
            "rodadas_total": 38,
            "times_total": 20,
            "campeao": campeao,
            "campeao_pontos": campeao_pts,
            "artilheiro": artilheiro_nome,
            "artilheiro_gols": artilheiro_gols,
        },
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    try:
        print(f"Dados gerados em: {OUTPUT_FILE}")
        print(f"{len(dados['classificacao'])} times | {len(dados['artilharia'])} artilheiros")
    except UnicodeEncodeError:
        print(f"Dados gerados em: {OUTPUT_FILE}")


if __name__ == "__main__":
    gerar_dados()
