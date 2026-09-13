# Marca tipográfica e destaques integrados

## Entendimento

- Preservar o restante do dashboard e sua navegação contínua.
- Manter a faixa verde e o menu atual.
- Substituir a apresentação artificial da marca por um nome puramente tipográfico.
- Manter melhor ataque e melhor defesa sem um componente separado da tabela.
- Mostrar os destaques exatamente nas linhas e métricas às quais pertencem.
- Representar todos os clubes empatados em ataque ou defesa.
- Preservar o funcionamento em mobile, por teclado e sem JavaScript.

## Premissas

- O nome exibido será “Brasileirão Série A”.
- Melhor ataque usa o maior valor de `gols_pro` e melhor defesa usa o menor valor de `gols_contra`.
- Não serão adicionados fontes, imagens, bibliotecas ou requisições.
- Desempenho, segurança, disponibilidade e manutenção permanecem iguais aos do dashboard atual.

## Design

O cabeçalho mantém uma única faixa verde e o menu existente. A marca passa a ser um único texto, “Brasileirão Série A”, sem monograma, selo, subtítulo ou ano destacado.

O resumo independente acima da tabela deixa de existir. A primeira posição não recebe uma legenda redundante. Nas colunas GP e GC, os valores recordistas ganham respectivamente as legendas “Melhor ataque” e “Melhor defesa”. Em telas pequenas, onde essas colunas são recolhidas, as legendas reaparecem dentro da campanha expansível do clube.

O tratamento visual usa apenas tipografia, peso e um detalhe azul discreto. Não há novos cards, ícones decorativos, sombras ou superfícies.

## Decisões

- Marca tipográfica em vez de símbolos inventados, para manter autenticidade.
- Destaques de ataque e defesa integrados à tabela em vez de uma faixa ou cards, para ligar significado e dado.
- Ausência do rótulo “Líder”, pois a posição 1 já comunica essa informação.
- Todos os empates de ataque e defesa são destacados, evitando seleção arbitrária.
- Versão mobile usa a expansão já existente, evitando aumentar a largura da tabela.
