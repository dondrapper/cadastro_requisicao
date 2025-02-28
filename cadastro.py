import streamlit as st
import sqlite3
import os

# No início do seu arquivo, logo após imports e set_page_config
if os.path.exists("style.css"):
    with open("style.css") as css:
        st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)
def app():
    

    st.markdown("<h1 style='text-align: center;'>Cadastro de Usuários 👤</h1>", unsafe_allow_html=True)

    usuario = st.text_input("Usuário 👤")
    senha = st.text_input("Senha 🔒", type="password")
    senha_confirma = st.text_input("Confirme a Senha 🔒", type="password")

    if st.button("Cadastrar Usuário ✅"):
        if not usuario or not senha or not senha_confirma:
            st.warning("Por favor, preencha todos os campos.")
        elif senha != senha_confirma:
            st.error("As senhas não conferem!")
        else:
            try:
                conn = sqlite3.connect("sistema.db")
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM ADMINISTRADORES WHERE usuario = ?", (usuario,))
                if cursor.fetchone():
                    st.error("Usuário já cadastrado!")
                else:
                    cursor.execute("INSERT INTO ADMINISTRADORES (usuario, senha) VALUES (?, ?)", (usuario, senha))
                    conn.commit()
                    st.success("Usuário cadastrado com sucesso! 🎉")
                    
            except Exception as e:
                st.error("Erro ao cadastrar usuário: " + str(e))
            finally:
                conn.close()

if __name__ == "__main__":
    app()
