import json
import os

import pytest

import app as app_module
from app import app as flask_app


@pytest.fixture(autouse=True)
def _limpar_cache():
    app_module._dados_cache = None
    app_module._dados_mtime = 0.0
    app_module._ultimo_refresh_automatico = 0.0
    yield
    app_module._dados_cache = None
    app_module._dados_mtime = 0.0
    app_module._ultimo_refresh_automatico = 0.0


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


@pytest.fixture
def dados_json_validos():
    from gerar_dados import gerar_artilharia, gerar_classificacao, montar_info

    classificacao = gerar_classificacao()
    artilharia = gerar_artilharia()
    return {
        "classificacao": classificacao,
        "artilharia": artilharia,
        "info": montar_info(classificacao, artilharia, "2025"),
    }


class TestRotaWeb:
    def test_index_retorna_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Brasileir" in resp.data
        assert b"editorial-v2-production" in resp.data
        assert b"Dados atualizados em" in resp.data

    def test_prototipos_header_retorna_200(self, client):
        resp = client.get("/prototipos/header/")
        assert resp.status_code == 200
        assert b"Editorial de domingo" in resp.data
        assert b"Editorial v2" in resp.data
        assert b"Placar ao vivo" in resp.data
        assert b"Capa de revista" in resp.data

    def test_prototipo_editorial_em_largura_real_retorna_200(self, client):
        resp = client.get("/prototipos/header/editorial/")
        assert resp.status_code == 200
        assert b"Header editorial do Brasileir" in resp.data
        assert b"prototype-live-frame" in resp.data

    def test_prototipo_editorial_v2_em_largura_real_retorna_200(self, client):
        resp = client.get("/prototipos/header/editorial-v2/")
        assert resp.status_code == 200
        assert b"Header editorial v2" in resp.data
        assert b"editorial-v2-scoreboard" in resp.data

    def test_formata_data_de_atualizacao_salva_nos_dados(self):
        dados = {"dados_atualizados_em": "2026-08-10T02:35:34+00:00"}
        assert app_module.formatar_atualizacao_dados(dados) == "09/08/2026"


class TestRotaTime:
    def test_time_existente_retorna_200(self, client):
        resp = client.get("/time/FLA")
        assert resp.status_code == 200
        assert b"Flamengo" in resp.data or b"FLA" in resp.data

    def test_time_existente_com_barra_final_retorna_200(self, client):
        resp = client.get("/time/CAP/")
        assert resp.status_code == 200
        assert b"CAP" in resp.data or b"Paranaense" in resp.data

    def test_time_inexistente_retorna_404(self, client):
        resp = client.get("/time/XXX")
        assert resp.status_code == 404
        assert "Página não encontrada" in resp.get_data(as_text=True)

    def test_rota_inexistente_usa_pagina_404(self, client):
        resp = client.get("/rota-inexistente")
        assert resp.status_code == 404
        assert "Página não encontrada" in resp.get_data(as_text=True)


class TestAPIClassificacao:
    def test_retorna_json_lista(self, client):
        resp = client.get("/api/classificacao")
        assert resp.status_code == 200
        assert resp.content_type == "application/json"
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) == 20

    def test_campos_minimos(self, client):
        resp = client.get("/api/classificacao")
        time = resp.get_json()[0]
        campos = {"posicao", "time", "sigla", "pontos", "jogos", "vitorias", "empates", "derrotas"}
        assert campos.issubset(time.keys())


class TestAPIArtilharia:
    def test_retorna_json_lista(self, client):
        resp = client.get("/api/artilharia")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) == 20

    def test_campos_minimos(self, client):
        resp = client.get("/api/artilharia")
        jogador = resp.get_json()[0]
        campos = {"jogador", "time", "sigla", "gols"}
        assert campos.issubset(jogador.keys())

    def test_normaliza_posicoes_em_ingles_ao_carregar_json(self, client, monkeypatch, tmp_path, dados_json_validos):
        dados_json_validos["artilharia"][0]["posicao"] = "Centre-Forward"
        dados_json_validos["artilharia"][1]["posicao"] = "Defensive Midfield"
        arquivo = tmp_path / "dados_mistos.json"
        arquivo.write_text(json.dumps(dados_json_validos, ensure_ascii=False), encoding="utf-8")
        monkeypatch.setattr(app_module, "DATA_PATH", str(arquivo))

        resp = client.get("/api/artilharia")

        assert resp.status_code == 200
        data = resp.get_json()
        assert data[0]["posicao"] == "Centroavante"
        assert data[1]["posicao"] == "Volante"


class TestErros:
    def test_arquivo_ausente_api_retorna_json(self, client, monkeypatch, tmp_path):
        caminho_falso = str(tmp_path / "nao_existe.json")
        monkeypatch.setattr(app_module, "DATA_PATH", caminho_falso)
        resp = client.get("/api/classificacao")
        assert resp.status_code == 503
        data = resp.get_json()
        assert data["codigo"] == "DADOS_NAO_ENCONTRADOS"

    def test_arquivo_ausente_web_retorna_html(self, client, monkeypatch, tmp_path):
        caminho_falso = str(tmp_path / "nao_existe.json")
        monkeypatch.setattr(app_module, "DATA_PATH", caminho_falso)
        resp = client.get("/")
        assert resp.status_code == 503
        assert b"<h1>" in resp.data

    def test_json_invalido_api(self, client, monkeypatch, tmp_path):
        arquivo = tmp_path / "ruim.json"
        arquivo.write_text("{invalido", encoding="utf-8")
        monkeypatch.setattr(app_module, "DATA_PATH", str(arquivo))
        resp = client.get("/api/classificacao")
        assert resp.status_code == 500
        data = resp.get_json()
        assert data["codigo"] == "JSON_INVALIDO"

    def test_dados_invalidos_api(self, client, monkeypatch, tmp_path):
        arquivo = tmp_path / "vazio.json"
        arquivo.write_text('{"classificacao":[],"artilharia":[],"info":{}}', encoding="utf-8")
        monkeypatch.setattr(app_module, "DATA_PATH", str(arquivo))
        resp = client.get("/api/classificacao")
        assert resp.status_code == 500
        data = resp.get_json()
        assert data["codigo"] == "DADOS_INVALIDOS"


class TestCacheInvalidacao:
    def test_recarrega_quando_arquivo_muda(self, client, monkeypatch, tmp_path, dados_json_validos):
        arquivo = tmp_path / "dados.json"
        arquivo.write_text(json.dumps(dados_json_validos, ensure_ascii=False), encoding="utf-8")
        monkeypatch.setattr(app_module, "DATA_PATH", str(arquivo))

        resp1 = client.get("/api/classificacao")
        assert resp1.status_code == 200

        dados_json_validos["classificacao"][0]["cor"] = "#123456"
        arquivo.write_text(json.dumps(dados_json_validos, ensure_ascii=False), encoding="utf-8")

        os.utime(str(arquivo), (arquivo.stat().st_mtime + 10, arquivo.stat().st_mtime + 10))

        resp2 = client.get("/api/classificacao")
        assert resp2.status_code == 200
        times_v2 = resp2.get_json()
        assert times_v2[0]["cor"] == "#123456"

    def test_refresh_automatico_atualiza_arquivo_antigo(self, client, monkeypatch, tmp_path, dados_json_validos):
        arquivo = tmp_path / "dados.json"
        arquivo.write_text(json.dumps(dados_json_validos, ensure_ascii=False), encoding="utf-8")
        monkeypatch.setattr(app_module, "DATA_PATH", str(arquivo))
        monkeypatch.setenv("FOOTBALL_DATA_TOKEN", "token_teste")
        monkeypatch.setenv("DATA_AUTO_REFRESH_HOURS", "1")
        monkeypatch.setenv("DATA_AUTO_REFRESH_COOLDOWN_MINUTES", "0")

        dados_atualizados = json.loads(json.dumps(dados_json_validos))
        dados_atualizados["classificacao"][0]["cor"] = "#654321"
        os.utime(str(arquivo), (1, 1))

        def fake_atualizar(_temporada=None):
            arquivo.write_text(json.dumps(dados_atualizados, ensure_ascii=False), encoding="utf-8")
            os.utime(str(arquivo), None)

        import atualizar_dados as atu

        monkeypatch.setattr(atu, "atualizar", fake_atualizar)

        app_module.app.config["TESTING"] = False
        try:
            resp = client.get("/api/classificacao")
        finally:
            app_module.app.config["TESTING"] = True

        assert resp.status_code == 200
        assert resp.get_json()[0]["cor"] == "#654321"


class TestAPIAtualizar:
    def test_sem_token_retorna_501(self, client, monkeypatch):
        monkeypatch.delenv("API_UPDATE_TOKEN", raising=False)
        resp = client.post("/api/atualizar", headers={"Authorization": "Bearer "})
        assert resp.status_code == 501
        data = resp.get_json()
        assert data.get("codigo") == "NAO_CONFIGURADO"

    def test_token_errado_retorna_403(self, client, monkeypatch):
        monkeypatch.setenv("API_UPDATE_TOKEN", "segredo")
        resp = client.post("/api/atualizar", headers={"Authorization": "Bearer token_errado"})
        assert resp.status_code == 403
        data = resp.get_json()
        assert data.get("codigo") == "NAO_AUTORIZADO"

    def test_com_token_retorna_200(self, client, monkeypatch, tmp_path, dados_json_validos):
        arquivo = tmp_path / "dados.json"
        arquivo.write_text(json.dumps(dados_json_validos, ensure_ascii=False), encoding="utf-8")
        monkeypatch.setattr(app_module, "DATA_PATH", str(arquivo))
        monkeypatch.setenv("API_UPDATE_TOKEN", "segredo")

        def fake_atualizar(_temporada=None):
            pass

        import atualizar_dados as atu

        monkeypatch.setattr(atu, "atualizar", fake_atualizar)

        resp = client.post("/api/atualizar", headers={"Authorization": "Bearer segredo"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data.get("status") == "ok"


class TestAPIHealth:
    def test_health_indica_refresh_automatico_da_cbf_sem_token(self, client, monkeypatch):
        monkeypatch.setenv("DATA_SOURCE", "cbf")
        monkeypatch.delenv("FOOTBALL_DATA_TOKEN", raising=False)
        monkeypatch.setenv("DATA_AUTO_REFRESH_HOURS", "6")

        resp = client.get("/api/health")

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["refresh_automatico"] is True
        assert "temporada_padrao" in data

    def test_health_exige_token_apenas_para_football_data(self, client, monkeypatch):
        monkeypatch.setenv("DATA_SOURCE", "football-data")
        monkeypatch.delenv("FOOTBALL_DATA_TOKEN", raising=False)
        monkeypatch.setenv("DATA_AUTO_REFRESH_HOURS", "6")

        sem_token = client.get("/api/health").get_json()
        assert sem_token["refresh_automatico"] is False

        monkeypatch.setenv("FOOTBALL_DATA_TOKEN", "token_teste")
        com_token = client.get("/api/health").get_json()
        assert com_token["refresh_automatico"] is True
