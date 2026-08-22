from typing import Any

ESCUDOS_LOCAIS: dict[str, str] = {
    "BAH": "static/img/escudos/normalizados/BAH.png",
    "BOT": "static/img/escudos/normalizados/BOT.png",
    "CAM": "static/img/escudos/normalizados/CAM.png",
    "CAP": "static/img/escudos/normalizados/CAP.png",
    "CFC": "static/img/escudos/normalizados/CFC.png",
    "CHA": "static/img/escudos/normalizados/CHA.png",
    "COR": "static/img/escudos/normalizados/COR.png",
    "CRU": "static/img/escudos/normalizados/CRU.png",
    "FLA": "static/img/escudos/normalizados/FLA.png",
    "FLU": "static/img/escudos/normalizados/FLU.png",
    "GRE": "static/img/escudos/normalizados/GRE.png",
    "INT": "static/img/escudos/normalizados/INT.png",
    "MIR": "static/img/escudos/normalizados/MIR.png",
    "PAL": "static/img/escudos/normalizados/PAL.png",
    "RBB": "static/img/escudos/normalizados/RBB.png",
    "REM": "static/img/escudos/normalizados/REM.png",
    "SAN": "static/img/escudos/normalizados/SAN.png",
    "SAO": "static/img/escudos/normalizados/SAO.png",
    "VAS": "static/img/escudos/normalizados/VAS.png",
    "VIT": "static/img/escudos/normalizados/VIT.png",
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
