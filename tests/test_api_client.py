import api_client
from temporada import temporada_brasileirao_atual


def test_busca_classificacao_prefere_tla_da_api(monkeypatch):
    payload = {
        "standings": [
            {
                "table": [
                    {
                        "position": 1,
                        "team": {"name": "Nome Variavel FC", "tla": "PAL", "crest": "https://example.com/pal.png"},
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
    monkeypatch.setattr(api_client, "_fetch", lambda url: payload)

    classificacao = api_client.buscar_classificacao()

    assert classificacao[0]["sigla"] == "PAL"
    assert classificacao[0]["estado"] == "SP"


def test_busca_classificacao_normaliza_tla_oficial_para_sigla_do_dashboard(monkeypatch):
    payload = {
        "standings": [
            {
                "table": [
                    {
                        "position": 1,
                        "team": {"name": "São Paulo FC", "tla": "PAU", "crest": "https://example.com/sp.png"},
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
    monkeypatch.setattr(api_client, "_fetch", lambda url: payload)

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
    capturado = {}

    def fake_fetch(url):
        capturado["url"] = url
        return {
            "standings": [
                {
                    "table": [
                        {
                            "position": 1,
                            "team": {"name": "Nome Variavel FC", "tla": "PAL", "crest": ""},
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

    monkeypatch.setattr(api_client, "_fetch", fake_fetch)

    api_client.buscar_classificacao()

    assert f"season={temporada_brasileirao_atual()}" in capturado["url"]
