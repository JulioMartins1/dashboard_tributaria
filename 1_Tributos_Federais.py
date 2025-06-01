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
    page_title="Dashboard Tributária: V1 com Drill-Down e Top-5",
    layout="wide",
)

st.title("📊 Dashboard Tributária: Análise por Tipo de Imposto (v1)")
st.markdown("""
Neste dashboard (v1), você poderá:
1. Ver a **série temporal** de qualquer tributo (ou receita total) por UF, com opção de **drill-down** (mensal) ou **drill-up** (anual), mostrando apenas as 5 UFs de maior arrecadação por padrão.  
2. Visualizar um **mapa choropleth** do Brasil, pintando cada UF de acordo com a média mensal do tributo selecionado.  
3. Conferir um mini-relatório (CTA) ao final, indicando os estados com maior queda e maior crescimento, de acordo com o intervalo de anos selecionado.

Use os filtros na barra lateral para escolher:
- A UF (ou “Todas”)  
- O intervalo de anos (2000–2024)  
- O tributo para a série temporal (com nomes limpos)  
- O nível de detalhe (“Anual” vs “Mensal”)  
- O tributo para o mapa (média mensal)  
""")

# --------------------------------------------------
# 2) Conexão com o banco SQLite (caminho relativo)
# --------------------------------------------------

DB_PATH = os.path.join("base_de_dados", "tributos.db")
if not os.path.isfile(DB_PATH):
    st.error(
        f"O arquivo de banco de dados não foi encontrado em:\n  {DB_PATH}\n\n"
        "Certifique-se de executar o ETL localmente e de ter adicionado 'tributos.db' à pasta 'base_de_dados/'."
    )
    st.stop()

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
inspector = inspect(engine)

# --------------------------------------------------
# 3) Carregamento da tabela de arrecadação (cacheado)
# --------------------------------------------------

@st.cache_data(show_spinner=False)
def load_arrecadacao():
    df = pd.read_sql("SELECT * FROM arrecadacao_federal", engine)

    colunas_fixas = {"ano", "mes", "sigla_uf", "sigla_uf_nome", "ano_mes"}
    todas_colunas = set(df.columns)
    colunas_tributos = sorted(list(todas_colunas - colunas_fixas))

    for col in colunas_tributos:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    if "receita_total" not in df.columns:
        df["receita_total"] = df[colunas_tributos].sum(axis=1)

    if "ano_mes" not in df.columns:
        df["ano_mes"] = pd.to_datetime(
            df["ano"].astype(str) + "-" + df["mes"].astype(str).str.zfill(2),
            format="%Y-%m",
            errors="coerce"
        )

    return df, colunas_tributos

df_arrec, colunas_tributos = load_arrecadacao()

# --------------------------------------------------
# 4) Função para “limpar” nomes de coluna
# --------------------------------------------------

def limpar_nome(col):
    return col.replace("_", " ").capitalize()

dicionario_limpo_para_original = {"Receita Total": "receita_total"}
for trib in colunas_tributos:
    dicionario_limpo_para_original[limpar_nome(trib)] = trib

opcoes_tributos_limpos = list(dicionario_limpo_para_original.keys())
opcoes_tributos_limpos.sort()

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

# 5.3) Tributo para Série Temporal (nome limpo)
tributo_serie_limpo = st.sidebar.selectbox(
    "Tributo para Série Temporal:",
    options=opcoes_tributos_limpos,
    index=opcoes_tributos_limpos.index("Receita Total")
)
tributo_serie = dicionario_limpo_para_original[tributo_serie_limpo]

# 5.4) Drill-down / Drill-up
nivel_detail = st.sidebar.radio(
    "Nível de Detalhamento:",
    options=["Anual", "Mensal"],
    index=1  # Mensal por padrão
)

# 5.5) Tributo para Mapa (nome limpo)
tributo_mapa_limpo = st.sidebar.selectbox(
    "Tributo para Mapa (Média Mensal por UF):",
    options=opcoes_tributos_limpos,
    index=opcoes_tributos_limpos.index("Receita Total")
)
tributo_mapa = dicionario_limpo_para_original[tributo_mapa_limpo]

# --------------------------------------------------
# 6) Filtragem do DataFrame de arrecadação
# --------------------------------------------------

df_filtrado = df_arrec.copy()

if uf_selecionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado["sigla_uf"] == uf_selecionada]

df_filtrado = df_filtrado[
    (df_filtrado["ano"] >= ano_inicio) &
    (df_filtrado["ano"] <= ano_fim)
]

# --------------------------------------------------
# 7) Gráfico 1: Série Temporal com Drill-Down/Up e Top-5
# --------------------------------------------------

st.subheader("1. Evolução do Tributo Selecionado")

if df_filtrado.empty:
    st.warning("Não há dados de arrecadação para esses filtros (UF ou período).")
else:
    if nivel_detail == "Mensal":
        if "ano_mes" not in df_filtrado.columns or df_filtrado["ano_mes"].isna().all():
            df_filtrado["ano_mes"] = pd.to_datetime(
                df_filtrado["ano"].astype(str) + "-" +
                df_filtrado["mes"].astype(str).str.zfill(2),
                format="%Y-%m",
                errors="coerce"
            )

    if nivel_detail == "Anual":
        df_agrupado = (
            df_filtrado
            .groupby(["ano", "sigla_uf"], as_index=False)[[tributo_serie]]
            .sum()
            .rename(columns={tributo_serie: "valor_agrupado"})
        )
        eixo_x = "ano"
        label_x = "Ano"
        titulo_tempo = f"Série Anual de {tributo_serie_limpo} ({ano_inicio}–{ano_fim})"
    else:
        df_agrupado = df_filtrado.rename(columns={tributo_serie: "valor_agrupado"})
        eixo_x = "ano_mes"
        label_x = "Ano-Mês"
        titulo_tempo = f"Série Mensal de {tributo_serie_limpo} ({ano_inicio}–{ano_fim})"

    soma_por_uf = (
        df_agrupado
        .groupby("sigla_uf")["valor_agrupado"]
        .sum()
        .sort_values(ascending=False)
    )
    top5_ufs = soma_por_uf.head(5).index.tolist()
    df_top5 = df_agrupado[df_agrupado["sigla_uf"].isin(top5_ufs)]

    fig_tempo = px.line(
        df_top5.sort_values(eixo_x),
        x=eixo_x,
        y="valor_agrupado",
        color="sigla_uf",
        labels={
            eixo_x: label_x,
            "valor_agrupado": tributo_serie_limpo + " (R$)",
            "sigla_uf": "UF"
        },
        title=titulo_tempo + "  (Top 5 UFs por Arrecadação)"
    )
    fig_tempo.update_layout(legend_title_text="UF")

    if nivel_detail == "Mensal":
        fig_tempo.update_traces(
            hovertemplate=(
                "<b>UF: %{color}</b><br>"
                f"{label_x}: %{{x|%Y-%m}}<br>"
                f"{tributo_serie_limpo}: R$ %{{y:,.2f}}<extra></extra>"
            )
        )
    else:
        fig_tempo.update_traces(
            hovertemplate=(
                "<b>UF: %{color}</b><br>"
                f"Ano: %{{x}}<br>"
                f"{tributo_serie_limpo}: R$ %{{y:,.2f}}<extra></extra>"
            )
        )

    st.plotly_chart(fig_tempo, use_container_width=True)
    st.markdown(
        "*Observe que, por padrão, estamos exibindo apenas as 5 UFs com maior soma de receita no período filtrado.*"
    )

# --------------------------------------------------
# 8) Mapa e Tabela: Média Mensal do Tributo por UF
# --------------------------------------------------

st.subheader("2. Tabela e Mapa: Média Mensal do Tributo por UF")

CAMINHO_GEOJSON = "geojson/ufs_brasil.json"
if not os.path.isfile(CAMINHO_GEOJSON):
    st.warning(
        f"GeoJSON não encontrado em `{CAMINHO_GEOJSON}`.\n"
        "Certifique-se de gerar `ufs_brasil.json` dentro da pasta `geojson/`, "
        "com `properties.sigla` para cada UF."
    )
else:
    with open(CAMINHO_GEOJSON, "r", encoding="utf-8") as f:
        geojson_uf = json.load(f)

    df_mapa = (
        df_filtrado
        .groupby("sigla_uf", as_index=False)[[tributo_mapa]]
        .mean()
        .rename(columns={tributo_mapa: "valor_medio"})
    )

    if df_mapa.empty:
        st.info("Não há dados suficientes para gerar a tabela ou o mapa.")
    else:
        df_mapa["sigla_uf"] = df_mapa["sigla_uf"].str.upper().str.strip()
        df_mapa["Valor Médio (R$)"] = df_mapa["valor_medio"].apply(lambda x: f"R$ {x:,.2f}")

        df_exibir = df_mapa[["sigla_uf", "Valor Médio (R$)"]].rename(columns={"sigla_uf": "UF"})
        st.markdown("**Tabela de Amostra: Média Mensal por UF**")
        st.dataframe(df_exibir, use_container_width=True)

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

        fig_mapa.update_geos(fitbounds="locations", visible=False)
        fig_mapa.update_traces(marker_line_color="white", marker_line_width=0.8)

        hover_map = (
            "<b>UF: %{location}</b><br>"
            f"Média de {tributo_mapa_limpo}: R$ %{{z:,.2f}}<extra></extra>"
        )
        fig_mapa.update_traces(hovertemplate=hover_map)

        fig_mapa.update_coloraxes(
            colorbar_title_text=f"Média de {tributo_mapa_limpo} (R$)",
            colorbar_tickprefix="R$ ",
            colorbar_tickformat=",.0f"
        )

        fig_mapa.update_layout(
            margin={"r": 0, "t": 40, "l": 0, "b": 0},
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )

        st.plotly_chart(fig_mapa, use_container_width=True)

# --------------------------------------------------
# 9) CTA: Crescimento percentual dinâmico no intervalo selecionado
# --------------------------------------------------

st.subheader("3. Crescimento Percentual no Intervalo Selecionado")

# 9.1) Soma anual do tributo_serie por UF, mas só dentro do intervalo de anos filtrado
soma_ano = (
    df_filtrado
    .groupby(["ano", "sigla_uf"])[tributo_serie]
    .sum()
    .reset_index()
)

# 9.2) Agora usamos ano_inicio e ano_fim do filtro (em vez de "2000" e "2024" fixos)
if ano_inicio in soma_ano["ano"].values and ano_fim in soma_ano["ano"].values:
    soma_start = (
        soma_ano[soma_ano["ano"] == ano_inicio]
        .set_index("sigla_uf")[tributo_serie]
    )
    soma_end = (
        soma_ano[soma_ano["ano"] == ano_fim]
        .set_index("sigla_uf")[tributo_serie]
    )
    comuns = soma_start.index.intersection(soma_end.index)
    crescimento = ((soma_end[comuns] - soma_start[comuns]) / soma_start[comuns] * 100).sort_values()

    top_quedas = crescimento.head(3)
    top_crescimentos = crescimento.tail(3)

    st.markdown(f"**Três UFs com maior queda percentual ({ano_inicio} → {ano_fim}):**")
    if not top_quedas.empty:
        df_quedas = pd.DataFrame({
            "UF": top_quedas.index,
            "Queda (%)": top_quedas.values
        })
        df_quedas["Queda (%)"] = df_quedas["Queda (%)"].apply(lambda x: f"{x:.2f}%")
        st.table(df_quedas)
    else:
        st.write("Não há dados completos para calcular quedas neste intervalo.")

    st.markdown(f"**Três UFs com maior crescimento percentual ({ano_inicio} → {ano_fim}):**")
    if not top_crescimentos.empty:
        df_cres = pd.DataFrame({
            "UF": top_crescimentos.index,
            "Crescimento (%)": top_crescimentos.values
        })
        df_cres["Crescimento (%)"] = df_cres["Crescimento (%)"].apply(lambda x: f"{x:.2f}%")
        st.table(df_cres)
    else:
        st.write("Não há dados completos para calcular crescimentos neste intervalo.")
else:
    st.info(f"Não há valores de {ano_inicio} e/ou {ano_fim} suficientes para calcular crescimento percentual neste intervalo.")
