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

  # Limpar nomes das colunas originais (remover espaços extras)
  df.columns = df.columns.astype(str).str.strip()

  # Identificar colunas dinamicamente para evitar erro de digitação
  def buscar_coluna(termos_busca):
    for col in df.columns:
      col_clean = (
          col.upper()
          .replace("Ç", "C")
          .replace("Ã", "A")
          .replace("Õ", "O")
          .replace("É", "E")
          .replace("Ê", "E")
      )
      for termo in termos_busca:
        if termo in col_clean:
          return col
    return None

  col_lider = buscar_coluna(["LIDER", "INDICACAO"])
  col_bairro = buscar_coluna(["BAIRRO"])
  col_nome = buscar_coluna(["NOME"])
  col_contato = buscar_coluna(["CONTATO", "TELEFONE", "CELULAR", "ZAP"])
  col_sexo = buscar_coluna(["SEXO", "GENERO"])
  col_nasc = buscar_coluna(["NASCIMENTO", "DATA_NASC"])
  col_veic_posssui = buscar_coluna(["POSSUI VEICULO", "TEM VEICULO", "VEICULO"])
  col_veic_tipo = buscar_coluna(["TIPO DE VEICULO", "TIPO VEICULO", "MODELO"])

  # Mapear para nomes padronizados internos
  renomear = {}
  if col_lider:
    renomear[col_lider] = "LIDER_PADRAO"
  if col_bairro:
    renomear[col_bairro] = "BAIRRO_PADRAO"
  if col_nome:
    renomear[col_nome] = "NOME_PADRAO"
  if col_contato:
    renomear[col_contato] = "CONTATO_PADRAO"
  if col_sexo:
    renomear[col_sexo] = "SEXO_PADRAO"
  if col_nasc:
    renomear[col_nasc] = "NASCIMENTO_PADRAO"
  if col_veic_posssui:
    renomear[col_veic_posssui] = "VEICULO_POSSUI_PADRAO"
  if col_veic_tipo:
    renomear[col_veic_tipo] = "VEICULO_TIPO_PADRAO"

  df = df.rename(columns=renomear)

  # Tratamento de textos
  text_cols = [c for c in df.columns if "_PADRAO" in c]
  for c in text_cols:
    df[c] = df[c].astype(str).str.strip().str.upper()

  # Tratamento de Idade
  if "NASCIMENTO_PADRAO" in df.columns:
    df["Data_Nasc_DT"] = pd.to_datetime(
        df["NASCIMENTO_PADRAO"], format="%d/%m/%Y", errors="coerce"
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
    df["LIDER_PADRAO"].replace("NAN", np.nan).dropna().nunique()
    if "LIDER_PADRAO" in df.columns
    else 0
)
bairros_cobertos = (
    df["BAIRRO_PADRAO"].replace("NAN", np.nan).dropna().nunique()
    if "BAIRRO_PADRAO" in df.columns
    else 0
)

# Filtro flexível para saber quem tem veículo
if "VEICULO_POSSUI_PADRAO" in df.columns:
  df_veiculos_filtro = df[
      df["VEICULO_POSSUI_PADRAO"].str.contains(
          "SIM|S|TRUE|1|CARRO|MOTO", na=False
      )
  ]
  veiculos_mapeados = len(df_veiculos_filtro)
else:
  df_veiculos_filtro = pd.DataFrame()
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

  if "LIDER_PADRAO" in df.columns and not df.empty:
    df_clean_lider = df[
        ~df["LIDER_PADRAO"].isin(["NAN", "NONE", "", "NÃO INFORMADO"])
    ]
    df_lideres = (
        df_clean_lider["LIDER_PADRAO"]
        .value_counts()
        .reset_index()
        .rename(columns={"LIDER_PADRAO": "Líder", "count": "Total de Apoiadores"})
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
  else:
    st.warning(
        "Não foi encontrada a coluna referente aos Líderes/Indicações na"
        " planilha."
    )

# ==========================================
# ABA 2: LISTAGEM DE APOIADORES POR BAIRRO
# ==========================================
with tab2:
  st.header("2. Raio-X de Bairros e Apoiadores Inclusos")

  if "BAIRRO_PADRAO" in df.columns:
    bairros_validos = sorted(
        [
            b
            for b in df["BAIRRO_PADRAO"].dropna().unique()
            if b not in ["NAN", "NONE", ""]
        ]
    )
    lista_bairros = ["TODOS OS BAIRROS"] + bairros_validos
    bairro_sel = st.selectbox("🔍 Filtrar por Bairro Específico:", lista_bairros)

    df_bairros_filtro = df.copy()
    if bairro_sel != "TODOS OS BAIRROS":
      df_bairros_filtro = df_bairros_filtro[
          df_bairros_filtro["BAIRRO_PADRAO"] == bairro_sel
      ]

    contagem_bairros = (
        df_bairros_filtro["BAIRRO_PADRAO"]
        .value_counts()
        .drop(labels=["NAN", ""], errors="ignore")
    )
    bairros_ordenados = contagem_bairros.index.tolist()

    # Organizar nomes amigáveis para exibir na tabela
    mapa_exibicao = {
        "CONTATO_PADRAO": "Contato",
        "NOME_PADRAO": "Nome",
        "LIDER_PADRAO": "Líder",
        "BAIRRO_PADRAO": "Bairro",
    }
    cols_presentes = [
        c for c in ["CONTATO_PADRAO", "NOME_PADRAO", "LIDER_PADRAO"] if c in df.columns
    ]

    for b in bairros_ordenados:
      sub_df = df_bairros_filtro[df_bairros_filtro["BAIRRO_PADRAO"] == b]
      tabela_exibir = sub_df[cols_presentes].rename(columns=mapa_exibicao)
      with st.expander(f"🏠 {b} — ({len(sub_df)} apoiador(es) cadastrado(s))"):
        st.dataframe(tabela_exibir, use_container_width=True, hide_index=True)

# ==========================================
# ABA 3: PERFIL DEMOGRÁFICO
# ==========================================
with tab3:
  st.header("3. Perfil Demográfico do Eleitorado")

  if "SEXO_PADRAO" in df.columns and "Idade" in df.columns:
    df_sexo_clean = df[~df["SEXO_PADRAO"].isin(["NAN", "NONE", ""])]
    st.subheader("Resumo por Gênero e Idade Média")
    resumo_sexo = (
        df_sexo_clean.groupby("SEXO_PADRAO")
        .agg(
            Quantidade=("SEXO_PADRAO", "count"),
            Idade_Media=("Idade", lambda x: round(x.mean(), 1)),
        )
        .reset_index()
    )
    resumo_sexo["% da Base"] = (
        (resumo_sexo["Quantidade"] / total_cadastros) * 100
    ).round(1).astype(str) + "%"
    resumo_sexo["Idade Média"] = (
        resumo_sexo["Idade_Media"].fillna(0).astype(str) + " anos"
    )
    resumo_sexo = resumo_sexo.rename(
        columns={"SEXO_PADRAO": "Gênero"}
    ).sort_values(by="Quantidade", ascending=False)

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

  if not df_veiculos_filtro.empty:
    c_v1, c_v2 = st.columns(2)
    c_v1.metric("Total de Veículos Registrados", len(df_veiculos_filtro))
    c_v2.metric(
        "Bairros Cobertos com Veículo",
        (
            df_veiculos_filtro["BAIRRO_PADRAO"].replace("NAN", np.nan).nunique()
            if "BAIRRO_PADRAO" in df_veiculos_filtro
            else 0
        ),
    )

    st.markdown("---")

    bairros_v_validos = sorted(
        [
            b
            for b in df_veiculos_filtro["BAIRRO_PADRAO"].dropna().unique()
            if b not in ["NAN", "NONE", ""]
        ]
    )
    lista_bairros_v = ["TODOS OS BAIRROS"] + bairros_v_validos
    bairro_v_sel = st.selectbox(
        "🔍 Filtrar Veículos por Bairro:", lista_bairros_v
    )

    df_veic_exibir = df_veiculos_filtro.copy()
    if bairro_v_sel != "TODOS OS BAIRROS":
      df_veic_exibir = df_veic_exibir[
          df_veic_exibir["BAIRRO_PADRAO"] == bairro_v_sel
      ]

    mapa_veic = {
        "NOME_PADRAO": "Nome",
        "CONTATO_PADRAO": "Contato",
        "BAIRRO_PADRAO": "Bairro",
        "LIDER_PADRAO": "Líder",
        "VEICULO_TIPO_PADRAO": "Tipo de Veículo",
    }

    cols_veic = [
        c
        for c in [
            "NOME_PADRAO",
            "CONTATO_PADRAO",
            "BAIRRO_PADRAO",
            "LIDER_PADRAO",
            "VEICULO_TIPO_PADRAO",
        ]
        if c in df_veic_exibir.columns
    ]
    st.dataframe(
        df_veic_exibir[cols_veic].rename(columns=mapa_veic),
        use_container_width=True,
        hide_index=True,
    )
  else:
    st.info("Nenhum apoiador com veículo registrado ou identificado na planilha.")
