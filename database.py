import sqlite3

# Conectar ao banco de dados
conn = sqlite3.connect("sistema.db")
cursor = conn.cursor()

# Criar tabela de funcionários
cursor.execute("""
CREATE TABLE IF NOT EXISTS FUNCIONARIOS (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cpf TEXT UNIQUE NOT NULL,
    setor TEXT NOT NULL,
    codigo TEXT UNIQUE NOT NULL
);
""")

# Criar tabela de requisições
cursor.execute("""
CREATE TABLE IF NOT EXISTS REQUISICOES (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_funcionario TEXT NOT NULL,
    codigo_requisicao TEXT NOT NULL,
    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (codigo_funcionario) REFERENCES FUNCIONARIOS(codigo)
);
""")

conn.commit()
conn.close()

print("✅ Banco de dados e tabelas criados com sucesso!")
