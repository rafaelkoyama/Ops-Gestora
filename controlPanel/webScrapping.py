import shutil
import time
from datetime import date, datetime

import numpy as np
import pandas as pd
import requests
from __init__ import *  # noqa: F403, F405, E402
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager

append_paths()  # noqa: F403, F405, E402

from tools.db_helper import SQL_Manager  # noqa: F403, F405, E402
from tools.my_logger import Logger  # noqa: F403, F405, E402
from tools.py_tools import FuncoesPyTools  # noqa: F403, F405, E402

# -------------------------------------------------------------------------------------------------------

VERSION_APP = '1.1.1'
VERSION_REFDATE = "2024-07-10"
ENVIRONMENT = os.getenv("ENVIRONMENT")  # noqa: F403, F405, E402
SCRIPT_NAME = os.path.basename(__file__)  # noqa: F403, F405, E402

if ENVIRONMENT == "DEVELOPMENT":
    print(f"{SCRIPT_NAME.upper()} - {ENVIRONMENT} - {VERSION_APP} - {VERSION_REFDATE}")

# -------------------------------------------------------------------------------------------------------

pd.set_option('future.no_silent_downcasting', True)

# Configurar as opções do Edge
edge_options = Options()
edge_options.add_argument("--log-level=3")  # Suprimir logs de depuração do navegador
edge_options.add_argument("--silent")  # Suprimir logs adicionais do navegador


class openEdgeDriver():

    def __init__(self):
        self.open_edge()

    def open_edge(self):
        try:
            self.service = Service(EdgeChromiumDriverManager().install())
            self.driver = webdriver.Edge(service=self.service, options=edge_options)
        except Exception as e:
            print(f"Erro ao abrir o navegador: {e}")
            return None


class debenturesAnbima():
    def __init__(self, manager_sql=None, funcoes_pytools=None, logger=None):
        if manager_sql is None:
            self.manager_sql = SQL_Manager()
        else:
            self.manager_sql = manager_sql

        if funcoes_pytools is None:
            self.funcoes_pytools = FuncoesPyTools(self.manager_sql)
        else:
            self.funcoes_pytools = funcoes_pytools

        if logger is None:
            self.logger = Logger(self.manager_sql)
        else:
            self.logger = logger

        self.logger.info(
            log_message=f"debenturesAnbima - {VERSION_APP} - {ENVIRONMENT} - Instanciado",
            script_original=SCRIPT_NAME
        )

    def set_refdate(self, refdate: date):
        self.refdate = refdate

    def urlDownload(self):
        str_date = self.funcoes_pytools.date_str_arquivo_anbima(self.refdate)
        return f"https://www.anbima.com.br/informacoes/merc-sec-debentures/arqs/{str_date}.xls"

    def pathArq(self):
        str_date = self.funcoes_pytools.date_str_arquivo_anbima(self.refdate)
        return f'C:\\Users\\{str_user}\\Strix Capital\\Backoffice - General\\ANBIMA\\{str_date}.xls'  # noqa: F403, F405, E402

    def downloadArquivo(self):
        if not self.check_arq_salvo:
            try:
                response = requests.get(self.url)
                response.raise_for_status()

                with open(self.path_arq, 'wb') as file:
                    file.write(response.content)
                return 'ok'
            except requests.RequestException as e:
                return e
            except Exception as e:
                return e
        else:
            return 'ok'

    def ipcaSpread(self):

        df_ipca_spread = pd.read_excel(self.path_arq, sheet_name='IPCA_SPREAD', skiprows=8)
        df_ipca_spread = df_ipca_spread.rename(columns={
            'Unnamed: 0': 'COD_ATIVO',
            'Unnamed: 1': 'NOME',
            'Unnamed: 2': 'REPAC_VENC',
            'Unnamed: 3': 'INDICE_CORRECAO',
            'Unnamed: 4': 'TAXA_COMPRA',
            'Unnamed: 5': 'TAXA_VENDA',
            'Unnamed: 6': 'TAXA_INDICATIVA',
            'Unnamed: 7': 'DESVIO_PADRAO',
            'Min.': 'INTERVALO_MIN',
            'Máx.': 'INTERVALO_MAX',
            'Unnamed: 10': 'PU',
            'Unnamed: 11': 'PERC_PU_PAR',
            'Unnamed: 12': 'DURATION',
            'Unnamed: 13': 'PERC_REUNE',
            'Unnamed: 14': 'REFERENCIA_NTNB'
        })

        df_ipca_spread.insert(0, 'REFDATE', self.refdate.strftime('%Y-%m-%d'))
        df_ipca_spread = df_ipca_spread[(df_ipca_spread['COD_ATIVO'].str.len() <= 10) & (df_ipca_spread['COD_ATIVO'].notna())]
        for column in ['REPAC_VENC', 'REFERENCIA_NTNB']:
            df_ipca_spread[column] = pd.to_datetime(df_ipca_spread[column], dayfirst=True)

        for column in [
            'TAXA_COMPRA',
            'TAXA_VENDA',
            'TAXA_INDICATIVA',
            'DESVIO_PADRAO',
            'INTERVALO_MIN',
            'INTERVALO_MAX',
            'PU',
            'PERC_PU_PAR',
            'DURATION'
        ]:
            df_ipca_spread[column] = df_ipca_spread[column].replace('--', np.nan).replace('N/D', np.nan).astype('float64')

        return df_ipca_spread

    def diSpread(self):

        df_di_spread = pd.read_excel(self.path_arq, sheet_name='DI_SPREAD', skiprows=8)
        df_di_spread = df_di_spread.rename(columns={
            'Unnamed: 0': 'COD_ATIVO',
            'Unnamed: 1': 'NOME',
            'Unnamed: 2': 'REPAC_VENC',
            'Unnamed: 3': 'INDICE_CORRECAO',
            'Unnamed: 4': 'TAXA_COMPRA',
            'Unnamed: 5': 'TAXA_VENDA',
            'Unnamed: 6': 'TAXA_INDICATIVA',
            'Unnamed: 7': 'DESVIO_PADRAO',
            'Min.': 'INTERVALO_MIN',
            'Máx.': 'INTERVALO_MAX',
            'Unnamed: 10': 'PU',
            'Unnamed: 11': 'PERC_PU_PAR',
            'Unnamed: 12': 'DURATION',
            'Unnamed: 13': 'PERC_REUNE'
        })

        df_di_spread.insert(0, 'REFDATE', self.refdate.strftime('%Y-%m-%d'))
        df_di_spread = df_di_spread[(df_di_spread['COD_ATIVO'].str.len() <= 10) & (df_di_spread['COD_ATIVO'].notna())]
        df_di_spread['REFERENCIA_NTNB'] = pd.NaT
        df_di_spread['REPAC_VENC'] = pd.to_datetime(df_di_spread['REPAC_VENC'], dayfirst=True)
        df_di_spread.drop(columns=['Unnamed: 14'], inplace=True)

        for column in [
            'TAXA_COMPRA',
            'TAXA_VENDA',
            'TAXA_INDICATIVA',
            'DESVIO_PADRAO',
            'INTERVALO_MIN',
            'INTERVALO_MAX',
            'PU',
            'PERC_PU_PAR',
            'DURATION'
        ]:
            df_di_spread[column] = df_di_spread[column].replace('--', np.nan).replace('N/D', np.nan).astype('float64')

        return df_di_spread

    def diPercentual(self):

        df_di_percentual = pd.read_excel(self.path_arq, sheet_name='DI_PERCENTUAL', skiprows=8)
        df_di_percentual = df_di_percentual.rename(columns={
            'Unnamed: 0': 'COD_ATIVO',
            'Unnamed: 1': 'NOME',
            'Unnamed: 2': 'REPAC_VENC',
            'Unnamed: 3': 'INDICE_CORRECAO',
            'Unnamed: 4': 'TAXA_COMPRA',
            'Unnamed: 5': 'TAXA_VENDA',
            'Unnamed: 6': 'TAXA_INDICATIVA',
            'Unnamed: 7': 'DESVIO_PADRAO',
            'Min.': 'INTERVALO_MIN',
            'Máx.': 'INTERVALO_MAX',
            'Unnamed: 10': 'PU',
            'Unnamed: 11': 'PERC_PU_PAR',
            'Unnamed: 12': 'DURATION',
            'Unnamed: 13': 'PERC_REUNE'
        })

        df_di_percentual.insert(0, 'REFDATE', self.refdate.strftime('%Y-%m-%d'))
        df_di_percentual = df_di_percentual[(df_di_percentual['COD_ATIVO'].str.len() <= 10) & (df_di_percentual['COD_ATIVO'].notna())]
        df_di_percentual['REFERENCIA_NTNB'] = pd.NaT
        df_di_percentual['REPAC_VENC'] = pd.to_datetime(df_di_percentual['REPAC_VENC'], dayfirst=True)
        df_di_percentual.drop(columns=['Unnamed: 14'], inplace=True)

        for column in [
            'TAXA_COMPRA',
            'TAXA_VENDA',
            'TAXA_INDICATIVA',
            'DESVIO_PADRAO',
            'INTERVALO_MIN',
            'INTERVALO_MAX',
            'PU',
            'PERC_PU_PAR',
            'DURATION'
        ]:
            df_di_percentual[column] = df_di_percentual[column].replace('--', np.nan).replace('N/D', np.nan).astype('float64')

        return df_di_percentual

    def uploadBases(self):

        self.manager_sql.delete_records('TB_ANBIMA_DEBENTURES', f"REFDATE = '{self.refdate.strftime('%Y-%m-%d')}'")
        try:
            self.manager_sql.insert_dataframe(self.ipcaSpread(), 'TB_ANBIMA_DEBENTURES')
            self.manager_sql.insert_dataframe(self.diSpread(), 'TB_ANBIMA_DEBENTURES')
            self.manager_sql.insert_dataframe(self.diPercentual(), 'TB_ANBIMA_DEBENTURES')
            return 'ok'
        except Exception as e:
            print(f'Erro ao inserir dados: {e}')
            return e

    def check_sql_uploaded(self):

        check_sql = self.manager_sql.check_if_data_exists(
            f"SELECT DISTINCT REFDATE FROM TB_ANBIMA_DEBENTURES "
            f"WHERE REFDATE = '{self.funcoes_pytools.convert_data_sql(self.refdate)}'")

        return check_sql

    def run(self, refdate: date):

        self.set_refdate(refdate)

        if not self.check_sql_uploaded():

            self.url = self.urlDownload()
            self.path_arq = self.pathArq()
            self.check_arq_salvo = self.funcoes_pytools.checkFileExists(self.path_arq)

            check_arquivo = self.downloadArquivo()
            if check_arquivo == 'ok':
                self.logger.info(log_message="debenturesAnbima - Arquivo baixado com sucesso", script_original=SCRIPT_NAME)
                check_upload = self.uploadBases()
                if check_upload == 'ok':
                    self.logger.info(log_message="debenturesAnbima - Upload - ok", script_original=SCRIPT_NAME)
                    return 'ok'
                else:
                    self.logger.error(log_message=f"debenturesAnbima - check_update - {check_upload}", script_original=SCRIPT_NAME)
                    return check_upload
            else:
                self.logger.error(log_message=f"debenturesAnbima - check_arquivo - {check_arquivo}", script_original=SCRIPT_NAME)
                return check_arquivo
        else:
            self.logger.info(log_message="debenturesAnbima - Já baixado anteriormente", script_original=SCRIPT_NAME)
            return 'Já baixado anteriormente'


class curvasB3():

    def __init__(self, manager_sql=None, funcoes_pytools=None, logger=None):

        if manager_sql is None:
            self.manager_sql = SQL_Manager()
        else:
            self.manager_sql = manager_sql

        if funcoes_pytools is None:
            self.funcoes_pytools = FuncoesPyTools(self.manager_sql)
        else:
            self.funcoes_pytools = funcoes_pytools

        if logger is None:
            self.logger = Logger(self.manager_sql)
        else:
            self.logger = logger

        self.logger.info(
            log_message=f"curvasB3 - {VERSION_APP} - {ENVIRONMENT} - Instanciado",
            script_original=SCRIPT_NAME
        )

        self.path_download = f"C:\\Users\\{str_user}\\Downloads"  # noqa: F403, F405, E402
        self.path_to_move = f'C:\\Users\\{str_user}\\Strix Capital\\Backoffice - General\\Processos\\Arquivos bases'  # noqa: F403, F405

        self.dict_tipo = {
            'DI X PRE': 'PRE'
        }

    def set_refdate(self, refdate: date):
        self.refdate = refdate

    def check_sql_uploaded(self):

        str_curvas = f"'{"', '".join(self.dict_tipo.keys())}'"

        lista_curvas_sql = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT CURVA AS CURVAS FROM TB_CURVAS "
            f"WHERE FONTE = 'B3' AND REFDATE = '{self.funcoes_pytools.convert_data_sql(self.refdate)}' "
            f"AND CURVA IN ({str_curvas})")['CURVAS'].tolist()

        check_all_curvas_ok = set(self.dict_tipo.keys()).issubset(lista_curvas_sql)

        if check_all_curvas_ok is True:
            return True
        else:
            return [item for item in set(self.dict_tipo.keys()) if item not in lista_curvas_sql]

    def verificaDownload(self):

        timeout = 10
        start_time = time.time()

        while True:
            if self.funcoes_pytools.checkFileExists(
                os.path.join(  # noqa: F403, F405, E402
                    self.path_download,
                    f"{self.dict_tipo[self.tipo]}{self.refdate.strftime('%Y%m%d')} .xls")):
                self.ajustaNomeArquivo()
                return True
            elif time.time() - start_time > timeout:
                return False
            else:
                time.sleep(1)

    def urlDownload(self):
        str_date = self.refdate.strftime('%d/%m/%Y')
        str_date1 = self.refdate.strftime('%Y%m%d')
        return f"https://www2.bmf.com.br/pages/portal/bmfbovespa/boletim1/TxRef1.asp?Data={str_date}&Data1={str_date1}&slcTaxa={self.dict_tipo[self.tipo]}"  # noqa: E501

    def ajustaNomeArquivo(self):
        arq = f"{self.dict_tipo[self.tipo]}{self.refdate.strftime('%Y%m%d')} .xls"
        arq_corrigido = f"{self.dict_tipo[self.tipo]}{self.refdate.strftime('%Y%m%d')}.html"
        os.rename(os.path.join(self.path_download, arq), os.path.join(self.path_download, arq_corrigido))  # noqa: F403, F405, E402

    def moveArquivo(self):

        source_file = os.path.join(self.path_download, self.arq)  # noqa: F403, F405, E402

        if not self.funcoes_pytools.checkFileExists(self.destination_file):
            shutil.move(source_file, self.destination_file)

    def downloadArquivo(self):

        self.driver.get(self.url)

        try:
            self.driver.find_element(By.XPATH, "/html/body/form/table[2]/tbody/tr/td/b")
            return False
        except:  # noqa: F403, F405, E402, E722
            download_button = self.driver.find_element(By.XPATH, "/html/body/form/table[1]/tbody/tr[2]/td[2]/img")
            download_button.click()
            self.check_download = self.verificaDownload()
            return True

    def captDataframe(self):

        dfs = pd.read_html(self.destination_file, decimal=',', thousands='.')
        self.df = dfs[0]
        self.df.columns = ['DIAS_CORRIDOS', 'DI_252', 'DI_360']
        self.df = self.df[['DIAS_CORRIDOS', 'DI_252']].copy()
        self.df = self.df[self.df['DIAS_CORRIDOS'].notna()]
        self.df = self.df[self.df['DIAS_CORRIDOS'] != 'Dias Corridos']
        self.df['DIAS_CORRIDOS'] = self.df['DIAS_CORRIDOS'].astype(int)
        self.df['DI_252'] = self.df['DI_252'].astype(float)

        self.df.insert(0, 'REFDATE', self.refdate)
        self.df.insert(1, 'CURVA', self.tipo)
        self.df['FONTE'] = 'B3'
        self.df = self.df.rename(columns={'DI_252': 'TAXA_252'}).sort_values(by='DIAS_CORRIDOS')

    def uploadBase(self):

        self.manager_sql.delete_records(
            'TB_CURVAS', f"REFDATE = '{self.refdate.strftime('%Y-%m-%d')}' AND CURVA = '{self.tipo}' AND FONTE = 'B3'")
        self.manager_sql.insert_dataframe(self.df, 'TB_CURVAS')

    def call_processo(self):

        if not self.funcoes_pytools.checkFileExists(self.destination_file):
            try:
                self.url = self.urlDownload()
                if self.downloadArquivo():
                    self.moveArquivo()
                    self.captDataframe()
                    self.uploadBase()
                else:
                    return 'Arquivo não encontrado'
            except Exception as e:
                return e
        else:
            self.captDataframe()
            self.uploadBase()
        return 'ok'

    def check_need_download(self):

        for tipo in self.dict_tipo:
            arq = f"{self.dict_tipo[tipo]}{self.refdate.strftime('%Y%m%d')}.html"
            destination_file = os.path.join(self.path_to_move, arq)  # noqa: F403, F405, E402
            if not self.funcoes_pytools.checkFileExists(destination_file):
                return True

        return False

    def run(self, refdate: date, p_webdriver=None):

        self.set_refdate(refdate)

        check_sql_uploaded = self.check_sql_uploaded()

        if check_sql_uploaded is not True:

            results = {}

            if p_webdriver is None:
                self.service = Service(EdgeChromiumDriverManager().install())
                self.driver = webdriver.Edge(service=self.service)
            else:
                self.driver = p_webdriver

            for tipo in self.dict_tipo:

                if tipo in check_sql_uploaded:
                    self.tipo = tipo
                    self.arq = f"{self.dict_tipo[self.tipo]}{self.refdate.strftime('%Y%m%d')}.html"
                    self.destination_file = os.path.join(self.path_to_move, self.arq)  # noqa: F403, F405, E402
                    results[self.tipo] = f"{self.call_processo()}"
                else:
                    results[self.tipo] = "Baixado anteriormente."

            if p_webdriver is None:
                self.driver.quit()

            return results
        else:
            return 'all_uploaded'


class dadosB3():

    def __init__(self, manager_sql=None, funcoes_pytools=None, logger=None):

        if manager_sql is None:
            self.manager_sql = SQL_Manager()
        else:
            self.manager_sql = manager_sql

        if funcoes_pytools is None:
            self.funcoes_pytools = FuncoesPyTools(self.manager_sql)
        else:
            self.funcoes_pytools = funcoes_pytools

        if logger is None:
            self.logger = Logger(self.manager_sql)
        else:
            self.logger = logger

        self.logger.info(
            log_message=f"dadosB3 - {VERSION_APP} - {ENVIRONMENT} - Instanciado",
            script_original=SCRIPT_NAME
        )

        self.tb_indexadores = 'TB_INDEXADORES'

        self.str_url = (
            "http://estatisticas.cetip.com.br/astec/series_v05/paginas/lum_web_v05_template_informacoes_di.asp?"
            "str_Modulo=completo&int_Idioma=1&int_Titulo=6&int_NivelBD=2")

    def set_refdate(self, refdate: date):
        self.refdate = refdate

    def open_edge(self):

        self.service = Service(EdgeChromiumDriverManager().install())
        self.driver = webdriver.Edge(service=self.service)

    def check_last_date_cdi_selic_b3(self, refdate: date = None, manual_check=False):
        if manual_check and refdate is None:
            return 'Refdate deve ser preenchido.'
        elif manual_check and refdate is not None:
            self.refdate = refdate
            self.open_edge()

        self.driver.get(self.str_url)

        try:
            last_date_disp = datetime.strptime(
                self.driver.find_element(By.XPATH, '//*[@id="col_esq"]/div/form/div[2]/div/label').get_property("innerText")[-10:],
                '%d/%m/%Y'
            ).date()
        except Exception:
            return False

        if last_date_disp >= self.refdate:
            if manual_check:
                self.driver.quit()
            return True
        else:
            if manual_check:
                self.driver.quit()
            return False

    def scrapping_cdi_selic_b3(self):

        def dividir_lista_em_blocos(list_values, len_bloco):
            """
            Divide uma lista em blocos de um tamanho específico, remove espaços em branco de cada elemento
            e converte os elementos das posições especificadas para float.

            :param lista: A lista original a ser dividida.
            :param tamanho_bloco: O tamanho de cada bloco.
            :return: Uma lista de listas, onde cada sublista tem o tamanho especificado.
            """
            # Remove espaços em branco de cada elemento da lista
            lista_sem_espacos = [item.strip() for item in list_values]

            # Divide a lista sem espaços em blocos de tamanho específico
            listas_divididas = [lista_sem_espacos[i:i + len_bloco] for i in range(0, len(lista_sem_espacos), len_bloco)]

            # Converter os elementos nas posições 3, 4 e 5 para float
            for sublista in listas_divididas:
                sublista[3] = float(sublista[3].replace(',', '.'))
                sublista[4] = float(sublista[4].replace(',', '.'))
                sublista[5] = float(sublista[5].replace(',', '.'))

            return listas_divididas

        self.start_day_b3 = self.driver.find_element(By.NAME, "DT_DIA_DE")
        self.start_month_b3 = self.driver.find_element(By.NAME, "DT_MES_DE")
        self.start_year_b3 = self.driver.find_element(By.NAME, "DT_ANO_DE")

        self.last_day_b3 = self.driver.find_element(By.NAME, "DT_DIA_ATE")
        self.last_month_b3 = self.driver.find_element(By.NAME, "DT_MES_ATE")
        self.last_year_b3 = self.driver.find_element(By.NAME, "DT_ANO_ATE")

        self.check_media = self.driver.find_element(By.NAME, "chk_M1")
        self.check_selic = self.driver.find_element(By.NAME, "chk_M6")

        self.btn_limpar = self.driver.find_element(By.XPATH, '//*[@id="col_esq"]/div/form/div[6]/div/a[1]')
        self.btn_pesquisar = self.driver.find_element(By.XPATH, '//*[@id="col_esq"]/div/form/div[6]/div/a[2]')

        self.btn_limpar.click()
        self.check_media.click()
        self.check_selic.click()

        self.start_day_b3.clear()
        self.start_month_b3.clear()
        self.start_year_b3.clear()

        self.last_day_b3.clear()
        self.last_month_b3.clear()
        self.last_year_b3.clear()

        self.start_day_b3.send_keys(self.refdate.strftime('%d'))
        self.start_month_b3.send_keys(self.refdate.strftime('%m'))
        self.start_year_b3.send_keys(self.refdate.strftime('%Y'))

        self.last_day_b3.send_keys(self.refdate.strftime('%d'))
        self.last_month_b3.send_keys(self.refdate.strftime('%m'))
        self.last_year_b3.send_keys(self.refdate.strftime('%Y'))

        self.btn_pesquisar.click()

        values_table = self.driver.find_elements(By.CSS_SELECTOR, '[class^="ConsultaDados_R"]')
        list_values = []
        for element in values_table:
            list_values.append(element.text)

        list_dados_cdi_selic_b3 = dividir_lista_em_blocos(list_values, 6)

        for dados in list_dados_cdi_selic_b3:
            if datetime.strptime(dados[0], '%d/%m/%Y').date() == self.refdate:
                self.cdi_ano = round(dados[3] / 100, 9)
                self.cdi_dia = round(dados[4] - 1, 11)
                self.selic_ano = round(dados[5] / 100, 9)
                self.selic_dia = round((1 + self.selic_ano) ** (1 / 252) - 1, 7)
                break

    def upload_cdi_b3(self):

        dmenos1 = self.funcoes_pytools.workday_br(self.refdate, -1)

        cota_cdi_dmenos1 = self.manager_sql.select_dataframe(
            f"SELECT COTA_INDEXADOR FROM {self.tb_indexadores} "
            f"WHERE INDEXADOR = 'CDI' AND REFDATE = '{self.funcoes_pytools.convert_data_sql(dmenos1)}'")

        if len(cota_cdi_dmenos1) == 0:
            self.result_scrapping_cdi_selic_b3['CDI'] = "Cota CDI dmenos1 indisponivel"
        else:
            cota_cdi_dmenos1 = cota_cdi_dmenos1['COTA_INDEXADOR'][0]

            cota_cdi_d0 = cota_cdi_dmenos1 * (1 + self.cdi_dia)

            df_cdi_d0 = pd.DataFrame({
                'REFDATE': [self.refdate],
                'INDEXADOR': ['CDI'],
                'VALOR_ANO': [self.cdi_ano],
                'VALOR_DIA': [self.cdi_dia],
                'COTA_INDEXADOR': [cota_cdi_d0]
            })

            self.manager_sql.delete_records(
                self.tb_indexadores, f"REFDATE = '{self.funcoes_pytools.convert_data_sql(self.refdate)}' AND INDEXADOR = 'CDI'")
            self.manager_sql.insert_dataframe(df_cdi_d0, self.tb_indexadores)
            self.result_scrapping_cdi_selic_b3['CDI'] = "Upload ok!"

    def upload_selic_b3(self):

        dmenos1 = self.funcoes_pytools.workday_br(self.refdate, -1)

        cota_selic_dmenos1 = self.manager_sql.select_dataframe(
            f"SELECT COTA_INDEXADOR FROM {self.tb_indexadores} "
            f"WHERE INDEXADOR = 'SELIC' AND REFDATE = '{self.funcoes_pytools.convert_data_sql(dmenos1)}'")

        if len(cota_selic_dmenos1) == 0:
            self.result_scrapping_cdi_selic_b3['SELIC'] = "Cota SELIC dmenos1 indisponivel"
        else:
            cota_selic_dmenos1 = cota_selic_dmenos1['COTA_INDEXADOR'][0]

            cota_selic_d0 = cota_selic_dmenos1 * (1 + self.selic_dia)

            df_selic_d0 = pd.DataFrame({
                'REFDATE': [self.refdate],
                'INDEXADOR': ['SELIC'],
                'VALOR_ANO': [self.cdi_ano],
                'VALOR_DIA': [self.cdi_dia],
                'COTA_INDEXADOR': [cota_selic_d0]
            })

            self.manager_sql.delete_records(
                self.tb_indexadores, f"REFDATE = '{self.funcoes_pytools.convert_data_sql(self.refdate)}' AND INDEXADOR = 'SELIC'")
            self.manager_sql.insert_dataframe(df_selic_d0, self.tb_indexadores)
            self.result_scrapping_cdi_selic_b3['SELIC'] = "Upload ok!"

    def check_if_sql_uploaded(self):

        str_cdi_selic = "'CDI', 'SELIC'"

        lista_sql = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT INDEXADOR AS INDEXADORES FROM {self.tb_indexadores} "
            f"WHERE REFDATE = '{self.funcoes_pytools.convert_data_sql(self.refdate)}' "
            f"AND INDEXADOR IN ({str_cdi_selic})")['INDEXADORES'].tolist()

        check_cdi_sql = set(['CDI', 'SELIC']).issubset(lista_sql)

        if check_cdi_sql is True:
            return True
        else:
            return [item for item in set(['CDI', 'SELIC']) if item not in lista_sql]

    def run_scrapping_cdi_selic_b3(self, refdate, p_webdriver=None):

        self.set_refdate(refdate)

        # check_sql_uploaded = self.check_if_sql_uploaded()

        # if check_sql_uploaded is not True:

        if p_webdriver is None:
            self.open_edge()
        else:
            self.driver = p_webdriver

        self.result_scrapping_cdi_selic_b3 = {}

        if self.check_last_date_cdi_selic_b3(manual_check=False):
            self.scrapping_cdi_selic_b3()
            if p_webdriver is None:
                self.driver.quit()
            self.upload_cdi_b3()
            self.upload_selic_b3()
        else:
            if p_webdriver is None:
                self.driver.quit()
            self.result_scrapping_cdi_selic_b3['Scrapping'] = (
                f"{self.funcoes_pytools.convert_data_sql(self.refdate)} não disponível na B3")
        return self.result_scrapping_cdi_selic_b3
        # else:
            # return 'all_uploaded'


class agendaDebenturesAnbima():

    def __init__(self, manager_sql=None):

        if manager_sql is None:
            self.manager_sql = SQL_Manager()
        else:
            self.manager_sql = manager_sql

        self.funcoes_pytools = FuncoesPyTools(self.manager_sql)

        self.dict_vne = self.manager_sql.select_dataframe(
            "SELECT DISTINCT ATIVO, VNE FROM TB_CADASTRO_ATIVOS WHERE TIPO_ATIVO = 'DEBÊNTURE'")\
            .set_index('ATIVO')['VNE'].to_dict()

        self.service = Service(EdgeChromiumDriverManager().install())

        self.xpath_tabela = '//*[@id="root"]/main/div[3]/main/div/article/article/section/div/div[1]/table/tbody'

    def convert_percentual(self, x):
        return float(x[:-2].replace(',', '.'))

    def convert_valor_pago(self, x):
        if x == '-':
            return None
        else:
            x = x.replace('.', '')
            return float(x[3:].replace(',', '.'))

    def captura_lista_ativos(self, refdate: date = None, lista_ativos: list = None):
        if refdate is None:
            refdate = self.refdate
        else:
            refdate = refdate

        if lista_ativos is None:
            lista_ativos = self.manager_sql.select_dataframe(
                f"SELECT DISTINCT ATIVO FROM TB_CARTEIRAS "
                f"WHERE REFDATE = '{self.funcoes_pytools.convert_data_sql(refdate)}' "
                f"AND TIPO_ATIVO = 'Debênture' AND FINANCEIRO_D0 <> 0")['ATIVO'].tolist()
        else:
            lista_ativos = lista_ativos

        self.ativos = lista_ativos
        self.ativos_str = ', '.join([f"'{ativo}'" for ativo in self.ativos])

    def cria_vna(self, df, vna):
        df = df.loc[:, ['ATIVO', 'DATA_LIQUIDACAO', 'PERCENTUAL']].copy()

        if len(df) == 1:
            df['VNA'] = vna
            df = df[['ATIVO', 'DATA_LIQUIDACAO', 'VNA']]
            return df
        elif len(df) == 0:
            df = df[['ATIVO', 'DATA_LIQUIDACAO', 'VNA']]
            return df
        else:
            for i in range(len(df)):
                if i == 0:
                    df.loc[i, 'VNA'] = vna
                else:
                    df.loc[i, 'VNA'] = round(df.loc[i - 1, 'VNA'] * (1 - df.loc[i - 1, 'PERCENTUAL'] / 100), 7)
            df = df[['ATIVO', 'DATA_LIQUIDACAO', 'VNA']]
            return df

    def set_refdate(self, refdate):
        self.refdate = refdate

    def base_url(self, ativo):
        return f"https://data.anbima.com.br/debentures/{ativo}/agenda?page=1&size=100&"

    def captura_agendas_anbima(self):

        print("Capturando agendas Anbima...")
        driver = webdriver.Edge(service=self.service)

        self.dados = []

        for ativo in self.ativos:
            driver.get(self.base_url(ativo))
            print("Sleeping 20s...")
            time.sleep(20)
            try:
                tabela = driver.find_element(By.XPATH, self.xpath_tabela)
            except Exception as e:  # noqa: F841
                print(self.base_url(ativo))
                print("")
                input(f"Erro ao buscar ativo {ativo}. Aperte enter para continuar")

                tabela = driver.find_element(By.XPATH, self.xpath_tabela)

            linhas = tabela.find_elements(By.TAG_NAME, "tr")
            for linha in linhas:
                colunas = linha.find_elements(By.TAG_NAME, "td")
                dados_linha = [coluna.text for coluna in colunas]
                dados_linha.append(ativo)
                self.dados.append(dados_linha)

        driver.quit()

        print("Captura agenda Anbima finalizada")

    def tratamento_dados_agenda_abima(self):

        print("Tratando dados agenda Anbima...")
        df = pd.DataFrame(self.dados, columns=['DATA_EVENTO', 'DATA_LIQUIDACAO', 'EVENTO', 'PERCENTUAL', 'VALOR_PAGO', 'STATUS', 'ATIVO'])
        df['PERCENTUAL'] = df['PERCENTUAL'].map(self.convert_percentual)
        df['VALOR_PAGO'] = df['VALOR_PAGO'].map(self.convert_valor_pago)
        df = df[['DATA_EVENTO', 'DATA_LIQUIDACAO', 'EVENTO', 'PERCENTUAL', 'VALOR_PAGO', 'ATIVO']]

        df_list = []

        for ativo in self.ativos:
            df_vna = df[(df['ATIVO'] == ativo) &  # noqa: F403, F405, E402, W504
                    ((df['EVENTO'] == 'Amortizacao') |  # noqa: F403, F405, E402, W504
                    (df['EVENTO'] == 'Vencimento (resgate)') |  # noqa: E501, F405, E402, W504
                    (df['EVENTO'] == 'Resgate total antecipado'))][['ATIVO', 'DATA_LIQUIDACAO', 'PERCENTUAL']].reset_index(drop=True)  # noqa: E501, F405, E402, W504

            df_vna = self.cria_vna(df_vna, self.dict_vne[ativo])

            df_ativo = df[df['ATIVO'] == ativo].copy()
            df_ativo = pd.merge(df_ativo, df_vna, on=['DATA_LIQUIDACAO', 'ATIVO'], how='left')
            df_ativo['VNA'] = df_ativo['VNA'].bfill()

            df_list.append(df_ativo)

        self.df_ativos = pd.concat(df_list, ignore_index=True)

        self.df_ativos['TIPO_ATIVO'] = 'Debênture'

        for coluna in ['DATA_EVENTO', 'DATA_LIQUIDACAO']:
            self.df_ativos[coluna] = pd.to_datetime(self.df_ativos[coluna], format='%d/%m/%Y')

        self.df_ativos = self.df_ativos[[
            'TIPO_ATIVO', 'ATIVO', 'DATA_EVENTO', 'DATA_LIQUIDACAO', 'EVENTO', 'PERCENTUAL', 'VALOR_PAGO', 'VNA']]

        self.df_ativos.insert(0, 'REFDATE', self.refdate)

        print("Tratamento de dados finalizado")

    def upload_agenda_anbima(self):

        print("Upload agenda Anbima...")

        self.manager_sql.delete_records('TB_FLUXO_PAGAMENTO_ATIVOS_REFDATE',
            f"REFDATE = '{self.funcoes_pytools.convert_data_sql(self.refdate)}' "
            f"AND ATIVO IN ({self.ativos_str})")

        self.manager_sql.insert_dataframe(self.df_ativos, 'TB_FLUXO_PAGAMENTO_ATIVOS_REFDATE')

        print("Upload finalizado")

    def run(self, refdate, lista_ativos: list = None):

        print("Iniciando processo de captura de agendas Anbima...")

        self.set_refdate(refdate)

        self.captura_lista_ativos(lista_ativos=lista_ativos)

        self.captura_agendas_anbima()

        self.tratamento_dados_agenda_abima()

        self.upload_agenda_anbima()

        print("Processo finalizado")
