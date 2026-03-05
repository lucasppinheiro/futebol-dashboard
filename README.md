# Futebol Dashboard

Dashboard do Brasileirão Série A. Flask no backend, dados em JSON, front com Chart.js.

- Tabela de classificação (ordenável, filtros por zona, busca)
- Artilharia top 20
- Gráficos: pontos, artilheiros, aproveitamento, gols pro/contra
- Página por time (`/time/<sigla>`)
- API: `GET /api/classificacao`, `GET /api/artilharia`, `POST /api/atualizar` (protegido)

## Stack

Python 3, Flask 3, Chart.js 4. Testes: pytest (backend), npm (front).

## Setup

```bash
git clone <repo>
cd futebol-dashboard
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
python gerar_dados.py    # gera data/brasileirao.json se não existir
python app.py
```

Abra http://127.0.0.1:5000 no navegador (só na sua máquina; não fica exposto na internet).

## Variáveis de ambiente

| Variável | Uso |
|----------|-----|
| `DATA_PATH` | Caminho do JSON (default: `data/brasileirao.json`) |
| `FLASK_DEBUG` | `1` ou `0` (default: `1`) |
| `FLASK_HOST` | default `127.0.0.1` |
| `FLASK_PORT` | default `5000` |
| `API_UPDATE_TOKEN` | Token Bearer para `POST /api/atualizar`. Se vazio, rota retorna 501. |
| `FOOTBALL_DATA_TOKEN` | Token da [football-data.org](https://www.football-data.org/) para `atualizar_dados.py` |

Copie `.env.example` para `.env` e preencha as variáveis que for usar.

## Atualizar dados pela API externa

```bash
set FOOTBALL_DATA_TOKEN=seu_token
python atualizar_dados.py
# ou: python atualizar_dados.py --temporada 2026
```

Para atualizar via app (com `API_UPDATE_TOKEN` definido):

```bash
curl -X POST http://127.0.0.1:5000/api/atualizar -H "Authorization: Bearer SEU_TOKEN"
```

## Testes

```bash
# Backend
python -m pytest tests/ -v

# Frontend
npm install && npm test
```

## Estrutura

```
├── app.py              # rotas Flask, cache, error handlers
├── dados_schema.py     # validação do JSON (classificação, artilharia, info)
├── gerar_dados.py      # gera data/brasileirao.json (dados estáticos)
├── atualizar_dados.py  # busca football-data.org e regrava o JSON
├── api_client.py       # cliente da API football-data.org
├── data/brasileirao.json
├── templates/          # index.html, time.html
├── static/css/, static/js/
├── tests/              # test_app.py, test_dados_schema.py, test_gerar_dados.py, js/
├── requirements.txt
├── package.json
└── .env.example
```

## Licença

MIT
