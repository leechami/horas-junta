import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

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
    conn.commit()
    return conn

st.set_page_config(page_title="Portal de Horas - Junta Comunal", layout="wide")
st.title("🏛️ Sistema de Control de Horas Extras y Compensatorios")
st.markdown("### Junta Comunal de Ancón — Portal de Autoservicio")

menu = st.sidebar.selectbox("Seleccione el Módulo", [
    "📊 Consulta de Saldos Públicos",
    "✍️ Reportar Horas Extras (Suma)", 
    "🔻 Solicitar Día Compensatorio (Resta)",
    "🔐 Panel de Control (Administrador)"
])

conn = conectar_db()
cursor = conn.cursor()

if menu == "📊 Consulta de Saldos Públicos":
    st.header("📊 Saldo de Horas Compensatorias Disponibles por Personal")
    resumen = pd.read_sql_query('''
        SELECT nombre as 'Nombre del Servidor Público', 
               SUM(total_horas) as 'Horas Disponibles a Favor (Saldo Neto)' 
        FROM registro_horas 
        WHERE estado = 'Aprobado' 
        GROUP BY nombre
    ''', conn)
    if not resumen.empty:
        busqueda = st.text_input("🔍 Buscar mi nombre en la planilla:")
        if busqueda:
            resumen = resumen[resumen['Nombre del Servidor Público'].str.contains(busqueda, case=False)]
        st.dataframe(resumen, use_container_width=True, hide_index=True)
    else:
        st.warning("Aún no se registran saldos de horas consolidados en el sistema.")

elif menu == "✍️ Reportar Horas Extras (Suma)":
    st.header("✍️ Formulario para Reportar Horas Extras")
    with st.form("formulario_horas", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            nombre = st.text_input("Nombre Completo del Servidor Público:")
            cargo = st.text_input("Cargo / Posición:")
        with col2:
            fecha_input = st.date_input("Fecha de la Jornada:", value=datetime.today())
            dia_semana = st.selectbox("Día de la Semana en que laboró:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])
        with col3:
            area = st.selectbox("Área / Sección asignada:", ["Cuadrilla Compartida (16 op.)", "Atención Ciudadana", "Administración", "Ornato", "Relaciones Públicas"])
            motivo = st.text_area("Motivo o Evento de la jornada extraordinaria (ej. Feria del IMA, Ancón Recicla):")
        st.markdown("#### Horario Ejecutado")
        col4, col5 = st.columns(2)
        with col4:
            hora_inicio = st.time_input("Hora de Inicio:")
        with col5:
            hora_fin = st.time_input("Hora de Finalización:")
        foto_adjunta = st.file_uploader("Adjuntar foto de la nota firmada o comprobante del trabajo:", type=["png", "jpg", "jpeg"])
        enviar = st.form_submit_button("Enviar Solicitud de Horas Extras")
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
                foto_bytes = foto_adjunta.read() if foto_adjunta is not None else None
                cursor.execute('''
                    INSERT INTO registro_horas (nombre, fecha, dia, area, cargo, hora_inicio, hora_fin, motivo, total_horas, estado, evidencia, tipo_movimiento)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pendiente', ?, 'INGRESO')
                ''', (nombre, fecha_str, dia_semana, area, cargo, str(hora_inicio), str(hora_fin), motivo, total_horas_calculadas, foto_bytes))
                conn.commit()
                st.success(f"✔️ Solicitud enviada. Total: {total_horas_calculadas} hrs.")

elif menu == "🔻 Solicitar Día Compensatorio (Resta)":
    st.header("🔻 Formulario de Solicitud de Tiempo Libre / Día Compensatorio")
    with st.form("formulario_libres", clear_on_submit=True):
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            nombre_libre = st.text_input("Nombre Completo del Servidor Público:")
            cargo_libre = st.text_input("Cargo / Sección:")
        with col_c2:
            fecha_libre = st.date_input("Fecha exacta solicitada para el día libre:", value=datetime.today())
            dia_libre_semana = st.selectbox("Día de la semana solicitado a ausentarse:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])
        with col_c3:
            horas_solicitadas = st.number_input("Cantidad de horas a descontar:", min_value=0.5, max_value=40.0, value=8.0, step=0.5)
        motivo_libre = st.text_area("Justificación del tiempo libre:")
        enviar_libre = st.form_submit_button("Enviar Solicitud de Tiempo Libre al Jefe")
        if enviar_libre:
            if nombre_libre == "" or motivo_libre == "":
                st.error("❌ Por favor, rellene los campos obligatorios.")
            else:
                fecha_libre_str = fecha_libre.strftime("%d/%m/%Y")
                horas_negativas = -float(horas_solicitadas)
                cursor.execute('''
                    INSERT INTO registro_horas (nombre, fecha, dia, area, cargo, hora_inicio, hora_fin, motivo, total_horas, estado, evidencia, tipo_movimiento)
                    VALUES (?, ?, ?, 'Uso de Tiempo', ?, 'N/A', 'N/A', ?, ?, 'Pendiente', None, 'REDUCCION')
                ''', (nombre_libre, fecha_libre_str, dia_libre_semana, cargo_libre, motivo_libre, horas_negativas))
                conn.commit()
                st.success(f"🔻 Solicitud de descanso enviada por {horas_solicitadas} hrs.")

elif menu == "🔐 Panel de Control (Administrador)":
    st.header("🔐 Acceso Restringido - Panel del Jefe / Encargado")
    with st.form("login_admin"):
        usuario = st.text_input("Usuario Administrador:")
        contrasena = st.text_input("Contraseña de Acceso:", type="password")
        boton_login = st.form_submit_button("Ingresar al Panel")
    if boton_login:
        if usuario == "admin_ancon" and contrasena == "Ancon2026*":
            st.session_state["autenticado"] = True
        else:
            st.error("❌ Credenciales incorrectas.")
    if st.session_state.get("autenticado", False):
        st.subheader("📥 Solicitudes Pendientes")
        pendientes = pd.read_sql_query("SELECT * FROM registro_horas WHERE estado = 'Pendiente'", conn)
        if not pendientes.empty:
            for index, fila in pendientes.iterrows():
                tipo = fila['tipo_movimiento']
                color_tipo = f"🟢 EXTRAS ({fila['dia']})" if tipo == 'INGRESO' else f"🔴 LIBRE ({fila['dia']})"
                with st.expander(f"{color_tipo} | {fila['nombre']} — {fila['fecha']}"):
                    st.write(f"**Motivo:** {fila['motivo']} | **Horas:** {abs(fila['total_horas'])}")
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        if st.button(f"🟢 Autorizar##{fila['id']}", key=f"ap_{fila['id']}"):
                            cursor.execute("UPDATE registro_horas SET estado = 'Aprobado' WHERE id = ?", (fila['id'],))
                            conn.commit()
                            st.rerun()
                    with col_b2:
                        if st.button(f"🔴 Denegar##{fila['id']}", key=f"re_{fila['id']}"):
                            cursor.execute("UPDATE registro_horas SET estado = 'Rechazado' WHERE id = ?", (fila['id'],))
                            conn.commit()
                            st.rerun()
        else:
            st.success("✅ No hay solicitudes pendientes.")
        st.subheader("📚 Historial de Transacciones Aprobadas")
        historial = pd.read_sql_query("SELECT id, nombre, fecha, dia, area, total_horas, estado, tipo_movimiento, motivo FROM registro_horas", conn)
        st.dataframe(historial, use_container_width=True)

conn.close()
