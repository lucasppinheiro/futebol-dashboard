# Brasileirão Dashboard

[![Data refresh](https://img.shields.io/github/actions/workflow/status/lucasppinheiro/futebol-dashboard/refresh-data.yml?label=data%20refresh)](https://github.com/lucasppinheiro/futebol-dashboard/actions)
[![CI](https://img.shields.io/github/actions/workflow/status/lucasppinheiro/futebol-dashboard/ci.yml?label=CI)](https://github.com/lucasppinheiro/futebol-dashboard/actions/workflows/ci.yml)
[![Live Demo](https://img.shields.io/badge/demo-Vercel-000000)](https://futebol-dashboard.vercel.app/)

Dashboard do Campeonato Brasileiro Série A com classificação atual, rodadas, artilharia, gráficos, comparador de clubes e páginas individuais por time. O projeto combina dados oficiais da CBF, geração estática e uma interface esportiva minimalista.

**[Abrir demonstração](https://futebol-dashboard.vercel.app/)**

## O que o projeto demonstra

- Produto web completo: coleta de dados, validação, build estático, publicação e interface responsiva.
- Automação confiável: GitHub Actions atualiza os dados, roda testes e só publica informações versionadas quando a validação passa.
- Cuidado com dados reais: a CBF é a fonte principal; football-data.org enriquece agenda e histórico sem bloquear classificação e artilharia.
- Engenharia de portfólio: rotas estáticas, páginas por clube, APIs JSON, sitemap, robots, página 404 e deploy na Vercel.

## Funcionalidades

- Página contínua em tema claro com navegação por Tabela, Rodada, Artilharia, Gráficos e Comparador.
- Classificação atual sempre identificada como dado da CBF; a rodada selecionada altera somente as partidas e permanece compartilhável pela URL.
- Navegação entre as 38 rodadas para consultar calendário e resultados disponíveis.
- Tabela de classificação com filtros por zona, busca, favoritos, ordenação e expansão mobile da campanha.
- Artilharia em tabela compacta e quatro leituras não redundantes: ataque × defesa, casa × fora, forma recente e gols por rodada.
- Comparador de clubes com escudos, métricas lado a lado e seleção preservada na URL.
- Páginas individuais por time com forma, confrontos, média da liga, artilheiros e atalho para comparação.
- Vinte escudos oficiais preservados localmente, com versões transparentes e visualmente equilibradas.
- Endpoints JSON em `dist/api/` para classificação atual, classificações históricas, artilharia, partidas e saúde dos dados.

## Arquitetura

```text
CBF oficial -------- classificação atual + artilharia + rodada
football-data.org -- partidas + contingência da rodada
              \       /
             atualizar_dados.py
    |
validacao + escrita atomica
    |
data/brasileirao.json
    |
build_static.py
    |
dist/ -> Vercel
```

O GitHub Actions roda a cada hora, tenta atualizar os dados pela CBF, valida o JSON, executa os testes e só então commita o dataset. A integração Git da Vercel publica `main` automaticamente quando há novo commit.

## Desenvolvimento local

Requisitos: Python 3.10+ e Node.js 24+.

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
pip install -r requirements.txt --group dev
npm ci
npx playwright install chromium
python app.py
```

A aplicação estará em [http://127.0.0.1:5000](http://127.0.0.1:5000). Para buscar dados oficiais novos pela CBF, execute `python atualizar_dados.py`. Quando `FOOTBALL_DATA_TOKEN` estiver configurado, o mesmo comando enriquece o snapshot com calendário e resultados da football-data.org, mesmo mantendo `DATA_SOURCE=cbf`. Casa × fora, forma recente e gols por rodada são calculados somente a partir dessas partidas encerradas; sem agenda válida, a interface informa que aguarda sincronização em vez de inventar valores. O comando `python gerar_dados.py` gera apenas um fixture sintético para desenvolvimento e nunca deve ser usado como atualização oficial.

Durante o atendimento, as páginas e APIs leem e validam primeiro o snapshot local. Quando ele está desatualizado e a atualização automática está habilitada, a resposta usa esse snapshot e uma atualização daemon é iniciada em segundo plano; assim, a consulta não espera a fonte externa. Se o arquivo ainda não existir e a atualização automática estiver habilitada, a aplicação agenda a tentativa e responde `503` até que uma atualização consiga criá-lo. JSON ou schema inválidos continuam sendo reportados como erro explícito.

O `POST /api/atualizar` permanece síncrono quando consegue reservar a atualização. Se já houver uma atualização automática ou manual em andamento, ele responde `409` com o código `ATUALIZACAO_EM_ANDAMENTO`. O cooldown começa ao reservar uma tentativa automática e também vale quando o worker não consegue iniciar. A coordenação e o cooldown valem somente para o processo atual, e o worker daemon pode ser encerrado junto com o servidor; a atualização periódica durável continua sendo responsabilidade do GitHub Actions.

## Qualidade e build

```bash
ruff check .
npm run test:python
npm test
npm run test:e2e
npm run lint
npm run format:check
npm run audit
npm run build
```

`npm run format:check` verifica tanto a formatação Python com Ruff quanto JavaScript com Prettier, igual ao job de lint do CI.

Para gerar exatamente o conteúdo servido pela Vercel:

```bash
python build_static.py
```

O resultado é escrito em `dist/`, incluindo páginas dos clubes, APIs JSON, `404.html`, `robots.txt` e `sitemap.xml`.

## Escudos dos clubes

Os arquivos recebidos da CBF ficam preservados, sem alterações, em `static/img/escudos/cbf/`. O site usa as versões de exibição em `static/img/escudos/normalizados/`, com fundo transparente, tela quadrada e margem proporcional para equilibrar formatos redondos, largos e verticais.

A normalização remove somente o fundo claro e neutro conectado às bordas. Áreas brancas internas, estrelas e demais elementos oficiais são mantidos. A arte não é recortada, esticada nem reamostrada durante o processo.

Para recriar os PNGs depois de substituir algum original da CBF:

```bash
pip install "Pillow>=12,<13"
python scripts/normalize_crests.py
```

O script exige exatamente os 20 arquivos JPG da temporada e gera novamente todos os PNGs. Não edite os arquivos normalizados manualmente.

## Dados e configuração

As variáveis disponíveis estão documentadas em `.env.example`. A fonte padrão é `DATA_SOURCE=cbf`; classificação e artilharia continuam atualizando sem token. Para habilitar o calendário, mantenha `FOOTBALL_DATA_TOKEN` apenas no servidor e em **Settings > Secrets and variables > Actions** — nunca no HTML ou no JavaScript enviado ao navegador.

Em execuções agendadas, uma falha temporária da fonte de dados não sobrescreve o dataset válido existente. Em execuções manuais (`workflow_dispatch`), o workflow falha para facilitar diagnóstico.

## Observações técnicas

- A aplicação é estática por escolha arquitetural: os dados são atualizados pelo GitHub Actions e publicados automaticamente pela Vercel.
- A CBF é usada como fonte principal; caso o formato da fonte mude, a rotina de coleta pode precisar de manutenção.
- Campos indisponíveis na fonte oficial não são inventados pela aplicação.

## Publicação na Vercel

1. Importe `lucasppinheiro/futebol-dashboard` no painel da Vercel.
2. Mantenha o diretório raiz como `.`; o `vercel.json` já define o build e a saída `dist`.
3. Use `main` como branch de produção.
4. Configure `SITE_ORIGIN` caso o domínio final seja diferente de `https://futebol-dashboard.vercel.app`.

Não é necessário cadastrar tokens na Vercel: a atualização ocorre no GitHub Actions e o JSON validado é versionado.

Nunca registre tokens no código, no histórico Git ou em arquivos versionados.
