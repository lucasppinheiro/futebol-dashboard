from typing import Any

from club_assets import aplicar_escudos_locais
from club_identity import nome_popular_cbf, uf_cbf
from dados_schema import DadosInvalidosError

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


def _validar_forma_dashboard(dados: Any) -> None:
    if not isinstance(dados, dict):
        raise DadosInvalidosError("dados deve ser um objeto")

    for bloco in ("classificacao", "artilharia"):
        itens = dados.get(bloco)
        if not isinstance(itens, list):
            raise DadosInvalidosError(f"{bloco} deve ser uma lista")
        for indice, item in enumerate(itens, start=1):
            if not isinstance(item, dict):
                raise DadosInvalidosError(f"{bloco}[{indice}] deve ser um objeto")

    if not isinstance(dados.get("info"), dict):
        raise DadosInvalidosError("info deve ser um objeto")


def normalizar_dados_dashboard(dados: dict[str, Any]) -> dict[str, Any]:
    _validar_forma_dashboard(dados)
    classificacao = dados.get("classificacao")
    for time in classificacao:
        sigla = str(time.get("sigla") or "").upper()
        time["time"] = nome_popular_cbf(sigla, str(time.get("time") or ""))
        time["estado"] = uf_cbf(sigla, str(time.get("estado") or ""))
    aplicar_escudos_locais(classificacao)
    classificacao.sort(key=lambda time: _safe_int(time.get("posicao"), 10**9))

    info = dados.get("info")
    if classificacao:
        jogos = [_safe_int(time.get("jogos")) for time in classificacao]
        jogos_minimos = min(jogos)
        jogos_maximos = max(jogos)
        rodada_confirmada = jogos_minimos == jogos_maximos
        info.setdefault("rodada_confirmada", rodada_confirmada)
        info.setdefault("jogos_minimos", jogos_minimos)
        info.setdefault("jogos_maximos", jogos_maximos)

    artilharia = dados.get("artilharia")
    for jogador in artilharia:
        sigla = str(jogador.get("sigla") or "").upper()
        jogador["time"] = nome_popular_cbf(sigla, str(jogador.get("time") or ""))
        jogador["posicao"] = normalizar_posicao_jogador(jogador.get("posicao"))

    artilharia.sort(
        key=lambda jogador: (
            -_safe_int(jogador.get("gols")),
            str(jogador.get("jogador") or ""),
            str(jogador.get("time") or ""),
        )
    )

    partidas = dados.setdefault("partidas", [])
    partidas.sort(
        key=lambda partida: (
            _safe_int(partida.get("rodada"), 10**9),
            str(partida.get("inicio_em") or ""),
            _safe_int(partida.get("id"), 10**9),
        )
    )

    historico = dados.setdefault("classificacao_por_rodada", {})
    if not isinstance(historico, dict):
        raise DadosInvalidosError("classificacao_por_rodada deve ser objeto")
    for classificacao_historica in historico.values():
        if not isinstance(classificacao_historica, list):
            continue
        for time in classificacao_historica:
            if not isinstance(time, dict):
                continue
            sigla = str(time.get("sigla") or "").upper()
            time["time"] = nome_popular_cbf(sigla, str(time.get("time") or ""))
            time["estado"] = uf_cbf(sigla, str(time.get("estado") or ""))
        aplicar_escudos_locais(classificacao_historica)
        classificacao_historica.sort(key=lambda time: _safe_int(time.get("posicao"), 10**9))

    rodada_atual = _safe_int(info.get("rodada_atual"))
    if classificacao and rodada_atual > 0:
        historico[str(rodada_atual)] = classificacao
    dados.setdefault(
        "historico_desatualizado",
        any(str(rodada) not in historico for rodada in range(1, rodada_atual)),
    )

    fonte_legada = str(dados.get("fonte") or "Fonte não informada")
    dados.setdefault(
        "fontes",
        {
            "classificacao": fonte_legada,
            "artilharia": fonte_legada,
            "partidas": "Não disponível",
        },
    )
    dados.setdefault("agenda_desatualizada", not bool(partidas))

    if classificacao:
        info["lider"] = classificacao[0].get("time")
    if artilharia:
        info["artilheiro"] = artilharia[0].get("jogador")
        info["artilheiro_gols"] = artilharia[0].get("gols")

    return dados
