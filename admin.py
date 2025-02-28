"""
Módulo da interface administrativa do sistema.
Gerencia o painel administrativo, autenticação e navegação.
"""

import streamlit as st
import relatorio_requisicoes
import listagem
import cadastro_fun
import cadastro
from auth import autenticar_admin

# Constantes para páginas
DASHBOARD = "dashboard"
CADASTRO_FUNCIONARIO = "cadastro_fun"
LISTAGEM_CRACHAS = "listagem"
RELATORIO_REQUISICOES = "requisicoes"
CADASTRO_USUARIO = "cadastro"
LOGIN = "login"

# Estrutura de menu para facilitar manutenção
MENU_ITEMS = [
    {"titulo": "📊 Dashboard", "pagina": DASHBOARD},
    {"titulo": "🆕 Cadastro de Crachá", "pagina": CADASTRO_FUNCIONARIO},
    {"titulo": "📋 Listagem de Crachás", "pagina": LISTAGEM_CRACHAS},
    {"titulo": "📑 Relatório de Requisições", "pagina": RELATORIO_REQUISICOES},
    {"titulo": "👤 Cadastrar Usuário", "pagina": CADASTRO_USUARIO},
    {"titulo": "🚪 Logout", "pagina": None},  # Caso especial tratado separadamente
]

def inicializar_estado():
    """Inicializa variáveis de estado se necessário"""
    if "admin_authenticated" not in st.session_state:
        st.session_state["admin_authenticated"] = False
    
    if "admin_page" not in st.session_state:
        st.session_state["admin_page"] = DASHBOARD

def criar_menu():
    """Cria o menu de navegação administrativa"""
    st.markdown("<h2>🔑 Área Administrativa</h2>", unsafe_allow_html=True)
    
    # Calcula o número de colunas baseado nos itens de menu
    colunas = st.columns(len(MENU_ITEMS))
    
    # Cria os botões em cada coluna
    for i, item in enumerate(MENU_ITEMS):
        with colunas[i]:
            if st.button(item["titulo"]):
                if item["pagina"] is None:  # Caso de logout
                    st.session_state["admin_authenticated"] = False
                    st.session_state["page"] = "login"
                    st.rerun()
                else:
                    st.session_state["admin_page"] = item["pagina"]
                    st.rerun()

def exibir_conteudo():
    """Exibe o conteúdo da página selecionada"""
    pagina_atual = st.session_state["admin_page"]
    
    if pagina_atual == DASHBOARD:
        st.markdown("### 📊 Bem-vindo à área administrativa!")
        st.markdown("Selecione uma opção no menu acima para gerenciar o sistema.")
        
        # Exibir estatísticas básicas
        try:
            import sqlite3
            import pandas as pd
            
            conn = sqlite3.connect("sistema.db")
            
            # Estatísticas de funcionários
            funcionarios_df = pd.read_sql("SELECT COUNT(*) as total, setor FROM FUNCIONARIOS GROUP BY setor", conn)
            
            # Estatísticas de requisições
            req_df = pd.read_sql("""
                SELECT COUNT(*) as total, 
                       strftime('%Y-%m-%d', data) as data 
                FROM REQUISICOES 
                GROUP BY strftime('%Y-%m-%d', data)
                ORDER BY data DESC
                LIMIT 7
            """, conn)
            
            # Exibir estatísticas
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Funcionários por Setor")
                st.dataframe(funcionarios_df)
            
            with col2:
                st.subheader("Requisições Recentes")
                st.dataframe(req_df)
                
            conn.close()
        except Exception as e:
            st.error(f"Erro ao carregar estatísticas: {str(e)}")
    
    elif pagina_atual == LISTAGEM_CRACHAS:
        listagem.app()
    
    elif pagina_atual == RELATORIO_REQUISICOES:
        relatorio_requisicoes.app()
    
    elif pagina_atual == CADASTRO_FUNCIONARIO:
        cadastro_fun.app()
    
    elif pagina_atual == CADASTRO_USUARIO:
        cadastro.app()

def exibir_login():
    """Exibe o formulário de login"""
    st.markdown('<h2>🔐 Login Administrativo</h2>', unsafe_allow_html=True)
    
    usuario = st.text_input("Usuário", key="admin_usuario")
    senha = st.text_input("Senha", type="password", key="admin_senha")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if st.button("🔑 Entrar", use_container_width=True):
            if autenticar_admin(usuario, senha):
                st.session_state["admin_authenticated"] = True
                st.success("✅ Login efetuado com sucesso!")
                st.rerun()
            else:
                st.error("🚫 Usuário ou senha incorretos!")
    
    with col3:
        if st.button("🔙 Voltar ao Sistema", use_container_width=True):
            st.session_state["page"] = "login"
            st.rerun()

def painel_admin():
    """Gerencia o painel administrativo"""
    criar_menu()
    st.markdown("<hr>", unsafe_allow_html=True)
    exibir_conteudo()

def app():
    """Função principal do aplicativo administrativo"""
    inicializar_estado()
    
    if not st.session_state["admin_authenticated"]:
        exibir_login()
    else:
        painel_admin()

# Executa o aplicativo diretamente se chamado como script principal
if __name__ == "__main__":
    app()