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
# Paleta "centro de comando" premium: base institucional em azul-marinho
# profundo, com âmbar como acento de destaque (topo do ranking, alertas)
# e verde reservado para metas atingidas.
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
AMBER_TEXT = "#8A5A12"  # tom escuro do âmbar, usado só em texto sobre fundo claro

PLOTLY_FONT = "Manrope, sans-serif"
PLOTLY_PALETTE = [BLUE, AMBER, GREEN]


def estilizar_grafico(fig, height=320, margin=None):
    """Aplica a identidade visual premium (fonte, cores, grid) a qualquer
    figura Plotly do painel, sem tocar nos dados ou na lógica do gráfico."""
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

# Senha de acesso: de preferência configure em Settings > Secrets no
# Streamlit Cloud com a chave "senha_acesso" (não fica visível no
# GitHub). Se não configurar, usa a senha abaixo como padrão.
SENHA_PADRAO = "BEBETO123"


def inject_css():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Manrope', sans-serif;
        }}

        #MainMenu, footer, header {{ visibility: hidden; }}

        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        @keyframes fillBar {{
            from {{ width: 0%; }}
        }}
        @keyframes pulseGlow {{
            0%, 100% {{ box-shadow: 0 0 0 0 rgba(240, 166, 41, 0.35); }}
            50% {{ box-shadow: 0 0 0 7px rgba(240, 166, 41, 0); }}
        }}
        @keyframes shimmer {{
            0% {{ background-position: -200% 0; }}
            100% {{ background-position: 200% 0; }}
        }}

        /* ---------- Fundo institucional com glow suave ---------- */
        .stApp {{
            background: {BG};
            position: relative;
        }}
        .stApp::before, .stApp::after {{
            content: "";
            position: fixed;
            width: 620px;
            height: 620px;
            border-radius: 50%;
            pointer-events: none;
            z-index: 0;
        }}
        .stApp::before {{
            top: -260px;
            right: -220px;
            background: radial-gradient(circle, rgba(29, 95, 166, 0.14), transparent 70%);
        }}
        .stApp::after {{
            bottom: -260px;
            left: -220px;
            background: radial-gradient(circle, rgba(240, 166, 41, 0.12), transparent 70%);
        }}

        .block-container {{
            padding-top: 1rem;
            padding-bottom: 3rem;
            max-width: 1200px;
            position: relative;
            z-index: 1;
        }}

        /* ---------- Cabeçalho (hero / centro de comando) ---------- */
        .hero {{
            position: relative;
            overflow: hidden;
            background: linear-gradient(135deg, {NAVY} 0%, {NAVY_SOFT} 55%, {BLUE} 100%);
            border-radius: 22px;
            padding: 32px 32px 28px 32px;
            color: white;
            margin-bottom: 24px;
            box-shadow: 0 24px 44px -20px rgba(7, 26, 45, 0.5), inset 0 1px 0 rgba(255,255,255,0.08);
            animation: fadeInUp 0.5s ease-out;
        }}
        .hero::before {{
            content: "";
            position: absolute;
            inset: 0;
            background: radial-gradient(circle at 12% -20%, rgba(255,255,255,0.18), transparent 55%);
            pointer-events: none;
        }}
        .hero::after {{
            content: "";
            position: absolute;
            top: -50%;
            right: -8%;
            width: 280px;
            height: 280px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(240,166,41,0.28), transparent 70%);
            pointer-events: none;
        }}
        .hero .eyebrow {{
            position: relative;
            color: {AMBER};
            font-weight: 800;
            font-size: 0.8rem;
            letter-spacing: 1.2px;
            margin-bottom: 4px;
            z-index: 1;
        }}
        .hero h1 {{
            position: relative;
            margin: 0;
            font-size: 2.05rem;
            font-weight: 800;
            line-height: 1.15;
            letter-spacing: -0.01em;
            z-index: 1;
        }}
        .hero p {{
            position: relative;
            margin-top: 6px;
            color: #C7D3E0;
            font-size: 0.92rem;
            z-index: 1;
        }}

        /* ---------- Grid de indicadores (KPIs) ---------- */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 14px;
            margin-bottom: 8px;
        }}
        @media (max-width: 900px) {{
            .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
        @media (max-width: 680px) {{
            .kpi-grid {{ grid-template-columns: repeat(2, 1fr); gap: 10px; }}
            .hero h1 {{ font-size: 1.5rem; }}
            .hero {{ padding: 22px 18px; border-radius: 18px; }}
        }}
        @media (max-width: 420px) {{
            .kpi-grid {{ grid-template-columns: 1fr; }}
        }}
        .kpi-card {{
            position: relative;
            overflow: hidden;
            background: linear-gradient(180deg, #FFFFFF 0%, #FBFCFE 100%);
            border: 1px solid {BORDER};
            border-radius: 16px;
            padding: 18px 20px 16px 20px;
            box-shadow: 0 10px 22px -16px rgba(7, 26, 45, 0.2);
            animation: fadeInUp 0.5s ease-out backwards;
            transition: transform 0.25s ease, box-shadow 0.25s ease;
        }}
        .kpi-card::before {{
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 4px;
            background: linear-gradient(90deg, {BLUE}, {AMBER});
        }}
        .kpi-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 18px 32px -16px rgba(7, 41, 66, 0.28);
        }}
        .kpi-grid .kpi-card:nth-child(1) {{ animation-delay: 0.05s; }}
        .kpi-grid .kpi-card:nth-child(2) {{ animation-delay: 0.12s; }}
        .kpi-grid .kpi-card:nth-child(3) {{ animation-delay: 0.19s; }}
        .kpi-grid .kpi-card:nth-child(4) {{ animation-delay: 0.26s; }}
        .kpi-card .kpi-label {{
            color: {MUTED};
            font-size: 0.8rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .kpi-card .kpi-value {{
            color: {TEXT};
            font-size: 2.15rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            margin-top: 5px;
        }}

        /* ---------- Cartão de seção (glassmorphism leve) ---------- */
        .section-card {{
            background: rgba(255, 255, 255, 0.78);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid {BORDER};
            border-radius: 18px;
            padding: 22px 24px;
            margin-bottom: 20px;
            box-shadow: 0 14px 30px -22px rgba(7, 26, 45, 0.18);
            animation: fadeInUp 0.4s ease-out;
        }}
        .section-title {{
            font-size: 1.15rem;
            font-weight: 800;
            color: {TEXT};
            margin-bottom: 2px;
        }}
        .section-subtitle {{
            color: {MUTED};
            font-size: 0.85rem;
            margin-bottom: 16px;
        }}

        /* ---------- Ranking de líderes (leaderboard premium) ---------- */
        .rank-row {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 11px 8px;
            border-bottom: 1px solid {BORDER};
            border-radius: 10px;
            transition: background 0.2s ease, transform 0.2s ease;
            animation: fadeInUp 0.4s ease-out backwards;
        }}
        .rank-row:hover {{ background: #F7F9FC; transform: translateX(2px); }}
        .rank-row:last-child {{ border-bottom: none; }}
        .rank-badge {{
            width: 30px;
            height: 30px;
            min-width: 30px;
            border-radius: 9px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 0.95rem;
            background: #EEF1F5;
            color: {MUTED};
            transition: transform 0.2s ease;
        }}
        .rank-row:hover .rank-badge {{ transform: scale(1.1) rotate(-2deg); }}
        .rank-badge.gold {{
            background: linear-gradient(135deg, #FFE39B, {AMBER});
            color: #5B3A08;
            box-shadow: 0 4px 10px -3px rgba(240, 166, 41, 0.55);
            animation: pulseGlow 2.4s ease-in-out infinite;
            font-size: 1.05rem;
        }}
        .rank-badge.silver {{
            background: linear-gradient(135deg, #F1F3F6, #C7CDD6);
            color: #3B4250;
            box-shadow: 0 4px 10px -3px rgba(120, 130, 145, 0.4);
            font-size: 1.05rem;
        }}
        .rank-badge.bronze {{
            background: linear-gradient(135deg, #E9C29A, #B5773F);
            color: #43270C;
            box-shadow: 0 4px 10px -3px rgba(181, 119, 63, 0.45);
            font-size: 1.05rem;
        }}
        .rank-info {{ flex: 1; min-width: 0; }}
        .rank-name {{
            font-weight: 700;
            color: {TEXT};
            font-size: 0.92rem;
        }}
        .rank-bar-track {{
            background: #EEF1F5;
            border-radius: 6px;
            height: 7px;
            margin-top: 6px;
            overflow: hidden;
        }}
        .rank-bar-fill {{
            background: {BLUE};
            height: 100%;
            border-radius: 6px;
            animation: fillBar 0.9s ease-out;
            transition: width 0.6s ease;
        }}
        .rank-bar-fill.top {{ background: linear-gradient(90deg, {AMBER}, #FFD37A); }}
        .rank-bar-fill.meta-ok {{ background: linear-gradient(90deg, {GREEN}, #55C793); }}
        .rank-count {{
            text-align: right;
            min-width: 64px;
        }}
        .rank-count .n {{
            font-weight: 800;
            color: {TEXT};
            font-size: 1rem;
        }}
        .rank-count .p {{
            color: {MUTED};
            font-size: 0.72rem;
        }}

        /* ---------- Badges / chips ---------- */
        .chip {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 20px;
            font-size: 0.72rem;
            font-weight: 700;
        }}
        .chip-blue {{ background: #E7F0FA; color: {BLUE}; }}
        .chip-green {{ background: #E5F5EE; color: {GREEN}; }}
        .chip-amber {{ background: #FCF1DF; color: {AMBER_TEXT}; }}
        .chip-muted {{ background: #EEF1F5; color: {MUTED}; }}

        /* ---------- Tela de login (institucional) ---------- */
        .login-card {{
            position: relative;
            overflow: hidden;
            background: linear-gradient(135deg, {NAVY} 0%, {NAVY_SOFT} 60%, {BLUE} 100%);
            border-radius: 24px;
            padding: 42px 36px 34px 36px;
            text-align: center;
            color: white;
            box-shadow: 0 28px 55px -20px rgba(7, 26, 45, 0.55), inset 0 1px 0 rgba(255,255,255,0.08);
            animation: fadeInUp 0.5s ease-out;
        }}
        .login-card::before {{
            content: "";
            position: absolute;
            inset: 0;
            background: radial-gradient(circle at 20% -10%, rgba(255,255,255,0.18), transparent 55%);
            pointer-events: none;
        }}
        .login-card::after {{
            content: "";
            position: absolute;
            bottom: -50%;
            left: -10%;
            width: 260px;
            height: 260px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(240,166,41,0.25), transparent 70%);
            pointer-events: none;
        }}
        .login-shield {{
            position: relative;
            width: 66px;
            height: 66px;
            border-radius: 50%;
            background: rgba(255,255,255,0.12);
            border: 1px solid rgba(255,255,255,0.25);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.9rem;
            margin: 0 auto 14px auto;
            z-index: 1;
        }}
        .login-eyebrow {{
            position: relative;
            color: {AMBER};
            font-weight: 800;
            font-size: 0.78rem;
            letter-spacing: 1.4px;
            z-index: 1;
        }}
        .login-title {{
            position: relative;
            margin: 6px 0 2px 0;
            font-size: 1.7rem;
            font-weight: 800;
            z-index: 1;
        }}
        .login-sub {{
            position: relative;
            color: {AMBER};
            font-weight: 700;
            font-size: 0.82rem;
            margin: 0;
            z-index: 1;
        }}
        .login-desc {{
            position: relative;
            color: #C7D3E0;
            font-size: 0.88rem;
            margin-top: 14px;
            z-index: 1;
        }}

        /* ---------- Cartão de pessoa (bairro / veículo) ---------- */
        .person-card {{
            border: 1px solid {BORDER};
            border-radius: 12px;
            padding: 12px 14px;
            margin-bottom: 8px;
            background: {CARD};
            transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
            animation: fadeInUp 0.35s ease-out;
        }}
        .person-card:hover {{
            transform: translateX(2px);
            border-color: {BLUE};
            box-shadow: 0 6px 14px -8px rgba(15, 41, 66, 0.2);
        }}
        .person-top {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 10px;
        }}
        .person-name {{
            font-weight: 700;
            color: {TEXT};
            font-size: 0.94rem;
        }}
        .person-meta {{
            color: {MUTED};
            font-size: 0.8rem;
            margin-top: 3px;
        }}
        .wa-link {{
            text-decoration: none;
            background: {GREEN};
            color: white !important;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 5px 11px;
            border-radius: 8px;
            white-space: nowrap;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
            display: inline-block;
        }}
        .wa-link:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 10px -4px rgba(46, 158, 109, 0.5);
        }}

        /* Botões nativos do Streamlit */
        div[data-testid="stButton"] button {{
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }}
        div[data-testid="stButton"] button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 6px 14px -6px rgba(29, 95, 166, 0.4);
        }}

        /* Menu de navegação horizontal */
        .nav-link {{ transition: background 0.2s ease, color 0.2s ease; }}

        /* Inputs */
        .stSelectbox, .stTextInput {{ font-weight: 600; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# =====================================================================
# 3. CARREGAMENTO E TRATAMENTO DOS DADOS (lógica original preservada)
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
    if col_veiculo:
        renomear[col_veiculo] = "VEICULO_INFO_PADRAO"
    if col_adesivo:
        renomear[col_adesivo] = "ADESIVO_PADRAO"
    if col_trabalho_dia:
        renomear[col_trabalho_dia] = "TRABALHO_DIA_PADRAO"

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
    """Bloqueia o painel até o usuário digitar a senha correta."""
    senha_correta = st.secrets.get("senha_acesso", SENHA_PADRAO)

    if st.session_state.get("autenticado"):
        return

    st.markdown(
        f"""
        <div class="login-card" style="max-width:440px; margin:70px auto 0 auto;">
            <div class="login-shield">🛡️</div>
            <div class="login-eyebrow">ACESSO RESTRITO</div>
            <h1 class="login-title">Campanha 2026</h1>
            <div class="login-sub">PAINEL DE CAMPO · CENTRO DE COMANDO</div>
            <p class="login-desc">Digite a senha da equipe para entrar no painel.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_a, col_b, col_c = st.columns([1, 1.4, 1])
    with col_b:
        senha_digitada = st.text_input("Senha", type="password", label_visibility="collapsed", placeholder="Digite a senha")
        if st.button("Entrar", use_container_width=True):
            if senha_digitada == senha_correta:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
    st.stop()


def whatsapp_link(contato: str) -> str:
    """Gera um botão de WhatsApp a partir de um telefone, se válido."""
    if not contato or contato in ("NAN", "NONE", ""):
        return ""
    digitos = re.sub(r"\D", "", contato)
    if len(digitos) < 10:
        return contato
    if not digitos.startswith("55"):
        digitos = "55" + digitos
    return f'<a class="wa-link" href="https://wa.me/{digitos}" target="_blank">💬 {contato}</a>'


df = carregar_dados()

# ---------- Filtro de veículos válidos ----------
if "VEICULO_INFO_PADRAO" in df.columns:
    valores_invalidos = [
        "NONE", "NAO", "NÃO", "NAN", "", "NEHUM", "NENHUM", "NAO POSSUI", "NÂO",
    ]
    df_veiculos_filtro = df[
        ~df["VEICULO_INFO_PADRAO"].isin(valores_invalidos)
        & df["VEICULO_INFO_PADRAO"].notna()
    ].copy()
    df_veiculos_filtro = df_veiculos_filtro[
        df_veiculos_filtro["VEICULO_INFO_PADRAO"].str.strip() != ""
    ]
    veiculos_mapeados = len(df_veiculos_filtro)
else:
    df_veiculos_filtro = pd.DataFrame()
    veiculos_mapeados = 0

# ---------- Filtro de Apoio Extra: Adesivo e Trabalho no Dia ----------
VALORES_SIM = ["SIM", "S", "YES", "X", "TRUE", "1"]

if "ADESIVO_PADRAO" in df.columns:
    df_adesivo_filtro = df[df["ADESIVO_PADRAO"].isin(VALORES_SIM)].copy()
else:
    df_adesivo_filtro = pd.DataFrame()

if "TRABALHO_DIA_PADRAO" in df.columns:
    df_trabalho_filtro = df[df["TRABALHO_DIA_PADRAO"].isin(VALORES_SIM)].copy()
else:
    df_trabalho_filtro = pd.DataFrame()

total_cadastros = len(df)
lideres_ativos = (
    df["LIDER_PADRAO"].replace("NAN", np.nan).dropna().nunique()
    if "LIDER_PADRAO" in df.columns else 0
)
bairros_cobertos = (
    df["BAIRRO_PADRAO"].replace("NAN", np.nan).dropna().nunique()
    if "BAIRRO_PADRAO" in df.columns else 0
)

# =====================================================================
# 4. INTERFACE
# =====================================================================
inject_css()
verificar_senha()

agora = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y às %H:%M")
pct_meta = min(total_cadastros / META_CAMPANHA * 100, 100) if META_CAMPANHA else 0
meta_atingida = total_cadastros >= META_CAMPANHA
cor_meta = GREEN if meta_atingida else AMBER
texto_meta = (
    f"Meta batida! 🎉 {total_cadastros} de {META_CAMPANHA} apoiadores"
    if meta_atingida
    else f"{total_cadastros} de {META_CAMPANHA} apoiadores · faltam {META_CAMPANHA - total_cadastros}"
)

st.markdown(
    f"""
    <div class="hero">
        <div class="eyebrow">PAINEL DE CAMPO</div>
        <h1>Campanha 2026</h1>
        <p>Dados sincronizados automaticamente com a planilha de campo · atualizado em {agora}</p>
        <div style="margin-top:18px;">
            <div style="display:flex; justify-content:space-between; font-size:0.82rem; color:#C7D3E0; margin-bottom:6px;">
                <span>Meta geral da campanha</span>
                <span style="font-weight:700; color:white;">{pct_meta:.0f}%</span>
            </div>
            <div style="background:rgba(255,255,255,0.18); border-radius:8px; height:10px; overflow:hidden;">
                <div style="width:{pct_meta:.0f}%; background:{cor_meta}; height:100%; border-radius:8px; animation: fillBar 1.1s ease-out; transition: width 0.6s ease;"></div>
            </div>
            <div style="font-size:0.8rem; color:#C7D3E0; margin-top:6px;">{texto_meta}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-label">👥 Cadastros válidos</div>
            <div class="kpi-value">{total_cadastros}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">⭐ Líderes ativos</div>
            <div class="kpi-value">{lideres_ativos}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">📍 Bairros cobertos</div>
            <div class="kpi-value">{bairros_cobertos}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">🚗 Veículos no dia E</div>
            <div class="kpi-value">{veiculos_mapeados}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

selected = option_menu(
    menu_title=None,
    options=["Lideranças", "Bairros", "Perfil", "Veículos", "Apoio Extra"],
    icons=["people-fill", "geo-alt-fill", "bullseye", "car-front-fill", "star-fill"],
    orientation="horizontal",
    styles={
        "container": {
            "padding": "6px",
            "background-color": CARD,
            "border": f"1px solid {BORDER}",
            "border-radius": "14px",
            "margin-bottom": "20px",
            "box-shadow": "0 12px 26px -20px rgba(7, 26, 45, 0.25)",
        },
        "icon": {"color": MUTED, "font-size": "14px"},
        "nav-link": {
            "font-family": "Manrope, sans-serif",
            "font-weight": "700",
            "font-size": "0.85rem",
            "color": MUTED,
            "text-align": "center",
            "border-radius": "10px",
            "padding": "11px 10px",
            "margin": "0 3px",
        },
        "nav-link-selected": {
            "background-color": NAVY,
            "color": "white",
            "box-shadow": "0 8px 16px -6px rgba(7, 26, 45, 0.45)",
        },
    },
)

# ==========================================
# ABA 1: LIDERANÇAS
# ==========================================
if selected == "Lideranças":
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Ranking de captadores</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Quem está trazendo mais apoiadores para a base</div>', unsafe_allow_html=True)

    if "LIDER_PADRAO" in df.columns and not df.empty:
        df_clean_lider = df[~df["LIDER_PADRAO"].isin(["NAN", "NONE", "", "NÃO INFORMADO"])]
        df_lideres = (
            df_clean_lider["LIDER_PADRAO"].value_counts().reset_index()
            .rename(columns={"LIDER_PADRAO": "Líder", "count": "Total"})
            .sort_values(by="Total", ascending=False)
            .reset_index(drop=True)
        )
        lideres_com_meta = int((df_lideres["Total"] >= META_POR_LIDER).sum())
        st.markdown(
            f'<div class="section-subtitle" style="margin-bottom:14px;">'
            f'<span class="chip chip-green">✅ {lideres_com_meta} de {len(df_lideres)} líderes bateram a meta</span> '
            f'<span class="chip chip-muted">Meta individual: {META_POR_LIDER} apoiadores</span>'
            f"</div>",
            unsafe_allow_html=True,
        )

        MEDALHAS = {1: ("gold", "🥇"), 2: ("silver", "🥈"), 3: ("bronze", "🥉")}
        rows_html = ""
        for i, row in df_lideres.iterrows():
            rank = i + 1
            badge_class, badge_conteudo = MEDALHAS.get(rank, ("", str(rank)))
            atingiu = row["Total"] >= META_POR_LIDER
            largura = min(row["Total"] / META_POR_LIDER * 100, 100) if META_POR_LIDER else 0
            cor_barra = "meta-ok" if atingiu else ("top" if rank == 1 else "")
            legenda = "🏆 meta batida" if atingiu else f"faltam {META_POR_LIDER - row['Total']}"
            rows_html += f"""
            <div class="rank-row" style="animation-delay:{min(i * 0.05, 0.4):.2f}s">
                <div class="rank-badge {badge_class}">{badge_conteudo}</div>
                <div class="rank-info">
                    <div class="rank-name">{row['Líder'].title()}</div>
                    <div class="rank-bar-track"><div class="rank-bar-fill {cor_barra}" style="width:{largura:.0f}%"></div></div>
                </div>
                <div class="rank-count"><div class="n">{row['Total']}/{META_POR_LIDER}</div><div class="p">{legenda}</div></div>
            </div>
            """
        st.markdown(rows_html, unsafe_allow_html=True)
    else:
        st.info("Nenhum dado de liderança encontrado na planilha.")
    st.markdown('</div>', unsafe_allow_html=True)

    if "LIDER_PADRAO" in df.columns and not df_lideres.empty:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Volume por líder</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Comparativo visual entre captadores</div>', unsafe_allow_html=True)

        fig_lider = px.bar(
            df_lideres, x="Total", y="Líder", orientation="h", text="Total",
        )
        cores_barras = []
        for i in range(len(df_lideres)):
            if i == 0:
                cores_barras.append(AMBER)
            elif i == 1:
                cores_barras.append(BLUE)
            elif i == 2:
                cores_barras.append(GREEN)
            else:
                cores_barras.append(BLUE)
        fig_lider.update_traces(
            marker_color=cores_barras,
            textposition="outside",
            marker_line_width=0,
            textfont=dict(family=PLOTLY_FONT, color=TEXT, size=12),
        )
        fig_lider.update_layout(
            xaxis_title="", yaxis_title="",
            yaxis={"categoryorder": "total ascending"},
            bargap=0.28,
        )
        estilizar_grafico(
            fig_lider,
            height=max(280, 42 * len(df_lideres)),
            margin=dict(l=0, r=20, t=10, b=10),
        )
        fig_lider.update_xaxes(showgrid=True, gridcolor=BORDER)
        st.plotly_chart(fig_lider, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# ABA 2: BAIRROS
# ==========================================
if selected == "Bairros":
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Raio-X de bairros</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Apoiadores agrupados por região</div>', unsafe_allow_html=True)

    if "BAIRRO_PADRAO" in df.columns:
        bairros_validos = sorted(
            [b for b in df["BAIRRO_PADRAO"].dropna().unique() if b not in ["NAN", "NONE", ""]]
        )
        col_f1, col_f2 = st.columns([2, 2])
        with col_f1:
            bairro_sel = st.selectbox("Filtrar por bairro", ["Todos os bairros"] + bairros_validos)
        with col_f2:
            busca_nome = st.text_input("Buscar por nome", placeholder="Digite um nome…")

        df_bairros_filtro = df.copy()
        if bairro_sel != "Todos os bairros":
            df_bairros_filtro = df_bairros_filtro[df_bairros_filtro["BAIRRO_PADRAO"] == bairro_sel]
        if busca_nome and "NOME_PADRAO" in df_bairros_filtro.columns:
            df_bairros_filtro = df_bairros_filtro[
                df_bairros_filtro["NOME_PADRAO"].str.contains(busca_nome.upper(), na=False)
            ]

        contagem_bairros = (
            df_bairros_filtro["BAIRRO_PADRAO"].value_counts().drop(labels=["NAN", ""], errors="ignore")
        )
        st.markdown("<br>", unsafe_allow_html=True)

        for b in contagem_bairros.index.tolist():
            sub_df = df_bairros_filtro[df_bairros_filtro["BAIRRO_PADRAO"] == b]
            with st.expander(f"🏠  {b.title()} · {len(sub_df)} apoiador(es)"):
                for _, r in sub_df.iterrows():
                    nome = r.get("NOME_PADRAO", "—").title() if "NOME_PADRAO" in r else "—"
                    lider = r.get("LIDER_PADRAO", "") if "LIDER_PADRAO" in r else ""
                    contato = r.get("CONTATO_PADRAO", "") if "CONTATO_PADRAO" in r else ""
                    wa = whatsapp_link(contato)
                    lider_chip = f'<span class="chip chip-blue">Líder: {lider.title()}</span>' if lider and lider not in ("NAN", "NONE", "") else ""
                    st.markdown(
                        f"""
                        <div class="person-card">
                            <div class="person-top">
                                <div>
                                    <div class="person-name">{nome}</div>
                                    <div class="person-meta">{lider_chip}</div>
                                </div>
                                {wa}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# ABA 3: PERFIL DEMOGRÁFICO
# ==========================================
if selected == "Perfil":
    if "SEXO_PADRAO" in df.columns and "Idade" in df.columns:
        df_sexo_clean = df[~df["SEXO_PADRAO"].isin(["NAN", "NONE", ""])]
        resumo_sexo = (
            df_sexo_clean.groupby("SEXO_PADRAO")
            .agg(Quantidade=("SEXO_PADRAO", "count"), Idade_Media=("Idade", lambda x: round(x.mean(), 1)))
            .reset_index()
            .sort_values(by="Quantidade", ascending=False)
        )

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Perfil do eleitorado</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Distribuição por gênero e idade média</div>', unsafe_allow_html=True)

        total_sexo = resumo_sexo["Quantidade"].sum()
        cols = st.columns(len(resumo_sexo)) if len(resumo_sexo) > 0 else []
        cores_genero = {0: BLUE, 1: GREEN}
        for i, (_, r) in enumerate(resumo_sexo.iterrows()):
            pct = r["Quantidade"] / total_sexo * 100 if total_sexo else 0
            with cols[i]:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-label">{r['SEXO_PADRAO'].title()}</div>
                        <div class="kpi-value">{r['Quantidade']}</div>
                        <div class="section-subtitle" style="margin-bottom:0;">{pct:.1f}% da base · média {r['Idade_Media']} anos</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # Barra de proporção única (visual de gênero)
        segments = ""
        for i, (_, r) in enumerate(resumo_sexo.iterrows()):
            largura = r["Quantidade"] / total_sexo * 100 if total_sexo else 0
            cor = cores_genero.get(i, MUTED)
            segments += f'<div style="width:{largura:.1f}%; background:{cor};"></div>'
        st.markdown(
            f"""
            <div style="display:flex; height:14px; border-radius:8px; overflow:hidden; margin-top:16px;">
                {segments}
            </div>
            """,
            unsafe_allow_html=True,
        )

        media_geral = df["Idade"].mean()
        if not np.isnan(media_geral):
            st.markdown(
                f'<div class="section-subtitle" style="margin-top:10px;">Idade média geral da base: <b style="color:{TEXT}">{media_geral:.1f} anos</b></div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

    if "Faixa_Etaria" in df.columns:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Distribuição por faixa etária</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Onde está concentrado o eleitorado cadastrado</div>', unsafe_allow_html=True)

        df_faixa = df["Faixa_Etaria"].value_counts().reset_index()
        df_faixa.columns = ["Faixa Etária", "Quantidade"]
        ordem = ["18-24 anos", "25-39 anos", "40-59 anos", "60+ anos", "Não informado"]
        df_faixa["ordem"] = df_faixa["Faixa Etária"].apply(lambda x: ordem.index(x) if x in ordem else 99)
        df_faixa = df_faixa.sort_values("ordem")

        fig_faixa = px.bar(df_faixa, x="Faixa Etária", y="Quantidade", text="Quantidade")
        cores_faixa = [PLOTLY_PALETTE[i % len(PLOTLY_PALETTE)] for i in range(len(df_faixa))]
        fig_faixa.update_traces(
            marker_color=cores_faixa,
            textposition="outside",
            marker_line_width=0,
            textfont=dict(family=PLOTLY_FONT, color=TEXT, size=12),
        )
        fig_faixa.update_layout(xaxis_title="", yaxis_title="", bargap=0.35)
        estilizar_grafico(fig_faixa, height=320, margin=dict(l=0, r=0, t=10, b=10))
        st.plotly_chart(fig_faixa, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# ABA 4: VEÍCULOS
# ==========================================
if selected == "Veículos":
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Apoiadores com veículo</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Base de logística para o dia da eleição</div>', unsafe_allow_html=True)

    if not df_veiculos_filtro.empty:
        bairros_com_veic = (
            df_veiculos_filtro["BAIRRO_PADRAO"].replace("NAN", np.nan).nunique()
            if "BAIRRO_PADRAO" in df_veiculos_filtro else 0
        )
        c1, c2 = st.columns(2)
        c1.markdown(f'<div class="kpi-card"><div class="kpi-label">🚗 Veículos registrados</div><div class="kpi-value">{len(df_veiculos_filtro)}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="kpi-card"><div class="kpi-label">📍 Bairros cobertos</div><div class="kpi-value">{bairros_com_veic}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        bairros_v_validos = sorted(
            [b for b in df_veiculos_filtro["BAIRRO_PADRAO"].dropna().unique() if b not in ["NAN", "NONE", ""]]
        )
        bairro_v_sel = st.selectbox("Filtrar veículos por bairro", ["Todos os bairros"] + bairros_v_validos)

        df_veic_exibir = df_veiculos_filtro.copy()
        if bairro_v_sel != "Todos os bairros":
            df_veic_exibir = df_veic_exibir[df_veic_exibir["BAIRRO_PADRAO"] == bairro_v_sel]

        st.markdown("<br>", unsafe_allow_html=True)
        for _, r in df_veic_exibir.iterrows():
            nome = r.get("NOME_PADRAO", "—").title() if "NOME_PADRAO" in r else "—"
            bairro = r.get("BAIRRO_PADRAO", "") if "BAIRRO_PADRAO" in r else ""
            veiculo = r.get("VEICULO_INFO_PADRAO", "") if "VEICULO_INFO_PADRAO" in r else ""
            lider = r.get("LIDER_PADRAO", "") if "LIDER_PADRAO" in r else ""
            contato = r.get("CONTATO_PADRAO", "") if "CONTATO_PADRAO" in r else ""
            wa = whatsapp_link(contato)
            st.markdown(
                f"""
                <div class="person-card">
                    <div class="person-top">
                        <div>
                            <div class="person-name">{nome}</div>
                            <div class="person-meta">🚙 {veiculo.title()}</div>
                            <div class="person-meta">
                                <span class="chip chip-muted">{bairro.title()}</span>
                                <span class="chip chip-blue">Líder: {lider.title()}</span>
                            </div>
                        </div>
                        {wa}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("Nenhum apoiador com veículo registrado ou identificado na planilha.")
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# ABA 5: APOIO EXTRA (ADESIVO / TRABALHO NO DIA)
# ==========================================
if selected == "Apoio Extra":
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Apoio extra da campanha</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Adesivo veicular e trabalho no dia da eleição</div>', unsafe_allow_html=True)

    subgrupo = st.radio(
        "Selecione o grupo",
        ["🎨 Adesivo Veicular", "🗳️ Trabalho no Dia da Eleição"],
        horizontal=True,
        label_visibility="collapsed",
    )
    st.markdown("<br>", unsafe_allow_html=True)

    if subgrupo == "🎨 Adesivo Veicular":
        if "ADESIVO_PADRAO" not in df.columns:
            st.warning(
                "Ainda não encontrei uma coluna de adesivo veicular na planilha. "
                "Crie uma coluna chamada, por exemplo, **ADESIVO_VEICULAR** com "
                "respostas **Sim/Não** e o painel detecta automaticamente."
            )
        else:
            st.markdown(
                f'<div class="kpi-card" style="max-width:260px;"><div class="kpi-label">🎨 Com adesivo instalado</div>'
                f'<div class="kpi-value">{len(df_adesivo_filtro)}</div></div>',
                unsafe_allow_html=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)
            if df_adesivo_filtro.empty:
                st.info("Nenhum apoiador com adesivo veicular registrado ainda.")
            else:
                for _, r in df_adesivo_filtro.iterrows():
                    nome = r.get("NOME_PADRAO", "—").title() if "NOME_PADRAO" in r else "—"
                    bairro = r.get("BAIRRO_PADRAO", "") if "BAIRRO_PADRAO" in r else ""
                    lider = r.get("LIDER_PADRAO", "") if "LIDER_PADRAO" in r else ""
                    contato = r.get("CONTATO_PADRAO", "") if "CONTATO_PADRAO" in r else ""
                    veiculo = r.get("VEICULO_INFO_PADRAO", "") if "VEICULO_INFO_PADRAO" in r else ""
                    wa = whatsapp_link(contato)
                    linha_veiculo = f'<div class="person-meta">🚙 {veiculo.title()}</div>' if veiculo and veiculo not in ("NAN", "NONE", "") else ""
                    st.markdown(
                        f"""
                        <div class="person-card">
                            <div class="person-top">
                                <div>
                                    <div class="person-name">{nome}</div>
                                    {linha_veiculo}
                                    <div class="person-meta">
                                        <span class="chip chip-muted">{bairro.title()}</span>
                                        <span class="chip chip-blue">Líder: {lider.title()}</span>
                                    </div>
                                </div>
                                {wa}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    else:  # Trabalho no Dia da Eleição
        if "TRABALHO_DIA_PADRAO" not in df.columns:
            st.warning(
                "Ainda não encontrei uma coluna de trabalho no dia da eleição na planilha. "
                "Crie uma coluna chamada, por exemplo, **TRABALHO_DIA_ELEICAO** com "
                "respostas **Sim/Não** e o painel detecta automaticamente."
            )
        else:
            st.markdown(
                f'<div class="kpi-card" style="max-width:260px;"><div class="kpi-label">🗳️ Confirmados para o dia E</div>'
                f'<div class="kpi-value">{len(df_trabalho_filtro)}</div></div>',
                unsafe_allow_html=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)
            if df_trabalho_filtro.empty:
                st.info("Nenhum apoiador confirmado para trabalhar no dia da eleição ainda.")
            else:
                for _, r in df_trabalho_filtro.iterrows():
                    nome = r.get("NOME_PADRAO", "—").title() if "NOME_PADRAO" in r else "—"
                    bairro = r.get("BAIRRO_PADRAO", "") if "BAIRRO_PADRAO" in r else ""
                    lider = r.get("LIDER_PADRAO", "") if "LIDER_PADRAO" in r else ""
                    contato = r.get("CONTATO_PADRAO", "") if "CONTATO_PADRAO" in r else ""
                    veiculo = r.get("VEICULO_INFO_PADRAO", "") if "VEICULO_INFO_PADRAO" in r else ""
                    wa = whatsapp_link(contato)
                    linha_veiculo = f'<div class="person-meta">🚙 {veiculo.title()}</div>' if veiculo and veiculo not in ("NAN", "NONE", "") else ""
                    st.markdown(
                        f"""
                        <div class="person-card">
                            <div class="person-top">
                                <div>
                                    <div class="person-name">{nome}</div>
                                    {linha_veiculo}
                                    <div class="person-meta">
                                        <span class="chip chip-muted">{bairro.title()}</span>
                                        <span class="chip chip-blue">Líder: {lider.title()}</span>
                                    </div>
                                </div>
                                {wa}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
    st.markdown('</div>', unsafe_allow_html=True)
