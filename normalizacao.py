from typing import Any

from club_assets import aplicar_escudos_locais

POSICOES_MAPA: dict[str, str] = {
    "Offence": "Atacante",
    "Attack": "Atacante",
    "Attacker": "Atacante",
    "Forward": "Atacante",
    "Centre-Forward": "Centroavante",
    "Second Striker": "Segundo atacante",
    "Left Winger": "Ponta esquerda",
    "Right Winger": "Ponta direita",
    "Midfield": "Meia",
    "Midfielder": "Meia",
    "Central Midfield": "Meia central",
    "Attacking Midfield": "Meia ofensivo",
    "Defensive Midfield": "Volante",
    "Defence": "Defensor",
    "Defense": "Defensor",
    "Defender": "Defensor",
    "Centre-Back": "Zagueiro",
    "Left-Back": "Lateral-esquerdo",
    "Right-Back": "Lateral-direito",
    "Goalkeeper": "Goleiro",
}


def normalizar_posicao_jogador(posicao: str | None) -> str:
    valor = (posicao or "").strip()
    if not valor:
        return "Nao informado"
    return POSICOES_MAPA.get(valor, valor)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalizar_dados_dashboard(dados: dict[str, Any]) -> dict[str, Any]:
    classificacao = dados.get("classificacao")
    if isinstance(classificacao, list):
        aplicar_escudos_locais(classificacao)
        classificacao.sort(key=lambda time: _safe_int(time.get("posicao"), 10**9))

    artilharia = dados.get("artilharia")
    if isinstance(artilharia, list):
        for jogador in artilharia:
            jogador["posicao"] = normalizar_posicao_jogador(jogador.get("posicao"))

        artilharia.sort(
            key=lambda jogador: (
                -_safe_int(jogador.get("gols")),
                str(jogador.get("jogador") or ""),
                str(jogador.get("time") or ""),
            )
        )

    return dados
