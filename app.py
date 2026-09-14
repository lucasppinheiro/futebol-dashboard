import json
import logging
import os
import re
import secrets
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from flask import Flask, has_request_context, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from dados_schema import DadosInvalidosError, validar_dados_dashboard
from env_config import carregar_env_local
from normalizacao import normalizar_dados_dashboard
from temporada import temporada_brasileirao_atual

carregar_env_local()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.environ.get("DATA_PATH", os.path.join(BASE_DIR, "data", "brasileirao.json"))
_ABSOLUTE_URL_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def normalizar_site_base_path(base_path: str | None) -> str:
    valor = (base_path or "").strip()
    if not valor or valor == "/":
        return ""
    return "/" + valor.strip("/")


app = Flask(__name__)
app.config["SITE_BASE_PATH"] = normalizar_site_base_path(os.environ.get("SITE_BASE_PATH"))


def site_url(path: str = "") -> str:
    base_path = normalizar_site_base_path(app.config.get("SITE_BASE_PATH"))
    destino = (path or "").strip()

    if not destino:
        return f"{base_path}/" if base_path else "/"

    if _ABSOLUTE_URL_RE.match(destino) or destino.startswith("//"):
        return destino

    if destino.startswith("#"):
        raiz = f"{base_path}/" if base_path else "/"
        return f"{raiz}{destino}"

    destino_normalizado = destino.lstrip("/")
    url = f"{base_path}/{destino_normalizado}" if base_path else f"/{destino_normalizado}"
    if destino.endswith("/") and not url.endswith("/"):
        url = f"{url}/"
    return url


def public_url(path: str = "") -> str:
    destino = site_url(path)
    if _ABSOLUTE_URL_RE.match(destino) or destino.startswith("//"):
        return destino

    origem = (os.environ.get("SITE_ORIGIN") or "https://futebol-dashboard.vercel.app").strip().rstrip("/")
    return f"{origem}/{destino.lstrip('/')}"


def asset_url(path: str) -> str:
    """Retorna um asset local com versão baseada no arquivo para invalidar cache."""
    url = site_url(path)
    destino = (path or "").strip().lstrip("/")
    if not destino.startswith("static/"):
        return url

    caminho = os.path.join(BASE_DIR, *destino.split("/"))
    try:
        versao = format(os.stat(caminho).st_mtime_ns, "x")
    except OSError:
        return url
    separador = "&" if "?" in url else "?"
    return f"{url}{separador}v={versao}"


app.jinja_env.globals["site_url"] = site_url
app.jinja_env.globals["public_url"] = public_url
app.jinja_env.globals["asset_url"] = asset_url

_dados_cache: dict | None = None
_dados_cache_chave: tuple[str, int] | None = None
_dados_cache_lock = threading.Lock()
_ultimo_refresh_automatico: float = 0.0
_refresh_estado_lock = threading.Lock()
_refresh_em_andamento = False
_refresh_threads: set[threading.Thread] = set()


def limpar_cache() -> None:
    """Limpa o cache de dados."""
    global _dados_cache, _dados_cache_chave
    with _dados_cache_lock:
        _dados_cache = None
        _dados_cache_chave = None


def _caminho_dados(caminho: str | os.PathLike[str] | None = None) -> str:
    return os.path.abspath(os.fspath(caminho if caminho is not None else DATA_PATH))


def _ler_numero_env(nome: str, padrao: float) -> float:
    bruto = (os.environ.get(nome) or "").strip()
    if not bruto:
        return padrao
    try:
        return float(bruto)
    except ValueError:
        logger.warning("Valor invalido em %s=%r. Usando padrao %s.", nome, bruto, padrao)
        return padrao


def _refresh_automatico_horas() -> float:
    return max(0.0, _ler_numero_env("DATA_AUTO_REFRESH_HOURS", 6.0))


def _refresh_automatico_cooldown_segundos() -> float:
    minutos = max(0.0, _ler_numero_env("DATA_AUTO_REFRESH_COOLDOWN_MINUTES", 15.0))
    return minutos * 60.0


def _token_football_data_disponivel() -> bool:
    return bool((os.environ.get("FOOTBALL_DATA_TOKEN") or "").strip())


def _refresh_automatico_disponivel() -> bool:
    if _refresh_automatico_horas() <= 0:
        return False

    fonte = (os.environ.get("DATA_SOURCE") or "cbf").strip().lower()
    return fonte != "football-data" or _token_football_data_disponivel()


def _dados_estao_desatualizados(mtime: float, agora: float | None = None) -> bool:
    horas = _refresh_automatico_horas()
    if horas <= 0:
        return False
    idade_segundos = max(0.0, (time.time() if agora is None else agora) - mtime)
    return idade_segundos >= horas * 3600.0


def _timestamp_frescor_dados(dados: dict[str, Any], fallback_mtime: float | None = None) -> float | None:
    for campo in ("dados_verificados_em", "dados_atualizados_em"):
        valor = dados.get(campo)
        if not isinstance(valor, str):
            continue
        try:
            timestamp = datetime.fromisoformat(valor.replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            return timestamp.timestamp()
        except ValueError:
            continue
    return fallback_mtime


def dados_dashboard_desatualizados(
    dados: dict[str, Any],
    *,
    fallback_mtime: float | None = None,
    agora: float | None = None,
) -> bool:
    """Indica apenas uma desatualizacao explicitamente confirmada.

    A idade do arquivo orienta o refresh automatico, mas nao basta para
    afirmar que o campeonato mudou. Sem um sinal explicito do fornecedor, a
    interface mostra a data da ultima atualizacao sem criar um alerta falso.
    """
    del fallback_mtime, agora
    return dados.get("dados_desatualizados") is True


def dados_dashboard_refresh_necessario(
    dados: dict[str, Any],
    *,
    fallback_mtime: float | None = None,
    agora: float | None = None,
) -> bool:
    """Indica se vale tentar consultar a fonte novamente por idade do snapshot."""
    timestamp = _timestamp_frescor_dados(dados, fallback_mtime=fallback_mtime)
    if timestamp is None:
        return True
    return _dados_estao_desatualizados(timestamp, agora=agora)


def _reservar_refresh(*, automatico: bool) -> bool:
    """Reserva o unico refresh do processo antes de qualquer trabalho externo."""
    global _ultimo_refresh_automatico, _refresh_em_andamento

    with _refresh_estado_lock:
        if _refresh_em_andamento:
            return False
        if automatico:
            cooldown = _refresh_automatico_cooldown_segundos()
            agora = time.time()
            if cooldown > 0 and _ultimo_refresh_automatico != 0.0:
                if agora - _ultimo_refresh_automatico < cooldown:
                    return False
            _ultimo_refresh_automatico = agora
        _refresh_em_andamento = True
        return True


def _liberar_refresh() -> None:
    global _refresh_em_andamento
    with _refresh_estado_lock:
        _refresh_em_andamento = False


def _executar_refresh(destino: str, temporada: str) -> None:
    from atualizar_dados import atualizar

    atualizar(temporada, destino=destino)
    limpar_cache()


def _refresh_em_backgroundo(
    destino: str,
    temporada: str,
    thread: threading.Thread | None = None,
) -> None:
    global _refresh_em_andamento

    try:
        _executar_refresh(destino, temporada)
        logger.info("Refresh automatico concluido com sucesso.")
    except Exception as e:
        logger.warning("Refresh automatico falhou. Mantendo cache local atual: %s", e)
    finally:
        with _refresh_estado_lock:
            _refresh_em_andamento = False
            _refresh_threads.discard(thread or threading.current_thread())


def _tentar_refresh_automatico(
    caminho: str | os.PathLike[str] | None = None,
    mtime_ns: int | None = None,
    *,
    dados: dict[str, Any] | None = None,
) -> None:
    """Agenda uma atualização daemon sem bloquear a requisição que leu o snapshot."""
    if app.config.get("TESTING"):
        return

    if not _refresh_automatico_disponivel():
        return

    destino = _caminho_dados(caminho)
    if mtime_ns is None:
        try:
            mtime_ns = os.stat(destino).st_mtime_ns
        except FileNotFoundError:
            logger.info("Arquivo de dados nao existe. Tentando gerar dados atualizados automaticamente.")
    if mtime_ns is not None:
        mtime = mtime_ns / 1_000_000_000
        refresh_necessario = (
            dados_dashboard_refresh_necessario(dados, fallback_mtime=mtime)
            if dados is not None
            else _dados_estao_desatualizados(mtime)
        )
        if not refresh_necessario:
            return
        logger.info("Dados locais estao desatualizados. Agendando refresh automatico.")

    if not _reservar_refresh(automatico=True):
        return

    global _refresh_em_andamento
    thread: threading.Thread | None = None
    try:
        temporada = temporada_brasileirao_atual()

        def executar_refresh(destino_capturado: str, temporada_capturada: str) -> None:
            _refresh_em_backgroundo(destino_capturado, temporada_capturada, thread)

        thread = threading.Thread(
            target=executar_refresh,
            args=(destino, temporada),
            daemon=True,
        )
        with _refresh_estado_lock:
            _refresh_threads.add(thread)
        thread.start()
    except Exception as e:
        with _refresh_estado_lock:
            _refresh_em_andamento = False
            if thread is not None:
                _refresh_threads.discard(thread)
        logger.warning("Nao foi possivel iniciar refresh automatico: %s", e)


def carregar_dados(*, permitir_refresh: bool = True) -> dict[str, Any]:
    global _dados_cache, _dados_cache_chave

    destino = _caminho_dados()
    try:
        stat = os.stat(destino)
    except FileNotFoundError as erro:
        if permitir_refresh:
            _tentar_refresh_automatico(destino)
        raise FileNotFoundError(
            f"Dados oficiais nao encontrados em {destino}. Execute: python atualizar_dados.py. "
            "Use python gerar_dados.py apenas para fixture local."
        ) from erro

    chave = (destino, stat.st_mtime_ns)
    with _dados_cache_lock:
        if _dados_cache is not None and _dados_cache_chave == chave:
            dados = _dados_cache
        else:
            try:
                with open(destino, encoding="utf-8") as arquivo:
                    arquivo_stat = os.fstat(arquivo.fileno())
                    data: Any = json.load(arquivo)
            except FileNotFoundError as erro:
                if permitir_refresh:
                    _tentar_refresh_automatico(destino)
                raise FileNotFoundError(
                    f"Dados oficiais nao encontrados em {destino}. Execute: python atualizar_dados.py. "
                    "Use python gerar_dados.py apenas para fixture local."
                ) from erro

            normalizar_dados_dashboard(data)
            validar_dados_dashboard(data)
            chave = (destino, arquivo_stat.st_mtime_ns)
            try:
                chave_atual = (destino, os.stat(destino).st_mtime_ns)
            except FileNotFoundError:
                chave_atual = None
            if chave_atual == chave:
                _dados_cache = data
                _dados_cache_chave = chave
            dados = data

    if permitir_refresh:
        _tentar_refresh_automatico(*chave, dados=dados)
    return dados


def _is_api_request() -> bool:
    return request.path.startswith("/api/")


def formatar_atualizacao_dados(dados: dict[str, Any] | None = None) -> str:
    atualizado_em: datetime | None = None
    valor_salvo = dados.get("dados_atualizados_em") if dados else None

    if isinstance(valor_salvo, str):
        try:
            atualizado_em = datetime.fromisoformat(valor_salvo.replace("Z", "+00:00"))
        except ValueError:
            atualizado_em = None

    if atualizado_em is None:
        try:
            atualizado_em = datetime.fromtimestamp(os.path.getmtime(DATA_PATH), tz=timezone.utc)
        except OSError:
            return "data indisponível"

    if atualizado_em.tzinfo is None:
        atualizado_em = atualizado_em.replace(tzinfo=timezone.utc)

    horario_brasilia = timezone(timedelta(hours=-3))
    return atualizado_em.astimezone(horario_brasilia).strftime("%d/%m/%Y")


def status_dados_dashboard(dados: dict[str, Any]) -> dict[str, Any]:
    return {
        "desatualizados": dados_dashboard_desatualizados(dados),
        "refresh_necessario": dados_dashboard_refresh_necessario(dados),
        "fonte": dados.get("fonte") or "Fonte não informada",
    }


_MESES_CURTOS = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")
_STATUS_PARTIDA_LABEL = {
    "agendada": "Agendado",
    "em_andamento": "Em andamento",
    "intervalo": "Intervalo",
    "encerrada": "Encerrado",
    "adiada": "Adiado",
    "suspensa": "Suspenso",
    "cancelada": "Cancelado",
}


def _instante_partida(partida: dict[str, Any]) -> datetime:
    valor = str(partida.get("inicio_em") or "")
    try:
        instante = datetime.fromisoformat(valor.replace("Z", "+00:00"))
    except ValueError:
        return datetime.max.replace(tzinfo=timezone.utc)
    if instante.tzinfo is None:
        instante = instante.replace(tzinfo=timezone.utc)
    return instante


def _partida_para_exibicao(partida: dict[str, Any], times_por_sigla: dict[str, dict]) -> dict[str, Any]:
    instante_local = _instante_partida(partida).astimezone(timezone(timedelta(hours=-3)))
    return {
        **partida,
        "mandante_time": times_por_sigla.get(partida.get("mandante"), {"time": partida.get("mandante"), "escudo": ""}),
        "visitante_time": times_por_sigla.get(
            partida.get("visitante"), {"time": partida.get("visitante"), "escudo": ""}
        ),
        "data_curta": f"{instante_local.day:02d} {_MESES_CURTOS[instante_local.month - 1]}",
        "hora": instante_local.strftime("%H:%M"),
        "status_label": _STATUS_PARTIDA_LABEL.get(str(partida.get("status")), "A confirmar"),
    }


def _rodada_inicial(dados: dict[str, Any]) -> int:
    atual = int(dados["info"]["rodada_atual"])
    total = int(dados["info"]["rodadas_total"])
    if not has_request_context():
        return atual
    try:
        solicitada = int(request.args.get("rodada", atual))
    except (TypeError, ValueError):
        return atual
    return solicitada if 1 <= solicitada <= total else atual


def _classificacao_da_rodada(dados: dict[str, Any], rodada: int) -> list[dict[str, Any]] | None:
    historico = dados.get("classificacao_por_rodada")
    if isinstance(historico, dict):
        classificacao = historico.get(str(rodada)) or historico.get(rodada)
        if isinstance(classificacao, list) and classificacao:
            return classificacao
    if rodada == int(dados["info"]["rodada_atual"]):
        return dados["classificacao"]
    return None


def _calcular_leituras_campeonato(dados: dict[str, Any]) -> dict[str, Any]:
    """Deriva os gráficos somente de placares finais já validados no snapshot."""
    classificacao = dados["classificacao"]
    clubes = {time["sigla"]: time for time in classificacao}
    ordem = {time["sigla"]: indice for indice, time in enumerate(classificacao)}
    mandos = {
        sigla: {
            "time": time["time"],
            "sigla": sigla,
            "jogos_casa": 0,
            "pontos_casa": 0,
            "jogos_fora": 0,
            "pontos_fora": 0,
        }
        for sigla, time in clubes.items()
    }
    resultados = {sigla: [] for sigla in clubes}
    rodadas: dict[int, dict[str, int]] = {}
    encerradas: list[dict[str, Any]] = []

    for partida in dados.get("partidas", []):
        if not isinstance(partida, dict) or partida.get("status") != "encerrada":
            continue
        mandante = partida.get("mandante")
        visitante = partida.get("visitante")
        placar = partida.get("placar") or {}
        gols_mandante = placar.get("mandante")
        gols_visitante = placar.get("visitante")
        if (
            mandante not in clubes
            or visitante not in clubes
            or not isinstance(gols_mandante, int)
            or isinstance(gols_mandante, bool)
            or not isinstance(gols_visitante, int)
            or isinstance(gols_visitante, bool)
            or gols_mandante < 0
            or gols_visitante < 0
        ):
            continue
        encerradas.append(partida)

    encerradas.sort(key=lambda partida: (_instante_partida(partida), int(partida.get("id") or 0)))
    for partida in encerradas:
        mandante = partida["mandante"]
        visitante = partida["visitante"]
        gols_mandante = partida["placar"]["mandante"]
        gols_visitante = partida["placar"]["visitante"]
        rodada = int(partida["rodada"])
        resumo_rodada = rodadas.setdefault(rodada, {"gols": 0, "jogos": 0})
        resumo_rodada["gols"] += gols_mandante + gols_visitante
        resumo_rodada["jogos"] += 1

        mandos[mandante]["jogos_casa"] += 1
        mandos[visitante]["jogos_fora"] += 1
        if gols_mandante > gols_visitante:
            mandos[mandante]["pontos_casa"] += 3
            resultado_mandante, resultado_visitante = "V", "D"
        elif gols_mandante < gols_visitante:
            mandos[visitante]["pontos_fora"] += 3
            resultado_mandante, resultado_visitante = "D", "V"
        else:
            mandos[mandante]["pontos_casa"] += 1
            mandos[visitante]["pontos_fora"] += 1
            resultado_mandante = resultado_visitante = "E"
        resultados[mandante].append(resultado_mandante)
        resultados[visitante].append(resultado_visitante)

    def percentual(pontos: int, jogos: int) -> float | None:
        return round(pontos / (jogos * 3) * 100, 1) if jogos else None

    leitura_mandos = []
    leitura_forma = []
    for sigla, resumo in mandos.items():
        if resumo["jogos_casa"] or resumo["jogos_fora"]:
            leitura_mandos.append(
                {
                    **resumo,
                    "aproveitamento_casa": percentual(resumo["pontos_casa"], resumo["jogos_casa"]),
                    "aproveitamento_fora": percentual(resumo["pontos_fora"], resumo["jogos_fora"]),
                    "aproveitamento_total": percentual(
                        resumo["pontos_casa"] + resumo["pontos_fora"],
                        resumo["jogos_casa"] + resumo["jogos_fora"],
                    ),
                }
            )
        ultimos = resultados[sigla][-5:]
        if ultimos:
            pontos = sum(3 if resultado == "V" else 1 if resultado == "E" else 0 for resultado in ultimos)
            leitura_forma.append(
                {
                    "time": clubes[sigla]["time"],
                    "sigla": sigla,
                    "pontos": pontos,
                    "jogos": len(ultimos),
                    "resultados": ultimos,
                }
            )

    leitura_mandos.sort(
        key=lambda item: (
            -(item["aproveitamento_total"] or 0),
            ordem[item["sigla"]],
        )
    )
    melhores_casa = sorted(
        leitura_mandos,
        key=lambda item: (
            -(item["aproveitamento_casa"] if item["aproveitamento_casa"] is not None else -1),
            ordem[item["sigla"]],
        ),
    )[:5]
    melhores_fora = sorted(
        leitura_mandos,
        key=lambda item: (
            -(item["aproveitamento_fora"] if item["aproveitamento_fora"] is not None else -1),
            ordem[item["sigla"]],
        ),
    )[:5]
    leitura_forma.sort(key=lambda item: (-item["pontos"], -item["jogos"], ordem[item["sigla"]]))
    gols_por_rodada = [
        {
            "rodada": rodada,
            "gols": resumo["gols"],
            "jogos": resumo["jogos"],
            "completa": resumo["jogos"] == 10,
        }
        for rodada, resumo in sorted(rodadas.items())
    ]

    jogos_esperados = sum(int(time.get("jogos") or 0) for time in classificacao)
    gols_esperados = sum(int(time.get("gols_pro") or 0) for time in classificacao)
    gols_calculados = sum(item["gols"] for item in gols_por_rodada)
    consistente = bool(encerradas) and jogos_esperados == len(encerradas) * 2 and gols_esperados == gols_calculados
    return {
        "disponivel": bool(encerradas),
        "desatualizado": bool(dados.get("agenda_desatualizada")) or (bool(encerradas) and not consistente),
        "consistente_com_classificacao": consistente,
        "partidas_encerradas": len(encerradas),
        "mandos": leitura_mandos,
        "melhores_casa": melhores_casa,
        "melhores_fora": melhores_fora,
        "forma": leitura_forma,
        "gols_por_rodada": gols_por_rodada,
    }


def _contexto_time(dados: dict[str, Any], time_selecionado: dict[str, Any]) -> dict[str, Any]:
    sigla = time_selecionado["sigla"]
    times_por_sigla = {time["sigla"]: time for time in dados["classificacao"]}
    partidas = [
        partida for partida in dados.get("partidas", []) if sigla in {partida.get("mandante"), partida.get("visitante")}
    ]
    partidas.sort(key=_instante_partida)
    encerradas = [partida for partida in partidas if partida.get("status") == "encerrada"]
    futuras = [partida for partida in partidas if partida.get("status") == "agendada"]
    ultimas = list(reversed(encerradas[-5:]))

    forma = []
    for partida in ultimas:
        gols_time = partida["placar"]["mandante"] if partida["mandante"] == sigla else partida["placar"]["visitante"]
        gols_rival = partida["placar"]["visitante"] if partida["mandante"] == sigla else partida["placar"]["mandante"]
        forma.append("V" if gols_time > gols_rival else "E" if gols_time == gols_rival else "D")

    classificacao = dados["classificacao"]

    def media(campo: str) -> float:
        return round(sum(float(time[campo]) for time in classificacao) / len(classificacao), 1)

    medias_liga = {
        "pontos": media("pontos"),
        "gols_pro": media("gols_pro"),
        "gols_contra": media("gols_contra"),
        "aproveitamento": media("aproveitamento"),
    }
    benchmarks = []
    for campo, rotulo, sufixo in (
        ("pontos", "Pontos", ""),
        ("gols_pro", "Gols pró", ""),
        ("aproveitamento", "Aproveitamento", "%"),
    ):
        valor = float(time_selecionado[campo])
        media_liga = float(medias_liga[campo])
        escala = max(valor, media_liga, 1.0)
        benchmarks.append(
            {
                "rotulo": rotulo,
                "valor": f"{time_selecionado[campo]}{sufixo}",
                "media": f"{medias_liga[campo]:g}{sufixo}",
                "largura": round((valor / escala) * 100, 1),
                "media_largura": round((media_liga / escala) * 100, 1),
            }
        )
    adversario = next((time for time in classificacao if time["sigla"] != sigla), None)
    return {
        "ultimas_partidas": [_partida_para_exibicao(partida, times_por_sigla) for partida in ultimas],
        "ultimo_jogo": _partida_para_exibicao(encerradas[-1], times_por_sigla) if encerradas else None,
        "proximo_jogo": _partida_para_exibicao(futuras[0], times_por_sigla) if futuras else None,
        "forma": forma,
        "medias_liga": medias_liga,
        "benchmarks": benchmarks,
        "adversario_comparacao": adversario,
    }


def _destaques_classificacao(classificacao: list[dict[str, Any]]) -> dict[str, Any]:
    if not classificacao:
        return {"melhores_ataques": set(), "melhores_defesas": set()}

    gols_pro = max(clube["gols_pro"] for clube in classificacao)
    gols_contra = min(clube["gols_contra"] for clube in classificacao)
    return {
        "melhores_ataques": {clube["sigla"] for clube in classificacao if clube["gols_pro"] == gols_pro},
        "melhores_defesas": {clube["sigla"] for clube in classificacao if clube["gols_contra"] == gols_contra},
    }


def _contexto_dados(dados: dict[str, Any]) -> dict[str, Any]:
    times_por_sigla = {time["sigla"]: time for time in dados["classificacao"]}
    rodada_inicial = _rodada_inicial(dados)
    classificacao_inicial = dados["classificacao"]
    partidas_rodada = [
        _partida_para_exibicao(partida, times_por_sigla)
        for partida in dados.get("partidas", [])
        if partida.get("rodada") == rodada_inicial
    ]
    return {
        "dados": dados,
        "atualizado_em": formatar_atualizacao_dados(dados),
        "dados_status": status_dados_dashboard(dados),
        "times_por_sigla": times_por_sigla,
        "rodada_inicial": rodada_inicial,
        "classificacao_inicial": classificacao_inicial,
        "classificacao_disponivel": True,
        "partidas_rodada": partidas_rodada,
        "leituras_campeonato": _calcular_leituras_campeonato(dados),
        "destaques_classificacao": _destaques_classificacao(classificacao_inicial),
    }


@app.route("/")
def index():
    dados = carregar_dados()
    return render_template("index.html", **_contexto_dados(dados))


@app.route("/prototipos/header/")
@app.route("/prototipos/header")
def prototipos_header():
    dados = carregar_dados()
    return render_template("prototipos-header.html", **_contexto_dados(dados))


@app.route("/prototipos/header/editorial/")
@app.route("/prototipos/header/editorial")
def prototipo_header_editorial():
    dados = carregar_dados()
    return render_template("prototipo-header-editorial.html", **_contexto_dados(dados), full_width=True)


@app.route("/prototipos/header/editorial-v2/")
@app.route("/prototipos/header/editorial-v2")
def prototipo_header_editorial_v2():
    dados = carregar_dados()
    return render_template("prototipo-header-editorial-v2.html", **_contexto_dados(dados), full_width=True)


@app.route("/time/<sigla>/")
@app.route("/time/<sigla>")
def detalhe_time(sigla: str):
    dados = carregar_dados()
    sigla_upper = sigla.upper()
    time = next((t for t in dados["classificacao"] if t["sigla"] == sigla_upper), None)
    if not time:
        return render_template("404.html", dados=dados), 404
    artilheiros_time = [j for j in dados["artilharia"] if j["sigla"] == sigla_upper]
    return render_template(
        "time.html",
        time=time,
        artilheiros=artilheiros_time,
        **_contexto_dados(dados),
        **_contexto_time(dados, time),
    )


@app.route("/api/classificacao")
def api_classificacao():
    dados = carregar_dados()
    return jsonify(dados["classificacao"])


@app.route("/api/artilharia")
def api_artilharia():
    dados = carregar_dados()
    return jsonify(dados["artilharia"])


@app.route("/api/partidas")
def api_partidas():
    dados = carregar_dados()
    return jsonify(dados["partidas"])


@app.route("/api/atualizar", methods=["POST"])
def api_atualizar():
    token = (os.environ.get("API_UPDATE_TOKEN") or "").strip()
    if not token:
        return jsonify({"erro": "Endpoint nao configurado", "codigo": "NAO_CONFIGURADO"}), 501
    auth = (request.headers.get("Authorization") or "").strip()
    if not secrets.compare_digest(auth, f"Bearer {token}"):
        return jsonify({"erro": "Nao autorizado", "codigo": "NAO_AUTORIZADO"}), 403

    if not _reservar_refresh(automatico=False):
        return jsonify({"erro": "Atualizacao ja em andamento", "codigo": "ATUALIZACAO_EM_ANDAMENTO"}), 409

    try:
        destino = _caminho_dados()
        temporada = temporada_brasileirao_atual()
        _executar_refresh(destino, temporada)
        return jsonify({"status": "ok", "mensagem": "Dados atualizados com sucesso"})
    except (OSError, ConnectionError, ValueError) as e:
        logger.error("Falha ao atualizar dados: %s", e)
        return jsonify({"erro": "Falha ao atualizar dados", "codigo": "ATUALIZACAO_FALHOU"}), 500
    except Exception as e:
        logger.error("Erro inesperado ao atualizar dados: %s", e, exc_info=True)
        return jsonify({"erro": "Falha inesperada ao atualizar dados", "codigo": "ATUALIZACAO_FALHOU"}), 500
    finally:
        _liberar_refresh()


@app.route("/api/health")
def api_health():
    """Endpoint de health check."""
    status = {"status": "ok", "versao": "1.0.0"}
    try:
        dados = carregar_dados(permitir_refresh=False)
        mtime = os.path.getmtime(DATA_PATH)
        status["dados_atualizados_em"] = dados.get(
            "dados_atualizados_em", datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
        )
        status["dados_verificados_em"] = dados.get("dados_verificados_em")
        status["dados_desatualizados"] = dados_dashboard_desatualizados(dados, fallback_mtime=mtime)
        status["dados_refresh_necessario"] = dados_dashboard_refresh_necessario(dados, fallback_mtime=mtime)
        status["fonte"] = dados.get("fonte") or "Fonte não informada"
    except OSError:
        status["dados_atualizados_em"] = None
        status["dados_verificados_em"] = None
        status["dados_desatualizados"] = True
        status["dados_refresh_necessario"] = True
        status["fonte"] = None
    status["refresh_automatico"] = _refresh_automatico_disponivel()
    status["temporada_padrao"] = temporada_brasileirao_atual()
    return jsonify(status)


@app.errorhandler(404)
def pagina_nao_encontrada(_erro):
    if _is_api_request():
        return jsonify({"erro": "Recurso nao encontrado", "codigo": "NAO_ENCONTRADO"}), 404

    try:
        dados = carregar_dados()
    except (FileNotFoundError, json.JSONDecodeError, DadosInvalidosError, KeyError):
        dados = None
    return render_template("404.html", dados=dados), 404


@app.errorhandler(FileNotFoundError)
def erro_arquivo_nao_encontrado(_erro: Exception):
    if _is_api_request():
        return jsonify({"erro": "Dados nao encontrados", "codigo": "DADOS_NAO_ENCONTRADOS"}), 503
    return (
        "<h1>Dados nao encontrados</h1>"
        "<p>Execute no terminal: <code>python atualizar_dados.py</code></p>"
        "<p><code>python gerar_dados.py</code> serve apenas para fixture local.</p>"
        "<p>Depois inicie o servidor novamente com <code>python app.py</code></p>",
        503,
    )


@app.errorhandler(json.JSONDecodeError)
def erro_json_invalido(e: Exception):
    if _is_api_request():
        return jsonify({"erro": "Arquivo de dados com JSON invalido", "codigo": "JSON_INVALIDO"}), 500
    return "<h1>Erro nos dados</h1><p>O arquivo de dados esta corrompido.</p>", 500


@app.errorhandler(DadosInvalidosError)
def erro_dados_invalidos(erro: Exception):
    logger.error("Dados invalidos: %s", erro)
    if _is_api_request():
        return jsonify({"erro": "Arquivo de dados invalido", "codigo": "DADOS_INVALIDOS"}), 500
    return "<h1>Dados invalidos</h1><p>O arquivo de dados nao atende ao formato esperado.</p>", 500


@app.errorhandler(KeyError)
def erro_chave_ausente(erro: Exception):
    logger.error("Chave ausente nos dados: %s", erro)
    if _is_api_request():
        return jsonify({"erro": "Arquivo de dados incompleto", "codigo": "CHAVE_AUSENTE"}), 500
    return "<h1>Erro interno</h1><p>O arquivo de dados esta incompleto.</p>", 500


@app.errorhandler(Exception)
def erro_inesperado(erro: Exception):
    logger.error("Erro inesperado na aplicacao: %s", erro, exc_info=True)
    if isinstance(erro, HTTPException):
        status_code = erro.code or 500
        if not _is_api_request():
            return erro
        resposta = jsonify(
            {
                "erro": "Metodo nao permitido" if status_code == 405 else "Requisicao invalida",
                "codigo": "METODO_NAO_PERMITIDO" if status_code == 405 else "REQUISICAO_INVALIDA",
            }
        )
        resposta.status_code = status_code
        allow = erro.get_response().headers.get("Allow")
        if allow:
            resposta.headers["Allow"] = allow
        return resposta

    if _is_api_request():
        return jsonify({"erro": "Erro interno do servidor", "codigo": "ERRO_INTERNO"}), 500
    return "<h1>Erro interno</h1><p>Ocorreu um erro inesperado.</p>", 500


def _flask_debug_habilitado() -> bool:
    valor = (os.environ.get("FLASK_DEBUG") or "0").strip().lower()
    return valor in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    if not os.path.exists(DATA_PATH):
        raise SystemExit(
            "Dados oficiais nao encontrados. Execute 'python atualizar_dados.py' "
            "ou use 'python gerar_dados.py' apenas para fixture local."
        )

    limpar_cache()

    debug = _flask_debug_habilitado()
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", "5000"))

    logger.info("Futebol Dashboard rodando em http://%s:%d", host, port)
    app.run(debug=debug, port=port, host=host, use_reloader=False)
