"""
Módulo de relatório de requisições refatorado.
Permite gerar relatórios filtrados por período e setor, nos formatos sintético e analítico.
Agora com exportação para PDF.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3
import tempfile
from fpdf import FPDF
import base64

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

def create_download_link(val, filename):
    """Cria um link para download de um arquivo.
    
    Args:
        val (bytes): Conteúdo do arquivo em bytes
        filename (str): Nome do arquivo
        
    Returns:
        str: HTML com link para download
    """
    b64 = base64.b64encode(val)
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}">📥 Clique aqui para baixar o PDF</a>'

def gerar_pdf_sintetico(df, data_inicio, data_fim, setor_filtro, total_funcionarios, total_requisicoes):
    """Gera um PDF para o relatório sintético.
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados
        data_inicio (str): Data inicial
        data_fim (str): Data final
        setor_filtro (str): Setor selecionado ou None
        total_funcionarios (int): Total de funcionários
        total_requisicoes (int): Total de requisições
        
    Returns:
        bytes: Arquivo PDF em bytes
    """
    pdf = FPDF()
    pdf.add_page()
    
    # Configuração da fonte
    pdf.set_font("Arial", "B", 16)
    
    # Título do relatório
    pdf.cell(190, 10, "Relatório Sintético de Requisições", 0, 1, "C")
    pdf.set_font("Arial", "", 10)
    
    # Período e filtros
    pdf.cell(190, 10, f"Período: {data_inicio} a {data_fim}", 0, 1, "L")
    setor_texto = setor_filtro if setor_filtro else "Todos os Setores"
    pdf.cell(190, 10, f"Setor: {setor_texto}", 0, 1, "L")
    
    # Totais
    pdf.cell(190, 10, f"Total de funcionários: {total_funcionarios}", 0, 1, "L")
    pdf.cell(190, 10, f"Total de requisições no período: {total_requisicoes}", 0, 1, "L")
    
    # Tabela de dados
    pdf.ln(5)
    
    # Cabeçalho da tabela
    pdf.set_font("Arial", "B", 10)
    pdf.cell(60, 10, "Nome", 1, 0, "C")
    pdf.cell(40, 10, "Código do Crachá", 1, 0, "C")
    pdf.cell(50, 10, "Setor", 1, 0, "C")
    pdf.cell(40, 10, "Total Requisições", 1, 1, "C")
    
    # Conteúdo da tabela
    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        pdf.cell(60, 10, str(row["nome"])[:28], 1, 0, "L")
        pdf.cell(40, 10, str(row["codigo_funcionario"]), 1, 0, "C")
        pdf.cell(50, 10, str(row["setor"])[:24], 1, 0, "L")
        pdf.cell(40, 10, str(row["total_requisicoes"]), 1, 1, "C")
    
    # Rodapé
    pdf.set_y(-15)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", 0, 0, "C")
    
    return pdf.output(dest="S").encode("latin1")

def gerar_pdf_analitico(df, data_inicio, data_fim, setor_filtro, total_funcionarios, total_requisicoes):
    """Gera um PDF para o relatório analítico.
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados
        data_inicio (str): Data inicial
        data_fim (str): Data final
        setor_filtro (str): Setor selecionado ou None
        total_funcionarios (int): Total de funcionários
        total_requisicoes (int): Total de requisições
        
    Returns:
        bytes: Arquivo PDF em bytes
    """
    pdf = FPDF()
    pdf.add_page()
    
    # Configuração da fonte
    pdf.set_font("Arial", "B", 16)
    
    # Título do relatório
    pdf.cell(190, 10, "Relatório Analítico de Requisições", 0, 1, "C")
    pdf.set_font("Arial", "", 10)
    
    # Período e filtros
    pdf.cell(190, 10, f"Período: {data_inicio} a {data_fim}", 0, 1, "L")
    setor_texto = setor_filtro if setor_filtro else "Todos os Setores"
    pdf.cell(190, 10, f"Setor: {setor_texto}", 0, 1, "L")
    
    # Totais
    pdf.cell(190, 10, f"Funcionários envolvidos: {total_funcionarios}", 0, 1, "L")
    pdf.cell(190, 10, f"Total de requisições no período: {total_requisicoes}", 0, 1, "L")
    
    # Tabela de dados
    pdf.ln(5)
    
    # Cabeçalho da tabela
    pdf.set_font("Arial", "B", 9)
    pdf.cell(50, 10, "Nome", 1, 0, "C")
    pdf.cell(30, 10, "Código", 1, 0, "C")
    pdf.cell(30, 10, "Setor", 1, 0, "C")
    pdf.cell(35, 10, "Requisição", 1, 0, "C")
    pdf.cell(45, 10, "Data e Hora", 1, 1, "C")
    
    # Conteúdo da tabela
    pdf.set_font("Arial", "", 8)
    for _, row in df.iterrows():
        # Quebrar células se necessário para caber no PDF
        pdf.cell(50, 10, str(row["nome"])[:25], 1, 0, "L")
        pdf.cell(30, 10, str(row["codigo_funcionario"]), 1, 0, "C")
        pdf.cell(30, 10, str(row["setor"])[:13], 1, 0, "L")
        pdf.cell(35, 10, str(row["codigo_requisicao"]), 1, 0, "C")
        data_formatada = datetime.strptime(str(row["data"]), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
        pdf.cell(45, 10, data_formatada, 1, 1, "C")
        
        # Verificar se precisa adicionar uma nova página
        if pdf.get_y() > 270:
            pdf.add_page()
            
            # Reimprime o cabeçalho da tabela
            pdf.set_font("Arial", "B", 9)
            pdf.cell(50, 10, "Nome", 1, 0, "C")
            pdf.cell(30, 10, "Código", 1, 0, "C")
            pdf.cell(30, 10, "Setor", 1, 0, "C")
            pdf.cell(35, 10, "Requisição", 1, 0, "C")
            pdf.cell(45, 10, "Data e Hora", 1, 1, "C")
            pdf.set_font("Arial", "", 8)
    
    # Rodapé
    pdf.set_y(-15)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", 0, 0, "C")
    
    return pdf.output(dest="S").encode("latin1")

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
            
            # Botão para gerar PDF do relatório sintético
            if st.button("🖨️ Gerar Relatório em PDF"):
                pdf = gerar_pdf_sintetico(df, data_inicio, data_fim, setor_filtro, 
                                         total_funcionarios, total_requisicoes)
                
                # Criação do link para download
                html = create_download_link(pdf, f"relatorio_sintetico_{data_inicio}_a_{data_fim}.pdf")
                st.markdown(html, unsafe_allow_html=True)
            
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
            
            # Botão para gerar PDF do relatório analítico
            if st.button("🖨️ Gerar Relatório em PDF"):
                pdf = gerar_pdf_analitico(df, data_inicio, data_fim, setor_filtro, 
                                         total_funcionarios, total_requisicoes)
                
                # Criação do link para download
                html = create_download_link(pdf, f"relatorio_analitico_{data_inicio}_a_{data_fim}.pdf")
                st.markdown(html, unsafe_allow_html=True)
        
        # Exibir o dataframe formatado
        st.dataframe(df_display, use_container_width=True)
        
    else:
        setor_msg = f" no setor {setor_selecionado}" if setor_filtro else ""
        st.info(f"📌 Nenhuma requisição encontrada{setor_msg} no período selecionado.")

# Garantia que o script seja executado corretamente
if __name__ == "__main__":
    app()