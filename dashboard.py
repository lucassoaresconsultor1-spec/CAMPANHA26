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
AMBER_TEXT = "#8A5A12"  

PLOTLY_FONT = "Manrope, sans-serif"
PLOTLY_PALETTE = [BLUE, AMBER, GREEN]


def estilizar_grafico(fig, height=320, margin=None):
    """Aplica a identidade visual premium a qualquer figura Plotly."""
    fig.update_layout(
        font_family=PLOTLY_FONT,
        font_color=TEXT,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=margin or dict(l=0, r=10, t=10, b=10),
        height=height,
        hoverlabel=dict(
            bgcolor="white",
            bordercolor=BORDER,
            font_size=12,
            font_family=PLOTLY_FONT,
        ),
        hovermode="closest",
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=BORDER)
    fig.update_yaxes(showgrid=True, gridcolor=BORDER, zeroline=False, linecolor=BORDER)
    return fig

# Metas de campanha
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
# 3. CARREGAMENTO E TRATAMENTO DOS DADOS
# =====================================================================
URL_SHEETS = "https://docs.google.com/spreadsheets/d/1YBtjLKdfZ-waj_s51MauE7Zo5xYs_TnjjhiT_WkA9Rc/export?format=csv"


@st.cache_data(ttl=60)
def carregar_dados():
    df = pd.read_csv(URL_SHEETS)
    df.columns = df.columns.astype(str).str.strip()

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
    col_veiculo = buscar_coluna(["POSSUI VEICULO", "MODEL", "VEICULO", "TEM VEICULO"])
    col_adesivo = buscar_coluna(["ADESIVO"])
    col_trabalho_dia = buscar_coluna(["TRABALHO DIA", "DIA DA ELEICAO", "DIA E", "MESARIO", "TRABALHO ELEICAO"])

    renomear = {}
    if col_lider: renomear[col_lider] = "LIDER_PADRAO"
    if col_bairro: renomear[col_bairro] = "BAIRRO_PADRAO"
    if col_nome: renomear[col_nome] = "NOME_PADRAO"
    if col_contato: renomear[col_contato] = "CONTATO_PADRAO"
    if col_sexo: renomear[col_sexo] = "SEXO_PADRAO"
    if col_nasc: renomear[col_nasc] = "NASCIMENTO_PADRAO"
    if col_veiculo: renomear[col_veiculo] = "VEICULO_INFO_PADRAO"
    if col_adesivo: renomear[col_adesivo] = "ADESIVO_PADRAO"
    if col_trabalho_dia: renomear[col_trabalho_dia] = "TRABALHO_DIA_PADRAO"

    df = df.rename(columns=renomear)

    text_cols = [c for c in df.columns if "_PADRAO" in c]
    for c in text_cols:
        df[c] = df[c].astype(str).str.strip().str.upper()

    if "NASCIMENTO_PADRAO" in df.columns:
        df["Data_Nasc_DT"] = pd.to_datetime(
            df["NASCIMENTO_PADRAO"], format="%d/%m/%Y", errors="coerce"
        )
        df["Idade"] = 2026 - df["Data_Nasc_DT"].dt.year

        def classificar_faixa(idade):
            if pd.isna(idade):
                return "Não informado"
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


def verificar_senha():
    senha_correta = st.secrets.get("senha_acesso", SENHA_PADRAO)

    if st.session_state.get("autenticado"):
        return

    st.markdown(
        f"""
