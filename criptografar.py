import sqlite3
import bcrypt

def atualizar_senhas():
    conn = sqlite3.connect("sistema.db")
    cursor = conn.cursor()
    
    # Busca todas as senhas do banco
    cursor.execute("SELECT usuario, senha FROM ADMINISTRADORES")
    administradores = cursor.fetchall()

    for usuario, senha in administradores:
        # Verifica se a senha já está criptografada (bcrypt começa com '$2b$' ou similar)
        if not senha.startswith("$2b$"):
            senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
            cursor.execute("UPDATE ADMINISTRADORES SET senha = ? WHERE usuario = ?", (senha_hash, usuario))

    conn.commit()
    conn.close()
    print("Senhas atualizadas com sucesso!")

# Executar a atualização
atualizar_senhas()
