import streamlit as st
import sqlite3
import time  
import os

# No início do seu arquivo, logo após imports e set_page_config
if os.path.exists("style.css"):
    with open("style.css") as css:
        st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)

# 🔹 ✅ Função para carregar a interface do cadastro de crachá
def app():
    
    
    st.markdown("<h1 style='text-align: center;'>Cadastro de Funcionários</h1>", unsafe_allow_html=True)

    setores = ["Dermato", "Farmacêutica", "Xarope", "Peso Médio", "Conferência", "Encapsulação", "Pesagem", "Sache"]

    if "nome" not in st.session_state:
        st.session_state["nome"] = ""
    if "cpf" not in st.session_state:
        st.session_state["cpf"] = ""
    if "setor" not in st.session_state:
        st.session_state["setor"] = setores[0]  

    def limpar_inputs():
        st.session_state["nome"] = ""
        st.session_state["cpf"] = ""
        st.session_state["setor"] = setores[0]
        st.session_state["input_key"] += 1  

    if "input_key" not in st.session_state:
        st.session_state["input_key"] = 0

    with st.form("cadastro_form"):
        nome = st.text_input("Nome", max_chars=50, value=st.session_state["nome"], key=f"nome_input_{st.session_state['input_key']}")
        cpf = st.text_input("CPF (Apenas números)", max_chars=11, value=st.session_state["cpf"], key=f"cpf_input_{st.session_state['input_key']}")
        setor = st.selectbox("Setor", setores, index=setores.index(st.session_state["setor"]), key=f"setor_input_{st.session_state['input_key']}")

        codigo = cpf if cpf.isdigit() and len(cpf) == 11 else ""

        st.text_input("Código do Crachá", value=codigo, disabled=True, key=f"codigo_cracha_{st.session_state['input_key']}")

        col1, col2 = st.columns(2)
        with col1:
            limpar = st.form_submit_button("🧹 Limpar", on_click=limpar_inputs)
        with col2:
            cadastrar = st.form_submit_button("✅ Cadastrar")

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

                    time.sleep(2)
                    limpar_inputs()

                except sqlite3.IntegrityError:
                    st.error("❌ CPF ou Código já cadastrados!")
        else:
            st.warning("⚠️ Preencha todos os campos!")

# 🔹 ✅ Garantia que o script seja executado corretamente
if __name__ == "__main__":
    app()
