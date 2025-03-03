"""
Módulo da interface administrativa do sistema.
Gerencia o painel administrativo, autenticação e navegação.
"""

import streamlit as st
import time
import sqlite3
import pandas as pd
import relatorio_requisicoes
import listagem
import cadastro_fun
import cadastro
from auth import autenticar_admin
from functools import wraps

# Constantes para páginas
DASHBOARD = "dashboard"
CADASTRO_FUNCIONARIO = "cadastro_fun"
LISTAGEM_CRACHAS = "listagem"
RELATORIO_REQUISICOES = "requisicoes"
CADASTRO_USUARIO = "cadastro"
LOGIN = "login"

# Estrutura de menu para facilitar manutenção
MENU_ITEMS = [
    {"titulo": "📊 Dashboard", "pagina": DASHBOARD, "nivel": 1},
    {"titulo": "🆕 Cadastro de Crachá", "pagina": CADASTRO_FUNCIONARIO, "nivel": 1},
    {"titulo": "📋 Listagem de Crachás", "pagina": LISTAGEM_CRACHAS, "nivel": 1},
    {"titulo": "📑 Relatório de Requisições", "pagina": RELATORIO_REQUISICOES, "nivel": 1},
    {"titulo": "👤 Cadastrar Usuário", "pagina": CADASTRO_USUARIO, "nivel": 2},  # Nível mais alto para administradores
    {"titulo": "🚪 Logout", "pagina": None, "nivel": 1},  # Caso especial tratado separadamente
]

# Tempo limite de sessão em segundos (30 minutos)
TIMEOUT_SESSAO = 30 * 60

def inicializar_indices():
    """Cria índices para melhorar o desempenho das consultas"""
    try:
        conn = sqlite3.connect("sistema.db")
        cursor = conn.cursor()
        
        # Índice para busca rápida de funcionários por código
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_funcionarios_codigo ON FUNCIONARIOS(codigo)")
        
        # Índice para busca rápida de requisições por código de funcionário
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_requisicoes_codigo ON REQUISICOES(codigo_funcionario)")
        
        # Índice para busca rápida de requisições por data
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_requisicoes_data ON REQUISICOES(data)")
        
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Erro ao inicializar índices: {str(e)}")

def configurar_tema():
    """Configura o tema da interface administrativa"""
    # Configuração de tema em CSS
    st.markdown("""
    <style>
    .stApp {
        background-color: #f5f7fa;
    }
    .stButton button {
        border-radius: 10px;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    .stSidebar {
        background-color: #34495e;
        color: white !important;
    }
    .sidebar-title {
        color: white !important;
        padding: 10px 0;
    }
    .sidebar-info {
        color: #ecf0f1 !important;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

def inicializar_estado():
    """Inicializa variáveis de estado se necessário"""
    if "admin_authenticated" not in st.session_state:
        st.session_state["admin_authenticated"] = False
    
    if "admin_page" not in st.session_state:
        st.session_state["admin_page"] = DASHBOARD
        
    if "admin_nivel" not in st.session_state:
        st.session_state["admin_nivel"] = 1
        
    if "last_activity" not in st.session_state:
        st.session_state["last_activity"] = time.time()
        
    if "pagina_atual" not in st.session_state:
        st.session_state["pagina_atual"] = 1

def verificar_timeout():
    """Verifica se a sessão expirou por inatividade
    
    Returns:
        bool: True se a sessão expirou, False caso contrário
    """
    # Verifica se o tempo limite foi atingido
    if (time.time() - st.session_state["last_activity"]) > TIMEOUT_SESSAO:
        st.session_state["admin_authenticated"] = False
        st.warning("Sessão expirada por inatividade. Por favor, faça login novamente.")
        return True
    
    # Atualiza o tempo da última atividade
    st.session_state["last_activity"] = time.time()
    return False

def verificar_permissao(nivel_minimo):
    """Verifica se o usuário tem permissão para acessar recurso
    
    Args:
        nivel_minimo (int): Nível mínimo de permissão necessário
        
    Returns:
        bool: True se tem permissão, False caso contrário
    """
    nivel_usuario = st.session_state.get("admin_nivel", 0)
    return nivel_usuario >= nivel_minimo

def safe_db_operation(func):
    """Decorator para operações seguras de banco de dados"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except sqlite3.Error as e:
            st.error(f"Erro de banco de dados: {e}")
            return None
        except Exception as e:
            st.error(f"Erro inesperado: {e}")
            return None
    return wrapper

def operacao_com_feedback(mensagem):
    """Decorator para exibir feedback durante operações demoradas"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with st.spinner(mensagem):
                resultado = func(*args, **kwargs)
            return resultado
        return wrapper
    return decorator

@st.cache_data(ttl=300)  # Cache por 5 minutos
def carregar_estatisticas():
    """Carrega estatísticas com cache para melhorar desempenho
    
    Returns:
        tuple: (funcionarios_df, req_df) ou (None, None) em caso de erro
    """
    try:
        conn = sqlite3.connect("sistema.db")
        
        # Estatísticas de funcionários
        funcionarios_df = pd.read_sql("SELECT COUNT(*) as total, setor FROM FUNCIONARIOS GROUP BY setor", conn)
        
        # Estatísticas de requisições
        req_df = pd.read_sql("""
            SELECT COUNT(*) as total, 
                   strftime('%Y-%m-%d', data) as data 
            FROM REQUISICOES 
            GROUP BY strftime('%Y-%m-%d', data)
            ORDER BY data DESC
            LIMIT 7
        """, conn)
        
        conn.close()
        return funcionarios_df, req_df
    except Exception as e:
        st.error(f"Erro ao carregar estatísticas: {str(e)}")
        return None, None

def listar_com_paginacao(query, params=None, items_por_pagina=10):
    """Lista registros com paginação
    
    Args:
        query (str): Consulta SQL base
        params (tuple, optional): Parâmetros para a consulta
        items_por_pagina (int, optional): Itens por página
        
    Returns:
        pandas.DataFrame: DataFrame com os resultados da página atual
    """
    try:
        conn = sqlite3.connect("sistema.db")
        
        # Consulta de contagem
        count_query = f"SELECT COUNT(*) FROM ({query})"
        if params:
            total = pd.read_sql(count_query, conn, params=params).iloc[0, 0]
        else:
            total = pd.read_sql(count_query, conn).iloc[0, 0]
        
        # Consulta paginada
        pagina = st.session_state["pagina_atual"]
        offset = (pagina - 1) * items_por_pagina
        query_paginada = f"{query} LIMIT {items_por_pagina} OFFSET {offset}"
        
        if params:
            df = pd.read_sql(query_paginada, conn, params=params)
        else:
            df = pd.read_sql(query_paginada, conn)
        
        conn.close()
        
        # Exibir dados
        st.dataframe(df, use_container_width=True)
        
        # Exibir controles de paginação
        total_paginas = max(1, (total + items_por_pagina - 1) // items_por_pagina)
        
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            if st.button("⬅️ Anterior", disabled=pagina <= 1) and pagina > 1:
                st.session_state["pagina_atual"] -= 1
                st.rerun()
        
        with col2:
            st.markdown(f"**Página {pagina} de {total_paginas}** (Total: {total} registros)")
        
        with col3:
            if st.button("Próxima ➡️", disabled=pagina >= total_paginas) and pagina < total_paginas:
                st.session_state["pagina_atual"] += 1
                st.rerun()
        
        return df
    except Exception as e:
        st.error(f"Erro ao listar registros: {str(e)}")
        return pd.DataFrame()

def criar_menu_sidebar():
    """Cria menu na barra lateral para navegação mais eficiente"""
    with st.sidebar:
        st.markdown('<div class="sidebar-title"><h2>🔑 Menu Administrativo</h2></div>', unsafe_allow_html=True)
        
        # Adicionar informações do usuário logado
        st.markdown(f'<div class="sidebar-info"><b>Usuário:</b> {st.session_state.get("nome_usuario_logado", "Administrador")}</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-info"><b>Nível:</b> {}</div>'.format(
            "Administrador" if st.session_state.get("admin_nivel", 1) >= 2 else "Operador"
        ), unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Criar o menu na barra lateral
        for item in MENU_ITEMS:
            # Verificar permissão
            if verificar_permissao(item["nivel"]):
                if item["pagina"] is None:  # Caso de logout
                    if st.button(item["titulo"], type="primary", use_container_width=True):
                        st.session_state["admin_authenticated"] = False
                        st.session_state["page"] = "login"
                        st.rerun()
                else:
                    button_type = "primary" if st.session_state["admin_page"] == item["pagina"] else "secondary"
                    if st.button(item["titulo"], type=button_type, use_container_width=True):
                        st.session_state["admin_page"] = item["pagina"]
                        st.rerun()

def exibir_dashboard():
    """Exibe o conteúdo do dashboard"""
    st.title("📊 Dashboard")
    st.markdown("### Bem-vindo à área administrativa!")
    st.markdown("Utilize o menu lateral para navegar pelo sistema.")
    
    funcionarios_df, req_df = carregar_estatisticas()
    
    if funcionarios_df is not None and req_df is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Funcionários por Setor")
            if not funcionarios_df.empty:
                st.bar_chart(funcionarios_df.set_index('setor'))
            st.dataframe(funcionarios_df, use_container_width=True)
        
        with col2:
            st.subheader("Requisições Recentes")
            if not req_df.empty:
                req_df = req_df.sort_values('data')
                st.line_chart(req_df.set_index('data'))
            st.dataframe(req_df, use_container_width=True)
    else:
        st.info("Nenhum dado disponível para exibição.")

def exibir_conteudo():
    """Exibe o conteúdo da página selecionada"""
    pagina_atual = st.session_state["admin_page"]
    
    # Utilizamos o if/elif mutuamente exclusivo para garantir que apenas uma página é exibida
    if pagina_atual == DASHBOARD:
        exibir_dashboard()
    
    elif pagina_atual == LISTAGEM_CRACHAS:
        # Verificar permissão
        if not verificar_permissao(1):
            st.warning("Você não tem permissão para acessar esta página.")
            return
        listagem.app()
    
    elif pagina_atual == RELATORIO_REQUISICOES:
        # Verificar permissão
        if not verificar_permissao(1):
            st.warning("Você não tem permissão para acessar esta página.")
            return
        relatorio_requisicoes.app()
    
    elif pagina_atual == CADASTRO_FUNCIONARIO:
        # Verificar permissão
        if not verificar_permissao(1):
            st.warning("Você não tem permissão para acessar esta página.")
            return
        cadastro_fun.app()
    
    elif pagina_atual == CADASTRO_USUARIO:
        # Verificar permissão
        if not verificar_permissao(2):
            st.warning("Você não tem permissão para acessar esta página.")
            return
        cadastro.app()

def exibir_login():
    """Exibe o formulário de login"""
    st.markdown('<h2>🔐 Login Administrativo</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("login_form"):
            # Use chaves diferentes para o formulário vs. session_state
            usuario = st.text_input("Usuário", key="input_usuario")
            senha = st.text_input("Senha", type="password", key="input_senha")
            
            cols = st.columns([1, 1, 1])
            with cols[1]:
                submit = st.form_submit_button("🔑 Entrar", use_container_width=True)
            
            if submit:
                with st.spinner("Verificando credenciais..."):
                    if autenticar_admin(usuario, senha):
                        # Armazenar o nome de usuário e nível em novas chaves
                        st.session_state["nome_usuario_logado"] = usuario
                        st.session_state["admin_nivel"] = 2 if usuario == "admin" else 1  # Exemplo: admin tem nível 2
                        st.session_state["admin_authenticated"] = True
                        st.session_state["last_activity"] = time.time()
                        st.success("✅ Login efetuado com sucesso!")
                        time.sleep(1)  # Breve pausa para mostrar a mensagem
                        st.rerun()
                    else:
                        st.error("🚫 Usuário ou senha incorretos!")
    
    with col2:
        st.markdown("### Informações")
        st.info("""
        Este é o painel de administração do sistema.
        
        Se você não possui credenciais de acesso, entre em contato com o administrador.
        """)
        
        if st.button("🔙 Voltar ao Sistema", use_container_width=True):
            st.session_state["page"] = "login"
            st.rerun()

def app():
    """Função principal do aplicativo administrativo"""
    # Inicializações
    inicializar_estado()
    configurar_tema()
    inicializar_indices()
    
    # Solução: usar st.empty() para criar um espaço que pode ser limpo e substituído
    # Isso garante que apenas uma interface seja mostrada por vez
    main_container = st.empty()
    
    if not st.session_state["admin_authenticated"]:
        with main_container.container():
            exibir_login()
    else:
        # Verifica timeout de sessão
        if verificar_timeout():
            with main_container.container():
                exibir_login()
            return
                
        # Exibe o menu lateral
        criar_menu_sidebar()
        
        # Exibe o conteúdo da página atual
        with main_container.container():
            try:
                exibir_conteudo()
            except Exception as e:
                st.error(f"Erro ao carregar a página: {str(e)}")
                if st.button("🔄 Tentar Novamente"):
                    st.rerun()

# Executa o aplicativo diretamente se chamado como script principal
if __name__ == "__main__":
    app()