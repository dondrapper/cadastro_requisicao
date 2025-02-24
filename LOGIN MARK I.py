import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import time  # Para o delay de 3 segundos

# Inicializa a sessão apenas para o código de requisição e controle da tela
if "codigo_requisicao" not in st.session_state:
    st.session_state["codigo_requisicao"] = ""
if "input_key" not in st.session_state:
    st.session_state["input_key"] = 0
if "etapa" not in st.session_state:
    st.session_state["etapa"] = "login"  # 🔥 Define a tela inicial como "login"

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

# Função para verificar se a requisição já foi registrada e há quanto tempo
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
        data_registro = datetime.strptime(resultado[0], "%Y-%m-%d %H:%M:%S")
        tempo_passado = datetime.now() - data_registro
        return True, tempo_passado
    return False, None  # Retorna False se não foi registrado ainda

# Função para resetar o campo de entrada sem erro
def resetar_input():
    st.session_state["input_key"] += 1  # 🔥 Atualiza a key do input para forçar um novo campo

# Função para salvar a requisição
def salvar_requisicao(codigo_funcionario, codigo_requisicao):
    ja_bipado, tempo_passado = requisicao_ja_registrada(codigo_funcionario, codigo_requisicao)

    if ja_bipado:
        minutos, segundos = divmod(int(tempo_passado.total_seconds()), 60)
        st.error(f"🚫 O código **{codigo_requisicao}** já foi bipado há {minutos} min e {segundos} segundos!")

        # Aguarda 3 segundos antes de resetar o input
        time.sleep(3)
        resetar_input()  # 🔥 Força a recriação do input
        st.rerun()
        return False

    # Se não foi bipado, salva no banco
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

    # Aguarda 3 segundos antes de resetar
    time.sleep(3)
    resetar_input()  # 🔥 Força a recriação do input
    st.session_state["etapa"] = "login"  # 🔥 Retorna para a tela de login
    st.rerun()
    return True

# 🔥 **Interface com separação de telas (Login -> Requisição)**
st.set_page_config(page_title="Sistema de Controle", layout="centered")

st.markdown("<h1 style='text-align: center;'>SISTEMA DE CONTROLE DE PRODUÇÃO PRINCIPIUM</h1>", unsafe_allow_html=True)

# 🔵 **Tela de Login (Escanear Crachá)**
if st.session_state["etapa"] == "login":
    st.markdown("<h3 style='text-align: center;'>Aproxime o crachá para identificação</h3>", unsafe_allow_html=True)

    codigo_funcionario = st.text_input("Escaneie seu Crachá", max_chars=10)

    if codigo_funcionario:
        nome = autenticar_funcionario(codigo_funcionario)
        if nome:
            st.success(f"✅ Autenticado com sucesso! Bem-vindo, {nome}!")
            st.session_state["usuario"] = nome
            st.session_state["codigo_funcionario"] = codigo_funcionario
            st.session_state["etapa"] = "requisicao"  # 🔥 Avança para a tela de requisição
            st.rerun()
        else:
            st.error("🚫 Crachá não cadastrado!")

# 🔵 **Tela de Requisição (Escanear Código de Barras)**
elif st.session_state["etapa"] == "requisicao":
    st.markdown("<h3 style='text-align: center;'>Faça a leitura do código de barras</h3>", unsafe_allow_html=True)

    st.info(f"👤 Usuário autenticado: **{st.session_state['usuario']}**")

    # 🔥 Criando um campo de entrada dinâmico para evitar erro ao resetar
    codigo_requisicao = st.text_input("Escaneie o código do item (Apenas números, 13 caracteres)", 
                                      max_chars=13, 
                                      key=f"codigo_requisicao_{st.session_state['input_key']}")

    # Verificação do código de barras
    if codigo_requisicao:
        if not codigo_requisicao.isdigit() or len(codigo_requisicao) != 13:
            st.error("⚠ O código de barras precisa ter exatamente **13 números**!")

            # Aguarda 3 segundos antes de resetar
            time.sleep(3)
            resetar_input()  # 🔥 Atualiza a chave do input
            st.rerun()
        else:
            salvar_requisicao(st.session_state["codigo_funcionario"], codigo_requisicao)
