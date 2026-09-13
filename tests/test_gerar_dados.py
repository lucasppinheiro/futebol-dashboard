import json

from gerar_dados import gerar_artilharia, gerar_classificacao, gerar_dados, montar_info


class TestGerarClassificacao:
    def test_retorna_20_times(self):
        resultado = gerar_classificacao()
        assert len(resultado) == 20

    def test_campos_calculados_presentes(self):
        resultado = gerar_classificacao()
        for time in resultado:
            assert "pontos" in time
            assert "saldo" in time
            assert "aproveitamento" in time

    def test_primeiro_tem_mais_pontos(self):
        resultado = gerar_classificacao()
        pontos = [t["pontos"] for t in resultado]
        assert pontos[0] == max(pontos)


class TestGerarArtilharia:
    def test_retorna_20_artilheiros(self):
        resultado = gerar_artilharia()
        assert len(resultado) == 20

    def test_ordenado_por_gols_decrescente(self):
        resultado = gerar_artilharia()
        gols = [j["gols"] for j in resultado]
        assert gols == sorted(gols, reverse=True)


class TestGerarDados:
    def test_gera_arquivo_json(self, tmp_path, monkeypatch):
        import gerar_dados as modulo

        arquivo = tmp_path / "brasileirao.json"
        monkeypatch.setattr(modulo, "DATA_DIR", str(tmp_path))
        monkeypatch.setattr(modulo, "OUTPUT_FILE", str(arquivo))

        gerar_dados()

        assert arquivo.exists()
        with open(arquivo, encoding="utf-8") as f:
            dados = json.load(f)
        assert "classificacao" in dados
        assert "artilharia" in dados
        assert "dados_atualizados_em" in dados
        assert "info" in dados
        assert dados["info"]["lider"] == dados["classificacao"][0]["time"]
        assert dados["info"]["artilheiro"] == dados["artilharia"][0]["jogador"]
        assert dados["fonte"] == "fixture"
        assert "dados_verificados_em" in dados


def test_montar_info_preserva_rodada_do_campeonato_separada_dos_jogos():
    classificacao = [
        {"time": "Palmeiras", "jogos": 24, "pontos": 48},
        {"time": "Flamengo", "jogos": 26, "pontos": 54},
    ]
    artilharia = [{"jogador": "Atacante", "gols": 10}]

    info = montar_info(classificacao, artilharia, "2026", rodada_atual=27)

    assert info["rodada_atual"] == 27
    assert info["rodada_confirmada"] is False
    assert info["jogos_minimos"] == 24
    assert info["jogos_maximos"] == 26
