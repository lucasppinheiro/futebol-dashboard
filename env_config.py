import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ENV_PATH = os.path.join(BASE_DIR, ".env")


def carregar_env_local(env_path: str | None = None, override: bool = False) -> None:
    caminho = env_path or os.environ.get("ENV_FILE") or DEFAULT_ENV_PATH
    if not os.path.exists(caminho):
        return

    with open(caminho, "r", encoding="utf-8") as arquivo:
        for linha in arquivo:
            conteudo = linha.strip()
            if not conteudo or conteudo.startswith("#") or "=" not in conteudo:
                continue

            chave, valor = conteudo.split("=", 1)
            chave = chave.strip()
            valor = valor.strip()

            if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in {"'", '"'}:
                valor = valor[1:-1]

            if override or not os.environ.get(chave):
                os.environ[chave] = valor
