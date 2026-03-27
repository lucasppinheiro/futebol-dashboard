from normalizacao import normalizar_dados_dashboard, normalizar_posicao_jogador


def test_normaliza_posicoes_em_ingles_para_portugues():
    assert normalizar_posicao_jogador("Centre-Forward") == "Centroavante"
    assert normalizar_posicao_jogador("Defensive Midfield") == "Volante"
    assert normalizar_posicao_jogador("Left Winger") == "Ponta esquerda"
    assert normalizar_posicao_jogador("Goalkeeper") == "Goleiro"


def test_mantem_posicao_ja_em_portugues():
    assert normalizar_posicao_jogador("Atacante") == "Atacante"


def test_normaliza_artilharia_dentro_do_dashboard():
    dados = {
        "classificacao": [],
        "artilharia": [
            {"jogador": "A", "posicao": "Centre-Forward", "gols": 1},
            {"jogador": "B", "posicao": "Defensive Midfield", "gols": 1},
        ],
        "info": {},
    }

    normalizar_dados_dashboard(dados)

    assert dados["artilharia"][0]["posicao"] == "Centroavante"
    assert dados["artilharia"][1]["posicao"] == "Volante"
