import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

def conectar_banco():
    return sqlite3.connect("sistema.db")

def carregar_requisicoes(data_inicio, data_fim, codigo_funcionario=None):
    conn = conectar_banco()
    if codigo_funcionario:
        query = """
            SELECT codigo_funcionario, codigo_requisicao, data FROM REQUISICOES
            WHERE codigo_funcionario = ? AND date(data) BETWEEN date(?) AND date(?)
            ORDER BY data DESC
        """
        df = pd.read_sql(query, conn, params=(codigo_funcionario, data_inicio, data_fim))
    else:
        query = """
            SELECT codigo_funcionario, codigo_requisicao, data FROM REQUISICOES
            WHERE date(data) BETWEEN date(?) AND date(?)
            ORDER BY data DESC
        """
        df = pd.read_sql(query, conn, params=(data_inicio, data_fim))
    conn.close()
    return df

def app():
    st.markdown("<h1 style='text-align:center;'>📑 Relatório de Requisições</h1>", unsafe_allow_html=True)

    tipo_relatorio = st.radio("Escolha o tipo de relatório:", ["Relatório Geral", "Relatório por Crachá"])

    data_inicio = st.date_input("📅 Data Início")
    data_fim = st.date_input("📅 Data Fim")

    if data_inicio > data_fim:
        st.error("⚠️ Data inicial não pode ser posterior à data final.")
        return

    # Inicializando df vazio para evitar erros
    df = pd.DataFrame()

    if tipo_relatorio == "Relatório por Crachá":
        funcionarios_df = pd.read_sql("SELECT nome, codigo FROM FUNCIONARIOS", conectar_banco())
        funcionario_selecionado = st.selectbox("Selecione o funcionário:", funcionarios_df["nome"].tolist())
        codigo_funcionario = funcionarios_df.loc[funcionarios_df['nome'] == funcionario_selecionado, 'codigo'].iloc[0]

        df = carregar_requisicoes(data_inicio, data_fim, codigo_funcionario)

        if not df.empty:
            total = df.shape[0]
            st.success(f"✅ Total de requisições do crachá {funcionario_selecionado} no período: {total}")
        else:
            st.info("ℹ️ Nenhuma requisição encontrada para o funcionário selecionado neste período.")

    elif tipo_relatorio == "Relatório Geral":
        df = carregar_requisicoes(data_inicio, data_fim)

        if not df.empty:
            total = df.shape[0]
            st.success(f"✅ Total de requisições no período: {total}")
        else:
            st.info("📌 Nenhuma requisição encontrada no período selecionado.")

    # Exibir o DataFrame apenas se não estiver vazio
    if not df.empty:
        st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    app()
