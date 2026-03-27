from typing import Any


POSICOES_MAPA: dict[str, str] = {
    "Offence": "Atacante",
    "Attack": "Atacante",
    "Centre-Forward": "Centroavante",
    "Second Striker": "Segundo atacante",
    "Left Winger": "Ponta esquerda",
    "Right Winger": "Ponta direita",
    "Midfield": "Meia",
    "Central Midfield": "Meia central",
    "Attacking Midfield": "Meia ofensivo",
    "Defensive Midfield": "Volante",
    "Defence": "Defensor",
    "Defense": "Defensor",
    "Centre-Back": "Zagueiro",
    "Left-Back": "Lateral-esquerdo",
    "Right-Back": "Lateral-direito",
    "Goalkeeper": "Goleiro",
}


def normalizar_posicao_jogador(posicao: str | None) -> str:
    valor = (posicao or "").strip()
    if not valor:
        return "Atacante"
    return POSICOES_MAPA.get(valor, valor)


def normalizar_dados_dashboard(dados: dict[str, Any]) -> dict[str, Any]:
    for jogador in dados.get("artilharia", []):
        jogador["posicao"] = normalizar_posicao_jogador(jogador.get("posicao"))
    return dados
