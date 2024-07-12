from __init__ import *

VERSION_APP = "2.0.2"
VERSION_REFDATE = "2024-07-05"
ENVIRONMENT = os.getenv("ENVIRONMENT")
SCRIPT_NAME = os.path.basename(__file__)

if ENVIRONMENT == "DEVELOPMENT":
    print(f"{SCRIPT_NAME.upper()} - {ENVIRONMENT} - {VERSION_APP} - {VERSION_REFDATE}")

# -----------------------------------------------------------------------

import urllib
from datetime import date, datetime

import pandas as pd
from sqlalchemy import create_engine, text

# -----------------------------------------------------------------------


class SQL_Manager:

    def __init__(self):
        self.db_name = os.getenv("DB_NAME")
        self.uname = os.getenv("DB_UNAME")
        self.pword = os.getenv("DB_PWORD")
        self.host = os.getenv("DB_HOST")
        self.driver = "ODBC Driver 17 for SQL Server"
        self.port = None
        self.engine = self.create_engine()
        self.conn = self.engine.connect()
        self.conn.execution_options(isolation_level="AUTOCOMMIT")

    def create_engine(self):
        connection_string = (
            f"mssql+pyodbc://{self.uname}:{urllib.parse.quote_plus(self.pword)}"
            f"@{self.host}/{self.db_name}?driver={urllib.parse.quote(self.driver)}"
        )
        return create_engine(connection_string)

    def check_connection(self):
        try:
            self.conn.execute(text("SELECT 1"))
        except:
            self.conn = self.engine.connect()
            self.conn.execution_options(isolation_level="AUTOCOMMIT")

    def formatar_dado(self, dado):
        if isinstance(dado, str):
            return f"'{dado}'"
        elif isinstance(dado, (int, float)):
            return str(dado)
        elif isinstance(dado, (date, datetime)):
            return f"'{dado.strftime('%Y-%m-%d')}'"
        else:
            return str(dado)

    def select_dataframe(self, query: str):
        self.check_connection()
        try:
            result_df = pd.read_sql_query(query, self.conn)
            return result_df
        except Exception as e:
            return e

    def delete_records(self, table_name: str, condition: str):
        self.check_connection()
        delete_query = text(f"DELETE FROM {table_name} WHERE {condition}")
        try:
            self.conn.execute(delete_query)
            return True
        except Exception as e:
            return e

    def insert_dataframe(self, df, table_name, chunk_size=10000):
        chunks = [df[i : i + chunk_size] for i in range(0, df.shape[0], chunk_size)]
        for chunk in chunks:
            chunk.to_sql(table_name, con=self.engine, if_exists="append", index=False)

    def check_if_data_exists(self, query: str):
        self.check_connection()
        query_text = text(query)
        try:
            result = self.conn.execute(query_text)
            return result.fetchone() is not None
        except Exception as e:
            return e

    def update_table(
        self,
        table_name: str,
        column_with_data_to_update: str,
        column_with_condition: str,
    ):
        self.check_connection()
        update_query = text(
            f"UPDATE {table_name} SET {column_with_data_to_update} WHERE {column_with_condition}"
        )
        try:
            self.conn.execute(update_query)
            return True
        except Exception as e:
            return e

    def insert_manual(self, table_name: str, list_columns: list, list_values: list):
        self.check_connection()

        str_colunas = ", ".join(list_columns)
        str_dados = ", ".join([self.formatar_dado(dado) for dado in list_values])
        query_insert = text(
            f"INSERT INTO {table_name} ({str_colunas}) VALUES ({str_dados})"
        )

        try:
            self.conn.execute(query_insert)
            return True
        except Exception as e:
            return e

    def get_single_value(self, query: str):
        self.check_connection()
        try:
            result = self.conn.execute(text(query)).scalar()
            return result
        except Exception as e:
            return e
