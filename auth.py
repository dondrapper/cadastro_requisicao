"""
Módulo de autenticação para o sistema de controle.
"""

from utils import verificar_senha, hash_senha
from database import buscar_administrador

def autenticar_admin(usuario, senha_digitada):
    """
    Autentica um administrador verificando suas credenciais.
    
    Args:
        usuario (str): Nome de usuário do administrador.
        senha_digitada (str): Senha fornecida para autenticação.
        
    Returns:
        bool: True se as credenciais são válidas, False caso contrário.
    """
    admin_data = buscar_administrador(usuario)
    if admin_data:
        usuario_db, senha_hash_db = admin_data
        return verificar_senha(senha_digitada, senha_hash_db)
    return False