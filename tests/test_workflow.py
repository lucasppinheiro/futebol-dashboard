from pathlib import Path


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "refresh-data.yml"


def test_workflow_valida_dados_antes_do_commit():
    conteudo = WORKFLOW.read_text(encoding="utf-8")

    assert "schedule:" in conteudo
    assert "python -m pytest tests -q" in conteudo
    assert "npm test" in conteudo
    assert conteudo.index("python build_static.py") < conteudo.index("git commit")


def test_workflow_limita_tempo_e_permissoes_por_job():
    conteudo = WORKFLOW.read_text(encoding="utf-8")

    assert conteudo.count("timeout-minutes:") == 1
    assert "\npermissions:" not in conteudo
    assert conteudo.count("    permissions:") == 1
