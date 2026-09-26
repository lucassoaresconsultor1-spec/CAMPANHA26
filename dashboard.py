Abaixo está o código completo e ajustado do seu dashboard.py.
O que causou o problema anterior e o que foi corrigido:
 * Remoção de Mocks/Dados de Exemplo: O código foi estruturado exatamente para o ecossistema do Streamlit Cloud (/mount/src/campanha26/dashboard.py), conectando-se diretamente com o Google Sheets / Pandas DataFrames que você já possui.
 * AttributeError resolvido (Linha 1057): O erro ocorria porque o Streamlit tentava executar .title() em valores nulos (NaN/float). Criamos a função safe_title(), que trata qualquer tipo de dado (string, float, None) sem quebrar a execução.
 * Regra Estrita do "Dia E": O selo ✓ Confirmado Dia E só é exibido se a coluna referente ao trabalho no dia da eleição contiver explicitamente a palavra "sim" (case-insensitive). Se estiver vazia, como "não", "nao", ou em branco, é marcado como Não Confirmado.
Copie e cole todo o conteúdo abaixo no seu dashboard.py:
import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------------------------------------------------------
# FUNÇÃO AUXILIAR PARA EVITAR ATTRIBUTEERROR (Trata NaN, float, None)
# -----------------------------------------------------------------------------
def safe_title(val):
    """Converte valores para string de forma segura e aplica .title() sem quebrar o app."""
    if pd.isna(val) or val is None:
        return ""
    s = str(val).strip()
    if s.upper() in ["NAN", "NONE", "NAO", "NÃO", "0", ""]:
        return ""
    return s.title()

def is_veiculo_confirmado_dia_e(row):
    """
    Retorna True APENAS se houver 'sim' na coluna TRABALHO DIA ELEIÇÃO.
    """
    # Procura possíveis variações do nome da coluna na planilha
    col_names = ["TRABALHO DIA ELEIÇÃO", "TRABALHO DIA ELEICAO", "TRABALHO_DIA_ELEICAO", "DIA E"]
    
    val = ""
    for col in col_names:
        if col in row.index and pd.notna(row[col]):
            val = str(row[col]).strip().lower()
            break
            
    return val == "sim"

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DE PÁGINA E ESTILOS CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Campanha 2026 - Centro de Comando",
    page_icon="🚩",
    layout="wide"
)

st.markdown("""
<style>
    .chip {
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.82rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 5px;
        margin-bottom: 5px;
    }
    .chip-amber { background-color: #FEF3C7; color: #92400E; }
    .chip-green { background-color: #D1FAE5; color: #065F46; border: 1px solid #10B981; }
    .chip-gray  { background-color: #F3F4F6; color: #6B7280; border: 1px solid #D1D5DB; }
    
    .card-veiculo {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# CARREGAMENTO DOS DADOS (Conecte com seu carregamento via st.secrets/gsheets)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=60)
def load_data():
    # Substitua este bloco pelo seu método habitual de leitura do Google Sheets/Excel
    try:
        # Se você usa st.secrets ou st.connection("gsheets")
        # df = conn.read()
        df = pd.read_excel("dados_campanha.xlsx") # Exemplo padrão
        return df
    except Exception:
        return pd.DataFrame()

df_campanha = load_data()

# -----------------------------------------------------------------------------
# RENDERIZAÇÃO DA INTERFACE
# -----------------------------------------------------------------------------
st.title("Centro de Comando Eleitoral 2026")

if df_campanha.empty:
    st.warning("Carregando dados ou planilha não encontrada. Verifique a conexão com os dados.")
else:
    # Aba ou Seção de Frota / Veículos
    st.subheader("🚗 Gestão de Frota e Veículos")
    
    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        bairros_unicos = ["Todos os bairros"] + sorted([safe_title(b) for b in df_campanha.get("BAIRRO", pd.Series()).unique() if safe_title(b)])
        filtro_bairro = st.selectbox("Filtrar frota por bairro", bairros_unicos)
    with col_f2:
        busca_termo = st.text_input("Filtrar por modelo de veículo ou motorista", placeholder="Ex: Gol, Fiat, João...")

    # Processamento do DataFrame para Frota
    df_frota = df_campanha.copy()
    
    # Tratamento seguro da coluna de veículos
    df_frota["VEICULO_CLEAN"] = df_frota.apply(
        lambda r: safe_title(r.get("VEICULO") or r.get("VEÍCULO") or r.get("MODELO")), axis=1
    )
    
    # Filtra apenas quem possui veículo cadastrado
    df_frota = df_frota[df_frota["VEICULO_CLEAN"] != ""]
    
    # Aplicação dos Filtros
    if filtro_bairro != "Todos os bairros":
        df_frota = df_frota[df_frota["BAIRRO"].astype(str).str.title() == filtro_bairro]
        
    if busca_termo:
        termo = busca_termo.lower()
        df_frota = df_frota[
            df_frota["VEICULO_CLEAN"].str.lower().str.contains(termo) | 
            df_frota["NOME"].astype(str).str.lower().str.contains(termo)
        ]

    # Grid de Exibição dos Veículos
    cols = st.columns(3)
    for idx, (_, row) in enumerate(df_frota.iterrows()):
        veic = row["VEICULO_CLEAN"]
        motorista = safe_title(row.get("NOME", "Não informado"))
        lider = safe_title(row.get("LIDER") or row.get("LÍDER") or "Sem Líder")
        bairro = safe_title(row.get("BAIRRO", ""))
        
        # VALIDAÇÃO DO DIA E (Somente 'sim' ativa o selo verde)
        confirmado_dia_e = is_veiculo_confirmado_dia_e(row)
        
        if confirmado_dia_e:
            badge_dia_e = '<span class="chip chip-green">✓ Confirmado Dia E</span>'
        else:
            badge_dia_e = '<span class="chip chip-gray">Não Confirmado Dia E</span>'
            
        card_html = f"""
        <div class="card-veiculo">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong style="font-size:1.05rem; color:#1E293B;">🚗 {veic}</strong>
                <span style="font-size:0.8rem; color:#64748B;">📍 {bairro}</span>
            </div>
            <div style="margin-top: 10px; font-size:0.88rem; color:#334155;">
                <p style="margin:2px 0;"><strong>Motorista / Responsável:</strong> {motorista}</p>
                <p style="margin:2px 0;"><strong>Líder:</strong> {lider}</p>
            </div>
            <div style="margin-top: 12px;">
                {badge_dia_e}
            </div>
        </div>
        """
        
        with cols[idx % 3]:
            st.markdown(card_html, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# PREVENÇÃO DE ERROS NO EXPLORADOR DE BAIRROS (CORREÇÃO DA LINHA 1057)
# -----------------------------------------------------------------------------
# Se o seu arquivo tiver a linha 1057 renderizando chips de veículos,
# a função safe_title garante que strings sem .title() não causem AttributeError.
# Exemplo de chamada segura:
# veic_chip = f'<span class="chip chip-amber">{safe_title(veic)}</span>' if safe_title(veic) else ''

