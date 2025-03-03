"""
Módulo de utilitários para o sistema de controle.
Contém funções reutilizáveis para geração e manipulação de crachás.
"""

import os
import barcode
from barcode.writer import ImageWriter
import streamlit as st
import io
from PIL import Image, ImageDraw, ImageFont
import base64
import bcrypt

def gerar_cracha(codigo, nome, setor):
    """
    Gera um crachá com código de barras para o funcionário.
    
    Args:
        codigo (str): Código do funcionário (CPF).
        nome (str): Nome do funcionário.
        setor (str): Setor do funcionário.
        
    Returns:
        bytes: Imagem do crachá em formato bytes ou None em caso de erro.
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
    Cria um botão para download do crachá no Streamlit.
    
    Args:
        codigo (str): Código do funcionário (CPF).
        nome (str): Nome do funcionário.
        setor (str): Setor do funcionário.
        
    Returns:
        bool: True se o crachá foi gerado e disponibilizado para download, False caso contrário.
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

def hash_senha(senha):
    """
    Cria um hash seguro para a senha usando bcrypt.
    
    Args:
        senha (str): Senha em texto simples.
        
    Returns:
        str: Hash da senha codificado.
    """
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

def verificar_senha(senha_digitada, senha_armazenada):
    """
    Verifica se a senha digitada corresponde ao hash armazenado.
    
    Args:
        senha_digitada (str): Senha fornecida pelo usuário.
        senha_armazenada (str): Hash da senha armazenado no banco.
        
    Returns:
        bool: True se a senha corresponde ao hash, False caso contrário.
    """
    return bcrypt.checkpw(senha_digitada.encode(), senha_armazenada.encode())

def validar_cpf(cpf):
    """
    Valida se o CPF possui 11 dígitos e contém apenas números.
    
    Args:
        cpf (str): CPF a ser validado.
        
    Returns:
        bool: True se o CPF é válido, False caso contrário.
    """
    return cpf.isdigit() and len(cpf) == 11

def carregar_estilo_css():
    """
    Carrega o arquivo CSS se existir e aplica ao Streamlit.
    
    Returns:
        bool: True se o arquivo foi carregado, False caso contrário.
    """
    try:
        if os.path.exists("style.css"):
            with open("style.css") as css:
                st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)
            return True
        return False
    except Exception:
        return False