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

import pandas as pd

import streamlit as st
from tools.db_helper import SQL_Manager

st.set_page_config(
    page_title="Strix Capital - Painel de Controle",
    page_icon="🦉",
    layout="wide",
    initial_sidebar_state="expanded",
)

manager_sql = SQL_Manager()


def get_perf_att_classe(df_perf_att):
    df_perf_att_classes = (
        df_perf_att[["REFDATE", "FUNDO", "TIPO_ATIVO", "RENT_SI"]]
        .groupby(["REFDATE", "FUNDO", "TIPO_ATIVO"])
        .sum()
        .reset_index()
    )
    df_perf_att_classes.sort_values(by="RENT_SI", ascending=False, inplace=True)
    df_perf_att_classes["RENT_SI"] = df_perf_att_classes["RENT_SI"].apply(
        lambda x: f"{x*100:,.2f}%"
    )
    return df_perf_att_classes


def get_perf_att_ativos(df_perf_att):
    df_perf_att_ativos = (
        df_perf_att[df_perf_att["REFDATE"] == df_perf_att["REFDATE"].max()][
            ["REFDATE", "FUNDO", "TIPO_ATIVO", "ATIVO", "RENT_SI"]
        ]
        .groupby(["REFDATE", "FUNDO", "TIPO_ATIVO", "ATIVO"])
        .sum()
        .reset_index()
    )
    df_perf_att_ativos["RENT_SI"] = df_perf_att_ativos["RENT_SI"].apply(
        lambda x: f"{x*100:,.2f}%"
    )
    df_perf_att_ativos.sort_values("TIPO_ATIVO", ascending=True, inplace=True)
    return df_perf_att_ativos


df_perf_att = manager_sql.select_dataframe(
    "SELECT * FROM TB_ATT_PERFORMANCE_ATVIOS WHERE FUNDO = 'Strix Yield Master' \
     AND REFDATE = (SELECT MAX(REFDATE) FROM TB_DADOS_FUNDOS WHERE FUNDO = 'STRIX YIELD MASTER')"
)


st.header("Strix Yield Master")

with st.container(border=True):
    st.subheader("Performance Att por Classe")
    # st.write(get_perf_att_classe(df_perf_att).to_html(index=False, justify='center', classes='dataframe', escape=False), unsafe_allow_html=True)
    st.dataframe(get_perf_att_classe(df_perf_att), hide_index=True, height=460)

    st.subheader("Performance Att por Ativos")
    # st.write(get_perf_att_ativos(df_perf_att).to_html(index=False, justify='center', classes='dataframe', escape=False), unsafe_allow_html=True)
    st.dataframe(
        get_perf_att_ativos(df_perf_att),
        use_container_width=False,
        height=800,
        hide_index=True,
        width=1300,
    )
