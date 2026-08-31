import pandas as pd
import streamlit as st

# Configuração da Página
st.set_page_config(
    page_title='Inteligência Eleitoral 2026', page_icon='📊', layout='wide'
)

# Título Principal
st.title('📊 Dashboard de Inteligência Eleitoral & Gestão de Lideranças')
st.markdown('---')

# Carregar Dados do Google Sheets
URL_SHEETS = 'https://docs.google.com/spreadsheets/d/1YBtjLKdfZ-waj_s51MauE7Zo5xYs_TnjjhiT_WkA9Rc/export?format=csv'


@st.cache_data(ttl=60)  # Atualiza a cada 60 segundos
def carregar_dados():
  df = pd.read_csv(URL_SHEETS)

  # Padronização de textos
  text_cols = [
      'INDICAÇÃO/LÍDER',
      'Nome',
      'Endereço',
      'Bairro',
      'Sexo',
      'Local de Votação',
  ]
  for col in text_cols:
    if col in df.columns:
      df[col] = df[col].astype(str).str.strip().str.title()

  # Idade
  if 'Data de Nascimento' in df.columns:
    df['Data_Nasc_DT'] = pd.to_datetime(
        df['Data de Nascimento'], format='%d/%m/%Y', errors='coerce'
    )
    df['Idade'] = 2026 - df['Data_Nasc_DT'].dt.year

  return df


df = carregar_dados()

# --- FILTROS LATERAIS ---
st.sidebar.header('Filtros da Campanha')
bairro_selecionado = st.sidebar.multiselect(
    'Filtrar por Bairro:',
    options=df['Bairro'].dropna().unique(),
    default=df['Bairro'].dropna().unique(),
)

# Aplicar Filtro
df_filtrado = df[df['Bairro'].isin(bairro_selecionado)]

# --- MÉTRICAS PRINCIPAIS (KPIs) ---
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric('Total de Apoiadores', len(df_filtrado))

if 'INDICAÇÃO/LÍDER' in df.columns:
  kpi2.metric(
      'Lideranças Ativas', df_filtrado['INDICAÇÃO/LÍDER'].nunique()
  )

if 'Idade' in df.columns and not df_filtrado['Idade'].isna().all():
  kpi3.metric('Média de Idade', f"{df_filtrado['Idade'].mean():.1f} anos")

st.markdown('---')

# --- GRÁFICOS E TABELAS ---
col1, col2 = st.columns(2)

with col1:
  st.subheader('📍 Apoiadores por Bairro')
  bairro_counts = df_filtrado['Bairro'].value_counts()
  st.bar_chart(bairro_counts)

with col2:
  st.subheader('👥 Desempenho dos Líderes')
  if 'INDICAÇÃO/LÍDER' in df.columns:
    lider_counts = df_filtrado['INDICAÇÃO/LÍDER'].value_counts()
    st.bar_chart(lider_counts)

# --- TABELA DE DADOS BRUTOS ---
st.markdown('---')
st.subheader('📋 Base de Dados Detalhada')
st.dataframe(df_filtrado, use_container_width=True)
