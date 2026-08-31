import pandas as pd
import plotly.express as px
import streamlit as st

# 1. Configuração da Página
st.set_page_config(
    page_title='Painel de Inteligência Eleitoral 2026',
    page_icon='📊',
    layout='wide',
    initial_sidebar_state='expanded',
)

# 2. Estilização CSS Personalizada (Visual Profissional / Dark Mode)
st.markdown(
    """
    <style>
    .main { background-color: #0F172A; }
    .stMetric {
        background-color: #1E293B;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    div[data-testid="stMetricValue"] { color: #38BDF8 !important; font-size: 2rem; font-weight: bold; }
    div[data-testid="stMetricLabel"] { color: #94A3B8 !important; font-size: 0.9rem; }
    </style>
""",
    unsafe_allow_html=True,
)

# 3. Carregamento dos Dados
URL_SHEETS = "https://docs.google.com/spreadsheets/d/1YBtjLKdfZ-waj_s51MauE7Zo5xYs_TnjjhiT_WkA9Rc/export?format=csv"


@st.cache_data(ttl=60)
def carregar_dados():
  df = pd.read_csv(URL_SHEETS)

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

  if "Data de Nascimento" in df.columns:
    df["Data_Nasc_DT"] = pd.to_datetime(
        df["Data de Nascimento"], format="%d/%m/%Y", errors="coerce"
    )
    df["Idade"] = 2026 - df["Data_Nasc_DT"].dt.year

  return df


df = carregar_dados()

# 4. Barra Lateral - Filtros
st.sidebar.title("🎯 Filtros Estratégicos")
st.sidebar.markdown("---")

bairros_unicos = (
    sorted(df["Bairro"].dropna().unique()) if "Bairro" in df.columns else []
)
bairro_sel = st.sidebar.multiselect(
    "Filtrar Bairro:", options=bairros_unicos, default=bairros_unicos
)

lideres_unicos = (
    sorted(df["INDICAÇÃO/LÍDER"].dropna().unique())
    if "INDICAÇÃO/LÍDER" in df.columns
    else []
)
lider_sel = st.sidebar.multiselect(
    "Filtrar Liderança:", options=lideres_unicos, default=lideres_unicos
)

# Aplicação de Filtros
df_filtrado = df.copy()
if "Bairro" in df.columns and bairro_sel:
  df_filtrado = df_filtrado[df_filtrado["Bairro"].isin(bairro_sel)]
if "INDICAÇÃO/LÍDER" in df.columns and lider_sel:
  df_filtrado = df_filtrado[
      df_filtrado["INDICAÇÃO/LÍDER"].isin(lider_sel)
  ]

# 5. Cabeçalho do Painel
st.title("📊 Painel Estratégico de Inteligência Eleitoral")
st.caption("Acompanhamento e Metrificação da Base de Apoiadores em Tempo Real")
st.markdown("---")

# 6. KPIs Principais
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

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

kpi1.metric("Apoiadores Mapeados", tot_apoiadores)
kpi2.metric("Lideranças Ativas", tot_lideres)
kpi3.metric("Bairros Cobertos", tot_bairros)
kpi4.metric("Média de Idade", media_idade)

st.markdown("<br>", unsafe_allow_html=True)

# 7. Organização por Abas (Navegação Limpa)
aba1, aba2, aba3 = st.tabs([
    "📈 Visão Geral & Bairros",
    "👥 Ranking de Lideranças",
    "📋 Base Detalhada",
])

with aba1:
  st.subheader("📍 Concentração de Votos por Bairro")
  if "Bairro" in df_filtrado.columns and not df_filtrado.empty:
    df_bairro = (
        df_filtrado["Bairro"]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "Bairro", "count": "Apoiadores"})
    )
    fig_bairro = px.bar(
        df_bairro,
        x="Apoiadores",
        y="Bairro",
        orientation="h",
        text="Apoiadores",
        color="Apoiadores",
        color_continuous_scale="Blues",
    )
    fig_bairro.update_layout(
        xaxis_title="Total de Apoiadores",
        yaxis_title="",
        showlegend=False,
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#FFFFFF"),
    )
    st.plotly_chart(fig_bairro, use_container_width=True)

with aba2:
  st.subheader("🏆 Top Lideranças por Recrutamento")
  if "INDICAÇÃO/LÍDER" in df_filtrado.columns and not df_filtrado.empty:
    df_lider = (
        df_filtrado["INDICAÇÃO/LÍDER"]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "Líder", "count": "Apoiadores"})
    )
    fig_lider = px.bar(
        df_lider.head(10),
        x="Líder",
        y="Apoiadores",
        text="Apoiadores",
        color="Apoiadores",
        color_continuous_scale="Teal",
    )
    fig_lider.update_layout(
        xaxis_title="",
        yaxis_title="Apoiadores Domiciliados",
        showlegend=False,
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#FFFFFF"),
    )
    st.plotly_chart(fig_lider, use_container_width=True)

with aba3:
  st.subheader("📋 Registros Filtrados da Campanha")
  st.dataframe(df_filtrado, use_container_width=True)
