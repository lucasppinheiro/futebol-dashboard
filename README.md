# Futebol Dashboard

[![CI](https://img.shields.io/github/actions/workflow/status/lucasppinheiro/futebol-dashboard/ci.yml?label=CI)](https://github.com/lucasppinheiro/futebol-dashboard/actions/workflows/ci.yml)
[![Data refresh](https://img.shields.io/github/actions/workflow/status/lucasppinheiro/futebol-dashboard/refresh-data.yml?label=data%20refresh)](https://github.com/lucasppinheiro/futebol-dashboard/actions/workflows/refresh-data.yml)
[![Live Demo](https://img.shields.io/badge/demo-Vercel-000000)](https://futebol-dashboard.vercel.app/)

Dashboard responsivo do Campeonato Brasileiro Série A com classificação, artilharia, páginas por clube, gráficos e comparação de desempenho.

**[Abrir demonstração](https://futebol-dashboard.vercel.app/)**

## Destaques técnicos

- Site estático gerado com Python/Jinja (Flask usado como SSG) e deploy na Vercel.
- Dados da [football-data.org](https://www.football-data.org/) atualizados automaticamente.
- Validação de schema e gravação atômica para proteger o dataset.
- Testes com pytest, Jest e jsdom executados em todo push/PR (CI) e antes de cada refresh de dados.
- Lint e formatação com Ruff (Python) e ESLint + Prettier (JavaScript).
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

O GitHub Actions atualiza e valida os dados a cada hora (`refresh-data.yml`) e roda lint + testes + build em todo push/PR (`ci.yml`). A integração Git da Vercel cria previews para branches e publica `main` automaticamente.

## Desenvolvimento local

Requisitos: Python 3.10+ (CI testa 3.10 e 3.12) e Node.js 24+.

```bash
git clone https://github.com/lucasppinheiro/futebol-dashboard.git
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
python -m pip install -U pip
pip install -r requirements.txt --group dev
npm ci   # necessário apenas para testes/lint JS
python app.py
```

A aplicação estará em [http://127.0.0.1:5000](http://127.0.0.1:5000) (defina `FLASK_DEBUG=1` no `.env` para modo debug em desenvolvimento). Para buscar dados novos, configure `FOOTBALL_DATA_TOKEN` no `.env` e execute `python atualizar_dados.py`.

## Qualidade e build

```bash
python -m pytest tests -q   # testes Python
npm test                    # testes JS (Jest + jsdom)
ruff check .                # lint Python
ruff format --check .       # formatação Python
npm run lint                # ESLint
npm run format:check        # Prettier
npm audit                   # auditoria de dependências JS
```

Hooks de pre-commit (Ruff, Prettier, ESLint, gitleaks) estão configurados em `.pre-commit-config.yaml`:

```bash
pip install pre-commit
pre-commit install
```

Para gerar exatamente o conteúdo servido pela Vercel:

```bash
python build_static.py
```

O resultado é escrito em `dist/`, incluindo páginas dos clubes, APIs JSON, `404.html`, `robots.txt` e `sitemap.xml`.

## API estática

O build publica snapshots JSON somente leitura, atualizados junto com cada deploy:

- `https://futebol-dashboard.vercel.app/api/classificacao.json` — os 20 times com campos como `posicao`, `time`, `sigla`, `pontos`, `jogos`, `aproveitamento`.
- `https://futebol-dashboard.vercel.app/api/artilharia.json` — artilheiros com `jogador`, `time`, `sigla`, `posicao`, `gols`.
- `https://futebol-dashboard.vercel.app/api/health.json` — status do dataset (`dados_atualizados_em`, `dados_desatualizados`).

## Configuração

As variáveis disponíveis estão documentadas em `.env.example`:

| Variável | Efeito |
|---|---|
| `FOOTBALL_DATA_TOKEN` | Token da football-data.org para atualizar dados. |
| `API_UPDATE_TOKEN` | Habilita o endpoint `POST /api/atualizar` (Bearer token). |
| `DATA_AUTO_REFRESH_HOURS` | Idade máxima dos dados antes do refresh automático (padrão 6; 0 desativa). |
| `DATA_AUTO_REFRESH_COOLDOWN_MINUTES` | Intervalo mínimo entre tentativas de refresh (padrão 15). |
| `FLASK_DEBUG` / `FLASK_HOST` / `FLASK_PORT` | Configuração do servidor local (debug desligado por padrão). |
| `SITE_BASE_PATH` / `SITE_ORIGIN` | Subdiretório e origem usados no build estático. |

No GitHub, `FOOTBALL_DATA_TOKEN` deve existir apenas em **Settings > Secrets and variables > Actions**.

## Publicação na Vercel

1. Importe `lucasppinheiro/futebol-dashboard` no painel da Vercel.
2. Mantenha o diretório raiz como `.`; o `vercel.json` já define o build e a saída `dist`.
3. Use `main` como branch de produção.
4. Configure `SITE_ORIGIN` caso o domínio final seja diferente de `https://futebol-dashboard.vercel.app`.

Não é necessário cadastrar o token da football-data.org na Vercel: a atualização ocorre no GitHub Actions e o JSON validado é versionado.

Nunca registre tokens no código, no histórico Git ou em arquivos versionados.

## Licença

[ISC](LICENSE)
