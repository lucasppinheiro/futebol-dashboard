import copy
import pytest

from dados_schema import validar_dados_dashboard, DadosInvalidosError


@pytest.fixture
def dados_validos():
    from gerar_dados import gerar_classificacao, gerar_artilharia

    classificacao = gerar_classificacao()
    artilharia = gerar_artilharia()
    rodada_atual = max(t["jogos"] for t in classificacao)
    return {
        "classificacao": classificacao,
        "artilharia": artilharia,
        "info": {
            "campeonato": "Brasileirao Serie A",
            "temporada": "2025",
            "rodadas_total": 38,
            "rodada_atual": rodada_atual,
            "times_total": len(classificacao),
            "campeonato_finalizado": rodada_atual >= 38,
            "lider": classificacao[0]["time"],
            "lider_pontos": classificacao[0]["pontos"],
            "artilheiro": artilharia[0]["jogador"],
            "artilheiro_gols": artilharia[0]["gols"],
        },
    }


class TestValidacaoCompleta:
    def test_dados_validos_passam(self, dados_validos):
        resultado = validar_dados_dashboard(dados_validos)
        assert resultado is dados_validos

    def test_rejeita_tipo_invalido(self):
        with pytest.raises(DadosInvalidosError, match="deve ser um objeto"):
            validar_dados_dashboard([])

    def test_rejeita_bloco_ausente(self, dados_validos):
        del dados_validos["artilharia"]
        with pytest.raises(DadosInvalidosError, match="artilharia"):
            validar_dados_dashboard(dados_validos)


class TestClassificacao:
    def test_invariante_jogos(self, dados_validos):
        for time in dados_validos["classificacao"]:
            assert time["jogos"] == time["vitorias"] + time["empates"] + time["derrotas"]

    def test_invariante_pontos(self, dados_validos):
        for time in dados_validos["classificacao"]:
            assert time["pontos"] == time["vitorias"] * 3 + time["empates"]

    def test_invariante_saldo(self, dados_validos):
        for time in dados_validos["classificacao"]:
            assert time["saldo"] == time["gols_pro"] - time["gols_contra"]

    def test_posicoes_unicas(self, dados_validos):
        posicoes = [t["posicao"] for t in dados_validos["classificacao"]]
        assert len(posicoes) == len(set(posicoes))

    def test_rejeita_jogos_inconsistentes(self, dados_validos):
        dados_validos["classificacao"][0]["jogos"] = 99
        with pytest.raises(DadosInvalidosError, match="vitorias \\+ empates \\+ derrotas"):
            validar_dados_dashboard(dados_validos)

    def test_rejeita_pontos_inconsistentes(self, dados_validos):
        dados_validos["classificacao"][0]["pontos"] = 0
        with pytest.raises(DadosInvalidosError, match="vitorias\\*3 \\+ empates"):
            validar_dados_dashboard(dados_validos)

    def test_rejeita_saldo_inconsistente(self, dados_validos):
        dados_validos["classificacao"][0]["saldo"] = 999
        with pytest.raises(DadosInvalidosError, match="gols_pro - gols_contra"):
            validar_dados_dashboard(dados_validos)

    def test_rejeita_posicao_duplicada(self, dados_validos):
        dados_validos["classificacao"][1]["posicao"] = dados_validos["classificacao"][0]["posicao"]
        with pytest.raises(DadosInvalidosError, match="duplicada"):
            validar_dados_dashboard(dados_validos)

    def test_rejeita_classificacao_fora_de_ordem(self, dados_validos):
        dados_validos["classificacao"][0], dados_validos["classificacao"][1] = (
            dados_validos["classificacao"][1],
            dados_validos["classificacao"][0],
        )
        with pytest.raises(DadosInvalidosError, match="ordenada por posicao crescente"):
            validar_dados_dashboard(dados_validos)

    def test_rejeita_lista_vazia(self, dados_validos):
        dados_validos["classificacao"] = []
        with pytest.raises(DadosInvalidosError, match="nao vazia"):
            validar_dados_dashboard(dados_validos)

    def test_rejeita_campo_ausente(self, dados_validos):
        del dados_validos["classificacao"][0]["time"]
        with pytest.raises(DadosInvalidosError, match="campos ausentes"):
            validar_dados_dashboard(dados_validos)

    def test_rejeita_cor_invalida(self, dados_validos):
        dados_validos["classificacao"][0]["cor"] = "vermelho"
        with pytest.raises(DadosInvalidosError, match="hexadecimal"):
            validar_dados_dashboard(dados_validos)

    def test_rejeita_gols_negativos(self, dados_validos):
        dados_validos["classificacao"][0]["gols_pro"] = -1
        with pytest.raises(DadosInvalidosError, match="negativo"):
            validar_dados_dashboard(dados_validos)


class TestArtilharia:
    def test_rejeita_lista_vazia(self, dados_validos):
        dados_validos["artilharia"] = []
        with pytest.raises(DadosInvalidosError, match="nao vazia"):
            validar_dados_dashboard(dados_validos)

    def test_rejeita_gols_negativos(self, dados_validos):
        dados_validos["artilharia"][0]["gols"] = -5
        with pytest.raises(DadosInvalidosError, match="negativo"):
            validar_dados_dashboard(dados_validos)

    def test_rejeita_jogador_vazio(self, dados_validos):
        dados_validos["artilharia"][0]["jogador"] = ""
        with pytest.raises(DadosInvalidosError, match="texto nao vazio"):
            validar_dados_dashboard(dados_validos)

    def test_rejeita_artilharia_fora_de_ordem(self, dados_validos):
        dados_validos["artilharia"][0], dados_validos["artilharia"][1] = (
            dados_validos["artilharia"][1],
            dados_validos["artilharia"][0],
        )
        with pytest.raises(DadosInvalidosError, match="ordenada por gols decrescente"):
            validar_dados_dashboard(dados_validos)


class TestInfo:
    def test_rejeita_campeao_inconsistente(self, dados_validos):
        dados_validos["info"]["lider"] = "Time Falso"
        with pytest.raises(DadosInvalidosError, match="lider inconsistente"):
            validar_dados_dashboard(dados_validos)

    def test_rejeita_artilheiro_inconsistente(self, dados_validos):
        dados_validos["info"]["artilheiro"] = "Jogador Falso"
        with pytest.raises(DadosInvalidosError, match="artilheiro inconsistente"):
            validar_dados_dashboard(dados_validos)

    def test_rejeita_times_total_inconsistente(self, dados_validos):
        dados_validos["info"]["times_total"] = 10
        with pytest.raises(DadosInvalidosError, match="times_total inconsistente"):
            validar_dados_dashboard(dados_validos)

    def test_rejeita_rodada_maior_que_total(self, dados_validos):
        dados_validos["info"]["rodada_atual"] = dados_validos["info"]["rodadas_total"] + 1
        with pytest.raises(DadosInvalidosError, match="rodada_atual"):
            validar_dados_dashboard(dados_validos)

    def test_rejeita_finalizado_com_rodada_incompleta(self, dados_validos):
        dados_validos["info"]["campeonato_finalizado"] = True
        dados_validos["info"]["rodada_atual"] = max(1, dados_validos["info"]["rodadas_total"] - 1)
        with pytest.raises(DadosInvalidosError, match="campeonato_finalizado"):
            validar_dados_dashboard(dados_validos)
