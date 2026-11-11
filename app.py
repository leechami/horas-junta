import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# 1. CONFIGURACIÓN DE LA BASE DE DATOS INSTITUCIONAL (CON TABLA DE USUARIOS)
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
            area TEXT
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM usuarios_personal")
    if cursor.fetchone() == 0:
        cursor.execute("""
            INSERT INTO usuarios_personal (usuario, contrasena, nombre_completo, cargo, area)
            VALUES ('operario.ancon', 'Ancon123', 'Juan Pérez', 'Operador de Campo', 'Cuadrilla Compartida (16 op.)')
        """)
    conn.commit()
    return conn

st.set_page_config(page_title="Portal de Horas - Junta Comunal", layout="wide")
st.title("🏛️ Sistema de Control de Horas Extras y Compensatorios")
st.markdown("### Junta Comunal de Ancón — Portal Seguro de Cuentas")

# INICIALIZAR VARIABLES DE SESIÓN PARA SEGURIDAD
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "user_fullname" not in st.session_state:
    st.session_state["user_fullname"] = ""
if "user_role" not in st.session_state:
    st.session_state["user_role"] = ""

conn = conectar_db()
cursor = conn.cursor()

# -------------------------------------------------------------------------
# PANTALLA GENERAL: INICIO DE SESIÓN UNIFICADO (LOGIN)
# -------------------------------------------------------------------------
if not st.session_state["logged_in"]:
    st.subheader("🔐 Iniciar Sesión en el Portal")
    col_l1, col_l2 = st.columns(2)
    
    with col_l1:
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
                    st.rerun()
                else:
                    cursor.execute("SELECT contrasena, nombre_completo FROM usuarios_personal WHERE usuario = ?", (input_usuario,))
                    datos_user = cursor.fetchone()
                    if datos_user and datos_user[0] == input_clave:
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = input_usuario
                        st.session_state["user_fullname"] = datos_user[1]
                        st.session_state["user_role"] = "PERSONAL"
                        st.rerun()
                    else:
                        st.error("❌ Credenciales incorrectas o usuario no registrado.")

# -------------------------------------------------------------------------
# SI YA INICIÓ SESIÓN: DESPLEGAR LOS MÓDULOS SEGÚN EL ROL
# -------------------------------------------------------------------------
else:
    # BOTÓN PARA CERRAR SESIÓN SIEMPRE VISIBLE EN LA BARRA LATERAL
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.session_state["user_fullname"] = ""
        st.session_state["user_role"] = ""
        st.rerun()

    # ---------------------------------------------------------------------
    # PERFIL DEL ADMINISTRADOR (JEFE PRINCIPAL)
    # ---------------------------------------------------------------------
    if st.session_state["user_role"] == "ADMIN":
        st.sidebar.markdown("### 👑 Menú de Dirección")
        menu_admin = st.sidebar.selectbox("Módulos de Gestión", [
            "👤 Registrar Nuevos Colaboradores",
            "📥 Bandeja de Solicitudes Pendientes",
            "📊 Bolsa Acumulativa General",
            "📚 Historial de Auditoría"
        ])
        
        if menu_admin == "👤 Registrar Nuevos Colaboradores":
            st.header("👤 Crear Cuenta de Acceso para el Personal")
            st.info("Utilice este formulario para registrar un operario y generarle su usuario y clave institucional.")
            with st.form("form_crear_user", clear_on_submit=True):
                col_u1, col_u2 = st.columns(2)
                with col_u1:
                    new_nombre = st.text_input("Nombre Completo del Servidor Público:")
                    new_user = st.text_input("Crear Nombre de Usuario (ej: jose.perez):")
                    new_clave = st.text_input("Asignar Contraseña Inicial:", type="password")
                with col_u2:
                    new_cargo = st.text_input("Cargo / Posición:")
                    new_area = st.selectbox("Área / Sección asignada:", ["Cuadrilla Compartida (16 op.)", "Atención Ciudadana", "Administración", "Ornato", "Relaciones Públicas"])
                boton_crear_cuenta = st.form_submit_button("Sellar Registro y Crear Cuenta")
                if boton_crear_cuenta:
                    if new_nombre == "" or new_user == "" or new_clave == "":
                        st.error("❌ Por favor, rellene todos los campos del registro.")
                    else:
                        try:
                            cursor.execute("""
                                INSERT INTO usuarios_personal (usuario, contrasena, nombre_completo, cargo, area)
                                VALUES (?, ?, ?, ?, ?)
                            """, (new_user, new_clave, new_nombre, new_cargo, new_area))
                            conn.commit()
                            st.success(f"🎉 Cuenta creada con éxito para {new_nombre}. Ya puede ingresar con el usuario '{new_user}' y la clave asignada.")
                        except:
                            st.error("❌ El nombre de usuario ya existe. Elija otro diferente.")

        elif menu_admin == "📥 Bandeja de Solicitudes Pendientes":
            st.header("📥 Solicitudes Pendientes por Validar")
            pendientes = pd.read_sql_query("SELECT * FROM registro_horas WHERE estado = 'Pendiente'", conn)
            if not pendientes.empty:
                for index, fila in pendientes.iterrows():
                    tipo = fila['tipo_movimiento']
                    color_tipo = f"🟢 SOLICITUD DE HORAS EXTRAS (+) — Laboró: {fila['dia']}" if tipo == 'INGRESO' else f"🔴 SOLICITUD DE DÍA LIBRE (-) — Solicita libre: {fila['dia']}"
                    with st.expander(f"{color_tipo} | Empleado: {fila['nombre']} — Fecha: {fila['fecha']}"):
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.markdown(f"**Cargo:** {fila['cargo']} | **Área:** {fila['area']}")
                            if tipo == 'INGRESO':
                                st.markdown(f"**Horas a sumar:** {fila['total_horas']} hrs")
                                st.markdown(f"**Horario:** {fila['hora_inicio']} a {fila['hora_fin']}")
                            else:
                                st.markdown(f"**Horas a descontar:** {abs(fila['total_horas'])} hrs")
                        with col_b:
                            st.markdown(f"**Detalle / Motivo:** {fila['motivo']}")
                        with col_c:
                            if tipo == 'INGRESO' and fila['evidencia'] is not None:
                                st.image(fila['evidencia'], caption="📷 Evidencia del Trabajo", width=300)
                            else:
                                st.caption("No requiere o no contiene archivo de foto.")
                        col_btn1, col_btn2, _ = st.columns(3)
                        with col_btn1:
                            if st.button(f"🟢 Autorizar##{fila['id']}", key=f"ap_{fila['id']}"):
                                cursor.execute("UPDATE registro_horas SET estado = 'Aprobado' WHERE id = ?", (fila['id'],))
                                conn.commit()
                                st.rerun()
                        with col_btn2:
                            if st.button(f"🔴 Denegar##{fila['id']}", key=f"re_{fila['id']}"):
                                cursor.execute("UPDATE registro_horas SET estado = 'Rechazado' WHERE id = ?", (fila['id'],))
                                conn.commit()
                                st.rerun()
            else:
                st.success("✅ Bandeja limpia. No hay solicitudes pendientes por procesar.")

        elif menu_admin == "📊 Bolsa Acumulativa General":
            st.header("📊 Bolsa Acumulativa de Horas Reales Disponibles")
            resumen = pd.read_sql_query("""
                SELECT nombre as 'Empleado', SUM(total_horas) as 'Saldo Neto de Horas Disponibles' 
                FROM registro_horas WHERE estado = 'Aprobado' GROUP BY nombre
            """, conn)
            if not resumen.empty:
                st.dataframe(resumen, use_container_width=True, hide_index=True)
            else:
                st.warning("No hay horas aprobadas consolidadas en este periodo.")

        elif menu_admin == "📚 Historial de Auditoría":
            st.header("📚 Historial de Transacciones de la Planilla")
