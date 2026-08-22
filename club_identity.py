NOMES_POPULARES_CBF: dict[str, str] = {
    "PAL": "Palmeiras",
    "FLA": "Flamengo",
    "CAP": "Athletico Paranaense",
    "FLU": "Fluminense",
    "CRU": "Cruzeiro",
    "BAH": "Bahia",
    "RBB": "Red Bull Bragantino",
    "CAM": "Atlético Mineiro",
    "COR": "Corinthians",
    "CFC": "Coritiba SAF",
    "BOT": "Botafogo",
    "VIT": "Vitória",
    "SAO": "São Paulo",
    "SAN": "Santos FC",
    "GRE": "Grêmio",
    "INT": "Internacional",
    "MIR": "Mirassol",
    "REM": "Remo",
    "VAS": "Vasco da Gama Saf",
    "CHA": "Chapecoense",
}

UFS_CBF: dict[str, str] = {
    "PAL": "SP",
    "FLA": "RJ",
    "CAP": "PR",
    "FLU": "RJ",
    "CRU": "MG",
    "BAH": "BA",
    "RBB": "SP",
    "CAM": "MG",
    "COR": "SP",
    "CFC": "PR",
    "BOT": "RJ",
    "VIT": "BA",
    "SAO": "SP",
    "SAN": "SP",
    "GRE": "RS",
    "INT": "RS",
    "MIR": "SP",
    "REM": "PA",
    "VAS": "RJ",
    "CHA": "SC",
}


def nome_popular_cbf(sigla: str, fallback: str = "") -> str:
    return NOMES_POPULARES_CBF.get(sigla.upper(), fallback)


def uf_cbf(sigla: str, fallback: str = "") -> str:
    return UFS_CBF.get(sigla.upper(), fallback)
