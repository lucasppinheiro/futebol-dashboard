# Futebol Dashboard

[![Data refresh](https://img.shields.io/github/actions/workflow/status/lucassgsantos/futebol-dashboard/refresh-data.yml?label=data%20refresh)](https://github.com/lucassgsantos/futebol-dashboard/actions)
[![Live Demo](https://img.shields.io/badge/demo-Vercel-000000)](https://futebol-dashboard.vercel.app/)

Dashboard responsivo do Campeonato Brasileiro Série A com classificação, artilharia, páginas por clube, gráficos e comparação de desempenho.

**[Abrir demonstração](https://futebol-dashboard.vercel.app/)**

## Destaques técnicos

- Aplicação Flask com geração estática e deploy na Vercel.
- Dados da [football-data.org](https://www.football-data.org/) atualizados automaticamente.
- Validação de schema e gravação atômica para proteger o dataset.
- Testes com pytest, Jest e jsdom executados antes de cada deploy.
- URLs compatíveis com subdiretórios e páginas individuais para os clubes.
- Tema claro/escuro, navegação por teclado e layout responsivo.

## Arquitetura

```text
football-data.org
       |
atualizar_dados.py -> validação -> data/brasileirao.json
                                      |
                               build_static.py
                                      |
                               dist/ -> Vercel
```

O GitHub Actions atualiza e valida os dados a cada hora. A integração Git da Vercel cria previews para branches e publica `main` automaticamente.

## Desenvolvimento local

Requisitos: Python 3.10+ e Node.js 24+.

```bash
git clone https://github.com/lucassgsantos/futebol-dashboard.git
cd futebol-dashboard
python -m venv .venv
```

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
```

macOS/Linux:

```bash
source .venv/bin/activate
cp .env.example .env
```

Instale e execute:

```bash
pip install -r requirements.txt
npm ci
python app.py
```

A aplicação estará em [http://127.0.0.1:5000](http://127.0.0.1:5000). Para buscar dados novos, configure `FOOTBALL_DATA_TOKEN` no `.env` e execute `python atualizar_dados.py`.

## Qualidade e build

```bash
python -m pytest tests -q
npm test
npm audit
python build_static.py
```

Para gerar exatamente o conteúdo servido pela Vercel:

```bash
python build_static.py
```

O resultado é escrito em `dist/`, incluindo páginas dos clubes, APIs JSON, `404.html`, `robots.txt` e `sitemap.xml`.

## Configuração

As variáveis disponíveis estão documentadas em `.env.example`. No GitHub, `FOOTBALL_DATA_TOKEN` deve existir apenas em **Settings > Secrets and variables > Actions**.

## Publicação na Vercel

1. Importe `lucassgsantos/futebol-dashboard` no painel da Vercel.
2. Mantenha o diretório raiz como `.`; o `vercel.json` já define o build e a saída `dist`.
3. Use `main` como branch de produção.
4. Configure `SITE_ORIGIN` caso o domínio final seja diferente de `https://futebol-dashboard.vercel.app`.

Não é necessário cadastrar o token da football-data.org na Vercel: a atualização ocorre no GitHub Actions e o JSON validado é versionado.

Nunca registre tokens no código, no histórico Git ou em arquivos versionados.
