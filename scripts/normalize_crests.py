"""Gera escudos transparentes e equilibrados sem alterar os arquivos CBF.

O fundo removido precisa ser claro, neutro e estar conectado a uma borda. Isso
preserva as areas brancas internas dos escudos. Depois do recorte das margens
externas, a arte inteira e redimensionada proporcionalmente e centralizada em
uma tela transparente quadrada.
"""

from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_ROOT / "static" / "img" / "escudos" / "cbf"
OUTPUT_DIR = PROJECT_ROOT / "static" / "img" / "escudos" / "normalizados"

BACKGROUND_MIN_CHANNEL = 230
BACKGROUND_MAX_CHROMA = 18
PADDING_RATIO = 1 / 32


def _parece_fundo(pixel: tuple[int, int, int]) -> bool:
    """Aceita apenas tons muito claros e praticamente neutros."""
    return min(pixel) >= BACKGROUND_MIN_CHANNEL and max(pixel) - min(pixel) <= BACKGROUND_MAX_CHROMA


def _mascara_fundo_externo(imagem: Image.Image) -> Image.Image:
    """Encontra somente o fundo claro alcancavel pelas bordas da imagem."""
    rgb = imagem.convert("RGB")
    largura, altura = rgb.size
    pixels = rgb.load()
    visitado = bytearray(largura * altura)
    fila: deque[tuple[int, int]] = deque()

    def adicionar(x: int, y: int) -> None:
        indice = y * largura + x
        if not visitado[indice] and _parece_fundo(pixels[x, y]):
            visitado[indice] = 1
            fila.append((x, y))

    for x in range(largura):
        adicionar(x, 0)
        adicionar(x, altura - 1)
    for y in range(altura):
        adicionar(0, y)
        adicionar(largura - 1, y)

    while fila:
        x, y = fila.popleft()
        if x:
            adicionar(x - 1, y)
        if x + 1 < largura:
            adicionar(x + 1, y)
        if y:
            adicionar(x, y - 1)
        if y + 1 < altura:
            adicionar(x, y + 1)

    alpha = Image.new("L", (largura, altura), 255)
    alpha_pixels = alpha.load()
    for indice, removido in enumerate(visitado):
        if removido:
            alpha_pixels[indice % largura, indice // largura] = 0
    return alpha


def normalizar_escudo(origem: Path, destino: Path) -> None:
    imagem = Image.open(origem).convert("RGBA")
    imagem.putalpha(_mascara_fundo_externo(imagem))

    limites = imagem.getchannel("A").getbbox()
    if limites is None:
        raise ValueError(f"Nenhuma arte encontrada em {origem}")

    arte = imagem.crop(limites)
    largura, altura = arte.size
    maior_dimensao = max(largura, altura)
    margem = max(2, round(maior_dimensao * PADDING_RATIO))
    tamanho_canvas = maior_dimensao + 2 * margem

    canvas = Image.new("RGBA", (tamanho_canvas, tamanho_canvas), (0, 0, 0, 0))
    posicao = ((tamanho_canvas - largura) // 2, (tamanho_canvas - altura) // 2)
    canvas.alpha_composite(arte, posicao)

    destino.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destino, format="PNG", optimize=True)


def main() -> None:
    origens = sorted(SOURCE_DIR.glob("*.jpg"))
    if len(origens) != 20:
        raise RuntimeError(f"Esperados 20 escudos CBF; encontrados {len(origens)}")

    for origem in origens:
        normalizar_escudo(origem, OUTPUT_DIR / f"{origem.stem}.png")


if __name__ == "__main__":
    main()
