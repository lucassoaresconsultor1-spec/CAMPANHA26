import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Campanha 2026 - Centro de Comando",
    page_icon="🚩",
    layout="wide"
)

# Estilização CSS Customizada
st.markdown("""
<style>
    .main-title {
        color: #1E3A8A;
        font-weight: 800;
        margin-bottom: 5px;
    }
    .chip {
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 5px;
        margin-bottom: 5px;
    }
    .chip-amber { background-color: #FEF3C7; color: #92400E; }
    .chip-green { background-color: #D1FAE5; color: #065F46; }
    .chip-red { background-color: #FEE2E2; color: #991B1B; }
    .chip-gray { background-color: #F3F4F6; color: #374151; }
    
    .card-veiculo {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# CARREGAMENTO E TRATAMENTO DE DADOS
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # Substitua pelo caminho correto da sua planilha Google Sheets / Excel
    file_path = "dados_campanha.xlsx"
    
    try:
        # Carrega as abas relevantes da planilha
        xls = pd.ExcelFile(file_path)
        
        df_apoiadores = pd.read_excel(xls, sheet_name=0) if len(xls.sheet_names) > 0 else pd.DataFrame()
        
        # Tenta carregar a aba de Trabalho Dia Eleição, se existir separadamente
        if "TRABALHO DIA ELEIÇÃO" in xls.sheet_names:
            df_dia_e = pd.read_excel(xls, sheet_name="TRABALHO DIA ELEIÇÃO")
        else:
            df_dia_e = df_apoiadores.copy()
            
        return df_apoiadores, df_dia_e
    except Exception as e:
        # Retorna DataFrames vazios em caso de erro na leitura local para simulação
        return pd.DataFrame(), pd.DataFrame()

df_apoiadores, df_dia_e = load_data()

# -----------------------------------------------------------------------------
# FUNÇÕES AUXILIARES DE FORMATAÇÃO E VALIDAÇÃO (CORREÇÃO DE ERROS DE TIPO)
# -----------------------------------------------------------------------------
def safe_title(val):
    """Converte e formata strings com segurança evitando AttributeError em NaN/Floats."""
    if pd.isna(val) or val is None:
        return ""
    s = str(val).strip()
    if s.upper() in ["NAN", "NONE", "NAO", "NÃO", "", "0"]:
        return ""
    return s.title()

def is_veiculo_confirmado_dia_e(row):
    """
    Verifica se o veículo/pessoa está confirmado para o trabalho no Dia E.
    Apenas retorna True se houver um 'sim' na coluna correspondente.
    """
    # Checa possíveis nomes de coluna para o trabalho no dia da eleição
    col_candidates = ["TRABALHO DIA ELEIÇÃO", "TRABALHO_DIA_ELEICAO", "DIA_E", "CONFIRMADO_DIA_E"]
    
    val_status = ""
    for col in col_candidates:
        if col in row.index and pd.notna(row[col]):
            val_status = str(row[col]).strip().lower()
            break
            
    return val_status == "sim"

# -----------------------------------------------------------------------------
# INTERFACE PRINCIPAL / DASHBOARD
# -----------------------------------------------------------------------------
st.title("Centro de Comando Eleitoral 2026")
st.subheader("Painel de Operações de Campo")

# Abas do Dashboard
tab_geral, tab_bairros, tab_frota = st.tabs(["📊 Visão Geral", "📍 Bairros", "🚗 Frota / Veículos"])

# -----------------------------------------------------------------------------
# ABA: FROTA DE VEÍCULOS (CORREÇÃO DA EXIBIÇÃO DO DIA E)
# -----------------------------------------------------------------------------
with tab_frota:
    st.header("Gestão de Frota e Mobilidade")
    
    col_search1, col_search2 = st.columns(2)
    with col_search1:
        filtro_bairro = st.selectbox("Filtrar frota por bairro", ["Todos os bairros"] + list(df_apoiadores.get("BAIRRO", pd.Series()).dropna().unique()))
    with col_search2:
        busca_veiculo = st.text_input("Filtrar por modelo de veículo ou motorista", placeholder="Ex: Gol, Fiat, João...")

    if not df_apoiadores.empty:
        df_frota = df_apoiadores.copy()
        
        # Normalização dos dados de veículo
        df_frota["VEICULO_CLEAN"] = df_frota.apply(
            lambda r: safe_title(r.get("VEICULO", r.get("VEÍCULO", r.get("MODELO", "")))), axis=1
        )
        
        # Filtra apenas registros que contenham algum veículo cadastrado
        df_frota = df_frota[df_frota["VEICULO_CLEAN"] != ""]
        
        if filtro_bairro != "Todos os bairros":
            df_frota = df_frota[df_frota["BAIRRO"] == filtro_bairro]
            
        if busca_veiculo:
            term = busca_veiculo.lower()
            df_frota = df_frota[
                df_frota["VEICULO_CLEAN"].str.lower().str.contains(term) | 
                df_frota["NOME"].astype(str).str.lower().str.contains(term)
            ]
            
        # Renderização dos Cards de Veículos em Grid
        cols_cards = st.columns(3)
        for idx, (_, row) in enumerate(df_frota.iterrows()):
            veic = row["VEICULO_CLEAN"]
            motorista = safe_title(row.get("NOME", "Não Informado"))
            lider = safe_title(row.get("LIDER", row.get("LÍDER", "Sem Líder")))
            bairro = safe_title(row.get("BAIRRO", ""))
            
            # LÓGICA DE CONFIRMAÇÃO DO DIA E
            confirmado = is_veiculo_confirmado_dia_e(row)
            
            if confirmado:
                badge_dia_e = '<span class="chip chip-green">✓ Confirmado Dia E</span>'
            else:
                badge_dia_e = '<span class="chip chip-red">✗ Não Confirmado Dia E</span>'
                
            chip_veic = f'<span class="chip chip-amber">🚗 {veic}</span>' if veic else ''
            
            card_html = f"""
            <div class="card-veiculo">
                <div style="display:flex; justify-between; align-items:center;">
                    <strong style="font-size:1.1rem;">{veic}</strong>
                    <span style="font-size:0.8rem; color:#6B7280;">{bairro}</span>
                </div>
                <div style="margin-top: 8px;">
                    <p style="margin:2px 0; font-size:0.9rem;"><strong>Motorista/Responsável:</strong> {motorista}</p>
                    <p style="margin:2px 0; font-size:0.9rem;"><strong>Líder:</strong> {lider}</p>
                </div>
                <div style="margin-top:10px;">
                    {badge_dia_e}
                </div>
            </div>
            """
            
            with cols_cards[idx % 3]:
                st.markdown(card_html, unsafe_allow_html=True)
    else:
        st.info("Nenhum dado de veículos encontrado na planilha.")

# -----------------------------------------------------------------------------
# CORREÇÃO DA LINHA 1057 (EXPLORADOR DE BAIRROS)
# -----------------------------------------------------------------------------
with tab_bairros:
    st.header("Explorador Dinâmico de Bairros")
    
    if not df_apoiadores.empty:
        # Tratamento seguro contra AttributeError na iteração
        for idx, row in df_apoiadores.iterrows():
            veic_raw = row.get("VEICULO") or row.get("VEÍCULO") or ""
            veic = safe_title(veic_raw)
            
            # Verificação com validação de tipo e string limpa
            if veic and veic.upper() not in ["NAN", "NONE", "NAO", "NÃO"]:
                veic_chip = f'<span class="chip chip-amber">{veic}</span>'
            else:
                veic_chip = ""
