import os
from datetime import date

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from __init__ import append_paths
from matplotlib.ticker import FuncFormatter
from scipy.stats import norm

append_paths()

from tools.biblioteca_processos import capturaDados  # noqa: E402
from tools.db_helper import SQL_Manager  # noqa: E402
from tools.dictionaries_lists_library import (  # noqa: E402
    FixedDictionariesListsLibrary,
    SqlDictionariesLists,
)
from tools.py_tools import FuncoesPyTools  # noqa: E402

VERSION_APP = "2.0.2"
VERSION_REFDATE = "2024-07-15"
ENVIRONMENT = os.getenv("ENVIRONMENT")
SCRIPT_NAME = os.path.basename(__file__)

if ENVIRONMENT == "DEVELOPMENT":
    print(f"{SCRIPT_NAME.upper()} - {ENVIRONMENT} - {VERSION_APP} - {VERSION_REFDATE}")

# -----------------------------------------------------------------------


class enquadramentoCarteira:

    def __init__(self, manager_sql=None, funcoes_pytools=None):

        if manager_sql is None:
            self.manager_sql = SQL_Manager()
        else:
            self.manager_sql = manager_sql

        if funcoes_pytools is None:
            self.funcoes_pytools = FuncoesPyTools(self.manager_sql)
        else:
            self.funcoes_pytools = funcoes_pytools

        self.dict_limites_emissor = {
            "Instituição Financeira": 0.2,
            "Fundo de Investimento": None,
            "União federal": None,
            "Emissor Companhia Aberta ou assemelhada": 0.1,
        }

        self.dict_limites_modalidade = {
            "Debênture": 1,
            "Tit. Publicos": 1,
            "FIDC": 0.4,
            "LF": 1,
            "LFSC": 1,
            "LFSN-PRE": 1,
            "CCB": 1,
            "Compromissada": 1,
        }

    def set_refdate(self, refdate: date):

        self.refdate = refdate

    def formatar_valores(self, df):
        df_formated = df.copy()

        def format_value(value, column):
            if column == "Financeiro":
                return f"{value:,.0f}" if value != 0 else "-"
            elif column == "Exposição":
                return (
                    f"{value * 100:.2f}%" if pd.notnull(value) and value != 0 else "-"
                )
            elif column == "Limite Individual":
                return f"{value * 100:.0f}%" if pd.notnull(value) else "-"
            elif column == "Limite em Conjunto":
                return f"{value * 100:.0f}%" if pd.notnull(value) else "-"
            return value

        for col in df_formated.columns:
            df_formated[col] = df_formated[col].apply(lambda x: format_value(x, col))

        return df_formated

    def call_dados_yield_master(self):

        self.df_carteira_yield_master = self.manager_sql.select_dataframe(
            "SELECT REFDATE, FUNDO, TIPO_ATIVO, ATIVO, FINANCEIRO_D0 FROM TB_CARTEIRAS "
            f"WHERE REFDATE = '{self.refdate.strftime('%Y-%m-%d')}' "
            "AND FUNDO = 'STRIX YIELD MASTER' AND FINANCEIRO_D0 > 0.1"
        )

        self.pl_yield_master = self.manager_sql.select_dataframe(
            f"SELECT PATRIMONIO_LIQUIDO FROM TB_XML_CARTEIRAS_HEADER WHERE "
            f"REFDATE = '{self.refdate.strftime('%Y-%m-%d')}' AND FUNDO = 'STRIX YIELD MASTER F'"
        )["PATRIMONIO_LIQUIDO"].values[0]

    def call_suportes(self):

        self.dict_limites_modalidade_ativos_com_limite = {
            "Cotas de FICD e Companhias Fechadas": 0.4,
            "Cotas de FIDC": None,
            "Emissões de Companhias Fechadas": None,
            "FIF Destinados a Investidores Profissionais": 0.1,
            "Certificado de Recebíveis": 0.4,
            "Subtotal Não Padronizados": 0.1,
            "Cotas de FIDC Não Padronizados": None,
            "Certificados de Recebíveis DC NP": None,
            "Total": 0.4,
        }

        self.ordem_df_modalidade_ativos_com_limite = [
            "Cotas de FICD e Companhias Fechadas",
            "Cotas de FIDC",
            "Emissões de Companhias Fechadas",
            "FIF Destinados a Investidores Profissionais",
            "Certificado de Recebíveis",
            "Subtotal Não Padronizados",
            "Cotas de FIDC Não Padronizados",
            "Certificados de Recebíveis DC NP",
            "Total",
        ]

        self.lista_modalidade_ativos_com_limite = [
            "Cotas de FIDC",
            "Emissões de Companhias Fechadas",
            "FIF Destinados a Investidores Profissionais",
            "Certificado de Recebíveis",
            "Cotas de FIDC Não Padronizados",
            "Certificados de Recebíveis DC NP",
        ]

        self.dict_modalidade_ativos = (
            self.manager_sql.select_dataframe(
                "SELECT DISTINCT ATIVO, MODALIDADE_ENQUADRAMENTO FROM TB_CADASTRO_ATIVOS"
            )
            .set_index("ATIVO")["MODALIDADE_ENQUADRAMENTO"]
            .to_dict()
        )

        self.dict_cad_ativo = (
            self.manager_sql.select_dataframe(
                "SELECT DISTINCT ATIVO, EMISSOR FROM TB_CADASTRO_ATIVOS WHERE EMISSOR IS NOT NULL"
            )
            .set_index("ATIVO")["EMISSOR"]
            .to_dict()
        )

        self.df_cad_emissor = self.manager_sql.select_dataframe(
            "SELECT * FROM TB_CADASTRO_EMISSOR"
        )

        self.dict_limites_grupo_economico = {
            "Instituição Financeira": 0.2,
            "Emissor Companhia Aberta": 0.1,
            "Emissor Companhia Fechada": 0.05,
        }

        self.lista_tipo_emissores_com_limite = [
            "Emissor Companhia Aberta",
            "Emissor Companhia Fechada",
            "Instituição Financeira",
        ]

        self.dict_limites_emissores = {"BANCO BRADESCO S/A": 0.06}

    def call_enquadramento_modalidade_ativos_com_limite(self):

        df_carteira = self.df_carteira_yield_master

        df_carteira["MODALIDADE_ENQUADRAMENTO"] = df_carteira["ATIVO"].map(
            self.dict_modalidade_ativos
        )

        df_pl_modalidade_ativos = (
            df_carteira.groupby("MODALIDADE_ENQUADRAMENTO")["FINANCEIRO_D0"]
            .sum()
            .reset_index()
        )

        df_pl_modalidade_ativos["Exposição"] = (
            df_pl_modalidade_ativos["FINANCEIRO_D0"] / self.pl_yield_master
        )
        df_pl_modalidade_ativos["pl_fundo"] = self.pl_yield_master

        df_exposicao_com_limites = df_pl_modalidade_ativos[
            df_pl_modalidade_ativos["MODALIDADE_ENQUADRAMENTO"].isin(
                self.lista_modalidade_ativos_com_limite
            )
        ]
        df_exposicao_com_limites.reset_index(drop=True, inplace=True)

        lista_modalidades_com_limite_sem_posicao = list(
            set(self.lista_modalidade_ativos_com_limite) - set(df_exposicao_com_limites["MODALIDADE_ENQUADRAMENTO"])
        )

        if len(lista_modalidades_com_limite_sem_posicao) > 0:
            df_exposicao_com_limite_sem_posicao = pd.DataFrame(
                {
                    "MODALIDADE_ENQUADRAMENTO": lista_modalidades_com_limite_sem_posicao,
                    "FINANCEIRO_D0": 0,
                    "Exposição": 0,
                    "pl_fundo": self.pl_yield_master,
                }
            )
            df_exposicao_com_limites = pd.concat(
                [df_exposicao_com_limites, df_exposicao_com_limite_sem_posicao], axis=0
            )

        fin_cotas_fidc_e_companhias_fechadas = df_exposicao_com_limites[
            df_exposicao_com_limites["MODALIDADE_ENQUADRAMENTO"].isin(
                ["Cotas de FIDC", "Emissões de Companhias Fechadas"]
            )
        ]["FINANCEIRO_D0"].sum()

        exp_cotas_fidc_e_companhias_fechadas = (
            fin_cotas_fidc_e_companhias_fechadas / self.pl_yield_master
        )

        fin_subtotal_nao_padronizados = df_exposicao_com_limites[
            df_exposicao_com_limites["MODALIDADE_ENQUADRAMENTO"].isin(
                ["Cotas de FIDC Não Padronizados", "Certificados de Recebíveis DC NP"]
            )
        ]["FINANCEIRO_D0"].sum()

        exp_subtotal_nao_padronizados = (
            fin_subtotal_nao_padronizados / self.pl_yield_master
        )

        total_com_limites = df_exposicao_com_limites["FINANCEIRO_D0"].sum()
        exp_total_com_limites = total_com_limites / self.pl_yield_master

        df_subtotais = pd.DataFrame(
            {
                "MODALIDADE_ENQUADRAMENTO": [
                    "Cotas de FICD e Companhias Fechadas",
                    "Subtotal Não Padronizados",
                    "Total",
                ],
                "FINANCEIRO_D0": [
                    fin_cotas_fidc_e_companhias_fechadas,
                    fin_subtotal_nao_padronizados,
                    total_com_limites,
                ],
                "Exposição": [
                    exp_cotas_fidc_e_companhias_fechadas,
                    exp_subtotal_nao_padronizados,
                    exp_total_com_limites,
                ],
                "pl_fundo": [
                    self.pl_yield_master,
                    self.pl_yield_master,
                    self.pl_yield_master,
                ],
            }
        )

        df_exposicao_com_limites = pd.concat(
            [df_exposicao_com_limites, df_subtotais], axis=0
        )

        df_exposicao_com_limites.reset_index(drop=True, inplace=True)

        df_exposicao_com_limites["temp_order"] = df_exposicao_com_limites[
            "MODALIDADE_ENQUADRAMENTO"
        ].apply(lambda x: self.ordem_df_modalidade_ativos_com_limite.index(x))

        df_exposicao_com_limites = df_exposicao_com_limites.sort_values(
            by="temp_order"
        ).reset_index(drop=True)

        df_exposicao_com_limites.drop(columns=["temp_order", "pl_fundo"], inplace=True)

        df_exposicao_com_limites["Limite Individual"] = df_exposicao_com_limites[
            "MODALIDADE_ENQUADRAMENTO"
        ].map(self.dict_limites_modalidade_ativos_com_limite)

        df_exposicao_com_limites["Limite em Conjunto"] = np.nan

        df_exposicao_com_limites["Status Enquadramento"] = (
            df_exposicao_com_limites.apply(
                lambda x: (
                    "-"
                    if pd.isna(x["Limite Individual"])
                    else (
                        "Fora do Limite"
                        if x["Exposição"] > x["Limite Individual"]
                        else "Dentro do Limite"
                    )
                ),
                axis=1,
            )
        )

        substituicoes = {
            "Cotas de FIDC": "   - Cotas de FIDC",
            "Emissões de Companhias Fechadas": "    - Emissões de Companhias Fechadas",
            "Cotas de FIDC Não Padronizados": "    - Cotas de FIDC Não Padronizados",
            "Certificados de Recebíveis DC NP": "    - Certificados de Recebíveis DC NP",
        }

        df_exposicao_com_limites["MODALIDADE_ENQUADRAMENTO"] = df_exposicao_com_limites[
            "MODALIDADE_ENQUADRAMENTO"
        ].replace(substituicoes)

        df_exposicao_com_limites.rename(
            columns={
                "MODALIDADE_ENQUADRAMENTO": "Modalidade Enquadramento",
                "FINANCEIRO_D0": "Financeiro",
            },
            inplace=True,
        )

        self.df_enquadramento_modalidade_ativos_com_limite = df_exposicao_com_limites

    def call_enquadramento_grupos_economicos_com_limite(self):

        df_carteira = self.df_carteira_yield_master.copy()

        df_carteira["EMISSOR"] = df_carteira["ATIVO"].map(self.dict_cad_ativo)

        df_carteira = df_carteira.merge(self.df_cad_emissor, on="EMISSOR", how="left")

        df_carteira["Exposição"] = df_carteira["FINANCEIRO_D0"] / self.pl_yield_master

        df_carteira = df_carteira[
            df_carteira["TIPO_EMISSOR"].isin(self.lista_tipo_emissores_com_limite)
        ]

        df_carteira["Limite Individual"] = df_carteira["TIPO_EMISSOR"].map(
            self.dict_limites_grupo_economico
        )

        df_carteira = (
            df_carteira[
                [
                    "TIPO_EMISSOR",
                    "GRUPO_ECONOMICO",
                    "Limite Individual",
                    "FINANCEIRO_D0",
                    "Exposição",
                ]
            ]
            .groupby(["TIPO_EMISSOR", "GRUPO_ECONOMICO", "Limite Individual"])
            .sum()
            .reset_index()
        )

        df_carteira["Status Enquadramento"] = np.where(
            df_carteira["Exposição"] > df_carteira["Limite Individual"],
            "Fora do Limite",
            "Dentro do Limite",
        )

        df_carteira.rename(
            columns={
                "GRUPO_ECONOMICO": "Grupo Econômico",
                "FINANCEIRO_D0": "Financeiro",
            },
            inplace=True,
        )

        self.df_enquadramento_grupos_economicos_com_limite = df_carteira.copy()

        self.df_instituicoes_financeiras = (
            df_carteira[df_carteira["TIPO_EMISSOR"] == "Instituição Financeira"][
                [
                    "Grupo Econômico",
                    "Financeiro",
                    "Exposição",
                    "Limite Individual",
                    "Status Enquadramento",
                ]
            ]
            .sort_values("Exposição", ascending=False)
            .reset_index(drop=True)
            .rename(columns={"Grupo Econômico": "Instituições Financeiras"})
        )

        self.df_companhias_abertas = (
            df_carteira[df_carteira["TIPO_EMISSOR"] == "Emissor Companhia Aberta"][
                [
                    "Grupo Econômico",
                    "Financeiro",
                    "Exposição",
                    "Limite Individual",
                    "Status Enquadramento",
                ]
            ]
            .sort_values("Exposição", ascending=False)
            .reset_index(drop=True)
            .rename(columns={"Grupo Econômico": "Companhias Abertas"})
        )

        self.df_companhias_fechadas = (
            df_carteira[df_carteira["TIPO_EMISSOR"] == "Emissor Companhia Fechada"][
                [
                    "Grupo Econômico",
                    "Financeiro",
                    "Exposição",
                    "Limite Individual",
                    "Status Enquadramento",
                ]
            ]
            .sort_values("Exposição", ascending=False)
            .reset_index(drop=True)
            .rename(columns={"Grupo Econômico": "Companhias Fechadas"})
        )

    def call_enquadramento_emissores(self):

        df_carteira = self.df_carteira_yield_master.copy()
        df_carteira["EMISSOR"] = df_carteira["ATIVO"].map(self.dict_cad_ativo)
        df_carteira = df_carteira[~df_carteira["EMISSOR"].isnull()]
        df_carteira = df_carteira[
            (df_carteira["TIPO_ATIVO"] != "Compromissada") & (df_carteira["TIPO_ATIVO"] != "Tit. Publicos")
        ]
        df_carteira["Exposição"] = df_carteira["FINANCEIRO_D0"] / self.pl_yield_master

        df_carteira = (
            df_carteira[["EMISSOR", "TIPO_ATIVO", "FINANCEIRO_D0", "Exposição"]]
            .groupby(["EMISSOR", "TIPO_ATIVO"])
            .sum()
            .sort_values("Exposição", ascending=False)
            .reset_index()
        )

        df_carteira["Limite Individual"] = df_carteira["EMISSOR"].map(
            lambda x: self.dict_limites_emissores.get(x, 0.05)
        )
        df_carteira["Status Enquadramento"] = np.where(
            df_carteira["Exposição"] > df_carteira["Limite Individual"],
            "Fora do Limite",
            "Dentro do Limite",
        )

        df_carteira.rename(
            columns={
                "EMISSOR": "Emissor",
                "FINANCEIRO_D0": "Financeiro",
                "TIPO_ATIVO": "Classe Ativo",
            },
            inplace=True,
        )

        self.df_enquandramento_emissores = df_carteira.copy()


class dadosRiscoFundos:

    def __init__(self, strFundo: str = None, manager_sql=None):

        if manager_sql is None:
            self.manager_sql = SQL_Manager()
        else:
            self.manager_sql = manager_sql

        self.fundo = strFundo

        self.dict_suporte = {
            "IMABAJUST": "IPCA + Yield IMA-B",
            "CDI": "CDI",
            "STRIX YIELD MASTER F": "CDI",
            "STRIX FIA": "IMABAJUST",
        }

    def set_refdate(self, refdate: date):

        self.refdate = refdate

    def set_suporte_dados(self):

        self.df_suporte_dados = self.manager_sql.select_dataframe(
            f"SELECT REFDATE, COTA_LIQUIDA, VAR_COTA_DIA/100 AS VAR_COTA_DIA "
            "FROM TB_BASE_BTG_PERFORMANCE_COTA "
            f"WHERE FUNDO = '{self.fundo}' AND REFDATE <= '{self.refdate}' "
            f"ORDER BY REFDATE"
        )

    def to_percent(self, y, position):
        s = f"{100 * y:.1f}%"
        return s

    def df_drawdown_fundo(self):

        df_dados = self.df_suporte_dados[["REFDATE", "COTA_LIQUIDA"]].copy()

        from collections import defaultdict

        lista_cotas = df_dados.values.tolist()
        dicionario_cotas = dict(lista_cotas)
        maior_cota_por_dia = defaultdict(float)
        maior_cota = 0
        resultados = []

        for data in sorted(dicionario_cotas.keys()):
            cota_do_dia = dicionario_cotas[data]
            if cota_do_dia > maior_cota:
                maior_cota = cota_do_dia
            maior_cota_por_dia[data] = maior_cota
            drawdown = cota_do_dia / maior_cota - 1
            resultados.append((data, drawdown))

        df_resultados = pd.DataFrame(resultados, columns=["Data", "Drawdown"])

        return df_resultados

    def grafico_drawdown_fundo(self, tamanho_fig=(12, 6)):

        df_dados = self.df_drawdown_fundo()

        lista_dados = df_dados.values.tolist()

        datas = [row[0].strftime("%Y-%m-%d") for row in lista_dados]
        valores = [row[1] for row in lista_dados]

        plt.style.use("seaborn-v0_8-dark")

        plt.figure(figsize=tamanho_fig)
        plt.bar(datas, valores, color="DarkSlateGray")

        plt.title(f"{self.fundo} - Drawdown", fontsize=16, fontweight="bold")

        intervalo = int(len(datas) / 20)
        plt.xticks(
            ticks=np.arange(len(datas))[::intervalo],
            labels=[datas[i] for i in np.arange(len(datas))[::intervalo]],
            rotation=90,
        )  # Fonte maior nos ticks

        formatter = FuncFormatter(self.to_percent)
        plt.gca().yaxis.set_major_formatter(formatter)

        plt.grid(
            True, which="major", linestyle="--", linewidth=0.5, color="grey", axis="y"
        )

        plt.tight_layout()

        return plt

    def grafico_dispersao_x_normal(self, tamanho_fig=(12, 6)):

        df_dados = self.df_suporte_dados.copy()

        if df_dados["VAR_COTA_DIA"].iloc[0] == 0:
            df_dados = df_dados.drop(index=0).reset_index(drop=True)

        data = df_dados["VAR_COTA_DIA"].values.tolist()

        # Calculando a média e o desvio padrão das rentabilidades do fundo
        media = np.mean(data)
        desvio_padrao = np.std(data)

        # Criando uma distribuição normal com base na média e no desvio padrão
        distribuicao_normal = norm(media, desvio_padrao)

        # Gerando valores para a distribuição normal
        x = np.linspace(min(data), max(data), 100)
        y = distribuicao_normal.pdf(x)

        plt.style.use("seaborn-v0_8-dark")

        plt.figure(figsize=tamanho_fig)  # Definindo o tamanho do gráfico
        plt.hist(
            data,
            bins=5,
            density=True,
            alpha=0.6,
            color="green",
            label="Rentabilidades Fundo",
        )
        plt.plot(x, y, "k--", label="Distribuição Normal")

        # Adicionando legenda e título ao gráfico
        plt.legend()
        plt.title(
            f"{self.fundo} - Rentabilidade vs. Distribuição Normal",
            fontsize=16,
            fontweight="bold",
        )
        plt.xlabel("Rentabilidade")
        plt.ylabel("Densidade de Probabilidade")
        plt.grid(
            True, which="major", linestyle="--", linewidth=0.5, color="grey", axis="y"
        )

        plt.tight_layout()

        return plt

    def df_volatilidade_anualizada(self, window=21):

        df = self.df_suporte_dados.copy()

        if df["VAR_COTA_DIA"].iloc[0] == 0:
            df = df.drop(index=0).reset_index(drop=True)

        df["volatilidade"] = (
            df["VAR_COTA_DIA"].rolling(window=window, min_periods=1).std()
        )
        df["volatilidade_anualizada"] = df["volatilidade"] * np.sqrt(252)
        df = df[["REFDATE", "volatilidade_anualizada"]]

        return df

    def grafico_volatilidade(self, tamanho_fig=(12, 6), janela=21):

        df_volatiliadde = self.df_volatilidade_anualizada(window=janela)

        dados_fundo = df_volatiliadde.values.tolist()
        # Unpacking dos dados
        datas_fundo, volatilidade = zip(*dados_fundo)

        # Convertendo datas para formato legível se necessário
        datas_fundo = [
            data.strftime("%Y-%m-%d") if not isinstance(data, str) else data
            for data in datas_fundo
        ]

        # Usar um estilo predefinido
        plt.style.use("seaborn-v0_8-dark")  # Estilo para o gráfico

        plt.figure(figsize=tamanho_fig)

        # Plotando fundo
        plt.plot(
            datas_fundo, volatilidade, label="Fundo", color="DarkSlateGray", linewidth=1
        )

        plt.title(
            f"{self.fundo} - Volatilidade 21d Anualizada",
            fontsize=16,
            fontweight="bold",
        )  # Título com fonte maior e em negrito

        plt.ylabel("Volatilidade 21d anualizada")

        formatter = FuncFormatter(self.to_percent)
        plt.gca().yaxis.set_major_formatter(formatter)

        intervalo = int(len(datas_fundo) / 20)
        plt.xticks(
            ticks=np.arange(len(datas_fundo))[::intervalo],
            labels=[datas_fundo[i] for i in np.arange(len(datas_fundo))[::intervalo]],
            rotation=90,
        )  # Fonte maior nos ticks
        plt.xticks(rotation=90)

        plt.grid(
            True, which="major", linestyle="--", linewidth=0.5, color="grey", axis="y"
        )

        # Ajusta layout para não cortar conteúdo
        plt.tight_layout()

        # Adicionando legenda
        plt.legend()

        return plt

    def rentabilidade_acumulada_fundo(self):

        df_fundo = self.df_suporte_dados[["REFDATE", "COTA_LIQUIDA"]].copy()

        df_fundo["REFDATE"] = pd.to_datetime(df_fundo["REFDATE"])
        df_fundo["RENTABILIDADE_ACUMULADA"] = (
            df_fundo["COTA_LIQUIDA"] / df_fundo["COTA_LIQUIDA"].iloc[0] - 1
        )
        df_fundo = df_fundo[["REFDATE", "RENTABILIDADE_ACUMULADA"]]
        return df_fundo

    def rentabilidade_acumulada_benchmark(self):

        df_benchmark = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT REFDATE, COTA_INDEXADOR FROM TB_INDEXADORES "
            f"WHERE REFDATE >= (SELECT MIN(REFDATE) FROM TB_BASE_BTG_PERFORMANCE_COTA "
            f"WHERE FUNDO = '{self.fundo}') "
            f"AND REFDATE <= '{self.refdate}' "
            f"AND INDEXADOR = '{self.dict_suporte[self.fundo]}' "
            f"ORDER BY REFDATE"
        )
        df_benchmark["REFDATE"] = pd.to_datetime(df_benchmark["REFDATE"])
        df_benchmark["RENTABILIDADE_ACUMULADA"] = (
            df_benchmark["COTA_INDEXADOR"] / df_benchmark["COTA_INDEXADOR"].iloc[0] - 1
        )
        df_benchmark = df_benchmark[["REFDATE", "RENTABILIDADE_ACUMULADA"]]
        return df_benchmark

    def grafico_rentabilidade_fundo_x_benchmark(self, tamanho_fig=(12, 6)):

        df_fundo = self.rentabilidade_acumulada_fundo()
        dados_fundo = df_fundo.values.tolist()

        df_benchmark = self.rentabilidade_acumulada_benchmark()
        dados_benchmark = df_benchmark.values.tolist()

        # Unpacking dos dados
        datas_fundo, rentabilidade_fundo = zip(*dados_fundo)
        datas_benchmark, rentabilidade_benchmark = zip(*dados_benchmark)

        # Convertendo datas para formato legível se necessário
        datas_fundo = [
            data.strftime("%Y-%m-%d") if not isinstance(data, str) else data
            for data in datas_fundo
        ]
        datas_benchmark = [
            data.strftime("%Y-%m-%d") if not isinstance(data, str) else data
            for data in datas_benchmark
        ]

        # Usar um estilo predefinido
        plt.style.use("seaborn-v0_8-dark")  # Estilo para o gráfico

        plt.figure(figsize=tamanho_fig)

        # Plotando fundo
        plt.plot(
            datas_fundo,
            rentabilidade_fundo,
            label="Fundo",
            color="DarkSlateGray",
            linewidth=1,
        )

        # Plotando benchmark
        plt.plot(
            datas_benchmark,
            rentabilidade_benchmark,
            label=self.dict_suporte[self.dict_suporte[self.fundo]],
            color="red",
            linewidth=1,
        )

        plt.title(f"{self.fundo} x Benchmark", fontsize=16, fontweight="bold")

        plt.ylabel("Rentabilidade Acumulada")

        formatter = FuncFormatter(self.to_percent)
        plt.gca().yaxis.set_major_formatter(formatter)

        intervalo = int(len(datas_fundo) / 20)
        plt.xticks(
            ticks=np.arange(len(datas_fundo))[::intervalo],
            labels=[datas_fundo[i] for i in np.arange(len(datas_fundo))[::intervalo]],
            rotation=90,
        )  # Fonte maior nos ticks

        plt.xticks(rotation=90)
        # plt.grid(True)
        plt.grid(
            True, which="major", linestyle="--", linewidth=0.5, color="grey", axis="y"
        )

        # Ajusta layout para não cortar conteúdo
        plt.tight_layout()

        # Adicionando legenda
        plt.legend()

        return plt

    def var_parametrico(self):

        df_dados = self.df_suporte_dados.copy()

        if df_dados["VAR_COTA_DIA"].iloc[0] == 0:
            df_dados = df_dados.drop(index=0).reset_index(drop=True)
        results = df_dados["VAR_COTA_DIA"].values.tolist()
        desvio_padrao = np.std(results, ddof=1)
        media = np.mean(results)
        z = 2.33  # para 99% confianca
        var_parametrico = -(media - (z * desvio_padrao))

        if var_parametrico < 0:
            return 0
        else:
            return var_parametrico * 100

    def var_historico(self):

        df_dados = self.df_suporte_dados.copy()

        df_var_hist = df_dados
        if df_var_hist["VAR_COTA_DIA"].iloc[0] == 0:
            df_var_hist = df_var_hist.drop(index=0).reset_index(drop=True)

        df_var_hist = df_var_hist[["VAR_COTA_DIA"]]

        df_var_hist = df_var_hist.sort_values(
            by="VAR_COTA_DIA", ascending=True
        ).reset_index(drop=True)

        index_var_hist = int(len(df_var_hist) * 0.01) - 1

        var = df_var_hist.iloc[index_var_hist]["VAR_COTA_DIA"] * -1

        if var < 0:
            return 0
        else:
            return var * 100

    def diasPositivos(self):

        df_dados = self.df_suporte_dados.copy()

        if df_dados["VAR_COTA_DIA"].iloc[0] == 0:
            df_dados = df_dados.drop(index=0).reset_index(drop=True)
        dias_positivos = df_dados.query("VAR_COTA_DIA > 0").shape[0]
        return dias_positivos

    def diasNegativos(self):

        df_dados = self.df_suporte_dados.copy()

        if df_dados["VAR_COTA_DIA"].iloc[0] == 0:
            df_dados = df_dados.drop(index=0).reset_index(drop=True)
        dias_negativos = df_dados.query("VAR_COTA_DIA < 0").shape[0]
        return dias_negativos

    def maioresRentabilidades(self):

        df_dados = self.df_suporte_dados.copy()

        if df_dados["VAR_COTA_DIA"].iloc[0] == 0:
            df_dados = df_dados.drop(index=0).reset_index(drop=True)
        df_maiores_rents = (
            df_dados.sort_values(by="VAR_COTA_DIA", ascending=False)
            .head(5)
            .reset_index(drop=True)
        )
        df_maiores_rents["VAR_COTA_DIA"] = (
            df_maiores_rents["VAR_COTA_DIA"] * 100
        ).round(2).astype(str) + "%"
        df_maiores_rents = df_maiores_rents.rename(
            columns={
                "REFDATE": "Refdate",
                "COTA_LIQUIDA": "Cota",
                "VAR_COTA_DIA": "Rent. Cota",
            }
        )
        return df_maiores_rents

    def menoresRentabilidades(self):

        df_dados = self.df_suporte_dados.copy()

        if df_dados["VAR_COTA_DIA"].iloc[0] == 0:
            df_dados = df_dados.drop(index=0).reset_index(drop=True)
        df_menores_rents = (
            df_dados.sort_values(by="VAR_COTA_DIA", ascending=True)
            .head(5)
            .reset_index(drop=True)
        )
        df_menores_rents["VAR_COTA_DIA"] = (
            df_menores_rents["VAR_COTA_DIA"] * 100
        ).round(2).astype(str) + "%"
        df_menores_rents = df_menores_rents.rename(
            columns={
                "REFDATE": "Refdate",
                "COTA_LIQUIDA": "Cota",
                "VAR_COTA_DIA": "Rent. Cota",
            }
        )
        return df_menores_rents


class liquidezAtivos:

    def __init__(self, manager_sql=None, funcoes_pytools=None):

        self.manager_sql = manager_sql if manager_sql is not None else SQL_Manager()

        self.funcoes_pytools = funcoes_pytools if funcoes_pytools is not None else FuncoesPyTools(self.manager_sql)

        self.manager_dados = capturaDados(
            manager_sql=self.manager_sql, funcoes_pytools=self.funcoes_pytools
        )

        self.sql_aux_dict_lists = SqlDictionariesLists(manager_sql=self.manager_sql, funcoes_pytools=self.funcoes_pytools)

        self.fixed_aux_dict_lists = FixedDictionariesListsLibrary()

        self.lista_tipo_ativos_observaveis = self.fixed_aux_dict_lists.lista_tipo_ativos_observaveis
        self.lista_tipo_ativos_titulos_publicos = self.fixed_aux_dict_lists.lista_tipo_ativos_titulos_publicos
        self.lista_tipo_ativos_fluxo = self.fixed_aux_dict_lists.lista_tipo_ativos_fluxo
        self.lista_tipo_ativos_fundos = self.fixed_aux_dict_lists.lista_tipo_ativos_fundos

        self.dict_fundos_fic_master = self.fixed_aux_dict_lists.dict_fundos_fic_master

        # self.refdate = None
        self.df_carteira_fundos = None
        self.df_base_b3_observaveis = None
        self.lista_ativos_observaveis_sem_liquidez = None

        self.df_base_liquidez_diaria_observavel = None
        self.df_resumo_observavel = None

        self.df_base_liquidez_diaria_fluxo = None
        self.df_resumo_liquidez_fluxo = None

        self.df_base_liquidez_diaria_fluxo_fidcs = None
        self.df_resumo_liquidez_fidcs = None

        self.df_base_liquidez_diaria_fluxo_fundos = None
        self.df_resumo_liquidez_fundos = None

    def set_df_negocios_b3_observaveis(self):

        lista_ativos_observaveis = (
            self.df_carteira_fundos[
                self.df_carteira_fundos["TIPO_ATIVO"].isin(
                    self.lista_tipo_ativos_observaveis
                )
            ]["ATIVO"]
            .unique()
            .tolist()
        )

        str_lista_ativos_observaveis = self.funcoes_pytools.convert_list_to_str(
            lista_ativos_observaveis
        )

        df = self.manager_sql.select_dataframe(
            f"SELECT COD_IF, SUM(FINANCEIRO) AS FINANCEIRO FROM TB_B3_NEGOCIOS_BALCAO_RENDA_FIXA "
            f"WHERE REFDATE >= '{self.dmenos21}' AND REFDATE < '{self.refdate}' "
            f"AND [STATUS] = 'Confirmado' "
            f"AND COD_IF IN ({str_lista_ativos_observaveis}) GROUP BY COD_IF"
        )

        self.df_base_b3_observaveis = df.copy()

    def set_df_carteira_fundos(self):

        df = self.manager_sql.select_dataframe(
            "SELECT REFDATE, FUNDO, TIPO_ATIVO, ATIVO, ROUND(SUM(FINANCEIRO_D0),2) [FINANCEIRO], "
            "SUM(QUANTIDADE_D0) [QUANTIDADE] FROM TB_CARTEIRAS "
            f"WHERE REFDATE = '{self.refdate}' AND "
            "TIPO_ATIVO NOT IN ('Ajuste Cisão', 'Provisões & Despesas') AND FINANCEIRO_D0 > 0 "
            "GROUP BY REFDATE, FUNDO, TIPO_ATIVO, ATIVO"
        )

        self.df_carteira_fundos = df.copy()

    def set_lista_ativos_observaveis_sem_liquidez(self):

        set_carteira = set(
            self.df_carteira_fundos[
                self.df_carteira_fundos["TIPO_ATIVO"].isin(
                    self.lista_tipo_ativos_observaveis
                )
            ]["ATIVO"].unique()
        )
        set_b3 = set(self.df_base_b3_observaveis["COD_IF"].unique())

        self.lista_ativos_observaveis_sem_liquidez = list(set_carteira - set_b3)

    def set_refdate(self, refdate: date):

        self.refdate = refdate

        self.dmenos21 = self.funcoes_pytools.workday_br(self.refdate, -21)

        self.set_df_carteira_fundos()

        self.set_df_negocios_b3_observaveis()

        self.set_lista_ativos_observaveis_sem_liquidez()

        self.liquidez_mercado_observavel()

        self.liquidez_titulos_publicos()

        self.liquidez_fluxo()

        self.liquidez_fluxo_fidc()

        self.liquidez_fluxo_fundos()

        self.set_df_resumo_liquidez_all()

        self.set_df_liquidez_fundos_x_passivo()

    def isRefdateSet(self):

        if self.refdate is None:
            return False

        return True

    def liquidez_mercado_observavel(self):

        def set_df_premissa_venda():

            df_base_b3 = self.df_base_b3_observaveis.copy()

            df_premissa = (
                df_base_b3[["COD_IF", "FINANCEIRO"]]
                .groupby("COD_IF")
                .sum()
                .reset_index()
            )
            df_premissa["Premissa venda"] = (
                df_premissa["FINANCEIRO"] / 21 * 0.3
            ).round(2)
            df_premissa = df_premissa[["COD_IF", "Premissa venda"]].rename(
                columns={"COD_IF": "Ativo"}
            )
            return df_premissa

        def set_df_liquidez() -> pd.DataFrame:

            df_premissa = set_df_premissa_venda()

            df_carteira = self.df_carteira_fundos[
                (
                    self.df_carteira_fundos["TIPO_ATIVO"].isin(
                        self.lista_tipo_ativos_observaveis
                    )
                ) & (
                    ~self.df_carteira_fundos["ATIVO"].isin(
                        self.lista_ativos_observaveis_sem_liquidez
                    )
                )
            ].copy()
            df_carteira = df_carteira[
                ["REFDATE", "FUNDO", "TIPO_ATIVO", "ATIVO", "FINANCEIRO"]
            ].rename(
                columns={
                    "REFDATE": "Refdate",
                    "FUNDO": "Fundo",
                    "TIPO_ATIVO": "Tipo Ativo",
                    "ATIVO": "Ativo",
                    "FINANCEIRO": "Posição dia",
                }
            )
            df_carteira.insert(2, "Categoria", "Mercado observável")

            df_liquidez = pd.merge(df_carteira, df_premissa, on="Ativo", how="left")

            df_liquidez = df_liquidez[
                [
                    "Refdate",
                    "Fundo",
                    "Categoria",
                    "Tipo Ativo",
                    "Ativo",
                    "Posição dia",
                    "Premissa venda",
                ]
            ]

            return df_liquidez

        def set_df_base() -> pd.DataFrame:

            df = set_df_liquidez()

            refdate_atual = self.funcoes_pytools.workday_br(self.refdate, 1)
            refdate_anterior = self.refdate
            saldo_posicao = df["Posição dia"].sum()

            df_liquidez_diaria = df.copy()
            df_liquidez_diaria.loc[:, "Saldo posição dia"] = df_liquidez_diaria.apply(
                lambda x: (
                    0
                    if x["Posição dia"] < x["Premissa venda"]
                    else x["Posição dia"] - x["Premissa venda"]
                ),
                axis=1,
            )
            df_liquidez_diaria.loc[:, "Liquidez gerada dia"] = df_liquidez_diaria.apply(
                lambda x: (
                    0
                    if x["Posição dia"] == 0
                    else x["Posição dia"] - x["Saldo posição dia"]
                ),
                axis=1,
            )
            df_liquidez_diaria["Liquidez total gerada"] = df_liquidez_diaria[
                "Liquidez gerada dia"
            ]

            while True:

                if saldo_posicao == 0:
                    break

                df_atual = df_liquidez_diaria[
                    df_liquidez_diaria["Refdate"] == refdate_anterior
                ][
                    [
                        "Fundo",
                        "Categoria",
                        "Tipo Ativo",
                        "Ativo",
                        "Saldo posição dia",
                        "Premissa venda",
                        "Liquidez total gerada",
                    ]
                ].copy()
                df_atual.rename(
                    columns={
                        "Saldo posição dia": "Posição dia",
                        "Liquidez total gerada": "Liquidez total gerada dm1",
                    },
                    inplace=True,
                )

                df_atual.loc[:, "Saldo posição dia"] = df_atual.apply(
                    lambda x: (
                        0
                        if x["Posição dia"] < x["Premissa venda"]
                        else x["Posição dia"] - x["Premissa venda"]
                    ),
                    axis=1,
                )
                df_atual.loc[:, "Liquidez gerada dia"] = df_atual.apply(
                    lambda x: (
                        0
                        if x["Posição dia"] == 0
                        else x["Posição dia"] - x["Saldo posição dia"]
                    ),
                    axis=1,
                )
                df_atual.loc[:, "Liquidez total gerada"] = df_atual.apply(
                    lambda x: x["Liquidez total gerada dm1"] + x["Liquidez gerada dia"],
                    axis=1,
                )
                df_atual = df_atual.drop(columns=["Liquidez total gerada dm1"])
                df_atual.insert(0, "Refdate", refdate_atual)

                df_liquidez_diaria = pd.concat([df_liquidez_diaria, df_atual])

                saldo_posicao = df_atual["Saldo posição dia"].sum()
                refdate_anterior = refdate_atual
                refdate_atual = self.funcoes_pytools.workday_br(refdate_atual, 1)

            # Trabalha resumo
            df_resumo = df_liquidez_diaria.copy()

            df_resumo = (
                df_resumo[
                    [
                        "Refdate",
                        "Fundo",
                        "Categoria",
                        "Posição dia",
                        "Premissa venda",
                        "Saldo posição dia",
                        "Liquidez gerada dia",
                    ]
                ]
                .groupby(["Refdate", "Fundo", "Categoria"])
                .sum()
                .reset_index()
            )

            fundos = df_resumo["Fundo"].unique()

            df_resumo_liquidez = pd.DataFrame()

            for fundo in fundos:
                df_fundo = df_resumo[df_resumo["Fundo"] == fundo].copy()
                df_fundo.sort_values(by="Refdate", inplace=True)
                df_fundo["Liquidez total gerada"] = df_fundo[
                    "Liquidez gerada dia"
                ].cumsum()
                df_resumo_liquidez = pd.concat([df_resumo_liquidez, df_fundo])

            df_resumo_liquidez = df_resumo_liquidez.sort_values(
                by=["Fundo", "Refdate"]
            ).reset_index(drop=True)

            return df_liquidez_diaria, df_resumo_liquidez

        self.df_base_liquidez_diaria_observavel, self.df_resumo_liquidez_observavel = (
            set_df_base()
        )

    def liquidez_titulos_publicos(self):

        def set_df_base() -> pd.DataFrame:

            str_lista_tipo_ativos = self.funcoes_pytools.convert_list_to_str(
                self.lista_tipo_ativos_titulos_publicos
            )

            df = self.manager_sql.select_dataframe(
                f"SELECT REFDATE, FUNDO, TIPO_ATIVO, ATIVO, ROUND(SUM(FINANCEIRO_D0),2) "
                "[FINANCEIRO] FROM TB_CARTEIRAS "
                f"WHERE REFDATE = '{self.refdate}' AND TIPO_ATIVO IN ({str_lista_tipo_ativos}) "
                "AND QUANTIDADE_D0 > 0 "
                f"GROUP BY REFDATE, FUNDO, TIPO_ATIVO, ATIVO"
            )

            return df

        def work_on_df_base():

            df = set_df_base().copy()

            df.insert(2, "Categoria", "Títulos Públicos")

            df_refdate = df.copy()

            df_refdate["Premissa venda"] = df_refdate.apply(
                lambda x: x["FINANCEIRO"] if x["TIPO_ATIVO"] == "Compromissada" else 0,
                axis=1,
            )
            df_refdate["Liquidez gerada dia"] = df_refdate.apply(
                lambda x: x["FINANCEIRO"] if x["TIPO_ATIVO"] == "Compromissada" else 0,
                axis=1,
            )
            df_refdate["Saldo posição dia"] = df_refdate.apply(
                lambda x: 0 if x["TIPO_ATIVO"] == "Compromissada" else x["FINANCEIRO"],
                axis=1,
            )
            df_refdate["Liquidez total gerada"] = df_refdate.apply(
                lambda x: x["FINANCEIRO"] if x["TIPO_ATIVO"] == "Compromissada" else 0,
                axis=1,
            )

            df_dmais1 = df_refdate[
                [
                    "FUNDO",
                    "Categoria",
                    "TIPO_ATIVO",
                    "ATIVO",
                    "Saldo posição dia",
                    "Liquidez total gerada",
                ]
            ].rename(
                columns={
                    "Saldo posição dia": "FINANCEIRO",
                    "Liquidez total gerada": "Liquidez total gerada dm1",
                }
            )

            df_dmais1["Premissa venda"] = df_dmais1["FINANCEIRO"]
            df_dmais1["Liquidez gerada dia"] = df_dmais1["FINANCEIRO"]
            df_dmais1["Saldo posição dia"] = 0
            df_dmais1["Liquidez total gerada"] = df_dmais1.apply(
                lambda x: x["FINANCEIRO"] + x["Liquidez total gerada dm1"], axis=1
            )

            refdate_dmais1 = self.funcoes_pytools.workday_br(self.refdate, 1)

            df_dmais1.insert(0, "REFDATE", refdate_dmais1)

            return df_refdate, df_dmais1

        def set_df_liquidez_tit_publicos():

            df_refdate, df_dmais1 = work_on_df_base()

            df_dmais1 = df_dmais1[
                [
                    "REFDATE",
                    "FUNDO",
                    "Categoria",
                    "TIPO_ATIVO",
                    "ATIVO",
                    "FINANCEIRO",
                    "Premissa venda",
                    "Saldo posição dia",
                    "Liquidez gerada dia",
                    "Liquidez total gerada",
                ]
            ].rename(
                columns={
                    "REFDATE": "Refdate",
                    "FUNDO": "Fundo",
                    "TIPO_ATIVO": "Tipo Ativo",
                    "ATIVO": "Ativo",
                    "FINANCEIRO": "Posição dia",
                }
            )

            df_refdate = df_refdate[
                [
                    "REFDATE",
                    "FUNDO",
                    "Categoria",
                    "TIPO_ATIVO",
                    "ATIVO",
                    "FINANCEIRO",
                    "Premissa venda",
                    "Saldo posição dia",
                    "Liquidez gerada dia",
                    "Liquidez total gerada",
                ]
            ].rename(
                columns={
                    "REFDATE": "Refdate",
                    "FUNDO": "Fundo",
                    "TIPO_ATIVO": "Tipo Ativo",
                    "ATIVO": "Ativo",
                    "FINANCEIRO": "Posição dia",
                }
            )

            df_base_tit_publicos = pd.concat([df_refdate, df_dmais1])

            df_base_tit_publicos = df_base_tit_publicos.sort_values(
                by=["Fundo", "Refdate", "Ativo"]
            ).reset_index(drop=True)

            df_base_liquidez_diaria_tit_publicos = df_base_tit_publicos.copy()

            # Trabalha a df de resumo
            df_base = df_base_tit_publicos.copy()
            df_resumo = pd.DataFrame()
            fundos = df_base['Fundo'].unique()

            for fundo in fundos:
                df_fundo = df_base[df_base['Fundo'] == fundo][[
                    'Refdate', 'Fundo', 'Categoria', 'Posição dia', 'Premissa venda', 'Saldo posição dia', 'Liquidez gerada dia']].copy()
                df_fundo = df_fundo.groupby(['Refdate', 'Fundo', 'Categoria']).sum().sort_values(by=['Refdate']).reset_index()
                df_fundo['Liquidez total gerada'] = df_fundo['Liquidez gerada dia'].cumsum()
                df_resumo = pd.concat([df_resumo, df_fundo])

            df_resumo.reset_index(drop=True, inplace=True)

            return df_base_liquidez_diaria_tit_publicos, df_resumo

        self.df_base_liquidez_diaria_tit_publicos, self.df_resumo_liquidez_tit_publicos = set_df_liquidez_tit_publicos()

    def liquidez_fluxo(self):

        def set_variaveis_pesquisa():

            str_sem_liquidez = self.funcoes_pytools.convert_list_to_str(
                self.lista_ativos_observaveis_sem_liquidez
            )
            str_observaveis = self.funcoes_pytools.convert_list_to_str(
                self.lista_tipo_ativos_observaveis
            )
            str_tipo_ativos_fluxo = self.funcoes_pytools.convert_list_to_str(
                self.lista_tipo_ativos_fluxo
            )

            return str_sem_liquidez, str_observaveis, str_tipo_ativos_fluxo

        def set_df_base_to_work():

            str_sem_liquidez, str_observaveis, str_tipo_ativos_fluxo = (
                set_variaveis_pesquisa()
            )

            df_ativos_fluxo = self.manager_sql.select_dataframe(
                "SELECT * FROM TB_FLUXO_FUTURO_ATIVOS WHERE "
                f"REFDATE = '{self.refdate}' AND TIPO_ATIVO NOT IN ({str_observaveis})"
            )
            df_fluxo_observaveis_sem_liquidez = self.manager_sql.select_dataframe(
                f"SELECT * FROM TB_FLUXO_FUTURO_ATIVOS WHERE REFDATE = '{self.refdate}' "
                f"AND ATIVO IN ({str_sem_liquidez})"
            )

            df_ativos_fluxo = pd.concat(
                [df_ativos_fluxo, df_fluxo_observaveis_sem_liquidez]
            )

            df_ativos_fluxo = df_ativos_fluxo[
                ["ATIVO", "DATA_LIQUIDACAO", "FLUXO_DESCONTADO"]
            ]

            df_carteira = self.manager_sql.select_dataframe(
                "SELECT REFDATE, FUNDO, TIPO_ATIVO, ATIVO, QUANTIDADE_D0 FROM TB_CARTEIRAS WHERE "
                f"REFDATE = '{self.refdate}' AND FINANCEIRO_D0 > 0 "
                f"AND TIPO_ATIVO IN ({str_tipo_ativos_fluxo})"
            )

            df_carteira_observaveis_sem_liquidez = self.manager_sql.select_dataframe(
                "SELECT REFDATE, FUNDO, TIPO_ATIVO, ATIVO, QUANTIDADE_D0 FROM TB_CARTEIRAS WHERE "
                f"REFDATE = '{self.refdate}' "
                f"AND FINANCEIRO_D0 > 0 AND ATIVO IN ({str_sem_liquidez})"
            )

            df_carteira = pd.concat([df_carteira, df_carteira_observaveis_sem_liquidez])

            df = pd.merge(df_carteira, df_ativos_fluxo, on="ATIVO", how="left")

            return df

        def set_df_base_liquidez():

            df_liquidez_fluxo = set_df_base_to_work().copy()

            df_liquidez_fluxo.loc[:, "Liquidez gerada dia"] = (
                df_liquidez_fluxo["FLUXO_DESCONTADO"] * df_liquidez_fluxo["QUANTIDADE_D0"]
            )

            df_liquidez_fluxo.loc[:, "Categoria"] = "Fluxo"

            df_liquidez_fluxo.rename(
                columns={
                    "DATA_LIQUIDACAO": "Refdate",
                    "TIPO_ATIVO": "Tipo Ativo",
                    "FUNDO": "Fundo",
                    "ATIVO": "Ativo",
                },
                inplace=True,
            )

            df_liquidez_fluxo = (
                df_liquidez_fluxo[
                    [
                        "Refdate",
                        "Fundo",
                        "Categoria",
                        "Tipo Ativo",
                        "Ativo",
                        "Liquidez gerada dia",
                    ]
                ]
                .sort_values(by=["Refdate", "Fundo"])
                .reset_index(drop=True)
            )

            # Trabalha ativos
            fundos = df_liquidez_fluxo["Fundo"].unique()

            df_base_liquidez = pd.DataFrame()

            for fundo in fundos:
                df_fundo = df_liquidez_fluxo[df_liquidez_fluxo["Fundo"] == fundo].copy()
                ativos = df_fundo["Ativo"].unique()
                for ativo in ativos:
                    df_ativo = df_fundo[df_fundo["Ativo"] == ativo].copy()
                    df_ativo.sort_values(by=["Refdate"], inplace=True)
                    df_ativo["Liquidez total gerada"] = df_ativo[
                        "Liquidez gerada dia"
                    ].cumsum()
                    df_base_liquidez = pd.concat([df_base_liquidez, df_ativo])

            # Trabalha resumo
            df_resumo = pd.DataFrame()
            df_base_resumo = df_liquidez_fluxo.copy()
            df_base_resumo.sort_values(by=["Fundo", "Refdate"], inplace=True)

            for fundo in fundos:
                df_fundo = df_base_resumo[df_base_resumo["Fundo"] == fundo].copy()
                df_fundo = (
                    df_fundo[["Refdate", "Fundo", "Categoria", "Liquidez gerada dia"]]
                    .groupby(["Refdate", "Fundo", "Categoria"])
                    .sum()
                )
                df_fundo["Liquidez total gerada"] = df_fundo[
                    "Liquidez gerada dia"
                ].cumsum()
                df_resumo = pd.concat([df_resumo, df_fundo])

            df_resumo.reset_index(inplace=True)

            return df_base_liquidez, df_resumo

        self.df_base_liquidez_diaria_fluxo, self.df_resumo_liquidez_fluxo = (
            set_df_base_liquidez()
        )

    def liquidez_fluxo_fidc(self):

        def set_df_base_to_work():

            df = self.manager_sql.select_dataframe(
                "SELECT DATA_LIQUIDACAO, ATIVO, VALOR FROM TB_FLUXO_PAGAMENTO_FIDC "
                f"WHERE MONTH(REFDATE) = {self.refdate.month} "
                f"AND YEAR(REFDATE) = {self.refdate.year}"
            )

            return df

        def set_df_bases_fluxo_fidcs():

            df_fluxo_fidcs = set_df_base_to_work().copy()

            df_fluxo_fidcs = (
                df_fluxo_fidcs.groupby(["DATA_LIQUIDACAO", "ATIVO"]).sum().reset_index()
            )

            df_fluxo_fidcs.insert(1, "Categoria", "Fluxo FIDC")
            df_fluxo_fidcs.insert(2, "Tipo Ativo", "FIDC")

            df_fluxo_fidcs.rename(
                columns={
                    "DATA_LIQUIDACAO": "Refdate",
                    "ATIVO": "Ativo",
                    "VALOR": "Liquidez gerada dia",
                },
                inplace=True,
            )

            ativos = df_fluxo_fidcs["Ativo"].unique()
            df_liquidez_diaria_ativos = pd.DataFrame()

            for ativo in ativos:
                df_ativo = df_fluxo_fidcs[df_fluxo_fidcs["Ativo"] == ativo].copy()
                df_ativo.sort_values(by=["Refdate"], inplace=True)
                df_ativo["Liquidez total gerada"] = df_ativo[
                    "Liquidez gerada dia"
                ].cumsum()
                df_liquidez_diaria_ativos = pd.concat(
                    [df_liquidez_diaria_ativos, df_ativo]
                )

            df_resumo_liquidez_fidcs = df_fluxo_fidcs[
                ["Refdate", "Categoria", "Liquidez gerada dia"]
            ].copy()
            df_resumo_liquidez_fidcs = (
                df_resumo_liquidez_fidcs.groupby(["Refdate", "Categoria"])
                .sum()
                .sort_values(by=["Refdate"])
                .reset_index()
            )
            df_resumo_liquidez_fidcs["Liquidez total gerada"] = (
                df_resumo_liquidez_fidcs["Liquidez gerada dia"].cumsum()
            )

            df_liquidez_diaria_ativos.insert(1, "Fundo", "Strix Yield Master")
            df_resumo_liquidez_fidcs.insert(1, "Fundo", "Strix Yield Master")

            return df_liquidez_diaria_ativos, df_resumo_liquidez_fidcs

        self.df_base_liquidez_diaria_fluxo_fidcs, self.df_resumo_liquidez_fidcs = (
            set_df_bases_fluxo_fidcs()
        )

    def liquidez_fluxo_fundos(self):

        def data_liquidacao_resgate(row):

            if (
                row["DIAS_COTIZACAO_RESGATE"] == 0 and row["DIAS_LIQUIDACAO_RESGATE"] == 0
            ):
                return row["REFDATE"]

            if row["TIPO_COTIZACAO_RESGATE"] == "DC":
                refdate_cotizacao = self.funcoes_pytools.diasCorridos_br(
                    row["REFDATE"], row["DIAS_COTIZACAO_RESGATE"]
                )
            else:
                refdate_cotizacao = self.funcoes_pytools.workday_br(
                    row["REFDATE"], row["DIAS_COTIZACAO_RESGATE"]
                )

            if row["TIPO_LIQUIDACAO_RESGATE"] == "DC":
                return self.funcoes_pytools.diasCorridos_br(
                    refdate_cotizacao, row["DIAS_LIQUIDACAO_RESGATE"]
                )
            else:
                return self.funcoes_pytools.workday_br(
                    refdate_cotizacao, row["DIAS_LIQUIDACAO_RESGATE"]
                )

        def set_df_base_to_work():

            df_carteira = self.manager_sql.select_dataframe(
                "SELECT REFDATE, FUNDO, ATIVO, FINANCEIRO_D0 FROM TB_CARTEIRAS "
                f"WHERE REFDATE = '{self.refdate}' AND "
                "TIPO_ATIVO IN "
                f"({self.funcoes_pytools.convert_list_to_str(self.lista_tipo_ativos_fundos)}) "
                "AND FINANCEIRO_D0 > 0"
            )

            df_cadastro_fundos = self.manager_sql.select_dataframe(
                "SELECT DISTINCT ATIVO, TIPO_COTIZACAO_RESGATE, DIAS_COTIZACAO_RESGATE, "
                "TIPO_LIQUIDACAO_RESGATE, DIAS_LIQUIDACAO_RESGATE FROM TB_CADASTRO_ATIVOS "
                "WHERE TIPO_ATIVO IN "
                f"({self.funcoes_pytools.convert_list_to_str(self.lista_tipo_ativos_fundos)})"
            )

            df = pd.merge(df_carteira, df_cadastro_fundos, on="ATIVO", how="left")

            return df

        def set_df_bases_fluxo_fundos():

            df_fundos = set_df_base_to_work().copy()

            df_fundos["DATA_LIQUIDACAO"] = df_fundos.apply(
                lambda row: data_liquidacao_resgate(row), axis=1
            )

            df_fundos = (
                df_fundos[
                    ["DATA_LIQUIDACAO", "FUNDO", "ATIVO", "FINANCEIRO_D0"]
                ]
                .rename(
                    columns={
                        "DATA_LIQUIDACAO": "Refdate",
                        "FUNDO": "Fundo",
                        "FINANCEIRO_D0": "Liquidez gerada dia",
                        "ATIVO": "Ativo",
                    }
                )
                .sort_values(by=["Fundo", "Refdate"])
                .reset_index(drop=True)
            )

            df_fundos.insert(2, "Categoria", "Fluxo FI")

            # Trabalha base ativos
            df_base_ativos = df_fundos.copy()
            df_base_ativos["Liquidez total gerada"] = df_base_ativos[
                "Liquidez gerada dia"
            ]

            # Trabalha base resumo
            df_resumo = df_fundos.copy()

            df_resumo = (
                df_resumo[["Refdate", "Fundo", "Categoria", "Liquidez gerada dia"]]
                .groupby(["Refdate", "Fundo", "Categoria"])
                .sum()
                .sort_values(by=["Fundo", "Refdate"])
                .reset_index()
            )

            df_resumo_fundos = pd.DataFrame()
            fundos = df_resumo["Fundo"].unique()
            for fundo in fundos:
                df_fundo = df_resumo[df_resumo["Fundo"] == fundo].copy()
                df_fundo["Liquidez total gerada"] = df_fundo[
                    "Liquidez gerada dia"
                ].cumsum()
                df_resumo_fundos = pd.concat([df_resumo_fundos, df_fundo])

            return df_base_ativos, df_resumo_fundos

        self.df_base_liquidez_diaria_fluxo_fundos, self.df_resumo_liquidez_fundos = (
            set_df_bases_fluxo_fundos()
        )

    def set_df_resumo_liquidez_all(self):

        def set_df_categoria_fluxo_all():

            # Juntando todos categoria Fluxo
            df_resumo_fluxo = self.df_resumo_liquidez_fluxo
            df_resumo_fluxo_fidcs = self.df_resumo_liquidez_fidcs
            df_resumo_fluxo_fundos = self.df_resumo_liquidez_fundos

            df_fluxo_all = pd.concat(
                [df_resumo_fluxo, df_resumo_fluxo_fidcs, df_resumo_fluxo_fundos],
                axis=0).sort_values(by=['Fundo', 'Refdate']).reset_index(drop=True)

            df_resumo_fluxo_all = pd.DataFrame()
            fundos = df_fluxo_all['Fundo'].unique()
            for fundo in fundos:
                df_fundo = df_fluxo_all[df_fluxo_all['Fundo'] == fundo][['Refdate', 'Fundo', 'Liquidez gerada dia']].copy()
                df_fundo = df_fundo.groupby(['Refdate', 'Fundo']).sum().reset_index()
                df_fundo.loc[:, 'Liquidez total gerada'] = df_fundo['Liquidez gerada dia'].cumsum()
                df_resumo_fluxo_all = pd.concat([df_resumo_fluxo_all, df_fundo], axis=0)

            return df_resumo_fluxo_all

        def set_df_resumo_all():

            df_resumo_liquidez_tit_publicos = self.df_resumo_liquidez_tit_publicos[
                ['Refdate', 'Fundo', 'Liquidez gerada dia', 'Liquidez total gerada']].copy()
            df_resumo_liquidez_observavel = self.df_resumo_liquidez_observavel[
                ['Refdate', 'Fundo', 'Liquidez gerada dia', 'Liquidez total gerada']].copy()

            df_all = pd.concat([self.df_resumo_liquidez_fluxo_all, df_resumo_liquidez_tit_publicos, df_resumo_liquidez_observavel])

            df_resumo_all = pd.DataFrame()
            fundos = df_all['Fundo'].unique()

            for fundo in fundos:
                df_fundos = df_all[df_all['Fundo'] == fundo][['Refdate', 'Fundo', 'Liquidez gerada dia']].copy()
                df_fundos = df_fundos.groupby(['Refdate', 'Fundo']).sum().sort_values(by='Refdate').reset_index()
                df_fundos['Liquidez total gerada'] = df_fundos['Liquidez gerada dia'].cumsum()
                df_resumo_all = pd.concat([df_resumo_all, df_fundos])

            return df_resumo_all

        self.df_resumo_liquidez_fluxo_all = set_df_categoria_fluxo_all()
        self.df_resumo_liquidez_all = set_df_resumo_all()

    def set_df_liquidez_fundos_x_passivo(self):

        def get_df_resgates():

            df_resgates = self.manager_sql.select_dataframe(
                "SELECT DATA_IMPACTO AS DATA_LIQUIDACAO, FUNDO, DESC_TIPO_OPERACAO, VALOR * -1 AS VALOR, QTD_COTAS * -1 AS QTD_COTAS "
                f"FROM TB_BASE_BTG_MOVIMENTACAO_PASSIVO "
                f"WHERE DATA_OPERACAO <= '{self.refdate}' AND DATA_IMPACTO >= '{self.refdate}' AND TIPO_OPERACAO = 'RESGATE' "
                f"AND FUNDO NOT IN ('STRIX YIELD MASTER F')")

            if 'RESGATE TOTAL' in df_resgates['DESC_TIPO_OPERACAO'].unique().tolist():
                df_resgates['Cota'] = df_resgates['FUNDO'].map(self.sql_aux_dict_lists.get_dict_last_cotas(self.refdate))
                df_resgates.loc[:, 'VALOR'] = df_resgates.apply(
                    lambda x: x['Cota'] * x['QTD_COTAS'] if x['DESC_TIPO_OPERACAO'] == 'RESGATE TOTAL' else x['VALOR'], axis=1)

            df_resgates = df_resgates[['DATA_LIQUIDACAO', 'FUNDO', 'VALOR']]

            df_resgates['FUNDO_MASTER'] = df_resgates['FUNDO'].map(self.fixed_aux_dict_lists.dict_fundos_fic_master)

            df_resgates = df_resgates[['FUNDO_MASTER', 'DATA_LIQUIDACAO', 'VALOR']].groupby([
                'FUNDO_MASTER', 'DATA_LIQUIDACAO']).sum().sort_values(by=['FUNDO_MASTER', 'DATA_LIQUIDACAO']).reset_index()

            df_resgates = df_resgates.rename(columns={
                'FUNDO_MASTER': 'Fundo', 'DATA_LIQUIDACAO': 'Refdate', 'VALOR': 'Resgates a Liquidar'})

            return df_resgates

        def set_df_liquidez_x_passivo():

            df_resgates = get_df_resgates()

            df_fundos = self.df_resumo_liquidez_all[['Refdate', 'Fundo', 'Liquidez gerada dia']].copy()

            fundos = pd.concat([df_fundos[['Refdate', 'Fundo']], df_resgates[['Refdate', 'Fundo']]]).drop_duplicates()

            df_resumo_fundos = pd.DataFrame()

            for fundo in fundos['Fundo'].unique():
                df_fundo = fundos[fundos['Fundo'] == fundo].copy()
                df_fundo = pd.merge(df_fundo, df_fundos, on=['Refdate', 'Fundo'], how='left').merge(
                    df_resgates, on=['Refdate', 'Fundo'], how='left')
                df_resumo_fundos = pd.concat([df_resumo_fundos, df_fundo])

            df_resumo_fundos['Resgates a Liquidar'] = df_resumo_fundos['Resgates a Liquidar'].fillna(0)

            df_resumo_fundos['Saldo gerado dia'] = df_resumo_fundos.apply(
                lambda x: x['Liquidez gerada dia'] + x['Resgates a Liquidar'], axis=1)

            return df_resumo_fundos

        def set_saldo_liquidez_total_gerada():

            df_resumo = set_df_liquidez_x_passivo()
            df_resumo_fundos = pd.DataFrame()

            fundos = df_resumo['Fundo'].unique()

            for fundo in fundos:
                df_fundo = df_resumo[df_resumo['Fundo'] == fundo].copy()
                df_fundo.sort_values(by='Refdate', inplace=True)
                df_fundo['Saldo total gerado'] = df_fundo['Saldo gerado dia'].cumsum()
                df_resumo_fundos = pd.concat([df_resumo_fundos, df_fundo])

            return df_resumo_fundos

        self.df_liquidez_fundos_x_passivo = set_saldo_liquidez_total_gerada()
