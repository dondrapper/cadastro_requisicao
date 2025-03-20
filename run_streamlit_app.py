"""
Script adaptador para iniciar a aplicação Streamlit como um executável.
"""

import os
import sys
import importlib.util
import streamlit.web.bootstrap

# Configura o ambiente
def configurar_ambiente():
    """Configura o ambiente para a aplicação."""
    # Determinar o diretório base
    if getattr(sys, 'frozen', False):
        # Executando como executável congelado
        diretorio_base = os.path.dirname(sys.executable)
    else:
        # Executando como script
        diretorio_base = os.path.dirname(os.path.abspath(__file__))
    
    # Mudar para o diretório base
    os.chdir(diretorio_base)
    
    # Criar diretório .streamlit se não existir
    diretorio_streamlit = os.path.join(diretorio_base, ".streamlit")
    if not os.path.exists(diretorio_streamlit):
        os.makedirs(diretorio_streamlit)
    
    # Criar arquivo de configuração do Streamlit se não existir
    arquivo_config = os.path.join(diretorio_streamlit, "config.toml")
    if not os.path.exists(arquivo_config):
        with open(arquivo_config, "w") as f:
            f.write("""
[server]
port = 8501
address = "0.0.0.0"
baseUrlPath = ""
enableCORS = true
enableXsrfProtection = true
maxUploadSize = 200
maxMessageSize = 200

[browser]
serverAddress = "localhost"
gatherUsageStats = false
serverPort = 8501

[theme]
primaryColor = "#007bff"
backgroundColor = "#f5f7fa"
secondaryBackgroundColor = "#e9ecef"
textColor = "#212529"
font = "sans serif"
""")
    
    # Verificar se o arquivo de estilo existe
    arquivo_estilo = os.path.join(diretorio_base, "style.css")
    if not os.path.exists(arquivo_estilo):
        print(f"Aviso: Arquivo de estilo não encontrado em {arquivo_estilo}")
    
    # Verificar se o banco de dados existe
    arquivo_db = os.path.join(diretorio_base, "sistema.db")
    if not os.path.exists(arquivo_db):
        print(f"Aviso: Banco de dados não encontrado em {arquivo_db}")
    
    return diretorio_base

def executar_aplicacao():
    """Executa a aplicação Streamlit."""
    diretorio_base = configurar_ambiente()
    
    # Definir o script principal
    script_principal = os.path.join(diretorio_base, "main.py")
    if not os.path.exists(script_principal):
        script_principal = [arquivo for arquivo in os.listdir(diretorio_base) 
                           if arquivo.endswith('.py') and 'main' in arquivo.lower()]
        if script_principal:
            script_principal = os.path.join(diretorio_base, script_principal[0])
        else:
            print("Erro: Não foi possível encontrar o script principal.")
            sys.exit(1)
    
    # Configurar argumentos do Streamlit
    sys.argv = ["streamlit", "run", script_principal, "--server.address=0.0.0.0", "--server.port=8501"]
    
    # Iniciar a aplicação Streamlit
    streamlit.web.bootstrap.run(script_principal, "", args=[], flag_options={})

if __name__ == "__main__":
    try:
        executar_aplicacao()
    except Exception as e:
        # Registrar erros em um arquivo de log
        with open("erro_aplicacao.log", "a") as f:
            import traceback
            import datetime
            f.write(f"\n{datetime.datetime.now()} - Erro: {str(e)}\n")
            f.write(traceback.format_exc())
        
        # Exibir mensagem ao usuário
        print(f"Erro ao iniciar a aplicação: {str(e)}")
        print("Verifique o arquivo erro_aplicacao.log para mais detalhes.")
        input("Pressione Enter para sair...")
        sys.exit(1)