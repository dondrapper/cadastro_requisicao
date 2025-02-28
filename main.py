import streamlit as st
import sqlite3
from datetime import datetime
import time
import os

# Importações centralizadas
from database import (
    autenticar_funcionario,
    requisicao_ja_registrada,
    salvar_requisicao
)

# Importar o novo módulo de captura de códigos de barras
from api_barcode import init_barcode_listener, check_for_barcode, display_barcode_messages, init_session_state

# Configuração da página
st.set_page_config(page_title="Sistema de Controle", layout="centered")

# Carregar CSS se disponível
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
if "auto_capture" not in st.session_state:
    st.session_state["auto_capture"] = True

# Garantir que as variáveis de sessão para os códigos de barras estejam inicializadas
init_session_state()

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

# Inicializar o listener de códigos de barras
try:
    init_barcode_listener()
except Exception as e:
    st.error(f"Erro ao inicializar o listener de códigos de barras: {str(e)}")

# Verificar a página atual e carregar o conteúdo correspondente
if st.session_state["page"] == "admin":
    import admin
    admin.app()
    st.stop()
else:
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
        
        # Opção para habilitar/desabilitar captura automática
        auto_capture = st.checkbox("Habilitar captura automática via extensão Chrome", 
                                  value=st.session_state["auto_capture"],
                                  key="auto_capture_checkbox")
        st.session_state["auto_capture"] = auto_capture
        
        if auto_capture:
            st.info("✨ A captura automática está ativada. Use a extensão Chrome para escanear seu crachá.")
            
            # Verificar se há um código de barras capturado pela extensão
            try:
                if check_for_barcode():
                    # Se estamos na tela de login e o login foi bem-sucedido, devemos recarregar a página
                    # para mostrar a tela de requisição
                    if st.session_state.get("etapa") == "requisicao" and st.session_state.get("usuario"):
                        st.rerun()
                    else:
                        # Caso contrário, apenas verificamos novamente
                        time.sleep(0.1)
                        check_for_barcode()
            except Exception as e:
                st.error(f"Erro ao verificar código de barras: {str(e)}")
                
            # Ainda manter o campo manual como fallback
            st.markdown("### Ou insira manualmente:")
            
        codigo_funcionario = st.text_input("Código do Crachá", max_chars=11)
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
        
        # Exibir histórico de mensagens de leitura de códigos de barras
        try:
            display_barcode_messages()
        except Exception as e:
            st.error(f"Erro ao exibir mensagens de códigos de barras: {str(e)}")
        
        # Opção para habilitar/desabilitar captura automática
        auto_capture = st.checkbox("Habilitar captura automática via extensão Chrome", 
                                  value=st.session_state["auto_capture"],
                                  key="auto_capture_requisicao")
        st.session_state["auto_capture"] = auto_capture
        
        if auto_capture:
            st.info("✨ A captura automática está ativada. Use a extensão Chrome para escanear os códigos de barras.")
            
            # Verificar se há um código de barras capturado pela extensão
            try:
                if check_for_barcode():
                    st.rerun()  # Recarregar para processar o código
            except Exception as e:
                st.error(f"Erro ao verificar código de barras: {str(e)}")
                
            # Ainda manter o campo manual como fallback
            st.markdown("### Ou insira manualmente:")
            
        codigo_requisicao = st.text_input(
            "Escaneie o código do item (Apenas números, 12 caracteres)", 
            max_chars=12, 
            key=f"codigo_requisicao_{st.session_state['input_key']}"
        )
        
        # Botão para sair/logout
        if st.button("🚪 Sair"):
            st.session_state["etapa"] = "login"
            st.rerun()
            
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
                        st.rerun()
                    else:
                        st.error("❌ Erro ao registrar requisição. Tente novamente.")