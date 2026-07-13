import os

from env_config import carregar_env_local


def _escrever_env(tmp_path, conteudo):
    arquivo = tmp_path / ".env"
    arquivo.write_text(conteudo, encoding="utf-8")
    return str(arquivo)


def test_define_variavel_ausente(monkeypatch, tmp_path):
    monkeypatch.delenv("TESTE_ENV_NOVA", raising=False)
    caminho = _escrever_env(tmp_path, "TESTE_ENV_NOVA=valor\n")

    carregar_env_local(caminho)

    assert os.environ["TESTE_ENV_NOVA"] == "valor"
    monkeypatch.delenv("TESTE_ENV_NOVA", raising=False)


def test_ignora_comentarios_linhas_vazias_e_sem_igual(monkeypatch, tmp_path):
    monkeypatch.delenv("TESTE_ENV_COMENTARIO", raising=False)
    caminho = _escrever_env(tmp_path, "# TESTE_ENV_COMENTARIO=1\n\nlinha sem igual\n")

    carregar_env_local(caminho)

    assert "TESTE_ENV_COMENTARIO" not in os.environ


def test_remove_aspas_simples_e_duplas(monkeypatch, tmp_path):
    monkeypatch.delenv("TESTE_ENV_DUPLA", raising=False)
    monkeypatch.delenv("TESTE_ENV_SIMPLES", raising=False)
    caminho = _escrever_env(tmp_path, "TESTE_ENV_DUPLA=\"com espacos\"\nTESTE_ENV_SIMPLES='x'\n")

    carregar_env_local(caminho)

    assert os.environ["TESTE_ENV_DUPLA"] == "com espacos"
    assert os.environ["TESTE_ENV_SIMPLES"] == "x"
    monkeypatch.delenv("TESTE_ENV_DUPLA", raising=False)
    monkeypatch.delenv("TESTE_ENV_SIMPLES", raising=False)


def test_nao_sobrescreve_variavel_ja_definida(monkeypatch, tmp_path):
    monkeypatch.setenv("TESTE_ENV_EXISTENTE", "original")
    caminho = _escrever_env(tmp_path, "TESTE_ENV_EXISTENTE=novo\n")

    carregar_env_local(caminho)

    assert os.environ["TESTE_ENV_EXISTENTE"] == "original"


def test_nao_sobrescreve_variavel_definida_como_vazia(monkeypatch, tmp_path):
    monkeypatch.setenv("TESTE_ENV_VAZIA", "")
    caminho = _escrever_env(tmp_path, "TESTE_ENV_VAZIA=preenchida\n")

    carregar_env_local(caminho)

    assert os.environ["TESTE_ENV_VAZIA"] == ""


def test_override_sobrescreve(monkeypatch, tmp_path):
    monkeypatch.setenv("TESTE_ENV_OVERRIDE", "original")
    caminho = _escrever_env(tmp_path, "TESTE_ENV_OVERRIDE=novo\n")

    carregar_env_local(caminho, override=True)

    assert os.environ["TESTE_ENV_OVERRIDE"] == "novo"


def test_arquivo_ausente_e_noop(tmp_path):
    carregar_env_local(str(tmp_path / "nao_existe.env"))


def test_usa_env_file_quando_caminho_nao_informado(monkeypatch, tmp_path):
    monkeypatch.delenv("TESTE_ENV_VIA_ENV_FILE", raising=False)
    caminho = _escrever_env(tmp_path, "TESTE_ENV_VIA_ENV_FILE=ok\n")
    monkeypatch.setenv("ENV_FILE", caminho)

    carregar_env_local()

    assert os.environ["TESTE_ENV_VIA_ENV_FILE"] == "ok"
    monkeypatch.delenv("TESTE_ENV_VIA_ENV_FILE", raising=False)
