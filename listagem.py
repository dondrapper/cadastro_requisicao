import streamlit as st
import sqlite3
import pandas as pd
import os
import io
import base64
from PIL import Image, ImageDraw, ImageFont

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

# 🔹 ✅ Função para conectar ao banco de dados
def conectar_banco():
    return sqlite3.connect("sistema.db")

# 🔹 ✅ Função para carregar funcionários
def carregar_funcionarios():
    conn = conectar_banco()
    df = pd.read_sql("SELECT id, nome, cpf, setor, codigo FROM FUNCIONARIOS", conn)
    conn.close()
    return df

# 🔹 ✅ Função para excluir múltiplos funcionários
def excluir_funcionarios(ids_selecionados):
    if ids_selecionados:
        conn = conectar_banco()
        cursor = conn.cursor()
        for funcionario_id in ids_selecionados:
            cursor.execute("DELETE FROM FUNCIONARIOS WHERE id = ?", (funcionario_id,))
        conn.commit()
        conn.close()
        st.success(f"✅ {len(ids_selecionados)} funcionário(s) removido(s) com sucesso!")
        st.rerun()

# 🔹 ✅ Função para obter detalhes de um funcionário pelo ID
def obter_funcionario(funcionario_id):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT nome, cpf, setor, codigo FROM FUNCIONARIOS WHERE id = ?", (funcionario_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            "nome": result[0],
            "cpf": result[1],
            "setor": result[2],
            "codigo": result[3]
        }
    return None

# 🔹 ✅ Criar a função `app()` para ser chamada pelo `admin.py`
def app():
    """Carrega a página de listagem de crachás."""

    # 🔹 ✅ Carregar CSS externo se disponível
    if os.path.exists("style.css"):
        with open("style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    # 🔹 ✅ Inicialização de estados de sessão
    if "exibindo_cracha" not in st.session_state:
        st.session_state["exibindo_cracha"] = False
    if "funcionario_id_selecionado" not in st.session_state:
        st.session_state["funcionario_id_selecionado"] = None

    # 🔹 ✅ Exibir título centralizado
    st.markdown("<h1 class='title'>📋 Listagem de Crachás</h1>", unsafe_allow_html=True)

    # 🔹 ✅ Verificar se está exibindo um crachá específico
    if st.session_state["exibindo_cracha"] and st.session_state["funcionario_id_selecionado"] is not None:
        func = obter_funcionario(st.session_state["funcionario_id_selecionado"])
        
        if func:
            st.markdown(f"<h2 style='text-align: center;'>Crachá de {func['nome']}</h2>", unsafe_allow_html=True)
            
            # Criar colunas para centralizar o crachá
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                download_cracha(func["cpf"], func["nome"], func["setor"])
                
            # Botão para voltar para a listagem
            if st.button("← Voltar para a listagem"):
                st.session_state["exibindo_cracha"] = False
                st.session_state["funcionario_id_selecionado"] = None
                st.rerun()
        else:
            st.error("Funcionário não encontrado")
            st.session_state["exibindo_cracha"] = False
            st.session_state["funcionario_id_selecionado"] = None
            st.rerun()
    else:
        # 🔹 ✅ Criando um container centralizado para os botões
        st.markdown("<div class='button-container'>", unsafe_allow_html=True)
        col1, col2 = st.columns([3, 1])  # Criar colunas para centralizar o botão de atualizar
        with col1:
            st.markdown("")  # Espaço vazio para alinhamento
        with col2:
            if st.button("🔄 Atualizar Lista", use_container_width=True):
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # 🔹 ✅ Carregar e exibir os funcionários em uma tabela formatada
        df = carregar_funcionarios()

        # 🔹 ✅ Criar tabela interativa centralizada com checkboxes para seleção
        if not df.empty:
            st.markdown("<div class='table-container'>", unsafe_allow_html=True)
            
            # Separar em duas tabs: Gerenciar Funcionários e Imprimir Crachás
            tab1, tab2 = st.tabs(["Gerenciar Funcionários", "Imprimir Crachás"])
            
            with tab1:
                st.markdown("### 📜 Lista de Funcionários:")
                st.write("Selecione os funcionários que deseja excluir e clique no botão **Excluir Selecionados**.")

                # Adicionando checkbox na primeira coluna
                df_select = df.copy()
                df_select.insert(0, "Selecionar", False)

                # Criar tabela interativa usando `st.data_editor()`
                tabela_editavel = st.data_editor(
                    df_select,
                    hide_index=True,
                    column_config={"Selecionar": st.column_config.CheckboxColumn()},
                    disabled=["id", "nome", "cpf", "setor", "codigo"],  # Bloqueia edição de outras colunas
                )

                # Filtrar os IDs dos funcionários selecionados para exclusão
                ids_selecionados = tabela_editavel.loc[tabela_editavel["Selecionar"], "id"].tolist()

                # 🔹 ✅ Centralizando o botão de exclusão
                col1, col2, col3 = st.columns([3, 2, 3])  # Criar colunas para alinhar o botão no centro
                with col2:
                    if ids_selecionados:
                        if st.button("❌ Excluir Selecionados", use_container_width=True):
                            excluir_funcionarios(ids_selecionados)
            
            with tab2:
                st.markdown("### 🖨️ Impressão de Crachás:")
                st.write("Selecione um funcionário para visualizar e imprimir seu crachá.")
                
                # Criar um selectbox para escolher o funcionário
                options = df['id'].tolist()
                
                if options:
                    funcionario_id = st.selectbox(
                        "Selecione um funcionário:",
                        options=options,
                        format_func=lambda x: df.loc[df['id'] == x, 'nome'].iloc[0]
                    )
                    
                    col1, col2, col3 = st.columns([3, 2, 3])
                    with col2:
                        if st.button("🖨️ Gerar Crachá", use_container_width=True):
                            st.session_state["funcionario_id_selecionado"] = funcionario_id
                            st.session_state["exibindo_cracha"] = True
                            st.rerun()
                else:
                    st.info("Nenhum funcionário disponível para impressão de crachá.")

            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("📌 Nenhum funcionário cadastrado.")

# 🔹 ✅ Garantia que o script seja executado corretamente
if __name__ == "__main__":
    app()