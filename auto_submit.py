"""
Módulo para detecção e processamento automático de códigos de barras no Streamlit
sem a necessidade de pressionar Enter ou usar a extensão Chrome.
"""

import streamlit as st
import time
from datetime import datetime

class AutoSubmitDetector:
    """Classe para detectar e processar automaticamente códigos de barras"""
    
    def __init__(self):
        # Inicializar variáveis de estado
        if "auto_code_buffer" not in st.session_state:
            st.session_state["auto_code_buffer"] = ""
        if "last_char_time" not in st.session_state:
            st.session_state["last_char_time"] = 0
        if "processed_codes" not in st.session_state:
            st.session_state["processed_codes"] = set()
        
        # Configurações
        self.timeout = 0.5  # Tempo em segundos para considerar que a entrada terminou
        self.min_code_length = 8  # Tamanho mínimo de um código válido
    
    def inject_listener(self):
        """Injeta o código JavaScript para capturar teclas pressionadas"""
        js_code = """
        <script>
        // Função para enviar tecla pressionada para o Streamlit
        function sendKeyToStreamlit(key) {
            const data = {
                key: key,
                time: Date.now()
            };
            
            // Usar sessionStorage para comunicação com Streamlit
            sessionStorage.setItem('keypress_data', JSON.stringify(data));
            
            // Forçar recarregamento para processar a tecla
            window.dispatchRerun.dispatchMessage('rerun');
        }
        
        // Listener para capturar teclas
        document.addEventListener('keypress', function(e) {
            // Capturar apenas teclas relevantes (dígitos, Enter)
            if (/^\\d$/.test(e.key) || e.key === 'Enter') {
                sendKeyToStreamlit(e.key);
                // Evitar comportamento padrão para Enter
                if (e.key === 'Enter') {
                    e.preventDefault();
                }
            }
        });
        
        // Verificar periodicamente por dados no sessionStorage
        function checkKeyPressData() {
            try {
                const keypressData = sessionStorage.getItem('keypress_buffer');
                if (keypressData) {
                    const data = JSON.parse(keypressData);
                    // Enviar para o Streamlit
                    window.Streamlit.setComponentValue(data);
                    // Limpar após leitura
                    sessionStorage.removeItem('keypress_buffer');
                }
            } catch (e) {
                console.error('Erro ao processar dados:', e);
            }
            
            // Verificar novamente em 50ms
            setTimeout(checkKeyPressData, 50);
        }
        
        // Iniciar verificação
        checkKeyPressData();
        </script>
        """
        
        # Injetar o código JavaScript
        st.components.v1.html(js_code, height=0)
    
    def check_buffer(self):
        """Verifica se o buffer contém um código completo"""
        current_time = time.time()
        buffer = st.session_state["auto_code_buffer"]
        
        # Se o buffer está vazio, não há nada para processar
        if not buffer:
            return None
        
        # Se passou tempo suficiente desde o último caractere, considerar completo
        if current_time - st.session_state["last_char_time"] > self.timeout:
            # Verificar se o buffer tem tamanho mínimo válido
            if len(buffer) >= self.min_code_length:
                # Limpar o buffer e retornar o código
                code = buffer
                st.session_state["auto_code_buffer"] = ""
                
                # Verificar se já foi processado recentemente
                if code in st.session_state["processed_codes"]:
                    return None
                
                # Adicionar ao conjunto de códigos processados
                st.session_state["processed_codes"].add(code)
                
                # Limitar o tamanho do conjunto de códigos processados
                if len(st.session_state["processed_codes"]) > 100:
                    # Remover os códigos antigos
                    st.session_state["processed_codes"] = set(list(st.session_state["processed_codes"])[-50:])
                
                return code
            else:
                # Buffer muito pequeno, provavelmente inválido
                st.session_state["auto_code_buffer"] = ""
                return None
        
        return None
    
    def add_char(self, char):
        """Adiciona um caractere ao buffer"""
        if char == 'Enter':
            # Enter força o processamento imediato
            code = st.session_state["auto_code_buffer"]
            st.session_state["auto_code_buffer"] = ""
            
            if len(code) >= self.min_code_length:
                return code
            return None
        else:
            # Adicionar o caractere ao buffer
            st.session_state["auto_code_buffer"] += char
            st.session_state["last_char_time"] = time.time()
            return None
    
    def process_keypress(self):
        """Processa dados de tecla pressionada do sessionStorage"""
        # Esta função é chamada pelo frontend quando dados estão disponíveis
        pass