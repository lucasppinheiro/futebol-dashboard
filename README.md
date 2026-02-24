# Brasileirão Dashboard

Dashboard interativo do Campeonato Brasileiro Série A 2025, construído com Python e Flask.

Utiliza dados reais da temporada, incluindo classificação final, artilharia e gráficos comparativos dos 20 clubes.

## Funcionalidades

- Tabela de classificação com pontuação, vitórias, empates, derrotas e saldo de gols
- Ranking dos 20 maiores artilheiros do campeonato
- Gráficos interativos com Chart.js (pontuação, artilheiros, aproveitamento e gols pró vs contra)

## Tecnologias

- Python 3 / Flask
- HTML5, CSS3, JavaScript
- Chart.js 4
- JSON

## Como executar

```bash
git clone https://github.com/lucassgsantos/futebol-dashboard.git
cd futebol-dashboard
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python gerar_dados.py
python app.py
```

Acesse http://localhost:5000 no navegador.

## Estrutura do projeto

```
futebol-dashboard/
├── app.py
├── gerar_dados.py
├── requirements.txt
├── data/
│   └── brasileirao.json
├── templates/
│   └── index.html
└── static/
    ├── css/style.css
    └── js/
        ├── charts.js
        └── main.js
```

## Autor

Lucas Santos — [@lucassgsantos](https://github.com/lucassgsantos)

## Licença

MIT
