from __init__ import *

VERSION_APP = "2.0.0"
VERSION_REFDATE = "2024-07-12"
ENVIRONMENT = os.getenv("ENVIRONMENT")
SCRIPT_NAME = os.path.basename(__file__)

if ENVIRONMENT == "DEVELOPMENT":
    print(f"{SCRIPT_NAME.upper()} - {ENVIRONMENT} - {VERSION_APP} - {VERSION_REFDATE}")

append_paths()

# -----------------------------------------------------------------------

# Import bibliotecas:

from datetime import date

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from db_helper import SQL_Manager
from matplotlib.ticker import FuncFormatter
from py_tools import FuncoesPyTools
from scipy.stats import norm

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
            f"SELECT REFDATE, FUNDO, TIPO_ATIVO, ATIVO, FINANCEIRO_D0 FROM TB_CARTEIRAS "
            f"WHERE REFDATE = '{self.refdate.strftime('%Y-%m-%d')}' AND FUNDO = 'STRIX YIELD MASTER' AND FINANCEIRO_D0 > 0.1"
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
                f"SELECT DISTINCT ATIVO, MODALIDADE_ENQUADRAMENTO FROM TB_CADASTRO_ATIVOS"
            )
            .set_index("ATIVO")["MODALIDADE_ENQUADRAMENTO"]
            .to_dict()
        )

        self.dict_cad_ativo = (
            self.manager_sql.select_dataframe(
                f"SELECT DISTINCT ATIVO, EMISSOR FROM TB_CADASTRO_ATIVOS WHERE EMISSOR IS NOT NULL"
            )
            .set_index("ATIVO")["EMISSOR"]
            .to_dict()
        )

        self.df_cad_emissor = self.manager_sql.select_dataframe(
            f"SELECT * FROM TB_CADASTRO_EMISSOR"
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

        df_carteira = self.df_carteira_yield_master.copy()

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
            set(self.lista_modalidade_ativos_com_limite)
            - set(df_exposicao_com_limites["MODALIDADE_ENQUADRAMENTO"])
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
            (df_carteira["TIPO_ATIVO"] != "Compromissada")
            & (df_carteira["TIPO_ATIVO"] != "Tit. Publicos")
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

    def __init__(self, strFundo, manager_sql=None):

        if manager_sql is None:
            self.manager = SQL_Manager()
        else:
            self.manager = manager_sql

        self.fundo = strFundo
        self.df_suporte_dados = self.suporte_dados()
        self.dict_suporte = {
            "IMABAJUST": "IPCA + Yield IMA-B",
            "CDI": "CDI",
            "STRIX YIELD MASTER F": "CDI",
            "STRIX FIA": "IMABAJUST",
        }

    def to_percent(self, y, position):
        s = f"{100 * y:.1f}%"
        return s

    def suporte_dados(self):
        self.df_suporte_dados = self.manager.select_dataframe(
            f"SELECT REFDATE, COTA_LIQUIDA, VAR_COTA_DIA/100 AS VAR_COTA_DIA FROM TB_BASE_BTG_PERFORMANCE_COTA WHERE FUNDO = '{self.fundo}' order by refdate"
        )
        return self.df_suporte_dados

    def df_drawdown_fundo(self):

        df_dados = self.df_suporte_dados[["REFDATE", "COTA_LIQUIDA"]]
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

        df_dados = self.df_suporte_dados

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

        df = self.df_suporte_dados

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

        df_fundo = self.manager.select_dataframe(
            f"SELECT DISTINCT REFDATE, COTA_LIQUIDA FROM TB_BASE_BTG_PERFORMANCE_COTA WHERE FUNDO = '{self.fundo}' ORDER BY REFDATE"
        )
        df_fundo["REFDATE"] = pd.to_datetime(df_fundo["REFDATE"])
        df_fundo["RENTABILIDADE_ACUMULADA"] = (
            df_fundo["COTA_LIQUIDA"] / df_fundo["COTA_LIQUIDA"].iloc[0] - 1
        )
        df_fundo = df_fundo[["REFDATE", "RENTABILIDADE_ACUMULADA"]]
        return df_fundo

    def rentabilidade_acumulada_benchmark(self):

        df_benchmark = self.manager.select_dataframe(
            f"SELECT DISTINCT REFDATE, COTA_INDEXADOR FROM TB_INDEXADORES WHERE REFDATE >= (SELECT MIN(REFDATE) FROM TB_BASE_BTG_PERFORMANCE_COTA WHERE FUNDO = '{self.fundo}') AND INDEXADOR = '{self.dict_suporte[self.fundo]}' ORDER BY REFDATE"
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
        df_dados = self.df_suporte_dados
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

        df_dados = self.df_suporte_dados

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
        df_dados = self.df_suporte_dados
        if df_dados["VAR_COTA_DIA"].iloc[0] == 0:
            df_dados = df_dados.drop(index=0).reset_index(drop=True)
        dias_positivos = df_dados.query("VAR_COTA_DIA > 0").shape[0]
        return dias_positivos

    def diasNegativos(self):
        df_dados = self.df_suporte_dados
        if df_dados["VAR_COTA_DIA"].iloc[0] == 0:
            df_dados = df_dados.drop(index=0).reset_index(drop=True)
        dias_negativos = df_dados.query("VAR_COTA_DIA < 0").shape[0]
        return dias_negativos

    def maioresRentabilidades(self):
        df_dados = self.df_suporte_dados
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
        df_dados = self.df_suporte_dados
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

        if manager_sql is None:
            self.manager_sql = SQL_Manager()
        else:
            self.manager_sql = manager_sql

        if funcoes_pytools is None:
            self.funcoes_pytools = FuncoesPyTools(self.manager_sql)
        else:
            self.funcoes_pytools = funcoes_pytools

    def set_refdate(self, refdate: date):

        self.refdate = refdate
        self.dmenos21 = self.funcoes_pytools.workday_br(self.refdate, -21)

    def captura_base_negocios_b3(self, lista_ativos: list):
        """
        Retorna DataFrame contendo dados de negociação de ativos que estão na tabela TB_B3_NEGOCIOS_BALCAO_RENDA_FIXA

        Args:
            lista_ativos (list): Lista de ativos para captura dos dados.

        """

        str_ativos = "', '".join(lista_ativos)

        df = self.manager_sql.select_dataframe(
            f"SELECT * FROM TB_B3_NEGOCIOS_BALCAO_RENDA_FIXA WHERE REFDATE >= '{self.dmenos21}' AND REFDATE < '{self.refdate}' "
            f"AND COD_IF IN ('{str_ativos}') AND STATUS = 'Confirmado'"
        )

        return df

    def mercado_observavel(self, lista_tipo_ativos: list):
        """
        Cria DataFrame 'df_liquidez_mercado_observavel' contendo dados de liquidez dos ativos em carteira que compõem o mercado observável de liquidez.

        Args:
            lista_tipo_ativos (list): Lista de TIPO_ATIVO que compõem mercado observável.

        """

        def captura_base_carteira(lista_tipo_ativos):

            str_lista_tipo_ativos = "', '".join(lista_tipo_ativos)

            df = self.manager_sql.select_dataframe(
                f"SELECT REFDATE, FUNDO, TIPO_ATIVO, ATIVO, ROUND(SUM(FINANCEIRO_D0),2) [FINANCEIRO] FROM TB_CARTEIRAS "
                f"WHERE REFDATE = '{self.refdate}' AND TIPO_ATIVO IN ('{str_lista_tipo_ativos}') AND QUANTIDADE_D0 > 0 "
                f"GROUP BY REFDATE, FUNDO, TIPO_ATIVO, ATIVO"
            )

            lista_ativos = df["ATIVO"].unique().tolist()

            return df, lista_ativos

        # bases a serem trabalhdas:
        df_carteira, lista_ativos = captura_base_carteira(lista_tipo_ativos)
        df_base_b3 = self.captura_base_negocios_b3(lista_ativos)

        # trabalha premissa de venda
        dias = df_base_b3["REFDATE"].nunique()
        df_base_b3 = df_base_b3.groupby(["COD_IF"])["FINANCEIRO"].sum().reset_index()
        df_base_b3["PREMISSA_VENDA"] = (df_base_b3["FINANCEIRO"] / dias * 0.3).round(2)
        df_base_b3 = df_base_b3[["COD_IF", "PREMISSA_VENDA"]].rename(
            columns={"COD_IF": "ATIVO"}
        )

        # df carteira com liquidez e percentual de liquidez da carteira
        df_liquidez = pd.merge(df_carteira, df_base_b3, on="ATIVO", how="left")
        df_liquidez["LIQUIDEZ_ATIVO_CARTEIRA"] = (
            df_liquidez["PREMISSA_VENDA"] / df_liquidez["FINANCEIRO"]
        )
        df_liquidez["PREMISSA_VENDA"] = df_liquidez["PREMISSA_VENDA"].apply(
            lambda x: 0 if pd.isnull(x) else x
        )
        df_liquidez["LIQUIDEZ_ATIVO_CARTEIRA"] = df_liquidez[
            "LIQUIDEZ_ATIVO_CARTEIRA"
        ].apply(lambda x: 0 if pd.isnull(x) else x)
        df_liquidez["LIQUIDEZ_ATIVO_CARTEIRA"] = df_liquidez[
            "LIQUIDEZ_ATIVO_CARTEIRA"
        ].apply(lambda x: 1 if x > 1 else x)

        df_liquidez.insert(3, "TIPO_LIQUIDEZ", "Mercado observável")

        self.df_liquidez_mercado_observavel = df_liquidez.copy()

    def titulos_publicos(self, lista_tipo_ativos: list):
        """
        Cria DataFrame 'df_liquidez_titulos_publicos' contendo dados de liquidez dos ativos em carteira que compõem o mercado de títulos públicos.

        Args:
            lista_tipo_ativos (list): Lista de TIPO_ATIVO que compõem títulos públicos.

        """

        str_lista_tipo_ativos = "', '".join(lista_tipo_ativos)

        df = self.manager_sql.select_dataframe(
            f"SELECT REFDATE, FUNDO, TIPO_ATIVO, ATIVO, ROUND(SUM(FINANCEIRO_D0),2) [FINANCEIRO] FROM TB_CARTEIRAS "
            f"WHERE REFDATE = '{self.refdate}' AND TIPO_ATIVO IN ('{str_lista_tipo_ativos}') AND QUANTIDADE_D0 > 0 "
            f"GROUP BY REFDATE, FUNDO, TIPO_ATIVO, ATIVO"
        )

        df["PREMISSA_VENDA"] = df["FINANCEIRO"]
        df["LIQUIDEZ_ATIVO_CARTEIRA"] = 1
        df.insert(3, "TIPO_LIQUIDEZ", "Títulos Públicos")

        self.df_liquidez_titulos_publicos = df.copy()

    def run_all(self, refdate: date, dict_tipo_ativos: dict = None):
        """
        Cria DataFrame 'df_liquidez_all' contendo dados de liquidez dos ativos em carteira.

        Args:
            dict_tipo_ativos (dict): Dicionário contendo lista de TIPO_ATIVO que compõem mercado observável, títulos públicos.

        """

        def set_dict_listas_tipo_ativos():

            dict_lista_tipo_ativos = {
                "mercado_observavel": ["Debênture"],
                "titulos_publicos": ["Tit. Publicos", "Compromissada"],
            }

            return dict_lista_tipo_ativos

        self.set_refdate(refdate)

        dict_aux_tipo_ativos = (
            dict_tipo_ativos
            if dict_tipo_ativos is not None
            else set_dict_listas_tipo_ativos()
        )

        self.mercado_observavel(
            lista_tipo_ativos=dict_aux_tipo_ativos["mercado_observavel"]
        )
        self.titulos_publicos(
            lista_tipo_ativos=dict_aux_tipo_ativos["titulos_publicos"]
        )

        self.df_liquidez_all = pd.concat(
            [self.df_liquidez_mercado_observavel, self.df_liquidez_mercado_observavel]
        )
