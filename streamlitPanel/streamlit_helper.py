from __init__ import *

VERSION_APP = "1.0.0"
VERSION_REFDATE = "2024-07-10"
ENVIRONMENT = os.getenv("ENVIRONMENT")
SCRIPT_NAME = os.path.basename(__file__)

if ENVIRONMENT == "DEVELOPMENT":
    print(f"{SCRIPT_NAME.upper()} - {ENVIRONMENT} - {VERSION_APP} - {VERSION_REFDATE}")

append_paths()

# -----------------------------------------------------------------------

from datetime import date

import pandas as pd
from dateutil.relativedelta import relativedelta

from tools.db_helper import SQL_Manager
from tools.py_tools import FuncoesPyTools

opcoes_fundos = [
    "Strix Yield Master",
    "Strix Yield FIC",
    "Strix D1 FIC FIRF CP",
    "Strix FIA",
    "Strix Infra",
    "Strix Master FIA",
    "Crystal FICFIM CP",
]

dict_aux_btg_bases_cc_e_movs = {
    "Strix Yield Master": "STRIX YIELD MASTER F",
    "Strix Yield FIC": "STRIX YIELD FC FIRF",
    "Strix D1 FIC FIRF CP": "STRIX D1 FIC FIRF",
    "Strix FIA": "STRIX FIA",
    "Strix Infra": "STRIX INFRA FICFIRF",
    "Strix Master FIA": "STRIX MASTER FIA",
    "Crystal FICFIM CP": "CRYSTAL FIC FIM CP",
}

dict_aux_dados_fundos = {
    "Strix Yield Master": "STRIX YIELD MASTER F",
    "Strix Yield FIC": "STRIX YIELD FC FIRF",
    "Strix Infra": "STRIX INFRA FICFIRF",
    "Strix FIA": "STRIX FIA",
    "Strix D1 FIC RF CP": "STRIX D1 FIC FIRF",
    "Crystal FIC": "CRYSTAL FIC FIM CP",
}

lista_cnpjs = ["53076975000160", "52792894000101", "52797717000100", "52797894000196"]

dict_fundos_cnpj = {
    "Strix Yield Master": "53076975000160",
    "Strix Yield FIC": "52792894000101",
    "Strix FIA": "52797717000100",
    "Strix D1 FIC FIRF CP": "52797894000196",
    "Crystal FICFIM CP": "12630565000131",
    "Strix Infra": "54995819000165",
}

dict_carteiras_excel = {
    "Strix FIA": "Backoffice - General\\Carteiras\\Strix FIA\\xlsx\\ResumoCarteira_STRIX FIA_",
    "Strix Yield Master": "Backoffice - General\\Carteiras\\Strix Yield Master\\xlsx\\ResumoCarteira_STRIX YIELD MASTER FIRF CP_",
    "Strix Yield FIC": "Backoffice - General\\Carteiras\\Strix Yield FIC\\xlsx\\ResumoCarteira_STRIX YIELD FC FIRF CRED PRIV_",
}


class gerencialFront:

    def __init__(self, manager_sql=None, funcoes_pytools=None):

        if manager_sql is None:
            self.manager_sql = SQL_Manager()
        else:
            self.manager_sql = manager_sql

        if funcoes_pytools is None:
            self.funcs_pytools = FuncoesPyTools(manager_sql=self.manager_sql)
        else:
            self.funcs_pytools = funcoes_pytools

        self.lista_classes_credito_privado = [
            "Debênture",
            "FIDC",
            "LF",
            "LFSC",
            "LFSN-PRE",
            "CCB",
            "CDB",
        ]
        self.taxa_adm_ano = 0.001 + 0.005  # (0.10%)

    def set_refdate(self, refdate):
        self.refdate = refdate

    def ipca_fidc_home_equity(self):

        refdate_menos_2m = self.refdate - relativedelta(months=2)

        str_mes_menos_dois = self.funcs_pytools.date_str_mes_ano(refdate_menos_2m)

        ipca_mes = self.manager_sql.select_dataframe(
            f"SELECT VALOR_MES FROM TB_IPCA_EFETIVO WHERE MES_ANO = '{str_mes_menos_dois}'"
        )

        if len(ipca_mes) > 0:
            ipca_mes = ipca_mes["VALOR_MES"][0]
        else:
            ipca_mes = 1

        self.ipca_2meses = ((1 + ipca_mes) ** 12) - 1

    def ajustes_manuais_carteira_trabalhada(self, df):

        df.loc[df["ATIVO"] == "SOLIS NOCTUA FC FIM", "Taxa"] = 0.03

        return df

    def carteira_trabalhada(self):

        def convert_cdi_mais(perc_papel, tipo_indexador):

            if tipo_indexador == "CDI +":
                return perc_papel
            elif tipo_indexador == "CDI %":
                papel = perc_papel
                rent_papel = papel * self.cdi_ano
                rent_cdi_mais = rent_papel - self.cdi_ano
                return rent_cdi_mais
            else:
                papel = perc_papel
                rent_papel = papel * self.cdi_ano
                rent_cdi_mais = rent_papel - self.cdi_ano
                return rent_cdi_mais

        def convert_perc_cdi(perc_papel, tipo_indexador, ativo):

            if tipo_indexador == "SELIC %":
                papel = perc_papel
                rent_papel = papel * self.selic_ano
                rent_papel_cdi = rent_papel / self.cdi_ano
                return rent_papel_cdi
            elif tipo_indexador == "SELIC +":
                papel = perc_papel
                rent_papel = self.selic_ano + papel
                rent_papel_cdi = rent_papel / self.cdi_ano
                return rent_papel_cdi
            elif tipo_indexador == "PRE":
                papel = perc_papel
                rent_papel = papel / self.cdi_ano
                return rent_papel
            elif (
                ativo
                in ["FIDC EMP HOME SN1", "FIDC EMP HOME SN4", "FIDC HOME EQUITY SR5"]
                and tipo_indexador == "IPCA +"
            ):
                papel = perc_papel
                rent_papel = self.ipca_2meses + papel
                rent_papel_cdi = rent_papel / self.cdi_ano
                return rent_papel_cdi
            else:
                return perc_papel

        # Realizar merges
        df_carteira = pd.merge(
            self.df_carteira, self.df_anbima_debentures, on="ATIVO", how="left"
        )
        df_carteira = pd.merge(df_carteira, self.df_cadastro, on="ATIVO", how="left")
        df_carteira = pd.merge(df_carteira, self.df_taxas_btg, on="ATIVO", how="left")
        df_carteira = pd.merge(
            df_carteira, self.df_risco_duration, on="ATIVO", how="left"
        )

        df_carteira.sort_values(by="FINANCEIRO_D0", ascending=False, inplace=True)

        # Calcular % Alocação
        df_carteira["% Alocação"] = round(
            df_carteira["FINANCEIRO_D0"] / self.pl_fundo * 100, 2
        )

        # Calcular Duration e Taxa
        df_carteira["Duration"] = df_carteira["DURATION_ANBIMA"].where(
            df_carteira["DURATION_ANBIMA"].notnull(), df_carteira["DURATION_RISCO"]
        )
        df_carteira["Duration"] = df_carteira.apply(
            lambda x: (
                x["Duration"]
                if pd.notnull(x["Duration"])
                else (1 if x["TIPO_ATIVO"] in ["Tit. Publicos", "Compromissada"] else 0)
            ),
            axis=1,
        )

        df_carteira["Taxa"] = df_carteira["TAXA_ANBIMA"].where(
            df_carteira["TAXA_ANBIMA"].notnull(), df_carteira["TAXA_BTG"]
        )
        df_carteira["Taxa"] = df_carteira["Taxa"].where(
            df_carteira["Taxa"].notnull(), df_carteira["TAXA_EMISSAO"]
        )

        df_carteira = self.ajustes_manuais_carteira_trabalhada(df_carteira)

        # Calcular AUX_TO_CDI e Carrego CDI +
        df_carteira["AUX_TO_CDI"] = df_carteira.apply(
            lambda x: (
                convert_perc_cdi(x["Taxa"], x["INDEXADOR"], x["ATIVO"])
                if pd.notnull(x["INDEXADOR"])
                else None
            ),
            axis=1,
        )
        df_carteira["Carrego CDI +"] = df_carteira.apply(
            lambda x: (
                convert_cdi_mais(x["AUX_TO_CDI"], x["INDEXADOR"])
                if pd.notnull(x["INDEXADOR"])
                else None
            ),
            axis=1,
        )

        # Converter para percentual e formatar
        df_carteira["Carrego CDI +"] = df_carteira["Carrego CDI +"].apply(
            lambda x: x * 100 if pd.notnull(x) else None
        )
        df_carteira["Taxa"] = df_carteira["Taxa"].apply(
            lambda x: x * 100 if pd.notnull(x) else None
        )

        self.df_carteira_all = df_carteira[
            [
                "TIPO_ATIVO",
                "ATIVO",
                "FINANCEIRO_D0",
                "EMISSOR",
                "DATA_VENCIMENTO",
                "INDEXADOR",
                "% Alocação",
                "Duration",
                "Taxa",
                "Carrego CDI +",
                "TAXA_EMISSAO",
            ]
        ].rename(
            columns={
                "TIPO_ATIVO": "Classe Ativo",
                "ATIVO": "Ativo",
                "FINANCEIRO_D0": "Exposição (R$)",
                "EMISSOR": "Emissor",
                "DATA_VENCIMENTO": "Vencimento",
                "INDEXADOR": "Indexador",
                "Taxa": "Carrego Original",
                "TAXA_EMISSAO": "Taxa de Emissão",
            }
        )

    def ajustes_manuais_resumo_classes(self, df):

        if "SOLIS NOCTUA FC FIM" in df.values:
            df.loc[df["Ativo"] == "SOLIS NOCTUA FC FIM", "Classe Ativo"] = (
                "Solis Coruja"
            )
            self.lista_classes_credito_privado.append("Solis Coruja")

        return df

    def resumo_classes(self):

        df_carteira_all = self.df_carteira_all.copy()

        self.df_carteira_all_classes_ajustada = self.ajustes_manuais_resumo_classes(
            df_carteira_all
        )

        classes = self.df_carteira_all_classes_ajustada["Classe Ativo"].unique()

        # Lista para acumular os resultados
        results = []

        for classe in classes:
            df_classe = self.df_carteira_all_classes_ajustada[
                self.df_carteira_all_classes_ajustada["Classe Ativo"] == classe
            ].copy()
            total_alocacao = df_classe["% Alocação"].sum()
            total = df_classe["Exposição (R$)"].sum()

            # Calcular as porcentagens e acumular os resultados
            df_classe["perc"] = df_classe.apply(
                lambda x: x["Exposição (R$)"] / total, axis=1
            )
            df_classe["perc_carrego_cdi"] = df_classe.apply(
                lambda x: x["perc"] * x["Carrego CDI +"], axis=1
            )
            df_classe["perc_duration"] = df_classe.apply(
                lambda x: x["perc"] * x["Duration"], axis=1
            )

            carrego_classe = round(df_classe["perc_carrego_cdi"].sum(), 2)
            duration_classe = int(round(df_classe["perc_duration"].sum(), 0))

            # Adicionar os resultados à lista
            results.append(
                {
                    "Classe Ativo": classe,
                    "Exposição (R$)": total,
                    "% Alocação": total_alocacao,
                    "Carrego CDI +": carrego_classe,
                    "Duration": duration_classe,
                }
            )

        # Converter a lista de resultados em um DataFrame
        self.df_resultados_classes = (
            pd.DataFrame(results)
            .sort_values(by="Exposição (R$)", ascending=False)
            .reset_index(drop=True)
        )

    def quebra_resumo_classes(self):

        # Para Crédito Privado
        self.df_cred_privado_classes = self.df_resultados_classes[
            self.df_resultados_classes["Classe Ativo"].isin(
                self.lista_classes_credito_privado
            )
        ].reset_index(drop=True)
        self.credito_privado_exposicao_total = self.df_cred_privado_classes[
            "Exposição (R$)"
        ].sum()
        self.credito_privado_alocacao_total = self.df_cred_privado_classes[
            "% Alocação"
        ].sum()

        df_carrego_valido = self.df_cred_privado_classes[
            self.df_cred_privado_classes["Carrego CDI +"] != 0
        ]
        df_duration_valido = self.df_cred_privado_classes[
            self.df_cred_privado_classes["Duration"] != 0
        ]

        self.credito_privado_carrego_total = (
            df_carrego_valido["Exposição (R$)"] * df_carrego_valido["Carrego CDI +"]
        ).sum() / df_carrego_valido["Exposição (R$)"].sum()
        self.credito_privado_duration_total = (
            df_duration_valido["Exposição (R$)"] * df_duration_valido["Duration"]
        ).sum() / df_duration_valido["Exposição (R$)"].sum()

        # Para Outras Classes
        self.df_outras_classes = self.df_resultados_classes[
            ~self.df_resultados_classes["Classe Ativo"].isin(
                self.lista_classes_credito_privado
            )
        ].reset_index(drop=True)
        self.outras_classes_exposicao_total = self.df_outras_classes[
            "Exposição (R$)"
        ].sum()
        self.outras_classes_alocacao_total = self.df_outras_classes["% Alocação"].sum()

        df_carrego_valido = self.df_outras_classes[
            (self.df_outras_classes["Carrego CDI +"] != 0)
            | (
                self.df_outras_classes["Classe Ativo"].isin(
                    ["Tit. Publicos", "Compromissada"]
                )
            )
        ]

        df_duration_valido = self.df_outras_classes[
            self.df_outras_classes["Duration"] != 0
        ]

        self.outras_classes_carrego_total = (
            df_carrego_valido["Exposição (R$)"] * df_carrego_valido["Carrego CDI +"]
        ).sum() / df_carrego_valido["Exposição (R$)"].sum()
        self.outras_classes_duration_total = (
            df_duration_valido["Exposição (R$)"] * df_duration_valido["Duration"]
        ).sum() / df_duration_valido["Exposição (R$)"].sum()

        # Para a Carteira Consolidada ex provisoes
        self.exposicao_total_antes_adm = self.df_resultados_classes[
            "Exposição (R$)"
        ].sum()
        self.alocacao_total_antes_adm = self.df_resultados_classes["% Alocação"].sum()

        df_carrego_valido = self.df_resultados_classes[
            (self.df_resultados_classes["Carrego CDI +"] != 0)
            | (
                self.df_resultados_classes["Classe Ativo"].isin(
                    ["Tit. Publicos", "Compromissada"]
                )
            )
        ]

        df_duration_valido = self.df_resultados_classes[
            self.df_resultados_classes["Duration"] != 0
        ]

        self.carrego_total_antes_adm = (
            df_carrego_valido["Exposição (R$)"] * df_carrego_valido["Carrego CDI +"]
        ).sum() / df_carrego_valido["Exposição (R$)"].sum()
        self.duration_total_antes_adm = (
            df_duration_valido["Exposição (R$)"] * df_duration_valido["Duration"]
        ).sum() / df_duration_valido["Exposição (R$)"].sum()

        # Carrego pela ADM
        self.carrego_total_pos_adm = (
            (1 + (self.carrego_total_antes_adm / 100)) / (1 + self.taxa_adm_ano) - 1
        ) * 100

    def format_resumo_classes(self):

        # Formatação das variáveis retiradas das DataFrames
        self.credito_privado_exposicao_total = (
            f"{self.credito_privado_exposicao_total:,.0f}"
        )
        self.credito_privado_alocacao_total = (
            f"{self.credito_privado_alocacao_total:,.2f}%"
        )
        self.credito_privado_carrego_total = (
            f"{self.credito_privado_carrego_total:,.2f}%"
            if self.credito_privado_carrego_total != 0
            else "Sem dado"
        )
        self.credito_privado_duration_total = (
            f"{self.credito_privado_duration_total:,.0f}"
            if self.credito_privado_duration_total != 0
            else "Sem dado"
        )

        self.outras_classes_exposicao_total = (
            f"{self.outras_classes_exposicao_total:,.0f}"
        )
        self.outras_classes_alocacao_total = (
            f"{self.outras_classes_alocacao_total:,.2f}%"
        )
        self.outras_classes_carrego_total = (
            f"{self.outras_classes_carrego_total:,.2f}%"
            if self.outras_classes_carrego_total != 0
            else "Sem dado"
        )
        self.outras_classes_duration_total = (
            f"{self.outras_classes_duration_total:,.0f}"
            if self.outras_classes_duration_total != 0
            else "Sem dado"
        )

        self.exposicao_total_antes_adm = f"{self.exposicao_total_antes_adm:,.0f}"
        self.alocacao_total_antes_adm = f"{self.alocacao_total_antes_adm:,.2f}%"
        self.carrego_total_antes_adm = (
            f"{self.carrego_total_antes_adm:,.2f}%"
            if self.carrego_total_antes_adm != 0
            else "Sem dado"
        )
        self.duration_total_antes_adm = (
            f"{self.duration_total_antes_adm:,.0f}"
            if self.duration_total_antes_adm != 0
            else "Sem dado"
        )

        self.carrego_total_pos_adm = f"{self.carrego_total_pos_adm:,.2f}%"

        # Formatação das DataFrames

        self.df_cred_privado_classes_formated = self.df_cred_privado_classes.copy()
        self.df_outras_classes_formated = self.df_outras_classes.copy()

        for df in [
            self.df_cred_privado_classes_formated,
            self.df_outras_classes_formated,
        ]:

            for coluna in ["% Alocação", "Carrego CDI +"]:
                df[coluna] = df[coluna].apply(
                    lambda x: f"{x:,.2f}%" if pd.notnull(x) else None
                )

            df["Exposição (R$)"] = df["Exposição (R$)"].apply(
                lambda x: f"{x:,.0f}" if pd.notnull(x) else None
            )
            df["Duration"] = df["Duration"].apply(
                lambda x: int(x) if pd.notnull(x) else None
            )

    def ajustes_manuais_resumo_indexadores(self, df):

        if "SELIC +" in df.values:
            df.loc[df["Indexador"] == "SELIC +", "Indexador"] = "CDI +"

        if "SELIC %" in df.values:
            df.loc[df["Indexador"] == "SELIC %", "Indexador"] = "CDI %"

        return df

    def resumo_indexadores(self):

        # df_carteira_indexadores = self.df_carteira_all.copy()

        df_carteira_indexadores = self.df_carteira_all_classes_ajustada.copy()

        df_carteira_indexadores = df_carteira_indexadores[
            df_carteira_indexadores["Classe Ativo"].isin(
                self.lista_classes_credito_privado
            )
        ].reset_index(drop=True)

        df_carteira_indexadores.loc[:, "Indexador"] = df_carteira_indexadores.apply(
            lambda x: x["Indexador"] if pd.notnull(x["Indexador"]) else "Sem cadastro",
            axis=1,
        )

        df_carteira_indexadores = self.ajustes_manuais_resumo_indexadores(
            df_carteira_indexadores
        )

        indexadores = df_carteira_indexadores["Indexador"].unique()

        # Lista para acumular os resultados
        results_indexadores = []

        # Iterar pelos indexadores
        for indexador in indexadores:
            df_indexador = df_carteira_indexadores[
                df_carteira_indexadores["Indexador"] == indexador
            ].copy()
            total_alocacao = df_indexador["% Alocação"].sum()
            total = df_indexador["Exposição (R$)"].sum()

            # Calcular as porcentagens e acumular os resultados
            df_indexador["perc"] = df_indexador.apply(
                lambda x: x["Exposição (R$)"] / total, axis=1
            )
            df_indexador["perc_carrego_cdi"] = df_indexador.apply(
                lambda x: x["perc"] * x["Carrego CDI +"], axis=1
            )
            df_indexador["perc_duration"] = df_indexador.apply(
                lambda x: x["perc"] * x["Duration"], axis=1
            )

            carrego_indexador = df_indexador["perc_carrego_cdi"].sum()
            duration_indexador = df_indexador["perc_duration"].sum()

            # Adicionar os resultados à lista
            results_indexadores.append(
                {
                    "Indexador": indexador,
                    "Exposição (R$)": total,
                    "% Alocação": total_alocacao,
                    "Carrego CDI +": carrego_indexador,
                    "Duration": duration_indexador,
                }
            )

        # Converter a lista de resultados em um DataFrame
        self.df_resultados_indexadores = (
            pd.DataFrame(results_indexadores)
            .sort_values(by="Exposição (R$)", ascending=False)
            .reset_index(drop=True)
        )

    def format_resumo_indexadores(self):

        # Formatação das DataFrames
        self.df_resultados_indexadores_formated = self.df_resultados_indexadores.copy()

        for coluna in ["% Alocação", "Carrego CDI +"]:
            self.df_resultados_indexadores_formated[coluna] = (
                self.df_resultados_indexadores_formated[coluna].apply(
                    lambda x: f"{x:,.2f}%" if pd.notnull(x) else None
                )
            )

        self.df_resultados_indexadores_formated["Exposição (R$)"] = (
            self.df_resultados_indexadores_formated["Exposição (R$)"].apply(
                lambda x: f"{x:,.0f}" if pd.notnull(x) else None
            )
        )
        self.df_resultados_indexadores_formated["Duration"] = (
            self.df_resultados_indexadores_formated["Duration"].apply(
                lambda x: int(x) if pd.notnull(x) else None
            )
        )

    def base_debentures(self):

        df_debentures = (
            self.df_carteira_all[self.df_carteira_all["Classe Ativo"] == "Debênture"]
            .copy()
            .reset_index(drop=True)
        )
        df_debentures = df_debentures[
            [
                "Emissor",
                "Ativo",
                "Indexador",
                "Exposição (R$)",
                "% Alocação",
                "Taxa de Emissão",
                "Carrego Original",
                "Carrego CDI +",
                "Duration",
                "Vencimento",
            ]
        ]
        df_debentures["Taxa de Emissão"] = df_debentures["Taxa de Emissão"].apply(
            lambda x: x * 100 if x != 0 else None
        )

        emissores = (
            df_debentures[["Emissor", "Exposição (R$)"]]
            .groupby("Emissor")
            .sum()
            .sort_values("Exposição (R$)", ascending=False)
            .reset_index(drop=False)
        )
        emissores = emissores["Emissor"].unique()

        emissores_debentures = {}
        for emissor in emissores:
            aux_df_emissor = df_debentures[df_debentures["Emissor"] == emissor].copy()
            aux_df_emissor.loc[:, "aux_carrego"] = aux_df_emissor["Carrego CDI +"] * (
                aux_df_emissor["Exposição (R$)"]
                / aux_df_emissor["Exposição (R$)"].sum()
            )
            aux_df_emissor.loc[:, "aux_duration"] = aux_df_emissor["Duration"] * (
                aux_df_emissor["Exposição (R$)"]
                / aux_df_emissor["Exposição (R$)"].sum()
            )
            aux_df_emissor = (
                aux_df_emissor[
                    [
                        "Emissor",
                        "Exposição (R$)",
                        "% Alocação",
                        "aux_carrego",
                        "aux_duration",
                    ]
                ]
                .groupby("Emissor")
                .sum()
                .reset_index(drop=False)
            )
            emissores_debentures[emissor] = [
                aux_df_emissor["Exposição (R$)"].values[0],
                aux_df_emissor["% Alocação"].values[0],
                aux_df_emissor["aux_carrego"].values[0],
                aux_df_emissor["aux_duration"].values[0],
            ]

        df_debentures["Exposição (R$)"] = df_debentures["Exposição (R$)"].apply(
            lambda x: f"{x:,.0f}"
        )
        df_debentures["Duration"] = df_debentures["Duration"].apply(
            lambda x: int(x) if pd.notnull(x) else None
        )
        for coluna in [
            "% Alocação",
            "Carrego Original",
            "Carrego CDI +",
            "Taxa de Emissão",
        ]:
            df_debentures[coluna] = df_debentures[coluna].apply(
                lambda x: f"{x:,.2f}%" if pd.notnull(x) else None
            )

        self.df_debentures = df_debentures
        self.emissores_debentures = emissores_debentures

    def base_lfs(self):

        df_letras_financeiras = (
            self.df_carteira_all[
                (self.df_carteira_all["Classe Ativo"] == "LF")
                | (self.df_carteira_all["Classe Ativo"] == "LFSC")
                | (self.df_carteira_all["Classe Ativo"] == "LFSN-PRE")
            ]
            .copy()
            .reset_index(drop=True)
        )
        df_letras_financeiras = df_letras_financeiras[
            [
                "Emissor",
                "Ativo",
                "Indexador",
                "Exposição (R$)",
                "% Alocação",
                "Taxa de Emissão",
                "Carrego Original",
                "Carrego CDI +",
                "Duration",
                "Vencimento",
            ]
        ]
        df_letras_financeiras["Taxa de Emissão"] = df_letras_financeiras[
            "Taxa de Emissão"
        ].apply(lambda x: x * 100 if x != 0 else None)

        emissores = (
            df_letras_financeiras[["Emissor", "Exposição (R$)"]]
            .groupby("Emissor")
            .sum()
            .sort_values("Exposição (R$)", ascending=False)
            .reset_index(drop=False)
        )
        emissores = emissores["Emissor"].unique()

        emissores_lfs = {}
        for emissor in emissores:
            aux_df_emissor = df_letras_financeiras[
                df_letras_financeiras["Emissor"] == emissor
            ].copy()
            aux_df_emissor.loc[:, "aux_carrego"] = aux_df_emissor["Carrego CDI +"] * (
                aux_df_emissor["Exposição (R$)"]
                / aux_df_emissor["Exposição (R$)"].sum()
            )
            aux_df_emissor.loc[:, "aux_duration"] = aux_df_emissor["Duration"] * (
                aux_df_emissor["Exposição (R$)"]
                / aux_df_emissor["Exposição (R$)"].sum()
            )
            aux_df_emissor = (
                aux_df_emissor[
                    [
                        "Emissor",
                        "Exposição (R$)",
                        "% Alocação",
                        "aux_carrego",
                        "aux_duration",
                    ]
                ]
                .groupby("Emissor")
                .sum()
                .reset_index(drop=False)
            )
            emissores_lfs[emissor] = [
                aux_df_emissor["Exposição (R$)"].values[0],
                aux_df_emissor["% Alocação"].values[0],
                aux_df_emissor["aux_carrego"].values[0],
                aux_df_emissor["aux_duration"].values[0],
            ]

        df_letras_financeiras["Exposição (R$)"] = df_letras_financeiras[
            "Exposição (R$)"
        ].apply(lambda x: f"{x:,.0f}")
        df_letras_financeiras["Duration"] = df_letras_financeiras["Duration"].apply(
            lambda x: int(x) if pd.notnull(x) else None
        )
        for coluna in [
            "% Alocação",
            "Carrego Original",
            "Carrego CDI +",
            "Taxa de Emissão",
        ]:
            df_letras_financeiras[coluna] = df_letras_financeiras[coluna].apply(
                lambda x: f"{x:,.2f}%" if pd.notnull(x) else None
            )

        self.df_letras_financeiras = df_letras_financeiras
        self.emissores_lfs = emissores_lfs

    def base_fidcs(self):

        df_fidcs = (
            self.df_carteira_all[self.df_carteira_all["Classe Ativo"] == "FIDC"]
            .copy()
            .reset_index(drop=True)
        )
        df_fidcs = df_fidcs[
            [
                "Emissor",
                "Ativo",
                "Indexador",
                "Exposição (R$)",
                "% Alocação",
                "Taxa de Emissão",
                "Carrego Original",
                "Carrego CDI +",
                "Duration",
                "Vencimento",
            ]
        ]
        df_fidcs["Taxa de Emissão"] = df_fidcs["Taxa de Emissão"].apply(
            lambda x: x * 100 if x != 0 else None
        )

        emissores = (
            df_fidcs[["Emissor", "Exposição (R$)"]]
            .groupby("Emissor")
            .sum()
            .sort_values("Exposição (R$)", ascending=False)
            .reset_index(drop=False)
        )
        emissores = emissores["Emissor"].unique()

        emissores_fidcs = {}
        for emissor in emissores:
            aux_df_emissor = df_fidcs[df_fidcs["Emissor"] == emissor].copy()
            aux_df_emissor.loc[:, "aux_carrego"] = aux_df_emissor["Carrego CDI +"] * (
                aux_df_emissor["Exposição (R$)"]
                / aux_df_emissor["Exposição (R$)"].sum()
            )
            aux_df_emissor.loc[:, "aux_duration"] = aux_df_emissor["Duration"] * (
                aux_df_emissor["Exposição (R$)"]
                / aux_df_emissor["Exposição (R$)"].sum()
            )
            aux_df_emissor = (
                aux_df_emissor[
                    [
                        "Emissor",
                        "Exposição (R$)",
                        "% Alocação",
                        "aux_carrego",
                        "aux_duration",
                    ]
                ]
                .groupby("Emissor")
                .sum()
                .reset_index(drop=False)
            )
            emissores_fidcs[emissor] = [
                aux_df_emissor["Exposição (R$)"].values[0],
                aux_df_emissor["% Alocação"].values[0],
                aux_df_emissor["aux_carrego"].values[0],
                aux_df_emissor["aux_duration"].values[0],
            ]

        df_fidcs["Exposição (R$)"] = df_fidcs["Exposição (R$)"].apply(
            lambda x: f"{x:,.0f}"
        )
        df_fidcs["Duration"] = df_fidcs["Duration"].apply(
            lambda x: int(x) if pd.notnull(x) else None
        )
        for coluna in [
            "% Alocação",
            "Carrego Original",
            "Carrego CDI +",
            "Taxa de Emissão",
        ]:
            df_fidcs[coluna] = df_fidcs[coluna].apply(
                lambda x: f"{x:,.2f}%" if pd.notnull(x) else None
            )

        self.df_fidcs = df_fidcs
        self.emissores_fidcs = emissores_fidcs

    def base_df_classes_to_fig(self):

        df = self.df_resultados_classes[["Classe Ativo", "Exposição (R$)"]].copy()
        df = df.groupby("Classe Ativo").sum().reset_index()

        self.df_to_fig_classes = df

    def base_df_indexadores_to_fig(self):

        df = self.df_resultados_indexadores[["Indexador", "Exposição (R$)"]].copy()
        df.loc[:, "Indexador"] = df.apply(
            lambda x: x["Indexador"] if pd.notnull(x["Indexador"]) else "Sem cadastro",
            axis=1,
        )
        df = df.groupby("Indexador").sum().reset_index()

        self.df_to_fig_indexador = df

    def puxa_bases(self):

        self.df_cadastro = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT ATIVO, EMISSOR, TAXA_EMISSAO/100 AS TAXA_EMISSAO, GESTOR, DATA_VENCIMENTO, INDEXADOR "
            f"FROM TB_CADASTRO_ATIVOS WHERE TIPO_ATIVO NOT IN ('Provisões & Despesas', 'Ações BR', 'Bonds', 'CD', 'TIPS')"
        )

        self.df_carteira = self.manager_sql.select_dataframe(
            f"SELECT TIPO_ATIVO, ATIVO, FINANCEIRO_D0 FROM TB_CARTEIRAS "
            f"WHERE REFDATE = '{self.funcs_pytools.convert_data_sql(self.refdate)}' "
            f"AND FUNDO = 'Strix Yield Master' AND TIPO_ATIVO NOT IN ('Provisões & Despesas', 'Ajuste Cisão') AND FINANCEIRO_D0 <> 0"
        )

        self.df_anbima_debentures = self.manager_sql.select_dataframe(
            f"SELECT COD_ATIVO AS ATIVO, TAXA_INDICATIVA/100 AS TAXA_ANBIMA, ROUND(DURATION, 0) AS DURATION_ANBIMA "
            f"FROM TB_ANBIMA_DEBENTURES WHERE REFDATE = '{self.funcs_pytools.convert_data_sql(self.refdate)}'"
        )

        self.df_taxas_btg = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT ATIVO, TAXA AS TAXA_BTG FROM TB_PRECOS "
            f"WHERE REFDATE = '{self.funcs_pytools.convert_data_sql(self.refdate)}' AND FONTE = 'BTG' AND TAXA IS NOT NULL"
        )

        self.df_risco_duration = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT ATIVO, DURATION AS DURATION_RISCO FROM TB_RISCO_DURATION "
            f"WHERE REFDATE = '{self.funcs_pytools.convert_data_sql(self.refdate)}'"
        )

        self.pl_fundo = self.manager_sql.select_dataframe(
            f"SELECT PATRIMONIO_LIQUIDO FROM TB_XML_CARTEIRAS_HEADER "
            f"WHERE REFDATE = '{self.funcs_pytools.convert_data_sql(self.refdate)}' "
            f"AND FUNDO = 'STRIX YIELD MASTER F'"
        )["PATRIMONIO_LIQUIDO"][0]

        self.cdi_ano = self.manager_sql.select_dataframe(
            f"SELECT VALOR_ANO FROM TB_INDEXADORES WHERE REFDATE = '{self.funcs_pytools.convert_data_sql(self.refdate)}' "
            f"AND INDEXADOR = 'CDI'"
        )["VALOR_ANO"][0]

        self.selic_ano = self.manager_sql.select_dataframe(
            f"SELECT VALOR_ANO FROM TB_INDEXADORES WHERE REFDATE = '{self.funcs_pytools.convert_data_sql(self.refdate)}' "
            f"AND INDEXADOR = 'SELIC'"
        )["VALOR_ANO"][0]

    def run(self):

        self.puxa_bases()

        # Run processos quadros de resumo
        self.ipca_fidc_home_equity()
        self.carteira_trabalhada()
        self.resumo_classes()
        self.quebra_resumo_classes()
        self.format_resumo_classes()

        self.resumo_indexadores()
        self.format_resumo_indexadores()

        self.base_df_classes_to_fig()
        self.base_df_indexadores_to_fig()

        # Run processos quadros de detalhamento dos ativos
        self.base_debentures()
        self.base_lfs()
        self.base_fidcs()


class extratoContaCorrenteFundos:

    def __init__(self, manager_sql=None):

        self.manager_sql = manager_sql

    def set_refdate(self, refdate: date, dmenos: date):

        self.refdate = refdate
        self.dmenos = dmenos

    def base_extratos_fundos(self):

        df_all = pd.DataFrame()

        df_btg_cc = self.manager_sql.select_dataframe(
            f"SELECT REFDATE, FUNDO, HISTORICO, OBS, CREDITO, DEBITO, BALANCO AS SALDO FROM TB_BASE_BTG_EXTRATO_CONTA_CORRENTE "
            f"WHERE REFDATE <= '{self.refdate}' AND REFDATE >= '{self.dmenos}' ORDER BY FUNDO, REFDATE, INDEX_BTG_ORDEM"
        )

        df_all = pd.concat([df_all, df_btg_cc])

        df_xml_cc = self.manager_sql.select_dataframe(
            f"SELECT REFDATE, FUNDO, HISTORICO, USUARIO AS OBS, VALOR FROM TB_XML_CONTA_CORRENTE "
            f"WHERE REFDATE <= '{self.refdate}' AND REFDATE >= '{self.dmenos}' ORDER BY FUNDO, REFDATE, HISTORICO"
        )

        df_xml_cc["CREDITO"] = df_xml_cc["VALOR"].apply(lambda x: x if x > 0 else 0)
        df_xml_cc["DEBITO"] = df_xml_cc["VALOR"].apply(lambda x: x if x < 0 else 0)
        df_xml_cc.drop(columns=["VALOR"], inplace=True)

        for fundo in df_xml_cc["FUNDO"].unique():
            df_fundo = df_xml_cc[df_xml_cc["FUNDO"] == fundo].copy()
            df_fundo["SALDO"] = df_fundo["CREDITO"] + df_fundo["DEBITO"]
            df_fundo["SALDO"] = df_fundo["SALDO"].cumsum()
            df_all = pd.concat([df_all, df_fundo])

        df_all.reset_index(drop=True, inplace=True)
        df_all["OBS"] = df_all["OBS"].apply(lambda x: x if x else None)

        self.df_cc_all = df_all.copy()


class movimentacaoPassivos:

    def __init__(self, manager_sql=None):

        if manager_sql is None:
            self.manager_sql = SQL_Manager()
        else:
            self.manager_sql = manager_sql

    def set_refdate(self, refdate: date, dmenos: date):

        self.refdate = refdate
        self.dmenos = dmenos

    def base_movimentacao_passivos(self):

        df = self.manager_sql.select_dataframe(
            f"SELECT * FROM TB_BASE_BTG_MOVIMENTACAO_PASSIVO "
            f"WHERE DATA_OPERACAO <= '{self.refdate}' AND DATA_OPERACAO >= '{self.dmenos}' "
            f"ORDER BY FUNDO, DATA_OPERACAO, DATA_IMPACTO"
        )

        df = df[
            [
                "FUNDO",
                "DATA_OPERACAO",
                "DATA_COTIZACAO",
                "DATA_IMPACTO",
                "COTISTA",
                "TIPO_OPERACAO",
                "VALOR",
                "QTD_COTAS",
                "DESC_TIPO_OPERACAO",
                "STATUS_OPERACAO",
                "PLATAFORMA",
                "OFFICER",
            ]
        ]

        df.rename(
            columns={
                "FUNDO": "Fundo",
                "DATA_OPERACAO": "Data Operação",
                "DATA_COTIZACAO": "Data Cotização",
                "DATA_IMPACTO": "Data Liquidação",
                "COTISTA": "Cotista",
                "TIPO_OPERACAO": "Operação",
                "VALOR": "Financeiro",
                "QTD_COTAS": "Qtd. Cotas",
                "DESC_TIPO_OPERACAO": "Desc. Operação",
                "STATUS_OPERACAO": "Status",
                "PLATAFORMA": "Plataforma",
                "OFFICER": "Officer",
            },
            inplace=True,
        )

        self.df_mov_passivos = df.copy()


class passivosCotizar:

    def __init__(self, manager_sql=None):

        if manager_sql is None:
            self.manager_sql = SQL_Manager()
        else:
            self.manager_sql = manager_sql

    def set_refdate(self, refdate: date, dmenos: date):

        self.refdate = refdate
        self.dmenos = dmenos

    def base_passivos_cotizar(self):

        df_cotas = self.manager_sql.select_dataframe(
            f"SELECT d.REFDATE, d.FUNDO, d.COTA_LIQUIDA "
            f"FROM TB_DADOS_FUNDOS d "
            f"INNER JOIN ("
            f"SELECT FUNDO, MAX(REFDATE) AS MAX_REFDATE "
            f"FROM TB_DADOS_FUNDOS "
            f"GROUP BY FUNDO"
            f") m ON d.FUNDO = m.FUNDO AND d.REFDATE = m.MAX_REFDATE;"
        ).rename(columns={"FUNDO": "FUNDO_SUPORTE"})

        df_cotas["FUNDO"] = df_cotas["FUNDO_SUPORTE"].map(dict_aux_dados_fundos)
        df_cotas = df_cotas[df_cotas["FUNDO"].notnull()]
        dict_cotas = df_cotas.set_index("FUNDO")["COTA_LIQUIDA"].to_dict()

        # ---------------------------------------------------

        df = self.manager_sql.select_dataframe(
            f"SELECT * FROM TB_BASE_BTG_MOVIMENTACAO_PASSIVO "
            f"WHERE TIPO_OPERACAO = 'RESGATE' AND DATA_COTIZACAO >= '{self.refdate}' "
            f"ORDER BY FUNDO, DATA_OPERACAO, DATA_IMPACTO"
        )

        df = df[
            [
                "FUNDO",
                "DATA_OPERACAO",
                "DATA_COTIZACAO",
                "DATA_IMPACTO",
                "COTISTA",
                "TIPO_OPERACAO",
                "VALOR",
                "QTD_COTAS",
                "DESC_TIPO_OPERACAO",
                "STATUS_OPERACAO",
                "PLATAFORMA",
                "OFFICER",
            ]
        ]

        df.rename(
            columns={
                "FUNDO": "Fundo",
                "DATA_OPERACAO": "Data Operação",
                "DATA_COTIZACAO": "Data Cotização",
                "DATA_IMPACTO": "Data Liquidação",
                "COTISTA": "Cotista",
                "TIPO_OPERACAO": "Operação",
                "VALOR": "Financeiro",
                "QTD_COTAS": "Qtd. Cotas",
                "DESC_TIPO_OPERACAO": "Desc. Operação",
                "STATUS_OPERACAO": "Status",
                "PLATAFORMA": "Plataforma",
                "OFFICER": "Officer",
            },
            inplace=True,
        )

        df["COTA_AUX"] = df["Fundo"].map(dict_cotas)

        df["Financeiro"] = df.apply(
            lambda x: (
                x["Qtd. Cotas"] * x["COTA_AUX"]
                if x["Desc. Operação"] == "RESGATE TOTAL"
                else x["Financeiro"]
            ),
            axis=1,
        )

        df.drop(columns=["COTA_AUX"], inplace=True)

        self.df_passivos_cotizar = df.copy()
