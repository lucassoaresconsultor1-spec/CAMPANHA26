import pandas as pd
import plotly.express as px
import streamlit as st

# 1. Configuração da Página
st.set_page_config(
    page_title="Painel de Inteligência Eleitoral 2026",
    page_icon="📊",
    layout="wide",
)

# 2. Estilo Corporativo Limpo
st.markdown(
    """
    <style>
    .stApp { background-color: #F8FAFC; color: #0F172A; }
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        padding: 18px;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    [data-testid="stMetricValue"] { color: #1E40AF !important; font-size: 2.2rem; font-weight: 700; }
    [data-testid="stMetricLabel"] { color: #64748B !important; font-size: 0.9rem; font-weight: 600; }
    h1, h2, h3 { color: #0F172A; font-family: 'Segoe UI', sans-serif; }
    </style>
""",
    unsafe_allow_html=True,
)

# 3. Carregamento e Tratamento dos Dados
URL_SHEETS = "https://docs.google.com/spreadsheets/d/1YBtjLKdfZ-waj_s51MauE7Zo5xYs_TnjjhiT_WkA9Rc/export?format=csv"


@st.cache_data(ttl=60)
def carregar_dados():
  df = pd.read_csv(URL_SHEETS)

  # Padronização de Colunas de Texto
  colunas_texto = [
      "INDICAÇÃO/LÍDER",
      "Nome",
      "Endereço",
      "Bairro",
      "Sexo",
      "Local de Votação",
      "Possui Veículo?",
      "Tipo de Veículo",
  ]
  for col in colunas_texto:
    if col in df.columns:
      df[col] = df[col].astype(str).str.strip().str.title()

  # Idade e Faixa Etária
  if "Data de Nascimento" in df.columns:
    df["Data_Nasc_DT"] = pd.to_datetime(
        df["Data de Nascimento"], format="%d/%m/%Y", errors="coerce"
    )
    df["Idade"] = 2026 - df["Data_Nasc_DT"].dt.year

    def classificar_faixa(idade):
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

    df["Faixa_Etaria"] = df["Idade"].apply(classificar_faixa)

  return df


df = carregar_dados()

# 4. Filtros Laterais
st.sidebar.header("🎯 Filtros da Campanha")

bairros_opts = (
    sorted(df["Bairro"].dropna().unique()) if "Bairro" in df.columns else []
)
bairro_sel = st.sidebar.multiselect(
    "Filtrar Bairro:", options=bairros_opts, default=bairros_opts
)

lideres_opts = (
    sorted(df["INDICAÇÃO/LÍDER"].dropna().unique())
    if "INDICAÇÃO/LÍDER" in df.columns
    else []
)
lider_sel = st.sidebar.multiselect(
    "Filtrar Liderança:", options=lideres_opts, default=lideres_opts
)

# Aplicando Filtros
df_filtrado = df.copy()
if "Bairro" in df.columns and bairro_sel:
  df_filtrado = df_filtrado[df_filtrado["Bairro"].isin(bairro_sel)]
if "INDICAÇÃO/LÍDER" in df.columns and lider_sel:
  df_filtrado = df_filtrado[
      df_filtrado["INDICAÇÃO/LÍDER"].isin(lider_sel)
  ]

# 5. Cabeçalho Principal
st.title("📊 Painel de Inteligência Eleitoral & Gestão de Base")
st.caption("Visão estratégica unificada de apoiadores, lideranças e logística")
st.markdown("---")

# 6. Métricas/KPIs Gerais
k1, k2, k3, k4, k5 = st.columns(5)

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

# Contagem de veículos
if "Possui Veículo?" in df_filtrado.columns:
  tot_veiculos = df_filtrado[
      df_filtrado["Possui Veículo?"].isin(["Sim", "S", "True"])
  ].shape[0]
else:
  tot_veiculos = 0

k1.metric("Total Apoiadores", tot_apoiadores)
k2.metric("Lideranças Ativas", tot_lideres)
k3.metric("Bairros Cobertos", tot_bairros)
k4.metric("Média de Idade", media_idade)
k5.metric("Veículos Cadastrados", tot_veiculos)

st.markdown("<br>", unsafe_allow_html=True)

# 7. SEÇÃO 1: Gestão de Lideranças & Listagem de Apoiadores por Bairros
st.header("👥 1. Gestão de Lideranças & Mapeamento por Bairro")
col_lider, col_bairro = st.columns(2)

with col_lider:
  st.subheader("Desempenho dos Líderes (Top Recrutadores)")
  if "INDICAÇÃO/LÍDER" in df_filtrado.columns and not df_filtrado.empty:
    df_lider = (
        df_filtrado["INDICAÇÃO/LÍDER"]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "Líder", "count": "Apoiadores"})
    )
    df_lider = df_lider.sort_values(by="Apoiadores", ascending=False)

    fig_lider = px.bar(
        df_lider,
        x="Líder",
        y="Apoiadores",
        text="Apoiadores",
        color_discrete_sequence=["#0284C7"],
    )
    fig_lider.update_traces(textposition="outside", textfont_size=12)
    fig_lider.update_layout(
        xaxis_title="",
        yaxis_title="Total Indicado",
        height=350,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_lider, use_container_width=True)

with col_bairro:
  st.subheader("Listagem de Apoiadores por Bairro")
  if "Bairro" in df_filtrado.columns and not df_filtrado.empty:
    df_bairro = (
        df_filtrado["Bairro"]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "Bairro", "count": "Apoiadores"})
    )
    df_bairro = df_bairro.sort_values(by="Apoiadores", ascending=True)

    fig_bairro = px.bar(
        df_bairro,
        x="Apoiadores",
        y="Bairro",
        orientation="h",
        text="Apoiadores",
        color_discrete_sequence=["#1E40AF"],
    )
    fig_bairro.update_traces(
        textposition="outside", cliponaxis=False, textfont_size=12
    )
    fig_bairro.update_layout(
        xaxis_title="",
        yaxis_title="",
        height=350,
        margin=dict(l=0, r=25, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_bairro, use_container_width=True)

st.markdown("---")

# 8. SEÇÃO 2: Perfil Demográfico & Veículos Cadastrados
st.header("🎂 2. Perfil Demográfico & Logística (Veículos)")
col_demo1, col_demo2, col_veic = st.columns(3)

with col_demo1:
  st.subheader("Faixa Etária")
  if "Faixa_Etaria" in df_filtrado.columns and not df_filtrado.empty:
    df_faixa = (
        df_filtrado["Faixa_Etaria"]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "Faixa", "count": "Quantidade"})
    )
    df_faixa = df_faixa.sort_values(by="Quantidade", ascending=False)

    fig_faixa = px.bar(
        df_faixa,
        x="Faixa",
        y="Quantidade",
        text="Quantidade",
        color_discrete_sequence=["#6366F1"],
    )
    fig_faixa.update_traces(textposition="outside", textfont_size=12)
    fig_faixa.update_layout(
        xaxis_title="",
        yaxis_title="",
        height=300,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_faixa, use_container_width=True)

with col_demo2:
  st.subheader("Distribuição por Sexo")
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
        color_discrete_sequence=["#0284C7", "#EC4899", "#94A3B8"],
    )
    fig_sexo.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_sexo, use_container_width=True)

with col_veic:
  st.subheader("Tipos de Veículos")
  if "Tipo de Veículo" in df_filtrado.columns and not df_filtrado.empty:
    df_veic_tipo = (
        df_filtrado["Tipo de Veículo"]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "Tipo", "count": "Quantidade"})
    )
    df_veic_tipo = df_veic_tipo.sort_values(by="Quantidade", ascending=False)

    fig_veic = px.bar(
        df_veic_tipo,
        x="Tipo",
        y="Quantidade",
        text="Quantidade",
        color_discrete_sequence=["#0D9488"],
    )
    fig_veic.update_traces(textposition="outside", textfont_size=12)
    fig_veic.update_layout(
        xaxis_title="",
        yaxis_title="",
        height=300,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_veic, use_container_width=True)
  else:
    st.info("Sem dados de tipo de veículo registrados.")

# 9. SEÇÃO 3: Tabela Detalhada dos Dados
st.markdown("---")
st.header("📋 3. Base de Dados Detalhada")
st.dataframe(df_filtrado, use_container_width=True)
