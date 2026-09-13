# Brasileirão Dashboard — plano de implementação

**Objetivo:** alinhar toda a página à rodada selecionada, simplificar a identidade e remover o tema escuro.

**Arquitetura:** ampliar o snapshot com classificações históricas validadas, renderizar a rodada inicial no servidor e atualizar o DOM a partir do cache serializado. Preservar Flask, Jinja, CSS e JavaScript sem dependências de runtime adicionais.

## 1. Contrato histórico

- Adicionar testes de cliente para `standings?season=&matchday=`.
- Adicionar testes de schema para rodadas, clubes e classificação inválida.
- Implementar busca e normalização de uma classificação por rodada.

## 2. Atualização incremental

- Testar rodadas ausentes, cache existente, falha parcial e CBF autoritativa na rodada atual.
- Enriquecer somente entradas necessárias e preservar o último cache válido.
- Persistir metadados de atualização e defasagem do histórico.

## 3. Contexto e build

- Testar query `?rodada=N`, contexto inicial e serialização no build estático.
- Expor `classificacao_por_rodada` ao template sem criar uma API pública com token.
- Manter base path e saída estática compatíveis.

## 4. Shell claro e ordem do conteúdo

- Adicionar testes estruturais para nova marca, ausência de tema e ordem Tabela → Rodada.
- Reconstruir o cabeçalho compacto e mover o seletor para uma faixa global.
- Remover CSS, JavaScript e armazenamento relacionados ao modo escuro.

## 5. Interações e artilharia

- Testar a troca coordenada de classificação, jogos, destaques, mapa ataque–defesa, comparador e URL; manter a corrida de artilharia identificada como leitura da temporada atual.
- Preservar busca, filtros, ordenação, favoritos, expansão móvel e comparador.
- Substituir pódio/lista progressiva por uma tabela única de artilheiros.

## 6. Páginas auxiliares e validação

- Alinhar páginas de clube e 404 à marca e ao tema claro.
- Rodar pytest, Jest, Ruff, ESLint, Prettier, build e Playwright/axe.
- Verificar os quatro viewports, Lighthouse, console e ausência de overflow.
- Reiniciar o preview e apresentar a versão final no navegador.
