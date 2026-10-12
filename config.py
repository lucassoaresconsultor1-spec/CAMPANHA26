"""Configurações gerais do painel Campanha 2026.

Altere aqui as regras do painel (meta, data da eleição, etc.).
Senhas e credenciais NUNCA ficam neste arquivo: elas vão no secrets do Streamlit.
"""
from datetime import date

# ---- Regras da campanha -------------------------------------------------
META_POR_MULTIPLICADOR = 15          # meta de cadastros de cada multiplicador
DATA_ELEICAO = date(2026, 10, 4)      # usada na contagem regressiva
DIAS_PARADO = 7                       # sem cadastro há X dias = "parado"

# ---- Segurança ----------------------------------------------------------
SENHA_DEMO = "demo2026"              # só funciona no MODO DEMONSTRAÇÃO
MINUTOS_INATIVIDADE = 30              # sai sozinho após X minutos sem uso
TENTATIVAS_POR_SESSAO = 5             # erros seguidos antes de bloquear
BLOQUEIO_SESSAO_MIN = 5               # minutos de bloqueio da sessão
TENTATIVAS_GLOBAIS = 20               # erros somando todos os acessos...
JANELA_GLOBAL_MIN = 15                # ...dentro desta janela de minutos
BLOQUEIO_GLOBAL_MIN = 15              # bloqueia o login de todos por X min

# ---- Dados --------------------------------------------------------------
TTL_DADOS_SEG = 60                    # a planilha é relida a cada 60 s

ABAS_PADRAO = {
    "respostas": "Respostas ao formulário 1",
    "equipe": "EQUIPE",
    "bairros": "BAIRROS",
    "secoes": "SECOES",
}
