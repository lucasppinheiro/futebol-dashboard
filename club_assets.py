from typing import Any


ESCUDOS_LOCAIS: dict[str, str] = {
    "CAP": "static/img/escudos/CAP.png",
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
