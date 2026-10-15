"""Campanha 2026 · Centro de Comando — painel completo em UM arquivo.

Para atualizar o painel, basta trocar este arquivo no GitHub.
Modo demonstração: funciona sem configurar nada (senha demo2026).
Modo planilha: configure o Secrets do Streamlit (veja o LEIA-ME).
"""
from __future__ import annotations


class _Modulo:
    """Atalho interno: C., P., R., S. e ui. apontam para este mesmo arquivo."""

    def __getattr__(self, nome):
        try:
            return globals()[nome]
        except KeyError as erro:
            raise AttributeError(nome) from erro

    def __setattr__(self, nome, valor):
        globals()[nome] = valor


C = P = R = S = ui = _Modulo()


# ===========================================================================
# CONFIG
# ===========================================================================
from datetime import date

# ---- Regras da campanha -------------------------------------------------
VERSAO = "1.3"
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


# ===========================================================================
# SEGURANCA
# ===========================================================================
import hashlib
import hmac
import secrets
import threading
import time

ITERACOES = 600_000


def gerar_hash(senha: str, iteracoes: int = ITERACOES) -> str:
    sal = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), bytes.fromhex(sal), iteracoes)
    return f"pbkdf2_sha256${iteracoes}${sal}${dk.hex()}"


def conferir_senha(senha: str, hash_salvo: str) -> bool:
    try:
        algoritmo, iteracoes, sal, esperado = hash_salvo.strip().split("$")
        if algoritmo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), bytes.fromhex(sal), int(iteracoes))
        return hmac.compare_digest(dk.hex(), esperado)
    except (ValueError, AttributeError):
        return False


class Limitador:
    """Conta erros de senha de TODOS os acessos (protege contra tentativa e erro)."""

    def __init__(self, maximo: int, janela_min: int, bloqueio_min: int):
        self.maximo = maximo
        self.janela = janela_min * 60
        self.bloqueio = bloqueio_min * 60
        self._falhas = []
        self._bloqueado_ate = 0.0
        self._trava = threading.Lock()

    def segundos_bloqueado(self) -> int:
        with self._trava:
            return max(0, int(self._bloqueado_ate - time.time()))

    def registrar_falha(self):
        agora = time.time()
        with self._trava:
            self._falhas = [t for t in self._falhas if agora - t < self.janela] + [agora]
            if len(self._falhas) >= self.maximo:
                self._bloqueado_ate = agora + self.bloqueio
                self._falhas = []


# ===========================================================================
# PROCESSAMENTO
# ===========================================================================
import re
import unicodedata
from datetime import date, timedelta

import pandas as pd


SEM_LIDER = "Sem líder definido"
SEM_MULT = "Sem multiplicador"
NAO_INFORMADO = "Não informado"

VALORES_SIM = {"SIM", "S", "YES", "Y", "X", "TRUE", "VERDADEIRO", "1", "OK"}
VALORES_NAO = {"", "NAO", "N", "NO", "FALSE", "FALSO", "0", "NENHUM", "NEHUM", "NAO POSSUI", "NAO TENHO", "-"}

FAIXAS = ["16–17", "18–24", "25–34", "35–44", "45–59", "60+"]

CORES_HEX = {
    "BRANCO": "#F8FAFC", "BRANCA": "#F8FAFC", "PRATA": "#C0C7D1", "PRATEADO": "#C0C7D1",
    "PRETO": "#111827", "PRETA": "#111827", "CINZA": "#6B7280", "GRAFITE": "#4B5563",
    "VERMELHO": "#DC2626", "VERMELHA": "#DC2626", "VINHO": "#7F1D1D", "AZUL": "#2563EB",
    "VERDE": "#16A34A", "AMARELO": "#FACC15", "AMARELA": "#FACC15", "BEGE": "#D6C7A1",
    "MARROM": "#7C4A2D", "LARANJA": "#F97316", "DOURADO": "#D4AF37", "ROSA": "#F472B6",
}


# ---------------------------------------------------------------------------
# Texto
# ---------------------------------------------------------------------------
def sem_acento(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))


def texto(v) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except (TypeError, ValueError):
        pass
    s = str(v).strip()
    return "" if s.upper() in {"NAN", "NONE", "NAT", "NULL", "<NA>"} else s


def chave(v) -> str:
    s = sem_acento(texto(v)).upper()
    s = re.sub(r"[^A-Z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def chave_col(v) -> str:
    return re.sub(r"[^A-Z0-9]", "", sem_acento(str(v)).upper())


_PARTICULAS = {"DA", "DE", "DO", "DAS", "DOS", "E", "DI", "DU"}


def nome_bonito(v) -> str:
    s = re.sub(r"\s+", " ", texto(v))
    if not s:
        return ""
    partes = []
    for i, p in enumerate(s.split(" ")):
        up = sem_acento(p).upper()
        if i > 0 and up in _PARTICULAS:
            partes.append(p.lower())
        elif re.fullmatch(r"[IVX]{1,4}", up) and up not in {"I"}:
            partes.append(p.upper())
        else:
            partes.append(p[:1].upper() + p[1:].lower())
    return " ".join(partes)


def modelo_bonito(v) -> str:
    s = re.sub(r"\s+", " ", texto(v))
    out = []
    for p in s.split(" "):
        if not p:
            continue
        if any(ch.isdigit() for ch in p) or len(p) <= 2:
            out.append(p.upper())
        elif p.isupper() or p.islower():
            out.append(p[:1].upper() + p[1:].lower())
        else:
            out.append(p)
    return " ".join(out)


def so_digitos(v) -> str:
    return re.sub(r"\D", "", texto(v))


# ---------------------------------------------------------------------------
# Documentos e contatos
# ---------------------------------------------------------------------------
def cpf_valido(d: str) -> bool:
    if len(d) != 11 or len(set(d)) == 1:
        return False
    nums = [int(c) for c in d]
    for pos in (9, 10):
        soma = sum(n * w for n, w in zip(nums[:pos], range(pos + 1, 1, -1)))
        r = (soma * 10) % 11
        if (0 if r == 10 else r) != nums[pos]:
            return False
    return True


def mascarar_cpf(d: str) -> str:
    if len(d) != 11:
        return d and "inválido"
    return f"***.{d[3:6]}.{d[6:9]}-**"


def mascarar_titulo(d: str) -> str:
    if len(d) < 4:
        return d
    return "•" * (len(d) - 4) + d[-4:]


def normalizar_telefone(v) -> str:
    d = so_digitos(v)
    if d.startswith("55") and len(d) in (12, 13):
        d = d[2:]
    if d.startswith("0") and len(d) in (11, 12):
        d = d[1:]
    return d


def telefone_formatado(d: str) -> str:
    if len(d) == 11:
        return f"({d[:2]}) {d[2:7]}-{d[7:]}"
    if len(d) == 10:
        return f"({d[:2]}) {d[2:6]}-{d[6:]}"
    return d


def link_whatsapp(d: str) -> str:
    return f"https://wa.me/55{d}" if len(d) in (10, 11) else ""


def eh_sim(v) -> bool:
    k = chave(v)
    return k in VALORES_SIM or k.startswith("SIM")


def formatar_placa(v) -> str:
    p = re.sub(r"[^A-Z0-9]", "", sem_acento(texto(v)).upper())
    if re.fullmatch(r"[A-Z]{3}\d{4}", p):
        return f"{p[:3]}-{p[3:]}"
    return p


# ---------------------------------------------------------------------------
# Datas
# ---------------------------------------------------------------------------
_FORMATOS = [
    "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y",
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d",
    "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%y",
]


def parse_datas(serie: pd.Series) -> pd.Series:
    s = serie.map(texto)
    out = pd.Series([pd.NaT] * len(s), index=s.index, dtype="datetime64[ns]")
    for fmt in _FORMATOS:
        falta = out.isna() & s.ne("")
        if not falta.any():
            break
        conv = pd.to_datetime(s[falta], format=fmt, errors="coerce")
        ok = conv.notna()
        if ok.any():
            out.loc[conv[ok].index] = conv[ok].astype("datetime64[ns]")
    return out


def idade_em(nasc: date, hoje: date):
    if nasc is None or pd.isna(nasc):
        return None
    anos = hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))
    return anos if 16 <= anos <= 110 else None


def faixa_etaria(idade) -> str:
    if idade is None or pd.isna(idade):
        return NAO_INFORMADO
    idade = int(idade)
    if idade < 18:
        return "16–17"
    if idade < 25:
        return "18–24"
    if idade < 35:
        return "25–34"
    if idade < 45:
        return "35–44"
    if idade < 60:
        return "45–59"
    return "60+"


def normalizar_sexo(v) -> str:
    k = chave(v)
    if k in {"F", "FEM"} or k.startswith("FEMIN") or k.startswith("MULHER"):
        return "Feminino"
    if k in {"M", "H", "MASC"} or k.startswith("MASCUL") or k.startswith("HOMEM"):
        return "Masculino"
    return NAO_INFORMADO


# ---------------------------------------------------------------------------
# Mapeamento flexível das colunas do formulário
# ---------------------------------------------------------------------------
MAPA_RESPOSTAS = [
    ("DATA", ["CARIMBODEDATAHORA", "CARIMBO", "DATAHORA", "TIMESTAMP", "DATADOCADASTRO"], []),
    ("MULTIPLICADOR", ["MULTIPLICADOR"], []),
    ("LIDER", ["LIDER", "LIDERANCA", "INDICACAO"], ["MULTIPLICADOR"]),
    ("NOME", ["NOMECOMPLETO", "NOMEDOELEITOR", "NOMEDOAPOIADOR", "NOME"],
     ["MAE", "PAI", "MULTIPLICADOR", "LIDER", "MOTORISTA", "LOCAL"]),
    ("TITULO", ["TITULODEELEITOR", "TITULO"], []),
    ("CPF", ["CPF"], []),
    ("NASCIMENTO", ["DATADENASCIMENTO", "NASCIMENTO", "DATANASC", "NASC"], []),
    ("SEXO", ["SEXO", "GENERO"], []),
    ("CONTATO", ["WHATSAPP", "CELULAR", "TELEFONE", "CONTATO", "ZAP", "FONE"], ["MULTIPLICADOR", "LIDER"]),
    ("BAIRRO", ["BAIRRO"], []),
    ("SECAO", ["NUMERODASECAO", "SECAO"], []),
    ("LOCAL", ["LOCALDEVOTACAO", "LOCAL"], []),
    ("POSSUI_VEICULO", ["POSSUIVEICULO", "TEMVEICULO", "POSSUICARRO", "VEICULO"], ["MODELO", "COR", "PLACA"]),
    ("MODELO", ["MODELODOVEICULO", "MODELO"], []),
    ("COR", ["CORDOVEICULO", "COR"], []),
    ("PLACA", ["PLACA"], []),
    ("APOIOS", ["COMOPODEAPOIAR", "APOIOS", "APOIO"], []),
    ("ADESIVO", ["ADESIVO"], []),
    ("BANDEIRA", ["BANDEIRA"], []),
    ("DIA_E", ["TRABALHONODIADAELEICAO", "TRABALHODIA", "DIADAELEICAO", "DIAE", "MESARIO"], []),
]
MAPA_EQUIPE = [
    ("MULTIPLICADOR", ["MULTIPLICADOR", "NOME"], ["LIDER"]),
    ("CONTATO_LIDER", ["WHATSAPPDOLIDER", "TELEFONEDOLIDER", "CELULARDOLIDER", "CONTATODOLIDER", "WHATSAPPLIDER"], []),
    ("LIDER", ["LIDER", "LIDERANCA"], ["WHATSAPP", "TELEFONE", "CELULAR", "CONTATO"]),
    ("CONTATO", ["WHATSAPP", "CELULAR", "TELEFONE", "CONTATO"], ["LIDER"]),
]
MAPA_SECOES = [
    ("SECAO", ["SECAO", "NUMERO"], []),
    ("LOCAL", ["LOCALDEVOTACAO", "LOCAL", "ESCOLA"], []),
    ("BAIRRO", ["BAIRRO", "REGIAO"], []),
    ("MAPA", ["LINKDOMAPA", "MAPA", "LINK", "MAPS"], []),
]
_SEM_CONTEM = {"COR", "DIAE", "ZAP", "NOME"}


def mapear_colunas(colunas, regras):
    colunas = list(colunas)
    norm = {c: chave_col(c) for c in colunas}
    usados, mapa = set(), {}
    for canon, padroes, excl in regras:
        achou = None
        for modo in ("igual", "comeca", "contem"):
            for p in padroes:
                for c in colunas:
                    if c in usados:
                        continue
                    n = norm[c]
                    if any(e in n for e in excl):
                        continue
                    if (modo == "igual" and n == p) or (modo == "comeca" and n.startswith(p)) or (
                            modo == "contem" and p not in _SEM_CONTEM and p in n):
                        achou = c
                        break
                if achou:
                    break
            if achou:
                break
        if achou:
            mapa[canon] = achou
            usados.add(achou)
    return mapa


def _limpar_tabela(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or len(df.columns) == 0:
        return pd.DataFrame()
    df = df.copy()
    nomes, vistos = [], {}
    for c in df.columns:
        c = texto(c) or "coluna"
        vistos[c] = vistos.get(c, 0) + 1
        nomes.append(c if vistos[c] == 1 else f"{c} ({vistos[c]})")
    df.columns = nomes
    df = df.reset_index(drop=True)
    for c in df.columns:
        df[c] = df[c].map(texto)
    return df


# ---------------------------------------------------------------------------
# Preparação da base
# ---------------------------------------------------------------------------
def preparar(brutos: dict, hoje: date | None = None) -> dict:
    hoje = hoje or date.today()
    avisos = []

    resp = _limpar_tabela(brutos.get("respostas"))
    eq_raw = _limpar_tabela(brutos.get("equipe"))
    ba_raw = _limpar_tabela(brutos.get("bairros"))
    se_raw = _limpar_tabela(brutos.get("secoes"))

    # ---- EQUIPE ----
    eq_map = mapear_colunas(eq_raw.columns, MAPA_EQUIPE) if len(eq_raw) else {}
    equipe_rows = []
    if "MULTIPLICADOR" in eq_map and "LIDER" in eq_map:
        for _, r in eq_raw.iterrows():
            m = nome_bonito(r[eq_map["MULTIPLICADOR"]])
            lid = nome_bonito(r[eq_map["LIDER"]])
            if not m:
                continue
            tel = normalizar_telefone(r[eq_map["CONTATO"]]) if "CONTATO" in eq_map else ""
            tel_l = normalizar_telefone(r[eq_map["CONTATO_LIDER"]]) if "CONTATO_LIDER" in eq_map else ""
            equipe_rows.append({"MULT": m, "MULT_KEY": chave(m), "LIDER": lid or SEM_LIDER,
                                "LIDER_KEY": chave(lid) or chave(SEM_LIDER), "WA": link_whatsapp(tel),
                                "TEL_FMT": telefone_formatado(tel), "LIDER_WA": link_whatsapp(tel_l)})
    elif len(eq_raw):
        avisos.append("A aba EQUIPE precisa das colunas Multiplicador e Líder.")
    else:
        avisos.append("Aba EQUIPE não encontrada ou vazia: os líderes vêm só do formulário.")
    equipe = pd.DataFrame(equipe_rows, columns=["MULT", "MULT_KEY", "LIDER", "LIDER_KEY", "WA", "TEL_FMT", "LIDER_WA"])
    # WhatsApp do líder: coluna própria na EQUIPE ou a linha em que o líder é o próprio multiplicador
    wa_lider = {}
    for r in equipe.itertuples():
        if r.LIDER_WA and r.LIDER_KEY not in wa_lider:
            wa_lider[r.LIDER_KEY] = r.LIDER_WA
    for r in equipe.itertuples():
        if r.MULT_KEY == r.LIDER_KEY and r.WA and r.LIDER_KEY not in wa_lider:
            wa_lider[r.LIDER_KEY] = r.WA
    equipe = equipe.drop_duplicates("MULT_KEY", keep="first").reset_index(drop=True)
    mult_info = {r.MULT_KEY: r for r in equipe.itertuples()}

    # ---- BAIRROS ----
    bairros_oficiais = []
    if len(ba_raw.columns):
        col = ba_raw.columns[0]
        for v in ba_raw[col]:
            b = texto(v)
            if b and chave(b) not in {chave(x) for x in bairros_oficiais}:
                bairros_oficiais.append(b)
    bairro_oficial = {chave(b): b for b in bairros_oficiais}

    # ---- SECOES ----
    secoes = pd.DataFrame(columns=["SECAO", "LOCAL", "BAIRRO", "MAPA"])
    if len(se_raw):
        se_map = mapear_colunas(se_raw.columns, MAPA_SECOES)
        if "SECAO" in se_map:
            secoes = pd.DataFrame({
                "SECAO": se_raw[se_map["SECAO"]].map(lambda v: str(int(so_digitos(v))) if so_digitos(v) else ""),
                "LOCAL": se_raw[se_map["LOCAL"]] if "LOCAL" in se_map else "",
                "BAIRRO": se_raw[se_map["BAIRRO"]] if "BAIRRO" in se_map else "",
                "MAPA": se_raw[se_map["MAPA"]] if "MAPA" in se_map else "",
            })
            secoes = secoes[secoes.SECAO.ne("")].drop_duplicates("SECAO")
    secao_info = {r.SECAO: r for r in secoes.itertuples()}

    # ---- RESPOSTAS ----
    mapa = mapear_colunas(resp.columns, MAPA_RESPOSTAS)
    if len(resp) and "NOME" not in mapa:
        avisos.append("Não encontrei a coluna de nome no formulário (ex.: 'Nome completo').")
    if len(resp) and "MULTIPLICADOR" not in mapa and "LIDER" not in mapa:
        avisos.append("Não encontrei a coluna 'Multiplicador' no formulário.")

    def col(canon):
        if canon in mapa:
            return resp[mapa[canon]]
        return pd.Series([""] * len(resp), index=resp.index, dtype=object)

    vazia = resp.apply(lambda r: not any(r.values), axis=1) if len(resp) else pd.Series(dtype=bool)
    cad = pd.DataFrame(index=resp.index)
    cad["LINHA"] = resp.index + 2  # linha real na planilha (linha 1 = cabeçalho)
    cad["DATA"] = parse_datas(col("DATA"))

    # Multiplicador / líder
    mult_raw = col("MULTIPLICADOR") if "MULTIPLICADOR" in mapa else col("LIDER")
    cad["MULT_KEY"] = mult_raw.map(chave)
    lider_form = col("LIDER").map(nome_bonito) if ("LIDER" in mapa and "MULTIPLICADOR" in mapa) else None

    mults, lideres, lkeys, mwa = [], [], [], []
    for i, k in zip(cad.index, cad["MULT_KEY"]):
        info = mult_info.get(k)
        if info is not None:
            mults.append(info.MULT)
            lideres.append(info.LIDER)
            lkeys.append(info.LIDER_KEY)
            mwa.append(info.WA)
            continue
        m = nome_bonito(mult_raw[i]) or SEM_MULT
        lid = lider_form[i] if lider_form is not None and lider_form[i] else ""
        if not lid and "MULTIPLICADOR" not in mapa:
            lid = m
        lid = lid or SEM_LIDER
        mults.append(m)
        lideres.append(lid)
        lkeys.append(chave(lid))
        mwa.append("")
    cad["MULT"] = mults
    cad["LIDER"] = lideres
    cad["LIDER_KEY"] = lkeys
    cad["MULT_WA"] = mwa
    cad.loc[cad.MULT_KEY.eq(""), "MULT_KEY"] = chave(SEM_MULT)

    # Pessoa
    cad["NOME"] = col("NOME").map(nome_bonito)
    cad["NOME_KEY"] = cad["NOME"].map(chave)
    cad["CPF"] = col("CPF").map(so_digitos)
    cad["CPF_OK"] = cad["CPF"].map(cpf_valido)
    cad["TITULO"] = col("TITULO").map(so_digitos)
    cad["TITULO_OK"] = cad["TITULO"].str.len().eq(12)
    nasc = parse_datas(col("NASCIMENTO"))
    cad["NASC"] = [d.date() if pd.notna(d) else None for d in nasc]
    cad["IDADE"] = [idade_em(d, hoje) for d in cad["NASC"]]
    cad.loc[cad["IDADE"].isna(), "NASC"] = None
    cad["FAIXA"] = cad["IDADE"].map(faixa_etaria)
    cad["SEXO"] = col("SEXO").map(normalizar_sexo)

    tel = col("CONTATO").map(normalizar_telefone)
    cad["TEL"] = tel
    cad["TEL_OK"] = tel.str.len().isin([10, 11])
    cad["WA"] = tel.map(link_whatsapp)
    cad["TEL_FMT"] = tel.map(telefone_formatado)

    bairro_raw = col("BAIRRO")
    cad["BAIRRO"] = [bairro_oficial.get(chave(b), nome_bonito(b)) or NAO_INFORMADO for b in bairro_raw]
    cad["BAIRRO_KEY"] = cad["BAIRRO"].map(chave)

    cad["SECAO"] = col("SECAO").map(lambda v: str(int(so_digitos(v))) if so_digitos(v) else "")
    local_form = col("LOCAL").map(texto) if "LOCAL" in mapa else None
    locais, mapas = [], []
    for i, s in zip(cad.index, cad["SECAO"]):
        info = secao_info.get(s)
        if info is not None:
            locais.append(texto(info.LOCAL))
            mapas.append(texto(info.MAPA))
        else:
            locais.append(local_form[i] if local_form is not None else "")
            mapas.append("")
    cad["LOCAL"] = locais
    cad["MAPA"] = mapas

    # Veículo
    possui = col("POSSUI_VEICULO")
    modelo = col("MODELO")
    if "MODELO" not in mapa:  # formato antigo: modelo escrito na própria pergunta
        modelo = possui.map(lambda v: "" if (chave(v) in VALORES_NAO or eh_sim(v)) else v)
    cad["MODELO"] = modelo.map(modelo_bonito)
    cad["VEICULO"] = [eh_sim(p) or (bool(m) and chave(m) not in VALORES_NAO) for p, m in zip(possui, cad["MODELO"])]
    cad["COR"] = col("COR").map(nome_bonito)
    cad["COR_HEX"] = cad["COR"].map(lambda c: CORES_HEX.get(chave(c).split(" ")[0] if c else "", ""))
    cad["PLACA"] = col("PLACA").map(formatar_placa)

    # Apoios
    apoios = col("APOIOS").map(chave)
    cad["ADESIVO"] = apoios.str.contains("ADESIVO") | col("ADESIVO").map(eh_sim)
    cad["BANDEIRA"] = apoios.str.contains("BANDEIR") | col("BANDEIRA").map(eh_sim)
    cad["DIA_E"] = (apoios.str.contains("TRABALH") | apoios.str.contains("DIA DA ELEI")
                    | col("DIA_E").map(eh_sim))

    for c in ["CPF_OK", "TITULO_OK", "TEL_OK", "VEICULO", "ADESIVO", "BANDEIRA", "DIA_E"]:
        cad[c] = cad[c].fillna(False).astype(bool)
    for c in ["MULT_KEY", "MULT", "LIDER", "LIDER_KEY", "MULT_WA", "NOME", "NOME_KEY", "CPF", "TITULO", "SEXO", "TEL",
              "WA", "TEL_FMT", "BAIRRO", "BAIRRO_KEY", "SECAO", "LOCAL", "MAPA", "MODELO", "COR", "COR_HEX", "PLACA", "FAIXA"]:
        cad[c] = cad[c].astype(object).where(cad[c].notna(), "").astype(str)
    cad["DATA"] = pd.to_datetime(cad["DATA"], errors="coerce")
    cad["IDADE"] = pd.to_numeric(cad["IDADE"], errors="coerce")

    if len(cad):
        cad = cad[~vazia.reindex(cad.index, fill_value=False).astype(bool)]
        cad = cad[cad["NOME"].ne("") | cad["MULT_KEY"].ne(chave(SEM_MULT))]
    cad = cad.reset_index(drop=True)

    # Multiplicadores que aparecem no formulário mas não estão na EQUIPE
    fora = []
    if len(equipe):
        conhecidos = set(equipe.MULT_KEY)
        for k, g in cad.groupby("MULT_KEY"):
            if k not in conhecidos:
                fora.append({"MULT": g.MULT.iloc[0], "QTD": len(g)})
        fora.sort(key=lambda x: -x["QTD"])

    return {
        "cadastros": cad,
        "equipe": equipe,
        "bairros": bairros_oficiais,
        "secoes": secoes,
        "mapa_colunas": mapa,
        "avisos": avisos,
        "fora_equipe": fora,
        "wa_lider": wa_lider,
        "hoje": hoje,
    }


# ---------------------------------------------------------------------------
# Lideranças
# ---------------------------------------------------------------------------
def ranking_liderancas(base: dict, meta: int = META_POR_MULTIPLICADOR, dias_parado: int = DIAS_PARADO) -> list:
    cad, equipe, hoje = base["cadastros"], base["equipe"], base["hoje"]
    grupos = {k: g.sort_values("DATA", ascending=False, na_position="last") for k, g in cad.groupby("MULT_KEY")}

    universo = {}
    for r in equipe.itertuples():
        universo[r.MULT_KEY] = {"nome": r.MULT, "lider": r.LIDER, "lider_key": r.LIDER_KEY,
                                "wa": r.WA, "tel": r.TEL_FMT}
    for k, g in grupos.items():
        if k not in universo:
            universo[k] = {"nome": g.MULT.iloc[0], "lider": g.LIDER.iloc[0],
                           "lider_key": g.LIDER_KEY.iloc[0], "wa": "", "tel": ""}

    vazio = cad.iloc[0:0]
    por_lider = {}
    for k, info in universo.items():
        g = grupos.get(k, vazio)
        total = len(g)
        ultimo = g["DATA"].max() if total else pd.NaT
        dias_sem = (hoje - ultimo.date()).days if pd.notna(ultimo) else None
        ok = total >= meta
        parado = (not ok) and (total == 0 or dias_sem is None or dias_sem >= dias_parado)
        m = {
            "nome": info["nome"], "key": k, "lider": info["lider"], "lider_key": info["lider_key"],
            "wa": info["wa"], "tel": info["tel"], "total": total, "meta": meta,
            "pct": round(total / meta * 100) if meta else 0, "ok": ok, "parado": parado,
            "dias_sem": dias_sem, "ultimo": ultimo, "pessoas": g,
        }
        por_lider.setdefault(info["lider_key"], {"nome": info["lider"], "key": info["lider_key"], "mults": []})
        por_lider[info["lider_key"]]["mults"].append(m)

    lideres = []
    for lk, d in por_lider.items():
        mults = sorted(d["mults"], key=lambda x: (-x["total"], x["nome"]))
        total = sum(x["total"] for x in mults)
        meta_l = len(mults) * meta
        lideres.append({
            "nome": d["nome"], "key": lk, "mults": mults, "wa": base.get("wa_lider", {}).get(lk, ""), "total": total, "meta": meta_l,
            "pct": round(total / meta_l * 100) if meta_l else 0,
            "n_mult": len(mults), "na_meta": sum(1 for x in mults if x["ok"]),
            "parados": sum(1 for x in mults if x["parado"]),
        })
    lideres.sort(key=lambda x: (x["key"] == chave(SEM_LIDER), -x["total"], x["nome"]))
    for i, lid in enumerate(lideres, start=1):
        lid["pos"] = i
    return lideres


def serie_semanal(cad: pd.DataFrame, hoje: date, semanas: int = 8) -> list:
    datas = cad["DATA"].dropna().dt.date
    out = []
    for i in range(semanas):
        fim = hoje - timedelta(days=7 * (semanas - 1 - i))
        ini = fim - timedelta(days=6)
        n = int(((datas >= ini) & (datas <= fim)).sum())
        out.append({"ini": ini, "fim": fim, "n": n, "rotulo": ini.strftime("%d/%m")})
    return out


def serie_campanha(cad: pd.DataFrame, hoje: date, maximo: int = 52) -> list:
    """Série semanal desde o primeiro cadastro (no mínimo 8 semanas, no máximo `maximo`)."""
    datas = cad["DATA"].dropna()
    if datas.empty:
        return serie_semanal(cad, hoje)
    semanas = (hoje - datas.min().date()).days // 7 + 1
    return serie_semanal(cad, hoje, max(8, min(semanas, maximo)))


def ritmo_recente(cad: pd.DataFrame, hoje: date, dias: int = 14, n: int = 10) -> list:
    """Multiplicadores que mais cadastraram nos últimos `dias` dias."""
    recentes = cad[cad["DATA"].notna() & (cad["DATA"].dt.date > hoje - timedelta(days=dias))]
    if recentes.empty:
        return []
    cont = recentes.groupby(["MULT", "LIDER"]).size().reset_index(name="total")
    cont = cont.sort_values(["total", "MULT"], ascending=[False, True]).head(n)
    return [{"nome": r.MULT, "lider": r.LIDER, "total": int(r.total)} for r in cont.itertuples()]


# ---------------------------------------------------------------------------
# Bairros, perfil, veículos
# ---------------------------------------------------------------------------
def resumo_bairros(base: dict) -> tuple:
    cad = base["cadastros"]
    linhas = []
    for b, g in cad.groupby("BAIRRO"):
        vc = g["LIDER"].value_counts()
        linhas.append({
            "bairro": b, "total": len(g), "lideres": g["LIDER_KEY"].nunique(),
            "mults": g["MULT_KEY"].nunique(), "veiculos": int(g["VEICULO"].sum()),
            "lider_top": vc.index[0] if len(vc) else "", "lider_top_n": int(vc.iloc[0]) if len(vc) else 0,
        })
    df = pd.DataFrame(linhas, columns=["bairro", "total", "lideres", "mults", "veiculos", "lider_top", "lider_top_n"])
    df = df.sort_values(["total", "bairro"], ascending=[False, True]).reset_index(drop=True)
    com = set(df["bairro"].map(chave))
    sem = [b for b in base["bairros"] if chave(b) not in com]
    return df, sem


def perfil(base: dict) -> dict:
    cad = base["cadastros"]
    total = len(cad)
    sexos = {}
    for s in ["Masculino", "Feminino", NAO_INFORMADO]:
        g = cad[cad.SEXO.eq(s)]
        idades = pd.to_numeric(g["IDADE"], errors="coerce").dropna()
        sexos[s] = {"n": len(g), "pct": (len(g) / total * 100) if total else 0,
                    "media": float(idades.mean()) if len(idades) else None}
    idades = pd.to_numeric(cad["IDADE"], errors="coerce").dropna()
    piramide = []
    for f in FAIXAS:
        piramide.append({"faixa": f,
                         "m": int(((cad.FAIXA == f) & (cad.SEXO == "Masculino")).sum()),
                         "f": int(((cad.FAIXA == f) & (cad.SEXO == "Feminino")).sum()),
                         "total": int((cad.FAIXA == f).sum())})
    return {
        "total": total, "sexos": sexos,
        "media_geral": float(idades.mean()) if len(idades) else None,
        "mediana": float(idades.median()) if len(idades) else None,
        "piramide": piramide,
        "sem_idade": int(cad["IDADE"].isna().sum()),
    }


def aniversariantes(cad: pd.DataFrame, hoje: date, dias: int = 7) -> list:
    out = []
    for r in cad.itertuples():
        n = r.NASC
        if n is None or pd.isna(n):
            continue
        for ano in (hoje.year, hoje.year + 1):
            try:
                aniv = date(ano, n.month, n.day)
            except ValueError:  # 29/02 em ano não bissexto
                aniv = date(ano, 2, 28)
            if aniv >= hoje:
                break
        falta = (aniv - hoje).days
        if falta < dias:
            out.append({"nome": r.NOME, "data": aniv, "faltam": falta, "idade": aniv.year - n.year,
                        "wa": r.WA, "bairro": r.BAIRRO, "mult": r.MULT, "lider": r.LIDER})
    out.sort(key=lambda x: (x["faltam"], x["nome"]))
    return out


def top_locais(cad: pd.DataFrame, n: int = 8) -> list:
    g = cad[cad.LOCAL.ne("")].groupby("LOCAL").agg(total=("LOCAL", "size"), bairro=("BAIRRO", lambda s: s.mode().iat[0]))
    g = g.sort_values("total", ascending=False).head(n)
    return [{"local": i, "total": int(r.total), "bairro": r.bairro} for i, r in g.iterrows()]


def resumo_veiculos(base: dict) -> dict:
    cad = base["cadastros"]
    v = cad[cad.VEICULO]
    por_bairro = (v.groupby("BAIRRO").size().sort_values(ascending=False)
                  .reset_index(name="total").rename(columns={"BAIRRO": "bairro"}))
    por_lider = (v.groupby("LIDER").size().sort_values(ascending=False)
                 .reset_index(name="total").rename(columns={"LIDER": "lider"}))
    return {"df": v, "total": len(v), "bairros": int(v.BAIRRO.nunique()),
            "dia_e": int(v.DIA_E.sum()), "adesivo": int(v.ADESIVO.sum()),
            "pct": (len(v) / len(cad) * 100) if len(cad) else 0,
            "por_bairro": por_bairro, "por_lider": por_lider}


# ---------------------------------------------------------------------------
# Duplicatas
# ---------------------------------------------------------------------------
def encontrar_duplicatas(cad: pd.DataFrame) -> list:
    n = len(cad)
    if n == 0:
        return []
    pai = list(range(n))

    def raiz(i):
        while pai[i] != i:
            pai[i] = pai[pai[i]]
            i = pai[i]
        return i

    def unir(a, b):
        ra, rb = raiz(a), raiz(b)
        if ra != rb:
            pai[rb] = ra

    df = cad.reset_index(drop=True).copy()
    df["_TEL8"] = df["TEL"].where(df["TEL_OK"], "").str[-8:]

    def grupos_por(coluna, cond):
        return [set(g.index) for _, g in df[cond].groupby(coluna) if len(g) > 1]

    # 1) Critérios fortes (podem indicar a MESMA pessoa): CPF, título e nome
    fortes = [
        ("CPF", grupos_por("CPF", df["CPF"].str.len().eq(11) & df["CPF"].map(lambda d: len(set(d)) > 1))),
        ("Título", grupos_por("TITULO", df["TITULO"].str.len().ge(10) & df["TITULO"].map(lambda d: len(set(d)) > 1))),
        ("Nome", grupos_por("NOME_KEY", df["NOME_KEY"].str.count(" ").ge(1))),
    ]
    achados = []
    for nome_crit, conjuntos in fortes:
        for pos in conjuntos:
            ordem = sorted(pos)
            for p in ordem[1:]:
                unir(ordem[0], p)
            achados.append((nome_crit, pos))
    clusters = {}
    for _, pos in achados:
        for p in pos:
            clusters.setdefault(raiz(p), set()).add(p)
    crits_por_raiz = {}
    for nome_crit, pos in achados:
        lista = crits_por_raiz.setdefault(raiz(next(iter(pos))), [])
        if nome_crit not in lista:
            lista.append(nome_crit)

    # 2) Telefone: sozinho costuma ser família; vira grupo próprio de confiança baixa
    so_telefone = []
    for pos in grupos_por("_TEL8", df["_TEL8"].str.len().eq(8)):
        raizes = {raiz(p) for p in pos}
        r0 = next(iter(raizes))
        if len(raizes) == 1 and r0 in clusters and pos <= clusters[r0]:
            if "Telefone" not in crits_por_raiz[r0]:
                crits_por_raiz[r0].append("Telefone")
        else:
            so_telefone.append(pos)

    ordem_conf = {"Alta": 0, "Média": 1, "Baixa": 2}
    grupos = []

    def montar(membros, crits, conf):
        g = df.loc[sorted(membros)].sort_values("DATA", na_position="last")
        grupos.append({
            "criterios": crits, "confianca": conf, "membros": g,
            "conflito": g["LIDER_KEY"].nunique() > 1,
            "mesmo_mult": g["MULT_KEY"].nunique() == 1,
            "linhas": list(g["LINHA"]),
        })

    for r, membros in clusters.items():
        crits = crits_por_raiz.get(r, [])
        if "CPF" in crits or "Título" in crits:
            conf = "Alta"
        else:
            nasc = df.loc[sorted(membros), "NASC"].dropna()
            conf = "Alta" if len(nasc) and nasc.duplicated().any() else "Média"
        montar(membros, crits, conf)
    for pos in so_telefone:
        montar(pos, ["Telefone"], "Baixa")
    grupos.sort(key=lambda x: (ordem_conf[x["confianca"]], -len(x["membros"]), x["linhas"][0]))
    return grupos


def linhas_duplicadas(grupos: list, confiancas=("Alta",)) -> set:
    """Linhas da planilha que estão em grupos de duplicata (exceto o 1º cadastro)."""
    out = set()
    for g in grupos:
        if g["confianca"] in confiancas:
            out.update(g["linhas"][1:])
    return out


def qualidade(base: dict) -> dict:
    cad = base["cadastros"]
    return {
        "sem_cpf": int(cad.CPF.eq("").sum()),
        "cpf_invalido": int((cad.CPF.ne("") & ~cad.CPF_OK).sum()),
        "titulo_invalido": int((cad.TITULO.ne("") & ~cad.TITULO_OK).sum()),
        "sem_titulo": int(cad.TITULO.eq("").sum()),
        "tel_invalido": int((~cad.TEL_OK).sum()),
        "sem_nasc": int(cad.IDADE.isna().sum()),
        "sem_sexo": int(cad.SEXO.eq(NAO_INFORMADO).sum()),
        "sem_secao": int(cad.SECAO.eq("").sum()),
        "sem_bairro": int(cad.BAIRRO.eq(NAO_INFORMADO).sum()),
        "fora_equipe": base.get("fora_equipe", []),
    }


# ---------------------------------------------------------------------------
# Formatação numérica (padrão brasileiro)
# ---------------------------------------------------------------------------
def fmt_int(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def fmt_dec(x, casas: int = 1) -> str:
    if x is None or pd.isna(x):
        return "—"
    return f"{x:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ===========================================================================
# DEMO
# ===========================================================================
import random
from datetime import date, datetime, timedelta
from urllib.parse import quote_plus

import pandas as pd

COLUNAS_RESPOSTAS = [
    "Carimbo de data/hora",
    "Multiplicador",
    "Nome completo",
    "Título de eleitor",
    "CPF",
    "Data de nascimento",
    "Sexo",
    "WhatsApp",
    "Bairro",
    "Número da seção",
    "Possui veículo?",
    "Modelo do veículo",
    "Cor do veículo",
    "Placa",
    "Como pode apoiar?",
    "Consentimento (LGPD)",
]

OPCAO_ADESIVO = "Adesivo no veículo"
OPCAO_BANDEIRA = "Bandeira"
OPCAO_DIA_E = "Trabalho no dia da eleição"

LIDERES = [
    "Bebeto", "Ana Paula", "Marcos Vinícius", "Rose", "Diego",
    "Jorge", "Cida", "Paulinho", "Tereza", "Washington",
    "Kelly", "Robson", "Neide", "Fabiano", "Sandra Lúcia",
]
# força de cada liderança (deixa o ranking variado)
FORCA_LIDER = [1.25, 1.15, 1.1, 1.05, 1.0, 1.0, 0.95, 0.95, 0.9, 0.9, 0.85, 0.8, 0.75, 0.65, 0.55]

# Lista de exemplo — confira e ajuste com a lista oficial de bairros.
BAIRROS = [
    ("Centro", 10), ("Parque Hotel", 6), ("Iguabinha", 6), ("Praia Seca", 5),
    ("Bananeiras", 5), ("Coqueiral", 4), ("Areal", 4), ("Pontinha", 4),
    ("Ponte dos Leites", 4), ("Outeiro", 3), ("Mataruna", 3), ("Fazendinha", 3),
    ("São Vicente de Paulo", 3), ("Hospício", 3), ("Vila Capri", 2), ("Parati", 2),
    ("Morro Grande", 2), ("Barbudo", 2), ("XV de Novembro", 2), ("Viaduto", 2),
    ("Rio do Limão", 1), ("Três Vendas", 1), ("Sobradinho", 0), ("Boa Perna", 0),
]

NOMES_M = [
    "Lucas", "Jean", "Carlos", "Rafael", "Thiago", "Wellington", "Roberto", "Márcio",
    "Felipe", "Renato", "Igor", "Paulo", "Vitor", "Edson", "Gustavo", "Leandro",
    "André", "Hugo", "Sérgio", "Fábio", "Otávio", "José", "Antônio", "Francisco",
    "João", "Pedro", "Luiz", "Marcelo", "Ricardo", "Eduardo", "Rodrigo", "Leonardo",
    "Bruno", "Daniel", "Mateus", "Gabriel", "Alexandre", "Fernando", "Sebastião",
    "Raimundo", "Manoel", "Cláudio", "Adriano", "Wagner", "Anderson", "Rogério",
    "Valdir", "Gilberto", "Mário", "Davi", "Samuel", "Caio", "Vinícius", "Diogo",
    "Emerson", "Juliano", "Nelson", "Ronaldo", "Severino", "Josias",
]
NOMES_F = [
    "Fernanda", "Patrícia", "Bruna", "Juliana", "Camila", "Sandra", "Luana", "Débora",
    "Simone", "Aline", "Kátia", "Cláudia", "Mônica", "Tânia", "Priscila", "Viviane",
    "Larissa", "Elaine", "Raquel", "Sílvia", "Maria", "Ana", "Francisca", "Antônia",
    "Adriana", "Márcia", "Aparecida", "Luciana", "Vanessa", "Jéssica", "Letícia",
    "Beatriz", "Gabriela", "Rosângela", "Cristiane", "Eliane", "Fátima", "Rita", "Vera",
    "Lúcia", "Helena", "Isabela", "Carla", "Daniela", "Tatiane", "Josiane", "Rosana",
    "Michele", "Regina", "Sônia", "Natália", "Amanda", "Bianca", "Rafaela", "Sueli",
    "Neusa", "Ivone", "Marlene", "Edna", "Graça",
]
SOBRENOMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira",
    "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho", "Almeida", "Lopes",
    "Fernandes", "Vieira", "Barbosa", "Rocha", "Dias", "Nascimento", "Andrade",
    "Moreira", "Nunes", "Marques", "Machado", "Mendes", "Freitas", "Cardoso", "Ramos",
    "Gonçalves", "Santana", "Teixeira", "Moraes", "Correia", "Pinto", "Cavalcanti",
    "Monteiro", "Batista", "Campos", "Azevedo", "Reis", "Matos", "Siqueira", "Coelho",
    "Brito", "Pacheco", "Quintanilha", "Viana",
]

MODELOS = [
    ("Gol", 8), ("Onix", 8), ("HB20", 7), ("Ka", 6), ("Palio", 5), ("Uno", 6),
    ("Strada", 4), ("Saveiro", 3), ("Fiesta", 3), ("Sandero", 4), ("Argo", 3),
    ("Mobi", 4), ("Kwid", 4), ("Celta", 4), ("Fox", 3), ("Corolla", 2), ("Civic", 1),
    ("Hilux", 1), ("Spin", 2), ("Prisma", 3), ("CG 160", 4), ("Biz", 2),
]
CORES = [("Branco", 8), ("Prata", 8), ("Preto", 6), ("Cinza", 5), ("Vermelho", 3),
         ("Azul", 2), ("Bege", 1), ("Verde", 1)]

TIPOS_LOCAL = ["Escola Municipal", "Colégio Estadual", "Centro Educacional", "Escola Estadual", "CIEP"]

FAIXAS_IDADE = [((16, 17), 3), ((18, 24), 13), ((25, 34), 19), ((35, 44), 20), ((45, 59), 26), ((60, 84), 19)]


def _peso(rng, itens):
    valores = [i for i, _ in itens]
    pesos = [p for _, p in itens]
    return rng.choices(valores, weights=pesos, k=1)[0]


def _cpf(rng, valido=True, pontuado=True):
    base = [rng.randint(0, 9) for _ in range(9)]
    if len(set(base)) == 1:
        base[0] = (base[0] + 1) % 10

    def dv(nums):
        soma = sum(n * w for n, w in zip(nums, range(len(nums) + 1, 1, -1)))
        r = (soma * 10) % 11
        return 0 if r == 10 else r

    d1 = dv(base)
    d2 = dv(base + [d1])
    nums = base + [d1, d2]
    if not valido:
        nums[-1] = (nums[-1] + 1) % 10
    s = "".join(str(n) for n in nums)
    return f"{s[:3]}.{s[3:6]}.{s[6:9]}-{s[9:]}" if pontuado else s


def _titulo(rng, valido=True):
    corpo = "".join(str(rng.randint(0, 9)) for _ in range(8)) + "03" + "".join(str(rng.randint(0, 9)) for _ in range(2))
    if not valido:
        corpo = corpo[:-1]
    if rng.random() < 0.5:
        return f"{corpo[:4]} {corpo[4:8]} {corpo[8:]}"
    return corpo


def _telefone(rng, usados):
    # Prefixo 900xx: números claramente fictícios
    while True:
        meio = f"900{rng.randint(0, 99):02d}"
        fim = f"{rng.randint(0, 9999):04d}"
        if (meio, fim) not in usados:
            usados.add((meio, fim))
            break
    estilo = rng.random()
    if estilo < 0.6:
        return f"(22) {meio}-{fim}"
    if estilo < 0.85:
        return f"22{meio}{fim}"
    return f"22 {meio} {fim}"


def _placa(rng):
    letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    l3 = "".join(rng.choice(letras) for _ in range(3))
    if rng.random() < 0.7:
        return f"{l3}{rng.randint(0, 9)}{rng.choice(letras)}{rng.randint(0, 99):02d}"
    return f"{l3}-{rng.randint(0, 9999):04d}"


def _nome(rng, sexo):
    pool = NOMES_F if sexo == "F" else NOMES_M
    primeiro = rng.choice(pool)
    if rng.random() < 0.25:
        segundo = rng.choice(pool)
        if segundo != primeiro:
            primeiro = f"{primeiro} {segundo}"
    s1, s2 = rng.sample(SOBRENOMES, 2)
    if rng.random() < 0.3:
        s1 = rng.choice(["da Silva", "dos Santos", "de Souza", "da Costa", "de Oliveira", "da Rocha", "dos Reis",
                         "de Almeida", "do Nascimento", "de Freitas"])
    return f"{primeiro} {s1} {s2}"


def gerar_demo(seed=2026, hoje=None):
    """Retorna um dict com as 4 abas brutas (DataFrames de texto)."""
    rng = random.Random(seed)
    hoje = hoje or date.today()
    agora = datetime.combine(hoje, datetime.min.time()) + timedelta(hours=19)

    # ---- SECOES ---------------------------------------------------------
    secoes, secoes_por_bairro = [], {}
    numero = 1
    homenageados = set()
    for bairro, peso in BAIRROS:
        n_locais = 1 if peso <= 2 else (2 if peso <= 5 else 3)
        for _ in range(n_locais):
            while True:
                tit = rng.choice(["Prof.", "Prof.ª", "Dr.", "", ""])
                pessoa = rng.choice(NOMES_F if tit == "Prof.ª" else NOMES_M + NOMES_F)
                nome_local = f"{rng.choice(TIPOS_LOCAL)} {tit + ' ' if tit else ''}{pessoa} {rng.choice(SOBRENOMES)}"
                if nome_local not in homenageados:
                    homenageados.add(nome_local)
                    break
            mapa = "https://www.google.com/maps/search/?api=1&query=" + quote_plus(f"{nome_local}, {bairro}, Araruama RJ")
            for _ in range(rng.randint(3, 7)):
                secoes.append({"Seção": str(numero), "Local de votação": nome_local, "Bairro": bairro, "Link do mapa": mapa})
                secoes_por_bairro.setdefault(bairro, []).append(numero)
                numero += 1

    bairros_ativos = [(b, p) for b, p in BAIRROS if p > 0]

    # ---- EQUIPE ---------------------------------------------------------
    usados_nomes, usados_tel = set(), set()
    equipe, plano = [], []
    for i_lider, lider in enumerate(LIDERES):
        tel_lider = _telefone(rng, usados_tel)
        n_mult = rng.randint(5, 10)
        for j in range(n_mult):
            if lider == "Bebeto" and j < 3:
                nome_mult = ["Lucas Andrade", "Jean Carvalho", "Carlos Mendes"][j]
            else:
                while True:
                    sx = rng.choice("MF")
                    nome_mult = f"{rng.choice(NOMES_F if sx == 'F' else NOMES_M)} {rng.choice(SOBRENOMES)}"
                    if nome_mult not in usados_nomes:
                        break
            usados_nomes.add(nome_mult)
            equipe.append({"Multiplicador": nome_mult, "Líder": lider, "WhatsApp": _telefone(rng, usados_tel),
                           "WhatsApp do líder": tel_lider})

            r = rng.random()
            if r < 0.10:
                n = rng.randint(0, 3)
            elif r < 0.30:
                n = rng.randint(4, 9)
            elif r < 0.70:
                n = rng.randint(10, 15)
            elif r < 0.92:
                n = rng.randint(15, 20)
            else:
                n = rng.randint(21, 28)
            n = max(0, round(n * FORCA_LIDER[i_lider]))
            if lider == "Bebeto" and j < 3:
                n = [24, 21, 18][j]
            inicio = hoje - timedelta(days=rng.randint(55, 84))
            if rng.random() < 0.15:
                fim = hoje - timedelta(days=rng.randint(8, 24))
            else:
                fim = hoje - timedelta(days=rng.randint(0, 3))
            plano.append({"mult": nome_mult, "n": n, "inicio": inicio, "fim": fim,
                          "casa": _peso(rng, bairros_ativos)})

    # Multiplicador que ainda não foi lançado na aba EQUIPE (para o alerta)
    plano.append({"mult": "Josué Martins", "n": 4, "inicio": hoje - timedelta(days=20),
                  "fim": hoje - timedelta(days=2), "casa": "Areal"})

    # ---- RESPOSTAS ------------------------------------------------------
    linhas = []
    for p in plano:
        dias = max(1, (p["fim"] - p["inicio"]).days)
        for k in range(p["n"]):
            u = 1.0 if k == 0 else rng.random() ** 0.55  # o último cadastro cai no fim da atividade
            dia = p["inicio"] + timedelta(days=int(u * dias))
            momento = datetime.combine(dia, datetime.min.time()) + timedelta(
                hours=rng.randint(8, 21), minutes=rng.randint(0, 59), seconds=rng.randint(0, 59))
            momento = min(momento, agora)

            sexo = "F" if rng.random() < 0.53 else "M"
            faixa = _peso(rng, FAIXAS_IDADE)
            idade = rng.randint(faixa[0], faixa[1])
            nasc = hoje - timedelta(days=int(idade * 365.25) + rng.randint(1, 360))
            bairro = p["casa"] if rng.random() < 0.6 else _peso(rng, bairros_ativos)
            secao = rng.choice(secoes_por_bairro[bairro])

            tem_veiculo = rng.random() < 0.22
            apoios = []
            if tem_veiculo and rng.random() < 0.5:
                apoios.append(OPCAO_ADESIVO)
            if rng.random() < 0.12:
                apoios.append(OPCAO_BANDEIRA)
            if rng.random() < (0.35 if tem_veiculo else 0.12):
                apoios.append(OPCAO_DIA_E)

            cpf_r = rng.random()
            cpf = "" if cpf_r < 0.01 else _cpf(rng, valido=cpf_r >= 0.03, pontuado=rng.random() < 0.6)
            tel = _telefone(rng, usados_tel) if rng.random() > 0.01 else "22 9912"

            linhas.append({
                "_t": momento,
                "Carimbo de data/hora": momento.strftime("%d/%m/%Y %H:%M:%S"),
                "Multiplicador": p["mult"],
                "Nome completo": _nome(rng, sexo) if rng.random() > 0.08 else _nome(rng, sexo).upper(),
                "Título de eleitor": _titulo(rng, valido=rng.random() > 0.01),
                "CPF": cpf,
                "Data de nascimento": "" if rng.random() < 0.03 else nasc.strftime("%d/%m/%Y"),
                "Sexo": "" if rng.random() < 0.02 else ("Feminino" if sexo == "F" else "Masculino"),
                "WhatsApp": tel,
                "Bairro": bairro if rng.random() > 0.05 else bairro.upper(),
                "Número da seção": str(secao),
                "Possui veículo?": "Sim" if tem_veiculo else "Não",
                "Modelo do veículo": _peso(rng, MODELOS) if tem_veiculo else "",
                "Cor do veículo": _peso(rng, CORES) if tem_veiculo else "",
                "Placa": _placa(rng) if tem_veiculo else "",
                "Como pode apoiar?": ", ".join(apoios),
                "Consentimento (LGPD)": "Sim, autorizo",
            })

    # ---- Duplicatas propositais (para a aba Duplicatas) ------------------
    mults_por_lider = {}
    for e in equipe:
        mults_por_lider.setdefault(e["Líder"], []).append(e["Multiplicador"])
    lider_de = {e["Multiplicador"]: e["Líder"] for e in equipe}

    def outro_mult(mult):
        lider = lider_de.get(mult)
        lideres = [lid for lid in LIDERES if lid != lider]
        return rng.choice(mults_por_lider[rng.choice(lideres)])

    base = list(linhas)
    extras = []
    for _ in range(8):   # mesma pessoa cadastrada por outra liderança
        orig = rng.choice(base)
        c = dict(orig)
        c["Multiplicador"] = outro_mult(orig["Multiplicador"])
        c["_t"] = min(orig["_t"] + timedelta(days=rng.randint(1, 12), hours=rng.randint(0, 5)), agora)
        c["Nome completo"] = orig["Nome completo"].upper() if rng.random() < 0.5 else orig["Nome completo"]
        extras.append(c)
    for _ in range(4):   # mesmo multiplicador enviou duas vezes
        orig = rng.choice(base)
        c = dict(orig)
        c["_t"] = min(orig["_t"] + timedelta(minutes=rng.randint(1, 9)), agora)
        extras.append(c)
    for _ in range(4):   # homônimo (mesmo nome, outra pessoa)
        orig = rng.choice(base)
        c = dict(rng.choice(base))
        c["Nome completo"] = orig["Nome completo"]
        c["CPF"] = _cpf(rng)
        c["Título de eleitor"] = _titulo(rng)
        c["WhatsApp"] = _telefone(rng, usados_tel)
        c["_t"] = min(orig["_t"] + timedelta(days=rng.randint(1, 20)), agora)
        extras.append(c)
    for _ in range(4):   # família com o mesmo telefone
        orig = rng.choice(base)
        sexo = rng.choice("MF")
        c = dict(orig)
        c["Nome completo"] = _nome(rng, sexo)
        c["Sexo"] = "Feminino" if sexo == "F" else "Masculino"
        c["CPF"] = _cpf(rng)
        c["Título de eleitor"] = _titulo(rng)
        c["Data de nascimento"] = (hoje - timedelta(days=rng.randint(18 * 365, 70 * 365))).strftime("%d/%m/%Y")
        c["_t"] = min(orig["_t"] + timedelta(days=rng.randint(0, 6), hours=1), agora)
        extras.append(c)
    for c in extras:
        c["Carimbo de data/hora"] = c["_t"].strftime("%d/%m/%Y %H:%M:%S")

    todas = sorted(linhas + extras, key=lambda r: r["_t"])
    respostas = pd.DataFrame([{k: r[k] for k in COLUNAS_RESPOSTAS} for r in todas], columns=COLUNAS_RESPOSTAS)

    return {
        "respostas": respostas,
        "equipe": pd.DataFrame(equipe, columns=["Multiplicador", "Líder", "WhatsApp", "WhatsApp do líder"]),
        "bairros": pd.DataFrame({"Bairro": [b for b, _ in BAIRROS]}),
        "secoes": pd.DataFrame(secoes, columns=["Seção", "Local de votação", "Bairro", "Link do mapa"]),
    }


# ===========================================================================
# RELATORIOS
# ===========================================================================
import re
from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

AZUL = colors.HexColor("#2563EB")
MARINHO = colors.HexColor("#0B1C42")
CINZA = colors.HexColor("#5B6B85")
LINHA = colors.HexColor("#D7E0EE")
ZEBRA = colors.HexColor("#F3F6FB")


def _data_fmt(v) -> str:
    if v is None or pd.isna(v):
        return ""
    return pd.Timestamp(v).strftime("%d/%m/%Y %H:%M")


def _sim(v) -> str:
    return "Sim" if bool(v) else ""


def mascarar_tel(t: str) -> str:
    """(22) 90012-3456 -> (22) 9••••-3456"""
    t = str(t or "")
    d = re.sub(r"\D", "", t)
    if len(d) < 8:
        return t
    return f"({d[:2]}) {'9' if len(d) == 11 else ''}••••-{d[-4:]}"


def _tel(t, sensivel: bool) -> str:
    return t if sensivel else mascarar_tel(t)


def _nasc(n) -> str:
    try:
        return n.strftime("%d/%m/%Y") if n is not None and not pd.isna(n) else ""
    except (AttributeError, ValueError):
        return ""


# ---------------------------------------------------------------------------
# Excel
# ---------------------------------------------------------------------------
def _escritor(buf):
    # strings_to_formulas=False impede que um texto começando com "=" vire fórmula
    return pd.ExcelWriter(buf, engine="xlsxwriter",
                          engine_kwargs={"options": {"strings_to_formulas": False, "strings_to_urls": False}})


def _planilha(writer, df: pd.DataFrame, nome: str, larguras: dict | None = None):
    df.to_excel(writer, sheet_name=nome, index=False)
    wb, ws = writer.book, writer.sheets[nome]
    cab = wb.add_format({"bold": True, "font_color": "#FFFFFF", "bg_color": "#2563EB", "border": 0,
                         "valign": "vcenter"})
    for i, c in enumerate(df.columns):
        ws.write(0, i, c, cab)
        largura = (larguras or {}).get(c)
        if largura is None:
            amostra = df[c].astype(str).head(300)
            largura = min(48, max(10, len(str(c)) + 2, (amostra.map(len).max() if len(amostra) else 0) + 2))
        ws.set_column(i, i, largura)
    ws.freeze_panes(1, 0)
    if len(df.columns):
        ws.autofilter(0, 0, max(len(df), 1), len(df.columns) - 1)
    ws.set_row(0, 22)


def _nome_aba(texto: str, usados: set) -> str:
    base = re.sub(r"[\[\]:*?/\\]", "", texto)[:31] or "Aba"
    nome, i = base, 2
    while nome.lower() in usados:
        sufixo = f" {i}"
        nome = base[:31 - len(sufixo)] + sufixo
        i += 1
    usados.add(nome.lower())
    return nome


def _linhas_pessoas(lideres: list, sensivel: bool = False) -> pd.DataFrame:
    linhas = []
    for lid in lideres:
        for pos_m, m in enumerate(lid["mults"], start=1):
            for p in m["pessoas"].itertuples():
                linha = {
                    "Pos. líder": lid["pos"], "Líder": lid["nome"], "Pos. multiplicador": pos_m,
                    "Multiplicador": m["nome"], "Nome": p.NOME, "WhatsApp": _tel(p.TEL_FMT, sensivel),
                    "Bairro": p.BAIRRO, "Seção": p.SECAO, "Local de votação": p.LOCAL,
                    "Data do cadastro": _data_fmt(p.DATA), "Linha na planilha": p.LINHA,
                }
                if sensivel:
                    linha.update({"CPF": p.CPF, "Título": p.TITULO, "Nascimento": _nasc(p.NASC)})
                linhas.append(linha)
    colunas = ["Pos. líder", "Líder", "Pos. multiplicador", "Multiplicador", "Nome", "WhatsApp", "Bairro", "Seção",
               "Local de votação", "Data do cadastro", "Linha na planilha"]
    if sensivel:
        colunas += ["CPF", "Título", "Nascimento"]
    return pd.DataFrame(linhas, columns=colunas)


def excel_liderancas(lideres: list, sensivel: bool = False) -> bytes:
    resumo = pd.DataFrame([{
        "Posição": lid["pos"], "Líder": lid["nome"], "Multiplicadores": lid["n_mult"],
        "Cadastros": lid["total"], "Meta": lid["meta"], "% da meta": lid["pct"],
        "Multiplicadores na meta": lid["na_meta"], "Multiplicadores parados": lid["parados"],
    } for lid in lideres])
    mults = pd.DataFrame([{
        "Pos. líder": lid["pos"], "Líder": lid["nome"], "Multiplicador": m["nome"], "Cadastros": m["total"],
        "Meta": m["meta"], "% da meta": m["pct"],
        "Situação": "Meta batida" if m["ok"] else ("Parado" if m["parado"] else f"Faltam {m['meta'] - m['total']}"),
        "Dias sem cadastrar": "" if m["dias_sem"] is None else m["dias_sem"], "WhatsApp": _tel(m["tel"], sensivel),
    } for lid in lideres for m in lid["mults"]])
    pessoas = _linhas_pessoas(lideres, sensivel)

    buf = BytesIO()
    with _escritor(buf) as w:
        _planilha(w, resumo, "Resumo")
        _planilha(w, mults, "Multiplicadores")
        _planilha(w, pessoas, "Cadastros")
        usados = {"resumo", "multiplicadores", "cadastros"}
        for lid in lideres:
            sub = pessoas[pessoas["Líder"].eq(lid["nome"])].drop(columns=["Pos. líder", "Líder"])
            _planilha(w, sub, _nome_aba(f"{lid['pos']:02d} {lid['nome']}", usados))
    return buf.getvalue()


def _df_veiculos(v: pd.DataFrame, ordem_bairros: list, sensivel: bool = False) -> pd.DataFrame:
    pos = {b: i for i, b in enumerate(ordem_bairros)}
    v = v.assign(_o=v["BAIRRO"].map(pos)).sort_values(["_o", "NOME"])
    return pd.DataFrame({
        "Bairro": v["BAIRRO"], "Motorista": v["NOME"], "Modelo": v["MODELO"], "Cor": v["COR"],
        "Placa": v["PLACA"], "WhatsApp": v["TEL_FMT"].map(lambda t: _tel(t, sensivel)), "Líder": v["LIDER"], "Multiplicador": v["MULT"],
        "Dia da eleição": v["DIA_E"].map(_sim), "Adesivo": v["ADESIVO"].map(_sim),
        "Seção": v["SECAO"], "Linha na planilha": v["LINHA"],
    })


def excel_veiculos(v: pd.DataFrame, por_bairro: pd.DataFrame, sensivel: bool = False) -> bytes:
    ordem = list(por_bairro["bairro"])
    resumo = por_bairro.rename(columns={"bairro": "Bairro", "total": "Veículos"})
    resumo.insert(0, "Posição", range(1, len(resumo) + 1))
    tabela = _df_veiculos(v, ordem, sensivel)
    buf = BytesIO()
    with _escritor(buf) as w:
        _planilha(w, resumo, "Por bairro")
        _planilha(w, tabela, "Veículos")
    return buf.getvalue()


def excel_apoios(cad: pd.DataFrame, sensivel: bool = False) -> bytes:
    def tabela(df):
        df = df.sort_values(["BAIRRO", "NOME"])
        return pd.DataFrame({
            "Nome": df["NOME"], "WhatsApp": df["TEL_FMT"].map(lambda t: _tel(t, sensivel)), "Bairro": df["BAIRRO"], "Líder": df["LIDER"],
            "Multiplicador": df["MULT"], "Veículo": (df["MODELO"] + " " + df["COR"]).str.strip(),
            "Placa": df["PLACA"], "Seção": df["SECAO"],
        })
    buf = BytesIO()
    with _escritor(buf) as w:
        _planilha(w, tabela(cad[cad.ADESIVO]), "Adesivo veicular")
        _planilha(w, tabela(cad[cad.BANDEIRA]), "Bandeiras")
        _planilha(w, tabela(cad[cad.DIA_E]), "Dia da eleição")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------
_ST_TIT = ParagraphStyle("tit", fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=MARINHO)
_ST_SUB = ParagraphStyle("sub", fontName="Helvetica", fontSize=9.5, leading=13, textColor=CINZA)
_ST_H1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=13, leading=17, textColor=MARINHO,
                        spaceBefore=6, spaceAfter=4)
_ST_H2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=10.5, leading=14, textColor=AZUL,
                        spaceBefore=8, spaceAfter=3)
_ST_CEL = ParagraphStyle("cel", fontName="Helvetica", fontSize=8, leading=10, alignment=TA_LEFT)
_ST_CAB = ParagraphStyle("cab", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=colors.white)


def _p(txt, st=_ST_CEL):
    return Paragraph(escape(str(txt if txt is not None else "")), st)


def _tabela(cabecalho, linhas, larguras):
    dados = [[_p(c, _ST_CAB) for c in cabecalho]] + [[_p(c) for c in l] for l in linhas]
    t = Table(dados, colWidths=larguras, repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINHA),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for i in range(2, len(dados), 2):
        estilo.append(("BACKGROUND", (0, i), (-1, i), ZEBRA))
    t.setStyle(TableStyle(estilo))
    return t


def _doc(buf, titulo, paisagem=False):
    tamanho = landscape(A4) if paisagem else A4
    gerado = datetime.now().strftime("%d/%m/%Y %H:%M")

    def rodape(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(CINZA)
        canvas.drawString(14 * mm, 9 * mm, f"Campanha 2026 · {titulo} · gerado em {gerado}")
        canvas.drawRightString(tamanho[0] - 14 * mm, 9 * mm, f"Página {doc.page}")
        canvas.setFillColor(AZUL)
        canvas.rect(0, tamanho[1] - 4 * mm, tamanho[0], 4 * mm, stroke=0, fill=1)
        canvas.restoreState()

    doc = SimpleDocTemplate(buf, pagesize=tamanho, leftMargin=14 * mm, rightMargin=14 * mm,
                            topMargin=14 * mm, bottomMargin=16 * mm, title=titulo, author="Campanha 2026")
    return doc, rodape, gerado


def pdf_liderancas(lideres: list, sensivel: bool = False) -> bytes:
    buf = BytesIO()
    doc, rodape, gerado = _doc(buf, "Cadastros por liderança")
    largura = doc.width
    total = sum(lid["total"] for lid in lideres)
    meta = sum(lid["meta"] for lid in lideres)
    n_lid = sum(1 for lid in lideres if lid["nome"] != "Sem líder definido")
    hist = [
        Paragraph("Relatório de cadastros por liderança", _ST_TIT),
        Spacer(1, 3),
        Paragraph(escape(f"Gerado em {gerado} · {total} cadastros · meta {meta} "
                         f"({round(total / meta * 100) if meta else 0}%) · {n_lid} lideranças"), _ST_SUB),
        Spacer(1, 10),
        _tabela(["#", "Líder", "Multiplicadores", "Na meta", "Cadastros", "Meta", "%"],
                [[lid["pos"], lid["nome"], lid["n_mult"], lid["na_meta"], lid["total"], lid["meta"],
                  f"{lid['pct']}%"] for lid in lideres],
                [10 * mm, largura - 120 * mm, 26 * mm, 18 * mm, 22 * mm, 18 * mm, 16 * mm]),
    ]
    for lid in lideres:
        hist.append(PageBreak())
        hist.append(Paragraph(escape(f"{lid['pos']}º · {lid['nome']}"), _ST_H1))
        hist.append(Paragraph(escape(
            f"{lid['total']} cadastros · meta {lid['meta']} ({lid['pct']}%) · {lid['n_mult']} multiplicadores · "
            f"{lid['na_meta']} na meta"), _ST_SUB))
        for pos_m, m in enumerate(lid["mults"], start=1):
            sit = "meta batida" if m["ok"] else ("parado" if m["parado"] else f"faltam {m['meta'] - m['total']}")
            cab = Paragraph(escape(f"{pos_m}. {m['nome']} — {m['total']}/{m['meta']} ({sit})"), _ST_H2)
            if m["total"] == 0:
                hist.append(KeepTogether([cab, Paragraph("Nenhum cadastro.", _ST_SUB)]))
                continue
            linhas = [[i, p.NOME, _tel(p.TEL_FMT, sensivel), p.BAIRRO, p.SECAO,
                       pd.Timestamp(p.DATA).strftime("%d/%m/%y") if pd.notna(p.DATA) else ""]
                      for i, p in enumerate(m["pessoas"].itertuples(), start=1)]
            t = _tabela(["#", "Nome", "WhatsApp", "Bairro", "Seção", "Cadastro"], linhas,
                        [9 * mm, largura - 108 * mm, 30 * mm, 36 * mm, 13 * mm, 20 * mm])
            hist.append(KeepTogether([cab, t]) if len(linhas) <= 12 else cab)
            if len(linhas) > 12:
                hist.append(t)
    doc.build(hist, onFirstPage=rodape, onLaterPages=rodape)
    return buf.getvalue()


def pdf_veiculos(v: pd.DataFrame, por_bairro: pd.DataFrame, sensivel: bool = False) -> bytes:
    buf = BytesIO()
    doc, rodape, gerado = _doc(buf, "Gestão de veículos por bairro", paisagem=True)
    largura = doc.width
    hist = [
        Paragraph("Gestão de veículos por bairro", _ST_TIT),
        Spacer(1, 3),
        Paragraph(escape(f"Gerado em {gerado} · {len(v)} veículos em {len(por_bairro)} bairros · "
                         f"{int(v['DIA_E'].sum())} confirmados para o dia da eleição"), _ST_SUB),
        Spacer(1, 10),
        _tabela(["#", "Bairro", "Veículos"],
                [[i, r.bairro, r.total] for i, r in enumerate(por_bairro.itertuples(), start=1)],
                [12 * mm, 90 * mm, 28 * mm]),
    ]
    for i, r in enumerate(por_bairro.itertuples(), start=1):
        sub = v[v.BAIRRO.eq(r.bairro)].sort_values("NOME")
        cab = Paragraph(escape(f"{i}º · {r.bairro} — {r.total} veículo(s)"), _ST_H1)
        linhas = [[p.NOME, p.MODELO, p.COR, p.PLACA, _tel(p.TEL_FMT, sensivel), p.LIDER, p.MULT, _sim(p.DIA_E), _sim(p.ADESIVO)]
                  for p in sub.itertuples()]
        t = _tabela(["Motorista", "Modelo", "Cor", "Placa", "WhatsApp", "Líder", "Multiplicador", "Dia E",
                     "Adesivo"], linhas,
                    [largura - 222 * mm, 28 * mm, 20 * mm, 22 * mm, 30 * mm, 34 * mm, 40 * mm, 14 * mm, 16 * mm])
        hist.append(Spacer(1, 6))
        hist.append(KeepTogether([cab, t]) if len(linhas) <= 14 else cab)
        if len(linhas) > 14:
            hist.append(t)
    doc.build(hist, onFirstPage=rodape, onLaterPages=rodape)
    return buf.getvalue()


# ===========================================================================
# UI
# ===========================================================================
import html as _html
from urllib.parse import quote

import pandas as pd



SENSIVEL = False  # muda pelo botão VISÍVEL/RESTRITO do painel

# Outras ferramentas da campanha (abrem em nova aba): título, para que serve, endereço, ícone, cor.
LINKS = [
    ("Carona Amiga", "Central de caronas: pedidos, motoristas e corridas do dia.",
     "https://projcaronaamiga.netlify.app/painel.html", "carro", "verde"),
    ("Onde eu voto", "O eleitor digita a seção e recebe o local com rota no mapa.",
     "https://projlocaldevotacao.netlify.app/", "urna", "azul"),
    ("Mapa de escolas", "Todos os locais de votação da zona no mapa.",
     "https://mapa2026.streamlit.app/", "mapa", "ambar"),
]


def esc(v) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except (TypeError, ValueError):
        pass
    return _html.escape(str(v), quote=True)


def url_segura(u: str) -> str:
    u = str(u or "").strip()
    return esc(u) if u.startswith("https://") else ""


# ---------------------------------------------------------------------------
# Ícones (SVG em máscara CSS: leve e reaproveitável)
# ---------------------------------------------------------------------------
_ICONES = {
    "wa": '<path d="M21 11.5a8.4 8.4 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.4 8.4 0 0 1-3.8-.9L3 21l1.9-5.7a8.4 8.4 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.4 8.4 0 0 1 3.8-.9h.5a8.5 8.5 0 0 1 8 8v.5z"/>',
    "pin": '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.9"/><path d="M16 3.1a4 4 0 0 1 0 7.8"/>',
    "rede": '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4"/>',
    "carro": '<path d="M3 13l2-6h14l2 6v5H3z"/><circle cx="7.5" cy="16.5" r="1.5"/><circle cx="16.5" cy="16.5" r="1.5"/>',
    "bandeira": '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><path d="M4 22v-7"/>',
    "copia": '<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
    "doc": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h6"/>',
    "relogio": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "alerta": '<path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/>',
    "check": '<path d="M20 6L9 17l-5-5"/>',
    "chev": '<path d="M6 9l6 6 6-6"/>',
    "estrela": '<path d="M12 2l3.1 6.3 6.9 1-5 4.9 1.2 6.8-6.2-3.2-6.2 3.2L7 14.2 2 9.3l6.9-1z"/>',
    "trofeu": '<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6M18 9h1.5a2.5 2.5 0 0 0 0-5H18M4 22h16M10 14.7V17c0 .6-.5 1-1 1.2C7.9 18.8 7 20.2 7 22M14 14.7V17c0 .6.5 1 1 1.2 1.1.6 2 2 2 3.8M18 2H6v7a6 6 0 0 0 12 0z"/>',
    "escudo": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    "bolo": '<path d="M20 21v-8a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8M4 16s.5-1 2-1 2.5 2 4 2 2.5-2 4-2 2.5 2 4 2 2-1 2-1M2 21h20M7 8v3M12 8v3M17 8v3M7 4h.01M12 4h.01M17 4h.01"/>',
    "escola": '<path d="M22 10L12 5 2 10l10 5 10-5z"/><path d="M6 12v5c3 2 9 2 12 0v-5"/>',
    "pessoa": '<circle cx="12" cy="8" r="4"/><path d="M4 21v-1a6 6 0 0 1 6-6h4a6 6 0 0 1 6 6v1"/>',
    "grafico": '<path d="M3 3v18h18M7 16l4-4 4 4 5-6"/>',
    "etiqueta": '<path d="M20.6 13.4l-7.2 7.2a2 2 0 0 1-2.8 0L2 12V2h10l8.6 8.6a2 2 0 0 1 0 2.8z"/><path d="M7 7h.01"/>',
    "urna": '<path d="M4 11h16v9H4zM8 11V4h8v7M10 7h4"/>',
    "busca": '<circle cx="11" cy="11" r="8"/><path d="M21 21l-4.3-4.3"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>',
    "link": '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6M15 3h6v6M10 14L21 3"/>',
    "mapa": '<path d="M1 6v16l7-4 8 4 7-4V2l-7 4-8-4-7 4zM8 2v16M16 6v16"/>',
}


def _svg_uri(path: str) -> str:
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" '
           f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{path}</svg>')
    return "data:image/svg+xml;utf8," + quote(svg, safe="")


def ic(nome: str, extra: str = "") -> str:
    return f'<i class="cv-i i-{nome} {extra}" aria-hidden="true"></i>'


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
:root{--bg:#040B1F;--painel:rgba(13,32,74,.62);--painel2:rgba(4,12,32,.55);--borda:rgba(125,170,255,.16);--borda2:rgba(125,170,255,.30);--txt:#EAF2FF;--mut:#93A8CC;--sua:#C7D6F0;--azul:#2563EB;--azul2:#3B82F6;--ciano:#38BDF8;--ciano2:#7DD3FC;--verde2:#4ADE80;--ambar2:#FCD34D;--fd:'Outfit',system-ui,sans-serif;--fb:'Plus Jakarta Sans',system-ui,sans-serif}
.stApp{background:radial-gradient(700px 520px at 8% 0px,rgba(37,99,235,.38),transparent 70%),radial-gradient(620px 620px at 100% 900px,rgba(14,165,233,.14),transparent 70%),radial-gradient(640px 640px at 0% 2200px,rgba(37,99,235,.12),transparent 70%),#040B1F !important;color:var(--txt)}
html,body,.stApp,.stApp p,.stApp label,.stApp input,.stApp button,.stApp textarea,.stApp li{font-family:var(--fb)}
header[data-testid="stHeader"],#MainMenu,footer,[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"],.stDeployButton,[data-testid="stAppDeployButton"],[data-testid="manage-app-button"]{display:none !important}
.block-container,[data-testid="stMainBlockContainer"]{max-width:1280px !important;padding:16px 14px 48px !important}
@media(min-width:768px){.block-container,[data-testid="stMainBlockContainer"]{padding:28px 32px 60px !important}}
.stTextInput [data-baseweb="input"],.stTextInput [data-baseweb="base-input"],div[data-baseweb="select"]>div{background:rgba(13,32,74,.78) !important;border-color:var(--borda2) !important;border-radius:14px !important;min-height:46px}
.stTextInput input{color:var(--txt) !important;font-size:15px !important}
.stTextInput label p,.stSelectbox label p,.stCheckbox label p{color:var(--sua) !important;font-weight:700 !important;font-size:12.5px !important}
.stButton>button,.stDownloadButton>button,[data-testid="stFormSubmitButton"] button{width:100%;min-height:48px;border-radius:14px !important;border:0 !important;background:#2563EB !important;color:#FFFFFF !important;font-weight:800 !important;box-shadow:0 8px 22px rgba(37,99,235,.35)}
.stButton>button:hover,.stDownloadButton>button:hover,[data-testid="stFormSubmitButton"] button:hover{background:#1D4ED8 !important}
.stButton>button p,.stDownloadButton>button p,[data-testid="stFormSubmitButton"] button p{font-weight:800 !important;color:#FFFFFF !important}
.st-key-sair button,.st-key-atualizar button{background:rgba(13,32,74,.62) !important;border:1px solid var(--borda2) !important;box-shadow:none !important}
[data-testid="stForm"]{background:rgba(13,32,74,.62);border:1px solid var(--borda) !important;border-radius:22px;padding:22px 20px}
div[data-testid="stRadio"] div[role="radiogroup"]{display:flex !important;flex-direction:row !important;flex-wrap:nowrap !important;overflow-x:auto;gap:8px !important;padding:2px 2px 8px;scrollbar-width:none;width:100%}
div[data-testid="stRadio"] div[role="radiogroup"]::-webkit-scrollbar{display:none}
div[data-testid="stRadio"] div[role="radiogroup"] label{flex:0 0 auto !important;width:auto !important;max-width:none !important;margin:0 !important;padding:0 18px !important;min-height:44px;display:flex !important;align-items:center;border-radius:14px;background:rgba(13,32,74,.62);border:1px solid var(--borda);cursor:pointer}
div[data-testid="stRadio"] div[role="radiogroup"] label>div:not(:last-child),div[data-testid="stRadio"] div[role="radiogroup"] label>span:not(:last-child){display:none !important}
div[data-testid="stRadio"] div[role="radiogroup"] label>div>div:not([data-testid="stMarkdownContainer"]){display:none !important}
div[data-testid="stRadio"] div[role="radiogroup"] label input{position:absolute;opacity:0;width:1px;height:1px}
div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked){background:#2563EB;border-color:transparent;box-shadow:0 6px 18px rgba(37,99,235,.4)}
div[data-testid="stRadio"] div[role="radiogroup"] label *{white-space:nowrap !important;word-break:normal !important;overflow-wrap:normal !important}
div[data-testid="stRadio"] div[role="radiogroup"] label p{margin:0 !important;font-weight:700 !important;font-size:13.5px !important;color:var(--sua) !important}
div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) p{color:#FFFFFF !important}
.stToggle label p,[data-testid="stToggle"] label p,.stCheckbox label p{color:var(--sua) !important;font-weight:700 !important}
.cv-links{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-top:14px}
.cv-link{display:flex;flex-direction:column;align-items:flex-start;gap:6px;padding:12px;border-radius:16px;background:var(--painel);border:1px solid var(--borda2);color:var(--txt) !important;min-width:0}
.cv-link:hover{border-color:#3B82F6;background:rgba(37,99,235,.22)}
.cv-link b{font-size:12.5px;font-weight:800;line-height:1.2}
.cv-link small{font-size:10.5px;color:var(--mut);font-weight:600}
.cv-link-ico{width:34px;height:34px;border-radius:10px;display:flex;align-items:center;justify-content:center;background:rgba(56,189,248,.16);color:#7DD3FC}
@media(min-width:768px){.cv-link{flex-direction:row;align-items:center;gap:12px;padding:14px 16px}.cv-link b{font-size:14px}}
.cv-tools-h{display:flex;align-items:baseline;justify-content:space-between;gap:6px 12px;flex-wrap:wrap;margin:18px 0 8px}
.cv-tools-h .cv-over{display:inline-flex;align-items:center;gap:6px;color:var(--sua)}
.cv-tools-n{font-size:11.5px;color:var(--mut);font-weight:600}
.cv-tools{display:grid;grid-template-columns:minmax(0,1fr);gap:10px}
@media(min-width:768px){.cv-tools{grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}}
.cv-tool{--c:#38BDF8;--cf:rgba(56,189,248,.16);display:flex;align-items:center;gap:12px;min-height:76px;padding:14px;border-radius:18px;background:linear-gradient(135deg,var(--cf),rgba(13,32,74,.62) 70%);border:1px solid var(--borda2);border-left:4px solid var(--c);color:var(--txt) !important;transition:transform .15s ease,border-color .15s ease,box-shadow .15s ease}
.cv-tool:hover{transform:translateY(-2px);border-color:var(--c);box-shadow:0 10px 26px rgba(0,0,0,.35)}
.cv-tool:focus-visible{outline:2px solid #7DD3FC;outline-offset:3px}
.cv-tool.verde{--c:#4ADE80;--cf:rgba(34,197,94,.18)}.cv-tool.azul{--c:#60A5FA;--cf:rgba(59,130,246,.22)}.cv-tool.ambar{--c:#FCD34D;--cf:rgba(251,191,36,.16)}
.cv-tool-ico{width:46px;height:46px;flex-shrink:0;border-radius:14px;display:flex;align-items:center;justify-content:center;background:var(--cf);color:var(--c)}
.cv-tool-txt{flex:1 1 150px;min-width:0;display:flex;flex-direction:column;gap:3px}
.cv-tool{flex-wrap:wrap}
.cv-tool-btn{margin-left:auto}
@media(min-width:768px) and (max-width:1099px){.cv-tool-ico{width:40px;height:40px}.cv-tool-btn{width:100%;justify-content:center}}
.cv-tool-txt b{font-family:var(--fd);font-size:16px;font-weight:700}
.cv-tool-txt small{font-size:12px;color:var(--sua);line-height:1.35}
.cv-tool-btn{flex-shrink:0;display:inline-flex;align-items:center;gap:6px;min-height:40px;padding:0 14px;border-radius:12px;background:var(--c);color:#04112B;font-weight:800;font-size:13px}
.cv-demo{font-size:10px;font-weight:800;letter-spacing:1px;padding:3px 8px;border-radius:999px;background:rgba(251,191,36,.14);color:#FCD34D;border:1px solid rgba(251,191,36,.35)}
.cv-wa-mini{width:30px;height:30px;flex-shrink:0;border-radius:9px;background:#16A34A;color:#FFFFFF !important;display:inline-flex;align-items:center;justify-content:center}
.cv-wa-mini::before{content:"";width:15px;height:15px;background:currentColor;-webkit-mask:var(--m) center/contain no-repeat;mask:var(--m) center/contain no-repeat}
.cv-nome-l{display:flex;align-items:center;gap:8px;min-width:0}
.cv{color:var(--txt);font-family:var(--fb);font-size:14px;line-height:1.35}
.cv *{box-sizing:border-box}
.cv a{color:inherit;text-decoration:none}
.cv-i{display:inline-block;width:16px;height:16px;flex-shrink:0;background:currentColor;-webkit-mask:var(--m) center/contain no-repeat;mask:var(--m) center/contain no-repeat}
.cv-i.p{width:12px;height:12px}.cv-i.g{width:20px;height:20px}.cv-i.gg{width:26px;height:26px}
.cv-card{background:var(--painel);border:1px solid var(--borda);border-radius:20px;box-shadow:inset 0 1px 0 rgba(255,255,255,.06);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px)}
.cv-pad{padding:16px}
@media(min-width:768px){.cv-pad{padding:20px 22px}}
.cv-over{font-size:10.5px;font-weight:800;letter-spacing:1.3px;text-transform:uppercase;color:var(--mut)}
.cv-num{font-family:var(--fd);font-weight:700;line-height:1;letter-spacing:-.5px}
.cv-titulo{font-family:var(--fd);font-size:18px;font-weight:700;letter-spacing:-.1px}
.cv-cab{display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap}
.cv-mut{color:var(--mut)}.cv-sua{color:var(--sua)}
.cv-topo{display:flex;align-items:center;justify-content:space-between;gap:12px}
.cv-marca{display:flex;align-items:center;gap:10px}
.cv-logo{width:40px;height:40px;border-radius:12px;background:#2563EB;display:flex;align-items:center;justify-content:center;color:#FFFFFF;box-shadow:0 6px 18px rgba(37,99,235,.45)}
.cv-marca b{display:block;font-family:var(--fd);font-size:17px;font-weight:700}
.cv-marca small{display:block;font-size:10px;font-weight:800;letter-spacing:1.4px;text-transform:uppercase;color:var(--mut)}
.cv-status{display:flex;align-items:center;gap:6px;font-size:11px;font-weight:700;color:var(--mut);padding:6px 10px;border-radius:999px;background:var(--painel);border:1px solid var(--borda);white-space:nowrap}
.cv-dot{width:8px;height:8px;border-radius:50%;background:#4ADE80;box-shadow:0 0 10px #4ADE80}
.cv-faixa{margin-top:12px;display:flex;align-items:center;gap:8px;padding:9px 12px;border-radius:14px;font-size:12.5px;font-weight:700;background:rgba(251,191,36,.10);border:1px solid rgba(251,191,36,.35);color:#FCD34D}
.cv-hero{display:flex;flex-direction:column;gap:14px;margin-top:18px}
@media(min-width:900px){.cv-hero{flex-direction:row;align-items:flex-end;justify-content:space-between}}
.cv-h1{font-family:var(--fd);font-size:30px;font-weight:700;letter-spacing:-.6px;line-height:1.08}
@media(min-width:768px){.cv-h1{font-size:40px}}
.cv-lead{font-size:13.5px;color:var(--mut);font-weight:500;margin-top:5px}
.cv-cont{display:flex;align-items:center;gap:14px;padding:14px 16px}
@media(min-width:900px){.cv-cont{min-width:380px}}
.cv-cont-ico{width:48px;height:48px;border-radius:14px;flex-shrink:0;display:flex;align-items:center;justify-content:center;background:rgba(56,189,248,.14);color:#7DD3FC}
.cv-cont b{display:block;font-size:15px;font-weight:700;margin-top:2px}
.cv-cont-num{margin-left:auto;font-family:var(--fd);font-size:36px;font-weight:700;color:#7DD3FC;line-height:1}
.cv-ov{display:grid;grid-template-columns:minmax(0,1fr);gap:12px;margin-top:14px}
@media(min-width:900px){.cv-ov{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}}
.cv-aneis{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:16px}
.cv-anel-box{display:flex;flex-direction:column;align-items:center;gap:10px;text-align:center}
.cv-anel{position:relative;width:126px;height:126px;filter:drop-shadow(0 0 10px rgba(56,189,248,.30))}
@media(min-width:768px){.cv-anel{width:150px;height:150px}}
.cv-anel-r{position:absolute;inset:0;border-radius:50%;-webkit-mask:radial-gradient(farthest-side,transparent calc(100% - 14px),#000 calc(100% - 13px)),repeating-conic-gradient(#000 0deg 7.4deg,transparent 7.4deg 10deg);-webkit-mask-composite:source-in;mask:radial-gradient(farthest-side,transparent calc(100% - 14px),#000 calc(100% - 13px)),repeating-conic-gradient(#000 0deg 7.4deg,transparent 7.4deg 10deg);mask-composite:intersect}
.cv-anel-c{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.cv-anel-c b{font-family:var(--fd);font-size:30px;font-weight:700;line-height:1}
@media(min-width:768px){.cv-anel-c b{font-size:36px}}
.cv-anel-c small{font-size:11px;font-weight:600;color:var(--mut);margin-top:4px}
.cv-anel-leg{font-size:12.5px;color:var(--sua);font-weight:600;line-height:1.3}
.cv-kpis{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.cv-kpis.q4{grid-template-columns:repeat(2,minmax(0,1fr))}
.cv-kpis.q3>:last-child{grid-column:1/-1}
@media(min-width:900px){.cv-kpis{gap:12px}.cv-kpis.q4{grid-template-columns:repeat(4,minmax(0,1fr))}.cv-kpis.q3{grid-template-columns:repeat(3,minmax(0,1fr))}.cv-kpis.q3>:last-child{grid-column:auto}}
.cv-kpi{padding:14px;display:flex;flex-direction:column;gap:7px;border-radius:18px;min-width:0}
.cv-kpi-h{display:flex;align-items:center;justify-content:space-between;gap:6px}
.cv-kpi .cv-num{font-size:30px}
@media(min-width:768px){.cv-kpi .cv-num{font-size:34px}}
.cv-kpi-p{display:flex;align-items:center;justify-content:space-between;gap:6px;font-size:12px;color:var(--sua);font-weight:600;min-height:20px}
.cv-kpi.ativo{border-color:#3B82F6;box-shadow:0 0 0 1px #3B82F6 inset}
.cv-c-ciano{color:#7DD3FC}.cv-c-azul{color:#93C5FD}.cv-c-ambar{color:#FCD34D}.cv-c-verde{color:#4ADE80}.cv-c-rosa{color:#F9A8D4}
.cv-sec{display:flex;flex-direction:column;gap:7px;margin:4px 0 2px}
.cv-sec-t{font-family:var(--fd);font-size:23px;font-weight:700;letter-spacing:-.2px}
@media(min-width:768px){.cv-sec-t{font-size:27px}}
.cv-sec-s{font-size:13px;color:var(--mut);line-height:1.45}
.cv-chips{display:flex;flex-wrap:wrap;gap:6px}
.cv-chip{display:inline-flex;align-items:center;gap:5px;font-size:11.5px;font-weight:700;padding:4px 10px;border-radius:999px;background:rgba(147,168,204,.12);color:var(--sua);border:1px solid var(--borda);white-space:nowrap}
.cv-chip.ok{background:rgba(34,197,94,.14);color:#4ADE80;border-color:rgba(34,197,94,.3)}
.cv-chip.al{background:rgba(251,191,36,.14);color:#FCD34D;border-color:rgba(251,191,36,.3)}
.cv-chip.az{background:rgba(59,130,246,.16);color:#BFDBFE;border-color:rgba(59,130,246,.32)}
.cv-chip.vm{background:rgba(248,113,113,.14);color:#FCA5A5;border-color:rgba(248,113,113,.32)}
.cv-chip.sm{font-size:10.5px;padding:2px 8px}
.cv-bar{display:block;height:8px;border-radius:999px;background:rgba(148,163,184,.18);overflow:hidden;width:100%}
.cv-bar.fina{height:6px}
.cv-bar>i{display:block;height:100%;border-radius:999px;background:linear-gradient(90deg,#2563EB,#38BDF8)}
.cv-bar>i.ok{background:linear-gradient(90deg,#16A34A,#4ADE80)}
.cv-bar>i.al{background:linear-gradient(90deg,#F59E0B,#FCD34D)}
.cv-bar>i.ou{background:linear-gradient(90deg,#F59E0B,#FDE68A)}
.cv-lista{display:flex;flex-direction:column;gap:10px}
details.cv-lid,details.cv-bai{background:var(--painel);border:1px solid var(--borda);border-radius:20px;box-shadow:inset 0 1px 0 rgba(255,255,255,.06);overflow:hidden}
details.cv-lid[open],details.cv-bai[open]{border-color:#3B82F6}
.cv-lid>summary,.cv-mul>summary,.cv-bai>summary{list-style:none;cursor:pointer;display:block;outline:none;-webkit-tap-highlight-color:transparent}
.cv-lid>summary::-webkit-details-marker,.cv-mul>summary::-webkit-details-marker,.cv-bai>summary::-webkit-details-marker{display:none}
.cv-lid>summary:focus-visible,.cv-mul>summary:focus-visible,.cv-bai>summary:focus-visible{box-shadow:inset 0 0 0 2px #7DD3FC}
.cv-lid>summary{padding:16px}
.cv-row{display:flex;align-items:center;gap:12px;width:100%}
.cv-rank{width:40px;height:40px;flex-shrink:0;border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:var(--fd);font-weight:700;font-size:17px;background:rgba(59,130,246,.2);color:#BFDBFE}
.r1{background:linear-gradient(135deg,#FDE68A,#F59E0B) !important;color:#3D2500 !important}
.r2{background:linear-gradient(135deg,#F1F5F9,#B8C2D6) !important;color:#1F2937 !important}
.r3{background:linear-gradient(135deg,#FFD1A8,#F08A4B) !important;color:#4A1D05 !important}
.cv-info{flex:1;min-width:0;display:flex;flex-direction:column;gap:3px}
.cv-nome{font-family:var(--fd);font-size:19px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cv-sub{font-size:12px;color:var(--sua)}
.cv-tot{display:flex;flex-direction:column;align-items:flex-end;gap:2px;flex-shrink:0}
.cv-tot b{font-family:var(--fd);font-size:28px;font-weight:700;line-height:1}
.cv-tot small{font-size:11px;color:var(--mut);font-weight:600;white-space:nowrap}
.cv-chev{color:var(--mut);transition:transform .2s}
details[open]>summary .cv-chev{transform:rotate(180deg)}
.cv-prog{display:flex;align-items:center;gap:10px;margin-top:12px}
.cv-prog b{font-size:12px;font-weight:800;color:#BFDBFE;min-width:40px;text-align:right}
.cv-corpo{padding:0 12px 14px;display:flex;flex-direction:column;gap:8px}
.cv-corpo-cab{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:12px 4px 2px;border-top:1px solid rgba(125,170,255,.14);flex-wrap:wrap}
details.cv-mul{background:var(--painel2);border:1px solid rgba(125,170,255,.14);border-radius:14px;overflow:hidden}
details.cv-mul[open]{border-color:#2F6FE0}
.cv-mul>summary{padding:12px}
.cv-ini{width:34px;height:34px;flex-shrink:0;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:800;background:rgba(59,130,246,.2);color:#BFDBFE}
.cv-mul-nome{font-size:14px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cv-mul-num{font-family:var(--fd);font-size:17px;font-weight:700;white-space:nowrap}
.cv-mul-corpo{padding:0 12px 12px;display:flex;flex-direction:column;gap:8px}
.cv-mul-ct{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;padding:2px 0 4px}
.cv-pessoas{display:grid;grid-template-columns:minmax(0,1fr);gap:8px}
@media(min-width:1100px){.cv-pessoas.duas{grid-template-columns:repeat(2,minmax(0,1fr))}}
.cv-pes{display:flex;align-items:center;gap:10px;padding:10px 10px 10px 12px;border-radius:12px;background:rgba(37,99,235,.12);border:1px solid rgba(125,170,255,.12);min-width:0}
.cv-pes-i{flex:1;min-width:0;display:flex;flex-direction:column;gap:3px}
.cv-pes-i>b{font-size:13.5px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cv-meta{display:flex;align-items:flex-start;gap:5px;font-size:12px;line-height:1.35;color:var(--mut);min-width:0}
.cv-meta>.cv-i,.cv-pi::before{margin-top:2px}
.cv-wa{width:44px;height:44px;flex-shrink:0;border-radius:12px;background:#16A34A;color:#FFFFFF !important;display:flex;align-items:center;justify-content:center}
.cv-wa::before{content:"";width:20px;height:20px;background:currentColor;-webkit-mask:var(--m) center/contain no-repeat;mask:var(--m) center/contain no-repeat}
.cv-pi::before{content:"";width:12px;height:12px;flex-shrink:0;background:currentColor;-webkit-mask:var(--m) center/contain no-repeat;mask:var(--m) center/contain no-repeat}
.cv-wa.off{background:rgba(148,163,184,.16);color:var(--mut) !important}
.cv-wa-l{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:44px;padding:0 16px;border-radius:12px;background:#16A34A;color:#FFFFFF !important;font-weight:800;font-size:13px}
.cv-cobrar{flex-shrink:0;display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:0 14px;border-radius:12px;background:#16A34A;color:#FFFFFF !important;font-weight:800;font-size:13px}
.cv-cobrar::before{content:"";width:16px;height:16px;background:currentColor;-webkit-mask:var(--m) center/contain no-repeat;mask:var(--m) center/contain no-repeat}
.cv-cobrar:hover{background:#15803D}
.cv-cobrar.off{background:rgba(148,163,184,.14);color:var(--mut) !important;font-size:11.5px;padding:0 10px}
.cv-cobrar.off::before{display:none}
.cv-busca-r{display:flex;flex-direction:column;gap:8px;margin:4px 0 16px}
.st-key-barra_topo{margin-top:10px}
.st-key-barra_topo [data-testid="stHorizontalBlock"]{flex-wrap:nowrap !important;gap:8px !important;justify-content:flex-end}
.st-key-barra_topo [data-testid="stColumn"]{flex:0 0 auto !important;width:auto !important;min-width:0 !important}
.st-key-barra_topo .stButton>button{min-height:44px;padding:0 18px}
.st-key-barra_topo .stButton,.st-key-barra_topo [data-testid="stButton"]{width:100% !important}
.cv-marca b{white-space:nowrap}
@media(max-width:640px){.st-key-barra_topo [data-testid="stColumn"]{flex:1 1 0 !important}}
.cv-mais{display:flex;align-items:center;justify-content:center;min-height:40px;border-radius:12px;border:1px dashed rgba(125,170,255,.35);color:var(--sua);font-size:12.5px;font-weight:700}
.cv-top-l{display:flex;flex-direction:column;gap:10px;margin-top:12px}
.cv-top{display:flex;align-items:center;gap:12px;min-width:0}
.cv-av{width:40px;height:40px;flex-shrink:0;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:14px;background:rgba(59,130,246,.2);color:#BFDBFE}
.cv-top .cv-info b{font-size:14px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cv-top .cv-num{font-size:20px}
.cv-cols{position:relative;height:150px;display:flex;align-items:flex-end;gap:6px;margin-top:16px}
.cv-colx{flex:1;display:flex;flex-direction:column;align-items:center;gap:6px;min-width:0;position:relative;z-index:1}
.cv-colx span{font-size:11px;font-weight:700;color:var(--sua)}
.cv-colx i{display:block;width:100%;max-width:44px;border-radius:6px 6px 3px 3px;background:rgba(226,232,240,.85)}
.cv-colx.hi i{background:#38BDF8;box-shadow:0 0 16px rgba(56,189,248,.45)}
.cv-colx.hi span{color:#7DD3FC}
.cv-media{position:absolute;left:0;right:0;border-top:1px dashed rgba(226,232,240,.45);z-index:2}
.cv-media span{position:absolute;right:0;top:-21px;font-size:10px;font-weight:800;color:var(--txt);background:rgba(37,99,235,.55);padding:2px 6px;border-radius:6px}
.cv-rot{display:flex;gap:6px;margin-top:8px}
.cv-rot span{flex:1;text-align:center;font-size:10px;color:var(--mut);font-weight:600}
.cv-rk{display:grid;grid-template-columns:26px minmax(0,1fr) auto;grid-template-areas:"p n v" "p b b";column-gap:10px;row-gap:6px;align-items:center;padding:9px 0;border-bottom:1px solid rgba(125,170,255,.08)}
.cv-rk:last-child{border-bottom:0}
.cv-rk-p{grid-area:p;font-family:var(--fd);font-weight:700;color:var(--mut);font-size:14px;text-align:center}
.cv-rk-n{grid-area:n;font-size:13.5px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cv-rk-n small{font-weight:600;color:var(--mut);font-size:11.5px;margin-left:6px}
.cv-rk-v{grid-area:v;font-family:var(--fd);font-weight:700;font-size:16px;text-align:right}
.cv-rk>.cv-bar{grid-area:b}
@media(min-width:1000px){.cv-rk{grid-template-columns:28px minmax(130px,230px) minmax(0,1fr) 54px;grid-template-areas:"p n b v"}}
.cv-grid2{display:grid;grid-template-columns:minmax(0,1fr);gap:10px;align-items:start}
@media(min-width:760px){.cv-grid2{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(min-width:1150px){.cv-grid2.tres{grid-template-columns:repeat(3,minmax(0,1fr))}}
.cv-bai>summary{padding:14px}
.cv-mini{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-top:12px}
.cv-mini>span{padding:8px 10px;border-radius:12px;background:var(--painel2);border:1px solid rgba(125,170,255,.1);display:flex;flex-direction:column;gap:2px}
.cv-mini b{font-family:var(--fd);font-size:20px;font-weight:700}
.cv-mini small{font-size:10px;color:var(--mut);font-weight:800;text-transform:uppercase;letter-spacing:.6px}
.cv-vei{padding:14px;display:flex;flex-direction:column;gap:10px;border-radius:18px}
.cv-vei-top{display:flex;align-items:center;gap:12px}
.cv-vei-ico{width:44px;height:44px;border-radius:12px;flex-shrink:0;background:rgba(56,189,248,.14);color:#7DD3FC;display:flex;align-items:center;justify-content:center}
.cv-vei-mod{font-family:var(--fd);font-size:18px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cv-cor{display:inline-block;width:12px;height:12px;border-radius:50%;border:1px solid rgba(255,255,255,.45);flex-shrink:0}
.cv-placa{margin-left:auto;display:flex;flex-direction:column;align-items:center;min-width:94px;border-radius:7px;background:#F8FAFC;color:#0F172A;border:2px solid #0F172A;overflow:hidden;flex-shrink:0}
.cv-placa small{display:block;width:100%;background:#1E40AF;color:#FFFFFF;font-size:7.5px;font-weight:800;letter-spacing:1.6px;text-align:center;padding:1px 0}
.cv-placa b{font-family:var(--fd);font-size:15px;font-weight:700;letter-spacing:1px;padding:2px 8px;color:#0F172A}
.cv-vei-mot{font-size:13px;color:var(--sua)}
.cv-vei-mot b{color:var(--txt)}
.cv-vei-pe{display:flex;align-items:center;justify-content:space-between;gap:8px}
.cv-pir{display:flex;flex-direction:column;gap:9px;margin-top:14px}
.cv-pir-r{display:grid;grid-template-columns:minmax(0,1fr) 54px minmax(0,1fr);align-items:center;gap:8px}
.cv-pir-l,.cv-pir-d{display:flex;align-items:center;gap:6px;min-width:0}
.cv-pir-l{justify-content:flex-end}
.cv-pir-l i,.cv-pir-d i{display:block;height:18px;border-radius:6px;min-width:2px}
.cv-pir-l i{background:#3B82F6}.cv-pir-d i{background:#67E8F9}
.cv-pir-l b,.cv-pir-d b{font-size:12px;font-weight:700;color:var(--sua);min-width:22px}
.cv-pir-l b{text-align:right}
.cv-pir-f{text-align:center;font-size:12px;font-weight:800}
.cv-leg{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--sua);font-weight:600}
.cv-leg i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;vertical-align:-1px}
.cv-split{display:flex;height:10px;border-radius:999px;overflow:hidden;margin-top:12px;background:rgba(148,163,184,.18)}
.cv-gen{padding:16px;display:flex;flex-direction:column;gap:8px}
.cv-gen .cv-num{font-size:38px}
.cv-dup{padding:14px;display:flex;flex-direction:column;gap:10px;border-radius:18px}
.cv-dup-r{display:flex;align-items:flex-start;gap:10px;padding:10px;border-radius:12px;background:var(--painel2);border:1px solid rgba(125,170,255,.1);min-width:0}
.cv-linha{flex-shrink:0;min-width:64px;text-align:center;padding:6px 8px;border-radius:10px;background:rgba(59,130,246,.18);color:#BFDBFE;font-family:var(--fd);font-weight:700;font-size:16px;line-height:1.1}
.cv-linha small{display:block;font-family:var(--fb);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:var(--mut)}
.cv-dup-i{flex:1;min-width:0;display:flex;flex-direction:column;gap:4px}
.cv-dup-n{display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap}
.cv-dup-n>b{font-size:14px;font-weight:700}
@media(max-width:600px){.cv-tab .so-pc{display:none}}
.cv-qual{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-top:12px}
@media(min-width:900px){.cv-qual{grid-template-columns:repeat(4,minmax(0,1fr))}}
.cv-qual>span{padding:10px 12px;border-radius:12px;background:var(--painel2);border:1px solid rgba(125,170,255,.1);display:flex;flex-direction:column;gap:3px}
.cv-qual b{font-family:var(--fd);font-size:22px;font-weight:700}
.cv-qual small{font-size:11.5px;color:var(--sua);font-weight:600}
.cv-rel{padding:18px;display:flex;flex-direction:column;gap:10px;height:100%}
.cv-rel-ico{width:46px;height:46px;border-radius:14px;background:rgba(37,99,235,.22);color:#BFDBFE;display:flex;align-items:center;justify-content:center}
.cv-rel ul{margin:0;padding-left:18px;color:var(--sua);font-size:12.5px;line-height:1.6}
.cv-tab{width:100%;border-collapse:collapse;font-size:13px;margin-top:10px}
.cv-tab th{text-align:left;font-size:10.5px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:var(--mut);padding:8px 6px;border-bottom:1px solid var(--borda)}
.cv-tab td{padding:9px 6px;border-bottom:1px solid rgba(125,170,255,.08)}
.cv-tab td.n,.cv-tab th.n{text-align:right;font-variant-numeric:tabular-nums}
.cv-tab-w{overflow-x:auto}
.cv-vazio{padding:26px 16px;text-align:center;color:var(--mut);font-size:13.5px}
.cv-nota{display:flex;gap:10px;align-items:flex-start;padding:12px 14px;border-radius:14px;background:rgba(59,130,246,.12);border:1px solid rgba(59,130,246,.3);color:#DBEAFE;font-size:13px;line-height:1.5}
.cv-nota.al{background:rgba(251,191,36,.10);border-color:rgba(251,191,36,.35);color:#FDE68A}
.cv-nota .cv-i{margin-top:2px}
.cv-login{max-width:440px;margin:28px auto 6px;text-align:center;padding:30px 22px}
.cv-login-ico{width:62px;height:62px;border-radius:18px;margin:0 auto 14px;background:#2563EB;display:flex;align-items:center;justify-content:center;color:#FFFFFF;box-shadow:0 10px 28px rgba(37,99,235,.5)}
.cv-rodape{margin-top:18px;text-align:center;font-size:11.5px;color:var(--mut);line-height:1.6}
.cv-esp{height:4px}
"""


def estilo() -> str:
    icones = "".join(f'.i-{n}{{--m:url("{_svg_uri(p)}")}}' for n, p in _ICONES.items())
    css = " ".join(l.strip() for l in _CSS.strip().splitlines())
    return f"<style>{css}{icones}</style>"


# ---------------------------------------------------------------------------
# Peças básicas
# ---------------------------------------------------------------------------
def chip(txt, tipo: str = "", icone: str | None = None, pequeno: bool = False) -> str:
    classes = " ".join(c for c in ["cv-chip", tipo, "sm" if pequeno else ""] if c)
    return f'<span class="{classes}">{ic(icone, "p") if icone else ""}{esc(txt)}</span>'


def barra(pct, tipo: str = "", fina: bool = False) -> str:
    p = max(0.0, min(100.0, float(pct or 0)))
    return f'<span class="cv-bar{" fina" if fina else ""}"><i class="{tipo}" style="width:{p:.1f}%"></i></span>'


def whats(link: str, nome: str = "") -> str:
    if link:
        return (f'<a class="cv-wa i-wa" href="{esc(link)}" target="_blank" rel="noopener" '
                f'aria-label="WhatsApp de {esc(nome)}"></a>')
    return '<span class="cv-wa i-wa off" title="Sem WhatsApp válido"></span>'


def _wa_mini(link: str, nome: str) -> str:
    if not link:
        return ""
    return (f'<a class="cv-wa-mini i-wa" href="{esc(link)}" target="_blank" rel="noopener" '
            f'aria-label="WhatsApp do líder {esc(nome)}"></a>')


def iniciais(nome: str) -> str:
    partes = [p for p in str(nome).split() if p[:1].isalpha()]
    if not partes:
        return "?"
    if len(partes) == 1:
        return partes[0][:1].upper()
    return (partes[0][:1] + partes[-1][:1]).upper()


def classe_rank(pos: int) -> str:
    return {1: "r1", 2: "r2", 3: "r3"}.get(pos, "")


def secao(titulo: str, subtitulo: str = "", chips: list | None = None) -> str:
    c = f'<div class="cv-chips">{"".join(chips)}</div>' if chips else ""
    s = f'<div class="cv-sec-s">{esc(subtitulo)}</div>' if subtitulo else ""
    return f'<div class="cv"><div class="cv-sec"><div class="cv-sec-t" role="heading" aria-level="2">{esc(titulo)}</div>{s}{c}</div></div>'


def nota(txt_html: str, tipo: str = "", icone: str = "info") -> str:
    return f'<div class="cv"><div class="cv-nota {tipo}">{ic(icone)}<div>{txt_html}</div></div></div>'


def selo_sigilo(visivel: bool) -> str:
    if visivel:
        return ('<div class="cv"><div class="cv-nota al">' + ic("alerta") + '<div><b>DADOS VISÍVEIS</b> · CPF, título, '
                'nascimento e telefone aparecem completos na tela e nos relatórios. Desligue ao terminar.</div></div></div>')
    return ('<div class="cv"><div class="cv-chips">' + chip("PROTEGIDO · CPF, título e telefone mascarados", "ok", "escudo")
            + '</div></div>')


def vazio(msg: str) -> str:
    return f'<div class="cv"><div class="cv-card cv-vazio">{esc(msg)}</div></div>'


def kpi(rotulo, valor, icone, rodape_html="", cor="cv-c-ciano", ativo=False) -> str:
    return (f'<div class="cv-card cv-kpi{" ativo" if ativo else ""}"><div class="cv-kpi-h"><span class="cv-over">{esc(rotulo)}</span>'
            f'<span class="{cor}">{ic(icone)}</span></div><span class="cv-num">{esc(valor)}</span>'
            f'<span class="cv-kpi-p">{rodape_html}</span></div>')


def kpis(itens: list, quatro: bool = True) -> str:
    classe = " q4" if quatro else (" q3" if len(itens) == 3 else "")
    return f'<div class="cv"><div class="cv-kpis{classe}">{"".join(itens)}</div></div>'


def anel(pct: float, centro: str, sub_centro: str, legenda: str, cores=("#2563EB", "#38BDF8", "#22D3EE")) -> str:
    p = max(0.0, min(100.0, float(pct or 0)))
    trilho = "rgba(148,163,184,.18)"
    if p <= 0:
        fundo = f"conic-gradient({trilho} 0% 100%)"
    elif p >= 100:
        fundo = f"conic-gradient({cores[0]} 0%,{cores[1]} 50%,{cores[2]} 100%)"
    else:
        fundo = f"conic-gradient({cores[0]} 0%,{cores[1]} {p * .55:.1f}%,{cores[2]} {p:.1f}%,{trilho} {p:.1f}% 100%)"
    return (f'<div class="cv-anel-box"><div class="cv-anel" role="img" aria-label="{esc(legenda)}: {esc(centro)}">'
            f'<div class="cv-anel-r" style="background:{fundo}"></div>'
            f'<div class="cv-anel-c"><b>{esc(centro)}</b><small>{esc(sub_centro)}</small></div></div>'
            f'<div class="cv-anel-leg">{esc(legenda)}</div></div>')


def sparkline(valores: list, cor: str = "#38BDF8") -> str:
    if not valores or max(valores) == 0:
        return ""
    w, h = 44, 20
    mx = max(valores)
    passo = w / max(1, len(valores) - 1)
    pts = " ".join(f"{i * passo:.1f},{h - 2 - (v / mx) * (h - 4):.1f}" for i, v in enumerate(valores))
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" aria-hidden="true"><polyline points="{pts}" '
            f'fill="none" stroke="{cor}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></polyline></svg>')


# ---------------------------------------------------------------------------
# Login, cabeçalho e visão geral
# ---------------------------------------------------------------------------
def login_card(modo: str, aviso: str | None = None, erro_config: bool = False) -> str:
    if erro_config:
        corpo = ('<div class="cv-nota al" style="text-align:left;margin-top:14px">' + ic("alerta") +
                 '<div>Falta configurar a senha do painel (<b>senha_hash</b> em [auth] no secrets). '
                 'Sem ela o acesso fica bloqueado. Veja o LEIA-ME.</div></div>')
    else:
        corpo = '<div class="cv-sec-s" style="margin-top:6px">Digite a senha do coordenador para entrar.</div>'
        if modo == "demo":
            corpo += ('<div class="cv-faixa" style="justify-content:center">' + ic("info") +
                      'Modo demonstração · senha: <b>demo2026</b></div>')
    if aviso:
        corpo += f'<div class="cv-faixa" style="justify-content:center">{ic("relogio")}{esc(aviso)}</div>'
    return (f'<div class="cv"><div class="cv-card cv-login"><div class="cv-login-ico">{ic("escudo", "gg")}</div>'
            f'<div class="cv-over" style="color:#7DD3FC">Acesso restrito</div>'
            f'<div class="cv-h1" style="font-size:28px;margin-top:6px">Campanha 2026</div>{corpo}</div></div>')


def marca(agora_txt: str, modo: str) -> str:
    return f"""<div class="cv"><div class="cv-topo">
<div class="cv-marca"><span class="cv-logo">{ic("escudo", "g")}</span><span><b>Campanha 2026</b><small>Centro de Comando</small></span></div>
<div style="display:flex;align-items:center;gap:6px">{'<span class="cv-demo">DEMO</span>' if modo == "demo" else ""}<div class="cv-status"><span class="cv-dot"></span>{esc(agora_txt)}</div></div>
</div></div>"""


def ferramentas() -> str:
    """Atalhos para as outras ferramentas: grandes, coloridos e com aviso de que abrem em nova aba."""
    cards = "".join(
        f'<a class="cv-tool {cor}" href="{url_segura(u)}" target="_blank" rel="noopener noreferrer" '
        f'aria-label="Abrir {esc(t)} em uma nova aba">'
        f'<span class="cv-tool-ico">{ic(i, "g")}</span>'
        f'<span class="cv-tool-txt"><b>{esc(t)}</b><small>{esc(desc)}</small></span>'
        f'<span class="cv-tool-btn">Abrir{ic("link", "p")}</span></a>'
        for t, desc, u, i, cor in LINKS)
    return (f'<div class="cv"><div class="cv-tools-h"><span class="cv-over">{ic("link", "p")} Outras ferramentas da campanha</span>'
            f'<span class="cv-tools-n">Abrem em uma nova aba · o painel continua aberto aqui</span></div>'
            f'<div class="cv-tools">{cards}</div></div>')


def cabecalho(contagem: dict, avisos: list) -> str:
    faixa = "".join(f'<div class="cv-faixa">{ic("alerta")}{esc(a)}</div>' for a in avisos)
    return f"""<div class="cv">
{faixa}
<div class="cv-hero">
<div><div class="cv-h1" role="heading" aria-level="1">Painel de Operações</div><div class="cv-lead">Base de apoiadores atualizada em tempo real</div></div>
<div class="cv-card cv-cont"><span class="cv-cont-ico">{ic(contagem.get("icone", "relogio"), "g")}</span>
<span><span class="cv-over">{esc(contagem["rotulo"])}</span><b>{esc(contagem["texto"])}</b></span>
<span class="cv-cont-num">{esc(contagem["numero"])}</span></div>
</div>
</div>"""


def visao_geral(total, meta, pct, mult_ok, n_mult, pct_mult, semana, kpi_html) -> str:
    sem_txt = f"+{fmt_int(semana)} esta semana" if semana else "nenhum nesta semana"
    return f"""<div class="cv"><div class="cv-ov">
<div class="cv-card cv-pad">
<div class="cv-cab"><span class="cv-titulo">Visão geral</span>{chip(sem_txt, "ok" if semana else "")}</div>
<div class="cv-aneis">
{anel(pct, f"{pct:.0f}%", "da meta", f"{fmt_int(total)} de {fmt_int(meta)} cadastros")}
{anel(pct_mult, f"{pct_mult:.0f}%", "na meta", f"{mult_ok} de {n_mult} multiplicadores", cores=("#16A34A", "#22D3EE", "#38BDF8"))}
</div>
</div>
<div class="cv-kpis">{kpi_html}</div>
</div></div>"""


# ---------------------------------------------------------------------------
# Lideranças
# ---------------------------------------------------------------------------
def _status_mult(m: dict) -> str:
    if m["ok"]:
        return chip("Meta batida", "ok", "check", pequeno=True)
    if m["total"] == 0:
        return chip("Sem cadastros", "al", "alerta", pequeno=True)
    if m["parado"]:
        return chip(f"Parado há {m['dias_sem']} dias", "al", "alerta", pequeno=True)
    return chip(f"Faltam {m['meta'] - m['total']}", "", pequeno=True)


def pessoa(p, detalhe_html: str = "", chips_html: str = "", icone: str = "pin") -> str:
    return (f'<div class="cv-pes"><div class="cv-pes-i"><b>{esc(p.NOME) or "Sem nome"}</b>'
            f'<span class="cv-meta cv-pi i-{icone}">{detalhe_html}</span>{chips_html}</div>{whats(p.WA, p.NOME)}</div>')


def _detalhe_local(p) -> str:
    partes = [esc(p.BAIRRO)]
    if SENSIVEL and p.TEL_FMT:
        partes.append(esc(p.TEL_FMT))
    if p.SECAO:
        partes.append(f"Seção {esc(p.SECAO)}")
    if pd.notna(p.DATA):
        partes.append(pd.Timestamp(p.DATA).strftime("%d/%m"))
    return " · ".join(partes)


def lista_lideres(lideres: list, abrir_lid: set, abrir_mult: set, dup_linhas: set, hoje_txt: str = "") -> str:
    blocos = []
    for lid in lideres:
        mults_html = []
        for m in lid["mults"]:
            pessoas = []
            for p in m["pessoas"].itertuples():
                extra = chip("Possível duplicata", "vm", "copia", pequeno=True) if p.LINHA in dup_linhas else ""
                pessoas.append(pessoa(p, _detalhe_local(p), f'<span class="cv-chips">{extra}</span>' if extra else ""))
            if m["dias_sem"] is None:
                ult = "Ainda sem cadastros"
            elif m["dias_sem"] == 0:
                ult = "Último cadastro hoje"
            else:
                ult = f"Último cadastro há {m['dias_sem']} dia{'s' if m['dias_sem'] > 1 else ''}"
            contato = (f'<a class="cv-wa-l" href="{esc(m["wa"])}" target="_blank" rel="noopener noreferrer">'
                       f'{ic("wa")}Falar com {esc(m["nome"].split(" ")[0])}</a>') if m["wa"] else ""
            tipo_barra = "ok" if m["ok"] else ("al" if m["parado"] else "")
            corpo = (f'<div class="cv-mul-corpo"><div class="cv-mul-ct"><span class="cv-meta">{ic("relogio", "p")}{esc(ult)}</span>{contato}</div>'
                     f'<div class="cv-pessoas duas">{"".join(pessoas) or "<span class=cv-meta>Nenhum cadastro ainda.</span>"}</div></div>')
            mults_html.append(
                f'<details class="cv-mul"{" open" if m["key"] in abrir_mult else ""}><summary>'
                f'<span class="cv-row" style="gap:10px"><span class="cv-ini">{esc(iniciais(m["nome"]))}</span>'
                f'<span class="cv-info" style="gap:4px;align-items:flex-start"><span class="cv-mul-nome">{esc(m["nome"])}</span>{_status_mult(m)}</span>'
                f'<span class="cv-mul-num">{m["total"]}/{m["meta"]}</span>{ic("chev", "cv-chev")}</span>'
                f'<span style="display:block;margin-top:9px">{barra(m["pct"], tipo_barra, fina=True)}</span>'
                f'</summary>{corpo}</details>')
        aviso_parados = chip(f"{lid['parados']} parado{'s' if lid['parados'] > 1 else ''}", "al", "alerta", True) if lid["parados"] else ""
        blocos.append(
            f'<details class="cv-lid"{" open" if lid["key"] in abrir_lid else ""}><summary>'
            f'<span class="cv-row"><span class="cv-rank {classe_rank(lid["pos"])}">{lid["pos"]}</span>'
            f'<span class="cv-info"><span class="cv-over">Líder</span><span class="cv-nome-l"><span class="cv-nome">{esc(lid["nome"])}</span>{_wa_mini(lid.get("wa", ""), lid["nome"])}</span>'
            f'<span class="cv-sub">{lid["n_mult"]} multiplicadores · {lid["na_meta"]} na meta</span></span>'
            f'<span class="cv-tot"><b>{fmt_int(lid["total"])}</b><small>de {fmt_int(lid["meta"])}</small></span>{ic("chev", "cv-chev g")}</span>'
            f'<span class="cv-prog">{barra(lid["pct"], "ok" if lid["pct"] >= 100 else "")}<b>{lid["pct"]}%</b></span>'
            f'</summary><div class="cv-corpo"><div class="cv-corpo-cab"><span class="cv-over">Multiplicadores</span>'
            f'<span class="cv-chips">{aviso_parados}{chip("meta de " + str(lid["mults"][0]["meta"]) + " cada" if lid["mults"] else "", "", None, True)}</span></div>'
            f'{"".join(mults_html)}</div></details>')
    return f'<div class="cv"><div class="cv-lista">{"".join(blocos)}</div></div>'


def mensagem_cobranca(m: dict) -> str:
    """Texto pronto (editável no WhatsApp) para retomar o contato com um multiplicador parado."""
    primeiro = str(m["nome"]).split()[0] if str(m["nome"]).split() else ""
    if m["total"] == 0:
        return (f"Oi {primeiro}, tudo bem? Aqui é da coordenação da campanha. Ainda não apareceu nenhum cadastro seu "
                f"no painel. Precisa de ajuda com o formulário? Me chama que eu te explico!")
    falta = max(m["meta"] - m["total"], 0)
    return (f"Oi {primeiro}, tudo bem? Aqui é da coordenação da campanha. Você já tem {m['total']} de {m['meta']} "
            f"cadastros no painel, faltam só {falta}! Bora retomar? Qualquer dúvida me chama.")


def botao_cobrar(m: dict) -> str:
    if not m["wa"]:
        return '<span class="cv-cobrar off" title="Sem WhatsApp válido na aba EQUIPE">Sem WhatsApp</span>'
    link = f'{m["wa"]}?text={quote(mensagem_cobranca(m))}'
    return (f'<a class="cv-cobrar i-wa" href="{esc(link)}" target="_blank" rel="noopener noreferrer" '
            f'aria-label="Cobrar {esc(m["nome"])} pelo WhatsApp com mensagem pronta">Cobrar</a>')


def card_parados(parados: list, limite: int = 10) -> str:
    if not parados:
        corpo = f'<div class="cv-meta" style="margin-top:10px">{ic("check")}Nenhum multiplicador parado. Equipe toda ativa!</div>'
    else:
        itens = []
        for m in parados[:limite]:
            quando = "sem cadastros" if m["total"] == 0 or m["dias_sem"] is None else f"há {m['dias_sem']} dias"
            itens.append(f'<div class="cv-top"><span class="cv-av" style="background:rgba(251,191,36,.16);color:#FCD34D">{esc(iniciais(m["nome"]))}</span>'
                         f'<span class="cv-info"><b>{esc(m["nome"])}</b><span class="cv-sub">Líder {esc(m["lider"])} · {m["total"]}/{m["meta"]} · {quando}</span></span>'
                         f'{botao_cobrar(m)}</div>')
        resto = len(parados) - limite
        mais = f'<div class="cv-mais">e mais {resto} multiplicador{"es" if resto > 1 else ""}</div>' if resto > 0 else ""
        corpo = f'<div class="cv-top-l">{"".join(itens)}{mais}</div>'
    return (f'<div class="cv"><div class="cv-card cv-pad"><div class="cv-cab"><span class="cv-titulo">Precisam de atenção</span>'
            f'{chip(str(len(parados)) + " parados", "al" if parados else "ok", "alerta" if parados else "check")}</div>'
            f'<div class="cv-sec-s" style="margin-top:4px">Sem cadastro há 7 dias ou mais e abaixo da meta. '
            f'<b>Cobrar</b> abre o WhatsApp com uma mensagem pronta, que você pode editar antes de enviar.</div>{corpo}</div></div>')


def card_top(mults: list, titulo: str = "Top 10 multiplicadores", rotulo: str = "campanha toda") -> str:
    itens = []
    for i, m in enumerate(mults, start=1):
        itens.append(f'<div class="cv-top"><span class="cv-av {classe_rank(i)}">{i}</span>'
                     f'<span class="cv-info"><b>{esc(m["nome"])}</b><span class="cv-sub">Líder {esc(m["lider"])}</span></span>'
                     f'<span class="cv-num">{m["total"]}</span></div>')
    corpo = "".join(itens) or '<div class="cv-meta">Sem cadastros ainda.</div>'
    return (f'<div class="cv"><div class="cv-card cv-pad"><div class="cv-cab"><span class="cv-titulo">{esc(titulo)}</span>'
            f'<span class="cv-over">{esc(rotulo)}</span></div><div class="cv-top-l">{corpo}</div></div></div>')


def card_semanal(serie: list, titulo: str = "Histórico de cadastros") -> str:
    vals = [s["n"] for s in serie]
    mx = max(vals) if vals and max(vals) > 0 else 1
    media = sum(vals) / len(vals) if vals else 0
    altura = 120
    top3 = sorted(range(len(vals)), key=lambda i: -vals[i])[:3]
    cols = "".join(
        f'<div class="cv-colx{" hi" if i in top3 and vals[i] > 0 else ""}"><span>{v}</span><i style="height:{max(3, v / mx * altura):.0f}px"></i></div>'
        for i, v in enumerate(vals))
    rot = "".join(f'<span>{esc(s["rotulo"])}</span>' for s in serie)
    linha_media = f'<div class="cv-media" style="bottom:{media / mx * altura:.0f}px"></div>' if media > 0 else ""
    return (f'<div class="cv"><div class="cv-card cv-pad"><div class="cv-cab"><span class="cv-titulo">{esc(titulo)}</span>'
            f'{chip("Média " + fmt_dec(media, 0) + "/semana", "az")}</div>'
            f'<div class="cv-sec-s">por semana · últimas {len(serie)} semanas · linha tracejada = média</div>'
            f'<div class="cv-cols">{linha_media}{cols}</div><div class="cv-rot">{rot}</div></div></div>')


def card_acumulado(serie: list, total: int, meta: int) -> str:
    """Total acumulado ao fim de cada semana, com a linha da meta."""
    vals = [s["n"] for s in serie]
    inicial = max(total - sum(vals), 0)  # cadastros anteriores à janela (ou sem data)
    acum, soma = [], inicial
    for v in vals:
        soma += v
        acum.append(soma)
    teto = max([meta] + acum) or 1
    altura = 120
    cols = "".join(
        f'<div class="cv-colx{" hi" if i == len(acum) - 1 else ""}"><span>{fmt_int(a)}</span>'
        f'<i style="height:{max(3, a / teto * altura):.0f}px;background:{"#22C55E" if meta and a >= meta else ""}"></i></div>'
        for i, a in enumerate(acum))
    rot = "".join(f'<span>{esc(s["rotulo"])}</span>' for s in serie)
    linha_meta = (f'<div class="cv-media" style="bottom:{meta / teto * altura:.0f}px;border-top-color:rgba(74,222,128,.7)">'
                  f'<span style="background:rgba(22,163,74,.7)">Meta {fmt_int(meta)}</span></div>') if meta else ""
    pct = total / meta * 100 if meta else 0
    return (f'<div class="cv"><div class="cv-card cv-pad"><div class="cv-cab"><span class="cv-titulo">Total acumulado</span>'
            f'{chip(f"{pct:.0f}% da meta", "ok" if pct >= 100 else "az")}</div>'
            f'<div class="cv-sec-s">quanto a base somava ao fim de cada semana · linha verde = meta</div>'
            f'<div class="cv-cols">{linha_meta}{cols}</div><div class="cv-rot">{rot}</div></div></div>')


# ---------------------------------------------------------------------------
# Rankings genéricos (bairros, veículos, apoios)
# ---------------------------------------------------------------------------
def ranking_card(titulo: str, itens: list, subtitulo: str = "", limite: int | None = None, rotulo_extra: str = "") -> str:
    """itens: lista de (nome, valor, texto_pequeno)."""
    if not itens:
        corpo = '<div class="cv-meta" style="margin-top:10px">Nada para mostrar ainda.</div>'
    else:
        mx = max(v for _, v, _ in itens) or 1
        mostrar = itens[:limite] if limite else itens
        linhas = []
        for i, (nome, valor, peq) in enumerate(mostrar, start=1):
            tipo = "ou" if i == 1 else ""
            linhas.append(f'<div class="cv-rk"><span class="cv-rk-p">{i}</span><span class="cv-rk-n">{esc(nome)}'
                          f'{"<small>" + esc(peq) + "</small>" if peq else ""}</span>{barra(valor / mx * 100, tipo, fina=True)}'
                          f'<span class="cv-rk-v">{fmt_int(valor)}</span></div>')
        if limite and len(itens) > limite:
            resto = "".join(
                f'<div class="cv-rk"><span class="cv-rk-p">{i}</span><span class="cv-rk-n">{esc(nome)}'
                f'{"<small>" + esc(peq) + "</small>" if peq else ""}</span>{barra(valor / mx * 100, "", fina=True)}'
                f'<span class="cv-rk-v">{fmt_int(valor)}</span></div>'
                for i, (nome, valor, peq) in enumerate(itens[limite:], start=limite + 1))
            linhas.append(f'<details class="cv-mul" style="margin-top:8px;background:transparent;border:0"><summary>'
                          f'<span class="cv-mais">Ver todos ({len(itens)}) {ic("chev", "p cv-chev")}</span></summary>{resto}</details>')
        corpo = f'<div style="margin-top:8px">{"".join(linhas)}</div>'
    sub = f'<div class="cv-sec-s">{esc(subtitulo)}</div>' if subtitulo else ""
    return (f'<div class="cv"><div class="cv-card cv-pad"><div class="cv-cab"><span class="cv-titulo">{esc(titulo)}</span>'
            f'{rotulo_extra}</div>{sub}{corpo}</div></div>')


def card_cobertura(com: int, sem_lista: list) -> str:
    total = com + len(sem_lista)
    pct = com / total * 100 if total else 0
    chips_sem = "".join(chip(b, "al", "pin") for b in sem_lista) or chip("Todos os bairros têm cadastro", "ok", "check")
    return (f'<div class="cv"><div class="cv-card cv-pad"><div class="cv-titulo">Cobertura de bairros</div>'
            f'<div class="cv-sec-s">Bairros da lista oficial com pelo menos um cadastro.</div>'
            f'<div style="display:flex;justify-content:center;margin:16px 0 8px">'
            f'{anel(pct, f"{pct:.0f}%", "cobertos", f"{com} de {total} bairros")}</div>'
            f'<div class="cv-over" style="margin:10px 0 8px">Sem nenhum cadastro</div><div class="cv-chips">{chips_sem}</div></div></div>')


def cards_bairros(resumo: pd.DataFrame, pessoas_por_bairro: dict, abrir: bool, posicoes: dict) -> str:
    cards = []
    for r in resumo.itertuples():
        pes = pessoas_por_bairro.get(r.bairro)
        if pes is None or len(pes) == 0:
            continue
        lista = "".join(
            pessoa(p, f'{esc(p.MULT)} · Líder {esc(p.LIDER)}' + (f" · Seção {esc(p.SECAO)}" if p.SECAO else ""), icone="rede")
            for p in pes.itertuples())
        pos = posicoes.get(r.bairro, 0)
        cards.append(
            f'<details class="cv-bai"{" open" if abrir else ""}><summary>'
            f'<span class="cv-row"><span class="cv-rank {classe_rank(pos)}" style="width:36px;height:36px;font-size:15px">{pos}</span>'
            f'<span class="cv-info"><span class="cv-nome" style="font-size:18px">{esc(r.bairro)}</span>'
            f'<span class="cv-sub">Líder mais forte: {esc(r.lider_top)} ({r.lider_top_n})</span></span>{ic("chev", "cv-chev g")}</span>'
            f'<span class="cv-mini"><span><small>Cadastros</small><b>{fmt_int(r.total)}</b></span>'
            f'<span><small>Líderes</small><b>{r.lideres}</b></span><span><small>Veículos</small><b>{r.veiculos}</b></span></span>'
            f'</summary><div class="cv-corpo" style="padding-top:12px">'
            f'{"<div class=cv-over>Mostrando " + str(len(pes)) + " de " + str(r.total) + "</div>" if len(pes) != r.total else ""}'
            f'<div class="cv-pessoas">{lista}</div></div></details>')
    if not cards:
        return vazio("Nenhum cadastro encontrado com esses filtros.")
    return f'<div class="cv"><div class="cv-grid2 tres">{"".join(cards)}</div></div>'


# ---------------------------------------------------------------------------
# Perfil
# ---------------------------------------------------------------------------
def cards_genero(perf: dict) -> str:
    m, f, n = perf["sexos"]["Masculino"], perf["sexos"]["Feminino"], perf["sexos"][NAO_INFORMADO]

    def card(rotulo, d, cor, icone):
        media = f"{fmt_dec(d['media'])} anos" if d["media"] is not None else "—"
        return (f'<div class="cv-card cv-gen"><div class="cv-kpi-h"><span class="cv-over">{rotulo}</span><span style="color:{cor}">{ic(icone, "g")}</span></div>'
                f'<span class="cv-num">{fmt_int(d["n"])}</span>'
                f'<span class="cv-chips">{chip(fmt_dec(d["pct"]) + "% da base", "az")}{chip("Idade média " + media)}</span>'
                f'{barra(d["pct"])}</div>')

    geral = perf["media_geral"]
    geral_card = (f'<div class="cv-card cv-gen"><div class="cv-kpi-h"><span class="cv-over">Idade média geral</span>'
                  f'<span class="cv-c-ambar">{ic("bolo", "g")}</span></div>'
                  f'<span class="cv-num">{fmt_dec(geral)}{" <small style=font-size:16px>anos</small>" if geral is not None else ""}</span>'
                  f'<span class="cv-chips">{chip("Mediana " + fmt_dec(perf["mediana"], 0) + " anos")}'
                  f'{chip(str(perf["sem_idade"]) + " sem data de nascimento", "al" if perf["sem_idade"] else "")}</span></div>')
    total = perf["total"] or 1
    split = (f'<div class="cv-split"><i style="width:{m["n"] / total * 100:.1f}%;background:#3B82F6"></i>'
             f'<i style="width:{f["n"] / total * 100:.1f}%;background:#67E8F9"></i></div>')
    leg = (f'<div class="cv-leg" style="margin-top:8px"><span><i style="background:#3B82F6"></i>Masculino {fmt_dec(m["pct"])}%</span>'
           f'<span><i style="background:#67E8F9"></i>Feminino {fmt_dec(f["pct"])}%</span>'
           f'{"<span><i style=background:rgba(148,163,184,.4)></i>Não informado " + fmt_dec(n["pct"]) + "%</span>" if n["n"] else ""}</div>')
    return (f'<div class="cv"><div class="cv-kpis" style="grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr))">'
            f'{card("Masculino", m, "#93C5FD", "pessoa")}{card("Feminino", f, "#67E8F9", "pessoa")}{geral_card}</div>'
            f'<div class="cv-card cv-pad" style="margin-top:12px"><div class="cv-over">Proporção da base</div>{split}{leg}</div></div>')


def card_piramide(perf: dict) -> str:
    mx = max([max(r["m"], r["f"]) for r in perf["piramide"]] + [1])
    linhas = "".join(
        f'<div class="cv-pir-r"><span class="cv-pir-l"><b>{r["m"]}</b><i style="width:{r["m"] / mx * 100:.0f}%"></i></span>'
        f'<span class="cv-pir-f">{esc(r["faixa"])}</span>'
        f'<span class="cv-pir-d"><i style="width:{r["f"] / mx * 100:.0f}%"></i><b>{r["f"]}</b></span></div>'
        for r in reversed(perf["piramide"]))
    return (f'<div class="cv"><div class="cv-card cv-pad"><div class="cv-cab"><span class="cv-titulo">Pirâmide etária</span>'
            f'<span class="cv-leg"><span><i style="background:#3B82F6"></i>Masc.</span><span><i style="background:#67E8F9"></i>Fem.</span></span></div>'
            f'<div class="cv-sec-s">Inclui 16–17 anos (voto facultativo).</div><div class="cv-pir">{linhas}</div></div></div>')


def card_aniversariantes(lista: list, limite: int = 12) -> str:
    if not lista:
        corpo = '<div class="cv-meta" style="margin-top:10px">Nenhum aniversariante nos próximos 7 dias.</div>'
    else:
        itens = []
        for a in lista[:limite]:
            quando = "Hoje!" if a["faltam"] == 0 else ("Amanhã" if a["faltam"] == 1 else a["data"].strftime("%d/%m"))
            itens.append(f'<div class="cv-top"><span class="cv-av" style="background:rgba(251,191,36,.16);color:#FCD34D">{ic("bolo")}</span>'
                         f'<span class="cv-info"><b>{esc(a["nome"])}</b><span class="cv-sub">{esc(quando)} · faz {a["idade"]} anos · {esc(a["bairro"])}</span></span>'
                         f'{whats(a["wa"], a["nome"])}</div>')
        resto = len(lista) - limite
        if resto > 0:
            itens.append(f'<div class="cv-mais">e mais {resto}</div>')
        corpo = f'<div class="cv-top-l">{"".join(itens)}</div>'
    return (f'<div class="cv"><div class="cv-card cv-pad"><div class="cv-cab"><span class="cv-titulo">Aniversariantes da semana</span>'
            f'{chip(str(len(lista)), "al" if lista else "")}</div><div class="cv-sec-s">Próximos 7 dias · um ótimo motivo para mandar mensagem.</div>{corpo}</div></div>')


def card_qualidade(q: dict, total: int) -> str:
    itens = [
        ("Sem data de nascimento", q["sem_nasc"]), ("CPF inválido", q["cpf_invalido"]), ("Sem CPF", q["sem_cpf"]),
        ("Título incompleto", q["titulo_invalido"]), ("WhatsApp inválido", q["tel_invalido"]),
        ("Sem sexo informado", q["sem_sexo"]), ("Sem seção", q["sem_secao"]), ("Sem bairro", q["sem_bairro"]),
    ]
    caixas = "".join(f'<span><b class="{"cv-c-ambar" if v else "cv-c-verde"}">{fmt_int(v)}</b><small>{esc(t)}</small></span>' for t, v in itens)
    fora = ""
    if q["fora_equipe"]:
        lista = "".join(chip(f'{x["MULT"]} ({x["QTD"]})', "al", "rede") for x in q["fora_equipe"])
        fora = (f'<div class="cv-over" style="margin:14px 0 8px">Multiplicadores fora da aba EQUIPE</div>'
                f'<div class="cv-sec-s" style="margin-bottom:8px">Cadastre na aba EQUIPE para ligar ao líder certo.</div><div class="cv-chips">{lista}</div>')
    return (f'<div class="cv"><div class="cv-card cv-pad"><div class="cv-titulo">Qualidade dos cadastros</div>'
            f'<div class="cv-sec-s">De {fmt_int(total)} cadastros, quantos têm algum dado faltando ou errado.</div>'
            f'<div class="cv-qual">{caixas}</div>{fora}</div></div>')


# ---------------------------------------------------------------------------
# Veículos e apoios
# ---------------------------------------------------------------------------
def card_veiculo(p) -> str:
    cor = (f'<span class="cv-cor" style="background:{esc(p.COR_HEX)}"></span>' if p.COR_HEX else "")
    placa = f'<span class="cv-placa"><small>BRASIL</small><b>{esc(p.PLACA)}</b></span>' if p.PLACA else ""
    chips = [chip(p.BAIRRO, "", "pin"), chip("Líder " + p.LIDER, "az")]
    if p.DIA_E:
        chips.append(chip("Dia da eleição", "ok", "check"))
    if p.ADESIVO:
        chips.append(chip("Adesivo", "", "etiqueta"))
    return (f'<div class="cv-card cv-vei"><div class="cv-vei-top"><span class="cv-vei-ico">{ic("carro", "g")}</span>'
            f'<span class="cv-info"><span class="cv-vei-mod">{esc(p.MODELO) or "Veículo"}</span>'
            f'<span class="cv-meta">{cor}{esc(p.COR) or "Cor não informada"}</span></span>{placa}</div>'
            f'<div class="cv-vei-mot">Motorista: <b>{esc(p.NOME)}</b> · via {esc(p.MULT)}</div>'
            f'<div class="cv-vei-pe"><span class="cv-chips">{"".join(chips)}</span>{whats(p.WA, p.NOME)}</div></div>')


def grade(cards: list, tres: bool = True, limite: int | None = None, total: int | None = None) -> str:
    if not cards:
        return vazio("Nenhum registro encontrado com esses filtros.")
    aviso = ""
    if limite and total and total > limite:
        aviso = f'<div class="cv-sec-s" style="margin-top:10px;text-align:center">Mostrando {limite} de {fmt_int(total)}. Use os filtros para achar alguém específico.</div>'
    return f'<div class="cv"><div class="cv-grid2{" tres" if tres else ""}">{"".join(cards)}</div>{aviso}</div>'


def card_apoio(p, tipo: str) -> str:
    detalhe = f'{esc(p.MULT)} · Líder {esc(p.LIDER)}'
    chips = [chip(p.BAIRRO, "", "pin")]
    if p.SECAO:
        chips.append(chip("Seção " + p.SECAO, ""))
    if tipo == "ADESIVO" and (p.MODELO or p.PLACA):
        chips.append(chip(f"{p.MODELO} {p.PLACA}".strip(), "az", "carro"))
    return pessoa(p, detalhe, f'<span class="cv-chips" style="margin-top:3px">{"".join(chips)}</span>', icone="rede")


# ---------------------------------------------------------------------------
# Duplicatas
# ---------------------------------------------------------------------------
def card_duplicata(g: dict) -> str:
    tipo = {"Alta": "vm", "Média": "al", "Baixa": ""}[g["confianca"]]
    cab = [chip(f"Confiança {g['confianca'].lower()}", tipo), chip("Coincide: " + " · ".join(g["criterios"]), "az")]
    if g["conflito"]:
        cab.append(chip("Líderes diferentes", "al", "alerta"))
    elif g["mesmo_mult"]:
        cab.append(chip("Mesmo multiplicador", ""))
    linhas = []
    for i, p in enumerate(g["membros"].itertuples()):
        quando = pd.Timestamp(p.DATA).strftime("%d/%m/%Y %H:%M") if pd.notna(p.DATA) else "sem data"
        docs = []
        if p.CPF:
            if SENSIVEL:
                docs.append("CPF " + (f"{p.CPF[:3]}.{p.CPF[3:6]}.{p.CPF[6:9]}-{p.CPF[9:]}" if len(p.CPF) == 11 else p.CPF))
            else:
                docs.append("CPF " + (f"***.{p.CPF[3:6]}.{p.CPF[6:9]}-**" if len(p.CPF) == 11 else "inválido"))
        if p.TITULO:
            docs.append("Título " + (p.TITULO if SENSIVEL else "••••" + p.TITULO[-4:]))
        if p.TEL_FMT:
            docs.append(p.TEL_FMT if SENSIVEL else f"{p.TEL_FMT[:5]} 9••••-{p.TEL_FMT[-4:]}" if len(p.TEL_FMT) > 9 else p.TEL_FMT)
        nasc = p.NASC.strftime("%d/%m/%Y") if p.NASC is not None and not pd.isna(p.NASC) else ""
        if i == 0:
            selo = chip("1º cadastro", "ok", "check", True)
        elif g["confianca"] == "Alta":
            selo = chip("Cópia", "vm", "copia", True)
        elif g["confianca"] == "Média":
            selo = chip("Conferir", "al", "alerta", True)
        else:
            selo = chip("Mesmo telefone", "", "wa", True)
        linhas.append(
            f'<div class="cv-dup-r"><span class="cv-linha"><small>Linha</small>{p.LINHA}</span>'
            f'<span class="cv-dup-i"><span class="cv-dup-n"><b>{esc(p.NOME)}</b>{selo}</span>'
            f'<span class="cv-meta">{ic("rede", "p")}<span>{esc(p.MULT)} → {esc(p.LIDER)}</span></span>'
            f'<span class="cv-meta">{ic("relogio", "p")}<span>{esc(quando)} · {esc(p.BAIRRO)}{(" · nasc. " + esc(nasc)) if nasc else ""}</span></span>'
            f'<span class="cv-meta">{ic("doc", "p")}<span>{esc(" · ".join(docs))}</span></span></span></div>')
    return (f'<div class="cv-card cv-dup"><div class="cv-chips">{"".join(cab)}</div>{"".join(linhas)}</div>')


# ---------------------------------------------------------------------------
# Relatórios e rodapé
# ---------------------------------------------------------------------------
def card_relatorio(titulo: str, descricao: str, itens: list, icone: str) -> str:
    li = "".join(f"<li>{esc(i)}</li>" for i in itens)
    return (f'<div class="cv"><div class="cv-card cv-rel"><span class="cv-rel-ico">{ic(icone, "g")}</span>'
            f'<span class="cv-titulo">{esc(titulo)}</span><span class="cv-sec-s">{esc(descricao)}</span><ul>{li}</ul></div></div>')


def tabela_resumo(lideres: list) -> str:
    linhas = "".join(
        f'<tr><td>{lid["pos"]}</td><td><b>{esc(lid["nome"])}</b></td><td class="n">{lid["n_mult"]}</td>'
        f'<td class="n so-pc">{lid["na_meta"]}</td><td class="n"><b>{fmt_int(lid["total"])}</b></td><td class="n so-pc">{fmt_int(lid["meta"])}</td>'
        f'<td class="n">{lid["pct"]}%</td></tr>' for lid in lideres)
    return (f'<div class="cv"><div class="cv-card cv-pad"><div class="cv-titulo">Prévia: resumo por liderança</div>'
            f'<div class="cv-tab-w"><table class="cv-tab"><thead><tr><th>#</th><th>Líder</th><th class="n">Mult.</th>'
            f'<th class="n so-pc">Na meta</th><th class="n">Cadastros</th><th class="n so-pc">Meta</th><th class="n">%</th></tr></thead>'
            f'<tbody>{linhas}</tbody></table></div></div></div>')


def rodape(modo: str, atualizado: str, versao: str = "") -> str:
    origem = "dados fictícios de demonstração" if modo == "demo" else "planilha do Google (somente leitura)"
    return (f'<div class="cv"><div class="cv-rodape">Campanha 2026 · Centro de Comando<br>'
            f'Fonte: {origem} · atualizado às {esc(atualizado)} · atualiza sozinho a cada minuto'
            f'{"<br>versão " + esc(versao) if versao else ""}</div></div>')


# ===========================================================================
# APP
# ===========================================================================
import hmac
import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Campanha 2026 · Centro de Comando",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

FUSO = ZoneInfo("America/Sao_Paulo")
ABAS = ["Lideranças", "Histórico", "Bairros", "Perfil", "Veículos", "Apoio Extra", "Duplicatas", "Relatórios"]
LIMITE_CARDS = 120


def html(conteudo: str):
    """Mostra HTML numa linha só (evita que o Markdown do Streamlit quebre o layout)."""
    st.markdown("".join(l.strip() for l in conteudo.splitlines() if l.strip()), unsafe_allow_html=True)


def segredo(*caminho, padrao=None):
    try:
        valor = st.secrets
        for parte in caminho:
            valor = valor[parte]
        return valor
    except Exception:
        return padrao


def modo_app() -> str:
    return "planilha" if str(segredo("app", "modo", padrao="demo")).strip().lower() == "planilha" else "demo"


def botao_download(rotulo, dados, arquivo, mime, chave):
    try:
        st.download_button(rotulo, data=dados, file_name=arquivo, mime=mime, key=chave, width="stretch")
    except TypeError:  # versões antigas do Streamlit
        st.download_button(rotulo, data=dados, file_name=arquivo, mime=mime, key=chave, use_container_width=True)


# ---------------------------------------------------------------------------
# Segurança
# ---------------------------------------------------------------------------
@st.cache_resource
def limitador_global():
    return S.Limitador(C.TENTATIVAS_GLOBAIS, C.JANELA_GLOBAL_MIN, C.BLOQUEIO_GLOBAL_MIN)


def exigir_login(modo: str):
    ss = st.session_state
    agora = time.time()
    if ss.get("auth_ok"):
        if agora - ss.get("auth_ultimo", 0) > C.MINUTOS_INATIVIDADE * 60:
            ss["auth_ok"] = False
            ss["aviso_login"] = "Sessão encerrada por inatividade. Entre novamente."
        else:
            ss["auth_ultimo"] = agora
            return

    hash_salvo = str(segredo("auth", "senha_hash", padrao="") or "").strip()
    if modo == "planilha" and not hash_salvo:
        html(ui.login_card(modo, erro_config=True))
        st.stop()

    html(ui.login_card(modo if not hash_salvo else "planilha", aviso=ss.pop("aviso_login", None)))
    _, meio, _ = st.columns([1, 2, 1])
    with meio:
        espera = max(limitador_global().segundos_bloqueado(), int(ss.get("bloqueio_ate", 0) - agora))
        if espera > 0:
            st.error(f"Acesso bloqueado por excesso de tentativas. Tente de novo em {max(1, round(espera / 60))} min.")
            st.stop()
        with st.form("login", clear_on_submit=True):
            senha = st.text_input("Senha de acesso", type="password", placeholder="Digite a senha")
            enviar = st.form_submit_button("Entrar no painel")
        if enviar:
            if hash_salvo:
                ok = S.conferir_senha(senha, hash_salvo)
            else:
                ok = modo == "demo" and hmac.compare_digest(senha.encode(), C.SENHA_DEMO.encode())
            if ok:
                ss["auth_ok"] = True
                ss["auth_ultimo"] = time.time()
                ss["erros"] = 0
                st.rerun()
            time.sleep(1.2)
            limitador_global().registrar_falha()
            ss["erros"] = ss.get("erros", 0) + 1
            if ss["erros"] >= C.TENTATIVAS_POR_SESSAO:
                ss["bloqueio_ate"] = time.time() + C.BLOQUEIO_SESSAO_MIN * 60
                ss["erros"] = 0
            st.error("Senha incorreta.")
    st.stop()


# ---------------------------------------------------------------------------
# Dados
# ---------------------------------------------------------------------------
def ler_google_sheets(planilha_id: str, abas: dict, cred_json: str) -> dict:
    import gspread
    from google.oauth2.service_account import Credentials

    cred = Credentials.from_service_account_info(
        json.loads(cred_json), scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    planilha = gspread.authorize(cred).open_by_key(planilha_id)
    por_titulo = {ws.title.strip().lower(): ws for ws in planilha.worksheets()}

    def achar(titulo, prefixos=()):
        ws = por_titulo.get(str(titulo).strip().lower())
        if ws is None:
            for t, w in por_titulo.items():
                if any(t.startswith(p) for p in prefixos):
                    return w
        return ws

    brutos = {}
    for chave_aba, titulo in abas.items():
        prefixos = ("respostas", "form responses") if chave_aba == "respostas" else ()
        ws = achar(titulo, prefixos)
        if ws is None and chave_aba == "respostas":
            raise ValueError(f"Não encontrei a aba de respostas '{titulo}' na planilha.")
        valores = ws.get_all_values() if ws is not None else []
        if not valores:
            brutos[chave_aba] = pd.DataFrame()
            continue
        cab, linhas = valores[0], valores[1:]
        linhas = [l + [""] * (len(cab) - len(l)) for l in linhas]
        brutos[chave_aba] = pd.DataFrame(linhas, columns=cab)
    return brutos


@st.cache_data(ttl=C.TTL_DADOS_SEG, show_spinner=False)
def carregar(modo: str, hoje_iso: str, planilha_id: str, abas_json: str, cred_json: str) -> dict:
    hoje = datetime.fromisoformat(hoje_iso).date()
    if modo == "demo":
        brutos = gerar_demo(hoje=hoje)
    else:
        brutos = ler_google_sheets(planilha_id, json.loads(abas_json), cred_json)
    base = P.preparar(brutos, hoje=hoje)
    lideres = P.ranking_liderancas(base)
    grupos = P.encontrar_duplicatas(base["cadastros"])
    return {
        "base": base,
        "lideres": lideres,
        "semanal": P.serie_semanal(base["cadastros"], hoje),
        "semanal_todo": P.serie_campanha(base["cadastros"], hoje),
        "ritmo": P.ritmo_recente(base["cadastros"], hoje),
        "bairros": P.resumo_bairros(base),
        "perfil": P.perfil(base),
        "aniversariantes": P.aniversariantes(base["cadastros"], hoje),
        "locais": P.top_locais(base["cadastros"]),
        "veiculos": P.resumo_veiculos(base),
        "duplicatas": grupos,
        "dup_linhas": P.linhas_duplicadas(grupos),
        "qualidade": P.qualidade(base),
        "carregado": datetime.now(FUSO).strftime("%H:%M"),
    }


def parametros_dados(modo: str) -> tuple:
    hoje_iso = datetime.now(FUSO).date().isoformat()
    if modo == "demo":
        return (modo, hoje_iso, "", "{}", "{}")
    abas = dict(C.ABAS_PADRAO)
    for k in abas:
        abas[k] = str(segredo("planilha", f"aba_{k}", padrao=abas[k]))
    cred = segredo("gcp_service_account", padrao=None)
    planilha_id = str(segredo("planilha", "id", padrao="") or "").strip()
    if not cred or not planilha_id:
        html(ui.nota("O modo <b>planilha</b> está ligado, mas faltam o <b>id</b> da planilha ou a credencial "
                     "<b>gcp_service_account</b> no secrets. Veja o passo a passo no LEIA-ME.", "al", "alerta"))
        st.stop()
    return (modo, hoje_iso, planilha_id, json.dumps(abas, sort_keys=True), json.dumps(dict(cred), sort_keys=True))


@st.cache_data(ttl=C.TTL_DADOS_SEG, show_spinner=False)
def arquivos_liderancas(parametros: tuple, sensivel: bool):
    d = carregar(*parametros)
    return R.excel_liderancas(d["lideres"], sensivel), R.pdf_liderancas(d["lideres"], sensivel)


@st.cache_data(ttl=C.TTL_DADOS_SEG, show_spinner=False)
def arquivos_veiculos(parametros: tuple, sensivel: bool):
    v = carregar(*parametros)["veiculos"]
    return (R.excel_veiculos(v["df"], v["por_bairro"], sensivel),
            R.pdf_veiculos(v["df"], v["por_bairro"], sensivel))


@st.cache_data(ttl=C.TTL_DADOS_SEG, show_spinner=False)
def arquivo_apoios(parametros: tuple, sensivel: bool):
    return R.excel_apoios(carregar(*parametros)["base"]["cadastros"], sensivel)


# ---------------------------------------------------------------------------
# Topo
# ---------------------------------------------------------------------------
def contagem_regressiva(hoje, total: int = 0, semanal_todo: list | None = None) -> dict:
    dias = (C.DATA_ELEICAO - hoje).days
    rotulo = f"Contagem · Eleição {C.DATA_ELEICAO.strftime('%d/%m/%Y')}"
    if dias > 1:
        return {"rotulo": rotulo, "texto": f"Faltam {dias} dias", "numero": str(dias)}
    if dias == 1:
        return {"rotulo": rotulo, "texto": "Falta 1 dia!", "numero": "1"}
    if dias == 0:
        return {"rotulo": rotulo, "texto": "É hoje! Dia da eleição", "numero": "0"}
    # Depois da eleição o cartão vira um balanço da campanha.
    melhor = max(semanal_todo or [], key=lambda s: s["n"], default=None)
    texto = "cadastros na campanha"
    if melhor and melhor["n"]:
        texto += f" · melhor semana {melhor['rotulo']} ({P.fmt_int(melhor['n'])})"
    return {"rotulo": f"Balanço · eleição de {C.DATA_ELEICAO.strftime('%d/%m/%Y')}", "texto": texto,
            "numero": P.fmt_int(total), "icone": "trofeu"}


def barra_topo(modo: str):
    """Marca, horário e as ações principais (atualizar e sair) sempre no alto."""
    agora = datetime.now(FUSO).strftime("%d/%m · %H:%M")
    html(ui.marca(agora, modo))
    with st.container(key="barra_topo"):
        c_atualizar, c_sair = st.columns(2)
        with c_atualizar:
            if st.button("↻ Atualizar", key="atualizar", help="Busca agora os cadastros mais recentes da planilha"):
                limpar_caches()
                st.rerun()
        with c_sair:
            if st.button("Sair", key="sair", help="Fecha o painel neste aparelho"):
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.rerun()


def limpar_caches():
    carregar.clear()
    arquivos_liderancas.clear()
    arquivos_veiculos.clear()
    arquivo_apoios.clear()


def topo(d: dict, modo: str):
    base, lideres = d["base"], d["lideres"]
    hoje = base["hoje"]
    total = len(base["cadastros"])
    meta = sum(l["meta"] for l in lideres)
    n_mult = sum(l["n_mult"] for l in lideres)
    mult_ok = sum(l["na_meta"] for l in lideres)
    lideres_reais = [l for l in lideres if l["key"] != P.chave(P.SEM_LIDER)]
    semanal = d["semanal"]
    resumo_b, _ = d["bairros"]
    v = d["veiculos"]
    html(ui.cabecalho(contagem_regressiva(hoje, total, d["semanal_todo"]), base["avisos"]))
    html(ui.ferramentas())

    vals = [s["n"] for s in semanal]
    kpi_html = "".join([
        ui.kpi("Cadastros", P.fmt_int(total), "users",
               f'<span class="cv-c-verde">+{P.fmt_int(vals[-1] if vals else 0)} na semana</span>{ui.sparkline(vals)}'),
        ui.kpi("Multiplicadores", P.fmt_int(n_mult), "rede", f"em {len(lideres_reais)} lideranças", "cv-c-azul"),
        ui.kpi("Bairros", P.fmt_int(len(resumo_b)), "pin",
               f"{ui.esc(resumo_b.iloc[0]['bairro'])} no topo" if len(resumo_b) else "—"),
        ui.kpi("Veículos", P.fmt_int(v["total"]), "carro", f"{v['dia_e']} confirmados Dia E", "cv-c-ambar"),
    ])
    pct = total / meta * 100 if meta else 0
    pct_mult = mult_ok / n_mult * 100 if n_mult else 0
    html(ui.visao_geral(total, meta, pct, mult_ok, n_mult, pct_mult, vals[-1] if vals else 0, kpi_html))


# ---------------------------------------------------------------------------
# Abas
# ---------------------------------------------------------------------------
def aba_liderancas(d: dict):
    lideres = d["lideres"]
    n_mult = sum(l["n_mult"] for l in lideres)
    na_meta = sum(l["na_meta"] for l in lideres)
    n_lideres = sum(1 for l in lideres if l["key"] != P.chave(P.SEM_LIDER))
    html(ui.secao("Ranking de lideranças",
                  "Toque no líder para abrir os multiplicadores. Toque no multiplicador para ver as pessoas cadastradas.",
                  [ui.chip(f"{na_meta} de {n_mult} multiplicadores na meta", "ok", "check"),
                   ui.chip(f"Meta: {C.META_POR_MULTIPLICADOR} por multiplicador", "", "estrela"),
                   ui.chip(f"{n_lideres} lideranças", "az", "users")]))
    busca = st.text_input("Buscar líder ou multiplicador", placeholder="Buscar líder ou multiplicador…",
                          key="busca_lideranca", label_visibility="collapsed")

    abrir_lid, abrir_mult, mostrar = set(), set(), lideres
    termo = P.chave(busca)
    if termo:
        mostrar = []
        for lid in lideres:
            achou_lid = termo in P.chave(lid["nome"])
            mults = [m for m in lid["mults"] if termo in P.chave(m["nome"])]
            if achou_lid or mults:
                mostrar.append(lid)
                if mults:
                    abrir_lid.add(lid["key"])
                    abrir_mult.update(m["key"] for m in mults)

    todos_mults = [m for lid in lideres for m in lid["mults"]]
    parados = sorted([m for m in todos_mults if m["parado"]],
                     key=lambda m: (m["total"] > 0, -(m["dias_sem"] or 999), m["nome"]))
    top = sorted(todos_mults, key=lambda m: (-m["total"], m["nome"]))[:10]

    col1, col2 = st.columns([1.75, 1], gap="large")
    with col1:
        if mostrar:
            html(ui.lista_lideres(mostrar, abrir_lid, abrir_mult, d["dup_linhas"]))
        elif not lideres:
            html(ui.vazio("Nenhum cadastro ainda. Assim que o formulário receber respostas, o ranking aparece aqui."))
        else:
            html(ui.vazio("Nenhum líder ou multiplicador com esse nome."))
    with col2:
        html(ui.card_parados(parados))
        html(ui.card_top(top))
        html(ui.nota("O gráfico de cadastros por semana agora fica na aba <b>Histórico</b>.", "", "grafico"))


def busca_geral(d: dict, limite: int = 30):
    """Busca rápida em toda a base: nome, bairro, multiplicador, líder ou telefone."""
    busca = st.text_input("Buscar apoiador", key="busca_geral",
                          placeholder="Buscar apoiador por nome, bairro, multiplicador, líder ou telefone…",
                          help="Procura em todos os cadastros. Apague o texto para fechar os resultados.")
    termo = P.chave(busca)
    if not termo:
        return
    cad = d["base"]["cadastros"]
    achou = (cad["NOME_KEY"].str.contains(termo, regex=False, na=False)
             | cad["BAIRRO_KEY"].str.contains(termo, regex=False, na=False)
             | cad["MULT"].map(P.chave).str.contains(termo, regex=False, na=False)
             | cad["LIDER"].map(P.chave).str.contains(termo, regex=False, na=False))
    digitos = P.so_digitos(busca)
    if len(digitos) >= 4:
        achou |= cad["TEL"].str.contains(digitos, regex=False, na=False)
    res = cad[achou].sort_values("NOME")
    chips = [ui.chip(f"{P.fmt_int(len(res))} encontrado{'s' if len(res) != 1 else ''}", "az" if len(res) else "al", "busca")]
    if len(res) > limite:
        chips.append(ui.chip(f"mostrando {limite}: refine a busca", "", "info"))
    html(ui.secao(f"Resultado para “{busca.strip()}”", "", chips))
    if res.empty:
        html(ui.vazio("Ninguém encontrado. Confira a grafia ou tente só parte do nome."))
        return
    cartoes = "".join(
        ui.pessoa(p, ui._detalhe_local(p),
                  f'<span class="cv-chips">{ui.chip("Mult. " + p.MULT, "az", None, True)}{ui.chip("Líder " + p.LIDER, "", None, True)}</span>')
        for p in res.head(limite).itertuples())
    html(f'<div class="cv"><div class="cv-busca-r">{cartoes}</div></div>')


def aba_historico(d: dict):
    serie = d["semanal_todo"]
    vals = [s["n"] for s in serie]
    total = len(d["base"]["cadastros"])
    meta = sum(l["meta"] for l in d["lideres"])
    hoje = d["base"]["hoje"]
    esta, anterior = (vals[-1] if vals else 0), (vals[-2] if len(vals) > 1 else 0)
    media = sum(vals) / len(vals) if vals else 0
    melhor = max(serie, key=lambda s: s["n"], default=None)
    falta = max(meta - total, 0)

    if anterior:
        var = (esta - anterior) / anterior * 100
        comp = f'<span class="{"cv-c-verde" if var >= 0 else "cv-c-ambar"}">{"+" if var >= 0 else ""}{var:.0f}% vs. anterior</span>'
    else:
        comp = '<span>sem semana anterior</span>'
    if falta == 0:
        meta_txt, meta_val = "meta batida!", "✓"
    elif (C.DATA_ELEICAO - hoje).days > 0:
        semanas = max(1, -(-(C.DATA_ELEICAO - hoje).days // 7))
        meta_txt, meta_val = f"≈ {P.fmt_int(-(-falta // semanas))} por semana até a eleição", P.fmt_int(falta)
    else:
        meta_txt, meta_val = "ficaram faltando", P.fmt_int(falta)

    html(ui.secao("Histórico de cadastros",
                  "Como a base cresceu semana a semana. Use para ver o ritmo da equipe e comparar períodos.",
                  [ui.chip(f"{len(serie)} semanas", "az", "grafico"),
                   ui.chip(f"Média {P.fmt_dec(media, 0)}/semana", "", "estrela")]))
    html(ui.kpis([
        ui.kpi("Esta semana", P.fmt_int(esta), "grafico", comp, "cv-c-ciano"),
        ui.kpi("Média semanal", P.fmt_dec(media, 0), "relogio", f"em {len(serie)} semanas", "cv-c-azul"),
        ui.kpi("Melhor semana", P.fmt_int(melhor["n"]) if melhor else "—", "trofeu",
               f"semana de {ui.esc(melhor['rotulo'])}" if melhor else "", "cv-c-ambar"),
        ui.kpi("Para a meta", meta_val, "estrela", meta_txt, "cv-c-verde"),
    ]))
    col1, col2 = st.columns([1.75, 1], gap="large")
    with col1:
        janela = serie[-16:]  # mais que isso espreme as colunas no celular
        html(ui.card_semanal(janela, "Cadastros por semana"))
        html(ui.card_acumulado(janela, total, meta))
    with col2:
        html(ui.card_top(d["ritmo"], "Em ritmo agora", "últimos 14 dias") if d["ritmo"] else
             ui.vazio("Nenhum cadastro nos últimos 14 dias."))
        html(ui.nota("<b>Em ritmo agora</b> mostra quem mais cadastrou nos <b>últimos 14 dias</b>. "
                     "É um bom termômetro de quem está engajado neste momento.", "", "info"))


def aba_bairros(d: dict):
    cad = d["base"]["cadastros"]
    resumo, sem = d["bairros"]
    html(ui.secao("Mapeamento por bairro", "Ranking de cadastros por bairro, cobertura e explorador de apoiadores."))
    if resumo.empty:
        html(ui.vazio("Ainda não há cadastros com bairro informado."))
        return
    topo_b = resumo.iloc[0]
    media = len(cad) / len(resumo) if len(resumo) else 0
    html(ui.kpis([
        ui.kpi("Bairros com cadastro", P.fmt_int(len(resumo)), "pin", "na base atual"),
        ui.kpi("Maior base", topo_b["bairro"], "trofeu", f'{P.fmt_int(topo_b["total"])} cadastros', "cv-c-ambar"),
        ui.kpi("Sem cadastro", P.fmt_int(len(sem)), "alerta", "da lista oficial", "cv-c-ambar" if sem else "cv-c-verde"),
        ui.kpi("Média por bairro", P.fmt_dec(media), "grafico", "cadastros", "cv-c-azul"),
    ]))
    col1, col2 = st.columns([1.5, 1], gap="large")
    with col1:
        itens = [(r.bairro, r.total, f"{r.lideres} líd. · {r.veiculos} veíc.") for r in resumo.itertuples()]
        html(ui.ranking_card("Ranking de bairros", itens, "Do bairro com mais cadastros para o com menos.", limite=12))
    with col2:
        html(ui.card_cobertura(len(resumo), sem))

    html(ui.secao("Explorador de bairros", "Filtre por bairro ou procure uma pessoa pelo nome."))
    f1, f2 = st.columns(2)
    with f1:
        escolha = st.selectbox("Bairro", ["Todos os bairros"] + list(resumo["bairro"]), key="filtro_bairro")
    with f2:
        busca = st.text_input("Nome da pessoa", placeholder="Ex.: Maria, José da Silva…", key="busca_bairro")
    filtrado = cad
    if escolha != "Todos os bairros":
        filtrado = filtrado[filtrado.BAIRRO.eq(escolha)]
    termo = P.chave(busca)
    if termo:
        filtrado = filtrado[filtrado.NOME_KEY.str.contains(termo, regex=False)]
    res = resumo[resumo.bairro.isin(set(filtrado.BAIRRO))]
    pessoas = {b: g.sort_values("NOME") for b, g in filtrado.groupby("BAIRRO")}
    posicoes = {b: i for i, b in enumerate(resumo["bairro"], start=1)}
    html(ui.cards_bairros(res, pessoas, abrir=bool(termo) or escolha != "Todos os bairros", posicoes=posicoes))


def aba_perfil(d: dict):
    perf = d["perfil"]
    html(ui.secao("Perfil demográfico", "Gênero, idade e dados que ajudam a falar com cada público."))
    html(ui.cards_genero(perf))
    col1, col2 = st.columns(2, gap="large")
    with col1:
        html(ui.card_piramide(perf))
        itens = [(l["local"], l["total"], l["bairro"]) for l in d["locais"]]
        html(ui.ranking_card("Top locais de votação", itens, "Onde estão mais apoiadores, pela seção informada."))
    with col2:
        html(ui.card_aniversariantes(d["aniversariantes"]))
        html(ui.card_qualidade(d["qualidade"], perf["total"]))


def aba_veiculos(d: dict):
    v = d["veiculos"]
    html(ui.secao("Frota de apoio", "Veículos cadastrados, onde estão e quem confirmou o dia da eleição."))
    html(ui.kpis([
        ui.kpi("Veículos", P.fmt_int(v["total"]), "carro", f"{P.fmt_dec(v['pct'])}% da base"),
        ui.kpi("Bairros cobertos", P.fmt_int(v["bairros"]), "pin", "com pelo menos 1", "cv-c-azul"),
        ui.kpi("Dia da eleição", P.fmt_int(v["dia_e"]), "urna", "motoristas confirmados", "cv-c-verde"),
        ui.kpi("Com adesivo", P.fmt_int(v["adesivo"]), "etiqueta", "veículos adesivados", "cv-c-ambar"),
    ]))
    if v["total"] == 0:
        html(ui.vazio("Nenhum veículo cadastrado ainda."))
        return
    col1, col2 = st.columns(2, gap="large")
    with col1:
        itens = [(r.bairro, r.total, "") for r in v["por_bairro"].itertuples()]
        html(ui.ranking_card("Veículos por bairro", itens, "Do maior para o menor.", limite=10))
    with col2:
        itens = [(r.lider, r.total, "") for r in v["por_lider"].itertuples()]
        html(ui.ranking_card("Veículos por liderança", itens, "Quem trouxe mais motoristas.", limite=10))

    html(ui.secao("Lista de veículos", "Filtre por bairro, modelo, placa ou nome do motorista."))
    f1, f2 = st.columns(2)
    with f1:
        escolha = st.selectbox("Bairro", ["Todos os bairros"] + list(v["por_bairro"]["bairro"]), key="filtro_veic_bairro")
    with f2:
        busca = st.text_input("Buscar", placeholder="Ex.: Onix, prata, ABC1D23, João…", key="busca_veic")
    so_dia_e = st.checkbox("Mostrar só os confirmados para o dia da eleição", key="so_dia_e")
    df = v["df"]
    if escolha != "Todos os bairros":
        df = df[df.BAIRRO.eq(escolha)]
    termo = P.chave(busca)
    if termo:
        alvo = (df.NOME_KEY + " " + df.MODELO.map(P.chave) + " " + df.COR.map(P.chave) + " "
                + df.PLACA.map(P.chave).str.replace(" ", "", regex=False) + " " + df.MULT.map(P.chave))
        df = df[alvo.str.contains(termo, regex=False)
                | alvo.str.contains(termo.replace(" ", ""), regex=False)]
    if so_dia_e:
        df = df[df.DIA_E]
    ordem = {b: i for i, b in enumerate(v["por_bairro"]["bairro"])}
    df = df.assign(_o=df.BAIRRO.map(ordem)).sort_values(["_o", "NOME"])
    cards = [ui.card_veiculo(p) for p in df.head(LIMITE_CARDS).itertuples()]
    html(ui.grade(cards, limite=LIMITE_CARDS, total=len(df)))


def aba_apoio(d: dict):
    cad = d["base"]["cadastros"]
    opcoes = {"Adesivo veicular": ("ADESIVO", "etiqueta"), "Bandeiras": ("BANDEIRA", "bandeira"),
              "Dia da eleição": ("DIA_E", "urna")}
    html(ui.secao("Apoio extra", "Quem topou ajudar além do voto: adesivo no carro, bandeira e trabalho no dia da eleição."))
    escolha = st.radio("Tipo de apoio", list(opcoes), horizontal=True, key="tipo_apoio", label_visibility="collapsed")
    col_flag, _ = opcoes[escolha]
    html(ui.kpis([
        ui.kpi(nome, P.fmt_int(int(cad[c].sum())), icone, f"{P.fmt_dec(cad[c].mean() * 100 if len(cad) else 0)}% da base",
               "cv-c-ciano", ativo=(nome == escolha))
        for nome, (c, icone) in opcoes.items()
    ], quatro=False))
    sub = cad[cad[col_flag]]
    if sub.empty:
        html(ui.vazio(f"Ninguém marcou '{escolha}' ainda."))
        return
    col1, col2 = st.columns(2, gap="large")
    with col1:
        itens = [(b, n, "") for b, n in sub.BAIRRO.value_counts().items()]
        html(ui.ranking_card(f"{escolha} por bairro", itens, limite=8))
    with col2:
        itens = [(b, n, "") for b, n in sub.LIDER.value_counts().items()]
        html(ui.ranking_card(f"{escolha} por liderança", itens, limite=8))
    f1, f2 = st.columns(2)
    with f1:
        bairro = st.selectbox("Bairro", ["Todos os bairros"] + sorted(sub.BAIRRO.unique()), key="filtro_apoio_bairro")
    with f2:
        busca = st.text_input("Nome", placeholder="Buscar pessoa…", key="busca_apoio")
    if bairro != "Todos os bairros":
        sub = sub[sub.BAIRRO.eq(bairro)]
    termo = P.chave(busca)
    if termo:
        sub = sub[sub.NOME_KEY.str.contains(termo, regex=False)]
    sub = sub.sort_values(["BAIRRO", "NOME"])
    cards = [ui.card_apoio(p, col_flag) for p in sub.head(LIMITE_CARDS).itertuples()]
    html(ui.grade(cards, limite=LIMITE_CARDS, total=len(sub)))


def aba_duplicatas(d: dict):
    grupos = d["duplicatas"]
    html(ui.secao("Cadastros duplicados", "Comparação por nome completo, CPF, título de eleitor e WhatsApp."))
    envolvidos = sum(len(g["membros"]) for g in grupos)
    html(ui.kpis([
        ui.kpi("Grupos encontrados", P.fmt_int(len(grupos)), "copia", "possíveis repetições"),
        ui.kpi("Cadastros envolvidos", P.fmt_int(envolvidos), "users", "somando os grupos", "cv-c-azul"),
        ui.kpi("Confiança alta", P.fmt_int(sum(g["confianca"] == "Alta" for g in grupos)), "alerta",
               "CPF, título ou nome + nascimento", "cv-c-rosa"),
        ui.kpi("Líderes diferentes", P.fmt_int(sum(g["conflito"] for g in grupos)), "rede",
               "mesma pessoa em 2 redes", "cv-c-ambar"),
    ]))
    html(ui.nota("<b>Como limpar:</b> confira os líderes de cada grupo e apague na planilha a linha da cópia. "
                 "O <b>1º cadastro</b> é o mais antigo. Apague <b>de baixo para cima</b> (maior número de linha primeiro), "
                 "porque ao apagar uma linha as de baixo sobem. O painel atualiza em até 1 minuto. "
                 "<b>Confiança baixa</b> (só telefone) costuma ser família usando o mesmo número."))
    f1, f2 = st.columns(2)
    with f1:
        conf = st.selectbox("Confiança", ["Todas", "Alta", "Média", "Baixa"], key="filtro_conf")
    with f2:
        busca = st.text_input("Nome", placeholder="Buscar nome…", key="busca_dup")
    so_conflito = st.checkbox("Mostrar só a mesma pessoa cadastrada por líderes diferentes", key="so_conflito")
    mostrar = grupos
    if conf != "Todas":
        mostrar = [g for g in mostrar if g["confianca"] == conf]
    if so_conflito:
        mostrar = [g for g in mostrar if g["conflito"]]
    termo = P.chave(busca)
    if termo:
        mostrar = [g for g in mostrar if g["membros"].NOME_KEY.str.contains(termo, regex=False).any()]
    if not grupos:
        html(ui.vazio("Nenhuma duplicata encontrada. Base limpa!"))
    else:
        html(ui.grade([ui.card_duplicata(g) for g in mostrar], tres=False))
    html(ui.card_qualidade(d["qualidade"], len(d["base"]["cadastros"])))


def aba_relatorios(d: dict, parametros: tuple):
    html(ui.secao("Relatórios", "Arquivos prontos para imprimir, mandar no grupo ou trabalhar no Excel."))
    hoje = d["base"]["hoje"].strftime("%Y-%m-%d")
    xlsx = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    col1, col2, col3 = st.columns(3, gap="medium")
    with col1:
        html(ui.card_relatorio(
            "Cadastros por liderança", "Do líder com mais cadastros para o com menos, com todos os multiplicadores e pessoas.",
            ["Resumo das lideranças e metas", "Multiplicadores em ordem decrescente", "Lista completa de cadastros",
             "Uma aba por líder (Excel)"], "users"))
        with st.spinner("Gerando arquivos…"):
            x, p = arquivos_liderancas(parametros, ui.SENSIVEL)
        botao_download("Baixar Excel", x, f"cadastros_por_lideranca_{hoje}.xlsx", xlsx, "dl_lid_x")
        botao_download("Baixar PDF", p, f"cadastros_por_lideranca_{hoje}.pdf", "application/pdf", "dl_lid_p")
    with col2:
        html(ui.card_relatorio(
            "Gestão de veículos por bairro", "Frota separada por bairro, do bairro com mais veículos para o com menos.",
            ["Motorista, modelo, cor e placa", "WhatsApp, líder e multiplicador", "Quem confirmou o dia da eleição",
             "Quem tem adesivo"], "carro"))
        with st.spinner("Gerando arquivos…"):
            x, p = arquivos_veiculos(parametros, ui.SENSIVEL)
        botao_download("Baixar Excel", x, f"veiculos_por_bairro_{hoje}.xlsx", xlsx, "dl_vei_x")
        botao_download("Baixar PDF", p, f"veiculos_por_bairro_{hoje}.pdf", "application/pdf", "dl_vei_p")
    with col3:
        html(ui.card_relatorio(
            "Listas de apoio extra", "Uma aba para cada tipo de apoio, organizada por bairro.",
            ["Adesivo veicular", "Bandeiras", "Trabalho no dia da eleição", "Com WhatsApp para contato"], "bandeira"))
        with st.spinner("Gerando arquivo…"):
            x = arquivo_apoios(parametros, ui.SENSIVEL)
        botao_download("Baixar Excel", x, f"apoio_extra_{hoje}.xlsx", xlsx, "dl_apo_x")
    if ui.SENSIVEL:
        html(ui.nota("<b>Dados sensíveis VISÍVEIS:</b> os arquivos saem com CPF, título, nascimento e WhatsApp completos. "
                     "Não repasse em grupos. Para gerar a versão protegida, volte o botão lá em cima para RESTRITO.",
                     "al", "alerta"))
    else:
        html(ui.nota("<b>Modo RESTRITO:</b> os arquivos saem sem CPF, título e nascimento, e com o WhatsApp mascarado "
                     "(ex.: (22) 9••••-3456). Para a versão completa, ligue o botão de dados sensíveis lá em cima.",
                     "", "escudo"))
    html(ui.tabela_resumo(d["lideres"]))


# ---------------------------------------------------------------------------
# Página
# ---------------------------------------------------------------------------
def main():
    st.markdown(ui.estilo(), unsafe_allow_html=True)
    modo = modo_app()
    exigir_login(modo)

    parametros = parametros_dados(modo)
    try:
        with st.spinner("Carregando a base…"):
            d = carregar(*parametros)
    except Exception as erro:  # mostra o motivo sem expor detalhes técnicos
        html(ui.nota(f"<b>Não consegui ler a planilha.</b> Confira se ela foi compartilhada com o e-mail da conta de "
                     f"serviço e se o ID e os nomes das abas estão certos no secrets.<br><small>{ui.esc(type(erro).__name__)}: "
                     f"{ui.esc(str(erro)[:200])}</small>", "al", "alerta"))
        st.stop()

    barra_topo(modo)
    topo(d, modo)
    rotulo_sensivel = "Mostrar CPF, título, nascimento e telefone completos"
    ajuda_sensivel = ("Desligado (recomendado): esses dados ficam mascarados na tela e nos relatórios. "
                      "Ligue só quando precisar e desligue ao terminar.")
    try:
        visivel = st.toggle(rotulo_sensivel, key="sensivel", value=False, help=ajuda_sensivel)
    except AttributeError:  # Streamlit muito antigo
        visivel = st.checkbox(rotulo_sensivel, key="sensivel", value=False, help=ajuda_sensivel)
    ui.SENSIVEL = bool(visivel)
    html(ui.selo_sigilo(ui.SENSIVEL))
    busca_geral(d)

    contadores = {"Duplicatas": len(d["duplicatas"]), "Veículos": d["veiculos"]["total"]}
    aba = st.radio("Seções do painel", ABAS, horizontal=True, key="aba", label_visibility="collapsed",
                   format_func=lambda a: f"{a} ({P.fmt_int(contadores[a])})" if contadores.get(a) else a)

    if aba == "Lideranças":
        aba_liderancas(d)
    elif aba == "Histórico":
        aba_historico(d)
    elif aba == "Bairros":
        aba_bairros(d)
    elif aba == "Perfil":
        aba_perfil(d)
    elif aba == "Veículos":
        aba_veiculos(d)
    elif aba == "Apoio Extra":
        aba_apoio(d)
    elif aba == "Duplicatas":
        aba_duplicatas(d)
    else:
        aba_relatorios(d, parametros)

    html(ui.rodape(modo, d["carregado"], C.VERSAO))


main()
