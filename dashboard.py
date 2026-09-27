import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_option_menu import option_menu

# =====================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# =====================================================================
st.set_page_config(
    page_title="Campanha 2026 · Centro de Comando",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =====================================================================
# 2. IDENTIDADE VISUAL & CSS DESIGN SYSTEM (MOBILE OPTIMIZED)
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

SENHA_PADRAO = "BEBETO123"

DATA_ELEICAO = date(2026, 10, 4)


def inject_css():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Plus Jakarta Sans', 'Manrope', -apple-system, sans-serif;
            color: {TEXT};
            background-color: {BG};
            -webkit-font-smoothing: antialiased;
        }}

        #MainMenu, footer, header {{ visibility: hidden; height: 0; }}

        .stApp {{
            background:
                radial-gradient(800px circle at 15% -10%, rgba(29, 95, 166, 0.12) 0%, transparent 60%),
                radial-gradient(700px circle at 85% 110%, rgba(240, 166, 41, 0.08) 0%, transparent 50%),
                radial-gradient(600px circle at 50% 50%, rgba(2, 132, 199, 0.03) 0%, transparent 70%),
                {BG};
            background-attachment: fixed;
        }}

        .block-container {{
            padding-top: 1rem;
            padding-bottom: 3rem;
            padding-left: 1rem;
            padding-right: 1rem;
            max-width: 1280px;
        }}

        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(16px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        @keyframes pulseDot {{
            0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 158, 109, 0.7); }}
            70% {{ transform: scale(1); box-shadow: 0 0 0 8px rgba(46, 158, 109, 0); }}
            100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 158, 109, 0.7); }}
        }}

        /* HERO BANNER RESPONSIVO */
        .hero-banner {{
            background: linear-gradient(135deg, {NAVY} 0%, {NAVY_SOFT} 50%, {BLUE} 100%);
            border-radius: 20px;
            padding: 24px 20px;
            color: #FFFFFF;
            margin-bottom: 20px;
            position: relative;
            overflow: hidden;
            box-shadow: 0 16px 32px -10px rgba(7, 26, 45, 0.35), inset 0 1px 0 0 rgba(255, 255, 255, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.12);
            animation: fadeInUp 0.45s ease-out;
        }}
        @media (min-width: 768px) {{
            .hero-banner {{ border-radius: 24px; padding: 36px 40px; margin-bottom: 24px; }}
        }}

        .hero-tag-container {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .hero-tag {{
            background: rgba(240, 166, 41, 0.15);
            border: 1px solid rgba(240, 166, 41, 0.4);
            color: {AMBER};
            font-weight: 800;
            font-size: 0.68rem;
            letter-spacing: 1.2px;
            text-transform: uppercase;
            padding: 4px 10px;
            border-radius: 30px;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            backdrop-filter: blur(8px);
        }}
        @media (min-width: 768px) {{
            .hero-tag {{ font-size: 0.72rem; letter-spacing: 1.5px; padding: 5px 14px; gap: 8px; }}
        }}

        .status-dot {{
            width: 8px;
            height: 8px;
            background-color: {GREEN};
            border-radius: 50%;
            display: inline-block;
            animation: pulseDot 2s infinite;
        }}
        .hero-banner h1 {{
            margin: 0;
            font-size: 1.6rem;
            font-weight: 800;
            line-height: 1.2;
            letter-spacing: -0.5px;
            color: #FFFFFF;
        }}
        @media (min-width: 768px) {{
            .hero-banner h1 {{ font-size: 2.3rem; letter-spacing: -0.8px; }}
        }}

        .hero-banner p {{
            margin-top: 6px;
            color: #D2E0EE;
            font-size: 0.88rem;
            font-weight: 500;
        }}
        @media (min-width: 768px) {{
            .hero-banner p {{ margin-top: 8px; font-size: 0.96rem; }}
        }}

        .countdown-box {{
            margin-top: 14px;
            background: rgba(240, 166, 41, 0.15);
            border: 1px solid rgba(240, 166, 41, 0.4);
            border-radius: 14px;
            padding: 12px 16px;
            display: flex;
            align-items: center;
            gap: 12px;
            backdrop-filter: blur(10px);
        }}
        .countdown-icon {{ font-size: 1.5rem; line-height: 1; }}
        .countdown-title {{
            font-size: 0.68rem;
            font-weight: 800;
            letter-spacing: 1px;
            text-transform: uppercase;
            color: #FCE7F3;
        }}
        .countdown-text {{
            font-size: 1.05rem;
            font-weight: 800;
            color: {AMBER};
            margin-top: 2px;
            line-height: 1.1;
        }}
        @media (min-width: 768px) {{
            .countdown-box {{ margin-top: 18px; padding: 14px 20px; gap: 16px; border-radius: 16px; }}
            .countdown-icon {{ font-size: 1.8rem; }}
            .countdown-title {{ font-size: 0.75rem; letter-spacing: 1.2px; }}
            .countdown-text {{ font-size: 1.25rem; }}
        }}

        /* GRID DE KPIS RESPONSIVO */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-bottom: 18px;
        }}
        @media (min-width: 900px) {{
            .kpi-grid {{ grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 22px; }}
        }}

        .kpi-card {{
            background: {CARD};
            border: 1px solid {BORDER};
            border-radius: 14px;
            padding: 14px 16px;
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 14px rgba(7, 26, 45, 0.03);
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
            animation: fadeInUp 0.4s ease-out backwards;
        }}
        @media (min-width: 768px) {{
            .kpi-card {{ border-radius: 18px; padding: 20px 22px; }}
        }}
        .kpi-card::before {{
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 4px;
            background: linear-gradient(90deg, {NAVY} 0%, {BLUE} 100%);
        }}
        .kpi-card .kpi-icon-wrap {{
            width: 32px;
            height: 32px;
            border-radius: 10px;
            background: #F0F5FA;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1rem;
            margin-bottom: 8px;
        }}
        @media (min-width: 768px) {{
            .kpi-card .kpi-icon-wrap {{ width: 40px; height: 40px; border-radius: 12px; font-size: 1.2rem; margin-bottom: 12px; }}
        }}
        .kpi-card .kpi-label {{
            color: {MUTED};
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        @media (min-width: 768px) {{
            .kpi-card .kpi-label {{ font-size: 0.8rem; letter-spacing: 0.6px; }}
        }}
        .kpi-card .kpi-value {{
            color: {NAVY};
            font-size: 1.7rem;
            font-weight: 800;
            margin-top: 2px;
            line-height: 1;
            letter-spacing: -0.5px;
        }}
        @media (min-width: 768px) {{
            .kpi-card .kpi-value {{ font-size: 2.3rem; margin-top: 4px; letter-spacing: -0.8px; }}
        }}

        /* SEÇÃO CARD */
        .section-card {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(16px);
            border: 1px solid {BORDER};
            border-radius: 16px;
            padding: 16px 18px;
            margin-bottom: 18px;
            box-shadow: 0 4px 20px rgba(7, 26, 45, 0.04);
            animation: fadeInUp 0.4s ease-out;
        }}
        @media (min-width: 768px) {{
            .section-card {{ border-radius: 20px; padding: 26px 30px; margin-bottom: 22px; }}
        }}

        .section-header-wrap {{
            border-bottom: 1px solid {BORDER};
            padding-bottom: 10px;
            margin-bottom: 16px;
        }}
        @media (min-width: 768px) {{
            .section-header-wrap {{ padding-bottom: 14px; margin-bottom: 20px; }}
        }}
        .section-title {{
            font-size: 1.1rem;
            font-weight: 800;
            color: {NAVY};
            letter-spacing: -0.3px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        @media (min-width: 768px) {{
            .section-title {{ font-size: 1.25rem; letter-spacing: -0.4px; gap: 10px; }}
        }}
        .section-subtitle {{
            color: {MUTED};
            font-size: 0.8rem;
            font-weight: 500;
            margin-top: 2px;
        }}
        @media (min-width: 768px) {{
            .section-subtitle {{ font-size: 0.88rem; }}
        }}

        /* VEÍCULOS CARD RESPONSIVO */
        .veiculo-card-interactive {{
            background: #FFFFFF;
            border: 1px solid {BORDER};
            border-radius: 14px;
            padding: 16px;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
            position: relative;
            box-shadow: 0 4px 12px rgba(7, 26, 45, 0.03);
            margin-bottom: 12px;
        }}
        @media (min-width: 768px) {{
            .veiculo-card-interactive {{ border-radius: 18px; padding: 22px; margin-bottom: 16px; }}
        }}
        .veiculo-title {{
            font-size: 1rem;
            font-weight: 800;
            color: {NAVY};
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        @media (min-width: 768px) {{
            .veiculo-title {{ font-size: 1.1rem; gap: 8px; }}
        }}
        .veiculo-owner {{
            font-size: 0.82rem;
            font-weight: 600;
            color: {MUTED};
            margin-top: 2px;
        }}
        @media (min-width: 768px) {{
            .veiculo-owner {{ font-size: 0.9rem; }}
        }}

        /* RANKING ROW RESPONSIVO */
        .rank-row {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 12px;
            margin-bottom: 8px;
            border-radius: 12px;
            background: #FFFFFF;
            border: 1px solid {BORDER};
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }}
        @media (min-width: 768px) {{
            .rank-row {{ gap: 16px; padding: 14px 18px; border-radius: 14px; }}
        }}
        .rank-badge {{
            width: 32px;
            height: 32px;
            min-width: 32px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 0.95rem;
            background: #EDF2F7;
            color: {MUTED};
        }}
        @media (min-width: 768px) {{
            .rank-badge {{ width: 38px; height: 38px; min-width: 38px; border-radius: 12px; font-size: 1.1rem; }}
        }}
        .rank-badge.gold {{ background: linear-gradient(135deg, #FFE899 0%, {AMBER} 100%); color: #4A3000; }}
        .rank-badge.silver {{ background: linear-gradient(135deg, #F1F5F9 0%, #CBD5E1 100%); color: #334155; }}
        .rank-badge.bronze {{ background: linear-gradient(135deg, #FFEDD5 0%, #FB923C 100%); color: #7C2D12; }}
        .rank-info {{ flex: 1; min-width: 0; }}
        .rank-name {{
            font-weight: 700;
            color: {NAVY};
            font-size: 0.88rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        @media (min-width: 768px) {{
            .rank-name {{ font-size: 1rem; }}
        }}
        .rank-bar-track {{
            background: #EDF2F7;
            border-radius: 10px;
            height: 7px;
            margin-top: 6px;
            overflow: hidden;
        }}
        @media (min-width: 768px) {{
            .rank-bar-track {{ height: 9px; margin-top: 8px; }}
        }}
        .rank-bar-fill {{ background: linear-gradient(90deg, {BLUE} 0%, #3B82F6 100%); height: 100%; border-radius: 10px; }}
        .rank-bar-fill.gold {{ background: linear-gradient(90deg, {AMBER} 0%, #FBBF24 100%); }}

        .rank-count {{ text-align: right; min-width: 65px; }}
        @media (min-width: 768px) {{
            .rank-count {{ min-width: 90px; }}
        }}
        .rank-count .n {{ font-weight: 800; color: {NAVY}; font-size: 0.95rem; }}
        @media (min-width: 768px) {{
            .rank-count .n {{ font-size: 1.1rem; }}
        }}
        .rank-count .p {{ color: {MUTED}; font-size: 0.68rem; font-weight: 600; }}
        @media (min-width: 768px) {{
            .rank-count .p {{ font-size: 0.76rem; }}
        }}

        .chip {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 3px 8px;
            border-radius: 30px;
            font-size: 0.7rem;
            font-weight: 700;
        }}
        @media (min-width: 768px) {{
            .chip {{ gap: 5px; padding: 4px 12px; font-size: 0.76rem; }}
        }}
        .chip-blue {{ background: #EBF3FA; color: {BLUE}; border: 1px solid rgba(29, 95, 166, 0.15); }}
        .chip-green {{ background: #E8F5E9; color: {GREEN}; border: 1px solid rgba(46, 158, 109, 0.2); }}
        .chip-amber {{ background: #FEF3D6; color: #B47818; border: 1px solid rgba(240, 166, 41, 0.25); }}
        .chip-muted {{ background: #F1F5F9; color: {MUTED}; border: 1px solid {BORDER}; }}

        /* PERSON CARD RESPONSIVO */
        .person-card {{
            border: 1px solid {BORDER};
            border-radius: 14px;
            padding: 12px 14px;
            margin-bottom: 8px;
            background: {CARD};
        }}
        @media (min-width: 768px) {{
            .person-card {{ border-radius: 16px; padding: 16px 20px; margin-bottom: 10px; }}
        }}
        .person-top {{
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            gap: 10px;
        }}
        @media (min-width: 550px) {{
            .person-top {{ flex-direction: row; justify-content: space-between; align-items: center; gap: 14px; }}
        }}
        .person-name {{ font-weight: 800; color: {NAVY}; font-size: 0.95rem; }}
        @media (min-width: 768px) {{
            .person-name {{ font-size: 1.02rem; }}
        }}
        .person-meta {{
            color: {MUTED};
            font-size: 0.78rem;
            margin-top: 4px;
            display: flex;
            align-items: center;
            gap: 6px;
            flex-wrap: wrap;
        }}
        @media (min-width: 768px) {{
            .person-meta {{ font-size: 0.84rem; margin-top: 5px; gap: 8px; }}
        }}
        .wa-link {{
            text-decoration: none !important;
            background: linear-gradient(135deg, {GREEN} 0%, #227C55 100%);
            color: #FFFFFF !important;
            font-size: 0.75rem;
            font-weight: 800;
            padding: 6px 12px;
            border-radius: 10px;
            white-space: nowrap;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            width: 100%;
        }}
        @media (min-width: 550px) {{
            .wa-link {{ width: auto; font-size: 0.8rem; padding: 8px 16px; border-radius: 12px; }}
        }}

        .ficha-grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 8px;
            margin-top: 6px;
        }}
        @media (min-width: 640px) {{
            .ficha-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
        .ficha-item {{
            background: #F8FAFC;
            border: 1px solid {BORDER};
            border-radius: 10px;
            padding: 8px 12px;
        }}
        .ficha-label {{
            font-size: 0.68rem;
            font-weight: 800;
            color: {MUTED};
            text-transform: uppercase;
            letter-spacing: 0.4px;
        }}
        .ficha-value {{ font-size: 0.86rem; font-weight: 700; color: {NAVY}; margin-top: 2px; }}

        .login-card {{
            background: {CARD};
            border: 1px solid {BORDER};
            border-radius: 20px;
            padding: 32px 20px;
            max-width: 440px;
            margin: 30px auto 0 auto;
            text-align: center;
            box-shadow: 0 24px 48px rgba(7, 26, 45, 0.12);
        }}
        @media (min-width: 768px) {{
            .login-card {{ border-radius: 24px; padding: 48px 36px; margin-top: 70px; }}
        }}
        .login-icon {{
            width: 54px;
            height: 54px;
            background: linear-gradient(135deg, {NAVY} 0%, {NAVY_SOFT} 100%);
            color: {AMBER};
            border-radius: 16px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            margin-bottom: 16px;
        }}
        @media (min-width: 768px) {{
            .login-icon {{ width: 64px; height: 64px; border-radius: 20px; font-size: 1.8rem; margin-bottom: 20px; }}
        }}

        div[data-testid="stButton"] button {{
            background: linear-gradient(135deg, {NAVY} 0%, {BLUE} 100%);
            color: white;
            border: none;
            font-weight: 700;
            border-radius: 12px;
            padding: 10px 18px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# =====================================================================
# 3. CARREGAMENTO E TRATAMENTO DOS DADOS
# =====================================================================
URL_SHEETS = "https://docs.google.com/spreadsheets/d/17FGnNHegZTxubuE2B3bGNQcgiTT8i8EpqD6rOdmItVM/export?format=csv"

VALORES_VAZIOS = ["NAN", "NONE", "NAO", "NÃO", "NAO POSSUI", "NÃO POSSUI", "NENHUM", "NEHUM", "", "0", "-"]


def safe_title(text):
    """Converte e formata strings com segurança, evitando erros em NaN/floats."""
    if pd.isna(text) or text is None:
        return ""
    txt = str(text).strip()
    if txt.upper() in VALORES_VAZIOS:
        return ""
    return txt.title()


def normalizar(col: str) -> str:
    return (
        col.upper()
        .replace("Ç", "C")
        .replace("Ã", "A")
        .replace("Á", "A")
        .replace("Â", "A")
        .replace("Õ", "O")
        .replace("Ó", "O")
        .replace("É", "E")
        .replace("Ê", "E")
        .replace("Í", "I")
        .replace("Ú", "U")
        .strip()
    )


def mask_cpf(cpf: str) -> str:
    digitos = re.sub(r"\D", "", str(cpf))
    if len(digitos) < 4:
        return "—"
    return f"***.***.**{digitos[-4:-2]}-{digitos[-2:]}"


def whatsapp_link(contato: str) -> str:
    if not contato or contato in VALORES_VAZIOS:
        return ""
    digitos = re.sub(r"\D", "", str(contato))
    if len(digitos) < 10:
        return str(contato)
    if not digitos.startswith("55"):
        digitos = "55" + digitos
    return f'<a class="wa-link" href="https://wa.me/{digitos}" target="_blank">💬 Chamar no WhatsApp</a>'


@st.cache_data(ttl=60)
def carregar_dados():
    df = pd.read_csv(URL_SHEETS)
    df.columns = df.columns.astype(str).str.strip()

    def buscar_coluna(termos_busca, excluir=None):
        excluir = excluir or []
        for col in df.columns:
            col_clean = normalizar(col)
            if any(ex in col_clean for ex in excluir):
                continue
            for termo in termos_busca:
                if termo in col_clean:
                    return col
        return None

    col_timestamp = buscar_coluna(["CARIMBO"])
    col_lider = buscar_coluna(["LIDER", "INDICACAO"])
    col_nome = buscar_coluna(["NOME"], excluir=["MAE"])
    col_contato = buscar_coluna(["CONTATO", "TELEFONE", "CELULAR", "ZAP", "WHATSAPP"])
    col_nasc = buscar_coluna(["NASCIMENTO"])
    col_mae = buscar_coluna(["MAE"])
    col_titulo = buscar_coluna(["TITULO"])
    col_cpf = buscar_coluna(["CPF"])
    col_local_votacao = buscar_coluna(["LOCAL DE VOTACAO", "LOCAL VOTACAO", "SECAO", "COLEGIO"])
    col_bairro = buscar_coluna(["BAIRRO"])
    col_veiculo = buscar_coluna(["VEICULO", "MODELO"])

    renomear = {}
    if col_timestamp:
        renomear[col_timestamp] = "TIMESTAMP_PADRAO"
    if col_lider:
        renomear[col_lider] = "LIDER_PADRAO"
    if col_nome:
        renomear[col_nome] = "NOME_PADRAO"
    if col_contato:
        renomear[col_contato] = "CONTATO_PADRAO"
    if col_nasc:
        renomear[col_nasc] = "NASCIMENTO_PADRAO"
    if col_mae:
        renomear[col_mae] = "MAE_PADRAO"
    if col_titulo:
        renomear[col_titulo] = "TITULO_PADRAO"
    if col_cpf:
        renomear[col_cpf] = "CPF_PADRAO"
    if col_local_votacao:
        renomear[col_local_votacao] = "LOCAL_VOTACAO_PADRAO"
    if col_bairro:
        renomear[col_bairro] = "BAIRRO_PADRAO"
    if col_veiculo:
        renomear[col_veiculo] = "VEICULO_INFO_PADRAO"

    df = df.rename(columns=renomear)

    texto_cols = [
        "LIDER_PADRAO", "BAIRRO_PADRAO", "VEICULO_INFO_PADRAO",
    ]
    for c in texto_cols:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().str.upper()

    for c in ["NOME_PADRAO", "MAE_PADRAO", "LOCAL_VOTACAO_PADRAO"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()

    for c in ["CONTATO_PADRAO", "TITULO_PADRAO", "CPF_PADRAO"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()

    if "TIMESTAMP_PADRAO" in df.columns:
        df["Timestamp_DT"] = pd.to_datetime(df["TIMESTAMP_PADRAO"], dayfirst=True, errors="coerce")

    hoje = date.today()
    if "NASCIMENTO_PADRAO" in df.columns:
        df["Data_Nasc_DT"] = pd.to_datetime(df["NASCIMENTO_PADRAO"], dayfirst=True, errors="coerce")

        def calcular_idade(nasc):
            if pd.isna(nasc):
                return np.nan
            nasc = nasc.date()
            idade = hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))
            return idade if 0 <= idade <= 120 else np.nan

        df["Idade"] = df["Data_Nasc_DT"].apply(calcular_idade)

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
        <div class="login-card">
            <div class="login-icon">🛡️</div>
            <div style="color:{AMBER}; font-weight:800; font-size:0.75rem; letter-spacing:1.5px; text-transform:uppercase;">ACESSO EXCLUSIVO</div>
            <h1 style="font-size:1.5rem; font-weight:800; color:{NAVY}; margin:8px 0 4px 0;">Campanha 2026</h1>
            <p style="color:{MUTED}; font-size:0.85rem; margin-bottom:20px;">Insira a credencial de segurança para acessar o Centro de Comando de Campo.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_a, col_b, col_c = st.columns([0.2, 1.6, 0.2])
    with col_b:
        senha_digitada = st.text_input("Senha", type="password", label_visibility="collapsed", placeholder="Sua senha de acesso")
        if st.button("Autenticar no Painel", use_container_width=True):
            if senha_digitada == senha_correta:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
    st.stop()


def parse_veiculo(info: str):
    """Recebe 'MODELO,COR,PLACA' e devolve dict com as partes disponíveis."""
    partes = [p.strip() for p in str(info).split(",") if p.strip()]
    resultado = {"modelo": "", "cor": "", "placa": ""}
    campos = ["modelo", "cor", "placa"]
    for i, valor in enumerate(partes[:3]):
        resultado[campos[i]] = valor.title() if campos[i] != "placa" else valor.upper()
    return resultado


def veiculo_valido(valor: str) -> bool:
    if pd.isna(valor):
        return False
    return str(valor).strip().upper() not in VALORES_VAZIOS


def render_ficha_completa(r, mostrar_cpf: bool):
    nasc = r.get("NASCIMENTO_PADRAO", "")
    idade = r.get("Idade", np.nan)
    idade_txt = f"{int(idade)} anos" if pd.notna(idade) else "—"
    mae = safe_title(r.get("MAE_PADRAO", "")) or "—"
    titulo = str(r.get("TITULO_PADRAO", "")).strip() or "—"
    titulo = "—" if titulo.upper() in VALORES_VAZIOS else titulo
    cpf_raw = str(r.get("CPF_PADRAO", "")).strip()
    if cpf_raw.upper() in VALORES_VAZIOS or not cpf_raw:
        cpf_txt = "—"
    else:
        cpf_txt = cpf_raw if mostrar_cpf else mask_cpf(cpf_raw)
    local_votacao = safe_title(r.get("LOCAL_VOTACAO_PADRAO", "")) or "—"

    st.markdown(
        f"""
        <div class="ficha-grid">
            <div class="ficha-item"><div class="ficha-label">Data de Nascimento</div><div class="ficha-value">{nasc or "—"} ({idade_txt})</div></div>
            <div class="ficha-item"><div class="ficha-label">Nome da Mãe</div><div class="ficha-value">{mae}</div></div>
            <div class="ficha-item"><div class="ficha-label">Título de Eleitor</div><div class="ficha-value">{titulo}</div></div>
            <div class="ficha-item"><div class="ficha-label">CPF</div><div class="ficha-value">{cpf_txt}</div></div>
            <div class="ficha-item" style="grid-column: 1 / -1;"><div class="ficha-label">Local de Votação</div><div class="ficha-value">{local_votacao}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_person_card(r, mostrar_cpf: bool, mostrar_ficha: bool = True):
    nome = safe_title(r.get("NOME_PADRAO", "—")) or "—"
    bairro = safe_title(r.get("BAIRRO_PADRAO", ""))
    lider = safe_title(r.get("LIDER_PADRAO", ""))
    contato = r.get("CONTATO_PADRAO", "") if "CONTATO_PADRAO" in r else ""
    wa = whatsapp_link(contato)

    chips = ""
    if bairro:
        chips += f'<span class="chip chip-muted">📍 {bairro}</span>'
    if lider:
        chips += f'<span class="chip chip-blue">Líder: {lider}</span>'

    st.markdown(
        f"""
        <div class="person-card">
            <div class="person-top">
                <div>
                    <div class="person-name">{nome}</div>
                    <div class="person-meta">{chips}</div>
                </div>
                {wa}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if mostrar_ficha:
        with st.expander("🔎 Ver ficha completa"):
            render_ficha_completa(r, mostrar_cpf)


# =====================================================================
# 4. INTERFACE
# =====================================================================
inject_css()
verificar_senha()

df = carregar_dados()

# ---------- Bases auxiliares ----------
if "VEICULO_INFO_PADRAO" in df.columns:
    df_veiculos_filtro = df[df["VEICULO_INFO_PADRAO"].apply(veiculo_valido)].copy()
else:
    df_veiculos_filtro = pd.DataFrame()

total_cadastros = len(df)
lideres_ativos = (
    df["LIDER_PADRAO"].replace("NAN", np.nan).dropna().nunique()
    if "LIDER_PADRAO" in df.columns else 0
)
bairros_cobertos = (
    df["BAIRRO_PADRAO"].replace("NAN", np.nan).dropna().nunique()
    if "BAIRRO_PADRAO" in df.columns else 0
)
veiculos_mapeados = len(df_veiculos_filtro)

hoje = date.today()
dias_restantes = (DATA_ELEICAO - hoje).days
if dias_restantes > 1:
    texto_dias = f"Faltam <b>{dias_restantes} dias</b> para as eleições."
elif dias_restantes == 1:
    texto_dias = "Falta apenas <b>1 dia</b> para as eleições!"
elif dias_restantes == 0:
    texto_dias = "É HOJE! Dia da Eleição! 🗳️"
else:
    texto_dias = f"Eleições realizadas há {abs(dias_restantes)} dias."

agora = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y às %H:%M")

st.markdown(
    f"""<div class="hero-banner">
        <div class="hero-tag-container">
            <div class="hero-tag"><span class="status-dot"></span> CENTRO DE COMANDO 2026</div>
            <div style="font-size:0.75rem; color:#CBD5E1; font-weight:600;">🔄 {agora}</div>
        </div>
        <h1>Painel de Operações</h1>
        <p>Monitoramento estratégico de mobilização e base em tempo real.</p>
        <div class="countdown-box">
            <div class="countdown-icon">⏳</div>
            <div>
                <div class="countdown-title">Contagem Regressiva · {DATA_ELEICAO.strftime('%d/%m/%Y')}</div>
                <div class="countdown-text">{texto_dias}</div>
            </div>
        </div>
    </div>""",
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-icon-wrap">👥</div>
            <div class="kpi-label">Cadastros</div>
            <div class="kpi-value">{total_cadastros}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon-wrap">⭐</div>
            <div class="kpi-label">Líderes</div>
            <div class="kpi-value">{lideres_ativos}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon-wrap">📍</div>
            <div class="kpi-label">Bairros</div>
            <div class="kpi-value">{bairros_cobertos}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon-wrap">🚗</div>
            <div class="kpi-label">Veículos</div>
            <div class="kpi-value">{veiculos_mapeados}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

col_toggle, _ = st.columns([1, 3])
with col_toggle:
    mostrar_cpf = st.checkbox("🔓 Exibir CPF completo nas fichas", value=False)

selected = option_menu(
    menu_title=None,
    options=["Liderança", "Bairros", "Veículos", "Perfil Demográfico"],
    icons=["people-fill", "geo-alt-fill", "car-front-fill", "bar-chart-fill"],
    orientation="horizontal",
    styles={
        "container": {"padding": "4px", "background-color": CARD, "border": f"1px solid {BORDER}", "border-radius": "14px", "margin-bottom": "18px", "box-shadow": "0 2px 10px rgba(7, 26, 45, 0.03)"},
        "icon": {"color": MUTED, "font-size": "13px"},
        "nav-link": {"font-family": "Plus Jakarta Sans, sans-serif", "font-weight": "700", "font-size": "0.78rem", "color": MUTED, "text-align": "center", "border-radius": "10px", "padding": "8px 6px"},
        "nav-link-selected": {"background-color": NAVY, "color": "#FFFFFF"},
    },
)

# ==========================================
# ABA 1: LIDERANÇA
# ==========================================
if selected == "Liderança":
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(
        '''
        <div class="section-header-wrap">
            <div class="section-title">🏆 Leaderboard de Lideranças</div>
            <div class="section-subtitle">Ranking de captação de eleitores por liderança</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    df_lideres = pd.DataFrame()
    if "LIDER_PADRAO" in df.columns and not df.empty:
        df_clean_lider = df[~df["LIDER_PADRAO"].isin(VALORES_VAZIOS + ["NÃO INFORMADO"])]
        df_lideres = (
            df_clean_lider["LIDER_PADRAO"].value_counts().reset_index()
            .rename(columns={"LIDER_PADRAO": "Líder", "count": "Total"})
            .sort_values(by="Total", ascending=False)
            .reset_index(drop=True)
        )
        maior_total = df_lideres["Total"].max() if not df_lideres.empty else 0

        rows_html = ""
        for i, row in df_lideres.iterrows():
            rank = i + 1
            if rank == 1:
                badge_class, badge_icon = "gold", "🥇"
            elif rank == 2:
                badge_class, badge_icon = "silver", "🥈"
            elif rank == 3:
                badge_class, badge_icon = "bronze", "🥉"
            else:
                badge_class, badge_icon = "", str(rank)

            largura = (row["Total"] / maior_total * 100) if maior_total else 0
            cor_barra = "gold" if rank == 1 else ""
            pct_da_base = (row["Total"] / total_cadastros * 100) if total_cadastros else 0
            rows_html += f"""
            <div class="rank-row">
                <div class="rank-badge {badge_class}">{badge_icon}</div>
                <div class="rank-info">
                    <div class="rank-name">{safe_title(row['Líder'])}</div>
                    <div class="rank-bar-track"><div class="rank-bar-fill {cor_barra}" style="width:{largura:.0f}%"></div></div>
                </div>
                <div class="rank-count"><div class="n">{row['Total']}</div><div class="p">{pct_da_base:.1f}% da base</div></div>
            </div>
            """
        st.markdown(rows_html, unsafe_allow_html=True)
    else:
        st.info("Nenhum dado de liderança encontrado na planilha.")
    st.markdown('</div>', unsafe_allow_html=True)

    if not df_lideres.empty:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown(
            '''
            <div class="section-header-wrap">
                <div class="section-title">📊 Distributivo por Captador</div>
                <div class="section-subtitle">Análise comparativa quantitativa do desempenho individual</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )
        fig_lider = px.bar(df_lideres, x="Total", y="Líder", orientation="h", text="Total")
        fig_lider.update_traces(
            marker_color=[AMBER if i == 0 else BLUE for i in range(len(df_lideres))],
            textposition="outside",
            marker_line_width=0,
            textfont=dict(size=11, color=TEXT, family=PLOTLY_FONT),
        )
        fig_lider.update_layout(
            font_family=PLOTLY_FONT, font_color=TEXT,
            xaxis_title="", yaxis_title="",
            yaxis={"categoryorder": "total ascending"},
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=20, t=10, b=10),
            height=max(260, 40 * len(df_lideres)),
        )
        fig_lider.update_xaxes(showgrid=True, gridcolor=BORDER)
        st.plotly_chart(fig_lider, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown(
            '''
            <div class="section-header-wrap">
                <div class="section-title">🔍 Explorador por Líder</div>
                <div class="section-subtitle">Veja todos os cadastros captados por uma liderança específica</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )
        lider_sel = st.selectbox("Selecione a liderança", ["Todas as lideranças"] + list(df_lideres["Líder"]))
        df_lider_view = df_clean_lider.copy()
        if lider_sel != "Todas as lideranças":
            df_lider_view = df_lider_view[df_lider_view["LIDER_PADRAO"] == lider_sel]

        st.markdown("<br>", unsafe_allow_html=True)
        for _, r in df_lider_view.iterrows():
            render_person_card(r, mostrar_cpf)
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# ABA 2: BAIRROS
# ==========================================
if selected == "Bairros":
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(
        '''
        <div class="section-header-wrap">
            <div class="section-title">📍 Mapeamento por Bairro</div>
            <div class="section-subtitle">Distribuição geográfica e cobertura de apoiadores</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    if "BAIRRO_PADRAO" in df.columns:
        df_bairros_validos = df[~df["BAIRRO_PADRAO"].isin(VALORES_VAZIOS)]

        bairros_summary = (
            df_bairros_validos.groupby("BAIRRO_PADRAO")
            .agg(
                Total_Apoiadores=("BAIRRO_PADRAO", "count"),
                Lideres_Distintos=("LIDER_PADRAO", lambda x: len(set(x.dropna()) - set(VALORES_VAZIOS))),
                Veiculos=("VEICULO_INFO_PADRAO", lambda x: len([v for v in x if veiculo_valido(v)])),
            )
            .reset_index()
            .sort_values(by="Total_Apoiadores", ascending=False)
        )
        fig_bairros = px.bar(
            bairros_summary.head(10),
            x="BAIRRO_PADRAO", y="Total_Apoiadores", text="Total_Apoiadores",
            color_discrete_sequence=[BLUE],
        )
        fig_bairros.update_traces(
            textposition="outside", marker_line_width=0,
            textfont=dict(size=11, color=TEXT, family=PLOTLY_FONT),
        )
        fig_bairros.update_layout(
            font_family=PLOTLY_FONT, font_color=TEXT,
            xaxis_title="", yaxis_title="",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=20, b=10), height=280,
        )
        fig_bairros.update_yaxes(showgrid=True, gridcolor=BORDER)

        st.markdown("<h4 style='font-size:0.95rem; font-weight:800; color:#071A2D; margin-bottom:8px;'>🔥 Top 10 Bairros</h4>", unsafe_allow_html=True)
        st.plotly_chart(fig_bairros, use_container_width=True, config={"displayModeBar": False})

        st.markdown("<hr style='border:none; border-top:1px solid #E6EBF2; margin:18px 0;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='font-size:0.95rem; font-weight:800; color:#071A2D; margin-bottom:8px;'>🔍 Explorador de Bairros</h4>", unsafe_allow_html=True)

        col_f1, col_f2 = st.columns([1, 1])
        with col_f1:
            lista_bairros_select = ["Todos os Bairros"] + list(bairros_summary["BAIRRO_PADRAO"])
            bairro_sel = st.selectbox("Filtrar visualização", lista_bairros_select)
        with col_f2:
            busca_nome = st.text_input("Buscar apoiador", placeholder="Digite um nome...")

        df_filtrado_bairros = df_bairros_validos.copy()
        if bairro_sel != "Todos os Bairros":
            df_filtrado_bairros = df_filtrado_bairros[df_filtrado_bairros["BAIRRO_PADRAO"] == bairro_sel]
        if busca_nome and "NOME_PADRAO" in df_filtrado_bairros.columns:
            df_filtrado_bairros = df_filtrado_bairros[
                df_filtrado_bairros["NOME_PADRAO"].str.upper().str.contains(busca_nome.upper(), na=False)
            ]

        bairros_para_exibir = (
            [bairro_sel] if bairro_sel != "Todos os Bairros"
            else list(df_filtrado_bairros["BAIRRO_PADRAO"].unique())
        )

        st.markdown("<br>", unsafe_allow_html=True)
        for b in bairros_para_exibir:
            if b in VALORES_VAZIOS:
                continue
            sub_df = df_filtrado_bairros[df_filtrado_bairros["BAIRRO_PADRAO"] == b]
            if sub_df.empty:
                continue
            with st.expander(f"📍 {safe_title(b)} — {len(sub_df)} Apoiador(es)"):
                for _, r in sub_df.iterrows():
                    render_person_card(r, mostrar_cpf)
    else:
        st.info("Coluna de bairro não encontrada na planilha.")
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# ABA 3: VEÍCULOS
# ==========================================
if selected == "Veículos":
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(
        '''
        <div class="section-header-wrap">
            <div class="section-title">🚗 Frota de Apoio</div>
            <div class="section-subtitle">Mapeamento de veículos disponíveis por região</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    if not df_veiculos_filtro.empty:
        bairros_com_veic = (
            df_veiculos_filtro["BAIRRO_PADRAO"].replace("NAN", np.nan).nunique()
            if "BAIRRO_PADRAO" in df_veiculos_filtro else 0
        )
        ratio = (len(df_veiculos_filtro) / total_cadastros * 100) if total_cadastros > 0 else 0

        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.markdown(f'<div class="kpi-card" style="margin-bottom:8px;"><div class="kpi-icon-wrap">🚙</div><div class="kpi-label">Frota</div><div class="kpi-value">{len(df_veiculos_filtro)}</div></div>', unsafe_allow_html=True)
        with col_m2:
            st.markdown(f'<div class="kpi-card" style="margin-bottom:8px;"><div class="kpi-icon-wrap">📍</div><div class="kpi-label">Bairros</div><div class="kpi-value">{bairros_com_veic}</div></div>', unsafe_allow_html=True)
        with col_m3:
            st.markdown(f'<div class="kpi-card" style="margin-bottom:8px;"><div class="kpi-icon-wrap">⚡</div><div class="kpi-label">Cobertura</div><div class="kpi-value">{ratio:.1f}%</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        c_v1, c_v2 = st.columns([1, 1])
        with c_v1:
            bairros_v_validos = sorted(
                [b for b in df_veiculos_filtro["BAIRRO_PADRAO"].dropna().unique() if b not in VALORES_VAZIOS]
            )
            bairro_v_sel = st.selectbox("Filtrar por bairro", ["Todos os bairros"] + bairros_v_validos)
        with c_v2:
            busca_veiculo = st.text_input("Filtrar por modelo/motorista", placeholder="Ex: Gol, Fiat, João...")

        df_veic_exibir = df_veiculos_filtro.copy()
        if bairro_v_sel != "Todos os bairros":
            df_veic_exibir = df_veic_exibir[df_veic_exibir["BAIRRO_PADRAO"] == bairro_v_sel]
        if busca_veiculo:
            termo = busca_veiculo.upper()
            df_veic_exibir = df_veic_exibir[
                df_veic_exibir["VEICULO_INFO_PADRAO"].str.upper().str.contains(termo, na=False)
                | df_veic_exibir["NOME_PADRAO"].str.upper().str.contains(termo, na=False)
            ]

        st.markdown("<br>", unsafe_allow_html=True)

        cols_veic = st.columns([1, 1])
        for idx, (_, r) in enumerate(df_veic_exibir.iterrows()):
            nome = safe_title(r.get("NOME_PADRAO", "—"))
            bairro = safe_title(r.get("BAIRRO_PADRAO", ""))
            lider = safe_title(r.get("LIDER_PADRAO", ""))
            contato = r.get("CONTATO_PADRAO", "") if "CONTATO_PADRAO" in r else ""
            wa = whatsapp_link(contato)

            partes = parse_veiculo(r.get("VEICULO_INFO_PADRAO", ""))
            veiculo_titulo = partes["modelo"] or "Veículo"
            chip_cor = f'<span class="chip chip-amber">🎨 {partes["cor"]}</span>' if partes["cor"] else ""
            chip_placa = f'<span class="chip chip-muted">🔖 {partes["placa"]}</span>' if partes["placa"] else ""

            target_col = cols_veic[idx % 2]
            with target_col:
                st.markdown(
                    f"""
                    <div class="veiculo-card-interactive">
                        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:8px;">
                            <div>
                                <div class="veiculo-title">🚗 {veiculo_titulo}</div>
                                <div class="veiculo-owner">Motorista: <b>{nome}</b></div>
                            </div>
                            <div style="width:100%;">{wa}</div>
                        </div>
                        <div style="margin-top:10px; display:flex; gap:6px; flex-wrap:wrap;">
                            <span class="chip chip-muted">📍 {bairro}</span>
                            <span class="chip chip-blue">Líder: {lider}</span>
                            {chip_cor}
                            {chip_placa}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.info("Nenhum apoiador com veículo registrado na planilha.")
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# ABA 4: PERFIL DEMOGRÁFICO
# ==========================================
if selected == "Perfil Demográfico":
    if "Idade" in df.columns:
        idades_validas = df["Idade"].dropna()

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown(
            '''
            <div class="section-header-wrap">
                <div class="section-title">👤 Perfil Etário da Base</div>
                <div class="section-subtitle">Visão geral de idade dos apoiadores cadastrados</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )
        col_i1, col_i2, col_i3 = st.columns(3)
        with col_i1:
            media_idade = idades_validas.mean()
            valor = f"{media_idade:.1f}" if pd.notna(media_idade) else "—"
            st.markdown(f'<div class="kpi-card"><div class="kpi-icon-wrap">📊</div><div class="kpi-label">Idade Média</div><div class="kpi-value">{valor}</div></div>', unsafe_allow_html=True)
        with col_i2:
            mais_jovem = idades_validas.min()
            valor = f"{int(mais_jovem)}" if pd.notna(mais_jovem) else "—"
            st.markdown(f'<div class="kpi-card"><div class="kpi-icon-wrap">🌱</div><div class="kpi-label">Mais Jovem</div><div class="kpi-value">{valor}</div></div>', unsafe_allow_html=True)
        with col_i3:
            mais_velho = idades_validas.max()
            valor = f"{int(mais_velho)}" if pd.notna(mais_velho) else "—"
            st.markdown(f'<div class="kpi-card"><div class="kpi-icon-wrap">🌳</div><div class="kpi-label">Mais Velho</div><div class="kpi-value">{valor}</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown(
            '''
            <div class="section-header-wrap">
                <div class="section-title">🎂 Pirâmide Etária</div>
                <div class="section-subtitle">Distribuição por faixas etárias estratégicas</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )
        df_faixa = df["Faixa_Etaria"].value_counts().reset_index()
        df_faixa.columns = ["Faixa Etária", "Quantidade"]
        ordem = ["18-24 anos", "25-39 anos", "40-59 anos", "60+ anos", "Não informado"]
        df_faixa["ordem"] = df_faixa["Faixa Etária"].apply(lambda x: ordem.index(x) if x in ordem else 99)
        df_faixa = df_faixa.sort_values("ordem")

        fig_faixa = px.bar(df_faixa, x="Faixa Etária", y="Quantidade", text="Quantidade")
        fig_faixa.update_traces(
            marker_color=BLUE, textposition="outside", marker_line_width=0,
            textfont=dict(size=11, color=TEXT, family=PLOTLY_FONT),
        )
        fig_faixa.update_layout(
            font_family=PLOTLY_FONT, font_color=TEXT,
            xaxis_title="", yaxis_title="",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=10), height=280,
        )
        fig_faixa.update_yaxes(showgrid=True, gridcolor=BORDER)
        st.plotly_chart(fig_faixa, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    if "Timestamp_DT" in df.columns and df["Timestamp_DT"].notna().any():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown(
            '''
            <div class="section-header-wrap">
                <div class="section-title">📈 Evolução dos Cadastros</div>
                <div class="section-subtitle">Ritmo de captação de apoiadores ao longo do tempo</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )
        df_evolucao = (
            df.dropna(subset=["Timestamp_DT"])
            .assign(Dia=lambda d: d["Timestamp_DT"].dt.date)
            .groupby("Dia").size().reset_index(name="Cadastros")
            .sort_values("Dia")
        )
        df_evolucao["Acumulado"] = df_evolucao["Cadastros"].cumsum()

        fig_evolucao = px.line(df_evolucao, x="Dia", y="Acumulado", markers=True)
        fig_evolucao.update_traces(line_color=BLUE, line_width=3, marker=dict(size=6, color=NAVY))
        fig_evolucao.update_layout(
            font_family=PLOTLY_FONT, font_color=TEXT,
            xaxis_title="", yaxis_title="Cadastros acumulados",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=10), height=280,
        )
        fig_evolucao.update_yaxes(showgrid=True, gridcolor=BORDER)
        fig_evolucao.update_xaxes(showgrid=False)
        st.plotly_chart(fig_evolucao, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(
        '''
        <div class="section-header-wrap">
            <div class="section-title">✅ Qualidade do Cadastro</div>
            <div class="section-subtitle">Percentual de fichas com cada campo preenchido corretamente</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )
    campos_qualidade = {
        "Contato": "CONTATO_PADRAO",
        "Data de Nascimento": "NASCIMENTO_PADRAO",
        "Nome da Mãe": "MAE_PADRAO",
        "Título de Eleitor": "TITULO_PADRAO",
        "CPF": "CPF_PADRAO",
        "Local de Votação": "LOCAL_VOTACAO_PADRAO",
        "Bairro": "BAIRRO_PADRAO",
    }
    linhas_qualidade = []
    for label, col in campos_qualidade.items():
        if col in df.columns:
            preenchidos = df[col].apply(lambda v: str(v).strip().upper() not in VALORES_VAZIOS and str(v).strip() != "").sum()
            pct = (preenchidos / total_cadastros * 100) if total_cadastros else 0
            linhas_qualidade.append({"Campo": label, "Percentual": round(pct, 1)})

    if linhas_qualidade:
        df_qualidade = pd.DataFrame(linhas_qualidade).sort_values("Percentual", ascending=True)
        fig_qualidade = px.bar(df_qualidade, x="Percentual", y="Campo", orientation="h", text="Percentual")
        fig_qualidade.update_traces(
            marker_color=GREEN, textposition="outside", marker_line_width=0,
            texttemplate="%{text:.1f}%",
            textfont=dict(size=11, color=TEXT, family=PLOTLY_FONT),
        )
        fig_qualidade.update_layout(
            font_family=PLOTLY_FONT, font_color=TEXT,
            xaxis_title="", yaxis_title="",
            xaxis_range=[0, 110],
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=20, t=10, b=10), height=max(220, 40 * len(df_qualidade)),
        )
        fig_qualidade.update_xaxes(showgrid=True, gridcolor=BORDER)
        st.plotly_chart(fig_qualidade, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Não foi possível calcular a qualidade dos dados com as colunas disponíveis.")
    st.markdown('</div>', unsafe_allow_html=True)
