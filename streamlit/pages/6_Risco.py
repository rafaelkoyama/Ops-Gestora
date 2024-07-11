from __init__ import *

VERSION_APP = "1.0.0"
VERSION_REFDATE = "2024-07-10"
ENVIRONMENT = os.getenv("ENVIRONMENT")
SCRIPT_NAME = os.path.basename(__file__)

if ENVIRONMENT == "DEVELOPMENT":
    print(f"{SCRIPT_NAME.upper()} - {ENVIRONMENT} - {VERSION_APP} - {VERSION_REFDATE}")

append_paths()

# -----------------------------------------------------------------------


import streamlit as st
from db_helper import SQL_Manager
from py_tools import FuncoesPyTools
from relatoriosRisco import dadosRiscoFundos

if "manager_sql" not in st.session_state:
    st.session_state.manager_sql = SQL_Manager()

if "funcoes_pytools" not in st.session_state:
    st.session_state.funcoes_pytools = FuncoesPyTools(st.session_state.manager_sql)

if "riskcalculador_fia" not in st.session_state:
    st.session_state.riskcalculador_fia = dadosRiscoFundos(
        "STRIX FIA", manager_sql=st.session_state.manager_sql
    )

if "riskcalculator_yield" not in st.session_state:
    st.session_state.riskcalculator_yield = dadosRiscoFundos(
        "STRIX YIELD MASTER F", manager_sql=st.session_state.manager_sql
    )


st.set_page_config(
    page_title="Strix Capital - Painel de Controle",
    page_icon="🦉",
    layout="wide",
    initial_sidebar_state="expanded",
)

with st.container(border=True):
    st.header("Strix FIA", divider="grey")
    with st.container(border=True):

        tb_col1, tb_col2 = st.columns([1, 1])

        with tb_col1.container(border=True):
            col_var, col_rents = st.columns(2)
            col_var.write(
                f"VaR Paramétrico: {st.session_state.riskcalculador_fia.var_parametrico():.2f}%"
            )
            col_var.write(
                f"VaR Histórico: {st.session_state.riskcalculador_fia.var_historico():.2f}%"
            )
            col_rents.write(
                f"Rent. Positivas: {st.session_state.riskcalculador_fia.diasPositivos()}"
            )
            col_rents.write(
                f"Rent. Negativas: {st.session_state.riskcalculador_fia.diasNegativos()}"
            )

        with tb_col1.container(border=True):
            sub_tb_col1, sub_tb_col2 = st.columns(2)
            sub_tb_col1.write(f"**Top5 - Maiores Rentabilidades**")
            sub_tb_col1.write(
                st.session_state.riskcalculador_fia.maioresRentabilidades().to_html(
                    index=False, justify="center", classes="dataframe", escape=False
                ),
                unsafe_allow_html=True,
            )
            sub_tb_col2.write(f"**Top5 - Menores Rentabilidades**")
            sub_tb_col2.write(
                st.session_state.riskcalculador_fia.menoresRentabilidades().to_html(
                    index=False, justify="center", classes="dataframe", escape=False
                ),
                unsafe_allow_html=True,
            )
            sub_tb_col1.write("")
            sub_tb_col1.write("")
        with tb_col2.container(border=True):
            st.pyplot(
                st.session_state.riskcalculador_fia.grafico_rentabilidade_fundo_x_benchmark()
            )

    with st.container(border=True):
        plt_col1, plt_col2, plt_col3 = st.columns(3)
        plt_col1.pyplot(
            st.session_state.riskcalculador_fia.grafico_dispersao_x_normal()
        )
        plt_col2.pyplot(st.session_state.riskcalculador_fia.grafico_volatilidade())
        plt_col3.pyplot(st.session_state.riskcalculador_fia.grafico_drawdown_fundo())

with st.container(border=True):
    st.header("Strix Yield Master", divider="grey")

    with st.container(border=True):
        tb_col1, tb_col2 = st.columns([1, 1])

        with tb_col1.container(border=True):
            col_var, col_rents = st.columns(2)
            col_var.write(
                f"VaR Paramétrico: {st.session_state.riskcalculator_yield.var_parametrico():.2f}%"
            )
            col_var.write(
                f"VaR Histórico: {st.session_state.riskcalculator_yield.var_historico():.2f}%"
            )
            col_rents.write(
                f"Rent. Positivas: {st.session_state.riskcalculator_yield.diasPositivos()}"
            )
            col_rents.write(
                f"Rent. Negativas: {st.session_state.riskcalculator_yield.diasNegativos()}"
            )

        with tb_col1.container(border=True):
            sub_tb_col1, sub_tb_col2 = st.columns(2)
            sub_tb_col1.write(f"**Top5 - Maiores Rentabilidades**")
            sub_tb_col1.write(
                st.session_state.riskcalculator_yield.maioresRentabilidades().to_html(
                    index=False, justify="center", classes="dataframe", escape=False
                ),
                unsafe_allow_html=True,
            )
            sub_tb_col2.write(f"**Top5 - Menores Rentabilidades**")
            sub_tb_col2.write(
                st.session_state.riskcalculator_yield.menoresRentabilidades().to_html(
                    index=False, justify="center", classes="dataframe", escape=False
                ),
                unsafe_allow_html=True,
            )
            sub_tb_col1.write("")
            sub_tb_col1.write("")
        with tb_col2.container(border=True):
            st.pyplot(
                st.session_state.riskcalculator_yield.grafico_rentabilidade_fundo_x_benchmark()
            )

    with st.container(border=True):
        plt_col1, plt_col2, plt_col3 = st.columns(3)
        plt_col1.pyplot(
            st.session_state.riskcalculator_yield.grafico_dispersao_x_normal()
        )
        plt_col2.pyplot(st.session_state.riskcalculator_yield.grafico_volatilidade())
        plt_col3.pyplot(st.session_state.riskcalculator_yield.grafico_drawdown_fundo())
