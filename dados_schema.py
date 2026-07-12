from __future__ import annotations

import re
from typing import Any

from normalizacao import calcular_aproveitamento


class DadosInvalidosError(ValueError):
    """Erro de validacao para estrutura e regras dos dados do dashboard."""


_COR_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def _validar_campos_obrigatorios(item: dict[str, Any], campos: tuple[str, ...], contexto: str) -> None:
    faltantes = [campo for campo in campos if campo not in item]
    if faltantes:
        raise DadosInvalidosError(f"{contexto}: campos ausentes: {', '.join(faltantes)}")


def _validar_int_nao_negativo(item: dict[str, Any], campo: str, contexto: str) -> int:
    valor = item.get(campo)
    if not isinstance(valor, int) or isinstance(valor, bool):
        raise DadosInvalidosError(f"{contexto}: campo '{campo}' deve ser inteiro")
    if valor < 0:
        raise DadosInvalidosError(f"{contexto}: campo '{campo}' nao pode ser negativo")
    return valor


def _validar_numero_intervalo(item: dict[str, Any], campo: str, minimo: float, maximo: float, contexto: str) -> float:
    valor = item.get(campo)
    if not isinstance(valor, (int, float)) or isinstance(valor, bool):
        raise DadosInvalidosError(f"{contexto}: campo '{campo}' deve ser numero")
    valor_float = float(valor)
    if valor_float < minimo or valor_float > maximo:
        raise DadosInvalidosError(
            f"{contexto}: campo '{campo}' deve estar entre {minimo} e {maximo}"
        )
    return valor_float


def _validar_str_nao_vazia(item: dict[str, Any], campo: str, contexto: str) -> str:
    valor = item.get(campo)
    if not isinstance(valor, str) or not valor.strip():
        raise DadosInvalidosError(f"{contexto}: campo '{campo}' deve ser texto nao vazio")
    return valor


def _validar_classificacao(classificacao: Any) -> list[dict[str, Any]]:
    if not isinstance(classificacao, list) or not classificacao:
        raise DadosInvalidosError("classificacao deve ser uma lista nao vazia")

    campos = (
        "posicao",
        "time",
        "sigla",
        "estado",
        "cor",
        "escudo",
        "jogos",
        "vitorias",
        "empates",
        "derrotas",
        "gols_pro",
        "gols_contra",
        "saldo",
        "pontos",
        "aproveitamento",
    )

    posicoes: set[int] = set()
    siglas: set[str] = set()
    nomes: set[str] = set()
    for indice, time in enumerate(classificacao, start=1):
        contexto = f"classificacao[{indice}]"
        if not isinstance(time, dict):
            raise DadosInvalidosError(f"{contexto}: item deve ser objeto")

        _validar_campos_obrigatorios(time, campos, contexto)
        posicao = _validar_int_nao_negativo(time, "posicao", contexto)
        if posicao == 0:
            raise DadosInvalidosError(f"{contexto}: campo 'posicao' deve ser maior que zero")
        if posicao in posicoes:
            raise DadosInvalidosError(f"{contexto}: posicao duplicada '{posicao}'")
        posicoes.add(posicao)
        if posicao != indice:
            raise DadosInvalidosError(f"{contexto}: lista deve estar ordenada por posicao crescente")

        nome = _validar_str_nao_vazia(time, "time", contexto)
        sigla = _validar_str_nao_vazia(time, "sigla", contexto)
        if nome.casefold() in nomes:
            raise DadosInvalidosError(f"{contexto}: time duplicado '{nome}'")
        if sigla.upper() in siglas:
            raise DadosInvalidosError(f"{contexto}: sigla duplicada '{sigla}'")
        nomes.add(nome.casefold())
        siglas.add(sigla.upper())
        _validar_str_nao_vazia(time, "estado", contexto)

        cor = _validar_str_nao_vazia(time, "cor", contexto)
        if not _COR_HEX_RE.fullmatch(cor):
            raise DadosInvalidosError(f"{contexto}: campo 'cor' deve ser hexadecimal")

        escudo = time.get("escudo")
        if not isinstance(escudo, str):
            raise DadosInvalidosError(f"{contexto}: campo 'escudo' deve ser string")

        jogos = _validar_int_nao_negativo(time, "jogos", contexto)
        vitorias = _validar_int_nao_negativo(time, "vitorias", contexto)
        empates = _validar_int_nao_negativo(time, "empates", contexto)
        derrotas = _validar_int_nao_negativo(time, "derrotas", contexto)
        gols_pro = _validar_int_nao_negativo(time, "gols_pro", contexto)
        gols_contra = _validar_int_nao_negativo(time, "gols_contra", contexto)
        saldo = time.get("saldo")
        pontos = time.get("pontos")

        if not isinstance(saldo, int) or isinstance(saldo, bool):
            raise DadosInvalidosError(f"{contexto}: campo 'saldo' deve ser inteiro")
        if not isinstance(pontos, int) or isinstance(pontos, bool):
            raise DadosInvalidosError(f"{contexto}: campo 'pontos' deve ser inteiro")

        aproveitamento = _validar_numero_intervalo(time, "aproveitamento", 0.0, 100.0, contexto)

        if jogos != vitorias + empates + derrotas:
            raise DadosInvalidosError(
                f"{contexto}: jogos deve ser igual a vitorias + empates + derrotas"
            )
        if pontos != vitorias * 3 + empates:
            raise DadosInvalidosError(
                f"{contexto}: pontos deve ser igual a vitorias*3 + empates"
            )
        if saldo != gols_pro - gols_contra:
            raise DadosInvalidosError(
                f"{contexto}: saldo deve ser igual a gols_pro - gols_contra"
            )

        aproveitamento_esperado = calcular_aproveitamento(pontos, jogos)
        if round(aproveitamento, 1) != aproveitamento_esperado:
            raise DadosInvalidosError(
                f"{contexto}: aproveitamento inconsistente com jogos e pontos"
            )

    return classificacao


def _validar_artilharia(artilharia: Any, siglas_classificacao: set[str]) -> list[dict[str, Any]]:
    if not isinstance(artilharia, list) or not artilharia:
        raise DadosInvalidosError("artilharia deve ser uma lista nao vazia")

    campos = ("jogador", "time", "sigla", "posicao", "gols")
    gols_anteriores: int | None = None
    for indice, jogador in enumerate(artilharia, start=1):
        contexto = f"artilharia[{indice}]"
        if not isinstance(jogador, dict):
            raise DadosInvalidosError(f"{contexto}: item deve ser objeto")

        _validar_campos_obrigatorios(jogador, campos, contexto)
        _validar_str_nao_vazia(jogador, "jogador", contexto)
        _validar_str_nao_vazia(jogador, "time", contexto)
        sigla = _validar_str_nao_vazia(jogador, "sigla", contexto)
        if sigla.upper() not in siglas_classificacao:
            raise DadosInvalidosError(f"{contexto}: sigla '{sigla}' nao existe na classificacao")
        _validar_str_nao_vazia(jogador, "posicao", contexto)
        gols = _validar_int_nao_negativo(jogador, "gols", contexto)
        if gols_anteriores is not None and gols > gols_anteriores:
            raise DadosInvalidosError(f"{contexto}: lista deve estar ordenada por gols decrescente")
        gols_anteriores = gols

    return artilharia


def _validar_info(info: Any, classificacao: list[dict[str, Any]], artilharia: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(info, dict):
        raise DadosInvalidosError("info deve ser objeto")

    campos_obrigatorios = (
        "campeonato",
        "temporada",
        "rodadas_total",
        "rodada_atual",
        "times_total",
        "campeonato_finalizado",
        "lider",
        "lider_pontos",
        "artilheiro",
        "artilheiro_gols",
    )
    _validar_campos_obrigatorios(info, campos_obrigatorios, "info")

    _validar_str_nao_vazia(info, "campeonato", "info")
    _validar_str_nao_vazia(info, "temporada", "info")
    _validar_str_nao_vazia(info, "lider", "info")
    _validar_str_nao_vazia(info, "artilheiro", "info")
    _validar_int_nao_negativo(info, "times_total", "info")
    rodadas_total = _validar_int_nao_negativo(info, "rodadas_total", "info")
    rodada_atual = _validar_int_nao_negativo(info, "rodada_atual", "info")
    _validar_int_nao_negativo(info, "lider_pontos", "info")
    _validar_int_nao_negativo(info, "artilheiro_gols", "info")

    if not isinstance(info["campeonato_finalizado"], bool):
        raise DadosInvalidosError("info.campeonato_finalizado deve ser booleano")
    if rodada_atual > rodadas_total:
        raise DadosInvalidosError("info.rodada_atual nao pode ser maior que info.rodadas_total")
    if info["campeonato_finalizado"] and rodada_atual != rodadas_total:
        raise DadosInvalidosError("info.campeonato_finalizado exige rodada_atual igual a rodadas_total")

    lider = classificacao[0]
    artilheiro_top = artilharia[0]
    if info["times_total"] != len(classificacao):
        raise DadosInvalidosError("info.times_total inconsistente com classificacao")
    if info["lider"] != lider["time"] or info["lider_pontos"] != lider["pontos"]:
        raise DadosInvalidosError("info do lider inconsistente com classificacao")
    if info["artilheiro"] != artilheiro_top["jogador"] or info["artilheiro_gols"] != artilheiro_top["gols"]:
        raise DadosInvalidosError("info do artilheiro inconsistente com artilharia")

    return info


def validar_dados_dashboard(dados: Any) -> dict[str, Any]:
    if not isinstance(dados, dict):
        raise DadosInvalidosError("dados deve ser um objeto JSON")

    for bloco in ("classificacao", "artilharia", "info"):
        if bloco not in dados:
            raise DadosInvalidosError(f"bloco '{bloco}' ausente")

    classificacao = _validar_classificacao(dados["classificacao"])
    siglas_classificacao = {time["sigla"].upper() for time in classificacao}
    artilharia = _validar_artilharia(dados["artilharia"], siglas_classificacao)
    _validar_info(dados["info"], classificacao, artilharia)

    return dados
