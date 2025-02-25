import sqlite3
from datetime import datetime

def conectar_banco():
    return sqlite3.connect("sistema.db")

def buscar_usuario_por_codigo(codigo):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM FUNCIONARIOS WHERE codigo = ?", (codigo,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else None

def verificar_requisicao(codigo_funcionario, codigo_requisicao):
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

def registrar_requisicao(codigo_funcionario, codigo_requisicao, data_hora_atual):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO REQUISICOES (codigo_funcionario, codigo_requisicao, data)
        VALUES (?, ?, ?)
    """, (codigo_funcionario, codigo_requisicao, data_hora_atual))
    conn.commit()
    conn.close()

def buscar_administrador(usuario):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT usuario, senha FROM ADMINISTRADORES WHERE usuario = ?", (usuario,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado  # retorna (usuario, senha) ou None

# 🔥 Função que estava faltando, corrigindo o erro atual.
def listar_requisicoes():
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT codigo_funcionario, codigo_requisicao, data FROM REQUISICOES ORDER BY data DESC")
    requisicoes = cursor.fetchall()
    conn.close()
    return requisicoes
