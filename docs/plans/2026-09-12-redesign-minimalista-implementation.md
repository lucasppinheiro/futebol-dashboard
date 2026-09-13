# Redesign minimalista esportivo Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reduzir o ruído visual do Caderno da Rodada, recuperando a clareza da versão anterior sem remover as novas funções.

**Architecture:** Preservar contratos, seletores DOM e lógica JavaScript. Ajustar o shell Jinja somente onde a hierarquia muda e substituir os tokens/tratamentos do `caderno.css` por um sistema minimalista único. Usar testes de build, jsdom e Playwright como proteção de comportamento e aparência estrutural.

**Tech Stack:** Flask, Jinja, CSS, JavaScript, pytest, Jest/jsdom, Playwright e axe.

---

### Task 1: Fixar o contrato visual minimalista

**Files:**
- Modify: `tests/test_build_static.py`
- Modify: `tests/e2e/caderno.spec.js`

1. Escrever asserções que proíbem Source Serif e elementos editoriais decorativos no build.
2. Escrever asserções de navegador para tipografia sans-serif, cabeçalho compacto, seções menores e comparador claro.
3. Executar os testes focados e confirmar falha pelo visual atual.

### Task 2: Simplificar shell e sistema visual

**Files:**
- Modify: `templates/index.html`
- Modify: `templates/time.html`
- Modify: `templates/404.html`
- Modify: `static/css/caderno.css`

1. Remover a família serifada e os elementos puramente decorativos do HTML.
2. Reescrever tokens, hierarquia, densidade, superfícies e responsividade no CSS.
3. Manter IDs, data attributes e controles usados por JavaScript e testes.
4. Executar testes focados até ficarem verdes.

### Task 3: Reduzir a artilharia por revelação progressiva

**Files:**
- Modify: `templates/index.html`
- Modify: `static/js/caderno.js`
- Modify: `tests/js/caderno.test.js`

1. Escrever teste jsdom para expandir/recolher os artilheiros secundários.
2. Confirmar a falha do teste.
3. Implementar controle acessível preservando funcionamento sem JavaScript.
4. Confirmar o teste focado e a regressão Jest completa.

### Task 4: Alinhar páginas de clube e 404

**Files:**
- Modify: `templates/time.html`
- Modify: `templates/404.html`
- Modify: `static/css/caderno.css`
- Test: `tests/test_app.py`

1. Adicionar asserções estruturais focadas.
2. Confirmar a falha esperada.
3. Aplicar a mesma densidade, tipografia e profundidade.
4. Rodar testes de rotas e acessibilidade.

### Task 5: Verificação final e apresentação

**Files:**
- Modify: `README.md` se a descrição visual precisar de ajuste.

1. Rodar pytest, Jest, Ruff, ESLint, Prettier e build estático.
2. Rodar Playwright/axe nos quatro viewports e dois temas.
3. Verificar Lighthouse de produção.
4. Reiniciar o servidor local e abrir o resultado no navegador do usuário.
