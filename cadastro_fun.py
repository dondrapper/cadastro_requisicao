import streamlit as st
import sqlite3
import time  
import os
import io
import base64
from PIL import Image, ImageDraw, ImageFont

# No início do seu arquivo, logo após imports e set_page_config
if os.path.exists("style.css"):
    with open("style.css") as css:
        st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)

# Importar as funções de utilidade
try:
    from utils import gerar_cracha, download_cracha
except ImportError:
    # Definir as funções aqui como fallback se o arquivo utils.py não existir
    import barcode
    from barcode.writer import ImageWriter
    
    def gerar_cracha(codigo, nome, setor):
        """
        Gera um crachá com código de barras para o funcionário
        
        Args:
            codigo (str): Código do funcionário (CPF)
            nome (str): Nome do funcionário
            setor (str): Setor do funcionário
            
        Returns:
            bytes: Imagem do crachá em formato bytes
        """
        try:
            # Obter o tipo de código de barras
            barcode_type = barcode.get_barcode_class("code128")
            
            # Criar o código de barras
            barcode_image = barcode_type(codigo, writer=ImageWriter())
            
            # Gerar a imagem do código de barras em memória
            buffer = io.BytesIO()
            barcode_image.write(buffer)
            
            # Criar o layout do crachá
            cracha = Image.new('RGB', (400, 600), color=(255, 255, 255))
            draw = ImageDraw.Draw(cracha)
            
            # Tentar usar uma fonte padrão ou uma que esteja disponível no sistema
            try:
                # Para título
                titulo_font = ImageFont.truetype("Arial", 24)
                # Para dados
                dados_font = ImageFont.truetype("Arial", 18)
            except IOError:
                # Fallback para fonte padrão
                titulo_font = ImageFont.load_default()
                dados_font = ImageFont.load_default()
            
            # Desenhar o cabeçalho do crachá
            draw.rectangle([(0, 0), (400, 60)], fill=(0, 102, 204))
            draw.text((200, 30), "CRACHÁ FUNCIONÁRIO", fill=(255, 255, 255), font=titulo_font, anchor="mm")
            
            # Adicionar dados do funcionário
            draw.text((20, 100), f"Nome: {nome}", fill=(0, 0, 0), font=dados_font)
            draw.text((20, 140), f"Setor: {setor}", fill=(0, 0, 0), font=dados_font)
            draw.text((20, 180), f"Código: {codigo}", fill=(0, 0, 0), font=dados_font)
            
            # Abrir a imagem do código de barras e redimensioná-la
            buffer.seek(0)
            barcode_img = Image.open(buffer)
            barcode_img = barcode_img.resize((360, 120))
            
            # Adicionar o código de barras ao crachá
            cracha.paste(barcode_img, (20, 220))
            
            # Desenhar o rodapé
            draw.rectangle([(0, 540), (400, 600)], fill=(0, 102, 204))
            draw.text((200, 570), "Uso exclusivo da empresa", fill=(255, 255, 255), font=dados_font, anchor="mm")
            
            # Salvar a imagem em bytes
            img_byte_arr = io.BytesIO()
            cracha.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            return img_byte_arr.getvalue()
        
        except Exception as e:
            st.error(f"Erro ao gerar crachá: {e}")
            return None

    def download_cracha(codigo, nome, setor):
        """
        Cria um botão para download do crachá
        
        Args:
            codigo (str): Código do funcionário (CPF)
            nome (str): Nome do funcionário
            setor (str): Setor do funcionário
        """
        cracha_bytes = gerar_cracha(codigo, nome, setor)
        
        if cracha_bytes:
            # Codificar a imagem para exibição e download
            b64 = base64.b64encode(cracha_bytes).decode()
            
            # Mostrar preview do crachá
            st.image(cracha_bytes, caption=f"Crachá de {nome}", width=300)
            
            # Criar link de download
            href = f'<a href="data:image/png;base64,{b64}" download="cracha_{codigo}.png">⬇️ Baixar Crachá</a>'
            st.markdown(href, unsafe_allow_html=True)
            
            return True
        return False

# 🔹 ✅ Função para carregar a interface do cadastro de crachá
def app():
    st.markdown("<h1 style='text-align: center;'>Cadastro de Funcionários</h1>", unsafe_allow_html=True)

    setores = ["Dermato", "Farmacêutica", "Xarope", "Peso Médio", "Conferência", "Encapsulação", "Pesagem", "Sache"]

    # Inicialização de estados de sessão
    if "nome" not in st.session_state:
        st.session_state["nome"] = ""
    if "cpf" not in st.session_state:
        st.session_state["cpf"] = ""
    if "setor" not in st.session_state:
        st.session_state["setor"] = setores[0]  
    if "input_key" not in st.session_state:
        st.session_state["input_key"] = 0
    if "cadastro_bem_sucedido" not in st.session_state:
        st.session_state["cadastro_bem_sucedido"] = False
    if "func_cadastrado" not in st.session_state:
        st.session_state["func_cadastrado"] = {}

    def limpar_inputs():
        st.session_state["nome"] = ""
        st.session_state["cpf"] = ""
        st.session_state["setor"] = setores[0]
        st.session_state["cadastro_bem_sucedido"] = False
        st.session_state["func_cadastrado"] = {}
        st.session_state["input_key"] += 1

    # Se o cadastro foi bem sucedido, mostrar o crachá
    if st.session_state["cadastro_bem_sucedido"]:
        func = st.session_state["func_cadastrado"]
        
        st.success(f"✅ Funcionário **{func['nome']}** cadastrado com sucesso!")
        st.subheader("Crachá Gerado")
        
        # Criar colunas para centralizar o crachá
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            download_cracha(func["cpf"], func["nome"], func["setor"])
        
        # Botão para voltar ao cadastro
        if st.button("🔄 Novo Cadastro"):
            limpar_inputs()
            st.rerun()
    else:
        # Formulário de cadastro
        with st.form("cadastro_form"):
            nome = st.text_input("Nome", max_chars=50, value=st.session_state["nome"], key=f"nome_input_{st.session_state['input_key']}")
            cpf = st.text_input("CPF (Apenas números)", max_chars=11, value=st.session_state["cpf"], key=f"cpf_input_{st.session_state['input_key']}")
            setor = st.selectbox("Setor", setores, index=setores.index(st.session_state["setor"]), key=f"setor_input_{st.session_state['input_key']}")

            codigo = cpf if cpf.isdigit() and len(cpf) == 11 else ""
            st.text_input("Código do Crachá", value=codigo, disabled=True, key=f"codigo_cracha_{st.session_state['input_key']}")

            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                limpar = st.form_submit_button("🧹 Limpar", on_click=limpar_inputs)
            with col3:
                cadastrar = st.form_submit_button("✅ Cadastrar e Gerar Crachá")

        if cadastrar:
            if nome and cpf and setor:
                if not cpf.isdigit() or len(cpf) != 11:
                    st.error("⚠️ O CPF deve conter **exatamente 11 números**!")
                else:
                    try:
                        conn = sqlite3.connect("sistema.db", timeout=10)
                        cursor = conn.cursor()

                        cursor.execute("INSERT INTO FUNCIONARIOS (nome, cpf, setor, codigo) VALUES (?, ?, ?, ?)",
                                    (nome, cpf, setor, cpf))
                        
                        conn.commit()
                        conn.close()
                        
                        # Atualizar estados de sessão
                        st.session_state["cadastro_bem_sucedido"] = True
                        st.session_state["func_cadastrado"] = {
                            "nome": nome,
                            "cpf": cpf,
                            "setor": setor
                        }
                        
                        st.rerun()  # Recarregar a página para mostrar o crachá

                    except sqlite3.IntegrityError:
                        st.error("❌ CPF ou Código já cadastrados!")
            else:
                st.warning("⚠️ Preencha todos os campos!")

# 🔹 ✅ Garantia que o script seja executado corretamente
if __name__ == "__main__":
    app()