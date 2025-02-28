"""
Módulo para comunicação entre a extensão Chrome e o aplicativo Streamlit.
Fornece endpoints para recebimento de códigos de barras.
"""

import streamlit as st
import json
import time
from datetime import datetime
from database import autenticar_funcionario, requisicao_ja_registrada, salvar_requisicao

# Inicialização das variáveis de sessão - deve ser executado no início do módulo
def init_session_state():
    """Inicializa as variáveis de sessão necessárias para o módulo."""
    if "barcode_data" not in st.session_state:
        st.session_state["barcode_data"] = None
    if "last_barcode_time" not in st.session_state:
        st.session_state["last_barcode_time"] = 0
    if "barcode_messages" not in st.session_state:
        st.session_state["barcode_messages"] = []
    if "last_processed_barcode" not in st.session_state:
        st.session_state["last_processed_barcode"] = None

# Inicializar as variáveis de sessão
init_session_state()

def init_barcode_listener():
    """
    Inicializa o listener de códigos de barras.
    Este método deve ser chamado na inicialização do aplicativo principal.
    """
    # Garantir que as variáveis de sessão estejam inicializadas
    init_session_state()
    
    # Adicionar hook para verificação periódica de novos códigos
    # Será usado JavaScript no frontend para comunicação com a extensão
    js_code = """
    <script>
    // Configuração para receber mensagens da extensão Chrome
    window.addEventListener('message', function(event) {
        if (event.data && event.data.type === 'barcode_data') {
            // Enviar dados para o Streamlit via sessionStorage e forçar rerun
            sessionStorage.setItem('barcode_data', JSON.stringify(event.data));
            window.dispatchRerun.dispatchMessage('rerun');
        }
    }, false);
    
    // Hook para verificar se há dados de código de barras no sessionStorage
    function checkBarcodeData() {
        const data = sessionStorage.getItem('barcode_data');
        if (data) {
            // Limpar dados após leitura
            sessionStorage.removeItem('barcode_data');
            // Enviar para o backend do Streamlit
            const args = {
                barcode: JSON.parse(data)
            };
            window.Streamlit.setComponentValue(args);
        }
        setTimeout(checkBarcodeData, 50); // Verificar mais frequentemente (50ms)
    }
    
    // Iniciar a verificação
    checkBarcodeData();
    </script>
    """
    
    # Injetar o código JavaScript
    st.components.v1.html(js_code, height=0)

def process_incoming_barcode(barcode_value):
    """
    Processa um código de barras recebido da extensão Chrome.
    
    Args:
        barcode_value (str): Valor do código de barras
    
    Returns:
        tuple: (processado, mensagem)
    """
    # Verificar se é o mesmo código que acabou de ser processado (debounce)
    if st.session_state.get("last_processed_barcode") == barcode_value:
        # Se foi processado nos últimos 0.5 segundos, ignora
        current_time = time.time()
        if current_time - st.session_state.get("last_barcode_time", 0) < 0.5:
            return False, "Código repetido ignorado"
    
    # Atualizar o último código processado e timestamp
    st.session_state["last_processed_barcode"] = barcode_value
    st.session_state["last_barcode_time"] = time.time()
    
    # Verificar se o código é válido
    if not barcode_value or not isinstance(barcode_value, str) or not barcode_value.isdigit():
        return False, "Código de barras inválido"
    
    # Verificar a etapa atual do sistema
    etapa_atual = st.session_state.get("etapa", "login")
    
    # --- ETAPA DE LOGIN (CRACHÁ) ---
    if etapa_atual == "login":
        # Tentar autenticar como crachá de funcionário
        nome = autenticar_funcionario(barcode_value)
        if nome:
            # Autenticação bem-sucedida
            st.session_state["usuario"] = nome
            st.session_state["codigo_funcionario"] = barcode_value
            st.session_state["etapa"] = "requisicao"
            return True, f"Funcionário autenticado: {nome}"
        else:
            return False, "Crachá não cadastrado"
    
    # --- ETAPA DE REQUISIÇÃO ---
    elif etapa_atual == "requisicao":
        # Verificar se há um usuário autenticado
        if "usuario" not in st.session_state or "codigo_funcionario" not in st.session_state:
            return False, "Usuário não autenticado"
        
        # Verificar formato do código de requisição (12 dígitos)
        if len(barcode_value) != 12:
            return False, "Código de requisição inválido (deve ter 12 dígitos)"
        
        # Verificar requisição já registrada
        ja_registrado, tempo_passado, data_registro = requisicao_ja_registrada(
            st.session_state["codigo_funcionario"], 
            barcode_value
        )
        
        if ja_registrado:
            return False, f"Requisição já registrada em {data_registro}"
        
        # Registrar nova requisição
        data_hora_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sucesso = salvar_requisicao(
            st.session_state["codigo_funcionario"], 
            barcode_value, 
            data_hora_atual
        )
        
        if sucesso:
            return True, f"Requisição registrada com sucesso: {barcode_value}"
        else:
            return False, "Erro ao registrar requisição"
    
    else:
        return False, f"Etapa não reconhecida: {etapa_atual}"

def check_for_barcode():
    """
    Verifica se há um novo código de barras disponível.
    Deve ser chamado periodicamente no loop principal do Streamlit.
    """
    # Garantir que as variáveis de sessão estejam inicializadas
    init_session_state()
    
    # Verificar se há dados no session_state (colocados pelo JavaScript)
    if "barcode_data" in st.session_state and st.session_state["barcode_data"]:
        barcode_value = st.session_state["barcode_data"]
        st.session_state["barcode_data"] = None  # Limpar após processamento
        
        # Processar o código
        success, message = process_incoming_barcode(barcode_value)
        
        # Adicionar mensagem ao histórico
        st.session_state["barcode_messages"].append({
            "success": success,
            "message": message,
            "time": datetime.now().strftime("%H:%M:%S")
        })
        
        # Manter apenas as 5 últimas mensagens
        if len(st.session_state["barcode_messages"]) > 5:
            st.session_state["barcode_messages"] = st.session_state["barcode_messages"][-5:]
        
        # Retornar True para indicar que um código foi processado
        return True
    
    return False

def display_barcode_messages():
    """
    Exibe as mensagens relacionadas à leitura de códigos de barras.
    """
    # Garantir que as variáveis de sessão estejam inicializadas
    init_session_state()
    
    if st.session_state["barcode_messages"]:
        for msg in st.session_state["barcode_messages"]:
            if msg["success"]:
                st.success(f"[{msg['time']}] {msg['message']}")
            else:
                st.error(f"[{msg['time']}] {msg['message']}")