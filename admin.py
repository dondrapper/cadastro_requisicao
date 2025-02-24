import streamlit as st
import sqlite3
from datetime import datetime

# Deve ser a primeira instrução
st.set_page_config(page_title="Área Administrativa", layout="wide")

# --- Custom CSS para Visual do Sistema ---
st.markdown(
    """
    <style>
    /* Corpo e fundo */
    body {
        background-color: #f5f5f5;
        font-family: Arial, sans-serif;
    }
    /* Cabeçalho */
    .header {
        background-color: #2c3e50;
        color: #ecf0f1;
        padding: 20px;
        text-align: center;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    /* Botões do menu */
    .menu-button {
        background-color: #3498db;
        color: white;
        border: none;
        padding: 10px 15px;
        border-radius: 5px;
        cursor: pointer;
        margin: 5px;
    }
    .menu-button:hover {
        background-color: #2980b9;
    }
    /* Inputs */
    .stTextInput>div>div>input {
        border: 2px solid #bdc3c7;
        border-radius: 5px;
        padding: 8px;
    }
    /* Tabelas */
    table {
        width: 100%;
        border-collapse: collapse;
    }
    table, th, td {
        border: 1px solid #bdc3c7;
        padding: 8px;
    }
    th {
        background-color: #34495e;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Funções Auxiliares ---

def conectar_banco():
    return sqlite3.connect("sistema.db")

def autenticar_admin(usuario, senha):
    try:
        conn = conectar_banco()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ADMINISTRADORES WHERE usuario = ? AND senha = ?", (usuario, senha))
        admin_data = cursor.fetchone()
        # Debug: exibe o resultado da consulta
        st.write("Resultado da consulta:", admin_data)
        conn.close()
        return admin_data is not None
    except Exception as e:
        st.error("Erro ao consultar administrador: " + str(e))
        return False

def cadastrar_cracha():
    st.subheader("Cadastro de Crachá")
    codigo = st.text_input("Código do Crachá", max_chars=10)
    nome = st.text_input("Nome do Funcionário")
    
    if st.button("Cadastrar Crachá", key="btn_cadastrar_cracha"):
        if codigo and nome:
            try:
                conn = conectar_banco()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM FUNCIONARIOS WHERE codigo = ?", (codigo,))
                if cursor.fetchone():
                    st.error("Crachá já cadastrado!")
                else:
                    cursor.execute("INSERT INTO FUNCIONARIOS (codigo, nome) VALUES (?, ?)", (codigo, nome))
                    conn.commit()
                    st.success("Crachá cadastrado com sucesso!")
            except Exception as e:
                st.error("Erro ao cadastrar: " + str(e))
            finally:
                conn.close()
        else:
            st.warning("Por favor, preencha todos os campos.")

def relatorio_usuarios():
    st.subheader("Relatório de Usuários Cadastrados")
    try:
        conn = conectar_banco()
        cursor = conn.cursor()
        cursor.execute("SELECT codigo, nome FROM FUNCIONARIOS")
        usuarios = cursor.fetchall()
    except Exception as e:
        st.error("Erro ao buscar usuários: " + str(e))
        usuarios = []
    finally:
        conn.close()
        
    if usuarios:
        st.table(usuarios)
    else:
        st.info("Nenhum usuário cadastrado.")

def relatorio_requisicoes():
    st.subheader("Relatório de Requisições Cadastradas")
    try:
        conn = conectar_banco()
        cursor = conn.cursor()
        cursor.execute("SELECT codigo_funcionario, codigo_requisicao, data FROM REQUISICOES")
        requisicoes = cursor.fetchall()
    except Exception as e:
        st.error("Erro ao buscar requisições: " + str(e))
        requisicoes = []
    finally:
        conn.close()
        
    if requisicoes:
        st.table(requisicoes)
    else:
        st.info("Nenhuma requisição cadastrada.")

# --- Função Principal do Admin ---

def app():
    # Se o administrador não estiver autenticado, exibe o formulário de login centralizado
    if "admin_authenticated" not in st.session_state or not st.session_state["admin_authenticated"]:
        st.markdown('<div class="header"><h1>Login Administrativo</h1></div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            usuario = st.text_input("Usuário", key="admin_usuario")
            senha = st.text_input("Senha", type="password", key="admin_senha")
            if st.button("Entrar", key="btn_admin_login"):
                if usuario and senha:
                    if autenticar_admin(usuario, senha):
                        st.session_state["admin_authenticated"] = True
                        st.success("Login efetuado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos!")
                else:
                    st.warning("Preencha usuário e senha.")
        return  # Não continua se não estiver autenticado

    # Se autenticado, exibe a interface administrativa com cabeçalho e menu de botões
    st.markdown('<div class="header"><h1>Área Administrativa</h1></div>', unsafe_allow_html=True)
    
    # Menu de navegação com botões (dispostos em uma linha)
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        if st.button("Dashboard", key="btn_dashboard", use_container_width=True,
                     on_click=lambda: st.session_state.update(admin_page="dashboard")):
            pass
    with col2:
        if st.button("Cadastro de Crachá", key="btn_cadastro", use_container_width=True,
                     on_click=lambda: st.session_state.update(admin_page="cadastro")):
            pass
    with col3:
        if st.button("Relatório de Usuários", key="btn_usuarios", use_container_width=True,
                     on_click=lambda: st.session_state.update(admin_page="usuarios")):
            pass
    with col4:
        if st.button("Relatório de Requisições", key="btn_requisicoes", use_container_width=True,
                     on_click=lambda: st.session_state.update(admin_page="requisicoes")):
            pass
    with col5:
        if st.button("Logout", key="btn_logout", use_container_width=True):
            st.session_state["admin_authenticated"] = False
            st.session_state["page"] = "login"
            st.rerun()
    
    # Define a página atual do admin (padrão Dashboard)
    if "admin_page" not in st.session_state:
        st.session_state["admin_page"] = "dashboard"

    # Exibe a seção correspondente
    if st.session_state["admin_page"] == "dashboard":
        st.write("Bem-vindo à área administrativa! Selecione uma opção acima.")
    elif st.session_state["admin_page"] == "cadastro":
        cadastrar_cracha()
    elif st.session_state["admin_page"] == "usuarios":
        relatorio_usuarios()
    elif st.session_state["admin_page"] == "requisicoes":
        relatorio_requisicoes()

if __name__ == "__main__":
    app()
