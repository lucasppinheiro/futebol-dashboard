# Brasileirão Dashboard — histórico por rodada

## Entendimento confirmado

- A marca passa de “Caderno da Rodada” para “Brasileirão Dashboard”.
- O produto terá somente tema claro.
- Um seletor global precede o conteúdo e controla a fotografia do campeonato.
- A classificação aparece antes dos jogos e representa o fim da rodada selecionada.
- Partidas, destaques, mapa ataque–defesa e comparador acompanham a mesma rodada; a artilharia e sua corrida resumem a temporada atual, pois a fonte não fornece histórico por rodada.
- A artilharia vira uma tabela única, compacta e escaneável.
- Verde permanece como identidade principal; azul da bandeira aparece apenas em detalhes funcionais.

## Arquitetura de dados

O snapshot passa a incluir `classificacao_por_rodada`, um objeto indexado pelo número da rodada. Cada valor usa o mesmo contrato de `classificacao`, o que permite reutilizar validação, filtros, favoritos, gráficos e comparador.

O backend consulta `football-data.org` somente para rodadas ausentes ou que ainda podem mudar. Rodadas concluídas permanecem em cache. A classificação atual da CBF continua prioritária e substitui a entrada correspondente à rodada atual. Se o enriquecimento falhar, o último histórico válido é preservado e sua defasagem é indicada.

O HTML renderiza a rodada inicial por completo. O restante do histórico validado é serializado para JavaScript e para o build estático, permitindo navegação imediata sem expor token. A URL continua compartilhável por `?rodada=N`.

## Interface

O cabeçalho é uma barra branca compacta com marca textual, temporada, estado dos dados e navegação. Uma linha azul fina e o estado ativo da navegação fornecem o acento brasileiro sem disputar com o verde.

A ordem é: seletor global, classificação, jogos da rodada, artilharia, desempenho e comparador. A classificação mostra explicitamente “após a Rodada N”. A seção de jogos não repete resumo, líder ou tabela; apresenta apenas confrontos e estado da agenda.

A artilharia usa colunas Posição, Jogador, Clube e Gols. Escudo e sigla ficam junto ao clube, gols são alinhados à direita e as três primeiras posições recebem um marcador azul discreto. Não há pódio, cards ou revelação progressiva.

## Requisitos não funcionais

- Token somente no servidor e custo mensal zero.
- Atualização horária com cache incremental e escrita atômica.
- Conteúdo útil sem JavaScript para a rodada inicial.
- Navegação por teclado, foco visível, contraste WCAG 2.2 AA e alvos de 44 px.
- Sem rolagem horizontal acidental nos viewports de aceite.
- Build estático inclui o histórico disponível.
- Performance local de produção ≥ 90, acessibilidade ≥ 95 e CLS < 0,1.

## Decisões

| Decisão | Alternativas | Motivo |
| --- | --- | --- |
| Snapshot completo em cache | Consulta sob demanda; cálculo local | Navegação instantânea, build estático e fidelidade ao provedor. |
| Seletor global antes da tabela | Controle dentro dos jogos | Evita um controle abaixo alterando conteúdo acima. |
| Tabela antes da rodada | Jogos antes; abas isoladas | Ordem explicitamente escolhida pelo usuário. |
| Tema claro único | Dois temas | Reduz código, manutenção e ruído visual. |
| Artilharia tabular | Pódio; cards | Melhora comparação e densidade. |

## Riscos e contingências

- A API gratuita limita chamadas: o backfill é incremental e respeita o cache.
- Tabelas históricas do provedor podem não refletir punições administrativas: a interface identifica a fonte e a rodada atual da CBF permanece autoritativa.
- Se uma rodada não tiver histórico válido, a UI informa indisponibilidade sem substituir silenciosamente por dados atuais.
