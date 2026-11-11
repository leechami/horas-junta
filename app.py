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
    if cursor.fetchone()[0] == 0:
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
# SI YA INICIÓ SESIÓN: DESPLEGAR LOS MÓDULOS CORRESPONDIENTES
# -------------------------------------------------------------------------
else:
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.session_state["user_fullname"] = ""
        st.session_state["user_role"] = ""
        st.rerun()

    # PERFIL DEL COLABORADOR (TRABAJADOR LOGUEADO)
    if st.session_state["user_role"] == "PERSONAL":
        st.sidebar.markdown(f"**Empleado:**\n{st.session_state['user_fullname']}")
        menu_personal = st.sidebar.selectbox("Acciones Disponibles", [
            "📊 Mi Panel y Estatus de Solicitudes",
            "✍️ Reportar Horas Extras (+)",
            "🔻 Solicitar Día Compensatorio (-)"
        ])
        
        cursor.execute("SELECT nombre_completo, cargo, area FROM usuarios_personal WHERE usuario = ?", (st.session_state["username"],))
        info_emp = cursor.fetchone()
        emp_nombre, emp_cargo, emp_area = info_emp[0], info_emp[1], info_emp[2]

        if menu_personal == "📊 Mi Panel y Estatus de Solicitudes":
            st.header(f"👋 ¡Bienvenido, {emp_nombre}!")
            cursor.execute("SELECT SUM(total_horas) FROM registro_horas WHERE nombre = ? AND estado = 'Aprobado'", (emp_nombre,))
            saldo_res = cursor.fetchone()[0]
            saldo_neto = saldo_res if saldo_res is not None else 0.0
            st.metric(label="⌛ Tu Saldo de Horas Disponibles a Favor:", value=f"{saldo_neto} hrs")
            
            st.subheader("📚 Estado de mis Solicitudes Enviadas")
            df_mis_solicitudes = pd.read_sql_query("""
                SELECT fecha as 'Fecha', dia as 'Día', total_horas as 'Horas', 
                       estado as 'Estatus del Jefe', tipo_movimiento as 'Tipo', motivo as 'Detalle/Motivo' 
                FROM registro_horas WHERE nombre = ? ORDER BY id DESC
            """, conn, params=(emp_nombre,))
            if not df_mis_solicitudes.empty:
                st.dataframe(df_mis_solicitudes, use_container_width=True, hide_index=True)
            else:
                st.caption("Aún no has enviado ninguna solicitud al sistema.")

        elif menu_personal == "✍️ Reportar Horas Extras (+)":
            st.header("✍️ Reportar Jornada Extraordinaria")
            st.caption(f"Registrando como: **{emp_nombre}** | Cargo: {emp_cargo} | Área: {emp_area}")
            with st.form("form_extras_p", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    fecha_input = st.date_input("Fecha de la Jornada:", value=datetime.today())
                    dia_semana = st.selectbox("Día de la Semana:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])
                with col2:
                    hora_inicio = st.time_input("Hora de Inicio:")
                    hora_fin = st.time_input("Hora de Finalización:")
                motivo = st.text_area("Motivo o Evento de la jornada extraordinaria (ej. Feria del IMA):")
                foto_adjunta = st.file_uploader("Adjuntar foto de la nota firmada o comprobante:", type=["png", "jpg", "jpeg"])
                enviar = st.form_submit_button("Subir Solicitud de Horas Extras")
                if enviar:
                    fmt = "%H:%M:%S"
                    t1 = datetime.strptime(str(hora_inicio), fmt)
                    t2 = datetime.strptime(str(hora_fin), fmt)
                    if t2 >= t1: diferencia = t2 - t1
                    else: diferencia = (t2 - t1) + pd.Timedelta(days=1)
                    total_horas_calculadas = round(diferencia.seconds / 3600, 2)
                    foto_bytes = foto_adjunta.read() if foto_adjunta is not None else None
                    fecha_str = fecha_input.strftime("%d/%m/%Y")
                    cursor.execute("""
                        INSERT INTO registro_horas (nombre, fecha, dia, area, cargo, hora_inicio, hora_fin, motivo, total_horas, estado, evidencia, tipo_movimiento)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pendiente', ?, 'INGRESO')
                    """, (emp_nombre, fecha_str, dia_semana, emp_area, emp_cargo, str(hora_inicio), str(hora_fin), motivo, total_horas_calculadas, foto_bytes))
                    conn.commit()
                    st.success(f"✔️ Solicitud registrada. Total calculado: {total_horas_calculadas} hrs. Esperando revisión del jefe.")

        elif menu_personal == "🔻 Solicitar Día Compensatorio (-)":
            st.header("🔻 Solicitar Uso de Tiempo Libre / Día Compensatorio")
            st.caption(f"Registrando como: **{emp_nombre}**")
            with st.form("form_libres_p", clear_on_submit=True):
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    fecha_libre = st.date_input("Fecha exacta solicitada para el día libre:", value=datetime.today())
                    dia_libre_semana = st.selectbox("Día de la semana solicitado:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])
                with col_c2:
                    horas_solicitadas = st.number_input("Cantidad de horas a descontar (ej: 8.0 para un día entero):", min_value=0.5, max_value=40.0, value=8.0, step=0.5)
                motivo_libre = st.text_area("Justificación del tiempo libre solicitado:")
                enviar_libre = st.form_submit_button("Enviar Solicitud de Tiempo Libre")
                if enviar_libre:
                    fecha_libre_str = fecha_libre.strftime("%d/%m/%Y")
                    horas_negativas = -float(horas_solicitadas)
                    cursor.execute("""
                        INSERT INTO registro_horas (nombre, fecha, dia, area, cargo, hora_inicio, hora_fin, motivo, total_horas, estado, evidencia, tipo_movimiento)
                        VALUES (?, ?, ?, 'Uso de Tiempo', ?, 'N/A', 'N/A', ?, ?, 'Pendiente', None, 'REDUCCION')
                    """, (emp_nombre, fecha_libre_str, dia_libre_semana, emp_cargo, motivo_libre, horas_negativas))
                    conn.commit()
                    st.success(f"🔻 Solicitud enviada. Esperando aprobación para descontar {horas_solicitadas} hrs el día {dia_libre_semana}.")

    # PORTAL DEL ADMINISTRADOR (JEFE / ENCARGADO LOGUEADO)
