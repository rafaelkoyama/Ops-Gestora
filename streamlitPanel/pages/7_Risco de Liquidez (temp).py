from __init__ import *

VERSION_APP = "1.0.1"
VERSION_REFDATE = "2024-07-15"
ENVIRONMENT = os.getenv("ENVIRONMENT")
SCRIPT_NAME = os.path.basename(__file__)

if ENVIRONMENT == "DEVELOPMENT":
    print(f"{SCRIPT_NAME.upper()} - {ENVIRONMENT} - {VERSION_APP} - {VERSION_REFDATE}")

append_paths()

# -----------------------------------------------------------------------

from datetime import date
from io import BytesIO

import pandas as pd
import streamlit as st

from risco.relatoriosRisco import liquidezAtivos
from tools.db_helper import SQL_Manager
from tools.py_tools import FuncoesPyTools

# -----------------------------------------------------------------------

st.set_page_config(
    page_title="Strix Capital - Risco de Liquidez",
    page_icon="🦉",
    layout="wide",
    initial_sidebar_state="expanded",
)

lista_states = [
    "risco_liquidez_ativos",
]

if "manager_sql" not in st.session_state:
    st.session_state.manager_sql = SQL_Manager()

if "funcoes_pytools" not in st.session_state:
    st.session_state.funcoes_pytools = FuncoesPyTools(
        manager_sql=st.session_state.manager_sql
    )

if "logo_backoffice" not in st.session_state:
    st.session_state.logo_backoffice = True

if "manager_liquidez" not in st.session_state:
    st.session_state.manager_liquidez = liquidezAtivos(
        manager_sql=st.session_state.manager_sql,
        funcoes_pytools=st.session_state.funcoes_pytools,
    )

for state in lista_states:
    if state not in st.session_state:
        st.session_state[state] = False


def desliga_states():
    st.session_state.logo_backoffice = True
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
        col1, col2, col3 = st.columns([1, 2, 0.1])
        col2.image(
            os.path.join(base_path, "streamlitPanel", "static", "logotipo_strix.png"),  # type: ignore
            width=500,
        )


view_ativos = st.sidebar.checkbox(
    label="Gerar view por ativos", value=False, on_change=desliga_states
)

refdate = st.sidebar.date_input(
    "Refdate", value=date(2024, 6, 25), format="DD/MM/YYYY", on_change=desliga_states
)

st.sidebar.button(
    label="Executar",
    use_container_width=True,
    on_click=lambda: select_state("risco_liquidez_ativos"),
)

# -----------------------------------------------------------------------

if st.session_state.risco_liquidez_ativos:

    if not st.session_state.manager_sql.check_if_data_exists(
        f"SELECT DISTINCT REFDATE FROM TB_B3_NEGOCIOS_BALCAO_RENDA_FIXA WHERE REFDATE = '{refdate}'"
    ):
        st.error(f"Refdate ainda não disponível: {refdate}")

    else:

        def exibir_resumo_observaveis(df):

            df_resumo_observaveis_formated = (
                st.session_state.funcoes_pytools.format_df_float_columns_to_str(
                    df=df,
                    columns=[
                        "Posição dia",
                        "Premissa venda",
                        "Saldo posição dia",
                        "Liquidez gerada dia",
                        "Liquidez total gerada",
                    ],
                    decimals=0,
                )
            )

            fundos = df_resumo_observaveis_formated["Fundo"].unique()

            if len(fundos) > 1:

                colunas = st.columns(len(fundos))

                for idx, fundo in enumerate(fundos):
                    df_fundo = df_resumo_observaveis_formated[
                        df_resumo_observaveis_formated["Fundo"] == fundo
                    ]

                    with colunas[idx]:
                        st.dataframe(df_fundo, hide_index=True, height=900)
            else:
                st.dataframe(
                    df_resumo_observaveis_formated, hide_index=True, height=900
                )

        def exibir_observaveis_por_ativo(df):

            df = df.sort_values(by=["Fundo", "Ativo", "Refdate"])

            df_ativos_observaveis_formated = (
                st.session_state.funcoes_pytools.format_df_float_columns_to_str(
                    df=df,
                    columns=[
                        "Posição dia",
                        "Premissa venda",
                        "Saldo posição dia",
                        "Liquidez gerada dia",
                        "Liquidez total gerada",
                    ],
                    decimals=0,
                )
            )

            fundos = df_ativos_observaveis_formated["Fundo"].unique()
            ativos = df_ativos_observaveis_formated["Ativo"].unique()

            if len(fundos) > 1:

                colunas = st.columns(len(fundos))

                for idx, fundo in enumerate(fundos):
                    df_fundo = df_ativos_observaveis_formated[
                        df_ativos_observaveis_formated["Fundo"] == fundo
                    ]

                    with colunas[idx]:

                        for ativo in ativos:
                            df_ativo = df_fundo[
                                (df_fundo["Ativo"] == ativo)
                                & (df_fundo["Posição dia"] != "0")
                                & (df_fundo["Liquidez gerada dia"] != "0")
                            ].reset_index(drop=True)
                            st.dataframe(df_ativo, hide_index=True)

            else:

                for ativo in ativos:
                    df_ativo = df_ativos_observaveis_formated[
                        (df_ativos_observaveis_formated["Ativo"] == ativo)
                        & (df_ativos_observaveis_formated["Posição dia"] != "0")
                        & (df_ativos_observaveis_formated["Liquidez gerada dia"] != "0")
                    ].reset_index(drop=True)
                    st.dataframe(df_ativo, hide_index=True)

        st.session_state.manager_liquidez.set_refdate(refdate)

        # Call da base mercado observavel

        df_base_observaveis = (
            st.session_state.manager_liquidez.df_base_liquidez_diaria_observavel.copy()
        )

        df_resumo_observaveis = (
            df_base_observaveis[
                [
                    "Refdate",
                    "Fundo",
                    "Categoria",
                    "Posição dia",
                    "Premissa venda",
                    "Saldo posição dia",
                    "Liquidez gerada dia",
                    "Liquidez total gerada",
                ]
            ]
            .groupby(["Refdate", "Fundo", "Categoria"])
            .sum()
            .sort_values(by=["Fundo", "Refdate"])
            .reset_index()
        )

        dias_liquidez_total_observaveis = (
            st.session_state.funcoes_pytools.networkdays_br(
                data_inicio=df_base_observaveis["Refdate"].min(),
                data_fim=df_base_observaveis["Refdate"].max(),
            )
        )

        # # -----------------------------------------------------------------------

        st.header(f"Risco de Liquidez - Ativos - {refdate.strftime('%d/%m/%Y')}")
        st.subheader("Resumo")

        st.write(
            f"Dias úteis zeragem mercado observável: {dias_liquidez_total_observaveis}"
        )

        with st.expander("Mercado Observável - Resumo"):

            exibir_resumo_observaveis(df_resumo_observaveis)

        if view_ativos:

            with st.expander("Mercado Observável - Ativos"):

                exibir_observaveis_por_ativo(df_base_observaveis)
