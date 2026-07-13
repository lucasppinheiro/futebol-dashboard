from datetime import datetime

from temporada import temporada_brasileirao_atual


def test_usa_ano_da_data_informada():
    assert temporada_brasileirao_atual(datetime(2026, 7, 12)) == "2026"


def test_fronteira_de_virada_de_ano():
    assert temporada_brasileirao_atual(datetime(2025, 12, 31, 23, 59)) == "2025"
    assert temporada_brasileirao_atual(datetime(2026, 1, 1, 0, 0)) == "2026"


def test_sem_argumento_usa_ano_corrente():
    assert temporada_brasileirao_atual() == str(datetime.now().year)
