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

        lista_observaveis = ["Debênture"]
        lista_titulos_publicos = ["Tit. Publicos", "Compromissada"]

        st.session_state.manager_liquidez.set_refdate(refdate)

        st.session_state.manager_liquidez.mercado_observavel(lista_observaveis)

        df_resumo_observaveis = (
            st.session_state.manager_liquidez.df_resumo_liquidez_diaria_observaveis.copy()
        )

        dias_liquidez_total_observaveis = len(df_resumo_observaveis["Refdate"].unique())

        st.session_state.manager_liquidez.titulos_publicos(lista_titulos_publicos)
        df_resumo_titulos_publicos = (
            st.session_state.manager_liquidez.df_resumo_tit_publicos.copy()
        )

        # -----------------------------------------------------------------------

        st.header(f"Risco de Liquidez - Ativos - {refdate.strftime('%d/%m/%Y')}")
        st.subheader("Resumo")

        st.write(f"Dias úteis zeragem títulos publicos: 1")
        st.write(
            f"Dias úteis zeragem mercado observável: {dias_liquidez_total_observaveis}"
        )

        with st.expander("Tabela Resumo Título Público"):
            st.dataframe(df_resumo_titulos_publicos, hide_index=True)

        with st.expander("Tabela Resumo Mercado Observável"):
            st.dataframe(df_resumo_observaveis, hide_index=True, height=1000)
