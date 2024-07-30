from datetime import date, datetime
from io import BytesIO  # noqa: F403, F405, E402, F401

import pandas as pd
import streamlit as st
from __init__ import *  # noqa: F403

append_paths()  # noqa: F405

from risco.relatoriosRisco import enquadramentoCarteira  # noqa: F403, F405, E402
from streamlitPanel.streamlit_helper import tabelasHTML  # noqa: F403, F405, E402
from tools.biblioteca_processos import capturaDados  # noqa: F403, F405, E402
from tools.db_helper import SQL_Manager  # noqa: F403, F405, E402

# -------------------------------------------------------------------------------------------------------

VERSION_APP = "1.0.0"
VERSION_REFDATE = "2024-07-10"
ENVIRONMENT = os.getenv("ENVIRONMENT")  # noqa: F403, F405
SCRIPT_NAME = os.path.basename(__file__)  # noqa: F403, F405

if ENVIRONMENT == "DEVELOPMENT":
    print(f"{SCRIPT_NAME.upper()} - {ENVIRONMENT} - {VERSION_APP} - {VERSION_REFDATE}")

# -------------------------------------------------------------------------------------------------------

if "manager_sql" not in st.session_state:
    st.session_state.manager_sql = SQL_Manager()

if "logo_pre_trading" not in st.session_state:
    st.session_state.logo_pre_trading = True

if "enquadramento" not in st.session_state:
    st.session_state.enquadramento = enquadramentoCarteira(st.session_state.manager_sql)

if "capturaDados" not in st.session_state:
    st.session_state.capturaDados = capturaDados(st.session_state.manager_sql)

if "tabela_normal_html" not in st.session_state:
    st.session_state.tabela_normal_html = tabelasHTML.df_to_normal_html

if "tabela_transpose_html" not in st.session_state:
    st.session_state.tabela_transpose_html = tabelasHTML.df_to_transpose_html

st.set_page_config(
    page_title="Strix Capital - Pré Trade",
    page_icon="🦉",
    layout="wide",
    initial_sidebar_state="expanded",
)

lista_states = ["enquadramento_boletas_pre_trading"]

for state in lista_states:
    if state not in st.session_state:
        st.session_state[state] = False


def desliga_states():
    st.session_state.logo_pre_trading = True
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
        col1, col2, col3 = st.columns([1.4, 2, 0.1])
        col2.image(
            os.path.join(base_path, "streamlitPanel", "static", "logotipo_strix.png"),  # noqa: F403, F405, E402  # type: ignore
            width=350,
        )
    st.divider()


def lists_suporte_refdate_month_year():

    df_refdates = st.session_state.manager_sql.select_dataframe(
        "SELECT DISTINCT TRADE_DATE FROM TB_BOLETAS_PRE_TRADING ORDER BY TRADE_DATE")
    df_refdates['month_year'] = df_refdates['TRADE_DATE'].apply(lambda x: x.strftime('%m/%Y'))

    df = df_refdates['TRADE_DATE'].copy()

    df = pd.to_datetime(df)

    return df, df_refdates['month_year'].unique().tolist()


df_refdates, list_month_year = lists_suporte_refdate_month_year()

select_periodo = st.sidebar.selectbox(label="Tipo Período", options=["Diário", "Mensal"], index=1)

if select_periodo == "Mensal":
    select_month_year = st.sidebar.selectbox(label="Mês-Ano", options=list_month_year, index=len(list_month_year) - 1)

    report_month = int(select_month_year.split("/")[0])
    report_year = int(select_month_year.split("/")[1])

    list_refdate = df_refdates[(df_refdates.dt.month == report_month) & (df_refdates.dt.year == report_year)].tolist()
    list_refdate = [x.strftime('%Y-%m-%d') for x in list_refdate]

else:
    list_refdate = [st.sidebar.selectbox(label="Refdate", options=[x.strftime('%Y-%m-%d') for x in df_refdates.tolist()], index=len(df_refdates) - 1)]


st.sidebar.divider()

select_state("enquadramento_boletas_pre_trading")

if st.session_state["enquadramento_boletas_pre_trading"] is True:

    st.session_state.logo_pre_trading = False
    LogoStrix()

    for refdate in list_refdate:

        def captura_lista_hist_ativos():
            max_refdate = st.session_state.capturaDados.lastRefdateCarteira(fundo="Strix Yield Master", refdate=refdate)

            lista_ativos_hist = st.session_state.manager_sql.select_dataframe(
                "SELECT DISTINCT ATIVO FROM TB_CARTEIRAS "
                f"WHERE REFDATE = '{max_refdate}' AND TIPO_ATIVO NOT IN ('Provisões & Despesas')")['ATIVO'].tolist()

            return lista_ativos_hist

        def get_dfs_bases():

            st.session_state.enquadramento.call_enquadramento_pre_trading(refdate)

            df_boletas_pre_trading = st.session_state.manager_sql.select_dataframe(
                "SELECT ATIVO, SUM(QUANTIDADE) AS QUANTIDADE, SUM(QUANTIDADE * PU) AS FINANCEIRO FROM TB_BOLETAS_PRE_TRADING "
                f"WHERE TRADE_DATE = '{refdate}' GROUP BY ATIVO")

            df_modalidade = st.session_state.enquadramento.df_detalhes_boletas_pre_trading_modalidade_ativos_com_limite
            df_grupo_economico = st.session_state.enquadramento.df_detalhes_boletas_pre_trading_enquadramento_grupo_economico
            df_emissor = st.session_state.enquadramento.df_detalhes_boletas_pre_trading_enquadramento_emissores

            return df_boletas_pre_trading, df_modalidade, df_grupo_economico, df_emissor

        def get_dfs_html(df_modalidade_ativo, df_grupo_economico_ativo, df_emissor_ativo, df_boletas_pre_trading_ativo):

            df_info_ativo = pd.DataFrame({
                "Ativo": [ativo],
                "Emissor": [df_emissor_ativo['EMISSOR'][0]],
                "Grupo Econômico": [df_emissor_ativo['GRUPO_ECONOMICO'][0]],
                "Modalidade Ativo": [
                    "Não se encaixa" if pd.isna(
                        df_modalidade_ativo['Modalidade Enquadramento'][0]) else df_modalidade_ativo['Modalidade Enquadramento'][0]],
                "Volume Pré-Trade": [f"R$ {df_boletas_pre_trading_ativo['FINANCEIRO'][0]:,.2F}"],
                "Ativo Novo": ["Sim" if ativo not in lista_ativos_hist else "Não"]
            })

            df_exposicao = pd.DataFrame({
                "": ['Antes Pré-Trade', 'Após Pré-Trade', 'Limite', 'Status'],
                "Exposição Emissor": [
                    f"{df_emissor_ativo['Exposição Dm1'][0] * 100:,.2f}%" if pd.notna(df_emissor_ativo['Exposição Dm1'][0]) else '--',
                    f"{df_emissor_ativo['Exposição'][0] * 100:,.2f}%",
                    f"{df_emissor_ativo['Limite Individual'][0] * 100:,.0f}%",
                    df_emissor_ativo['Status Enquadramento'][0]],
                "Exposição Grupo Econômico": [
                    f"{df_grupo_economico_ativo['Exposição Dm1'][0] * 100:,.2f}%" if pd.notna(df_grupo_economico_ativo['Exposição Dm1'][0]) else '--',
                    f"{df_grupo_economico_ativo['Exposição'][0] * 100:,.2f}%",
                    f"{df_grupo_economico_ativo['Limite Individual'][0] * 100:,.0f}%",
                    df_grupo_economico_ativo['Status Enquadramento'][0]],
                "Exposição Modalidade": [
                    "Não se encaixa" if pd.isna(
                        df_modalidade_ativo['Exposição Dm1'][0]) else f"{df_modalidade_ativo['Exposição Dm1'][0] * 100:,.2f}%",
                    "Não se encaixa" if pd.isna(
                        df_modalidade_ativo['Exposição'][0]) else f"{df_modalidade_ativo['Exposição'][0] * 100:,.2f}%",
                    "Não se encaixa" if pd.isna(
                        df_modalidade_ativo['Limite Individual'][0]) else f"{df_modalidade_ativo['Limite Individual'][0] * 100:,.2f}%",
                    "Não se encaixa" if pd.isna(
                        df_modalidade_ativo['Status Enquadramento'][0]) else df_modalidade_ativo['Status Enquadramento'][0]
                ]
            })

            df_info_ativo_html = st.session_state.tabela_transpose_html(df_info_ativo, width=20)
            df_exposicao_html = st.session_state.tabela_normal_html(df_exposicao, width=30, align_text="center")

            return df_info_ativo_html, df_exposicao_html

        lista_ativos_hist = captura_lista_hist_ativos()

        df_boletas_pre_trading, df_modalidade, df_grupo_economico, df_emissor = get_dfs_bases()

        ativos = pd.concat([
            df_modalidade['ATIVO'],
            df_grupo_economico['ATIVO'],
            df_emissor['ATIVO'],
            df_boletas_pre_trading['ATIVO']
        ]).unique()

        st.subheader(datetime.strptime(refdate, '%Y-%m-%d').strftime('%d/%m/%Y'))

        for ativo in ativos:

            df_modalidade_ativo = df_modalidade[df_modalidade['ATIVO'] == ativo].copy()
            df_grupo_economico_ativo = df_grupo_economico[df_grupo_economico['ATIVO'] == ativo].copy()
            df_emissor_ativo = df_emissor[df_emissor['ATIVO'] == ativo].copy()
            df_boletas_pre_trading_ativo = df_boletas_pre_trading[df_boletas_pre_trading['ATIVO'] == ativo].copy()

            df_info_ativo_html, df_exposicao_html = get_dfs_html(
                df_modalidade_ativo,
                df_grupo_economico_ativo,
                df_emissor_ativo,
                df_boletas_pre_trading_ativo
            )

            with st.container(border=True):
                st.html(df_info_ativo_html)
                st.html(df_exposicao_html)

if st.session_state.logo_pre_trading:
    LogoStrix()
