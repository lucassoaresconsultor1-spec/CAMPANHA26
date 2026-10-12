"""Tratamento e análise dos dados (sem Streamlit, para poder ser testado).

Entrada: as abas brutas da planilha (ou do gerador de demonstração).
Saída: cadastros padronizados + rankings, duplicatas e indicadores.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date, timedelta

import pandas as pd

from config import DIAS_PARADO, META_POR_MULTIPLICADOR

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
