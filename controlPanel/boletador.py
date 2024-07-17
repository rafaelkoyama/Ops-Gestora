from __init__ import *

VERSION_APP = "1.0.1"
VERSION_REFDATE = "2024-07-01"
ENVIRONMENT = os.getenv("ENVIRONMENT")
SCRIPT_NAME = os.path.basename(__file__)
CONNECT_MANAGER_BTG = True

if ENVIRONMENT == "DEVELOPMENT":
    print(f"{SCRIPT_NAME.upper()} - {ENVIRONMENT} - {VERSION_APP} - {VERSION_REFDATE}")

append_paths()

#-----------------------------------------------------------------------

try:

    from datetime import date, datetime
    from tkinter import StringVar

    import numpy as np
    import pandas as pd
    from ttkbootstrap import Separator, Toplevel, Window
    from ttkbootstrap.constants import *
    from ttkbootstrap.tableview import Tableview

    from controlPanel.biblioteca_widgets import (
        Messagebox,
        newBooleanVar,
        newButton,
        newCombobox,
        newDateEntry,
        newEntry,
        newFrame,
        newLabelFrame,
        newLabelStatus,
        newLabelSubtitle,
        newLabelTitle,
        newMenu,
        newMenuButton,
        newRadioButton,
        newScrolledText,
        newStringVar,
    )
    from tools.db_helper import SQL_Manager
    from tools.py_tools import FuncoesPyTools

except Exception as e:
    print(e)


class BoletadorAPP(Window if __name__ == "__main__" else Toplevel):

    def __init__(self, app=None, manager_sql=None, funcoes_pytools=None, *args, **kwargs):
        if isinstance(self, Window):
            super().__init__(themename='vapor', *args, **kwargs)
        else:
            super().__init__(*args, **kwargs)

        if manager_sql is None:
            self.manager_sql = SQL_Manager()
        else:
            self.manager_sql = manager_sql

        if funcoes_pytools is None:
            self.funcoes_pytools = FuncoesPyTools(self.manager_sql)
        else:
            self.funcoes_pytools = funcoes_pytools

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.app = app

        if self.app is None:
            self.refdate = date.today()
        else:
            self.refdate = self.app.refdate

        self.lista_fundos = ['Strix Yield Master']
        self.lista_tipo_ativos = ['Debênture', 'CCB', 'CDB', 'LF', 'LFSC', 'LFSN', 'LFSN-PRE']

        self.refdate = date.today()

        self.config_app()
        self.config_menu()
        BoletadorBTG(app=self, manager_sql=self.manager_sql, funcoes_pytools=self.funcoes_pytools)
        self.mainloop()

    def on_close(self):
        self.destroy()

    def set_refdate(self, refdate: date):

        self.refdate = refdate
        self.lbl_refdate.configure(text=f"Refdate Boletador: {self.refdate.strftime('%d/%m/%Y')}")

    def config_app(self):

        self.title("BackOffice Systems")
        self.geometry("625x200")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self.frame_menu = newFrame(self, bootstyle="light")
        self.frame_menu.grid(row=0, column=0, sticky="ew")

        frame_header = newFrame(self)
        frame_header.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        frame_header.columnconfigure(0, weight=1)

        newLabelTitle(frame_header, text=f"{"DESENVOLVIMENTO" if ENVIRONMENT == 'DEVELOPMENT' else "Boletador Operações"}")\
            .grid(row=0, column=0, sticky="ew")

        self.lbl_refdate = newLabelSubtitle(frame_header, text=f"Refdate Boletador: {self.refdate.strftime('%d/%m/%Y')}")
        self.lbl_refdate.grid(row=1, column=0, sticky="ew")

        newLabelSubtitle(frame_header, text=f"Usuário: {str_user}").grid(row=2, column=0, sticky="ew")

        Separator(frame_header, orient="horizontal").grid(row=3, column=0, sticky="ew", pady=(10, 0))

        self.frame_body = newFrame(self)
        self.frame_body.grid(row=2, column=0, sticky="nsew")
        self.frame_body.columnconfigure(0, weight=1)
        self.frame_body.rowconfigure(2, weight=1)

    def config_menu(self):

        def menu_tela():

            self.menu_tela = newMenuButton(self.frame_menu, text='Opt Tela', bootstyle="light")
            self.menu_tela.grid(row=0, column=0, padx=0, pady=0)
            
            self.menu_change_tela = newMenu(self.menu_tela, tearoff=0)
            self.menu_tela['menu'] = self.menu_change_tela

            self.menu_change_tela.add_command(
                label='Interno',
                command=lambda: BoletadorInterno(app=self, manager_sql=self.manager_sql, funcoes_pytools=self.funcoes_pytools))

            self.menu_change_tela.add_command(
                label='BTG FaaS',
                command=lambda: BoletadorBTG(app=self, manager_sql=self.manager_sql, funcoes_pytools=self.funcoes_pytools))

        menu_tela()


class BoletadorBTG:

    def __init__(self, app=None, manager_sql=None, funcoes_pytools=None):

        self.app = app

        self.manager_sql = manager_sql
        self.funcoes_pytools = funcoes_pytools

        self.lista_fundos = self.app.lista_fundos
        self.lista_tipo_ativos = self.app.lista_tipo_ativos

        # self.process_manager = ProcessManagerBTG(
        #     app=self,
        #     manager_sql=self.manager_sql,
        #     funcoes_pytools=self.funcoes_pytools)
        
        self.set_refdate()
        self.frame_body()
        self.labelFrames()
        self.grid_labelFrames()
        self.widgets()
        self.grid_widgets()

        self.process_manager = ProcessManagerBTG(
            app=self,
            manager_sql=self.manager_sql,
            funcoes_pytools=self.funcoes_pytools)



        self.app.geometry("1090x850")

    def set_refdate(self):

        self.refdate = date.today()
        self.app.set_refdate(self.refdate)

    def frame_body(self):

        self.app.frame_body.destroy()

        self.app.frame_body = newFrame(self.app)
        self.app.frame_body.grid(row=2, column=0, sticky="nsew")
        self.app.frame_body.columnconfigure(0, weight=1)
        self.app.frame_body.rowconfigure(1, weight=1)

        self.frame_body = self.app.frame_body

    def labelFrames(self):

        self.frame_controle = newFrame(self.frame_body)
        self.frame_controle.grid(row=0, column=0, sticky="ew")
        self.frame_controle.columnconfigure(0, weight=1)

        self.frame_tabelas = newFrame(self.frame_body)
        self.frame_tabelas.grid(row=1, column=0, sticky="nsew")
        self.frame_tabelas.columnconfigure(0, weight=1)
        self.frame_tabelas.columnconfigure(1, weight=1)
        self.frame_tabelas.columnconfigure(2, weight=1)
        self.frame_tabelas.rowconfigure(0, weight=1)
        self.frame_tabelas.rowconfigure(1, weight=1)

        self.frame_botoes_controle = newLabelFrame(self.frame_controle, text="Controle")

        self.frame_boletas_internas = newLabelFrame(self.frame_tabelas, text="Histórico Boletas")
        self.frame_boletas_btg = newLabelFrame(self.frame_tabelas, text="Histórico Boletas BTG")
        self.frame_boletas_pendentes = newLabelFrame(self.frame_tabelas, text="Boletas Pendentes")

    def grid_labelFrames(self):

        self.frame_botoes_controle.grid(row=0, column=0, sticky="ew", padx=(10,10), pady=(10,0))

        self.frame_boletas_pendentes.grid(row=0, column=0, sticky="nsew", padx=(10,0), pady=(10,0))
        self.frame_boletas_pendentes.columnconfigure(0, weight=1)
        self.frame_boletas_pendentes.rowconfigure(0, weight=1)

        self.frame_boletas_btg.grid(row=0, column=1, sticky="nsew", padx=10, pady=(10,0), columnspan=2)
        self.frame_boletas_btg.columnconfigure(0, weight=1)
        self.frame_boletas_btg.rowconfigure(0, weight=1)

        self.frame_boletas_internas.grid(row=1, column=0, sticky="nsew", padx=10, pady=(10,10), columnspan=3)
        self.frame_boletas_internas.columnconfigure(0, weight=1)
        self.frame_boletas_internas.rowconfigure(0, weight=1)

    def widgets(self):

        self.btn_refresh = newButton(self.frame_botoes_controle, text="Refresh", width=15)
        self.btn_boletagem = newButton(self.frame_botoes_controle, text="Boletar", width=15)

        self.tabela_boletas_internas = Tableview(
            self.frame_boletas_internas,
            searchable=False,
            autofit=True,
            paginated=False,
            autoalign=True,
            coldata=[
                {"text": "ID Interno", "stretch": True},
                {"text": "Trade Date", "stretch": True},
                {"text": "Fundo", "stretch": True},
                {"text": "Tipo Ativo", "stretch": True},
                {"text": "Ativo", "stretch": True},
                {"text": "C/V", "stretch": True},
                {"text": "Quantidade", "stretch": True},
                {"text": "PU", "stretch": True},
                {"text": "Taxa", "stretch": True},
                {"text": "Broker", "stretch": True}
                ])

        self.tabela_status_btg = Tableview(
            self.frame_boletas_btg,
            searchable=False,
            autofit=True,
            paginated=False,
            autoalign=True,
            coldata=[
                {"text": "ID Interno", "stretch": True},
                {"text": "ID BTG", "stretch": True},
                {"text": "Status", "stretch": True},
                {"text": "Hora Boletagem", "stretch": True}
                ])

        self.tabela_pendentes = Tableview(
            self.frame_boletas_pendentes,
            searchable=False,
            autofit=True,
            paginated=False,
            autoalign=True,
            coldata=[
                {"text": "ID Interno", "stretch": True},
                {"text": "Fundo", "stretch": True},
                {"text": "Ativo", "stretch": True}
                ])

    def grid_widgets(self):

        self.btn_refresh.grid(row=0, column=0, sticky="w", padx=(10,0), pady=(10,10))
        self.btn_boletagem.grid(row=0, column=1, sticky="w", padx=(10,10), pady=(10,10))

        self.tabela_boletas_internas.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.tabela_status_btg.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.tabela_pendentes.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

class ProcessManagerBTG:

    def __init__(self, app=None, manager_sql=None, funcoes_pytools=None):

        self.app = app
        self.manager_sql = manager_sql
        self.funcoes_pytools = funcoes_pytools

        self.lista_fundos = self.app.app.lista_fundos
        self.lista_tipo_ativos = self.app.app.lista_tipo_ativos

        self.str_fundos = "', '".join(self.lista_fundos)
        self.str_tipo_ativos = "', '".join(self.lista_tipo_ativos)

        if ENVIRONMENT == 'DEVELOPMENT':
            self.tb_boletas = "TB_BOLETAS_TESTE"
        else:
            self.tb_boletas = "TB_BOLETAS"

        self.comando_boletas_internas()

    def comando_boletas_internas(self):

        lista_boletas = self.manager_sql.select_dataframe(
            f"SELECT ID, TRADE_DATE, FUNDO, TIPO_ATIVO, ATIVO, C_V, QUANTIDADE, PU, TAXA, NOME_BROKER "
            f"FROM {self.tb_boletas} WHERE TRADE_DATE = '{self.app.refdate.strftime('%Y-%m-%d')}' "
            f"AND FUNDO IN ('{self.str_fundos}') AND TIPO_ATIVO IN ('{self.str_tipo_ativos}') "
            f"ORDER BY ID").values.tolist()

        self.app.tabela_boletas_internas.reset_table()
        self.app.tabela_boletas_internas.delete_rows(indices=None, iids=None)
        self.app.tabela_boletas_internas.insert_rows('end', lista_boletas)
        self.app.tabela_boletas_internas.load_table_data()
        self.app.tabela_boletas_internas.autoalign_columns()
        self.app.tabela_boletas_internas.autofit_columns()


class BoletadorInterno:

    def __init__(self, app=None, manager_sql=None, funcoes_pytools=None):

        self.app = app

        self.manager_sql = manager_sql
        self.funcoes_pytools = funcoes_pytools

        self.lista_fundos = self.app.lista_fundos
        self.lista_tipo_ativos = self.app.lista_tipo_ativos

        self.refdate = self.app.refdate

        self.process_manager = ProcessManagerInterno(
            app=self,
            manager_sql=self.manager_sql,
            funcoes_pytools=self.funcoes_pytools)

        self.frame_body()
        self.variaveis()
        self.controle_variaveis()
        self.labelFrames()
        self.grid_labelFrames()
        self.frames_widgets()
        self.widgets()
        self.controle_widgets()
        self.grid_widgets()
        self.values_boxes()
        self.update_broker()
        self.process_manager.comando_consulta_boletas()

        self.app.geometry("1090x850")

    def set_refdate(self, refdate):

        self.refdate = refdate

        self.app.set_refdate(self.refdate)

    def frame_body(self):

        self.app.frame_body.destroy()

        self.app.frame_body = newFrame(self.app)
        self.app.frame_body.grid(row=2, column=0, sticky="nsew")
        self.app.frame_body.columnconfigure(0, weight=1)
        self.app.frame_body.rowconfigure(2, weight=1)

        self.frame_body = self.app.frame_body

    def update_broker(self):

        self.lista_brokers = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT NOME_BROKER FROM TB_CADASTRO_BROKER ORDER BY NOME_BROKER")['NOME_BROKER'].tolist()

        self.dict_cnpj_broker = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT NOME_BROKER, CNPJ_BROKER "
            f"FROM TB_CADASTRO_BROKER").set_index('NOME_BROKER')['CNPJ_BROKER'].to_dict()
        
        self.dict_boletas_broker = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT NOME_BROKER, BOLETAS_BROKER "
            f"FROM TB_CADASTRO_BROKER").set_index('NOME_BROKER')['BOLETAS_BROKER'].to_dict()
        
        self.entry_broker['values'] = self.lista_brokers

    def values_boxes(self):

        self.entry_fundo['values'] = self.lista_fundos
        self.entry_tipo_ativo['values'] = self.lista_tipo_ativos

    def variaveis(self):

        self.fundo = StringVar()
        self.tipo_ativo = StringVar()
        self.ativo = StringVar()
        self.cv = StringVar()
        self.quantidade = StringVar()
        self.pu = StringVar()
        self.taxa = StringVar()
        self.broker = StringVar()
        self.cnpj_broker = StringVar()

    def controle_variaveis(self):

        self.tipo_ativo.trace_add('write', self.process_manager.controle_entry_tipo_ativo)
        self.broker.trace_add('write', self.process_manager.controle_entry_broker)

    def controle_widgets(self):

        self.entry_quantidade.bind("<FocusOut>", self.process_manager.check_quantidade)
        self.entry_pu.bind("<FocusOut>", self.process_manager.check_pu)
        self.entry_taxa.bind("<FocusOut>", self.process_manager.check_taxa)

    def labelFrames(self):

        self.frame_controle = newFrame(self.frame_body)
        self.frame_controle.grid(row=0, column=0, sticky="ew")
        self.frame_controle.columnconfigure(0, weight=1)
        self.frame_controle.columnconfigure(1, weight=1)

        self.frame_refdate = newLabelFrame(self.frame_controle, text="Refdate")
        self.frame_botoes_controle = newLabelFrame(self.frame_controle, text="Controle")

        self.frame_dados_boleta = newLabelFrame(self.frame_body, text="Dados Boleta")
        self.frame_historico_boletagem = newLabelFrame(self.frame_body, text="Histórico Boletagem")

    def grid_labelFrames(self):

        self.frame_refdate.grid(row=0, column=0, sticky="ew", padx=(10,0), pady=(10,0))
        self.frame_botoes_controle.grid(row=0, column=1, sticky="ew", padx=(10,10), pady=(10,0))

        self.frame_dados_boleta.grid(row=1, column=0, sticky="nsew", padx=10, pady=(10,0))
        self.frame_dados_boleta.columnconfigure(0, weight=1)
        self.frame_dados_boleta.columnconfigure(1, weight=1)
        self.frame_dados_boleta.columnconfigure(2, weight=1)
        self.frame_dados_boleta.columnconfigure(3, weight=1)

        self.frame_historico_boletagem.grid(row=2, column=0, sticky="nsew", padx=10, pady=(10,10))
        self.frame_historico_boletagem.columnconfigure(0, weight=1)
        self.frame_historico_boletagem.rowconfigure(0, weight=1)

    def frames_widgets(self):

        self.frame_fundo = newFrame(self.frame_dados_boleta)
        self.frame_fundo.columnconfigure(0, weight=1)

        self.frame_ativo = newFrame(self.frame_dados_boleta)
        self.frame_ativo.columnconfigure(0, weight=1)

        self.frame_quantidade = newFrame(self.frame_dados_boleta)
        self.frame_quantidade.columnconfigure(0, weight=1)

        self.frame_pu = newFrame(self.frame_dados_boleta)
        self.frame_pu.columnconfigure(0, weight=1)

        self.frame_taxa = newFrame(self.frame_dados_boleta)
        self.frame_taxa.columnconfigure(0, weight=1)

        self.frame_cv = newFrame(self.frame_dados_boleta)
        self.frame_cv.columnconfigure(0, weight=1)

        self.frame_broker = newFrame(self.frame_dados_boleta)
        self.frame_broker.columnconfigure(0, weight=10)
        self.frame_broker.columnconfigure(1, weight=1)

        self.frame_tipo_ativo = newFrame(self.frame_dados_boleta)
        self.frame_tipo_ativo.columnconfigure(0, weight=1)

    def widgets(self):

        self.entry_refdate = newDateEntry(self.frame_refdate, startdate=self.refdate, dateformat="%d/%m/%Y")
        self.btn_change_date = newButton(
            self.frame_refdate, text="Mudar Refdate", width=15, command=self.process_manager.comando_change_refdate)

        self.btn_reset = newButton(
            self.frame_botoes_controle, text="Reset", width=15, command=self.process_manager.comando_reset)
        self.btn_boletagem = newButton(
            self.frame_botoes_controle, text="Boletar", width=15, command=self.process_manager.comando_boletagem)
        self.btn_refresh = newButton(
            self.frame_botoes_controle, text="Refresh", width=15, command=self.process_manager.comando_consulta_boletas)

        newLabelStatus(self.frame_tipo_ativo, text="Tipo Ativo").grid(row=0, column=0, sticky="w")
        self.entry_tipo_ativo = newCombobox(self.frame_tipo_ativo, textvariable=self.tipo_ativo, values=self.lista_tipo_ativos)
        self.entry_tipo_ativo.grid(row=1, column=0, sticky="we")
        self.entry_tipo_ativo.set_readonly()

        newLabelStatus(self.frame_fundo, text="Fundo").grid(row=0, column=0, sticky="w")
        self.entry_fundo = newCombobox(self.frame_fundo, textvariable=self.fundo)
        self.entry_fundo.grid(row=1, column=0, sticky="we")
        self.entry_fundo.set_readonly()

        newLabelStatus(self.frame_ativo, text="Ativo").grid(row=0, column=0, sticky="w")
        self.entry_ativo = newCombobox(self.frame_ativo, textvariable=self.ativo)
        self.entry_ativo.grid(row=1, column=0, sticky="we")
        self.entry_ativo.set_readonly()

        newLabelStatus(self.frame_quantidade, text="Quantidade").grid(row=0, column=0, sticky="w")
        self.entry_quantidade = newEntry(self.frame_quantidade, textvariable=self.quantidade)
        self.entry_quantidade.grid(row=1, column=0, sticky="we")

        newLabelStatus(self.frame_pu, text="PU").grid(row=0, column=0, sticky="w")
        self.entry_pu = newEntry(self.frame_pu, textvariable=self.pu)
        self.entry_pu.grid(row=1, column=0, sticky="we")

        newLabelStatus(self.frame_taxa, text="Taxa (%)").grid(row=0, column=0, sticky="w")
        self.entry_taxa = newEntry(self.frame_taxa, textvariable=self.taxa)
        self.entry_taxa.grid(row=1, column=0, sticky="we")

        newLabelStatus(self.frame_cv, text="Compra / Venda").grid(row=0, column=0, sticky="w")
        self.entry_cv = newCombobox(self.frame_cv, textvariable=self.cv, values=['C', 'V'])
        self.entry_cv.grid(row=1, column=0, sticky="we")
        self.entry_cv.set_readonly()

        newLabelStatus(self.frame_broker, text="Broker").grid(row=0, column=0, sticky="w")
        self.entry_broker = newCombobox(self.frame_broker, textvariable=self.broker)
        self.entry_broker.grid(row=1, column=0, sticky="we", padx=(0,10))
        self.entry_broker.set_readonly()

        newLabelStatus(self.frame_broker, text="CNPJ Broker").grid(row=0, column=1, sticky="w")
        self.entry_cnpj_broker = newEntry(self.frame_broker, textvariable=self.cnpj_broker)
        self.entry_cnpj_broker.grid(row=1, column=1, sticky="we")
        self.entry_cnpj_broker.set_readonly()

        self.tabela_historico_boletas = Tableview(
            self.frame_historico_boletagem,
            searchable=True,
            autofit=True,
            paginated=False,
            autoalign=True,
            coldata=[
                {"text": "ID", "stretch": True},
                {"text": "Trade Date", "stretch": True},
                {"text": "Fundo", "stretch": True},
                {"text": "Tipo Ativo", "stretch": True},
                {"text": "Ativo", "stretch": True},
                {"text": "C/V", "stretch": True},
                {"text": "Quantidade", "stretch": True},
                {"text": "PU", "stretch": True},
                {"text": "Taxa", "stretch": True},
                {"text": "Broker", "stretch": True}
                ])
        self.tabela_historico_boletas.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def grid_widgets(self):

        self.entry_refdate.grid(row=0, column=0, sticky="w", padx=(10,0), pady=10)
        self.btn_change_date.grid(row=0, column=1, sticky="w", padx=(10,10), pady=10)

        self.btn_reset.grid(row=0, column=0, sticky="w", padx=(10,0), pady=(10,10))
        self.btn_refresh.grid(row=0, column=1, sticky="w", padx=(10,0), pady=(10,10))
        self.btn_boletagem.grid(row=0, column=2, sticky="w", padx=(10,10), pady=(10,10))

        self.frame_fundo.grid(row=0, column=0, sticky="we", padx=(10,0), pady=(10,0), columnspan=2)
        self.frame_tipo_ativo.grid(row=0, column=2, sticky="we", padx=(10,10), pady=(10,0), columnspan=2)

        self.frame_ativo.grid(row=1, column=0, sticky="we", padx=(10,0), pady=(10,0), columnspan=2)
        self.frame_cv.grid(row=1, column=2, sticky="we", padx=(10,0), pady=(10,0))
        self.frame_quantidade.grid(row=1, column=3, sticky="we", padx=(10,10), pady=(10,0))

        self.frame_pu.grid(row=2, column=0, sticky="we", padx=(10,0), pady=(10,10))
        self.frame_taxa.grid(row=2, column=1, sticky="we", padx=(10,0), pady=(10,10))
        self.frame_broker.grid(row=2, column=2, sticky="we", padx=(10,10), pady=(10,10), columnspan=2)

class ProcessManagerInterno:

    def __init__(self, app=None, manager_sql=None, funcoes_pytools=None):

        if manager_sql is None:
            self.manager_sql = SQL_Manager()
        else:
            self.manager_sql = manager_sql

        if funcoes_pytools is None:
            self.funcoes_pytools = FuncoesPyTools(self.manager_sql)
        else:
            self.funcoes_pytools = funcoes_pytools

        if ENVIRONMENT == 'DEVELOPMENT':
            self.tb_boletas = "TB_BOLETAS_TESTE"
        else:
            self.tb_boletas = "TB_BOLETAS"


        self.app = app

    def comando_change_refdate(self):

        refdate = datetime.strptime(self.app.entry_refdate.entry.get(), "%d/%m/%Y").date()

        self.app.set_refdate(refdate)

        self.comando_consulta_boletas()

    def comando_consulta_boletas(self):

        lista_boletas = self.manager_sql.select_dataframe(
            f"SELECT ID, TRADE_DATE, FUNDO, TIPO_ATIVO, ATIVO, C_V, QUANTIDADE, PU, TAXA, CUSTODIA "
            f"FROM {self.tb_boletas} WHERE TRADE_DATE = '{self.app.refdate.strftime('%Y-%m-%d')}'").values.tolist()

        self.app.tabela_historico_boletas.reset_table()
        self.app.tabela_historico_boletas.delete_rows(indices=None, iids=None)
        self.app.tabela_historico_boletas.insert_rows('end', lista_boletas)
        self.app.tabela_historico_boletas.load_table_data()
        self.app.tabela_historico_boletas.autoalign_columns()
        self.app.tabela_historico_boletas.autofit_columns()

    def controle_entry_tipo_ativo(self, *args):
        _ = args

        self.app.ativo.set('')

        self.app.entry_ativo['values'] = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT ATIVO FROM TB_CADASTRO_ATIVOS "
            f"WHERE TIPO_ATIVO IN ('{self.app.tipo_ativo.get()}') "
            f"AND DATA_VENCIMENTO >= '{self.app.refdate.strftime('%Y-%m-%d')}' ORDER BY ATIVO")['ATIVO'].tolist()

    def controle_entry_broker(self, *args):
        _ = args

        def format_cnpj(cnpj_str):
            return f"{cnpj_str[:2]}.{cnpj_str[2:5]}.{cnpj_str[5:8]}/{cnpj_str[8:12]}-{cnpj_str[12:]}"

        if self.app.broker.get() != '':
            self.app.cnpj_broker.set(format_cnpj(self.app.dict_cnpj_broker[self.app.broker.get()]))

    def check_quantidade(self, event):
        _ = event
        
        if self.app.quantidade.get() != '':
            try:
                int(self.app.quantidade.get())

                if int(self.app.quantidade.get()) < 0:
                    self.app.quantidade.set(int(self.app.quantidade.get())*-1)
                    Messagebox.show_info(title="Erro Quantidade", message="Quantidade deve ser um número inteiro maior que zero.")
                    self.app.app.lift()

                if int(self.app.quantidade.get()) == 0:
                    self.app.quantidade.set('')
                    Messagebox.show_info(title="Erro Quantidade", message="Quantidade deve ser um número inteiro maior que zero.")
                    self.app.app.lift()

            except ValueError:
                self.app.quantidade.set('')
                Messagebox.show_error(title="Erro Quantidade", message="Quantidade deve ser um número inteiro")
                self.app.app.lift()

    def check_pu(self, event):
        _ = event

        if self.app.pu.get() != '':
            try:
                float(self.app.pu.get())

                if float(self.app.pu.get()) <= 0:
                    self.app.pu.set('')
                    Messagebox.show_info(title="Erro PU", message="PU deve ser um número maior que zero.")
                    self.app.app.lift()

            except ValueError:
                self.app.pu.set('')
                Messagebox.show_error(title="Erro PU", message="Usar ',' como separador decimal.")
                self.app.app.lift()

    def check_taxa(self, event):
        _ = event

        if self.app.taxa.get() != '':
            try:
                float(self.app.taxa.get())

                if float(self.app.taxa.get()) <= 0:
                    self.app.taxa.set('')
                    Messagebox.show_info(title="Erro Taxa", message="Taxa deve ser um número maior que zero.")
                    self.app.app.lift()

            except ValueError:
                self.app.taxa.set('')
                Messagebox.show_error(title="Erro Taxa", message="Usar ',' como separador decimal.")
                self.app.app.lift()

    def comando_boletagem(self):

        if self.app.fundo.get() == '' or self.app.tipo_ativo.get() == '' or self.app.ativo.get() == '' or \
                self.app.cv.get() == '' or self.app.quantidade.get() == '' or self.app.pu.get() == '' or \
                self.app.taxa.get() == '' or self.app.broker.get() == '':
            Messagebox.show_error(title="Erro Boletagem", message="Preencher todos os campos.")
            self.app.app.lift()
        else:
            confirma = Messagebox.okcancel(
                title="Confirmação Boletagem",
                message=f"Confirmar boletagem para o dia {self.app.refdate.strftime('%d/%m/%Y')}?")

            if confirma == "OK":

                broker_boleta = self.app.dict_boletas_broker[self.app.broker.get()]

                data = {
                    'TRADE_DATE': [self.app.refdate],
                    'FUNDO': [self.app.fundo.get()],
                    'TIPO_ATIVO': [self.app.tipo_ativo.get()],
                    'ATIVO': [self.app.ativo.get()],
                    'C_V': [self.app.cv.get()],
                    'QUANTIDADE': [int(self.app.quantidade.get())],
                    'PU': [float(self.app.pu.get())],
                    'CUSTODIA': [self.app.broker.get() if broker_boleta is None else broker_boleta],
                    'PU_LIMPO_BONDS': [None],
                    'TAXA': [float(self.app.taxa.get())],
                    'NOME_BROKER': [self.app.broker.get()]
                    }

                df_boleta = pd.DataFrame(data)

                self.manager_sql.insert_dataframe(df_boleta, self.tb_boletas)

                self.comando_travar_campos()
                Messagebox.show_info(title="Boletagem", message="Boletagem realizada.")
                self.comando_consulta_boletas()
            else:
                Messagebox.show_info(title="Boletagem", message="Boletagem cancelada.")

            self.app.app.lift()

    def comando_travar_campos(self):

        self.app.btn_boletagem.set_disabled()

        self.app.entry_fundo.set_disabled()
        self.app.entry_tipo_ativo.set_disabled()
        self.app.entry_ativo.set_disabled()
        self.app.entry_cv.set_disabled()
        self.app.entry_quantidade.set_disabled()
        self.app.entry_pu.set_disabled()
        self.app.entry_taxa.set_disabled()
        self.app.entry_broker.set_disabled()
        self.app.entry_cnpj_broker.set_disabled()

    def comando_reset(self):

        self.app.fundo.set('')
        self.app.tipo_ativo.set('')
        self.app.ativo.set('')
        self.app.cv.set('')
        self.app.quantidade.set('')
        self.app.pu.set('')
        self.app.taxa.set('')
        self.app.broker.set('')
        self.app.cnpj_broker.set('')

        self.app.btn_boletagem.set_enabled()

        self.app.entry_fundo.set_readonly()
        self.app.entry_tipo_ativo.set_readonly()
        self.app.entry_ativo.set_readonly()
        self.app.entry_cv.set_readonly()
        self.app.entry_quantidade.set_enabled()
        self.app.entry_pu.set_enabled()
        self.app.entry_taxa.set_enabled()
        self.app.entry_broker.set_readonly()
        self.app.entry_cnpj_broker.set_readonly()

        self.comando_consulta_boletas()

if __name__ == "__main__":
    app = BoletadorAPP()
