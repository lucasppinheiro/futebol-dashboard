"""
Cliente para buscar dados do Brasileirao via football-data.org v4.

Requer variavel de ambiente FOOTBALL_DATA_TOKEN com o token da API.
Documentacao: https://docs.football-data.org/general/v4/index.html
"""

import os
import urllib.request
import urllib.error
import json
from typing import Any


API_BASE = "https://api.football-data.org/v4"
COMPETITION = "BSA"


def _get_token() -> str:
    token = os.environ.get("FOOTBALL_DATA_TOKEN", "").strip()
    if not token:
        raise EnvironmentError(
            "Variavel FOOTBALL_DATA_TOKEN nao definida. "
            "Cadastre-se em https://www.football-data.org/client/register e defina o token."
        )
    return token


def _fetch(url: str) -> dict[str, Any]:
    token = _get_token()
    req = urllib.request.Request(url, headers={"X-Auth-Token": token})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        raise ConnectionError(f"API retornou HTTP {e.code}: {e.reason} — {body}") from e
    except urllib.error.URLError as e:
        raise ConnectionError(f"Erro de conexao com a API: {e.reason}") from e

    if "errorCode" in data:
        raise ValueError(f"API retornou erro: {data.get('message', data)}")

    return data


def _cor_padrao(sigla: str) -> str:
    cores: dict[str, str] = {
        "COR": "#000000", "FLA": "#E11D1D", "PAL": "#006437", "SAO": "#FF0000",
        "SAN": "#000000", "RBB": "#E30613", "MIR": "#FFD700", "FLU": "#7B0023",
        "VAS": "#000000", "BOT": "#000000", "CRU": "#003DA5", "CAM": "#000000",
        "BAH": "#004A99", "VIT": "#E11D1D", "GRE": "#0080C8", "INT": "#E30613",
        "CFC": "#006633", "CAP": "#E11D1D", "CHA": "#008000", "REM": "#00008B",
        "CEA": "#1a1a2e", "FOR": "#004A99", "JUV": "#006633", "SPO": "#E30613",
        "NOV": "#E30613", "AME": "#006633", "CUI": "#006437", "GOI": "#006437", "AVA": "#004A99",
    }
    return cores.get(sigla.upper(), "#64748b")


SIGLAS_MAPA: dict[str, str] = {
    "CR Flamengo": "FLA", "Flamengo": "FLA",
    "SE Palmeiras": "PAL", "Palmeiras": "PAL",
    "Cruzeiro EC": "CRU", "Cruzeiro": "CRU",
    "Mirassol FC": "MIR", "Mirassol": "MIR",
    "Fluminense FC": "FLU", "Fluminense": "FLU",
    "Botafogo FR": "BOT", "Botafogo": "BOT",
    "EC Bahia": "BAH", "Bahia": "BAH",
    "São Paulo FC": "SAO", "Sao Paulo": "SAO", "São Paulo": "SAO",
    "Grêmio FBPA": "GRE", "Gremio": "GRE", "Grêmio": "GRE",
    "Red Bull Bragantino": "RBB", "Bragantino": "RBB", "RB Bragantino": "RBB",
    "Clube Atlético Mineiro": "CAM", "Atlético Mineiro": "CAM", "CA Mineiro": "CAM", "Atletico-MG": "CAM", "Atlético-MG": "CAM",
    "Santos FC": "SAN", "Santos": "SAN",
    "SC Corinthians": "COR", "Corinthians": "COR", "SC Corinthians Paulista": "COR",
    "CR Vasco da Gama": "VAS", "Vasco da Gama": "VAS", "Vasco": "VAS",
    "EC Vitória": "VIT", "Vitoria": "VIT", "Vitória": "VIT",
    "SC Internacional": "INT", "Internacional": "INT",
    "Ceará SC": "CEA", "Ceara": "CEA", "Ceará": "CEA",
    "Fortaleza EC": "FOR", "Fortaleza": "FOR",
    "EC Juventude": "JUV", "Juventude": "JUV",
    "Sport Club do Recife": "SPO", "Sport Recife": "SPO", "Sport": "SPO",
    "Coritiba FC": "CFC", "Coritiba": "CFC",
    "EC Noroeste": "NOV", "Noroeste": "NOV",
    "América MG": "AME", "América Mineiro": "AME",
    "Cuiabá EC": "CUI", "Cuiaba": "CUI", "Cuiabá": "CUI",
    "Goiás EC": "GOI", "Goias": "GOI", "Goiás": "GOI",
    "Athletico Paranaense": "CAP", "Athletico-PR": "CAP", "CA Paranaense": "CAP",
    "Chapecoense AF": "CHA", "Chapecoense": "CHA",
    "Clube do Remo": "REM", "Remo": "REM",
    "Avaí FC": "AVA", "Avai": "AVA",
}


def _sigla_de(nome: str) -> str:
    if nome in SIGLAS_MAPA:
        return SIGLAS_MAPA[nome]
    for chave, sigla in SIGLAS_MAPA.items():
        if chave.lower() in nome.lower() or nome.lower() in chave.lower():
            return sigla
    return nome[:3].upper()


def _estado_de(sigla: str) -> str:
    estados: dict[str, str] = {
        "FLA": "RJ", "PAL": "SP", "CRU": "MG", "MIR": "SP", "FLU": "RJ",
        "BOT": "RJ", "BAH": "BA", "SAO": "SP", "GRE": "RS", "RBB": "SP",
        "CAM": "MG", "SAN": "SP", "COR": "SP", "VAS": "RJ", "VIT": "BA",
        "INT": "RS", "CEA": "CE", "FOR": "CE", "JUV": "RS", "SPO": "PE",
        "CFC": "PR", "AME": "MG", "CUI": "MT", "GOI": "GO", "CAP": "PR",
        "AVA": "SC", "CHA": "SC", "REM": "PA",
    }
    return estados.get(sigla.upper(), "??")


NOME_DISPLAY: dict[str, str] = {
    "CA Mineiro": "Atlético Mineiro",
    "Clube Atlético Mineiro": "Atlético Mineiro",
}


def buscar_classificacao(temporada: str = "2026") -> list[dict[str, Any]]:
    url = f"{API_BASE}/competitions/{COMPETITION}/standings?season={temporada}"
    data = _fetch(url)

    standings = data.get("standings") or []
    if not standings or not isinstance(standings[0].get("table"), list):
        raise ValueError("API retornou standings vazio ou invalido")
    table = standings[0]["table"]

    resultado = []
    for item in table:
        team = item["team"]
        nome = team["name"]
        nome_exibir = NOME_DISPLAY.get(nome, nome)
        sigla = _sigla_de(nome)
        jogos = item["playedGames"]
        vitorias = item["won"]
        empates = item["draw"]
        derrotas = item["lost"]
        gols_pro = item["goalsFor"]
        gols_contra = item["goalsAgainst"]
        pontos = item["points"]

        resultado.append({
            "posicao": item["position"],
            "time": nome_exibir,
            "sigla": sigla,
            "estado": _estado_de(sigla),
            "cor": _cor_padrao(sigla),
            "jogos": jogos,
            "vitorias": vitorias,
            "empates": empates,
            "derrotas": derrotas,
            "gols_pro": gols_pro,
            "gols_contra": gols_contra,
            "saldo": gols_pro - gols_contra,
            "pontos": pontos,
            "aproveitamento": round(pontos / (jogos * 3) * 100, 1) if jogos > 0 else 0.0,
        })

    return resultado


def buscar_artilharia(temporada: str = "2026", limite: int = 20) -> list[dict[str, Any]]:
    url = f"{API_BASE}/competitions/{COMPETITION}/scorers?season={temporada}&limit={limite}"
    data = _fetch(url)

    resultado = []
    for item in data.get("scorers", []):
        player = item["player"]
        team = item.get("team", {})
        team_name = team.get("name", "")
        team_name_exibir = NOME_DISPLAY.get(team_name, team_name)
        sigla = _sigla_de(team_name) if team_name else "???"

        posicao_map = {
            "Offence": "Atacante", "Midfield": "Meia",
            "Defence": "Defensor", "Goalkeeper": "Goleiro",
        }
        posicao_raw = player.get("section") or player.get("position") or ""
        posicao = posicao_map.get(posicao_raw, posicao_raw or "Atacante")

        gols = item.get("goals") or item.get("numberOfGoals") or 0

        resultado.append({
            "jogador": player.get("name", "Desconhecido"),
            "time": team_name_exibir,
            "sigla": sigla,
            "posicao": posicao,
            "gols": gols,
        })

    return resultado
