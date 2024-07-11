from __init__ import *

VERSION_APP = "1.0.0"
VERSION_REFDATE = "2024-07-10"
ENVIRONMENT = os.getenv("ENVIRONMENT")
SCRIPT_NAME = os.path.basename(__file__)

if ENVIRONMENT == "DEVELOPMENT":
    print(f"{SCRIPT_NAME.upper()} - {ENVIRONMENT} - {VERSION_APP} - {VERSION_REFDATE}")

append_paths()

# -----------------------------------------------------------------------

from io import BytesIO

import pandas as pd
import streamlit as st
from db_helper import SQL_Manager
from py_tools import FuncoesPyTools

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

if "logo_info_fundos" not in st.session_state:
    st.session_state.logo_info_fundos = True

if "df_dados_fundos_infos_fundos" not in st.session_state:
    st.session_state.df_dados_fundos_infos_fundos = (
        st.session_state.manager_sql.select_dataframe(f"SELECT * FROM TB_INFOS_FUNDOS")
    )


def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine="xlsxwriter")
    df.to_excel(writer, index=False, sheet_name="Sheet1")
    writer.close()
    processed_data = output.getvalue()
    return processed_data


def LogoStrix():
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 0.1])
        col2.image(
            os.path.join(base_path, "streamlit", "static", "logotipo_strix.png"),  # type: ignore
            width=500,
        )


if st.session_state.logo_info_fundos:
    LogoStrix()


for fundo in st.session_state.df_dados_fundos_infos_fundos["FUNDO"].unique():

    df_fundo = st.session_state.df_dados_fundos_infos_fundos[
        st.session_state.df_dados_fundos_infos_fundos["FUNDO"] == fundo
    ].copy()

    with st.container(border=True):

        st.write(f"### {fundo}")

        with st.container():
            col1, col2, col3, col4, col5, col6 = st.columns([0.9, 0.8, 0.8, 0.8, 1, 1])

            col1.text(f"Razão Social: {df_fundo['RAZAO_SOCIAL'].values[0]}")
            col1.text(
                f"CNPJ: {st.session_state.funcoes_pytools.formatar_cnpj(df_fundo['CNPJ'].values[0])}"
            )
            col1.text(f"Qualificação: {df_fundo['QUALIFICACAO'].values[0]}")
            col1.text(f"Restrição: {df_fundo['RESTRICAO'].values[0]}")
            col1.text(f"Condomínio: {df_fundo['CONDOMINIO'].values[0]}")
            col1.text(f"Tributação: {df_fundo['TRIBUTACAO'].values[0]}")
            col1.text(f"Exercício Fiscal: {df_fundo['EXERCICIO_FISCAL'].values[0]}")

            col2.text(f"Banco Conta BTG: {df_fundo['BANCO_BTG'].values[0]}")
            col2.text(f"Agencia Conta BTG: {df_fundo['AGENCIA_BTG'].values[0]}")
            col2.text(f"Conta BTG: {df_fundo['CONTA_BTG'].values[0]}")
            col2.text(f"Conta SELIC: {df_fundo['CONTA_SELIC'].values[0]}")
            col2.text(f"Conta CETIP: {df_fundo['CONTA_CETIP'].values[0]}")
            col2.text(f"Conta CBLC Cliente: {df_fundo['CONTA_CBLC_CLIENTE'].values[0]}")
            col2.text(f"Conta CBLC Usuário: {df_fundo['CONTA_CBLC_USUARIO'].values[0]}")
            col2.text(
                f"Conta CBLC Custodia: {df_fundo['CONTA_CBLC_CUSTODIA'].values[0]}"
            )

            col3.text(f"Cod. Isin: {df_fundo['CODIGO_ISIN'].values[0]}")
            col3.text(f"Cod. ANBID: {df_fundo['CODIGO_ANBID'].values[0]}")
            col3.text(f"Cod. GIIN: {df_fundo['CODIGO_GIIN'].values[0]}")
            col3.text(f"Cod. Mneumônico: {df_fundo['CODIGO_MNEUMONICO'].values[0]}")
            col3.text(f"Cod. Galgo: {df_fundo['CODIGO_GALGO'].values[0]}")
            col3.text(f"Ticket B3: {df_fundo['TICKETB3'].values[0]}")

            col4.text(f"Aberto Captação: {df_fundo['ABERTO_CAPTACAO'].values[0]}")
            col4.text(f"Cot. Aplicação: D+{df_fundo['QUOTIZACAO_APLICACAO'].values[0]}")
            col4.text(f"Cot. Resgate: D+{df_fundo['QUOTIZACAO_RESGATE'].values[0]}")
            col4.text(f"Liq. Resgate: D+{df_fundo['LIQUIDACAO_RESGATE'].values[0]}")
            col4.text(f"Aplicação Inicial: {df_fundo['APLICACAO_INICIAL'].values[0]}")
            col4.text(f"Mov. Minima: {df_fundo['MOVIMENTACAO_MINIMA'].values[0]}")
            col4.text(f"Saldo Minimo: {df_fundo['SALDO_MINIMO'].values[0]}")

            tx_adm = df_fundo["TAXA_DE_ADMINISTRACAO"].values[0]
            if tx_adm < 1:
                tx_adm = f"{tx_adm:.2f}%"
            else:
                tx_adm = f"R$ {tx_adm:,.2f}"

            col5.text(f"Taxa Adm: {tx_adm}")
            col5.text(
                f"Taxa Adm Mín: {df_fundo['TAXA_ADMINISTRACAO_MINIMA'].values[0]}"
            )
            col5.text(f"Taxa Perf: {df_fundo['TAXA_DE_PERFORMANCE'].values[0]}")
            col5.text(f"Benchmark: {df_fundo['BENCHMARCK'].values[0]}")
            col5.text(f"Taxa Custódia: {df_fundo['TAXA_CUSTODIA'].values[0]}")

            col6.text(
                f"Fundo de Infraestrutura: {df_fundo['FUNDO_INFRAESTRUTURA'].values[0]}"
            )
            col6.text(f"Classificação CVM: {df_fundo['CLASSIFICACAO_CVM'].values[0]}")
            col6.text(
                f"Classificação ANBIMA: {df_fundo['CLASSIFICACAO_AMBIMA'].values[0]}"
            )
            col6.text(f"Perfil Risco: {df_fundo['PERFIL_DE_RISCO'].values[0]}")
