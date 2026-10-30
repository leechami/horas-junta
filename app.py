import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# 1. CONFIGURACIÓN DE LA BASE DE DATOS
def conectar_db():
    conn = sqlite3.connect("control_horas_comunal.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registro_horas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT, fecha TEXT, dia TEXT, area TEXT, cargo TEXT,
            hora_inicio TEXT, hora_fin TEXT, motivo TEXT,
            total_horas REAL, estado TEXT, evidencia BLOB
        )
    """)
    conn.commit()
    return conn

st.set_page_config(page_title="Portal de Horas - Junta Comunal", layout="wide")
st.title("🏛️ Sistema de Control de Horas Extras y Compensatorios")
st.markdown("### Junta Comunal de Ancón")

# MENÚ DE ENTRADA WEB
menu = st.sidebar.selectbox("Seleccione el Módulo", ["✍️ Reportar Horas (Personal)", "🔐 Panel de Control (Administrador)"])

# -------------------------------------------------------------------------
# LINK PÚBLICO: FORMULARIO PARA EL PERSONAL
# -------------------------------------------------------------------------
if menu == "✍️ Reportar Horas (Personal)":
    st.header("Formulario de Autoservicio para el Personal")
    st.info("Ingrese los datos de la jornada extraordinaria realizada y adjunte su foto de evidencia.")
    
    with st.form("formulario_horas", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            nombre = st.text_input("Nombre Completo del Servidor Público:")
            cargo = st.text_input("Cargo / Posición:")
        with col2:
            fecha_input = st.date_input("Fecha de la Jornada:", value=datetime.today())
            dia_semana = st.selectbox("Día de la Semana:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])
        with col3:
            area = st.selectbox("Área / Sección asignada:", ["Cuadrilla Compartida (16 op.)", "Atención Ciudadana", "Administración", "Ornato", "Relaciones Públicas"])
            motivo = st.text_area("Motivo o Evento de la jornada (ej. Feria del IMA, Ancón Recicla):")
            
        st.markdown("#### Horario Ejecutado")
        col4, col5 = st.columns(2)
        with col4:
            hora_inicio = st.time_input("Hora de Inicio:")
        with col5:
            hora_fin = st.time_input("Hora de Finalización:")
            
        st.markdown("#### 📷 Evidencia Física")
        foto_adjunta = st.file_uploader("Adjuntar foto de la nota firmada o del trabajo:", type=["png", "jpg", "jpeg"])
            
        enviar = st.form_submit_button("Subir Reporte de Horas")
        
        if enviar:
            if nombre == "" or cargo == "" or motivo == "":
                st.error("❌ Por favor, rellene todos los campos obligatorios.")
            else:
                fmt = "%H:%M:%S"
                t1 = datetime.strptime(str(hora_inicio), fmt)
                t2 = datetime.strptime(str(hora_fin), fmt)
                
                if t2 >= t1:
                    diferencia = t2 - t1
                else:
                    diferencia = (t2 - t1) + pd.Timedelta(days=1)
                    
                total_horas_calculadas = round(diferencia.seconds / 3600, 2)
                fecha_str = fecha_input.strftime("%d/%m/%Y")
                
                foto_bytes = None
                if foto_adjunta is not None:
                    foto_bytes = foto_adjunta.read()
                
                conn = conectar_db()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO registro_horas (nombre, fecha, dia, area, cargo, hora_inicio, hora_fin, motivo, total_horas, estado, evidencia)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pendiente', ?)
                """, (nombre, fecha_str, dia_semana, area, cargo, str(hora_inicio), str(hora_fin), motivo, total_horas_calculadas, foto_bytes))
                conn.commit()
                conn.close()
                
                st.success(f"✔️ Reporte enviado con éxito. Total: {total_horas_calculadas} hrs.")
                st.balloons()

# -------------------------------------------------------------------------
# ÁREA RESTRINGIDA: PANEL DE ADMIN CON LOGIN Y CONTRASEÑA
# -------------------------------------------------------------------------
elif menu == "🔐 Panel de Control (Administrador)":
    st.header("🔐 Acceso Restringido - Administración")
    
    # Formulario de Login
    with st.form("login_admin"):
        usuario = st.text_input("Usuario Administrador:")
        contrasena = st.text_input("Contraseña de Acceso:", type="password")
        boton_login = st.form_submit_button("Ingresar al Panel")
    
    # Credenciales fijas de la oficina
    if boton_login:
        if usuario == "admin_ancon" and contrasena == "Ancon2026*":
            st.session_state["autenticado"] = True
            st.success("🔓 Acceso concedido.")
        else:
            st.error("❌ Usuario o contraseña incorrectos.")
            st.session_state["autenticado"] = False

    # Si pasa la seguridad, se muestra todo el panel
    if st.session_state.get("autenticado", False):
        st.markdown("---")
        st.subheader("📥 Formularios Registrados por el Personal")
        
        conn = conectar_db()
        cursor = conn.cursor()
        
        # Tabla acumulativa general
        st.markdown("#### 📊 Bolsa Acumulativa de Horas Aprobadas")
        resumen = pd.read_sql_query("SELECT nombre as 'Empleado', cargo as 'Cargo', SUM(total_horas) as 'Total Horas' FROM registro_horas WHERE estado = 'Aprobado' GROUP BY nombre", conn)
        if not resumen.empty:
            st.dataframe(resumen, use_container_width=True)
            
        # Bandeja de aprobación
        st.markdown("#### 📥 Solicitudes Pendientes")
        pendientes = pd.read_sql_query("SELECT * FROM registro_horas WHERE estado = 'Pendiente'", conn)
        
        if not pendientes.empty:
            for index, fila in pendientes.iterrows():
                with st.expander(f"📋 Solicitud de {fila['nombre']} - {fila['fecha']} ({fila['total_horas']} hrs)"):
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.markdown(f"**Cargo:** {fila['cargo']} | **Área:** {fila['area']}")
                        st.markdown(f"**Horario:** {fila['hora_inicio']} a {fila['hora_fin']}")
                    with col_b:
                        st.markdown(f"**Motivo:** {fila['motivo']}")
                    with col_c:
                        cursor.execute("SELECT evidencia FROM registro_horas WHERE id = ?", (fila['id'],))
                        registro_foto = cursor.fetchone()
                        if registro_foto and registro_foto[0] is not None:
                            st.image(registro_foto[0], caption="Evidencia", width=180)
                        else:
                            st.caption("Sin foto.")
                    
                    col_btn1, col_btn2, _ = st.columns()
                    with col_btn1:
                        if st.button(f"🟢 Aprobar##{fila['id']}", key=f"ap_{fila['id']}"):
                            cursor.execute("UPDATE registro_horas SET estado = 'Aprobado' WHERE id = ?", (fila['id'],))
                            conn.commit()
                            st.rerun()
                    with col_btn2:
                        if st.button(f"🔴 Rechazar##{fila['id']}", key=f"re_{fila['id']}"):
                            cursor.execute("UPDATE registro_horas SET estado = 'Rechazado' WHERE id = ?", (fila['id'],))
                            conn.commit()
                            st.rerun()
        else:
            st.success("✅ No hay solicitudes pendientes.")
            
        # Historial y Excel
        st.markdown("#### 📚 Historial General")
        historial = pd.read_sql_query("SELECT id, nombre, fecha, area, total_horas, estado FROM registro_horas", conn)
        st.dataframe(historial, use_container_width=True)
        conn.close()
