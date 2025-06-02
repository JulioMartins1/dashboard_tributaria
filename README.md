# Dashboard Tributária

Este repositório contém a versão 1.0 de um **Dashboard Tributária** em Streamlit, que permite explorar a evolução, distribuição e crescimento da arrecadação de tributos federais no Brasil por estado (UF) e por natureza jurídica, usando dados públicos (2000–2024).
https://dashtributosbr.streamlit.app
---

## Estrutura do Repositório

dashboard_tributaria/
├── app.py
├── pages/
│ ├── 1_Tributos_Federais.py
│ └── 2_Carga_por_Natureza_Juridica.py
├── base_de_dados/
│ ├── tributos.db
│ └── arrecadacao_CNAE_2016_2024.xlsx
├── geojson/
│ └── ufs_brasil.json
├── requirements.txt
└── README.md

markdown
Copiar
Editar

- **app.py**  
  Página principal: análise de tributos federais por UF e tipo de imposto (série temporal, mapa e crescimento percentual).

- **pages/1_Tributos_Federais.py**  
  Página “Tributos Federais” navegável a partir do menu lateral.

- **pages/2_Carga_por_Natureza_Juridica.py**  
  Página “Arrecadação por Natureza Jurídica” (2016–2024), com filtros de período, seleção de meses e ranking completo.

- **base_de_dados/tributos.db**  
  Banco SQLite gerado localmente contendo a tabela `arrecadacao_federal`.

- **base_de_dados/arrecadacao_CNAE_2016_2024.xlsx**  
  Planilha de arrecadação por CNAE (usada para futuras extensões).

- **geojson/ufs_brasil.json**  
  GeoJSON com os limites das UFs brasileiras (para o mapa choropleth).

- **requirements.txt**  
  Lista de dependências Python necessárias para rodar o projeto.

---

## Tecnologias Utilizadas

- **Linguagem:** Python 3.8+  
- **Framework de Dashboard:** Streamlit  
- **Gráficos e Mapas:** Plotly Express  
- **Geo dados:** GeoPandas (para gerar/manipular `ufs_brasil.json`)  
- **Banco de Dados Local:** SQLite + SQLAlchemy / Pandas  
- **Dados Originais:** Base dos Dados (arrecadação federal) + geobr (malha das UFs)

---

## Objetivos da Versão 1.0

1. **Série Temporal por Tributo (ou Receita Total)**  
   - Filtros: UF (ou “Todas”) e intervalo de anos (2000–2024)  
   - Drill-down mensal ou drill-up anual  
   - Exibe as 5 UFs com maior soma de receita no período

2. **Mapa Choropleth Interativo**  
   - Cada UF colorida pela média mensal do tributo escolhido  
   - Hover com valor formatado em “R$ x.xxx.xxx.xxx”

3. **Crescimento Percentual Dinâmico**  
   - Calcula variação entre o ano de início e fim definidos no filtro  
   - Mostra as 3 UFs com maior queda e as 3 com maior crescimento dentro do intervalo escolhido

4. **Arrecadação por Natureza Jurídica (2016–2024)**  
   - Filtros: intervalo de anos, seleção de meses (nomes em português), natureza jurídica (ou “Todas”) e nível temporal (mensal/anual)  
   - Série temporal de receita total agregada por natureza jurídica  
   - Ranking completo de todas as naturezas jurídicas em barras horizontais ascendentes

---

## Como Executar Localmente

1. **Clone este repositório**  
   ```bash
   git clone https://github.com/SEU_USUARIO/dashboard_tributaria.git
   cd dashboard_tributaria
Crie e ative um ambiente virtual (opcional)

bash
Copiar
Editar
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate
Instale as dependências

bash
Copiar
Editar
pip install --upgrade pip
pip install -r requirements.txt
Verifique se os arquivos estão no lugar

base_de_dados/tributos.db

base_de_dados/arrecadacao_CNAE_2016_2024.xlsx

geojson/ufs_brasil.json

Execute o Streamlit

bash
Copiar
Editar
streamlit run app.py
Acesse no navegador
Abra http://localhost:8501.

A página padrão é “Tributos Federais”.

No menu lateral, clique em “Carga por Natureza Jurídica” para acessar a segunda página.

## Screenshots 

- **Página “Tributos Federais”**: série temporal, mapa e crescimento percentual  
![image](https://github.com/user-attachments/assets/78091cd2-db32-4889-a00c-84587c097dc3)

- **Página “Arrecadação por Natureza Jurídica”**: série temporal e ranking completo


  ![image](https://github.com/user-attachments/assets/22dfe854-3f73-4761-bb77-63f6ec021de4)


## Próximos Passos

1. **Integração de Novas Bases**  
   - PIB estadual, população, número de empresas por UF  
   - Indicadores normalizados (receita per capita, receita por CNPJ)

2. **Filtros Avançados**  
   - Adicionar filtro por UF na página de Natureza Jurídica  
   - Filtrar por regime tributário ou CNAE na página principal

3. **Mapas Temáticos Adicionais**  
   - Choropleth por natureza jurídica  
   - Shapefiles municipais para análises mais detalhadas

4. **Insights Automatizados**  
   - Edição de callouts nos gráficos para destacar variações fora da curva

---

## Contribuições

Se você encontrar bugs, tiver sugestões ou quiser adicionar algo, abra uma **issue** ou envie um **pull request**. Toda ajuda é bem-vinda!

---

## Licença

Este projeto está disponível sob a **MIT License**.

---

Obrigado por visitar este projeto! Se tiver dúvidas, abra uma issue ou entre em contato.  
