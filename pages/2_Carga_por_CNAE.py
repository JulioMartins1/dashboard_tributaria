# pages/2_Carga_por_Natureza_Juridica.py

import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(
    page_title="Carga por Natureza Jurídica",
    layout="wide",
)

st.title("📊 Dashboard Tributária: Arrecadação por Natureza Jurídica (2016–2024)")
st.markdown("""
Nesta página, exploramos a arrecadação agregada por **Natureza Jurídica** (tipo de pessoa/entidade) entre 2016 e 2024.  
Use os filtros na barra lateral para:
- Selecionar intervalo de anos e meses (com nomes).  
- Escolher uma Natureza Jurídica específica (ou “Todas”).  
- Alternar entre visão **Mensal** ou **Anual** na série temporal.  
1. **Série Temporal**: mensal ou anual.  
2. **Ranking Completo**: barras horizontais maiores, ordenadas ascendentemente.  
""")

# --------------------------------------------------
# 1) Caminho para o arquivo Excel de Natureza Jurídica
# --------------------------------------------------

EXCEL_CNAE = r"dashboard_tributaria/base_de_dados/arrecadacao_CNAE_2016_2024.xlsx"
if not os.path.isfile(EXCEL_CNAE):
    st.error(f"Arquivo não encontrado em:\n  {EXCEL_CNAE}\nVerifique se está no local correto.")
    st.stop()

# --------------------------------------------------
# 2) Carregamento do Excel (cacheado)
# --------------------------------------------------

@st.cache_data
def load_natureza():
    df = pd.read_excel(EXCEL_CNAE)
    tributos_cols = [
        "imposto_importacao", "imposto_exportacao", "ipi", "irpf", "irpj", "irrf",
        "iof", "itr", "cofins", "pis_pasep", "csll", "cide_combustiveis",
        "contribuicao_previdenciaria", "cpsss", "pagamento_unificado",
        "outras_receitas_rfb", "demais_receitas"
    ]
    for c in tributos_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df["receita_total"] = df[tributos_cols].sum(axis=1)
    if "ano_mes" not in df.columns:
        df["ano_mes"] = pd.to_datetime(
            df["ano"].astype(str) + "-" + df["mes"].astype(str).str.zfill(2),
            format="%Y-%m", errors="coerce"
        )
    return df

df_nat = load_natureza()

# --------------------------------------------------
# 3) Filtros na sidebar (incluindo nomes de meses e nível de detalhe)
# --------------------------------------------------

st.sidebar.header("Filtros: Natureza Jurídica")

# 3.1) Faixa de Anos (2016–2024)
anos = sorted(df_nat["ano"].unique().tolist())
anos_validos = [a for a in anos if 2016 <= a <= 2024]
if not anos_validos:
    st.warning("Não há dados entre 2016 e 2024.")
    st.stop()

ano_inicio, ano_fim = st.sidebar.select_slider(
    "Faixa de Ano (2016–2024):",
    options=anos_validos,
    value=(2016, 2024)
)

# 3.2) Mês com nomes
mes_num_to_nome = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}
meses_disponiveis = sorted(df_nat["mes"].unique().tolist())
meses_validos = [m for m in meses_disponiveis if 1 <= m <= 12]
meses_nomeados = [mes_num_to_nome[m] for m in meses_validos]

meses_selecionado_nome = st.sidebar.multiselect(
    "Meses:",
    options=meses_nomeados,
    default=meses_nomeados
)
meses_selecionado = [k for k, v in mes_num_to_nome.items() if v in meses_selecionado_nome]

# 3.3) Natureza Jurídica
njs = df_nat["natureza_juridica_codigo_descricao"].dropna().unique().tolist()
njs.sort()
nj_sel = st.sidebar.selectbox(
    "Natureza Jurídica:",
    options=["Todas"] + njs,
    index=0
)

# 3.4) Nível de detalhe: Mensal ou Anual
nivel = st.sidebar.radio(
    "Nível Temporal:",
    options=["Mensal", "Anual"],
    index=0
)

# --------------------------------------------------
# 4) Filtragem principal
# --------------------------------------------------

df_filtrado = df_nat[
    (df_nat["ano"] >= ano_inicio) &
    (df_nat["ano"] <= ano_fim) &
    (df_nat["mes"].isin(meses_selecionado))
].copy()

if nj_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado["natureza_juridica_codigo_descricao"] == nj_sel]

# --------------------------------------------------
# 5) Série Temporal de Receita Total (Mensal ou Anual)
# --------------------------------------------------

st.subheader("1. Evolução da Receita Total por Natureza Jurídica")

if df_filtrado.empty:
    st.warning("Sem dados para estes filtros.")
else:
    if nivel == "Mensal":
        df_series = (
            df_filtrado
            .groupby("ano_mes", as_index=False)["receita_total"]
            .sum()
            .sort_values("ano_mes")
        )
        eixo_x = "ano_mes"
        label_x = "Ano-Mês"
        title_tempo = (
            "Receita Mensal "
            + (f"de {nj_sel} " if nj_sel != "Todas" else "")
            + f"({ano_inicio}–{ano_fim})"
        )
    else:  # Anual
        df_series = (
            df_filtrado
            .groupby("ano", as_index=False)["receita_total"]
            .sum()
            .sort_values("ano")
        )
        eixo_x = "ano"
        label_x = "Ano"
        title_tempo = (
            "Receita Anual "
            + (f"de {nj_sel} " if nj_sel != "Todas" else "")
            + f"({ano_inicio}–{ano_fim})"
        )

    fig1 = px.line(
        df_series,
        x=eixo_x,
        y="receita_total",
        labels={eixo_x: label_x, "receita_total": "Receita Total (R$)"},
        title=title_tempo
    )
    fig1.update_layout(
        template="plotly_white",
        title_font_size=18,
        xaxis_title_font_size=14,
        yaxis_title_font_size=14,
        xaxis_tickfont_size=12,
        yaxis_tickfont_size=12
    )
    if nivel == "Mensal":
        fig1.update_traces(
            hovertemplate="<b>Ano-Mês:</b> %{x|%Y-%m}<br><b>Receita:</b> R$ %{y:,.2f}<extra></extra>"
        )
    else:
        fig1.update_traces(
            hovertemplate="<b>Ano:</b> %{x}<br><b>Receita:</b> R$ %{y:,.2f}<extra></extra>"
        )
    st.plotly_chart(fig1, use_container_width=True)

# --------------------------------------------------
# 6) Ranking: Todas as Naturezas Jurídicas – Barra Horizontal Ascendente
# --------------------------------------------------

st.subheader("2. Ranking de Naturezas Jurídicas (Receita Total)")

df_para_ranking = df_nat[
    (df_nat["ano"] >= ano_inicio) &
    (df_nat["ano"] <= ano_fim) &
    (df_nat["mes"].isin(meses_selecionado))
].copy()

if nj_sel != "Todas":
    df_para_ranking = df_para_ranking[
        df_para_ranking["natureza_juridica_codigo_descricao"] == nj_sel
    ]

if df_para_ranking.empty:
    st.info("Sem dados para ranking.")
else:
    df_rank = (
        df_para_ranking
        .groupby("natureza_juridica_codigo_descricao", as_index=False)["receita_total"]
        .sum()
        .sort_values("receita_total", ascending=True)
    )

    fig2 = px.bar(
        df_rank,
        x="receita_total",
        y="natureza_juridica_codigo_descricao",
        orientation="h",
        labels={
            "natureza_juridica_codigo_descricao": "Natureza Jurídica",
            "receita_total": "Receita Total (R$)"
        },
        title=f"Naturezas Jurídicas Ordenadas por Receita Total ({ano_inicio}–{ano_fim})"
    )
    fig2.update_layout(
        template="plotly_white",
        title_font_size=18,
        xaxis_title_font_size=14,
        yaxis_title_font_size=14,
        xaxis_tickfont_size=12,
        yaxis_tickfont_size=12,
        margin={"l": 300, "r": 20, "t": 40, "b": 20},
        height=1200  # altura maior para que toda a lista apareça, e o usuário role a página
    )
    fig2.update_traces(
        marker=dict(color="#1f77b4"),
        hovertemplate="<b>Natureza Jurídica:</b> %{y}<br><b>Receita:</b> R$ %{x:,.2f}<extra></extra>"
    )
    st.plotly_chart(fig2, use_container_width=True)

# --------------------------------------------------
# 7) Observações e próximos passos
# --------------------------------------------------

st.markdown("---")
st.write("""
Nesta página (“Carga por Natureza Jurídica”), você pode:

- Filtrar por **anos** (2016–2024) e **meses** (com nomes).  
- Selecionar uma **natureza jurídica** específica ou “Todas”.  
- Alternar entre visão **Mensal** e **Anual** na série temporal.  
- Ver o **ranking completo** (barras horizontais) de todas as naturezas jurídicas, ordenado da menor para a maior receita total.  
  - Como definimos `height=1200` no gráfico, toda a lista fica visível e a página exibirá a barra de rolagem do próprio Streamlit quando necessário.

Em futuras versões, poderemos:
1. Incluir um **mapa** por natureza jurídica.  
2. Adicionar filtros por UF.  
3. Permitir segmentação por tributos individuais dentro de cada natureza jurídica.  
""")
