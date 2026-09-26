import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime
from zoneinfo import ZoneInfo

# =====================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# =====================================================================
st.set_page_config(
    page_title="Campanha 2026 · Painel de Campo",
    page_icon="🗳️",
    layout="wide",
)

# Metas de campanha
META_CAMPANHA = 165
META_POR_LIDER = 15
SENHA_PADRAO = "BEBETO123"

# =====================================================================
# 2. CARREGAMENTO DOS DADOS
# =====================================================================
URL_SHEETS = "https://docs.google.com/spreadsheets/d/1YBtjLKdfZ-waj_s51MauE7Zo5xYs_TnjjhiT_WkA9Rc/export?format=csv"

@st.cache_data(ttl=60)
def carregar_dados():
    df = pd.read_csv(URL_SHEETS)
    df.columns = df.columns.astype(str).str.strip()
    
    def buscar_coluna(termos_busca):
        for col in df.columns:
            col_clean = col.upper().replace("Ç", "C").replace("Ã", "A").replace("Õ", "O").replace("É", "E")
            for termo in termos_busca:
                if termo in col_clean:
                    return col
        return None

    col_lider = buscar_coluna(["LIDER", "INDICACAO"])
    col_bairro = buscar_coluna(["BAIRRO"])
    col_nome = buscar_coluna(["NOME"])
    col_contato = buscar_coluna(["CONTATO", "TELEFONE", "CELULAR"])
    col_veiculo = buscar_coluna(["VEICULO", "POSSUI VEICULO"])

    renomear = {}
    if col_lider: renomear[col_lider] = "LIDER_PADRAO"
    if col_bairro: renomear[col_bairro] = "BAIRRO_PADRAO"
    if col_nome: renomear[col_nome] = "NOME_PADRAO"
    if col_contato: renomear[col_contato] = "CONTATO_PADRAO"
    if col_veiculo: renomear[col_veiculo] = "VEICULO_INFO_PADRAO"

    df = df.rename(columns=renomear)
    for c in [col for col in df.columns if "_PADRAO" in col]:
        df[c] = df[c].astype(str).str.strip().str.upper()
    return df

# =====================================================================
# 3. AUTENTICAÇÃO
# =====================================================================
def verificar_senha():
    senha_correta = st.secrets.get("senha_acesso", SENHA_PADRAO)
    if st.session_state.get("autenticado"):
        return

    st.subheader("🛡️ Acesso Restrito - Campanha 2026")
    senha_digitada = st.text_input("Digite a senha da equipe:", type="password")
    if st.button("Entrar"):
        if senha_digitada == senha_correta:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
    st.stop()

verificar_senha()

# =====================================================================
# 4. PAINEL PRINCIPAL
# =====================================================================
df = carregar_dados()

total_cadastros = len(df)
lideres_ativos = df["LIDER_PADRAO"].replace("NAN", pd.NA).dropna().nunique() if "LIDER_PADRAO" in df.columns else 0
bairros_cobertos = df["BAIRRO_PADRAO"].replace("NAN", pd.NA).dropna().nunique() if "BAIRRO_PADRAO" in df.columns else 0

agora = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y às %H:%M")

st.title("🗳️ Campanha 2026 · Painel de Campo")
st.caption(f"Dados sincronizados com a planilha · Atualizado em {agora}")

# Métricas (KPIs)
col1, col2, col3, col4 = st.columns(4)
col1.metric("👥 Cadastros Válidos", total_cadastros, f"Meta: {META_CAMPANHA}")
col2.metric("⭐ Líderes Ativos", lideres_ativos)
col3.metric("📍 Bairros Cobertos", bairros_cobertos)
col4.metric("📊 Progresso Geral", f"{(total_cadastros/META_CAMPANHA)*100:.1f}%")

st.progress(min(total_cadastros / META_CAMPANHA, 1.0))

st.divider()

# Abas de navegação simples
aba1, aba2, aba3 = st.tabs(["🏆 Lideranças", "📍 Bairros", "📋 Lista Completa"])

with aba1:
    st.subheader("Ranking de Captadores")
    if "LIDER_PADRAO" in df.columns:
        df_lideres = df[~df["LIDER_PADRAO"].isin(["NAN", "NONE", ""])]
        ranking = df_lideres["LIDER_PADRAO"].value_counts().reset_index()
        ranking.columns = ["Líder", "Total"]
        st.dataframe(ranking, use_container_width=True)
    else:
        st.info("Coluna de liderança não identificada.")

with aba2:
    st.subheader("Distribuição por Bairro")
    if "BAIRRO_PADRAO" in df.columns:
        df_bairros = df[~df["BAIRRO_PADRAO"].isin(["NAN", "NONE", ""])]
        bairros_counts = df_bairros["BAIRRO_PADRAO"].value_counts().reset_index()
        bairros_counts.columns = ["Bairro", "Total"]
        fig = px.bar(bairros_counts, x="Bairro", y="Total", text="Total")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Coluna de bairro não identificada.")

with aba3:
    st.subheader("Base de Apoiadores Cadastrados")
    st.dataframe(df, use_container_width=True)
