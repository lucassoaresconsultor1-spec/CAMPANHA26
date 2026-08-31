import pandas as pd
import streamlit as st

# 1. Configuração da página Streamlit
st.set_page_config(
    page_title="Dashboard Campanha 2026 - Gestão Estratégica",
    layout="wide",
    page_icon="📊",
)

st.title("📊 Painel de Controle e Inteligência Eleitoral - Campanha 2026")

# 2. Conexão direta com Google Sheets (Aba 'cadastro')
ID_PLANILHA = "1YBtjLKdfZ-waj_s51MauE7Zo5xYs_TnjjhiT_WkA9Rc"
URL_GOOGLE_SHEETS = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/gviz/tq?tqx=out:csv&sheet=cadastro"


@st.cache_data(ttl=30)
def carregar_dados_nuvem(url):
    df = pd.read_csv(url)

    # Tratamento e Limpeza da coluna de Liderança
    df["INDICAÇÃO/LIDER"] = (
        df["INDICAÇÃO/LIDER"]
        .fillna("DESCONHECIDO")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Unificação do BEBETO e Reatribuição do TIAGO RODRIGUES
    mapeamento_correcoes = {
        "BEBETO BARCELOS": "BEBETO",
        "BEBETO ": "BEBETO",
        "JOAO LUIZ DA SILVA": "TIAGO RODRIGUES",
        "JOÃO LUIZ DIAS DA SILVA": "TIAGO RODRIGUES",
        "YASMIM MENDONÇA": "TIAGO RODRIGUES",
        "YASMIM MENDONCA": "TIAGO RODRIGUES",
    }
    df["INDICAÇÃO/LIDER"] = df["INDICAÇÃO/LIDER"].replace(
        mapeamento_correcoes
    )

    # Tratamento de Bairros
    df["Bairro_Limpo"] = (
        df["Bairro"].fillna("Não Informado").astype(str).str.strip().str.title()
    )

    # Cálculo de Idade
    df["Data_Nasc"] = pd.to_datetime(
        df["Data de Nascimento"], errors="coerce", dayfirst=True
    )
    df["Idade"] = 2026 - df["Data_Nasc"].dt.year

    # Mapeamento de Frota de Veículos
    df["POSSUI_VEICULO"] = (
        df["POSSUI VEICULO? MODELO/COR/PLACA"]
        .fillna("NÃO")
        .astype(str)
        .str.upper()
    )
    df["TEM_VEICULO_BOOL"] = ~df["POSSUI_VEICULO"].str.contains(
        "NÃO|NAO|N/A|SEM", regex=True
    )

    return df


try:
    df = carregar_dados_nuvem(URL_GOOGLE_SHEETS)

    # --- MÉTRICAS DE IMPACTO NO TOPO ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="Total de Cadastros Válidos",
            value=len(df),
            help="Total de apoiadores registrados",
        )
    with col2:
        st.metric(
            label="Líderes Ativos",
            value=df["INDICAÇÃO/LIDER"].nunique(),
            help="Total de multiplicadores captando",
        )
    with col3:
        st.metric(
            label="Bairros Cobertos",
            value=df["Bairro_Limpo"].nunique(),
            help="Presença territorial em bairros",
        )
    with col4:
        st.metric(
            label="Veículos Mapeados (Dia E)",
            value=int(df["TEM_VEICULO_BOOL"].sum()),
            help="Carros e motos para suporte eleitoral",
        )

    st.markdown("---")

    # --- NAVEGAÇÃO POR EIXOS ESTRATÉGICOS ---
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "👥 1. Gestão de Lideranças",
            "📍 2. Listagem de Apoiadores por Bairro",
            "🎯 3. Perfil Demográfico",
            "🚗 4. Veículos Disponíveis",
        ]
    )

    # -------------------------------------------------------------
    # EIXO 1: LIDERANÇAS
    # -------------------------------------------------------------
    with tab1:
        st.subheader("1. Desempenho e Produtividade dos Multiplicadores")

        col_a, col_b = st.columns([1, 1])

        with col_a:
            st.markdown("##### Ranking de Captadores")
            resumo_lideres = (
                df["INDICAÇÃO/LIDER"]
                .value_counts()
                .reset_index()
                .rename(
                    columns={
                        "INDICAÇÃO/LIDER": "Líder",
                        "count": "Total de Apoiadores",
                    }
                )
            )
            resumo_lideres["% da Base"] = (
                (resumo_lideres["Total de Apoiadores"] / len(df)) * 100
            ).round(1).astype(str) + "%"

            st.dataframe(resumo_lideres, use_container_width=True)

        with col_b:
            st.markdown("##### Volume por Líder")
            st.bar_chart(
                data=resumo_lideres, x="Líder", y="Total de Apoiadores"
            )

        st.info(
            "💡 **Diagnóstico Operacional:** LUIS FELIPE e BEBETO representam **64,5%** de todos os cadastros."
        )

    # -------------------------------------------------------------
    # EIXO 2: LISTAGEM DE APOIADORES POR BAIRRO
    # -------------------------------------------------------------
    with tab2:
        st.subheader("📍 Relação Detalhada de Bairros e Apoiadores Inclusos")

        # Filtro por bairro
        bairros_disponiveis = ["TODOS OS BAIRROS"] + sorted(
            df["Bairro_Limpo"].unique().tolist()
        )
        bairro_selecionado = st.selectbox(
            "🔍 Filtrar por Bairro Específico:", bairros_disponiveis
        )

        if bairro_selecionado != "TODOS OS BAIRROS":
            df_bairros_filtrado = df[
                df["Bairro_Limpo"] == bairro_selecionado
            ]
        else:
            df_bairros_filtrado = df

        # Ordenação dos bairros pelo volume decrescente de apoiadores
        bairros_ordenados = (
            df_bairros_filtrado["Bairro_Limpo"]
            .value_counts()
            .index.tolist()
        )

        for bairro in bairros_ordenados:
            apoiadores_bairro = df_bairros_filtrado[
                df_bairros_filtrado["Bairro_Limpo"] == bairro
            ]
            qtd_apoiadores = len(apoiadores_bairro)

            with st.expander(
                f"🏘️ **{bairro}** — ({qtd_apoiadores} apoiador(es) cadastrado(s))",
                expanded=True,
            ):
                tabela_bairro = apoiadores_bairro[
                    [
                        "Nome",
                        "Contato",
                        "INDICAÇÃO/LIDER",
                        "Local de Votação",
                        "POSSUI VEICULO? MODELO/COR/PLACA",
                    ]
                ].rename(
                    columns={
                        "INDICAÇÃO/LIDER": "Líder Responsável",
                        "POSSUI VEICULO? MODELO/COR/PLACA": "Veículo",
                    }
                )

                st.dataframe(
                    tabela_bairro,
                    use_container_width=True,
                    hide_index=True,
                )

    # -------------------------------------------------------------
    # EIXO 3: PERFIL DEMOGRÁFICO
    # -------------------------------------------------------------
    with tab3:
        st.subheader("3. Perfil Demográfico do Eleitorado")

        df["Sexo_Limpo"] = (
            df["Sexo"].fillna("NÃO INFORMADO").astype(str).str.strip().str.upper()
        )

        col_g1, col_g2 = st.columns([1, 1])

        with col_g1:
            st.markdown("##### Resumo por Gênero e Idade Média")

            demografia_genero = df.groupby("Sexo_Limpo").agg(
                Quantidade=("Nome", "count"),
                Idade_Media=("Idade", "mean"),
            ).reset_index()

            demografia_genero.rename(
                columns={"Sexo_Limpo": "Gênero"}, inplace=True
            )

            demografia_genero["% da Base"] = (
                (demografia_genero["Quantidade"] / len(df)) * 100
            ).round(1).astype(str) + "%"

            demografia_genero["Idade Média"] = demografia_genero[
                "Idade_Media"
            ].apply(
                lambda x: f"{x:.1f} anos" if pd.notnull(x) and x > 0 else "N/A"
            )

            tabela_genero = demografia_genero[
                ["Gênero", "Quantidade", "% da Base", "Idade Média"]
            ]

            st.dataframe(
                tabela_genero, use_container_width=True, hide_index=True
            )

            idade_media_geral = df["Idade"].mean()
            if pd.notnull(idade_media_geral):
                st.metric(
                    "Média de Idade Geral da Base", f"{idade_media_geral:.1f} anos"
                )

        with col_g2:
            st.markdown("##### Distribuição por Faixa Etária")
            df_idade_valida = df.dropna(subset=["Idade"])
            if not df_idade_valida.empty:
                faixas = pd.cut(
                    df_idade_valida["Idade"],
                    bins=[0, 24, 34, 49, 64, 100],
                    labels=["18-24", "25-34", "35-49", "50-64", "65+"],
                )
                df_faixas = faixas.value_counts().reset_index()
                df_faixas.columns = ["Faixa Etária", "Quantidade"]
                st.bar_chart(data=df_faixas, x="Faixa Etária", y="Quantidade")

    # -------------------------------------------------------------
    # EIXO 4: VEÍCULOS DISPONÍVEIS
    # -------------------------------------------------------------
    with tab4:
        st.subheader("🚗 4. Relação de Apoiadores com Veículos Disponíveis")

        # Filtrar apenas quem possui veículo
        df_veiculos = df[df["TEM_VEICULO_BOOL"]].copy()

        # Métricas rápidas sobre a frota
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            st.metric(
                label="Total de Veículos Registrados",
                value=len(df_veiculos),
            )
        with col_v2:
            st.metric(
                label="Bairros Cobertos com Veículo",
                value=df_veiculos["Bairro_Limpo"].nunique(),
            )

        st.markdown("---")

        # Filtro opcional por bairro na aba de veículos
        bairros_com_veiculo = ["TODOS OS BAIRROS"] + sorted(
            df_veiculos["Bairro_Limpo"].unique().tolist()
        )
        bairro_v_selecionado = st.selectbox(
            "🔍 Filtrar Veículos por Bairro:", bairros_com_veiculo
        )

        if bairro_v_selecionado != "TODOS OS BAIRROS":
            df_veiculos_exibicao = df_veiculos[
                df_veiculos["Bairro_Limpo"] == bairro_v_selecionado
            ]
        else:
            df_veiculos_exibicao = df_veiculos

        # Tabela completa de apoiadores com veículo
        tabela_veiculos = df_veiculos_exibicao[
            [
                "Nome",
                "Contato",
                "Bairro_Limpo",
                "INDICAÇÃO/LIDER",
                "POSSUI VEICULO? MODELO/COR/PLACA",
            ]
        ].rename(
            columns={
                "Bairro_Limpo": "Bairro",
                "INDICAÇÃO/LIDER": "Líder Responsável",
                "POSSUI VEICULO? MODELO/COR/PLACA": "Descrição do Veículo",
            }
        )

        st.dataframe(
            tabela_veiculos,
            use_container_width=True,
            hide_index=True,
        )

except Exception as e:
    st.error(f"❌ Ocorreu um erro ao carregar o dashboard: {e}")
    