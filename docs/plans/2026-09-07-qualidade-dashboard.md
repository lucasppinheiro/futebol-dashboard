# Plano de melhoria do futebol-dashboard

**Objetivo:** corrigir falhas comprovadas de UX, segurança de respostas e integração sem substituir Flask/Jinja ou remover funcionalidades.

**Arquitetura:** preservar CBF → JSON validado → Flask/Jinja → build estático. A geração estática deve consumir somente o snapshot local. Subagentes gpt-5.6-luna, esforço xhigh, contexto independente; revisão e decisões pelo agente principal.

**Restrições:** sem commit, push, merge, PR ou deploy; sem atualização real da CBF; preservar dados e identidade editorial. Não acrescentar dependências de produção.

## Auditoria e prioridades

| Prioridade | Problema e impacto | Solução escolhida | Risco / arquivos |
| --- | --- | --- | --- |
| Alto | Debug ativo por padrão pode expor diagnóstico ao disponibilizar Flask | Desativar por padrão; manter ativação explícita de desenvolvimento | Baixo; app.py, .env.example |
| Alto | DATA_PATH diverge do destino de atualização e mantém dados antigos após sucesso | Destino explícito opcional no updater, propagado pelo Flask e usado no timestamp/escrita | Médio; app.py, atualizar_dados.py, testes |
| Alto | Build pode consultar CBF por detectar snapshot antigo | Carregamento explicitamente sem refresh, preservando comportamento Flask | Baixo; app.py, build_static.py, testes |
| Alto | Workflow manual perde status da atualização e mascara falha | Capturar código no ramo else e testar comportamento | Baixo; refresh-data.yml, test_workflow.py |
| Médio | Dados interpolados em HTML do comparador | Escapar valores ou construir nós seguros e tratar URLs | Médio; main.js, testes JS |
| Médio | Gráficos indisponíveis aparecem vazios | Estados visíveis, fallback textual e recuperação correta | Baixo; templates, JS, CSS |
| Médio | Tabela móvel depende de JS para rótulos | Renderizar data-label no HTML e explicitar abreviações | Baixo; templates |
| Médio | Comparador customizado tem associação ARIA incompleta | Completar associação e foco mantendo interação existente | Médio; main.js, index.html |
| Médio | JSON inesperado causa exceções e respostas revelam detalhes | Verificar forma antes de normalizar; respostas neutras, logging interno e erros HTTP preservados | Médio; app.py, normalizacao.py, testes |
| Médio | Desempate de artilharia pode divergir do resumo | Reconciliar resumo após normalização com regressão de empate | Baixo; normalizacao.py, testes |
| Médio | URLs canônicas/sitemap ignoram origem ou subcaminho | Helper public_url(path), origem SITE_ORIGIN e site_url; usar em metadados e build | Baixo; app.py, templates, build_static.py |
| Baixo | Cabeçalho mantém Em disputa no fim da temporada | Usar campeonato_finalizado e progresso limitado | Baixo; partial do cabeçalho |

Nenhum problema crítico foi confirmado. Adiadas: migração do refresh para worker, rate limiting de infraestrutura, manifest por temporada, consolidação ampla de CSS e dependências. Não impor mesma rodada a todos os clubes ou mínimo fixo de artilheiros sem contrato validado.

## Ordem e propriedade dos arquivos

1. Qualidade prepara ferramentas locais e executa baseline, sem alterar código ou dados.
2. Backend possui app.py, atualizar_dados.py, normalizacao.py, .env.example e testes Python desses módulos. Adiciona carregar_dados(*, permitir_refresh=True) e public_url(path='') como contratos com build/templates. Não toca build nem templates.
3. Frontend possui templates de produção, static/js, CSS estritamente necessário e tests/js. Usa public_url nos metadados. Não toca Python.
4. Build possui build_static.py, .github/workflows/refresh-data.yml, tests/test_build_static.py e tests/test_workflow.py. Usa carregar_dados(permitir_refresh=False) e public_url. Não toca app.py.
5. Revisão dos diffs pelo principal; revisão independente de integração; corrigir somente achados confirmados e validar novamente o necessário.

## Verificação

- Regressões de comportamento importante devem falhar antes da correção e passar depois, quando viável.
- Python: pytest tests, ruff check ., ruff format --check .
- JavaScript: npm test -- --runInBand, npm run lint, npm run format:check.
- Build: executar build_static.py com refresh desativado e conferir home, 404, vinte clubes, JSONs e sitemap.
- Smoke local Flask e estático: home, clube, erro, tabs, busca, ordenação, comparador e fallback de gráficos; desktop/tablet/mobile.
- Confirmar git diff --check e que data/brasileirao.json não mudou. Registrar limitações de ferramentas/rede sem alegar verificações não executadas.

## Revisão e validação em 09/09/2026

Implementação realizada por subagentes `gpt-5.6-luna`, `reasoning_effort=xhigh`, `fork_turns=none`, com propriedade separada dos arquivos. O principal revisou os diffs e solicitou correções para preservar HTTP 405/Allow, evitar falsos positivos nos testes de build e corrigir estados de erro do radar e navegação do comparador.

- Python: 111 testes aprovados, 1 pulado por Bash indisponível; cobertura total 80%.
- JavaScript: 39 testes aprovados em quatro suítes, incluindo ausência do global de classificação no radar e troca direta de foco entre seletores do comparador.
- Ruff (análise e formatação), ESLint, Prettier e `git diff --check`: aprovados.
- Dependências de desenvolvimento: Browserslist atualizado para 4.28.9 e js-yaml para 3.15.2, apenas alterações transitivas compatíveis no lockfile; auditoria npm sem vulnerabilidades reportadas após a atualização.
- Dataset preservado, sem diff. SHA-256: `92f3a8150fdedad62a6f15551ce0d2a65f2aa723e1d1553c133bbd02cb47c387`.
- Não foram realizadas atualizações reais na CBF, commit, push, merge, PR ou deploy.

O ganho de performance verificado é a remoção do refresh externo do caminho de build. Não foi medido ganho de tempo de carregamento no navegador. O refresh síncrono do servidor Flask permanece como melhoria futura, assim como a consolidação ampla de CSS, execução E2E no CI e gestão de clubes por temporada.

### Build e navegador

Build final concluído após a última correção do comparador. Verificação Playwright em Flask e no diretório estático, nas larguras 390, 768 e 1440, nos modos normal, CDN bloqueada e sem JavaScript: nenhuma falha no script final. Foram verificados rotas, APIs, página 404, metadados, rótulos, largura da página, busca, comparador, teclado, gráficos reais e fallback textual. Nenhum erro de execução da página foi registrado; respostas 404 esperadas no teste de rota inválida foram distinguidas de erros da aplicação.

O navegador confirmou e orientou a correção de uma corrida de foco: o fechamento atrasado do primeiro seletor não pode fechar o segundo que acabou de abrir. A implementação agora fecha apenas o seletor que perdeu foco. A lista também deixa de criar uma parada adicional de tabulação.

Limitações: o teste de shell do workflow permaneceu pulado por falta de Bash utilizável no Windows; não houve execução remota de GitHub Actions ou Vercel. As abas da página inicial continuam dependendo de JavaScript; sem ele, a classificação renderizada permanece legível. O primeiro teste de CDN encontrou bloqueio de rede do ambiente; a execução com acesso autorizado confirmou o Chart.js real nas três larguras.
