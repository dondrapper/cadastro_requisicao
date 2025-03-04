import streamlit as st
import sqlite3
from datetime import datetime
import time
import os
import json
import streamlit.components.v1 as components

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
if "js_counter" not in st.session_state:
    st.session_state["js_counter"] = 0

# Incrementar contador para garantir a execução do JavaScript
st.session_state["js_counter"] += 1

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

# Script JavaScript para proteção do botão Deploy e foco automático
def injetar_js_protetor():
    counter = st.session_state["js_counter"]
    etapa_atual = st.session_state["etapa"]
    js_code = f"""
    <script>
    // Função executada quando a página carrega
    (function() {{
        console.log("Inicializando proteção do botão Deploy (counter: {counter})");
        
        // 1. Proteger o botão Deploy
        function protectDeployButton() {{
            // Encontrar o botão Deploy (usa o seletor de um botão que contenha "Deploy" no texto ou esteja no cabeçalho)
            const deployButton = window.parent.document.querySelector('button[data-baseweb="button"]');
            if (deployButton) {{
                console.log("Botão Deploy encontrado, aplicando proteção");
                
                // Criar um bloqueador de eventos para o botão
                const blockHandler = function(event) {{
                    // Se o evento não foi gerado por um clique humano direto
                    if (!event.isTrusted) {{
                        console.log("Bloqueando clique automático no botão Deploy");
                        event.preventDefault();
                        event.stopPropagation();
                        event.stopImmediatePropagation();
                        return false;
                    }}
                }};
                
                // Adicionar o bloqueador em fase de captura
                deployButton.addEventListener('click', blockHandler, true);
                
                // Podemos também desabilitar temporariamente o botão durante a leitura
                const originalPointerEvents = deployButton.style.pointerEvents;
                
                // Monitorar teclas para detectar leitura de código de barras
                let barcodeBuffer = '';
                let lastKeyTime = 0;
                const MAX_DELAY = 100;  // ms entre teclas
                
                window.parent.document.addEventListener('keydown', function(event) {{
                    const currentTime = new Date().getTime();
                    
                    // Se é parte de uma leitura rápida (típico de scanner)
                    if (event.key.length === 1 && /[\\d]/.test(event.key)) {{
                        if (currentTime - lastKeyTime > MAX_DELAY) {{
                            // Nova leitura iniciando, desabilitar botão temporariamente
                            deployButton.style.pointerEvents = 'none';
                            barcodeBuffer = '';
                        }}
                        barcodeBuffer += event.key;
                        lastKeyTime = currentTime;
                    }}
                    else if (event.key === 'Enter' && barcodeBuffer.length > 0) {{
                        // Fim da leitura, processar e restaurar botão após um delay
                        setTimeout(function() {{
                            deployButton.style.pointerEvents = originalPointerEvents;
                        }}, 500);
                        
                        // Se causou problemas com o botão Deploy, parar propagação do Enter
                        if (event.target.tagName === 'INPUT') {{
                            event.stopPropagation();
                        }}
                    }}
                }}, true);
                
                return true;
            }}
            return false;
        }}
        
        // 2. Focar no campo de entrada apropriado com base na etapa atual
        function focusInput() {{
            // Determinar qual campo focar com base na etapa atual
            const etapa = '{etapa_atual}';
            let inputSelector = '';
            
            if (etapa === 'login') {{
                // Na tela de login, procurar campo de crachá
                inputSelector = 'input[aria-label="Escaneie seu Crachá"]';
            }} else if (etapa === 'requisicao') {{
                // Na tela de requisição, procurar campo de código de barras
                inputSelector = 'input[aria-label="Escaneie o código do item (Apenas números, 12 caracteres)"]';
            }}
            
            if (inputSelector) {{
                const inputField = window.parent.document.querySelector(inputSelector);
                if (inputField) {{
                    console.log("Campo encontrado para etapa " + etapa + ", aplicando foco");
                    setTimeout(() => inputField.focus(), 100);
                    return true;
                }}
            }}
            
            // Fallback: tentar focar em qualquer input de texto visível
            const visibleInputs = window.parent.document.querySelectorAll('input[type="text"]:not([disabled]):not([readonly])');
            if (visibleInputs.length > 0) {{
                console.log("Campo de entrada encontrado (fallback), aplicando foco");
                setTimeout(() => visibleInputs[0].focus(), 100);
                return true;
            }}
            
            return false;
        }}
        
        // Tenta aplicar as proteções imediatamente
        let deployProtected = protectDeployButton();
        let inputFocused = focusInput();
        
        // Se falhar, tentar novamente após um curto delay (DOM pode não estar totalmente carregado)
        if (!deployProtected || !inputFocused) {{
            setTimeout(function() {{
                if (!deployProtected) deployProtected = protectDeployButton();
                if (!inputFocused) inputFocused = focusInput();
            }}, 300);
        }}
    }})();
    </script>
    """
    
    # Injetar o JavaScript via components.html
    components.html(js_code, height=0)

# Verificar a página atual e carregar o conteúdo correspondente
if st.session_state["page"] == "admin":
    import admin
    admin.app()
    st.stop()
else:
    # Injetar JavaScript de proteção do botão Deploy e foco automático
    injetar_js_protetor()
    
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