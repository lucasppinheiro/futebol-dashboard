from datetime import datetime


def temporada_brasileirao_atual(agora: datetime | None = None) -> str:
    referencia = agora or datetime.now()
    return str(referencia.year)
