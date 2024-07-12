from __init__ import *

VERSION_APP = "1.1.1"
VERSION_REFDATE = "2024-07-10"
ENVIRONMENT = os.getenv("ENVIRONMENT")
SCRIPT_NAME = os.path.basename(__file__)

if ENVIRONMENT == "DEVELOPMENT":
    print(f"{SCRIPT_NAME.upper()} - {ENVIRONMENT} - {VERSION_APP} - {VERSION_REFDATE}")

append_paths()

# -----------------------------------------------------------------------

from datetime import date
from decimal import Decimal

import numpy as np
import pandas as pd
import QuantLib as ql

from tools.db_helper import SQL_Manager
from tools.my_logger import Logger
from tools.py_tools import FuncoesPyTools

# -----------------------------------------------------------------------


class calculadoraAtivos:

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
            log_message=f"calculadoraAtivos - {VERSION_APP} - {ENVIRONMENT} - Instanciado",
            script_original=SCRIPT_NAME,
        )

        self.controle_update_dados_ativos_fluxo_pagamento = False
        self.status_check_pre_dados = False
        self.tipo_ativos_fluxo_pagamento = [
            "CCB",
            "Debênture",
            "LF",
            "LFSC",
            "LFSN",
            "LFSN-PRE",
            "CDB",
        ]
        self.indexadores = ["CDI", "SELIC"]

    def update_dados_ativos_fluxo_pagamento(self, refdate):

        def update_taxas(refdate, tipos_formatados):

            df_taxa_anbima = self.manager_sql.select_dataframe(
                f"SELECT DISTINCT COD_ATIVO AS ATIVO, TAXA_INDICATIVA AS TAXA_ANBIMA FROM TB_ANBIMA_DEBENTURES WHERE REFDATE = '{self.funcoes_pytools.convert_data_sql(refdate)}' AND TAXA_INDICATIVA IS NOT NULL"
            )

            df_taxa_btg = self.manager_sql.select_dataframe(
                f"SELECT DISTINCT ATIVO, TAXA*100 AS TAXA_BTG FROM TB_PRECOS WHERE REFDATE = '{self.funcoes_pytools.convert_data_sql(refdate)}' AND FONTE = 'BTG' AND TAXA IS NOT NULL AND TIPO_ATIVO IN ({tipos_formatados})"
            )

            df_taxa_emissao = self.manager_sql.select_dataframe(
                f"SELECT DISTINCT ATIVO, TAXA_EMISSAO FROM TB_CADASTRO_ATIVOS WHERE TIPO_ATIVO IN ({tipos_formatados})"
            )

            df_ativos = pd.concat(
                [
                    df_taxa_anbima["ATIVO"],
                    df_taxa_btg["ATIVO"],
                    df_taxa_emissao["ATIVO"],
                ]
            ).drop_duplicates()
            df_taxas_ativos_fluxo_pagamento = pd.merge(
                df_ativos, df_taxa_anbima, on="ATIVO", how="left"
            )
            df_taxas_ativos_fluxo_pagamento = pd.merge(
                df_taxas_ativos_fluxo_pagamento, df_taxa_btg, on="ATIVO", how="left"
            )
            df_taxas_ativos_fluxo_pagamento = pd.merge(
                df_taxas_ativos_fluxo_pagamento, df_taxa_emissao, on="ATIVO", how="left"
            )
            df_taxas_ativos_fluxo_pagamento.loc[:, "TAXA"] = (
                df_taxas_ativos_fluxo_pagamento.apply(
                    lambda x: (
                        x["TAXA_ANBIMA"]
                        if not np.isnan(x["TAXA_ANBIMA"])
                        else (
                            x["TAXA_BTG"]
                            if not np.isnan(x["TAXA_BTG"])
                            else x["TAXA_EMISSAO"]
                        )
                    ),
                    axis=1,
                )
            )
            dict_taxas_ativos_fluxo_pagamento = (
                df_taxas_ativos_fluxo_pagamento.set_index("ATIVO")["TAXA"].to_dict()
            )

            return dict_taxas_ativos_fluxo_pagamento

        def update_cadastro(tipos_formatados):

            df_cadastro_ativos = self.manager_sql.select_dataframe(
                f"SELECT DISTINCT TIPO_ATIVO, ATIVO, INDEXADOR, DATA_INICIO_RENTABILDIADE FROM TB_CADASTRO_ATIVOS \
                WHERE TIPO_ATIVO IN ({tipos_formatados})"
            )

            dict_indexadores_ativos_fluxo_pagamento = df_cadastro_ativos.set_index(
                "ATIVO"
            )["INDEXADOR"].to_dict()
            dict_tipo_ativo_fluxo_pagamento = df_cadastro_ativos.set_index("ATIVO")[
                "TIPO_ATIVO"
            ].to_dict()
            dict_inicio_rentabilidade_fluxo_pagamento = df_cadastro_ativos.set_index(
                "ATIVO"
            )["DATA_INICIO_RENTABILDIADE"].to_dict()

            return (
                dict_indexadores_ativos_fluxo_pagamento,
                dict_tipo_ativo_fluxo_pagamento,
                dict_inicio_rentabilidade_fluxo_pagamento,
            )

        def update_fluxo_pagamentos(tipos_formatados):

            df_fluxo_all = self.manager_sql.select_dataframe(
                f"SELECT DISTINCT ATIVO, DATA_LIQUIDACAO, EVENTO, PERCENTUAL, VNA from TB_FLUXO_PAGAMENTO_ATIVOS WHERE TIPO_ATIVO IN ({tipos_formatados}) ORDER BY ATIVO, DATA_LIQUIDACAO, EVENTO"
            )

            ativos = df_fluxo_all["ATIVO"].unique()

            dict_df_fluxo_pagamentos = {}

            for ativo in ativos:
                dict_df_fluxo_pagamentos[ativo] = df_fluxo_all[
                    df_fluxo_all["ATIVO"] == ativo
                ]

            return dict_df_fluxo_pagamentos

        def update_interpolacao(refdate):

            df_curvas = self.manager_sql.select_dataframe(
                f"SELECT DISTINCT CURVA, DIAS_CORRIDOS, TAXA_252 FROM TB_CURVAS WHERE REFDATE = '{self.funcoes_pytools.convert_data_sql(refdate)}' AND CURVA IN ('PRE_DI', 'DI1FUT', 'DI X PRE') ORDER BY CURVA, DIAS_CORRIDOS"
            )

            curvas = df_curvas["CURVA"].unique()

            dict_interpolacao = {}
            for curva in curvas:
                df_curva = (
                    df_curvas[df_curvas["CURVA"] == curva].copy().reset_index(drop=True)
                )
                rows = df_curva[["DIAS_CORRIDOS", "TAXA_252"]].values.tolist()
                X = [float(row[0]) for row in rows]
                Y = [float(row[1]) for row in rows]
                dict_interpolacao[curva] = ql.LinearInterpolation(X, Y)

            return dict_interpolacao

        def update_cota_indexadores(refdate):

            self.check_indexadores = []

            dict_indexadores = {}

            for indexador in self.indexadores:
                df_indexador = self.manager_sql.select_dataframe(
                    f"SELECT DISTINCT REFDATE, COTA_INDEXADOR FROM TB_INDEXADORES WHERE INDEXADOR = '{indexador}' ORDER BY REFDATE"
                )

                if (
                    self.funcoes_pytools.workday_br(refdate, -1)
                    in df_indexador["REFDATE"].values
                ):
                    dict_indexadores[indexador] = df_indexador
                else:
                    self.check_indexadores.append(indexador)

            return dict_indexadores

        def update_rent_dia_indexadores():

            dict_rent_dia_indexadores = {}

            for indexador in self.indexadores:
                df_indexador = self.manager_sql.select_dataframe(
                    f"SELECT DISTINCT REFDATE, VALOR_DIA FROM TB_INDEXADORES WHERE INDEXADOR = '{indexador}' ORDER BY REFDATE"
                )
                dict_rent_dia_indexadores[indexador] = df_indexador

            return dict_rent_dia_indexadores

        tipos_formatados = "', '".join(self.tipo_ativos_fluxo_pagamento)
        tipos_formatados = f"'{tipos_formatados}'"

        (
            self.dict_indexadores_ativos_fluxo_pagamento,
            self.dict_tipo_ativo_fluxo_pagamento,
            self.dict_inicio_rentabilidade_fluxo_pagamento,
        ) = update_cadastro(tipos_formatados)
        self.dict_taxas_ativos_fluxo_pagamento = update_taxas(
            refdate=refdate, tipos_formatados=tipos_formatados
        )
        self.dict_fluxo_pagamentos = update_fluxo_pagamentos(
            tipos_formatados=tipos_formatados
        )
        self.dict_interpolacao = update_interpolacao(refdate=refdate)
        self.dict_cota_indexadores = update_cota_indexadores(refdate=refdate)
        self.dict_rent_dia_indexadores = update_rent_dia_indexadores()

        # print("Dados atualizados com sucesso!")

    def taxa_interpolada(self, curva, dias):
        try:
            interp_tx = self.dict_interpolacao[curva](dias)
            return self.funcoes_pytools.trunc_number(interp_tx, 2)
        except Exception as e:
            print(f"Erro ao calcular taxa interpolada: {e}")
            return 0

    def captura_rent_indexador(self, data_inicio, data_fim, nomeIndexador):

        df = self.dict_cota_indexadores[nomeIndexador]

        cota_inicio_indexador = df[(df["REFDATE"] == data_inicio)][
            "COTA_INDEXADOR"
        ].reset_index(drop=True)[0]
        cota_fim_indexador = df[(df["REFDATE"] == data_fim)][
            "COTA_INDEXADOR"
        ].reset_index(drop=True)[0]

        rent_indexador = cota_fim_indexador / cota_inicio_indexador
        return rent_indexador

    def valor_amortizacao(self, df):

        if len(df) == 0:
            return 0

        vna = df["VNA"][0]
        percentual_amortizacao = df["PERCENTUAL"][0]
        valoramortizacao = self.funcoes_pytools.trunc_number(
            vna * percentual_amortizacao / 100, 6
        )
        return valoramortizacao

    def fator_juros(self, data_referencia, data_fluxo, ativo, df_fluxo_pagamento_ativo):

        data_ult_pagamento = df_fluxo_pagamento_ativo[
            (df_fluxo_pagamento_ativo["EVENTO"] == "Pagamento de juros")
            & (df_fluxo_pagamento_ativo["DATA_LIQUIDACAO"] <= data_referencia)
        ]["DATA_LIQUIDACAO"].max()

        if pd.isna(data_ult_pagamento):
            data_ult_pagamento = self.dict_inicio_rentabilidade_fluxo_pagamento[ativo]

        juros_ativo = df_fluxo_pagamento_ativo[
            (df_fluxo_pagamento_ativo["EVENTO"] == "Pagamento de juros")
            & (df_fluxo_pagamento_ativo["DATA_LIQUIDACAO"] == data_fluxo)
        ]["PERCENTUAL"].reset_index(drop=True)

        if len(juros_ativo) == 0:
            return 0
        else:
            juros_ativo = juros_ativo[0]

        if self.dict_indexadores_ativos_fluxo_pagamento[ativo] in ["CDI +", "SELIC +"]:

            index_acum = self.captura_rent_indexador(
                self.funcoes_pytools.workday_br(data_ult_pagamento, -1),
                self.funcoes_pytools.workday_br(data_referencia, -1),
                self.dict_indexadores_ativos_fluxo_pagamento[ativo][:-2],
            )

            n_dias = self.funcoes_pytools.networkdays_br(
                data_ult_pagamento, data_referencia
            )

            cdi_acum = round(index_acum, 8)
            spread = round((1 + (juros_ativo / 100)) ** (n_dias / 252), 9)

            fator = round(cdi_acum * spread, 9)

            return fator

        elif self.dict_indexadores_ativos_fluxo_pagamento[ativo] in [
            "CDI %",
            "SELIC %",
        ]:

            data_fim_indexador = self.funcoes_pytools.workday_br(data_referencia, -1)

            df = self.dict_rent_dia_indexadores[
                self.dict_indexadores_ativos_fluxo_pagamento[ativo][:-2]
            ]

            lista_indexador = df[
                (df["REFDATE"] >= data_ult_pagamento)
                & (df["REFDATE"] <= data_fim_indexador)
            ]["VALOR_DIA"].tolist()

            cota_indexador = 1

            for row in lista_indexador:
                rent_dia = row * (juros_ativo / 100) + 1
                cota_indexador = cota_indexador * rent_dia

            fator = cota_indexador

            return round(fator, 9)

        elif self.dict_indexadores_ativos_fluxo_pagamento[ativo] in ["PRE"]:

            du = self.funcoes_pytools.networkdays_br(
                data_ult_pagamento, data_referencia
            )
            juros_ativo_dia = (1 + (juros_ativo / 100)) ** (1 / 252)
            fator = (juros_ativo_dia) ** (du)
            return round(fator, 9)

    def primeiro_juros(
        self, data_referencia, data_fluxo, ativo, df_fluxo_pagamento_ativo
    ):

        fatorjuros = self.fator_juros(
            data_referencia, data_fluxo, ativo, df_fluxo_pagamento_ativo
        )

        if fatorjuros == 0:
            return 0

        data_prox_pagto = data_fluxo

        df = df_fluxo_pagamento_ativo[
            (df_fluxo_pagamento_ativo["EVENTO"] == "Pagamento de juros")
            & (df_fluxo_pagamento_ativo["DATA_LIQUIDACAO"] == data_fluxo)
        ][["PERCENTUAL", "VNA"]].reset_index(drop=True)

        vna = df["VNA"][0]
        juros_ativo = df["PERCENTUAL"][0]
        taxa_interp = self.taxa_interpolada(
            self.curva_interpolacao,
            self.funcoes_pytools.dias_corridos(data_referencia, data_prox_pagto),
        )
        du = self.funcoes_pytools.networkdays_br(data_referencia, data_prox_pagto)

        exp_dia = (1 + (taxa_interp / 100)) ** (1 / 252)

        if self.dict_indexadores_ativos_fluxo_pagamento[ativo] in ["CDI +", "SELIC +"]:
            juros_ativo_dia = (1 + (juros_ativo / 100)) ** (1 / 252)
            exp_juros_dia = (exp_dia * juros_ativo_dia) ** du
            a = exp_juros_dia * fatorjuros
            valor = (a - 1) * vna
            return self.funcoes_pytools.trunc_number(valor, 6)

        elif self.dict_indexadores_ativos_fluxo_pagamento[ativo] in [
            "CDI %",
            "SELIC %",
        ]:
            a = ((exp_dia - 1) * (juros_ativo / 100) + 1) ** du
            a = (a * fatorjuros) - 1
            valor = a * vna
            return self.funcoes_pytools.trunc_number(valor, 6)

        elif self.dict_indexadores_ativos_fluxo_pagamento[ativo] == "PRE":
            juros_ativo_dia = (1 + (juros_ativo / 100)) ** (1 / 252)
            exp_juros_dia = (juros_ativo_dia) ** du
            a = exp_juros_dia * fatorjuros
            valor = (a - 1) * vna

            return self.funcoes_pytools.trunc_number(valor, 6)

    def prox_juros(self, data_referencia, data_fluxo, ativo, df_fluxo_pagamento_ativo):

        data_anterior = df_fluxo_pagamento_ativo[
            (df_fluxo_pagamento_ativo["EVENTO"] == "Pagamento de juros")
            & (df_fluxo_pagamento_ativo["DATA_LIQUIDACAO"] < data_fluxo)
        ]["DATA_LIQUIDACAO"].max()

        df = df_fluxo_pagamento_ativo[
            (df_fluxo_pagamento_ativo["EVENTO"] == "Pagamento de juros")
            & (df_fluxo_pagamento_ativo["DATA_LIQUIDACAO"] == data_fluxo)
        ][["PERCENTUAL", "VNA"]].reset_index(drop=True)

        vna = df["VNA"][0]
        juros_ativo = df["PERCENTUAL"][0]
        juros_ativo = juros_ativo / 100

        taxa_interpolada_anterior = self.taxa_interpolada(
            self.curva_interpolacao,
            self.funcoes_pytools.dias_corridos(data_referencia, data_anterior),
        )
        taxa_interpolada_anterior_dia = (1 + (taxa_interpolada_anterior / 100)) ** (
            1 / 252
        )

        taxa_interpolada_fluxo = self.taxa_interpolada(
            self.curva_interpolacao,
            self.funcoes_pytools.dias_corridos(data_referencia, data_fluxo),
        )
        taxa_interpolada_fluxo_dia = (1 + (taxa_interpolada_fluxo / 100)) ** (1 / 252)

        du = self.funcoes_pytools.networkdays_br(data_referencia, data_anterior)
        du_dmais = self.funcoes_pytools.networkdays_br(data_referencia, data_fluxo)

        if self.dict_indexadores_ativos_fluxo_pagamento[ativo] in ["CDI +", "SELIC +"]:
            juros_ativo_dia = (1 + juros_ativo) ** (1 / 252)
            j = (taxa_interpolada_anterior_dia * juros_ativo_dia) ** du
            j_mais = (taxa_interpolada_fluxo_dia * juros_ativo_dia) ** du_dmais
            jj = j_mais / j - 1
            termo = self.funcoes_pytools.trunc_number(vna * jj, 6)
            return termo

        elif self.dict_indexadores_ativos_fluxo_pagamento[ativo] in [
            "CDI %",
            "SELIC %",
        ]:
            a = (((taxa_interpolada_fluxo_dia - 1) * juros_ativo) + 1) ** du_dmais
            b = (((taxa_interpolada_anterior_dia - 1) * juros_ativo) + 1) ** du
            termo = self.funcoes_pytools.trunc_number(vna * (a / b - 1), 6)
            return termo

    def upload_ativosFluxoPagamentos(
        self, refdate, ativo, lista_fluxo, pu_calculado, taxa
    ):

        self.manager_sql.delete_records(
            "TB_FLUXO_FUTURO_ATIVOS",
            f"REFDATE = '{self.funcoes_pytools.convert_data_sql(refdate)}' AND ATIVO = '{ativo}'",
        )
        df_upload = pd.DataFrame(
            lista_fluxo,
            columns=[
                "REFDATE",
                "TIPO_ATIVO",
                "ATIVO",
                "DATA_LIQUIDACAO",
                "EXP_JUROS",
                "JUROS_PROJETADO_ATIVO",
                "AMORTIZACAO_ATIVO",
                "FLUXO_DESCONTADO",
            ],
        )
        self.manager_sql.insert_dataframe(df_upload, "TB_FLUXO_FUTURO_ATIVOS")

        self.manager_sql.delete_records(
            "TB_PRECOS",
            f"REFDATE = '{self.funcoes_pytools.convert_data_sql(refdate)}' AND ATIVO = '{ativo}' AND FONTE = 'RISCO'",
        )
        df_pu_calculado = pd.DataFrame(
            {
                "REFDATE": [refdate],
                "TIPO_ATIVO": [self.dict_tipo_ativo_fluxo_pagamento[ativo]],
                "ATIVO": [ativo],
                "PU": [pu_calculado],
                "PU_LIMPO_BONDS": [np.nan],
                "FONTE": ["RISCO"],
                "TAXA": [taxa],
            }
        )
        self.manager_sql.insert_dataframe(df_pu_calculado, "TB_PRECOS")

    def check_dados_run(self, ativo):

        check_missing = []

        if self.curva_interpolacao not in self.dict_interpolacao.keys():
            check_missing.append(f"Curva: {self.curva_interpolacao}")

        if ativo not in self.dict_fluxo_pagamentos.keys():
            check_missing.append(f"FLuxo de pagamento: {ativo}")

        if ativo not in self.dict_taxas_ativos_fluxo_pagamento.keys():
            check_missing.append(f"Taxa ativo: {ativo}")

        if len(check_missing) == 0:
            return True
        else:
            return " | ".join(check_missing)

    def ativosFluxoPagamentos(
        self, data_referencia, ativo, curva_interpolacao="DI1FUT"
    ):

        if not self.controle_update_dados_ativos_fluxo_pagamento:
            self.update_dados_ativos_fluxo_pagamento(data_referencia)
            self.controle_update_dados_ativos_fluxo_pagamento = True

        self.curva_interpolacao = curva_interpolacao

        if len(self.check_indexadores) != 0:
            return f"Erro Indexador: {', '.join(self.check_indexadores)}"

        check_dados_run = self.check_dados_run(ativo)

        if check_dados_run != True:
            # print(f"Erro ao calcular para {ativo}: {self.check_dados_run(ativo)}")
            return check_dados_run

        taxa_papel = self.funcoes_pytools.trunc_number(
            self.dict_taxas_ativos_fluxo_pagamento[ativo], 4
        )

        df_fluxo_pagamento_ativo = self.dict_fluxo_pagamentos[ativo]

        data_primeiro_juros = df_fluxo_pagamento_ativo[
            (df_fluxo_pagamento_ativo["EVENTO"] == "Pagamento de juros")
            & (df_fluxo_pagamento_ativo["DATA_LIQUIDACAO"] > data_referencia)
        ]["DATA_LIQUIDACAO"].min()

        fluxo_datas = df_fluxo_pagamento_ativo[
            df_fluxo_pagamento_ativo["DATA_LIQUIDACAO"] > data_referencia
        ]["DATA_LIQUIDACAO"].unique()

        # print(f"Calculando para {ativo}...")

        pu_ativo = Decimal("0")
        lista_total = []

        for data in fluxo_datas:
            lista_temp = []

            amortizacao = self.valor_amortizacao(
                df_fluxo_pagamento_ativo.loc[
                    (df_fluxo_pagamento_ativo["DATA_LIQUIDACAO"] == data)
                    & (
                        (df_fluxo_pagamento_ativo["EVENTO"] == "Amortizacao")
                        | (df_fluxo_pagamento_ativo["EVENTO"] == "Vencimento (resgate)")
                        | (
                            df_fluxo_pagamento_ativo["EVENTO"]
                            == "Resgate total antecipado"
                        )
                    ),
                    ["PERCENTUAL", "VNA"],
                ].reset_index(drop=True)
            )

            taxa_interp = self.taxa_interpolada(
                self.curva_interpolacao,
                self.funcoes_pytools.dias_corridos(data_referencia, data),
            )

            if data == data_primeiro_juros:
                valorjuros = self.primeiro_juros(
                    data_referencia, data, ativo, df_fluxo_pagamento_ativo
                )
            else:
                valorjuros = self.prox_juros(
                    data_referencia, data, ativo, df_fluxo_pagamento_ativo
                )

            sum_a_j = amortizacao + valorjuros
            du = self.funcoes_pytools.networkdays_br(data_referencia, data)

            if self.dict_indexadores_ativos_fluxo_pagamento[ativo] in [
                "CDI +",
                "SELIC +",
            ]:
                taxa_inter_dia = (1 + (taxa_interp / 100)) ** (du / 252)
                taxa_papel_dia = (1 + (taxa_papel / 100)) ** (du / 252)
                preco_ajustado = Decimal(
                    f"{self.funcoes_pytools.trunc_number(sum_a_j / (taxa_inter_dia * taxa_papel_dia), 6)}"
                )

            elif self.dict_indexadores_ativos_fluxo_pagamento[ativo] in [
                "CDI %",
                "SELIC %",
            ]:
                a = (((1 + (taxa_interp / 100)) ** (1 / 252)) - 1) * (
                    taxa_papel / 100
                ) + 1
                a = a**du
                preco_ajustado = Decimal(
                    f"{self.funcoes_pytools.trunc_number(sum_a_j / a, 6)}"
                )

            elif self.dict_indexadores_ativos_fluxo_pagamento[ativo] in ["PRE"]:
                taxa_papel_dia = (1 + (taxa_papel / 100)) ** (du / 252)
                preco_ajustado = Decimal(
                    f"{self.funcoes_pytools.trunc_number(sum_a_j / taxa_papel_dia, 6)}"
                )

            pu_ativo += preco_ajustado

            lista_temp.append(self.funcoes_pytools.convert_data_sql(data_referencia))
            lista_temp.append(self.dict_tipo_ativo_fluxo_pagamento[ativo])
            lista_temp.append(ativo)
            lista_temp.append(self.funcoes_pytools.convert_data_sql(data))
            lista_temp.append(taxa_interp)
            lista_temp.append(valorjuros)
            lista_temp.append(amortizacao)
            lista_temp.append(preco_ajustado)

            lista_total.append(lista_temp)

        self.upload_ativosFluxoPagamentos(
            data_referencia, ativo, lista_total, pu_ativo, taxa_papel
        )

        return "ok"

    def durationAtivos(self, refdate, ativo_calc=None):

        def uploadBase(df, refdate, ativo=None):

            result = {}

            try:
                if ativo is None:
                    self.manager_sql.delete_records(
                        "TB_RISCO_DURATION",
                        f"REFDATE = '{refdate.strftime('%Y-%m-%d')}'",
                    )
                    self.manager_sql.insert_dataframe(df, "TB_RISCO_DURATION")
                    result["Duration Ativos"] = "ok"
                else:
                    self.manager_sql.delete_records(
                        "TB_RISCO_DURATION",
                        f"REFDATE = '{refdate.strftime('%Y-%m-%d')}' AND ATIVO = '{ativo}'",
                    )
                    self.manager_sql.insert_dataframe(df, "TB_RISCO_DURATION")
                    result[f"Duration {ativo}"] = "ok"

                return result
            except Exception as e:
                if ativo is None:
                    result["Duration Ativos"] = f"Erro --> {e}"
                else:
                    result[f"Duration {ativo}"] = f"Erro --> {e}"
                return result

        df_ativos = pd.DataFrame(
            {
                "REFDATE": pd.Series(dtype="datetime64[ns]"),
                "TIPO_ATIVO": pd.Series(dtype="str"),
                "ATIVO": pd.Series(dtype="str"),
                "DURATION": pd.Series(dtype="int"),
            }
        )

        if ativo_calc is None:
            df_fluxo = self.manager_sql.select_dataframe(
                f"SELECT REFDATE, TIPO_ATIVO, ATIVO, DATA_LIQUIDACAO, FLUXO_DESCONTADO FROM TB_FLUXO_FUTURO_ATIVOS WHERE REFDATE = '{refdate.strftime('%Y-%m-%d')}'"
            )
        else:
            df_fluxo = self.manager_sql.select_dataframe(
                f"SELECT REFDATE, TIPO_ATIVO, ATIVO, DATA_LIQUIDACAO, FLUXO_DESCONTADO FROM TB_FLUXO_FUTURO_ATIVOS WHERE REFDATE = '{refdate.strftime('%Y-%m-%d')}' AND ATIVO = '{ativo_calc}'"
            )

        ativos = df_fluxo["ATIVO"].unique()

        df_fluxo["REFDATE"] = pd.to_datetime(df_fluxo["REFDATE"]).dt.date
        df_fluxo["DATA_LIQUIDACAO"] = pd.to_datetime(
            df_fluxo["DATA_LIQUIDACAO"]
        ).dt.date
        df_fluxo["NETWORKDAYS"] = df_fluxo.apply(
            lambda x: self.funcoes_pytools.networkdays_br(
                x["REFDATE"], x["DATA_LIQUIDACAO"]
            ),
            axis=1,
        )

        for ativo in ativos:
            df_ativo = df_fluxo[df_fluxo["ATIVO"] == ativo].copy()
            total_fluxo = df_ativo["FLUXO_DESCONTADO"].sum()
            df_ativo.loc[:, "PERC"] = (
                df_ativo["FLUXO_DESCONTADO"] / total_fluxo * df_ativo["NETWORKDAYS"]
            )
            duration = int(round(df_ativo["PERC"].sum(), 0))
            df_ativo = df_ativo[["REFDATE", "TIPO_ATIVO", "ATIVO"]].drop_duplicates()
            df_ativo["DURATION"] = duration
            df_ativo = df_ativo[["REFDATE", "TIPO_ATIVO", "ATIVO", "DURATION"]]
            df_ativos = pd.concat([df_ativos, df_ativo])

        check_upload = uploadBase(df_ativos, refdate, ativo_calc)

        return check_upload

    def reconPrecos(self, refdate):

        str_tipos_ativos = ", ".join(
            [f"'{tipo}'" for tipo in self.tipo_ativos_fluxo_pagamento]
        )

        df_dados_precos = self.manager_sql.select_dataframe(
            f"SELECT DISTINCT REFDATE, TIPO_ATIVO, ATIVO, PU, FONTE FROM TB_PRECOS \
                WHERE REFDATE = '{self.funcoes_pytools.convert_data_sql(refdate)}' \
                AND FONTE IN ('BTG', 'RISCO') AND TIPO_ATIVO IN ({str_tipos_ativos})"
        )

        self.df_precos_btg = df_dados_precos.loc[
            df_dados_precos["FONTE"] == "BTG", ["REFDATE", "TIPO_ATIVO", "ATIVO", "PU"]
        ].rename(columns={"PU": "PU_BTG"})

        self.df_precos_risco = df_dados_precos.loc[
            df_dados_precos["FONTE"] == "RISCO",
            ["REFDATE", "TIPO_ATIVO", "ATIVO", "PU"],
        ].rename(columns={"PU": "PU_RISCO"})

        self.df_recon_precos = pd.merge(
            self.df_precos_btg,
            self.df_precos_risco,
            on=["REFDATE", "TIPO_ATIVO", "ATIVO"],
            how="inner",
        )

        self.df_recon_precos["Diferença"] = round(
            self.df_recon_precos["PU_BTG"] - self.df_recon_precos["PU_RISCO"], 4
        )

        self.df_recon_precos.rename(
            columns={
                "REFDATE": "Refdate",
                "TIPO_ATIVO": "Tipo Ativo",
                "ATIVO": "Ativo",
                "PU_BTG": "BTG",
                "PU_RISCO": "Risco",
            },
            inplace=True,
        )
