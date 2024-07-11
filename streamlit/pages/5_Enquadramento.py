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

import pandas as pd
import streamlit as st
from db_helper import SQL_Manager
from py_tools import FuncoesPyTools
from relatoriosRisco import enquadramentoCarteira

if "manager_sql" not in st.session_state:
    st.session_state.manager_sql = SQL_Manager()

if "funcoes_pytools" not in st.session_state:
    st.session_state.funcoes_pytools = FuncoesPyTools(st.session_state.manager_sql)

if "relatorio_risco" not in st.session_state:
    st.session_state.relatorio_risco = enquadramentoCarteira(
        manager_sql=st.session_state.manager_sql,
        funcoes_pytools=st.session_state.funcoes_pytools,
    )


def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine="xlsxwriter")
    df.to_excel(writer, index=False, sheet_name="Sheet1")
    writer.close()
    processed_data = output.getvalue()
    return processed_data


if "logo_enquadramento" not in st.session_state:
    st.session_state.logo_enquadramento = True

if "check_download_gerencial" not in st.session_state:
    st.session_state.check_download_gerencial = False

if "check_download_regulamento" not in st.session_state:
    st.session_state.check_download_regulamento = False

if "check_download_todos" not in st.session_state:
    st.session_state.check_download_todos = False

st.set_page_config(
    page_title="Strix Capital",
    page_icon="🦉",
    layout="wide",
    initial_sidebar_state="expanded",
)


def LogoStrix():
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 0.01])
        col2.image(
            os.path.join(base_path, "streamlit", "static", "logotipo_strix.png"),  # type: ignore
            width=500,
        )


def check_last_refdate_carteira_yield(refdate):

    check_carteira = st.session_state.manager_sql.check_if_data_exists(
        f"SELECT DISTINCT FUNDO FROM TB_CARTEIRAS "
        f"WHERE FUNDO = 'STRIX YIELD MASTER' AND REFDATE = '{st.session_state.funcoes_pytools.convert_data_sql(refdate)}'"
    )

    if check_carteira:
        return True
    else:
        return False


def restart_states():

    st.session_state.logo_enquadramento = True

    if "check_download_gerencial" in st.session_state:
        st.session_state.check_download_gerencial = False

    if "check_download_regulamento" in st.session_state:
        st.session_state.check_download_regulamento = False

    if "check_download_todos" in st.session_state:
        st.session_state.check_download_todos = False

    if "df_enquadramento_emissores" in st.session_state:
        st.session_state.df_enquadramento_emissores = None

    if "df_enquadramento_grupo_economico" in st.session_state:
        st.session_state.df_enquadramento_grupo_economico = None

    if "df_enquadramento_modalidade" in st.session_state:
        st.session_state.df_enquadramento_modalidade = None


def altura_tabela(linhas):

    if linhas > 30:
        mult = 36.1
    else:
        mult = 38

    altura = int(round(linhas * mult, 0))

    if altura > 1155:
        altura = 1155
    else:
        altura = altura

    return altura


if st.session_state.logo_enquadramento:
    LogoStrix()

refdate = st.sidebar.date_input(
    label="Refdate",
    value=st.session_state.funcoes_pytools.workday_br(date.today(), -1),
    format="DD/MM/YYYY",
    on_change=restart_states,
)


def run_dados():

    st.session_state.relatorio_risco.set_refdate(refdate)
    st.session_state.relatorio_risco.call_suportes()
    st.session_state.relatorio_risco.call_dados_yield_master()


def enquadramento_regulamento():

    st.session_state.relatorio_risco.call_enquadramento_modalidade_ativos_com_limite()
    df_enquadramento_modalidades = (
        st.session_state.relatorio_risco.df_enquadramento_modalidade_ativos_com_limite
    )
    df_enquadramento_modalidades = st.session_state.relatorio_risco.formatar_valores(
        df_enquadramento_modalidades
    )

    st.session_state.relatorio_risco.call_enquadramento_grupos_economicos_com_limite()
    df_grupo_economico_instituicoes_financeiras = (
        st.session_state.relatorio_risco.df_instituicoes_financeiras
    )
    df_grupo_economico_companhias_abertas = (
        st.session_state.relatorio_risco.df_companhias_abertas
    )
    df_grupo_economico_companhas_fechadas = (
        st.session_state.relatorio_risco.df_companhias_fechadas
    )

    df_grupo_economico_instituicoes_financeiras = (
        st.session_state.relatorio_risco.formatar_valores(
            df_grupo_economico_instituicoes_financeiras
        )
    )
    df_grupo_economico_companhias_abertas = (
        st.session_state.relatorio_risco.formatar_valores(
            df_grupo_economico_companhias_abertas
        )
    )
    df_grupo_economico_companhas_fechadas = (
        st.session_state.relatorio_risco.formatar_valores(
            df_grupo_economico_companhas_fechadas
        )
    )

    st.session_state.logo_enquadramento = False
    LogoStrix()

    with st.container():
        col1, col2, col3 = st.columns([0.4, 2, 0.1])

        df_enquadramento_grupo_economico = (
            st.session_state.relatorio_risco.df_enquadramento_grupos_economicos_com_limite.copy()
        )
        df_enquadramento_grupo_economico.insert(0, "Refdate", refdate)
        st.session_state.df_enquadramento_grupo_economico = (
            df_enquadramento_grupo_economico
        )

        df_enquadramento_modalidade = (
            st.session_state.relatorio_risco.df_enquadramento_modalidade_ativos_com_limite.copy()
        )
        df_enquadramento_modalidade.insert(0, "Refdate", refdate)
        st.session_state.df_enquadramento_modalidade = df_enquadramento_modalidade

        with col2.container():

            st.title("Relatório de Enquadramento")

            st.subheader("Limites Enquadramento por Modalidade Ativos")
            st.dataframe(df_enquadramento_modalidades, hide_index=True, width=1150)

            st.subheader("Limites Enquadramento por Grupo Econômico")
            st.dataframe(
                df_grupo_economico_instituicoes_financeiras, hide_index=True, width=1150
            )

            altura = altura_tabela(df_grupo_economico_companhias_abertas.shape[0])
            st.dataframe(
                df_grupo_economico_companhias_abertas,
                hide_index=True,
                width=1150,
                height=altura,
            )

            st.dataframe(
                df_grupo_economico_companhas_fechadas, hide_index=True, width=1150
            )

    if "check_download_gerencial" in st.session_state:
        st.session_state.check_download_gerencial = False

    st.session_state.check_download_regulamento = True


def enquadramento_gerencial():

    st.session_state.relatorio_risco.call_enquadramento_emissores()
    df_enquadramento_emissores = (
        st.session_state.relatorio_risco.df_enquandramento_emissores
    )
    df_enquadramento_emissores_formated = df_enquadramento_emissores.copy()
    df_enquadramento_emissores_formated = (
        st.session_state.relatorio_risco.formatar_valores(
            df_enquadramento_emissores_formated
        )
    )
    df_enquadramento_emissores.insert(0, "Refdate", refdate)

    st.session_state.df_enquadramento_emissores = df_enquadramento_emissores

    altura = altura_tabela(df_enquadramento_emissores.shape[0])

    st.session_state.logo_enquadramento = False
    LogoStrix()

    with st.container():
        col1, col2, col3 = st.columns([0.5, 6, 1.5])

        with col2.container():

            st.title("Limites Enquadramento Emissores")
            st.dataframe(
                df_enquadramento_emissores_formated,
                hide_index=True,
                height=altura,
                use_container_width=True,
            )

    if "check_download_regulamento" in st.session_state:
        st.session_state.check_download_regulamento = False

    st.session_state.check_download_gerencial = True


def enquadramento_todos():

    st.session_state.relatorio_risco.call_enquadramento_modalidade_ativos_com_limite()
    df_enquadramento_modalidades = (
        st.session_state.relatorio_risco.df_enquadramento_modalidade_ativos_com_limite
    )
    df_enquadramento_modalidades = st.session_state.relatorio_risco.formatar_valores(
        df_enquadramento_modalidades
    )

    st.session_state.relatorio_risco.call_enquadramento_grupos_economicos_com_limite()
    df_grupo_economico_instituicoes_financeiras = (
        st.session_state.relatorio_risco.df_instituicoes_financeiras
    )
    df_grupo_economico_companhias_abertas = (
        st.session_state.relatorio_risco.df_companhias_abertas
    )
    df_grupo_economico_companhas_fechadas = (
        st.session_state.relatorio_risco.df_companhias_fechadas
    )

    df_grupo_economico_instituicoes_financeiras = (
        st.session_state.relatorio_risco.formatar_valores(
            df_grupo_economico_instituicoes_financeiras
        )
    )
    df_grupo_economico_companhias_abertas = (
        st.session_state.relatorio_risco.formatar_valores(
            df_grupo_economico_companhias_abertas
        )
    )
    df_grupo_economico_companhas_fechadas = (
        st.session_state.relatorio_risco.formatar_valores(
            df_grupo_economico_companhas_fechadas
        )
    )

    st.session_state.relatorio_risco.call_enquadramento_emissores()
    df_enquadramento_emissores = (
        st.session_state.relatorio_risco.df_enquandramento_emissores
    )
    df_enquadramento_emissores = st.session_state.relatorio_risco.formatar_valores(
        df_enquadramento_emissores
    )

    df_enquadramento_modalidade = (
        st.session_state.relatorio_risco.df_enquadramento_modalidade_ativos_com_limite.copy()
    )
    df_enquadramento_modalidade.insert(0, "Refdate", refdate)
    st.session_state.df_enquadramento_modalidade = df_enquadramento_modalidade

    df_enquadramento_grupo_economico = (
        st.session_state.relatorio_risco.df_enquadramento_grupos_economicos_com_limite.copy()
    )
    df_enquadramento_grupo_economico.insert(0, "Refdate", refdate)
    st.session_state.df_enquadramento_grupo_economico = df_enquadramento_grupo_economico

    df_enquadramento_emissores = (
        st.session_state.relatorio_risco.df_enquandramento_emissores
    )
    df_enquadramento_emissores.insert(0, "Refdate", refdate)
    st.session_state.df_enquadramento_emissores = df_enquadramento_emissores

    altura = altura_tabela(df_enquadramento_emissores.shape[0])

    st.session_state.logo_enquadramento = False
    LogoStrix()

    with st.container():
        col1, col2, col3 = st.columns([1.2, 6, 1])

        with col2.container():

            st.title("Relatórios de Enquadramento")

            st.subheader("Limites Enquadramento por Modalidade Ativos")
            st.dataframe(df_enquadramento_modalidades, hide_index=True, width=1300)

            st.subheader("Limites Enquadramento por Grupo Econômico")
            st.text("Instituições Financeiras")
            st.dataframe(
                df_grupo_economico_instituicoes_financeiras, hide_index=True, width=1300
            )

            st.text("Companhias Abertas")
            st.dataframe(
                df_grupo_economico_companhias_abertas, hide_index=True, width=1300
            )

            st.text("Companhias Fechadas")
            st.dataframe(
                df_grupo_economico_companhas_fechadas, hide_index=True, width=1300
            )

            st.subheader("Limites Enquadramento Emissores")
            st.dataframe(
                df_enquadramento_emissores, hide_index=True, width=1300, height=altura
            )

    if "check_download_gerencial" in st.session_state:
        st.session_state.check_download_gerencial = False

    if "check_download_regulamento" in st.session_state:
        st.session_state.check_download_regulamento = False

    st.session_state.check_download_todos = True


if not check_last_refdate_carteira_yield(refdate):
    st.warning(
        f"Relatório de enquadramento ainda não disponiveis para {refdate.strftime('%d/%m/%Y')}"
    )
else:
    run_dados()

    st.sidebar.button(
        "Regulamento", use_container_width=True, on_click=enquadramento_regulamento
    )
    st.sidebar.button(
        "Gerencial", use_container_width=True, on_click=enquadramento_gerencial
    )
    st.sidebar.button("Todos", use_container_width=True, on_click=enquadramento_todos)

    if st.session_state.check_download_gerencial:

        st.sidebar.divider()
        st.sidebar.download_button(
            label="Download - Emissores",
            data=to_excel(st.session_state.df_enquadramento_emissores),
            file_name="relatorio_enquadramento_emissores.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            on_click=enquadramento_gerencial,
            use_container_width=True,
        )

    if st.session_state.check_download_regulamento:

        st.sidebar.divider()
        st.sidebar.download_button(
            label="Download - Modalidade Ativos",
            data=to_excel(st.session_state.df_enquadramento_modalidade),
            file_name="relatorio_enquadramento_modalidade_ativos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            on_click=enquadramento_regulamento,
            key="download_modalidade",
        )

        st.sidebar.download_button(
            label="Download - Grupo Econômico",
            data=to_excel(st.session_state.df_enquadramento_grupo_economico),
            file_name="relatorio_enquadramento_grupo_economico.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            on_click=enquadramento_regulamento,
            key="download_grupo_economico",
        )

    if st.session_state.check_download_todos:

        st.sidebar.divider()

        st.sidebar.download_button(
            label="Download - Emissores",
            data=to_excel(st.session_state.df_enquadramento_emissores),
            file_name="relatorio_enquadramento_emissores.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            on_click=enquadramento_todos,
            use_container_width=True,
            key="download_emissores",
        )

        st.sidebar.download_button(
            label="Download - Modalidade Ativos",
            data=to_excel(st.session_state.df_enquadramento_modalidade),
            file_name="relatorio_enquadramento_modalidade_ativos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            on_click=enquadramento_todos,
            key="download_modalidade2",
        )

        st.sidebar.download_button(
            label="Download - Grupo Econômico",
            data=to_excel(st.session_state.df_enquadramento_grupo_economico),
            file_name="relatorio_enquadramento_grupo_economico.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            on_click=enquadramento_todos,
            key="download_grupo_economico2",
        )
