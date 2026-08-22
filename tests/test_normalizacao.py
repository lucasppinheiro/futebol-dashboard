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
