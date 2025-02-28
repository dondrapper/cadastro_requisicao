"""
Solução direta para o problema de leitura de código de barras sem extensão Chrome.
Este arquivo pode ser usado diretamente no lugar do main.py.
"""

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
    st.session_state["page"] = "login"
if "input_key" not in st.session_state:
    st.session_state["input_key"] = 0
if "etapa" not in st.session_state:
    st.session_state["etapa"] = "login"
if "auto_detection" not in st.session_state:
    st.session_state["auto_detection"] = True

# Injetar JavaScript para capturar códigos de barras
js_code = """
<script>
// Buffer para armazenar o código de barras
let barcodeBuffer = '';
let lastKeyTime = 0;
const MAX_DELAY = 100; // Tempo máximo entre caracteres (ms)

// Função para enviar o código para o Streamlit
function sendBarcodeToStreamlit() {
    if (barcodeBuffer.length > 0) {
        console.log('Enviando código:', barcodeBuffer);
        
        // Salvar no sessionStorage para o Streamlit ler
        sessionStorage.setItem('barcode_data', barcodeBuffer);
        
        // Forçar um rerun do Streamlit
        window.dispatchRerun.dispatchMessage('rerun');
        
        // Limpar o buffer
        barcodeBuffer = '';
    }
}

// Listener para capturar teclas
document.addEventListener('keydown', function(event) {
    const currentTime = new Date().getTime();
    
    // Se passou muito tempo desde a última tecla, limpar o buffer
    if (currentTime - lastKeyTime > MAX_DELAY && barcodeBuffer.length > 0) {
        sendBarcodeToStreamlit();
    }
    
    lastKeyTime = currentTime;
    
    // Capturar apenas dígitos
    if (event.key.match(/^[0-9]$/)) {
        barcodeBuffer += event.key;
        
        // Quando o buffer atingir tamanhos específicos, enviar automaticamente
        if ((barcodeBuffer.length === 11 || barcodeBuffer.length === 12) && 
            barcodeBuffer.match(/^[0-9]+$/)) {
            // Pequeno delay para garantir que todas as teclas foram capturadas
            setTimeout(sendBarcodeToStreamlit, 10);
        }
    } else if (event.key === 'Enter' && barcodeBuffer.length > 0) {
        // Enter força o envio imediato
        event.preventDefault(); // Prevenir comportamento padrão do Enter
        sendBarcodeToStreamlit();
    }
});

// Função para verificar se há dados no sessionStorage
function checkBarcodeData() {
    const data = sessionStorage.getItem('barcode_data');
    if (data) {
        // Limpar dados após leitura para evitar processamento duplicado
        sessionStorage.removeItem('barcode_data');
        
        // Enviar para o Streamlit via API de componentes
        if (window.Streamlit) {
            window.Streamlit.setComponentValue({barcode: data});
        }
    }
    setTimeout(checkBarcodeData, 50);
}

// Iniciar a verificação
checkBarcodeData();
</script>
"""

# Injetar o JavaScript na página
st.components.v1.html(js_code, height=0)

def resetar_input():
    """Incrementa a chave de input para limpar os campos de texto."""
    st.session_state["input_key"] += 1

def processar_codigo_barras():
    """Verifica se há um código de barras disponível e o processa."""
    if 'barcode_data' in st.session_state and st.session_state['barcode_data']:
        codigo = st.session_state['barcode_data']
        # Limpar para evitar processamento duplicado
        st.session_state['barcode_data'] = None
        
        # Processar de acordo com a etapa atual
        if st.session_state["etapa"] == "login":
            if len(codigo) == 11 and codigo.isdigit():
                nome = autenticar_funcionario(codigo)
                if nome:
                    st.session_state["usuario"] = nome
                    st.session_state["codigo_funcionario"] = codigo
                    st.session_state["etapa"] = "requisicao"
                    st.rerun()
                    return True
                else:
                    st.error("🚫 Crachá não cadastrado!")
                    time.sleep(1)
                    st.rerun()
                    return True
                    
        elif st.session_state["etapa"] == "requisicao":
            if len(codigo) == 12 and codigo.isdigit():
                ja_registrado, tempo_passado, data_registro = requisicao_ja_registrada(
                    st.session_state["codigo_funcionario"], 
                    codigo
                )
                
                if ja_registrado:
                    st.error(f"🚫 Você já bipou esse item em {data_registro}.")
                else:
                    data_hora_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    sucesso = salvar_requisicao(
                        st.session_state["codigo_funcionario"], 
                        codigo, 
                        data_hora_atual
                    )
                    
                    if sucesso:
                        st.success(f"✅ Requisição registrada com sucesso!\n🕒 {data_hora_atual}")
                    else:
                        st.error("❌ Erro ao registrar requisição. Tente novamente.")
                
                time.sleep(1)
                st.rerun()
                return True
                
    return False

# Verificar a página atual e carregar o conteúdo correspondente
if st.session_state["page"] == "admin":
    import admin
    admin.app()
    st.stop()
else:
    # Verificar se há um código de barras para processar
    processar_codigo_barras()
    
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
        
        # Opção para habilitar/desabilitar detecção automática
        auto_detection = st.checkbox("Habilitar detecção automática (sem Enter)", 
                               value=st.session_state["auto_detection"],
                               key="auto_detection_checkbox")
        st.session_state["auto_detection"] = auto_detection
        
        if auto_detection:
            st.info("✨ Detecção automática ativada. Apenas escaneie seu crachá sem pressionar Enter.")
        else:
            st.info("🔄 Escaneie seu crachá e pressione Enter para confirmar.")
        
        # Campo para entrada manual
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
        
        # Opção para habilitar/desabilitar detecção automática
        auto_detection = st.checkbox("Habilitar detecção automática (sem Enter)", 
                               value=st.session_state["auto_detection"],
                               key="auto_detection_requisicao")
        st.session_state["auto_detection"] = auto_detection
        
        if auto_detection:
            st.info("✨ Detecção automática ativada. Apenas escaneie o código sem pressionar Enter.")
        else:
            st.info("🔄 Escaneie o código e pressione Enter para confirmar.")
        
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
            if not codigo_requisicao.isdigit() or len(codigo_requisicao) != 12:
                st.error("⚠ O código de barras precisa ter exatamente **12 números**!")
                resetar_input()
                st.rerun()
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