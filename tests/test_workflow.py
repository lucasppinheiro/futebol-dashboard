import json
import shutil
import subprocess
from pathlib import Path

import pytest

WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "refresh-data.yml"
VERCEL_CONFIG = Path(__file__).parents[1] / "vercel.json"


def _bash_disponivel() -> bool:
    if shutil.which("bash") is None:
        return False
    try:
        return (
            subprocess.run(
                ["bash", "-c", ":"],
                capture_output=True,
                check=False,
                timeout=5,
            ).returncode
            == 0
        )
    except OSError:
        return False


def _refresh_step_script() -> str:
    conteudo = WORKFLOW.read_text(encoding="utf-8")
    inicio = conteudo.index("        run: |", conteudo.index("- name: Refresh competition data"))
    linhas = []
    for linha in conteudo[inicio:].splitlines()[1:]:
        if linha.startswith("      - name:"):
            break
        if linha.startswith("          "):
            linhas.append(linha[10:])
    return "\n".join(linhas)


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


def test_workflow_usa_cbf_e_nao_falha_refresh_agendado_por_api():
    conteudo = WORKFLOW.read_text(encoding="utf-8")

    assert 'DATA_SOURCE: "cbf"' in conteudo
    assert 'if [ -z "${FOOTBALL_DATA_TOKEN:-}" ]; then' not in conteudo
    assert "keeping the current dataset" in conteudo
    assert 'if [ "${{ github.event_name }}" = "workflow_dispatch" ]; then' in conteudo
    assert "Competition data refresh failed" in conteudo


@pytest.mark.skipif(not _bash_disponivel(), reason="bash indisponivel")
def test_workflow_preserva_status_manual_e_sucesso_agendado():
    script = _refresh_step_script().replace(
        "python atualizar_dados.py",
        "(exit 7)",
    )

    resultados = {}
    for evento in ("workflow_dispatch", "schedule"):
        script_evento = script.replace("${{ github.event_name }}", evento)
        processo = subprocess.run(
            ["bash", "-c", script_evento],
            cwd=WORKFLOW.parents[2],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        resultados[evento] = processo.returncode

    assert resultados == {"workflow_dispatch": 7, "schedule": 0}


def test_vercel_publica_o_build_estatico_sem_detectar_flask():
    config = json.loads(VERCEL_CONFIG.read_text(encoding="utf-8"))

    assert config["framework"] is None
    assert config["outputDirectory"] == "dist"
    assert config["buildCommand"] == "python3 build_static.py"
