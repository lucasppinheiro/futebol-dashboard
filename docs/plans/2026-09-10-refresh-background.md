# Plano: atualização Flask em segundo plano

**Objetivo:** responder páginas e APIs com o snapshot local válido sem esperar consultas externas.

**Arquitetura:** manter Flask e atualização atômica existente. Uma thread daemon executa o refresh automático; um estado protegido por lock impede sobreposição de refresh automático e manual no mesmo processo. Cache usa caminho e timestamp em nanossegundos, com lock curto separado da rede.

**Restrições:** preservar todas as alterações anteriores; nenhuma nova dependência; não consultar CBF real durante validação; sem commit, push, PR ou deploy.

## Decisões

- Snapshot válido, mesmo vencido: ler/validar, guardar referência local e agendar atualização antes de retornar, sem esperar o worker.
- Arquivo ausente: agendar tentativa quando habilitada e responder 503 imediatamente. Não gerar dados fictícios nem esperar rede na requisição.
- JSON ou schema inválido: manter resposta explícita de erro; não substituir por cache antigo para esconder corrupção. Recuperação forçada de arquivo inválido não faz parte desta mudança.
- Build com `permitir_refresh=False`: nunca inicia worker ou consulta externa, inclusive em falhas de leitura.
- POST autenticado de atualização: manter execução síncrona e resposta 200 após sucesso. Quando ocupado, responder 409 com código estável `ATUALIZACAO_EM_ANDAMENTO`.
- Reservar execução antes de iniciar a thread; capturar destino e temporada. Liberar estado em todos os caminhos, inclusive falha de `Thread.start()`; preservar cooldown após falha de rede.
- O cooldown também se aplica quando a thread não consegue iniciar, evitando tentativas a cada GET em situação de falta de recursos. O estado ocupado é liberado e a atualização manual continua disponível.
- Cache protegido separadamente: chave por caminho absoluto e `st_mtime_ns`; retornar referência local e evitar publicar snapshot associado ao timestamp errado durante troca atômica.
- Coordenação e cooldown são por processo. Não implementar fila durável, lock distribuído ou garantir execução após encerramento do servidor; documentar essas limitações.

## Implementação

1. Alterar somente `app.py`, `tests/test_app.py`, `.env.example` e `README.md` quando necessário.
2. Testes determinísticos com Event/Barrier: retorno antes da liberação da fonte, concorrência com cooldown zero, recuperação e cooldown após falha, arquivo ausente, inválido explícito, destino capturado, POST ocupado/sucesso, falha de start e cache por caminho.
3. Adaptar teste antigo que esperava atualização síncrona. Aguardar workers antes do teardown de fixtures; sem sleeps arbitrários ou threads escapando entre testes.
4. Revisão independente de concorrência e integração pelo segundo subagente; principal revisa diffs e resolve achados.
5. Executar pytest, Ruff, suíte JavaScript existente e build estático sem refresh. Provar responsividade com updater simulado bloqueado por Event, sem depender de tempo de internet.

Baseline em 10/09/2026: 111 testes Python aprovados, 1 pulado por indisponibilidade de Bash. Nenhum arquivo de dados foi alterado.

## Resultado da execução

- Implementação e revisão delegadas a subagentes `gpt-5.6-luna`, esforço `xhigh`, contexto independente. O principal revisou os diffs e a integração.
- 119 testes Python aprovados e 1 pulado (Bash indisponível); 39 testes JavaScript aprovados.
- Ruff, ESLint, Prettier e `git diff --check` aprovados.
- Build estático aprovado, com home, 404, API e páginas dos 20 clubes, sem refresh externo.
- Smoke independente com fonte simulada bloqueada por Event: GET respondeu com snapshot antigo antes de liberar a atualização; GET seguinte recebeu os dados novos depois da conclusão.
- Nenhuma alteração no dataset, nenhuma consulta real à CBF e nenhuma operação de commit, push, PR ou deploy.
- Limites preservados: atualização em background é por processo e não durável; falha de inicialização do worker respeita cooldown; arquivo inválido continua apresentando erro explícito.
