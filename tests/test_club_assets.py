import struct
from pathlib import Path

from club_assets import ESCUDOS_LOCAIS


def test_serie_a_usa_vinte_escudos_normalizados_transparentes():
    assert len(ESCUDOS_LOCAIS) == 20

    for caminho_relativo in ESCUDOS_LOCAIS.values():
        assert caminho_relativo.startswith("static/img/escudos/normalizados/")
        caminho = Path(caminho_relativo)
        conteudo = caminho.read_bytes()
        assert conteudo[:8] == b"\x89PNG\r\n\x1a\n"
        largura, altura = struct.unpack(">II", conteudo[16:24])
        assert largura == altura
        assert largura >= 64
        assert conteudo[25] == 6  # RGBA: o fundo externo tem canal alfa.
