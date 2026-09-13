import json
from datetime import datetime

import pytest

import atualizar_dados


@pytest.fixture(autouse=True)
def desativar_agenda_remota_por_padrao(monkeypatch):
    monkeypatch.delenv("FOOTBALL_DATA_TOKEN", raising=False)
    monkeypatch.setattr(atualizar_dados, "buscar_rodada_atual_cbf", lambda _: None, raising=False)


def test_atualizar_substitui_arquivo_atomicamente(monkeypatch, tmp_path):
    output = tmp_path / "brasileirao.json"
    output.write_text('{"original": true}', encoding="utf-8")
    classificacao = [
        {
            "posicao": 1,
            "time": "Palmeiras",
            "sigla": "PAL",
            "estado": "SP",
            "cor": "#006437",
            "escudo": "",
            "jogos": 1,
            "vitorias": 1,
            "empates": 0,
            "derrotas": 0,
            "gols_pro": 1,
            "gols_contra": 0,
            "saldo": 1,
            "pontos": 3,
            "aproveitamento": 100.0,
        }
    ]
    artilharia = [{"jogador": "Jogador", "time": "Palmeiras", "sigla": "PAL", "posicao": "Atacante", "gols": 1}]

    monkeypatch.setattr(atualizar_dados, "OUTPUT_FILE", str(output))
    monkeypatch.setattr(atualizar_dados, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(atualizar_dados, "buscar_classificacao_cbf", lambda _: classificacao)
    monkeypatch.setattr(atualizar_dados, "buscar_artilharia_cbf", lambda _: artilharia)

    atualizar_dados.atualizar("2026")

    dados = json.loads(output.read_text(encoding="utf-8"))
    assert dados["info"]["temporada"] == "2026"
    assert datetime.fromisoformat(dados["dados_atualizados_em"]).tzinfo is not None
    assert dados["fonte"] == "CBF"
    assert datetime.fromisoformat(dados["dados_verificados_em"]).tzinfo is not None
    assert list(tmp_path.glob("*.tmp")) == []


def test_atualizar_escreve_no_destino_informado(monkeypatch, tmp_path):
    destino = tmp_path / "custom" / "brasileirao.json"
    classificacao = [
        {
            "posicao": 1,
            "time": "Palmeiras",
            "sigla": "PAL",
            "estado": "SP",
            "cor": "#006437",
            "escudo": "",
            "jogos": 1,
            "vitorias": 1,
            "empates": 0,
            "derrotas": 0,
            "gols_pro": 1,
            "gols_contra": 0,
            "saldo": 1,
            "pontos": 3,
            "aproveitamento": 100.0,
        }
    ]
    artilharia = [{"jogador": "Jogador", "time": "Palmeiras", "sigla": "PAL", "posicao": "Atacante", "gols": 1}]

    monkeypatch.setattr(atualizar_dados, "OUTPUT_FILE", str(tmp_path / "padrao.json"))
    monkeypatch.setattr(atualizar_dados, "buscar_classificacao_cbf", lambda _: classificacao)
    monkeypatch.setattr(atualizar_dados, "buscar_artilharia_cbf", lambda _: artilharia)

    atualizar_dados.atualizar("2026", destino=destino)

    assert destino.exists()
    assert not (tmp_path / "padrao.json").exists()

    primeira_data = json.loads(destino.read_text(encoding="utf-8"))["dados_atualizados_em"]
    atualizar_dados.atualizar("2026", destino=destino)
    assert json.loads(destino.read_text(encoding="utf-8"))["dados_atualizados_em"] == primeira_data


def test_atualizar_preserva_timestamp_quando_dados_nao_mudam(monkeypatch, tmp_path):
    output = tmp_path / "brasileirao.json"
    classificacao = [
        {
            "posicao": 1,
            "time": "Palmeiras",
            "sigla": "PAL",
            "estado": "SP",
            "cor": "#006437",
            "escudo": "",
            "jogos": 1,
            "vitorias": 1,
            "empates": 0,
            "derrotas": 0,
            "gols_pro": 1,
            "gols_contra": 0,
            "saldo": 1,
            "pontos": 3,
            "aproveitamento": 100.0,
        }
    ]
    artilharia = [{"jogador": "Jogador", "time": "Palmeiras", "sigla": "PAL", "posicao": "Atacante", "gols": 1}]
    timestamp = "2026-08-10T02:35:34+00:00"
    dados_existentes = {
        "classificacao": classificacao,
        "artilharia": artilharia,
        "dados_atualizados_em": timestamp,
        "info": atualizar_dados.montar_info(classificacao, artilharia, "2026"),
    }
    output.write_text(json.dumps(dados_existentes), encoding="utf-8")

    monkeypatch.setattr(atualizar_dados, "OUTPUT_FILE", str(output))
    monkeypatch.setattr(atualizar_dados, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(atualizar_dados, "buscar_classificacao_cbf", lambda _: classificacao)
    monkeypatch.setattr(atualizar_dados, "buscar_artilharia_cbf", lambda _: artilharia)

    atualizar_dados.atualizar("2026")

    dados = json.loads(output.read_text(encoding="utf-8"))
    assert dados["dados_atualizados_em"] == timestamp


def test_atualizar_usa_football_data_como_fallback(monkeypatch, tmp_path):
    output = tmp_path / "brasileirao.json"
    classificacao = [
        {
            "posicao": 1,
            "time": "Palmeiras",
            "sigla": "PAL",
            "estado": "SP",
            "cor": "#006437",
            "escudo": "",
            "jogos": 1,
            "vitorias": 1,
            "empates": 0,
            "derrotas": 0,
            "gols_pro": 1,
            "gols_contra": 0,
            "saldo": 1,
            "pontos": 3,
            "aproveitamento": 100.0,
        }
    ]
    artilharia = [{"jogador": "Jogador", "time": "Palmeiras", "sigla": "PAL", "posicao": "Atacante", "gols": 1}]

    monkeypatch.setattr(atualizar_dados, "OUTPUT_FILE", str(output))
    monkeypatch.setattr(atualizar_dados, "DATA_DIR", str(tmp_path))

    def falhar_busca_cbf(_temporada):
        raise RuntimeError("cbf fora")

    monkeypatch.setattr(atualizar_dados, "buscar_classificacao_cbf", falhar_busca_cbf)
    monkeypatch.setattr(atualizar_dados, "buscar_artilharia_cbf", lambda _: [])
    monkeypatch.setattr(atualizar_dados, "buscar_classificacao", lambda _: classificacao)
    monkeypatch.setattr(atualizar_dados, "buscar_artilharia", lambda _: artilharia)

    atualizar_dados.atualizar("2026")

    dados = json.loads(output.read_text(encoding="utf-8"))
    assert dados["classificacao"][0]["sigla"] == "PAL"


def test_escrita_atomica_preserva_original_se_replace_falhar(monkeypatch, tmp_path):
    output = tmp_path / "brasileirao.json"
    output.write_text('{"original": true}', encoding="utf-8")
    monkeypatch.setattr(atualizar_dados.os, "replace", lambda *_: (_ for _ in ()).throw(OSError("falha")))

    with pytest.raises(OSError, match="falha"):
        atualizar_dados._escrever_json_atomico(output, {"novo": True})

    assert json.loads(output.read_text(encoding="utf-8")) == {"original": True}


def test_atualizar_enriquece_snapshot_e_prioriza_rodada_cbf(monkeypatch, tmp_path):
    output = tmp_path / "brasileirao.json"
    classificacao = [
        {
            "posicao": 1,
            "time": "Palmeiras",
            "sigla": "PAL",
            "estado": "SP",
            "cor": "#006437",
            "escudo": "",
            "jogos": 1,
            "vitorias": 1,
            "empates": 0,
            "derrotas": 0,
            "gols_pro": 1,
            "gols_contra": 0,
            "saldo": 1,
            "pontos": 3,
            "aproveitamento": 100.0,
        },
        {
            "posicao": 2,
            "time": "Flamengo",
            "sigla": "FLA",
            "estado": "RJ",
            "cor": "#E11D1D",
            "escudo": "",
            "jogos": 1,
            "vitorias": 0,
            "empates": 0,
            "derrotas": 1,
            "gols_pro": 0,
            "gols_contra": 1,
            "saldo": -1,
            "pontos": 0,
            "aproveitamento": 0.0,
        },
    ]
    artilharia = [{"jogador": "Jogador", "time": "Palmeiras", "sigla": "PAL", "posicao": "Atacante", "gols": 1}]
    partidas = [
        {
            "id": 77,
            "rodada": 1,
            "inicio_em": "2026-04-25T20:00:00Z",
            "status": "encerrada",
            "mandante": "PAL",
            "visitante": "FLA",
            "placar": {"mandante": 1, "visitante": 0},
        }
    ]
    monkeypatch.setenv("FOOTBALL_DATA_TOKEN", "token")
    monkeypatch.setattr(atualizar_dados, "buscar_classificacao_cbf", lambda _: classificacao)
    monkeypatch.setattr(atualizar_dados, "buscar_artilharia_cbf", lambda _: artilharia)
    monkeypatch.setattr(atualizar_dados, "buscar_rodada_atual_cbf", lambda _: 1)
    monkeypatch.setattr(atualizar_dados, "buscar_rodada_atual_football_data", lambda _: 2, raising=False)
    monkeypatch.setattr(atualizar_dados, "buscar_partidas", lambda _: partidas, raising=False)

    atualizar_dados.atualizar("2026", destino=output)

    dados = json.loads(output.read_text(encoding="utf-8"))
    assert dados["partidas"] == partidas
    assert dados["info"]["rodada_atual"] == 1
    assert dados["info"]["rodada_confirmada"] is True
    assert dados["fontes"] == {
        "classificacao": "CBF",
        "artilharia": "CBF",
        "partidas": "football-data.org",
    }
    assert dados["agenda_desatualizada"] is False
    assert datetime.fromisoformat(dados["agenda_atualizada_em"]).tzinfo is not None


def test_atualizar_preserva_agenda_anterior_quando_enriquecimento_falha(monkeypatch, tmp_path):
    output = tmp_path / "brasileirao.json"
    classificacao = [
        {
            "posicao": 1,
            "time": "Palmeiras",
            "sigla": "PAL",
            "estado": "SP",
            "cor": "#006437",
            "escudo": "",
            "jogos": 1,
            "vitorias": 1,
            "empates": 0,
            "derrotas": 0,
            "gols_pro": 1,
            "gols_contra": 0,
            "saldo": 1,
            "pontos": 3,
            "aproveitamento": 100.0,
        }
    ]
    artilharia = [{"jogador": "Jogador", "time": "Palmeiras", "sigla": "PAL", "posicao": "Atacante", "gols": 1}]
    partida_anterior = {
        "id": 77,
        "rodada": 1,
        "inicio_em": "2026-04-25T20:00:00Z",
        "status": "agendada",
        "mandante": "PAL",
        "visitante": "PAL",
        "placar": {"mandante": None, "visitante": None},
    }
    existentes = {
        "classificacao": classificacao,
        "artilharia": artilharia,
        "partidas": [partida_anterior],
        "agenda_atualizada_em": "2026-09-10T10:00:00+00:00",
        "fontes": {"classificacao": "CBF", "artilharia": "CBF", "partidas": "football-data.org"},
        "info": atualizar_dados.montar_info(classificacao, artilharia, "2026", rodada_atual=1),
    }
    output.write_text(json.dumps(existentes), encoding="utf-8")
    monkeypatch.setattr(atualizar_dados, "buscar_classificacao_cbf", lambda _: classificacao)
    monkeypatch.setattr(atualizar_dados, "buscar_artilharia_cbf", lambda _: artilharia)

    atualizar_dados.atualizar("2026", destino=output)

    dados = json.loads(output.read_text(encoding="utf-8"))
    assert dados["partidas"] == [partida_anterior]
    assert dados["agenda_atualizada_em"] == "2026-09-10T10:00:00+00:00"
    assert dados["agenda_desatualizada"] is True
    assert dados["fontes"]["partidas"] == "football-data.org"


def test_enriquecimento_descarta_agenda_com_clube_fora_da_classificacao(monkeypatch):
    agenda_salva = [
        {
            "id": 10,
            "rodada": 1,
            "inicio_em": "2026-04-25T20:00:00Z",
            "status": "agendada",
            "mandante": "PAL",
            "visitante": "FLA",
            "placar": {"mandante": None, "visitante": None},
        }
    ]
    monkeypatch.setenv("FOOTBALL_DATA_TOKEN", "token")
    monkeypatch.setattr(
        atualizar_dados,
        "buscar_partidas",
        lambda _: [{**agenda_salva[0], "visitante": "XYZ"}],
    )

    partidas, rodada, atualizado_em, desatualizada = atualizar_dados._enriquecer_agenda(
        "2026",
        {"partidas": agenda_salva, "agenda_atualizada_em": "2026-09-10T10:00:00+00:00"},
        {"PAL", "FLA"},
    )

    assert partidas == agenda_salva
    assert rodada is None
    assert atualizado_em == "2026-09-10T10:00:00+00:00"
    assert desatualizada is True


def test_enriquecimento_preserva_agenda_se_football_data_estiver_indisponivel(monkeypatch):
    agenda_salva = [
        {
            "id": 10,
            "rodada": 1,
            "inicio_em": "2026-04-25T20:00:00Z",
            "status": "agendada",
            "mandante": "PAL",
            "visitante": "FLA",
            "placar": {"mandante": None, "visitante": None},
        }
    ]
    monkeypatch.setenv("FOOTBALL_DATA_TOKEN", "token")
    monkeypatch.setattr(
        atualizar_dados,
        "buscar_partidas",
        lambda _: (_ for _ in ()).throw(ConnectionError("servico indisponivel")),
    )

    partidas, rodada, atualizado_em, desatualizada = atualizar_dados._enriquecer_agenda(
        "2026",
        {"partidas": agenda_salva, "agenda_atualizada_em": "2026-09-10T10:00:00+00:00"},
        {"PAL", "FLA"},
    )

    assert partidas == agenda_salva
    assert rodada is None
    assert atualizado_em == "2026-09-10T10:00:00+00:00"
    assert desatualizada is True


def test_enriquecimento_historico_busca_apenas_rodadas_ausentes_em_lote(monkeypatch):
    classificacao_atual = [{"sigla": "PAL", "pontos": 30}]
    rodada_um = [{"sigla": "PAL", "pontos": 3}]
    chamadas = []
    monkeypatch.setenv("FOOTBALL_DATA_TOKEN", "token")
    monkeypatch.setenv("HISTORICO_RODADAS_POR_ATUALIZACAO", "2")

    def buscar(_temporada, rodada):
        chamadas.append(rodada)
        return [{"sigla": "PAL", "pontos": rodada * 3}]

    monkeypatch.setattr(atualizar_dados, "buscar_classificacao_por_rodada", buscar)

    historico, atualizado_em, desatualizado = atualizar_dados._enriquecer_historico(
        "2026",
        {"classificacao_por_rodada": {"1": rodada_um}},
        classificacao_atual,
        rodada_atual=4,
    )

    assert chamadas == [2, 3]
    assert historico["1"] == rodada_um
    assert historico["2"][0]["pontos"] == 6
    assert historico["3"][0]["pontos"] == 9
    assert historico["4"] == classificacao_atual
    assert atualizado_em
    assert desatualizado is False


def test_enriquecimento_historico_sem_token_preserva_cache_e_marca_defasagem(monkeypatch):
    monkeypatch.delenv("FOOTBALL_DATA_TOKEN", raising=False)
    atual = [{"sigla": "PAL", "pontos": 30}]
    salvo = [{"sigla": "PAL", "pontos": 3}]

    historico, atualizado_em, desatualizado = atualizar_dados._enriquecer_historico(
        "2026",
        {
            "classificacao_por_rodada": {"1": salvo},
            "historico_atualizado_em": "2026-09-10T10:00:00+00:00",
        },
        atual,
        rodada_atual=4,
    )

    assert historico == {"1": salvo, "4": atual}
    assert atualizado_em == "2026-09-10T10:00:00+00:00"
    assert desatualizado is True


def test_enriquecimento_historico_revalida_rodada_que_tinha_jogo_suspenso(monkeypatch):
    atual = [{"sigla": "PAL", "pontos": 30}]
    rodada_antiga = [{"sigla": "PAL", "pontos": 4}]
    chamadas = []
    monkeypatch.setenv("FOOTBALL_DATA_TOKEN", "token")

    def buscar(_temporada, rodada):
        chamadas.append(rodada)
        return [{"sigla": "PAL", "pontos": 7}]

    monkeypatch.setattr(atualizar_dados, "buscar_classificacao_por_rodada", buscar)
    historico, _, desatualizado = atualizar_dados._enriquecer_historico(
        "2026",
        {
            "classificacao_por_rodada": {
                "1": [{"sigla": "PAL", "pontos": 3}],
                "2": rodada_antiga,
                "3": [{"sigla": "PAL", "pontos": 10}],
            },
            "partidas": [{"rodada": 2, "status": "suspensa"}],
        },
        atual,
        rodada_atual=4,
        partidas=[{"rodada": 2, "status": "encerrada"}],
    )

    assert chamadas == [2]
    assert historico["2"][0]["pontos"] == 7
    assert desatualizado is False


def test_enriquecimento_historico_prioriza_rodadas_ausentes_no_lote(monkeypatch):
    chamadas = []
    monkeypatch.setenv("FOOTBALL_DATA_TOKEN", "token")
    monkeypatch.setenv("HISTORICO_RODADAS_POR_ATUALIZACAO", "2")
    monkeypatch.setattr(
        atualizar_dados,
        "buscar_classificacao_por_rodada",
        lambda _temporada, rodada: chamadas.append(rodada) or [{"sigla": "PAL", "pontos": rodada * 3}],
    )
    historico_salvo = {str(rodada): [{"sigla": "PAL", "pontos": rodada * 3}] for rodada in range(1, 5)}
    pendentes = [{"rodada": rodada, "status": "adiada"} for rodada in range(1, 5)]

    historico, _, desatualizado = atualizar_dados._enriquecer_historico(
        "2026",
        {"classificacao_por_rodada": historico_salvo, "partidas": pendentes},
        [{"sigla": "PAL", "pontos": 21}],
        rodada_atual=7,
        partidas=pendentes,
    )

    assert chamadas == [5, 6]
    assert historico["5"][0]["pontos"] == 15
    assert historico["6"][0]["pontos"] == 18
    assert desatualizado is True


def test_atualizar_descarta_cache_de_outra_temporada(monkeypatch, tmp_path):
    destino = tmp_path / "brasileirao.json"
    classificacao = [
        {
            "posicao": 1,
            "time": "Palmeiras",
            "sigla": "PAL",
            "estado": "SP",
            "cor": "#006437",
            "escudo": "",
            "jogos": 1,
            "vitorias": 1,
            "empates": 0,
            "derrotas": 0,
            "gols_pro": 1,
            "gols_contra": 0,
            "saldo": 1,
            "pontos": 3,
            "aproveitamento": 100.0,
        }
    ]
    artilharia = [{"jogador": "Jogador", "time": "Palmeiras", "sigla": "PAL", "posicao": "Atacante", "gols": 1}]
    destino.write_text(
        json.dumps(
            {
                "info": {"temporada": "2025", "rodada_atual": 38},
                "partidas": [{"id": 1, "rodada": 38, "mandante": "FLA", "visitante": "BOT"}],
                "classificacao_por_rodada": {"38": [{"sigla": "FLA", "pontos": 80}]},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(atualizar_dados, "buscar_classificacao_cbf", lambda _: classificacao)
    monkeypatch.setattr(atualizar_dados, "buscar_artilharia_cbf", lambda _: artilharia)

    atualizar_dados.atualizar("2026", destino=destino)

    dados = json.loads(destino.read_text(encoding="utf-8"))
    assert dados["partidas"] == []
    assert dados["info"]["rodada_atual"] == 1
    assert dados["classificacao_por_rodada"] == {"1": classificacao}
