# Futebol Dashboard

Dashboard editorial do Brasileirao Serie A 2026 com classificacao, artilharia, comparador de clubes, paginas por time e graficos em Chart.js.

Demo em producao:
[https://futebol-dashboard-brasileirao.netlify.app](https://futebol-dashboard-brasileirao.netlify.app)

## O que o projeto entrega

- Tabela de classificacao com ordenacao, busca, filtros por zona e favoritos salvos em `localStorage`
- Painel visual com tema claro/escuro, cards editoriais e layout responsivo
- Paginas por clube em `/time/<sigla>` com resumo de campanha e radar de desempenho
- Graficos com carregamento sob demanda para reduzir peso inicial da pagina
- Normalizacao de dados da API para evitar mistura de idiomas em posicoes e siglas
- Atualizacao automatica do arquivo local quando a base estiver antiga e houver token configurado

## Stack

- Backend local: Python, Flask e scripts de sincronizacao
- Frontend: HTML, CSS, JavaScript vanilla e Chart.js
- Testes: `pytest`, `jest` e `jsdom`
- Deploy: export estatico via `build_static.py` e publicacao no Netlify
- Automacao: GitHub Actions para refresh horario dos dados e deploy no Netlify

## Como os dados funcionam

Durante o desenvolvimento local, o app Flask serve o arquivo `data/brasileirao.json`.

Quando `FOOTBALL_DATA_TOKEN` estiver configurado, o projeto pode:

- atualizar os dados manualmente com `python atualizar_dados.py`
- tentar refresh automatico quando o arquivo local estiver velho

Variaveis relacionadas:

- `FOOTBALL_DATA_TOKEN`: token da API football-data.org
- `API_UPDATE_TOKEN`: protege `POST /api/atualizar`
- `DATA_AUTO_REFRESH_HOURS`: idade maxima do arquivo local antes de tentar refresh automatico
- `DATA_AUTO_REFRESH_COOLDOWN_MINUTES`: intervalo minimo entre tentativas automaticas

## Executando localmente

Requisitos:

- Python 3.9+
- Node.js 18+ ou superior

1. Clone o repositorio:

```bash
git clone https://github.com/lucassgsantos/futebol-dashboard.git
cd futebol-dashboard
```

2. Crie e ative um ambiente virtual:

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. Instale as dependencias Python:

```bash
pip install -r requirements.txt
```

4. Instale as dependencias JavaScript:

```bash
npm install
```

5. Crie seu arquivo local de ambiente:

```bash
copy .env.example .env
```

No macOS/Linux:

```bash
cp .env.example .env
```

6. Atualize os dados e rode o servidor:

```bash
python atualizar_dados.py
python app.py
```

App local:
[http://127.0.0.1:5000](http://127.0.0.1:5000)

## Testes

Python:

```bash
python -m pytest tests -q
```

JavaScript:

```bash
npx jest tests/js --runInBand
```

## Build estatico para producao

O deploy publicado no Netlify nao roda Flask em runtime. O projeto gera uma versao estatica a partir dos templates e do JSON local atualizado.

Gerar a saida estatica:

```bash
python build_static.py
```

Publicar no Netlify:

```bash
npx netlify deploy --prod
```

O `netlify.toml` usa:

- comando de build: `python build_static.py`
- diretorio publicado: `dist`

## Automacao de atualizacao

O repositorio inclui o workflow `.github/workflows/refresh-data-and-deploy.yml`.

Ele faz:

- atualizacao horaria dos dados via `python atualizar_dados.py`
- commit do `data/brasileirao.json` quando houver mudanca real
- rebuild estatico
- deploy de producao no Netlify

Secrets esperados no GitHub Actions:

- `FOOTBALL_DATA_TOKEN`
- `NETLIFY_AUTH_TOKEN`
- `NETLIFY_SITE_ID`

## Seguranca e higiene do repositorio

- `.env`, `.netlify/` e arquivos locais de anotacao nao vao para o Git
- tokens nao devem ser commitados; use apenas placeholders em `.env.example`
- o endpoint `POST /api/atualizar` deve ser exposto apenas com `API_UPDATE_TOKEN`
- a automacao de producao depende dos secrets configurados no GitHub Actions e nunca deve usar tokens hardcoded no repositorio

## Licenca

MIT
