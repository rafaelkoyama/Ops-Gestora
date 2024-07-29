import threading
from datetime import date, datetime, timedelta
from time import sleep

import pandas as pd
from __init__ import *  # noqa: F403, F405, E402
from ttkbootstrap import Toplevel, Window
from ttkbootstrap.dialogs.dialogs import Messagebox, Querybox
from ttkbootstrap.tableview import Tableview

append_paths()  # noqa: F403, F405, E402

from btg_faas.new_btg_api_reports import BTGReports  # noqa: F403, F405, E402
from controlPanel.biblioteca_widgets import (  # noqa: F403, F405, E402
    newBooleanVar,
    newButton,
    newCheckButton,
    newDateEntry,
    newFrame,
    newLabelFrame,
    newLabelStatus,
    newLabelSubtitle,
    newLabelTitle,
    newMenu,
    newMenuButton,
    newProgressBar,
    newScrolledText,
    newSpinBox,
    newStringVar,
    newWindowStatus,
)
from controlPanel.sistemaCadastro import TelaCadastro  # noqa: F403, F405, E402
from controlPanel.webScrapping import (  # noqa: F403, F405, E402
    curvasB3,
    dadosB3,
    debenturesAnbima,
    openEdgeDriver,
)
from risco.calculadoraRisco import calculadoraAtivos  # noqa: F403, F405, E402
from tools.biblioteca_processos import (  # noqa: F403, F405, E402
    UpdateIndexadores,
    UploadArquivosXML,
)
from tools.db_helper import SQL_Manager  # noqa: F403, F405, E402
from tools.my_logger import Logger  # noqa: F403, F405, E402
from tools.py_tools import FuncoesPyTools, OutlookHandler  # noqa: F403, F405, E402

# -------------------------------------------------------------------------------------------------------

VERSION_APP = "2.3.1"
VERSION_REFDATE = "2024-07-10"
ENVIRONMENT = os.getenv("ENVIRONMENT")  # noqa: F403, F405, E402
SCRIPT_NAME = os.path.basename(__file__)  # noqa: F403, F405, E402
CONNECT_MANAGER_BTG = True

if ENVIRONMENT == "DEVELOPMENT":
    print(f"{SCRIPT_NAME.upper()} - {ENVIRONMENT} - {VERSION_APP} - {VERSION_REFDATE}")

# -------------------------------------------------------------------------------------------------------

base_path_carteiras = f"C:\\Users\\{str_user}\\Strix Capital\\Backoffice - General\\Carteiras"  # noqa: F403, F405, E402


class ProcessManagerAutoOpen:

    def __init__(self, app):

        self.app = app
        self.manager_sql = self.app.manager_sql
        self.funcoes_pytools = self.app.funcoes_pytools
        self.manager_outlook = self.app.manager_outlook

        self.refdate = self.app.refdate
        self.dmenos1 = self.funcoes_pytools.workday_br(self.refdate, -1)

        self.lista_processos_app = self.app.lista_processos_app

        self.update_controle_processos()
        self.passivos_a_cotizar()

    def update_controle_processos(self):

        for processo in self.lista_processos_app:
            if not self.manager_sql.check_if_data_exists(
                    f"SELECT * FROM TB_AUX_CONTROL_PANEL_CONTROLE_PROCESSOS "
                    f"WHERE REFDATE = '{self.dmenos1}' AND PROCESSO = '{processo}'"):
                self.manager_sql.insert_manual(
                    table_name="TB_AUX_CONTROL_PANEL_CONTROLE_PROCESSOS",
                    list_columns=['REFDATE', 'PROCESSO', 'STATUS'],
                    list_values=[self.dmenos1, processo, '0'])

    def passivos_a_cotizar(self):

        refdate = date.today()

        if not self.manager_sql.check_if_data_exists(
                f"SELECT * FROM TB_AUX_CONTROL_PANEL_CONTROLE_PROCESSOS "
                f"WHERE REFDATE = '{refdate}' AND PROCESSO = 'OPEN_CHECK_PASSIVOS_A_COTIZAR'"):

            df_movs_cotizar = self.manager_sql.select_dataframe(
                f"SELECT * FROM TB_BASE_BTG_MOVIMENTACAO_PASSIVO "
                f"WHERE DATA_COTIZACAO = '{refdate}' AND FUNDO NOT IN ('STRIX YIELD MASTER F') "
                f"AND TIPO_OPERACAO = 'RESGATE' AND DATA_COTIZACAO <> DATA_OPERACAO "
                f"AND STATUS_OPERACAO NOT IN ('Excluido') "
                f"ORDER BY FUNDO")

            if len(df_movs_cotizar) > 0:

                fundos = df_movs_cotizar['FUNDO'].unique()

                dict_last_cota = {}

                for fundo in fundos:
                    dict_last_cota[fundo] = self.manager_sql.select_dataframe(
                        f"SELECT COTA FROM TB_XML_CARTEIRAS_HEADER WHERE FUNDO = '{fundo}' AND "
                        f"REFDATE = (SELECT MAX(REFDATE) FROM TB_XML_CARTEIRAS_HEADER WHERE FUNDO = '{fundo}')")['COTA'][0]

                df_movs_cotizar['COTA'] = df_movs_cotizar['FUNDO'].map(dict_last_cota)

                df_movs_cotizar['VALOR'] = df_movs_cotizar.apply(
                    lambda x: x['COTA'] * x['QTD_COTAS'] if x['DESC_TIPO_OPERACAO'] == 'RESGATE TOTAL' else x['VALOR'], axis=1)

                df_movs_total = df_movs_cotizar[['FUNDO', 'VALOR', 'QTD_COTAS']].groupby(['FUNDO']).sum().reset_index()

                for row in df_movs_total.itertuples(index=False):
                    str_body_fundos = (
                        f"{row.FUNDO}\n"
                        f"Valor total Resgate: {row.VALOR:,.2f}\n"
                        f"Qtd. Total Cotas: {row.QTD_COTAS:,.7f}\n\n"
                    )

                for row in df_movs_cotizar.itertuples(index=False):
                    str_body_movs = (
                        f"Fundo: {row.FUNDO}\n"
                        f"Data Operação: {row.DATA_OPERACAO.strftime('%d/%m/%Y')}\n"
                        f"Data Cotização: {row.DATA_COTIZACAO.strftime('%d/%m/%Y')}\n"
                        f"Data Liquidação: {row.DATA_IMPACTO.strftime('%d/%m/%Y')}\n"
                        f"Cotista: {row.COTISTA}\n"
                        f"Tipo Resgate: {row.DESC_TIPO_OPERACAO}\n"
                        f"Valor: {row.VALOR:,.2f}\n"
                        f"Qtd. Cotas: {row.QTD_COTAS:,.7f}\n"
                        f"Plataforma: {row.PLATAFORMA}\n"
                        f"Officer: {row.OFFICER}\n"
                        f"ID BTG: {row.ID_BTG}\n\n"
                    )

                str_head = (
                    "Mensagem automática.\n\n"
                    "## Resumo Fundos ##\n\n"
                )

                str_head_fundos = (
                    "## Resgates ##\n\n"
                )

                str_body = str_head + str_body_fundos + str_head_fundos + str_body_movs

                if ENVIRONMENT == "DEVELOPMENT":
                    to_lista = [os.getenv("EMAIL_ME")]  # noqa: F403, F405, E402
                else:
                    to_lista = [os.getenv("EMAIL_BO")]  # noqa: F403, F405, E402

                self.manager_outlook.send_email(
                    to_list=to_lista,
                    subject=f"Passivos a Cotizar: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                    msg_body=str_body,
                    sendBehalf=os.getenv("EMAIL_ROBO"),  # noqa: F403, F405, E402
                    importance=2)

            self.manager_sql.insert_manual(
                table_name="TB_AUX_CONTROL_PANEL_CONTROLE_PROCESSOS",
                list_columns=['REFDATE', 'PROCESSO', 'STATUS'],
                list_values=[refdate, 'OPEN_CHECK_PASSIVOS_A_COTIZAR', '1'])


class ProcessManager:

    def __init__(self, app):

        super().__init__()

        if ENVIRONMENT == "DEVELOPMENT":
            self.tb_indexadores = 'TB_INDEXADORES_TESTE'
        else:
            self.tb_indexadores = 'TB_INDEXADORES'

        self.app = app

        self.manager_sql = self.app.manager_sql

        self.funcoes_pytools = self.app.funcoes_pytools

        self.manager_btg = self.app.manager_btg

        self.logger = self.app.logger

        self.debenturesAnbima = debenturesAnbima(manager_sql=self.manager_sql, funcoes_pytools=self.funcoes_pytools, logger=self.logger)
        self.curvasb3 = curvasB3(manager_sql=self.manager_sql, funcoes_pytools=self.funcoes_pytools, logger=self.logger)
        self.dadosB3 = dadosB3(manager_sql=self.manager_sql, funcoes_pytools=self.funcoes_pytools, logger=self.logger)
        self.calculadora = calculadoraAtivos(manager_sql=self.manager_sql, funcoes_pytools=self.funcoes_pytools, logger=self.logger)
        self.manager_xml = UploadArquivosXML(manager_sql=self.manager_sql, funcoes_pytools=self.funcoes_pytools, logger=self.logger)

        self.fundos_btg = self.manager_btg.list_funds
        self.fundos_all = self.fundos_btg.copy()
        self.fundos_all.append('STRIX KINEA INFRA')

        self.tipos_carteiras_btg = self.manager_btg.tipos_carteiras_btg

        self.dict_icons_status = {
            'ok': '✅',
            'not': '❌',
            'warning': '⚠️'
        }

        self.window_status_outras_bases = None
        self.window_status_bases_carteiras = None

    def call_status_all_bases(self):

        self.status_bases()
        self.check_bases_calculadora()

    def btgFundsPerfNav(self):

        self.window_status_bases_carteiras.text_box.insert("end", "Rodando: BTG Funds Perf NAV\n")

        lista_fundos_sql = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT FUNDO AS FUNDOS FROM TB_BASE_BTG_PERFORMANCE_COTA "
            f"WHERE REFDATE = '{self.funcoes_pytools.convert_data_sql(self.refdate_upload_bases_carteiras)}'")['FUNDOS'].tolist()

        for fundo in self.fundos_btg:
            if fundo in lista_fundos_sql:
                self.window_status_bases_carteiras.text_box.insert("end", f"  {fundo}: Já baixado anteriormente.\n")
            else:
                if self.dict_status_carteiras_bases_btg[fundo] == 'Liberados':
                    results = self.manager_btg.funds_nav_performance(fund_name=fundo, refdate=self.refdate_upload_bases_carteiras)
                    if results[fundo] == 'ok':
                        self.window_status_bases_carteiras.text_box.insert("end", f"  {fundo}: Perf Nav baixado.\n")
                    else:
                        self.window_status_bases_carteiras.text_box.insert("end", f"  {fundo}: {results[fundo]}\n")
                else:
                    self.window_status_bases_carteiras.text_box.insert("end", f"  {fundo}: Carteira não liberada.\n")

        self.window_status_bases_carteiras.text_box.insert("end", "\n")

    def updateIndexadores(self):

        self.window_status_bases_carteiras.text_box.insert("end", "Rodando: Update Indexadores\n")

        results = UpdateIndexadores(
            refdate=self.refdate_upload_bases_carteiras,
            manager_sql=self.manager_sql,
            funcoes_pytools=self.funcoes_pytools).run()

        for indexador in results:
            if results[indexador] == 'ok':
                self.window_status_bases_carteiras.text_box.insert("end", f"  {indexador}: Sucesso!\n")
            else:
                self.window_status_bases_carteiras.text_box.insert("end", f"  {indexador}: {results[indexador]}\n")
        self.window_status_bases_carteiras.text_box.insert("end", "\n")

    def btgFundsPerfCotistas(self):

        self.window_status_bases_carteiras.text_box.insert("end", "Rodando: BTG Perfornace Cotistas\n")

        lista_fundos_sql = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT FUNDO AS FUNDOS FROM TB_BASE_BTG_PERFORMANCE_COTISTAS "
            f"WHERE REFDATE = '{self.funcoes_pytools.convert_data_sql(self.refdate_upload_bases_carteiras)}'")['FUNDOS'].tolist()

        for fundo in self.fundos_btg:
            if fundo in lista_fundos_sql:
                self.window_status_bases_carteiras.text_box.insert("end", f"  {fundo}: Já baixado anteriormente.\n")
            else:
                if self.dict_status_carteiras_bases_btg[fundo] == 'Liberados':
                    results = self.manager_btg.funds_performance_cotistas(fund_name=fundo, refdate=self.refdate_upload_bases_carteiras)
                    if results[fundo] == 'ok':
                        self.window_status_bases_carteiras.text_box.insert("end", f"  {fundo}: Perf cotistas baixado.\n")
                    else:
                        self.window_status_bases_carteiras.text_box.insert("end", f"  {fundo}: {results[fundo]}\n")
                else:
                    self.window_status_bases_carteiras.text_box.insert("end", f"  {fundo}: Carteira não liberada.\n")

        self.window_status_bases_carteiras.text_box.insert("end", "\n")

    def btgFundsAdmCotistas(self):

        self.window_status_bases_carteiras.text_box.insert("end", "Rodando: BTG Adm Cotistas\n")

        lista_fundos_sql = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT FUNDO AS FUNDOS FROM TB_BASE_BTG_TX_ADM_COTISTAS "
            f"WHERE REFDATE = '{self.funcoes_pytools.convert_data_sql(self.refdate_upload_bases_carteiras)}'")['FUNDOS'].tolist()

        for fundo in self.fundos_btg:
            if fundo in lista_fundos_sql:
                self.window_status_bases_carteiras.text_box.insert("end", f"  {fundo}: Já baixado anteriormente.\n")
            else:
                if self.dict_status_carteiras_bases_btg[fundo] == 'Liberados':
                    results = self.manager_btg.funds_managementfee_cotistas(fund_name=fundo, refdate=self.refdate_upload_bases_carteiras)
                    if results[fundo] == 'ok':
                        self.window_status_bases_carteiras.text_box.insert("end", f"  {fundo}: Adm cotistas baixado.\n")
                    else:
                        self.window_status_bases_carteiras.text_box.insert("end", f"  {fundo}: {results[fundo]}\n")
                else:
                    self.window_status_bases_carteiras.text_box.insert("end", f"  {fundo}: Carteira não liberada.\n")

        self.window_status_bases_carteiras.text_box.insert("end", "\n")

    def btgFundsDownloadCarteiras(self):

        self.window_status_bases_carteiras.text_box.insert("end", "Rodando: Download Carteiras BTG")

        for fundo in self.fundos_btg:
            if self.dict_status_carteiras_bases_btg[fundo] == 'Aguardando aprovação'\
                    or self.dict_status_carteiras_bases_btg[fundo] == 'Liberados':
                self.window_status_bases_carteiras.text_box.insert("end", f"\n  Fundo: {fundo}\n")
                for tipo in self.tipos_carteiras_btg:
                    self.window_status_bases_carteiras.text_box.insert(
                        "end", f"    {self.manager_btg.download_carteiras(
                            fundo=fundo, tipo_arq=tipo, refdate=self.refdate_upload_bases_carteiras)}\n")
            else:
                self.window_status_bases_carteiras.text_box.insert("end", f"\n  {fundo}: Carteira não liberada.\n")

        self.window_status_bases_carteiras.text_box.insert("end", "\n")

    def runCapturaArquivosEmail(self):

        self.window_status_bases_carteiras.text_box.insert("end", "Rodando: Arquivos email\n")
        self.capturaXmlKinea()
        self.capturaArquivosMasterFIA()
        self.capturaXmlYieldMastercc()

        self.window_status_bases_carteiras.text_box.insert("end", "\n")

    def capturaXmlKinea(self):

        refdate = self.refdate_upload_bases_carteiras
        str_kinea_infra_carteira = "Strix Kinea Infra"
        str_carteira_xml_to_find = f"FD54794777000102_{refdate.strftime('%Y%m%d')}"
        ext_carteira = "xml"
        str_file_carteira = f"STRIX_KINEA_INFRA_{refdate.strftime('%Y%m%d')}.xml"
        file_to_save = os.path.join(  # noqa: F403, F405, E402
            base_path_carteiras, str_kinea_infra_carteira, ext_carteira, str_file_carteira)

        if self.funcoes_pytools.checkFileExists(file_to_save):
            self.window_status_bases_carteiras.text_box.insert("end", "  Carteira Strix Kinea Infra: Arquivo já baixado anteriormente.\n")
        else:

            if self.app.manager_outlook.save_attachments_from_folder(
                    name_folder=str_kinea_infra_carteira,
                    refdate_email=refdate,
                    str_to_find_attachment=str_carteira_xml_to_find,
                    str_endswith=f".{ext_carteira}",
                    str_to_save_attchament=file_to_save):
                self.window_status_bases_carteiras.text_box.insert("end", "  Carteira Strix Kinea Infra: salvo na pasta.\n")
            else:
                self.window_status_bases_carteiras.text_box.insert("end", "  Carteira Strix Kinea Infra: não encontrado.\n")

    def capturaArquivosMasterFIA(self):

        refdate = self.refdate_upload_bases_carteiras

        # Extrato Conta corrente:
        pasta_arquivo = "STRIX MASTER FIA CC"
        str_arquivo_to_find = f"5218073_{self.funcoes_pytools.workday_br(refdate, 1).strftime('%Y-%m-%d')}"
        ext_arquivo = "xml"
        str_file_name = f"{str_arquivo_to_find}.xml"
        file_to_save = os.path.join(  # noqa: F403, F405, E402
            base_path_carteiras, "Strix Master FIA", "Conta Corrente", str_file_name)

        if self.funcoes_pytools.checkFileExists(file_to_save):
            self.window_status_bases_carteiras.text_box.insert("end", "  Extrato CC Strix Master FIA: Arquivo já baixado anteriormente.\n")
        else:
            if self.app.manager_outlook.save_attachments_from_folder(
                    name_folder=pasta_arquivo,
                    refdate_email=refdate,
                    str_to_find_attachment=str_arquivo_to_find,
                    str_endswith=f".{ext_arquivo}",
                    str_to_save_attchament=file_to_save):
                self.window_status_bases_carteiras.text_box.insert("end", "  Extrato CC Strix Master FIA: Arquivo salvo na pasta.\n")
            else:
                self.window_status_bases_carteiras.text_box.insert("end", "  Extrato CC Strix Master FIA: Arquivo não encontrado.\n")

        # Carteiras:

        # xml:
        pasta_arquivo = "Strix Master FIA"
        str_arquivo_to_find = f"ResumoCarteira_STRIX MASTER FC FIA_{refdate.strftime('%Y%m%d')}"
        ext_arquivo = "xml"
        str_file_name = f"STRIX_MASTER_FIA_{refdate.strftime('%Y%m%d')}.xml"
        file_to_save = os.path.join(  # noqa: F403, F405, E402
            base_path_carteiras, "Strix Master FIA", "xml", str_file_name)

        if self.funcoes_pytools.checkFileExists(file_to_save):
            self.window_status_bases_carteiras.text_box.insert(
                "end", "  Carteira XML Strix Master FIA: Arquivo já baixado anteriormente.\n")
        else:
            if self.app.manager_outlook.save_attachments_from_folder(
                    name_folder=pasta_arquivo,
                    refdate_email=refdate,
                    str_to_find_attachment=str_arquivo_to_find,
                    str_endswith=f".{ext_arquivo}",
                    str_to_save_attchament=file_to_save):
                self.window_status_bases_carteiras.text_box.insert("end", "  Carteira XML Strix Master FIA: Arquivo salvo na pasta.\n")
            else:
                self.window_status_bases_carteiras.text_box.insert("end", "  Carteira XML Strix Master FIA: Arquivo não encontrado.\n")

        # xlsx:
        pasta_arquivo = "Strix Master FIA"
        str_arquivo_to_find = f"ResumoCarteira_STRIX MASTER FC FIA_{refdate.strftime('%Y%m%d')}"
        ext_arquivo = "xlsx"
        str_file_name = f"ResumoCarteira_STRIX_MASTER_FC_FIA_{refdate.strftime('%Y%m%d')}.xlsx"
        file_to_save = os.path.join(  # noqa: F403, F405, E402
            base_path_carteiras, "Strix Master FIA", "xlsx", str_file_name)

        if self.funcoes_pytools.checkFileExists(file_to_save):
            self.window_status_bases_carteiras.text_box.insert(
                "end", "  Carteira XLSX Strix Master FIA: Arquivo já baixado anteriormente.\n")
        else:
            if self.app.manager_outlook.save_attachments_from_folder(
                    name_folder=pasta_arquivo,
                    refdate_email=refdate,
                    str_to_find_attachment=str_arquivo_to_find,
                    str_endswith=f".{ext_arquivo}",
                    str_to_save_attchament=file_to_save):
                self.window_status_bases_carteiras.text_box.insert("end", "  Carteira XLSX Strix Master FIA: Arquivo salvo na pasta.\n")
            else:
                self.window_status_bases_carteiras.text_box.insert("end", "  Carteira XLSX Strix Master FIA: Arquivo não encontrado.\n")

    def capturaXmlYieldMastercc(self):

        refdate = self.refdate_upload_bases_carteiras
        pasta_arquivo = "STRIX YIELD MASTER"
        str_arquivo_to_find = f"5138475_{self.funcoes_pytools.workday_br(refdate, 1).strftime('%Y-%m-%d')}"
        ext_arquivo = "xlsx"
        str_file_arquivo = f"{str_arquivo_to_find}.xlsx"
        file_to_save = os.path.join(  # noqa: F403, F405, E402
            base_path_carteiras, "Strix Yield Master", "Conta Corrente", str_file_arquivo)

        if self.funcoes_pytools.checkFileExists(file_to_save):
            self.window_status_bases_carteiras.text_box.insert(
                "end", "  Extrato CC Strix Yield Master: Arquivo já baixado anteriormente.\n")
        else:
            if self.app.manager_outlook.save_attachments_from_folder(
                    name_folder=pasta_arquivo,
                    refdate_email=refdate,
                    str_to_find_attachment=str_arquivo_to_find,
                    str_endswith=f".{ext_arquivo}",
                    str_to_save_attchament=file_to_save):
                self.window_status_bases_carteiras.text_box.insert("end", "  Extrato CC Strix Yield Master: Arquivo salvo na pasta.\n")
            else:
                self.window_status_bases_carteiras.text_box.insert("end", "  Extrato CC Strix Yield Master: Arquivo não encontrado.\n")

    def uploadCarteirasXML(self):

        self.window_status_bases_carteiras.text_box.insert("end", "Rodando: Upload Carteiras XML\n")

        results = self.manager_xml.run_carteiras(refdate=self.refdate_upload_bases_carteiras)

        for fundo in results:
            if results[fundo] == 'ok':
                self.window_status_bases_carteiras.text_box.insert("end", f"  {fundo}: Sucesso!\n")
            else:
                str_erro = ''
                for erro in results[fundo]:
                    str_erro = str_erro + erro + ' | '
                self.window_status_bases_carteiras.text_box.insert("end", f"  {fundo}: {str_erro[:-2]}\n")

        self.window_status_bases_carteiras.text_box.insert("end", "\n")

    def uploadExtratosCCXML(self):

        self.window_status_bases_carteiras.text_box.insert("end", "Rodando: Upload Extratos CC XML\n")

        self.manager_xml.set_refdate(self.refdate_upload_bases_carteiras)

        results = self.manager_xml.run_strix_master_fia_cc()

        for fundo in results:
            self.window_status_bases_carteiras.text_box.insert("end", f"  {fundo}: {results[fundo]}\n")

        self.window_status_bases_carteiras.text_box.insert("end", "\n")

    def janelaToken(self):

        janela_token = newWindowStatus(status_running=False, title="Token BTG")
        janela_token.geometry("800x600")
        janela_token.text_box.insert("end", f"\n{self.manager_btg.btg_manager.token}\n")

    def run_calculadora_ativos(self):

        def execute_calculadora_ativos(text_box):

            text_box.insert("end", "\n\nRodando calculadora ativos...\n\n")

            self.result_calculo = {}

            data_referencia = datetime.strptime(self.app.entry_refdate_calculadora.entry.get(), "%d/%m/%Y").date()
            tipo_ativos = f"'{"', '".join(self.calculadora.tipo_ativos_fluxo_pagamento)}'"

            lista_ativos = self.manager_sql.select_dataframe(
                f"SELECT DISTINCT ATIVO FROM TB_CARTEIRAS WHERE REFDATE = '{self.funcoes_pytools.convert_data_sql(data_referencia)}' \
                    AND TIPO_ATIVO IN ({tipo_ativos}) AND FINANCEIRO_D0 <> 0")['ATIVO'].tolist()

            for ativo in lista_ativos:
                resp = self.calculadora.ativosFluxoPagamentos(data_referencia=data_referencia, ativo=ativo, curva_interpolacao='DI1FUT')
                self.result_calculo[ativo] = resp

            self.result_duration = self.calculadora.durationAtivos(refdate=data_referencia)

            self.calculadora.controle_update_dados_ativos_fluxo_pagamento = False

        def results_calculadora_ativos(text_box):

            text_box.delete("1.0", "end")

            text_box.insert("end", "Resultados Calculadora Ativos - Fluxo e PU\n")

            for ativo in self.result_calculo.keys():
                text_box.insert("end", f"  {ativo}: {self.result_calculo[ativo]}\n")

            text_box.insert("end", "\nResultados Calculadora Ativos - Duration\n")

            for ativo in self.result_duration.keys():
                text_box.insert("end", f"  {ativo}: {self.result_duration[ativo]}\n")

        self.check_bases_calculadora()

        if self.app.opt_check_btn_curva_di1fut.get() and self.app.opt_check_btn_anbima_debs.get() and self.app.opt_check_btn_cdi.get() \
                and self.app.opt_check_btn_selic.get() and self.app.opt_check_btn_carteira_yield_master.get():

            janela_status = newWindowStatus(status_running=False, title="Calculadora Ativos")
            janela_status.geometry("260x140")
            progress_bar = newProgressBar(janela_status, mode="indeterminate", style="info.Horizontal.TProgressbar")
            progress_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
            progress_bar.start(15)

            text_box = janela_status.text_box
            execute_calculadora_ativos(text_box)

            progress_bar.destroy()
            janela_status.geometry("620x990")
            results_calculadora_ativos(text_box)
            self.call_status_all_bases()
            janela_status.lift()

    def check_bases_calculadora(self):

        refdate = datetime.strptime(self.app.entry_refdate_calculadora.entry.get(), "%d/%m/%Y").date()

        if self.manager_sql.check_if_data_exists(
                f"SELECT DISTINCT REFDATE FROM TB_CURVAS WHERE REFDATE = '{self.funcoes_pytools.convert_data_sql(refdate)}' \
                AND CURVA = 'DI1FUT'"):
            self.app.opt_check_btn_curva_di1fut.set(True)
            self.app.txt_status_calculadora_curva_di1fut.set(f"{self.dict_icons_status['ok']} Curva DI1FUT")
            self.app.lbl_calculadora_ativos_di1fut.set_bootstyle('success')
        else:
            self.app.opt_check_btn_curva_di1fut.set(False)
            self.app.txt_status_calculadora_curva_di1fut.set(f"{self.dict_icons_status['not']} Curva DI1FUT")
            self.app.lbl_calculadora_ativos_di1fut.set_bootstyle('danger')

        if self.manager_sql.check_if_data_exists(
                f"SELECT DISTINCT REFDATE FROM TB_ANBIMA_DEBENTURES WHERE REFDATE = '{self.funcoes_pytools.convert_data_sql(refdate)}'"):
            self.app.opt_check_btn_anbima_debs.set(True)
            self.app.txt_status_calculadora_anbima_debs.set(f"{self.dict_icons_status['ok']} Anbima Debêntures")
            self.app.lbl_calculadora_ativos_anbima_debs.set_bootstyle('success')
        else:
            self.app.opt_check_btn_anbima_debs.set(False)
            self.app.txt_status_calculadora_anbima_debs.set(f"{self.dict_icons_status['not']} Anbima Debêntures")
            self.app.lbl_calculadora_ativos_anbima_debs.set_bootstyle('danger')

        if self.manager_sql.check_if_data_exists(
                f"SELECT DISTINCT REFDATE FROM {self.tb_indexadores} WHERE REFDATE = '{self.funcoes_pytools.convert_data_sql(refdate)}' \
                AND INDEXADOR = 'CDI'"):
            self.app.opt_check_btn_cdi.set(True)
            self.app.txt_status_calculadora_cdi.set(f"{self.dict_icons_status['ok']} Cota CDI")
            self.app.lbl_calculadora_ativos_cdi.set_bootstyle('success')
        else:
            self.app.opt_check_btn_cdi.set(False)
            self.app.txt_status_calculadora_cdi.set(f"{self.dict_icons_status['not']} Cota CDI")
            self.app.lbl_calculadora_ativos_cdi.set_bootstyle('danger')

        if self.manager_sql.check_if_data_exists(
                f"SELECT DISTINCT REFDATE FROM {self.tb_indexadores} WHERE REFDATE = '{self.funcoes_pytools.convert_data_sql(refdate)}' \
                AND INDEXADOR = 'SELIC'"):
            self.app.opt_check_btn_selic.set(True)
            self.app.txt_status_calculadora_selic.set(f"{self.dict_icons_status['ok']} Cota SELIC")
            self.app.lbl_calculadora_ativos_selic.set_bootstyle('success')
        else:
            self.app.opt_check_btn_selic.set(False)
            self.app.txt_status_calculadora_selic.set(f"{self.dict_icons_status['not']} Cota SELIC")
            self.app.lbl_calculadora_ativos_selic.set_bootstyle('danger')

        if self.manager_sql.check_if_data_exists(
                f"SELECT DISTINCT REFDATE FROM TB_CARTEIRAS WHERE REFDATE = '{self.funcoes_pytools.convert_data_sql(refdate)}' \
                AND FUNDO = 'STRIX YIELD MASTER'"):
            self.app.opt_check_btn_carteira_yield_master.set(True)
            self.app.txt_status_calculadora_carteira_yield_master.set(f"{self.dict_icons_status['ok']} Cota Yield Master")
            self.app.lbl_calculadora_ativos_yield_master.set_bootstyle('success')
        else:
            self.app.opt_check_btn_carteira_yield_master.set(False)
            self.app.txt_status_calculadora_carteira_yield_master.set(f"{self.dict_icons_status['not']} Cota Yield Master")
            self.app.lbl_calculadora_ativos_yield_master.set_bootstyle('danger')

    def recon_calculadora_ativos(self):

        self.check_bases_calculadora()

        refdate = datetime.strptime(self.app.entry_refdate_calculadora.entry.get(), "%d/%m/%Y").date()

        self.calculadora.reconPrecos(refdate=refdate)

        df_recon = self.calculadora.df_recon_precos
        df_recon.sort_values(by='Diferença', key=abs, ascending=True, inplace=True)

        df_recon['Diferença'] = df_recon['Diferença'].apply(lambda x: f"{x:,.4f}")

        lista_recon = df_recon.values.tolist()

        janela_recon = newWindowStatus(status_running=False, title="Reconciliação Precos Calculadora Ativos")
        janela_recon.geometry("800x600")
        janela_recon.text_box.destroy()
        janela_recon.columnconfigure(0, weight=1)
        janela_recon.rowconfigure(0, weight=1)

        tableview_recon = Tableview(
            janela_recon, searchable=True, autofit=True, paginated=False, height=30, coldata=df_recon.columns.tolist())

        tableview_recon.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        tableview_recon.reset_table()
        tableview_recon.delete_rows(indices=None, iids=None)
        tableview_recon.insert_rows('end', lista_recon)
        tableview_recon.load_table_data()
        tableview_recon.autofit_columns()

    def status_bases(self):

        def check_xml_fundos(app):
            lista_fundos_xml = self.manager_sql.select_dataframe(
                f"SELECT DISTINCT FUNDO FROM TB_XML_CARTEIRAS_HEADER WHERE REFDATE = '{self.refdate_status_bases}'")['FUNDO'].tolist()

            if len(lista_fundos_xml) == 0:
                app.lbl_status_bases_xml_carteiras.set_bootstyle('danger')
                app.txt_status_bases_xml_carteiras.set(f"{self.dict_icons_status['not']} XML Carteiras")
            elif set(self.fundos_all).issubset(set(lista_fundos_xml)):
                app.lbl_status_bases_xml_carteiras.set_bootstyle('success')
                app.txt_status_bases_xml_carteiras.set(f"{self.dict_icons_status['ok']} XML Carteiras")
            else:
                app.lbl_status_bases_xml_carteiras.set_bootstyle('warning')
                app.txt_status_bases_xml_carteiras.set(f"{self.dict_icons_status['warning']} XML Carteiras")

        def check_perf_nav(app):
            lista_fundos_perf_nav = self.manager_sql.select_dataframe(
                f"SELECT DISTINCT FUNDO FROM TB_BASE_BTG_PERFORMANCE_COTA WHERE REFDATE = '{self.refdate_status_bases}'")['FUNDO'].tolist()

            if len(lista_fundos_perf_nav) == 0:
                app.lbl_status_bases_perf_nav.set_bootstyle('danger')
                app.txt_status_bases_perf_nav.set(f"{self.dict_icons_status['not']} Perf Nav")
            elif set(self.fundos_btg).issubset(set(lista_fundos_perf_nav)):
                app.lbl_status_bases_perf_nav.set_bootstyle('success')
                app.txt_status_bases_perf_nav.set(f"{self.dict_icons_status['ok']} Perf Nav")
            else:
                app.lbl_status_bases_perf_nav.set_bootstyle('warning')
                app.txt_status_bases_perf_nav.set(f"{self.dict_icons_status['warning']} Perf Nav")

        def check_perf_cotistas(app):
            lista_fundos_perf_cotistas = self.manager_sql.select_dataframe(
                f"SELECT DISTINCT FUNDO FROM TB_BASE_BTG_PERFORMANCE_COTISTAS \
                    WHERE REFDATE = '{self.refdate_status_bases}'")['FUNDO'].tolist()

            if len(lista_fundos_perf_cotistas) == 0:
                app.lbl_status_bases_perf_cotistas.set_bootstyle('danger')
                app.txt_status_bases_perf_cotistas.set(f"{self.dict_icons_status['not']} Perf Cotistas")
            elif set(self.fundos_btg).issubset(set(lista_fundos_perf_cotistas)):
                app.lbl_status_bases_perf_cotistas.set_bootstyle('success')
                app.txt_status_bases_perf_cotistas.set(f"{self.dict_icons_status['ok']} Perf Cotistas")
            else:
                app.lbl_status_bases_perf_cotistas.set_bootstyle('warning')
                app.txt_status_bases_perf_cotistas.set(f"{self.dict_icons_status['warning']} Perf Cotistas")

        def check_adm_cotistas(app):
            lista_fundos_adm_cotistas = self.manager_sql.select_dataframe(
                f"SELECT DISTINCT FUNDO FROM TB_BASE_BTG_TX_ADM_COTISTAS \
                    WHERE REFDATE = '{self.refdate_status_bases}'")['FUNDO'].tolist()

            if len(lista_fundos_adm_cotistas) == 0:
                app.lbl_status_bases_adm_cotistas.set_bootstyle('danger')
                app.txt_status_bases_adm_cotistas.set(f"{self.dict_icons_status['not']} Adm Cotistas")
            elif set(self.fundos_btg).issubset(set(lista_fundos_adm_cotistas)):
                app.lbl_status_bases_adm_cotistas.set_bootstyle('success')
                app.txt_status_bases_adm_cotistas.set(f"{self.dict_icons_status['ok']} Adm Cotistas")
            else:
                app.lbl_status_bases_adm_cotistas.set_bootstyle('warning')
                app.txt_status_bases_adm_cotistas.set(f"{self.dict_icons_status['warning']} Adm Cotistas")

        def check_anbima_debentures(app):
            if self.manager_sql.check_if_data_exists(
                    f"SELECT DISTINCT REFDATE FROM TB_ANBIMA_DEBENTURES WHERE \
                        REFDATE = '{self.funcoes_pytools.convert_data_sql(self.refdate_status_bases)}'"):
                app.lbl_status_bases_anbima_debentures.set_bootstyle('success')
                app.txt_status_bases_anbima_debentures.set(f"{self.dict_icons_status['ok']} Anbima Debentures")
            else:
                app.lbl_status_bases_anbima_debentures.set_bootstyle('danger')
                app.txt_status_bases_anbima_debentures.set(f"{self.dict_icons_status['not']} Anbima Debentures")

        def check_curvas_b3(app):
            if self.manager_sql.check_if_data_exists(
                    f"SELECT DISTINCT FONTE FROM TB_CURVAS WHERE FONTE = 'B3' AND \
                        REFDATE = '{self.funcoes_pytools.convert_data_sql(self.refdate_status_bases)}'"):
                app.lbl_status_bases_curvasb3.set_bootstyle('success')
                app.txt_status_bases_curvas_b3.set(f"{self.dict_icons_status['ok']} Curvas B3")
            else:
                app.lbl_status_bases_curvasb3.set_bootstyle('danger')
                app.txt_status_bases_curvas_b3.set(f"{self.dict_icons_status['not']} Curvas B3")

        def check_imab(app):
            if self.manager_sql.check_if_data_exists(
                    f"SELECT INDEXADOR FROM {self.tb_indexadores} WHERE INDEXADOR = 'IMA-B' AND \
                        REFDATE = '{self.funcoes_pytools.convert_data_sql(self.refdate_status_bases)}'"):
                app.lbl_status_bases_imab.set_bootstyle('success')
                app.txt_status_bases_imab.set(f"{self.dict_icons_status['ok']} IMA-B")
            else:
                app.lbl_status_bases_imab.set_bootstyle('danger')
                app.txt_status_bases_imab.set(f"{self.dict_icons_status['not']} IMA-B")

        def check_imabjust(app):
            if self.manager_sql.check_if_data_exists(
                    f"SELECT INDEXADOR FROM {self.tb_indexadores} WHERE INDEXADOR = 'IMABAJUST' AND \
                        REFDATE = '{self.funcoes_pytools.convert_data_sql(self.refdate_status_bases)}'"):
                app.lbl_status_bases_imabjust.set_bootstyle('success')
                app.txt_status_bases_imabjust.set(f"{self.dict_icons_status['ok']} IMABJUST")
            else:
                app.lbl_status_bases_imabjust.set_bootstyle('danger')
                app.txt_status_bases_imabjust.set(f"{self.dict_icons_status['not']} IMABJUST")

        def check_cdi(app):
            if self.manager_sql.check_if_data_exists(
                    f"SELECT INDEXADOR FROM {self.tb_indexadores} WHERE INDEXADOR = 'CDI' AND \
                        REFDATE = '{self.funcoes_pytools.convert_data_sql(self.refdate_status_bases)}'"):
                app.lbl_status_bases_cdi.set_bootstyle('success')
                app.txt_status_bases_cdi.set(f"{self.dict_icons_status['ok']} CDI")
            else:
                app.lbl_status_bases_cdi.set_bootstyle('danger')
                app.txt_status_bases_cdi.set(f"{self.dict_icons_status['not']} CDI")

        def check_selic(app):
            if self.manager_sql.check_if_data_exists(
                    f"SELECT INDEXADOR FROM {self.tb_indexadores} WHERE INDEXADOR = 'SELIC' AND \
                        REFDATE = '{self.funcoes_pytools.convert_data_sql(self.refdate_status_bases)}'"):
                app.lbl_status_bases_selic.set_bootstyle('success')
                app.txt_status_bases_selic.set(f"{self.dict_icons_status['ok']} SELIC")
            else:
                app.lbl_status_bases_selic.set_bootstyle('danger')
                app.txt_status_bases_selic.set(f"{self.dict_icons_status['not']} SELIC")

        def check_result_calculadora_ativos(app):

            str_tipo_ativos = f"'{"', '".join(self.calculadora.tipo_ativos_fluxo_pagamento)}'"

            sQuery = (
                f"SELECT DISTINCT ATIVO FROM TB_CARTEIRAS WHERE REFDATE = "
                f"'{self.funcoes_pytools.convert_data_sql(self.refdate_status_bases)}' AND FINANCEIRO_D0 <> 0 AND "
                f"TIPO_ATIVO IN ({str_tipo_ativos})"
            )

            lista_ativos = self.manager_sql.select_dataframe(sQuery)['ATIVO'].tolist()

            lista_ativos_fluxo = self.manager_sql.select_dataframe(
                f"SELECT DISTINCT ATIVO FROM TB_FLUXO_FUTURO_ATIVOS "
                f"WHERE REFDATE = '{self.funcoes_pytools.convert_data_sql(self.refdate_status_bases)}'")['ATIVO'].tolist()

            if len(lista_ativos_fluxo) == 0:
                app.lbl_status_bases_calculadora.set_bootstyle('danger')
                app.txt_status_bases_calculadora.set(f"{self.dict_icons_status['not']} Calculadora")
            elif set(lista_ativos).issubset(set(lista_ativos_fluxo)) is True:
                app.lbl_status_bases_calculadora.set_bootstyle('success')
                app.txt_status_bases_calculadora.set(f"{self.dict_icons_status['ok']} Calculadora")
            else:
                app.lbl_status_bases_calculadora.set_bootstyle('warning')
                app.txt_status_bases_calculadora.set(f"{self.dict_icons_status['warning']} Calculadora")

        self.refdate_status_bases = datetime.strptime(self.app.entry_refdate_status_bases.entry.get(), "%d/%m/%Y").date()

        check_xml_fundos(self.app)
        check_perf_nav(self.app)
        check_perf_cotistas(self.app)
        check_adm_cotistas(self.app)
        check_anbima_debentures(self.app)
        check_curvas_b3(self.app)
        check_imab(self.app)
        check_imabjust(self.app)
        check_cdi(self.app)
        check_selic(self.app)
        check_result_calculadora_ativos(self.app)

    def upload_anbima_debentures(self):

        self.window_status_outras_bases.text_box.insert("end", "Rodando: Debêntures Anbima.\n")
        check_debentures_anbima = self.debenturesAnbima.run(refdate=self.refdate_upload_outras_bases)

        if check_debentures_anbima == 'ok':
            self.window_status_outras_bases.text_box.insert("end", "  Upload: OK.\n\n")
        elif check_debentures_anbima == 'Já baixado anteriormente':
            self.window_status_outras_bases.text_box.insert("end", "  Já baixado anteriormente.\n\n")
        else:
            self.window_status_outras_bases.text_box.insert("end", f"  Erro: {check_debentures_anbima}\n\n")

    def upload_curvasB3(self):

        self.window_status_outras_bases.text_box.insert("end", "Rodando: Curvas B3.\n")

        check_cruvas_b3 = self.curvasb3.run(refdate=self.refdate_upload_outras_bases, p_webdriver=self.driver)

        if check_cruvas_b3 == 'all_uploaded':
            self.window_status_outras_bases.text_box.insert("end", "  Já baixado anteriormente.\n\n")
        else:
            for dado in check_cruvas_b3:
                self.window_status_outras_bases.text_box.insert("end", f"  Curva: {dado}: {check_cruvas_b3[dado]}.\n")
            self.window_status_outras_bases.text_box.insert("end", "\n")

    def captura_cdi_selic_b3(self):

        def check_if_temp():

            if self.manager_sql.select_dataframe(
                    f"SELECT STATUS FROM TB_AUX_CONTROL_PANEL_CONTROLE_PROCESSOS "
                    f"WHERE PROCESSO = 'INDEXADORES_CDI_SELIC' AND REFDATE = '{self.refdate_upload_outras_bases}'")['STATUS'][0] == 0:

                self.manager_sql.delete_records(
                    self.tb_indexadores,
                    f"REFDATE = '{self.refdate_upload_outras_bases}' AND INDEXADOR IN ('CDI', 'SELIC')")

        def check_if_need_temp():

            if self.manager_sql.select_dataframe(
                    f"SELECT STATUS FROM TB_AUX_CONTROL_PANEL_CONTROLE_PROCESSOS "
                    f"WHERE PROCESSO = 'INDEXADORES_CDI_SELIC' AND REFDATE = '{self.refdate_upload_outras_bases}'")['STATUS'][0] == 0:

                dmenos1 = self.funcoes_pytools.workday_br(self.refdate_upload_outras_bases, -1)

                valor_cdi_dia_dmenos1 = self.manager_sql.select_dataframe(
                    f"SELECT VALOR_DIA FROM {self.tb_indexadores} WHERE REFDATE = '{dmenos1}' AND INDEXADOR = 'CDI'")['VALOR_DIA'][0]
                cota_cdi_dmenos1 = self.manager_sql.select_dataframe(
                    f"SELECT COTA_INDEXADOR FROM {self.tb_indexadores} "
                    f"WHERE REFDATE = '{dmenos1}' AND INDEXADOR = 'CDI'")['COTA_INDEXADOR'][0]
                valor_cdi_ano_dmenos1 = self.manager_sql.select_dataframe(
                    f"SELECT VALOR_ANO FROM {self.tb_indexadores} WHERE REFDATE = '{dmenos1}' AND INDEXADOR = 'CDI'")['VALOR_ANO'][0]

                valor_selic_dia_dmenos1 = self.manager_sql.select_dataframe(
                    f"SELECT VALOR_DIA FROM {self.tb_indexadores} WHERE REFDATE = '{dmenos1}' AND INDEXADOR = 'SELIC'")['VALOR_DIA'][0]
                cota_selic_dmenos1 = self.manager_sql.select_dataframe(
                    f"SELECT COTA_INDEXADOR FROM {self.tb_indexadores} "
                    f"WHERE REFDATE = '{dmenos1}' AND INDEXADOR = 'SELIC'")['COTA_INDEXADOR'][0]
                valor_selic_ano_dmenos1 = self.manager_sql.select_dataframe(
                    f"SELECT VALOR_ANO FROM {self.tb_indexadores} WHERE REFDATE = '{dmenos1}' AND INDEXADOR = 'SELIC'")['VALOR_ANO'][0]

                cota_cdi_d0_temp = cota_cdi_dmenos1 * (1 + valor_cdi_dia_dmenos1)
                cota_selic_d0_temp = cota_selic_dmenos1 * (1 + valor_selic_dia_dmenos1)

                data = {
                    "REFDATE": [self.refdate_upload_outras_bases, self.refdate_upload_outras_bases],
                    "INDEXADOR": ['CDI', 'SELIC'],
                    "VALOR_ANO": [valor_cdi_ano_dmenos1, valor_selic_ano_dmenos1],
                    "VALOR_DIA": [valor_cdi_dia_dmenos1, valor_selic_dia_dmenos1],
                    "COTA_INDEXADOR": [cota_cdi_d0_temp, cota_selic_d0_temp]
                }

                self.manager_sql.insert_dataframe(pd.DataFrame(data), self.tb_indexadores)

                return True
            else:
                return False

        self.window_status_outras_bases.text_box.insert("end", "Captura CDI & SELIC B3\n")

        check_if_temp()

        result = self.dadosB3.run_scrapping_cdi_selic_b3(
            refdate=self.refdate_upload_outras_bases,
            p_webdriver=self.driver)

        if result == 'all_uploaded':
            self.window_status_outras_bases.text_box.insert("end", "  Já baixados anteriormente.\n\n")
        else:
            for dado in result:
                self.window_status_outras_bases.text_box.insert("end", f"  {dado}: {result[dado]}\n")

            if self.manager_sql.check_if_data_exists(
                    f"SELECT * FROM TB_INDEXADORES WHERE REFDATE = '{self.refdate_upload_outras_bases}' AND INDEXADOR = 'CDI'"):
                self.manager_sql.update_table(
                    table_name="TB_AUX_CONTROL_PANEL_CONTROLE_PROCESSOS",
                    column_with_data_to_update="STATUS = '1'",
                    column_with_condition=f"PROCESSO = 'INDEXADORES_CDI_SELIC' AND REFDATE = '{self.refdate_upload_outras_bases}'")

            if check_if_need_temp():
                self.window_status_outras_bases.text_box.insert("end", "  Upload CDI e SELIC temporários.\n")

            self.window_status_outras_bases.text_box.insert("end", "\n")

    def check_if_need_upload_bases_b3(self):

        self.curvasb3.set_refdate(self.refdate_upload_outras_bases)
        self.dadosB3.set_refdate(self.refdate_upload_outras_bases)

        if self.curvasb3.check_sql_uploaded() is not True or self.dadosB3.check_sql_uploaded() is not True:
            return True
        else:
            return False

    def processos_outras_bases(self):

        if self.window_status_outras_bases is not None and self.window_status_outras_bases.winfo_exists():
            self.window_status_outras_bases.lift()
        else:
            self.window_status_outras_bases = newWindowStatus(title="Outras Bases", status_running=True)

            self.window_status_outras_bases.geometry("400x400")

            self.refdate_upload_outras_bases = datetime.strptime(self.app.entry_refdate_outras_bases.entry.get(), "%d/%m/%Y").date()

            self.window_status_outras_bases.text_box.insert("end", "Inicio processos - Upload outras bases\n\n")

            if self.app.opt_check_btn_anbima_debentures.get():
                self.upload_anbima_debentures()

            if self.app.opt_check_btn_curvas_b3.get() or self.app.opt_check_btn_cdi_selic_b3.get():

                check_need_driver = self.check_if_need_upload_bases_b3()

                if check_need_driver:
                    self.driver = openEdgeDriver().driver
                else:
                    self.driver = None

                if self.driver is not None:

                    print(f"Driver --> {self.driver}")

                    if self.app.opt_check_btn_curvas_b3.get():
                        self.upload_curvasB3()

                    if self.app.opt_check_btn_cdi_selic_b3.get():
                        self.captura_cdi_selic_b3()

                    if check_need_driver:
                        self.driver.quit()

                else:
                    self.window_status_outras_bases.text_box.insert("end", "Driver web falhou.\n")

            self.window_status_outras_bases.text_box.insert("end", "Processos finalizados.\n")
            self.window_status_outras_bases.status_running = False
            self.window_status_outras_bases.ajusta_tamanho()
            self.call_status_all_bases()
            self.window_status_outras_bases.lift()

    def processos_bases_carterias(self):

        if self.window_status_bases_carteiras is not None and self.window_status_bases_carteiras.winfo_exists():
            self.window_status_bases_carteiras.lift()
        else:
            if any(var.get() for var in self.app.lista_opts_bases_carteiras):

                self.window_status_bases_carteiras = newWindowStatus(title="Upload Bases BTG", status_running=True)

                self.window_status_bases_carteiras.geometry("400x550")

                self.refdate_upload_bases_carteiras = datetime.strptime(
                    self.app.entry_refdate_bases_carteiras.entry.get(), "%d/%m/%Y").date()

                self.dict_status_carteiras_bases_btg = self.manager_sql.select_dataframe(
                    f"SELECT FUNDO, STATUS_CARTEIRA FROM TB_BASE_BTG_STATUS_CARTEIRAS "
                    f"WHERE DATA_COTA = '{self.funcoes_pytools.convert_data_sql(self.refdate_upload_bases_carteiras)}'")\
                    .set_index('FUNDO').to_dict()['STATUS_CARTEIRA']

                self.window_status_bases_carteiras.text_box.insert("end", "Inicio processos - Bases BTG\n\n")

                if self.app.opt_check_btn_captura_arquivos_email.get():
                    self.runCapturaArquivosEmail()

                if self.app.opt_check_btn_upload_arquivos_xml.get():
                    self.uploadCarteirasXML()
                    self.uploadExtratosCCXML()

                if self.app.opt_check_btn_download_carteiras_btg.get():
                    self.btgFundsDownloadCarteiras()

                if self.app.opt_check_btn_funds_perf_nav.get():
                    self.btgFundsPerfNav()

                if self.app.opt_check_btn_update_indexadores.get():
                    self.updateIndexadores()

                if self.app.opt_check_btn_funds_perf_cotistas.get():
                    self.btgFundsPerfCotistas()

                if self.app.opt_check_btn_funds_adm_cotistas.get():
                    self.btgFundsAdmCotistas()

                self.window_status_bases_carteiras.text_box.insert("end", "Processos finalizados.\n")
                self.window_status_bases_carteiras.status_running = False
                self.window_status_bases_carteiras.ajusta_tamanho()
                self.call_status_all_bases()
                self.window_status_bases_carteiras.lift()

    def open_excel_control_panel(self):
        os.startfile(  # noqa: F403, F405, E402
            f"C:\\Users\\{str_user}\\Strix Capital\\Backoffice - General\\Processos\\Backoffice - Control Panel.xlsm")  # noqa: F403, F405
        self.call_status_all_bases()

    def open_excel_carteira_fundos(self):
        os.startfile(  # noqa: F403, F405, E402
            f"C:\\Users\\{str_user}\\Strix Capital\\Backoffice - General\\Processos\\Backoffice - Carteira Fundos.xlsm")  # noqa: F403, F405
        self.call_status_all_bases()

    def open_excel_upload_curvas_bbg(self):
        os.startfile(  # noqa: F403, F405, E402
            f"C:\\Users\\{str_user}\\Strix Capital\\Backoffice - General\\Processos\\Backoffice - Upload Curvas BBG.xlsm")  # noqa: F405
        self.call_status_all_bases()


class AutoProcessManager():

    def __init__(self, app):

        super().__init__()

        self.app = app

        self.manager_sql = self.app.manager_sql

        self.funcoes_pytools = self.app.funcoes_pytools

        self.manager_btg = app.manager_btg

        self.window_status_loop_btg = None

    def widgets_loop_btg(self):

        def check_close():
            self.need_to_close = True
            if self.status_btg_status_carteiras_running is False and self.status_btg_status_bases_btg_running is False:
                if self.status_bases_ready_to_close and self.status_carteiras_ready_to_close:
                    self.window_status_loop_btg.destroy()
            else:
                Messagebox.show_info(title="Aviso", message="Aguarde o término do processo para fechar a janela.")
                self.window_status_loop_btg.lift()

        def widgets_status_carteiras():

            def comando_btn_status_carteiras():
                self.controle_loop_status_carteiras_btg = 'restart'

            self.interval_loop_btg_status_carteiras = newStringVar(value=5)

            frame_status_carteiras = newLabelFrame(self.frame_loop_btg_body, text="Status Carteiras")
            frame_status_carteiras.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 0))
            frame_status_carteiras.columnconfigure(0, weight=1)
            frame_status_carteiras.rowconfigure(1, weight=1)

            frame_controle_status_carteiras = newFrame(frame_status_carteiras)
            frame_controle_status_carteiras.grid(row=0, column=0, sticky="w", padx=5, pady=(5, 0))

            btn_run_status_carteiras = newButton(
                frame_controle_status_carteiras, text="Executar", bootstyle="secondary", command=comando_btn_status_carteiras)

            btn_run_status_carteiras.grid(row=0, column=0, sticky="w", padx=(5, 0), pady=(5, 5))

            self.entry_tempo_status_carteiras = newSpinBox(
                frame_controle_status_carteiras,
                textvariable=self.interval_loop_btg_status_carteiras)

            self.entry_tempo_status_carteiras.set_secondary()
            self.entry_tempo_status_carteiras.set_values([1, 5, 10, 15, 20, 30])

            self.entry_tempo_status_carteiras.grid(row=0, column=1, sticky="w", padx=(5, 0), pady=(5, 5))

            frame_txt_status_carteiras = newFrame(frame_status_carteiras)
            frame_txt_status_carteiras.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
            frame_txt_status_carteiras.columnconfigure(0, weight=1)
            frame_txt_status_carteiras.rowconfigure(0, weight=1)

            self.txt_box_status_carteiras = newScrolledText(frame_txt_status_carteiras, height=9)
            self.txt_box_status_carteiras.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        def widgets_status_bases_btg():

            def comando_btn_status_bases_btg():
                self.controle_loop_bases_btg = 'restart'

            self.interval_loop_btg_status_bases_btg = newStringVar(value=5)

            frame_status_bases_btg = newLabelFrame(self.frame_loop_btg_body, text="Status Bases BTG")
            frame_status_bases_btg.grid(row=1, column=0, sticky="nsew", padx=10, pady=(10, 10))
            frame_status_bases_btg.columnconfigure(0, weight=1)
            frame_status_bases_btg.rowconfigure(1, weight=1)

            frame_controle_status_bases_btg = newFrame(frame_status_bases_btg)
            frame_controle_status_bases_btg.grid(row=0, column=0, sticky="w", padx=5, pady=(5, 0))

            btn_run_status_bases_btg = newButton(
                frame_controle_status_bases_btg, text="Executar", bootstyle="secondary", command=comando_btn_status_bases_btg)

            btn_run_status_bases_btg.grid(row=0, column=0, sticky="w", padx=(5, 0), pady=(5, 5))

            self.entry_tempo_status_bases_btg = newSpinBox(
                frame_controle_status_bases_btg,
                textvariable=self.interval_loop_btg_status_bases_btg)
            self.entry_tempo_status_bases_btg.set_secondary()
            self.entry_tempo_status_bases_btg.set_values([1, 5, 10, 15, 20, 30])

            self.entry_tempo_status_bases_btg.grid(row=0, column=1, sticky="w", padx=(5, 0), pady=(5, 5))

            frame_txt_status_bases_btg = newFrame(frame_status_bases_btg)
            frame_txt_status_bases_btg.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
            frame_txt_status_bases_btg.columnconfigure(0, weight=1)
            frame_txt_status_bases_btg.rowconfigure(0, weight=1)

            self.txt_box_status_bases_btg = newScrolledText(frame_txt_status_bases_btg, height=17)
            self.txt_box_status_bases_btg.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        if self.window_status_loop_btg is not None and self.window_status_loop_btg.winfo_exists():
            self.loop_carteiras_btg_oppened = True
            self.loop_bases_btg_oppened = True
            self.window_status_loop_btg.lift()
        else:
            self.window_status_loop_btg = newWindowStatus(title="Loop BTG", status_running=True)
            self.window_status_loop_btg.geometry("265x600")
            self.window_status_loop_btg.text_box.destroy()

            self.window_status_loop_btg.protocol("WM_DELETE_WINDOW", check_close)

            self.frame_loop_btg_body = newFrame(self.window_status_loop_btg)
            self.frame_loop_btg_body.grid(row=0, column=0, sticky="nsew")
            self.frame_loop_btg_body.columnconfigure(0, weight=1)

            widgets_status_carteiras()
            widgets_status_bases_btg()

            # Variaveis de controle
            self.need_to_close = False
            self.loop_carteiras_btg_oppened = False
            self.loop_bases_btg_oppened = False

            self.controle_loop_bases_btg = True
            self.status_bases_ready_to_close = False

            self.controle_loop_status_carteiras_btg = True
            self.status_carteiras_ready_to_close = False

    def loop_status_carteiras_btg(self):

        def loop_waiting():
            total = int(self.interval_loop_btg_status_carteiras.get()) * 60
            i = 0
            while i <= total:
                if self.need_to_close:
                    self.txt_box_status_carteiras.delete("1.0", "end")
                    self.txt_box_status_carteiras.insert("end", "\nPronto para fechar.")
                    return False
                elif self.controle_loop_status_carteiras_btg is True:
                    sleep(1)
                    i += 1
                elif self.controle_loop_status_carteiras_btg == 'restart':
                    self.controle_loop_status_carteiras_btg = True
                    return True
            return True

        def btgFundsStatusCarteiras():

            check_liberados = True

            self.txt_box_status_carteiras.delete("1.0", "end")
            self.txt_box_status_carteiras.insert("end", "Rodando: Status Carteiras BTG...\n")
            results = self.manager_btg.funds_status_carteiras(refdate=self.app.refdate)
            self.txt_box_status_carteiras.delete("1.0", "end")

            if results['insert'] == 'Sem registros.':
                self.txt_box_status_carteiras.insert("end", "No records.\n")
            elif results['insert'] == 'Erro do tratamento dados.':
                self.txt_box_status_carteiras.insert("end", "Erro no tratamento dos dados.\n")
            elif results['insert'] == 'Erro do get_data.':
                self.txt_box_status_carteiras.insert("end", "Erro do get_data da API.\n")
            elif results['insert'] == 'ok':
                df = self.manager_sql.select_dataframe(
                    f"SELECT FUNDO, STATUS_CARTEIRA FROM TB_BASE_BTG_STATUS_CARTEIRAS "
                    f"WHERE REFDATE = '{self.app.refdate.strftime('%Y-%m-%d')}'")
                results_df = df.set_index('FUNDO')['STATUS_CARTEIRA'].to_dict()

                for fundo in results_df:
                    if results_df[fundo] != 'Liberados':
                        check_liberados = False
                    self.txt_box_status_carteiras.insert("end", f"{fundo}: {results_df[fundo]}\n")
            else:
                self.txt_box_status_carteiras.insert("end", "Erro desconhecido.\n")
                check_liberados = False

            return check_liberados

        while True:
            self.status_btg_status_carteiras_running = True

            if btgFundsStatusCarteiras() is True:
                self.txt_box_status_carteiras.delete("1.0", "end")
                self.txt_box_status_carteiras.insert("end", "\n\nTodos os fundos estão liberados.\n")
                self.status_btg_status_carteiras_running = False
                self.status_carteiras_ready_to_close = True
                break

            last_run = datetime.now()
            next_run = last_run + timedelta(minutes=int(self.interval_loop_btg_status_carteiras.get()))

            self.txt_box_status_carteiras.insert("end", f"\nlast run: {last_run.strftime('%H:%M:%S')}\n")
            self.txt_box_status_carteiras.insert("end", f"next run: {next_run.strftime('%H:%M:%S')}")

            self.status_btg_status_carteiras_running = False

            if loop_waiting() is False:
                self.status_carteiras_ready_to_close = True
                break

    def loop_status_bases_btg(self):

        def emailNewMovCotistas():

            lista_ids_mov_cotistas = self.manager_sql.select_dataframe(
                f"SELECT ID_BTG FROM TB_BASE_BTG_MOVIMENTACAO_PASSIVO "
                f"WHERE DATA_OPERACAO = '{self.app.refdate.strftime('%Y-%m-%d')}'")['ID_BTG'].tolist()

            lista_ids_mov_cotistas_controle = self.manager_sql.select_dataframe(
                f"SELECT ID_EXTERNO FROM TB_AUX_CONTROL_PANEL_MOV_PASSIVOS "
                f"WHERE REFDATE = '{self.app.refdate.strftime('%Y-%m-%d')}' "
                f"AND TB_ID_EXTERNO = 'TB_BASE_BTG_MOVIMENTACAO_PASSIVO'")['ID_EXTERNO'].tolist()

            check_list = list((set(lista_ids_mov_cotistas) - set(lista_ids_mov_cotistas_controle)))

            if len(check_list) > 0:

                if ENVIRONMENT == "DEVELOPMENT":
                    to_list = [os.getenv("EMAIL_ME")]  # noqa: F403, F405, E402
                else:
                    to_list = [os.getenv("EMAIL_BO")]  # noqa: F403, F405, E402

                subject = f"Nova Movimentação Cotistas - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
                sedbehalf = os.getenv("EMAIL_ROBO")  # noqa: F403, F405, E402

                df_movs_cotistas = self.manager_sql.select_dataframe(
                    f"SELECT * FROM TB_BASE_BTG_MOVIMENTACAO_PASSIVO WHERE DATA_OPERACAO = '{self.app.refdate.strftime('%Y-%m-%d')}'")
                df_movs_cotistas.set_index('ID_BTG', inplace=True)

                for index, row in df_movs_cotistas.iterrows():
                    if index in check_list:

                        self.manager_sql.insert_manual(
                            'TB_AUX_CONTROL_PANEL_MOV_PASSIVOS',
                            ['REFDATE', 'ID_EXTERNO', 'TB_ID_EXTERNO'],
                            [self.app.refdate.strftime('%Y-%m-%d'), str(index), 'TB_BASE_BTG_MOVIMENTACAO_PASSIVO'])

                        str_body = (
                            f"Mensagem automática.\n\n"
                            f"Fundo: {row['FUNDO']}\n"
                            f"ID BTG: {str(index)}\n"
                            f"Tipo Operação: {row['TIPO_OPERACAO']}\n"
                            f"Valor: {row['VALOR']:,.2f}\n"
                            f"Data Operação: {row['DATA_OPERACAO']}\n"
                            f"Data Cotização: {row['DATA_COTIZACAO']}\n"
                            f"Data Liquidação: {row['DATA_IMPACTO']}\n\n\n"
                        )

                        self.app.manager_outlook.send_email(
                            to_list=to_list, subject=subject, msg_body=str_body, sendBehalf=sedbehalf)

        def loop_waiting():
            total = int(self.interval_loop_btg_status_bases_btg.get()) * 60
            i = 0
            while i <= total:
                if self.need_to_close:
                    self.txt_box_status_bases_btg.delete("1.0", "end")
                    self.txt_box_status_bases_btg.insert("end", "\nPronto para fechar.")
                    return False
                elif self.controle_loop_bases_btg is True:
                    sleep(1)
                    i += 1
                elif self.controle_loop_bases_btg == 'restart':
                    self.controle_loop_bases_btg = True
                    return True
            return True

        def btgFundsExtratoCC():

            self.txt_box_status_bases_btg.insert("end", "Extrato CC Funds:\n")

            results = self.manager_btg.funds_extrato_cc(refdate=self.app.refdate)

            for fundo in results:
                if results[fundo] == 'ok':
                    self.txt_box_status_bases_btg.insert("end", f"  {fundo}: OK!\n")
                else:
                    self.txt_box_status_bases_btg.insert("end", f"  {fundo}: {results[fundo]}\n")

        def btgFundsMovCotistas():

            self.txt_box_status_bases_btg.insert("end", "Movimentações Cotistas\n")

            results = self.manager_btg.funds_movimentacao_cotistas(refdate=self.app.refdate)

            for fundo in results:
                if results[fundo] == 'ok':
                    self.txt_box_status_bases_btg.insert("end", f"  {fundo}: OK!\n")
                else:
                    self.txt_box_status_bases_btg.insert("end", f"  {fundo}: {results[fundo]}\n")

        while True:

            self.status_btg_status_bases_btg_running = True
            self.txt_box_status_bases_btg.delete("1.0", "end")

            btgFundsExtratoCC()
            self.txt_box_status_bases_btg.insert("end", "\n")
            btgFundsMovCotistas()
            emailNewMovCotistas()

            last_run = datetime.now()
            next_run = last_run + timedelta(minutes=int(self.interval_loop_btg_status_bases_btg.get()))

            self.txt_box_status_bases_btg.insert("end", f"\nlast run: {last_run.strftime('%H:%M:%S')}\n")
            self.txt_box_status_bases_btg.insert("end", f"next run: {next_run.strftime('%H:%M:%S')}")

            self.status_btg_status_bases_btg_running = False
            if loop_waiting() is False:
                self.status_bases_ready_to_close = True
                break


class App(Window):

    def __init__(self):
        super().__init__(themename='cyborg')

        self.lista_processos_app = ['INDEXADORES_CDI_SELIC']

        self.manager_sql = SQL_Manager()

        self.logger = Logger(manager_sql=self.manager_sql)

        self.logger.info(
            f"Control Panel Backoffice - {VERSION_APP} - {ENVIRONMENT} - Iniciando",
            script_original=SCRIPT_NAME)

        self.funcoes_pytools = FuncoesPyTools(self.manager_sql, logger=self.logger)

        self.refdate = datetime.today()

        self.manager_outlook = OutlookHandler(
            manager_sql=self.manager_sql,
            funcoes_pytools=self.funcoes_pytools,
            logger=self.logger)

        self.config_app()
        self.menu_principal()
        self.variaveis_widgets()
        self.widgets()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.manager_btg = BTGReports(sql_manager=self.manager_sql, funcoes_pytools=self.funcoes_pytools, logger=self.logger)

        if ENVIRONMENT != "DEVELOPMENT":
            self.manager_btg.connect(user_id=os.getenv("USER_BTG_FAAS"), user_pass=os.getenv("PASS_BTG_FAAS_PROD"))  # noqa: F403, F405
        elif ENVIRONMENT == "DEVELOPMENT" and CONNECT_MANAGER_BTG:
            self.manager_btg.connect()

        self.running_processos_manuaus_bases = False

        self.process_manager = ProcessManager(app=self)

        self.auto_process_manager = AutoProcessManager(app=self)

        self.process_manager.status_bases()

        self.process_manager.check_bases_calculadora()

        self.process_manager_autoopen = ProcessManagerAutoOpen(app=self)

        self.mainloop()

    def on_close(self):
        if self.running_processos_manuaus_bases:
            if Messagebox.yesno(
                    title="Encerrar App", message="Existem processos em execução.\n\nDeseja encerrar o aplicativo mesmo assim?"):
                sys.exit()  # noqa: F403, F405, E402
        else:
            self.destroy()

    def change_refdate(self):
        self.refdate = Querybox.get_date(title="Select refdate")
        self.lbl_refdate.configure(text=f"Refdate: {self.refdate.strftime('%d/%m/%Y')}")

    def menu_principal(self):

        def menu_refdate():

            self.menu_refdate = newMenuButton(self.frame_menu, text='Refdate', bootstyle="light")
            self.menu_refdate.grid(row=0, column=0, padx=0, pady=0)

            self.menu_change_refdate = newMenu(self.menu_refdate, tearoff=0)
            self.menu_refdate['menu'] = self.menu_change_refdate
            self.menu_change_refdate.add_command(label='Select refdate', command=self.change_refdate)

        def menu_log():

            self.window_check_logs = None

            self.menu_log = newMenuButton(self.frame_menu, text='Log', bootstyle="light")
            self.menu_log.grid(row=0, column=1, padx=0, pady=0)

            self.menu_check_log = newMenu(self.menu_log, tearoff=0)
            self.menu_log['menu'] = self.menu_check_log
            self.menu_check_log.add_command(label='Check Logs', command=self.open_check_logs)

        def menu_ferramentas():

            def comando_get_token():
                self.process_manager.janelaToken()

            def comando_tela_cadastro():
                self.sistema_cadastro = TelaCadastro(
                    self, manager_sql=self.manager_sql, funcoes_pytools=self.funcoes_pytools)

            self.menu_ferramentas = newMenuButton(self.frame_menu, text='Ferramentas', bootstyle="light")
            self.menu_ferramentas.grid(row=0, column=2, padx=0, pady=0)

            self.menu_ferramentas_menu = newMenu(self.menu_ferramentas, tearoff=0)
            self.menu_ferramentas['menu'] = self.menu_ferramentas_menu
            self.menu_ferramentas_menu.add_command(label='Cadastro Ativos', command=comando_tela_cadastro)
            self.menu_ferramentas_menu.add_command(label='Get Token', command=comando_get_token)

        def menu_temas():

            def comando_darkly():
                self.style.theme_use('darkly')

            def comando_superhero():
                self.style.theme_use('superhero')

            def comando_cyborg():
                self.style.theme_use('cyborg')

            def comando_solar():
                self.style.theme_use('solar')

            def comando_flatly():
                self.style.theme_use('flatly')

            def comando_cosmo():
                self.style.theme_use('cosmo')

            def comando_journal():
                self.style.theme_use('journal')

            def comando_litera():
                self.style.theme_use('litera')

            def comando_materia():
                self.style.theme_use('materia')

            def comando_sandstone():
                self.style.theme_use('sandstone')

            def comando_united():
                self.style.theme_use('united')

            def comando_yeti():
                self.style.theme_use('yeti')

            def comando_vapor():
                self.style.theme_use('vapor')

            def comando_lumen():
                self.style.theme_use('lumen')

            def comando_minty():
                self.style.theme_use('minty')

            def comando_pulse():
                self.style.theme_use('pulse')

            def comando_morph():
                self.style.theme_use('morph')

            def comando_cerculean():
                self.style.theme_use('cerculean')

            self.menus_temas = newMenuButton(self.frame_menu, text='Temas', bootstyle="light")
            self.menus_temas.grid(row=0, column=3, padx=0, pady=0)

            self.menus_temas_menu = newMenu(self.menus_temas, tearoff=0)
            self.menus_temas['menu'] = self.menus_temas_menu

            self.menu_dark = newMenu(self.menus_temas_menu, tearoff=0)
            self.menu_light = newMenu(self.menus_temas_menu, tearoff=0)

            self.menus_temas_menu.add_cascade(label='Dark', menu=self.menu_dark)
            self.menus_temas_menu.add_cascade(label='Light', menu=self.menu_light)

            self.menu_dark.add_command(label='Darkly', command=comando_darkly)
            self.menu_dark.add_command(label='Superhero', command=comando_superhero)
            self.menu_dark.add_command(label='Cyborg', command=comando_cyborg)
            self.menu_dark.add_command(label='Solar', command=comando_solar)
            self.menu_dark.add_command(label='Vapor', command=comando_vapor)

            self.menu_light.add_command(label='Flatly', command=comando_flatly)
            self.menu_light.add_command(label='Cosmo', command=comando_cosmo)
            self.menu_light.add_command(label='Journal', command=comando_journal)
            self.menu_light.add_command(label='Litera', command=comando_litera)
            self.menu_light.add_command(label='Materia', command=comando_materia)
            self.menu_light.add_command(label='Sandstone', command=comando_sandstone)
            self.menu_light.add_command(label='United', command=comando_united)
            self.menu_light.add_command(label='Yeti', command=comando_yeti)
            self.menu_light.add_command(label='Lumen', command=comando_lumen)
            self.menu_light.add_command(label='Minty', command=comando_minty)
            self.menu_light.add_command(label='Pulse', command=comando_pulse)
            self.menu_light.add_command(label='United', command=comando_united)
            self.menu_light.add_command(label='Morph', command=comando_morph)
            self.menu_light.add_command(label='Cerculean', command=comando_cerculean)

        def menu_info():

            def comando_versao_app():

                file_name = os.path.basename(__file__)  # noqa: F403, F405, E402

                Messagebox.show_info(
                    title="Info App",
                    message=(f"Versão App: {VERSION_APP} @ {datetime.strptime(VERSION_REFDATE, '%Y-%m-%d').strftime('%d/%m/%Y')}\n"
                             f"File Name App: {file_name}"))

            self.menu_info = newMenuButton(self.frame_menu, text='Info', bootstyle="light")
            self.menu_info.grid(row=0, column=4, padx=0, pady=0)

            self.menu_info_menu = newMenu(self.menu_info, tearoff=0)
            self.menu_info['menu'] = self.menu_info_menu
            self.menu_info_menu.add_command(label='Versão App', command=comando_versao_app)

        menu_refdate()
        menu_log()
        menu_ferramentas()
        menu_temas()
        menu_info()

    def config_app(self):

        self.title("Strix - Backoffice - Control Panel")
        self.geometry("800x600")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.frame_app = newFrame(self)
        self.frame_app.grid(row=1, column=0, sticky="nsew")
        self.frame_app.columnconfigure(0, weight=1)
        self.frame_app.rowconfigure(1, weight=1)

        self.frame_menu = newFrame(self, bootstyle="light")
        self.frame_menu.grid(row=0, column=0, sticky="ew")

        self.frame_top = newFrame(self.frame_app)
        self.frame_top.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 0))
        self.frame_top.columnconfigure(0, weight=1)

        newLabelTitle(self.frame_top, text=f"{ENVIRONMENT if ENVIRONMENT == "DEVELOPMENT" else 'Control Panel - Backoffice'}")\
            .grid(row=0, column=0, sticky="nswe")

        self.lbl_refdate = newLabelSubtitle(self.frame_top, text=f"Refdate: {self.refdate.strftime("%d/%m/%Y")}")
        self.lbl_refdate.grid(row=1, column=0, sticky="nswe")
        # newLabelSubtitle(self.frame_top, text=f"Refdate: {self.refdate.strftime("%d/%m/%Y")}").grid(row=1, column=0, sticky="nswe")

        self.frame_body = newFrame(self.frame_app)
        self.frame_body.grid(row=1, column=0, sticky="nsew")

    def open_check_logs(self):

        def on_close():
            self.window_check_logs.destroy()
            self.window_check_logs = None

        def create_window():

            if self.window_check_logs is not None and self.window_check_logs.winfo_exists():
                self.window_check_logs.lift()
            else:
                self.window_check_logs = Toplevel(title="Check Logs")
                self.window_check_logs.geometry("1024x600")
                self.window_check_logs.columnconfigure(0, weight=1)
                self.window_check_logs.rowconfigure(1, weight=1)
                self.window_check_logs.protocol("WM_DELETE_WINDOW", on_close)

        def widgets_check_logs():

            self.check_logs_filter_lvl_info = newBooleanVar(value=False)
            self.check_logs_filter_lvl_error = newBooleanVar(value=True)
            self.check_logs_filter_lvl_debug = newBooleanVar(value=False)

            frame_check_logs_top = newLabelFrame(self.window_check_logs, text='Pré Filtros')
            frame_check_logs_top.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))

            frame_check_logs_body = newFrame(self.window_check_logs)
            frame_check_logs_body.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
            frame_check_logs_body.columnconfigure(0, weight=1)
            frame_check_logs_body.rowconfigure(0, weight=1)

            self.entry_check_logs_filter_refdate = newDateEntry(frame_check_logs_top, bootstyle="secondary", startdate=self.refdate)
            self.entry_check_logs_filter_refdate.grid(row=0, column=0, sticky="w", padx=(10, 0), pady=(5, 5))

            self.btn_check_logs_filter_execute = newButton(frame_check_logs_top, text="Execute", command=lambda: check_logs_execute())
            self.btn_check_logs_filter_execute.grid(row=0, column=1, sticky="w", padx=(10, 10), pady=(5, 5))

            self.check_btn_check_logs_filter_lvl_info = newCheckButton(
                frame_check_logs_top, text="INFO", variable=self.check_logs_filter_lvl_info)

            self.check_btn_check_logs_filter_lvl_info.grid(row=0, column=2, sticky="w", padx=(10, 0), pady=(5, 5))

            self.check_btn_check_logs_filter_lvl_error = newCheckButton(
                frame_check_logs_top, text="ERROR", variable=self.check_logs_filter_lvl_error)

            self.check_btn_check_logs_filter_lvl_error.grid(row=0, column=3, sticky="w", padx=(10, 0), pady=(5, 5))

            self.check_btn_check_logs_filter_lvl_debug = newCheckButton(
                frame_check_logs_top, text="DEBUG", variable=self.check_logs_filter_lvl_debug)

            self.check_btn_check_logs_filter_lvl_debug.grid(row=0, column=4, sticky="w", padx=(10, 0), pady=(5, 5))

            self.tableview_check_logs = Tableview(
                frame_check_logs_body,
                searchable=True,
                autofit=True,
                paginated=False,
                height=20,
                coldata=['IndexLog', 'DateTimeRun', 'ScriptRun', 'ScriptMaster', 'LevelLog', 'Processo'])

            self.tableview_check_logs.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        def check_logs_execute():

            month_str = datetime.strptime(self.entry_check_logs_filter_refdate.entry.get(), "%d/%m/%Y").month
            day_str = datetime.strptime(self.entry_check_logs_filter_refdate.entry.get(), "%d/%m/%Y").day
            year_str = datetime.strptime(self.entry_check_logs_filter_refdate.entry.get(), "%d/%m/%Y").year

            if self.check_logs_filter_lvl_info.get() \
                    and self.check_logs_filter_lvl_error.get() \
                    and self.check_logs_filter_lvl_debug.get() \
                    or not self.check_logs_filter_lvl_info.get() \
                    and not self.check_logs_filter_lvl_error.get() \
                    and not self.check_logs_filter_lvl_debug.get():
                df_logs = self.manager_sql.select_dataframe(
                    f"SELECT INDEX_LOG, DATETIME_RUN, SCRIPT_RUN, NOME_SCRIPT, LEVEL_LOG, PROCESSO "
                    f"FROM TB_PYTHON_MY_LOGGER WHERE YEAR(DATETIME_RUN) = {year_str} "
                    f"AND MONTH(DATETIME_RUN) = {month_str} AND DAY(DATETIME_RUN) = {day_str} ORDER BY INDEX_LOG, DATETIME_RUN")
            else:
                level = ""
                if self.check_logs_filter_lvl_info.get():
                    level = level + "'INFO',"
                if self.check_logs_filter_lvl_error.get():
                    level = level + "'ERROR',"
                if self.check_logs_filter_lvl_debug.get():
                    level = level + "'DEBUG',"
                df_logs = self.manager_sql.select_dataframe(
                    f"SELECT INDEX_LOG, DATETIME_RUN, SCRIPT_RUN, NOME_SCRIPT, LEVEL_LOG, PROCESSO "
                    f"FROM TB_PYTHON_MY_LOGGER WHERE LEVEL_LOG IN ({level[:-1]}) AND YEAR(DATETIME_RUN) = {year_str} "
                    f"AND MONTH(DATETIME_RUN) = {month_str} AND DAY(DATETIME_RUN) = {day_str} ORDER BY INDEX_LOG, DATETIME_RUN")

            lista_logs = df_logs.values.tolist()

            self.tableview_check_logs.reset_table()
            self.tableview_check_logs.delete_rows(indices=None, iids=None)
            self.tableview_check_logs.insert_rows('end', lista_logs)
            self.tableview_check_logs.load_table_data()
            self.tableview_check_logs.autofit_columns()

        create_window()
        widgets_check_logs()

    def variaveis_widgets(self):

        self.opt_check_btn_upload_arquivos_xml = newBooleanVar(value=False)
        self.opt_check_btn_funds_adm_cotistas = newBooleanVar(value=False)
        self.opt_check_btn_funds_perf_cotistas = newBooleanVar(value=False)
        self.opt_check_btn_funds_perf_nav = newBooleanVar(value=False)
        self.opt_check_btn_download_carteiras_btg = newBooleanVar(value=False)
        self.opt_check_btn_update_indexadores = newBooleanVar(value=False)
        self.opt_check_btn_captura_arquivos_email = newBooleanVar(value=False)

        self.lista_opts_bases_carteiras = [
            self.opt_check_btn_upload_arquivos_xml,
            self.opt_check_btn_funds_adm_cotistas,
            self.opt_check_btn_funds_perf_cotistas,
            self.opt_check_btn_funds_perf_nav,
            self.opt_check_btn_download_carteiras_btg,
            self.opt_check_btn_update_indexadores,
            self.opt_check_btn_captura_arquivos_email
        ]

    def widgets(self):

        def processos_automatizados():

            def run_loop_btg():
                self.auto_process_manager.widgets_loop_btg()

                if not self.auto_process_manager.loop_carteiras_btg_oppened:
                    threading.Thread(
                        target=self.auto_process_manager.loop_status_carteiras_btg,
                        name='processo_loop_btg_status_carteiras').start()

                if not self.auto_process_manager.loop_bases_btg_oppened:
                    threading.Thread(
                        target=self.auto_process_manager.loop_status_bases_btg,
                        name='processo_loop_btg_bases_btg').start()

            frame_processos_automatizados = newLabelFrame(self.frame_body, text="Processos Automatizados")
            frame_processos_automatizados.grid(row=0, column=0, sticky='ns', padx=(10, 0), pady=(10, 0))
            frame_processos_automatizados.columnconfigure(0, weight=1)

            btn_loop_btg = newButton(frame_processos_automatizados, text="Loop BTG", bootstyle="secondary", command=run_loop_btg)
            btn_loop_btg.grid(row=1, column=0, sticky="we", padx=(10, 10), pady=(10, 10))

        def bases_carteiras():

            def run_bases_carteiras():
                threading.Thread(target=self.process_manager.processos_bases_carterias, name='bases_carteiras').start()

            frame_bases_btg = newLabelFrame(self.frame_body, text="Bases Carteiras")
            frame_bases_btg.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=(10, 0))
            frame_bases_btg.columnconfigure(0, weight=1)

            frame_top = newFrame(frame_bases_btg)
            frame_top.grid(row=0, column=0, sticky="ew")

            frame_check_box = newFrame(frame_bases_btg)
            frame_check_box.grid(row=1, column=0, sticky="nsew")

            newButton(frame_top, text="Executar", command=lambda: run_bases_carteiras())\
                .grid(row=0, column=0, sticky="w", padx=(10, 0), pady=(10, 10))

            self.entry_refdate_bases_carteiras = newDateEntry(
                frame_top, bootstyle="secondary", startdate=self.funcoes_pytools.workday_br(self.refdate, -1))

            self.entry_refdate_bases_carteiras.grid(row=0, column=1, sticky="w", padx=(10, 10), pady=(10, 10))

            newCheckButton(frame_check_box, text="Upload arquivos XML", variable=self.opt_check_btn_upload_arquivos_xml)\
                .grid(row=0, column=0, sticky="w", padx=(10, 0), pady=(0, 10))

            newCheckButton(frame_check_box, text="Funds Perf Cotistas", variable=self.opt_check_btn_funds_perf_cotistas)\
                .grid(row=0, column=1, sticky="w", padx=(10, 10), pady=(0, 10))

            newCheckButton(frame_check_box, text="Funds Adm Cotistas", variable=self.opt_check_btn_funds_adm_cotistas)\
                .grid(row=1, column=0, sticky="w", padx=(10, 0), pady=(0, 10))

            newCheckButton(frame_check_box, text="Funds Perf NAV", variable=self.opt_check_btn_funds_perf_nav)\
                .grid(row=1, column=1, sticky="w", padx=(10, 10), pady=(0, 10))

            newCheckButton(frame_check_box, text="Update indexadores", variable=self.opt_check_btn_update_indexadores)\
                .grid(row=2, column=1, sticky="w", padx=(10, 10), pady=(0, 10))

            newCheckButton(frame_check_box, text="Arquivos Email", variable=self.opt_check_btn_captura_arquivos_email)\
                .grid(row=2, column=0, sticky="w", padx=(10, 0), pady=(0, 10))

            newCheckButton(frame_check_box, text="Donwload Carteiras BTG", variable=self.opt_check_btn_download_carteiras_btg)\
                .grid(row=3, column=0, sticky="w", padx=(10, 0), pady=(0, 10))

        def outras_bases():

            def run_outras_bases():
                if self.opt_check_btn_anbima_debentures.get() \
                        or self.opt_check_btn_curvas_b3.get() \
                        or self.opt_check_btn_cdi_selic_b3.get():
                    threading.Thread(target=self.process_manager.processos_outras_bases, name='outras_bases').start()

            self.opt_check_btn_anbima_debentures = newBooleanVar(value=False)
            self.opt_check_btn_curvas_b3 = newBooleanVar(value=False)
            self.opt_check_btn_cdi_selic_b3 = newBooleanVar(value=False)

            frame_outras_bases = newLabelFrame(self.frame_body, text="Upload Outras Bases")
            frame_outras_bases.grid(row=0, column=2, sticky="nsew", padx=(10, 0), pady=(10, 0))
            frame_outras_bases.columnconfigure(0, weight=1)

            frame_top = newFrame(frame_outras_bases)
            frame_top.grid(row=0, column=0, sticky="ew")

            frame_check_box = newFrame(frame_outras_bases)
            frame_check_box.grid(row=1, column=0, sticky="nsew")

            newButton(frame_top, text="Executar", command=lambda: run_outras_bases())\
                .grid(row=0, column=0, sticky="w", padx=(10, 0), pady=(10, 10))

            self.entry_refdate_outras_bases = newDateEntry(
                frame_top, bootstyle="secondary", startdate=self.funcoes_pytools.workday_br(self.refdate, -1))

            self.entry_refdate_outras_bases.grid(row=0, column=1, sticky="w", padx=(10, 10), pady=(10, 10))

            newCheckButton(frame_check_box, text="Anbima Debêntures",
                    variable=self.opt_check_btn_anbima_debentures)\
                .grid(row=0, column=0, sticky="w", padx=(10, 0), pady=(0, 10))

            newCheckButton(frame_check_box, text="Curvas B3",
                    variable=self.opt_check_btn_curvas_b3)\
                .grid(row=1, column=0, sticky="w", padx=(10, 0), pady=(0, 10))

            newCheckButton(frame_check_box, text="CDI & Selic B3",
                    variable=self.opt_check_btn_cdi_selic_b3)\
                .grid(row=2, column=0, sticky="w", padx=(10, 0), pady=(0, 10))

        def open_excell():

            self.frame_planilhas_excel = newLabelFrame(self.frame_body, text="Processos Planilhas")
            self.frame_planilhas_excel.grid(row=1, column=0, sticky="nsew", padx=(10, 0), pady=(10, 0))
            self.frame_planilhas_excel.columnconfigure(0, weight=1)

            newButton(self.frame_planilhas_excel, text="Control Panel", command=lambda: self.process_manager.open_excel_control_panel())\
                .grid(row=0, column=0, sticky="we", padx=(10, 10), pady=(10, 0))

            newButton(self.frame_planilhas_excel, text="Carteiras Fundos",
                      command=lambda: self.process_manager.open_excel_carteira_fundos())\
                .grid(row=1, column=0, sticky="we", padx=(10, 10), pady=(10, 0))

            newButton(self.frame_planilhas_excel, text="Curvas BBG", command=lambda: self.process_manager.open_excel_upload_curvas_bbg())\
                .grid(row=2, column=0, sticky="we", padx=(10, 10), pady=(10, 10))

        def calculadora_ativos():

            def run_calculadora_ativos():
                threading.Thread(target=self.process_manager.run_calculadora_ativos, name='calculadora_ativos').start()

            def call_var_widgets():

                self.opt_check_btn_curva_di1fut = newBooleanVar(value=False)
                self.opt_check_btn_anbima_debs = newBooleanVar(value=False)
                self.opt_check_btn_cdi = newBooleanVar(value=False)
                self.opt_check_btn_selic = newBooleanVar(value=False)
                self.opt_check_btn_carteira_yield_master = newBooleanVar(value=False)

                self.txt_status_calculadora_curva_di1fut = newStringVar(value="❌ Curva DI1FUT")
                self.txt_status_calculadora_anbima_debs = newStringVar(value="❌ Anbima Debentures")
                self.txt_status_calculadora_cdi = newStringVar(value="❌ Cota CDI")
                self.txt_status_calculadora_selic = newStringVar(value="❌ Cota SELIC")
                self.txt_status_calculadora_carteira_yield_master = newStringVar(value="❌ Cota Yield Master")

                self.lbl_calculadora_ativos_di1fut = newLabelStatus(frame_check_box, textvariable=self.txt_status_calculadora_curva_di1fut)
                self.lbl_calculadora_ativos_di1fut.grid(row=0, column=0, sticky="w", padx=(10, 0), pady=(10, 0))

                self.lbl_calculadora_ativos_anbima_debs = newLabelStatus(
                    frame_check_box, textvariable=self.txt_status_calculadora_anbima_debs)
                self.lbl_calculadora_ativos_anbima_debs.grid(row=1, column=0, sticky="w", padx=(10, 0), pady=(0, 0))

                self.lbl_calculadora_ativos_yield_master = newLabelStatus(
                    frame_check_box, textvariable=self.txt_status_calculadora_carteira_yield_master)
                self.lbl_calculadora_ativos_yield_master.grid(row=2, column=0, sticky="w", padx=(10, 0), pady=(0, 10))

                self.lbl_calculadora_ativos_cdi = newLabelStatus(frame_check_box, textvariable=self.txt_status_calculadora_cdi)
                self.lbl_calculadora_ativos_cdi.grid(row=0, column=1, sticky="w", padx=(5, 10), pady=(10, 0))

                self.lbl_calculadora_ativos_selic = newLabelStatus(frame_check_box, textvariable=self.txt_status_calculadora_selic)
                self.lbl_calculadora_ativos_selic.grid(row=1, column=1, sticky="w", padx=(5, 10), pady=(0, 0))

            frame_calculadora_ativos = newLabelFrame(self.frame_body, text="Calculadora Ativos")
            frame_calculadora_ativos.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=(10, 0))
            frame_calculadora_ativos.columnconfigure(0, weight=1)

            frame_top = newFrame(frame_calculadora_ativos)
            frame_top.grid(row=0, column=0, sticky="new")
            frame_top.columnconfigure(0, weight=1)

            self.entry_refdate_calculadora = newDateEntry(
                frame_top, startdate=self.funcoes_pytools.workday_br(self.refdate, -1))

            self.entry_refdate_calculadora.grid(row=0, column=0, sticky="nwe", padx=(10, 10), pady=(10, 0))

            frame_botoes = newFrame(frame_top)
            frame_botoes.grid(row=1, column=0, sticky="ew")
            frame_botoes.columnconfigure(0, weight=1)
            frame_botoes.columnconfigure(1, weight=1)

            btn_run_check_bases = newButton(frame_botoes, text="Check Bases", command=lambda: self.process_manager.call_status_all_bases())
            btn_run_check_bases.grid(row=0, column=0, sticky="we", padx=(10, 0), pady=(10, 10))

            btn_run_calculadora = newButton(frame_botoes, text="  Executar  ", command=run_calculadora_ativos)
            btn_run_calculadora.grid(row=0, column=1, sticky="we", padx=(10, 10), pady=(10, 10))

            btn_run_reconciliacao = newButton(frame_botoes, text="Recon", command=lambda: self.process_manager.recon_calculadora_ativos())
            btn_run_reconciliacao.grid(row=1, column=0, sticky="we", padx=(10, 10), pady=(0, 0), columnspan=2)

            frame_check_box = newFrame(frame_calculadora_ativos)
            frame_check_box.grid(row=1, column=0, sticky="we")

            call_var_widgets()

        def status_bases():

            def call_var_widgets():

                self.txt_status_bases_curvas_b3 = newStringVar(value="❌ Curvas B3")
                self.txt_status_bases_imabjust = newStringVar(value="❌ IMABJUST")
                self.txt_status_bases_imab = newStringVar(value="❌ IMA-B")
                self.txt_status_bases_selic = newStringVar(value="❌ SELIC")
                self.txt_status_bases_calculadora = newStringVar(value="❌ Calculadora")
                self.txt_status_bases_cdi = newStringVar(value="❌ CDI")
                self.txt_status_bases_perf_nav = newStringVar(value="❌ Perf NAV")
                self.txt_status_bases_perf_cotistas = newStringVar(value="❌ Perf Cotistas")
                self.txt_status_bases_adm_cotistas = newStringVar(value="❌ Adm Cotistas")
                self.txt_status_bases_xml_carteiras = newStringVar(value="❌ XML Carteiras")
                self.txt_status_bases_anbima_debentures = newStringVar(value="❌ Anbima Debêntures")

                self.lbl_status_bases_curvasb3 = newLabelStatus(frame_check_box, textvariable=self.txt_status_bases_curvas_b3)
                self.lbl_status_bases_curvasb3.grid(row=0, column=0, sticky="w", padx=(10, 0), pady=(5, 0))

                self.lbl_status_bases_anbima_debentures = newLabelStatus(
                    frame_check_box, textvariable=self.txt_status_bases_anbima_debentures)
                self.lbl_status_bases_anbima_debentures.grid(row=1, column=0, sticky="w", padx=(10, 0), pady=(0, 0))

                self.lbl_status_bases_xml_carteiras = newLabelStatus(frame_check_box, textvariable=self.txt_status_bases_xml_carteiras)
                self.lbl_status_bases_xml_carteiras.grid(row=2, column=0, sticky="w", padx=(10, 0), pady=(0, 0))

                self.lbl_status_bases_perf_nav = newLabelStatus(frame_check_box, textvariable=self.txt_status_bases_perf_nav)
                self.lbl_status_bases_perf_nav.grid(row=3, column=0, sticky="w", padx=(10, 0), pady=(0, 0))

                self.lbl_status_bases_perf_cotistas = newLabelStatus(frame_check_box, textvariable=self.txt_status_bases_perf_cotistas)
                self.lbl_status_bases_perf_cotistas.grid(row=4, column=0, sticky="w", padx=(10, 0), pady=(0, 0))

                self.lbl_status_bases_adm_cotistas = newLabelStatus(frame_check_box, textvariable=self.txt_status_bases_adm_cotistas)
                self.lbl_status_bases_adm_cotistas.grid(row=5, column=0, sticky="w", padx=(10, 0), pady=(0, 10))

                self.lbl_status_bases_imabjust = newLabelStatus(frame_check_box, textvariable=self.txt_status_bases_imabjust)
                self.lbl_status_bases_imabjust.grid(row=0, column=1, sticky="w", padx=(5, 10), pady=(5, 0))

                self.lbl_status_bases_imab = newLabelStatus(frame_check_box, textvariable=self.txt_status_bases_imab)
                self.lbl_status_bases_imab.grid(row=1, column=1, sticky="w", padx=(5, 10), pady=(0, 0))

                self.lbl_status_bases_cdi = newLabelStatus(frame_check_box, textvariable=self.txt_status_bases_cdi)
                self.lbl_status_bases_cdi.grid(row=2, column=1, sticky="w", padx=(5, 10), pady=(0, 0))

                self.lbl_status_bases_selic = newLabelStatus(frame_check_box, textvariable=self.txt_status_bases_selic)
                self.lbl_status_bases_selic.grid(row=3, column=1, sticky="w", padx=(5, 10), pady=(0, 0))

                self.lbl_status_bases_calculadora = newLabelStatus(frame_check_box, textvariable=self.txt_status_bases_calculadora)
                self.lbl_status_bases_calculadora.grid(row=4, column=1, sticky="w", padx=(5, 10), pady=(0, 0))

            frame_status_bases = newLabelFrame(self.frame_body, text="Status Bases")
            frame_status_bases.grid(row=1, column=2, sticky="nsew", padx=(10, 0), pady=(10, 0))
            frame_status_bases.columnconfigure(0, weight=1)

            frame_top = newFrame(frame_status_bases)
            frame_top.grid(row=0, column=0, sticky="new")

            frame_check_box = newFrame(frame_status_bases)
            frame_check_box.grid(row=1, column=0, sticky="nsew")

            self.entry_refdate_status_bases = newDateEntry(
                frame_top, startdate=self.funcoes_pytools.workday_br(self.refdate, -1))

            self.entry_refdate_status_bases.grid(row=0, column=1, sticky="nw", padx=(10, 10), pady=(10, 0))

            btn_run_check_bases = newButton(frame_top, text="Executar", command=lambda: self.process_manager.call_status_all_bases())
            # btn_run_check_bases = newButton(frame_top, text="Executar", command=lambda: self.process_manager.status_bases())
            btn_run_check_bases.grid(row=0, column=0, sticky="nw", padx=(10, 0), pady=(10, 10))

            call_var_widgets()

        processos_automatizados()
        bases_carteiras()
        outras_bases()
        open_excell()
        calculadora_ativos()
        status_bases()


if __name__ == "__main__":
    app = App()
