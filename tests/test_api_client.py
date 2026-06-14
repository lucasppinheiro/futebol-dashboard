import json
import urllib.error

import pytest

import api_client
from temporada import temporada_brasileirao_atual


def test_busca_classificacao_prefere_tla_da_api(monkeypatch):
    standings_payload = {
        "standings": [
            {
                "table": [
                    {
                        "position": 1,
                        "team": {"id": 1, "name": "Nome Variavel FC", "tla": "PAL", "crest": "https://example.com/pal.png"},
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
                        "team": {"id": 1776, "name": "São Paulo FC", "tla": "PAU", "crest": "https://example.com/sp.png"},
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
                        "team": {"id": 1776, "name": "São Paulo FC", "tla": "PAU", "crest": "https://example.com/sp.png"},
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
                        "team": {"id": 1771, "name": "Cruzeiro EC", "tla": "CRU", "crest": "https://example.com/cru.png"},
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
