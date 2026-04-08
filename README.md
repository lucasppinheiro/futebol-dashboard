# Futebol Dashboard

Projeto pessoal para acompanhar o Brasileirão Série A 2026.

Montei esse dashboard para reunir classificação, artilharia, páginas por clube, comparador e alguns gráficos em um lugar só. O projeto roda localmente com Flask e também gera uma versão estática para publicar no Netlify.

Site:
[https://futebol-dashboard-brasileirao.netlify.app](https://futebol-dashboard-brasileirao.netlify.app)

## Stack

- Python + Flask
- HTML, CSS e JavaScript vanilla
- Chart.js
- pytest
- jest + jsdom
- Netlify
- GitHub Actions

## Rodando localmente

Requisitos:

- Python 3.10+
- Node.js 18+

```bash
git clone https://github.com/lucassgsantos/futebol-dashboard.git
cd futebol-dashboard
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
copy .env.example .env
```

macOS/Linux:

```bash
source venv/bin/activate
cp .env.example .env
```

Depois:

```bash
pip install -r requirements.txt
npm install
python atualizar_dados.py
python app.py
```

Local:
[http://127.0.0.1:5000](http://127.0.0.1:5000)

## Dados

A base do projeto é o arquivo `data/brasileirao.json`.

Se `FOOTBALL_DATA_TOKEN` estiver configurada, dá para atualizar os dados com:

```bash
python atualizar_dados.py
```

No deploy, o site é estático. O workflow do repositório atualiza esse JSON, faz o build e publica no Netlify.

## Variáveis de ambiente

- `FOOTBALL_DATA_TOKEN`
- `API_UPDATE_TOKEN`
- `DATA_AUTO_REFRESH_HOURS`
- `DATA_AUTO_REFRESH_COOLDOWN_MINUTES`
- `FLASK_DEBUG`
- `FLASK_HOST`
- `FLASK_PORT`

O formato está em `.env.example`.

## Testes

Python:

```bash
python -m pytest tests -q
```

JavaScript:

```bash
npm test
```

## Build estático

```bash
python build_static.py
```

Saída em `dist/`.

## Automação

O workflow `.github/workflows/refresh-data-and-deploy.yml` roda periodicamente para:

- atualizar os dados
- commitar o JSON quando houver mudança
- gerar o build estático
- publicar no Netlify

Secrets esperados no GitHub Actions:

- `FOOTBALL_DATA_TOKEN`
- `NETLIFY_AUTH_TOKEN`
- `NETLIFY_SITE_ID`

## Observações

- `.env` e `.netlify/` não devem ir para o repositório
- tokens não devem ser commitados
- se a API atrasar, o site também atrasa

