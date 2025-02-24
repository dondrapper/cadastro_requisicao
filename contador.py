import streamlit as st
import time

# Configura a página
st.set_page_config(page_title="Contador de Login", layout="wide")

# CSS para posicionar o contador no canto inferior direito
contador_css = """
    <style>
        .contador-container {
            position: fixed;
            bottom: 10px;
            right: 10px;
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 18px;
            font-weight: bold;
        }
    </style>
"""

# Exibe o CSS personalizado
st.markdown(contador_css, unsafe_allow_html=True)

# Inicializa o estado da sessão para armazenar o tempo restante
if "tempo_restante" not in st.session_state:
    st.session_state["tempo_restante"] = 10  # 10 segundos

# Loop da contagem regressiva
for i in range(10, -1, -1):
    st.session_state["tempo_restante"] = i

    # Define a mensagem com base no tempo restante
    if i > 5:
        mensagem = "⌛ Tempo de login"
    elif i > 0:
        mensagem = "⏳ Prepare-se, reiniciando"
    else:
        mensagem = "🔴 Reiniciando agora..."

    # Exibe o contador no canto da tela
    contador_html = f"""
        <div class="contador-container">
            {mensagem} ({i}s)
        </div>
    """
    st.markdown(contador_html, unsafe_allow_html=True)

    time.sleep(1)  # Aguarda 1 segundo

# Mensagem final quando o tempo acabar
contador_html = """
    <div class="contador-container" style="background-color: red;">
        🔄 Reiniciando...
    </div>
"""
st.markdown(contador_html, unsafe_allow_html=True)
