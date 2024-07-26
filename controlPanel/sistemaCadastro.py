import unicodedata
from datetime import datetime
from tkinter import StringVar

import pandas as pd
from __init__ import *  # noqa: F403, F405, E402
from ttkbootstrap import Toplevel, Window  # noqa: F403, F405, E402
from ttkbootstrap.constants import *  # noqa: F403, F405, E402

append_paths()  # noqa: F403, F405, E402

from controlPanel.biblioteca_widgets import (  # noqa: F403, F405, E402
    Messagebox,
    newButton,
    newCombobox,
    newDateEntry,
    newEntry,
    newFrame,
    newLabelFrame,
    newLabelStatus,
    newLabelSubtitle,
    newLabelTitle,
    newRadioButton,
    newScrolledText,
    newStringVar,
)
from tools.db_helper import SQL_Manager  # noqa: F403, F405, E402
from tools.my_logger import Logger  # noqa: F403, F405, E402
from tools.py_tools import FuncoesPyTools  # noqa: F403, F405, E402

# -------------------------------------------------------------------------------------------------------

VERSION_APP = "2.1.2"
VERSION_REFDATE = "2024-07-10"
ENVIRONMENT = os.getenv("ENVIRONMENT")  # noqa: F403, F405, E402
SCRIPT_NAME = os.path.basename(__file__)  # noqa: F403, F405, E402

if ENVIRONMENT == "DEVELOPMENT":
    print(f"{SCRIPT_NAME.upper()} - {ENVIRONMENT} - {VERSION_APP} - {VERSION_REFDATE}")

# -------------------------------------------------------------------------------------------------------


def normalize_string(s):
    normalized = unicodedata.normalize("NFKD", s)
    return (
        "".join(c for c in normalized if not unicodedata.combining(c))
        .upper()
        .replace("Ç", "C")
    )


def check_in_list(string_list, variable):
    normalized_list = [normalize_string(item) for item in string_list]
    normalized_variable = normalize_string(variable)
    return normalized_variable in normalized_list


def ajuste_str(text):
    exceptions = ["e", "de", "da", "das", "dos", "do", "de"]
    words = text.split()
    capitalized_words = [
        (
            word.capitalize()
            if word.lower() not in exceptions and len(word) != 2
            else (word.upper() if len(word) == 2 else word.lower())
        )
        for word in words
    ]
    return " ".join(capitalized_words)


class TelaCadastro(Window if __name__ == "__main__" else Toplevel):

    def __init__(
        self,
        app=None,
        manager_sql=None,
        funcoes_pytools=None,
        *args,
        **kwargs,
    ):
        if isinstance(self, Window):
            super().__init__(themename="vapor", *args, **kwargs)
        else:
            super().__init__(*args, **kwargs)

        self.title("BOS - Sistema Cadastro")
        self.geometry("330x202")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.manager_sql = manager_sql if manager_sql is not None else SQL_Manager()

        self.funcoes_pytools = funcoes_pytools if funcoes_pytools is not None else FuncoesPyTools(self.manager_sql)

        self.logger = Logger(manager_sql=self.manager_sql, original_script=SCRIPT_NAME)

        self.logger.info(
            log_message=f"TelaCadastro - {VERSION_APP} - {ENVIRONMENT} - Instanciado"
        )

        self.logger.reset_index()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.app = app

        self.call_header()
        self.call_body()

        self.mainloop()

    def on_close(self):
        self.destroy()
        if self.app is not None:
            self.app.lift()

    def call_header(self):

        newFrame(self).grid(row=0, column=0, sticky="ew", padx=10, pady=(40, 20))

        lbl_titulo = newLabelTitle(
            self,
            text=f"{'DEVELOPMENT' if ENVIRONMENT == "DEVELOPMENT" else 'Sistema de Cadastro'}",
        )
        lbl_titulo.grid(row=0, column=0, sticky="we")
        lbl_titulo.set_tamanho_fonte(16)

    def call_body(self):

        def call_fluxo_financeiro():
            CadastroFluxoFinanceiro(
                app=self.app,
                janela_init=self,
                manager_sql=self.manager_sql,
                funcoes_pytools=self.funcoes_pytools,
            )

        def call_cadastro_ativos():
            CadastroAtivos(
                app=self.app,
                janela_init=self,
                manager_sql=self.manager_sql,
                funcoes_pytools=self.funcoes_pytools,
            )

        def call_pend_cod_btg():
            RegistroCodBTG(
                app=self.app,
                janela_init=self,
                manager_sql=self.manager_sql,
                funcoes_pytools=self.funcoes_pytools,
            )

        frame_body = newFrame(self)
        frame_body.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 5))
        frame_body.columnconfigure(0, weight=1)

        newButton(
            frame_body,
            text="Cadastro de Ativos",
            width=30,
            command=call_cadastro_ativos,
        ).grid(row=0, column=0, padx=5, pady=(0, 10))
        newButton(
            frame_body,
            text="Cadastro de Fluxo Financeiro",
            command=call_fluxo_financeiro,
            width=30,
        ).grid(row=1, column=0, padx=5, pady=(0, 10))
        newButton(
            frame_body,
            text="Update Pend. Cod. BTG",
            width=30,
            command=call_pend_cod_btg,
        ).grid(row=2, column=0, padx=5, pady=(0, 10))


class windowCadastroEmissor(Toplevel):

    def __init__(self, app, manager_sql=None, funcoes_pytools=None, logger=None, **kwargs):
        super().__init__(**kwargs)

        self.title("BOS - Sistema Cadastro")
        self.geometry("570x370")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self.manager_sql = manager_sql if manager_sql is not None else SQL_Manager()

        self.funcoes_pytools = funcoes_pytools if funcoes_pytools is not None else FuncoesPyTools(self.manager_sql)

        self.check_dados = None

        self.lista_tipo_emissor = self.manager_sql.select_dataframe(
            "SELECT DISTINCT TIPO_EMISSOR FROM TB_CADASTRO_EMISSOR ORDER BY TIPO_EMISSOR"
        )["TIPO_EMISSOR"].tolist()

        self.lista_grupo_economico = self.manager_sql.select_dataframe(
            "SELECT DISTINCT GRUPO_ECONOMICO FROM TB_CADASTRO_EMISSOR ORDER BY GRUPO_ECONOMICO"
        )["GRUPO_ECONOMICO"].tolist()

        self.app = app

        self.logger = logger

        self.logger.info(log_message="CadastroEmissor - Iniciado")

        self.frames()
        self.variaveis()
        self.widgets()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.logger.info(log_message="CadastroEmissor - Finalizado")
        self.logger.reset_index()
        self.destroy()

    def format_str(self, s):
        # Remover espaços em branco nas extremidades
        s = s.strip()
        # Converter para maiúsculas
        s = s.upper()
        # Substituir S.A., S.A, ou SA por S/A
        if s.endswith("S.A.") or s.endswith("S.A") or s.endswith("SA"):
            s = s.rsplit(" ", 1)[0] + " S/A"
        return s

    def frames(self):

        self.frame_header = newFrame(self)
        self.frame_header.grid(row=0, column=0, sticky="new", pady=10)
        self.frame_header.columnconfigure(0, weight=1)

        self.frame_botoes = newFrame(self)
        self.frame_botoes.grid(row=1, column=0, sticky="we", pady=(0, 5))

        self.frame_body = newLabelFrame(self, text="Dados cadastrais")
        self.frame_body.grid(row=2, column=0, sticky="new", padx=10, pady=(0, 5))
        self.frame_body.columnconfigure(0, weight=1)

    def variaveis(self):

        self.emissor = newStringVar()
        self.grupo_economico = newStringVar()
        self.tipo_emissor = newStringVar()

    def widgets(self):

        self.label_title = newLabelTitle(self.frame_header, text="Novo Emissor")
        self.label_title.grid(row=0, column=0, sticky="we")

        self.btn_reset = newButton(self.frame_botoes, text="Reset", width=15)
        self.btn_reset.grid(row=0, column=0, sticky="w", padx=(10, 5))

        self.btn_check_dados = newButton(
            self.frame_botoes,
            text="Check Dados",
            width=15,
            command=self.comando_check_dados,
        )
        self.btn_check_dados.grid(row=0, column=1, sticky="w", padx=(0, 5))

        self.btn_cadastrar = newButton(
            self.frame_botoes,
            text="Cadastrar",
            width=15,
            command=self.comando_cadastrar,
        )
        self.btn_cadastrar.grid(row=0, column=2, sticky="w", padx=(0, 5))
        self.btn_cadastrar.set_disabled()

        self.label_emissor = newLabelStatus(self.frame_body, text="Emissor")
        self.label_emissor.grid(row=0, column=0, sticky="w", padx=5, pady=(5, 0))

        self.entry_emissor = newEntry(self.frame_body, textvariable=self.emissor)
        self.entry_emissor.grid(row=1, column=0, sticky="we", padx=5, pady=(0, 5))
        self.entry_emissor.set_tooltip(
            msg="Campo obrigatório.", bootstyle_p=(INFO, INVERSE)  # noqa: F403, F405, E402
        )

        self.label_grupo_economico = newLabelStatus(
            self.frame_body, text="Grupo Econômico"
        )
        self.label_grupo_economico.grid(
            row=2, column=0, sticky="w", padx=5, pady=(5, 0)
        )

        self.entry_grupo_economico = newCombobox(
            self.frame_body, textvariable=self.grupo_economico
        )
        self.entry_grupo_economico.grid(
            row=3, column=0, sticky="we", padx=5, pady=(0, 5)
        )
        self.entry_grupo_economico.set_tooltip(
            msg="Campo obrigatório.\n\nCaso não tenha na lista, digitar um novo Grupo Econômico.",
            bootstyle_p=(INFO, INVERSE),  # noqa: F403, F405, E402
        )
        self.entry_grupo_economico["values"] = self.lista_grupo_economico

        self.label_tipo_emissor = newLabelStatus(self.frame_body, text="Tipo Emissor")
        self.label_tipo_emissor.grid(row=4, column=0, sticky="w", padx=5, pady=(5, 0))

        self.entry_tipo_emissor = newCombobox(
            self.frame_body, textvariable=self.tipo_emissor
        )
        self.entry_tipo_emissor.grid(row=5, column=0, sticky="we", padx=5, pady=(0, 5))
        self.entry_tipo_emissor.set_tooltip(
            msg="Campo obrigatório.", bootstyle_p=(INFO, INVERSE)  # noqa: F403, F405, E402
        )
        self.entry_tipo_emissor["values"] = self.lista_tipo_emissor

    def comando_reset(self):

        self.emissor.set("")
        self.grupo_economico.set("")
        self.tipo_emissor.set("")

        self.entry_emissor.set_default()
        self.entry_emissor.set_enabled()

        self.entry_grupo_economico.set_default()
        self.entry_grupo_economico.set_enabled()

        self.entry_tipo_emissor.set_default()
        self.entry_tipo_emissor.set_enabled()

        self.btn_cadastrar.set_disabled()
        self.btn_check_dados.set_enabled()

    def comando_check_dados(self):

        if (
            self.emissor.get() == "" or self.grupo_economico.get() == "" or self.tipo_emissor.get() == ""
        ):

            if self.emissor.get() == "":
                self.entry_emissor.set_danger()

            if self.grupo_economico.get() == "":
                self.entry_grupo_economico.set_danger()

            if self.tipo_emissor.get() == "":
                self.entry_tipo_emissor.set_danger()

            self.check_dados = False

        else:
            emissor = self.format_str(self.emissor.get())
            grupo_economico = self.format_str(self.grupo_economico.get())

            self.emissor.set(emissor)
            self.grupo_economico.set(grupo_economico)

            self.entry_emissor.set_success()
            self.entry_grupo_economico.set_success()

            if self.tipo_emissor.get() not in self.lista_tipo_emissor:
                self.entry_tipo_emissor.set_danger()
                self.tipo_emissor.set("")
                self.check_dados = False
                Messagebox.show_info(
                    title="Aviso", message="Tipo Emissor não permitido."
                )
                self.lift()
            else:
                self.entry_tipo_emissor.set_success()
                self.check_dados = True

        if self.check_dados is True:
            self.travar_widgets()
            self.btn_cadastrar.set_enabled()
            self.btn_check_dados.set_disabled()

    def travar_widgets(self):

        self.entry_emissor.set_disabled()
        self.entry_grupo_economico.set_disabled()
        self.entry_tipo_emissor.set_disabled()

    def comando_cadastrar(self):

        is_emissor_exists = self.manager_sql.check_if_data_exists(
            f"SELECT EMISSOR FROM TB_CADASTRO_EMISSOR WHERE EMISSOR = '{self.emissor.get()}'"
        )

        if is_emissor_exists is True:
            Messagebox.show_info(
                title="Aviso", message="Emissor já cadastrado anteriormente."
            )
            self.logger.info(log_message="CadastroEmissor - Tentativa de cadastro de emissor já cadastrado")
            self.lift()
        else:
            data = {
                "EMISSOR": [self.emissor.get()],
                "GRUPO_ECONOMICO": [self.grupo_economico.get()],
                "TIPO_EMISSOR": [self.tipo_emissor.get()],
            }

            df_to_upload = pd.DataFrame(data)

            self.manager_sql.insert_dataframe(df_to_upload, "TB_CADASTRO_EMISSOR")

            Messagebox.show_info(
                title="Aviso", message="Emissor cadastrado com sucesso."
            )
            self.logger.info(log_message=f"CadastroEmissor - Novo cadastro de emissor - {self.emissor.get()}")
            self.lift()


class windowCadastroSetor(Toplevel):

    def __init__(self, app, manager_sql=None, funcoes_pytools=None, logger=None, **kwargs):
        super().__init__(**kwargs)

        self.title("BOS - Sistema Cadastro")
        self.geometry("395x231")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self.manager_sql = manager_sql if manager_sql is None else SQL_Manager()

        self.funcoes_pytools = funcoes_pytools if funcoes_pytools is None else FuncoesPyTools(self.manager_sql)

        self.check_dados = None

        self.app = app

        self.logger = logger

        self.logger.info(log_message="CadastroSetor - Iniciado")

        self.setor = newStringVar()

        self.frames()
        self.widgets()
        self.lift()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.logger.info(log_message="CadastroSetor - Finalizado")
        self.logger.reset_index()
        self.destroy()

    def frames(self):

        self.frame_header = newFrame(self)
        self.frame_header.grid(row=0, column=0, sticky="new", pady=10)
        self.frame_header.columnconfigure(0, weight=1)

        self.frame_botoes = newFrame(self)
        self.frame_botoes.grid(row=1, column=0, sticky="we", pady=(0, 5))

        self.frame_body = newLabelFrame(self, text="Dados cadastrais")
        self.frame_body.grid(row=2, column=0, sticky="new", padx=10, pady=(0, 5))
        self.frame_body.columnconfigure(0, weight=1)

    def widgets(self):

        self.label_title = newLabelTitle(self.frame_header, text="Novo Setor")
        self.label_title.grid(row=0, column=0, sticky="we")
        self.label_title.set_tamanho_fonte(15)

        self.btn_reset = newButton(
            self.frame_botoes, text="Reset", width=15, command=self.comando_reset
        )
        self.btn_reset.grid(row=0, column=0, sticky="w", padx=(10, 5))

        self.btn_check_dados = newButton(
            self.frame_botoes,
            text="Check Dados",
            width=15,
            command=self.comando_check_dados,
        )
        self.btn_check_dados.grid(row=0, column=1, sticky="w", padx=(0, 5))

        self.btn_cadastrar = newButton(
            self.frame_botoes,
            text="Cadastrar",
            width=15,
            command=self.comando_cadastrar,
        )
        self.btn_cadastrar.grid(row=0, column=2, sticky="w", padx=(0, 5))
        self.btn_cadastrar.set_disabled()

        newLabelStatus(self.frame_body, text="Setor").grid(
            row=0, column=0, sticky="w", padx=5, pady=(5, 0)
        )

        self.entry_setor = newEntry(self.frame_body, textvariable=self.setor)
        self.entry_setor.grid(row=1, column=0, sticky="we", padx=5, pady=(0, 5))

    def comando_check_dados(self):

        if self.setor.get() == "":
            self.entry_setor.set_danger()
            self.check_dados = False
        else:
            self.app.update_setores()
            check_if_exists = check_in_list(
                self.app.lista_setores, self.setor.get().strip()
            )
            if check_if_exists is True:
                Messagebox.show_info(
                    title="Aviso", message="Setor já cadastrado anteriormente."
                )
                self.check_dados = False
                self.lift()
            else:
                self.entry_setor.set_success()
                self.entry_setor.set_disabled()
                self.setor.set(ajuste_str(self.setor.get().strip()))
                self.btn_check_dados.set_disabled()
                self.btn_cadastrar.set_enabled()
                self.check_dados = True

    def comando_cadastrar(self):

        is_setor_exists = self.manager_sql.check_if_data_exists(
            f"SELECT SETOR FROM TB_CADASTRO_SETOR WHERE SETOR = '{self.setor.get()}'"
        )

        if is_setor_exists is True:
            Messagebox.show_info(
                title="Aviso", message="Setor já cadastrado anteriormente."
            )
            self.logger.info(log_message="CadastroSetor - Tentativa de cadastro de setor já cadastrado")
            self.lift()
        else:
            data = {"SETOR": [self.setor.get()]}

            df_to_upload = pd.DataFrame(data)

            self.manager_sql.insert_dataframe(df_to_upload, "TB_CADASTRO_SETOR")

            Messagebox.show_info(title="Aviso", message="Setor cadastrado com sucesso.")

            self.logger.info(log_message=f"CadastroSetor - Novo cadastro de setor - {self.setor.get()}")

            self.lift()

    def comando_reset(self):

        self.setor.set("")
        self.entry_setor.set_default()
        self.entry_setor.set_enabled()
        self.btn_cadastrar.set_disabled()
        self.btn_check_dados.set_enabled()


class windowCadastroClasseAtivo(Toplevel):

    def __init__(self, app, manager_sql=None, funcoes_pytools=None, logger=None, **kwargs):
        super().__init__(**kwargs)

        self.title("BOS - Sistema Cadastro")
        self.geometry("395x231")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self.manager_sql = manager_sql if manager_sql is None else SQL_Manager()

        self.funcoes_pytools = funcoes_pytools if funcoes_pytools is None else FuncoesPyTools(self.manager_sql)

        self.check_dados = None

        self.app = app

        self.logger = logger

        self.logger.info(log_message="CadastroClasseAtivo - Iniciado")

        self.classe_ativo = newStringVar()

        self.frames()
        self.widgets()
        self.lift()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.logger.info(log_message="CadastroClasseAtivo - Finalizado")
        self.logger.reset_index()
        self.destroy()

    def frames(self):

        self.frame_header = newFrame(self)
        self.frame_header.grid(row=0, column=0, sticky="new", pady=10)
        self.frame_header.columnconfigure(0, weight=1)

        self.frame_botoes = newFrame(self)
        self.frame_botoes.grid(row=1, column=0, sticky="we", pady=(0, 5))

        self.frame_body = newLabelFrame(self, text="Dados cadastrais")
        self.frame_body.grid(row=2, column=0, sticky="new", padx=10, pady=(0, 5))
        self.frame_body.columnconfigure(0, weight=1)

    def widgets(self):

        self.label_title = newLabelTitle(
            self.frame_header, text="Cadastro Classe Ativo"
        )
        self.label_title.grid(row=0, column=0, sticky="we")
        self.label_title.set_tamanho_fonte(15)

        self.btn_reset = newButton(
            self.frame_botoes, text="Reset", width=15, command=self.comando_reset
        )
        self.btn_reset.grid(row=0, column=0, sticky="w", padx=(10, 5))

        self.btn_check_dados = newButton(
            self.frame_botoes,
            text="Check Dados",
            width=15,
            command=self.comando_check_dados,
        )
        self.btn_check_dados.grid(row=0, column=1, sticky="w", padx=(0, 5))

        self.btn_cadastrar = newButton(
            self.frame_botoes,
            text="Cadastrar",
            width=15,
            command=self.comando_cadastrar,
        )
        self.btn_cadastrar.grid(row=0, column=2, sticky="w", padx=(0, 5))
        self.btn_cadastrar.set_disabled()

        newLabelStatus(self.frame_body, text="Classe Ativo").grid(
            row=0, column=0, sticky="w", padx=5, pady=(5, 0)
        )

        self.entry_classe_ativo = newEntry(
            self.frame_body, textvariable=self.classe_ativo
        )
        self.entry_classe_ativo.grid(row=1, column=0, sticky="we", padx=5, pady=(0, 5))

    def comando_check_dados(self):

        if self.classe_ativo.get() == "":
            self.classe_ativo.set_danger()
            self.check_dados = False
        else:
            self.app.update_classe_ativo()
            check_if_exists = check_in_list(
                self.app.lista_classe_ativo, self.classe_ativo.get().strip()
            )
            if check_if_exists is True:
                Messagebox.show_info(
                    title="Aviso", message="Classe ativo já cadastrado anteriormente."
                )
                self.check_dados = False
                self.lift()
            else:
                self.entry_classe_ativo.set_success()
                self.entry_classe_ativo.set_disabled()
                self.classe_ativo.set(ajuste_str(self.classe_ativo.get().strip()))
                self.btn_check_dados.set_disabled()
                self.btn_cadastrar.set_enabled()
                self.check_dados = True

    def comando_cadastrar(self):

        is_classe_ativo_exists = self.manager_sql.check_if_data_exists(
            f"SELECT CLASSE_ATIVO FROM TB_CADASTRO_CLASSE_ATIVO WHERE CLASSE_ATIVO = '{self.classe_ativo.get()}'"
        )

        if is_classe_ativo_exists is True:
            Messagebox.show_info(
                title="Aviso", message="Classe ativo já cadastrado anteriormente."
            )
            self.logger.info(log_message="CadastroClasseAtivo - Tentativa de cadastro de classe ativo já cadastrado")
            self.lift()
        else:
            data = {"CLASSE_ATIVO": [self.classe_ativo.get()]}

            df_to_upload = pd.DataFrame(data)

            self.manager_sql.insert_dataframe(df_to_upload, "TB_CADASTRO_CLASSE_ATIVO")

            Messagebox.show_info(
                title="Aviso", message="Classe ativo cadastrado com sucesso."
            )
            self.logger.info(log_message=f"CadastroClasseAtivo - Novo cadastro de classe ativo - {self.classe_ativo.get()}")
            self.lift()

    def comando_reset(self):

        self.classe_ativo.set("")
        self.entry_classe_ativo.set_default()
        self.entry_classe_ativo.set_enabled()
        self.btn_cadastrar.set_disabled()
        self.btn_check_dados.set_enabled()


class windowCadastroModalideEnquadramento(Toplevel):

    def __init__(self, app, manager_sql=None, funcoes_pytools=None, logger=None, **kwargs):
        super().__init__(**kwargs)

        self.title("BOS - Sistema Cadastro")
        self.geometry("395x231")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self.manager_sql = manager_sql if manager_sql is None else SQL_Manager()

        self.funcoes_pytools = funcoes_pytools if funcoes_pytools is None else FuncoesPyTools(self.manager_sql)

        self.check_dados = None

        self.app = app

        self.logger = logger

        self.logger.info(log_message="CadastroModalidadeEnquadramento - Iniciado")

        self.modalidade_enquadramento = newStringVar()

        self.frames()
        self.widgets()
        self.lift()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.logger.info(log_message="CadastroModalidadeEnquadramento - Finalizado")
        self.logger.reset_index()
        self.destroy()
        if self.app is not None:
            self.app.lift()

    def frames(self):

        self.frame_header = newFrame(self)
        self.frame_header.grid(row=0, column=0, sticky="new", pady=10)
        self.frame_header.columnconfigure(0, weight=1)

        self.frame_botoes = newFrame(self)
        self.frame_botoes.grid(row=1, column=0, sticky="we", pady=(0, 5))

        self.frame_body = newLabelFrame(self, text="Dados cadastrais")
        self.frame_body.grid(row=2, column=0, sticky="new", padx=10, pady=(0, 5))
        self.frame_body.columnconfigure(0, weight=1)

    def widgets(self):

        self.label_title = newLabelTitle(
            self.frame_header, text="Nova Modalidade Enquadramento"
        )
        self.label_title.grid(row=0, column=0, sticky="we")
        self.label_title.set_tamanho_fonte(15)

        self.btn_reset = newButton(
            self.frame_botoes, text="Reset", width=15, command=self.comando_reset
        )
        self.btn_reset.grid(row=0, column=0, sticky="w", padx=(10, 5))

        self.btn_check_dados = newButton(
            self.frame_botoes,
            text="Check Dados",
            width=15,
            command=self.comando_check_dados,
        )
        self.btn_check_dados.grid(row=0, column=1, sticky="w", padx=(0, 5))

        self.btn_cadastrar = newButton(
            self.frame_botoes,
            text="Cadastrar",
            width=15,
            command=self.comando_cadastrar,
        )
        self.btn_cadastrar.grid(row=0, column=2, sticky="w", padx=(0, 5))
        self.btn_cadastrar.set_disabled()

        newLabelStatus(self.frame_body, text="Modalidade Enquadramento").grid(
            row=0, column=0, sticky="w", padx=5, pady=(5, 0)
        )

        self.entry_modalidade_enquadramento = newEntry(
            self.frame_body, textvariable=self.modalidade_enquadramento
        )
        self.entry_modalidade_enquadramento.grid(
            row=1, column=0, sticky="we", padx=5, pady=(0, 5)
        )

    def comando_check_dados(self):

        if self.modalidade_enquadramento.get() == "":
            self.entry_modalidade_enquadramento.set_danger()
            self.check_dados = False
        else:
            self.app.update_modalidade_enquadramento()
            check_if_exists = check_in_list(
                self.app.lista_modalidade_enquadramento,
                self.modalidade_enquadramento.get().strip(),
            )
            if check_if_exists is True:
                Messagebox.show_info(
                    title="Aviso",
                    message="Modalidade enquadramento já cadastrado anteriormente.",
                )
                self.check_dados = False
                self.lift()
            else:
                self.entry_modalidade_enquadramento.set_success()
                self.entry_modalidade_enquadramento.set_disabled()
                self.modalidade_enquadramento.set(
                    ajuste_str(self.modalidade_enquadramento.get().strip())
                )
                self.btn_check_dados.set_disabled()
                self.btn_cadastrar.set_enabled()
                self.check_dados = True

    def comando_cadastrar(self):

        is_modalidade_exists = self.manager_sql.check_if_data_exists(
            f"SELECT MODALIDADE_ENQUADRAMENTO FROM TB_CADASTRO_MODALIDADE_ENQUADRAMENTO "
            f"WHERE MODALIDADE_ENQUADRAMENTO = '{self.modalidade_enquadramento.get()}'"
        )

        if is_modalidade_exists is True:
            Messagebox.show_info(
                title="Aviso",
                message="Modalidade enquandramento já cadastrado anteriormente.",
            )
            self.logger.info(log_message="CadastroModalidadeEnquadramento - Tentativa de cadastro de emissor já cadastrado")
            self.lift()
        else:
            data = {"MODALIDADE_ENQUADRAMENTO": [self.modalidade_enquadramento.get()]}

            df_to_upload = pd.DataFrame(data)

            self.manager_sql.insert_dataframe(
                df_to_upload, "TB_CADASTRO_MODALIDADE_ENQUADRAMENTO"
            )

            Messagebox.show_info(
                title="Aviso", message="Modalide enquadramento cadastrado com sucesso."
            )
            self.logger.info(log_message=f"CadastroModalidadeEnquadramento - Novo cadastro de emissor - {self.emissor.get()}")
            self.lift()

    def comando_reset(self):

        self.modalidade_enquadramento.set("")
        self.entry_modalidade_enquadramento.set_default()
        self.entry_modalidade_enquadramento.set_enabled()
        self.btn_cadastrar.set_disabled()
        self.btn_check_dados.set_enabled()


class ProcessManagerCadastroAtivos:

    def __init__(self, app=None, manager_sql=None, funcoes_pytools=None):

        if manager_sql is None:
            self.manager_sql = SQL_Manager()
        else:
            self.manager_sql = manager_sql

        if funcoes_pytools is None:
            self.funcoes_pytools = FuncoesPyTools(self.manager_sql)
        else:
            self.funcoes_pytools = funcoes_pytools

        self.tab = (
            "TB_CADASTRO_ATIVOS_TESTE"
            if ENVIRONMENT == "DEVELOPMENT"
            else "TB_CADASTRO_ATIVOS"
        )

        self.app = app

        self.logger = self.app.logger

    def reset_variaveis(self):

        # Campos principais
        self.app.tipo_ativo.set("")
        self.app.ativo.set("")
        self.app.cod_ativo_btg.set("")
        self.app.isin.set("")
        self.app.cod_if.set("")
        self.app.vne.set("")
        self.app.indexador.set("")
        self.app.taxa_emissao.set("")
        self.app.emissor.set("")
        self.app.entry_data_emissao.clear_date()
        self.app.entry_data_vencimento.clear_date()

        # Campos secundários
        self.app.setor.set("")
        self.app.gestor.set("")
        self.app.cnpj.set("")
        self.app.cod_bbg.set("")
        self.app.grupo_economico.set("")
        self.app.tipo_emissor.set("")
        self.app.obs.set("")
        self.app.modalidade_enquadramento.set("")
        self.app.classe_ativo.set("")

        self.app.entry_data_rentabilidade.clear_date()

    def travar_widgets(self):

        # Campos principais
        self.app.entry_ativo.set_disabled()
        self.app.box_emissor.set_disabled()
        self.app.entry_cod_ativo_btg.set_disabled()
        self.app.entry_cod_if.set_disabled()
        self.app.box_indexador.set_disabled()
        self.app.entry_taxa_emissao.set_disabled()
        self.app.entry_isin.set_disabled()
        self.app.entry_vne.set_disabled()
        self.app.entry_data_emissao.set_disabled()
        self.app.entry_data_vencimento.set_disabled()

        # Campos secundários
        self.app.box_setor.set_disabled()
        self.app.box_gestor.set_disabled()
        self.app.entry_cnpj.set_disabled()
        self.app.entry_cod_bbg.set_disabled()
        self.app.entry_grupo_economico.set_disabled()
        self.app.entry_tipo_emissor.set_disabled()
        self.app.text_obs.clear_text()
        self.app.entry_data_rentabilidade.set_disabled()
        self.app.box_modalidade_enquadramento.set_disabled()
        self.app.box_classe_ativo.set_disabled()

    def reset_widgets(self):

        # Campos principais
        self.app.box_tipo_ativo.set_enabled()
        self.app.entry_ativo.set_disabled()
        self.app.box_emissor.set_disabled()
        self.app.entry_cod_ativo_btg.set_disabled()
        self.app.entry_cod_if.set_disabled()
        self.app.box_indexador.set_disabled()
        self.app.entry_taxa_emissao.set_disabled()
        self.app.entry_isin.set_disabled()
        self.app.entry_vne.set_disabled()
        self.app.entry_data_emissao.set_disabled()
        self.app.entry_data_vencimento.set_disabled()

        self.app.box_tipo_ativo.set_default()
        self.app.entry_ativo.set_default()
        self.app.box_emissor.set_default()
        self.app.entry_cod_ativo_btg.set_default()
        self.app.entry_cod_if.set_default()
        self.app.box_indexador.set_default()
        self.app.entry_taxa_emissao.set_default()
        self.app.entry_isin.set_default()
        self.app.entry_vne.set_default()
        self.app.entry_data_emissao.set_default()
        self.app.entry_data_vencimento.set_default()

        # Campos secundários
        self.app.box_setor.set_disabled()
        self.app.box_gestor.set_disabled()
        self.app.entry_cnpj.set_disabled()
        self.app.entry_cod_bbg.set_disabled()
        self.app.entry_grupo_economico.set_disabled()
        self.app.entry_tipo_emissor.set_disabled()
        self.app.text_obs.clear_text()
        self.app.entry_data_rentabilidade.set_disabled()
        self.app.box_modalidade_enquadramento.set_disabled()
        self.app.box_classe_ativo.set_disabled()

        self.app.box_setor.set_default()
        self.app.box_gestor.set_default()
        self.app.entry_cnpj.set_default()
        self.app.entry_cod_bbg.set_default()
        self.app.entry_grupo_economico.set_default()
        self.app.entry_tipo_emissor.set_default()
        self.app.entry_data_rentabilidade.set_default()
        self.app.box_modalidade_enquadramento.set_default()
        self.app.box_classe_ativo.set_default()

    def comando_reset(self):

        self.app.btn_check_dados.set_enabled()
        self.app.btn_confirmar_dados.set_disabled()
        self.app.btn_confirmar_dados.grid_remove()
        self.app.btn_exec_cadastro.set_disabled()
        self.app.btn_exec_cadastro.grid_remove()

        self.app.text_box_resumo.clear_text()
        self.app.text_box_resumo.set_default()

        self.reset_variaveis()
        self.reset_widgets()

        self.app.process_pre_check = False

    def set_states_widgets(self):

        if self.app.tipo_ativo.get() == "":
            self.app.text_box_resumo.insert("end", "Selecionar Tipo Ativo.\n\n")
            self.app.text_box_resumo.configure(bootstyle="danger")
            self.app.box_tipo_ativo.set_danger()
        else:
            self.app.process_pre_check = True
            self.app.text_box_resumo.delete("1.0", "end")
            self.app.box_tipo_ativo.set_success()
            self.app.box_tipo_ativo.set_disabled()

            # State Ativo:
            if self.app.tipo_ativo.get() in [
                "LF",
                "LFSC",
                "LFSN",
                "LFSN-PRE",
                "CCB",
                "CDB",
                "LFT",
                "NTN-B",
                "LTN",
                "NTN-F",
            ]:
                self.app.entry_ativo.set_readonly()
            elif self.app.tipo_ativo.get() in ["Debênture", "FIDC"]:
                self.app.entry_ativo.set_enabled()

            # State Emissor:
            if self.app.tipo_ativo.get() in [
                "LF",
                "LFSC",
                "LFSN",
                "LFSN-PRE",
                "CCB",
                "CDB",
                "Debênture",
                "FIDC",
            ]:
                self.app.box_emissor.set_enabled()
            elif self.app.tipo_ativo.get() in ["LFT", "NTN-B", "LTN", "NTN-F"]:
                self.app.emissor.set("TESOURO NACIONAL")

            # State Cod Ativo BTG:
            if self.app.tipo_ativo.get() in [
                "LF",
                "LFSC",
                "LFSN",
                "LFSN-PRE",
                "CCB",
                "CDB",
                "Debênture",
                "FIDC"
            ]:
                self.app.entry_cod_ativo_btg.set_enabled()

            # State Cod. IF:
            if self.app.tipo_ativo.get() in [
                "LF",
                "LFSC",
                "LFSN",
                "LFSN-PRE",
                "CCB",
                "CDB",
            ]:
                self.app.entry_cod_if.set_enabled()

            # State Indexador:
            if self.app.tipo_ativo.get() in [
                "LF",
                "LFSC",
                "LFSN",
                "LFSN-PRE",
                "CCB",
                "CDB",
                "Debênture",
                "FIDC",
            ]:
                self.app.box_indexador.set_enabled()

            # State Taxa Emissão:
            if self.app.tipo_ativo.get() in [
                "LF",
                "LFSC",
                "LFSN",
                "LFSN-PRE",
                "CCB",
                "CDB",
                "Debênture",
                "FIDC",
            ]:
                self.app.entry_taxa_emissao.set_enabled()

            # State ISIN:
            if self.app.tipo_ativo.get() in [
                "LF",
                "LFSC",
                "LFSN",
                "LFSN-PRE",
                "CCB",
                "CDB",
                "LFT",
                "NTN-B",
                "LTN",
                "NTN-F",
                "Debênture",
                "FIDC",
            ]:
                self.app.entry_isin.set_enabled()

            # State VNE:
            if self.app.tipo_ativo.get() in [
                "LF",
                "LFSC",
                "LFSN",
                "LFSN-PRE",
                "CCB",
                "CDB",
                "Debênture",
            ]:
                self.app.entry_vne.set_enabled()

            # State Data Emissão:
            if self.app.tipo_ativo.get() in [
                "LF",
                "LFSC",
                "LFSN",
                "LFSN-PRE",
                "CCB",
                "CDB",
                "LFT",
                "NTN-B",
                "LTN",
                "NTN-F",
                "Debênture",
                "FIDC",
            ]:
                self.app.entry_data_emissao.set_enabled()

            # State Data Vencimento:
            if self.app.tipo_ativo.get() in [
                "LF",
                "LFSC",
                "LFSN",
                "LFSN-PRE",
                "CCB",
                "CDB",
                "LFT",
                "NTN-B",
                "LTN",
                "NTN-F",
                "Debênture",
                "FIDC",
            ]:
                self.app.entry_data_vencimento.set_enabled()

            # State Modalidade Enquadramento:
            if self.app.tipo_ativo.get() in [
                "LF",
                "LFSC",
                "LFSN",
                "LFSN-PRE",
                "CCB",
                "CDB",
                "LFT",
                "NTN-B",
                "LTN",
                "NTN-F",
                "Debênture",
                "FIDC",
            ]:
                self.app.box_modalidade_enquadramento.set_enabled()

            # State Classe Ativo:
            if self.app.tipo_ativo.get() in [
                "LF",
                "LFSC",
                "LFSN",
                "LFSN-PRE",
                "CCB",
                "CDB",
                "LFT",
                "NTN-B",
                "LTN",
                "NTN-F",
                "Debênture",
                "FIDC",
            ]:
                self.app.box_classe_ativo.set_enabled()

            # State Setor:
            if self.app.tipo_ativo.get() in [
                "LF",
                "LFSC",
                "LFSN",
                "LFSN-PRE",
                "CCB",
                "CDB",
                "Debênture",
                "FIDC",
            ]:
                self.app.box_setor.set_enabled()

            # State Gestor:
            if self.app.tipo_ativo.get() in ["FIDC"]:
                self.app.box_gestor.set_enabled()

            # State CNPJ:
            if self.app.tipo_ativo.get() in ["FIDC"]:
                self.app.entry_cnpj.set_enabled()

            # State Cod BBG:
            if self.app.tipo_ativo.get() in [
                "LF",
                "LFSC",
                "LFSN",
                "LFSN-PRE",
                "CCB",
                "CDB",
                "LFT",
                "NTN-B",
                "LTN",
                "NTN-F",
                "Debênture",
                "FIDC",
            ]:
                self.app.entry_cod_bbg.set_enabled()

            # State Data Rentabilidade:
            if self.app.tipo_ativo.get() in ["Debênture"]:
                self.app.entry_data_rentabilidade.set_enabled()

    def comando_botao_check_dados(self):

        def check_all_pre_dados():

            resultado = "ok"

            if self.app.tipo_ativo.get() == "":
                self.app.text_box_resumo.insert("end", "Selecionar Tipo Ativo.\n\n")
                self.app.text_box_resumo.set_danger()
                return "not"

            if self.app.process_pre_check is False:
                self.set_states_widgets()

            if self.app.emissor.get() == "Cadastrar Novo":

                windowCadastroEmissor(
                    app=self,
                    manager_sql=self.app.manager_sql,
                    funcoes_pytools=self.app.funcoes_pytools,
                    logger=self.logger,
                )

                self.app.emissor.set("")

            elif self.app.emissor.get() != "":

                self.app.update_emissores()

                if self.app.emissor.get() not in self.app.lista_emissores:
                    self.app.box_emissor.set_danger()
                    self.app.text_box_resumo.insert(
                        "end", "Emissor: não cadastrado.\n\n"
                    )
                    resultado = "not"
                else:
                    self.app.box_emissor.set_success()

            if self.app.indexador.get() != "":

                if self.app.indexador.get() not in self.app.lista_indexadores:
                    self.app.box_indexador.set_danger()
                    self.app.text_box_resumo.insert(
                        "end", "Indexador: não cadastrado.\n\n"
                    )
                    resultado = "not"
                else:
                    self.app.box_indexador.set_success()

            if self.app.taxa_emissao.get() != "":
                try:
                    float(self.app.taxa_emissao.get())
                    self.app.entry_taxa_emissao.set_success()
                except ValueError:
                    self.app.entry_taxa_emissao.set_danger()
                    self.app.text_box_resumo.insert(
                        "end", "Taxa de Emissão: usar '.' como separador decimal.\n\n"
                    )
                    resultado = "not"

            if self.app.vne.get() != "":
                try:
                    float(self.app.vne.get())
                    self.app.entry_vne.set_success()
                except ValueError:
                    self.app.entry_vne.set_danger()
                    self.app.text_box_resumo.insert(
                        "end", "VNE: usar '.' como separador decimal.\n\n"
                    )
                    resultado = "not"

            if self.app.entry_data_emissao.entry.get() != "":
                try:
                    datetime.strptime(
                        self.app.entry_data_emissao.entry.get(), "%d/%m/%Y"
                    )
                    self.app.entry_data_emissao.set_success()
                except ValueError:
                    self.app.entry_data_emissao.set_danger()
                    self.app.text_box_resumo.insert(
                        "end", "Data de emissão: usar formato dd/mm/aaaa.\n\n"
                    )
                    resultado = "not"

            if self.app.entry_data_vencimento.entry.get() != "":
                try:
                    datetime.strptime(
                        self.app.entry_data_vencimento.entry.get(), "%d/%m/%Y"
                    )
                    self.app.entry_data_vencimento.set_success()
                except ValueError:
                    self.app.entry_data_vencimento.set_danger()
                    self.app.text_box_resumo.insert(
                        "end", "Data de vencimento: usar formato dd/mm/aaaa.\n\n"
                    )
                    resultado = "not"

            if resultado == "ok":
                self.app.text_box_resumo.configure(bootstyle="default")
            else:
                self.app.text_box_resumo.configure(bootstyle="danger")

            return resultado

        def suporte_convert_datas(data_to_convert):
            data = datetime.strptime(data_to_convert, "%d/%m/%Y").date()
            return data.strftime("%Y-%m-%d")

        def suporte_retorna_date(data_to_convert):
            return datetime.strptime(data_to_convert, "%d/%m/%Y").date()

        def remove_s_a_suffix(string):

            if string.endswith("S/A") or string.endswith("S.A."):
                last_space_index = string.rfind(" ", 0, -3)
                return string[:last_space_index].strip()
            return string

        def check_dados_ativo():

            if self.app.tipo_ativo.get() in [
                "LF",
                "LFSC",
                "LFSN",
                "LFSN-PRE",
                "CCB",
                "CDB",
            ]:

                if (
                    self.app.emissor.get() == "" or  # noqa: W504
                    self.app.entry_data_vencimento.entry.get() == "" or  # noqa: W504
                    self.app.indexador.get() == "" or  # noqa: W504
                    self.app.taxa_emissao.get() == "" or  # noqa: W504
                    self.app.indexador.get() == ""
                ):

                    self.app.entry_ativo.set_danger()
                    self.app.ativo.set("Pend. Dados")

                    self.app.text_box_resumo.insert("end", "Ativo:\n")

                    if self.app.emissor.get() == "":
                        self.app.text_box_resumo.insert(
                            "end", "  Selecionar emissor.\n"
                        )

                    if self.app.entry_data_vencimento.entry.get() == "":
                        self.app.text_box_resumo.insert(
                            "end", "  Data de vencimento vazia.\n"
                        )

                    if (
                        self.app.indexador.get() == "Selecione" or self.app.indexador.get() == ""
                    ):
                        self.app.text_box_resumo.insert(
                            "end", "  Selecionar indexador.\n"
                        )

                    if self.app.taxa_emissao.get() == "":
                        self.app.text_box_resumo.insert(
                            "end", "  Taxa de emissão vazia.\n"
                        )

                    self.check_ativo = False
                else:
                    self.app.entry_ativo.set_success()
                    ativo = (
                        f"{self.app.tipo_ativo.get()} {remove_s_a_suffix(self.app.emissor.get())} "
                        f"{suporte_convert_datas(self.app.entry_data_vencimento.entry.get())} "
                        f"@ {self.app.indexador.get()} {float(self.app.taxa_emissao.get()):.4f}"
                    )
                    self.app.ativo.set(ativo)
                    self.app.text_box_resumo.insert("end", f"Ativo: {ativo}\n")
                    self.check_ativo = True

            elif self.app.tipo_ativo.get() in ["LFT", "NTN-B", "LTN", "NTN-F"]:

                if self.app.entry_data_vencimento.entry.get() == "":
                    self.app.entry_ativo.set_danger()
                    self.app.ativo.set("Pend. Dados")
                    self.app.text_box_resumo.insert(
                        "end", "Ativo: Data de vencimento vazia.\n"
                    )
                    self.check_ativo = False
                else:
                    self.app.entry_ativo.set_success()
                    data_vencimento = suporte_retorna_date(
                        self.app.entry_data_vencimento.entry.get()
                    )
                    self.app.ativo.set(
                        f"{self.app.tipo_ativo.get()} {data_vencimento.strftime('%b-%y')}"
                    )
                    self.check_ativo = True

            else:
                if self.app.ativo.get() == "":
                    self.app.entry_ativo.set_danger()
                    self.app.text_box_resumo.insert(
                        "end", "Ativo: Campo obrigatório.\n"
                    )
                    self.check_ativo = False
                else:
                    self.app.entry_ativo.set_success()
                    self.app.ativo.set(self.app.ativo.get().strip().upper())
                    self.app.text_box_resumo.insert(
                        "end", f"Ativo: {self.app.ativo.get()}\n"
                    )
                    self.check_ativo = True

            self.lista_status_checks.append(self.check_ativo)

        def check_dados_cod_ativo_btg():

            if self.app.cod_ativo_btg.get() == "":

                self.app.entry_cod_ativo_btg.set_warning()
                self.app.text_box_resumo.insert(
                    "end",
                    "Cod. Ativo BTG: Permitido vazio, necessário para rodar carteira.\n",
                )
            else:
                self.app.entry_cod_ativo_btg.set_success()
                self.app.text_box_resumo.insert(
                    "end", f"Cod. Ativo BTG: {self.app.cod_ativo_btg.get()}\n"
                )

        def check_dados_isin():

            if self.app.isin.get() == "":
                self.app.entry_isin.set_warning()
                self.app.text_box_resumo.insert(
                    "end",
                    "ISIN: Permitido vazio, porém necessário preenchimento posterior.\n",
                )
            else:
                self.app.entry_isin.set_success()
                self.app.text_box_resumo.insert("end", f"ISIN: {self.app.isin.get()}\n")

        def check_dados_emissor():

            if self.app.emissor.get() == "":
                self.app.box_emissor.set_danger()
                self.app.text_box_resumo.insert(
                    "end", "Emissor: Preenchimento obrigarório.\n"
                )
                self.check_emissor = False
            else:
                self.app.box_emissor.set_success()
                self.app.text_box_resumo.insert(
                    "end", f"Emissor: {self.app.emissor.get()}\n"
                )
                self.check_emissor = True

            self.lista_status_checks.append(self.check_emissor)

        def check_dados_cod_if():

            if self.app.cod_if.get() == "":
                self.app.entry_cod_if.set_danger()
                self.app.text_box_resumo.insert(
                    "end", "Cod. IF: Preenchimento obrigarório.\n"
                )
                self.check_cod_if = False
            else:
                self.app.entry_cod_if.set_success()
                self.app.text_box_resumo.insert(
                    "end", f"Cod. IF: {self.app.cod_if.get()}\n"
                )
                self.check_cod_if = True

            self.lista_status_checks.append(self.check_cod_if)

        def check_dados_indexador():

            if self.app.indexador.get() == "":
                self.app.box_indexador.set_danger()
                self.app.text_box_resumo.insert(
                    "end", "Indexador: Preenchimento obrigarório.\n"
                )
                self.check_indexador = False
            else:
                self.app.box_indexador.set_success()
                self.app.text_box_resumo.insert(
                    "end", f"Indexador: {self.app.indexador.get()}\n"
                )
                self.check_indexador = True

            self.lista_status_checks.append(self.check_indexador)

        def check_dados_taxa_emissao():

            if self.app.taxa_emissao.get() == "":
                self.app.entry_taxa_emissao.set_danger()
                self.app.text_box_resumo.insert(
                    "end", "Taxa de Emissão: Preenchimento obrigarório.\n"
                )
                self.check_taxa_emissao = False
            else:
                self.app.entry_taxa_emissao.set_success()
                self.app.text_box_resumo.insert(
                    "end",
                    f"Taxa de Emissão: {float(self.app.taxa_emissao.get()):.4f}%\n",
                )
                self.check_taxa_emissao = True

            self.lista_status_checks.append(self.check_taxa_emissao)

        def check_dados_vne():

            if self.app.vne.get() == "":
                self.app.entry_vne.set_danger()
                self.app.text_box_resumo.insert(
                    "end", "VNE: Preenchimento obrigarório.\n"
                )
                self.check_vne = False
            else:
                self.app.entry_vne.set_success()
                self.app.text_box_resumo.insert(
                    "end", f"VNE: {float(self.app.vne.get()):,.2f}\n"
                )
                self.check_vne = True

            self.lista_status_checks.append(self.check_vne)

        def check_dados_data_emissao():

            if self.app.entry_data_emissao.entry.get() == "":
                self.app.entry_data_emissao.set_danger()
                self.app.text_box_resumo.insert(
                    "end", "Data Emissão: Preenchimento obrigarório.\n"
                )
                self.check_data_emissao = False
            else:
                self.app.entry_data_emissao.set_success()
                self.app.text_box_resumo.insert(
                    "end",
                    f"Data Emissão: {suporte_convert_datas(self.app.entry_data_emissao.entry.get())}\n",
                )
                self.check_data_emissao = True

            self.lista_status_checks.append(self.check_data_emissao)

        def check_dados_data_vencimento():

            if self.app.entry_data_vencimento.entry.get() == "":
                self.app.entry_data_vencimento.set_danger()
                self.app.text_box_resumo.insert(
                    "end", "Data Vencimento: Preenchimento obrigarório.\n"
                )
                self.check_data_vencimento = False
            else:
                self.app.entry_data_vencimento.set_success()
                self.app.text_box_resumo.insert(
                    "end",
                    f"Data Vencimento: {suporte_convert_datas(self.app.entry_data_vencimento.entry.get())}\n",
                )
                self.check_data_vencimento = True

            self.lista_status_checks.append(self.check_data_vencimento)

        def check_dados_data_rentabilidade():

            if self.app.tipo_ativo.get() in [
                "LF",
                "LFSC",
                "LFSN",
                "LFSN-PRE",
                "CCB",
                "CDB",
            ]:
                if self.app.entry_data_emissao.entry.get() == "":
                    self.app.entry_data_rentabilidade.set_danger()
                    self.app.text_box_resumo.insert(
                        "end",
                        "Data Inicio Rentabilidade: Aguardando preenchimento 'Data Emissão'.\n",
                    )
                    self.check_data_rentabilidade = False
                else:
                    self.app.entry_data_rentabilidade.set_success()
                    self.app.entry_data_rentabilidade.clear_date()
                    self.app.entry_data_rentabilidade.set_enabled()
                    self.app.entry_data_rentabilidade.set_date(
                        self.app.entry_data_emissao.entry.get()
                    )
                    self.app.entry_data_rentabilidade.set_disabled()
                    self.app.text_box_resumo.insert(
                        "end",
                        f"Data Inicio Rentabilidade: {suporte_convert_datas(self.app.entry_data_rentabilidade.entry.get())}\n",
                    )
                    self.check_data_rentabilidade = True
            elif self.app.tipo_ativo.get() in ["Debênture"]:
                if self.app.entry_data_emissao.entry.get() == "":
                    self.app.entry_data_rentabilidade.set_danger()
                    self.app.text_box_resumo.insert(
                        "end",
                        "Data Inicio Rentabilidade: Preenchimento obrigatório.\n",
                    )
                    self.check_data_rentabilidade = False
                else:
                    self.app.entry_data_rentabilidade.set_success()
                    self.app.text_box_resumo.insert(
                        "end",
                        f"Data Inicio Rentabilidade: {suporte_convert_datas(self.app.entry_data_rentabilidade.entry.get())}\n",
                    )
                    self.check_data_rentabilidade = True

            self.lista_status_checks.append(self.check_data_rentabilidade)

        def check_dados_grupo_economico():

            if self.app.emissor.get() == "":
                self.app.grupo_economico.set("Pend. Dados")
                self.app.entry_grupo_economico.set_danger()
            else:
                self.app.grupo_economico.set(
                    self.app.dict_grupo_economico[self.app.emissor.get()]
                )
                self.app.entry_grupo_economico.set_success()

        def check_dados_tipo_emissor():

            if self.app.emissor.get() == "":
                self.app.tipo_emissor.set("Pend. Dados")
                self.app.entry_tipo_emissor.set_danger()
            else:
                self.app.tipo_emissor.set(
                    self.app.dict_tipo_emissor[self.app.emissor.get()]
                )
                self.app.entry_tipo_emissor.set_success()

        def check_dados_setor():

            self.app.update_setores()

            if self.app.setor.get() == "":
                self.app.box_setor.set_warning()
                self.check_setor = False
            elif self.app.setor.get() == "Cadastrar Novo":
                self.app.box_setor.set_warning()
                self.app.setor.set("")
                windowCadastroSetor(
                    app=self.app,
                    manager_sql=self.app.manager_sql,
                    funcoes_pytools=self.app.funcoes_pytools,
                    logger=self.logger,
                )
                self.check_setor = False
            else:
                if self.app.setor.get() not in self.app.lista_setores:
                    self.app.box_setor.set_danger()
                    self.app.text_box_resumo.insert(
                        "end", "Setor: Preenchimento obrigatório.\n"
                    )
                    Messagebox.show_info(title="Aviso", message="Setor não cadastrado.")
                    self.app.setor.set("")
                    self.check_setor = False
                else:
                    self.app.box_setor.set_success()
                    self.check_setor = True

            self.lista_status_checks.append(self.check_setor)

        def check_dados_gestor():

            if self.app.gestor.get() == "":
                self.app.box_gestor.set_warning()
            else:
                self.app.box_gestor.set_success()

        def check_dados_cnpj():

            if self.app.cnpj.get() == "":
                self.app.entry_cnpj.set_warning()
            else:
                self.app.entry_cnpj.set_success()

        def check_dados_cod_bbg():

            if self.app.cod_bbg.get() == "":
                self.app.entry_cod_bbg.set_warning()
            else:
                self.app.entry_cod_bbg.set_success()

        def check_dados_obs():

            if self.app.text_obs.check_if_text():
                self.app.text_obs.set_max_chars(150)
                self.app.text_obs.set_success()
                self.app.obs = self.app.text_obs.get_text()

        def check_dados_classe_ativo():

            if self.app.classe_ativo.get() == "":
                try:
                    self.app.classe_ativo.set(
                        self.app.dict_classe_ativo[self.app.tipo_ativo.get()]
                    )
                    self.app.box_classe_ativo.set_warning()
                    self.app.text_box_resumo.insert(
                        "end",
                        f"Classe Ativo: {self.app.classe_ativo.get()}. Verificar se está correto.\n",
                    )
                    self.check_classe_ativo = True
                except Exception:
                    self.app.box_classe_ativo.set_danger()
                    self.app.text_box_resumo.insert(
                        "end", "Classe Ativo: Preenchimento obrigatório.\n"
                    )
                    self.check_classe_ativo = False
            elif self.app.classe_ativo.get() not in self.app.lista_classe_ativo:
                self.app.box_classe_ativo.set_danger()
                self.app.classe_ativo.set("")
                Messagebox.show_info(
                    title="Aviso", message="Classe ativo não cadastrado."
                )
                self.app.text_box_resumo.insert(
                    "end", "Classe Ativo: Preenchimento obrigatório.\n"
                )
                self.check_classe_ativo = False
            elif self.app.classe_ativo.get() == "Cadastrar Novo":
                self.app.box_classe_ativo.set_warning()
                self.app.classe_ativo.set("")
                windowCadastroClasseAtivo(
                    app=self.app,
                    manager_sql=self.app.manager_sql,
                    funcoes_pytools=self.app.funcoes_pytools,
                    logger=self.logger,
                )
                self.check_classe_ativo = False
            else:
                self.app.box_classe_ativo.set_warning()
                self.app.text_box_resumo.insert(
                    "end",
                    f"Classe Ativo: {self.app.classe_ativo.get()}. Verificar se está correto.\n",
                )
                self.check_classe_ativo = True

            self.lista_status_checks.append(self.check_classe_ativo)

        def check_dados_modalidade_enquadramento():

            if self.app.modalidade_enquadramento.get() == "":
                try:
                    self.app.modalidade_enquadramento.set(
                        self.app.dict_modalidade_enquadramento[
                            self.app.tipo_ativo.get()
                        ]
                    )
                    self.app.box_modalidade_enquadramento.set_warning()
                    self.app.text_box_resumo.insert(
                        "end",
                        f"Modalidade Enquadramento: {self.app.modalidade_enquadramento.get()}. Verificar se está correto.\n",
                    )
                    self.check_modalidade_enquadramento = True
                except Exception:
                    self.app.box_modalidade_enquadramento.set_danger()
                    self.app.text_box_resumo.insert(
                        "end", "Modalidade Enquadramento: Preenchimento obrigatório.\n"
                    )
                    self.check_modalidade_enquadramento = False
            elif (
                self.app.modalidade_enquadramento.get()
                not in self.app.lista_modalidade_enquadramento
            ):
                self.app.box_modalidade_enquadramento.set_danger()
                self.app.modalidade_enquadramento.set("")
                Messagebox.show_info(
                    title="Aviso", message="Modalidade enquadramento não cadastrado."
                )
                self.app.text_box_resumo.insert(
                    "end", "Modalidade Enquadramento: Preenchimento obrigatório.\n"
                )
                self.check_modalidade_enquadramento = False
            elif self.app.modalidade_enquadramento.get() == "Cadastrar Novo":
                self.app.box_modalidade_enquadramento.set_danger()
                self.app.modalidade_enquadramento.set("")
                windowCadastroModalideEnquadramento(
                    app=self.app,
                    manager_sql=self.app.manager_sql,
                    funcoes_pytools=self.app.funcoes_pytools,
                    logger=self.logger
                )
                self.check_modalidade_enquadramento = False
            else:
                self.app.box_modalidade_enquadramento.set_warning()
                self.app.text_box_resumo.insert(
                    "end",
                    f"Modalidade Enquadramento: {self.app.modalidade_enquadramento.get()}. Verificar se está correto.\n",
                )
                self.check_modalidade_enquadramento = True

            self.lista_status_checks.append(self.check_modalidade_enquadramento)

        # -------------------------------------------------------------------------------

        def checks_lfs_e_cdb():

            self.app.text_box_resumo.delete("1.0", "end")

            check_dados_ativo()
            check_dados_emissor()
            check_dados_cod_ativo_btg()
            check_dados_cod_if()
            check_dados_indexador()
            check_dados_taxa_emissao()
            check_dados_isin()
            check_dados_vne()
            check_dados_data_emissao()
            check_dados_data_rentabilidade()
            check_dados_data_vencimento()
            check_dados_grupo_economico()
            check_dados_tipo_emissor()
            check_dados_setor()
            check_dados_obs()
            check_dados_classe_ativo()
            check_dados_modalidade_enquadramento()

            if all(self.lista_status_checks):
                self.app.text_box_resumo.configure(bootstyle="success")
                all_checks_ok()
            else:
                self.app.text_box_resumo.configure(bootstyle="danger")

        def checks_debentures():

            self.app.text_box_resumo.delete("1.0", "end")

            check_dados_ativo()
            check_dados_emissor()
            check_dados_cod_ativo_btg()
            check_dados_indexador()
            check_dados_taxa_emissao()
            check_dados_isin()
            check_dados_vne()
            check_dados_data_emissao()
            check_dados_data_rentabilidade()
            check_dados_data_vencimento()
            check_dados_grupo_economico()
            check_dados_tipo_emissor()
            check_dados_setor()
            check_dados_obs()
            check_dados_classe_ativo()
            check_dados_modalidade_enquadramento()

            if all(self.lista_status_checks):
                self.app.text_box_resumo.configure(bootstyle="success")
                all_checks_ok()
            else:
                self.app.text_box_resumo.configure(bootstyle="danger")

        def checks_tit_publicos():

            self.app.text_box_resumo.clear_text()
            check_dados_ativo()
            check_dados_emissor()
            check_dados_isin()
            check_dados_data_emissao()
            check_dados_data_vencimento()
            check_dados_grupo_economico()
            check_dados_tipo_emissor()
            check_dados_classe_ativo()
            check_dados_modalidade_enquadramento()

            if all(self.lista_status_checks):
                self.app.text_box_resumo.configure(bootstyle="success")
                all_checks_ok()
            else:
                self.app.text_box_resumo.configure(bootstyle="danger")

        def checks_fidcs():

            self.app.text_box_resumo.delete("1.0", "end")
            check_dados_ativo()
            check_dados_emissor()
            check_dados_cod_ativo_btg()
            check_dados_indexador()
            check_dados_taxa_emissao()
            check_dados_isin()
            check_dados_data_emissao()
            check_dados_data_vencimento()
            check_dados_grupo_economico()
            check_dados_tipo_emissor()
            check_dados_obs()

            if all(self.lista_status_checks):
                self.app.text_box_resumo.configure(bootstyle="success")
                all_checks_ok()
            else:
                self.app.text_box_resumo.configure(bootstyle="danger")

        def all_checks_ok():

            self.app.btn_confirmar_dados.grid(
                row=0, column=4, sticky="e", padx=(10, 0), pady=5
            )
            self.app.btn_confirmar_dados.set_enabled()
            self.app.text_box_resumo.insert(
                "end", "\nTodos os campos obrigarórios preenchidos.\n"
            )
            self.app.text_box_resumo.insert("end", "Conferir dados de cadastro.\n")

        self.app.text_box_resumo.delete("1.0", "end")

        if check_all_pre_dados() == "ok":

            self.lista_status_checks = []

            if self.app.tipo_ativo.get() == "Debênture":
                checks_debentures()

            elif self.app.tipo_ativo.get() in [
                "LF",
                "LFSC",
                "LFSN",
                "LFSN-PRE",
                "CCB",
                "CDB",
            ]:
                checks_lfs_e_cdb()

            elif self.app.tipo_ativo.get() in ["LFT", "NTN-B", "LTN", "NTN-F"]:
                checks_tit_publicos()

            elif self.app.tipo_ativo.get() in ["FIDC"]:
                checks_fidcs()

            else:
                self.app.text_box_resumo.delete("1.0", "end")
                if self.app.ativo.get() == "":
                    self.app.ativo.set("Pend. Dados")
                    self.app.text_box_resumo.insert(
                        "end", "Ativo: Falta preenchimento.\n"
                    )
                else:
                    self.app.text_box_resumo.insert(
                        "end", f"Ativo: {self.app.ativo.get()}\n"
                    )
                    self.app.ativo_ok = True

    def comando_confirmar_dados(self):

        confirma = Messagebox.okcancel(
            message=("Travar dados para cadastro?"), title="Cadstro de Ativo"
        )

        if confirma == "OK":
            self.app.btn_check_dados.set_disabled()
            self.travar_widgets()
            self.app.btn_confirmar_dados.set_disabled()
            self.app.btn_confirmar_dados.grid_remove()
            self.app.btn_exec_cadastro.grid(
                row=0, column=4, sticky="e", padx=(10, 0), pady=5
            )
            self.app.btn_exec_cadastro.set_enabled()

            if self.app.tipo_ativo.get() in [
                "LF",
                "LFSC",
                "LFSN",
                "LFSN-PRE",
                "CCB",
                "CDB",
                "Debênture",
                "FIDC",
            ]:
                if self.app.cod_ativo_btg.get() == "":
                    self.app.cod_ativo_btg.set("Cadastrar")

    def comando_cadastrar_ativo(self):

        def suporte_convert_datas_df(data_to_convert):
            data = datetime.strptime(data_to_convert, "%d/%m/%Y").date()
            return data

        data = {}

        data["ATIVO"] = [self.app.ativo.get()]
        data["COD_BBG"] = [
            None if self.app.cod_bbg.get() == "" else self.app.cod_bbg.get()
        ]
        data["TIPO_ATIVO"] = [
            (
                "Tit. Publicos"
                if self.app.tipo_ativo.get() in ["LFT", "NTN-B", "NTN-F", "LTN"]
                else self.app.tipo_ativo.get()
            )
        ]
        data["COD_JPM"] = [None]
        data["OBS"] = [None if self.app.obs.get() == "" else self.app.obs.get()]
        data["ISIN"] = [None if self.app.isin.get() == "" else self.app.isin.get()]
        data["EMISSOR"] = [
            None if self.app.emissor.get() == "" else self.app.emissor.get()
        ]
        data["COD_ATIVO_BTG"] = [
            None if self.app.cod_ativo_btg.get() == "" else self.app.cod_ativo_btg.get()
        ]
        data["TAXA_EMISSAO"] = [
            None if self.app.taxa_emissao.get() == "" else self.app.taxa_emissao.get()
        ]
        data["SETOR"] = [None if self.app.setor.get() == "" else self.app.setor.get()]
        data["INDEXADOR"] = [
            None if self.app.indexador.get() == "" else self.app.indexador.get()
        ]
        data["DATA_VENCIMENTO"] = [
            (
                None
                if self.app.entry_data_vencimento.entry.get() == ""
                else suporte_convert_datas_df(
                    self.app.entry_data_vencimento.entry.get()
                )
            )
        ]
        data["CNPJ"] = [None if self.app.cnpj.get() == "" else self.app.cnpj.get()]
        data["GESTOR"] = [
            None if self.app.gestor.get() == "" else self.app.gestor.get()
        ]
        data["DATA_EMISSAO"] = [
            (
                None
                if self.app.entry_data_emissao.entry.get() == ""
                else suporte_convert_datas_df(self.app.entry_data_emissao.entry.get())
            )
        ]
        data["COD_IF"] = [
            None if self.app.cod_if.get() == "" else self.app.cod_if.get()
        ]
        data["VNE"] = [None if self.app.vne.get() == "" else self.app.vne.get()]
        data["DATA_INICIO_RENTABILDIADE"] = [
            (
                None
                if self.app.entry_data_rentabilidade.entry.get() == ""
                else suporte_convert_datas_df(
                    self.app.entry_data_rentabilidade.entry.get()
                )
            )
        ]
        data["GRUPO_ECONOMICO"] = [
            (
                None
                if self.app.grupo_economico.get() == ""
                else self.app.grupo_economico.get()
            )
        ]
        data["CLASSE_ATIVO"] = ["Pós fixado"]
        data["TIPO_EMISSOR"] = [
            None if self.app.tipo_emissor.get() == "" else self.app.tipo_emissor.get()
        ]
        data["MODALIDADE_ENQUADRAMENTO"] = [
            (
                None
                if self.app.modalidade_enquadramento.get() == ""
                else self.app.modalidade_enquadramento.get()
            )
        ]

        df = pd.DataFrame(data=data)

        self.manager_sql.insert_dataframe(df, self.tab)

        Messagebox.ok(
            message="Ativo cadastrado com sucesso.", title="Cadastro de Ativo"
        )

        self.app.janela_init.logger.info(log_message=f"CadastroAtivo - Ativo cadastrado com sucesso - {self.app.ativo.get()}")

        self.app.btn_exec_cadastro.set_disabled()


class CadastroAtivos(Toplevel):

    def __init__(
        self,
        app=None,
        janela_init=None,
        manager_sql=None,
        funcoes_pytools=None,
        *args,
        **kwargs,
    ):

        super().__init__(*args, **kwargs)

        self.title("BOS - Sistema Cadastro")
        self.geometry("970x1080")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.manager_sql = manager_sql if manager_sql is not None else SQL_Manager()

        self.funcoes_pytools = funcoes_pytools if funcoes_pytools is not None else FuncoesPyTools(self.manager_sql)

        self.lista_tipo_ativos = [
            "CCB",
            "CDB",
            "Debênture",
            "FIDC",
            "LF",
            "LFSC",
            "LFSN",
            "LFSN-PRE",
            "LFT",
            "NTN-B",
            "LTN",
            "NTN-F",
        ]

        self.lista_indexadores = [
            "CDI +",
            "CDI %",
            "SELIC +",
            "SELIC %",
            "IPCA +",
            "IPCA %",
            "PRE",
        ]

        self.app = app
        self.janela_init = janela_init
        self.logger = self.janela_init.logger

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.process_manager = ProcessManagerCadastroAtivos(
            app=self, manager_sql=self.manager_sql, funcoes_pytools=self.funcoes_pytools
        )

        self.process_pre_check = False

        self.digit_func = self.register(self.validate_number)

        self.update_dicionarios_suporte()
        self.update_emissores()
        self.update_setores()
        self.update_gestores()
        self.update_classe_ativo()
        self.update_modalidade_enquadramento()

        self.variaveis_cadastro_ativos()
        self.header_widgets()
        self.frame_body()
        self.widgets_pre_selecao()
        self.widgets_campos_principais()
        self.widgets_posicionamento_principais()
        self.widgets_campos_secundarios()
        self.widgets_posicionamento_secundarios()
        self.resumo_cadastro()

        self.logger.info(log_message="CadastroAtivo - Iniciado")

        self.mainloop()

    def on_close(self):
        self.janela_init.logger.info(log_message="CadastroAtivo - Finalizado")
        self.janela_init.logger.reset_index()
        self.destroy()
        self.janela_init.lift()

    def update_setores(self):

        self.lista_setores = self.manager_sql.select_dataframe(
            "SELECT * FROM TB_CADASTRO_SETOR ORDER BY SETOR"
        )["SETOR"].tolist()
        self.lista_setores.insert(0, "Cadastrar Novo")

    def update_box_setores(self):

        self.update_setores()
        self.box_setor["values"] = self.lista_setores

    def update_gestores(self):

        self.lista_gestores = self.manager_sql.select_dataframe(
            "SELECT DISTINCT GESTOR FROM TB_CADASTRO_ATIVOS WHERE GESTOR IS NOT NULL ORDER BY GESTOR"
        )["GESTOR"].tolist()

    def update_box_gestores(self):

        self.update_gestores()
        self.box_gestor["values"] = self.lista_gestores

    def update_emissores(self):

        tb_emissores = self.manager_sql.select_dataframe(
            "SELECT * FROM TB_CADASTRO_EMISSOR"
        )

        self.lista_emissores = tb_emissores["EMISSOR"].unique().tolist()
        self.lista_emissores.insert(0, "Cadastrar Novo")

        self.dict_grupo_economico = tb_emissores.set_index("EMISSOR")[
            "GRUPO_ECONOMICO"
        ].to_dict()
        self.dict_tipo_emissor = tb_emissores.set_index("EMISSOR")[
            "TIPO_EMISSOR"
        ].to_dict()

        self.dict_grupo_economico["Cadastrar Novo"] = "Aguardando novo cadastro."
        self.dict_tipo_emissor["Cadastrar Novo"] = "Aguardando novo cadastro."

    def update_box_emissores(self):

        self.update_emissores()
        self.box_emissor["values"] = self.lista_emissores

    def update_classe_ativo(self):

        self.lista_classe_ativo = self.manager_sql.select_dataframe(
            "SELECT * FROM TB_CADASTRO_CLASSE_ATIVO"
        )["CLASSE_ATIVO"].tolist()
        self.lista_classe_ativo.insert(0, "Cadastrar Novo")

    def update_box_classe_ativo(self):

        self.update_classe_ativo()
        self.box_classe_ativo["values"] = self.lista_classe_ativo

    def update_modalidade_enquadramento(self):

        self.lista_modalidade_enquadramento = self.manager_sql.select_dataframe(
            "SELECT * FROM TB_CADASTRO_MODALIDADE_ENQUADRAMENTO"
        )["MODALIDADE_ENQUADRAMENTO"].tolist()
        self.lista_modalidade_enquadramento.insert(0, "Cadastrar Novo")

    def update_box_modalidade_enquadramento(self):

        self.update_modalidade_enquadramento()
        self.box_modalidade_enquadramento["values"] = (
            self.lista_modalidade_enquadramento
        )

    def update_dicionarios_suporte(self):

        self.dict_modalidade_enquadramento = (
            self.manager_sql.select_dataframe(
                "SELECT DISTINCT TIPO_ATIVO, MODALIDADE_ENQUADRAMENTO FROM TB_CADASTRO_ATIVOS "
                " WHERE MODALIDADE_ENQUADRAMENTO IS NOT NULL AND TIPO_ATIVO NOT IN ('Tit. Publicos')"
            )
            .set_index("TIPO_ATIVO")["MODALIDADE_ENQUADRAMENTO"]
            .to_dict()
        )

        self.dict_modalidade_enquadramento["LFT"] = (
            "Títulos públicos federais e operações compromissadas"
        )
        self.dict_modalidade_enquadramento["NTN-B"] = (
            "Títulos públicos federais e operações compromissadas"
        )
        self.dict_modalidade_enquadramento["NTN-F"] = (
            "Títulos públicos federais e operações compromissadas"
        )
        self.dict_modalidade_enquadramento["LTN"] = (
            "Títulos públicos federais e operações compromissadas"
        )

        self.dict_classe_ativo = (
            self.manager_sql.select_dataframe(
                "SELECT DISTINCT TIPO_ATIVO, CLASSE_ATIVO FROM TB_CADASTRO_ATIVOS "
                " WHERE MODALIDADE_ENQUADRAMENTO IS NOT NULL AND TIPO_ATIVO NOT IN ('Tit. Publicos')"
            )
            .set_index("TIPO_ATIVO")["CLASSE_ATIVO"]
            .to_dict()
        )

        self.dict_classe_ativo["LFT"] = "Pós fixado"
        self.dict_classe_ativo["NTN-B"] = "Pós fixado"
        self.dict_classe_ativo["NTN-F"] = "Pós fixado"
        self.dict_classe_ativo["LTN"] = "Pós fixado"

    def validate_number(self, x) -> bool:

        if x == "":
            return True
        else:
            try:
                float(x)
                return True
            except Exception:
                return False

    def variaveis_cadastro_ativos(self):

        self.tipo_ativo = newStringVar()
        self.ativo = newStringVar()
        self.cod_ativo_btg = newStringVar()
        self.isin = newStringVar()
        self.cod_if = newStringVar()
        self.vne = newStringVar()
        self.indexador = newStringVar()
        self.taxa_emissao = newStringVar()
        self.emissor = newStringVar()
        self.setor = newStringVar()
        self.gestor = newStringVar()
        self.cnpj = newStringVar()
        self.cod_bbg = newStringVar()
        self.grupo_economico = newStringVar()
        self.tipo_emissor = newStringVar()
        self.obs = newStringVar()
        self.classe_ativo = newStringVar()
        self.modalidade_enquadramento = newStringVar()

    def header_widgets(self):

        frame_header = newFrame(self)
        frame_header.grid(row=0, column=0, sticky="new", padx=10, pady=10)
        frame_header.columnconfigure(0, weight=1)

        newLabelTitle(
            frame_header,
            text=f"{ENVIRONMENT if ENVIRONMENT == "DEVELOPMENT" else 'Cadastro de Ativos'}",
        ).grid(row=0, column=0, sticky="we")

        newLabelSubtitle(frame_header, text=f"Usuário: {str_user}").grid(  # noqa: F403, F405, E402
            row=1, column=0, sticky="we"
        )

    def frame_body(self):

        self.frame_body = newFrame(self)
        self.frame_body.grid(row=1, column=0, sticky="nsew", padx=10, pady=(10, 5))
        self.frame_body.columnconfigure(0, weight=1)

    def widgets_pre_selecao(self):

        frame_pre_selecao = newLabelFrame(
            self.frame_body, text="Pré Seleção - Tipo Ativo"
        )
        frame_pre_selecao.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 0))

        self.box_tipo_ativo = newCombobox(
            frame_pre_selecao, textvariable=self.tipo_ativo
        )
        self.box_tipo_ativo["values"] = self.lista_tipo_ativos
        self.box_tipo_ativo.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.btn_reset = newButton(
            frame_pre_selecao,
            text="Reset",
            command=self.process_manager.comando_reset,
            width=15,
        )
        self.btn_reset.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=5)

        self.btn_check_dados = newButton(
            frame_pre_selecao,
            text="Check Dados",
            command=self.process_manager.comando_botao_check_dados,
            width=15,
        )
        self.btn_check_dados.grid(row=0, column=2, sticky="w", padx=(10, 0), pady=5)

        self.btn_exec_cadastro = newButton(
            frame_pre_selecao,
            text="Cadastrar",
            width=15,
            command=self.process_manager.comando_cadastrar_ativo,
        )
        self.btn_exec_cadastro.set_disabled()

        self.btn_confirmar_dados = newButton(
            frame_pre_selecao,
            text="Confirmar dados",
            width=15,
            command=self.process_manager.comando_confirmar_dados,
        )
        self.btn_confirmar_dados.set_disabled()

    def widgets_campos_principais(self):

        def call_frames():

            self.frame_ativo = newFrame(frame_opts)
            self.frame_ativo.columnconfigure(0, weight=1)

            self.frame_cod_ativo_btg = newFrame(frame_opts)
            self.frame_cod_ativo_btg.columnconfigure(0, weight=1)

            self.frame_isin = newFrame(frame_opts)
            self.frame_isin.columnconfigure(0, weight=1)

            self.frame_cod_if = newFrame(frame_opts)
            self.frame_cod_if.columnconfigure(0, weight=1)

            self.frame_vne = newFrame(frame_opts)
            self.frame_vne.columnconfigure(0, weight=1)

            self.frame_indexador = newFrame(frame_opts)
            self.frame_indexador.columnconfigure(0, weight=1)

            self.frame_taxa_emissao = newFrame(frame_opts)
            self.frame_taxa_emissao.columnconfigure(0, weight=1)

            self.frame_data_emissao = newFrame(frame_opts)
            self.frame_data_emissao.columnconfigure(0, weight=1)

            self.frame_data_vencimento = newFrame(frame_opts)
            self.frame_data_vencimento.columnconfigure(0, weight=1)

            self.frame_emissor = newFrame(frame_opts)
            self.frame_emissor.columnconfigure(0, weight=1)

        def call_widgets_ativo():

            self.lbl_ativo = newLabelStatus(self.frame_ativo, text="Ativo")
            self.lbl_ativo.grid(row=0, column=0, sticky="w", padx=0, pady=0)
            self.entry_ativo = newEntry(
                self.frame_ativo, textvariable=self.ativo, state="disabled"
            )
            self.entry_ativo.grid(row=1, column=0, sticky="we", padx=0, pady=0)
            self.entry_ativo.set_tooltip(
                msg="Campo obrigarório.\nPara alguns ativos tem preenchimento automático.",
                bootstyle_p=(INFO, INVERSE),  # noqa: F403, F405, E402
            )

        def call_widgets_cod_ativo_btg():

            self.lbl_cod_ativo_btg = newLabelStatus(
                self.frame_cod_ativo_btg, text="Cod. Ativo BTG"
            )
            self.lbl_cod_ativo_btg.grid(row=0, column=0, sticky="w", padx=0, pady=0)
            self.entry_cod_ativo_btg = newEntry(
                self.frame_cod_ativo_btg,
                textvariable=self.cod_ativo_btg,
                state="disabled",
            )
            self.entry_cod_ativo_btg.grid(row=1, column=0, sticky="we", padx=0, pady=0)
            self.entry_cod_ativo_btg.set_tooltip(
                msg=(
                    "Campo permitido vazio.\n"
                    "Para crédito privado, é necessário preenchimento posterior no processo de batimento de carteira."
                ),
                bootstyle_p=(INFO, INVERSE),  # noqa: F403, F405, E402
            )

        def call_widgets_isin():

            self.lbl_isin = newLabelStatus(self.frame_isin, text="ISIN")
            self.lbl_isin.grid(row=0, column=0, sticky="w", padx=0, pady=0)
            self.entry_isin = newEntry(
                self.frame_isin, textvariable=self.isin, state="disabled"
            )
            self.entry_isin.grid(row=1, column=0, sticky="we", padx=0, pady=0)
            self.entry_isin.set_tooltip(
                msg="Campo opcional, mas importante preenchimento.",
                bootstyle_p=(INFO, INVERSE),  # noqa: F403, F405, E402
            )

        def call_widgets_cod_if():

            self.lbl_cod_if = newLabelStatus(self.frame_cod_if, text="Cod. IF")
            self.lbl_cod_if.grid(row=0, column=0, sticky="w", padx=0, pady=0)
            self.entry_cod_if = newEntry(
                self.frame_cod_if, textvariable=self.cod_if, state="disabled"
            )
            self.entry_cod_if.grid(row=1, column=0, sticky="we", padx=0, pady=0)
            self.entry_cod_if.set_tooltip(
                msg="Campo opcional, mas importante preenchimento.",
                bootstyle_p=(INFO, INVERSE),  # noqa: F403, F405, E402
            )

        def call_widgets_vne():

            self.lbl_vne = newLabelStatus(self.frame_vne, text="VNE")
            self.lbl_vne.grid(row=0, column=0, sticky="w", padx=0, pady=0)
            self.entry_vne = newEntry(
                self.frame_vne,
                textvariable=self.vne,
                validate="focus",
                validatecommand=(self.digit_func, "%P"),
                state="disabled",
            )
            self.entry_vne.grid(row=1, column=0, sticky="we", padx=0, pady=0)
            self.entry_vne.set_tooltip(
                msg="Usar '.' como separador decimal.", bootstyle_p=(INFO, INVERSE)  # noqa: F403, F405, E402
            )

        def call_widgets_indexador():

            self.lbl_indexador = newLabelStatus(self.frame_indexador, text="Indexador")
            self.lbl_indexador.grid(row=0, column=0, sticky="w", padx=0, pady=0)
            self.box_indexador = newCombobox(
                self.frame_indexador, textvariable=self.indexador, state="disabled"
            )
            self.box_indexador.grid(row=1, column=0, sticky="we", padx=0, pady=0)
            self.box_indexador["values"] = self.lista_indexadores
            self.box_indexador.set_default()
            self.box_indexador.set_tooltip(
                msg="Se não existir na lista vai abrir caixa de cadastro.",
                bootstyle_p=(INFO, INVERSE),  # noqa: F403, F405, E402
            )

        def call_widgets_taxa_emissao():

            self.lbl_taxa_emissao = newLabelStatus(
                self.frame_taxa_emissao, text="Taxa de Emissão"
            )
            self.lbl_taxa_emissao.grid(row=0, column=0, sticky="w", padx=0, pady=0)
            self.entry_taxa_emissao = newEntry(
                self.frame_taxa_emissao,
                textvariable=self.taxa_emissao,
                validate="focus",
                validatecommand=(self.digit_func, "%P"),
                state="disabled",
            )
            self.entry_taxa_emissao.grid(row=1, column=0, sticky="we", padx=0, pady=0)
            self.entry_taxa_emissao.set_tooltip(
                msg="Usar '.' como separador decimal.", bootstyle_p=(INFO, INVERSE)  # noqa: F403, F405, E402
            )

        def call_widgets_data_emissao():

            self.lbl_data_emissao = newLabelStatus(
                self.frame_data_emissao, text="Data Emissão"
            )
            self.lbl_data_emissao.grid(row=0, column=0, sticky="w", padx=0, pady=0)
            self.entry_data_emissao = newDateEntry(self.frame_data_emissao)
            self.entry_data_emissao.clear_date()
            self.entry_data_emissao.grid(row=1, column=0, sticky="we", padx=0, pady=0)
            self.entry_data_emissao.set_disabled()
            self.entry_data_emissao.set_tooltip(
                msg="Usar padrão: dd/mm/yyyy", bootstyle_p=(INFO, INVERSE)  # noqa: F403, F405, E402
            )

        def call_widgets_data_vencimento():

            self.lbl_data_vencimento = newLabelStatus(
                self.frame_data_vencimento, text="Data Vencimento"
            )
            self.lbl_data_vencimento.grid(row=0, column=0, sticky="w", padx=0, pady=0)
            self.entry_data_vencimento = newDateEntry(self.frame_data_vencimento)
            self.entry_data_vencimento.clear_date()
            self.entry_data_vencimento.grid(
                row=1, column=0, sticky="we", padx=0, pady=0
            )
            self.entry_data_vencimento.set_disabled()
            self.entry_data_vencimento.set_tooltip(
                msg="Usar padrão: dd/mm/yyyy", bootstyle_p=(INFO, INVERSE)  # noqa: F403, F405, E402
            )

        def call_widgets_emissor():

            self.lbl_emissor = newLabelStatus(self.frame_emissor, text="Emissor")
            self.lbl_emissor.grid(row=0, column=0, sticky="w", padx=0, pady=0)
            self.box_emissor = newCombobox(
                self.frame_emissor,
                textvariable=self.emissor,
                postcommand=self.update_box_emissores,
                state="disabled",
            )
            self.box_emissor.grid(row=1, column=0, sticky="we", padx=0, pady=0)
            self.box_emissor.set_default()
            self.box_emissor.set_tooltip(
                msg="Campo obrigarório.\nSe não existir na lista vai abrir caixa de cadastro.",
                bootstyle_p=(INFO, INVERSE),  # noqa: F403, F405, E402
            )

        def call_all_widgets():

            call_frames()
            call_widgets_ativo()
            call_widgets_cod_ativo_btg()
            call_widgets_isin()
            call_widgets_cod_if()
            call_widgets_vne()
            call_widgets_indexador()
            call_widgets_taxa_emissao()
            call_widgets_data_emissao()
            call_widgets_data_vencimento()
            call_widgets_emissor()

        frame_opts = newLabelFrame(self.frame_body, text="Campos Principais")
        frame_opts.grid(row=1, column=0, sticky="nsew", padx=5, pady=(5, 0))
        frame_opts.columnconfigure(0, weight=1)
        frame_opts.columnconfigure(1, weight=1)
        frame_opts.columnconfigure(2, weight=1)
        frame_opts.columnconfigure(3, weight=1)

        call_all_widgets()

    def widgets_posicionamento_principais(self):

        self.frame_ativo.grid(
            row=0, column=0, sticky="nsew", padx=5, pady=5, columnspan=2
        )
        self.frame_emissor.grid(
            row=0, column=2, sticky="nsew", padx=5, pady=5, columnspan=2
        )

        self.frame_cod_ativo_btg.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.frame_cod_if.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        self.frame_indexador.grid(row=1, column=2, sticky="nsew", padx=5, pady=5)
        self.frame_taxa_emissao.grid(row=1, column=3, sticky="nsew", padx=5, pady=5)

        self.frame_isin.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        self.frame_vne.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)
        self.frame_data_emissao.grid(row=2, column=2, sticky="nsew", padx=5, pady=5)
        self.frame_data_vencimento.grid(row=2, column=3, sticky="nsew", padx=5, pady=5)

    def widgets_campos_secundarios(self):

        def call_frames():

            self.frame_data_rentabilidade = newFrame(frame_opts_secondarios)
            self.frame_data_rentabilidade.set_column_weight(0, 1)

            self.frame_cod_bbg = newFrame(frame_opts_secondarios)
            self.frame_cod_bbg.set_column_weight(0, 1)

            self.frame_obs = newFrame(frame_opts_secondarios)
            self.frame_obs.set_column_weight(0, 1)

            self.frame_setor = newFrame(frame_opts_secondarios)
            self.frame_setor.set_column_weight(0, 1)

            self.frame_cnpj = newFrame(frame_opts_secondarios)
            self.frame_cnpj.set_column_weight(0, 1)

            self.frame_gestor = newFrame(frame_opts_secondarios)
            self.frame_gestor.set_column_weight(0, 1)

            self.frame_grupo_economico = newFrame(frame_opts_secondarios)
            self.frame_grupo_economico.set_column_weight(0, 1)

            self.frame_tipo_emissor = newFrame(frame_opts_secondarios)
            self.frame_tipo_emissor.set_column_weight(0, 1)

            self.frame_classe_ativo = newFrame(frame_opts_secondarios)
            self.frame_classe_ativo.set_column_weight(0, 1)

            self.frame_modalidade_enquadramento = newFrame(frame_opts_secondarios)
            self.frame_modalidade_enquadramento.set_column_weight(0, 1)

        def call_widgets_data_rentabilidade():

            self.lbl_data_rentabilidade = newLabelStatus(
                self.frame_data_rentabilidade, text="Data Inicio Rentabilidade"
            )
            self.lbl_data_rentabilidade.grid(
                row=0, column=0, sticky="w", padx=0, pady=0
            )

            self.entry_data_rentabilidade = newDateEntry(self.frame_data_rentabilidade)
            self.entry_data_rentabilidade.clear_date()
            self.entry_data_rentabilidade.grid(
                row=1, column=0, sticky="we", padx=0, pady=0
            )
            self.entry_data_rentabilidade.set_disabled()
            self.entry_data_rentabilidade.set_tooltip(
                msg="Para crédito privado vai ser preenchido = Data Emissão.",
                bootstyle_p=(INFO, INVERSE),  # noqa: F403, F405, E402
            )

        def call_widgets_setor():

            self.lbl_setor = newLabelStatus(self.frame_setor, text="Setor")
            self.lbl_setor.grid(row=0, column=0, sticky="w", padx=0, pady=0)
            self.box_setor = newCombobox(
                self.frame_setor,
                textvariable=self.setor,
                state="disabled",
                postcommand=self.update_box_setores,
            )
            self.box_setor.grid(row=1, column=0, sticky="we", padx=0, pady=0)
            self.box_setor["values"] = self.lista_setores
            self.box_setor.set_default()
            self.box_setor.set_tooltip(
                msg="Se não existir na lista vai abrir caixa de cadastro.",
                bootstyle_p=(INFO, INVERSE),  # noqa: F403, F405, E402
            )

        def call_widgets_gestor():

            self.lbl_gestor = newLabelStatus(self.frame_gestor, text="Gestor")
            self.lbl_gestor.grid(row=0, column=0, sticky="w", padx=0, pady=0)
            self.box_gestor = newCombobox(
                self.frame_gestor,
                textvariable=self.gestor,
                state="disabled",
                postcommand=self.update_box_gestores,
            )
            self.box_gestor.grid(row=1, column=0, sticky="we", padx=0, pady=0)
            self.box_gestor["values"] = self.lista_gestores
            self.box_gestor.set_default()
            self.box_gestor.set_tooltip(
                msg="Se não existir na lista vai abrir caixa de cadastro.",
                bootstyle_p=(INFO, INVERSE),  # noqa: F403, F405, E402
            )

        def call_widgets_cnpj():

            self.lbl_cnpj = newLabelStatus(self.frame_cnpj, text="CNPJ")
            self.lbl_cnpj.grid(row=0, column=0, sticky="w", padx=0, pady=0)
            self.entry_cnpj = newEntry(
                self.frame_cnpj, textvariable=self.cnpj, state="disabled"
            )
            self.entry_cnpj.grid(row=1, column=0, sticky="we", padx=0, pady=0)
            self.entry_cnpj.set_tooltip(
                msg="Apenas números.", bootstyle_p=(INFO, INVERSE)  # noqa: F403, F405, E402
            )

        def call_widgets_cod_bbg():

            self.lbl_cod_bbg = newLabelStatus(self.frame_cod_bbg, text="Cod. BBG")
            self.lbl_cod_bbg.grid(row=0, column=0, sticky="w", padx=0, pady=0)
            self.entry_cod_bbg = newEntry(
                self.frame_cod_bbg, textvariable=self.cod_bbg, state="disabled"
            )
            self.entry_cod_bbg.grid(row=1, column=0, sticky="we", padx=0, pady=0)

        def call_widgets_obs():

            self.lbl_obs = newLabelStatus(self.frame_obs, text="OBS")
            self.lbl_obs.grid(row=0, column=0, sticky="w", padx=0, pady=0)
            self.text_obs = newScrolledText(
                self.frame_obs, font=("consolas", 9), height=3
            )
            self.text_obs.grid(row=1, column=0, sticky="new", padx=0, pady=0)
            self.text_obs.configure(height=5)
            self.text_obs.set_tooltip(
                msg=(
                    "Campo opcional caso queria deixar alguma observação sobre o ativo.\n"
                    "Máximo de 150 caracteres."
                ),
                bootstyle_p=(INFO, INVERSE),  # noqa: F403, F405, E402
            )

        def call_widgets_grupo_economico():

            self.lbl_grupo_economico = newLabelStatus(
                self.frame_grupo_economico, text="Grupo Econômico"
            )
            self.lbl_grupo_economico.grid(row=0, column=0, sticky="w", padx=0, pady=0)
            self.entry_grupo_economico = newEntry(
                self.frame_grupo_economico,
                textvariable=self.grupo_economico,
                state="disabled",
            )
            self.entry_grupo_economico.grid(
                row=1, column=0, sticky="we", padx=0, pady=0
            )
            self.entry_grupo_economico.set_tooltip(
                msg="Vai ser preenchido de acordo com o emissor.",
                bootstyle_p=(INFO, INVERSE),  # noqa: F403, F405, E402
            )

        def call_widgets_tipo_emissor():

            self.lbl_tipo_emissor = newLabelStatus(
                self.frame_tipo_emissor, text="Tipo Emissor"
            )
            self.lbl_tipo_emissor.grid(row=0, column=0, sticky="w", padx=0, pady=0)
            self.entry_tipo_emissor = newEntry(
                self.frame_tipo_emissor,
                textvariable=self.tipo_emissor,
                state="disabled",
            )
            self.entry_tipo_emissor.grid(row=1, column=0, sticky="we", padx=0, pady=0)
            self.entry_tipo_emissor.set_tooltip(
                msg="Vai ser preenchido de acordo com o emissor.",
                bootstyle_p=(INFO, INVERSE),  # noqa: F403, F405, E402
            )

        def call_widgets_classe_ativo():

            self.lbl_classe_ativo = newLabelStatus(
                self.frame_classe_ativo, text="Classe Ativo"
            )
            self.lbl_classe_ativo.grid(row=0, column=0, sticky="w", padx=0, pady=0)
            self.box_classe_ativo = newCombobox(
                self.frame_classe_ativo,
                textvariable=self.classe_ativo,
                state="disabled",
                postcommand=self.update_box_classe_ativo,
            )
            self.box_classe_ativo.grid(row=1, column=0, sticky="we", padx=0, pady=0)
            self.box_classe_ativo["values"] = self.lista_classe_ativo
            self.box_classe_ativo.set_default()
            self.box_classe_ativo.set_tooltip(
                msg="Se não existir na lista, selecionar 'Cadastrar Novo'.",
                bootstyle_p=(INFO, INVERSE),  # noqa: F403, F405, E402
            )

        def call_widgets_modalidade_enquadramento():

            self.lbl_modalidade_enquadramento = newLabelStatus(
                self.frame_modalidade_enquadramento, text="Modalidade Enquadramento"
            )
            self.lbl_modalidade_enquadramento.grid(
                row=0, column=0, sticky="w", padx=0, pady=0
            )
            self.box_modalidade_enquadramento = newCombobox(
                self.frame_modalidade_enquadramento,
                textvariable=self.modalidade_enquadramento,
                state="disabled",
                postcommand=self.update_box_modalidade_enquadramento,
            )
            self.box_modalidade_enquadramento.grid(
                row=1, column=0, sticky="we", padx=0, pady=0
            )
            self.box_modalidade_enquadramento["values"] = (
                self.lista_modalidade_enquadramento
            )
            self.box_modalidade_enquadramento.set_default()
            self.box_modalidade_enquadramento.set_tooltip(
                msg="Se não existir na lista, selecionar 'Cadastrar Novo'.",
                bootstyle_p=(INFO, INVERSE),  # noqa: F403, F405, E402
            )

        def call_all_widgets():

            call_frames()

            call_widgets_data_rentabilidade()
            call_widgets_setor()
            call_widgets_gestor()
            call_widgets_cnpj()
            call_widgets_cod_bbg()
            call_widgets_obs()
            call_widgets_grupo_economico()
            call_widgets_tipo_emissor()
            call_widgets_classe_ativo()
            call_widgets_modalidade_enquadramento()

        frame_opts_secondarios = newLabelFrame(
            self.frame_body, text="Campos Secundários"
        )
        frame_opts_secondarios.grid(row=2, column=0, sticky="nsew", padx=5, pady=(5, 0))
        frame_opts_secondarios.columnconfigure(0, weight=1)
        frame_opts_secondarios.columnconfigure(1, weight=1)
        frame_opts_secondarios.columnconfigure(2, weight=1)
        frame_opts_secondarios.columnconfigure(3, weight=1)

        call_all_widgets()

    def widgets_posicionamento_secundarios(self):

        self.frame_data_rentabilidade.grid(
            row=0, column=0, sticky="nsew", padx=5, pady=5
        )
        self.frame_grupo_economico.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.frame_tipo_emissor.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        self.frame_modalidade_enquadramento.grid(
            row=0, column=3, sticky="nsew", padx=5, pady=5
        )

        self.frame_classe_ativo.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.frame_setor.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        self.frame_gestor.grid(row=1, column=2, sticky="nsew", padx=5, pady=5)
        self.frame_cnpj.grid(row=1, column=3, sticky="nsew", padx=5, pady=5)

        self.frame_cod_bbg.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

        self.frame_obs.grid(row=3, column=0, sticky="new", padx=5, pady=5, columnspan=4)

    def resumo_cadastro(self):

        frame_resumo = newLabelFrame(self.frame_body, text="Info cadastro")
        frame_resumo.grid(row=3, column=0, sticky="nsew", padx=5, pady=(5, 0))
        frame_resumo.columnconfigure(0, weight=1)
        frame_resumo.rowconfigure(0, weight=1)

        self.text_box_resumo = newScrolledText(
            frame_resumo, font=("consolas", 12), height=21
        )
        self.text_box_resumo.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)


class CadastroFluxoFinanceiro(Toplevel):

    def __init__(
        self,
        app=None,
        janela_init=None,
        manager_sql=None,
        funcoes_pytools=None,
        *args,
        **kwargs,
    ):

        super().__init__(*args, **kwargs)

        self.title("BackOffice Systems")
        self.geometry("834x550")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        if manager_sql is None:
            self.manager_sql = SQL_Manager()
        else:
            self.manager_sql = manager_sql

        if funcoes_pytools is None:
            self.funcoes_pytools = FuncoesPyTools(self.manager_sql)
        else:
            self.funcoes_pytools = funcoes_pytools

        self.lista_tipo_ativos = ["CCB", "CDB", "LF", "LFSC", "LFSN", "LFSN-PRE"]

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.app = app
        self.janela_init = janela_init

        self.process_manager = ProcessManagerFLuxoFinanceiro(
            app=self, manager_sql=self.manager_sql, funcoes_pytools=self.funcoes_pytools
        )

        self.header()
        self.body()
        self.variaveis_controle()
        self.widgets_head()
        self.widgets_select_tipo_ativo()
        self.widgets_select_ativo()
        self.frame_config_fluxo()
        self.widgets_config_juros()
        self.widgets_config_amortizacao()
        self.config_widgets()

        self.process_manager.comando_lista_ativos_new()

    def on_close(self):
        self.destroy()
        self.janela_init.lift()

    def header(self):

        frame_header = newFrame(self)
        frame_header.grid(row=0, column=0, sticky="new", padx=10, pady=10)
        frame_header.columnconfigure(0, weight=1)

        newLabelTitle(
            frame_header,
            text=f"{ENVIRONMENT if ENVIRONMENT == "DEVELOPMENT" else 'Cadastro de Fluxo Financeiro'}",
        ).grid(row=0, column=0, sticky="we")

        newLabelSubtitle(frame_header, text=f"Versão: {VERSION_APP}").grid(
            row=1, column=0, sticky="we"
        )

    def body(self):

        self.frame_body = newFrame(self)
        self.frame_body.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 5))
        self.frame_body.columnconfigure(0, weight=1)

    def variaveis_controle(self):

        self.data_rentabilidade = StringVar()
        self.data_vencimento = StringVar()
        self.vne = StringVar()
        self.taxa_emissao = StringVar()
        self.data_emissao = StringVar()

        self.fluxo_juros = StringVar()
        self.fluxo_amortizacao = StringVar()

        self.tipo_ativo = StringVar()
        self.tipo_ativo.trace_add("write", self.process_manager.comando_tipo_ativo)

        self.edit_new = StringVar(value="new")
        self.edit_new.trace_add("write", self.process_manager.comando_edit_new)

        self.ativo = StringVar()

    def widgets_head(self):

        frame_head = newLabelFrame(self.frame_body, text="Controle")
        frame_head.grid(row=0, column=0, sticky="we", padx=5, pady=(5, 0))

        newRadioButton(
            frame_head, text="Novo fluxo", value="new", variable=self.edit_new
        ).grid(row=0, column=0, sticky="w", padx=(10, 10), pady=10)

        newRadioButton(
            frame_head,
            text="Editar fluxo",
            value="edit",
            variable=self.edit_new,
            state="disabled",
        ).grid(row=0, column=1, sticky="w", padx=(0, 10), pady=10)

        self.btn_reset = newButton(
            frame_head,
            width=15,
            text="Reset",
            command=self.process_manager.comando_reset,
        )
        self.btn_reset.grid(row=0, column=2, sticky="e", padx=(30, 10), pady=10)

        self.btn_cadastrar = newButton(
            frame_head,
            width=15,
            text="Cadastrar",
            command=self.process_manager.comando_boletar,
        )
        self.btn_cadastrar.grid(row=0, column=3, sticky="e", padx=(0, 10), pady=10)

    def widgets_select_tipo_ativo(self):

        frame_tipo_ativo = newLabelFrame(self.frame_body, text="Tipo Ativo")
        frame_tipo_ativo.grid(row=1, column=0, sticky="we", padx=5, pady=(5, 0))

        self.tipo_ativo_ccb = newRadioButton(
            frame_tipo_ativo, text="CCB", value="CCB", variable=self.tipo_ativo
        )
        self.tipo_ativo_ccb.grid(row=0, column=0, sticky="w", padx=(10, 10), pady=10)
        self.tipo_ativo_ccb.set_disabled()

        self.tipo_ativo_cdb = newRadioButton(
            frame_tipo_ativo, text="CDB", value="CDB", variable=self.tipo_ativo
        )
        self.tipo_ativo_cdb.grid(row=0, column=1, sticky="w", padx=(0, 10), pady=10)
        self.tipo_ativo_cdb.set_disabled()

        self.tipo_ativo_lf = newRadioButton(
            frame_tipo_ativo, text="LF", value="LF", variable=self.tipo_ativo
        )
        self.tipo_ativo_lf.grid(row=0, column=2, sticky="w", padx=(0, 10), pady=10)
        self.tipo_ativo_lf.set_disabled()

        self.tipo_ativo_lfsc = newRadioButton(
            frame_tipo_ativo, text="LFSC", value="LFSC", variable=self.tipo_ativo
        )
        self.tipo_ativo_lfsc.grid(row=0, column=3, sticky="w", padx=(0, 10), pady=10)
        self.tipo_ativo_lfsc.set_disabled()

        self.tipo_ativo_lfsn = newRadioButton(
            frame_tipo_ativo, text="LFSN", value="LFSN", variable=self.tipo_ativo
        )
        self.tipo_ativo_lfsn.grid(row=0, column=4, sticky="w", padx=(0, 10), pady=10)
        self.tipo_ativo_lfsn.set_disabled()

        self.tipo_ativo_lfsn_pre = newRadioButton(
            frame_tipo_ativo,
            text="PFSN-PRE",
            value="PFSN-PRE",
            variable=self.tipo_ativo,
        )
        self.tipo_ativo_lfsn_pre.grid(
            row=0, column=5, sticky="w", padx=(0, 10), pady=10
        )
        self.tipo_ativo_lfsn_pre.set_disabled()

    def widgets_select_ativo(self):

        frame_ativo = newLabelFrame(self.frame_body, text="Dados Ativo")
        frame_ativo.grid(row=2, column=0, sticky="nsew", padx=5, pady=(5, 0))
        frame_ativo.columnconfigure(0, weight=1)
        frame_ativo.columnconfigure(1, weight=1)
        frame_ativo.columnconfigure(2, weight=1)
        frame_ativo.columnconfigure(3, weight=1)

        newLabelStatus(frame_ativo, text="Ativo").grid(
            row=0, column=0, sticky="w", padx=(10, 10), pady=(10, 0)
        )

        self.box_ativo = newCombobox(frame_ativo, textvariable=self.ativo)
        self.box_ativo.grid(
            row=1, column=0, sticky="we", padx=(10, 10), pady=(0, 0), columnspan=2
        )

        newLabelStatus(frame_ativo, text="Taxa Emissão").grid(
            row=0, column=2, sticky="w", padx=(5, 10), pady=(10, 0)
        )

        self.entry_taxa_emissao = newEntry(
            frame_ativo, textvariable=self.taxa_emissao, takefocus=False
        )
        self.entry_taxa_emissao.grid(
            row=1, column=2, sticky="we", padx=(0, 10), pady=(0, 0)
        )

        newLabelStatus(frame_ativo, text="VNE").grid(
            row=0, column=3, sticky="w", padx=(0, 5), pady=(10, 0)
        )

        self.entry_vne = newEntry(frame_ativo, textvariable=self.vne, takefocus=False)
        self.entry_vne.grid(row=1, column=3, sticky="we", padx=(0, 10), pady=(0, 0))

        newLabelStatus(frame_ativo, text="Data Emissão").grid(
            row=2, column=0, sticky="w", padx=(10, 5), pady=(10, 0)
        )

        self.entry_data_emissao = newEntry(
            frame_ativo, textvariable=self.data_emissao, takefocus=False
        )
        self.entry_data_emissao.grid(
            row=3, column=0, sticky="we", padx=(10, 10), pady=(0, 10)
        )

        newLabelStatus(frame_ativo, text="Data Inicio Rent.").grid(
            row=2, column=1, sticky="w", padx=(0, 5), pady=(10, 0)
        )

        self.entry_data_rentabilidade = newEntry(
            frame_ativo, textvariable=self.data_rentabilidade, takefocus=False
        )
        self.entry_data_rentabilidade.grid(
            row=3, column=1, sticky="we", padx=(0, 10), pady=(0, 10)
        )

        newLabelStatus(frame_ativo, text="Data Vencimento").grid(
            row=2, column=2, sticky="w", padx=(0, 5), pady=(10, 0)
        )

        self.entry_data_vencimento = newEntry(
            frame_ativo, textvariable=self.data_vencimento, takefocus=False
        )
        self.entry_data_vencimento.grid(
            row=3, column=2, sticky="we", padx=(0, 10), pady=(0, 10)
        )

    def frame_config_fluxo(self):

        self.frame_pre_config = newFrame(self.frame_body)
        self.frame_pre_config.grid(row=3, column=0, sticky="nsew", padx=5, pady=(5, 0))
        self.frame_pre_config.columnconfigure(0, weight=1)
        self.frame_pre_config.columnconfigure(1, weight=1)

    def widgets_config_juros(self):

        frame_config_juros = newLabelFrame(self.frame_pre_config, text="Fluxo Juros")
        frame_config_juros.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        newRadioButton(
            frame_config_juros, text="Bullet", value="bullet", variable=self.fluxo_juros
        ).grid(row=0, column=0, sticky="w", padx=10, pady=10)

        newRadioButton(
            frame_config_juros, text="Mensal", value="mensal", variable=self.fluxo_juros
        ).grid(row=0, column=1, sticky="w", padx=(0, 10), pady=10)

        newRadioButton(
            frame_config_juros,
            text="Semestral",
            value="semestral",
            variable=self.fluxo_juros,
        ).grid(row=0, column=2, sticky="w", padx=(0, 10), pady=10)

        newRadioButton(
            frame_config_juros, text="Anual", value="anual", variable=self.fluxo_juros
        ).grid(row=0, column=3, sticky="w", padx=(0, 10), pady=10)

    def widgets_config_amortizacao(self):

        frame_config_amortizacao = newLabelFrame(
            self.frame_pre_config, text="Fluxo Amortização"
        )
        frame_config_amortizacao.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        newRadioButton(
            frame_config_amortizacao,
            text="Bullet",
            value="bullet",
            variable=self.fluxo_amortizacao,
        ).grid(row=0, column=0, sticky="w", padx=10, pady=10)

        newRadioButton(
            frame_config_amortizacao,
            text="Mensal",
            value="mensal",
            variable=self.fluxo_amortizacao,
        ).grid(row=0, column=1, sticky="w", padx=(0, 10), pady=10)

        newRadioButton(
            frame_config_amortizacao,
            text="Semestral",
            value="semestral",
            variable=self.fluxo_amortizacao,
        ).grid(row=0, column=2, sticky="w", padx=(0, 10), pady=10)

        newRadioButton(
            frame_config_amortizacao,
            text="Anual",
            value="anual",
            variable=self.fluxo_amortizacao,
        ).grid(row=0, column=3, sticky="w", padx=(0, 10), pady=10)

    def config_widgets(self):

        self.ativo.trace_add("write", self.process_manager.comando_ativo)

        self.entry_taxa_emissao.bind(
            "<FocusOut>", self.process_manager.tratamento_entry
        )
        self.entry_vne.bind("<FocusOut>", self.process_manager.tratamento_entry)
        self.entry_data_emissao.bind(
            "<FocusOut>", self.process_manager.tratamento_entry
        )
        self.entry_data_rentabilidade.bind(
            "<FocusOut>", self.process_manager.tratamento_entry
        )
        self.entry_data_vencimento.bind(
            "<FocusOut>", self.process_manager.tratamento_entry
        )


class ProcessManagerFLuxoFinanceiro:

    def __init__(self, app=None, manager_sql=None, funcoes_pytools=None):

        self.app = app
        self.manager_sql = manager_sql
        self.funcoes_pytools = funcoes_pytools

        self.str_lista_tipo_ativos = "','".join(self.app.lista_tipo_ativos)
        self.comando_update_dics()

        if ENVIRONMENT == "DEVELOPMENT":
            self.tb_fluxo = "TB_FLUXO_PAGAMENTO_ATIVOS_TESTE"
        else:
            self.tb_fluxo = "TB_FLUXO_PAGAMENTO_ATIVOS"

    def comando_update_dics(self):

        self.dict_tipo_ativo = (
            self.manager_sql.select_dataframe(
                f"SELECT DISTINCT ATIVO, TIPO_ATIVO FROM TB_CADASTRO_ATIVOS "
                f"WHERE TIPO_ATIVO IN ('{self.str_lista_tipo_ativos}')"
            )
            .set_index("ATIVO")["TIPO_ATIVO"]
            .to_dict()
        )

        self.dict_ativo = (
            self.manager_sql.select_dataframe(
                f"SELECT DISTINCT ATIVO, TIPO_ATIVO, TAXA_EMISSAO, DATA_EMISSAO, DATA_VENCIMENTO, DATA_INICIO_RENTABILDIADE, VNE "
                f"FROM TB_CADASTRO_ATIVOS "
                f"WHERE TIPO_ATIVO IN ('{self.str_lista_tipo_ativos}')"
            )
            .set_index("ATIVO")
            .to_dict(orient="index")
        )

    def comando_tipo_ativo(self, *args):
        _ = args

        self.lista_ativos = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT ATIVO FROM TB_CADASTRO_ATIVOS WHERE TIPO_ATIVO = '{self.app.tipo_ativo.get()}'"
        )["ATIVO"].tolist()

        self.app.box_ativo["values"] = self.lista_ativos

    def tratamento_entry(self, *args):
        _ = args

        if self.app.ativo != "":
            self.comando_ativo()

    def comando_ativo(self, *args):
        _ = args

        try:
            self.app.taxa_emissao.set(
                "Sem cadastro"
                if pd.isna(self.dict_ativo[self.app.ativo.get()]["TAXA_EMISSAO"])
                else self.dict_ativo[self.app.ativo.get()]["TAXA_EMISSAO"]
            )

            self.app.vne.set(
                "Sem cadastro"
                if pd.isna(self.dict_ativo[self.app.ativo.get()]["VNE"])
                else self.dict_ativo[self.app.ativo.get()]["VNE"]
            )

            self.app.data_emissao.set(
                "Sem cadastro"
                if pd.isna(self.dict_ativo[self.app.ativo.get()]["DATA_EMISSAO"])
                else self.dict_ativo[self.app.ativo.get()]["DATA_EMISSAO"]
            )

            self.app.data_rentabilidade.set(
                "Sem cadastro"
                if pd.isna(
                    self.dict_ativo[self.app.ativo.get()]["DATA_INICIO_RENTABILDIADE"]
                )
                else self.dict_ativo[self.app.ativo.get()]["DATA_INICIO_RENTABILDIADE"]
            )

            self.app.data_vencimento.set(
                "Sem cadastro"
                if pd.isna(self.dict_ativo[self.app.ativo.get()]["DATA_VENCIMENTO"])
                else self.dict_ativo[self.app.ativo.get()]["DATA_VENCIMENTO"]
            )

        except KeyError:
            self.app.taxa_emissao.set("")
            self.app.vne.set("")
            self.app.data_emissao.set("")
            self.app.data_rentabilidade.set("")
            self.app.data_vencimento.set("")

    def comando_lista_ativos_new(self):

        lista_ativos = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT ATIVO FROM TB_CADASTRO_ATIVOS WHERE TIPO_ATIVO IN ('{self.str_lista_tipo_ativos}')"
        )["ATIVO"].tolist()

        lista_ativos_fluxo = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT ATIVO FROM {self.tb_fluxo} "
            f"WHERE TIPO_ATIVO IN ('{self.str_lista_tipo_ativos}')"
        )["ATIVO"].tolist()

        lista_ativos_new = list((set(lista_ativos) - set(lista_ativos_fluxo)))

        lista_ativos_new.sort()

        self.app.box_ativo["values"] = lista_ativos_new

    def comando_edit_new(self, *args):
        _ = args

        if self.app.edit_new.get() == "edit":
            self.app.tipo_ativo_ccb.set_enabled()
            self.app.tipo_ativo_cdb.set_enabled()
            self.app.tipo_ativo_lf.set_enabled()
            self.app.tipo_ativo_lfsc.set_enabled()
            self.app.tipo_ativo_lfsn.set_enabled()
            self.app.tipo_ativo_lfsn_pre.set_enabled()
        elif self.app.edit_new.get() == "new":
            self.app.tipo_ativo_ccb.set_disabled()
            self.app.tipo_ativo_cdb.set_disabled()
            self.app.tipo_ativo_lf.set_disabled()
            self.app.tipo_ativo_lfsc.set_disabled()
            self.app.tipo_ativo_lfsn.set_disabled()
            self.app.tipo_ativo_lfsn_pre.set_disabled()
            self.comando_lista_ativos_new()

    def comando_reset(self):

        self.app.ativo.set("")
        self.app.btn_cadastrar.set_enabled()
        self.app.fluxo_juros.set("")
        self.app.fluxo_amortizacao.set("")
        self.app.edit_new.set("new")

        self.app.box_ativo.set_enabled()
        self.app.entry_taxa_emissao.set_enabled()
        self.app.entry_vne.set_enabled()
        self.app.entry_data_emissao.set_enabled()
        self.app.entry_data_rentabilidade.set_enabled()
        self.app.entry_data_vencimento.set_enabled()

    def comando_travar_widgets(self):

        self.app.btn_cadastrar.set_disabled()

        self.app.box_ativo.set_disabled()
        self.app.entry_taxa_emissao.set_disabled()
        self.app.entry_vne.set_disabled()
        self.app.entry_data_emissao.set_disabled()
        self.app.entry_data_rentabilidade.set_disabled()
        self.app.entry_data_vencimento.set_disabled()

    def comando_boletar(self):

        lista_checks_cadastro = [
            self.app.taxa_emissao.get(),
            self.app.vne.get(),
            self.app.data_emissao.get(),
            self.app.data_rentabilidade.get(),
            self.app.data_vencimento.get(),
        ]

        lista_checks_fluxo = [
            self.app.fluxo_juros.get(),
            self.app.fluxo_amortizacao.get(),
        ]

        if self.app.ativo.get() == "":
            Messagebox.show_warning(
                title="Aviso", message="Campo ativo não preenchido!"
            )
        else:
            if self.app.edit_new.get() == "new":
                if "Sem cadastro" in lista_checks_cadastro:
                    Messagebox.show_warning(
                        title="Aviso", message="Ativo sem cadastro completo!"
                    )
                else:
                    if "" in lista_checks_fluxo:
                        Messagebox.show_warning(
                            title="Aviso",
                            message="Campos de fluxo devem ser selecionados!",
                        )
                    elif (
                        self.app.fluxo_juros.get() != "bullet" or self.app.fluxo_amortizacao.get() != "bullet"
                    ):
                        Messagebox.show_warning(
                            title="Aviso",
                            message="Apenas fluxos bullet disponíveis até o momento.",
                        )
                    else:
                        confirma = Messagebox.okcancel(
                            title="Confirmação cadastro novo fluxo",
                            message=f"Tipo Ativo: {self.dict_ativo[self.app.ativo.get()]['TIPO_ATIVO']}\n"
                            f"Ativo: {self.app.ativo.get()}\n"
                            f"Juros: {self.app.fluxo_juros.get()}\n"
                            f"Amortização: {self.app.fluxo_amortizacao.get()}\n",
                        )
                        if confirma == "OK":
                            Messagebox.show_info(
                                title="Aviso", message="Bolertagem executada!"
                            )
                            self.comando_travar_widgets()
                            self.comando_cadastro_new_juros()
                            self.comando_cadastro_new_amortizacao()
                            self.app.lift()

            elif self.app.edit_new.get() == "edit":
                Messagebox.show_warning(
                    title="Aviso", message="Edição de fluxo ainda em desenvolvimento."
                )

    def comando_cadastro_new_juros(self):

        if self.app.edit_new.get() == "new":

            tipo_ativo = self.dict_ativo[self.app.ativo.get()]["TIPO_ATIVO"]
            vne = float(self.app.vne.get())
            data_vencimento = datetime.strptime(
                self.app.data_vencimento.get(), "%Y-%m-%d"
            )
            taxa_emissao = float(self.app.taxa_emissao.get())

            if self.app.fluxo_juros.get() == "bullet":
                data = {
                    "TIPO_ATIVO": [tipo_ativo],
                    "ATIVO": [self.app.ativo.get()],
                    "DATA_EVENTO": [data_vencimento],
                    "DATA_LIQUIDACAO": [data_vencimento],
                    "EVENTO": ["Pagamento de juros"],
                    "PERCENTUAL": [taxa_emissao],
                    "VALOR_PAGO": [None],
                    "VNA": [vne],
                }
                df_to_upload = pd.DataFrame(data)
                self.manager_sql.insert_dataframe(df_to_upload, self.tb_fluxo)

    def comando_cadastro_new_amortizacao(self):

        if self.app.edit_new.get() == "new":

            tipo_ativo = self.dict_ativo[self.app.ativo.get()]["TIPO_ATIVO"]
            vne = float(self.app.vne.get())
            data_vencimento = datetime.strptime(
                self.app.data_vencimento.get(), "%Y-%m-%d"
            )

            if self.app.fluxo_amortizacao.get() == "bullet":
                data = {
                    "TIPO_ATIVO": [tipo_ativo],
                    "ATIVO": [self.app.ativo.get()],
                    "DATA_EVENTO": [data_vencimento],
                    "DATA_LIQUIDACAO": [data_vencimento],
                    "EVENTO": ["Amortizacao"],
                    "PERCENTUAL": [100],
                    "VALOR_PAGO": [None],
                    "VNA": [vne],
                }
                df_to_upload = pd.DataFrame(data)
                self.manager_sql.insert_dataframe(df_to_upload, self.tb_fluxo)


class RegistroCodBTG(Toplevel):

    def __init__(
        self,
        app=None,
        janela_init=None,
        manager_sql=None,
        funcoes_pytools=None,
        *args,
        **kwargs,
    ):

        super().__init__(*args, **kwargs)

        self.title("BackOffice Systems")
        self.geometry("380x315")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        if manager_sql is None:
            self.manager_sql = SQL_Manager()
        else:
            self.manager_sql = manager_sql

        if funcoes_pytools is None:
            self.funcoes_pytools = FuncoesPyTools(self.manager_sql)
        else:
            self.funcoes_pytools = funcoes_pytools

        self.lista_tipo_ativos = [
            "CCB",
            "CDB",
            "Debênture",
            "FIDC",
            "LF",
            "LFSC",
            "LFSN",
            "LFSN-PRE",
        ]
        self.str_lista_tipo_ativos = "','".join(self.lista_tipo_ativos)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.app = app
        self.janela_init = janela_init

        self.tb = (
            "TB_CADASTRO_ATIVOS"
            if ENVIRONMENT != "DEVELOPMENT"
            else "TB_CADASTRO_ATIVOS_TESTE"
        )

        self.variaveis_controle()

        self.process_manager = ProcessManagerRegistroBTG(
            app=self, manager_sql=self.manager_sql, funcoes_pytools=self.funcoes_pytools
        )

        self.header()
        self.body()
        self.frames_body()

        self.frames_widgets()
        self.widgets()
        self.grid_frames_widgets()

        self.update_ativos()

    def on_close(self):
        self.destroy()
        self.janela_init.lift()

    def update_ativos(self):

        lista_ativos = self.manager_sql.select_dataframe(
            f"SELECT ATIVO FROM {self.tb} "
            f"WHERE COD_ATIVO_BTG = 'Cadastrar' AND TIPO_ATIVO IN ('{self.str_lista_tipo_ativos}')"
        )["ATIVO"].tolist()

        self.entry_ativo["values"] = lista_ativos

    def variaveis_controle(self):

        def controle_entry_ativo(*args):
            _ = args

            if self.ativo.get() == "":
                self.cod_btg.set("")
                self.entry_cod_btg.set_disabled()
            else:
                self.entry_cod_btg.set_enabled()
                self.cod_btg.set("Preencher")

        self.ativo = StringVar()
        self.ativo.trace_add("write", controle_entry_ativo)

        self.cod_btg = StringVar()

    def bind_cod_btg(self, event):
        _ = event
        if self.cod_btg.get() == "Preencher":
            self.cod_btg.set("")

    def header(self):

        frame_header = newFrame(self)
        frame_header.grid(row=0, column=0, sticky="new", padx=10, pady=10)
        frame_header.columnconfigure(0, weight=1)

        newLabelTitle(
            frame_header,
            text=f"{ENVIRONMENT if ENVIRONMENT == "DEVELOPMENT" else 'Registro Cod. BTG'}",
        ).grid(row=0, column=0, sticky="we")

        newLabelSubtitle(frame_header, text=f"Versão: {VERSION_APP}").grid(
            row=1, column=0, sticky="we"
        )

    def body(self):

        self.frame_body = newFrame(self)
        self.frame_body.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 5))
        self.frame_body.columnconfigure(0, weight=1)

    def frames_body(self):

        self.frame_botoes = newFrame(self.frame_body)
        self.frame_botoes.grid(row=0, column=0, sticky="we", padx=10, pady=(10, 0))

        self.frame_controle = newLabelFrame(self.frame_body, text="Dados Ativo")
        self.frame_controle.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.frame_controle.columnconfigure(0, weight=1)

    def frames_widgets(self):

        self.frame_ativo = newFrame(self.frame_controle)
        self.frame_ativo.columnconfigure(0, weight=1)

        self.frame_cod_btg = newFrame(self.frame_controle)
        self.frame_cod_btg.columnconfigure(0, weight=1)

    def widgets(self):

        newLabelStatus(self.frame_ativo, text="Ativo").grid(row=0, column=0, sticky="w")
        self.entry_ativo = newCombobox(self.frame_ativo, textvariable=self.ativo)
        self.entry_ativo.grid(row=1, column=0, sticky="we")

        newLabelStatus(self.frame_cod_btg, text="Cod. BTG").grid(
            row=0, column=0, sticky="w"
        )
        self.entry_cod_btg = newEntry(
            self.frame_cod_btg, textvariable=self.cod_btg, state="disabled"
        )
        self.entry_cod_btg.grid(row=1, column=0, sticky="we")
        self.entry_cod_btg.bind("<FocusIn>", self.bind_cod_btg)

        self.btn_reset = newButton(
            self.frame_botoes,
            text="Reset",
            width=15,
            command=self.process_manager.comando_reset,
        )
        self.btn_reset.grid(row=0, column=0, sticky="w", pady=10, padx=10)

        self.btn_cadastrar = newButton(
            self.frame_botoes,
            text="Cadastrar",
            width=15,
            command=self.process_manager.comando_cadastrar,
        )
        self.btn_cadastrar.grid(row=0, column=1, sticky="w")

    def grid_frames_widgets(self):

        self.frame_ativo.grid(row=0, column=0, sticky="we", padx=10, pady=(10, 0))
        self.frame_cod_btg.grid(row=1, column=0, sticky="we", padx=10, pady=10)


class ProcessManagerRegistroBTG:

    def __init__(self, app=None, manager_sql=None, funcoes_pytools=None):

        if manager_sql is None:
            self.manager_sql = SQL_Manager()
        else:
            self.manager_sql = manager_sql

        if funcoes_pytools is None:
            self.funcoes_pytools = FuncoesPyTools(self.manager_sql)
        else:
            self.funcoes_pytools = funcoes_pytools

        self.app = app

    def comando_cadastrar(self):

        if self.app.ativo.get() == "":
            Messagebox.show_warning(title="Aviso", message="Sem ativo selecionado.")
        elif self.app.cod_btg.get() == "Preencher":
            Messagebox.show_warning(title="Aviso", message="Preencher campo Cod. BTG.")
        else:
            if self.manager_sql.check_if_data_exists(
                f"SELECT COD_ATIVO_BTG FROM {self.app.tb} WHERE COD_ATIVO_BTG = '{self.app.cod_btg.get()}'"
            ):
                self.app.cod_btg.set("")
                Messagebox.show_warning(
                    title="Aviso", message="Cod. BTG já cadastrado em outro ativo."
                )
            else:
                confirma = Messagebox.okcancel(
                    title="Confirmação cadastro Cod. BTG",
                    message=f"Ativo: {self.app.ativo.get()}\n"
                    f"Cod. BTG: {self.app.cod_btg.get()}\n",
                )

                if confirma == "OK":
                    self.app.entry_ativo.set_disabled()
                    self.app.entry_cod_btg.set_disabled()
                    self.manager_sql.update_table(
                        table_name=self.app.tb,
                        new_value=f"COD_ATIVO_BTG = '{self.app.cod_btg.get()}'",
                        condition=f"ATIVO = '{self.app.ativo.get()}' AND COD_ATIVO_BTG = 'Cadastrar'",
                    )
                    self.app.lift()
                else:
                    Messagebox.show_warning(
                        title="Aviso", message="Cadastro cancelado."
                    )
                    self.app.lift()

    def comando_reset(self):

        self.app.ativo.set("")
        self.app.cod_btg.set("")
        self.app.entry_ativo.set_enabled()
        self.app.entry_cod_btg.set_disabled()
        self.app.update_ativos()


if __name__ == "__main__":
    app = TelaCadastro()
