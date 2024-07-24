import os
from datetime import date
from io import BytesIO

import pandas as pd
import streamlit as st
from __init__ import append_paths, base_path

from risco.relatoriosRisco import liquidezAtivos
from tools.db_helper import SQL_Manager
from tools.py_tools import FuncoesPyTools

# -----------------------------------------------------------------------


VERSION_APP = "1.0.1"
VERSION_REFDATE = "2024-07-15"
ENVIRONMENT = os.getenv("ENVIRONMENT")
SCRIPT_NAME = os.path.basename(__file__)

if ENVIRONMENT == "DEVELOPMENT":
    print(f"{SCRIPT_NAME.upper()} - {ENVIRONMENT} - {VERSION_APP} - {VERSION_REFDATE}")

append_paths()

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
    st.session_state.funcoes_pytools = FuncoesPyTools(manager_sql=st.session_state.manager_sql)

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
            width=350,
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
        # -------------------------------------------------------------------------------------------------------
        # Definições de exibições:
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

            if len(fundos) == 1:
                colunas = st.columns(2)
            else:
                colunas = st.columns(len(fundos))

            for fundo in fundos:

                for idx, fundo in enumerate(fundos):
                    df_fundo = df_resumo_observaveis_formated[
                        df_resumo_observaveis_formated["Fundo"] == fundo
                    ][
                        [
                            "Refdate",
                            "Posição dia",
                            "Premissa venda",
                            "Saldo posição dia",
                            "Liquidez gerada dia",
                            "Liquidez total gerada",
                        ]
                    ]

                    with colunas[idx]:
                        st.subheader(fundo)
                        st.dataframe(
                            df_fundo, hide_index=True, height=900, use_container_width=True
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

            if len(fundos) == 1:
                colunas = st.columns(2)
            else:
                colunas = st.columns(len(fundos))

            for idx, fundo in enumerate(fundos):
                df_fundo = df_ativos_observaveis_formated[
                    df_ativos_observaveis_formated["Fundo"] == fundo
                ][
                    [
                        "Refdate",
                        "Ativo",
                        "Posição dia",
                        "Premissa venda",
                        "Saldo posição dia",
                        "Liquidez gerada dia",
                        "Liquidez total gerada",
                    ]
                ]

                with colunas[idx]:
                    st.subheader(fundo)
                    ativos = df_fundo["Ativo"].unique()
                    for ativo in ativos:
                        df_ativo = df_fundo[
                            (df_fundo["Ativo"] == ativo) & (df_fundo["Posição dia"] != "0") & (df_fundo["Liquidez gerada dia"] != "0")
                        ].reset_index(drop=True)
                        st.dataframe(df_ativo, hide_index=True, use_container_width=True)

        def exibir_resumno_titulos_publicos(df):

            df_resumo_titulos_publicos = df.copy()

            df_resumo_titulos_publicos_formated = (
                st.session_state.funcoes_pytools.format_df_float_columns_to_str(
                    df=df_resumo_titulos_publicos,
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

            fundos = df_resumo_titulos_publicos_formated["Fundo"].unique()

            if len(fundos) == 1:
                colunas = st.columns(2)
            else:
                colunas = st.columns(len(fundos))

            for fundo in fundos:

                for idx, fundo in enumerate(fundos):
                    df_fundo = df_resumo_titulos_publicos_formated[
                        df_resumo_titulos_publicos_formated["Fundo"] == fundo
                    ][
                        [
                            "Refdate",
                            "Posição dia",
                            "Premissa venda",
                            "Saldo posição dia",
                            "Liquidez gerada dia",
                            "Liquidez total gerada",
                        ]
                    ]

                    with colunas[idx]:
                        st.subheader(fundo)
                        st.dataframe(df_fundo, hide_index=True, use_container_width=True)

        def exibir_titulos_publicos_por_ativo(df):

            df_ativos_titulo_publicos = df.copy()

            df_ativos_titulo_publicos = df_ativos_titulo_publicos.sort_values(
                by=["Fundo", "Tipo Ativo", "Ativo", "Refdate"]
            )

            df_ativos_titulo_publicos_formated = (
                st.session_state.funcoes_pytools.format_df_float_columns_to_str(
                    df=df_ativos_titulo_publicos,
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

            fundos = df_ativos_titulo_publicos_formated["Fundo"].unique()

            if len(fundos) == 1:
                colunas = st.columns(2)
            else:
                colunas = st.columns(len(fundos))

            for idx, fundo in enumerate(fundos):
                df_fundo = df_ativos_titulo_publicos_formated[
                    df_ativos_titulo_publicos_formated["Fundo"] == fundo
                ][
                    [
                        "Refdate",
                        "Ativo",
                        "Posição dia",
                        "Premissa venda",
                        "Saldo posição dia",
                        "Liquidez gerada dia",
                        "Liquidez total gerada",
                    ]
                ]

                with colunas[idx]:
                    st.subheader(fundo)
                    ativos = df_fundo["Ativo"].unique()
                    for ativo in ativos:
                        df_ativo = df_fundo[(df_fundo["Ativo"] == ativo)].reset_index(drop=True)
                        st.dataframe(df_ativo, hide_index=True, use_container_width=True)

        def exibir_resumo_fluxos(df_fluxo, df_fluxo_fidcs, df_fluxo_fundos):
            # Concatenar os fundos únicos de todos os DataFrames
            fundos = pd.concat(
                [df_fluxo["Fundo"], df_fluxo_fidcs["Fundo"], df_fluxo_fundos["Fundo"]]
            ).unique()

            for fundo in fundos:
                with st.container(border=True):
                    st.subheader(fundo)

                    # Inicializar as colunas
                    col1, col2, col3 = st.columns(3)

                    # Inicializar uma lista de DataFrames
                    dataframes = []

                    # Adicionar DataFrames não vazios à lista
                    if not df_fluxo[df_fluxo["Fundo"] == fundo].empty:
                        dataframes.append(
                            df_fluxo[df_fluxo["Fundo"] == fundo][
                                [
                                    "Refdate",
                                    "Categoria",
                                    "Liquidez gerada dia",
                                    "Liquidez total gerada",
                                ]
                            ]
                        )

                    if not df_fluxo_fidcs[df_fluxo_fidcs["Fundo"] == fundo].empty:
                        dataframes.append(
                            df_fluxo_fidcs[df_fluxo_fidcs["Fundo"] == fundo][
                                [
                                    "Refdate",
                                    "Categoria",
                                    "Liquidez gerada dia",
                                    "Liquidez total gerada",
                                ]
                            ]
                        )

                    if not df_fluxo_fundos[df_fluxo_fundos["Fundo"] == fundo].empty:
                        dataframes.append(
                            df_fluxo_fundos[df_fluxo_fundos["Fundo"] == fundo][
                                [
                                    "Refdate",
                                    "Categoria",
                                    "Liquidez gerada dia",
                                    "Liquidez total gerada",
                                ]
                            ]
                        )

                    # Adicionar os DataFrames às colunas disponíveis
                    for idx, df in enumerate(dataframes):
                        if idx == 0:
                            col1.dataframe(df, hide_index=True, use_container_width=True)
                        elif idx == 1:
                            col2.dataframe(df, hide_index=True, use_container_width=True)
                        elif idx == 2:
                            col3.dataframe(df, hide_index=True, use_container_width=True)

        def exibir_fluxos_por_ativo(df_fluxo, df_fluxo_fidcs, df_fluxo_fundos):
            # Concatena os DataFrames para obter a lista completa de fundos
            df_combined = pd.concat([df_fluxo, df_fluxo_fidcs, df_fluxo_fundos])

            # Calcula o número de ativos por fundo
            ativos_por_fundo = df_combined.groupby("Fundo")["Ativo"].nunique().reset_index()
            ativos_por_fundo.columns = ["Fundo", "Num_Ativos"]

            # Ordena os fundos pelo número de ativos
            fundos_ordenados = ativos_por_fundo.sort_values("Num_Ativos")["Fundo"].unique()

            for fundo in fundos_ordenados:
                with st.container(border=True):
                    st.subheader(fundo)

                    dataframes = []

                    if not df_fluxo[df_fluxo["Fundo"] == fundo].empty:
                        dataframes.append(
                            df_fluxo[df_fluxo["Fundo"] == fundo][
                                [
                                    "Refdate",
                                    "Categoria",
                                    "Ativo",
                                    "Liquidez gerada dia",
                                    "Liquidez total gerada",
                                ]
                            ]
                        )

                    if not df_fluxo_fidcs[df_fluxo_fidcs["Fundo"] == fundo].empty:
                        dataframes.append(
                            df_fluxo_fidcs[df_fluxo_fidcs["Fundo"] == fundo][
                                [
                                    "Refdate",
                                    "Categoria",
                                    "Ativo",
                                    "Liquidez gerada dia",
                                    "Liquidez total gerada",
                                ]
                            ]
                        )

                    if not df_fluxo_fundos[df_fluxo_fundos["Fundo"] == fundo].empty:
                        dataframes.append(
                            df_fluxo_fundos[df_fluxo_fundos["Fundo"] == fundo][
                                [
                                    "Refdate",
                                    "Categoria",
                                    "Ativo",
                                    "Liquidez gerada dia",
                                    "Liquidez total gerada",
                                ]
                            ]
                        )

                    # Cria colunas dinamicamente com base no número de DataFrames não vazios
                    colunas = st.columns(3)

                    # Itera sobre os DataFrames e ativos dentro de cada DataFrame
                    for idx, df in enumerate(dataframes):
                        ativos = df["Ativo"].unique()
                        for ativo in ativos:
                            df_ativo = df[df["Ativo"] == ativo]
                            with colunas[idx]:
                                st.dataframe(df_ativo, hide_index=True, use_container_width=True)

        def exibir_resumo_fundos_all(df_observaveis, df_titulos_publicos, df_fluxos_all, df_resumo_all):

            df_observaveis = df_observaveis[["Refdate", "Fundo", "Liquidez gerada dia", "Liquidez total gerada"]]
            df_titulos_publicos = df_titulos_publicos[["Refdate", "Fundo", "Liquidez gerada dia", "Liquidez total gerada"]]

            fundos = df_resumo_all["Fundo"].unique()

            for fundo in fundos:
                with st.container(border=True):

                    st.subheader(fundo)

                    # Inicializar as colunas
                    col1, col2, col3, col4 = st.columns(4)

                    # Inicializar uma lista de DataFrames
                    dataframes = []

                    count = 0
                    dict_count = {}

                    # Adicionar DataFrames não vazios à lista
                    if not df_resumo_all[df_resumo_all["Fundo"] == fundo].empty:
                        dataframes.append(
                            df_resumo_all[df_resumo_all["Fundo"] == fundo][
                                ["Refdate", "Liquidez gerada dia", "Liquidez total gerada"]
                            ]
                        )
                        dict_count[count] = "Total"
                        count += 1

                    if not df_observaveis[df_observaveis["Fundo"] == fundo].empty:
                        dataframes.append(
                            df_observaveis[df_observaveis["Fundo"] == fundo][
                                ["Refdate", "Liquidez gerada dia", "Liquidez total gerada"]
                            ]
                        )
                        dict_count[count] = "Mercado Observável"
                        count += 1

                    if not df_fluxos_all[df_fluxos_all["Fundo"] == fundo].empty:
                        dataframes.append(
                            df_fluxos_all[df_fluxos_all["Fundo"] == fundo][
                                ["Refdate", "Liquidez gerada dia", "Liquidez total gerada"]
                            ]
                        )
                        dict_count[count] = "Fluxo"
                        count += 1

                    if not df_titulos_publicos[df_titulos_publicos["Fundo"] == fundo].empty:
                        dataframes.append(
                            df_titulos_publicos[df_titulos_publicos["Fundo"] == fundo][
                                ["Refdate", "Liquidez gerada dia", "Liquidez total gerada"]
                            ]
                        )
                        dict_count[count] = "Tit. Públicos"
                        count += 1

                    # Adicionar os DataFrames às colunas disponíveis
                    for idx, df in enumerate(dataframes):
                        if idx == 0:
                            col1.write(f"***{dict_count[idx]}***")
                            col1.dataframe(df, hide_index=True, use_container_width=True)
                        elif idx == 1:
                            col2.write(f"***{dict_count[idx]}***")
                            col2.dataframe(df, hide_index=True, use_container_width=True)
                        elif idx == 2:
                            col3.write(f"***{dict_count[idx]}***")
                            col3.dataframe(df, hide_index=True, use_container_width=True)

                        elif idx == 3:
                            col4.write(f"***{dict_count[idx]}***")
                            col4.dataframe(df, hide_index=True, use_container_width=True)

        def exibir_resumo_liquidez_x_passivo(df_liquidez_x_passivo):

            fundos = df_liquidez_x_passivo['Fundo'].unique()

            for fundo in fundos:
                df_fundo = df_liquidez_x_passivo[df_liquidez_x_passivo['Fundo'] == fundo].reset_index(drop=True)
                with st.container(border=True):
                    col1, col2, col3 = st.columns(3)
                    col1.subheader(fundo)
                    col1.dataframe(df_fundo, hide_index=True, use_container_width=True)


        # -------------------------------------------------------------------------------------------------------
        # Captura de bases:
        st.session_state.manager_liquidez.set_refdate(refdate)

        df_base_observaveis = st.session_state.manager_liquidez.df_base_liquidez_diaria_observavel
        df_resumo_observaveis = st.session_state.manager_liquidez.df_resumo_liquidez_observavel
        df_base_titulos_publicos = (
            st.session_state.manager_liquidez.df_base_liquidez_diaria_tit_publicos
        )
        df_base_titulos_publicos_resumo = (
            st.session_state.manager_liquidez.df_resumo_liquidez_tit_publicos
        )
        df_base_fluxo_ativos = st.session_state.manager_liquidez.df_base_liquidez_diaria_fluxo
        df_base_fluxo_resumo = st.session_state.manager_liquidez.df_resumo_liquidez_fluxo
        df_base_fluxo_fidcs_ativos = (
            st.session_state.manager_liquidez.df_base_liquidez_diaria_fluxo_fidcs
        )
        df_base_fluxo_fidcs_resumo = st.session_state.manager_liquidez.df_resumo_liquidez_fidcs
        df_base_fluxo_fundos_ativos = (
            st.session_state.manager_liquidez.df_base_liquidez_diaria_fluxo_fundos
        )
        df_base_fluxo_fundos_resumo = st.session_state.manager_liquidez.df_resumo_liquidez_fundos

        df_base_fluxo_all_resumo = st.session_state.manager_liquidez.df_resumo_liquidez_fluxo_all
        df_base_all_resumo = st.session_state.manager_liquidez.df_resumo_liquidez_all

        df_base_liquidez_x_passivo = st.session_state.manager_liquidez.df_liquidez_fundos_x_passivo


        # -------------------------------------------------------------------------------------------------------
        # Header pagina:
        st.header(f"Risco de Liquidez - {refdate.strftime('%d/%m/%Y')}")

        # -------------------------------------------------------------------------------------------------------
        # Tabelas resumo:
        st.subheader("Resumo - Liquidez x Passivo")

        exibir_resumo_liquidez_x_passivo(df_base_liquidez_x_passivo)

        st.subheader("Resumo - Liquidez por Categorias")

        exibir_resumo_fundos_all(
            df_resumo_observaveis,
            df_base_titulos_publicos_resumo,
            df_base_fluxo_all_resumo,
            df_base_all_resumo,
        )


        # -------------------------------------------------------------------------------------------------------
        # Aberuta tabelas resumo:
        st.subheader("Abertura Resumos")

        with st.expander("Mercado Observável - Resumo"):

            exibir_resumo_observaveis(df_resumo_observaveis)

        with st.expander("Títulos Publicos - Resumo"):

            exibir_resumno_titulos_publicos(df_base_titulos_publicos_resumo)

        with st.expander("Fluxo - Resumo"):

            exibir_resumo_fluxos(
                df_base_fluxo_resumo,
                df_base_fluxo_fidcs_resumo,
                df_base_fluxo_fundos_resumo,
            )


        # -------------------------------------------------------------------------------------------------------
        # Abertura tabelas por ativos:
        if view_ativos:
            st.subheader("Abertura Resumos por Ativos")

            with st.expander("Mercado Observável - Ativos"):

                exibir_observaveis_por_ativo(df_base_observaveis)

            with st.expander("Títulos Públicos - Ativos"):

                exibir_titulos_publicos_por_ativo(df_base_titulos_publicos)

            with st.expander("Fluxo - Ativos"):
                exibir_fluxos_por_ativo(
                    df_base_fluxo_ativos,
                    df_base_fluxo_fidcs_ativos,
                    df_base_fluxo_fundos_ativos,
                )
