def autenticar_admin(usuario, senha):
    try:
        conn = conectar_banco()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ADMINISTRADORES WHERE usuario = ? AND senha = ?", (usuario, senha))
        admin_data = cursor.fetchone()
        conn.close()
        st.write("Resultado da consulta:", admin_data)  # Linha de debug
        return admin_data is not None
    except Exception as e:
        st.error("Erro ao consultar administrador: " + str(e))
        return False
