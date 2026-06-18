import json
from pathlib import Path


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "refresh-data.yml"
VERCEL_CONFIG = Path(__file__).parents[1] / "vercel.json"


def test_workflow_valida_dados_antes_do_commit():
    conteudo = WORKFLOW.read_text(encoding="utf-8")

    assert "schedule:" in conteudo
    assert "workflow_dispatch:" in conteudo
    assert "python -m pytest tests -q" in conteudo
    assert "npm test" in conteudo
    assert conteudo.index("python build_static.py") < conteudo.index("git commit")


def test_workflow_limita_tempo_e_permissoes_por_job():
    conteudo = WORKFLOW.read_text(encoding="utf-8")

    assert conteudo.count("timeout-minutes:") == 1
    assert "\npermissions:" not in conteudo
    assert conteudo.count("    permissions:") == 1


def test_workflow_nao_falha_refresh_agendado_por_token_ou_api():
    conteudo = WORKFLOW.read_text(encoding="utf-8")

    assert 'if [ -z "${FOOTBALL_DATA_TOKEN:-}" ]; then' in conteudo
    assert "keeping the current dataset" in conteudo
    assert 'if [ "${{ github.event_name }}" = "workflow_dispatch" ]; then' in conteudo
    assert "Competition data refresh failed" in conteudo


def test_vercel_publica_o_build_estatico_sem_detectar_flask():
    config = json.loads(VERCEL_CONFIG.read_text(encoding="utf-8"))

    assert config["framework"] is None
    assert config["outputDirectory"] == "dist"
    assert config["buildCommand"] == "python3 build_static.py"
