import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# 1. CONFIGURACIÓN DE LA BASE DE DATOS INSTITUCIONAL (MARGEN DE ERROR CERO)
def conectar_db():
    conn = sqlite3.connect("control_horas_comunal.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registro_horas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT, fecha TEXT, dia TEXT, area TEXT, cargo TEXT,
            hora_inicio TEXT, hora_fin TEXT, motivo TEXT,
            total_horas REAL, estado TEXT, evidencia BLOB, tipo_movimiento TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios_personal (
            usuario TEXT PRIMARY KEY,
            contrasena TEXT,
            nombre_completo TEXT,
            cargo TEXT,
            area TEXT,
            requiere_cambio INTEGER DEFAULT 1
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM usuarios_personal")
    if cursor.fetchone() == 0:
        cursor.execute("""
            INSERT INTO usuarios_personal (usuario, contrasena, nombre_completo, cargo, area, requiere_cambio)
            VALUES ('operario.ancon', 'Ancon123', 'Juan Pérez', 'Operador de Campo', 'Cuadrilla Compartida (16 op.)', 1)
        """)
    conn.commit()
    return conn

st.set_page_config(page_title="Portal de Horas - Junta Comunal", layout="wide")
st.title("🏛️ Sistema de Control de Horas Extras y Compensatorios")
st.markdown("### Junta Comunal de Ancón — Portal Seguro de Cuentas")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "user_fullname" not in st.session_state:
    st.session_state["user_fullname"] = ""
if "user_role" not in st.session_state:
    st.session_state["user_role"] = ""
if "requiere_cambio" not in st.session_state:
    st.session_state["requiere_cambio"] = 0

conn = conectar_db()
cursor = conn.cursor()

# -------------------------------------------------------------------------
# PANTALLA GENERAL: INICIO DE SESIÓN UNIFICADO (LOGIN)
# -------------------------------------------------------------------------
if not st.session_state["logged_in"]:
    st.subheader("🔐 Iniciar Sesión en el Portal")
    with st.form("login_general"):
        input_usuario = st.text_input("Usuario asignado:")
        input_clave = st.text_input("Contraseña:", type="password")
        boton_ingresar = st.form_submit_button("Ingresar al Sistema")
        
        if boton_ingresar:
            if input_usuario == "admin_ancon" and input_clave == "Ancon2026*":
                st.session_state["logged_in"] = True
                st.session_state["username"] = "admin_ancon"
                st.session_state["user_fullname"] = "Director Administrador"
                st.session_state["user_role"] = "ADMIN"
                st.session_state["requiere_cambio"] = 0
                st.rerun()
            else:
                cursor.execute("SELECT contrasena, nombre_completo, requiere_cambio FROM usuarios_personal WHERE usuario = ?", (input_usuario,))
                datos_user = cursor.fetchone()
                if datos_user and datos_user == input_clave:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = input_usuario
                    st.session_state["user_fullname"] = datos_user
                    st.session_state["user_role"] = "PERSONAL"
                    st.session_state["requiere_cambio"] = datos_user
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas o usuario no registrado.")

# -------------------------------------------------------------------------
# CAMBIO DE CONTRASEÑA OBLIGATORIO PARA TRABAJADORES NUEVOS
# -------------------------------------------------------------------------
elif st.session_state["logged_in"] and st.session_state["requiere_cambio"] == 1:
    st.header("🔒 Cambio de Contraseña Obligatorio")
    st.warning("Detectamos que estás ingresando con una contraseña temporal de la oficina. Por seguridad, debes crear una contraseña nueva y secreta.")
    with st.form("form_cambio_obligatorio"):
        nueva_clave_1 = st.text_input("Digita tu nueva contraseña secreta:", type="password")
        nueva_clave_2 = st.text_input("Confirma tu nueva contraseña secreta:", type="password")
        boton_salvar_clave = st.form_submit_button("Guardar mi Contraseña Privada")
        
        if boton_salvar_clave:
            if nueva_clave_1 == "" or nueva_clave_2 == "":
                st.error("❌ Por favor, rellene ambos campos.")
            elif nueva_clave_1 != nueva_clave_2:
                st.error("❌ Las contraseñas no coinciden.")
            elif nueva_clave_1 in ["Ancon123", "Ancon2026", "Temporal123"]:
                st.error("❌ No puede usar una clave genérica de la oficina. Invente una propia.")
            else:
                cursor.execute("UPDATE usuarios_personal SET contrasena = ?, requiere_cambio = 0 WHERE usuario = ?", (nueva_clave_1, st.session_state["username"]))
                conn.commit()
                st.session_state["requiere_cambio"] = 0
                st.success("🎉 ¡Contraseña guardada con éxito! Tu portal se ha desbloqueado.")
                st.rerun()

# -------------------------------------------------------------------------
# PORTAL OPERATIVO PRINCIPAL (YA AUTENTICADOS CON ÉXITO)
# -------------------------------------------------------------------------
else:
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.session_state["user_fullname"] = ""
        st.session_state["user_role"] = ""
        st.rerun()

    # ---------------------------------------------------------------------
    # PERFIL ADMINISTRADOR (JEFE DE LA JUNTA COMUNAL)
    # ---------------------------------------------------------------------
    if st.session_state["user_role"] == "ADMIN":
        st.sidebar.markdown("### 👑 Menú de Dirección")
        menu_admin = st.sidebar.selectbox("Módulos de Gestión", [
            "👤 Registrar Nuevos Colaboradores",
            "🔑 Resetear Contraseña de Operario",
            "📥 Bandeja de Solicitudes Pendientes",
            "📊 Bolsa Acumulativa General",
            "📚 Historial de Auditoría"
        ])
        
        if menu_admin == "👤 Registrar Nuevos Colaboradores":
            st.header("👤 Crear Cuenta de Acceso para el Personal")
            with st.form("form_crear_user", clear_on_submit=True):
                col_u1, col_u2 = st.columns(2)
                with col_u1:
                    new_nombre = st.text_input("Nombre Completo del Servidor Público:")
                    new_user = st.text_input("Crear Nombre de Usuario (ej: jose.perez):")
                    new_clave = st.text_input("Asignar Contraseña Temporal:", type="password", value="Ancon123")
                with col_u2:
                    new_cargo = st.text_input("Cargo / Posición:")
                    new_area = st.selectbox("Área / Sección:", ["Cuadrilla Compartida (16 op.)", "Atención Ciudadana", "Administración", "Ornato", "Relaciones Públicas"])
                boton_crear_cuenta = st.form_submit_button("Sellar Registro y Crear Cuenta")
                if boton_crear_cuenta:
                    if new_nombre == "" or new_user == "" or new_clave == "":
                        st.error("❌ Por favor, rellene todos los campos.")
                    else:
                        try:
                            cursor.execute("INSERT INTO usuarios_personal (usuario, contrasena, nombre_completo, cargo, area, requiere_cambio) VALUES (?, ?, ?, ?, ?, 1)", (new_user, new_clave, new_nombre, new_cargo, new_area))
                            conn.commit()
                            st.success(f"🎉 Cuenta creada con éxito para {new_nombre}.")
                        except:
                            st.error("❌ El usuario ya existe.")

        elif menu_admin == "🔑 Resetear Contraseña de Operario":
            st.header("🔑 Blanquear / Restablecer Contraseña por Olvido")
            with st.form("form_reseteo_admin"):
                cursor.execute("SELECT usuario, nombre_completo FROM usuarios_personal")
                lista_usuarios = cursor.fetchall()
                opciones_usuarios = {f"{u} ({u})": u for u in lista_usuarios}
                if opciones_usuarios:
                    seleccionado = st.selectbox("Seleccione el Trabajador:", list(opciones_usuarios.keys()))
                    user_a_cambiar = opciones_usuarios[seleccionado]
                    clave_reseteo = st.text_input("Nueva contraseña temporal:", type="password", value="Temporal123")
                    boton_resetear = st.form_submit_button("Forzar Restablecimiento de Clave")
                    if boton_resetear:
                        cursor.execute("UPDATE usuarios_personal SET contrasena = ?, requiere_cambio = 1 WHERE usuario = ?", (clave_reseteo, user_a_cambiar))
                        conn.commit()
                        st.success(f"✔️ Contraseña restablecida con éxito para {seleccionado}.")
                else:
                    st.warning("No hay operarios registrados.")

        elif menu_admin == "📥 Bandeja de Solicitudes Pendientes":
            st.header("📥 Solicitudes Pendientes por Validar")
            pendientes = pd.read_sql_query("SELECT * FROM registro_horas WHERE estado = 'Pendiente'", conn)
            if not pendientes.empty:
                for index, fila in pendientes.iterrows():
                    tipo = fila['tipo_movimiento']
                    label_movimiento = "🟢 HORAS EXTRAS (+)" if tipo == 'INGRESO' else "🔴 DÍA LIBRE (-)"
                    
                    st.markdown("---")
                    st.markdown(f"### {label_movimiento} | Empleado: **{fila['nombre']}** — Fecha: {fila['fecha']}")
