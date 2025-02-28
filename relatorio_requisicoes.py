"""
Módulo de relatório de requisições refatorado.
Permite gerar relatórios filtrados por período e setor, nos formatos sintético e analítico.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3

def conectar_banco():
    """Conecta ao banco de dados SQLite.
    
    Returns:
        sqlite3.Connection: Conexão com o banco de dados.
    """
    return sqlite3.connect("sistema.db")

def carregar_requisicoes(data_inicio, data_fim, setor=None, tipo_relatorio="analitico"):
    """Carrega requisições com base nos filtros informados.
    
    Args:
        data_inicio (str): Data inicial no formato YYYY-MM-DD.
        data_fim (str): Data final no formato YYYY-MM-DD.
        setor (str, optional): Setor para filtrar ou None para todos.
        tipo_relatorio (str, optional): "analitico" ou "sintetico".
        
    Returns:
        pandas.DataFrame: DataFrame com as requisições encontradas.
    """
    conn = conectar_banco()
    
    if tipo_relatorio == "analitico":
        # Relatório analítico - mostra todas as requisições detalhadas
        if setor:
            query = """
                SELECT f.nome, f.codigo AS codigo_funcionario, f.setor, 
                       r.codigo_requisicao, r.data
                FROM REQUISICOES r
                JOIN FUNCIONARIOS f ON r.codigo_funcionario = f.codigo
                WHERE f.setor = ? AND date(r.data) BETWEEN date(?) AND date(?)
                ORDER BY f.nome, r.data DESC
            """
            df = pd.read_sql(query, conn, params=(setor, data_inicio, data_fim))
        else:
            query = """
                SELECT f.nome, f.codigo AS codigo_funcionario, f.setor, 
                       r.codigo_requisicao, r.data
                FROM REQUISICOES r
                JOIN FUNCIONARIOS f ON r.codigo_funcionario = f.codigo
                WHERE date(r.data) BETWEEN date(?) AND date(?)
                ORDER BY f.nome, r.data DESC
            """
            df = pd.read_sql(query, conn, params=(data_inicio, data_fim))
    else:
        # Relatório sintético - agrupa por funcionário e conta requisições
        if setor:
            query = """
                SELECT f.nome, f.codigo AS codigo_funcionario, f.setor, 
                       COUNT(r.codigo_requisicao) AS total_requisicoes
                FROM FUNCIONARIOS f
                LEFT JOIN REQUISICOES r ON f.codigo = r.codigo_funcionario
                    AND date(r.data) BETWEEN date(?) AND date(?)
                WHERE f.setor = ?
                GROUP BY f.nome, f.codigo, f.setor
                ORDER BY f.nome
            """
            df = pd.read_sql(query, conn, params=(data_inicio, data_fim, setor))
        else:
            query = """
                SELECT f.nome, f.codigo AS codigo_funcionario, f.setor, 
                       COUNT(r.codigo_requisicao) AS total_requisicoes
                FROM FUNCIONARIOS f
                LEFT JOIN REQUISICOES r ON f.codigo = r.codigo_funcionario
                    AND date(r.data) BETWEEN date(?) AND date(?)
                GROUP BY f.nome, f.codigo, f.setor
                ORDER BY f.nome
            """
            df = pd.read_sql(query, conn, params=(data_inicio, data_fim))
            
    conn.close()
    return df

def obter_setores():
    """Obtém a lista de setores disponíveis no sistema.
    
    Returns:
        list: Lista de setores cadastrados.
    """
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT setor FROM FUNCIONARIOS ORDER BY setor")
    setores = [row[0] for row in cursor.fetchall()]
    conn.close()
    return setores

def app():
    """Função principal do módulo de relatórios."""
    st.markdown("<h1 style='text-align:center;'>📑 Relatório de Requisições</h1>", unsafe_allow_html=True)
    
    # Escolha do tipo de relatório (Sintético ou Analítico)
    tipo_relatorio = st.radio(
        "Escolha o tipo de relatório:", 
        ["Relatório Sintético", "Relatório Analítico"],
        help="Sintético: resumo por funcionário. Analítico: detalhes de cada requisição."
    )
    
    # Seleção do setor
    setores = obter_setores()
    opcoes_setor = ["Todos os Setores"] + setores
    setor_selecionado = st.selectbox("Selecione o Setor:", opcoes_setor)
    
    # Configuração do período (lado a lado)
    st.markdown("### Período")
    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input("📅 Data Início")
    with col2:
        data_fim = st.date_input("📅 Data Fim")
    
    # Validação de datas
    if data_inicio > data_fim:
        st.error("⚠️ Data inicial não pode ser posterior à data final.")
        return
    
    # Preparar parâmetros para consulta
    tipo_consulta = "sintetico" if tipo_relatorio == "Relatório Sintético" else "analitico"
    setor_filtro = None if setor_selecionado == "Todos os Setores" else setor_selecionado
    
    # Carregar dados
    df = carregar_requisicoes(data_inicio, data_fim, setor_filtro, tipo_consulta)
    
    # Exibir resultados
    if not df.empty:
        if tipo_consulta == "sintetico":
            # Mostrar totais para relatório sintético
            total_funcionarios = len(df)
            total_requisicoes = df["total_requisicoes"].sum()
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"📊 Total de funcionários: {total_funcionarios}")
            with col2:
                st.success(f"✅ Total de requisições no período: {total_requisicoes}")
                
            # Renomear colunas para melhor apresentação
            df_display = df.rename(columns={
                "nome": "Nome",
                "codigo_funcionario": "Código do Crachá",
                "setor": "Setor",
                "total_requisicoes": "Total de Requisições"
            })
            
            # Botão para download do relatório sintético em CSV
            csv = df_display.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Baixar Relatório (CSV)",
                csv,
                f"relatorio_sintetico_{data_inicio}_a_{data_fim}.csv",
                "text/csv",
                key="download-csv"
            )
            
        else:  # tipo_consulta == "analitico"
            # Mostrar totais para relatório analítico
            total_requisicoes = len(df)
            total_funcionarios = df["codigo_funcionario"].nunique()
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"👥 Funcionários envolvidos: {total_funcionarios}")
            with col2:
                st.success(f"✅ Total de requisições no período: {total_requisicoes}")
                
            # Renomear colunas para melhor apresentação
            df_display = df.rename(columns={
                "nome": "Nome",
                "codigo_funcionario": "Código do Crachá",
                "setor": "Setor",
                "codigo_requisicao": "Código da Requisição",
                "data": "Data e Hora"
            })
        
        # Exibir o dataframe formatado
        st.dataframe(df_display, use_container_width=True)
        
    else:
        setor_msg = f" no setor {setor_selecionado}" if setor_filtro else ""
        st.info(f"📌 Nenhuma requisição encontrada{setor_msg} no período selecionado.")

# Garantia que o script seja executado corretamente
if __name__ == "__main__":
    app()