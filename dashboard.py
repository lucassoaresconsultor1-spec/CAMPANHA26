"""Campanha 2026 · Centro de Comando (Streamlit).

Rodar no computador:   streamlit run dashboard.py
Modo demonstração: funciona sem configurar nada (senha demo2026).
Modo planilha: configure o secrets (veja LEIA-ME.md).
"""
from __future__ import annotations

import hmac
import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

import config as C
import processamento as P
import relatorios as R
import seguranca as S
import ui
from demo import gerar_demo

st.set_page_config(
    page_title="Campanha 2026 · Centro de Comando",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

FUSO = ZoneInfo("America/Sao_Paulo")
ABAS = ["Lideranças", "Bairros", "Perfil", "Veículos", "Apoio Extra", "Duplicatas", "Relatórios"]
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
def arquivos_liderancas(parametros: tuple):
    d = carregar(*parametros)
    return R.excel_liderancas(d["lideres"]), R.pdf_liderancas(d["lideres"])


@st.cache_data(ttl=C.TTL_DADOS_SEG, show_spinner=False)
def arquivos_veiculos(parametros: tuple):
    v = carregar(*parametros)["veiculos"]
    return R.excel_veiculos(v["df"], v["por_bairro"]), R.pdf_veiculos(v["df"], v["por_bairro"])


@st.cache_data(ttl=C.TTL_DADOS_SEG, show_spinner=False)
def arquivo_apoios(parametros: tuple):
    return R.excel_apoios(carregar(*parametros)["base"]["cadastros"])


# ---------------------------------------------------------------------------
# Topo
# ---------------------------------------------------------------------------
def contagem_regressiva(hoje) -> dict:
    dias = (C.DATA_ELEICAO - hoje).days
    rotulo = f"Contagem · Eleição {C.DATA_ELEICAO.strftime('%d/%m/%Y')}"
    if dias > 1:
        return {"rotulo": rotulo, "texto": f"Faltam {dias} dias", "numero": str(dias)}
    if dias == 1:
        return {"rotulo": rotulo, "texto": "Falta 1 dia!", "numero": "1"}
    if dias == 0:
        return {"rotulo": rotulo, "texto": "É hoje! Dia da eleição", "numero": "0"}
    n = abs(dias)
    return {"rotulo": rotulo, "texto": f"Realizada há {n} dia{'s' if n > 1 else ''}", "numero": str(n)}


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
    agora = datetime.now(FUSO).strftime("%d/%m · %H:%M")
    html(ui.cabecalho(agora, modo, contagem_regressiva(hoje), base["avisos"]))

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
        html(ui.card_semanal(d["semanal"]))


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
            x, p = arquivos_liderancas(parametros)
        botao_download("Baixar Excel", x, f"cadastros_por_lideranca_{hoje}.xlsx", xlsx, "dl_lid_x")
        botao_download("Baixar PDF", p, f"cadastros_por_lideranca_{hoje}.pdf", "application/pdf", "dl_lid_p")
    with col2:
        html(ui.card_relatorio(
            "Gestão de veículos por bairro", "Frota separada por bairro, do bairro com mais veículos para o com menos.",
            ["Motorista, modelo, cor e placa", "WhatsApp, líder e multiplicador", "Quem confirmou o dia da eleição",
             "Quem tem adesivo"], "carro"))
        with st.spinner("Gerando arquivos…"):
            x, p = arquivos_veiculos(parametros)
        botao_download("Baixar Excel", x, f"veiculos_por_bairro_{hoje}.xlsx", xlsx, "dl_vei_x")
        botao_download("Baixar PDF", p, f"veiculos_por_bairro_{hoje}.pdf", "application/pdf", "dl_vei_p")
    with col3:
        html(ui.card_relatorio(
            "Listas de apoio extra", "Uma aba para cada tipo de apoio, organizada por bairro.",
            ["Adesivo veicular", "Bandeiras", "Trabalho no dia da eleição", "Com WhatsApp para contato"], "bandeira"))
        with st.spinner("Gerando arquivo…"):
            x = arquivo_apoios(parametros)
        botao_download("Baixar Excel", x, f"apoio_extra_{hoje}.xlsx", xlsx, "dl_apo_x")
    html(ui.nota("Os relatórios não trazem CPF nem título de eleitor completos, para reduzir o risco caso um arquivo "
                 "seja repassado. Guarde e compartilhe só com quem precisa.", "al", "escudo"))
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

    topo(d, modo)
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    aba = st.radio("Seções do painel", ABAS, horizontal=True, key="aba", label_visibility="collapsed")

    if aba == "Lideranças":
        aba_liderancas(d)
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

    html(ui.rodape(modo, d["carregado"]))
    b1, b2 = st.columns(2)
    with b1:
        if st.button("Atualizar dados agora", key="atualizar"):
            carregar.clear()
            arquivos_liderancas.clear()
            arquivos_veiculos.clear()
            arquivo_apoios.clear()
            st.rerun()
    with b2:
        if st.button("Sair do painel", key="sair"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


main()
