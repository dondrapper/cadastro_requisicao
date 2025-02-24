import streamlit as st
import sqlite3
import pandas as pd

# Função para conectar ao banco de dados
def conectar_banco():
    return sqlite3.connect("sistema.db")

# Função para carregar funcionários
def carregar_funcionarios():
    conn = conectar_banco()
    df = pd.read_sql("SELECT id, nome, cpf, setor, codigo FROM FUNCIONARIOS", conn)
    conn.close()
    return df

# Função para excluir funcionário
def excluir_funcionario(funcionario_id):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM FUNCIONARIOS WHERE id = ?", (funcionario_id,))
    conn.commit()
    conn.close()

# Configuração da interface
st.set_page_config(page_title="Lista de Funcionários", layout="centered")

st.markdown("<h1 style='text-align: center;'>Funcionários Cadastrados</h1>", unsafe_allow_html=True)

# Botão para atualizar a lista
if st.button("🔄 Atualizar Lista"):
    st.experimental_rerun()

# Carregar e exibir os funcionários
df = carregar_funcionarios()

# Exibir em formato de planilha com botão de exclusão
if not df.empty:
    for index, row in df.iterrows():
        col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 2, 1])
        col1.write(f"**{row['nome']}**")
        col2.write(row['cpf'])
        col3.write(row['setor'])
        col4.write(row['codigo'])
        
        # Botão de exclusão
        if col6.button("❌ Excluir", key=row["id"]):
            excluir_funcionario(row["id"])
            st.warning(f"⚠️ Funcionário {row['nome']} removido!")
            st.experimental_rerun()

else:
    st.info("📌 Nenhum funcionário cadastrado.")
