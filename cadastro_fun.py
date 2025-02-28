"""
Módulo de cadastro de funcionários e geração de crachás.
"""

import streamlit as st
import os
from utils import download_cracha, validar_cpf, carregar_estilo_css
from database import cadastrar_funcionario

# Carregar CSS se existir
if os.path.exists("style.css"):
    with open("style.css") as css:
        st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)

def app():
    """
    Inicializa a interface de cadastro de funcionários e geração de crachás.
    """
    st.markdown("<h1 style='text-align: center;'>Cadastro de Funcionários</h1>", unsafe_allow_html=True)

    # Lista de setores disponíveis
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
        """Limpa todos os campos de input e reseta o estado."""
        st.session_state["nome"] = ""
        st.session_state["cpf"] = ""
        st.session_state["setor"] = setores[0]
        st.session_state["cadastro_bem_sucedido"] = False
        st.session_state["func_cadastrado"] = {}
        st.session_state["input_key"] += 1

    # Se o cadastro foi bem-sucedido, mostrar o crachá
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
        with st.form("cadastro_form", clear_on_submit=False):
            nome = st.text_input("Nome", max_chars=50, value=st.session_state["nome"], key=f"nome_input_{st.session_state['input_key']}")
            cpf = st.text_input("CPF (Apenas números)", max_chars=11, value=st.session_state["cpf"], key=f"cpf_input_{st.session_state['input_key']}")
            
            # Forçando uma chave única para o selectbox
            setor_key = f"setor_input_{st.session_state['input_key']}"
            setor = st.selectbox(
                "Setor", 
                options=setores,
                index=setores.index(st.session_state["setor"]) if st.session_state["setor"] in setores else 0,
                key=setor_key
            )

            codigo = cpf if validar_cpf(cpf) else ""
            st.text_input("Código do Crachá", value=codigo, disabled=True, key=f"codigo_cracha_{st.session_state['input_key']}")

            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                limpar = st.form_submit_button("🧹 Limpar")
                if limpar:
                    limpar_inputs()
                    st.rerun()
            with col3:
                cadastrar = st.form_submit_button("✅ Cadastrar e Gerar Crachá")

        if cadastrar:
            if nome and cpf and setor:
                if not validar_cpf(cpf):
                    st.error("⚠️ O CPF deve conter **exatamente 11 números**!")
                else:
                    # Atualizar o valor no session_state antes de cadastrar
                    st.session_state["setor"] = setor
                    sucesso, mensagem = cadastrar_funcionario(nome, cpf, setor, cpf)
                    
                    if sucesso:
                        # Atualizar estados de sessão
                        st.session_state["cadastro_bem_sucedido"] = True
                        st.session_state["func_cadastrado"] = {
                            "nome": nome,
                            "cpf": cpf,
                            "setor": setor
                        }
                        
                        st.rerun()  # Recarregar a página para mostrar o crachá
                    else:
                        st.error(f"❌ {mensagem}")
            else:
                st.warning("⚠️ Preencha todos os campos!")

# Garantia que o script seja executado corretamente
if __name__ == "__main__":
    app()