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
# Paleta pensada para um "centro de comando" de campo: base sóbria em
# azul-marinho (confiança/institucional), cartões neutros e UM único
# acento (âmbar) reservado para destacar o topo do ranking e alertas.
NAVY = "#0F2942"
NAVY_SOFT = "#16385A"
BLUE = "#1D5FA6"
AMBER = "#E3A23C"
GREEN = "#2E9E6D"
BG = "#F4F6F9"
CARD = "#FFFFFF"
TEXT = "#1B2430"
MUTED = "#6B7686"
BORDER = "#E4E8EE"

PLOTLY_FONT = "Manrope, sans-serif"

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

        .stApp {{
            background: {BG};
        }}

        .block-container {{
            padding-top: 1rem;
            padding-bottom: 3rem;
            max-width: 1200px;
        }}

        /* ---------- Cabeçalho ---------- */
        .hero {{
            background: linear-gradient(135deg, {NAVY} 0%, {NAVY_SOFT} 100%);
            border-radius: 18px;
            padding: 28px 28px 24px 28px;
            color: white;
            margin-bottom: 22px;
        }}
        .hero .eyebrow {{
            color: {AMBER};
            font-weight: 700;
            font-size: 0.82rem;
            letter-spacing: 0.2px;
            margin-bottom: 4px;
        }}
        .hero h1 {{
            margin: 0;
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.15;
        }}
        .hero p {{
            margin-top: 6px;
            color: #C7D3E0;
            font-size: 0.92rem;
        }}

        /* ---------- Grid de indicadores ---------- */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 14px;
            margin-bottom: 8px;
        }}
        @media (max-width: 680px) {{
            .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .hero h1 {{ font-size: 1.5rem; }}
            .hero {{ padding: 20px 18px; }}
        }}
        .kpi-card {{
            background: {CARD};
            border: 1px solid {BORDER};
            border-radius: 14px;
            padding: 16px 18px;
        }}
        .kpi-card .kpi-label {{
            color: {MUTED};
            font-size: 0.8rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .kpi-card .kpi-value {{
            color: {TEXT};
            font-size: 1.9rem;
            font-weight: 800;
            margin-top: 4px;
        }}

        /* ---------- Cartão de seção ---------- */
        .section-card {{
            background: {CARD};
            border: 1px solid {BORDER};
            border-radius: 14px;
            padding: 20px 22px;
            margin-bottom: 18px;
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

        /* ---------- Ranking de líderes ---------- */
        .rank-row {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 0;
            border-bottom: 1px solid {BORDER};
        }}
        .rank-row:last-child {{ border-bottom: none; }}
        .rank-badge {{
            width: 26px;
            height: 26px;
            min-width: 26px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 0.78rem;
            background: #EEF1F5;
            color: {MUTED};
        }}
        .rank-badge.top {{
            background: {AMBER};
            color: white;
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
        }}
        .rank-bar-fill.top {{ background: {AMBER}; }}
        .rank-bar-fill.meta-ok {{ background: {GREEN}; }}
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
        .chip-amber {{ background: #FCF1DF; color: #A9701C; }}
        .chip-muted {{ background: #EEF1F5; color: {MUTED}; }}

        /* ---------- Cartão de pessoa (bairro / veículo) ---------- */
        .person-card {{
            border: 1px solid {BORDER};
            border-radius: 12px;
            padding: 12px 14px;
            margin-bottom: 8px;
            background: {CARD};
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
        }}

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
        <div class="hero" style="max-width:420px; margin:60px auto 0 auto; text-align:center;">
            <div class="eyebrow">ACESSO RESTRITO</div>
            <h1 style="font-size:1.5rem;">Campanha 2026</h1>
            <p>Digite a senha da equipe para entrar no painel de campo.</p>
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
                <div style="width:{pct_meta:.0f}%; background:{cor_meta}; height:100%; border-radius:8px;"></div>
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
    options=["Lideranças", "Bairros", "Perfil", "Veículos"],
    icons=["people-fill", "geo-alt-fill", "bullseye", "car-front-fill"],
    orientation="horizontal",
    styles={
        "container": {"padding": "4px", "background-color": CARD, "border": f"1px solid {BORDER}", "border-radius": "12px", "margin-bottom": "18px"},
        "icon": {"color": MUTED, "font-size": "14px"},
        "nav-link": {"font-family": "Manrope, sans-serif", "font-weight": "700", "font-size": "0.85rem", "color": MUTED, "text-align": "center", "border-radius": "9px", "padding": "10px 8px"},
        "nav-link-selected": {"background-color": "#E7F0FA", "color": BLUE},
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

        rows_html = ""
        for i, row in df_lideres.iterrows():
            rank = i + 1
            is_top = "top" if rank == 1 else ""
            atingiu = row["Total"] >= META_POR_LIDER
            largura = min(row["Total"] / META_POR_LIDER * 100, 100) if META_POR_LIDER else 0
            cor_barra = "meta-ok" if atingiu else ""
            legenda = "🏆 meta batida" if atingiu else f"faltam {META_POR_LIDER - row['Total']}"
            rows_html += f"""
            <div class="rank-row">
                <div class="rank-badge {is_top}">{rank}</div>
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
            margin=dict(l=0, r=10, t=10, b=10),
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
