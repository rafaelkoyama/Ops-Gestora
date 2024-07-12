from __init__ import *

VERSION_APP = "1.0.0"
VERSION_REFDATE = "2024-07-10"
ENVIRONMENT = os.getenv("ENVIRONMENT")
SCRIPT_NAME = os.path.basename(__file__)

if ENVIRONMENT == "DEVELOPMENT":
    print(f"{SCRIPT_NAME.upper()} - {ENVIRONMENT} - {VERSION_APP} - {VERSION_REFDATE}")

append_paths()

# -----------------------------------------------------------------------

# from socket import gethostbyname, gethostname

import streamlit as st

from risco.relatoriosRisco import dadosRiscoFundos, enquadramentoCarteira
from streamlitPanel.streamlit_helper import gerencialFront
from tools.db_helper import SQL_Manager
from tools.py_tools import FuncoesPyTools


def check_if_need_load_modules(list_modules):
    for module in list_modules:
        if module not in st.session_state:
            return True
    return False


list_modules = {
    "manager_sql",
    "funcoes_pytools",
    "manager_ger",
    "relatorio_risco",
    "riskcalculador_fia",
    "riskcalculator_yield",
}

st.set_page_config(
    page_title="Strix Capital - Painel de Controle",
    page_icon="🦉",
    layout="wide",
    initial_sidebar_state="expanded",
)


col1, col2, col3 = st.columns(3)
col2.image(
    os.path.join(base_path, "streamlitPanel", "static", "logotipo_strix.png"),  # type: ignore
    use_column_width=True,
)

if check_if_need_load_modules(list_modules):

    part = int(round(100 / len(list_modules), 0))
    total_part = 0

    text = "Carregando módulos..."
    my_bar = st.progress(total_part, text=text)

    next_total_part = total_part + part
    while total_part <= next_total_part:
        total_part += 1
        my_bar.progress(total_part, text=text)

    if "manager_sql" not in st.session_state:
        st.session_state.manager_sql = SQL_Manager()

    next_total_part = total_part + part
    while total_part <= next_total_part:
        total_part += 1
        my_bar.progress(total_part, text=text)

    if "funcoes_pytools" not in st.session_state:
        st.session_state.funcoes_pytools = FuncoesPyTools(st.session_state.manager_sql)

    next_total_part = total_part + part
    while total_part <= next_total_part:
        total_part += 1
        my_bar.progress(total_part, text=text)

    if "manager_ger" not in st.session_state:
        st.session_state.manager_ger = gerencialFront(
            manager_sql=st.session_state.manager_sql,
            funcoes_pytools=st.session_state.funcoes_pytools,
        )

    next_total_part = total_part + part
    while total_part <= next_total_part:
        total_part += 1
        my_bar.progress(total_part, text=text)

    if "relatorio_risco" not in st.session_state:
        st.session_state.relatorio_risco = enquadramentoCarteira(
            manager_sql=st.session_state.manager_sql,
            funcoes_pytools=st.session_state.funcoes_pytools,
        )

    next_total_part = total_part + part
    while total_part <= next_total_part:
        total_part += 1
        my_bar.progress(total_part, text=text)

    if "riskcalculador_fia" not in st.session_state:
        st.session_state.riskcalculador_fia = dadosRiscoFundos(
            "STRIX FIA", manager_sql=st.session_state.manager_sql
        )

    next_total_part = total_part + part
    while total_part <= next_total_part:
        total_part += 1
        if total_part > 100:
            total_part = 99
        my_bar.progress(total_part, text=text)
        if total_part == 99:
            break

    if "riskcalculator_yield" not in st.session_state:
        st.session_state.riskcalculator_yield = dadosRiscoFundos(
            "STRIX YIELD MASTER F", manager_sql=st.session_state.manager_sql
        )

    my_bar.progress(100, text=text)
    my_bar.empty()
