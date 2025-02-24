import streamlit as st
import sqlite3

# Configuração da página
st.set_page_config(page_title="Cadastro de Funcionários", layout="centered")

st.markdown("<h1 style='text-align: center; font-size: 18px;'>Cadastro de Funcionários</h1>", unsafe_allow_html=True)

# Conectar ao banco
conn = sqlite3.connect("sistema.db")
cursor = conn.cursor()

# Criar formulário
with st.form("cadastro_form"):
    nome = st.text_input("Nome", max_chars=50)
    cpf = st.text_input("CPF", max_chars=11)
    setor = st.text_input("Setor", max_chars=30)
    codigo = st.text_input("Código do Crachá", max_chars=10)

    # Botões
    col1, col2 = st.columns(2)
    with col1:
        limpar = st.form_submit_button("🧹 Limpar")
    with col2:
        cadastrar = st.form_submit_button("✅ Cadastrar")

# Ação do botão "Cadastrar"
if cadastrar:
    if nome and cpf and setor and codigo:
        try:
            cursor.execute("INSERT INTO FUNCIONARIOS (nome, cpf, setor, codigo) VALUES (?, ?, ?, ?)",
                           (nome, cpf, setor, codigo))
            conn.commit()
            st.success(f"✅ Funcionário {nome} cadastrado com sucesso!")
        except sqlite3.IntegrityError:
            st.error("❌ CPF ou Código já cadastrados!")
    else:
        st.warning("⚠️ Preencha todos os campos!")

conn.close()
