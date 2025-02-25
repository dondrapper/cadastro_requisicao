# auth.py
import bcrypt
from database import buscar_administrador

def hash_senha(senha):
    """Retorna a senha encriptada com bcrypt"""
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

def verificar_senha(senha_digitada, senha_armazenada):
    """Verifica se a senha digitada corresponde ao hash armazenado"""
    return bcrypt.checkpw(senha_digitada.encode(), senha_armazenada.encode())

def autenticar_admin(usuario, senha_digitada):
    admin_data = buscar_administrador(usuario)
    if admin_data:
        usuario_db, senha_hash_db = admin_data
        return bcrypt.checkpw(senha_digitada.encode(), senha_hash_db.encode())
    return False
