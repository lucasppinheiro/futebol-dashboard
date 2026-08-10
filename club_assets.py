from typing import Any

ESCUDOS_LOCAIS: dict[str, str] = {
    "BAH": "static/img/escudos/cbf/BAH.jpg",
    "BOT": "static/img/escudos/cbf/BOT.jpg",
    "CAM": "static/img/escudos/cbf/CAM.jpg",
    "CAP": "static/img/escudos/cbf/CAP.jpg",
    "CFC": "static/img/escudos/cbf/CFC.jpg",
    "CHA": "static/img/escudos/cbf/CHA.jpg",
    "COR": "static/img/escudos/cbf/COR.jpg",
    "CRU": "static/img/escudos/cbf/CRU.jpg",
    "FLA": "static/img/escudos/cbf/FLA.jpg",
    "FLU": "static/img/escudos/cbf/FLU.jpg",
    "GRE": "static/img/escudos/cbf/GRE.jpg",
    "INT": "static/img/escudos/cbf/INT.jpg",
    "MIR": "static/img/escudos/cbf/MIR.jpg",
    "PAL": "static/img/escudos/cbf/PAL.jpg",
    "RBB": "static/img/escudos/cbf/RBB.jpg",
    "REM": "static/img/escudos/cbf/REM.jpg",
    "SAN": "static/img/escudos/cbf/SAN.jpg",
    "SAO": "static/img/escudos/cbf/SAO.jpg",
    "VAS": "static/img/escudos/cbf/VAS.jpg",
    "VIT": "static/img/escudos/cbf/VIT.jpg",
}


def escudo_do_time(sigla: str, escudo_padrao: str | None = "") -> str:
    escudo_local = ESCUDOS_LOCAIS.get(sigla.upper())
    if escudo_local:
        return escudo_local
    return escudo_padrao or ""


def aplicar_escudos_locais(classificacao: list[dict[str, Any]]) -> None:
    for time in classificacao:
        sigla = str(time.get("sigla") or "").upper()
        if sigla in ESCUDOS_LOCAIS:
            time["escudo"] = ESCUDOS_LOCAIS[sigla]
