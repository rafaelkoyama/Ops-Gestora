import json
import re
from time import sleep, time

import requests
from __init__ import *  # noqa: F403, F405, E402

append_paths()  # noqa: F403, F405, E402

from tools.db_helper import SQL_Manager  # noqa: F403, F405, E402
from tools.my_logger import Logger  # noqa: F403, F405, E402

# -------------------------------------------------------------------------------------------------------

VERSION_APP = "2.2.2"
VERSION_REFDATE = "2024-07-10"
ENVIRONMENT = os.getenv("ENVIRONMENT")  # noqa: F403, F405, E402
SCRIPT_NAME = os.path.basename(__file__)  # noqa: F403, F405, E402

if ENVIRONMENT == "DEVELOPMENT":
    print(f"{SCRIPT_NAME.upper()} - {ENVIRONMENT} - {VERSION_APP} - {VERSION_REFDATE}")

# -------------------------------------------------------------------------------------------------------


def verifica_arquivo_existe(file_path: str) -> bool:
    return os.path.exists(file_path)  # noqa: F403, F405, E402


def deleta_arquivo_existente(file_path: str):
    os.remove(file_path)  # noqa: F403, F405, E402


class BTGDataManager:

    def __init__(
        self,
        client_id=None,
        client_secret=None,
        btg_reports=None,
        manager_sql=None,
        logger=None,
    ):

        if manager_sql is None:
            self.manager_sql = SQL_Manager()
        else:
            self.manager_sql = manager_sql

        if logger is None:
            self.logger = Logger(manager_sql=self.manager_sql)
        else:
            self.logger = logger

        self.logger.info(
            log_message=f"BTGDataManager - {VERSION_APP} - {ENVIRONMENT} - Instanciado",
            script_original=SCRIPT_NAME,
        )

        if ENVIRONMENT == "DEVELOPMENT":
            self.base_url = "https://funds-uat.btgpactual.com"
            self.client_id = os.getenv("USER_BTG_FAAS")  # noqa: F403, F405, E402
            self.client_secret = os.getenv("PASS_BTG_FASS_UAT")  # noqa: F403, F405, E402
        else:
            self.base_url = "https://funds.btgpactual.com"
            self.client_id = client_id
            self.client_secret = client_secret

        self.token, self.timeout = self.authenticate()

        if btg_reports is not None:
            self.dict_suporte_download = btg_reports.dict_suporte_download

    def authenticate(self):
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }
        response = requests.post(
            f"{self.base_url}/connect/token", headers=headers, data=payload
        )

        if response.status_code != 200:
            self.logger.error(
                log_message=f"BTGDataManager - Token - {response.text}",
                script_original=SCRIPT_NAME,
            )
            return None, None

        token = response.json()["access_token"]
        timeout = time() + response.json()["expires_in"] - 100
        self.logger.info(
            log_message="BTGDataManager - Token - ok", script_original=SCRIPT_NAME
        )
        return token, timeout

    def check_token(self):
        if time() > self.timeout:
            self.logger.info(
                log_message="BTGDataManager - Token - Expirado",
                script_original=SCRIPT_NAME,
            )
            self.token, self.timeout = self.authenticate()
        else:
            pass

    def get_data(self, p_params, p_point, fundo=None, refdate=None):
        self.logger.reset_index()
        self.check_token()

        if self.token is not None:

            if p_point in [
                "reports/Fund",
                "reports/RTA/PerformanceFee",
                "reports/Cash/MoneyMarket",
                "reports/Cash/Cashflow",
                "reports/Portfolio",
                "reports/NAVPerformance",
                "reports/RTA/ManagementFee",
                "reports/RTA/FundFlow",
                "reports/Cash/FundAccountStatement",
                "reports/RTA/Subscription",
                "reports/FixedIncome",
                "reports/Pricing/Curves",
                "reports/Pricing/Matrix",
            ]:

                endPoint = f"{self.base_url}/{p_point}"
                j_params = json.dumps({"contract": p_params})
                headers = {
                    "Content-Type": "application/json",
                    "X-SecureConnect-Token": self.token,
                }
                post_api = requests.post(endPoint, headers=headers, data=j_params)

                if post_api.status_code != 200:
                    return None
                else:
                    data_check_status_tkt = self.check_status_tkt(
                        post_api.text, fundo, refdate
                    )
                    return data_check_status_tkt

            elif p_point in [
                "reports/Portfolio/PortfolioQuotaListToDate",
                "reports/Pricing/Matrix/Types",
                "reports/Pricing/Matrix/Indexes",
                "reports/Pricing/Matrix/Issuers",
            ]:  # endPoint sem Ticket

                endPoint = f"{self.base_url}/{p_point}"
                j_params = p_params

                if p_point in [
                    "reports/Portfolio/PortfolioQuotaListToDate",
                    "reports/Pricing/Matrix/Types",
                    "reports/Pricing/Matrix/Indexes",
                    "reports/Pricing/Matrix/Issuers",
                ]:
                    headers = {"X-SecureConnect-Token": self.token}
                else:
                    headers = {
                        "Content-Type": "application/json",
                        "X-SecureConnect-Token": self.token,
                    }
                resp_api = requests.get(endPoint, headers=headers, params=j_params)

                if resp_api.status_code != 200:
                    return None
                else:
                    data = json.loads(resp_api.text)
                    return data

            else:  # endPoint não mapeado

                return "endpoint_nao_mapeado"
        else:  # Erro na geração de Token
            return "token_nao_gerado"

    def check_status_tkt(self, response_text, fundo=None, refdate=None):

        ticket_id = json.loads(response_text)["ticket"]
        endPoint = f"{self.base_url}/reports/Ticket"
        headers = {"X-SecureConnect-Token": self.token}

        resp_api = requests.get(
            endPoint, headers=headers, params={"ticketId": ticket_id}
        )

        if resp_api.status_code != 200:
            return None
        else:
            try:
                data = json.loads(resp_api.text)
                timeout = time() + 300  # Timeout after 5 minutes
                while time() < timeout:
                    if data["result"] in ["Processando", "Aguardando processamento"]:
                        sleep(5)
                        resp_api = requests.get(
                            endPoint, headers=headers, params={"ticketId": ticket_id}
                        )
                        try:
                            data = json.loads(resp_api.text)
                        except:
                            break
                    else:
                        break
            except:
                pass

            if (
                resp_api.headers["content-type"] == "application/octet-stream"
            ):  # Arquivos para download
                content_disposition = resp_api.headers.get("content-disposition", "")
                filename_match = re.search(r"filename=([^;]+)", content_disposition)
                if filename_match:
                    filename = filename_match.group(1)
                    filename = filename.strip("\"'")
                    if filename.endswith(".xml"):
                        tipo_file = "xml"
                    elif filename.endswith(".xlsx"):
                        tipo_file = "xlsx"
                    elif filename.endswith(".pdf"):
                        tipo_file = "pdf"

                file_name = os.path.join(  # noqa: F403, F405, E402
                    self.dict_suporte_download[fundo],
                    tipo_file,
                    f"{'ResumoCarteira_' if tipo_file == 'xlsx' else ''}"
                    f"{fundo.replace(' ', '_')}_{refdate.strftime('%Y%m%d')}.{tipo_file}",
                )

                try:
                    if verifica_arquivo_existe(file_name):
                        return "arquivo_existente"
                    else:
                        with open(file_name, "wb") as f:
                            f.write(resp_api.content)
                        return "ok"
                except Exception as e:
                    return e
            else:  # Json para leitura de dados
                return data
