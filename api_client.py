"""
Cliente para buscar dados do Brasileirao via CBF e football-data.org v4.

football-data.org requer FOOTBALL_DATA_TOKEN quando usado como fallback.
Documentacao football-data: https://docs.football-data.org/general/v4/index.html
"""

import os
import urllib.request
import urllib.error
import json
import re
import time
from typing import Any

from club_assets import escudo_do_time
from env_config import carregar_env_local
from normalizacao import normalizar_posicao_jogador
from temporada import temporada_brasileirao_atual


carregar_env_local()


API_BASE = "https://api.football-data.org/v4"
COMPETITION = "BSA"
CBF_COMPETITION_URL = "https://www.cbf.com.br/futebol-brasileiro/tabelas/campeonato-brasileiro/serie-a/{temporada}?documento=IMT"
CBF_SCORERS_URL = "https://www.cbf.com.br/api/cbf/artilheiros/42/1/{temporada}/{pagina}"


def _get_token() -> str:
    token = os.environ.get("FOOTBALL_DATA_TOKEN", "").strip()
    if not token:
        raise EnvironmentError(
            "Variavel FOOTBALL_DATA_TOKEN nao definida. "
            "Cadastre-se em https://www.football-data.org/client/register e defina o token."
        )
    return token


def _fetch(url: str, tentativas: int = 3) -> dict[str, Any]:
    token = _get_token()
    req = urllib.request.Request(url, headers={"X-Auth-Token": token})
    for tentativa in range(1, tentativas + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            if e.code not in {429, 500, 502, 503, 504} or tentativa == tentativas:
                raise ConnectionError(f"API retornou HTTP {e.code}: {e.reason} - {body}") from e
        except urllib.error.URLError as e:
            if tentativa == tentativas:
                raise ConnectionError(f"Erro de conexao com a API: {e.reason}") from e
        time.sleep(2 ** (tentativa - 1))

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
    "Coritiba FBC": "CFC",
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

SIGLAS_OFICIAIS_MAPA: dict[str, str] = {
    "PAU": "SAO",
    "FBP": "GRE",
    "SCI": "INT",
    "CRE": "REM",
}


def _sigla_por_nome(nome: str) -> str | None:
    if nome in SIGLAS_MAPA:
        return SIGLAS_MAPA[nome]
    for chave, sigla in SIGLAS_MAPA.items():
        if chave.lower() in nome.lower() or nome.lower() in chave.lower():
            return sigla
    return None


def _sigla_de(nome: str) -> str:
    sigla = _sigla_por_nome(nome)
    if sigla:
        return sigla
    return nome[:3].upper()


def _normalizar_sigla_oficial(sigla: str) -> str:
    return SIGLAS_OFICIAIS_MAPA.get(sigla.upper(), sigla.upper())


def _sigla_do_time(team: dict[str, Any], nome: str) -> str:
    sigla_nome = _sigla_por_nome(nome)
    if sigla_nome:
        return sigla_nome

    tla = str(team.get("tla") or "").strip().upper()
    if 2 <= len(tla) <= 4 and tla.isascii() and tla.isalpha():
        return _normalizar_sigla_oficial(tla)
    return _sigla_de(nome)


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
    "Athletico Paranaense": "CA Paranaense",
    "Coritiba SAF": "Coritiba FBC",
    "Vasco da Gama Saf": "CR Vasco da Gama",
    "Palmeiras": "SE Palmeiras",
    "Flamengo": "CR Flamengo",
    "Fluminense": "Fluminense FC",
    "São Paulo": "São Paulo FC",
    "Santos": "Santos FC",
    "Grêmio": "Grêmio FBPA",
}


def _fetch_public(url: str, tentativas: int = 3) -> Any:
    req = urllib.request.Request(url, headers={"Accept": "application/json,text/html"})
    for tentativa in range(1, tentativas + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
                content_type = resp.headers.get("content-type", "")
            if "application/json" in content_type or body.lstrip().startswith("{"):
                return json.loads(body)
            return body
        except urllib.error.HTTPError as e:
            if e.code not in {429, 500, 502, 503, 504} or tentativa == tentativas:
                raise ConnectionError(f"CBF retornou HTTP {e.code}: {e.reason}") from e
        except urllib.error.URLError as e:
            if tentativa == tentativas:
                raise ConnectionError(f"Erro de conexao com a CBF: {e.reason}") from e
        time.sleep(2 ** (tentativa - 1))

    raise ConnectionError("Nao foi possivel buscar dados da CBF")


def _extrair_array_next(html: str, chave: str, marcador_final: str) -> list[dict[str, Any]]:
    padrao = rf'\\\"{chave}\\\":\[(.*?)\],\\\"{marcador_final}\\\"'
    match = re.search(padrao, html)
    if not match:
        raise ValueError(f"Payload da CBF nao contem '{chave}'")

    payload = "[" + match.group(1).replace('\\"', '"') + "]"
    data = json.loads(payload)
    if not isinstance(data, list):
        raise ValueError(f"Payload da CBF para '{chave}' nao e uma lista")
    return data


def _display_nome(nome: str) -> str:
    return NOME_DISPLAY.get(nome, nome)


def _nome_clube_cbf(nome: str) -> str:
    return re.sub(r"\s*-\s*[A-Z]{2}$", "", nome).strip()


def _normalizar_linha_cbf(item: dict[str, Any]) -> dict[str, Any]:
    nome = str(item["time"])
    nome_exibir = _display_nome(nome)
    sigla = _sigla_de(nome_exibir)
    jogos = int(item["jogos"])
    vitorias = int(item["vitorias"])
    empates = int(item["empates"])
    derrotas = int(item["derrotas"])
    gols_pro = int(item["gols_pro"])
    gols_contra = int(item["gols_contra"])
    pontos = int(item["pontos"])

    return {
        "posicao": int(item["posicao"]),
        "time": nome_exibir,
        "sigla": sigla,
        "estado": str(item.get("uf_time") or _estado_de(sigla)),
        "cor": _cor_padrao(sigla),
        "escudo": escudo_do_time(sigla, item.get("escudo")),
        "jogos": jogos,
        "vitorias": vitorias,
        "empates": empates,
        "derrotas": derrotas,
        "gols_pro": gols_pro,
        "gols_contra": gols_contra,
        "saldo": gols_pro - gols_contra,
        "pontos": pontos,
        "aproveitamento": round(pontos / (jogos * 3) * 100, 1) if jogos > 0 else 0.0,
    }


def buscar_classificacao_cbf(temporada: str | None = None) -> list[dict[str, Any]]:
    temporada = temporada or temporada_brasileirao_atual()
    html = _fetch_public(CBF_COMPETITION_URL.format(temporada=temporada))
    if not isinstance(html, str):
        raise ValueError("CBF retornou payload de classificacao invalido")

    tabela = _extrair_array_next(html, "data", "message")
    classificacao = [_normalizar_linha_cbf(item) for item in tabela if "cod_time" in item and "pontos" in item]
    if len(classificacao) != 20:
        raise ValueError("CBF retornou classificacao incompleta")
    return classificacao


def _normalizar_artilheiro_cbf(item: dict[str, Any]) -> dict[str, Any]:
    clube = item.get("clube") or {}
    nome_clube = _nome_clube_cbf(str(clube.get("nome") or ""))
    nome_exibir = _display_nome(nome_clube)
    sigla = _sigla_de(nome_exibir) if nome_exibir else "???"

    return {
        "jogador": item.get("apelido") or item.get("nome") or "Desconhecido",
        "time": nome_exibir,
        "sigla": sigla,
        "posicao": normalizar_posicao_jogador(None),
        "gols": int(item.get("gols") or 0),
    }


def buscar_artilharia_cbf(temporada: str | None = None, limite: int = 20) -> list[dict[str, Any]]:
    temporada = temporada or temporada_brasileirao_atual()
    artilheiros: list[dict[str, Any]] = []
    pagina = 1

    while len(artilheiros) < limite:
        data = _fetch_public(CBF_SCORERS_URL.format(temporada=temporada, pagina=pagina))
        if not isinstance(data, dict):
            raise ValueError("CBF retornou payload de artilharia invalido")

        atletas = data.get("atletas")
        if not isinstance(atletas, list) or not atletas:
            break

        artilheiros.extend(_normalizar_artilheiro_cbf(item) for item in atletas)
        meta = data.get("meta")
        meta_item = meta[0] if isinstance(meta, list) and meta else meta if isinstance(meta, dict) else {}
        total_paginas = int(meta_item.get("total") or pagina)
        if pagina >= total_paginas:
            break
        pagina += 1

    return artilheiros[:limite]


def _normalizar_linha_classificacao(item: dict[str, Any]) -> dict[str, Any]:
    team = item["team"]
    nome = team["name"]
    nome_exibir = NOME_DISPLAY.get(nome, nome)
    sigla = _sigla_do_time(team, nome)
    jogos = item["playedGames"]
    vitorias = item["won"]
    empates = item["draw"]
    derrotas = item["lost"]
    gols_pro = item["goalsFor"]
    gols_contra = item["goalsAgainst"]
    pontos = item["points"]

    return {
        "posicao": item["position"],
        "time": nome_exibir,
        "sigla": sigla,
        "estado": _estado_de(sigla),
        "cor": _cor_padrao(sigla),
        "escudo": escudo_do_time(sigla, team.get("crest")),
        "jogos": jogos,
        "vitorias": vitorias,
        "empates": empates,
        "derrotas": derrotas,
        "gols_pro": gols_pro,
        "gols_contra": gols_contra,
        "saldo": gols_pro - gols_contra,
        "pontos": pontos,
        "aproveitamento": round(pontos / (jogos * 3) * 100, 1) if jogos > 0 else 0.0,
    }


def _buscar_standings(temporada: str) -> list[dict[str, Any]]:
    url = f"{API_BASE}/competitions/{COMPETITION}/standings?season={temporada}"
    data = _fetch(url)

    standings = data.get("standings") or []
    if not standings or not isinstance(standings[0].get("table"), list):
        raise ValueError("API retornou standings vazio ou invalido")

    return standings[0]["table"]


def _buscar_partidas(temporada: str) -> list[dict[str, Any]]:
    url = f"{API_BASE}/competitions/{COMPETITION}/matches?season={temporada}"
    data = _fetch(url)
    matches = data.get("matches")
    if not isinstance(matches, list):
        raise ValueError("API retornou matches invalido")
    return matches


def _registrar_estatisticas_time(classificacao: dict[str, Any], gols_pro: int, gols_contra: int) -> None:
    classificacao["jogos"] += 1
    classificacao["gols_pro"] += gols_pro
    classificacao["gols_contra"] += gols_contra
    classificacao["saldo"] = classificacao["gols_pro"] - classificacao["gols_contra"]

    if gols_pro > gols_contra:
        classificacao["vitorias"] += 1
        classificacao["pontos"] += 3
    elif gols_pro == gols_contra:
        classificacao["empates"] += 1
        classificacao["pontos"] += 1
    else:
        classificacao["derrotas"] += 1

    jogos = classificacao["jogos"]
    pontos = classificacao["pontos"]
    classificacao["aproveitamento"] = round(pontos / (jogos * 3) * 100, 1) if jogos > 0 else 0.0


def _criar_base_time(team: dict[str, Any], posicao_inicial: int = 999) -> dict[str, Any]:
    nome = team["name"]
    nome_exibir = NOME_DISPLAY.get(nome, nome)
    sigla = _sigla_do_time(team, nome)

    return {
        "posicao": posicao_inicial,
        "time": nome_exibir,
        "sigla": sigla,
        "estado": _estado_de(sigla),
        "cor": _cor_padrao(sigla),
        "escudo": escudo_do_time(sigla, team.get("crest")),
        "jogos": 0,
        "vitorias": 0,
        "empates": 0,
        "derrotas": 0,
        "gols_pro": 0,
        "gols_contra": 0,
        "saldo": 0,
        "pontos": 0,
        "aproveitamento": 0.0,
        "_seed_posicao": posicao_inicial,
    }


def _classificacao_dos_jogos(
    tabela_standings: list[dict[str, Any]],
    partidas: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    classificacao_por_id: dict[int, dict[str, Any]] = {}
    classificacao_base = [_normalizar_linha_classificacao(item) for item in tabela_standings]

    for item in tabela_standings:
        team = item["team"]
        team_id = int(team["id"])
        base = _criar_base_time(team, posicao_inicial=item["position"])
        classificacao_por_id[team_id] = base

    partidas_finalizadas = [partida for partida in partidas if partida.get("status") == "FINISHED"]
    if not partidas_finalizadas:
        return classificacao_base

    for partida in partidas_finalizadas:
        home_team = partida["homeTeam"]
        away_team = partida["awayTeam"]
        home_id = int(home_team["id"])
        away_id = int(away_team["id"])

        if home_id not in classificacao_por_id:
            classificacao_por_id[home_id] = _criar_base_time(home_team)
        if away_id not in classificacao_por_id:
            classificacao_por_id[away_id] = _criar_base_time(away_team)

        placar = partida.get("score", {}).get("fullTime", {})
        gols_casa = placar.get("home")
        gols_fora = placar.get("away")
        if not isinstance(gols_casa, int) or not isinstance(gols_fora, int):
            raise ValueError("Partida finalizada possui placar ausente ou invalido")

        _registrar_estatisticas_time(classificacao_por_id[home_id], gols_casa, gols_fora)
        _registrar_estatisticas_time(classificacao_por_id[away_id], gols_fora, gols_casa)

    classificacao = list(classificacao_por_id.values())
    classificacao.sort(
        key=lambda time: (
            -time["pontos"],
            -time["vitorias"],
            -time["saldo"],
            -time["gols_pro"],
            time["_seed_posicao"],
            time["time"],
        )
    )

    for index, time in enumerate(classificacao, start=1):
        time["posicao"] = index
        time.pop("_seed_posicao", None)

    return classificacao


def buscar_classificacao(temporada: str | None = None) -> list[dict[str, Any]]:
    temporada = temporada or temporada_brasileirao_atual()
    tabela_standings = _buscar_standings(temporada)
    return [_normalizar_linha_classificacao(item) for item in tabela_standings]


def buscar_artilharia(temporada: str | None = None, limite: int = 20) -> list[dict[str, Any]]:
    temporada = temporada or temporada_brasileirao_atual()
    url = f"{API_BASE}/competitions/{COMPETITION}/scorers?season={temporada}&limit={limite}"
    data = _fetch(url)

    resultado = []
    for item in data.get("scorers", []):
        player = item["player"]
        team = item.get("team", {})
        team_name = team.get("name", "")
        team_name_exibir = NOME_DISPLAY.get(team_name, team_name)
        sigla = _sigla_do_time(team, team_name) if team_name else "???"

        posicao_raw = player.get("section") or player.get("position") or ""
        posicao = normalizar_posicao_jogador(posicao_raw)

        gols = item.get("goals") or item.get("numberOfGoals") or 0

        resultado.append({
            "jogador": player.get("name", "Desconhecido"),
            "time": team_name_exibir,
            "sigla": sigla,
            "posicao": posicao,
            "gols": gols,
        })

    return resultado
