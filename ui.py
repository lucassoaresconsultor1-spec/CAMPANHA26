"""Visual "Azul Vidro": CSS e componentes HTML do painel.

Todo texto vindo da planilha passa por esc() antes de ir para a tela,
para ninguém conseguir injetar código pelo formulário.
"""
from __future__ import annotations

import html as _html
from urllib.parse import quote

import pandas as pd

from processamento import NAO_INFORMADO, fmt_dec, fmt_int


SENSIVEL = False  # muda pelo botão VISÍVEL/RESTRITO do painel

LINKS = [
    ("Painel Carona Amiga", "Corridas do dia", "https://projcaronaamiga.netlify.app/painel.html", "carro"),
    ("Onde eu voto", "Busca por seção", "https://projlocaldevotacao.netlify.app/", "urna"),
    ("Mapa de escolas", "Locais da zona", "https://mapa2026.streamlit.app/", "mapa"),
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
        return ('<div class="cv"><div class="cv-nota al">' + ic("alerta") + '<div><b>VISÍVEL</b> · CPF, título, '
                'nascimento e telefone aparecem completos na tela e nos relatórios. Desligue ao terminar.</div></div></div>')
    return ('<div class="cv"><div class="cv-chips">' + chip("RESTRITO · dados sensíveis protegidos", "ok", "escudo")
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


def cabecalho(agora_txt: str, modo: str, contagem: dict, avisos: list) -> str:
    faixa = '<div class="cv-links">' + "".join(
        f'<a class="cv-link" href="{esc(u)}" target="_blank" rel="noopener"><span class="cv-link-ico">{ic(i)}</span>'
        f'<span><b>{esc(t)}</b><br><small>{esc(st)}</small></span></a>' for t, st, u, i in LINKS) + "</div>"
    for a in avisos:
        faixa += f'<div class="cv-faixa">{ic("alerta")}{esc(a)}</div>'
    return f"""<div class="cv">
<div class="cv-topo">
<div class="cv-marca"><span class="cv-logo">{ic("escudo", "g")}</span><span><b>Campanha 2026</b><small>Centro de Comando</small></span></div>
<div style="display:flex;align-items:center;gap:6px">{'<span class="cv-demo">DEMO</span>' if modo == "demo" else ""}<div class="cv-status"><span class="cv-dot"></span>{esc(agora_txt)}</div></div>
</div>
{faixa}
<div class="cv-hero">
<div><div class="cv-h1" role="heading" aria-level="1">Painel de Operações</div><div class="cv-lead">Base de apoiadores atualizada em tempo real</div></div>
<div class="cv-card cv-cont"><span class="cv-cont-ico">{ic("relogio", "g")}</span>
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


def card_parados(parados: list, limite: int = 10) -> str:
    if not parados:
        corpo = f'<div class="cv-meta" style="margin-top:10px">{ic("check")}Nenhum multiplicador parado. Equipe toda ativa!</div>'
    else:
        itens = []
        for m in parados[:limite]:
            quando = "sem cadastros" if m["total"] == 0 or m["dias_sem"] is None else f"há {m['dias_sem']} dias"
            itens.append(f'<div class="cv-top"><span class="cv-av" style="background:rgba(251,191,36,.16);color:#FCD34D">{esc(iniciais(m["nome"]))}</span>'
                         f'<span class="cv-info"><b>{esc(m["nome"])}</b><span class="cv-sub">Líder {esc(m["lider"])} · {m["total"]}/{m["meta"]} · {quando}</span></span>'
                         f'{whats(m["wa"], m["nome"])}</div>')
        resto = len(parados) - limite
        mais = f'<div class="cv-mais">e mais {resto} multiplicador{"es" if resto > 1 else ""}</div>' if resto > 0 else ""
        corpo = f'<div class="cv-top-l">{"".join(itens)}{mais}</div>'
    return (f'<div class="cv"><div class="cv-card cv-pad"><div class="cv-cab"><span class="cv-titulo">Precisam de atenção</span>'
            f'{chip(str(len(parados)) + " parados", "al" if parados else "ok", "alerta" if parados else "check")}</div>'
            f'<div class="cv-sec-s" style="margin-top:4px">Sem cadastro há 7 dias ou mais e abaixo da meta.</div>{corpo}</div></div>')


def card_top(mults: list, titulo: str = "Top 10 multiplicadores") -> str:
    itens = []
    for i, m in enumerate(mults, start=1):
        itens.append(f'<div class="cv-top"><span class="cv-av {classe_rank(i)}">{i}</span>'
                     f'<span class="cv-info"><b>{esc(m["nome"])}</b><span class="cv-sub">Líder {esc(m["lider"])}</span></span>'
                     f'<span class="cv-num">{m["total"]}</span></div>')
    corpo = "".join(itens) or '<div class="cv-meta">Sem cadastros ainda.</div>'
    return (f'<div class="cv"><div class="cv-card cv-pad"><div class="cv-cab"><span class="cv-titulo">{esc(titulo)}</span>'
            f'<span class="cv-over">campanha toda</span></div><div class="cv-top-l">{corpo}</div></div></div>')


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


def rodape(modo: str, atualizado: str) -> str:
    origem = "dados fictícios de demonstração" if modo == "demo" else "planilha do Google (somente leitura)"
    return (f'<div class="cv"><div class="cv-rodape">Campanha 2026 · Centro de Comando<br>'
            f'Fonte: {origem} · atualizado às {esc(atualizado)} · atualiza sozinho a cada minuto</div></div>')
