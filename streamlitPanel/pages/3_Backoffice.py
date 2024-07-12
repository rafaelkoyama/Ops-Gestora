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

from streamlitPanel.streamlit_helper import (
    dict_aux_btg_bases_cc_e_movs,
    extratoContaCorrenteFundos,
    movimentacaoPassivos,
    opcoes_fundos,
    passivosCotizar,
)
from tools.db_helper import SQL_Manager

st.set_page_config(
    page_title="Strix Capital - Painel de Controle",
    page_icon="🦉",
    layout="wide",
    initial_sidebar_state="expanded",
)

lista_states = [
    "extrato_cc_fundos",
    "movs_passivo_fundos",
    "passivos_cotizar",
    "contatos_btg",
]

if "manager_sql" not in st.session_state:
    st.session_state.manager_sql = SQL_Manager()

if "logo_backoffice" not in st.session_state:
    st.session_state.logo_backoffice = True

if "opcoes_fundos" not in st.session_state:
    st.session_state.opcoes_fundos = opcoes_fundos

if "dict_aux_btg_bases_cc_e_movs" not in st.session_state:
    st.session_state.dict_aux_btg_bases_cc_e_movs = dict_aux_btg_bases_cc_e_movs

if "manager_extrato_cc" not in st.session_state:
    st.session_state.manager_extrato_cc = extratoContaCorrenteFundos(
        st.session_state.manager_sql
    )

if "manager_movs_passivo" not in st.session_state:
    st.session_state.manager_movs_passivo = movimentacaoPassivos(
        st.session_state.manager_sql
    )

if "manager_passivos_cotizar" not in st.session_state:
    st.session_state.manager_passivos_cotizar = passivosCotizar(
        st.session_state.manager_sql
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


def save_to_excel(df):
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
            os.path.join(base_path, "streamlitPanel", "static", "logotipo_strix.png"),  # type: ignore
            width=500,
        )


def contatos_btg():

    st.subheader("Contatos BTG", divider="grey")
    col1, col2, col3, col4 = st.columns(4)
    with col1.container(border=True):
        st.markdown(
            "**Eventos de Fundos**",
            help="Abertura de novos fundos, alteração de regulamento, transferência, cisão, incorporação, masterização etc.",
        )
        st.write(os.getenv("EMAIL_BTG_EVENTOS_FUNDOS"))
        st.text(os.getenv("TEXT_BTG_EVENTOS_FUNDOS_1"))
        st.text(os.getenv("TEL_BTG_EVENTOS_FUNDOS_1"))
        st.text(os.getenv("TEXT_BTG_EVENTOS_FUNDOS_2"))
        st.text(os.getenv("TEL_BTG_EVENTOS_FUNDOS_2"))

    with col2.container(border=True):
        st.markdown(
            "**Ativos de Fundo**",
            help="Cálculo de cota, controle de caixa, boletagem de ativos etc.",
        )
        st.write(os.getenv("EMAIL_BTG_ATIVOS_FUNDOS"))
        st.text(os.getenv("TEXT_BTG_ATIVOS_FUNDOS_1"))
        st.text(os.getenv("TEL_BTG_ATIVOS_FUNDOS_1"))
        st.text(os.getenv("TEXT_BTG_ATIVOS_FUNDOS_2"))
        st.text(os.getenv("TEL_BTG_ATIVOS_FUNDOS_2"))

    with col3.container(border=True):
        st.markdown(
            "**Middle Liquids**",
            help="Movimentações de cotistas, extratos de posição, informes de rendimento, relatórios, etc.",
        )
        st.write(os.getenv("EMAIL_BTG_MIDDLE_LIQUIDS"))
        st.text(os.getenv("TEXT_BTG_MIDDLE_LIQUIDS_1"))
        st.text(os.getenv("TEL_BTG_MIDDLE_LIQUIDS_1"))
        st.text(os.getenv("TEXT_BTG_MIDDLE_LIQUIDS_2"))
        st.text(os.getenv("TEL_BTG_MIDDLE_LIQUIDS_2"))

    with col4.container(border=True):
        st.markdown(
            "**Middle Support/Receita**",
            help="Contratos de distribuição, reversão e receita.",
        )
        st.write(os.getenv("EMAIL_BTG_MIDDLE_SUPPORT"))
        st.text(os.getenv("TEXT_BTG_MIDDLE_SUPPORT_1"))
        st.text(os.getenv("TEL_BTG_MIDDLE_SUPPORT_1"))
        st.text(os.getenv("TEXT_BTG_MIDDLE_SUPPORT_2"))
        st.text(os.getenv("TEL_BTG_MIDDLE_SUPPORT_2"))

    with col1.container(border=True):
        st.markdown("**FaaS**", help="API BTG")
        st.write(os.getenv("EMAIL_BTG_FAAS"))


# -----------------------------------------------------------------------------------------------------------------------

opt_data = st.sidebar.radio("Seleção Datas", ["Unica", "Mult"], horizontal=True)

if opt_data == "Mult":
    dmenos = st.sidebar.date_input("Inicial", value=date.today(), format="DD/MM/YYYY")
    refdate = st.sidebar.date_input("Final", value=date.today(), format="DD/MM/YYYY")
elif opt_data == "Unica":
    refdate = st.sidebar.date_input("Refdate", value=date.today(), format="DD/MM/YYYY")

fundos = st.sidebar.multiselect(
    label="Fundos",
    options=st.session_state.opcoes_fundos,
    default=st.session_state.opcoes_fundos,
)

st.sidebar.divider()
st.sidebar.button(
    "Extrato Conta Corrente Fundos",
    use_container_width=True,
    on_click=lambda: select_state("extrato_cc_fundos"),
)
st.sidebar.button(
    "Movimentações Passivo Fundos",
    use_container_width=True,
    on_click=lambda: select_state("movs_passivo_fundos"),
)
st.sidebar.button(
    "Passivos a Cotizar",
    use_container_width=True,
    on_click=lambda: select_state("passivos_cotizar"),
)
st.sidebar.button(
    "Contatos BTG",
    use_container_width=True,
    on_click=lambda: select_state("contatos_btg"),
)

# -----------------------------------------------------------------------------------------------------------------------

if st.session_state["extrato_cc_fundos"] == True:
    st.session_state.logo_backoffice = False
    LogoStrix()

    # Captura dados:

    if opt_data == "Unica":
        st.session_state.manager_extrato_cc.set_refdate(refdate, refdate)
    elif opt_data == "Mult":
        st.session_state.manager_extrato_cc.set_refdate(refdate, dmenos)

    st.session_state.manager_extrato_cc.base_extratos_fundos()

    df_extrato_all = st.session_state.manager_extrato_cc.df_cc_all.copy()

    # Botao download:

    st.sidebar.divider()

    st.sidebar.download_button(
        label="Download - Extrato",
        data=save_to_excel(df_extrato_all),
        file_name="extrato_cc_fundos.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    # Dados Pagina:

    with st.container(border=False):
        col1, col2, col3 = st.columns([0.1, 2, 0.6])

        for fundo in fundos:
            df_fundo = df_extrato_all[
                df_extrato_all["FUNDO"]
                == st.session_state.dict_aux_btg_bases_cc_e_movs[fundo]
            ].copy()
            df_fundo.drop(columns=["FUNDO"], inplace=True)
            col2.subheader(f"Fundo: {fundo}")
            if len(df_fundo) > 0:
                col2.dataframe(df_fundo, use_container_width=True, hide_index=True)
            else:
                col2.write("Sem movimentação no período.")

if st.session_state["movs_passivo_fundos"] == True:
    st.session_state.logo_backoffice = False
    LogoStrix()

    # Captura dados:

    if opt_data == "Unica":
        st.session_state.manager_movs_passivo.set_refdate(refdate, refdate)
    elif opt_data == "Mult":
        st.session_state.manager_movs_passivo.set_refdate(refdate, dmenos)

    st.session_state.manager_movs_passivo.base_movimentacao_passivos()

    df_movs_passivo = st.session_state.manager_movs_passivo.df_mov_passivos.copy()

    # Botao download:

    st.sidebar.divider()

    st.sidebar.download_button(
        label="Download - Movs Passivo",
        data=save_to_excel(df_movs_passivo),
        file_name="extrato_movs_passivo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    # Dados Pagina:

    with st.container(border=False):
        col1, col2, col3 = st.columns([0.1, 2, 0.6])

        for fundo in fundos:
            df_fundo = df_movs_passivo[
                df_movs_passivo["Fundo"]
                == st.session_state.dict_aux_btg_bases_cc_e_movs[fundo]
            ].copy()
            df_fundo.drop(columns=["Fundo"], inplace=True)

            col2.subheader(f"Fundo: {fundo}")
            if len(df_fundo) > 0:
                total_resgates = df_fundo[df_fundo["Operação"] == "RESGATE"][
                    "Financeiro"
                ].sum()
                total_aplicacoes = df_fundo[df_fundo["Operação"] == "APLICAÇÃO"][
                    "Financeiro"
                ].sum()

                if total_aplicacoes > 0 and total_resgates > 0:
                    col2.write(
                        f"Aplicações: R$ {total_aplicacoes:,.0f} | Resgates: R$ {total_resgates:,.0f}"
                    )
                elif total_aplicacoes > 0 and total_resgates == 0:
                    col2.write(f"Aplicações: R$ {total_aplicacoes:,.0f}")
                else:
                    col2.write(f"Resgates: R$ {total_resgates:,.0f}")

                col2.dataframe(df_fundo, use_container_width=True, hide_index=True)
            else:
                col2.write("Sem movimentação no período.")

if st.session_state["passivos_cotizar"] == True:
    st.session_state.logo_backoffice = False
    LogoStrix()

    # Captura dados:

    if opt_data == "Unica":
        st.session_state.manager_passivos_cotizar.set_refdate(refdate, refdate)
    elif opt_data == "Mult":
        st.session_state.manager_passivos_cotizar.set_refdate(refdate, refdate)

    st.session_state.manager_passivos_cotizar.base_passivos_cotizar()

    df_passivos_cotizar = (
        st.session_state.manager_passivos_cotizar.df_passivos_cotizar.copy()
    )

    # Botao download:

    st.sidebar.divider()

    st.sidebar.download_button(
        label="Download - Passivos Cotizar",
        data=save_to_excel(df_passivos_cotizar),
        file_name="passivos_a_cotizar.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    # Dados Pagina:

    with st.container(border=False):
        col1, col2, col3 = st.columns([0.1, 2, 0.6])

        for fundo in fundos:
            df_fundo = df_passivos_cotizar[
                df_passivos_cotizar["Fundo"]
                == st.session_state.dict_aux_btg_bases_cc_e_movs[fundo]
            ].copy()
            df_fundo.drop(columns=["Fundo"], inplace=True)
            col2.subheader(f"Fundo: {fundo}")
            if len(df_fundo) > 0:
                col2.dataframe(df_fundo, use_container_width=True, hide_index=True)
            else:
                col2.write("Sem passivos a cotizar.")

if st.session_state["contatos_btg"] == True:
    st.session_state.logo_backoffice = False
    LogoStrix()
    contatos_btg()

if st.session_state.logo_backoffice:
    LogoStrix()
