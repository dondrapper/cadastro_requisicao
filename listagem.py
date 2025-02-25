import streamlit as st
import sqlite3
import pandas as pd
import os

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

# 🔹 ✅ Criar a função `app()` para ser chamada pelo `admin.py`
def app():
    """Carrega a página de listagem de crachás."""

    # 🔹 ✅ Carregar CSS externo se disponível
    if os.path.exists("style.css"):
        with open("style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    # 🔹 ✅ Exibir título centralizado
    st.markdown("<h1 class='title'>📋 Listagem de Crachás</h1>", unsafe_allow_html=True)

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

        st.markdown("### 📜 Lista de Crachás:")
        st.write("Selecione os funcionários que deseja excluir e clique no botão **Excluir Selecionados**.")

        # Adicionando checkbox na primeira coluna
        df.insert(0, "Selecionar", False)

        # Criar tabela interativa usando `st.data_editor()`
        tabela_editavel = st.data_editor(
            df,
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

        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("📌 Nenhum funcionário cadastrado.")

# 🔹 ✅ Garantia que o script seja executado corretamente
if __name__ == "__main__":
    app()
