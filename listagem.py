"""
Módulo de listagem e gerenciamento de crachás.
Permite visualizar, filtrar e excluir funcionários, além de gerar crachás.
"""

import streamlit as st
import pandas as pd
import os

from utils import download_cracha, carregar_estilo_css
from database import (
    conectar_banco,
    listar_funcionarios,
    excluir_funcionarios as db_excluir_funcionarios,
    obter_funcionario as db_obter_funcionario
)

# Carregar CSS externo se disponível
if os.path.exists("style.css"):
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def carregar_funcionarios():
    """
    Carrega a lista de funcionários do banco de dados como DataFrame.
    
    Returns:
        pandas.DataFrame: DataFrame contendo os dados dos funcionários.
    """
    conn = conectar_banco()
    df = pd.read_sql("SELECT id, nome, cpf, setor, codigo FROM FUNCIONARIOS", conn)
    conn.close()
    return df

def excluir_funcionarios(ids_selecionados):
    """
    Exclui múltiplos funcionários e exibe mensagem de sucesso.
    
    Args:
        ids_selecionados (list): Lista de IDs dos funcionários a serem excluídos.
    """
    if ids_selecionados:
        contagem = db_excluir_funcionarios(ids_selecionados)
        st.success(f"✅ {contagem} funcionário(s) removido(s) com sucesso!")
        st.rerun()

def obter_funcionario(funcionario_id):
    """
    Obtém os dados de um funcionário pelo ID.
    
    Args:
        funcionario_id (int): ID do funcionário.
        
    Returns:
        dict: Dicionário com os dados do funcionário ou None se não encontrado.
    """
    return db_obter_funcionario(funcionario_id)

def app():
    """
    Carrega a página de listagem de crachás com todas as funcionalidades.
    """
    # Inicialização de estados de sessão
    if "exibindo_cracha" not in st.session_state:
        st.session_state["exibindo_cracha"] = False
    if "funcionario_id_selecionado" not in st.session_state:
        st.session_state["funcionario_id_selecionado"] = None

    # Exibir título centralizado
    st.markdown("<h1 class='title'>📋 Listagem de Crachás</h1>", unsafe_allow_html=True)

    # Verificar se está exibindo um crachá específico
    if st.session_state["exibindo_cracha"] and st.session_state["funcionario_id_selecionado"] is not None:
        exibir_cracha()
    else:
        exibir_lista_funcionarios()

def exibir_cracha():
    """
    Exibe o crachá do funcionário selecionado com opção de download.
    """
    func = obter_funcionario(st.session_state["funcionario_id_selecionado"])
    
    if func:
        st.markdown(f"<h2 style='text-align: center;'>Crachá de {func['nome']}</h2>", unsafe_allow_html=True)
        
        # Criar colunas para centralizar o crachá
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            download_cracha(func["cpf"], func["nome"], func["setor"])
            
        # Botão para voltar para a listagem
        if st.button("← Voltar para a listagem"):
            st.session_state["exibindo_cracha"] = False
            st.session_state["funcionario_id_selecionado"] = None
            st.rerun()
    else:
        st.error("Funcionário não encontrado")
        st.session_state["exibindo_cracha"] = False
        st.session_state["funcionario_id_selecionado"] = None
        st.rerun()

def exibir_lista_funcionarios():
    """
    Exibe a lista de funcionários com opções para gerenciar e imprimir crachás.
    """
    # Botão de atualização
    st.markdown("<div class='button-container'>", unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("")  # Espaço vazio para alinhamento
    with col2:
        if st.button("🔄 Atualizar Lista", use_container_width=True):
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # Carregar e exibir os funcionários
    df = carregar_funcionarios()

    # Criar tabela interativa com checkboxes
    if not df.empty:
        st.markdown("<div class='table-container'>", unsafe_allow_html=True)
        
        # Separar em duas tabs: Gerenciar Funcionários e Imprimir Crachás
        tab1, tab2 = st.tabs(["Gerenciar Funcionários", "Imprimir Crachás"])
        
        with tab1:
            exibir_tab_gerenciar(df)
        
        with tab2:
            exibir_tab_imprimir(df)

        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("📌 Nenhum funcionário cadastrado.")

def exibir_tab_gerenciar(df):
    """
    Exibe a aba de gerenciamento de funcionários.
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados dos funcionários.
    """
    st.markdown("### 📜 Lista de Funcionários:")
    st.write("Selecione os funcionários que deseja excluir e clique no botão **Excluir Selecionados**.")

    # Adicionando checkbox na primeira coluna
    df_select = df.copy()
    df_select.insert(0, "Selecionar", False)

    # Criar tabela interativa usando `st.data_editor()`
    tabela_editavel = st.data_editor(
        df_select,
        hide_index=True,
        column_config={"Selecionar": st.column_config.CheckboxColumn()},
        disabled=["id", "nome", "cpf", "setor", "codigo"],  # Bloqueia edição de outras colunas
    )

    # Filtrar os IDs dos funcionários selecionados para exclusão
    ids_selecionados = tabela_editavel.loc[tabela_editavel["Selecionar"], "id"].tolist()

    # Centralizando o botão de exclusão
    col1, col2, col3 = st.columns([3, 2, 3])
    with col2:
        if ids_selecionados:
            if st.button("❌ Excluir Selecionados", use_container_width=True):
                excluir_funcionarios(ids_selecionados)

def exibir_tab_imprimir(df):
    """
    Exibe a aba de impressão de crachás.
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados dos funcionários.
    """
    st.markdown("### 🖨️ Impressão de Crachás:")
    st.write("Selecione um funcionário para visualizar e imprimir seu crachá.")
    
    # Criar um selectbox para escolher o funcionário
    if not df.empty:
        # Criamos uma lista de tuplas (id, nome) para o selectbox
        funcionarios_lista = [(row['id'], row['nome']) for _, row in df.iterrows()]
        
        # Adicionamos uma opção vazia no início para forçar a seleção
        funcionarios_lista.insert(0, (None, "Selecione um funcionário..."))
        
        # Exibimos apenas o nome no selectbox, mas armazenamos o ID
        funcionario_escolhido = st.selectbox(
            "Funcionário:",
            options=funcionarios_lista,
            format_func=lambda x: x[1],  # Exibe apenas o nome
            key="selectbox_funcionario"
        )
        
        col1, col2, col3 = st.columns([3, 2, 3])
        with col2:
            # Só habilitamos o botão se uma opção válida foi selecionada
            if funcionario_escolhido[0] is not None:
                if st.button("🖨️ Gerar Crachá", use_container_width=True):
                    st.session_state["funcionario_id_selecionado"] = funcionario_escolhido[0]
                    st.session_state["exibindo_cracha"] = True
                    st.rerun()
            else:
                st.button("🖨️ Gerar Crachá", use_container_width=True, disabled=True)
    else:
        st.info("Nenhum funcionário disponível para impressão de crachá.")

# Garantia que o script seja executado corretamente
if __name__ == "__main__":
    app()