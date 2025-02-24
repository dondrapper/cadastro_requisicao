import streamlit as st
import sqlite3
import time  # Para aguardar antes de reiniciar

# Configuração da página
st.set_page_config(page_title="Cadastro de Funcionários", layout="centered")

st.markdown("<h1 style='text-align: center; font-size: 18px;'>Cadastro de Funcionários</h1>", unsafe_allow_html=True)

# Lista de setores fixos
setores = ["Dermato", "Farmacêutica", "Xarope", "Peso Médio", "Conferência", "Encapsulação", "Pesagem", "Sache"]

# 🔥 Inicializando os inputs no `st.session_state`
if "nome" not in st.session_state:
    st.session_state["nome"] = ""
if "cpf" not in st.session_state:
    st.session_state["cpf"] = ""
if "setor" not in st.session_state:
    st.session_state["setor"] = setores[0]  # Define um setor padrão

# Função para limpar inputs sem reiniciar a página
def limpar_inputs():
    st.session_state["nome"] = ""
    st.session_state["cpf"] = ""
    st.session_state["setor"] = setores[0]
    st.session_state["input_key"] += 1  # 🔥 Atualiza a key do input para resetar os campos

# Criar um identificador de chave dinâmico para os inputs
if "input_key" not in st.session_state:
    st.session_state["input_key"] = 0

# Criar formulário de cadastro
with st.form("cadastro_form"):
    nome = st.text_input("Nome", max_chars=50, value=st.session_state["nome"], key=f"nome_input_{st.session_state['input_key']}")
    cpf = st.text_input("CPF (Apenas números)", max_chars=11, value=st.session_state["cpf"], key=f"cpf_input_{st.session_state['input_key']}")
    setor = st.selectbox("Setor", setores, index=setores.index(st.session_state["setor"]), key=f"setor_input_{st.session_state['input_key']}")

    # Código do crachá gerado automaticamente com o CPF
    codigo = cpf if cpf.isdigit() and len(cpf) == 11 else ""

    # Exibir código do crachá automaticamente (somente leitura)
    st.text_input("Código do Crachá", value=codigo, disabled=True, key=f"codigo_cracha_{st.session_state['input_key']}")

    # Botões
    col1, col2 = st.columns(2)
    with col1:
        limpar = st.form_submit_button("🧹 Limpar", on_click=limpar_inputs)
    with col2:
        cadastrar = st.form_submit_button("✅ Cadastrar")

# Ação do botão "Cadastrar"
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

                st.success(f"✅ Funcionário **{nome}** cadastrado com sucesso!")

                # 🔥 Aguarda 2 segundos e reseta os campos sem travar a página
                time.sleep(2)
                limpar_inputs()

            except sqlite3.IntegrityError:
                st.error("❌ CPF ou Código já cadastrados!")
    else:
        st.warning("⚠️ Preencha todos os campos!")
