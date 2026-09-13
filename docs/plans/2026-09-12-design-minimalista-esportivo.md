# Design minimalista esportivo

## Entendimento

- O dashboard continua sendo um produto esportivo real e uma demonstração de frontend para recrutadores.
- A versão editorial ficou visualmente poluída; a nova direção deve recuperar a clareza da interface anterior.
- A página permanece contínua, com Linha da Rodada, classificação, artilharia, desempenho e comparador.
- Contratos de dados, URLs, filtros, favoritos, teclado, tema e páginas de clube permanecem funcionais.
- Títulos monumentais, números decorativos, fundos dramáticos e animações de entrada saem da produção.
- Custo zero, atualização horária e a stack Flask/Jinja/CSS/JavaScript continuam como restrições.

## Referências e tradução

- ge: tabela, jogos e artilharia próximos; artilheiros empatados compartilham colocação.
- Sofascore: classificação reduzida às colunas essenciais e zonas incorporadas à tabela.
- 365Scores: conteúdo secundário progressivamente revelado.
- ESPN: tabelas compactas, abreviações estáveis e leitura direta.

As referências orientam hierarquia e densidade, sem cópia de identidade visual.

## Sistema visual

- Libre Franklin em toda a leitura e nos títulos; IBM Plex Mono apenas em horários, rodadas e dados tabulares.
- Fundo claro `#F7F8F6`, superfícies brancas, texto `#20231F`, verde `#07523E` e amarelo apenas para alerta.
- Tema escuro em grafite esverdeado, com pequenas variações de luminosidade entre superfícies.
- Profundidade por bordas suaves e variação de superfície; sombra apenas no seletor de rodada.
- Escala de espaçamento de 8 px, seções de 64 px no desktop e 40 px no mobile.
- Cantos de 4–6 px em controles e cards; tabelas retas.
- Sem animação de entrada; transições de 160–180 ms somente em interações.

## Estrutura

1. Cabeçalho verde compacto com marca, temporada, rodada, líder e artilheiro.
2. Navegação fixa simples.
3. Linha da Rodada de baixa altura.
4. Tabela como superfície principal, com uma faixa curta de destaques.
5. Artilharia compacta, inicialmente limitada aos principais nomes.
6. Duas visualizações simples e comparador em fundo claro.
7. Páginas de clube alinhadas ao mesmo sistema.

## Decisões

| Decisão | Alternativas | Motivo |
| --- | --- | --- |
| Minimalismo esportivo | Monocromático; editorial leve | Preserva identidade e recupera a clareza da versão anterior. |
| Página contínua | Retorno às quatro abas | Mantém navegação e URLs do novo produto. |
| Bordas e superfícies | Sombras e grandes blocos de cor | Diminui ruído e facilita manutenção. |
| Sans-serif dominante | Serifada editorial | Melhora densidade e neutralidade. |
| Recursos secundários sob demanda | Tudo sempre visível | Reduz carga visual sem remover funcionalidade. |

## Premissas e riscos

- A escala continua em 20 clubes e uma atualização por hora.
- Nenhum dado sensível novo é processado e tokens continuam somente no servidor.
- O principal risco é perder identidade ao simplificar; escudos, zonas e Linha da Rodada permanecem como assinatura.
- O segundo risco é esconder informação importante; somente dados secundários entram em revelação progressiva.
