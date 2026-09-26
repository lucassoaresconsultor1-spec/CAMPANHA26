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
# 2. IDENTIDADE VISUAL OBRIGATÓRIA (Design Tokens)
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

# Metas de campanha
META_CAMPANHA = 165
META_POR_LIDER = 15

SENHA_PADRAO = "BEBETO123"


def inject_css():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Manrope', -apple-system, BlinkMacSystemFont, sans-serif;
            color: {TEXT};
            background-color: {BG};
        }}

        #MainMenu, footer, header {{ visibility: hidden; }}

        /* Background Gradientes Efeitos Ambientais/Glows */
        .stApp {{
            background: 
                radial-gradient(circle at 10% 5%, rgba(29, 95, 166, 0.08) 0%, transparent 45%),
                radial-gradient(circle at 90% 95%, rgba(240, 166, 41, 0.06) 0%, transparent 40%),
                {BG};
            background-attachment: fixed;
        }}

        .block-container {{
            padding-top: 1.5rem;
            padding-bottom: 3.5rem;
            max-width: 1240px;
        }}

        /* Animações e Transições Premium */
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(12px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        @keyframes fillBar {{
            from {{ width: 0%; }}
        }}
        @keyframes pulseGlow {{
            0%, 100% {{ box-shadow: 0 0 0 0 rgba(240, 166, 41, 0.4); }}
            50% {{ box-shadow: 0 0 0 8px rgba(240, 166, 41, 0); }}
        }}

        /* ---------- Header Hero ---------- */
        .hero {{
            background: linear-gradient(135deg, {NAVY} 0%, {NAVY_SOFT} 55%, {BLUE} 100%);
            border-radius: 20px;
            padding: 32px 36px;
            color: #FFFFFF;
            margin-bottom: 24px;
            animation: fadeInUp 0.5s ease-out;
            position: relative;
            overflow: hidden;
            box-shadow: 0 16px 32px -10px rgba(7, 26, 45, 0.28);
            border: 1px solid rgba(255, 255, 255, 0.12);
        }}
        .hero::before {{
            content: "";
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle at 70% 20%, rgba(255,255,255,0.08) 0%, transparent 50%);
            pointer-events: none;
        }}
        .hero .eyebrow {{
            color: {AMBER};
            font-weight: 800;
            font-size: 0.8rem;
            letter-spacing: 1.2px;
            text-transform: uppercase;
            margin-bottom: 6px;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        .hero h1 {{
            margin: 0;
            font-size: 2.2rem;
            font-weight: 800;
            line-height: 1.2;
            letter-spacing: -0.5px;
            color: #FFFFFF;
        }}
        .hero p {{
            margin-top: 8px;
            color: #D2E0EE;
            font-size: 0.95rem;
            font-weight: 500;
        }}

        /* ---------- KPI Grid ---------- */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 20px;
        }}
        @media (max-width: 850px) {{
            .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
        @media (max-width: 520px) {{
            .kpi-grid {{ grid-template-columns: 1fr; }}
            .hero h1 {{ font-size: 1.6rem; }}
            .hero {{ padding: 22px 20px; }}
        }}
        .kpi-card {{
            background: {CARD};
            border: 1px solid {BORDER};
            border-radius: 16px;
            padding: 20px;
            position: relative;
            overflow: hidden;
            animation: fadeInUp 0.4s ease-out backwards;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        }}
        .kpi-card::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, {NAVY} 0%, {BLUE} 100%);
        }}
        .kpi-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 24px -6px rgba(7, 26, 45, 0.12);
            border-color: {BLUE};
        }}
        .kpi-card .kpi-label {{
            color: {MUTED};
            font-size: 0.82rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .kpi-card .kpi-value {{
            color: {NAVY};
            font-size: 2.2rem;
            font-weight: 800;
            margin-top: 6px;
            line-height: 1;
            letter-spacing: -0.5px;
        }}

        /* ---------- Cartões de Seção (Glassmorphism) ---------- */
        .section-card {{
            background: rgba(255, 255, 255, 0.92);
            backdrop-filter: blur(12px);
            border: 1px solid {BORDER};
            border-radius: 18px;
            padding: 24px 28px;
            margin-bottom: 20px;
            box-shadow: 0 4px 16px rgba(7, 26, 45, 0.04);
            animation: fadeInUp 0.4s ease-out;
        }}
        .section-title {{
            font-size: 1.25rem;
            font-weight: 800;
            color: {NAVY};
            letter-spacing: -0.3px;
            margin-bottom: 2px;
        }}
        .section-subtitle {{
            color: {MUTED};
            font-size: 0.88rem;
            font-weight: 500;
            margin-bottom: 18px;
        }}

        /* ---------- Ranking Leaderboard ---------- */
        .rank-row {{
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 12px 14px;
            margin-bottom: 6px;
            border-radius: 12px;
            background: #FFFFFF;
            border: 1px solid {BORDER};
            transition: all 0.2s ease;
            animation: fadeInUp 0.4s ease-out backwards;
        }}
        .rank-row:hover {{
            background: #F8FAFC;
            transform: translateX(4px);
            border-color: {BLUE};
            box-shadow: 0 4px 12px rgba(7, 26, 45, 0.06);
        }}
        .rank-badge {{
            width: 34px;
            height: 34px;
            min-width: 34px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 0.95rem;
            background: #EEF2F6;
            color: {MUTED};
            transition: transform 0.2s ease;
        }}
        .rank-row:hover .rank-badge {{ transform: scale(1.08); }}
        .rank-badge.gold {{
            background: linear-gradient(135deg, #FFE082 0%, {AMBER} 100%);
            color: #5C3D00;
            font-size: 1.1rem;
            animation: pulseGlow 2.5s ease-in-out infinite;
        }}
        .rank-badge.silver {{
            background: linear-gradient(135deg, #E2E8F0 0%, #CBD5E1 100%);
            color: #334155;
            font-size: 1.1rem;
        }}
        .rank-badge.bronze {{
            background: linear-gradient(135deg, #FED7AA 0%, #F97316 100%);
            color: #7C2D12;
            font-size: 1.1rem;
        }}
        .rank-info {{ flex: 1; min-width: 0; }}
        .rank-name {{
            font-weight: 700;
            color: {TEXT};
            font-size: 0.96rem;
        }}
        .rank-bar-track {{
            background: #EDF2F7;
            border-radius: 8px;
            height: 8px;
            margin-top: 6px;
            overflow: hidden;
        }}
        .rank-bar-fill {{
            background: {BLUE};
            height: 100%;
            border-radius: 8px;
            animation: fillBar 0.9s ease-out;
            transition: width 0.6s ease;
        }}
        .rank-bar-fill.gold {{ background: linear-gradient(90deg, {AMBER} 0%, #FFC107 100%); }}
        .rank-bar-fill.meta-ok {{ background: linear-gradient(90deg, {GREEN} 0%, #34D399 100%); }}
        .rank-count {{
            text-align: right;
            min-width: 80px;
        }}
        .rank-count .n {{
            font-weight: 800;
            color: {NAVY};
            font-size: 1.05rem;
        }}
        .rank-count .p {{
            color: {MUTED};
            font-size: 0.75rem;
            font-weight: 600;
        }}

        /* ---------- Badges / Chips ---------- */
        .chip {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
        }}
        .chip-blue {{ background: #EBF3FA; color: {BLUE}; }}
        .chip-green {{ background: #E8F5E9; color: {GREEN}; }}
        .chip-amber {{ background: #FEF3D6; color: #B47818; }}
        .chip-muted {{ background: #EDF2F7; color: {MUTED}; }}

        /* ---------- Cartões de Pessoas ---------- */
        .person-card {{
            border: 1px solid {BORDER};
            border-radius: 14px;
            padding: 14px 18px;
            margin-bottom: 10px;
            background: {CARD};
            transition: all 0.2s ease;
            animation: fadeInUp 0.35s ease-out;
        }}
        .person-card:hover {{
            transform: translateX(4px);
            border-color: {BLUE};
            box-shadow: 0 6px 16px rgba(7, 26, 45, 0.08);
        }}
        .person-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
        }}
        .person-name {{
            font-weight: 700;
            color: {NAVY};
            font-size: 0.98rem;
        }}
        .person-meta {{
            color: {MUTED};
            font-size: 0.82rem;
            margin-top: 4px;
            display: flex;
            align-items: center;
            gap: 6px;
            flex-wrap: wrap;
        }}
        .wa-link {{
            text-decoration: none !important;
            background: linear-gradient(135deg, {GREEN} 0%, #25855A 100%);
            color: #FFFFFF !important;
            font-size: 0.78rem;
            font-weight: 700;
            padding: 7px 14px;
            border-radius: 10px;
            white-space: nowrap;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            box-shadow: 0 2px 6px rgba(46, 158, 109, 0.3);
        }}
        .wa-link:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(46, 158, 109, 0.4);
            color: #FFFFFF !important;
        }}

        /* ---------- Tela de Login Corporativa ---------- */
        .login-card {{
            background: {CARD};
            border: 1px solid {BORDER};
            border-radius: 20px;
            padding: 40px 32px;
            max-width: 420px;
            margin: 60px auto 0 auto;
            text-align: center;
            box-shadow: 0 20px 40px rgba(7, 26, 45, 0.12);
            animation: fadeInUp 0.5s ease-out;
        }}
        .login-icon {{
            width: 56px;
            height: 56px;
            background: linear-gradient(135deg, {NAVY} 0%, {BLUE} 100%);
            color: #FFFFFF;
            border-radius: 16px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 1.6rem;
            margin-bottom: 16px;
            box-shadow: 0 8px 16px rgba(29, 95, 166, 0.25);
        }}

        /* Customização de Botões e Inputs do Streamlit */
        div[data-testid="stButton"] button {{
            background: linear-gradient(135deg, {NAVY} 0%, {BLUE} 100%);
            color: white;
            border: none;
            font-weight: 700;
            border-radius: 10px;
            padding: 10px 20px;
            transition: all 0.2s ease;
            box-shadow: 0 4px 12px rgba(7, 26, 45, 0.15);
        }}
        div[data-testid="stButton"] button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 18px rgba(29, 95, 166, 0.35);
            color: white;
        }}
        .stSelectbox, .stTextInput {{ font-weight: 600; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# =====================================================================
# 3. CARREGAMENTO E TRATAMENTO DOS DADOS (Preservado)
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
        <div class="login-card">
            <div class="login-icon">🛡️</div>
            <div class="eyebrow" style="color:{AMBER}; font-weight:800; font-size:0.75rem; letter-spacing:1px; text-transform:uppercase;">ACESSO RESTRITO</div>
            <h1 style="font-size:1.6rem; font-weight:800; color:{NAVY}; margin:6px 0;">Campanha 2026</h1>
            <p style="color:{MUTED}; font-size:0.88rem; margin-bottom:20px;">Digite a credencial da equipe para entrar no centro de comando de campo.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_a, col_b, col_c = st.columns([1, 1.2, 1])
    with col_b:
        senha_digitada = st.text_input("Senha", type="password", label_visibility="collapsed", placeholder="Sua senha de acesso")
        if st.button("Autenticar", use_container_width=True):
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
        <div class="eyebrow">⚡ CENTRO DE COMANDO ELEITORAL</div>
        <h1>Campanha 2026 · Painel Geral</h1>
        <p>Dados sincronizados em tempo real com a planilha de campo · Atualizado em {agora}</p>
        <div style="margin-top:20px;">
            <div style="display:flex; justify-content:space-between; font-size:0.85rem; color:#E2E8F0; margin-bottom:8px; font-weight:600;">
                <span>Progresso da Meta Geral da Campanha</span>
                <span style="font-weight:800; color:{AMBER};">{pct_meta:.0f}%</span>
            </div>
            <div style="background:rgba(255,255,255,0.15); border-radius:10px; height:12px; overflow:hidden; backdrop-filter:blur(4px);">
                <div style="width:{pct_meta:.0f}%; background:linear-gradient(90deg, {cor_meta} 0%, #34D399 100%); height:100%; border-radius:10px; animation: fillBar 1.1s ease-out; transition: width 0.6s ease;"></div>
            </div>
            <div style="font-size:0.82rem; color:#CBD5E1; margin-top:8px; font-weight:500;">{texto_meta}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-label">👥 Cadastros Válidos</div>
            <div class="kpi-value">{total_cadastros}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">⭐ Líderes Ativos</div>
            <div class="kpi-value">{lideres_ativos}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">📍 Bairros Cobertos</div>
            <div class="kpi-value">{bairros_cobertos}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">🚗 Veículos Dia E</div>
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
        "container": {"padding": "6px", "background-color": CARD, "border": f"1px solid {BORDER}", "border-radius": "14px", "margin-bottom": "20px", "box-shadow": "0 2px 8px rgba(7, 26, 45, 0.04)"},
        "icon": {"color": MUTED, "font-size": "14px"},
        "nav-link": {"font-family": "Manrope, sans-serif", "font-weight": "700", "font-size": "0.88rem", "color": MUTED, "text-align": "center", "border-radius": "10px", "padding": "10px 12px"},
        "nav-link-selected": {"background-color": NAVY, "color": "#FFFFFF"},
    },
)

# ==========================================
# ABA 1: LIDERANÇAS
# ==========================================
if selected == "Lideranças":
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Ranking de Captadores</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Acompanhe quem está trazendo mais apoiadores para a base de campo</div>', unsafe_allow_html=True)

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
            f'<div class="section-subtitle" style="margin-bottom:16px;">'
            f'<span class="chip chip-green">✅ {lideres_com_meta} de {len(df_lideres)} líderes bateram a meta</span> '
            f'<span class="chip chip-muted">Meta individual: {META_POR_LIDER} apoiadores</span>'
            f"</div>",
            unsafe_allow_html=True,
        )

        rows_html = ""
        for i, row in df_lideres.iterrows():
            rank = i + 1
            if rank == 1:
                badge_class = "gold"
                badge_icon = "🥇"
            elif rank == 2:
                badge_class = "silver"
                badge_icon = "🥈"
            elif rank == 3:
                badge_class = "bronze"
                badge_icon = "🥉"
            else:
                badge_class = ""
                badge_icon = str(rank)

            atingiu = row["Total"] >= META_POR_LIDER
            largura = min(row["Total"] / META_POR_LIDER * 100, 100) if META_POR_LIDER else 0
            cor_barra = "gold" if rank == 1 else ("meta-ok" if atingiu else "")
            legenda = "🏆 meta batida" if atingiu else f"faltam {META_POR_LIDER - row['Total']}"
            rows_html += f"""
            <div class="rank-row" style="animation-delay:{min(i * 0.04, 0.4):.2f}s">
                <div class="rank-badge {badge_class}">{badge_icon}</div>
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
        st.markdown('<div class="section-title">Volume por Líder</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Comparativo visual entre captadores de campo</div>', unsafe_allow_html=True)

        fig_lider = px.bar(
            df_lideres, x="Total", y="Líder", orientation="h", text="Total",
        )
        fig_lider.update_traces(
            marker_color=[AMBER if i == 0 else BLUE for i in range(len(df_lideres))],
            textposition="outside",
            marker_line_width=0,
        )
        fig_lider.update_layout(
            font_family=PLOTLY_FONT, font_color=TEXT,
            xaxis_title="", yaxis_title="",
            yaxis={"categoryorder": "total ascending"},
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=20, t=10, b=10),
            height=max(280, 42 * len(df_lideres)),
        )
        fig_lider.update_xaxes(showgrid=True, gridcolor=BORDER)
        st.plotly_chart(fig_lider, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# ABA 2: BAIRROS
# ==========================================
if selected == "Bairros":
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Raio-X de Bairros</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Apoiadores agrupados por região geográfica</div>', unsafe_allow_html=True)

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
            with st.expander(f"📍  {b.title()} · {len(sub_df)} apoiador(es)"):
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
        st.markdown('<div class="section-title">Perfil do Eleitorado</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Distribuição por gênero e média de idade</div>', unsafe_allow_html=True)

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
                        <div class="section-subtitle" style="margin-bottom:0; margin-top:4px;">{pct:.1f}% da base · média {r['Idade_Media']} anos</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        segments = ""
        for i, (_, r) in enumerate(resumo_sexo.iterrows()):
            largura = r["Quantidade"] / total_sexo * 100 if total_sexo else 0
            cor = cores_genero.get(i, MUTED)
            segments += f'<div style="width:{largura:.1f}%; background:{cor};"></div>'
        st.markdown(
            f"""
            <div style="display:flex; height:12px; border-radius:8px; overflow:hidden; margin-top:16px;">
                {segments}
            </div>
            """,
            unsafe_allow_html=True,
        )

        media_geral = df["Idade"].mean()
        if not np.isnan(media_geral):
            st.markdown(
                f'<div class="section-subtitle" style="margin-top:12px;">Idade média geral da base: <b style="color:{NAVY}">{media_geral:.1f} anos</b></div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

    if "Faixa_Etaria" in df.columns:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Distribuição por Faixa Etária</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Concentração demográfica por faixas de idade</div>', unsafe_allow_html=True)

        df_faixa = df["Faixa_Etaria"].value_counts().reset_index()
        df_faixa.columns = ["Faixa Etária", "Quantidade"]
        ordem = ["18-24 anos", "25-39 anos", "40-59 anos", "60+ anos", "Não informado"]
        df_faixa["ordem"] = df_faixa["Faixa Etária"].apply(lambda x: ordem.index(x) if x in ordem else 99)
        df_faixa = df_faixa.sort_values("ordem")

        fig_faixa = px.bar(df_faixa, x="Faixa Etária", y="Quantidade", text="Quantidade")
        fig_faixa.update_traces(marker_color=BLUE, textposition="outside", marker_line_width=0)
        fig_faixa.update_layout(
            font_family=PLOTLY_FONT, font_color=TEXT,
            xaxis_title="", yaxis_title="",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=10), height=320,
        )
        fig_faixa.update_yaxes(showgrid=True, gridcolor=BORDER)
        st.plotly_chart(fig_faixa, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# ABA 4: VEÍCULOS
# ==========================================
if selected == "Veículos":
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Apoiadores com Veículo</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Mapeamento logístico para o dia da eleição</div>', unsafe_allow_html=True)

    if not df_veiculos_filtro.empty:
        bairros_com_veic = (
            df_veiculos_filtro["BAIRRO_PADRAO"].replace("NAN", np.nan).nunique()
            if "BAIRRO_PADRAO" in df_veiculos_filtro else 0
        )
        c1, c2 = st.columns(2)
        c1.markdown(f'<div class="kpi-card"><div class="kpi-label">🚗 Veículos Registrados</div><div class="kpi-value">{len(df_veiculos_filtro)}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="kpi-card"><div class="kpi-label">📍 Bairros Cobertos</div><div class="kpi-value">{bairros_com_veic}</div></div>', unsafe_allow_html=True)

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
                            <div class="person-meta" style="margin-top:6px;">
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
    st.markdown('<div class="section-title">Apoio Extra da Campanha</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Engajamento de adesivação e atuação direta no dia da eleição</div>', unsafe_allow_html=True)

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
                f'<div class="kpi-card" style="max-width:280px;"><div class="kpi-label">🎨 Com Adesivo Instalado</div>'
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
                                    <div class="person-meta" style="margin-top:6px;">
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
                f'<div class="kpi-card" style="max-width:280px;"><div class="kpi-label">🗳️ Confirmados Dia E</div>'
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
                                    <div class="person-meta" style="margin-top:6px;">
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