import pandas as pd
import streamlit as st


# Simular acesso a dados
class SQL_Manager:
    def select_dataframe(self, query):
        if "TIPO_ATIVO" in query:
            return pd.DataFrame({"TIPO_ATIVO": ["Ação", "Bônus", "CDB"]})
        elif "ATIVOS" in query:
            tipo_ativo = query.split("'")[1]  # Extrai o tipo ativo da query
            return pd.DataFrame({"ATIVO": [f"Ativo de {tipo_ativo} 1", f"Ativo de {tipo_ativo} 2"]})

if 'manager_sql' not in st.session_state:
    st.session_state.manager_sql = SQL_Manager()

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame({
        "Trade date": [pd.Timestamp('today').date()],
        "Fundo": [None],
        "Tipo Ativo": [None],
        "Ativo": [None],
        "Quantidade": [None],
        "PU": [None],
        "Taxa": [None]
    })

tipo_ativo_options = st.session_state.manager_sql.select_dataframe(
    "SELECT DISTINCT TIPO_ATIVO FROM TB_CADASTRO_ATIVOS ORDER BY TIPO_ATIVO"
)['TIPO_ATIVO'].tolist()

st.session_state.df['Tipo Ativo'] = st.selectbox("Tipo Ativo", tipo_ativo_options)

# Atualizando os ativos com base no tipo selecionado
if st.session_state.df['Tipo Ativo'][0]:
    ativos_options = st.session_state.manager_sql.select_dataframe(
        f"SELECT DISTINCT ATIVO FROM TB_CADASTRO_ATIVOS WHERE TIPO_ATIVO = '{st.session_state.df['Tipo Ativo'][0]}' ORDER BY ATIVO"
    )['ATIVO'].tolist()
    st.session_state.df['Ativo'] = st.selectbox("Ativo", ativos_options)

# Editando o DataFrame
quantidade = st.number_input("Quantidade", value=float(st.session_state.df['Quantidade'][0] or 0))
st.session_state.df['Quantidade'][0] = quantidade

# Exibir DataFrame atualizado
st.dataframe(st.session_state.df)
