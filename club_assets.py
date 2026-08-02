from typing import Any

ESCUDOS_LOCAIS: dict[str, str] = {
    "BAH": "static/img/escudos/BAH.jpg",
    "BOT": "static/img/escudos/BOT.gif",
    "CAM": "static/img/escudos/CAM.jpg",
    "CAP": "static/img/escudos/CAP.png",
    "CFC": "static/img/escudos/CFC.jpg",
    "CHA": "static/img/escudos/CHA.svg",
    "COR": "static/img/escudos/COR.jpg",
    "CRU": "static/img/escudos/CRU.gif",
    "FLA": "static/img/escudos/FLA.gif",
    "FLU": "static/img/escudos/FLU.gif",
    "GRE": "static/img/escudos/GRE.jpg",
    "INT": "static/img/escudos/INT.gif",
    "MIR": "static/img/escudos/MIR.svg",
    "PAL": "static/img/escudos/PAL.gif",
    "RBB": "static/img/escudos/RBB.svg",
    "REM": "static/img/escudos/REM.svg",
    "SAN": "static/img/escudos/SAN.gif",
    "SAO": "static/img/escudos/SAO.jpg",
    "SPO": "static/img/escudos/SPO.gif",
    "VAS": "static/img/escudos/VAS.gif",
    "VIT": "static/img/escudos/VIT.jpg",
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
