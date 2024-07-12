from __init__ import *

VERSION_APP = "2.0.4"
VERSION_REFDATE = "2024-07-05"
ENVIRONMENT = os.getenv("ENVIRONMENT")
SCRIPT_NAME = os.path.basename(__file__)

if ENVIRONMENT == "DEVELOPMENT":
    print(f"{SCRIPT_NAME.upper()} - {ENVIRONMENT} - {VERSION_APP} - {VERSION_REFDATE}")

# -----------------------------------------------------------------------

import inspect
import sys
from datetime import datetime

import win32com.client as win32

from tools.db_helper import SQL_Manager

# -----------------------------------------------------------------------

class Logger:

    def __init__(self, manager_sql=None):

        self.user = os.getlogin()
        self.refdate = datetime.today().strftime("%Y-%m-%d")
        self.index_log = f"{self.now_log()}_{self.user}_{self.get_script_name()}"
        self.script_running_name = self.get_script_name()
        self.outlook = win32.Dispatch("outlook.application")

        self.tb = "TB_PYTHON_MY_LOGGER"

        self.list_columns = [
            "REFDATE",
            "LOG_INDEX",
            "LOGIN_USER",
            "SCRIPT_ORIGINAL_NAME",
            "SCRIPT_ORIGINAL_LINE",
            "SCRIPT_RUNNING_NAME",
            "DATETIME_RUN",
            "LOG_LEVEL",
            "LOG_MESSAGE",
        ]

        if manager_sql is None:
            self.manager_sql = SQL_Manager()
        else:
            self.manager_sql = manager_sql

    def insert_sql(self, list_values: list):
        self.manager_sql.insert_manual(self.tb, self.list_columns, list_values)

    def reset_index(self):
        self.index_log = f"{self.now_log()}_{self.user}_{self.get_script_name()}"

    def get_current_line_number(self):
        return inspect.currentframe().f_back.f_back.f_lineno

    def get_script_name(self):
        return os.path.basename(sys.argv[0])

    def now_log(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    def send_email(self, log_message=None):

        outlook = win32.Dispatch("outlook.application")
        mail = outlook.CreateItem(0)
        mail.SentOnBehalfOfName = os.getenv("EMAIL_ROBO")
        if ENVIRONMENT == "DEVELOPMENT":
            mail.To = os.getenv("EMAIL_ME")
        else:
            mail.To = os.getenv("EMAIL_BO")
        if self.log_level == "CRITICAL":
            mail.Importance = 2
        else:
            mail.Importance = 1

        mail.subject = f"LogProcess: {self.log_level} - {self.script_running_name} - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"

        str_body = (
            f"Mensagem automática.\n\n"
            f"Refdate: {self.refdate}\n"
            f"Log Index: {self.index_log}\n"
            f"Datetime Run: {self.datetime_run}\n"
            f"Script Running: {self.script_running_name}\n"
            f"Script Original: {self.script_original_name}\n"
            f"Log Line: {self.script_original_line}\n"
            f"Log Message: {"No message" if log_message is None else log_message}\n\n\n"
        )

        mail.body = str_body

        mail.Send()

    def debug(self, log_message, script_original):

        """
        Registra uma mensagem de depuração no banco de dados de logs.

        Args:
            log_message (str): A mensagem de depuração a ser registrada.
            script_original (str): O nome do script original de onde o log está sendo registrado.

        Exemplo de uso:
            logger = Logger()
            logger.debug("Iniciando processo de verificação", os.path.basename(__file__))
        """


        log_entry = [
            self.refdate,
            self.index_log,
            self.user,
            script_original,
            self.get_current_line_number(),
            self.script_running_name,
            self.now_log(),
            "DEBUG",
            log_message,
        ]

        self.insert_sql(log_entry)

    def error(self, log_message, script_original):

        """
        Registra uma mensagem de erro no banco de dados de logs.

        Args:
            log_message (str): A mensagem de depuração a ser registrada.
            script_original (str): O nome do script original de onde o log está sendo registrado.

        Exemplo de uso:
            logger = Logger()
            logger.error("Iniciando processo de verificação", os.path.basename(__file__))
        """

        log_entry = [
            self.refdate,
            self.index_log,
            self.user,
            script_original,
            self.get_current_line_number(),
            self.script_running_name,
            self.now_log(),
            "ERROR",
            log_message,
        ]

        self.insert_sql(log_entry)

    def info(self, log_message, script_original):

        """
        Registra uma mensagem de info no banco de dados de logs.

        Args:
            log_message (str): A mensagem de depuração a ser registrada.
            script_original (str): O nome do script original de onde o log está sendo registrado.

        Exemplo de uso:
            logger = Logger()
            logger.info("Iniciando processo de verificação", os.path.basename(__file__))
        """

        log_entry = [
            self.refdate,
            self.index_log,
            self.user,
            script_original,
            self.get_current_line_number(),
            self.script_running_name,
            self.now_log(),
            "INFO",
            log_message,
        ]

        self.insert_sql(log_entry)

    def critical(self, log_message, script_original):

        """
        Registra uma mensagem de erro critico no banco de dados de logs.
        Envia email para o time de backoffice.

        Args:
            log_message (str): A mensagem de depuração a ser registrada.
            script_original (str): O nome do script original de onde o log está sendo registrado.

        Exemplo de uso:
            logger = Logger()
            logger.debug("Iniciando processo de verificação", os.path.basename(__file__))
        """

        self.log_level = "CRITICAL"
        self.datetime_run = self.now_log()
        self.script_original_line = self.get_current_line_number()

        log_entry = [
            self.refdate,
            self.index_log,
            self.user,
            script_original,
            self.script_original_line,
            self.script_running_name,
            self.datetime_run,
            self.log_level,
            log_message,
        ]

        self.insert_sql(log_entry)
        self.send_email(log_message=log_message)
