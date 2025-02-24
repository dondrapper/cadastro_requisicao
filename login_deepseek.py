import streamlit as st
import sqlite3
from datetime import datetime

# Inicializa a sessão para navegação
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "login"
if "codigo_requisicao" not in st.session_state:
    st.session_state["codigo_requisicao"] = ""

# Função para conectar ao banco
def conectar_banco():
    return sqlite3.connect("sistema.db")

# Função para autenticar o funcionário
def autenticar_funcionario(codigo):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM FUNCIONARIOS WHERE codigo = ?", (codigo,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else None

# Função para verificar se a requisição já foi registrada
def requisicao_ja_registrada(codigo_funcionario, codigo_requisicao):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM REQUISICOES 
        WHERE codigo_funcionario = ? AND codigo_requisicao = ?
    """, (codigo_funcionario, codigo_requisicao))
    resultado = cursor.fetchone()[0]
    conn.close()
    return resultado > 0  # Retorna True se já existir

# Função para salvar a requisição
def salvar_requisicao(codigo_funcionario, codigo_requisicao):
    if requisicao_ja_registrada(codigo_funcionario, codigo_requisicao):
        st.session_state["erro_requisicao"] = f"🚫 O código {codigo_requisicao} já foi bipado por você!"
        return False  # Não salva se já existir
    
    conn = conectar_banco()
    cursor = conn.cursor()
    data_hora_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO REQUISICOES (codigo_funcionario, codigo_requisicao, data)
        VALUES (?, ?, ?)
    """, (codigo_funcionario, codigo_requisicao, data_hora_atual))

    conn.commit()
    conn.close()
    st.session_state["sucesso_requisicao"] = f"✅ Requisição registrada com sucesso!\n🕒 {data_hora_atual}"
    return True  # Salvo com sucesso

# Interface de Login
def tela_login():
    st.set_page_config(page_title="Login", layout="centered")

    st.markdown("<h1 style='text-align: center;'>SISTEMA DE CONTROLE DE PRODUÇÃO PRINCIPIUM</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Aproxime o crachá para identificação</h3>", unsafe_allow_html=True)

    # Campo de entrada para o código do crachá (O leitor USB preencherá automaticamente)
    codigo = st.text_input("Escaneie seu Crachá", max_chars=10)

    if codigo:
        nome = autenticar_funcionario(codigo)
        if nome:
            st.success(f"✅ Autenticado com sucesso! Bem-vindo, {nome}!")
            st.session_state["usuario"] = nome
            st.session_state["codigo_funcionario"] = codigo
            st.session_state["pagina"] = "requisicao"  # Muda para a tela de requisição
            st.rerun()
        else:
            st.error("🚫 Crachá não cadastrado!")

# Interface de Requisição
def tela_requisicao():
    st.set_page_config(page_title="Registro de Requisição", layout="centered")
    st.markdown("<h1 style='text-align: center;'>Faça a leitura do código de barras</h1>", unsafe_allow_html=True)

    if "usuario" in st.session_state:
        st.info(f"Usuário autenticado: **{st.session_state['usuario']}**")

        # Exibe mensagem de erro, se existir
        if "erro_requisicao" in st.session_state:
            st.error(st.session_state["erro_requisicao"])
            del st.session_state["erro_requisicao"]  # Remove a mensagem após exibir

        # Exibe mensagem de sucesso, se existir
        if "sucesso_requisicao" in st.session_state:
            st.success(st.session_state["sucesso_requisicao"])
            del st.session_state["sucesso_requisicao"]  # Remove a mensagem após exibir

        # Campo de entrada para o código de barras do item
        codigo_requisicao = st.text_input("Escaneie o código do item", 
                                        max_chars=20, 
                                        key="input_codigo_requisicao")  # Chave única para o widget

        # Botão para salvar a requisição
        if st.button("Salvar Requisição"):
            if codigo_requisicao:
                if salvar_requisicao(st.session_state["codigo_funcionario"], codigo_requisicao):
                    # Limpa o valor do widget ANTES de recriá-lo
                    st.session_state["input_codigo_requisicao"] = ""
                    st.rerun()  # Recarrega a tela para atualizar o widget
            else:
                st.error("🚫 Por favor, escaneie um código válido!")

    else:
        st.error("🚫 Nenhum usuário autenticado! Redirecionando para login...")
        st.session_state["pagina"] = "login"
        st.rerun()

# Escolhe qual tela mostrar
if st.session_state["pagina"] == "login":
    tela_login()
else:
    tela_requisicao()