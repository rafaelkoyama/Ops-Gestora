from datetime import date, datetime, timedelta
from math import trunc

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import win32com.client as win32
from __init__ import *  # noqa: F403
from dateutil.relativedelta import relativedelta
from matplotlib.ticker import FuncFormatter

append_paths()  # noqa: F405

from tools.db_helper import SQL_Manager  # noqa: E402
from tools.my_logger import Logger  # noqa: E402

# -------------------------------------------------------------------------------------------------------

VERSION_APP = "1.1.4"
VERSION_REFDATE = "2024-07-08"
ENVIRONMENT = os.getenv("ENVIRONMENT")  # noqa: F405
SCRIPT_NAME = os.path.basename(__file__)  # noqa: F405

if ENVIRONMENT == "DEVELOPMENT":
    print(f"{SCRIPT_NAME.upper()} - {ENVIRONMENT} - {VERSION_APP} - {VERSION_REFDATE}")

# -------------------------------------------------------------------------------------------------------
# Classes:


class FuncoesPyTools:

    def __init__(self, manager_sql=None, logger=None):
        if manager_sql is None:
            self.manager_sql = SQL_Manager()
        else:
            self.manager_sql = manager_sql

        if logger is None:
            self.logger = Logger(manager_sql=self.manager_sql)
        else:
            self.logger = logger

        self.logger.info(
            log_message=f"FuncoesPyTools - {VERSION_APP} - {ENVIRONMENT} - instanciado",
            script_original=SCRIPT_NAME)

        self.feriados_br = self.captura_feriados_br()
        self.dias_semana = [0, 1, 2, 3, 4]

    def dias_uteis_mes(self, refdate):

        data_mes_mais = refdate + relativedelta(months=1)

        data_inicio = self.workday_br(
            date(refdate.year, refdate.month, 1) - timedelta(days=1), 1
        )
        data_fim = self.workday_br(
            date(data_mes_mais.year, data_mes_mais.month, 1), -1)

        return self.networkdays_br(data_inicio, data_fim)

    def date_str_arquivo_anbima(self, refdate):

        dict_meses = {
            1: "jan",
            2: "fev",
            3: "mar",
            4: "abr",
            5: "mai",
            6: "jun",
            7: "jul",
            8: "ago",
            9: "set",
            10: "out",
            11: "nov",
            12: "dez",
        }

        return f"d{refdate.strftime('%y')}{dict_meses[refdate.month]}{refdate.strftime('%d')}"

    def date_str_mes_ano(self, refdate):

        dict_meses = {
            1: "Jan",
            2: "Fev",
            3: "Mar",
            4: "Abr",
            5: "Mai",
            6: "Jun",
            7: "Jul",
            8: "Ago",
            9: "Set",
            10: "Out",
            11: "Nov",
            12: "Dez",
        }

        return f"{dict_meses[refdate.month]}-{refdate.strftime('%y')}"

    def captura_feriados_br(self):
        df = self.manager_sql.select_dataframe(
            "SELECT REFDATE_FERIADO FROM TB_FERIADOS WHERE CALENDARIO_FERIADO = 'BR' ORDER BY REFDATE_FERIADO"
        )
        lista_feriados = df.values.tolist()
        lista_feriados = list(row[0] for row in lista_feriados)
        return lista_feriados

    def networkdays(self, data_inicio, data_fim, feriados=None):

        feriados = set(feriados) if feriados is not None else set()

        data_ref = data_inicio
        count_days = 0

        while data_ref <= data_fim:
            if data_ref.weekday() in self.dias_semana and data_ref not in feriados:
                count_days += 1
            data_ref = data_ref + timedelta(days=1)

        return count_days - 1

    def workday(self, refdate, dias, feriados=None):

        feriados = set(feriados) if feriados is not None else set()

        data_ref = refdate
        count_days = 0
        loops = abs(dias)

        while count_days < loops:

            if dias > 0:
                data_ref = data_ref + timedelta(days=1)
            else:
                data_ref = data_ref - timedelta(days=1)

            if data_ref.weekday() in self.dias_semana and data_ref not in feriados:
                count_days += 1

        return data_ref

    def networkdays_br(self, data_inicio, data_fim):

        data_ref = data_inicio
        count_days = 0

        while data_ref <= data_fim:
            if (data_ref.weekday() in self.dias_semana and data_ref not in self.feriados_br):
                count_days += 1
            data_ref = data_ref + timedelta(days=1)

        return count_days - 1

    def workday_br(self, refdate, dias):

        data_ref = refdate
        count_days = 0
        loops = abs(dias)

        while count_days < loops:

            if dias > 0:
                data_ref = data_ref + timedelta(days=1)
            else:
                data_ref = data_ref - timedelta(days=1)

            if (data_ref.weekday() in self.dias_semana and data_ref not in self.feriados_br):
                count_days += 1

        return data_ref

    def diasCorridos_br(self, refdate, dias):
        data_ref = refdate
        count_days = 0
        loops = abs(dias)

        while count_days < loops:
            if dias > 0:
                data_ref = data_ref + timedelta(days=1)
            else:
                data_ref = data_ref - timedelta(days=1)
            count_days += 1

        while data_ref.weekday() not in self.dias_semana or data_ref in self.feriados_br:
            if data_ref.weekday() not in self.dias_semana:
                is_weekday = False
            else:
                is_weekday = True

            if data_ref in self.feriados_br:
                is_holiday = True
            else:
                is_holiday = False

            if is_weekday and not is_holiday:
                break
            else:
                if dias > 0:
                    data_ref = data_ref + timedelta(days=1)
                else:
                    data_ref = data_ref - timedelta(days=1)

        return data_ref

    def dias_corridos(self, data_inicio, data_fim):
        dif = data_fim - data_inicio
        return int(dif.days)

    def trunc_number(self, numero, casas_decimais):
        return trunc(numero * 10**casas_decimais) / 10**casas_decimais

    def convert_data_sql(self, data):
        return datetime.strftime(data, "%Y-%m-%d")

    def formatar_data_hora(self, data_hora_str):
        if data_hora_str is not None:
            data_hora_obj = datetime.strptime(
                data_hora_str, "%Y-%m-%dT%H:%M:%S")
            return data_hora_obj.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return "Sem dado"

    def formatar_cnpj(self, cnpj_str):
        cnpj_str = cnpj_str.strip()
        return f"{cnpj_str[:2]}.{cnpj_str[2:5]}.{cnpj_str[5:8]}/{cnpj_str[8:12]}-{cnpj_str[12:]}"

    def captura_rent_indexador(self, data_inicio, data_fim, nomeIndexador):

        cota_inicio = self.manager_sql.select_dataframe(
            f"SELECT COTA_INDEXADOR FROM TB_INDEXADORES WHERE INDEXADOR = '{
                nomeIndexador}' AND REFDATE = '{datetime.strftime(data_inicio, '%Y-%m-%d')}'"
        )["COTA_INDEXADOR"]

        cota_fim = self.manager_sql.select_dataframe(
            f"SELECT COTA_INDEXADOR FROM TB_INDEXADORES WHERE INDEXADOR = '{
                nomeIndexador}' AND REFDATE = '{datetime.strftime(data_fim, '%Y-%m-%d')}'"
        )["COTA_INDEXADOR"]

        rent_indexador = cota_fim / cota_inicio

        if cota_inicio.empty or cota_fim.empty:
            return None
        else:
            return rent_indexador

    def checkFileExists(self, path):
        return os.path.exists(path)  # noqa: F405

    def find_header_row(self, file_path, header_name):
        with open(file_path, 'r', encoding='utf-8') as file:
            for i, line in enumerate(file):
                if header_name in line:
                    return i

    def convert_list_to_str(self, data_list):
        """
        Converte uma lista de elementos em uma string.
        Strings são convertidas com aspas simples e separadas por vírgulas.
        Números são separados por vírgulas sem aspas.

        Args:
            data_list (list): Lista de elementos a serem convertidos.

        Returns:
            str: String convertida.
        """
        str_elements = []
        num_elements = []

        for item in data_list:
            if isinstance(item, str):
                str_elements.append(f"'{item}'")
            elif isinstance(item, (int, float)):
                num_elements.append(str(item))

        result = ', '.join(str_elements + num_elements)
        return result

    def format_df_float_columns_to_str(self, df: pd.DataFrame, columns: list, decimals: int = 2):
        """
        Formata as colunas especificadas de um DataFrame como strings com o número especificado de casas decimais.

        Args:
            df (pd.DataFrame): O DataFrame a ser formatado.
            columns (list): Lista de nomes das colunas a serem formatadas.
            decimals (int): Número de casas decimais para formatação. Padrão é 2.

        Returns:
            pd.DataFrame: O DataFrame com as colunas especificadas formatadas como strings.
        """

        for column in columns:
            if column in df.columns and pd.api.types.is_numeric_dtype(df[column]):
                df[column] = df[column].apply(lambda x: f"{x:,.{decimals}f}")

        return df


class ProcessManagerOutlook:

    def __init__(self, app):

        self.app = app

        self.manager_sql = self.app.manager_sql
        self.funcoes_pytools = self.app.funcoes_pytools
        self.logger = self.app.logger

    def send_email(
        self,
        to_list: list,
        subject: str,
        msg_body: str,
        attachment_list: list = None,
        sendBehalf: str = None,
        importance=1,
    ):

        try:
            try:
                mail = self.app.outlook.CreateItem(0)
            except AttributeError:
                outlook = win32.Dispatch("outlook.application")
                mail = outlook.CreateItem(0)

            except Exception as e:
                self.logger.critical(log_message=f"ProcessManagerOutlook - {e}", script_original=SCRIPT_NAME)
                self.logger.reset_index()
                return False

            mail.To = ";".join(to_list)
            mail.Subject = subject
            mail.Body = msg_body

            mail.Importance = importance

            if sendBehalf is not None:
                mail.SentOnBehalfOfName = sendBehalf

            if attachment_list is not None:
                for attachment in attachment_list:
                    mail.Attachments.Add(attachment)

            mail.Send()
            self.logger.info(log_message="ProcessManagerOutlook - Email enviado", script_original=SCRIPT_NAME)
            self.logger.reset_index()
            return True

        except Exception as e:
            self.logger.critical(log_message=f"ProcessManagerOutlook - {e}", script_original=SCRIPT_NAME)
            self.logger.reset_index()
            return False

    def find_folder_by_name(self, target_name, folder=None):

        try:
            if folder is None:
                folder = self.inbox

            if folder.Name == target_name:
                return folder

            for subfolder in folder.Folders:
                result = self.find_folder_by_name(target_name, subfolder)
                if result:
                    return result

            return False
        except Exception as e:
            self.logger.error(log_message=f"ProcessManagerOutlook - find_folder_by_name - {e}", script_original=SCRIPT_NAME)
            return False

    def save_attachments_from_folder(
        self,
        name_folder,
        refdate_email: date,
        str_to_find_attachment,
        str_endswith,
        str_to_save_attchament,
    ):

        if self.funcoes_pytools.checkFileExists(str_to_save_attchament):
            self.logger.info(
                log_message="ProcessManagerOutlook - save_attachments_from_folder - Arquivo já existe",
                script_original=SCRIPT_NAME
            )
            return "Arquivo já existe"

        try:
            self.inbox = self.app.outlook.GetNamespace("MAPI").GetDefaultFolder(6)
        except AttributeError:
            outlook = win32.Dispatch("outlook.application")
            self.inbox = outlook.GetNamespace("MAPI").GetDefaultFolder(6)
        except Exception as e:
            self.logger.critical(log_message=f"ProcessManagerOutlook - {e}", script_original=SCRIPT_NAME)
            self.logger.reset_index()
            return False

        folder = self.find_folder_by_name(target_name=name_folder)

        if folder is not False:
            self.logger.info(
                log_message=f"ProcessManagerOutlook - find_folder_by_name - Pasta encontada",
                script_original=SCRIPT_NAME)

            try:
                for email in folder.Items:
                    try:
                        if email.ReceivedTime.date() >= refdate_email:
                            for attachment in email.Attachments:
                                if (str_to_find_attachment in attachment.FileName and attachment.FileName.endswith(str_endswith)):
                                    attachment.SaveAsFile(str_to_save_attchament)
                                    self.logger.info(
                                        log_message=f"ProcessManagerOutlook - save_attachments_from_folder - Arquivo salvo",
                                        script_original=SCRIPT_NAME
                                    )
                                    self.logger.reset_index()
                                    return True
                    except AttributeError:
                        pass

                self.logger.info(
                    log_message=f"ProcessManagerOutlook - save_attachments_from_folder - Arquivo não encontrado",
                    script_original=SCRIPT_NAME
                )
                self.logger.reset_index()
                return False
            except Exception as e:
                self.logger.critical(
                    log_message=f"ProcessManagerOutlook - save_attachments_from_folder - {e}",
                    script_original=SCRIPT_NAME
                )
                self.logger.reset_index()
                return False


class OutlookHandler:

    def __init__(self, manager_sql=None, funcoes_pytools=None, logger=None):

        if manager_sql is None:
            self.manager_sql = SQL_Manager()
        else:
            self.manager_sql = manager_sql

        if funcoes_pytools is None:
            self.funcoes_pytools = FuncoesPyTools()
        else:
            self.funcoes_pytools = funcoes_pytools

        if logger is None:
            self.logger = Logger(manager_sql=self.manager_sql)
        else:
            self.logger = logger

        self.logger.info(
            log_message=f"OutlookHandler - {VERSION_APP} - {ENVIRONMENT} - instanciado",
            script_original=SCRIPT_NAME)

        self.outlook = win32.Dispatch("outlook.application")

        self.process_manager = ProcessManagerOutlook(app=self)

    def senf_email_robo(self, to_list: list, subject: str, msg_body: str, importance=1, attachment_list: list = None):

        msg_body_head = (
            f"Mensagem automática.\n\n"
        )

        return self.process_manager.send_email(
            to_list=to_list,
            subject=subject,
            msg_body=msg_body_head + msg_body,
            attachment_list=attachment_list,
            sendBehalf=os.getenv("EMAIL_ROBO"),  # noqa: F405
            importance=importance,
        )

    def send_email(
        self,
        to_list: list,
        subject: str,
        msg_body: str,
        attachment_list: list = None,
        sendBehalf: str = None,
        importance=1,
    ):

        return self.process_manager.send_email(
            to_list=to_list,
            subject=subject,
            msg_body=msg_body,
            attachment_list=attachment_list,
            sendBehalf=sendBehalf,
            importance=importance,
        )

    def find_folder_by_name(self, target_name, folder=None):
        return self.process_manager.find_folder_by_name(target_name, folder=folder)

    def save_attachments_from_folder(
        self,
        name_folder,
        refdate_email: date,
        str_to_find_attachment,
        str_endswith,
        str_to_save_attchament,
    ):

        return self.process_manager.save_attachments_from_folder(
            name_folder=name_folder,
            refdate_email=refdate_email,
            str_to_find_attachment=str_to_find_attachment,
            str_endswith=str_endswith,
            str_to_save_attchament=str_to_save_attchament,
        )


class Graficos:

    def to_percent(self, y, position, decimals=2):
        _ = position
        s = f"{100 * y:.{decimals}f}%"
        return s

    def graficoLinhas(self, df_dados: pd.DataFrame, titulo_grafico: str = None, label_dados: str = None, label_eixo_y: str = None,
                      tamanho_fig=(12, 6), dados_percent=True, decimals=2):

        df_dados = df_dados.values.tolist()
        refdates, dados = zip(*df_dados)

        refdates = [
            data.strftime("%Y-%m-%d") if not isinstance(data, str) else data
            for data in refdates
        ]

        plt.style.use("seaborn-v0_8-dark")

        plt.figure(figsize=tamanho_fig)

        plt.plot(
            refdates, dados, label=label_dados if label_dados else "", color="DarkSlateGray", linewidth=1
        )

        plt.title(
            titulo_grafico if titulo_grafico else "",
            fontsize=16,
            fontweight="bold",
        )

        if label_eixo_y:
            plt.ylabel(label_eixo_y)

        if dados_percent:
            formatter = FuncFormatter(lambda x, pos: self.to_percent(x, pos, decimals))
            plt.gca().yaxis.set_major_formatter(formatter)

        qtd_refdates = len(refdates)

        if qtd_refdates < 15:
            intervalo = 1
        else:
            intervalo = int(len(refdates) / 15)

        plt.xticks(
            ticks=np.arange(len(refdates))[::intervalo],
            labels=[refdates[i] for i in np.arange(len(refdates))[::intervalo]],
            rotation=90,
        )

        plt.grid(
            True, which="major", linestyle="--", linewidth=0.5, color="grey", axis="y"
        )

        plt.tight_layout()

        if label_dados:
            plt.legend()

        return plt
