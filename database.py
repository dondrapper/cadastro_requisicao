"""
Módulo centralizado para todas as operações de banco de dados.
Fornece funções para acesso e manipulação de dados no SQLite.
"""

import sqlite3
from datetime import datetime

def conectar_banco():
    """Conecta ao banco de dados SQLite.
    
    Returns:
        sqlite3.Connection: Conexão com o banco de dados.
    """
    return sqlite3.connect("sistema.db")

# --- Funções de Autenticação ---

def buscar_administrador(usuario):
    """Busca um administrador pelo nome de usuário.
    
    Args:
        usuario (str): Nome de usuário do administrador.
        
    Returns:
        tuple: Tupla contendo (usuario, senha_hash) ou None se não encontrado.
    """
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT usuario, senha FROM ADMINISTRADORES WHERE usuario = ?", (usuario,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado  # retorna (usuario, senha) ou None

def autenticar_funcionario(codigo):
    """Autentica um funcionário pelo código do crachá.
    
    Args:
        codigo (str): Código do crachá do funcionário.
        
    Returns:
        str: Nome do funcionário ou None se não encontrado.
    """
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM FUNCIONARIOS WHERE codigo = ?", (codigo,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else None

# --- Funções de Requisição ---

def requisicao_ja_registrada(codigo_funcionario, codigo_requisicao):
    """Verifica se uma requisição já foi registrada por um funcionário.
    
    Args:
        codigo_funcionario (str): Código do funcionário.
        codigo_requisicao (str): Código da requisição.
        
    Returns:
        tuple: (já_registrado, tempo_passado, data_registro)
    """
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT data FROM REQUISICOES 
        WHERE codigo_funcionario = ? AND codigo_requisicao = ?
        ORDER BY data DESC LIMIT 1
    """, (codigo_funcionario, codigo_requisicao))
    resultado = cursor.fetchone()
    conn.close()

    if resultado:
        data_registro = resultado[0]
        dt_registro = datetime.strptime(data_registro, "%Y-%m-%d %H:%M:%S")
        tempo_passado = datetime.now() - dt_registro
        return True, tempo_passado, data_registro
    return False, None, None

def salvar_requisicao(codigo_funcionario, codigo_requisicao, data_hora_atual):
    """Registra uma nova requisição no banco de dados.
    
    Args:
        codigo_funcionario (str): Código do funcionário.
        codigo_requisicao (str): Código da requisição.
        data_hora_atual (str): Data e hora atuais no formato "%Y-%m-%d %H:%M:%S".
        
    Returns:
        bool: True se a operação foi bem-sucedida.
    """
    try:
        conn = conectar_banco()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO REQUISICOES (codigo_funcionario, codigo_requisicao, data)
            VALUES (?, ?, ?)
        """, (codigo_funcionario, codigo_requisicao, data_hora_atual))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def listar_requisicoes(data_inicio=None, data_fim=None, codigo_funcionario=None):
    """Lista requisições com filtros opcionais.
    
    Args:
        data_inicio (str, optional): Data inicial para filtragem.
        data_fim (str, optional): Data final para filtragem.
        codigo_funcionario (str, optional): Código do funcionário para filtragem.
        
    Returns:
        list: Lista de tuplas com as requisições encontradas.
    """
    conn = conectar_banco()
    cursor = conn.cursor()
    
    if data_inicio and data_fim and codigo_funcionario:
        cursor.execute("""
            SELECT codigo_funcionario, codigo_requisicao, data FROM REQUISICOES
            WHERE codigo_funcionario = ? AND date(data) BETWEEN date(?) AND date(?)
            ORDER BY data DESC
        """, (codigo_funcionario, data_inicio, data_fim))
    elif data_inicio and data_fim:
        cursor.execute("""
            SELECT codigo_funcionario, codigo_requisicao, data FROM REQUISICOES
            WHERE date(data) BETWEEN date(?) AND date(?)
            ORDER BY data DESC
        """, (data_inicio, data_fim))
    else:
        cursor.execute("""
            SELECT codigo_funcionario, codigo_requisicao, data FROM REQUISICOES
            ORDER BY data DESC
        """)
    
    requisicoes = cursor.fetchall()
    conn.close()
    return requisicoes

# --- Funções de Funcionários ---

def cadastrar_funcionario(nome, cpf, setor, codigo=None):
    """Cadastra um novo funcionário no banco de dados.
    
    Args:
        nome (str): Nome do funcionário.
        cpf (str): CPF do funcionário.
        setor (str): Setor do funcionário.
        codigo (str, optional): Código do crachá, se não especificado usa o CPF.
        
    Returns:
        tuple: (sucesso, mensagem)
    """
    if codigo is None:
        codigo = cpf
        
    try:
        conn = conectar_banco()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO FUNCIONARIOS (nome, cpf, setor, codigo) VALUES (?, ?, ?, ?)",
                       (nome, cpf, setor, codigo))
        conn.commit()
        conn.close()
        return True, f"Funcionário {nome} cadastrado com sucesso!"
    except sqlite3.IntegrityError:
        return False, "CPF ou Código já cadastrados!"
    except Exception as e:
        return False, f"Erro ao cadastrar: {str(e)}"

def listar_funcionarios():
    """Lista todos os funcionários cadastrados.
    
    Returns:
        list: Lista de tuplas com os dados dos funcionários.
    """
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, cpf, setor, codigo FROM FUNCIONARIOS")
    funcionarios = cursor.fetchall()
    conn.close()
    return funcionarios

def obter_funcionario(funcionario_id):
    """Obtém os dados de um funcionário pelo ID.
    
    Args:
        funcionario_id (int): ID do funcionário.
        
    Returns:
        dict: Dicionário com os dados do funcionário ou None se não encontrado.
    """
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

def excluir_funcionario(funcionario_id):
    """Exclui um funcionário pelo ID.
    
    Args:
        funcionario_id (int): ID do funcionário.
        
    Returns:
        bool: True se a exclusão foi bem-sucedida.
    """
    try:
        conn = conectar_banco()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM FUNCIONARIOS WHERE id = ?", (funcionario_id,))
        sucesso = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return sucesso
    except Exception:
        return False

def excluir_funcionarios(ids_funcionarios):
    """Exclui múltiplos funcionários pelos IDs.
    
    Args:
        ids_funcionarios (list): Lista de IDs de funcionários.
        
    Returns:
        int: Número de funcionários excluídos.
    """
    if not ids_funcionarios:
        return 0
        
    try:
        conn = conectar_banco()
        cursor = conn.cursor()
        contador = 0
        
        for funcionario_id in ids_funcionarios:
            cursor.execute("DELETE FROM FUNCIONARIOS WHERE id = ?", (funcionario_id,))
            contador += cursor.rowcount
            
        conn.commit()
        conn.close()
        return contador
    except Exception:
        return 0

# --- Funções de Administração ---

def cadastrar_administrador(usuario, senha_hash):
    """Cadastra um novo administrador no sistema.
    
    Args:
        usuario (str): Nome de usuário.
        senha_hash (str): Hash da senha já criptografada.
        
    Returns:
        bool: True se o cadastro foi bem-sucedido.
    """
    try:
        conn = conectar_banco()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO ADMINISTRADORES (usuario, senha) VALUES (?, ?)",
                    (usuario, senha_hash))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception:
        return False