# Futebol Dashboard

Projeto pessoal para acompanhar o Brasileirao Serie A 2026.

O dashboard reune classificacao, artilharia, paginas por clube, comparador e graficos em um unico lugar. O projeto roda localmente com Flask e tambem gera uma versao estatica pronta para publicar no GitHub Pages.

Site:
[https://lucassgsantos.github.io/futebol-dashboard/](https://lucassgsantos.github.io/futebol-dashboard/)

## Stack

- Python + Flask
- HTML, CSS e JavaScript vanilla
- Chart.js
- pytest
- jest + jsdom
- GitHub Pages
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

A base do projeto e o arquivo `data/brasileirao.json`.

Se `FOOTBALL_DATA_TOKEN` estiver configurada, da para atualizar os dados com:

```bash
python atualizar_dados.py
```

No deploy, o site e estatico. O workflow do repositorio atualiza esse JSON, faz o build e publica no GitHub Pages.

## Variaveis de ambiente

- `FOOTBALL_DATA_TOKEN`
- `API_UPDATE_TOKEN`
- `DATA_AUTO_REFRESH_HOURS`
- `DATA_AUTO_REFRESH_COOLDOWN_MINUTES`
- `FLASK_DEBUG`
- `FLASK_HOST`
- `FLASK_PORT`
- `SITE_BASE_PATH`

O formato esta em `.env.example`.

## Testes

Python:

```bash
python -m pytest tests -q
```

JavaScript:

```bash
npm test
```

## Build estatico

Build local padrao:

```bash
python build_static.py
```

Build para GitHub Pages:

Windows PowerShell:

```powershell
$env:SITE_BASE_PATH = "/futebol-dashboard"
python build_static.py
```

macOS/Linux:

```bash
SITE_BASE_PATH=/futebol-dashboard python build_static.py
```

Saida em `dist/`.

## Automacao

O workflow `.github/workflows/refresh-data-and-deploy.yml` roda periodicamente para:

- atualizar os dados
- commitar o JSON quando houver mudanca
- gerar o build estatico com o prefixo do repositorio
- publicar no GitHub Pages

Secrets esperados no GitHub Actions:

- `FOOTBALL_DATA_TOKEN`

Tambem deixe o Pages configurado para publicar via GitHub Actions nas configuracoes do repositorio.

## Observacoes

- `.env` nao deve ir para o repositorio
- tokens nao devem ser commitados
- se a API atrasar, o site tambem atrasa
- no GitHub Pages, os arquivos JSON ficam disponiveis em `api/*.json`
