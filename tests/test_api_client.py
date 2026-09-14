import json
import urllib.error

import pytest

import api_client
from temporada import temporada_brasileirao_atual


def test_extrair_classificacao_ge_combina_clubes_e_estatisticas():
    linhas = ",".join(
        "{"
        f'"ordem":{posicao},"nome_popular":"Time {posicao}","sigla":"T{posicao:02}",'
        f'"pontos":{60 - posicao},"jogos":27,"vitorias":10,"empates":5,"derrotas":12,'
        f'"gols_pro":{40 - posicao},"gols_contra":20,"saldo_gols":{20 - posicao}'
        "}"
        for posicao in range(1, 21)
    )
    html = f'<script>const classificacao = {{"classificacao":[{linhas}]}};</script>'

    classificacao = api_client.extrair_classificacao_ge(html)

    assert classificacao[0]["time"] == "Time 1"
    assert classificacao[0]["pontos"] == 59
    assert classificacao[0]["jogos"] == 27
    assert classificacao[0]["saldo"] == 19
    assert classificacao[-1]["posicao"] == 20


def _payload_next(chave, dados, marcador="message"):
    texto = json.dumps(dados, ensure_ascii=False).replace('"', '\\"')
    return f'<script>self.__next_f.push([1,"\\"{chave}\\":{texto},\\"{marcador}\\":\\"\\""])</script>'


def test_busca_classificacao_cbf_normaliza_tabela_oficial(monkeypatch):
    clubes = [
        ("Palmeiras", "SP"),
        ("Flamengo", "RJ"),
        ("Athletico Paranaense", "PR"),
        ("Fluminense", "RJ"),
        ("Bahia", "BA"),
        ("Red Bull Bragantino", "SP"),
        ("Cruzeiro", "MG"),
        ("Botafogo", "RJ"),
        ("Corinthians", "SP"),
        ("Atlético Mineiro", "MG"),
        ("Coritiba SAF", "PR"),
        ("São Paulo", "SP"),
        ("Vitória", "BA"),
        ("Mirassol", "SP"),
        ("Santos FC", "SP"),
        ("Internacional", "RS"),
        ("Grêmio", "RS"),
        ("Vasco da Gama Saf", "RJ"),
        ("Remo", "PA"),
        ("Chapecoense", "SC"),
    ]
    tabela = []
    for indice, (nome, uf) in enumerate(clubes, start=1):
        pontos = 48 - indice
        jogos = 21
        vitorias = max(1, pontos // 3)
        empates = pontos - (vitorias * 3)
        if nome == "Corinthians":
            pontos, jogos, vitorias, empates = 29, 21, 7, 8

        tabela.append(
            {
                "cod_time": str(20000 + indice),
                "uf_time": uf,
                "time": nome,
                "escudo": f"https://conteudo.cbf.com.br/clubes/{20000 + indice}/escudo.jpg",
                "posicao": str(indice),
                "pontos": str(pontos),
                "jogos": str(jogos),
                "vitorias": str(vitorias),
                "empates": str(empates),
                "derrotas": str(jogos - vitorias - empates),
                "gols_pro": "22",
                "gols_contra": "20",
            }
        )

    monkeypatch.setattr(api_client, "_fetch_public", lambda url: _payload_next("data", tabela))

    classificacao = api_client.buscar_classificacao_cbf("2026")
    corinthians = classificacao[8]

    assert corinthians["sigla"] == "COR"
    assert corinthians["pontos"] == 29
    assert corinthians["jogos"] == 21
    assert corinthians["aproveitamento"] == 46.0
    assert [(time["time"], time["estado"]) for time in classificacao] == clubes


def test_busca_artilharia_cbf_paginada(monkeypatch):
    def atleta(indice, gols):
        return {
            "id": str(indice),
            "gols": str(gols),
            "nome": f"Jogador {indice}",
            "apelido": f"Apelido {indice}",
            "clube": {"nome": "Flamengo-RJ"},
        }

    def fake_fetch_public(url):
        if url.endswith("/2"):
            return {"atletas": [atleta(i, 6) for i in range(11, 21)], "meta": [{"pagina": "2", "total": "2"}]}
        return {"atletas": [atleta(i, 12) for i in range(1, 11)], "meta": [{"pagina": "1", "total": "2"}]}

    monkeypatch.setattr(api_client, "_fetch_public", fake_fetch_public)

    artilharia = api_client.buscar_artilharia_cbf("2026", limite=20)

    assert len(artilharia) == 20
    assert artilharia[0]["jogador"] == "Apelido 1"
    assert artilharia[0]["sigla"] == "FLA"
    assert artilharia[0]["time"] == "Flamengo"


def test_busca_classificacao_prefere_tla_da_api(monkeypatch):
    standings_payload = {
        "standings": [
            {
                "table": [
                    {
                        "position": 1,
                        "team": {
                            "id": 1,
                            "name": "Nome Variavel FC",
                            "tla": "PAL",
                            "crest": "https://example.com/pal.png",
                        },
                        "playedGames": 1,
                        "won": 1,
                        "draw": 0,
                        "lost": 0,
                        "goalsFor": 2,
                        "goalsAgainst": 0,
                        "points": 3,
                    }
                ]
            }
        ]
    }
    matches_payload = {"matches": []}

    def fake_fetch(url):
        if "standings" in url:
            return standings_payload
        return matches_payload

    monkeypatch.setattr(api_client, "_fetch", fake_fetch)

    classificacao = api_client.buscar_classificacao()

    assert classificacao[0]["sigla"] == "PAL"
    assert classificacao[0]["estado"] == "SP"


def test_busca_classificacao_normaliza_tla_oficial_para_sigla_do_dashboard(monkeypatch):
    standings_payload = {
        "standings": [
            {
                "table": [
                    {
                        "position": 1,
                        "team": {
                            "id": 1776,
                            "name": "São Paulo FC",
                            "tla": "PAU",
                            "crest": "https://example.com/sp.png",
                        },
                        "playedGames": 1,
                        "won": 1,
                        "draw": 0,
                        "lost": 0,
                        "goalsFor": 2,
                        "goalsAgainst": 0,
                        "points": 3,
                    }
                ]
            }
        ]
    }
    matches_payload = {"matches": []}

    def fake_fetch(url):
        if "standings" in url:
            return standings_payload
        return matches_payload

    monkeypatch.setattr(api_client, "_fetch", fake_fetch)

    classificacao = api_client.buscar_classificacao()

    assert classificacao[0]["sigla"] == "SAO"
    assert classificacao[0]["estado"] == "SP"


def test_busca_classificacao_usa_escudo_local_do_athletico(monkeypatch):
    standings_payload = {
        "standings": [
            {
                "table": [
                    {
                        "position": 1,
                        "team": {
                            "id": 1768,
                            "name": "CA Paranaense",
                            "tla": "CAP",
                            "crest": "https://example.com/api-cap.png",
                        },
                        "playedGames": 1,
                        "won": 1,
                        "draw": 0,
                        "lost": 0,
                        "goalsFor": 2,
                        "goalsAgainst": 0,
                        "points": 3,
                    }
                ]
            }
        ]
    }
    matches_payload = {"matches": []}

    def fake_fetch(url):
        if "standings" in url:
            return standings_payload
        return matches_payload

    monkeypatch.setattr(api_client, "_fetch", fake_fetch)

    classificacao = api_client.buscar_classificacao()

    assert classificacao[0]["sigla"] == "CAP"
    assert classificacao[0]["escudo"] == "static/img/escudos/normalizados/CAP.png"


def test_busca_artilharia_normaliza_posicao_e_preserva_nao_informado(monkeypatch):
    payload = {
        "scorers": [
            {
                "player": {"name": "Jogador A", "position": "Attacker"},
                "team": {"name": "Nome Variavel FC", "tla": "PAL"},
                "goals": 5,
            },
            {
                "player": {"name": "Jogador B"},
                "team": {"name": "Nome Variavel FC", "tla": "PAL"},
                "goals": 3,
            },
        ]
    }
    monkeypatch.setattr(api_client, "_fetch", lambda url: payload)

    artilharia = api_client.buscar_artilharia()

    assert artilharia[0]["sigla"] == "PAL"
    assert artilharia[0]["posicao"] == "Atacante"
    assert artilharia[1]["posicao"] == "Nao informado"


def test_busca_classificacao_usa_temporada_atual_por_padrao(monkeypatch):
    urls = []

    def fake_fetch(url):
        urls.append(url)
        if "standings" in url:
            return {
                "standings": [
                    {
                        "table": [
                            {
                                "position": 1,
                                "team": {"id": 1, "name": "Nome Variavel FC", "tla": "PAL", "crest": ""},
                                "playedGames": 1,
                                "won": 1,
                                "draw": 0,
                                "lost": 0,
                                "goalsFor": 1,
                                "goalsAgainst": 0,
                                "points": 3,
                            }
                        ]
                    }
                ]
            }
        return {"matches": []}

    monkeypatch.setattr(api_client, "_fetch", fake_fetch)

    api_client.buscar_classificacao()

    assert urls
    assert all(f"season={temporada_brasileirao_atual()}" in url for url in urls)


def test_busca_classificacao_preserva_tabela_oficial(monkeypatch):
    standings_payload = {
        "standings": [
            {
                "table": [
                    {
                        "position": 1,
                        "team": {
                            "id": 1776,
                            "name": "São Paulo FC",
                            "tla": "PAU",
                            "crest": "https://example.com/sp.png",
                        },
                        "playedGames": 9,
                        "won": 5,
                        "draw": 2,
                        "lost": 2,
                        "goalsFor": 15,
                        "goalsAgainst": 9,
                        "points": 17,
                    },
                    {
                        "position": 2,
                        "team": {
                            "id": 1771,
                            "name": "Cruzeiro EC",
                            "tla": "CRU",
                            "crest": "https://example.com/cru.png",
                        },
                        "playedGames": 9,
                        "won": 5,
                        "draw": 1,
                        "lost": 3,
                        "goalsFor": 11,
                        "goalsAgainst": 8,
                        "points": 16,
                    },
                ]
            }
        ]
    }
    matches_payload = {
        "matches": [
            {
                "status": "FINISHED",
                "matchday": 10,
                "homeTeam": {"id": 1776, "name": "São Paulo FC", "tla": "PAU", "crest": "https://example.com/sp.png"},
                "awayTeam": {"id": 1771, "name": "Cruzeiro EC", "tla": "CRU", "crest": "https://example.com/cru.png"},
                "score": {"fullTime": {"home": 4, "away": 1}},
            }
        ]
    }

    def fake_fetch(url):
        if "standings" in url:
            return standings_payload
        return matches_payload

    monkeypatch.setattr(api_client, "_fetch", fake_fetch)

    classificacao = api_client.buscar_classificacao("2026")

    assert classificacao[0]["sigla"] == "SAO"
    assert classificacao[0]["jogos"] == 9
    assert classificacao[0]["pontos"] == 17
    assert classificacao[0]["gols_pro"] == 15
    assert classificacao[0]["gols_contra"] == 9
    assert classificacao[1]["sigla"] == "CRU"
    assert classificacao[1]["derrotas"] == 3


def test_busca_classificacao_prefere_mapeamento_por_nome_quando_tla_colide(monkeypatch):
    standings_payload = {
        "standings": [
            {
                "table": [
                    {
                        "position": 1,
                        "team": {"id": 4241, "name": "Coritiba FBC", "tla": "COR", "crest": ""},
                        "playedGames": 9,
                        "won": 4,
                        "draw": 2,
                        "lost": 3,
                        "goalsFor": 10,
                        "goalsAgainst": 9,
                        "points": 14,
                    },
                    {
                        "position": 2,
                        "team": {"id": 1777, "name": "SC Corinthians Paulista", "tla": "COR", "crest": ""},
                        "playedGames": 9,
                        "won": 4,
                        "draw": 1,
                        "lost": 4,
                        "goalsFor": 11,
                        "goalsAgainst": 11,
                        "points": 13,
                    },
                ]
            }
        ]
    }
    matches_payload = {"matches": []}

    def fake_fetch(url):
        if "standings" in url:
            return standings_payload
        return matches_payload

    monkeypatch.setattr(api_client, "_fetch", fake_fetch)

    classificacao = api_client.buscar_classificacao("2026")

    assert classificacao[0]["sigla"] == "CFC"
    assert classificacao[0]["estado"] == "PR"
    assert classificacao[1]["sigla"] == "COR"
    assert classificacao[1]["estado"] == "SP"


def test_fetch_repete_erro_transitorio_antes_de_retornar(monkeypatch):
    tentativas = 0

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return json.dumps({"standings": []}).encode()

    def fake_urlopen(*args, **kwargs):
        nonlocal tentativas
        tentativas += 1
        if tentativas < 3:
            raise urllib.error.URLError("temporario")
        return FakeResponse()

    monkeypatch.setenv("FOOTBALL_DATA_TOKEN", "teste")
    monkeypatch.setattr(api_client.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(api_client.time, "sleep", lambda _: None)

    assert api_client._fetch("https://example.com") == {"standings": []}
    assert tentativas == 3


def test_classificacao_dos_jogos_rejeita_placar_ausente():
    standings = [
        {
            "position": 1,
            "team": {"id": 1, "name": "Palmeiras", "tla": "PAL", "crest": ""},
            "playedGames": 0,
            "won": 0,
            "draw": 0,
            "lost": 0,
            "goalsFor": 0,
            "goalsAgainst": 0,
            "points": 0,
        }
    ]
    partidas = [
        {
            "status": "FINISHED",
            "homeTeam": {"id": 1, "name": "Palmeiras", "tla": "PAL", "crest": ""},
            "awayTeam": {"id": 2, "name": "Santos", "tla": "SAN", "crest": ""},
            "score": {"fullTime": {"home": None, "away": 1}},
        }
    ]

    with pytest.raises(ValueError, match="placar"):
        api_client._classificacao_dos_jogos(standings, partidas)


@pytest.mark.parametrize(
    ("status_externo", "status_esperado"),
    [
        ("SCHEDULED", "agendada"),
        ("TIMED", "agendada"),
        ("IN_PLAY", "em_andamento"),
        ("PAUSED", "intervalo"),
        ("FINISHED", "encerrada"),
        ("AWARDED", "encerrada"),
        ("POSTPONED", "adiada"),
        ("SUSPENDED", "suspensa"),
        ("CANCELLED", "cancelada"),
    ],
)
def test_normaliza_status_de_partida(status_externo, status_esperado):
    assert api_client.normalizar_status_partida(status_externo) == status_esperado


def test_normaliza_partida_football_data_para_contrato_publico():
    partida = api_client.normalizar_partida_football_data(
        {
            "id": 987,
            "matchday": 27,
            "utcDate": "2026-09-12T22:30:00Z",
            "status": "FINISHED",
            "homeTeam": {"id": 1, "name": "Flamengo", "tla": "FLA"},
            "awayTeam": {"id": 2, "name": "SE Palmeiras", "tla": "PAL"},
            "score": {"fullTime": {"home": 2, "away": 1}},
        }
    )

    assert partida == {
        "id": 987,
        "rodada": 27,
        "inicio_em": "2026-09-12T22:30:00Z",
        "status": "encerrada",
        "mandante": "FLA",
        "visitante": "PAL",
        "placar": {"mandante": 2, "visitante": 1},
    }


def test_extrai_configuracao_e_normaliza_partida_ge():
    html = """
      <script>
        const contentResource = { tUUID: "abc-123", esporte: "futebol" }
        const fase = {"slug":"fase-unica-campeonato-brasileiro-2026"};
      </script>
    """
    assert api_client.extrair_configuracao_ge(html) == (
        "abc-123",
        "fase-unica-campeonato-brasileiro-2026",
    )

    partida = api_client.normalizar_partida_ge(
        {
            "id": 10,
            "data_realizacao": "2026-09-13T17:30",
            "jogo_ja_comecou": True,
            "placar_oficial_mandante": 2,
            "placar_oficial_visitante": 1,
            "equipes": {
                "mandante": {"nome_popular": "Flamengo", "sigla": "FLA"},
                "visitante": {"nome_popular": "Corinthians", "sigla": "COR"},
            },
            "transmissao": {"broadcast": {"id": "ENCERRADA"}},
        },
        27,
    )

    assert partida == {
        "id": 10,
        "rodada": 27,
        "inicio_em": "2026-09-13T20:30:00Z",
        "status": "encerrada",
        "mandante": "FLA",
        "visitante": "COR",
        "placar": {"mandante": 2, "visitante": 1},
    }


def test_buscar_partidas_ge_ignora_confronto_ainda_sem_data(monkeypatch):
    html = 'tUUID: "abc"; const fase = {"slug":"fase-2026"};'
    agendada = {
        "id": 1,
        "data_realizacao": "2026-01-28T19:00",
        "jogo_ja_comecou": False,
        "placar_oficial_mandante": None,
        "placar_oficial_visitante": None,
        "equipes": {
            "mandante": {"nome_popular": "Flamengo", "sigla": "FLA"},
            "visitante": {"nome_popular": "Palmeiras", "sigla": "PAL"},
        },
        "transmissao": {"broadcast": {"id": "PRE_DIA"}},
    }
    sem_data = {**agendada, "id": 2, "data_realizacao": None}

    def fake_fetch(url):
        if url == api_client.GE_COMPETITION_URL:
            return html
        return [agendada, sem_data] if "/rodada/1/" in url else []

    monkeypatch.setattr(api_client, "_fetch_public", fake_fetch)

    assert [partida["id"] for partida in api_client.buscar_partidas_ge("2026")] == [1]


def test_buscar_partidas_normaliza_e_ordena(monkeypatch):
    partidas = [
        {
            "id": 2,
            "matchday": 2,
            "utcDate": "2026-05-02T20:00:00Z",
            "status": "TIMED",
            "homeTeam": {"name": "Palmeiras", "tla": "PAL"},
            "awayTeam": {"name": "Flamengo", "tla": "FLA"},
            "score": {"fullTime": {"home": None, "away": None}},
        },
        {
            "id": 1,
            "matchday": 1,
            "utcDate": "2026-04-25T20:00:00Z",
            "status": "FINISHED",
            "homeTeam": {"name": "Flamengo", "tla": "FLA"},
            "awayTeam": {"name": "Palmeiras", "tla": "PAL"},
            "score": {"fullTime": {"home": 1, "away": 1}},
        },
    ]
    monkeypatch.setattr(api_client, "_buscar_partidas", lambda _: partidas)

    resultado = api_client.buscar_partidas("2026")

    assert [partida["id"] for partida in resultado] == [1, 2]


def test_extrai_rodada_atual_da_pagina_cbf():
    html = '<script>self.__next_f.push([1,"\\"rodada_atual\\":27,\\"message\\":\\"\\""])</script>'

    assert api_client.extrair_rodada_atual_cbf(html) == 27


def test_extrai_rodada_atual_de_rotulo_visivel_cbf():
    assert api_client.extrair_rodada_atual_cbf("<span>Rodada:</span><strong>18</strong>") == 18


def test_extrai_rodada_selecionada_sem_confundir_lista_de_opcoes_cbf():
    html = """
        <select>
            <option value="38">Rodada <!-- -->38</option>
            <option value="27">Rodada <!-- -->27</option>
            <option value="26" selected="">Rodada <!-- -->26</option>
        </select>
    """

    assert api_client.extrair_rodada_atual_cbf(html) == 26


def test_buscar_rodada_atual_football_data(monkeypatch):
    monkeypatch.setattr(api_client, "_fetch", lambda _: {"currentSeason": {"currentMatchday": 27}})

    assert api_client.buscar_rodada_atual_football_data("2026") == 27


def test_buscar_classificacao_por_rodada_inclui_matchday_e_normaliza(monkeypatch):
    chamadas = []

    def fake_fetch(url):
        chamadas.append(url)
        return {
            "standings": [
                {
                    "type": "TOTAL",
                    "table": [
                        {
                            "position": 1,
                            "team": {"id": 1, "name": "Palmeiras", "tla": "PAL", "crest": ""},
                            "playedGames": 10,
                            "won": 7,
                            "draw": 2,
                            "lost": 1,
                            "goalsFor": 20,
                            "goalsAgainst": 8,
                            "points": 23,
                        }
                    ],
                }
            ]
        }

    monkeypatch.setattr(api_client, "_fetch", fake_fetch)

    classificacao = api_client.buscar_classificacao_por_rodada("2026", 10)

    assert chamadas == ["https://api.football-data.org/v4/competitions/BSA/standings?season=2026&matchday=10"]
    assert classificacao[0]["sigla"] == "PAL"
    assert classificacao[0]["pontos"] == 23


@pytest.mark.parametrize("rodada", [0, 39, True, "10"])
def test_buscar_classificacao_por_rodada_rejeita_rodada_invalida(rodada):
    with pytest.raises(ValueError, match="rodada"):
        api_client.buscar_classificacao_por_rodada("2026", rodada)
