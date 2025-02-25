import streamlit as st
import sqlite3
from datetime import datetime
import time
import os

# No início do seu arquivo, logo após imports e set_page_config
if os.path.exists("style.css"):
    with open("style.css") as css:
        st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)
# --- Inicialização das variáveis de sessão ---
if "page" not in st.session_state:
    st.session_state["page"] = "login"  # Valores possíveis: "login", "requisicao", "admin"
if "input_key" not in st.session_state:
    st.session_state["input_key"] = 0
if "etapa" not in st.session_state:
    st.session_state["etapa"] = "login"

# Se a página for "admin", chama o arquivo admin.py e para a execução deste script
if st.session_state["page"] == "admin":
    import admin  # Certifique-se de que admin.py esteja no mesmo diretório
    admin.app()  # Supondo que a função principal em admin.py seja "app()"
    st.stop()

# --- Funções Auxiliares ---
def conectar_banco():
    return sqlite3.connect("sistema.db")

def autenticar_funcionario(codigo):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM FUNCIONARIOS WHERE codigo = ?", (codigo,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else None

def requisicao_ja_registrada(codigo_funcionario, codigo_requisicao):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT data FROM REQUISICOES 
        WHERE codigo_funcionario = ? AND codigo_requisicao = ?
        ORDER BY data DESC LIMIT 1
    """, (codigo_funcionario, codigo_requisicao))
    resultado = cursor.fetchone()
    conn.close()

    if resultado:
        data_registro = resultado[0]  # formato "%Y-%m-%d %H:%M:%S"
        dt_registro = datetime.strptime(data_registro, "%Y-%m-%d %H:%M:%S")
        tempo_passado = datetime.now() - dt_registro
        return True, tempo_passado, data_registro
    return False, None, None

def resetar_input():
    st.session_state["input_key"] += 1

def salvar_requisicao(codigo_funcionario, codigo_requisicao):
    ja_bipado, tempo_passado, data_registro = requisicao_ja_registrada(codigo_funcionario, codigo_requisicao)
    if ja_bipado:
        nome_usuario = autenticar_funcionario(codigo_funcionario)
        st.error(f"🚫 O código **{codigo_requisicao}** já foi bipado em **{data_registro}** pelo usuário **{nome_usuario}**!")
        countdown_placeholder = st.empty()
        for i in range(10, 0, -1):
            countdown_placeholder.warning(f"Encerrando sessão em {i} segundos...")
            time.sleep(1)
        st.session_state["etapa"] = "login"
        resetar_input()
        st.rerun()
        return False

    conn = conectar_banco()
    cursor = conn.cursor()
    data_hora_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO REQUISICOES (codigo_funcionario, codigo_requisicao, data)
        VALUES (?, ?, ?)
    """, (codigo_funcionario, codigo_requisicao, data_hora_atual))
    conn.commit()
    conn.close()
    st.success(f"✅ Requisição registrada com sucesso!\n🕒 {data_hora_atual}")
    time.sleep(3)
    resetar_input()
    st.session_state["etapa"] = "login"
    st.rerun()

# --- Configuração da Página ---
#st.set_page_config(page_title="Sistema de Controle", layout="centered")

# Cabeçalho com título e botão administrador
header_col1, header_col2 = st.columns([8, 2])
with header_col1:
    st.markdown("<h1 style='margin: 0;'>📋 SISTEMA DE CONTROLE DE REQUISIÇÃO</h1>", unsafe_allow_html=True)
with header_col2:
    if st.button("Acesso Administrador"):
         st.session_state["page"] = "admin"
         st.rerun()

# --- Tela de Login (Escanear Crachá) ---
if st.session_state["etapa"] == "login":
    st.markdown("<h3 style='text-align: center;'>Aproxime o crachá para identificação</h3>", unsafe_allow_html=True)
    codigo_funcionario = st.text_input("Escaneie seu Crachá", max_chars=11)
    if codigo_funcionario:
        nome = autenticar_funcionario(codigo_funcionario)
        if nome:
            st.success(f"✅ Autenticado com sucesso! Bem-vindo, {nome}!")
            st.session_state["usuario"] = nome
            st.session_state["codigo_funcionario"] = codigo_funcionario
            st.session_state["etapa"] = "requisicao"
            st.rerun()
        else:
            st.error("🚫 Crachá não cadastrado!")

# --- Tela de Requisição (Escanear Código de Barras) ---
elif st.session_state["etapa"] == "requisicao":
    st.markdown("<h3 style='text-align: center;'>Faça a leitura do código de barras</h3>", unsafe_allow_html=True)
    st.info(f"👤 Usuário autenticado: **{st.session_state['usuario']}**")
    codigo_requisicao = st.text_input(
        "Escaneie o código do item (Apenas números, 13 caracteres)", 
        max_chars=13, 
        key=f"codigo_requisicao_{st.session_state['input_key']}"
    )
    if codigo_requisicao:
        if not codigo_requisicao.isdigit() or len(codigo_requisicao) != 13:
            st.error("⚠ O código de barras precisa ter exatamente **13 números**!")
            time.sleep(3)
            resetar_input()
            st.rerun()
        else:
            ja_registrado, tempo_passado, data_registro = requisicao_ja_registrada(st.session_state["codigo_funcionario"], codigo_requisicao)
            if ja_registrado:
                st.error(f"🚫 Você já bipou esse item em {data_registro}.")
                countdown_placeholder = st.empty()
                for i in range(10, 0, -1):
                    countdown_placeholder.warning(f"Encerrando sessão em {i} segundos...")
                    time.sleep(1)
                st.session_state["etapa"] = "login"
                resetar_input()
                st.rerun()
            else:
                salvar_requisicao(st.session_state["codigo_funcionario"], codigo_requisicao)
