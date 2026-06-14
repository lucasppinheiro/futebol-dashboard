import json

import pytest

import atualizar_dados


def test_atualizar_substitui_arquivo_atomicamente(monkeypatch, tmp_path):
    output = tmp_path / "brasileirao.json"
    output.write_text('{"original": true}', encoding="utf-8")
    classificacao = [
        {
            "posicao": 1, "time": "Palmeiras", "sigla": "PAL", "estado": "SP",
            "cor": "#006437", "escudo": "", "jogos": 1, "vitorias": 1,
            "empates": 0, "derrotas": 0, "gols_pro": 1, "gols_contra": 0,
            "saldo": 1, "pontos": 3, "aproveitamento": 100.0,
        }
    ]
    artilharia = [{"jogador": "Jogador", "time": "Palmeiras", "sigla": "PAL", "posicao": "Atacante", "gols": 1}]

    monkeypatch.setattr(atualizar_dados, "OUTPUT_FILE", str(output))
    monkeypatch.setattr(atualizar_dados, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(atualizar_dados, "buscar_classificacao", lambda _: classificacao)
    monkeypatch.setattr(atualizar_dados, "buscar_artilharia", lambda _: artilharia)

    atualizar_dados.atualizar("2026")

    assert json.loads(output.read_text(encoding="utf-8"))["info"]["temporada"] == "2026"
    assert list(tmp_path.glob("*.tmp")) == []


def test_escrita_atomica_preserva_original_se_replace_falhar(monkeypatch, tmp_path):
    output = tmp_path / "brasileirao.json"
    output.write_text('{"original": true}', encoding="utf-8")
    monkeypatch.setattr(atualizar_dados.os, "replace", lambda *_: (_ for _ in ()).throw(OSError("falha")))

    with pytest.raises(OSError, match="falha"):
        atualizar_dados._escrever_json_atomico(output, {"novo": True})

    assert json.loads(output.read_text(encoding="utf-8")) == {"original": True}
