"""Relatórios para download (Excel e PDF). Não depende do Streamlit."""
from __future__ import annotations

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


def _linhas_pessoas(lideres: list) -> pd.DataFrame:
    linhas = []
    for lid in lideres:
        for pos_m, m in enumerate(lid["mults"], start=1):
            for p in m["pessoas"].itertuples():
                linhas.append({
                    "Pos. líder": lid["pos"], "Líder": lid["nome"], "Pos. multiplicador": pos_m,
                    "Multiplicador": m["nome"], "Nome": p.NOME, "WhatsApp": p.TEL_FMT, "Bairro": p.BAIRRO,
                    "Seção": p.SECAO, "Local de votação": p.LOCAL, "Data do cadastro": _data_fmt(p.DATA),
                    "Linha na planilha": p.LINHA,
                })
    return pd.DataFrame(linhas, columns=["Pos. líder", "Líder", "Pos. multiplicador", "Multiplicador", "Nome",
                                         "WhatsApp", "Bairro", "Seção", "Local de votação", "Data do cadastro",
                                         "Linha na planilha"])


def excel_liderancas(lideres: list) -> bytes:
    resumo = pd.DataFrame([{
        "Posição": lid["pos"], "Líder": lid["nome"], "Multiplicadores": lid["n_mult"],
        "Cadastros": lid["total"], "Meta": lid["meta"], "% da meta": lid["pct"],
        "Multiplicadores na meta": lid["na_meta"], "Multiplicadores parados": lid["parados"],
    } for lid in lideres])
    mults = pd.DataFrame([{
        "Pos. líder": lid["pos"], "Líder": lid["nome"], "Multiplicador": m["nome"], "Cadastros": m["total"],
        "Meta": m["meta"], "% da meta": m["pct"],
        "Situação": "Meta batida" if m["ok"] else ("Parado" if m["parado"] else f"Faltam {m['meta'] - m['total']}"),
        "Dias sem cadastrar": "" if m["dias_sem"] is None else m["dias_sem"], "WhatsApp": m["tel"],
    } for lid in lideres for m in lid["mults"]])
    pessoas = _linhas_pessoas(lideres)

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


def _df_veiculos(v: pd.DataFrame, ordem_bairros: list) -> pd.DataFrame:
    pos = {b: i for i, b in enumerate(ordem_bairros)}
    v = v.assign(_o=v["BAIRRO"].map(pos)).sort_values(["_o", "NOME"])
    return pd.DataFrame({
        "Bairro": v["BAIRRO"], "Motorista": v["NOME"], "Modelo": v["MODELO"], "Cor": v["COR"],
        "Placa": v["PLACA"], "WhatsApp": v["TEL_FMT"], "Líder": v["LIDER"], "Multiplicador": v["MULT"],
        "Dia da eleição": v["DIA_E"].map(_sim), "Adesivo": v["ADESIVO"].map(_sim),
        "Seção": v["SECAO"], "Linha na planilha": v["LINHA"],
    })


def excel_veiculos(v: pd.DataFrame, por_bairro: pd.DataFrame) -> bytes:
    ordem = list(por_bairro["bairro"])
    resumo = por_bairro.rename(columns={"bairro": "Bairro", "total": "Veículos"})
    resumo.insert(0, "Posição", range(1, len(resumo) + 1))
    tabela = _df_veiculos(v, ordem)
    buf = BytesIO()
    with _escritor(buf) as w:
        _planilha(w, resumo, "Por bairro")
        _planilha(w, tabela, "Veículos")
    return buf.getvalue()


def excel_apoios(cad: pd.DataFrame) -> bytes:
    def tabela(df):
        df = df.sort_values(["BAIRRO", "NOME"])
        return pd.DataFrame({
            "Nome": df["NOME"], "WhatsApp": df["TEL_FMT"], "Bairro": df["BAIRRO"], "Líder": df["LIDER"],
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


def pdf_liderancas(lideres: list) -> bytes:
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
            linhas = [[i, p.NOME, p.TEL_FMT, p.BAIRRO, p.SECAO,
                       pd.Timestamp(p.DATA).strftime("%d/%m/%y") if pd.notna(p.DATA) else ""]
                      for i, p in enumerate(m["pessoas"].itertuples(), start=1)]
            t = _tabela(["#", "Nome", "WhatsApp", "Bairro", "Seção", "Cadastro"], linhas,
                        [9 * mm, largura - 108 * mm, 30 * mm, 36 * mm, 13 * mm, 20 * mm])
            hist.append(KeepTogether([cab, t]) if len(linhas) <= 12 else cab)
            if len(linhas) > 12:
                hist.append(t)
    doc.build(hist, onFirstPage=rodape, onLaterPages=rodape)
    return buf.getvalue()


def pdf_veiculos(v: pd.DataFrame, por_bairro: pd.DataFrame) -> bytes:
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
        linhas = [[p.NOME, p.MODELO, p.COR, p.PLACA, p.TEL_FMT, p.LIDER, p.MULT, _sim(p.DIA_E), _sim(p.ADESIVO)]
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
