try:
    from datetime import date, datetime
    from tkinter import StringVar

    import pandas as pd
    from __init__ import *  # noqa: F403
    from ttkbootstrap import Separator, Toplevel, Window
    from ttkbootstrap.constants import *  # noqa: F403
    from ttkbootstrap.tableview import Tableview

    from controlPanel.biblioteca_widgets import (  # noqa: F401
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
    from controlPanel.sistemaCadastro import TelaCadastro
    from tools.db_helper import SQL_Manager
    from tools.py_tools import FuncoesPyTools

except Exception as e:
    print(e)
    input("Pressione ENTER para finalizar o programa.")

VERSION_APP = "1.0.0"
VERSION_REFDATE = "2024-07-24"
ENVIRONMENT = os.getenv("ENVIRONMENT")  # noqa: F405
SCRIPT_NAME = os.path.basename(__file__)  # noqa: F405


if ENVIRONMENT == "DEVELOPMENT":
    print(f"{SCRIPT_NAME.upper()} - {ENVIRONMENT} - {VERSION_APP} - {VERSION_REFDATE}")

append_paths()  # noqa: F405

# -------------------------------------------------------------------------------------------------------


class BoletadorPreTrading(Window if __name__ == "__main__" else Toplevel):

    def __init__(self, app=None, manager_sql=None, funcoes_pytools=None, *args, **kwargs):

        if isinstance(self, Window):
            super().__init__(themename='cyborg', *args, **kwargs)
        else:
            super().__init__(*args, **kwargs)

        self.manager_sql = manager_sql if manager_sql is not None else SQL_Manager()

        self.funcoes_pytools = funcoes_pytools if funcoes_pytools is not None else FuncoesPyTools(self.manager_sql)

        self.lista_fundos = ['Strix Yield Master']
        self.lista_tipo_ativos = ['FIDC', 'Debênture', 'CCB', 'CDB', 'LF', 'LFSC', 'LFSN', 'LFSN-PRE']

        self.refdate = date.today()

        self.process_manager = ProcessManagerPretrading(
            app=self,
            manager_sql=self.manager_sql,
            funcoes_pytools=self.funcoes_pytools)

        self.config_app()
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
        self.process_manager.comando_consulta_boletas()

        self.mainloop()

    def open_tela_cadastro(self):

        self.sistema_cadastro = TelaCadastro(self, manager_sql=self.manager_sql, funcoes_pytools=self.funcoes_pytools)

    def config_app(self):

        self.title("BOS - Boletador Pré-Trades")
        self.geometry("900x765")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self.frame_menu = newFrame(self, bootstyle="light")
        self.frame_menu.grid(row=0, column=0, sticky="ew")

        frame_header = newFrame(self)
        frame_header.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        frame_header.columnconfigure(0, weight=1)

        newLabelTitle(frame_header, text=f"{"DESENVOLVIMENTO" if ENVIRONMENT == 'DEVELOPMENT' else "Boletador Pré-Trades"}")\
            .grid(row=0, column=0, sticky="ew")

        self.lbl_refdate = newLabelSubtitle(frame_header, text=f"Refdate Boletador: {self.refdate.strftime('%d/%m/%Y')}")
        self.lbl_refdate.grid(row=1, column=0, sticky="ew")

        newLabelSubtitle(frame_header, text=f"Usuário: {str_user}").grid(row=2, column=0, sticky="ew")  # noqa: F405

        Separator(frame_header, orient="horizontal").grid(row=3, column=0, sticky="ew", pady=(10, 0))

    def set_refdate(self, refdate):

        self.refdate = refdate

        self.lbl_refdate.configure(text=f"Refdate Boletador: {self.refdate.strftime('%d/%m/%Y')}")

    def frame_body(self):

        self.frame_body = newFrame(self)
        self.frame_body.grid(row=2, column=0, sticky="nsew")
        self.frame_body.columnconfigure(0, weight=1)
        self.frame_body.rowconfigure(2, weight=1)

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

    def controle_variaveis(self):

        self.tipo_ativo.trace_add('write', self.process_manager.controle_entry_tipo_ativo)

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

        self.frame_botoes_1 = newFrame(self.frame_botoes_controle)
        self.frame_botoes_2 = newFrame(self.frame_botoes_controle)

        self.frame_dados_boleta = newLabelFrame(self.frame_body, text="Dados Boleta")
        self.frame_historico_boletagem = newLabelFrame(self.frame_body, text="Histórico Boletagem")

    def grid_labelFrames(self):

        self.frame_refdate.grid(row=0, column=0, sticky="ew", padx=(10, 0), pady=(10, 0))
        self.frame_botoes_controle.grid(row=0, column=1, sticky="ew", padx=(10, 10), pady=(10, 0))
        self.frame_botoes_controle.columnconfigure(0, weight=1)
        self.frame_botoes_controle.columnconfigure(1, weight=1)

        self.frame_botoes_1.grid(row=0, column=0, sticky="ew")
        self.frame_botoes_2.grid(row=0, column=1, sticky="ew")
        self.frame_botoes_2.columnconfigure(0, weight=1)

        self.frame_dados_boleta.grid(row=1, column=0, sticky="nsew", padx=10, pady=(10, 0))
        self.frame_dados_boleta.columnconfigure(0, weight=1)
        self.frame_dados_boleta.columnconfigure(1, weight=1)

        self.frame_historico_boletagem.grid(row=2, column=0, sticky="nsew", padx=10, pady=(10, 10))
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

        # self.frame_broker = newFrame(self.frame_dados_boleta)
        # self.frame_broker.columnconfigure(0, weight=10)
        # self.frame_broker.columnconfigure(1, weight=1)

        self.frame_tipo_ativo = newFrame(self.frame_dados_boleta)
        self.frame_tipo_ativo.columnconfigure(0, weight=1)

    def widgets(self):

        self.entry_refdate = newDateEntry(self.frame_refdate, startdate=self.refdate, dateformat="%d/%m/%Y")
        self.btn_change_date = newButton(
            self.frame_refdate, text="Mudar Refdate", width=15, command=self.process_manager.comando_change_refdate)

        self.btn_reset = newButton(
            self.frame_botoes_1, text="Reset", width=15, command=self.process_manager.comando_reset)

        self.btn_boletagem = newButton(
            self.frame_botoes_1, text="Boletar", width=15, command=self.process_manager.comando_boletagem)

        self.btn_refresh = newButton(
            self.frame_botoes_1, text="Refresh", width=15, command=self.process_manager.comando_consulta_boletas)

        self.btn_pre_cadastro = newButton(
            self.frame_botoes_2, text="Sist. Cadastro", width=15, command=self.open_tela_cadastro)

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
                {"text": "Taxa", "stretch": True}
            ])
        self.tabela_historico_boletas.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def grid_widgets(self):

        self.entry_refdate.grid(row=0, column=0, sticky="w", padx=(10, 0), pady=10)
        self.btn_change_date.grid(row=0, column=1, sticky="w", padx=(10, 10), pady=10)

        self.btn_reset.grid(row=0, column=0, sticky="w", padx=(10, 0), pady=(10, 10))
        self.btn_refresh.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=(10, 10))
        self.btn_boletagem.grid(row=0, column=2, sticky="w", padx=(10, 0), pady=(10, 10))
        self.btn_pre_cadastro.grid(row=0, column=3, sticky="e", padx=(10, 10), pady=(10, 10))

        self.frame_fundo.grid(row=0, column=0, sticky="we", padx=(10, 0), pady=(10, 0), columnspan=2)
        self.frame_tipo_ativo.grid(row=0, column=2, sticky="we", padx=(10, 10), pady=(10, 0), columnspan=2)

        self.frame_ativo.grid(row=1, column=0, sticky="we", padx=(10, 0), pady=(10, 0), columnspan=2)
        self.frame_cv.grid(row=1, column=2, sticky="we", padx=(10, 0), pady=(10, 0))
        self.frame_quantidade.grid(row=1, column=3, sticky="we", padx=(10, 10), pady=(10, 0))

        self.frame_pu.grid(row=2, column=0, sticky="we", padx=(10, 0), pady=(10, 10))
        self.frame_taxa.grid(row=2, column=1, sticky="we", padx=(10, 0), pady=(10, 10))


class ProcessManagerPretrading:

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
            self.tb_boletas = "TB_BOLETAS_PRE_TRADING"
        else:
            self.tb_boletas = "TB_BOLETAS_PRE_TRADING"

        self.app = app

    def comando_change_refdate(self):

        refdate = datetime.strptime(self.app.entry_refdate.entry.get(), "%d/%m/%Y").date()

        self.app.set_refdate(refdate)

        self.comando_consulta_boletas()

    def comando_consulta_boletas(self):

        lista_boletas = self.manager_sql.select_dataframe(
            f"SELECT ID, TRADE_DATE, FUNDO, TIPO_ATIVO, ATIVO, C_V, QUANTIDADE, PU, TAXA "
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

    def check_quantidade(self, event):
        _ = event

        if self.app.quantidade.get() != '':
            try:
                int(self.app.quantidade.get())

                if int(self.app.quantidade.get()) < 0:
                    self.app.quantidade.set(int(self.app.quantidade.get()) * -1)
                    Messagebox.show_info(title="Erro Quantidade", message="Quantidade deve ser um número inteiro maior que zero.")
                    self.app.lift()

                if int(self.app.quantidade.get()) == 0:
                    self.app.quantidade.set('')
                    Messagebox.show_info(title="Erro Quantidade", message="Quantidade deve ser um número inteiro maior que zero.")
                    self.app.lift()

            except ValueError:
                self.app.quantidade.set('')
                Messagebox.show_error(title="Erro Quantidade", message="Quantidade deve ser um número inteiro")
                self.app.lift()

    def check_pu(self, event):
        _ = event

        if self.app.pu.get() != '':
            try:
                float(self.app.pu.get())

                if float(self.app.pu.get()) <= 0:
                    self.app.pu.set('')
                    Messagebox.show_info(title="Erro PU", message="PU deve ser um número maior que zero.")
                    self.app.lift()

            except ValueError:
                self.app.pu.set('')
                Messagebox.show_error(title="Erro PU", message="Usar ',' como separador decimal.")
                self.app.lift()

    def check_taxa(self, event):
        _ = event

        if self.app.taxa.get() != '':
            try:
                float(self.app.taxa.get())

                if float(self.app.taxa.get()) <= 0:
                    self.app.taxa.set('')
                    Messagebox.show_info(title="Erro Taxa", message="Taxa deve ser um número maior que zero.")
                    self.app.lift()

            except ValueError:
                self.app.taxa.set('')
                Messagebox.show_error(title="Erro Taxa", message="Usar ',' como separador decimal.")
                self.app.lift()

    def comando_boletagem(self):

        if self.app.fundo.get() == '' or self.app.tipo_ativo.get() == '' or self.app.ativo.get() == '' or \
                self.app.cv.get() == '' or self.app.quantidade.get() == '' or self.app.pu.get() == '' or \
                self.app.taxa.get() == '':
            Messagebox.show_error(title="Erro Boletagem", message="Preencher todos os campos.")
            self.app.lift()
        else:
            confirma = Messagebox.okcancel(
                title="Confirmação Boletagem",
                message=f"Confirmar boletagem para o dia {self.app.refdate.strftime('%d/%m/%Y')}?")

            if confirma == "OK":

                data = {
                    'TRADE_DATE': [self.app.refdate],
                    'FUNDO': [self.app.fundo.get()],
                    'TIPO_ATIVO': [self.app.tipo_ativo.get()],
                    'ATIVO': [self.app.ativo.get()],
                    'C_V': [self.app.cv.get()],
                    'QUANTIDADE': [int(self.app.quantidade.get())],
                    'PU': [float(self.app.pu.get())],
                    'TAXA': [float(self.app.taxa.get())]
                }

                df_boleta = pd.DataFrame(data)

                self.manager_sql.insert_dataframe(df_boleta, self.tb_boletas)

                self.comando_travar_campos()
                Messagebox.show_info(title="Boletagem", message="Boletagem realizada.")
                self.comando_consulta_boletas()
            else:
                Messagebox.show_info(title="Boletagem", message="Boletagem cancelada.")

            self.app.lift()

    def comando_travar_campos(self):

        self.app.btn_boletagem.set_disabled()

        self.app.entry_fundo.set_disabled()
        self.app.entry_tipo_ativo.set_disabled()
        self.app.entry_ativo.set_disabled()
        self.app.entry_cv.set_disabled()
        self.app.entry_quantidade.set_disabled()
        self.app.entry_pu.set_disabled()
        self.app.entry_taxa.set_disabled()

    def comando_reset(self):

        self.app.fundo.set('')
        self.app.tipo_ativo.set('')
        self.app.ativo.set('')
        self.app.cv.set('')
        self.app.quantidade.set('')
        self.app.pu.set('')
        self.app.taxa.set('')

        self.app.btn_boletagem.set_enabled()

        self.app.entry_fundo.set_readonly()
        self.app.entry_tipo_ativo.set_readonly()
        self.app.entry_ativo.set_readonly()
        self.app.entry_cv.set_readonly()
        self.app.entry_quantidade.set_enabled()
        self.app.entry_pu.set_enabled()
        self.app.entry_taxa.set_enabled()

        self.comando_consulta_boletas()


if __name__ == "__main__":
    app = BoletadorPreTrading()
