import json
import os
import threading
from copy import deepcopy
from pathlib import Path

import pytest

import app as app_module
from app import app as flask_app


@pytest.fixture(autouse=True)
def _limpar_cache(monkeypatch):
    for thread in list(getattr(app_module, "_refresh_threads", ())):
        thread.join(timeout=5)
    app_module._dados_cache = None
    app_module._ultimo_refresh_automatico = 0.0
    if hasattr(app_module, "_dados_cache_chave"):
        app_module._dados_cache_chave = None
    if hasattr(app_module, "_refresh_em_andamento"):
        app_module._refresh_em_andamento = False
    yield
    for thread in list(getattr(app_module, "_refresh_threads", ())):
        thread.join(timeout=5)
    app_module._dados_cache = None
    app_module._ultimo_refresh_automatico = 0.0
    if hasattr(app_module, "_dados_cache_chave"):
        app_module._dados_cache_chave = None
    if hasattr(app_module, "_refresh_em_andamento"):
        app_module._refresh_em_andamento = False


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
    def test_debug_desligado_por_padrao_mas_ativavel_explicitamente(self, monkeypatch):
        monkeypatch.delenv("FLASK_DEBUG", raising=False)
        assert app_module._flask_debug_habilitado() is False

        monkeypatch.setenv("FLASK_DEBUG", "1")
        assert app_module._flask_debug_habilitado() is True

    @pytest.mark.parametrize("rota", ["/", "/time/FLA"])
    def test_artilharia_nao_exibe_posicao_tatica_do_jogador(self, client, rota):
        resp = client.get(rota)

        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert 'class="scorer-position"' not in html

    def test_index_retorna_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Brasileir" in resp.data
        assert b"site-header" in resp.data
        assert b"Jogos da Rodada" in resp.data
        assert b"Dados atualizados em" in resp.data

    def test_index_identifica_dinamicamente_a_fonte_da_classificacao(self, client):
        dados = app_module.carregar_dados()
        fonte_classificacao = dados["fontes"]["classificacao"]
        fonte_artilharia = dados["fontes"]["artilharia"]
        rodada = dados["info"]["rodada_atual"]
        html = client.get("/").get_data(as_text=True)

        assert "A classificação consolidada, com busca, filtros e ordenação." in html
        assert f'id="standings-source">{fonte_classificacao} · rodada {rodada}' in html
        assert f"Classificação: {fonte_classificacao}. Artilharia: {fonte_artilharia}." in html

    def test_index_usa_leitura_continua_sem_paineis_de_abas(self, client):
        html = client.get("/").get_data(as_text=True)

        for section_id in ("rodada", "classificacao", "artilharia", "desempenho", "comparador"):
            assert f'id="{section_id}"' in html
        assert 'role="tabpanel"' not in html
        assert 'class="tab-btn' not in html

    def test_index_usa_nova_marca_tema_claro_e_tabela_antes_da_rodada(self, client):
        html = client.get("/").get_data(as_text=True)

        assert "Brasileirão Dashboard" in html
        assert "Caderno da Rodada" not in html
        assert 'id="theme-toggle"' not in html
        assert "localStorage.getItem('theme')" not in html
        assert html.index('id="classificacao"') < html.index('id="rodada"')
        assert html.index('id="classificacao"') < html.index("data-round-controller")
        assert 'class="scorers-table"' in html
        assert 'class="scorer-podium"' not in html
        for titulo in ("Ataque × defesa", "Casa × fora", "Forma recente", "Gols por rodada"):
            assert titulo in html
        assert "Corrida pelos gols" not in html

    def test_index_usa_marca_tipografica_e_destaques_integrados_na_tabela(self, client):
        html = client.get("/").get_data(as_text=True)

        assert 'class="edition-brand-mark"' not in html
        assert 'class="header-status"' not in html
        assert 'class="standings-highlights"' not in html
        assert 'class="standings-summary"' not in html
        assert "Brasileirão Série A" in html
        assert 'class="club-achievement"' not in html
        assert 'class="mobile-leader-label"' not in html
        assert 'class="metric-record-label"' in html
        assert "Dados atualizados em" in html

    def test_classificacao_explica_as_cores_das_zonas(self, client):
        html = client.get("/").get_data(as_text=True)

        assert 'class="zone-legend"' in html
        assert 'class="zone-legend-mark zone-libertadores"' in html
        assert 'class="zone-legend-mark zone-pre-libertadores"' in html
        assert 'class="zone-legend-mark zone-sulamericana"' in html
        assert 'class="zone-legend-mark zone-rebaixamento"' in html
        for zona in ("Libertadores", "Pré-Libertadores", "Sul-Americana", "Rebaixamento"):
            assert zona in html

    def test_cor_da_pre_libertadores_tem_presenca_no_tema_claro(self):
        css = Path("static/css/dashboard.css").read_text(encoding="utf-8")

        assert "--zone-pre: #2f8f5b;" in css

    def test_cor_da_sulamericana_tem_presenca_no_tema_claro(self):
        css = Path("static/css/dashboard.css").read_text(encoding="utf-8")

        assert "--zone-sula: #d99700;" in css

    def test_destaques_exibem_empates_de_metricas_sem_repetir_o_lider(self):
        classificacao = [
            {"sigla": "FLA", "time": "Flamengo", "pontos": 54, "gols_pro": 51, "gols_contra": 21},
            {"sigla": "PAL", "time": "Palmeiras", "pontos": 54, "gols_pro": 51, "gols_contra": 20},
            {"sigla": "BOT", "time": "Botafogo", "pontos": 48, "gols_pro": 44, "gols_contra": 20},
        ]

        assert app_module._destaques_classificacao(classificacao) == {
            "melhores_ataques": {"FLA", "PAL"},
            "melhores_defesas": {"PAL", "BOT"},
        }

    def test_contexto_mantem_classificacao_atual_quando_query_muda_apenas_os_jogos(self, dados_json_validos):
        historica = deepcopy(dados_json_validos["classificacao"])
        historica[0]["pontos"] -= 3
        historica[0]["vitorias"] -= 1
        historica[0]["jogos"] -= 1
        historica[0]["gols_pro"] -= 1
        historica[0]["saldo"] -= 1
        historica[0]["aproveitamento"] = round(historica[0]["pontos"] / (historica[0]["jogos"] * 3) * 100, 1)
        dados_json_validos["classificacao_por_rodada"] = {"10": historica}

        with flask_app.test_request_context("/?rodada=10"):
            contexto = app_module._contexto_dados(dados_json_validos)

        assert contexto["rodada_inicial"] == 10
        assert contexto["classificacao_inicial"] == dados_json_validos["classificacao"]
        assert contexto["classificacao_disponivel"] is True

    def test_calcula_leituras_graficas_apenas_com_partidas_encerradas(self, dados_json_validos):
        dados_json_validos["agenda_desatualizada"] = False
        dados_json_validos["partidas"] = [
            {
                "id": 1,
                "rodada": 1,
                "inicio_em": "2026-04-01T22:00:00Z",
                "status": "encerrada",
                "mandante": "FLA",
                "visitante": "PAL",
                "placar": {"mandante": 2, "visitante": 0},
            },
            {
                "id": 2,
                "rodada": 2,
                "inicio_em": "2026-04-08T22:00:00Z",
                "status": "encerrada",
                "mandante": "PAL",
                "visitante": "FLA",
                "placar": {"mandante": 1, "visitante": 1},
            },
            {
                "id": 3,
                "rodada": 3,
                "inicio_em": "2026-04-15T22:00:00Z",
                "status": "agendada",
                "mandante": "FLA",
                "visitante": "PAL",
                "placar": {"mandante": None, "visitante": None},
            },
        ]

        leituras = app_module._calcular_leituras_campeonato(dados_json_validos)
        mandos = {item["sigla"]: item for item in leituras["mandos"]}
        formas = {item["sigla"]: item for item in leituras["forma"]}

        assert leituras["partidas_encerradas"] == 2
        assert leituras["disponivel"] is True
        assert mandos["FLA"]["aproveitamento_casa"] == 100.0
        assert mandos["FLA"]["aproveitamento_fora"] == 33.3
        assert mandos["PAL"]["aproveitamento_casa"] == 33.3
        assert mandos["PAL"]["aproveitamento_fora"] == 0.0
        assert formas["FLA"]["pontos"] == 4
        assert formas["FLA"]["resultados"] == ["V", "E"]
        assert leituras["gols_por_rodada"] == [
            {"rodada": 1, "gols": 2, "jogos": 1, "completa": False},
            {"rodada": 2, "gols": 2, "jogos": 1, "completa": False},
        ]

    def test_leituras_graficas_expoem_estado_vazio_sem_agenda(self, dados_json_validos):
        dados_json_validos["partidas"] = []
        dados_json_validos["agenda_desatualizada"] = True

        leituras = app_module._calcular_leituras_campeonato(dados_json_validos)

        assert leituras["disponivel"] is False
        assert leituras["desatualizado"] is True
        assert leituras["mandos"] == []
        assert leituras["forma"] == []
        assert leituras["gols_por_rodada"] == []

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

    def test_status_de_desatualizacao_exige_sinal_explicito(self, monkeypatch):
        monkeypatch.setenv("DATA_AUTO_REFRESH_HOURS", "6")
        dados = {
            "dados_atualizados_em": "2026-09-01T00:00:00+00:00",
            "dados_verificados_em": "2026-09-10T12:00:00+00:00",
        }

        assert app_module.dados_dashboard_desatualizados(dados, agora=1789041600) is False
        assert app_module.dados_dashboard_desatualizados({"dados_desatualizados": True}) is True

    def test_refresh_automatico_continua_usando_idade_do_snapshot(self, monkeypatch):
        monkeypatch.setenv("DATA_AUTO_REFRESH_HOURS", "6")
        dados = {"dados_atualizados_em": "2026-09-01T00:00:00+00:00"}

        assert app_module.dados_dashboard_refresh_necessario(dados, agora=1789041600) is True

    def test_public_url_respeita_origem_e_base_path(self, monkeypatch):
        monkeypatch.setenv("SITE_ORIGIN", "https://dashboard.example/")
        monkeypatch.setitem(app_module.app.config, "SITE_BASE_PATH", "/futebol-dashboard")

        assert app_module.public_url("time/PAL/") == "https://dashboard.example/futebol-dashboard/time/PAL/"
        assert app_module.public_url() == "https://dashboard.example/futebol-dashboard/"

    def test_public_url_preserva_url_absoluta(self, monkeypatch):
        monkeypatch.setenv("SITE_ORIGIN", "https://dashboard.example")
        assert app_module.public_url("https://cdn.example/arquivo.png") == "https://cdn.example/arquivo.png"


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

    def test_exibe_ultimo_proximo_jogo_e_forma(self, client, monkeypatch, tmp_path, dados_json_validos):
        time = dados_json_validos["classificacao"][0]
        rival = dados_json_validos["classificacao"][1]
        dados_json_validos["partidas"] = [
            {
                "id": 1,
                "rodada": 1,
                "inicio_em": "2025-04-25T20:00:00+00:00",
                "status": "encerrada",
                "mandante": time["sigla"],
                "visitante": rival["sigla"],
                "placar": {"mandante": 2, "visitante": 0},
            },
            {
                "id": 2,
                "rodada": 2,
                "inicio_em": "2027-04-25T20:00:00+00:00",
                "status": "agendada",
                "mandante": rival["sigla"],
                "visitante": time["sigla"],
                "placar": {"mandante": None, "visitante": None},
            },
        ]
        arquivo = tmp_path / "dados_time.json"
        arquivo.write_text(json.dumps(dados_json_validos, ensure_ascii=False), encoding="utf-8")
        monkeypatch.setattr(app_module, "DATA_PATH", str(arquivo))

        html = client.get(f"/time/{time['sigla']}/").get_data(as_text=True)

        assert "Último jogo" in html
        assert "Próximo jogo" in html
        assert 'data-forma="V"' in html
        assert "Média da liga" in html
        assert f"time1={time['sigla']}" in html

    def test_proximo_jogo_ignora_partida_cancelada(self, dados_json_validos):
        time = dados_json_validos["classificacao"][0]
        rival = dados_json_validos["classificacao"][1]
        dados_json_validos["partidas"] = [
            {
                "id": 2,
                "rodada": 2,
                "inicio_em": "2026-04-25T20:00:00+00:00",
                "status": "cancelada",
                "mandante": rival["sigla"],
                "visitante": time["sigla"],
                "placar": {"mandante": None, "visitante": None},
            },
            {
                "id": 3,
                "rodada": 3,
                "inicio_em": "2026-05-02T20:00:00+00:00",
                "status": "agendada",
                "mandante": time["sigla"],
                "visitante": rival["sigla"],
                "placar": {"mandante": None, "visitante": None},
            },
        ]

        contexto = app_module._contexto_time(dados_json_validos, time)

        assert contexto["proximo_jogo"]["id"] == 3


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


class TestAPIPartidas:
    def test_retorna_lista_vazia_para_snapshot_legado(self, client):
        resp = client.get("/api/partidas")

        assert resp.status_code == 200
        assert resp.content_type == "application/json"
        assert resp.get_json() == []

    def test_retorna_partidas_normalizadas_do_snapshot(self, client, monkeypatch, tmp_path, dados_json_validos):
        mandante, visitante = dados_json_validos["classificacao"][:2]
        dados_json_validos["partidas"] = [
            {
                "id": 12,
                "rodada": 1,
                "inicio_em": "2026-04-25T20:00:00+00:00",
                "status": "encerrada",
                "mandante": mandante["sigla"],
                "visitante": visitante["sigla"],
                "placar": {"mandante": 2, "visitante": 0},
            }
        ]
        arquivo = tmp_path / "dados_com_partidas.json"
        arquivo.write_text(json.dumps(dados_json_validos, ensure_ascii=False), encoding="utf-8")
        monkeypatch.setattr(app_module, "DATA_PATH", str(arquivo))

        resp = client.get("/api/partidas")

        assert resp.status_code == 200
        assert resp.get_json()[0]["id"] == 12


class TestErros:
    def test_arquivo_ausente_api_retorna_json(self, client, monkeypatch, tmp_path):
        caminho_falso = str(tmp_path / "nao_existe.json")
        monkeypatch.setattr(app_module, "DATA_PATH", caminho_falso)
        resp = client.get("/api/classificacao")
        assert resp.status_code == 503
        data = resp.get_json()
        assert data["codigo"] == "DADOS_NAO_ENCONTRADOS"
        assert caminho_falso not in data["erro"]

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

    def test_json_com_raiz_invalida_api_retorna_erro_de_dados(self, client, monkeypatch, tmp_path):
        arquivo = tmp_path / "lista.json"
        arquivo.write_text("[]", encoding="utf-8")
        monkeypatch.setattr(app_module, "DATA_PATH", str(arquivo))

        resp = client.get("/api/classificacao")

        assert resp.status_code == 500
        assert resp.get_json() == {"erro": "Arquivo de dados invalido", "codigo": "DADOS_INVALIDOS"}

    def test_dados_invalidos_api(self, client, monkeypatch, tmp_path):
        arquivo = tmp_path / "vazio.json"
        arquivo.write_text('{"classificacao":[],"artilharia":[],"info":{}}', encoding="utf-8")
        monkeypatch.setattr(app_module, "DATA_PATH", str(arquivo))
        resp = client.get("/api/classificacao")
        assert resp.status_code == 500
        data = resp.get_json()
        assert data["codigo"] == "DADOS_INVALIDOS"
        assert "classificacao" not in data["erro"]

    def test_dados_invalidos_web_nao_expoe_detalhes(self, client, monkeypatch, tmp_path):
        arquivo = tmp_path / "vazio.json"
        arquivo.write_text('{"classificacao":[],"artilharia":[],"info":{}}', encoding="utf-8")
        monkeypatch.setattr(app_module, "DATA_PATH", str(arquivo))

        resp = client.get("/")

        assert resp.status_code == 500
        assert "classificacao deve ser" not in resp.get_data(as_text=True)
        assert "O arquivo de dados nao atende ao formato esperado." in resp.get_data(as_text=True)

    def test_falha_inesperada_em_api_retorna_json(self, client, monkeypatch):
        monkeypatch.setattr(app_module, "carregar_dados", lambda: (_ for _ in ()).throw(RuntimeError("segredo")))
        app_module.app.config["TESTING"] = False
        try:
            resp = client.get("/api/classificacao")
        finally:
            app_module.app.config["TESTING"] = True

        assert resp.status_code == 500
        assert resp.content_type == "application/json"
        assert resp.get_json() == {"erro": "Erro interno do servidor", "codigo": "ERRO_INTERNO"}

    def test_metodo_invalido_em_api_preserva_405_e_allow(self, client):
        resp = client.post("/api/classificacao")

        assert resp.status_code == 405
        assert set(resp.headers["Allow"].split(", ")) == {"GET", "HEAD", "OPTIONS"}
        assert resp.get_json() == {"erro": "Metodo nao permitido", "codigo": "METODO_NAO_PERMITIDO"}


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

    def test_refresh_automatico_responde_snapshot_antes_da_rede(
        self, client, monkeypatch, tmp_path, dados_json_validos
    ):
        arquivo = tmp_path / "dados.json"
        arquivo.write_text(json.dumps(dados_json_validos, ensure_ascii=False), encoding="utf-8")
        monkeypatch.setattr(app_module, "DATA_PATH", str(arquivo))
        monkeypatch.setenv("FOOTBALL_DATA_TOKEN", "token_teste")
        monkeypatch.setenv("DATA_AUTO_REFRESH_HOURS", "1")
        monkeypatch.setenv("DATA_AUTO_REFRESH_COOLDOWN_MINUTES", "0")

        dados_atualizados = json.loads(json.dumps(dados_json_validos))
        dados_atualizados["classificacao"][0]["cor"] = "#654321"
        os.utime(str(arquivo), (1, 1))

        chamadas = []

        iniciou = threading.Event()
        liberar = threading.Event()

        def fake_atualizar(_temporada=None, **kwargs):
            chamadas.append(kwargs)
            iniciou.set()
            assert liberar.wait(timeout=5)
            arquivo.write_text(json.dumps(dados_atualizados, ensure_ascii=False), encoding="utf-8")
            os.utime(str(arquivo), None)

        import atualizar_dados as atu

        monkeypatch.setattr(atu, "atualizar", fake_atualizar)

        app_module.app.config["TESTING"] = False
        try:
            resp = client.get("/api/classificacao")
        finally:
            liberar.set()
            app_module.app.config["TESTING"] = True

        assert resp.status_code == 200
        assert resp.get_json()[0]["cor"] != "#654321"
        assert iniciou.wait(timeout=1)
        liberar.set()
        for thread in list(app_module._refresh_threads):
            thread.join(timeout=5)
        assert resp.get_json()[0]["cor"] != "#654321"
        assert client.get("/api/classificacao").get_json()[0]["cor"] == "#654321"
        assert chamadas == [{"destino": str(arquivo)}]

    def test_refresh_automatico_single_flight_com_cooldown_zero(
        self, client, monkeypatch, tmp_path, dados_json_validos
    ):
        arquivo = tmp_path / "dados.json"
        arquivo.write_text(json.dumps(dados_json_validos, ensure_ascii=False), encoding="utf-8")
        monkeypatch.setattr(app_module, "DATA_PATH", str(arquivo))
        monkeypatch.setenv("FOOTBALL_DATA_TOKEN", "token_teste")
        monkeypatch.setenv("DATA_AUTO_REFRESH_HOURS", "1")
        monkeypatch.setenv("DATA_AUTO_REFRESH_COOLDOWN_MINUTES", "0")
        os.utime(str(arquivo), (1, 1))

        iniciou = threading.Event()
        liberar = threading.Event()
        chamadas = []

        def fake_atualizar(_temporada=None, **kwargs):
            chamadas.append(kwargs)
            iniciou.set()
            assert liberar.wait(timeout=5)

        import atualizar_dados as atu

        monkeypatch.setattr(atu, "atualizar", fake_atualizar)
        respostas = [None, None]
        barreira = threading.Barrier(2)

        def fazer_requisicao(indice):
            barreira.wait(timeout=5)
            with flask_app.test_client() as cliente:
                respostas[indice] = cliente.get("/api/classificacao")

        requisicoes = [threading.Thread(target=fazer_requisicao, args=(indice,)) for indice in range(2)]
        app_module.app.config["TESTING"] = False
        try:
            for requisicao in requisicoes:
                requisicao.start()
            assert iniciou.wait(timeout=1)
            for requisicao in requisicoes:
                requisicao.join(timeout=5)
        finally:
            liberar.set()
            app_module.app.config["TESTING"] = True

        liberar.set()
        for thread in list(app_module._refresh_threads):
            thread.join(timeout=5)

        assert all(resposta is not None and resposta.status_code == 200 for resposta in respostas)
        assert len(chamadas) == 1

    def test_refresh_automatico_falha_respeita_cooldown(self, client, monkeypatch, tmp_path, dados_json_validos):
        arquivo = tmp_path / "dados.json"
        arquivo.write_text(json.dumps(dados_json_validos, ensure_ascii=False), encoding="utf-8")
        monkeypatch.setattr(app_module, "DATA_PATH", str(arquivo))
        monkeypatch.setenv("FOOTBALL_DATA_TOKEN", "token_teste")
        monkeypatch.setenv("DATA_AUTO_REFRESH_HOURS", "1")
        monkeypatch.setenv("DATA_AUTO_REFRESH_COOLDOWN_MINUTES", "10")
        os.utime(str(arquivo), (1, 1))

        chamadas = []

        def falhar(_temporada=None, **_kwargs):
            chamadas.append(True)
            raise OSError("fonte indisponivel")

        import atualizar_dados as atu

        monkeypatch.setattr(atu, "atualizar", falhar)
        app_module.app.config["TESTING"] = False
        try:
            assert client.get("/api/classificacao").status_code == 200
            for thread in list(app_module._refresh_threads):
                thread.join(timeout=5)
            assert client.get("/api/classificacao").status_code == 200
        finally:
            app_module.app.config["TESTING"] = True

        assert len(chamadas) == 1

    def test_arquivo_ausente_agenda_refresh_e_responde_503_ate_recuperar(
        self, client, monkeypatch, tmp_path, dados_json_validos
    ):
        arquivo = tmp_path / "ausente.json"
        monkeypatch.setattr(app_module, "DATA_PATH", str(arquivo))
        monkeypatch.setenv("FOOTBALL_DATA_TOKEN", "token_teste")
        monkeypatch.setenv("DATA_AUTO_REFRESH_HOURS", "1")
        monkeypatch.setenv("DATA_AUTO_REFRESH_COOLDOWN_MINUTES", "0")

        iniciou = threading.Event()
        liberar = threading.Event()

        def fake_atualizar(_temporada=None, **kwargs):
            iniciou.set()
            assert liberar.wait(timeout=5)
            arquivo.write_text(json.dumps(dados_json_validos, ensure_ascii=False), encoding="utf-8")

        import atualizar_dados as atu

        monkeypatch.setattr(atu, "atualizar", fake_atualizar)
        app_module.app.config["TESTING"] = False
        try:
            resposta = client.get("/api/classificacao")
        finally:
            liberar.set()
            app_module.app.config["TESTING"] = True

        assert resposta.status_code == 503
        assert iniciou.wait(timeout=1)
        liberar.set()
        for thread in list(app_module._refresh_threads):
            thread.join(timeout=5)
        assert client.get("/api/classificacao").status_code == 200

    def test_json_invalido_nao_usa_cache_valido_anterior(self, client, monkeypatch, tmp_path, dados_json_validos):
        arquivo = tmp_path / "dados.json"
        arquivo.write_text(json.dumps(dados_json_validos, ensure_ascii=False), encoding="utf-8")
        monkeypatch.setattr(app_module, "DATA_PATH", str(arquivo))
        monkeypatch.setenv("DATA_AUTO_REFRESH_HOURS", "0")

        assert client.get("/api/classificacao").status_code == 200
        arquivo.write_text("{invalido", encoding="utf-8")
        os.utime(arquivo, (arquivo.stat().st_mtime + 10, arquivo.stat().st_mtime + 10))

        resposta = client.get("/api/classificacao")

        assert resposta.status_code == 500
        assert resposta.get_json()["codigo"] == "JSON_INVALIDO"

    def test_cache_considera_caminho_mesmo_com_mesmo_mtime(self, monkeypatch, tmp_path, dados_json_validos):
        arquivo_um = tmp_path / "um.json"
        arquivo_dois = tmp_path / "dois.json"
        dados_dois = json.loads(json.dumps(dados_json_validos))
        dados_dois["classificacao"][0]["cor"] = "#654321"
        arquivo_um.write_text(json.dumps(dados_json_validos, ensure_ascii=False), encoding="utf-8")
        arquivo_dois.write_text(json.dumps(dados_dois, ensure_ascii=False), encoding="utf-8")
        timestamp_ns = 1234567890000000000
        os.utime(arquivo_um, ns=(timestamp_ns, timestamp_ns))
        os.utime(arquivo_dois, ns=(timestamp_ns, timestamp_ns))
        monkeypatch.setenv("DATA_AUTO_REFRESH_HOURS", "0")

        monkeypatch.setattr(app_module, "DATA_PATH", str(arquivo_um))
        primeiro = app_module.carregar_dados()
        monkeypatch.setattr(app_module, "DATA_PATH", str(arquivo_dois))
        segundo = app_module.carregar_dados()

        assert primeiro["classificacao"][0]["cor"] != segundo["classificacao"][0]["cor"]

    def test_refresh_captura_destino_e_temporada_antes_de_iniciar(
        self, client, monkeypatch, tmp_path, dados_json_validos
    ):
        arquivo_um = tmp_path / "um.json"
        arquivo_dois = tmp_path / "dois.json"
        arquivo_um.write_text(json.dumps(dados_json_validos, ensure_ascii=False), encoding="utf-8")
        arquivo_dois.write_text(json.dumps(dados_json_validos, ensure_ascii=False), encoding="utf-8")
        monkeypatch.setattr(app_module, "DATA_PATH", str(arquivo_um))
        monkeypatch.setenv("FOOTBALL_DATA_TOKEN", "token_teste")
        monkeypatch.setenv("DATA_AUTO_REFRESH_HOURS", "1")
        monkeypatch.setenv("DATA_AUTO_REFRESH_COOLDOWN_MINUTES", "0")
        os.utime(arquivo_um, (1, 1))

        iniciou = threading.Event()
        liberar = threading.Event()
        chamadas = []

        def fake_atualizar(temporada=None, **kwargs):
            chamadas.append((temporada, kwargs))
            iniciou.set()
            assert liberar.wait(timeout=5)

        import atualizar_dados as atu

        monkeypatch.setattr(atu, "atualizar", fake_atualizar)
        monkeypatch.setattr(app_module, "temporada_brasileirao_atual", lambda: "2026")
        app_module.app.config["TESTING"] = False
        try:
            assert client.get("/api/classificacao").status_code == 200
            assert iniciou.wait(timeout=1)
            monkeypatch.setattr(app_module, "DATA_PATH", str(arquivo_dois))
        finally:
            liberar.set()
            app_module.app.config["TESTING"] = True

        liberar.set()
        for thread in list(app_module._refresh_threads):
            thread.join(timeout=5)

        assert chamadas == [("2026", {"destino": os.path.abspath(arquivo_um)})]

    def test_carregar_dados_pode_pular_refresh_automatico(self, monkeypatch, tmp_path, dados_json_validos):
        arquivo = tmp_path / "dados.json"
        arquivo.write_text(json.dumps(dados_json_validos, ensure_ascii=False), encoding="utf-8")
        monkeypatch.setattr(app_module, "DATA_PATH", str(arquivo))
        monkeypatch.setattr(
            app_module,
            "_tentar_refresh_automatico",
            lambda: (_ for _ in ()).throw(RuntimeError("refresh")),
        )

        dados = app_module.carregar_dados(permitir_refresh=False)

        assert dados["info"]["temporada"] == "2025"


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

        chamadas = []

        def fake_atualizar(_temporada=None, **kwargs):
            chamadas.append(kwargs)

        import atualizar_dados as atu

        monkeypatch.setattr(atu, "atualizar", fake_atualizar)

        resp = client.post("/api/atualizar", headers={"Authorization": "Bearer segredo"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data.get("status") == "ok"
        assert chamadas == [{"destino": str(arquivo)}]

    def test_falha_de_atualizacao_nao_expoe_excecao(self, client, monkeypatch):
        monkeypatch.setenv("API_UPDATE_TOKEN", "segredo")

        def falhar(*_args, **_kwargs):
            raise OSError("caminho-secreto")

        import atualizar_dados as atu

        monkeypatch.setattr(atu, "atualizar", falhar)

        resp = client.post("/api/atualizar", headers={"Authorization": "Bearer segredo"})

        assert resp.status_code == 500
        assert resp.get_json() == {"erro": "Falha ao atualizar dados", "codigo": "ATUALIZACAO_FALHOU"}

    def test_manual_retorna_409_quando_refresh_automatico_esta_em_andamento(
        self, client, monkeypatch, tmp_path, dados_json_validos
    ):
        arquivo = tmp_path / "dados.json"
        arquivo.write_text(json.dumps(dados_json_validos, ensure_ascii=False), encoding="utf-8")
        monkeypatch.setattr(app_module, "DATA_PATH", str(arquivo))
        monkeypatch.setenv("FOOTBALL_DATA_TOKEN", "token_teste")
        monkeypatch.setenv("DATA_AUTO_REFRESH_HOURS", "1")
        monkeypatch.setenv("DATA_AUTO_REFRESH_COOLDOWN_MINUTES", "0")
        monkeypatch.setenv("API_UPDATE_TOKEN", "segredo")
        os.utime(arquivo, (1, 1))

        iniciou = threading.Event()
        liberar = threading.Event()

        def fake_atualizar(_temporada=None, **_kwargs):
            iniciou.set()
            assert liberar.wait(timeout=5)

        import atualizar_dados as atu

        monkeypatch.setattr(atu, "atualizar", fake_atualizar)
        app_module.app.config["TESTING"] = False
        try:
            assert client.get("/api/classificacao").status_code == 200
            assert iniciou.wait(timeout=1)
            resposta = client.post("/api/atualizar", headers={"Authorization": "Bearer segredo"})
        finally:
            liberar.set()
            app_module.app.config["TESTING"] = True

        liberar.set()
        for thread in list(app_module._refresh_threads):
            thread.join(timeout=5)

        assert resposta.status_code == 409
        assert resposta.get_json()["codigo"] == "ATUALIZACAO_EM_ANDAMENTO"

    def test_falha_ao_iniciar_thread_libera_refresh(self, monkeypatch, tmp_path, dados_json_validos):
        arquivo = tmp_path / "dados.json"
        arquivo.write_text(json.dumps(dados_json_validos, ensure_ascii=False), encoding="utf-8")
        monkeypatch.setattr(app_module, "DATA_PATH", str(arquivo))
        monkeypatch.setenv("FOOTBALL_DATA_TOKEN", "token_teste")
        monkeypatch.setenv("DATA_AUTO_REFRESH_HOURS", "1")
        monkeypatch.setenv("DATA_AUTO_REFRESH_COOLDOWN_MINUTES", "10")
        os.utime(arquivo, (1, 1))

        inicios = []

        class ThreadQueFalha:
            daemon = False

            def __init__(self, **_kwargs):
                pass

            def start(self):
                inicios.append(True)
                raise RuntimeError("start falhou")

        monkeypatch.setattr(app_module.threading, "Thread", ThreadQueFalha)
        app_module.app.config["TESTING"] = False
        try:
            app_module._tentar_refresh_automatico(os.path.abspath(arquivo), arquivo.stat().st_mtime_ns)
            app_module._tentar_refresh_automatico(os.path.abspath(arquivo), arquivo.stat().st_mtime_ns)
        finally:
            app_module.app.config["TESTING"] = True

        assert app_module._refresh_em_andamento is False
        assert len(inicios) == 1


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

    def test_health_expoe_fonte_e_frescor_do_snapshot(self, client, monkeypatch, tmp_path, dados_json_validos):
        dados_json_validos["fonte"] = "CBF"
        dados_json_validos["dados_atualizados_em"] = "2026-09-01T00:00:00+00:00"
        arquivo = tmp_path / "dados.json"
        arquivo.write_text(json.dumps(dados_json_validos, ensure_ascii=False), encoding="utf-8")
        monkeypatch.setattr(app_module, "DATA_PATH", str(arquivo))
        monkeypatch.setenv("DATA_AUTO_REFRESH_HOURS", "6")

        resposta = client.get("/api/health")

        assert resposta.status_code == 200
        dados = resposta.get_json()
        assert dados["fonte"] == "CBF"
        assert dados["dados_desatualizados"] is False
        assert dados["dados_refresh_necessario"] is True
