import re
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_option_menu import option_menu

# =====================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# =====================================================================
st.set_page_config(
    page_title="Campanha 2026 · Painel de Campo",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =====================================================================
# 2. IDENTIDADE VISUAL (design tokens)
# =====================================================================
NAVY = "#071A2D"
NAVY_SOFT = "#123A63"
BLUE = "#1D5FA6"
AMBER = "#F0A629"
GREEN = "#2E9E6D"
BG = "#F4F6F9"
CARD = "#FFFFFF"
TEXT = "#16202A"
MUTED = "#728096"
BORDER = "#E6EBF2"

PLOTLY_FONT = "Manrope, sans-serif"

META_CAMPANHA = 165
META_POR_LIDER = 15
SENHA_PADRAO = "BEBETO123"

def inject_css():
    st.markdown(
        f"""
        
        """,
        unsafe_allow_html=True,
    )

# =====================================================================
# 3. CARREGAMENTO E DADOS
# =====================================================================
URL_SHEETS = "https://docs.google.com/spreadsheets/d/1YBtjLKdfZ-waj_s51MauE7Zo5xYs_TnjjhiT_WkA9Rc/export?format=csv"

@st.cache_data(ttl=60)
def carregar_dados():
    df = pd.read_csv(URL_SHEETS)
    df.columns = df.columns.astype(str).str.strip()

    def buscar_coluna(termos_busca):
        for col in df.columns:
            col_clean = col.upper().replace("Ç", "C").replace("Ã", "A").replace("Õ", "O").replace("É", "E").replace("Ê", "E")
            for termo in termos_busca:
                if termo in col_clean:
                    return col
        return None

    col_lider = buscar_coluna(["LIDER", "INDICACAO"])
    col_bairro = buscar_coluna(["BAIRRO"])
    col_nome = buscar_coluna(["NOME"])
    col_contato = buscar_coluna(["CONTATO", "TELEFONE", "CELULAR", "ZAP"])
    col_veiculo = buscar_coluna(["POSSUI VEICULO", "MODEL", "VEICULO"])

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

def verificar_senha():
    senha_correta = st.secrets.get("senha_acesso", SENHA_PADRAO)
    if st.session_state.get("autenticado"):
        return

    st.markdown(
        """
