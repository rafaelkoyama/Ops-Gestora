from __init__ import *

VERSION_APP = "1.1.0"
VERSION_REFDATE = "2024-07-10"
ENVIRONMENT = os.getenv("ENVIRONMENT")
SCRIPT_NAME = os.path.basename(__file__)

if ENVIRONMENT == "DEVELOPMENT":
    print(f"{SCRIPT_NAME.upper()} - {ENVIRONMENT} - {VERSION_APP} - {VERSION_REFDATE}")

#-----------------------------------------------------------------------

from datetime import date, datetime
from xml.etree import ElementTree as ET

import numpy as np
import pandas as pd
from db_helper import SQL_Manager
from my_logger import Logger
from py_tools import FuncoesPyTools

#-----------------------------------------------------------------------

class UploadArquivosXML:

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
            log_message=f"UploadArquivosXML - {VERSION_APP} - {ENVIRONMENT} - instanciado",
            script_original=SCRIPT_NAME)

        self.refdate = None

        self.list_funds = [
            "CRYSTAL FIC FIM CP",
            "STRIX D1 FIC FIRF",
            "STRIX YIELD FC FIRF",
            "STRIX YIELD MASTER F",
            "STRIX FIA",
            "STRIX INFRA FICFIRF",
            "STRIX KINEA INFRA",
        ]

        self.dict_tit_pub = {
            "210100": "LFT",
            "760199": "NTN-B",
            "100000": "LTN",
            "950199": "NTN-F",
        }

        self.dict_suporte_xml = {
            "FIC DE FIM CP CRYSTAL IE": "CRYSTAL FIC FIM CP",
            "STRIX D1 FIC FIRF CP": "STRIX D1 FIC FIRF",
            "STRIX YIELD FIC FIRF CP": "STRIX YIELD FC FIRF",
            "STRIX YIELD MASTER FIRF CP": "STRIX YIELD MASTER F",
            "STRIX FIA": "STRIX FIA",
            "STRIX INFRA FIC FDO INC INV INFR RF": "STRIX INFRA FICFIRF",
            "STRIX KINEA FIF DEB DE INFRA RF CP RESP LTDA": "STRIX KINEA INFRA",
            "df_header": "TB_XML_CARTEIRAS_HEADER",
            "df_caixa": "TB_XML_CARTEIRAS_CAIXA",
            "df_provisoes": "TB_XML_CARTEIRAS_PROVISAO",
            "df_tit_privado": "TB_XML_CARTEIRAS_TIT_PRIVADO",
            "df_compromissada": "TB_XML_CARTEIRAS_COMPROMISSADA",
            "df_tit_pub": "TB_XML_CARTEIRAS_TIT_PUPLICO",
            "df_debentures": "TB_XML_CARTEIRAS_DEBENTURE",
            "df_cotas": "TB_XML_CARTEIRAS_COTA",
            "df_futuros": "TB_XML_CARTEIRAS_FUTUROS",
            "df_despesas": "TB_XML_CARTEIRAS_DESPESAS",
            "CRYSTAL FIC FIM CP": "Crystal",
            "STRIX D1 FIC FIRF": "Strix D1 FIC",
            "STRIX YIELD FC FIRF": "Strix Yield FIC",
            "STRIX YIELD MASTER F": "Strix Yield Master",
            "STRIX INFRA FICFIRF": "Strix Infra",
            "STRIX KINEA INFRA": "Strix Kinea Infra",
        }

        self.lista_tags = [
            "header",
            "caixa",
            "cotas",
            "provisao",
            "debenture",
            "titpublico",
            "titprivado",
            "futuros",
            "despesas",
        ]

        self.dict_colunas_dfs = {
            "header": [
                "ISIN",
                "CNPJ_FUNDO",
                "FUNDO",
                "REFDATE",
                "ADMINISTRADOR",
                "CNPJ_ADM",
                "GESTOR",
                "CNPJ_GESTOR",
                "CUSTODIANTES",
                "CNPJ_CUSTODIANTE",
                "COTA",
                "QTD_COTAS",
                "PATRIMONIO_LIQUIDO",
                "VALOR_ATIVOS",
                "VALOR_RECEBER",
                "VALOR_PAGAR",
                "VALOR_COTAS_EMITIR",
                "VALOR_COTAS_RESGATAR",
                "COD_ANBID",
                "TIPO_FUNDO",
                "NIVEL_RISCO",
            ],
            "caixa": ["ISIN_INSTITUICAO", "TIPO_CONTA", "SALDO_CONTA", "NIVEL_RSC"],
            "cotas": [
                "ISIN",
                "CNPJ_FUNDO",
                "QTD_DISPONIVEL",
                "QTD_GARANTIA",
                "PU_POSICAO",
                "TRIBUTOS",
                "NIVEL_RISCO",
            ],
            "debentures": [
                "ISIN",
                "ATIVO",
                "CONVERSIVEL",
                "PARTICIPACAO_LUCRO",
                "SPE",
                "CUSIP",
                "DATA_EMISSAO",
                "DATA_OPERACAO",
                "DATA_VENCIMENTO",
                "CNPJ_EMISSOR",
                "QTD_DISPONIVEL",
                "QTD_GARANTIA",
                "COD_DEPOSITARIO_GARANTIA",
                "PU_COMPRA",
                "PU_VENCIMENTO",
                "PU_POSICAO",
                "PU_EMISSAO",
                "PRINCIPAL",
                "TRIBUTOS",
                "FINANCEIRO_DISPONIVEL",
                "FINANCEIRO_GARANTIA",
                "TAXA",
                "INDEXADOR",
                "PERC_INDEXADOR",
                "CARACTERISTICA",
                "PERC_PROV_CRED",
                "CLASSE_OPERACAO",
                "ID_INTERNO",
                "NIVEL_RISCO",
            ],
            "provisoes": [
                "COD_PROVISAO",
                "PROVISAO",
                "CRED_DEB",
                "DATA_EFETIVACAO",
                "VALOR",
            ],
            "tit_pub": [
                "ISIN",
                "ATIVO",
                "CUSIP",
                "DATA_EMISSAO",
                "DATA_OPERACAO",
                "DATA_VENCIMENTO",
                "QTD_DISPONIVEL",
                "QTD_GARANTIA",
                "COD_DEPOSITARIO_GARANTIA",
                "PU_COMPRA",
                "PU_VENCIMENTO",
                "PU_POSICAO",
                "PU_EMISSAO",
                "PRINCIPAL",
                "TRIBUTOS",
                "FINANCEIRO_DISPONIVEL",
                "FINANCEIRO_GARANTIA",
                "TAXA",
                "INDEXADOR",
                "PERC_INDEXADOR",
                "CARACTERISTICA",
                "PERC_PROV_CRED",
                "CLASSE_OEPRACAO",
                "ID_INTERNO",
                "NIVEL_RISCO",
            ],
            "compromissada": [
                "ISIN",
                "ATIVO",
                "CUSIP",
                "DATA_EMISSAO",
                "DATA_OPERACAO",
                "DATA_VENCIMENTO",
                "QTD_DISPONIVEL",
                "QTD_GARANTIA",
                "COD_DEPOSITARIO_GARANTIA",
                "PU_COMPRA",
                "PU_VENCIMENTO",
                "PU_POSICAO",
                "PU_EMISSAO",
                "PRINCIPAL",
                "TRIBUTOS",
                "FINANCEIRO_DISPONIVEL",
                "FINANCEIRO_GARANTIA",
                "TAXA",
                "INDEXADOR",
                "PERC_INDEXADOR",
                "CARACTERISTICA",
                "PERC_PROV_CRED",
                "DATA_RETORNO_COMPROMISSADA",
                "PU_RETORNO_COMPROMISSADA",
                "INDEXADOR_COMPROMISSADA",
                "PERC_INDEXADOR_COMPROMISSADA",
                "TAXA_COMPROMISSADA",
                "CLASSE_COMPROMISSADA",
                "CLASSE_OEPRACAO",
                "ID_INTERNO",
                "NIVEL_RISCO",
            ],
            "tit_priv": [
                "ISIN",
                "COD_ATIVO",
                "CUSIP",
                "DATA_EMISSAO",
                "DATA_OPERACAO",
                "DATA_VENCIMENTO",
                "CNPJ_EMISSOR",
                "QTD_DISPONIVEL",
                "QTD_GARANTIA",
                "COD_DEPOSITARIO_GARANTIA",
                "PU_COMPRA",
                "PU_VENCIMENTO",
                "PU_POSICAO",
                "PU_EMISSAO",
                "PRINCIPAL",
                "TRIBUTOS",
                "FINANCEIRO_DISPONIVEL",
                "FINANCEIRO_GARANTIA",
                "TAXA",
                "INDEXADOR",
                "PERC_INDEXADOR",
                "CARACTERISTICA",
                "PERC_PROV_CRED",
                "CLASSE_OEPRACAO",
                "ID_INTERNO",
                "NIVEL_RISCO",
            ],
            "futuros": [
                "ISIN",
                "ATIVO",
                "CNPJ_CORRETORA",
                "SERIE",
                "QTD_DISPONIVEL",
                "FINANCEIRO_DISPONIVEL",
                "TRIBUTOS",
                "DATA_VENCIMENTO",
                "VALOR_AJUSTE",
                "CLASSE_OPERACAO",
                "HEDGE",
                "TIPO_HEDGE",
            ],
            "despesas": [
                "TAXA_ADM",
                "TRIBUTOS",
                "PERC_TAXA_ADM",
                "TX_PERF",
                "VALOR_TAXA_PERF",
                "PERC_TAXA_PERF",
                "PERC_INDEX",
                "OUT_TAX",
                "INDEXADOR",
            ],
        }

        self.dict_provisoes_xml = {
            "1": "Despesas advogado",
            "2": "Auditoria",
            "3": "Despesas bancárias",
            "4": "Cartório",
            "5": "Correspondências",
            "6": "Impressos",
            "7": "Despesas jurídicas",
            "8": "Outras despesas administrativas",
            "9": "Outras despesas exterior",
            "10": "Publicação de atas",
            "11": "Publicidade",
            "12": "Despesa Anbima",
            "13": "Despesa CETIP",
            "14": "Taxa CVM",
            "15": "Taxa custódia",
            "16": "Despesa SELIC",
            "17": "Taxa SISBACEN",
            "18": "Títulos públicos",
            "19": "Títulos privados",
            "20": "Debêntures",
            "21": "Ações ou Opções ações",
            "22": "Derivativos",
            "23": "Termo ações",
            "24": "Termo SELIC",
            "26": "Swap",
            "27": "Dividendos",
            "28": "Prov JCP",
            "29": "Subscrições",
            "30": "Juros (RF)",
            "31": "Empréstimo Ação",
            "32": "Empréstimo Título Publico",
            "33": "Aluguel imóvel",
            "34": "Taxa Administração",
            "35": "Performance",
            "36": "Despesa corretagem Bovespa",
            "37": "Despesa corretagem BM&F",
            "38": "Emolumentos",
            "39": "Valor Bovespa",
            "40": "Valor repasse Bovespa",
            "41": "Valor BM&F",
            "42": "Valor repasse BM&F",
            "43": "Valor outras bolsas",
            "44": "Valor repasse outras bolsas",
        }

    def set_refdate(self, refdate: date):

        self.refdate = refdate

    def verifica_arquivo_existe(self, file_name) -> bool:
        return os.path.exists(file_name)

    def root_xml(self, file_name):
        tree = ET.parse(file_name)
        root = tree.getroot()
        return root

    def check_tags(self):
        for tag in self.root[0]:
            if tag.tag not in self.lista_tags:
                self.list_temp.append(f"Tag '{tag.tag}' não mapeada.")

    def upload_sql(self):
        for nome, df in self.dict_dataframes.items():
            tb = self.dict_suporte_xml[nome]
            self.manager_sql.delete_records(
                tb,
                f"REFDATE = '{self.refdate.strftime('%Y-%m-%d')}' AND FUNDO = '{self.fundo}'",
            )
            self.manager_sql.insert_dataframe(df, tb)

    def trabalha_root(self):

        lista_header = []
        lista_caixa = []
        lista_cotas = []
        lista_debentures = []
        lista_provisoes = []
        lista_tit_pub = []
        lista_compromissada = []
        lista_tit_privado = []
        lista_futuros = []
        lista_despesas = []

        lista_temp = []

        for dado in self.root[0]:

            if dado.tag == "header":
                for subdado in dado:
                    if subdado.tag == "tipofundo":
                        lista_temp.append(int(subdado.text))
                    if subdado.tag == "isin":
                        lista_temp.append(
                            (None if subdado.text == "XXXXXXXXXXXX" else subdado.text)
                        )
                    if subdado.tag == "nome":
                        lista_temp.append(self.dict_suporte_xml[subdado.text])
                    if subdado.tag in [
                        "cnpj",
                        "nomeadm",
                        "cnpjadm",
                        "nomegestor",
                        "cnpjgestor",
                        "nomecustodiante",
                        "cnpjcustodiante",
                        "codanbid",
                        "nivelrsc",
                    ]:
                        lista_temp.append(subdado.text)
                    if subdado.tag in [
                        "valorcota",
                        "quantidade",
                        "patliq",
                        "valorativos",
                        "valorreceber",
                        "valorpagar",
                        "vlcotasemitir",
                        "vlcotasresgatar",
                    ]:
                        lista_temp.append(float(subdado.text))
                    if subdado.tag == "dtposicao":
                        lista_temp.append(datetime.strptime(subdado.text, "%Y%m%d"))
                lista_header.append(lista_temp)
                lista_temp = []

            if dado.tag == "caixa":
                for subdado in dado:
                    if subdado.tag in ["isininstituicao", "tpconta", "nivelrsc"]:
                        lista_temp.append(subdado.text)
                    if subdado.tag == "saldo":
                        lista_temp.append(float(subdado.text))
                lista_caixa.append(lista_temp)
                lista_temp = []

            if dado.tag == "cotas":
                for subdado in dado:
                    if subdado.tag in ["isin", "cnpjfundo", "nivelrsc"]:
                        lista_temp.append(subdado.text)

                    if subdado.tag in [
                        "qtdisponivel",
                        "qtgarantia",
                        "puposicao",
                        "tributos",
                    ]:
                        lista_temp.append(float(subdado.text))

                lista_cotas.append(lista_temp)
                lista_temp = []

            if dado.tag == "provisao":
                for subdado in dado:
                    if subdado.tag == "codprov":
                        lista_temp.append(subdado.text)
                        lista_temp.append(
                            self.dict_provisoes_xml.get(subdado.text, "sem descrição")
                        )
                    if subdado.tag == "credeb":
                        lista_temp.append(subdado.text)
                    if subdado.tag == "dt":
                        lista_temp.append(
                            (
                                date(2999, 12, 31).strftime("%Y-%m-%d")
                                if subdado.text == "00000000"
                                else datetime.strptime(subdado.text, "%Y%m%d")
                            )
                        )
                    if subdado.tag == "valor":
                        lista_temp.append(float(subdado.text))
                lista_provisoes.append(lista_temp)
                lista_temp = []

            if dado.tag == "debenture":
                for subdado in dado:
                    if subdado.tag in [
                        "isin",
                        "coddeb",
                        "debconv",
                        "debpartlucro",
                        "SPE",
                        "cusip",
                        "cnpjemissor",
                        "caracteristica",
                        "classeoperacao",
                        "idinternoativo",
                        "nivelrsc",
                        "depgar",
                    ]:
                        lista_temp.append(str(subdado.text))

                    if subdado.tag == "indexador":
                        lista_temp.append(
                            ("SELIC" if subdado.text == "SEL" else subdado.text)
                        )

                    if subdado.tag in ["dtemissao", "dtoperacao", "dtvencimento"]:
                        lista_temp.append(datetime.strptime(subdado.text, "%Y%m%d"))

                    if subdado.tag in [
                        "pucompra",
                        "puvencimento",
                        "puposicao",
                        "puemissao",
                        "principal",
                        "tributos",
                        "valorfindisp",
                        "valorfinemgar",
                        "coupom",
                        "percindex",
                        "percprovcred",
                    ]:
                        lista_temp.append(float(subdado.text))

                    if subdado.tag in ["qtdisponivel", "qtgarantia"]:

                        try:
                            lista_temp.append(int(subdado.text))
                        except ValueError:
                            lista_temp.append(int(float(subdado.text)))

                lista_debentures.append(lista_temp)
                lista_temp = []

            if dado.tag == "titpublico":
                compromissada_check = 0
                for titpub in dado:
                    if titpub.tag == "codativo":
                        lista_temp.append(self.dict_tit_pub[titpub.text])
                    if titpub.tag in [
                        "isin",
                        "cusip",
                        "caracteristica",
                        "classeoperacao",
                        "idinternoativo",
                        "nivelrsc",
                        "depgar",
                    ]:
                        lista_temp.append(str(titpub.text))
                    if titpub.tag == "indexador":
                        lista_temp.append(
                            ("SELIC" if titpub.text == "SEL" else titpub.text)
                        )

                    if titpub.tag in ("dtemissao", "dtoperacao", "dtvencimento"):
                        lista_temp.append(datetime.strptime(titpub.text, "%Y%m%d"))
                    if titpub.tag in ["qtdisponivel", "qtgarantia"]:

                        try:
                            lista_temp.append(int(titpub.text))
                        except ValueError:
                            lista_temp.append(int(float(titpub.text)))

                        # lista_temp.append(int(titpub.text))
                    if titpub.tag in [
                        "pucompra",
                        "puvencimento",
                        "puposicao",
                        "puemissao",
                        "principal",
                        "tributos",
                        "valorfindisp",
                        "valorfinemgar",
                        "coupom",
                        "percindex",
                        "percprovcred",
                        "",
                    ]:
                        lista_temp.append(float(titpub.text))
                    if titpub.tag == "compromisso":
                        compromissada_check = 1
                        for dado_compromissada in titpub:
                            if dado_compromissada.tag in [
                                "puretorno",
                                "perindexcomp",
                                "txoperacao",
                            ]:
                                lista_temp.append(float(dado_compromissada.text))
                            if dado_compromissada.tag == "dtretorno":
                                lista_temp.append(
                                    datetime.strptime(dado_compromissada.text, "%Y%m%d")
                                )
                            if dado_compromissada.tag in ["classecomp"]:
                                lista_temp.append(dado_compromissada.text)
                            if dado_compromissada.tag == "indexadorcomp":
                                lista_temp.append(
                                    (
                                        "SELIC"
                                        if dado_compromissada.text == "SEL"
                                        else dado_compromissada.text
                                    )
                                )
                            if dado_compromissada.tag == "indexador":
                                lista_temp.append(
                                    (
                                        "SELIC"
                                        if dado_compromissada.text == "SEL"
                                        else dado_compromissada.text
                                    )
                                )
                if compromissada_check == 1:
                    lista_compromissada.append(lista_temp)
                else:
                    lista_tit_pub.append(lista_temp)
                lista_temp = []

            if dado.tag == "titprivado":
                for titprivado in dado:
                    if titprivado.tag in ("dtemissao", "dtoperacao", "dtvencimento"):
                        lista_temp.append(datetime.strptime(titprivado.text, "%Y%m%d"))
                    elif titprivado.tag in (
                        "qtdisponivel",
                        "qtgarantia",
                        "pucompra",
                        "puvencimento",
                        "puposicao",
                        "puemissao",
                        "principal",
                        "tributos",
                        "valorfindisp",
                        "valorfinemgar",
                        "coupom",
                        "percindex",
                        "percprovcred",
                    ):
                        lista_temp.append(float(titprivado.text))
                    elif titprivado.tag in (
                        "isin",
                        "codativo",
                        "cusip",
                        "depgar",
                        "cnpjemissor",
                        "caracteristica",
                        "classeoperacao",
                        "idinternoativo",
                        "nivelrsc",
                    ):
                        lista_temp.append(str(titprivado.text))
                    elif titprivado.tag == "indexador":
                        lista_temp.append(
                            ("SELIC" if titprivado.text == "SEL" else titprivado.text)
                        )
                    else:
                        pass
                lista_tit_privado.append(lista_temp)
                lista_temp = []

            if dado.tag == "futuros":
                for fut in dado:
                    if fut.tag in [
                        "isin",
                        "ativo",
                        "cnpjcorretora",
                        "serie",
                        "classeoperacao",
                        "hedge",
                    ]:
                        lista_temp.append(str(fut.text))
                    elif fut.tag in [
                        "quantidade",
                        "vltotalpos",
                        "tributos",
                        "vlajuste",
                    ]:
                        lista_temp.append(float(fut.text))
                    elif fut.tag in ["dtvencimento"]:
                        lista_temp.append(datetime.strptime(fut.text, "%Y%m%d"))
                    elif fut.tag in ["tphedge"]:
                        lista_temp.append(int(fut.text))
                lista_futuros.append(lista_temp)
                lista_temp = []

            if dado.tag == "despesas":
                for subdado in dado:
                    if subdado.tag in ["txperf", "indexador"]:
                        lista_temp.append(str(subdado.text))
                    elif subdado.tag in [
                        "txadm",
                        "tributos",
                        "perctaxaadm",
                        "vltxperf",
                        "perctxperf",
                        "percindex",
                        "outtax",
                    ]:
                        lista_temp.append(float(subdado.text))

                lista_despesas.append(lista_temp)
                lista_temp = []

        return (
            lista_header,
            lista_caixa,
            lista_cotas,
            lista_debentures,
            lista_provisoes,
            lista_tit_pub,
            lista_compromissada,
            lista_tit_privado,
            lista_futuros,
            lista_despesas,
        )

    def run_processo(self):

        self.check_tags()

        (
            lista_header,
            lista_caixa,
            lista_cotas,
            lista_debentures,
            lista_provisoes,
            lista_tit_pub,
            lista_compromissada,
            lista_tit_privado,
            lista_futuros,
            lista_despesas,
        ) = self.trabalha_root()

        self.dict_dataframes = {}

        if len(lista_header) > 0:
            df_header = pd.DataFrame(
                lista_header, columns=self.dict_colunas_dfs["header"]
            )

            df_header = df_header[
                [
                    "REFDATE",
                    "FUNDO",
                    "ISIN",
                    "CNPJ_FUNDO",
                    "ADMINISTRADOR",
                    "CNPJ_ADM",
                    "GESTOR",
                    "CNPJ_GESTOR",
                    "CUSTODIANTES",
                    "CNPJ_CUSTODIANTE",
                    "COTA",
                    "QTD_COTAS",
                    "PATRIMONIO_LIQUIDO",
                    "VALOR_ATIVOS",
                    "VALOR_RECEBER",
                    "VALOR_PAGAR",
                    "VALOR_COTAS_EMITIR",
                    "VALOR_COTAS_RESGATAR",
                    "COD_ANBID",
                    "TIPO_FUNDO",
                    "NIVEL_RISCO",
                ]
            ]

            self.dict_dataframes["df_header"] = df_header

        if len(lista_caixa) > 0:
            df_caixa = pd.DataFrame(lista_caixa, columns=self.dict_colunas_dfs["caixa"])
            df_caixa.insert(0, "REFDATE", self.refdate)
            df_caixa.insert(1, "FUNDO", self.fundo)
            self.dict_dataframes["df_caixa"] = df_caixa

        if len(lista_provisoes) > 0:
            df_provisoes = pd.DataFrame(
                lista_provisoes, columns=self.dict_colunas_dfs["provisoes"]
            )
            df_provisoes.insert(0, "REFDATE", self.refdate)
            df_provisoes.insert(1, "FUNDO", self.fundo)
            self.dict_dataframes["df_provisoes"] = df_provisoes

        if len(lista_tit_privado) > 0:
            df_tit_privado = pd.DataFrame(
                lista_tit_privado, columns=self.dict_colunas_dfs["tit_priv"]
            )
            df_tit_privado.insert(0, "REFDATE", self.refdate)
            df_tit_privado.insert(1, "FUNDO", self.fundo)
            self.dict_dataframes["df_tit_privado"] = df_tit_privado

        if len(lista_compromissada) > 0:
            df_compromissada = pd.DataFrame(
                lista_compromissada, columns=self.dict_colunas_dfs["compromissada"]
            )
            df_compromissada.insert(0, "REFDATE", self.refdate)
            df_compromissada.insert(1, "FUNDO", self.fundo)
            self.dict_dataframes["df_compromissada"] = df_compromissada

        if len(lista_tit_pub) > 0:
            df_tit_pub = pd.DataFrame(
                lista_tit_pub, columns=self.dict_colunas_dfs["tit_pub"]
            )
            df_tit_pub.insert(0, "REFDATE", self.refdate)
            df_tit_pub.insert(1, "FUNDO", self.fundo)
            self.dict_dataframes["df_tit_pub"] = df_tit_pub

        if len(lista_debentures) > 0:
            df_debentures = pd.DataFrame(
                lista_debentures, columns=self.dict_colunas_dfs["debentures"]
            )
            df_debentures.insert(0, "REFDATE", self.refdate)
            df_debentures.insert(1, "FUNDO", self.fundo)
            self.dict_dataframes["df_debentures"] = df_debentures

        if len(lista_cotas) > 0:
            df_cotas = pd.DataFrame(lista_cotas, columns=self.dict_colunas_dfs["cotas"])
            df_cotas.insert(0, "REFDATE", self.refdate)
            df_cotas.insert(1, "FUNDO", self.fundo)
            self.dict_dataframes["df_cotas"] = df_cotas

        if len(lista_futuros) > 0:
            df_futuros = pd.DataFrame(
                lista_futuros, columns=self.dict_colunas_dfs["futuros"]
            )
            df_futuros.insert(0, "REFDATE", self.refdate)
            df_futuros.insert(1, "FUNDO", self.fundo)
            self.dict_dataframes["df_futuros"] = df_futuros

        if len(lista_despesas) > 0:
            df_despesas = pd.DataFrame(
                lista_despesas, columns=self.dict_colunas_dfs["despesas"]
            )
            df_despesas.insert(0, "REFDATE", self.refdate)
            df_despesas.insert(1, "FUNDO", self.fundo)
            self.dict_dataframes["df_despesas"] = df_despesas

        self.upload_sql()
        # self.logger.debug(f"Upload XML finalizado para o fundo {self.fundo}")

    def run_carteiras(self, refdate, lista_fundos: list = None):

        self.refdate = refdate

        if lista_fundos != None:
            self.list_funds.clear()
            for fundo in lista_fundos:
                self.list_funds.append(fundo)

        result = {}

        for fundo in self.list_funds:

            self.list_temp = []

            self.fundo = fundo

            self.file_name = (
                f"C:\\Users\\RafaelKoyama\\Strix Capital\\Backoffice - General\\Carteiras\\"
                f"{self.dict_suporte_xml[self.fundo]}\\xml\\{self.fundo.replace(' ', '_')}_{self.refdate.strftime('%Y%m%d')}.xml"
            )
            if self.verifica_arquivo_existe(self.file_name):
                self.root = self.root_xml(self.file_name)
                self.run_processo()
            else:
                # self.logger.error(f"Arq não encontrado: {self.file_name}")
                self.list_temp.append(f"Arquivo xml não encontrado.")

            if len(self.list_temp) == 0:
                result[self.fundo] = "ok"
            else:
                result[self.fundo] = self.list_temp

        return result

    def run_strix_master_fia_cc(self):

        self.logger.reset_index()
        self.logger.info(log_message="run_strix_master_fia_cc - Iniciado", script_original=SCRIPT_NAME)

        result = {}

        refdate_arq = self.funcoes_pytools.workday_br(refdate=self.refdate, dias=1)

        path = f"C:\\Users\\{str_user}\\Strix Capital\\Backoffice - General\\Carteiras\\Strix Master FIA\\Conta Corrente"

        path_arq = os.path.join(path, f"5218073_{refdate_arq.strftime('%Y-%m-%d')}.xml")

        if not self.verifica_arquivo_existe(path_arq):
            result["STRIX MASTER FIA"] = "Arquivo não encontrado."
            self.logger.info(log_message=f"run_strix_master_fia_cc - {path_arq} - Arquivo não encontrado", script_original=SCRIPT_NAME)
        else:
            error_tag = []
            self.logger.info(log_message=f"run_strix_master_fia_cc - {path_arq} - Arquivo encontrado", script_original=SCRIPT_NAME)
            root = self.root_xml(path_arq)

            lista_data_lancamento = []
            lista_historico = []
            lista_dc = []
            lista_financeiro = []
            lista_origem = []
            lista_usuario = []
            lista_obs = []

            for child in root:
                for row in child:
                    if row.tag == "Data":
                        lista_data_lancamento.append(
                            datetime.strptime(row.text, "%Y-%m-%d").date()
                        )
                    elif row.tag == "Historico":
                        lista_historico.append(row.text.strip())
                    elif row.tag == "DC":
                        lista_dc.append(row.text.strip())
                    elif row.tag == "Financeiro":
                        lista_financeiro.append(float(row.text))
                    elif row.tag == "Origem":
                        lista_origem.append(
                            row.text.strip() if row.text is not None else None
                        )
                    elif row.tag == "Usuario":
                        lista_usuario.append(
                            row.text.strip() if row.text is not None else None
                        )
                    elif row.tag == "Observacao":
                        lista_obs.append(
                            row.text.strip() if row.text is not None else None
                        )
                    else:
                        self.logger.error(log_message=f"run_strix_master_fia_cc - Tag não mapeada: {row.tag}", script_original=SCRIPT_NAME)
                        error_tag.append(row.tag)

            df_to_upload = pd.DataFrame(
                {
                    "REFDATE": lista_data_lancamento,
                    "D_C": lista_dc,
                    "VALOR": lista_financeiro,
                    "HISTORICO": lista_historico,
                    "ORIGEM": lista_origem,
                    "USUARIO": lista_usuario,
                    "OBS": lista_obs,
                }
            )

            df_to_upload.insert(1, "FUNDO", "STRIX MASTER FIA")

            df_to_upload = df_to_upload[df_to_upload["REFDATE"] == self.refdate]

            if len(df_to_upload) > 0:
                self.manager_sql.delete_records(
                    "TB_XML_CONTA_CORRENTE",
                    f"REFDATE = '{self.refdate.strftime('%Y-%m-%d')}' AND FUNDO = 'STRIX MASTER FIA'",
                )
                self.manager_sql.insert_dataframe(df_to_upload, "TB_XML_CONTA_CORRENTE")

                if len(error_tag) > 0:
                    error_tag = list(set(error_tag))
                    result["STRIX MASTER FIA"] = (f"Upload OK | Tag(s) não mapeada(s): {", ".join(error_tag)}")
                    self.logger.info(log_message="run_strix_master_fia_cc - Upload OK", script_original=SCRIPT_NAME)
                else:
                    result["STRIX MASTER FIA"] = "Upload OK!"
                    self.logger.info(log_message="run_strix_master_fia_cc - Upload OK", script_original=SCRIPT_NAME)
            else:
                result["STRIX MASTER FIA"] = "Sem lançamentos para o dia."
                self.logger.info(log_message="run_strix_master_fia_cc - Sem dados para o dia", script_original=SCRIPT_NAME)

        return result


class UpdateIndexadores:

    def __init__(self, refdate, manager_sql=None, funcoes_pytools=None):
        if manager_sql is None:
            self.manager_sql = SQL_Manager()
        else:
            self.manager_sql = manager_sql

        if funcoes_pytools is None:
            self.funcoes_pytools = FuncoesPyTools(self.manager_sql)
        else:
            self.funcoes_pytools = funcoes_pytools

        self.dict_indexador = {
            "STRIX FIA": "IMABAJUST",
            "STRIX YIELD MASTER F": "CDIE",
            "STRIX INFRA FICFIRF": "IMA-B",
            "IMABAJUST": "IMABAJUST",
            "CDIE": "CDI",
            "IMA-B": "IMA-B",
        }
        self.refdate = refdate
        self.lista_fundos = ["STRIX FIA", "STRIX INFRA FICFIRF"]
        self.dmenos = self.funcoes_pytools.workday_br(refdate=self.refdate, dias=-1)

    def captura_dados(self):

        cota_indexador_dm1 = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT COTA_INDEXADOR FROM TB_INDEXADORES WHERE REFDATE = '{self.dmenos.strftime('%Y-%m-%d')}' AND INDEXADOR = '{self.dict_indexador[self.dict_indexador[self.fundo]]}'"
        )
        try:
            cota_indexador_dm1 = float(cota_indexador_dm1.values[0][0])
        except IndexError:
            cota_indexador_dm1 = None

        rent_dia_indexador = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT VAR_INDEXADOR_DIA FROM TB_BASE_BTG_PERFORMANCE_COTA WHERE REFDATE = '{self.refdate.strftime('%Y-%m-%d')}' AND INDEXADOR_FUNDO = '{self.dict_indexador[self.fundo]}' AND FUNDO = '{self.fundo}'"
        )
        try:
            rent_dia_indexador = float(rent_dia_indexador.values[0][0] / 100)
            if self.dict_indexador[self.fundo] == "CDIE":
                rent_dia_indexador = self.funcoes_pytools.trunc_number(
                    rent_dia_indexador, 8
                )
        except IndexError:
            rent_dia_indexador = None

        return cota_indexador_dm1, rent_dia_indexador

    def sobe_dados(self):

        cota_indexador_dia = float(
            self.cota_indexador_dm1 * (1 + self.rent_dia_indexador)
        )
        valor_indexador_ano = round((1 + self.rent_dia_indexador) ** 252 - 1, 4)
        df_indexador = pd.DataFrame(
            {
                "REFDATE": [self.refdate],
                "INDEXADOR": [self.dict_indexador[self.dict_indexador[self.fundo]]],
                "VALOR_ANO": [valor_indexador_ano],
                "VALOR_DIA": [self.rent_dia_indexador],
                "COTA_INDEXADOR": [cota_indexador_dia],
            }
        )
        self.manager_sql.delete_records(
            "TB_INDEXADORES",
            f"REFDATE = '{self.refdate.strftime('%Y-%m-%d')}' AND INDEXADOR = '{self.dict_indexador[self.dict_indexador[self.fundo]]}'",
        )
        self.manager_sql.insert_dataframe(df_indexador, "TB_INDEXADORES")

    def run(self):

        result = {}

        for fundo in self.lista_fundos:
            self.fundo = fundo
            self.cota_indexador_dm1, self.rent_dia_indexador = self.captura_dados()
            if (
                self.cota_indexador_dm1 is not None
                and self.rent_dia_indexador is not None
            ):
                self.sobe_dados()
                result[self.dict_indexador[self.fundo]] = "ok"
            else:
                result[self.dict_indexador[self.fundo]] = (
                    f"ERROR --> {('Indexador dm1' if self.cota_indexador_dm1 is None else '')}{(' | Rent Indexador Dia' if self.rent_dia_indexador is None else '')}"
                )

        return result


class RentabilidadeAtivos:

    def __init__(self, manager_sql=None, funcoes_pytools=None):

        if manager_sql is None:
            self.manager_sql = SQL_Manager()
        else:
            self.manager_sql = manager_sql

        if funcoes_pytools is None:
            self.funcoes_pytools = FuncoesPyTools(self.manager_sql)
        else:
            self.funcoes_pytools = funcoes_pytools

        self.base_fluxo_pagamentos()
        self.call_base_tipo_ativos()

    def call_base_tipo_ativos(self):
        self.base_tipo_ativos = self.manager_sql.select_dataframe(
            "SELECT DISTINCT TIPO_ATIVO, ATIVO FROM TB_CADASTRO_ATIVOS"
        )

    def set_refdate(self, refdate):
        self.refdate = refdate
        self.dmenos1 = self.funcoes_pytools.workday_br(refdate=self.refdate, dias=-1)

    def calcular_rentabilidade(self, row):
        pu_d0 = row["PU_D0_AJUSTADO"]
        pu_dm1 = row["PU_DM1"]

        if pd.isna(pu_d0):  # Se o preço atual for NaN, rentabilidade é 0
            return 0
        if (
            pd.isna(pu_dm1) or pu_dm1 == 0
        ):  # Se o preço anterior for NaN ou 0, não pode calcular
            return np.nan
        return pu_d0 / pu_dm1 - 1

    def cotizacao_ativo(self, row):

        rent_pu_dia = row["RENT_PU_DIA"]
        cota_dm1 = row["COTA_PU_DM1"]

        if pd.isna(cota_dm1):  # Se o preço atual for NaN, rentabilidade é 0
            return 1
        else:
            return cota_dm1 * (1 + rent_pu_dia)

    def delta_pu(self, row):

        pu_d0 = row["PU_D0_AJUSTADO"]
        pu_dm1 = row["PU_DM1"]

        if pd.isna(pu_d0):  # Se o preço atual for NaN, rentabilidade é 0
            return 0
        if (
            pd.isna(pu_dm1) or pu_dm1 == 0
        ):  # Se o preço anterior for NaN ou 0, não pode calcular
            return np.nan
        return round(pu_d0 - pu_dm1, 6)

    def ajuste_preco(self, row):

        pu = row["PU"]
        valor_pago = row["VALOR_PAGO"]

        if pd.isna(pu) and pd.isna(valor_pago):
            return None
        elif pd.isna(pu) and not pd.isna(valor_pago):
            return valor_pago
        elif not pd.isna(pu) and pd.isna(valor_pago):
            return pu
        elif not pd.isna(pu) and not pd.isna(valor_pago):
            return pu + valor_pago

    def base_cota_pu(self):
        """Funcao captura base de cota para rentabilidade dos ativos."""
        self.df_cota_pu = self.manager_sql.select_dataframe(
            f"SELECT REFDATE, ATIVO, COTA_PU FROM TB_RENTABILIDADE_ATIVOS"
        )

    def base_fluxo_pagamentos(self):

        df_fluxo_pagamentos = self.manager_sql.select_dataframe(
            r"Exec PROCEDURE_BASE_PAGAMENTO_ATIVOS"
        )[["DATA_LIQUIDACAO", "ATIVO", "VALOR_PAGO"]]
        df_fluxo_pagamentos = df_fluxo_pagamentos[df_fluxo_pagamentos["VALOR_PAGO"] > 0]
        df_fluxo_pagamentos = (
            df_fluxo_pagamentos.groupby(["DATA_LIQUIDACAO", "ATIVO"])
            .sum()
            .reset_index()
        )
        df_fluxo_pagamentos.rename(columns={"DATA_LIQUIDACAO": "REFDATE"}, inplace=True)

        self.df_fluxo_pagamentos = df_fluxo_pagamentos

    def base_precos_fidcs(self):

        df_ativos_fidcs = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT ATIVO FROM TB_CARTEIRAS WHERE "
            f"TIPO_ATIVO = 'FIDC' AND REFDATE = '{self.funcoes_pytools.convert_data_sql(self.refdate)}'"
        )

        str_fidcs = ",".join([f"'{ativo}'" for ativo in df_ativos_fidcs["ATIVO"]])

        df_precos_fidcs = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT REFDATE, ATIVO, PU FROM TB_PRECOS WHERE FONTE = 'BTG' AND ATIVO IN ({str_fidcs})"
        )

        self.df_precos_fidcs = df_precos_fidcs

    def trabalha_dados_fidcs(self):

        df = pd.merge(
            self.df_precos_fidcs,
            self.df_fluxo_pagamentos,
            how="outer",
            on=["REFDATE", "ATIVO"],
        )

        df["PU_AJUSTADO"] = df.apply(self.ajuste_preco, axis=1)

        self.df_precos_fidcs_d0 = df[df["REFDATE"] == self.refdate][
            ["ATIVO", "PU", "VALOR_PAGO", "PU_AJUSTADO"]
        ].rename(
            columns={
                "PU": "PU_D0",
                "VALOR_PAGO": "VALOR_PAGO_DIA",
                "PU_AJUSTADO": "PU_D0_AJUSTADO",
            }
        )

        self.df_precos_fidcs_d1 = df[df["REFDATE"] == self.dmenos1][
            ["ATIVO", "PU"]
        ].rename(columns={"PU": "PU_DM1"})

        self.df_cota_pu_dm1 = self.df_cota_pu[
            self.df_cota_pu["REFDATE"] == self.dmenos1
        ][["ATIVO", "COTA_PU"]].rename(columns={"COTA_PU": "COTA_PU_DM1"})

    def base_rentabilidade_fidcs(self):

        df_rent = pd.merge(
            self.df_precos_fidcs_d0, self.df_precos_fidcs_d1, on="ATIVO", how="outer"
        )
        df_rent = pd.merge(df_rent, self.df_cota_pu_dm1, on="ATIVO", how="left")
        df_rent = pd.merge(df_rent, self.base_tipo_ativos, on="ATIVO", how="left")

        df_rent["RENT_PU_DIA"] = df_rent.apply(self.calcular_rentabilidade, axis=1)
        df_rent["COTA_PU"] = df_rent.apply(self.cotizacao_ativo, axis=1)
        df_rent["DELTA_PU"] = df_rent.apply(self.delta_pu, axis=1)

        df_rent.insert(0, "REFDATE", self.refdate)
        df_rent["ABS_RENT_PU_DIA"] = df_rent["RENT_PU_DIA"].abs()
        df_rent.sort_values(by=["ABS_RENT_PU_DIA"], ascending=[False], inplace=True)

        df_rent = df_rent[
            [
                "REFDATE",
                "TIPO_ATIVO",
                "ATIVO",
                "PU_D0",
                "VALOR_PAGO_DIA",
                "PU_D0_AJUSTADO",
                "PU_DM1",
                "DELTA_PU",
                "RENT_PU_DIA",
                "COTA_PU",
                "ABS_RENT_PU_DIA",
            ]
        ]

        df_rent = df_rent[
            (df_rent["PU_DM1"] != 0) & (df_rent["PU_D0_AJUSTADO"].notna())
        ]

        self.df_rent_fidcs = df_rent

    def base_precos_ccbs(self):

        df_ativos = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT ATIVO FROM TB_CARTEIRAS WHERE "
            f"TIPO_ATIVO = 'CCB' AND REFDATE = '{self.funcoes_pytools.convert_data_sql(self.refdate)}'"
        )

        str_ativos = ",".join([f"'{ativo}'" for ativo in df_ativos["ATIVO"]])

        df_precos = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT REFDATE, ATIVO, PU FROM TB_PRECOS WHERE FONTE = 'BTG' AND ATIVO IN ({str_ativos})"
        )

        self.df_precos_ccbs = df_precos

    def trabalha_dados_ccbs(self):

        df = pd.merge(
            self.df_precos_ccbs,
            self.df_fluxo_pagamentos,
            how="outer",
            on=["REFDATE", "ATIVO"],
        )

        df["PU_AJUSTADO"] = df.apply(self.ajuste_preco, axis=1)

        self.df_precos_ccbs_d0 = df[df["REFDATE"] == self.refdate][
            ["ATIVO", "PU", "VALOR_PAGO", "PU_AJUSTADO"]
        ].rename(
            columns={
                "PU": "PU_D0",
                "VALOR_PAGO": "VALOR_PAGO_DIA",
                "PU_AJUSTADO": "PU_D0_AJUSTADO",
            }
        )

        self.df_precos_ccbs_d1 = df[df["REFDATE"] == self.dmenos1][
            ["ATIVO", "PU"]
        ].rename(columns={"PU": "PU_DM1"})

        self.df_cota_pu_dm1 = self.df_cota_pu[
            self.df_cota_pu["REFDATE"] == self.dmenos1
        ][["ATIVO", "COTA_PU"]].rename(columns={"COTA_PU": "COTA_PU_DM1"})

    def base_rentabilidade_ccbs(self):

        df_rent = pd.merge(
            self.df_precos_ccbs_d0, self.df_precos_ccbs_d1, on="ATIVO", how="outer"
        )
        df_rent = pd.merge(df_rent, self.df_cota_pu_dm1, on="ATIVO", how="left")
        df_rent = pd.merge(df_rent, self.base_tipo_ativos, on="ATIVO", how="left")

        df_rent["RENT_PU_DIA"] = df_rent.apply(self.calcular_rentabilidade, axis=1)
        df_rent["COTA_PU"] = df_rent.apply(self.cotizacao_ativo, axis=1)
        df_rent["DELTA_PU"] = df_rent.apply(self.delta_pu, axis=1)

        df_rent.insert(0, "REFDATE", self.refdate)
        df_rent["ABS_RENT_PU_DIA"] = df_rent["RENT_PU_DIA"].abs()
        df_rent.sort_values(by=["ABS_RENT_PU_DIA"], ascending=[False], inplace=True)

        df_rent = df_rent[
            [
                "REFDATE",
                "TIPO_ATIVO",
                "ATIVO",
                "PU_D0",
                "VALOR_PAGO_DIA",
                "PU_D0_AJUSTADO",
                "PU_DM1",
                "DELTA_PU",
                "RENT_PU_DIA",
                "COTA_PU",
                "ABS_RENT_PU_DIA",
            ]
        ]

        df_rent = df_rent[
            (df_rent["PU_DM1"] != 0) & (df_rent["PU_D0_AJUSTADO"].notna())
        ]

        self.df_rent_ccbs = df_rent

    def base_precos_lfs(self):

        df_ativos_lf = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT ATIVO FROM TB_CARTEIRAS WHERE "
            f"TIPO_ATIVO like '%LF%' AND REFDATE = '{self.funcoes_pytools.convert_data_sql(self.refdate)}'"
        )

        str_lfs = ",".join([f"'{ativo}'" for ativo in df_ativos_lf["ATIVO"]])

        df_precos_lfs = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT REFDATE, ATIVO, PU FROM TB_PRECOS WHERE FONTE = 'BTG' AND ATIVO IN ({str_lfs})"
        )

        self.df_precos_lfs = df_precos_lfs

    def trabalha_dados_lfs(self):

        df_lfs = pd.merge(
            self.df_precos_lfs,
            self.df_fluxo_pagamentos,
            how="outer",
            on=["REFDATE", "ATIVO"],
        )

        df_lfs["PU_AJUSTADO"] = df_lfs.apply(self.ajuste_preco, axis=1)

        self.df_precos_lfs_d0 = df_lfs[df_lfs["REFDATE"] == self.refdate][
            ["ATIVO", "PU", "VALOR_PAGO", "PU_AJUSTADO"]
        ].rename(
            columns={
                "PU": "PU_D0",
                "VALOR_PAGO": "VALOR_PAGO_DIA",
                "PU_AJUSTADO": "PU_D0_AJUSTADO",
            }
        )

        self.df_precos_lfs_d1 = df_lfs[df_lfs["REFDATE"] == self.dmenos1][
            ["ATIVO", "PU"]
        ].rename(columns={"PU": "PU_DM1"})

        self.df_cota_pu_dm1 = self.df_cota_pu[
            self.df_cota_pu["REFDATE"] == self.dmenos1
        ][["ATIVO", "COTA_PU"]].rename(columns={"COTA_PU": "COTA_PU_DM1"})

    def base_rentabilidade_lfs(self):

        df_rent_lfs = pd.merge(
            self.df_precos_lfs_d0, self.df_precos_lfs_d1, on="ATIVO", how="outer"
        )
        df_rent_lfs = pd.merge(df_rent_lfs, self.df_cota_pu_dm1, on="ATIVO", how="left")
        df_rent_lfs = pd.merge(
            df_rent_lfs, self.base_tipo_ativos, on="ATIVO", how="left"
        )

        df_rent_lfs["RENT_PU_DIA"] = df_rent_lfs.apply(
            self.calcular_rentabilidade, axis=1
        )
        df_rent_lfs["COTA_PU"] = df_rent_lfs.apply(self.cotizacao_ativo, axis=1)
        df_rent_lfs["DELTA_PU"] = df_rent_lfs.apply(self.delta_pu, axis=1)

        df_rent_lfs.insert(0, "REFDATE", self.refdate)
        df_rent_lfs["ABS_RENT_PU_DIA"] = df_rent_lfs["RENT_PU_DIA"].abs()
        df_rent_lfs.sort_values(by=["ABS_RENT_PU_DIA"], ascending=[False], inplace=True)

        df_rent_lfs = df_rent_lfs[
            [
                "REFDATE",
                "TIPO_ATIVO",
                "ATIVO",
                "PU_D0",
                "VALOR_PAGO_DIA",
                "PU_D0_AJUSTADO",
                "PU_DM1",
                "DELTA_PU",
                "RENT_PU_DIA",
                "COTA_PU",
                "ABS_RENT_PU_DIA",
            ]
        ]

        df_rent_lfs = df_rent_lfs[
            (df_rent_lfs["PU_DM1"] != 0) & (df_rent_lfs["PU_D0_AJUSTADO"].notna())
        ]

        self.df_rent_lfs = df_rent_lfs

    def base_precos_debentures(self):

        df_posicao_debentures = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT ATIVO FROM TB_CARTEIRAS WHERE TIPO_ATIVO = 'Debênture' "
            f"AND FUNDO = 'STRIX YIELD MASTER' AND REFDATE = '{self.funcoes_pytools.convert_data_sql(self.refdate)}'"
        )

        str_debentures = ",".join(
            [f"'{ativo}'" for ativo in df_posicao_debentures["ATIVO"]]
        )

        df_anbima_debentures = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT REFDATE, COD_ATIVO AS ATIVO, PU AS PU_ANBIMA FROM TB_ANBIMA_DEBENTURES "
            f"WHERE COD_ATIVO IN ({str_debentures})"
        )

        df_btg_debentures = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT REFDATE, ATIVO, PU AS PU_BTG FROM TB_PRECOS WHERE TIPO_ATIVO = 'Debênture' AND FONTE = 'BTG'"
        )

        df_precos_debentures = pd.merge(
            df_anbima_debentures,
            df_btg_debentures,
            on=["REFDATE", "ATIVO"],
            how="outer",
        )
        df_precos_debentures["PU"] = df_precos_debentures.apply(
            lambda x: x["PU_BTG"] if np.isnan(x["PU_ANBIMA"]) else x["PU_ANBIMA"],
            axis=1,
        )
        df_precos_debentures = df_precos_debentures[["REFDATE", "ATIVO", "PU"]]

        self.df_precos_debentures = df_precos_debentures

    def trabalha_dados_debentures(self):

        df_debentures = pd.merge(
            self.df_precos_debentures,
            self.df_fluxo_pagamentos,
            how="left",
            on=["REFDATE", "ATIVO"],
        )

        df_debentures["PU_AJUSTADO"] = df_debentures.apply(
            lambda x: (
                x["PU"] + x["VALOR_PAGO"] if pd.notna(x["VALOR_PAGO"]) else x["PU"]
            ),
            axis=1,
        )

        self.df_precos_deb_d0 = df_debentures[df_debentures["REFDATE"] == self.refdate][
            ["ATIVO", "PU", "VALOR_PAGO", "PU_AJUSTADO"]
        ].rename(
            columns={
                "PU": "PU_D0",
                "VALOR_PAGO": "VALOR_PAGO_DIA",
                "PU_AJUSTADO": "PU_D0_AJUSTADO",
            }
        )

        self.df_precos_deb_d1 = df_debentures[df_debentures["REFDATE"] == self.dmenos1][
            ["ATIVO", "PU"]
        ].rename(columns={"PU": "PU_DM1"})

        self.df_cota_pu_dm1 = self.df_cota_pu[
            self.df_cota_pu["REFDATE"] == self.dmenos1
        ][["ATIVO", "COTA_PU"]].rename(columns={"COTA_PU": "COTA_PU_DM1"})

    def base_rentabilidade_debentures(self):

        df_rent_debentures = pd.merge(
            self.df_precos_deb_d0, self.df_precos_deb_d1, on="ATIVO", how="outer"
        )
        df_rent_debentures = pd.merge(
            df_rent_debentures, self.df_cota_pu_dm1, on="ATIVO", how="left"
        )

        df_rent_debentures["RENT_PU_DIA"] = df_rent_debentures.apply(
            self.calcular_rentabilidade, axis=1
        )
        df_rent_debentures["COTA_PU"] = df_rent_debentures.apply(
            self.cotizacao_ativo, axis=1
        )
        df_rent_debentures["DELTA_PU"] = df_rent_debentures.apply(self.delta_pu, axis=1)

        df_rent_debentures.insert(0, "REFDATE", self.refdate)
        df_rent_debentures.insert(1, "TIPO_ATIVO", "Debênture")
        df_rent_debentures["ABS_RENT_PU_DIA"] = df_rent_debentures["RENT_PU_DIA"].abs()
        df_rent_debentures.sort_values(
            by=["ABS_RENT_PU_DIA"], ascending=[False], inplace=True
        )

        df_rent_debentures = df_rent_debentures[
            [
                "REFDATE",
                "TIPO_ATIVO",
                "ATIVO",
                "PU_D0",
                "VALOR_PAGO_DIA",
                "PU_D0_AJUSTADO",
                "PU_DM1",
                "DELTA_PU",
                "RENT_PU_DIA",
                "COTA_PU",
                "ABS_RENT_PU_DIA",
            ]
        ]

        df_rent_debentures = df_rent_debentures[
            (df_rent_debentures["PU_DM1"] != 0)
            & (df_rent_debentures["PU_D0_AJUSTADO"].notna())
        ]

        self.df_rent_debentures = df_rent_debentures

    def upload_base_rentabilidade(self, df, tipo_ativo=None):

        self.manager_sql.delete_records(
            "TB_RENTABILIDADE_ATIVOS",
            f"REFDATE = '{self.funcoes_pytools.convert_data_sql(self.refdate)}' AND TIPO_ATIVO IN ('{tipo_ativo}')",
        )

        self.manager_sql.insert_dataframe(df, "TB_RENTABILIDADE_ATIVOS")

    def run_debentures(self, refdate):

        self.set_refdate(refdate)
        self.base_cota_pu()
        self.base_precos_debentures()
        self.trabalha_dados_debentures()
        self.base_rentabilidade_debentures()
        self.upload_base_rentabilidade(self.df_rent_debentures, "Debênture")

    def run_lfs(self, refdate):

        self.set_refdate(refdate)
        self.base_cota_pu()
        self.base_precos_lfs()
        self.trabalha_dados_lfs()
        self.base_rentabilidade_lfs()

        str_tipos_lfs = "','".join(
            [f"{tipo_ativo}" for tipo_ativo in self.df_rent_lfs["TIPO_ATIVO"].unique()]
        )

        self.upload_base_rentabilidade(self.df_rent_lfs, str_tipos_lfs)

    def run_fidcs(self, refdate):

        self.set_refdate(refdate)
        self.base_cota_pu()
        self.base_precos_fidcs()
        self.trabalha_dados_fidcs()
        self.base_rentabilidade_fidcs()
        self.upload_base_rentabilidade(self.df_rent_fidcs, "FIDC")

    def run_ccb(self, refdate):

        self.set_refdate(refdate)
        self.base_cota_pu()
        self.base_precos_ccbs()
        self.trabalha_dados_ccbs()
        self.base_rentabilidade_ccbs()
        self.upload_base_rentabilidade(self.df_rent_ccbs, "CCB")


class DadosBoletimB3:

    def __init__(self, manager_sql=None, funcoes_pytools=None):

        if manager_sql is None:
            self.manager_sql = SQL_Manager()
        else:
            self.manager_sql = manager_sql

        if funcoes_pytools is None:
            self.funcoes_pytools = FuncoesPyTools(self.manager_sql)
        else:
            self.funcoes_pytools = funcoes_pytools

        self.refdate = None
        self.df_negociosbalcao_rf = pd.DataFrame()
        self.result_csv = {}
        self.result_sql = {}

    def set_refdate(self, refdate: date):

        self.refdate = refdate

    def read_csv_negocios_balcao_rf(self, str_file: str):

        if not self.funcoes_pytools.checkFileExists(str_file):
            self.result_csv['Negócios Bancão RF'] = "Arquivo não encontrado"

        skip_row = self.funcoes_pytools.find_header_row(str_file, 'Data Negócio')

        df = pd.read_csv(str_file, skiprows=skip_row, skipfooter=1, engine='python', sep=';', decimal=',')

        df.rename(columns = {
            'Instrumento Financeiro': 'TIPO_ATIVO',
            'Emissor': 'EMISSOR',
            'Código IF': 'COD_IF',
            'Quantidade Negociada': 'QUANTIDADE',
            'Preço Negócio': 'PRECO',
            'Volume Financeiro (R$)': 'FINANCEIRO',
            'Taxa Negócio': 'TAXA',
            'Origem Negócio': 'ORIGEM',
            'Horário Negócio': 'HORARIO_NEGOCIADO',
            'Data Negócio': 'REFDATE',
            'Cód. Identificador do Negócio': 'ID_B3',
            'Código ISIN': 'ISIN',
            'Data Liquidação': 'DATA_LIQUIDACAO',
            'Situação Negócio': 'STATUS'
            }, inplace=True)

        df = df[[
            'REFDATE',
            'STATUS',
            'TIPO_ATIVO',
            'COD_IF',
            'EMISSOR',
            'TAXA',
            'QUANTIDADE',
            'PRECO',
            'FINANCEIRO',
            'HORARIO_NEGOCIADO',
            'DATA_LIQUIDACAO',
            'ISIN',
            'ORIGEM',
            'ID_B3'
            ]]
        
        df['HORARIO_NEGOCIADO'] = pd.to_datetime(df['HORARIO_NEGOCIADO'], format='%H:%M:%S').dt.time
        df['DATA_LIQUIDACAO'] = pd.to_datetime(df['DATA_LIQUIDACAO'], format='%d/%m/%Y').dt.date
        df['REFDATE'] = pd.to_datetime(df['REFDATE'], format='%d/%m/%Y').dt.date
        df['TAXA'] = df['TAXA'].apply(lambda x: None if x == '-' else float(x))
        df['QUANTIDADE'] = df['QUANTIDADE'].astype(int)
        df['ISIN'] = df['ISIN'].apply(lambda x: None if x in ['-', '0'] else x)
        df['ID_B3'] = df['ID_B3'].apply(lambda x: None if x in ['-', '0'] else x)
        df['FINANCEIRO'] = df['FINANCEIRO'].apply(lambda x: None if x in ['-'] else float(x))
        df = df.sort_values(by=['REFDATE', 'HORARIO_NEGOCIADO']).reset_index(drop=True)

        self.df_negociosbalcao_rf = df.copy()
        self.result_csv['Negócios Bancão RF'] = "CSV lido com sucesso"

    def upload_to_sql(self):

        if self.df_negociosbalcao_rf.empty:
            self.result_sql['Negócios Bancão RF'] = "Sem dados para upload"
        else:
            str_refdates = "', '".join(self.df_negociosbalcao_rf['REFDATE'].unique().astype(str).tolist())

            self.manager_sql.delete_records(
                table_name="TB_B3_NEGOCIOS_BALCAO_RENDA_FIXA",
                condition=f"REFDATE IN ('{str_refdates}')"
            )

            resp = self.manager_sql.insert_dataframe(df=self.df_negociosbalcao_rf, table_name="TB_B3_NEGOCIOS_BALCAO_RENDA_FIXA")
            self.result_sql['Negócios Bancão RF'] = resp
