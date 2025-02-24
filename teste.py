import streamlit as st

# Configuração da página (layout wide para melhor distribuição horizontal)
st.set_page_config(page_title="Minha Aplicação", layout="wide")

# Inicializa o estado de navegação se não existir
if "page" not in st.session_state:
    st.session_state["page"] = "main"

# Cabeçalho com título à esquerda e botão de acesso administrativo à direita
col_title, col_button = st.columns([8, 2])
with col_title:
    st.markdown("<h1 style='margin: 0;'>Minha Aplicação</h1>", unsafe_allow_html=True)
with col_button:
    if st.button("Acesso Administrador"):
        st.session_state["page"] = "admin_login"
        st.rerun()  # Atualiza a página para redirecionar para o login administrativo

# Renderiza o conteúdo conforme a página escolhida
if st.session_state["page"] == "main":
    st.write("Bem-vindo à aplicação! Aqui vai o conteúdo principal.")
    
elif st.session_state["page"] == "admin_login":
    st.markdown("<h1>Login Administrativo</h1>", unsafe_allow_html=True)
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        # Exemplo simples de validação de credenciais
        if usuario == "admin" and senha == "senha123":
            st.success("Login realizado com sucesso!")
        else:
            st.error("Usuário ou senha incorretos!")
