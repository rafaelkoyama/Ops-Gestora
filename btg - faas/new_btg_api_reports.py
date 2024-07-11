from __init__ import *

VERSION_APP = "1.2.0"
VERSION_REFDATE = "2024-07-10"
ENVIRONMENT = os.getenv("ENVIRONMENT")
SCRIPT_NAME = os.path.basename(__file__)

if ENVIRONMENT == "DEVELOPMENT":
    print(f"{SCRIPT_NAME.upper()} - {ENVIRONMENT} - {VERSION_APP} - {VERSION_REFDATE}")

append_paths()

# -----------------------------------------------------------------------

from datetime import date

import numpy as np
import pandas as pd
from btg_api_connect import BTGDataManager
from db_helper import SQL_Manager
from my_logger import Logger
from py_tools import FuncoesPyTools

# -----------------------------------------------------------------------


pd.set_option("future.no_silent_downcasting", True)


class BTGReports:

    def __init__(self, sql_manager=None, funcoes_pytools=None, logger=None):

        if sql_manager is None:
            self.sql_manager = SQL_Manager()
        else:
            self.sql_manager = sql_manager

        if funcoes_pytools is None:
            self.funcoes_pytools = FuncoesPyTools(self.sql_manager)
        else:
            self.funcoes_pytools = funcoes_pytools

        if logger is None:
            self.logger = Logger(manager_sql=self.manager_sql)
        else:
            self.logger = logger

        self.logger.info(
            log_message=f"BTGReports - {VERSION_APP} - {ENVIRONMENT} - Instanciado",
            script_original=SCRIPT_NAME,
        )

        self.list_funds = [
            "CRYSTAL FIC FIM CP",
            "STRIX D1 FIC FIRF",
            "STRIX YIELD FC FIRF",
            "STRIX YIELD MASTER F",
            "STRIX FIA",
            "STRIX INFRA FICFIRF",
        ]

        self.dict_fundos_cod_btg = {
            "CRYSTAL FIC FIM CP": "FIC DE FIM CP CRYSTAL IE",
            "STRIX D1 FIC FIRF": "STRIX D1 FIC FIRF CP",
            "STRIX YIELD FC FIRF": "STRIX YIELD FIC FIRF CP",
            "STRIX YIELD MASTER F": "STRIX YIELD MASTER FIRF CP",
            "STRIX FIA": "STRIX FIA",
            "STRIX INFRA FICFIRF": "STRIX INFRA FIC FDO INC INV INFR RF",
        }

        self.dict_fundos_cnpj = {
            "CRYSTAL FIC FIM CP": "12630565000131",
            "STRIX D1 FIC FIRF": "52797894000196",
            "STRIX YIELD FC FIRF": "52792894000101",
            "STRIX YIELD MASTER F": "53076975000160",
            "STRIX FIA": "52797717000100",
            "STRIX INFRA FICFIRF": "54995819000165",
        }

        self.dict_suporte_download = {
            2: "pdf",
            3: "xml",
            10: "xlsx",
            "STRIX YIELD MASTER F": f"C:\\Users\\{str_user}\\Strix Capital\\Backoffice - General\\Carteiras\\Strix Yield Master",
            "STRIX YIELD FC FIRF": f"C:\\Users\\{str_user}\\Strix Capital\\Backoffice - General\\Carteiras\\Strix Yield FIC",
            "STRIX D1 FIC FIRF": f"C:\\Users\\{str_user}\\Strix Capital\\Backoffice - General\\Carteiras\\Strix D1 FIC",
            "STRIX FIA": f"C:\\Users\\{str_user}\\Strix Capital\\Backoffice - General\\Carteiras\\Strix FIA",
            "CRYSTAL FIC FIM CP": f"C:\\Users\\{str_user}\\Strix Capital\\Backoffice - General\\Carteiras\\Crystal",
            "STRIX INFRA FICFIRF": f"C:\\Users\\{str_user}\\Strix Capital\\Backoffice - General\\Carteiras\\Strix Infra",
        }

        self.dict_funds_index = {
            "CRYSTAL FIC FIM CP": "CDIE",
            "STRIX D1 FIC FIRF": "CDIE",
            "STRIX YIELD FC FIRF": "CDIE",
            "STRIX YIELD MASTER F": "CDIE",
            "STRIX FIA": "IMABAJUST",
            "STRIX INFRA FICFIRF": "IMA-B",
        }

        self.tipos_carteiras_btg = [2, 3, 10]

    def connect(self, user_id=None, user_pass=None):

        if ENVIRONMENT == "DEVELOPMENT":
            self.btg_manager = BTGDataManager(
                btg_reports=self, logger=self.logger, manager_sql=self.sql_manager
            )
        else:
            self.btg_manager = BTGDataManager(
                client_id=user_id,
                client_secret=user_pass,
                btg_reports=self,
                logger=self.logger,
                manager_sql=self.sql_manager,
            )

    def funds_nav_performance(self, refdate, dmenos: date = None, fund_name=None):

        def parametros_api(refdate, dmenos, fund_name, id_index):
            p_params = {
                "startDate": dmenos.strftime("%Y-%m-%d"),
                "endDate": refdate.strftime("%Y-%m-%d"),
                "indexers": [id_index],
                "fundName": fund_name,
            }
            return p_params

        def flatten_data(data):
            flat_data = []
            for item in data["result"]:
                fund_name = item["fundName"]
                for entry in item["data"]:
                    flat_entry = {"fundName": fund_name}
                    flat_entry.update(entry)
                    # Extraindo dados de quotaProfitabilityDifference
                    if "quotaProfitabilityDifference" in entry:
                        for difference_key, difference_value in entry[
                            "quotaProfitabilityDifference"
                        ].items():
                            for inner_key, inner_value in difference_value.items():
                                if isinstance(inner_value, dict):
                                    for k, v in inner_value.items():
                                        # flat_entry[f"{difference_key}_{inner_key}_{k}"] = v
                                        flat_entry[f"{inner_key}_{k}"] = v
                        del flat_entry["quotaProfitabilityDifference"]
                    if "nominalQuoteList" in entry:
                        for quote in entry["nominalQuoteList"]:
                            quote_type = quote.get(
                                "type", "UnknownType"
                            )  # Usar 'UnknownType' se 'type' não estiver disponível
                            for key, value in quote.items():
                                if (
                                    key != "type"
                                ):  # Não duplicar a informação de 'type' como coluna
                                    flat_entry[f"{quote_type}_{key}"] = value
                        del flat_entry[
                            "nominalQuoteList"
                        ]  # Remover a chave 'nominalQuoteList' para evitar redundância
                    flat_data.append(flat_entry)
            df = pd.DataFrame(flat_data)
            return df

        def work_df(df, id_index, refdate):
            df["REFDATE"] = pd.to_datetime(df["referenceDate"])
            df["INDEXADOR_FUNDO"] = id_index
            df = df.rename(
                columns={
                    "fundName": "FUNDO",
                    "account": "CONTA_FUNDO",
                    "cnpj": "CNPJ_FUNDO",
                    "referenceDate": "DATA_REFERENCIA",
                    "liquidQuote": "COTA_LIQUIDA",
                    "rawQuote": "COTA_BRUTA",
                    "assetValue": "PATRIMONIO_LIQUIDO",
                    "numberOfQuotes": "QTD_COTAS",
                    "acquisitions": "APLICACOES",
                    "redemptions": "RESGATES",
                    "VariacaoIndexador_Accumulated": "VAR_INDEXADOR_ACUMULADO",
                    "VariacaoIndexador_Day": "VAR_INDEXADOR_DIA",
                    "VariacaoIndexador_Month": "VAR_INDEXADOR_MES",
                    "VariacaoIndexador_Year": "VAR_INDEXADOR_ANO",
                    "VariacaoIndexador_Twelve": "VAR_INDEXADOR_12M",
                    "VariacaoIndexador_TwentyFour": "VAR_INDEXADOR_24M",
                    "VariacaoIndexador_ThirtySix": "VAR_INDEXADOR_36M",
                    "NominalVsIndexador_Accumulated": "COTA_X_INDEXADOR_ACUMULADO",
                    "NominalVsIndexador_Day": "COTA_X_INDEXADOR_DIA",
                    "NominalVsIndexador_Month": "COTA_X_INDEXADOR_MES",
                    "NominalVsIndexador_Year": "COTA_X_INDEXADOR_ANO",
                    "NominalVsIndexador_Twelve": "COTA_X_INDEXADOR_12M",
                    "NominalVsIndexador_TwentyFour": "COTA_X_INDEXADOR_24M",
                    "NominalVsIndexador_ThirtySix": "COTA_X_INDEXADOR_36M",
                    "Nominal_day": "VAR_COTA_DIA",
                    "Nominal_month": "VAR_COTA_MES",
                    "Nominal_year": "VAR_COTA_ANO",
                    "Nominal_twelveMonths": "VAR_COTA_12M",
                    "Nominal_twentyFourMonths": "VAR_COTA_24M",
                    "Nominal_thirtySixMonths": "VAR_COTA_36M",
                }
            )
            df = df[
                [
                    "REFDATE",
                    "FUNDO",
                    "INDEXADOR_FUNDO",
                    "CONTA_FUNDO",
                    "CNPJ_FUNDO",
                    "DATA_REFERENCIA",
                    "COTA_LIQUIDA",
                    "COTA_BRUTA",
                    "PATRIMONIO_LIQUIDO",
                    "QTD_COTAS",
                    "APLICACOES",
                    "RESGATES",
                    "VAR_INDEXADOR_ACUMULADO",
                    "VAR_INDEXADOR_DIA",
                    "VAR_INDEXADOR_MES",
                    "VAR_INDEXADOR_ANO",
                    "VAR_INDEXADOR_12M",
                    "VAR_INDEXADOR_24M",
                    "VAR_INDEXADOR_36M",
                    "COTA_X_INDEXADOR_ACUMULADO",
                    "COTA_X_INDEXADOR_DIA",
                    "COTA_X_INDEXADOR_MES",
                    "COTA_X_INDEXADOR_ANO",
                    "COTA_X_INDEXADOR_12M",
                    "COTA_X_INDEXADOR_24M",
                    "COTA_X_INDEXADOR_36M",
                    "VAR_COTA_DIA",
                    "VAR_COTA_MES",
                    "VAR_COTA_ANO",
                    "VAR_COTA_12M",
                    "VAR_COTA_24M",
                    "VAR_COTA_36M",
                ]
            ]
            df[
                [
                    "COTA_LIQUIDA",
                    "COTA_BRUTA",
                    "PATRIMONIO_LIQUIDO",
                    "QTD_COTAS",
                    "APLICACOES",
                    "RESGATES",
                    "VAR_INDEXADOR_ACUMULADO",
                    "VAR_INDEXADOR_DIA",
                    "VAR_INDEXADOR_MES",
                    "VAR_INDEXADOR_ANO",
                    "VAR_INDEXADOR_12M",
                    "VAR_INDEXADOR_24M",
                    "VAR_INDEXADOR_36M",
                    "COTA_X_INDEXADOR_ACUMULADO",
                    "COTA_X_INDEXADOR_DIA",
                    "COTA_X_INDEXADOR_MES",
                    "COTA_X_INDEXADOR_ANO",
                    "COTA_X_INDEXADOR_12M",
                    "COTA_X_INDEXADOR_24M",
                    "COTA_X_INDEXADOR_36M",
                    "VAR_COTA_DIA",
                    "VAR_COTA_MES",
                    "VAR_COTA_ANO",
                    "VAR_COTA_12M",
                    "VAR_COTA_24M",
                    "VAR_COTA_36M",
                ]
            ] = df[
                [
                    "COTA_LIQUIDA",
                    "COTA_BRUTA",
                    "PATRIMONIO_LIQUIDO",
                    "QTD_COTAS",
                    "APLICACOES",
                    "RESGATES",
                    "VAR_INDEXADOR_ACUMULADO",
                    "VAR_INDEXADOR_DIA",
                    "VAR_INDEXADOR_MES",
                    "VAR_INDEXADOR_ANO",
                    "VAR_INDEXADOR_12M",
                    "VAR_INDEXADOR_24M",
                    "VAR_INDEXADOR_36M",
                    "COTA_X_INDEXADOR_ACUMULADO",
                    "COTA_X_INDEXADOR_DIA",
                    "COTA_X_INDEXADOR_MES",
                    "COTA_X_INDEXADOR_ANO",
                    "COTA_X_INDEXADOR_12M",
                    "COTA_X_INDEXADOR_24M",
                    "COTA_X_INDEXADOR_36M",
                    "VAR_COTA_DIA",
                    "VAR_COTA_MES",
                    "VAR_COTA_ANO",
                    "VAR_COTA_12M",
                    "VAR_COTA_24M",
                    "VAR_COTA_36M",
                ]
            ].astype(
                float
            )
            df = df[df["REFDATE"] == pd.Timestamp(refdate)]
            return df

        def processo_navs_performance(refdate, dmenos, fundo):

            try:
                data = self.btg_manager.get_data(
                    parametros_api(
                        refdate, dmenos, fundo, self.dict_funds_index[fundo]
                    ),
                    p_point="reports/NAVPerformance",
                )
                df_original = flatten_data(data)
                df_trabalhada = work_df(
                    df_original, self.dict_funds_index[fundo], refdate
                )
                if len(df_trabalhada) == 0:
                    return "No records."
                self.sql_manager.delete_records(
                    "TB_BASE_BTG_PERFORMANCE_COTA",
                    f"REFDATE >= '{dmenos}' AND REFDATE <= '{refdate}' AND FUNDO = '{fundo}'",
                )
                self.sql_manager.insert_dataframe(
                    df_trabalhada, "TB_BASE_BTG_PERFORMANCE_COTA"
                )
                return "ok"
            except Exception as e:
                return e

        def run(refdate, dmenos, fundo):

            results = {}

            if dmenos is None:
                dmenos = refdate

            if fundo is None:
                for fundo in self.list_funds:
                    results[fundo] = processo_navs_performance(refdate, dmenos, fundo)
            else:
                results[fundo] = processo_navs_performance(refdate, dmenos, fundo)

            return results

        return run(refdate, dmenos, fund_name)

    def funds_performance_cotistas(self, refdate, fund_name=None):

        def parametros_api(refdate, fund_name):
            p_params = {
                "queryDate": refdate.strftime("%Y-%m-%d"),
                "fundName": fund_name,
            }
            return p_params

        def captura_dados_performance_cotistas(refdate, fundo):
            p_point = "reports/RTA/PerformanceFee"
            data = self.btg_manager.get_data(parametros_api(refdate, fundo), p_point)
            return data

        def tratamento_dados_performance_cotistas(refdate, data, fundo):
            df = pd.DataFrame(data["result"])
            df["REFDATE"] = refdate
            df["dateBaseChange"] = df.loc[:, "dateBaseChange"].replace(
                "0001-01-01T00:00:00", np.nan
            )
            for column in ["dateAquisition", "dateBase", "dateBaseChange"]:
                df[column] = pd.to_datetime(df[column])
            df["dateBaseChange"] = df.loc[:, "dateBaseChange"].replace(
                "1900-01-01", np.nan
            )
            df["indexChange"] = df.loc[:, "indexChange"].replace("", np.nan)
            df["FUNDO"] = fundo
            df = df.rename(
                columns={
                    "accountNumber": "CONTA_COTISTA",
                    "name": "COTISTA",
                    "aquisitionNumber": "CERTIFICADO_COTISTA",
                    "dateAquisition": "DATA_AQUISICAO",
                    "dateBase": "DATA_BASE_PERFORMANCE",
                    "dateBaseChange": "DATA_BASE_PERF_TROCA",
                    "baseQuota": "COTA_BASE_PERFORMANCE",
                    "baseQuotaChange": "COTA_BASE_PERF_TROCA",
                    "todayQuota": "COTA_REFDATE",
                    "eventFactor": "EVENTFACTOR",
                    "index": "INDEXADOR",
                    "indexChange": "INDEXCHANGE",
                    "indexAccumulated": "INDEXADOR_ACUMULADO",
                    "indexAccumulatedChange": "INDEXADOR_ACUM_CHANGE",
                    "quantity": "QUANTIDADE_COTAS",
                    "gain": "VALOR_MAIOR_INDEXADOR",
                    "gainChange": "VALOR_MAIOR_INDEXADOR_CHANGE",
                    "prize": "VALOR_PERFORMANCE",
                }
            )
            df = df[
                [
                    "REFDATE",
                    "FUNDO",
                    "INDEXADOR",
                    "COTISTA",
                    "CONTA_COTISTA",
                    "CERTIFICADO_COTISTA",
                    "DATA_AQUISICAO",
                    "DATA_BASE_PERFORMANCE",
                    "COTA_BASE_PERFORMANCE",
                    "COTA_REFDATE",
                    "QUANTIDADE_COTAS",
                    "VALOR_MAIOR_INDEXADOR",
                    "VALOR_PERFORMANCE",
                    "INDEXADOR_ACUMULADO",
                    "INDEXADOR_ACUM_CHANGE",
                    "DATA_BASE_PERF_TROCA",
                    "COTA_BASE_PERF_TROCA",
                    "EVENTFACTOR",
                    "VALOR_MAIOR_INDEXADOR_CHANGE",
                    "INDEXCHANGE",
                ]
            ]
            return df

        def insert_performance_cotistas(refdate, fundo, df):
            self.sql_manager.delete_records(
                "TB_BASE_BTG_PERFORMANCE_COTISTAS",
                f"FUNDO = '{fundo}' AND REFDATE = '{refdate.strftime('%Y-%m-%d')}'",
            )
            self.sql_manager.insert_dataframe(df, "TB_BASE_BTG_PERFORMANCE_COTISTAS")

        def run_performance_cotistas(refdate, fundo):

            data = captura_dados_performance_cotistas(refdate, fundo)

            try:
                if data is None:
                    return "No records."
                elif data["result"] == "No records":
                    return "No records."
                else:
                    df = tratamento_dados_performance_cotistas(refdate, data, fundo)
                    insert_performance_cotistas(refdate, fundo, df)
                    return "ok"
            except Exception as e:
                return f"ERROR -> {e}"

        def run(refdate, fundo):

            results = {}

            if fundo is None:
                for fundo in self.list_funds:
                    results[fundo] = run_performance_cotistas(refdate, fundo)
            else:
                results[fundo] = run_performance_cotistas(refdate, fundo)

            return results

        return run(refdate, fund_name)

    def funds_managementfee_cotistas(self, refdate, fund_name=None):

        def parametros_api(refdate, fund_name):
            p_params = {
                "startDate": refdate.strftime("%Y-%m-%d"),
                "endDate": refdate.strftime("%Y-%m-%d"),
                "fundName": fund_name,
            }
            return p_params

        def captura_dados_api(refdate, fundo):
            p_point = "reports/RTA/ManagementFee"
            try:
                data = self.btg_manager.get_data(
                    parametros_api(refdate, fundo), p_point
                )
                return data
            except Exception as e:
                # self.logger.error(f"Erro ao capturar dados de taxa adm. cotistas: {e}")
                # self.logger.error(f"Captura dados, taxa adm cotistas {fundo}. Verificar log.", True)
                return None

        def tratamento_dados_api(refdate, fundo, data):
            if data is None:
                df = pd.DataFrame({})
                # self.logger.error(f"Sem dados para o fundo {fundo}. Conferir log para mais info.", True)
                return df
            elif data["result"] == "No records":
                df = pd.DataFrame({})
                # self.logger.info(f"'No records' para o fundo {fundo}", True)
                return df
            else:
                try:
                    df = pd.DataFrame(data["result"])
                    df["REFDATE"] = refdate
                    df["FUNDO"] = fundo
                    df = df.rename(
                        columns={
                            "account": "CONTA_COTISTA",
                            "quotaholder": "COTISTA",
                            "contact": "OFFICER",
                            "fee": "ADM_COTISTA",
                        }
                    )
                    df = df[
                        [
                            "REFDATE",
                            "FUNDO",
                            "CONTA_COTISTA",
                            "COTISTA",
                            "ADM_COTISTA",
                            "OFFICER",
                        ]
                    ]
                    return df
                except Exception as e:
                    # self.logger.error(f"Erro ao tratar dados de taxa adm. cotistas: {e}")
                    # self.logger.error(f"Tratamento taxa adm. cotistas {fundo}. Verificar log.", True)
                    return pd.DataFrame({})

        def insert_dados_api(refdate, fundo, df):
            try:
                self.sql_manager.delete_records(
                    "TB_BASE_BTG_TX_ADM_COTISTAS",
                    f"FUNDO = '{fundo}' AND REFDATE = '{refdate.strftime('%Y-%m-%d')}'",
                )
                # self.logger.info(f"Registros deletados para o fundo {fundo}")
                self.sql_manager.insert_dataframe(df, "TB_BASE_BTG_TX_ADM_COTISTAS")
                # self.logger.info(f"Registros inseridos para o fundo {fundo}")
            except Exception as e:
                print(e)
                # self.logger.error(f"Erro ao inserir dados de taxa adm. cotistas: {e}")
                # self.logger.error(f"Insert taxa adm. cotistas {fundo}. Verificar log.", True)

        def run_processo_api(refdate, fundo):
            try:
                data = captura_dados_api(refdate, fundo)
                df = tratamento_dados_api(refdate, fundo, data)
                if len(df) > 0:
                    insert_dados_api(refdate, fundo, df)
                    return "ok"
                else:
                    return "No records."
            except Exception as e:
                return f"ERROR -> {e}"

        def run(refdate, fundo):

            results = {}

            if fundo is None:
                for fundo in self.list_funds:
                    results[fundo] = run_processo_api(refdate, fundo)
            else:
                results[fundo] = run_processo_api(refdate, fundo)

            return results

        return run(refdate, fund_name)

    def download_carteiras(self, refdate, fundo, tipo_arq):

        def verifica_arquivo_existe(file_path: str) -> bool:
            return os.path.exists(file_path)

        def join_path(refdate, fundo, tipo):
            if tipo == 10:
                return os.path.join(
                    self.dict_suporte_download[fundo],
                    self.dict_suporte_download[tipo],
                    f"ResumoCarteira_{fundo.replace(' ', '_')}_{refdate.strftime('%Y%m%d')}.{self.dict_suporte_download[tipo]}",
                )
            else:
                return os.path.join(
                    self.dict_suporte_download[fundo],
                    self.dict_suporte_download[tipo],
                    f"{fundo.replace(' ', '_')}_{refdate.strftime('%Y%m%d')}.{self.dict_suporte_download[tipo]}",
                )

        def parametros_api(refdate, tipo, fundo):
            p_params = {
                "startDate": refdate.strftime("%Y-%m-%d"),
                "endDate": refdate.strftime("%Y-%m-%d"),
                "typeReport": tipo,
                "fundName": fundo,
            }
            return p_params

        def run_download_carteiras(refdate, fundo, tipo):

            if verifica_arquivo_existe(join_path(refdate, fundo, tipo)):
                return f"{self.dict_suporte_download[tipo]} - Já baixado anteriormente."
            else:
                data = self.btg_manager.get_data(
                    parametros_api(refdate, tipo, fundo),
                    "reports/Portfolio",
                    fundo,
                    refdate,
                )
                if data == "ok":
                    return f"{self.dict_suporte_download[tipo]} - Baixado com sucesso."
                else:
                    return f"{self.dict_suporte_download[tipo]} não encontrado."

        return run_download_carteiras(refdate, fundo, tipo_arq)

    def funds_status_carteiras(self, refdate):

        def parametros_api(refdate):
            p_params = {"dataInterface": refdate.strftime("%Y-%m-%d")}
            return p_params

        def captura_dados_api(refdate):
            p_point = "reports/Portfolio/PortfolioQuotaListToDate"
            data = None
            try:
                data = self.btg_manager.get_data(parametros_api(refdate), p_point)
                return "ok", data
            except Exception as e:
                return e, data

        def tratamento_dados_api(refdate, data):

            try:
                df = pd.DataFrame(data)
                df["REFDATE"] = refdate
                for coluna in [
                    "approvedDate",
                    "quotaDate",
                    "calculationDate",
                    "galgoDate",
                    "lastQuotaDate",
                ]:
                    df[coluna] = pd.to_datetime(df[coluna])
                df = df[
                    [
                        "REFDATE",
                        "id",
                        "fundName",
                        "quotaDate",
                        "status",
                        "cnpj",
                        "calculationDate",
                        "approvedDate",
                        "lastQuotaDate",
                        "galgoDate",
                        "dayProfit",
                        "quotaValue",
                        "account",
                        "defaultTime",
                        "RequestId",
                        "XLSFileId",
                        "PDFFileId",
                    ]
                ]
                df = df.rename(
                    columns={
                        "id": "ID_BTG",
                        "fundName": "FUNDO",
                        "quotaDate": "DATA_COTA",
                        "status": "STATUS_CARTEIRA",
                        "cnpj": "CNPJ_FUNDO",
                        "calculationDate": "DATA_CALCULO",
                        "approvedDate": "DATA_APROVACAO",
                        "lastQuotaDate": "DATA_ULTIMA_COTA",
                        "galgoDate": "DATA_GALGO",
                        "dayProfit": "RENTABILIDADE_DIA",
                        "quotaValue": "VALOR_COTA",
                        "account": "CONTA_FUNDO",
                        "defaultTime": "DAFAULT_HORA",
                        "RequestId": "ID_REQUEST",
                        "XLSFileId": "XLS_FIELD",
                        "PDFFileId": "PDF_FIELD",
                    }
                )
                return "ok", df
            except Exception as e:
                # self.logger.error(f"Tratamento dados status carteiras: {e}")
                # self.logger.error(f"Tratamento dados status carteiras. Verificar log.", True)
                return e, pd.DataFrame({})

        def insert_dados_api(refdate, df):
            try:
                self.sql_manager.delete_records(
                    "TB_BASE_BTG_STATUS_CARTEIRAS",
                    f"REFDATE = '{refdate.strftime('%Y-%m-%d')}'",
                )
                # self.logger.info(f"TB_BASE_BTG_STATUS_CARTEIRAS delete REFDATE = {refdate.strftime('%Y-%m-%d')}")
                self.sql_manager.insert_dataframe(df, "TB_BASE_BTG_STATUS_CARTEIRAS")
                # self.logger.info(f"TB_BASE_BTG_STATUS_CARTEIRAS insert REFDATE = {refdate.strftime('%Y-%m-%d')}")
                return "ok"
            except Exception as e:
                # self.logger.error(f"Insert dados status carteiras: {e}")
                # self.logger.error(f"Insert dados status carteiras. Verificar log.", True)
                return e

        def run_processo_api(refdate):
            result = {}
            check_data, data = captura_dados_api(refdate)
            if check_data == "ok":
                result["data"] = check_data
                check_df, df = tratamento_dados_api(refdate, data)
                if check_df == "ok":
                    result["df"] = check_df
                    if len(df) > 0:
                        check_insert = insert_dados_api(refdate, df)
                        result["insert"] = check_insert
                    else:
                        result["insert"] = "Sem registros."
                else:
                    result["df"] = check_df
                    result["insert"] = "Erro do tratamento dados."
            else:
                result["data"] = check_data
                result["df"] = "Erro do get_data."
                result["insert"] = "Erro do get_data."

            return result

        return run_processo_api(refdate)

    def funds_extrato_cc(self, refdate, fund_name=None):

        def parametros_api(refdate, fund_name):
            p_params = {
                "startDate": refdate.strftime("%Y-%m-%d"),
                "endDate": refdate.strftime("%Y-%m-%d"),
                "CPFCNPJ": self.dict_fundos_cnpj[fund_name],
            }
            return p_params

        def captura_dados_api(refdate, fundo):
            p_point = "reports/Cash/FundAccountStatement"
            try:
                data = self.btg_manager.get_data(
                    parametros_api(refdate, fundo), p_point
                )
                return data
            except Exception as e:
                # self.logger.error(f"Erro ao capturar dados de extrato cc {fundo}: {e}")
                # self.logger.error(f"Captura dados, extrato cc {fundo}. Verificar log.", True)
                return None

        def tratamento_dados_api(refdate, fundo, data):
            if data is None:
                df = pd.DataFrame({})
                # self.logger.error(f"Extrato cc do fundo {fundo}. Conferir log para mais info.", True)
                return df
            elif data["result"] == "No records":
                df = pd.DataFrame({})
                # self.logger.info(f"'No records' extrato cc para o fundo {fundo}", True)
                return df
            else:
                try:
                    df = pd.DataFrame(data["result"])
                    df["FUNDO"] = fundo
                    df = df.iloc[::-1].reset_index(drop=True).reset_index()
                    df = df.rename(
                        columns={
                            "index": "INDEX_BTG_ORDEM",
                            "history": "HISTORICO",
                            "observation": "OBS",
                            "credit": "CREDITO",
                            "debt": "DEBITO",
                            "balance": "BALANCO",
                            "assetDocument": "CNPJ_FUNDO",
                            "operationDate": "REFDATE",
                        }
                    )
                    df = df[
                        [
                            "INDEX_BTG_ORDEM",
                            "REFDATE",
                            "FUNDO",
                            "HISTORICO",
                            "OBS",
                            "CREDITO",
                            "DEBITO",
                            "BALANCO",
                            "CNPJ_FUNDO",
                        ]
                    ]
                    for coluna in ["CREDITO", "DEBITO"]:
                        df[coluna] = df.loc[:, coluna].replace("", 0)
                        df[coluna] = df[coluna].astype(float)
                    return df
                except Exception as e:
                    # self.logger.error(f"Tratamento dados extrato cc: {e}")
                    # self.logger.error(f"Tratamento dados extrato cc {fundo}. Verificar log.", True)
                    return pd.DataFrame({})

        def insert_dados_api(refdate, fundo, df):
            try:
                self.sql_manager.delete_records(
                    "TB_BASE_BTG_EXTRATO_CONTA_CORRENTE",
                    f"FUNDO = '{fundo}' AND REFDATE = '{refdate.strftime('%Y-%m-%d')}'",
                )
                # self.logger.info(f"Registros deletados para o fundo {fundo}")
                self.sql_manager.insert_dataframe(
                    df, "TB_BASE_BTG_EXTRATO_CONTA_CORRENTE"
                )
                # self.logger.info(f"Registros inseridos para o fundo {fundo}")
            except Exception as e:
                print(e)
                # self.logger.error(f"Insert dados extrato cc: {e}")
                # self.logger.error(f"Insert dados cc {fundo}. Verificar log.", True)

        def run_processo_api(refdate, fundo):
            try:
                data = captura_dados_api(refdate, fundo)
                df = tratamento_dados_api(refdate, fundo, data)
            except Exception as e:
                # self.logger.error(f"Erro no processo de extrato cc: {e}")
                return e

            if len(df) > 0:
                insert_dados_api(refdate, fundo, df)
                return "ok"
            else:
                # self.logger.info(f"Extrato cc {fundo} sem dados.")
                return "No records."

        def run(refdate, fund_name):

            results = {}
            if fund_name is not None:
                check_run = run_processo_api(refdate, fund_name)
                results[fund_name] = check_run
            else:
                for fundo in self.list_funds:
                    check_run = run_processo_api(refdate, fundo)
                    results[fundo] = check_run

            return results

        return run(refdate, fund_name)

    def funds_movimentacao_cotistas(self, refdate, fund_name=None, tipo_mov="OPERACAO"):

        def parametros_api(refdate, fund_name, tipo_mov):
            p_params = {
                "startDate": refdate.strftime("%Y-%m-%d"),
                "endDate": refdate.strftime("%Y-%m-%d"),
                "dateType": tipo_mov,
                "fundName": fund_name,
            }
            return p_params

        def captura_dados_api(refdate, fundo, tipo_mov):
            p_point = "reports/RTA/FundFlow"
            try:
                data = self.btg_manager.get_data(
                    parametros_api(refdate, fundo, tipo_mov), p_point
                )
                return data
            except Exception as e:
                # self.logger.error(f"Erro ao capturar dados de mov cotistas cotistas: {e}")
                # self.logger.error(f"Captura dados, mov cotistas {fundo}. Verificar log.", True)
                return None

        def tratamento_dados_api(fundo, data):
            if data is None:
                df = pd.DataFrame({})
                # self.logger.error(f"Sem dados para o fundo {fundo}. Conferir log para mais info.", True)
                return df
            elif data["result"] == "No records":
                df = pd.DataFrame({})
                # self.logger.info(f"'No records' para o fundo {fundo}")
                return df
            else:
                try:
                    df = pd.DataFrame(data["result"])

                    df = df.rename(
                        columns={
                            "customerName": "COTISTA",
                            "accountNumber": "ID_COTISTA",
                            "officer": "OFFICER",
                            "activeName": "FUNDO",
                            "aplicationDate": "DATA_OPERACAO",
                            "quotaSharing": "DATA_COTIZACAO",
                            "impactDate": "DATA_IMPACTO",
                            "type": "TIPO_OPERACAO",
                            "descTypeOperation": "DESC_TIPO_OPERACAO",
                            "valueTotal": "VALOR",
                            "quotas": "QTD_COTAS",
                            "descStatusOperation": "STATUS_OPERACAO",
                            "request": "PLATAFORMA",
                            "numControlMainAcess": "ID_CONTROLE",
                            "liquid": "TIPO_LIQUIDACAO",
                            "bancid": "BANCO_COTISTA",
                            "agencId": "AGENCIA_COTISTA",
                            "account": "CONTA_COTISTA",
                            "boletaIdFundOrder": "ID_BTG",
                        }
                    )

                    df = df[
                        [
                            "DATA_OPERACAO",
                            "DATA_COTIZACAO",
                            "DATA_IMPACTO",
                            "FUNDO",
                            "COTISTA",
                            "ID_COTISTA",
                            "TIPO_OPERACAO",
                            "VALOR",
                            "QTD_COTAS",
                            "DESC_TIPO_OPERACAO",
                            "TIPO_LIQUIDACAO",
                            "STATUS_OPERACAO",
                            "PLATAFORMA",
                            "OFFICER",
                            "ID_CONTROLE",
                            "ID_BTG",
                            "BANCO_COTISTA",
                            "AGENCIA_COTISTA",
                            "CONTA_COTISTA",
                        ]
                    ]

                    return df
                except Exception as e:
                    # self.logger.error(f"Erro ao tratar dados de movimentação cotistas: {e}")
                    # self.logger.error(f"Tratamento movimentação cotistas {fundo}. Verificar log.", True)
                    return pd.DataFrame({})

        def insert_dados_api(refdate, fundo, df):
            try:
                self.sql_manager.delete_records(
                    "TB_BASE_BTG_MOVIMENTACAO_PASSIVO",
                    f"FUNDO = '{fundo}' AND DATA_OPERACAO = '{refdate.strftime('%Y-%m-%d')}'",
                )
                # self.logger.info(f"Registros deletados para o fundo {fundo}")
                self.sql_manager.insert_dataframe(
                    df, "TB_BASE_BTG_MOVIMENTACAO_PASSIVO"
                )
                # self.logger.info(f"Registros inseridos para o fundo {fundo}")
                return "ok"
            except Exception as e:
                # self.logger.error(f"Erro ao inserir dados de taxa adm. cotistas: {e}")
                return e

        def run_processo_api(refdate, fundo, tipo_mov):
            try:
                data = captura_dados_api(refdate, fundo, tipo_mov)
                df = tratamento_dados_api(fundo, data)
            except Exception as e:
                # self.logger.error(f"Erro no processo de movimentação cotistas: {e}")
                return e

            if len(df) > 0:
                check_insert = insert_dados_api(refdate, fundo, df)
                # self.logger.info(f"Base movimentação cotistas {fundo} ok.")
                return check_insert
            else:
                # self.logger.info(f"Base movimentação cotistas {fundo} sem dados.")
                return "No records."

        def run(refdate, fund_name, tipo_mov):

            results = {}

            if fund_name is not None:
                check_run = run_processo_api(refdate, fund_name, tipo_mov)
                results[fund_name] = check_run
            else:
                for fundo in self.list_funds:
                    check_run = run_processo_api(refdate, fundo, tipo_mov)
                    results[fundo] = check_run

            return results

        return run(refdate, fund_name, tipo_mov)

    def pricing_matrix_types(self):

        def captura_dados_api():
            p_point = "reports/Pricing/Matrix/Types"
            try:
                data = self.btg_manager.get_data(p_params=None, p_point=p_point)
                return data
            except Exception as e:
                # self.logger.error(f"Capturar dados status carteiras: {e}")
                # self.logger.error(f"Captura dados, status carteiras. Verificar log.", True)
                return None

        self.pricing_matrix_types = captura_dados_api()

    def pricing_matrix_indexes(self):

        def captura_dados_api():
            p_point = "reports/Pricing/Matrix/Indexes"
            try:
                data = self.btg_manager.get_data(p_params=None, p_point=p_point)
                return data
            except Exception as e:
                # self.logger.error(f"Capturar dados status carteiras: {e}")
                # self.logger.error(f"Captura dados, status carteiras. Verificar log.", True)
                return None

        self.pricing_matrix_indexes = captura_dados_api()

    def pricing_matrix_issuers(self):

        def captura_dados_api():
            p_point = "reports/Pricing/Matrix/Issuers"
            try:
                data = self.btg_manager.get_data(p_params=None, p_point=p_point)
                return data
            except Exception as e:
                # self.logger.error(f"Capturar dados status carteiras: {e}")
                # self.logger.error(f"Captura dados, status carteiras. Verificar log.", True)
                return None

        self.pricing_matrix_issuers = captura_dados_api()

    def pricing_matrix(self, refdate):

        def parametros_api():
            p_params = {
                "types": self.pricing_matrix_types,
                "indexes": self.pricing_matrix_indexes,
                "issuers": self.pricing_matrix_issuers,
            }
            return p_params

        def captura_dados_api():

            self.pricing_matrix_types()
            self.pricing_matrix_indexes()
            self.pricing_matrix_issuers()

            sleep(5)

            p_point = "reports/Pricing/Matrix"
            try:
                data = self.btg_manager.get_data(parametros_api(), p_point)
                return data
            except Exception as e:
                # self.logger.error(f"Erro ao capturar dados de princig matrix: {e}")
                return None

        def tratamento_upload_dados(refdate):

            data = captura_dados_api()
            if data is None:
                pass
                # self.logger.error(f"Sem dados para Pricing Matrix. Conferir log para mais info.")
            elif data["result"] == "No records":
                pass
                # self.logger.info(f"'No records' para Pricing Matrix")
            else:
                df = pd.DataFrame(data["result"])
                df = df.rename(
                    columns={
                        "type": "TIPO_ATIVO",
                        "indexes": "INDEXADOR",
                        "issuer": "EMISSOR",
                        "min": "MINIMO_DIAS_VENCIMENTO",
                        "max": "MAXIMO_DIAS_VENCIMENTO",
                        "value": "MARCACAO",
                    }
                )
                df.insert(0, "REFDATE", refdate)
                self.sql_manager.delete_records(
                    "TB_BASE_BTG_PRICING_MATRIX",
                    f"REFDATE = '{refdate.strftime('%Y-%m-%d')}'",
                )
                self.sql_manager.insert_dataframe(df, "TB_BASE_BTG_PRICING_MATRIX")

        tratamento_upload_dados(refdate)

    def funds_ativos_renda_fixa(self, refdate, fund_name=None):

        def parametros_api(refdate, fund_name):
            p_params = {"date": refdate.strftime("%Y-%m-%d"), "fundName": fund_name}
            return p_params

        def captura_dados_api(refdate, fundo):
            p_point = "reports/FixedIncome"
            try:
                data = self.btg_manager.get_data(
                    parametros_api(refdate, fundo), p_point
                )
                return data
            except Exception as e:
                # self.logger.error(f"Erro ao capturar dados FixedIncome {fundo}: {e}")
                # self.logger.error(f"Erro ao capturar dados FixedIncome {fundo}. Verificar log.", True)
                return None

        def tratamento_dados_api(refdate, fundo, data):
            if data is None:
                df = pd.DataFrame({})
                # self.logger.error(f"Dados FixedIncome {fundo}. Conferir log para mais info.", True)
                return df
            elif data["result"] == "No records":
                df = pd.DataFrame({})
                # self.logger.info(f"'No records' FixedIncome para o fundo {fundo}", True)
                return df
            else:
                try:
                    df = pd.DataFrame(data["result"])
                    df["REFDATE"] = refdate
                    df["FUNDO"] = fundo
                    df = df.rename(
                        columns={
                            "snaCode": "COD_IF",
                            "type": "TIPO_ATIVO",
                            "issuerName": "EMISSOR",
                            "issuerDate": "DATA_EMISSAO",
                            "dueDate": "DATA_VENCIMENTO",
                            "indexer": "INDEXADOR",
                            "percentage": "PERC_INDEXADOR",
                            "availableQuantity": "QTD_DISPONIVEL",
                            "marginQuantity": "QTD_MARGEM",
                            "totalQuantity": "QTD_TOTAL",
                            "margin": "MARGEM",
                            "acquisitionDate": "DATA_AQUISICAO",
                            "puAcquisition": "PU_AQUISICAO",
                            "investedAmount": "VALOR_INVESTIDO",
                            "puCurrent": "PU_ATUAL",
                            "availableCurrentValue": "FINANCEIRO_ATUAL_DISPONIVEL",
                            "marginCurrentValue": "FINANCEIRO_ATUAL_MARGEM",
                            "currentValue": "FINANCEIRO",
                            "vlSpread": "VALOR_SPREAD",
                            "vlTax": "TAXA_ATUAL",
                            "vlDurationClos": "DURATION",
                            "vlPercentPupar": "VALOR_PERCENT_PUPAR",
                            "tpFlow": "TP_FLOW",
                        }
                    )
                    df = df[
                        [
                            "REFDATE",
                            "FUNDO",
                            "COD_IF",
                            "TIPO_ATIVO",
                            "EMISSOR",
                            "DATA_EMISSAO",
                            "DATA_VENCIMENTO",
                            "INDEXADOR",
                            "PERC_INDEXADOR",
                            "QTD_DISPONIVEL",
                            "QTD_MARGEM",
                            "QTD_TOTAL",
                            "MARGEM",
                            "DATA_AQUISICAO",
                            "PU_AQUISICAO",
                            "VALOR_INVESTIDO",
                            "PU_ATUAL",
                            "FINANCEIRO_ATUAL_DISPONIVEL",
                            "FINANCEIRO_ATUAL_MARGEM",
                            "FINANCEIRO",
                            "VALOR_SPREAD",
                            "TAXA_ATUAL",
                            "DURATION",
                            "VALOR_PERCENT_PUPAR",
                            "TP_FLOW",
                        ]
                    ]
                    for column in ["DATA_EMISSAO", "DATA_VENCIMENTO", "DATA_AQUISICAO"]:
                        df[column] = pd.to_datetime(df[column])
                    df["sup_tit_pub"] = df.apply(
                        lambda row: row["DATA_VENCIMENTO"].strftime("%b-%y"), axis=1
                    )
                    df["TIPO_ATIVO"] = df["TIPO_ATIVO"].apply(
                        lambda x: "NTN-B" if x == "NTNB" else x
                    )
                    df["COD_ATIVO"] = df.apply(
                        lambda row: (
                            row["TIPO_ATIVO"] + " " + row["sup_tit_pub"]
                            if row["TIPO_ATIVO"] in ["NTN-B", "LFT"]
                            else row["COD_IF"]
                        ),
                        axis=1,
                    )
                    df = df[
                        [
                            "REFDATE",
                            "FUNDO",
                            "TIPO_ATIVO",
                            "COD_ATIVO",
                            "EMISSOR",
                            "DATA_EMISSAO",
                            "DATA_VENCIMENTO",
                            "INDEXADOR",
                            "PERC_INDEXADOR",
                            "QTD_DISPONIVEL",
                            "QTD_MARGEM",
                            "QTD_TOTAL",
                            "MARGEM",
                            "DATA_AQUISICAO",
                            "PU_AQUISICAO",
                            "VALOR_INVESTIDO",
                            "PU_ATUAL",
                            "FINANCEIRO_ATUAL_DISPONIVEL",
                            "FINANCEIRO_ATUAL_MARGEM",
                            "FINANCEIRO",
                            "VALOR_SPREAD",
                            "TAXA_ATUAL",
                            "DURATION",
                            "VALOR_PERCENT_PUPAR",
                            "TP_FLOW",
                        ]
                    ]
                    # df.loc[:, 'MARGEM'] = df['MARGEM'].fillna(0).astype(float)
                    # self.logger.info(f"Tratamento dados FixedIncome {fundo} ok!")
                    return df
                except Exception as e:
                    # self.logger.error(f"Tratamento dados FixedIncome: {e}")
                    # self.logger.error(f"Tratamento dados FixedIncome {fundo}. Verificar log.", True)
                    return pd.DataFrame({})

        def insert_dados_api(refdate, fundo, df):
            try:
                self.sql_manager.delete_records(
                    "TB_BASE_BTG_FIXED_INCOME",
                    f"FUNDO = '{fundo}' AND REFDATE = '{refdate.strftime('%Y-%m-%d')}'",
                )
                # self.logger.info(f"Registros deletados para o fundo {fundo}")
                self.sql_manager.insert_dataframe(df, "TB_BASE_BTG_FIXED_INCOME")
                # self.logger.info(f"Registros inseridos para o fundo {fundo}")
            except Exception as e:
                print(e)
                # self.logger.error(f"Insert dados FixedIncome: {e}")
                # self.logger.error(f"Insert dados FixedIncome {fundo}. Verificar log.", True)

        def run_processo_api(refdate, fundo):
            data = captura_dados_api(refdate, fundo)
            df = tratamento_dados_api(refdate, fundo, data)
            if len(df) > 0:
                insert_dados_api(refdate, fundo, df)
            else:
                pass
                # self.logger.info(f"FixedIncome {fundo} sem dados.")

        if fund_name is not None:
            run_processo_api(refdate, fund_name)
        else:
            for fundo in self.list_funds:
                run_processo_api(refdate, fundo)

    def pricing_curves(self, refdate):

        def parametros_api(refdate):
            p_params = {
                "date": refdate.strftime("%Y-%m-%d"),
                "types": ["Pré", "Dólar", "Ibovespa", "IDI", "IPCA", "TR"],
            }
            return p_params

        def captura_dados_api(refdate):
            p_point = "reports/Pricing/Curves"
            try:
                data = self.btg_manager.get_data(parametros_api(refdate), p_point)
                return data
            except Exception as e:
                # self.logger.error(f"Erro ao capturar dados Princing Curves: {e}")
                # self.logger.error(f"Erro ao capturar dados Princing Curves. Verificar log.", True)
                return None

        def tratamento_dados_api(refdate, data):
            if data is None:
                df = pd.DataFrame({})
                # self.logger.error(f"Dados Pricing Curves. Conferir log para mais info.", True)
                return df
            elif data["result"] == "No records":
                df = pd.DataFrame({})
                # self.logger.info(f"'No records' Pricing Curves", True)
                return df
            else:
                try:
                    df = pd.DataFrame(data["result"])

                    for coluna in ["dateReference", "dateProjection"]:
                        df[coluna] = pd.to_datetime(df[coluna])

                    df["DIAS_CORRIDOS"] = (
                        df["dateProjection"] - df["dateReference"]
                    ).dt.days
                    df = df.query("DIAS_CORRIDOS != 0")
                    df = df[
                        [
                            "dateReference",
                            "typeCurve",
                            "DIAS_CORRIDOS",
                            "valueProjection",
                        ]
                    ].rename(
                        columns={
                            "dateReference": "REFDATE",
                            "typeCurve": "CURVA",
                            "valueProjection": "TAXA_252",
                        }
                    )
                    df["CURVA"] = (
                        df["CURVA"].replace("Pré", "PRE_DI").replace("Dólar", "DOL")
                    )
                    df["FONTE"] = "BTG"
                    return df

                except Exception as e:
                    # self.logger.error(f"Tratamento dados Pricing Curves: {e}")
                    # self.logger.error(f"Tratamento dados Pricing Curves. Verificar log.", True)
                    return pd.DataFrame({})

        def insert_dados_api(refdate, df):
            try:
                self.sql_manager.delete_records(
                    "TB_CURVAS",
                    f"FONTE = 'BTG' AND REFDATE = '{refdate.strftime('%Y-%m-%d')}'",
                )
                # self.logger.info(f"Registros deletados para Pricing Curves")
                self.sql_manager.insert_dataframe(df, "TB_CURVAS")
                # self.logger.info(f"Registros inseridos para Pricing Curves")
            except Exception as e:
                print(e)
                # self.logger.error(f"Insert dados Pricing Curves: {e}")
                # self.logger.error(f"Insert dados Pricing Curves. Verificar log.", True)

        def run_processo_api(refdate):
            data = captura_dados_api(refdate)
            df = tratamento_dados_api(refdate, data)
            if len(df) > 0:
                insert_dados_api(refdate, df)
            else:
                pass
                # self.logger.info(f"Pricing Curves sem dados.")

        run_processo_api(refdate)
