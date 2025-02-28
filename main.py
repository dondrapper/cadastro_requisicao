import streamlit as st
import sqlite3
from datetime import datetime
import time
import os
import json

# Importações centralizadas
from database import (
    autenticar_funcionario,
    requisicao_ja_registrada,
    salvar_requisicao
)

# Configuração da página
st.set_page_config(page_title="Sistema de Controle", layout="centered")

# Carregar CSS se disponível
if os.path.exists("style.css"):
    with open("style.css") as css:
        st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)

# Adicionar JavaScript para integração com a extensão de código de barras
barcode_integration_js = """
<script>
// Escutar mensagens da extensão Chrome
window.addEventListener('message', function(event) {
    // Verificar se a mensagem é um código de barras
    if (event.data && event.data.type === 'barcode_data') {
        const barcode = event.data.data;
        console.log('Código de barras recebido da extensão:', barcode);
        
        // Encontrar o campo de entrada apropriado com base na etapa atual
        const currentPage = %s;
        let inputSelector = '';
        
        if (currentPage === 'login') {
            // Na tela de login, procurar campo de crachá
            inputSelector = 'input[aria-label="Escaneie seu Crachá"]';
        } else if (currentPage === 'requisicao') {
            // Na tela de requisição, procurar campo de código de barras
            inputSelector = 'input[aria-label="Escaneie o código do item (Apenas números, 12 caracteres)"]';
        }
        
        if (inputSelector) {
            const inputField = document.querySelector(inputSelector);
            if (inputField) {
                // Preencher o campo com o código
                inputField.value = barcode;
                // Disparar eventos para notificar o Streamlit
                inputField.dispatchEvent(new Event('input', { bubbles: true }));
                inputField.dispatchEvent(new Event('change', { bubbles: true }));
                // Emular pressionar Enter
                setTimeout(() => {
                    inputField.dispatchEvent(new KeyboardEvent('keydown', {
                        key: 'Enter', 
                        code: 'Enter',
                        keyCode: 13,
                        which: 13,
                        bubbles: true
                    }));
                }, 100);
            }
        }
    }
}, false);

// Sinalizar para a extensão que esta página está pronta
window.postMessage({
    type: 'streamlit_ready',
    page: %s
}, '*');
</script>
"""

# --- Inicialização das variáveis de sessão ---
if "page" not in st.session_state:
    st.session_state["page"] = "login"  # Valores possíveis: "login", "requisicao", "admin"
if "input_key" not in st.session_state:
    st.session_state["input_key"] = 0
if "etapa" not in st.session_state:
    st.session_state["etapa"] = "login"

def resetar_input():
    """Incrementa a chave de input para limpar os campos de texto."""
    st.session_state["input_key"] += 1

def exibir_contagem_regressiva(segundos=10):
    """Exibe uma contagem regressiva antes de encerrar a sessão.
    
    Args:
        segundos (int): Quantidade de segundos para contar.
    """
    countdown_placeholder = st.empty()
    for i in range(segundos, 0, -1):
        countdown_placeholder.warning(f"Encerrando sessão em {i} segundos...")
        time.sleep(1)

# Verificar a página atual e carregar o conteúdo correspondente
if st.session_state["page"] == "admin":
    import admin
    admin.app()
    st.stop()
else:
    # Injetar o JavaScript para integração com a extensão
    etapa_atual = json.dumps(st.session_state["etapa"])
    st.markdown(barcode_integration_js % (etapa_atual, etapa_atual), unsafe_allow_html=True)
    
    # Cabeçalho com título e botão administrador
    header_col1, header_col2 = st.columns([8, 2])
    with header_col1:
        st.markdown("<h1 style='margin: 0;'>📋 SISTEMA DE CONTROLE DE REQUISIÇÃO</h1>", unsafe_allow_html=True)
    with header_col2:
        if st.button("🔐 Acesso Administrador"):
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
            "Escaneie o código do item (Apenas números, 12 caracteres)", 
            max_chars=12, 
            key=f"codigo_requisicao_{st.session_state['input_key']}"
        )
        if codigo_requisicao:
            if not codigo_requisicao.isdigit() or len(codigo_requisicao) != 12:
                st.error("⚠ O código de barras precisa ter exatamente **12 números**!")
                time.sleep(3)
                resetar_input()
                st.rerun()
            else:
                ja_registrado, tempo_passado, data_registro = requisicao_ja_registrada(
                    st.session_state["codigo_funcionario"], 
                    codigo_requisicao
                )
                if ja_registrado:
                    st.error(f"🚫 Você já bipou esse item em {data_registro}.")
                    exibir_contagem_regressiva()
                    st.session_state["etapa"] = "login"
                    resetar_input()
                    st.rerun()
                else:
                    data_hora_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    sucesso = salvar_requisicao(
                        st.session_state["codigo_funcionario"], 
                        codigo_requisicao, 
                        data_hora_atual
                    )
                    if sucesso:
                        st.success(f"✅ Requisição registrada com sucesso!\n🕒 {data_hora_atual}")
                        time.sleep(3)
                        resetar_input()
                        st.session_state["etapa"] = "login"
                        st.rerun()
                    else:
                        st.error("❌ Erro ao registrar requisição. Tente novamente.")