from __init__ import *

VERSION_APP = "1.0.0"
VERSION_REFDATE = "2024-07-10"
ENVIRONMENT = os.getenv("ENVIRONMENT")
SCRIPT_NAME = os.path.basename(__file__)

if ENVIRONMENT == "DEVELOPMENT":
    print(f"{SCRIPT_NAME.upper()} - {ENVIRONMENT} - {VERSION_APP} - {VERSION_REFDATE}")

append_paths()

# -----------------------------------------------------------------------

from datetime import date
from io import BytesIO
from time import sleep

import pandas as pd
import plotly.express as px
import streamlit as st

from streamlitPanel.streamlit_helper import gerencialFront
from tools.db_helper import SQL_Manager
from tools.py_tools import FuncoesPyTools

st.set_page_config(
    page_title="Strix Capital - Painel de Controle",
    page_icon="🦉",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "manager_sql" not in st.session_state:
    st.session_state.manager_sql = SQL_Manager()

if "funcoes_pytools" not in st.session_state:
    st.session_state.funcoes_pytools = FuncoesPyTools(st.session_state.manager_sql)

if "manager_ger" not in st.session_state:
    st.session_state.manager_ger = gerencialFront(
        manager_sql=st.session_state.manager_sql,
        funcoes_pytools=st.session_state.funcoes_pytools,
    )

lista_states = ["fluxo_caixas", "gerencial"]

for state in lista_states:
    if state not in st.session_state:
        st.session_state[state] = False


def save_to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine="xlsxwriter")
    df.to_excel(writer, index=False, sheet_name="Sheet1")
    writer.close()
    processed_data = output.getvalue()
    return processed_data


def desliga_states():
    for state in lista_states:
        st.session_state[state] = False


def select_state(select):
    for state in lista_states:
        if state == select:
            st.session_state[state] = True
        else:
            st.session_state[state] = False


def LogoStrix():
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 0.01])
        col2.image(
            os.path.join(base_path, "streamlitPanel", "static", "logotipo_strix.png"),  # type: ignore
            width=500,
        )


def fluxo_projetado(x):
    return x["FLUXO_DESCONTADO"] * x["QUANTIDADE_D0"]


def format_value(x):
    return f"{x:,.0f}"


def check_last_refdate_gerencial_front(refdate):

    check_carteira = st.session_state.manager_sql.check_if_data_exists(
        f"SELECT DISTINCT FUNDO FROM TB_CARTEIRAS "
        f"WHERE FUNDO = 'STRIX YIELD MASTER' AND REFDATE = '{st.session_state.funcoes_pytools.convert_data_sql(refdate)}'"
    )

    check_calculadora = st.session_state.manager_sql.check_if_data_exists(
        f"SELECT DISTINCT REFDATE FROM TB_FLUXO_FUTURO_ATIVOS WHERE REFDATE = '{st.session_state.funcoes_pytools.convert_data_sql(refdate)}'"
    )

    return check_carteira, check_calculadora


def fluxo_caixa():

    def fluxo_caixa_30(df_fluxo_ativos):

        # FLuxo de caixa projetado para os próximos 30 dias
        refdate_mais_30 = st.session_state.funcoes_pytools.workday_br(refdate, 30)
        df_fluxo_ativos_30 = df_fluxo_ativos[
            df_fluxo_ativos["DATA_LIQUIDACAO"] <= refdate_mais_30
        ]
        df_fluxo_ativos_30 = (
            df_fluxo_ativos_30[["DATA_LIQUIDACAO", "ATIVO", "Fluxo Projetado"]]
            .groupby(["DATA_LIQUIDACAO", "ATIVO"])
            .sum()
            .reset_index()
        )
        df_fluxo_ativos_30 = df_fluxo_ativos_30.pivot(
            index="ATIVO", columns="DATA_LIQUIDACAO", values="Fluxo Projetado"
        )
        df_fluxo_ativos_30 = df_fluxo_ativos_30.sort_index(axis=1)
        df_fluxo_ativos_30.columns.name = None
        df_fluxo_ativos_30 = df_fluxo_ativos_30.fillna(0)

        df_resumo_30 = df_fluxo_ativos_30.copy()
        df_resumo_30 = df_resumo_30.reset_index()
        df_resumo_30 = pd.DataFrame(df_resumo_30.drop(columns="ATIVO").sum()).T
        df_resumo_30["ATIVO"] = "Total"
        df_resumo_30 = df_resumo_30[["ATIVO"] + df_resumo_30.columns[:-1].tolist()]

        for coluna in df_resumo_30.columns:
            if coluna != "ATIVO":
                df_resumo_30[coluna] = df_resumo_30[coluna].map(format_value)

        df_fluxo_ativos_30 = df_fluxo_ativos_30.map(format_value)
        df_fluxo_ativos_30 = df_fluxo_ativos_30.reset_index()

        return df_fluxo_ativos_30, df_resumo_30

    def fluxo_caixa_mais(df_fluxo_ativos):

        refdate_mais_30 = st.session_state.funcoes_pytools.workday_br(refdate, 30)
        refdate_mais_60 = st.session_state.funcoes_pytools.workday_br(refdate, 60)
        refdate_mais_90 = st.session_state.funcoes_pytools.workday_br(refdate, 90)
        refdate_mais_120 = st.session_state.funcoes_pytools.workday_br(refdate, 120)
        refdate_mais_150 = st.session_state.funcoes_pytools.workday_br(refdate, 150)
        refdate_mais_180 = st.session_state.funcoes_pytools.workday_br(refdate, 180)

        df_fluxo_ativos_maior_30 = (
            df_fluxo_ativos[
                (df_fluxo_ativos["DATA_LIQUIDACAO"] > refdate_mais_30)
                & (df_fluxo_ativos["DATA_LIQUIDACAO"] <= refdate_mais_60)
            ][["ATIVO", "Fluxo Projetado"]]
            .groupby("ATIVO")
            .sum()
            .reset_index()
            .rename(columns={"Fluxo Projetado": "> 30 du"})
        )

        df_fluxo_ativos_maior_60 = (
            df_fluxo_ativos[
                (df_fluxo_ativos["DATA_LIQUIDACAO"] > refdate_mais_60)
                & (df_fluxo_ativos["DATA_LIQUIDACAO"] <= refdate_mais_90)
            ][["ATIVO", "Fluxo Projetado"]]
            .groupby("ATIVO")
            .sum()
            .reset_index()
            .rename(columns={"Fluxo Projetado": "> 60 du"})
        )

        df_fluxo_ativos_maior_90 = (
            df_fluxo_ativos[
                (df_fluxo_ativos["DATA_LIQUIDACAO"] > refdate_mais_90)
                & (df_fluxo_ativos["DATA_LIQUIDACAO"] <= refdate_mais_120)
            ][["ATIVO", "Fluxo Projetado"]]
            .groupby("ATIVO")
            .sum()
            .reset_index()
            .rename(columns={"Fluxo Projetado": "> 90 du"})
        )

        df_fluxo_ativos_maior_120 = (
            df_fluxo_ativos[
                (df_fluxo_ativos["DATA_LIQUIDACAO"] > refdate_mais_120)
                & (df_fluxo_ativos["DATA_LIQUIDACAO"] <= refdate_mais_150)
            ][["ATIVO", "Fluxo Projetado"]]
            .groupby("ATIVO")
            .sum()
            .reset_index()
            .rename(columns={"Fluxo Projetado": "> 120 du"})
        )

        df_fluxo_ativos_maior_150 = (
            df_fluxo_ativos[
                (df_fluxo_ativos["DATA_LIQUIDACAO"] > refdate_mais_150)
                & (df_fluxo_ativos["DATA_LIQUIDACAO"] <= refdate_mais_180)
            ][["ATIVO", "Fluxo Projetado"]]
            .groupby("ATIVO")
            .sum()
            .reset_index()
            .rename(columns={"Fluxo Projetado": "> 150 du"})
        )

        df_fluxo_ativos_maior_180 = (
            df_fluxo_ativos[(df_fluxo_ativos["DATA_LIQUIDACAO"] > refdate_mais_180)][
                ["ATIVO", "Fluxo Projetado"]
            ]
            .groupby("ATIVO")
            .sum()
            .reset_index()
            .rename(columns={"Fluxo Projetado": "> 180 du"})
        )

        df_ativos = (
            df_fluxo_ativos[["TIPO_ATIVO", "ATIVO"]]
            .drop_duplicates()
            .sort_values("TIPO_ATIVO")
        )
        df_fluxo_maior = pd.merge(
            df_ativos["ATIVO"], df_fluxo_ativos_maior_30, on="ATIVO", how="left"
        )
        df_fluxo_maior = pd.merge(
            df_fluxo_maior, df_fluxo_ativos_maior_60, on="ATIVO", how="left"
        )
        df_fluxo_maior = pd.merge(
            df_fluxo_maior, df_fluxo_ativos_maior_90, on="ATIVO", how="left"
        )
        df_fluxo_maior = pd.merge(
            df_fluxo_maior, df_fluxo_ativos_maior_120, on="ATIVO", how="left"
        )
        df_fluxo_maior = pd.merge(
            df_fluxo_maior, df_fluxo_ativos_maior_150, on="ATIVO", how="left"
        )
        df_fluxo_maior = pd.merge(
            df_fluxo_maior, df_fluxo_ativos_maior_180, on="ATIVO", how="left"
        )

        df_fluxo_maior = df_fluxo_maior.fillna(0)

        df_resumo_maior = pd.DataFrame(df_fluxo_maior.drop(columns="ATIVO").sum()).T
        df_resumo_maior["ATIVO"] = "Total"
        df_resumo_maior = df_resumo_maior[
            ["ATIVO"] + df_resumo_maior.columns[:-1].tolist()
        ]

        for coluna in df_fluxo_maior.columns:
            if coluna != "ATIVO":
                df_fluxo_maior[coluna] = df_fluxo_maior[coluna].map(format_value)

        for coluna in df_resumo_maior.columns:
            if coluna != "ATIVO":
                df_resumo_maior[coluna] = df_resumo_maior[coluna].map(format_value)

        return df_fluxo_maior, df_resumo_maior

    status_ger, status_calc = check_last_refdate_gerencial_front(refdate)

    if status_calc == False:
        st.sidebar.error(f"Fluxo de Caixa não disponível.")
    else:
        with st.container():

            df_base_fluxo_ativos = st.session_state.manager_sql.select_dataframe(
                f"SELECT * FROM TB_FLUXO_FUTURO_ATIVOS WHERE REFDATE = '{st.session_state.funcoes_pytools.convert_data_sql(refdate)}'"
            )

            df_base_posicao_ativos = st.session_state.manager_sql.select_dataframe(
                f"SELECT ATIVO, QUANTIDADE_D0 FROM TB_POSICAO "
                f"WHERE REFDATE = '{st.session_state.funcoes_pytools.convert_data_sql(refdate)}' AND FUNDO = 'STRIX YIELD MASTER'"
            )

            df_fluxo_ativos = pd.merge(
                df_base_fluxo_ativos, df_base_posicao_ativos, on="ATIVO", how="left"
            )
            df_fluxo_ativos["Fluxo Projetado"] = df_fluxo_ativos.apply(
                fluxo_projetado, axis=1
            )

            df_fluxo_30, df_resumo_30 = fluxo_caixa_30(df_fluxo_ativos)

            df_fluxo_maior, df_resumo_maior = fluxo_caixa_mais(df_fluxo_ativos)

            with st.container(border=True):
                st.write("### Fluxo Projetado")
                st.text(f"Proximos 30 du")
                st.dataframe(df_resumo_30, use_container_width=True, hide_index=True)
                st.dataframe(df_resumo_maior, use_container_width=True, hide_index=True)

            with st.container(border=True):
                st.write("### Fluxo Projetado Detalhado")
                st.dataframe(df_fluxo_30, use_container_width=True, hide_index=True)
                st.dataframe(df_fluxo_maior, use_container_width=True, hide_index=True)


def gerencial_front():

    status_ger, status_calc = check_last_refdate_gerencial_front(refdate)

    if status_ger == False:
        st.sidebar.error(f"Gerencial não disponivel.")
    else:
        aviso_pagina = st.sidebar.empty()
        aviso_pagina.status("Processando...")
        sleep(1)
        aviso_pagina.empty()

        with st.container(border=True):
            col1, col2, col3 = st.columns([0.5, 10, 0.5])

            with col2.container():
                st.header(
                    f"Gerencial Front - {refdate.strftime('%d/%m/%Y')}", divider="grey"
                )

            with col2.container():
                col1, col2, col3, col4 = st.columns([1, 0.1, 0.8, 0.2])

                st.session_state.manager_ger.set_refdate(refdate)

                st.session_state.manager_ger.run()

                df_resumo_indexadores = (
                    st.session_state.manager_ger.df_resultados_indexadores_formated
                )
                df_classes_cred_privado = (
                    st.session_state.manager_ger.df_cred_privado_classes_formated
                )
                df_classes_outros = (
                    st.session_state.manager_ger.df_outras_classes_formated
                )

                col1.header("Resumo Classes", divider="grey")

                col1.markdown(f"**Carteira Crédito Privado Consolidado:**")
                col1.text(
                    f"Exposição (R$): {st.session_state.manager_ger.credito_privado_exposicao_total}  "
                    f"|  Alocação: {st.session_state.manager_ger.credito_privado_alocacao_total}  "
                    f"|  Carrego: CDI + {st.session_state.manager_ger.credito_privado_carrego_total}  "
                    f"|  Duration: {st.session_state.manager_ger.credito_privado_duration_total}"
                )

                col1.dataframe(
                    df_classes_cred_privado, hide_index=True, use_container_width=True
                )
                col1.dataframe(
                    df_classes_outros, hide_index=True, use_container_width=True
                )

                col1.markdown(f"**Carteira Consolidada antes Adm:**")
                col1.text(
                    f"Exposição (R$): {st.session_state.manager_ger.exposicao_total_antes_adm}  "
                    f"|  Alocação: {st.session_state.manager_ger.alocacao_total_antes_adm}  "
                    f"|  Carrego: CDI + {st.session_state.manager_ger.carrego_total_antes_adm}  "
                    f"|  Duration: {st.session_state.manager_ger.duration_total_antes_adm}"
                )

                col1.text(
                    f"Carrego pós ADM: CDI + {st.session_state.manager_ger.carrego_total_pos_adm}"
                )

                col1.header("Resumo Indexadores", divider="grey")
                col1.markdown(f"**Carteira Crédito Privado Consolidado**")
                col1.dataframe(
                    df_resumo_indexadores, hide_index=True, use_container_width=True
                )

                fig_classes = px.pie(
                    st.session_state.manager_ger.df_to_fig_classes,
                    values="Exposição (R$)",
                    names="Classe Ativo",
                    title="Alocação Classe Ativos",
                )

                col3.plotly_chart(fig_classes)

                fig_classes = px.pie(
                    st.session_state.manager_ger.df_to_fig_indexador,
                    values="Exposição (R$)",
                    names="Indexador",
                    title="Alocação Indexadores Ativos",
                )

                col3.plotly_chart(fig_classes)

        with st.container(border=True):
            col1, col2, col3 = st.columns([0.5, 10, 0.5])
            col2.header("Debêntures", divider="grey")

            emissores_debentures = st.session_state.manager_ger.emissores_debentures
            df_debentures = st.session_state.manager_ger.df_debentures

            for emissor in emissores_debentures.keys():
                col2.text(
                    f"Emissor: {emissor}  "
                    f"|  Exposição (R$): {emissores_debentures[emissor][0]:,.0f}  "
                    f"|  Alocação: {emissores_debentures[emissor][1]:,.2f}%  "
                    f"|  Carrego: CDI + {emissores_debentures[emissor][2]:,.2f}%  "
                    f"|  Duration: {int(emissores_debentures[emissor][3])}"
                )

                col2.dataframe(
                    df_debentures.loc[
                        df_debentures["Emissor"] == emissor,
                        [
                            "Ativo",
                            "Indexador",
                            "Exposição (R$)",
                            "% Alocação",
                            "Taxa de Emissão",
                            "Carrego Original",
                            "Carrego CDI +",
                            "Duration",
                            "Vencimento",
                        ],
                    ],
                    hide_index=True,
                    use_container_width=True,
                )

        with st.container(border=True):
            col1, col2, col3 = st.columns([0.5, 10, 0.5])
            col2.header("Letras Financeiras", divider="grey")

            emissores_lfs = st.session_state.manager_ger.emissores_lfs
            df_letras_financeiras = st.session_state.manager_ger.df_letras_financeiras

            for emissor in emissores_lfs.keys():
                col2.text(
                    f"Emissor: {emissor}  "
                    f"|  Exposição (R$): {emissores_lfs[emissor][0]:,.0f}  "
                    f"|  Alocação: {emissores_lfs[emissor][1]:,.2f}%  "
                    f"|  Carrego: CDI + {emissores_lfs[emissor][2]:,.2f}%  "
                    f"|  Duration: {int(emissores_lfs[emissor][3])}"
                )

                col2.dataframe(
                    df_letras_financeiras.loc[
                        df_letras_financeiras["Emissor"] == emissor,
                        [
                            "Ativo",
                            "Indexador",
                            "Exposição (R$)",
                            "% Alocação",
                            "Taxa de Emissão",
                            "Carrego Original",
                            "Carrego CDI +",
                            "Duration",
                            "Vencimento",
                        ],
                    ],
                    hide_index=True,
                    use_container_width=True,
                )

        with st.container(border=True):
            col1, col2, col3 = st.columns([0.5, 10, 0.5])
            col2.header("FIDCs", divider="grey")

            emissores_fidcs = st.session_state.manager_ger.emissores_fidcs
            df_fidcs = st.session_state.manager_ger.df_fidcs

            for emissor in emissores_fidcs.keys():
                col2.text(
                    f"Emissor: {emissor}  "
                    f"|  Exposição (R$): {emissores_fidcs[emissor][0]:,.0f}  "
                    f"|  Alocação: {emissores_fidcs[emissor][1]:,.2f}%  "
                    f"|  Carrego: CDI + {emissores_fidcs[emissor][2]:,.2f}%  "
                    f"|  Duration: {int(emissores_fidcs[emissor][3])}"
                )

                col2.dataframe(
                    df_fidcs.loc[
                        df_fidcs["Emissor"] == emissor,
                        [
                            "Ativo",
                            "Indexador",
                            "Exposição (R$)",
                            "% Alocação",
                            "Taxa de Emissão",
                            "Carrego Original",
                            "Carrego CDI +",
                            "Duration",
                            "Vencimento",
                        ],
                    ],
                    hide_index=True,
                    use_container_width=True,
                )


refdate = st.sidebar.date_input(
    label="Refdate",
    value=st.session_state.funcoes_pytools.workday_br(date.today(), -1),
    format="DD/MM/YYYY",
    on_change=desliga_states,
)

st.sidebar.button(
    "Gerencial", use_container_width=True, on_click=lambda: select_state("gerencial")
)
st.sidebar.button(
    "Fluxo Caixas",
    use_container_width=True,
    on_click=lambda: select_state("fluxo_caixas"),
)

if st.session_state["fluxo_caixas"] == False and st.session_state["gerencial"] == False:

    st.sidebar.divider()
    LogoStrix()

    status_ger, status_calc = check_last_refdate_gerencial_front(refdate)

    if status_ger == False:
        st.sidebar.error(f"Gerencial não disponivel.")
    else:
        st.sidebar.success(f"Gerencial disponível.")

    if status_calc == False:
        st.sidebar.error(f"Fluxo de Caixa não disponível.")
    else:
        st.sidebar.success(f"Fluxo de Caixa disponível.")

if st.session_state["gerencial"] == True:
    LogoStrix()

    status_ger, status_calc = check_last_refdate_gerencial_front(refdate)

    if status_ger == False:
        st.sidebar.error(f"Gerencial não disponivel.")
    else:

        st.session_state.manager_ger.set_refdate(refdate)
        st.session_state.manager_ger.run()

        # Botao download:

        df_debentures = st.session_state.manager_ger.df_debentures
        df_letras_financeiras = st.session_state.manager_ger.df_letras_financeiras
        df_fidcs = st.session_state.manager_ger.df_fidcs

        df_all = pd.concat([df_debentures, df_letras_financeiras, df_fidcs])

        df_cadastro_emissor = st.session_state.manager_sql.select_dataframe(
            "SELECT DISTINCT EMISSOR AS Emissor, GRUPO_ECONOMICO, TIPO_EMISSOR FROM TB_CADASTRO_EMISSOR"
        )

        df_cadastro_ativo = st.session_state.manager_sql.select_dataframe(
            "SELECT DISTINCT ATIVO as Ativo, CLASSE_ATIVO as [Classe Ativo], TIPO_ATIVO as [Tipo Ativo] FROM TB_CADASTRO_ATIVOS WHERE TIPO_ATIVO NOT IN ('DIVIDENDOS', 'Caixa', 'Provisões & Despesas', 'Ajuste Cisão', 'Fundos Caixa', 'Ações BR')"
        )

        df_all = pd.merge(df_all, df_cadastro_emissor, on="Emissor", how="left")
        df_all = pd.merge(df_all, df_cadastro_ativo, on="Ativo", how="left")

        df_all.rename(
            columns={
                "GRUPO_ECONOMICO": "Grupo Economico",
                "TIPO_EMISSOR": "Tipo Emissor",
            },
            inplace=True,
        )

        df_all = df_all[
            [
                "Emissor",
                "Tipo Emissor",
                "Grupo Economico",
                "Tipo Ativo",
                "Ativo",
                "Classe Ativo",
                "Indexador",
                "Exposição (R$)",
                "% Alocação",
                "Taxa de Emissão",
                "Carrego Original",
                "Carrego CDI +",
                "Duration",
                "Vencimento",
            ]
        ]

        df_all.insert(0, "Refdate", refdate)

        st.sidebar.divider()

        st.sidebar.download_button(
            label="Download - Detalhes Ativos",
            data=save_to_excel(df_all),
            file_name="detalhes_ativos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

        with st.container(border=True):
            col1, col2, col3 = st.columns([0.5, 10, 0.5])

            with col2.container():
                st.header(
                    f"Gerencial Front - {refdate.strftime('%d/%m/%Y')}", divider="grey"
                )

            with col2.container():
                col1, col2, col3, col4 = st.columns([1, 0.1, 0.8, 0.2])

                # st.session_state.manager_ger.set_refdate(refdate)

                # st.session_state.manager_ger.run()

                df_resumo_indexadores = (
                    st.session_state.manager_ger.df_resultados_indexadores_formated
                )
                df_classes_cred_privado = (
                    st.session_state.manager_ger.df_cred_privado_classes_formated
                )
                df_classes_outros = (
                    st.session_state.manager_ger.df_outras_classes_formated
                )

                col1.header("Resumo Classes", divider="grey")

                col1.markdown(f"**Carteira Crédito Privado Consolidado:**")
                col1.text(
                    f"Exposição (R$): {st.session_state.manager_ger.credito_privado_exposicao_total}  "
                    f"|  Alocação: {st.session_state.manager_ger.credito_privado_alocacao_total}  "
                    f"|  Carrego: CDI + {st.session_state.manager_ger.credito_privado_carrego_total}  "
                    f"|  Duration: {st.session_state.manager_ger.credito_privado_duration_total}"
                )

                col1.dataframe(
                    df_classes_cred_privado, hide_index=True, use_container_width=True
                )
                col1.dataframe(
                    df_classes_outros, hide_index=True, use_container_width=True
                )

                col1.markdown(f"**Carteira Consolidada antes Adm:**")
                col1.text(
                    f"Exposição (R$): {st.session_state.manager_ger.exposicao_total_antes_adm}  "
                    f"|  Alocação: {st.session_state.manager_ger.alocacao_total_antes_adm}  "
                    f"|  Carrego: CDI + {st.session_state.manager_ger.carrego_total_antes_adm}  "
                    f"|  Duration: {st.session_state.manager_ger.duration_total_antes_adm}"
                )

                col1.text(
                    f"Carrego pós ADM: CDI + {st.session_state.manager_ger.carrego_total_pos_adm}"
                )

                col1.header("Resumo Indexadores", divider="grey")
                col1.markdown(f"**Carteira Crédito Privado Consolidado**")
                col1.dataframe(
                    df_resumo_indexadores, hide_index=True, use_container_width=True
                )

                fig_classes = px.pie(
                    st.session_state.manager_ger.df_to_fig_classes,
                    values="Exposição (R$)",
                    names="Classe Ativo",
                    title="Alocação Classe Ativos",
                )

                col3.plotly_chart(fig_classes)

                fig_classes = px.pie(
                    st.session_state.manager_ger.df_to_fig_indexador,
                    values="Exposição (R$)",
                    names="Indexador",
                    title="Alocação Indexadores Ativos",
                )

                col3.plotly_chart(fig_classes)

        with st.container(border=True):
            col1, col2, col3 = st.columns([0.5, 10, 0.5])
            col2.header("Debêntures", divider="grey")

            emissores_debentures = st.session_state.manager_ger.emissores_debentures
            df_debentures = st.session_state.manager_ger.df_debentures

            for emissor in emissores_debentures.keys():
                col2.text(
                    f"Emissor: {emissor}  "
                    f"|  Exposição (R$): {emissores_debentures[emissor][0]:,.0f}  "
                    f"|  Alocação: {emissores_debentures[emissor][1]:,.2f}%  "
                    f"|  Carrego: CDI + {emissores_debentures[emissor][2]:,.2f}%  "
                    f"|  Duration: {int(emissores_debentures[emissor][3])}"
                )

                col2.dataframe(
                    df_debentures.loc[
                        df_debentures["Emissor"] == emissor,
                        [
                            "Ativo",
                            "Indexador",
                            "Exposição (R$)",
                            "% Alocação",
                            "Taxa de Emissão",
                            "Carrego Original",
                            "Carrego CDI +",
                            "Duration",
                            "Vencimento",
                        ],
                    ],
                    hide_index=True,
                    use_container_width=True,
                )

        with st.container(border=True):
            col1, col2, col3 = st.columns([0.5, 10, 0.5])
            col2.header("Letras Financeiras", divider="grey")

            emissores_lfs = st.session_state.manager_ger.emissores_lfs
            df_letras_financeiras = st.session_state.manager_ger.df_letras_financeiras

            for emissor in emissores_lfs.keys():
                col2.text(
                    f"Emissor: {emissor}  "
                    f"|  Exposição (R$): {emissores_lfs[emissor][0]:,.0f}  "
                    f"|  Alocação: {emissores_lfs[emissor][1]:,.2f}%  "
                    f"|  Carrego: CDI + {emissores_lfs[emissor][2]:,.2f}%  "
                    f"|  Duration: {int(emissores_lfs[emissor][3])}"
                )

                col2.dataframe(
                    df_letras_financeiras.loc[
                        df_letras_financeiras["Emissor"] == emissor,
                        [
                            "Ativo",
                            "Indexador",
                            "Exposição (R$)",
                            "% Alocação",
                            "Taxa de Emissão",
                            "Carrego Original",
                            "Carrego CDI +",
                            "Duration",
                            "Vencimento",
                        ],
                    ],
                    hide_index=True,
                    use_container_width=True,
                )

        with st.container(border=True):
            col1, col2, col3 = st.columns([0.5, 10, 0.5])
            col2.header("FIDCs", divider="grey")

            emissores_fidcs = st.session_state.manager_ger.emissores_fidcs
            df_fidcs = st.session_state.manager_ger.df_fidcs

            for emissor in emissores_fidcs.keys():
                col2.text(
                    f"Emissor: {emissor}  "
                    f"|  Exposição (R$): {emissores_fidcs[emissor][0]:,.0f}  "
                    f"|  Alocação: {emissores_fidcs[emissor][1]:,.2f}%  "
                    f"|  Carrego: CDI + {emissores_fidcs[emissor][2]:,.2f}%  "
                    f"|  Duration: {int(emissores_fidcs[emissor][3])}"
                )

                col2.dataframe(
                    df_fidcs.loc[
                        df_fidcs["Emissor"] == emissor,
                        [
                            "Ativo",
                            "Indexador",
                            "Exposição (R$)",
                            "% Alocação",
                            "Taxa de Emissão",
                            "Carrego Original",
                            "Carrego CDI +",
                            "Duration",
                            "Vencimento",
                        ],
                    ],
                    hide_index=True,
                    use_container_width=True,
                )


if st.session_state["fluxo_caixas"] == True:
    LogoStrix()
    fluxo_caixa()
