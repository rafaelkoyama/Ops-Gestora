from __init__ import *

VERSION_APP = "1.0.0"
VERSION_REFDATE = "2024-07-10"
ENVIRONMENT = os.getenv("ENVIRONMENT")
SCRIPT_NAME = os.path.basename(__file__)

if ENVIRONMENT == "DEVELOPMENT":
    print(f"{SCRIPT_NAME.upper()} - {ENVIRONMENT} - {VERSION_APP} - {VERSION_REFDATE}")

# append_paths()

# -----------------------------------------------------------------------

from datetime import date
from io import BytesIO
from time import sleep

import pandas as pd
import streamlit as st

from tools.db_helper import SQL_Manager
from tools.py_tools import FuncoesPyTools, Graficos

st.set_page_config(
    page_title="Strix Capital - Painel de Controle",
    page_icon="🦉",
    layout="wide",
    initial_sidebar_state="expanded",
)

lista_states = [
    "run_grafico_yields",
]

if "manager_sql" not in st.session_state:
    st.session_state.manager_sql = SQL_Manager()

if "funcoes_pytools" not in st.session_state:
    st.session_state.funcoes_pytools = FuncoesPyTools(st.session_state.manager_sql)

if "graficos" not in st.session_state:
    st.session_state.graficos = Graficos()


if "logo_credito_privado" not in st.session_state:
    st.session_state.logo_credito_privado = True


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
            width=300,
        )


def get_df_yields():

    df_base_btg = st.session_state.manager_sql.select_dataframe(
        f"SELECT ATIVO, REFDATE, TAXA AS TAXA_BTG FROM TB_PRECOS WHERE TIPO_ATIVO = 'DEBÊNTURE' AND FONTE = 'BTG' AND TAXA IS NOT NULL AND TAXA <> 0 ORDER BY ATIVO, REFDATE"
    )

    df_base_anbima = st.session_state.manager_sql.select_dataframe(
        "SELECT DISTINCT COD_ATIVO AS ATIVO, REFDATE, TAXA_INDICATIVA/100 AS TAXA_ANBIMA FROM TB_ANBIMA_DEBENTURES ORDER BY COD_ATIVO, REFDATE"
    )

    df_base_anbima = df_base_anbima[df_base_anbima["ATIVO"].isin(df_base_btg["ATIVO"])]

    df_base = pd.merge(
        df_base_btg, df_base_anbima, on=["ATIVO", "REFDATE"], how="inner"
    )

    df_base.loc[:, "TAXA"] = df_base.apply(
        lambda x: x["TAXA_BTG"] if pd.isna(x["TAXA_ANBIMA"]) else x["TAXA_ANBIMA"],
        axis=1,
    )

    df_base = (
        df_base[["ATIVO", "REFDATE", "TAXA"]]
        .sort_values(by=["ATIVO", "REFDATE"])
        .reset_index(drop=True)
    )

    return df_base


if "df_base_yields" not in st.session_state:
    st.session_state.df_base_yields = get_df_yields()

if "select_ativos" not in st.session_state:
    st.session_state.select_ativos = []


opt_selecao = st.sidebar.radio(
    label="Opção",
    options=["Todos os Ativos", "Selecionar Ativos"],
    on_change=desliga_states,
)

if opt_selecao == "Selecionar Ativos":

    st.session_state.select_ativos = st.sidebar.multiselect(
        "Ativos",
        st.session_state.df_base_yields["ATIVO"].unique(),
        default=[],
        on_change=desliga_states,
    )

else:
    st.session_state.select_ativos = st.session_state.df_base_yields["ATIVO"].unique()


st.sidebar.button(
    "Gerar graficos",
    on_click=select_state,
    args=("run_grafico_yields",),
    use_container_width=True,
)


if st.session_state.run_grafico_yields:

    LogoStrix()

    with st.container():

        col1, col2, col3 = st.columns([1, 1, 1])

        df_base = st.session_state.df_base_yields.copy()

        i = 0

        wait_ger = st.sidebar.empty()

        wait_ger.error("Aguarde, gerando gráficos...")

        for ativo in df_base["ATIVO"].unique():

            if ativo in st.session_state.select_ativos:

                df_ativo = df_base[df_base["ATIVO"] == ativo][
                    ["REFDATE", "TAXA"]
                ].copy()
                last_yield = df_ativo["TAXA"].iloc[-1] * 100

                if i == 0:
                    plt = st.session_state.graficos.graficoLinhas(
                        df_dados=df_ativo, titulo_grafico=f"{ativo} - {last_yield:.2f}%"
                    )
                    col1.pyplot(plt)
                    plt.close()
                    i += 1

                elif i == 1:
                    plt = st.session_state.graficos.graficoLinhas(
                        df_dados=df_ativo, titulo_grafico=f"{ativo} - {last_yield:.2f}%"
                    )
                    col2.pyplot(plt)
                    plt.close()
                    i += 1

                elif i == 2:
                    plt = st.session_state.graficos.graficoLinhas(
                        df_dados=df_ativo, titulo_grafico=f"{ativo} - {last_yield:.2f}%"
                    )
                    col3.pyplot(plt)
                    plt.close()
                    i = 0

        wait_ger.success("Gráficos gerados com sucesso!")
        sleep(1)
        wait_ger.empty()
