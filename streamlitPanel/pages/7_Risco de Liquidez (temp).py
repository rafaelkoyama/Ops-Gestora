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
    page_title="Strix Capital - Painel de Controle",
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


# refdate = st.sidebar.date_input("Refdate", value=date.today(), format="DD/MM/YYYY")
refdate = date(2024, 6, 25)


# -----------------------------------------------------------------------

st.session_state.risco_liquidez_ativos = True

if st.session_state.risco_liquidez_ativos:

    if not st.session_state.manager_sql.check_if_data_exists(
        f"SELECT DISTINCT REFDATE FROM TB_B3_NEGOCIOS_BALCAO_RENDA_FIXA WHERE REFDATE = '{refdate}'"
    ):
        st.error(f"Refdate ainda não disponível: {refdate}")

    else:

        lista_titulos_publicos = ["Tit. Publicos", "Compromissada"]

        st.session_state.manager_liquidez.set_refdate(refdate)

        # Call da base mercado observavel

        st.session_state.manager_liquidez.liquidez_mercado_observavel()

        df_resumo_observaveis = (
            st.session_state.manager_liquidez.df_resumo_liquidez_diaria_observaveis.copy()
        )

        dias_liquidez_total_observaveis = (
            st.session_state.funcoes_pytools.networkdays_br(
                data_inicio=df_resumo_observaveis["Refdate"].min(),
                data_fim=df_resumo_observaveis["Refdate"].max(),
            )
        )

        # Call da base titulos publicos

        st.session_state.manager_liquidez.liquidez_titulos_publicos()

        df_resumo_titulos_publicos = (
            st.session_state.manager_liquidez.df_resumo_tit_publicos.copy()
        )

        # Call da base fluxo

        st.session_state.manager_liquidez.liquidez_fluxo()
        st.session_state.manager_liquidez.liquidez_fluxo_fidc()

        df_resumo_fluxo = (
            st.session_state.manager_liquidez.df_resumo_liquidez_fluxo.copy()
        )

        df_resumo_fluxo_fidcs = (
            st.session_state.manager_liquidez.df_resumo_liquidez_fluxo_fidc.copy()
        )

        dias_liquidez_total_fluxo = st.session_state.funcoes_pytools.networkdays_br(
            data_inicio=df_resumo_fluxo["Refdate"].min(),
            data_fim=df_resumo_fluxo["Refdate"].max(),
        )

        dias_liquidez_total_fluxo_fidcs = (
            st.session_state.funcoes_pytools.networkdays_br(
                data_inicio=df_resumo_fluxo_fidcs["Data Liquidação"].min(),
                data_fim=df_resumo_fluxo_fidcs["Data Liquidação"].max(),
            )
        )

        # -----------------------------------------------------------------------

        st.header(f"Risco de Liquidez - Ativos - {refdate.strftime('%d/%m/%Y')}")
        st.subheader("Resumo")

        st.write(f"Dias úteis zeragem títulos publicos: 1")

        st.write(
            f"Dias úteis zeragem mercado observável: {dias_liquidez_total_observaveis}"
        )

        st.write(f"Dias úteis zeragem fluxo: {dias_liquidez_total_fluxo}")

        st.write(f"Dias úteis zeragem fluxo FIDCs: {dias_liquidez_total_fluxo_fidcs}")

        with st.expander("Tabela Resumo Título Público"):
            st.dataframe(df_resumo_titulos_publicos, hide_index=True)

        with st.expander("Tabela Resumo Fluxo"):
            col1, col2, col3 = st.columns(3)
            col1.dataframe(
                df_resumo_fluxo, hide_index=True, height=1000, use_container_width=True
            )
            col2.dataframe(
                df_resumo_fluxo_fidcs,
                hide_index=True,
                height=1000,
                use_container_width=True,
            )

        with st.expander("Tabela Resumo Mercado Observável"):
            st.dataframe(df_resumo_observaveis, hide_index=True, height=1000)
