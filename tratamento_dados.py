# app.py

import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, inspect
import os
import json

# --------------------------------------------------
# 1) Configuração inicial do Streamlit e do título
# --------------------------------------------------

st.set_page_config(
    page_title="Dashboard Tributária: Drill‐Down e Filtros Limpinhos",
    layout="wide",
)

st.title("📊 Dashboard Tributária: Drill‐Down por Tipo de Imposto")
st.markdown("""
Neste dashboard, você poderá:
1. Ver a série temporal de qualquer tributo (ou receita total) por UF, com opção de **drill‐down** (mensal)  
   ou **drill‐up** (anual).  
2. Visualizar um **mapa choropleth** pintando cada UF conforme a média mensal do tributo selecionado.  

Use os filtros na barra lateral para escolher:
- A UF (ou “Todas”)  
- O intervalo de anos (2000–2024)  
- O tributo desejado (com nomes “limpos”)  
- O nível de detalhe (“Anual” vs “Mensal”)  
- O tributo para o mapa (média mensal)  
""")

# --------------------------------------------------
# 2) Conexão com o banco SQLite (caminho absoluto)
# --------------------------------------------------

DB_PATH = r"G:\Meu Drive\Portifolio\dashboard_tributaria\base_de_dados\tributos.db"
if not os.path.isfile(DB_PATH):
    st.error(
        f"O arquivo de banco de dados não foi encontrado em:\n  {DB_PATH}\n\n"
        "Certifique-se de que você executou o ETL para criar/popular o SQLite antes de rodar este app."
    )
    st.stop()

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
inspector = inspect(engine)

# --------------------------------------------------
# 3) Carregamento da tabela de arrecadação (cacheado)
# --------------------------------------------------

@st.cache_data(show_spinner=False)
def load_arrecadacao():
    # Lê a tabela de arrecadação federal
    df = pd.read_sql("SELECT * FROM arrecadacao_federal", engine)

    # Identificar colunas fixas e colunas de tributos
    colunas_fixas = {"ano", "mes", "sigla_uf", "sigla_uf_nome", "ano_mes"}
    todas_colunas = set(df.columns)
    colunas_tributos = sorted(list(todas_colunas - colunas_fixas))

    # Converter todas as colunas de tributos para numérico e criar 'receita_total'
    for col in colunas_tributos:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    if "receita_total" not in df.columns:
        df["receita_total"] = df[colunas_tributos].sum(axis=1)

    # Garantir coluna datetime 'ano_mes'
    if "ano_mes" not in df.columns:
        df["ano_mes"] = pd.to_datetime(
            df["ano"].astype(str) + "-" + df["mes"].astype(str).str.zfill(2),
            format="%Y-%m",
            errors="coerce"
        )

    return df, colunas_tributos

df_arrec, colunas_tributos = load_arrecadacao()

# --------------------------------------------------
# 4) “Limpeza” de nomes: cria dicionários para exibir nomes legíveis e mapear de volta
# --------------------------------------------------

def limpar_nome(col):
    """
    Recebe 'cofins_entidades_financeiras' e retorna 'Cofins Entidades Financeiras'.
    """
    return col.replace("_", " ").capitalize()

# Constrói um dict {nome_limpo: coluna_original}
# Ex: { "Cofins": "cofins", "Irpf": "irpf", ... }
dicionario_limpo_para_original = {"Receita Total": "receita_total"}
for trib in colunas_tributos:
    dicionario_limpo_para_original[limpar_nome(trib)] = trib

# Lista de opções “limpas” para exibir nos selects
opcoes_tributos_limpos = list(dicionario_limpo_para_original.keys())
opcoes_tributos_limpos.sort()  # Ordena alfabeticamente

# --------------------------------------------------
# 5) Filtros na sidebar
# --------------------------------------------------

st.sidebar.header("Filtros de Análise")

# 5.1) Filtro de UF
ufs = sorted(df_arrec["sigla_uf"].unique().tolist())
uf_selecionada = st.sidebar.selectbox(
    "Unidade da Federação (UF):",
    options=["Todas"] + ufs,
    index=0
)

# 5.2) Filtro de intervalo de anos (2000–2024)
anos_disponiveis = sorted(df_arrec["ano"].unique().tolist())
anos_validos = [ano for ano in anos_disponiveis if 2000 <= ano <= 2024]
if not anos_validos:
    st.warning("Não há registros de arrecadação entre 2000 e 2024.")
    st.stop()

ano_inicio, ano_fim = st.sidebar.select_slider(
    "Faixa de Ano (2000–2024):",
    options=list(range(min(anos_validos), max(anos_validos) + 1)),
    value=(2000, 2024)
)

# 5.3) Filtro de tributo para a série temporal (com nomes “limpos”)
tributo_serie_limpo = st.sidebar.selectbox(
    "Tributo para Série Temporal:",
    options=opcoes_tributos_limpos,
    index=opcoes_tributos_limpos.index("Receita Total")  # padrão “Receita Total”
)
# Para recuperar o nome da coluna original:
tributo_serie = dicionario_limpo_para_original[tributo_serie_limpo]

# 5.4) Radio para drill‐down: “Anual” vs “Mensal”
nivel_detail = st.sidebar.radio(
    "Nível de Detalhamento:",
    options=["Anual", "Mensal"],
    index=1  # padrão “Mensal”
)

# 5.5) Filtro de tributo para o mapa (média mensal por UF)
tributo_mapa_limpo = st.sidebar.selectbox(
    "Tributo para Mapa (Média Mensal):",
    options=opcoes_tributos_limpos,
    index=opcoes_tributos_limpos.index("Receita Total")
)
tributo_mapa = dicionario_limpo_para_original[tributo_mapa_limpo]

# --------------------------------------------------
# 6) Filtragem do DataFrame de arrecadação
# --------------------------------------------------

df_filtrado = df_arrec.copy()

# Filtra por UF (se não for “Todas”)
if uf_selecionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado["sigla_uf"] == uf_selecionada]

# Filtra por intervalo de anos (inclusivo)
df_filtrado = df_filtrado[
    (df_filtrado["ano"] >= ano_inicio) &
    (df_filtrado["ano"] <= ano_fim)
]

# --------------------------------------------------
# 7) Gráfico 1: Série Temporal com Drill‐Down/Up
# --------------------------------------------------

st.subheader("1. Evolução do Tributo Selecionado")

if df_filtrado.empty:
    st.warning("Não há dados de arrecadação para esses filtros (UF ou período).")
else:
    # Se o usuário escolher detalhe “Anual”, agrupar por ano:
    if nivel_detail == "Anual":
        df_agrupado = (
            df_filtrado
            .groupby(["ano", "sigla_uf"], as_index=False)[[tributo_serie]]
            .sum()
            .rename(columns={tributo_serie: "valor_agrupado"})
        )
        # Para exibir no eixo x, poderíamos usar apenas “ano” (inteiro). 
        eixo_x = "ano"
        label_x = "Ano"
        titulo_tempo = f"Série Anual de {tributo_serie_limpo} ({ano_inicio}–{ano_fim})"
    else:
        # Detalhamento Mensal: usar diretamente 'ano_mes' (datetime)
        # Garante a coluna ano_mes
        if "ano_mes" not in df_filtrado.columns or df_filtrado["ano_mes"].isna().all():
            df_filtrado["ano_mes"] = pd.to_datetime(
                df_filtrado["ano"].astype(str) + "-" +
                df_filtrado["mes"].astype(str).str.zfill(2),
                format="%Y-%m",
                errors="coerce"
            )
        df_agrupado = df_filtrado.rename(
            columns={tributo_serie: "valor_agrupado"}
        )
        eixo_x = "ano_mes"
        label_x = "Ano-Mês"
        titulo_tempo = f"Série Mensal de {tributo_serie_limpo} ({ano_inicio}–{ano_fim})"

    # Desenha o gráfico de linha
    fig_tempo = px.line(
        df_agrupado.sort_values(eixo_x),
        x=eixo_x,
        y="valor_agrupado",
        color="sigla_uf",
        labels={
            eixo_x: label_x,
            "valor_agrupado": tributo_serie_limpo + " (R$)",
            "sigla_uf": "UF"
        },
        title=titulo_tempo
    )
    fig_tempo.update_layout(legend_title_text="UF")

    # Formata tooltip em Real (R$)
    # Se estiver usando eixo_x = "ano_mes", `%{x|%Y-%m}` formata o hover do eixo x
    if nivel_detail == "Mensal":
        fig_tempo.update_traces(
            hovertemplate=(
                "<b>UF: %{color}</b><br>"
                f"{label_x}: %{{x|%Y-%m}}<br>"
                f"{tributo_serie_limpo}: R$ %{{y:,.2f}}<extra></extra>"
            )
        )
    else:  # Anual
        fig_tempo.update_traces(
            hovertemplate=(
                "<b>UF: %{color}</b><br>"
                f"Ano: %{{x}}<br>"
                f"{tributo_serie_limpo}: R$ %{{y:,.2f}}<extra></extra>"
            )
        )

    st.plotly_chart(fig_tempo, use_container_width=True)

# --------------------------------------------------
# 8) Mapa e Tabela: Média Mensal do Tributo por UF
# --------------------------------------------------

st.subheader("2. Tabela e Mapa: Média Mensal do Tributo por UF")

CAMINHO_GEOJSON = "geojson/ufs_brasil.json"
if not os.path.isfile(CAMINHO_GEOJSON):
    st.warning(
        f"GeoJSON não encontrado em `{CAMINHO_GEOJSON}`.\n"
        "Certifique‐se de gerar o arquivo `ufs_brasil.json` dentro de `geojson/`, "
        "com `properties.sigla` preenchido para cada UF."
    )
else:
    # Carrega GeoJSON
    with open(CAMINHO_GEOJSON, "r", encoding="utf-8") as f:
        geojson_uf = json.load(f)

    # Agrupa por UF para média mensal do tributo_mapa
    df_mapa = (
        df_filtrado
        .groupby("sigla_uf", as_index=False)[[tributo_mapa]]
        .mean()
        .rename(columns={tributo_mapa: "valor_medio"})
    )

    if df_mapa.empty:
        st.info("Não há dados suficientes para gerar a tabela ou o mapa.")
    else:
        # Normaliza siglas
        df_mapa["sigla_uf"] = df_mapa["sigla_uf"].str.upper().str.strip()

        # Formata coluna "valor_medio" como R$
        df_mapa["Valor Médio (R$)"] = df_mapa["valor_medio"].apply(lambda x: f"R$ {x:,.2f}")

        # Exibe tabela de amostra
        df_exibir = df_mapa[["sigla_uf", "Valor Médio (R$)"]].rename(columns={"sigla_uf": "UF"})
        st.markdown("**Tabela de Amostra: Média Mensal por UF**")
        st.dataframe(df_exibir, use_container_width=True)

        # Cria choropleth
        fig_mapa = px.choropleth(
            df_mapa,
            geojson=geojson_uf,
            locations="sigla_uf",
            featureidkey="properties.sigla",
            color="valor_medio",
            color_continuous_scale="plasma",
            labels={"valor_medio": f"Média de {tributo_mapa_limpo} (R$)"},
            title=f"Média Mensal de {tributo_mapa_limpo} por UF",
        )

        # Zoom no Brasil, sem eixos
        fig_mapa.update_geos(
            fitbounds="locations",
            visible=False
        )

        # Bordas brancas para destacar
        fig_mapa.update_traces(
            marker_line_color="white",
            marker_line_width=0.8
        )

        # Hovertemplate formatado (string normal, sem usar f-string para não confundir “z”)
        hover_map = (
            "<b>UF: %{location}</b><br>"
            f"Média de {tributo_mapa_limpo}: R$ %{{z:,.2f}}<extra></extra>"
        )
        fig_mapa.update_traces(
            hovertemplate=hover_map
        )

        # Colorbar formatado em R$
        fig_mapa.update_coloraxes(
            colorbar_title_text=f"Média de {tributo_mapa_limpo} (R$)",
            colorbar_tickprefix="R$ ",
            colorbar_tickformat=",.0f"
        )

        # Layout escuro, fundo transparente
        fig_mapa.update_layout(
            margin={"r": 0, "t": 40, "l": 0, "b": 0},
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )

        st.plotly_chart(fig_mapa, use_container_width=True)

# --------------------------------------------------
# 9) Observações e próximos passos
# --------------------------------------------------

st.markdown("---")
st.write("""
**Observações / Próximos Passos**  
- **Drill-down/Up**: use o radio “Nível de Detalhamento” para alternar entre:
  - Anual (soma por ano)  
  - Mensal (valores mês a mês)  
- **Nomes Limpinhos**: todos os selects de tributos exibem texto legível (por exemplo, “Irpf”),
  mas internamente o código mapeia de volta para `"irpf"` ao buscar no DataFrame.

- Em iterações futuras, você pode:
  1. Adicionar opção “Multiselect” para escolher **dois ou mais tributos** na série:
     - Fazer `df.melt(...)` e `px.line(...)` com `color="tipo_imposto"`.  
  2. Trocar `.mean()` por `.sum()` em **Mapa** para ver Valor Total Acumulado.  
  3. Ajustar paleta de cores (`color_continuous_scale`) ou estilo de bordas.  
  4. Inserir filtros adicionais (Região, CNAE, etc.) na sidebar.  
  5. Incluir botão de download para tabela CSV/PDF.
""")
