import pandas as pd
import plotly.express as px
import streamlit as st

# 1. Configuração da Página
st.set_page_config(
    page_title="Inteligência Eleitoral 2026",
    page_icon="📊",
    layout="wide",
)

# 2. Estilo Corporativo Limpo (Estilo Power BI)
st.markdown(
    """
    <style>
    /* Fundo corporativo */
    .stApp { background-color: #F8FAFC; color: #0F172A; }
    
    /* Cartões de KPI */
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        padding: 18px;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
    [data-testid="stMetricValue"] { color: #2563EB !important; font-size: 2.2rem; font-weight: 700; }
    [data-testid="stMetricLabel"] { color: #64748B !important; font-size: 0.9rem; font-weight: 600; }
    
    /* Títulos e Linhas */
    h1, h2, h3 { color: #0F172A; font-family: 'Segoe UI', sans-serif; }
    </style>
""",
    unsafe_allow_html=True,
)

# 3. Carregamento e Tratamento de Dados
URL_SHEETS = "https://docs.google.com/spreadsheets/d/1YBtjLKdfZ-waj_s51MauE7Zo5xYs_TnjjhiT_WkA9Rc/export?format=csv"


@st.cache_data(ttl=60)
def carregar_dados():
  df = pd.read_csv(URL_SHEETS)

  # Padronização de textos
  text_cols = [
      "INDICAÇÃO/LÍDER",
      "Nome",
      "Endereço",
      "Bairro",
      "Sexo",
      "Local de Votação",
  ]
  for col in text_cols:
    if col in df.columns:
      df[col] = df[col].astype(str).str.strip().str.title()

  # Tratamento de Data de Nascimento e Idade
  if "Data de Nascimento" in df.columns:
    df["Data_Nasc_DT"] = pd.to_datetime(
        df["Data de Nascimento"], format="%d/%m/%Y", errors="coerce"
    )
    df["Idade"] = 2026 - df["Data_Nasc_DT"].dt.year

    def faixa_etaria(idade):
      if pd.isna(idade):
        return "Não Informado"
      if idade < 25:
        return "18-24 anos"
      elif idade < 40:
        return "25-39 anos"
      elif idade < 60:
        return "40-59 anos"
      else:
        return "60+ anos"

    df["Faixa_Etaria"] = df["Idade"].apply(faixa_etaria)

  return df


df = carregar_dados()

# 4. Barra Lateral - Filtros
st.sidebar.header("🎯 Filtros da Campanha")

bairros_opts = (
    sorted(df["Bairro"].dropna().unique()) if "Bairro" in df.columns else []
)
bairro_sel = st.sidebar.multiselect(
    "Bairro:", options=bairros_opts, default=bairros_opts
)

lideres_opts = (
    sorted(df["INDICAÇÃO/LÍDER"].dropna().unique())
    if "INDICAÇÃO/LÍDER" in df.columns
    else []
)
lider_sel = st.sidebar.multiselect(
    "Liderança / Indicação:", options=lideres_opts, default=lideres_opts
)

# Aplicação dos Filtros
df_filtrado = df.copy()
if "Bairro" in df.columns and bairro_sel:
  df_filtrado = df_filtrado[df_filtrado["Bairro"].isin(bairro_sel)]
if "INDICAÇÃO/LÍDER" in df.columns and lider_sel:
  df_filtrado = df_filtrado[
      df_filtrado["INDICAÇÃO/LÍDER"].isin(lider_sel)
  ]

# 5. Cabeçalho
st.title("📊 Dashboard de Inteligência Eleitoral & Gestão de Lideranças")
st.markdown(
    "Acompanhamento em tempo real da base de apoiadores e desempenho das"
    " lideranças."
)
st.markdown("---")

# 6. Indicadores Principais (KPIs)
k1, k2, k3, k4 = st.columns(4)

tot_apoiadores = len(df_filtrado)
tot_lideres = (
    df_filtrado["INDICAÇÃO/LÍDER"].nunique()
    if "INDICAÇÃO/LÍDER" in df_filtrado.columns
    else 0
)
tot_bairros = (
    df_filtrado["Bairro"].nunique() if "Bairro" in df_filtrado.columns else 0
)
media_idade = (
    f"{df_filtrado['Idade'].mean():.1f} anos"
    if "Idade" in df_filtrado.columns and not df_filtrado["Idade"].isna().all()
    else "N/I"
)

k1.metric("Total de Apoiadores", tot_apoiadores)
k2.metric("Lideranças Ativas", tot_lideres)
k3.metric("Bairros Alcançados", tot_bairros)
k4.metric("Média de Idade", media_idade)

st.markdown("<br>", unsafe_allow_html=True)

# 7. Linha 1 de Gráficos (Bairros & Líderes - Decrescente)
col1, col2 = st.columns(2)

with col1:
  st.subheader("📍 Concentração por Bairro")
  if "Bairro" in df_filtrado.columns and not df_filtrado.empty:
    df_bairro = (
        df_filtrado["Bairro"]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "Bairro", "count": "Apoiadores"})
    )
    # Ordenar decrescente
    df_bairro = df_bairro.sort_values(by="Apoiadores", ascending=True)

    fig_bairro = px.bar(
        df_bairro,
        x="Apoiadores",
        y="Bairro",
        orientation="h",
        text="Apoiadores",
        color_discrete_sequence=["#2563EB"],
    )
    fig_bairro.update_traces(
        textposition="outside", cliponaxis=False, textfont_size=13
    )
    fig_bairro.update_layout(
        xaxis_title="",
        yaxis_title="",
        height=380,
        margin=dict(l=0, r=30, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_bairro, use_container_width=True)

with col2:
  st.subheader("👥 Desempenho dos Líderes (Top Recrutadores)")
  if "INDICAÇÃO/LÍDER" in df_filtrado.columns and not df_filtrado.empty:
    df_lider = (
        df_filtrado["INDICAÇÃO/LÍDER"]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "Líder", "count": "Apoiadores"})
    )
    # Ordenar decrescente
    df_lider = df_lider.sort_values(by="Apoiadores", ascending=False)

    fig_lider = px.bar(
        df_lider,
        x="Líder",
        y="Apoiadores",
        text="Apoiadores",
        color_discrete_sequence=["#0D9488"],
    )
    fig_lider.update_traces(
        textposition="outside", cliponaxis=False, textfont_size=13
    )
    fig_lider.update_layout(
        xaxis_title="",
        yaxis_title="",
        height=380,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_lider, use_container_width=True)

st.markdown("---")

# 8. Linha 2 de Gráficos (Faixa Etária & Gênero/Perfil)
col3, col4 = st.columns(2)

with col3:
  st.subheader("🎂 Distribuição por Faixa Etária")
  if "Faixa_Etaria" in df_filtrado.columns and not df_filtrado.empty:
    df_faixa = (
        df_filtrado["Faixa_Etaria"]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "Faixa", "count": "Apoiadores"})
    )
    df_faixa = df_faixa.sort_values(by="Apoiadores", ascending=False)

    fig_faixa = px.bar(
        df_faixa,
        x="Faixa",
        y="Apoiadores",
        text="Apoiadores",
        color_discrete_sequence=["#6366F1"],
    )
    fig_faixa.update_traces(textposition="outside", textfont_size=13)
    fig_faixa.update_layout(
        xaxis_title="",
        yaxis_title="",
        height=300,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_faixa, use_container_width=True)

with col4:
  st.subheader("👫 Distribuição por Sexo")
  if "Sexo" in df_filtrado.columns and not df_filtrado.empty:
    df_sexo = (
        df_filtrado["Sexo"]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "Sexo", "count": "Quantidade"})
    )
    fig_sexo = px.pie(
        df_sexo,
        names="Sexo",
        values="Quantidade",
        hole=0.4,
        color_discrete_sequence=["#3B82F6", "#EC4899", "#94A3B8"],
    )
    fig_sexo.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_sexo, use_container_width=True)

# 9. Tabela de Dados Brutos
st.markdown("---")
st.subheader("📋 Base de Dados Detalhada da Campanha")
st.dataframe(df_filtrado, use_container_width=True)
