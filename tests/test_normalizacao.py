import pytest

from dados_schema import DadosInvalidosError
from normalizacao import normalizar_dados_dashboard, normalizar_posicao_jogador


def test_normaliza_posicoes_em_ingles_para_portugues():
    assert normalizar_posicao_jogador("Centre-Forward") == "Centroavante"
    assert normalizar_posicao_jogador("Defensive Midfield") == "Volante"
    assert normalizar_posicao_jogador("Left Winger") == "Ponta esquerda"
    assert normalizar_posicao_jogador("Goalkeeper") == "Goleiro"


def test_mantem_posicao_ja_em_portugues():
    assert normalizar_posicao_jogador("Atacante") == "Atacante"


def test_normaliza_posicoes_adicionais_e_vazias():
    assert normalizar_posicao_jogador("Attacker") == "Atacante"
    assert normalizar_posicao_jogador("Midfielder") == "Meia"
    assert normalizar_posicao_jogador("") == "Nao informado"


def test_normaliza_artilharia_dentro_do_dashboard():
    dados = {
        "classificacao": [
            {"time": "B", "posicao": 2},
            {
                "time": "CA Paranaense",
                "sigla": "CAP",
                "estado": "SP",
                "posicao": 1,
                "escudo": "https://example.com/cap.png",
            },
        ],
        "artilharia": [
            {"jogador": "B", "posicao": "Defensive Midfield", "gols": 1},
            {"jogador": "A", "posicao": "Centre-Forward", "gols": 3},
        ],
        "info": {},
    }

    normalizar_dados_dashboard(dados)

    assert dados["classificacao"][0]["time"] == "Athletico Paranaense"
    assert dados["classificacao"][0]["estado"] == "PR"
    assert dados["classificacao"][0]["escudo"] == "static/img/escudos/normalizados/CAP.png"
    assert dados["classificacao"][1]["time"] == "B"
    assert dados["artilharia"][0]["posicao"] == "Centroavante"
    assert dados["artilharia"][1]["posicao"] == "Volante"
    assert dados["artilharia"][0]["jogador"] == "A"


def test_reconcilia_info_com_artilheiro_apos_ordenar_empate():
    dados = {
        "classificacao": [{"time": "Palmeiras", "sigla": "PAL", "posicao": 1}],
        "artilharia": [
            {"jogador": "Zeta", "sigla": "PAL", "time": "Palmeiras", "posicao": "Atacante", "gols": 3},
            {"jogador": "Alpha", "sigla": "PAL", "time": "Palmeiras", "posicao": "Atacante", "gols": 3},
        ],
        "info": {"artilheiro": "Zeta", "artilheiro_gols": 3},
    }

    normalizar_dados_dashboard(dados)

    assert dados["artilharia"][0]["jogador"] == "Alpha"
    assert dados["info"]["artilheiro"] == "Alpha"
    assert dados["info"]["artilheiro_gols"] == 3


def test_rejeita_forma_raiz_invalida_antes_de_normalizar():
    with pytest.raises(DadosInvalidosError, match="dados deve ser um objeto"):
        normalizar_dados_dashboard([])


def test_rejeita_item_de_lista_invalido_antes_de_normalizar():
    with pytest.raises(DadosInvalidosError, match=r"classificacao\[1\].*objeto"):
        normalizar_dados_dashboard({"classificacao": ["invalido"], "artilharia": [], "info": {}})


def test_normaliza_snapshot_preserva_rodada_e_calcula_faixa_de_jogos():
    dados = {
        "classificacao": [
            {"sigla": "PAL", "time": "Palmeiras", "estado": "SP", "jogos": 24, "posicao": 1},
            {"sigla": "FLA", "time": "Flamengo", "estado": "RJ", "jogos": 26, "posicao": 2},
        ],
        "artilharia": [],
        "info": {"rodada_atual": 26},
    }

    normalizar_dados_dashboard(dados)

    assert dados["info"]["rodada_atual"] == 26
    assert dados["info"]["rodada_confirmada"] is False
    assert dados["info"]["jogos_minimos"] == 24
    assert dados["info"]["jogos_maximos"] == 26


def test_normaliza_snapshot_antigo_com_defaults_de_agenda():
    dados = {
        "classificacao": [{"sigla": "PAL", "time": "Palmeiras", "estado": "SP", "jogos": 1, "posicao": 1}],
        "artilharia": [],
        "fonte": "CBF",
        "info": {"rodada_atual": 1},
    }

    normalizar_dados_dashboard(dados)

    assert dados["partidas"] == []
    assert dados["agenda_desatualizada"] is True
    assert dados["fontes"] == {
        "classificacao": "CBF",
        "artilharia": "CBF",
        "partidas": "Não disponível",
    }


def test_normaliza_ordem_das_partidas_por_rodada_data_e_id():
    dados = {
        "classificacao": [{"sigla": "PAL", "time": "Palmeiras", "estado": "SP", "jogos": 1, "posicao": 1}],
        "artilharia": [],
        "info": {"rodada_atual": 1},
        "partidas": [
            {"id": 3, "rodada": 2, "inicio_em": "2026-05-02T20:00:00Z"},
            {"id": 2, "rodada": 1, "inicio_em": "2026-04-26T20:00:00Z"},
            {"id": 1, "rodada": 1, "inicio_em": "2026-04-25T20:00:00Z"},
        ],
    }

    normalizar_dados_dashboard(dados)

    assert [partida["id"] for partida in dados["partidas"]] == [1, 2, 3]
