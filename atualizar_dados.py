"""
Busca dados atualizados do Brasileirao e grava em data/brasileirao.json.

Uso:
    python atualizar_dados.py
    python atualizar_dados.py --temporada 2026

Fonte padrao: CBF. Fallback opcional: football-data.org com FOOTBALL_DATA_TOKEN.
Fallback: se a API falhar, mantem os dados locais existentes.
"""

import argparse
import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from api_client import (
    buscar_artilharia,
    buscar_artilharia_cbf,
    buscar_classificacao,
    buscar_classificacao_cbf,
    buscar_classificacao_ge,
    buscar_classificacao_por_rodada,
    buscar_partidas,
    buscar_partidas_ge,
    buscar_rodada_atual_cbf,
    buscar_rodada_atual_football_data,
)
from dados_schema import validar_dados_dashboard
from env_config import carregar_env_local
from gerar_dados import montar_info
from temporada import temporada_brasileirao_atual

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "brasileirao.json")


carregar_env_local()


def _escrever_json_atomico(destino: str | Path, dados: object) -> None:
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destino.parent,
            prefix=f".{destino.name}.",
            suffix=".tmp",
            delete=False,
        ) as arquivo:
            temporario = Path(arquivo.name)
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
            arquivo.write("\n")
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(temporario, destino)
    finally:
        if temporario and temporario.exists():
            temporario.unlink()


def _buscar_dados(temporada: str) -> tuple[list[dict], list[dict], str, str]:
    fonte = os.environ.get("DATA_SOURCE", "cbf").strip().lower()
    if fonte == "football-data":
        return (
            buscar_classificacao(temporada),
            buscar_artilharia(temporada),
            "football-data.org",
            "football-data.org",
        )

    try:
        classificacao = buscar_classificacao_cbf(temporada)
        artilharia = buscar_artilharia_cbf(temporada)
        fonte_classificacao = "CBF"
        try:
            classificacao_ge = buscar_classificacao_ge(temporada)
            siglas_cbf = {time["sigla"] for time in classificacao}
            siglas_ge = {time["sigla"] for time in classificacao_ge}
            if siglas_ge == siglas_cbf and sum(time["jogos"] for time in classificacao_ge) > sum(
                time["jogos"] for time in classificacao
            ):
                classificacao = classificacao_ge
                fonte_classificacao = "ge"
        except Exception as exc:
            logger.warning("Nao foi possivel validar a classificacao no ge: %s", exc)
        return classificacao, artilharia, fonte_classificacao, "CBF"
    except Exception as e:
        logger.warning("Falha ao buscar dados da CBF: %s", e)
        logger.info("Tentando fallback via football-data.org...")
        return (
            buscar_classificacao(temporada),
            buscar_artilharia(temporada),
            "football-data.org",
            "football-data.org",
        )


def _timestamp_atualizacao(dados_base: dict, destino: str | Path | None = None) -> str:
    caminho_destino = Path(destino or OUTPUT_FILE)
    existentes: dict | None = None
    try:
        with caminho_destino.open(encoding="utf-8") as arquivo:
            carregados = json.load(arquivo)
            if isinstance(carregados, dict):
                existentes = carregados
    except (OSError, json.JSONDecodeError):
        existentes = None

    info_existente = dict(existentes.get("info") or {}) if existentes is not None else {}
    info_nova = dict(dados_base["info"])
    info_existente.pop("rodada_confirmada", None)
    info_nova.pop("rodada_confirmada", None)
    historico_existente = existentes.get("classificacao_por_rodada", {}) if existentes is not None else {}
    if existentes is not None and not historico_existente:
        rodada_existente = info_existente.get("rodada_atual")
        if isinstance(rodada_existente, int) and rodada_existente > 0:
            historico_existente = {str(rodada_existente): existentes.get("classificacao")}
    dados_inalterados = existentes is not None and (
        existentes.get("classificacao") == dados_base["classificacao"]
        and historico_existente == dados_base.get("classificacao_por_rodada", {})
        and existentes.get("artilharia") == dados_base["artilharia"]
        and existentes.get("partidas", []) == dados_base["partidas"]
        and info_existente == info_nova
    )

    if dados_inalterados:
        valor_salvo = existentes.get("dados_atualizados_em")
        if isinstance(valor_salvo, str) and valor_salvo:
            return valor_salvo
        try:
            return datetime.fromtimestamp(caminho_destino.stat().st_mtime, tz=timezone.utc).isoformat()
        except OSError:
            pass

    return datetime.now(timezone.utc).isoformat()


def _rodada_atual_salva(destino: str | Path | None = None) -> int | None:
    caminho_destino = Path(destino or OUTPUT_FILE)
    try:
        with caminho_destino.open(encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (OSError, json.JSONDecodeError):
        return None

    rodada = dados.get("info", {}).get("rodada_atual") if isinstance(dados, dict) else None
    return rodada if isinstance(rodada, int) and not isinstance(rodada, bool) else None


def _snapshot_salvo(destino: str | Path | None = None) -> dict:
    caminho_destino = Path(destino or OUTPUT_FILE)
    try:
        with caminho_destino.open(encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (OSError, json.JSONDecodeError):
        return {}
    return dados if isinstance(dados, dict) else {}


def _buscar_rodada_cbf(temporada: str, fonte: str) -> int | None:
    if fonte != "CBF":
        return None
    try:
        return buscar_rodada_atual_cbf(temporada)
    except Exception as exc:
        logger.warning("Nao foi possivel confirmar a rodada pela CBF: %s", exc)
        return None


def _enriquecer_agenda(
    temporada: str,
    snapshot: dict,
    siglas_validas: set[str],
) -> tuple[list[dict], int | None, str | None, bool, str | None]:
    partidas_salvas = snapshot.get("partidas") if isinstance(snapshot.get("partidas"), list) else []
    agenda_atualizada_em = snapshot.get("agenda_atualizada_em")
    token_disponivel = bool((os.environ.get("FOOTBALL_DATA_TOKEN") or "").strip())

    def tentar_ge() -> tuple[list[dict], int | None, str | None, bool, str | None]:
        try:
            partidas_ge = buscar_partidas_ge(temporada)
            siglas_ge = {
                str(sigla).upper()
                for partida in partidas_ge
                for sigla in (partida.get("mandante"), partida.get("visitante"))
            }
            desconhecidas_ge = siglas_ge - siglas_validas
            if desconhecidas_ge:
                raise ValueError(f"Agenda do ge contem siglas desconhecidas: {', '.join(sorted(desconhecidas_ge))}")
            rodadas_encerradas = [partida["rodada"] for partida in partidas_ge if partida["status"] == "encerrada"]
            rodada_ge = max(rodadas_encerradas, default=None)
            return partidas_ge, rodada_ge, datetime.now(timezone.utc).isoformat(), False, "ge"
        except Exception as exc:
            logger.warning("Falha ao atualizar agenda pelo ge: %s", exc)
            return partidas_salvas, None, agenda_atualizada_em, True, None

    if not token_disponivel:
        return tentar_ge()

    rodada_football_data: int | None = None
    try:
        partidas = buscar_partidas(temporada)
        siglas_da_agenda = {
            str(sigla).upper() for partida in partidas for sigla in (partida.get("mandante"), partida.get("visitante"))
        }
        desconhecidas = siglas_da_agenda - siglas_validas
        if desconhecidas:
            raise ValueError(f"Agenda contem siglas desconhecidas: {', '.join(sorted(desconhecidas))}")
    except Exception as exc:
        logger.warning("Falha ao atualizar agenda pelo football-data.org: %s", exc)
        return tentar_ge()

    try:
        rodada_football_data = buscar_rodada_atual_football_data(temporada)
    except Exception as exc:
        logger.warning("Falha ao consultar currentMatchday no football-data.org: %s", exc)

    return partidas, rodada_football_data, datetime.now(timezone.utc).isoformat(), False, "football-data.org"


def _limite_historico_por_atualizacao() -> int:
    try:
        limite = int(os.environ.get("HISTORICO_RODADAS_POR_ATUALIZACAO", "4"))
    except ValueError:
        limite = 4
    return max(1, min(limite, 6))


def _enriquecer_historico(
    temporada: str,
    snapshot: dict,
    classificacao_atual: list[dict],
    *,
    rodada_atual: int,
    partidas: list[dict] | None = None,
) -> tuple[dict[str, list[dict]], str | None, bool]:
    salvo = snapshot.get("classificacao_por_rodada")
    historico = dict(salvo) if isinstance(salvo, dict) else {}
    rodada_atual = max(1, min(int(rodada_atual), 38))
    historico[str(rodada_atual)] = classificacao_atual
    atualizado_em = snapshot.get("historico_atualizado_em")

    def rodadas_pendentes(lista: object) -> set[int]:
        if not isinstance(lista, list):
            return set()
        status_mutaveis = {"agendada", "em_andamento", "intervalo", "adiada", "suspensa"}
        return {
            int(partida["rodada"])
            for partida in lista
            if isinstance(partida, dict)
            and isinstance(partida.get("rodada"), int)
            and 1 <= int(partida["rodada"]) < rodada_atual
            and partida.get("status") in status_mutaveis
        }

    pendentes_anteriores = rodadas_pendentes(snapshot.get("partidas"))
    pendentes_atuais = rodadas_pendentes(partidas)
    revalidacoes_pendentes = {rodada for rodada in pendentes_anteriores | pendentes_atuais if str(rodada) in historico}
    faltantes = [rodada for rodada in range(1, rodada_atual) if str(rodada) not in historico]
    candidatas = faltantes + sorted(revalidacoes_pendentes)
    token_disponivel = bool((os.environ.get("FOOTBALL_DATA_TOKEN") or "").strip())
    if token_disponivel:
        siglas_atuais = {str(time.get("sigla") or "").upper() for time in classificacao_atual}
        houve_atualizacao = False
        for rodada in candidatas[: _limite_historico_por_atualizacao()]:
            try:
                classificacao = buscar_classificacao_por_rodada(temporada, rodada)
                siglas_historicas = {str(time.get("sigla") or "").upper() for time in classificacao}
                if siglas_historicas != siglas_atuais:
                    raise ValueError("classificacao historica possui clubes divergentes")
                historico[str(rodada)] = classificacao
                revalidacoes_pendentes.discard(rodada)
                houve_atualizacao = True
            except Exception as exc:
                logger.warning("Falha ao atualizar classificacao da rodada %d: %s", rodada, exc)
        if houve_atualizacao:
            atualizado_em = datetime.now(timezone.utc).isoformat()

    faltantes_restantes = [rodada for rodada in range(1, rodada_atual) if str(rodada) not in historico]
    desatualizado = bool(faltantes_restantes or revalidacoes_pendentes or pendentes_atuais)
    return historico, atualizado_em if isinstance(atualizado_em, str) else None, desatualizado


def atualizar(temporada: str | None = None, *, destino: str | Path | None = None) -> None:
    temporada = temporada or temporada_brasileirao_atual()
    caminho_destino = Path(destino or OUTPUT_FILE)
    logger.info("Buscando dados da temporada %s...", temporada)

    snapshot = _snapshot_salvo(caminho_destino)
    temporada_snapshot = (snapshot.get("info") or {}).get("temporada") if isinstance(snapshot, dict) else None
    if temporada_snapshot is not None and str(temporada_snapshot) != str(temporada):
        logger.info("Descartando cache da temporada %s ao iniciar %s.", temporada_snapshot, temporada)
        snapshot = {}
    try:
        classificacao, artilharia, fonte_classificacao, fonte_artilharia = _buscar_dados(temporada)
    except Exception as e:
        logger.error("Erro ao buscar dados: %s", e)
        if caminho_destino.exists():
            logger.info("Mantendo dados locais existentes.")
        else:
            logger.warning(
                "Nenhum dado oficial local disponivel. Use 'python gerar_dados.py' somente para fixture local."
            )
        raise

    if not classificacao:
        raise ValueError("API retornou classificacao vazia. Mantendo dados locais.")

    if not artilharia:
        raise ValueError("API retornou artilharia vazia. Mantendo dados locais.")

    rodada_cbf = _buscar_rodada_cbf(temporada, "CBF")
    siglas_validas = {str(time["sigla"]).upper() for time in classificacao}
    partidas, rodada_football_data, agenda_atualizada_em, agenda_desatualizada, fonte_agenda = _enriquecer_agenda(
        temporada, snapshot, siglas_validas
    )
    rodada_salva = (snapshot.get("info") or {}).get("rodada_atual")
    if not isinstance(rodada_salva, int) or isinstance(rodada_salva, bool):
        rodada_salva = None
    rodada_atual = rodada_cbf or rodada_football_data or rodada_salva
    rodada_atual = rodada_atual or max(int(time.get("jogos") or 0) for time in classificacao)
    rodada_confirmada = rodada_cbf is not None or rodada_football_data is not None
    classificacao_por_rodada, historico_atualizado_em, historico_desatualizado = _enriquecer_historico(
        temporada,
        snapshot,
        classificacao,
        rodada_atual=rodada_atual,
        partidas=partidas,
    )

    dados_base = {
        "classificacao": classificacao,
        "classificacao_por_rodada": classificacao_por_rodada,
        "artilharia": artilharia,
        "partidas": partidas,
        "info": montar_info(
            classificacao,
            artilharia,
            temporada,
            rodada_atual=rodada_atual,
            rodada_confirmada=rodada_confirmada,
        ),
    }
    fonte_partidas = fonte_agenda or ((snapshot.get("fontes") or {}).get("partidas") or "Não disponível")
    dados = {
        "classificacao": dados_base["classificacao"],
        "classificacao_por_rodada": dados_base["classificacao_por_rodada"],
        "artilharia": dados_base["artilharia"],
        "partidas": dados_base["partidas"],
        "dados_atualizados_em": _timestamp_atualizacao(dados_base, caminho_destino),
        "dados_verificados_em": datetime.now(timezone.utc).isoformat(),
        "dados_desatualizados": False,
        "agenda_desatualizada": agenda_desatualizada,
        "historico_desatualizado": historico_desatualizado,
        "fonte": fonte_classificacao,
        "fontes": {
            "classificacao": fonte_classificacao,
            "artilharia": fonte_artilharia,
            "partidas": fonte_partidas,
        },
        "info": dados_base["info"],
    }
    if isinstance(agenda_atualizada_em, str) and agenda_atualizada_em:
        dados["agenda_atualizada_em"] = agenda_atualizada_em
    if isinstance(historico_atualizado_em, str) and historico_atualizado_em:
        dados["historico_atualizado_em"] = historico_atualizado_em

    try:
        validar_dados_dashboard(dados)
    except Exception as e:
        logger.error("Dados da API falharam na validacao: %s", e)
        logger.info("Mantendo dados locais existentes.")
        raise

    _escrever_json_atomico(caminho_destino, dados)

    logger.info("Dados atualizados em: %s", caminho_destino)
    logger.info("Fonte da classificacao: %s", fonte_classificacao)
    logger.info("%d times | %d artilheiros", len(classificacao), len(artilharia))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Atualizar dados do Brasileirao")
    parser.add_argument("--temporada", default=None, help="Temporada (ex: 2026). Padrao: ano atual.")
    args = parser.parse_args()
    try:
        atualizar(args.temporada)
    except Exception as exc:
        raise SystemExit(1) from exc
