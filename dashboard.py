import re
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_option_menu import option_menu

=====================================================================
1. CONFIGURAÇÃO DA PÁGINA
=====================================================================
st.set_page_config(
page_title="Campanha 2026 · Centro de Comando",
page_icon="🗳️",
layout="wide",
initial_sidebar_state="collapsed",
)

=====================================================================
2. IDENTIDADE VISUAL & CSS DESIGN SYSTEM (SaaS / War Room Theme)
=====================================================================
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
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {{
font-family: 'Plus Jakarta Sans', 'Manrope', -apple-system, sans-serif;
color: {TEXT};
background-color: {BG};
-webkit-font-smoothing: antialiased;
}}

#MainMenu, footer, header {{ visibility: hidden; height: 0; }}

/* Canvas de Fundo com Micro-Mesh e Dual Lighting Glows */
.stApp {{
background:
radial-gradient(800px circle at 15% -10%, rgba(29, 95, 166, 0.12) 0%, transparent 60%),
radial-gradient(700px circle at 85% 110%, rgba(240, 166, 41, 0.08) 0%, transparent 50%),
radial-gradient(600px circle at 50% 50%, rgba(2, 132, 199, 0.03) 0%, transparent 70%),
{BG};
background-attachment: fixed;
}}

.block-container {{
padding-top: 1.5rem;
padding-bottom: 4rem;
max-width: 1280px;
}}

/* Keyframes de Micro-interações e Efeitos de Brilho */
@keyframes fadeInUp {{
from {{ opacity: 0; transform: translateY(16px); }}
to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes fillBar {{
from {{ width: 0%; }}
}}
@keyframes pulseDot {{
0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 158, 109, 0.7); }}
70% {{ transform: scale(1); box-shadow: 0 0 0 8px rgba(46, 158, 109, 0); }}
100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 158, 109, 0); }}
}}
@keyframes goldShine {{
0% {{ box-shadow: 0 0 0 0 rgba(240, 166, 41, 0.4); }}
50% {{ box-shadow: 0 0 16px 4px rgba(240, 166, 41, 0.25); }}
100% {{ box-shadow: 0 0 0 0 rgba(240, 166, 41, 0.4); }}
}}

/* ---------- HERO COMMAND HEADER ---------- */
.hero-banner {{
background: linear-gradient(135deg, {NAVY} 0%, {NAVY_SOFT} 50%, {BLUE} 100%);
border-radius: 24px;
padding: 36px 40px;
color: #FFFFFF;
margin-bottom: 24px;
position: relative;
overflow: hidden;
box-shadow: 0 20px 40px -12px rgba(7, 26, 45, 0.35), inset 0 1px 0 0 rgba(255, 255, 255, 0.2);
border: 1px solid rgba(255, 255, 255, 0.12);
animation: fadeInUp 0.45s ease-out;
}}
.hero-banner::after {{
content: "";
position: absolute;
top: -50%;
right: -20%;
width: 500px;
height: 500px;
background: radial-gradient(circle, rgba(240, 166, 41, 0.15) 0%, transparent 65%);
pointer-events: none;
}}
.hero-tag-container {{
display: flex;
align-items: center;
justify-content: space-between;
margin-bottom: 12px;
flex-wrap: wrap;
gap: 10px;
}}
.hero-tag {{
background: rgba(240, 166, 41, 0.15);
border: 1px solid rgba(240, 166, 41, 0.4);
color: {AMBER};
font-weight: 800;
font-size: 0.72rem;
letter-spacing: 1.5px;
text-transform: uppercase;
padding: 5px 14px;
border-radius: 30px;
display: inline-flex;
align-items: center;
gap: 8px;
backdrop-filter: blur(8px);
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
font-size: 2.3rem;
font-weight: 800;
line-height: 1.15;
letter-spacing: -0.8px;
color: #FFFFFF;
}}
.hero-banner p {{
margin-top: 8px;
color: #D2E0EE;
font-size: 0.96rem;
font-weight: 500;
}}
.hero-progress-wrapper {{
margin-top: 24px;
background: rgba(7, 26, 45, 0.4);
border: 1px solid rgba(255, 255, 255, 0.12);
padding: 16px 20px;
border-radius: 16px;
backdrop-filter: blur(12px);
}}

/* ---------- KPI EXECUTIVE METRICS ---------- */
.kpi-grid {{
display: grid;
grid-template-columns: repeat(4, 1fr);
gap: 16px;
margin-bottom: 22px;
}}
@media (max-width: 900px) {{ .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
@media (max-width: 550px) {{ .kpi-grid {{ grid-template-columns: 1fr; }} }}

.kpi-card {{
background: {CARD};
border: 1px solid {BORDER};
border-radius: 18px;
padding: 20px 22px;
position: relative;
overflow: hidden;
box-shadow: 0 4px 14px rgba(7, 26, 45, 0.03);
transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
animation: fadeInUp 0.4s ease-out backwards;
}}
.kpi-card::before {{
content: "";
position: absolute;
top: 0; left: 0; right: 0;
height: 4px;
background: linear-gradient(90deg, {NAVY} 0%, {BLUE} 100%);
}}
.kpi-card:hover {{
transform: translateY(-4px);
box-shadow: 0 14px 28px -6px rgba(7, 26, 45, 0.12);
border-color: {BLUE};
}}
.kpi-card .kpi-icon-wrap {{
width: 40px;
height: 40px;
border-radius: 12px;
background: #F0F5FA;
display: flex;
align-items: center;
justify-content: center;
font-size: 1.2rem;
margin-bottom: 12px;
}}
.kpi-card .kpi-label {{
color: {MUTED};
font-size: 0.8rem;
font-weight: 700;
text-transform: uppercase;
letter-spacing: 0.6px;
}}
.kpi-card .kpi-value {{
color: {NAVY};
font-size: 2.3rem;
font-weight: 800;
margin-top: 4px;
line-height: 1;
letter-spacing: -0.8px;
}}

/* ---------- SECTION CONTAINERS (Glassmorphism Light) ---------- */
.section-card {{
background: rgba(255, 255, 255, 0.95);
backdrop-filter: blur(16px);
border: 1px solid {BORDER};
border-radius: 20px;
padding: 26px 30px;
margin-bottom: 22px;
box-shadow: 0 4px 20px rgba(7, 26, 45, 0.04);
animation: fadeInUp 0.4s ease-out;
}}
.section-header-wrap {{
border-bottom: 1px solid {BORDER};
padding-bottom: 14px;
margin-bottom: 20px;
}}
.section-title {{
font-size: 1.25rem;
font-weight: 800;
color: {NAVY};
letter-spacing: -0.4px;
display: flex;
align-items: center;
gap: 10px;
}}
.section-subtitle {{
color: {MUTED};
font-size: 0.88rem;
font-weight: 500;
margin-top: 2px;
}}

/* ---------- LEADERBOARD HIGH-TECH ---------- */
.rank-row {{
display: flex;
align-items: center;
gap: 16px;
padding: 14px 18px;
margin-bottom: 8px;
border-radius: 14px;
background: #FFFFFF;
border: 1px solid {BORDER};
transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
animation: fadeInUp 0.35s ease-out backwards;
}}
.rank-row:hover {{
background: #F8FAFC;
transform: translateX(6px);
border-color: {BLUE};
box-shadow: 0 6px 18px rgba(7, 26, 45, 0.07);
}}
.rank-badge {{
width: 38px;
height: 38px;
min-width: 38px;
border-radius: 12px;
display: flex;
align-items: center;
justify-content: center;
font-weight: 800;
font-size: 1.1rem;
background: #EDF2F7;
color: {MUTED};
transition: transform 0.2s ease;
}}
.rank-row:hover .rank-badge {{ transform: scale(1.1); }}
.rank-badge.gold {{
background: linear-gradient(135deg, #FFE899 0%, {AMBER} 100%);
color: #4A3000;
animation: goldShine 3s infinite;
}}
.rank-badge.silver {{
background: linear-gradient(135deg, #F1F5F9 0%, #CBD5E1 100%);
color: #334155;
}}
.rank-badge.bronze {{
background: linear-gradient(135deg, #FFEDD5 0%, #FB923C 100%);
color: #7C2D12;
}}
.rank-info {{ flex: 1; min-width: 0; }}
.rank-name {{
font-weight: 700;
color: {NAVY};
font-size: 1rem;
display: flex;
align-items: center;
gap: 8px;
}}
.rank-bar-track {{
background: #EDF2F7;
border-radius: 10px;
height: 9px;
margin-top: 8px;
overflow: hidden;
}}
.rank-bar-fill {{
background: linear-gradient(90deg, {BLUE} 0%, #3B82F6 100%);
height: 100%;
border-radius: 10px;
animation: fillBar 0.9s ease-out;
transition: width 0.6s ease;
}}
.rank-bar-fill.gold {{ background: linear-gradient(90deg, {AMBER} 0%, #FBBF24 100%); }}
.rank-bar-fill.meta-ok {{ background: linear-gradient(90deg, {GREEN} 0%, #34D399 100%); }}

.rank-count {{
text-align: right;
min-width: 90px;
}}
.rank-count .n {{
font-weight: 800;
color: {NAVY};
font-size: 1.1rem;
}}
.rank-count .p {{
color: {MUTED};
font-size: 0.76rem;
font-weight: 600;
}}

/* ---------- BADGES & CHIPS ---------- */
.chip {{
display: inline-flex;
align-items: center;
gap: 5px;
padding: 4px 12px;
border-radius: 30px;
font-size: 0.76rem;
font-weight: 700;
}}
.chip-blue {{ background: #EBF3FA; color: {BLUE}; border: 1px solid rgba(29, 95, 166, 0.15); }}
.chip-green {{ background: #E8F5E9; color: {GREEN}; border: 1px solid rgba(46, 158, 109, 0.2); }}
.chip-amber {{ background: #FEF3D6; color: #B47818; border: 1px solid rgba(240, 166, 41, 0.25); }}
.chip-muted {{ background: #F1F5F9; color: {MUTED}; border: 1px solid {BORDER}; }}

/* ---------- CARDS DE PESSOAS / CONTATOS ---------- */
.person-card {{
border: 1px solid {BORDER};
border-radius: 16px;
padding: 16px 20px;
margin-bottom: 10px;
background: {CARD};
transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
animation: fadeInUp 0.35s ease-out;
}}
.person-card:hover {{
transform: translateX(4px);
border-color: {BLUE};
box-shadow: 0 8px 20px rgba(7, 26, 45, 0.08);
}}
.person-top {{
display: flex;
justify-content: space-between;
align-items: center;
gap: 14px;
}}
.person-name {{
font-weight: 800;
color: {NAVY};
font-size: 1.02rem;
}}
.person-meta {{
color: {MUTED};
font-size: 0.84rem;
margin-top: 5px;
display: flex;
align-items: center;
gap: 8px;
flex-wrap: wrap;
}}
.wa-link {{
text-decoration: none !important;
background: linear-gradient(135deg, {GREEN} 0%, #227C55 100%);
color: #FFFFFF !important;
font-size: 0.8rem;
font-weight: 800;
padding: 8px 16px;
border-radius: 12px;
white-space: nowrap;
transition: all 0.2s ease;
display: inline-flex;
align-items: center;
gap: 6px;
box-shadow: 0 4px 10px rgba(46, 158, 109, 0.25);
}}
.wa-link:hover {{
transform: translateY(-2px);
box-shadow: 0 8px 16px rgba(46, 158, 109, 0.35);
color: #FFFFFF !important;
}}

/* ---------- TELA DE LOGIN CORPORATIVA ---------- */
.login-card {{
background: {CARD};
border: 1px solid {BORDER};
border-radius: 24px;
padding: 48px 36px;
max-width: 440px;
margin: 70px auto 0 auto;
text-align: center;
box-shadow: 0 24px 48px rgba(7, 26, 45, 0.12);
animation: fadeInUp 0.5s ease-out;
position: relative;
overflow: hidden;
}}
.login-card::before {{
content: "";
position: absolute;
top: 0; left: 0; right: 0;
height: 6px;
background: linear-gradient(90deg, {NAVY} 0%, {BLUE} 50%, {AMBER} 100%);
}}
.login-icon {{
width: 64px;
height: 64px;
background: linear-gradient(135deg, {NAVY} 0%, {NAVY_SOFT} 100%);
color: {AMBER};
border-radius: 20px;
display: inline-flex;
align-items: center;
justify-content: center;
font-size: 1.8rem;
margin-bottom: 20px;
box-shadow: 0 10px 20px rgba(7, 26, 45, 0.2);
border: 1px solid rgba(255, 255, 255, 0.15);
}}

/* Customização de Botões e Inputs Nativos */
div[data-testid="stButton"] button {{
background: linear-gradient(135deg, {NAVY} 0%, {BLUE} 100%);
color: white;
border: none;
font-weight: 700;
border-radius: 12px;
padding: 12px 24px;
transition: all 0.2s ease;
box-shadow: 0 4px 14px rgba(7, 26, 45, 0.18);
}}
div[data-testid="stButton"] button:hover {{
transform: translateY(-2px);
box-shadow: 0 8px 22px rgba(29, 95, 166, 0.35);
color: white;
}}
.stSelectbox, .stTextInput {{ font-weight: 600; }}
</style>
""",
unsafe_allow_html=True,
)


=====================================================================
3. CARREGAMENTO E TRATAMENTO DOS DADOS (Preservado)
=====================================================================
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
<div style="color:{AMBER}; font-weight:800; font-size:0.75rem; letter-spacing:1.5px; text-transform:uppercase;">ACESSO EXCLUSIVO</div>
<h1 style="font-size:1.75rem; font-weight:800; color:{NAVY}; margin:8px 0 4px 0;">Campanha 2026</h1>
<p style="color:{MUTED}; font-size:0.9rem; margin-bottom:24px;">Insira a credencial de segurança para acessar o Centro de Comando de Campo.</p>
</div>
""",
unsafe_allow_html=True,
)
col_a, col_b, col_c = st.columns([1, 1.2, 1])
with col_b:
senha_digitada = st.text_input("Senha", type="password", label_visibility="collapsed", placeholder="Sua senha de acesso")
if st.button("Autenticar no Painel", use_container_width=True):
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

---------- Filtro de veículos válidos ----------
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

---------- Filtro de Apoio Extra: Adesivo e Trabalho no Dia ----------
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

=====================================================================
4. INTERFACE
=====================================================================
inject_css()
verificar_senha()

agora = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y às %H:%M")
pct_meta = min(total_cadastros / META_CAMPANHA * 100, 100) if META_CAMPANHA else 0
meta_atingida = total_cadastros >= META_CAMPANHA
cor_meta = GREEN if meta_atingida else AMBER
texto_meta = (
f"Meta Batida! 🎉 {total_cadastros} de {META_CAMPANHA} apoiadores registrados"
if meta_atingida
else f"{total_cadastros} de {META_CAMPANHA} apoiadores · Faltam apenas {META_CAMPANHA - total_cadastros} cadastros"
)

st.markdown(
f"""
<div class="hero-banner">
<div class="hero-tag-container">
<div class="hero-tag">
<span class="status-dot"></span> CENTRO DE COMANDO ELEITORAL 2026
</div>
<div style="font-size:0.8rem; color:#CBD5E1; font-weight:600;">
🔄 Atualizado em {agora}
</div>
</div>
<h1>Painel de Operações de Campo</h1>
<p>Monitoramento estratégico de mobilização, territorialidade e base de apoio em tempo real.</p>
<div class="hero-progress-wrapper">
<div style="display:flex; justify-content:space-between; align-items:center; font-size:0.88rem; color:#E2E8F0; margin-bottom:8px; font-weight:700;">
<span>Progresso da Meta Geral da Campanha</span>
<span style="font-weight:800; color:{AMBER}; font-size:1.05rem;">{pct_meta:.0f}%</span>
</div>
<div style="background:rgba(255,255,255,0.12); border-radius:12px; height:12px; overflow:hidden;">
<div style="width:{pct_meta:.0f}%; background:linear-gradient(90deg, {cor_meta} 0%, #34D399 100%); height:100%; border-radius:12px; animation: fillBar 1.1s ease-out; transition: width 0.6s ease;"></div>
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
<div class="kpi-icon-wrap">👥</div>
<div class="kpi-label">Cadastros Válidos</div>
<div class="kpi-value">{total_cadastros}</div>
</div>
<div class="kpi-card">
<div class="kpi-icon-wrap">⭐</div>
<div class="kpi-label">Líderes Ativos</div>
<div class="kpi-value">{lideres_ativos}</div>
</div>
<div class="kpi-card">
<div class="kpi-icon-wrap">📍</div>
<div class="kpi-label">Bairros Mapeados</div>
<div class="kpi-value">{bairros_cobertos}</div>
</div>
<div class="kpi-card">
<div class="kpi-icon-wrap">🚗</div>
<div class="kpi-label">Logística Dia E</div>
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
"container": {"padding": "6px", "background-color": CARD, "border": f"1px solid {BORDER}", "border-radius": "16px", "margin-bottom": "22px", "box-shadow": "0 2px 10px rgba(7, 26, 45, 0.03)"},
"icon": {"color": MUTED, "font-size": "15px"},
"nav-link": {"font-family": "Plus Jakarta Sans, sans-serif", "font-weight": "700", "font-size": "0.88rem", "color": MUTED, "text-align": "center", "border-radius": "12px", "padding": "12px 14px"},
"nav-link-selected": {"background-color": NAVY, "color": "#FFFFFF"},
},
)

==========================================
ABA 1: LIDERANÇAS
==========================================
if selected == "Lideranças":
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown(
'''
<div class="section-header-wrap">
<div class="section-title">🏆 Leaderboard de Lideranças</div>
<div class="section-subtitle">Ranking de engajamento e captação de eleitores por liderança</div>
</div>
''',
unsafe_allow_html=True
)

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
f'<div style="margin-bottom:20px; display:flex; gap:10px; flex-wrap:wrap;">'
f'<span class="chip chip-green">✅ {lideres_com_meta} de {len(df_lideres)} líderes atingiram a meta</span> '
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
legenda = "🏆 Meta Concluída" if atingiu else f"Faltam {META_POR_LIDER - row['Total']}"
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
st.markdown(
'''
<div class="section-header-wrap">
<div class="section-title">📊 Distributivo de Volume por Captador</div>
<div class="section-subtitle">Análise comparativa quantitativa do desempenho individual</div>
</div>
''',
unsafe_allow_html=True
)

fig_lider = px.bar(
df_lideres, x="Total", y="Líder", orientation="h", text="Total",
)
fig_lider.update_traces(
marker_color=[AMBER if i == 0 else BLUE for i in range(len(df_lideres))],
textposition="outside",
marker_line_width=0,
textfont=dict(size=12, color=TEXT, family=PLOTLY_FONT)
)
fig_lider.update_layout(
font_family=PLOTLY_FONT, font_color=TEXT,
xaxis_title="", yaxis_title="",
yaxis={"categoryorder": "total ascending"},
paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
margin=dict(l=0, r=20, t=10, b=10),
height=max(280, 44 * len(df_lideres)),
)
fig_lider.update_xaxes(showgrid=True, gridcolor=BORDER)
st.plotly_chart(fig_lider, use_container_width=True, config={"displayModeBar": False})
st.markdown('</div>', unsafe_allow_html=True)

==========================================
ABA 2: BAIRROS
==========================================
if selected == "Bairros":
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown(
'''
<div class="section-header-wrap">
<div class="section-title">📍 Mapeamento Territorial de Bairros</div>
<div class="section-subtitle">Localização exata e relação de apoiadores por região</div>
</div>
''',
unsafe_allow_html=True
)

if "BAIRRO_PADRAO" in df.columns:
bairros_validos = sorted(
[b for b in df["BAIRRO_PADRAO"].dropna().unique() if b not in ["NAN", "NONE", ""]]
)
col_f1, col_f2 = st.columns([2, 2])
with col_f1:
bairro_sel = st.selectbox("Filtrar por bairro", ["Todos os bairros"] + bairros_validos)
with col_f2:
busca_nome = st.text_input("Buscar por nome", placeholder="Digite um nome para localizar...")

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
with st.expander(f"📍 {b.title()} · {len(sub_df)} apoiador(es)"):
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

==========================================
ABA 3: PERFIL DEMOGRÁFICO
==========================================
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
st.markdown(
'''
<div class="section-header-wrap">
<div class="section-title">👤 Perfil Demográfico da Base</div>
<div class="section-subtitle">Proporção por gênero e média de idade do eleitorado</div>
</div>
''',
unsafe_allow_html=True
)

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
<div class="section-subtitle" style="margin-bottom:0; margin-top:6px;">{pct:.1f}% da base · Média {r['Idade_Media']} anos</div>
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
<div style="display:flex; height:12px; border-radius:10px; overflow:hidden; margin-top:20px;">
{segments}
</div>
""",
unsafe_allow_html=True,
)

media_geral = df["Idade"].mean()
if not np.isnan(media_geral):
st.markdown(
f'<div class="section-subtitle" style="margin-top:14px;">Idade média geral cadastrada: <b style="color:{NAVY}">{media_geral:.1f} anos</b></div>',
unsafe_allow_html=True,
)
st.markdown('</div>', unsafe_allow_html=True)

if "Faixa_Etaria" in df.columns:
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown(
'''
<div class="section-header-wrap">
<div class="section-title">🎂 Pirâmide Etária do Eleitorado</div>
<div class="section-subtitle">Distribuição por faixas etárias estratégicas</div>
</div>
''',
unsafe_allow_html=True
)

df_faixa = df["Faixa_Etaria"].value_counts().reset_index()
df_faixa.columns = ["Faixa Etária", "Quantidade"]
ordem = ["18-24 anos", "25-39 anos", "40-59 anos", "60+ anos", "Não informado"]
df_faixa["ordem"] = df_faixa["Faixa Etária"].apply(lambda x: ordem.index(x) if x in ordem else 99)
df_faixa = df_faixa.sort_values("ordem")

fig_faixa = px.bar(df_faixa, x="Faixa Etária", y="Quantidade", text="Quantidade")
fig_faixa.update_traces(
marker_color=BLUE,
textposition="outside",
marker_line_width=0,
textfont=dict(size=12, color=TEXT, family=PLOTLY_FONT)
)
fig_faixa.update_layout(
font_family=PLOTLY_FONT, font_color=TEXT,
xaxis_title="", yaxis_title="",
paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
margin=dict(l=0, r=0, t=10, b=10), height=320,
)
fig_faixa.update_yaxes(showgrid=True, gridcolor=BORDER)
st.plotly_chart(fig_faixa, use_container_width=True, config={"displayModeBar": False})
st.markdown('</div>', unsafe_allow_html=True)

==========================================
ABA 4: VEÍCULOS
==========================================
if selected == "Veículos":
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown(
'''
<div class="section-header-wrap">
<div class="section-title">🚗 Frota e Logística de Transporte</div>
<div class="section-subtitle">Mapeamento de veículos disponíveis para o Dia da Eleição</div>
</div>
''',
unsafe_allow_html=True
)

if not df_veiculos_filtro.empty:
bairros_com_veic = (
df_veiculos_filtro["BAIRRO_PADRAO"].replace("NAN", np.nan).nunique()
if "BAIRRO_PADRAO" in df_veiculos_filtro else 0
)
c1, c2 = st.columns(2)
c1.markdown(f'<div class="kpi-card"><div class="kpi-icon-wrap">🚙</div><div class="kpi-label">Veículos Cadastrados</div><div class="kpi-value">{len(df_veiculos_filtro)}</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="kpi-card"><div class="kpi-icon-wrap">📍</div><div class="kpi-label">Bairros Atendidos</div><div class="kpi-value">{bairros_com_veic}</div></div>', unsafe_allow_html=True)

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
<div class="person-meta">🚙 <b>{veiculo.title()}</b></div>
<div class="person-meta" style="margin-top:6px;">
<span class="chip chip-muted">📍 {bairro.title()}</span>
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
st.info("Nenhum apoiador com veículo registrado na planilha.")
st.markdown('</div>', unsafe_allow_html=True)

==========================================
ABA 5: APOIO EXTRA (ADESIVO / TRABALHO NO DIA)
==========================================
if selected == "Apoio Extra":
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown(
'''
<div class="section-header-wrap">
<div class="section-title">⭐ Força de Ação e Visibilidade</div>
<div class="section-subtitle">Apoiadores confirmados para adesivação veicular e atuação no Dia E</div>
</div>
''',
unsafe_allow_html=True
)

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
"Crie uma coluna chamada, por exemplo, ADESIVO_VEICULAR com "
"respostas Sim/Não e o painel detecta automaticamente."
)
else:
st.markdown(
f'<div class="kpi-card" style="max-width:300px;"><div class="kpi-icon-wrap">🎨</div><div class="kpi-label">Com Adesivo Instalado</div>'
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
linha_veiculo = f'<div class="person-meta">🚙 <b>{veiculo.title()}</b></div>' if veiculo and veiculo not in ("NAN", "NONE", "") else ""
st.markdown(
f"""
<div class="person-card">
<div class="person-top">
<div>
<div class="person-name">{nome}</div>
{linha_veiculo}
<div class="person-meta" style="margin-top:6px;">
<span class="chip chip-muted">📍 {bairro.title()}</span>
<span class="chip chip-blue">Líder: {lider.title()}</span>
</div>
</div>
{wa}
</div>
</div>
""",
unsafe_allow_html=True,
)
else: # Trabalho no Dia da Eleição
if "TRABALHO_DIA_PADRAO" not in df.columns:
st.warning(
"Ainda não encontrei uma coluna de trabalho no dia da eleição na planilha. "
"Crie uma coluna chamada, por exemplo, TRABALHO_DIA_ELEICAO com "
"respostas Sim/Não e o painel detecta automaticamente."
)
else:
st.markdown(
f'<div class="kpi-card" style="max-width:300px;"><div class="kpi-icon-wrap">🗳️</div><div class="kpi-label">Equipe Confirmada Dia E</div>'
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
linha_veiculo = f'<div class="person-meta">🚙 <b>{veiculo.title()}</b></div>' if veiculo and veiculo not in ("NAN", "NONE", "") else ""
st.markdown(
f"""
<div class="person-card">
<div class="person-top">
<div>
<div class="person-name">{nome}</div>
{linha_veiculo}
<div class="person-meta" style="margin-top:6px;">
<span class="chip chip-muted">📍 {bairro.title()}</span>
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

