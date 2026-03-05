import json
import os

import pytest

from app import app as flask_app
import app as app_module


@pytest.fixture(autouse=True)
def _limpar_cache():
    app_module._dados_cache = None
    app_module._dados_mtime = 0.0
    yield
    app_module._dados_cache = None
    app_module._dados_mtime = 0.0


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


@pytest.fixture
def dados_json_validos():
    from gerar_dados import gerar_classificacao, gerar_artilharia, montar_info

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


class TestRotaTime:
    def test_time_existente_retorna_200(self, client):
        resp = client.get("/time/FLA")
        assert resp.status_code == 200
        assert b"Flamengo" in resp.data or b"FLA" in resp.data

    def test_time_inexistente_retorna_404(self, client):
        resp = client.get("/time/XXX")
        assert resp.status_code == 404
        assert b"nao encontrado" in resp.data.lower() or b"nao existe" in resp.data.lower()


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
        times_v1 = resp1.get_json()

        dados_json_validos["classificacao"][0]["time"] = "Alterado FC"
        dados_json_validos["info"]["lider"] = "Alterado FC"
        arquivo.write_text(json.dumps(dados_json_validos, ensure_ascii=False), encoding="utf-8")

        os.utime(str(arquivo), (arquivo.stat().st_mtime + 10, arquivo.stat().st_mtime + 10))

        resp2 = client.get("/api/classificacao")
        assert resp2.status_code == 200
        times_v2 = resp2.get_json()
        assert times_v2[0]["time"] == "Alterado FC"


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

        def fake_atualizar():
            pass

        import atualizar_dados as atu
        monkeypatch.setattr(atu, "atualizar", fake_atualizar)

        resp = client.post("/api/atualizar", headers={"Authorization": "Bearer segredo"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data.get("status") == "ok"
