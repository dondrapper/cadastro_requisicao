import streamlit as st
import relatorio_requisicoes  # ✅ Importação correta no início do arquivo
import listagem
import cadastro_fun
import cadastro
from auth import autenticar_admin

# --- Função para interface administrativa ---
def painel_admin():
    st.markdown("<h1 style='text-align:center;'>🔑 Área Administrativa</h1>", unsafe_allow_html=True)

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        if st.button("📊 Dashboard"):
            st.session_state["admin_page"] = "dashboard"
    with col2:
        if st.button("🆕 Cadastro de Crachá"):
            st.session_state["admin_page"] = "cadastro_fun"
    with col3:
        if st.button("📋 Listagem de Crachás"):
            st.session_state["admin_page"] = "listagem"
    with col4:
        if st.button("📑 Relatório de Requisições"):
            st.session_state["admin_page"] = "requisicoes"
    with col5:
        if st.button("👤 Cadastrar Usuário"):
            st.session_state["admin_page"] = "cadastro"
    with col6:
        if st.button("🚪 Logout"):
            st.session_state["admin_authenticated"] = False
            st.session_state["page"] = "login"
            st.rerun()

    # Define página padrão ao entrar
    if "admin_page" not in st.session_state:
        st.session_state["admin_page"] = "dashboard"

    # Gerenciamento das páginas
    if st.session_state["admin_page"] == "dashboard":
        st.markdown("### 📊 Bem-vindo à área administrativa! Selecione uma opção acima.")

    elif st.session_state["admin_page"] == "listagem":
        listagem.app()

    elif st.session_state["admin_page"] == "requisicoes":
        relatorio_requisicoes.app()

    elif st.session_state["admin_page"] == "cadastro_fun":
        cadastro_fun.app()

    elif st.session_state["admin_page"] == "cadastro":
        cadastro.app()

# --- Função principal do Admin ---
def app():
    if "admin_authenticated" not in st.session_state:
        st.session_state["admin_authenticated"] = False

    # Login de administrador
    if not st.session_state["admin_authenticated"]:
        st.markdown('<h2 style="text-align:center;">🔐 Login Administrativo</h2>', unsafe_allow_html=True)
        usuario = st.text_input("Usuário", key="admin_usuario")
        senha = st.text_input("Senha", type="password", key="admin_senha")

        if st.button("🔑 Entrar"):
            if autenticar_admin(usuario, senha):
                st.session_state["admin_authenticated"] = True
                st.success("✅ Login efetuado com sucesso!")
                st.rerun()
            else:
                st.error("🚫 Usuário ou senha incorretos!")
    else:
        painel_admin()

# --- Executa o aplicativo diretamente ---
if __name__ == "__main__":
    app()