from datetime import date

import pandas as pd
from __init__ import append_paths

from tools.db_helper import SQL_Manager
from tools.py_tools import FuncoesPyTools

append_paths()

# -------------------------------------------------------------------------------------------------------
# Dicionários e listas fixas:


class FixedDictionariesListsLibrary:

    def __init__(self):

        self.dict_fundos_fic_master = {
            "STRIX D1 FIC FIRF": "Strix Yield Master",
            "STRIX YIELD FC FIRF": "Strix Yield Master"
        }

        self.lista_fundos = [
            "STRIX YIELD MASTER F",
            "STRIX YIELD FC FIRF",
            "STRIX D1 FIC FIRF",
            "STRIX FIA",
            "STRIX INFRA FICFIRF",
            "STRIX KINEA INFRA",
            "CRYSTAL FIC FIM CP"
        ]

        self.lista_tipo_ativos_observaveis = ["Debênture"]
        self.lista_tipo_ativos_titulos_publicos = ["Tit. Publicos", "Compromissada"]
        self.lista_tipo_ativos_fluxo = ["CCB", "CDB", "LF", "LFSC", "LFSN-PRE"]
        self.lista_tipo_ativos_fundos = ["Fundos BR", "Fundos Caixa"]

    def get_fundo_master(self, fundo_name):
        """
        Retorna o fundo master correspondente ao fundo fornecido.
        """
        return self.dict_fundos_fic_master.get(fundo_name, None)

# -------------------------------------------------------------------------------------------------------
# Dicionarios e listas from SQL:


class SqlDictionariesLists:

    def __init__(self, manager_sql=None, funcoes_pytools=None):

        self.manager_sql = manager_sql if manager_sql is not None else SQL_Manager()

        self.funcoes_pytools = funcoes_pytools if funcoes_pytools is not None else FuncoesPyTools(self.manager_sql)

    def get_dict_last_cotas(self, refdate: date) -> dict:

        dict_cotas = self.manager_sql.select_dataframe(
            "SELECT A.FUNDO, B.COTA FROM "
            f"(SELECT FUNDO, MAX(REFDATE) AS REFDATE FROM TB_XML_CARTEIRAS_HEADER WHERE REFDATE <= '{refdate}' GROUP BY FUNDO) A "
            "LEFT JOIN "
            "(SELECT REFDATE, FUNDO, COTA FROM TB_XML_CARTEIRAS_HEADER) B "
            "ON A.REFDATE = B.REFDATE AND A.FUNDO = B.FUNDO").set_index("FUNDO")["COTA"].to_dict()

        return dict_cotas

    def get_df_last_cotas(self, refdate: date) -> pd.DataFrame:

        df_cotas = self.manager_sql.select_dataframe(
            "SELECT A.FUNDO, B.COTA FROM "
            f"(SELECT FUNDO, MAX(REFDATE) AS REFDATE FROM TB_XML_CARTEIRAS_HEADER WHERE REFDATE <= '{refdate}' GROUP BY FUNDO) A "
            "LEFT JOIN "
            "(SELECT REFDATE, FUNDO, COTA FROM TB_XML_CARTEIRAS_HEADER) B "
            "ON A.REFDATE = B.REFDATE AND A.FUNDO = B.FUNDO")

        return df_cotas
