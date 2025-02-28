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
if "last_input" not in st.session_state:
    st.session_state["last_input"] = ""
if "last_time" not in st.session_state:
    st.session_state["last_time"] = time.time()
if "codigo_buffer" not in st.session_state:
    st.session_state["codigo_buffer"] = ""

def resetar_input():
    """Incrementa a chave de input para limpar os campos de texto."""
    st.session_state["input_key"] += 1
    st.session_state["codigo_buffer"] = ""

def auto_submit_callback():
    """Callback para verificar e enviar automaticamente códigos completos"""
    current_time = time.time()
    
    # Se o buffer não estiver vazio e passou tempo suficiente desde a última entrada
    if st.session_state["codigo_buffer"] and (current_time - st.session_state["last_time"] > 0.5):
        codigo = st.session_state["codigo_buffer"]
        st.session_state["codigo_buffer"] = ""
        
        # Processar baseado na etapa atual
        if st.session_state["etapa"] == "login" and len(codigo) == 11 and codigo.isdigit():
            # Processar como código de cracha (11 dígitos)
            nome = autenticar_funcionario(codigo)
            if nome:
                st.success(f"✅ Autenticado com sucesso! Bem-vindo, {nome}!")
                st.session_state["usuario"] = nome
                st.session_state["codigo_funcionario"] = codigo
                st.session_state["etapa"] = "requisicao"
                st.rerun()
            else:
                st.error("🚫 Crachá não cadastrado!")
        
        elif st.session_state["etapa"] == "requisicao" and len(codigo) == 12 and codigo.isdigit():
            # Processar como código de requisição (12 dígitos)
            if "usuario" in st.session_state and "codigo_funcionario" in st.session_state:
                ja_registrado, tempo_passado, data_registro = requisicao_ja_registrada(
                    st.session_state["codigo_funcionario"], 
                    codigo
                )
                
                if ja_registrado:
                    st.error(f"🚫 Você já bipou esse item em {data_registro}.")
                    resetar_input()
                else:
                    data_hora_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    sucesso = salvar_requisicao(
                        st.session_state["codigo_funcionario"], 
                        codigo, 
                        data_hora_atual
                    )
                    
                    if sucesso:
                        st.success(f"✅ Requisição registrada com sucesso!\n🕒 {data_hora_atual}")
                        resetar_input()
                    else:
                        st.error("❌ Erro ao registrar requisição. Tente novamente.")

def handle_key_input(key_char):
    """Manipula a entrada de caracteres para formar o código"""
    if key_char.isdigit():
        # Adiciona o dígito ao buffer
        st.session_state["codigo_buffer"] += key_char
        st.session_state["last_time"] = time.time()
        
        # Auto-submit se o buffer atingir o tamanho esperado
        if st.session_state["etapa"] == "login" and len(st.session_state["codigo_buffer"]) == 11:
            auto_submit_callback()
        elif st.session_state["etapa"] == "requisicao" and len(st.session_state["codigo_buffer"]) == 12:
            auto_submit_callback()

# Adicionar JavaScript para capturar entradas de teclado
js_code = """
<script>
document.addEventListener('keydown', function(e) {
    // Capturar apenas teclas de dígitos (0-9)
    if (/^\d$/.test(e.key)) {
        // Enviar para o Streamlit
        window.parent.postMessage({
            type: 'streamlit:keyPress',
            key: e.key
        }, '*');
    }
});
</script>
"""
st.components.v1.html(js_code, height=0)

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
        
        # Executar verificação automática
        auto_submit_callback()
        
        st.info("✨ Posicione o cursor nesta página e escaneie seu crachá com o leitor de códigos de barras.")
            
        # Campo para entrada manual
        st.markdown("### Ou insira manualmente:")
        
        codigo_funcionario = st.text_input("Código do Crachá", max_chars=11)
        if codigo_funcionario:
            # Processar apenas se for digitado manualmente (não através do buffer automático)
            if codigo_funcionario != st.session_state["last_input"]:
                st.session_state["last_input"] = codigo_funcionario
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
        
        # Executar verificação automática
        auto_submit_callback()
        
        if st.session_state["codigo_buffer"]:
            st.write(f"Lendo código: {st.session_state['codigo_buffer']}")
        
        st.info("✨ Posicione o cursor nesta página e escaneie o código de barras com o leitor.")
                
        # Campo para entrada manual
        st.markdown("### Ou insira manualmente:")
        
        codigo_requisicao = st.text_input(
            "Escaneie o código do item (Apenas números, 12 caracteres)", 
            max_chars=12, 
            key=f"codigo_requisicao_{st.session_state['input_key']}"
        )
        
        # Botão para sair/logout
        if st.button("🚪 Sair"):
            st.session_state["etapa"] = "login"
            resetar_input()
            st.rerun()
            
        if codigo_requisicao:
            # Processar apenas se for digitado manualmente
            if codigo_requisicao != st.session_state["last_input"]:
                st.session_state["last_input"] = codigo_requisicao
                
                if not codigo_requisicao.isdigit() or len(codigo_requisicao) != 12:
                    st.error("⚠ O código de barras precisa ter exatamente **12 números**!")
                else:
                    ja_registrado, tempo_passado, data_registro = requisicao_ja_registrada(
                        st.session_state["codigo_funcionario"], 
                        codigo_requisicao
                    )
                    if ja_registrado:
                        st.error(f"🚫 Você já bipou esse item em {data_registro}.")
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
                            resetar_input()
                            st.rerun()
                        else:
                            st.error("❌ Erro ao registrar requisição. Tente novamente.")

# Configurar receptor para eventos de tecla do JavaScript
if "streamlit:keyPress" in st.query_params:
    key_pressed = st.query_params["streamlit:keyPress"]
    handle_key_input(key_pressed)