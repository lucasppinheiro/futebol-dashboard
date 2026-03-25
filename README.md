# ⚽ Futebol Dashboard

Um dashboard moderno e com foco em performance para o **Brasileirão Série A**. O projeto consolida estatísticas atualizadas da competição, gráficos interativos, classificação em tempo real e páginas detalhadas para os times da primeira divisão, construído inicialmente para servir de referência pessoal e ferramenta rápida de análise.

---

## 🚀 Funcionalidades Principais

- **Classificação Interativa:** Tabela de pontuação ordenável, busca avançada por nome, filtragem simplificada por zonas (Libertadores, Sul-Americana, Rebaixamento) e animações responsivas.
- **Ecossistema Personalizado (Favoritos ⭐):** Sistema integrado (via `localStorage`) para favoritar, priorizar na visualização e acessar mais rápido o seu clube.
- **Páginas Dedicadas (Por Time):** Análise isolada através da rota `/time/<sigla>`, exibindo resumo de aproveitamento esportivo e métricas de desempenho.
- **Gráficos Dinâmicos e Tematizados:** Desenvolvidos em **Chart.js**. Uma coleção de indicadores visuais: evolução de pontos, aproveitamento percentual, saldo de gols e radar defensivo. Os gráficos reagem imediatamente à alternância entre modo claro e escuro.
- **Sincronização com API:** Extração periódica, sem excesso de chamadas, consolidando os dados da *football-data.org*, baixando escudos de clubes oficiais e formatando os resultados para JSON.

## 🛠️ Tecnologias Envolvidas

- **Backend:** Python 3 (Scripts de Web Scraping/API e Automação), Flask, biblioteca de logging padrão, pytest.
- **Frontend:** Vanilla JS limpo e componentizado (sem frameworks pesados), CSS3 com suporte nativo a Theming (Dark/Light mode via Custom Properties) e layout responsivo.
- **Metodologia:** Persistência leve e atômica. O backend responde com os arquivos `.json` diretamente ao in-memory cache do frontend para zero gargalos.

## ⚙️ Como Executar Localmente

Você precisará de Python 3.9+ e do Git instalados.

1. Clone e acesse o diretório:
   ```bash
   git clone https://github.com/lucassgsantos/futebol-dashboard.git
   cd futebol-dashboard
   ```

2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv venv
   # No Windows:
   venv\Scripts\activate
   # No macOS/Linux:
   source venv/bin/activate
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Variáveis de Ambiente e Token da API:
   Copie `.env.example` para criar o seu `.env`:
   ```bash
   cp .env.example .env
   ```
   > **Nota:** Para buscar os dados de times e escudos atualizados, obtenha uma chave gratuita de desenvolvedor no site oficial da [football-data.org](https://www.football-data.org/) e insira em `FOOTBALL_DATA_TOKEN=seu_token_aqui`.

5. Sicronizar Dados e Rodar o Servidor:
   ```bash
   python atualizar_dados.py
   python app.py
   ```
   O app ficará ativo localmente na porta 5000: **http://127.0.0.1:5000**.

## 🧪 Testes Unitários

Uma suíte foi incluída para garantir a estabilidade do JSON validado e a prevenção de _crashes_ relacionados aos payloads da integração externa. Para executar:

```bash
python -m pytest tests/ -v
```

## 📝 Licença
Projeto Open Source (MIT License). Livre para estudos, uso contínuo e derivação.
