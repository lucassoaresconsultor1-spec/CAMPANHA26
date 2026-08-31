import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# 1. Configuração da Página
st.set_page_config(
    page_title="Eleitoral - Campanha 2026", page_icon="📊", layout="wide"
)

# 2. Carregamento e Tratamento dos Dados
URL_SHEETS = "https://docs.google.com/spreadsheets/d/1YBtjLKdfZ-waj_s51MauE7Zo5xYs_TnjjhiT_WkA9Rc/export?format=csv"


@st.cache_data(ttl=60)
def carregar_dados():
  df = pd.read_csv(URL_SHEETS)

  # Limpeza das colunas de texto principais
  text_cols = [
      "INDICAÇÃO/LÍDER",
      "Nome",
      "Endereço",
      "Bairro",
      "Sexo",
      "Local de Votação",
      "Contato",
      "Possui Veículo?",
      "Tipo de Veículo",
  ]
  for col in text_cols:
    if col in df.columns:
      df[col] = df[col].astype(str).str.strip().str.upper()

  # Tratamento de Data de Nascimento e Idade
  if "Data de Nascimento" in df.columns:
    df["Data_Nasc_DT"] = pd.to_datetime(
        df["Data de Nascimento"], format="%d/%m/%Y", errors="coerce"
    )
    df["Idade"] = 2026 - df["Data_Nasc_DT"].dt.year

    def classificar_faixa(idade):
      if pd.isna(idade):
        return "Não Informado"
      elif idade < 25:
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

# 3. Cabeçalho e Métricas Principais (Topo)
st.title("Campanha 2026")

total_cadastros = len(df)
lideres_ativos = (
    df["INDICAÇÃO/LÍDER"].nunique() if "INDICAÇÃO/LÍDER" in df.columns else 0
)
bairros_cobertos = df["Bairro"].nunique() if "Bairro" in df.columns else 0

if "Possui Veículo?" in df.columns:
  veiculos_mapeados = df[
      df["Possui Veículo?"].astype(str).str.contains("SIM|S|TRUE|1", na=False)
  ].shape[0]
else:
  veiculos_mapeados = 0

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric(
    "Total de Cadastros Válidos",
    total_cadastros,
    help="Quantidade total de apoiadores registrados na base.",
)
col_m2.metric(
    "Líderes Ativos",
    lideres_ativos,
    help="Número de lideranças com pelo menos uma indicação.",
)
col_m3.metric(
    "Bairros Cobertos",
    bairros_cobertos,
    help="Total de bairros com presença registrada.",
)
col_m4.metric(
    "Veículos Mapeados (Dia E)",
    veiculos_mapeados,
    help="Total de veículos cadastrados para a logística de dia de eleição.",
)

st.markdown("---")

# 4. Navegação por Abas
tab1, tab2, tab3, tab4 = st.tabs([
    "👥 1. Gestão de Lideranças",
    "📍 2. Listagem de Apoiadores por Bairro",
    "🎯 3. Perfil Demográfico",
    "🚗 4. Veículos Disponíveis",
])

# ==========================================
# ABA 1: GESTÃO DE LIDERANÇAS
# ==========================================
with tab1:
  st.header("1. Desempenho e Produtividade dos Multiplicadores")

  if "INDICAÇÃO/LÍDER" in df.columns and not df.empty:
    df_lideres = (
        df["INDICAÇÃO/LÍDER"]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "Líder", "count": "Total de Apoiadores"})
    )
    df_lideres["% da Base"] = (
        (df_lideres["Total de Apoiadores"] / total_cadastros) * 100
    ).round(1).astype(str) + "%"

    # Ordenar decrescente
    df_lideres = df_lideres.sort_values(
        by="Total de Apoiadores", ascending=False
    )

    st.subheader("Ranking de Captadores")
    st.dataframe(df_lideres, use_container_width=True, hide_index=True)

    st.subheader("Volume por Líder")
    fig_lider = px.bar(
        df_lideres,
        x="Líder",
        y="Total de Apoiadores",
        text="Total de Apoiadores",
        color_discrete_sequence=["#0066CC"],
    )
    fig_lider.update_traces(textposition="outside")
    fig_lider.update_layout(
        xaxis_title="",
        yaxis_title="Total de Apoiadores",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"categoryorder": "total descending"},
    )
    st.plotly_chart(fig_lider, use_container_width=True)

# ==========================================
# ABA 2: LISTAGEM DE APOIADORES POR BAIRRO
# ==========================================
with tab2:
  st.header("2. Raio-X de Bairros e Apoiadores Inclusos")

  if "Bairro" in df.columns:
    lista_bairros = ["TODOS OS BAIRROS"] + sorted(
        [b for b in df["Bairro"].dropna().unique() if b != "NAN"]
    )
    bairro_sel = st.selectbox("🔍 Filtrar por Bairro Específico:", lista_bairros)

    df_bairros_filtro = df.copy()
    if bairro_sel != "TODOS OS BAIRROS":
      df_bairros_filtro = df_bairros_filtro[
          df_bairros_filtro["Bairro"] == bairro_sel
      ]

    bairros_unicos = df_bairros_filtro["Bairro"].dropna().unique()

    # Ordenar bairros pela quantidade decrescente de apoiadores
    contagem_bairros = df_bairros_filtro["Bairro"].value_counts()
    bairros_ordenados = contagem_bairros.index.tolist()

    cols_exibicao = [
        c
        for c in [
            "Contato",
            "Nome",
            "INDICAÇÃO/LÍDER",
            "Endereço",
            "Local de Votação",
        ]
        if c in df.columns
    ]

    for b in bairros_ordenados:
      sub_df = df_bairros_filtro[df_bairros_filtro["Bairro"] == b]
      with st.expander(f"🏠 {b} — ({len(sub_df)} apoiador(es) cadastrado(s))"):
        st.dataframe(
            sub_df[cols_exibicao], use_container_width=True, hide_index=True
        )

# ==========================================
# ABA 3: PERFIL DEMOGRÁFICO
# ==========================================
with tab3:
  st.header("3. Perfil Demográfico do Eleitorado")

  if "Sexo" in df.columns and "Idade" in df.columns:
    st.subheader("Resumo por Gênero e Idade Média")
    resumo_sexo = (
        df.groupby("Sexo")
        .agg(
            Quantidade=("Nome", "count"),
            Idade_Media=("Idade", lambda x: round(x.mean(), 1)),
        )
        .reset_index()
    )
    resumo_sexo["% da Base"] = (
        (resumo_sexo["Quantidade"] / total_cadastros) * 100
    ).round(1).astype(str) + "%"
    resumo_sexo["Idade Média"] = resumo_sexo["Idade_Media"].astype(str) + " anos"
    resumo_sexo = resumo_sexo.rename(columns={"Sexo": "Gênero"}).sort_values(
        by="Quantidade", ascending=False
    )

    st.dataframe(
        resumo_sexo[["Gênero", "Quantidade", "% da Base", "Idade Média"]],
        use_container_width=True,
        hide_index=True,
    )

    media_geral = df["Idade"].mean()
    if not np.isnan(media_geral):
      st.subheader("Média de Idade Geral da Base")
      st.markdown(f"### **{media_geral:.1f} anos**")

  st.subheader("Distribuição por Faixa Etária")
  if "Faixa_Etaria" in df.columns:
    df_faixa = df["Faixa_Etaria"].value_counts().reset_index()
    df_faixa.columns = ["Faixa Etária", "Quantidade"]
    # Ordenação decrescente por quantidade
    df_faixa = df_faixa.sort_values(by="Quantidade", ascending=False)

    fig_faixa = px.bar(
        df_faixa,
        x="Faixa Etária",
        y="Quantidade",
        text="Quantidade",
        color_discrete_sequence=["#0066CC"],
    )
    fig_faixa.update_traces(textposition="outside")
    fig_faixa.update_layout(
        xaxis_title="",
        yaxis_title="Quantidade",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"categoryorder": "total descending"},
    )
    st.plotly_chart(fig_faixa, use_container_width=True)

# ==========================================
# ABA 4: VEÍCULOS DISPONÍVEIS
# ==========================================
with tab4:
  st.header("🚗 4. Relação de Apoiadores com Veículos Disponíveis")

  if "Possui Veículo?" in df.columns:
    df_veiculos = df[
        df["Possui Veículo?"].astype(str).str.contains("SIM|S|TRUE|1", na=False)
    ].copy()

    c_v1, c_v2 = st.columns(2)
    c_v1.metric("Total de Veículos Registrados", len(df_veiculos))
    c_v2.metric(
        "Bairros Cobertos com Veículo",
        df_veiculos["Bairro"].nunique() if "Bairro" in df_veiculos else 0,
    )

    st.markdown("---")

    lista_bairros_v = ["TODOS OS BAIRROS"] + sorted(
        [b for b in df_veiculos["Bairro"].dropna().unique() if b != "NAN"]
    )
    bairro_v_sel = st.selectbox(
        "🔍 Filtrar Veículos por Bairro:", lista_bairros_v
    )

    if bairro_v_sel != "TODOS OS BAIRROS":
      df_veiculos = df_veiculos[df_veiculos["Bairro"] == bairro_v_sel]

    cols_veic = [
        c
        for c in [
            "Nome",
            "Contato",
            "Bairro",
            "Tipo de Veículo",
            "INDICAÇÃO/LÍDER",
        ]
        if c in df_veiculos.columns
    ]
    st.dataframe(
        df_veiculos[cols_veic], use_container_width=True, hide_index=True
    )
  else:
    st.info("A coluna 'Possui Veículo?' não foi encontrada na planilha.")
