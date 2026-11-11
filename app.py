import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io

def conectar_db():
    conn = sqlite3.connect("control_horas_comunal.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registro_horas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT, fecha TEXT, dia TEXT, area TEXT, cargo TEXT,
            hora_inicio TEXT, hora_fin TEXT, motivo TEXT,
            total_horas REAL, estado TEXT, evidencia BLOB, tipo_movimiento TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios_personal (
            usuario TEXT PRIMARY KEY,
            contrasena TEXT,
            nombre_completo TEXT,
            cargo TEXT,
            area TEXT,
            requiere_cambio INTEGER DEFAULT 1
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM usuarios_personal")
    conteo = cursor.fetchone()
    if conteo and conteo[0] == 0:
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
                if datos_user and str(datos_user[0]) == str(input_clave):
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = input_usuario
                    st.session_state["user_fullname"] = str(datos_user[1])
                    st.session_state["requiere_cambio"] = int(datos_user[2])
                    st.session_state["user_role"] = "PERSONAL"
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas o usuario no registrado.")

elif st.session_state["logged_in"] and st.session_state["requiere_cambio"] == 1:
    st.header("🔒 Cambio de Contraseña Obligatorio")
    st.warning("Detectamos que estás ingresando con una contraseña temporal. Por seguridad, debes crear una contraseña nueva y secreta.")
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

else:
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.session_state["user_fullname"] = ""
        st.session_state["user_role"] = ""
        st.rerun()

    if st.session_state["user_role"] == "ADMIN":
        st.sidebar.markdown("### 👑 Menú de Dirección")
        menu_admin = st.sidebar.selectbox("Módulos de Gestión", [
            "👤 Registrar Nuevos Colaboradores",
            "🔑 Resetear / Eliminar Operario",
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
                        except Exception:
                            st.error("❌ El usuario ya existe.")
            
            st.markdown("---")
            st.subheader("📋 Lista de Personal Registrado")
            df_usuarios = pd.read_sql_query("SELECT usuario as 'Usuario', nombre_completo as 'Nombre', cargo as 'Cargo', area as 'Área asignada' FROM usuarios_personal", conn)
            st.dataframe(df_usuarios, use_container_width=True, hide_index=True)

        elif menu_admin == "🔑 Resetear / Eliminar Operario":
            st.header("🔑 Gestión de Cuentas: Restablecer Clave o Eliminar Usuario")
            cursor.execute("SELECT usuario, nombre_completo FROM usuarios_personal")
            lista_usuarios = cursor.fetchall()
            opciones_usuarios = {f"{u[1]} (Usuario: {u[0]})": str(u[0]) for u in lista_usuarios}
            
            if opciones_usuarios:
                seleccionado = st.selectbox("Seleccione el Trabajador a Gestionar:", list(opciones_usuarios.keys()))
                user_a_cambiar = opciones_usuarios[seleccionado]
                
                st.markdown("---")
                st.markdown("#### 1. Restablecer Contraseña por Olvido")
                clave_reseteo = st.text_input("Nueva contraseña temporal:", type="password", value="Temporal123", key="input_reset_clave")
                if st.button("Forzar Restablecimiento de Clave", key="btn_reset_clave"):
                    cursor.execute("UPDATE usuarios_personal SET contrasena = ?, requiere_cambio = 1 WHERE usuario = ?", (clave_reseteo, user_a_cambiar))
                    conn.commit()
                    st.success(f"✔️ Contraseña restablecida con éxito para el usuario '{user_a_cambiar}'.")
                
                st.markdown("---")
                st.markdown("#### 2. Eliminar Cuenta por Baja Completa")
                st.warning(f"⚠️ ¡Cuidado! Si presiona el botón de abajo, se borrará de forma permanente el acceso del colaborador '{user_a_cambiar}'.")
                if st.button("🗑️ Eliminar Login de Colaborador del Sistema", key="btn_eliminar_user"):
                    cursor.execute("DELETE FROM usuarios_personal WHERE usuario = ?", (user_a_cambiar,))
                    conn.commit()
                    st.success(f"🗑️ El usuario '{user_a_cambiar}' ha sido borrado del sistema con éxito.")
                    st.rerun()
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
                    st.markdown(f"**Cargo:** {fila['cargo']} | **Área:** {fila['area']} | **Horas:** {abs(fila['total_horas'])} hrs")
                    st.markdown(f"**Motivo registrado:** {fila['motivo']}")
                    
                    if tipo == 'INGRESO' and fila['evidencia'] is not None:
                        st.image(fila['evidencia'], width=350)
                    
                    if st.button(f"🟢 Autorizar Solicitud #{fila['id']}", key=f"ap_{fila['id']}"):
                        cursor.execute("UPDATE registro_horas SET estado = 'Aprobado' WHERE id = ?", (fila['id'],))
                        conn.commit()
                        st.rerun()
                        
                    if st.button(f"🔴 Denegar Solicitud #{fila['id']}", key=f"re_{fila['id']}"):
                        cursor.execute("UPDATE registro_horas SET estado = 'Rechazado' WHERE id = ?", (fila['id'],))
                        conn.commit()
                        st.rerun()
            else:
                st.success("✅ Bandeja limpia. No hay pendientes por procesar.")

        elif menu_admin == "📊 Bolsa Acumulativa General":
            st.header("📊 Bolsa Acumulativa de Horas Reales Disponibles")
            resumen = pd.read_sql_query("SELECT nombre as 'Empleado', SUM(total_horas) as 'Saldo Neto de Horas Disponibles' FROM registro_horas WHERE estado = 'Aprobado' GROUP BY nombre", conn)
            if not resumen.empty:
                st.dataframe(resumen, use_container_width=True, hide_index=True)
            else:
                st.warning("No hay horas aprobadas consolidadas.")

        elif menu_admin == "📚 Historial de Auditoría":
            st.header("📚 Historial de Transacciones de la Planilla")
            historial = pd.read_sql_query("SELECT id, nombre, fecha, area, total_horas, estado, tipo_movimiento, motivo FROM registro_horas", conn)
            st.dataframe(historial, use_container_width=True, hide_index=True)
            if not historial.empty:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    historial.to_excel(writer, index=False, sheet_name='Bitacora_Horas_Ancon')
                processed_data = output.getvalue()
                st.download_button(label="📥 Descargar Libro Completo en Excel (.xlsx)", data=processed_data, file_name="Planilla_Horas_Ancon.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    elif st.session_state["user_role"] == "PERSONAL":
        emp_nombre = st.session_state["user_fullname"]
        st.sidebar.markdown(f"### 👨‍🔧 Panel de: \n**{emp_nombre}**")
        menu_personal = st.sidebar.selectbox("Acciones Disponibles", ["📊 Mi Panel y Estatus", "✍️ Reportar Horas Extras (+)", "🔻 Solicitar Día Compensatorio (-)"])

        if menu_personal == "📊 Mi Panel y Estatus":
            st.header(f"👋 ¡Bienvenido, {emp_nombre}!")
            cursor.execute("SELECT SUM(total_horas) FROM registro_horas WHERE nombre = ? AND estado = 'Aprobado'", (emp_nombre,))
            saldo_res = cursor.fetchone()
            saldo_neto = float(saldo_res[0]) if (saldo_res and saldo_res[0] is not None) else 0.0
            st.metric(label="⌛ Tu Saldo de Horas Disponibles a Favor:", value=f"{saldo_neto} hrs")
            
            df_mis_solicitudes = pd.read_sql_query("SELECT fecha as 'Fecha', dia as 'Día', total_horas as 'Horas', estado as 'Estatus del Jefe', motivo as 'Detalle/Motivo' FROM registro_horas WHERE nombre = ? ORDER BY id DESC", conn, params=(emp_nombre,))
            if not df_mis_solicitudes.empty:
                st.dataframe(df_mis_solicitudes, use_container_width=True, hide_index=True)
            else:
                st.caption("Aún no has enviado ninguna solicitud.")

        elif menu_personal == "✍️ Reportar Horas Extras (+)":
            st.header("✍️ Reportar Jornada Extraordinaria")
            with st.form("form_extras_p", clear_on_submit=True):
                fecha_input = st.date_input("Fecha de la Jornada:")
                dia_semana = st.selectbox("Día de la Semana:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])
                hora_inicio = st.time_input("Hora de Inicio:")
                hora_fin = st.time_input("Hora de Finalización:")
                motivo = st.text_area("Motivo de la jornada:")
                foto_adjunta = st.file_uploader("Adjuntar foto de comprobante:", type=["png", "jpg", "jpeg"])
                enviar = st.form_submit_button("Subir Solicitud")
                if enviar:
                    fmt = "%H:%M:%S"
                    t1 = datetime.strptime(str(hora_inicio), fmt)
                    t2 = datetime.strptime(str(hora_fin), fmt)
                    diferencia = (t2 - t1) if t2 >= t1 else (t2 - t1) + pd.Timedelta(days=1)
                    total_horas_calculadas = round(diferencia.seconds / 3600, 2)
                    foto_bytes = foto_adjunta.read() if foto_adjunta is not None else None
                    fecha_str = fecha_input.strftime("%d/%m/%Y")
                    cursor.execute("INSERT INTO registro_horas (nombre, fecha, dia, area, cargo, hora_inicio, hora_fin, motivo, total_horas, estado, evidencia, tipo_movimiento) VALUES (?, ?, ?, 'Operaciones', 'Operario', ?, ?, ?, ?, 'Pendiente', ?, 'INGRESO')", (emp_nombre, fecha_str, dia_semana, str(hora_inicio), str(hora_fin), motivo, total_horas_calculadas, foto_bytes))
                    conn.commit()
                    st.success("✔️ Solicitud registrada con éxito.")

        elif menu_personal == "🔻 Solicitar Día Compensatorio (-)":
            st.header("🔻 Solicitar Uso de Tiempo Libre / Día Compensatorio")
            with st.form("form_libres_p", clear_on_submit=True):
                fecha_libre = st.date_input("Fecha solicitada:")
                dia_libre_semana = st.selectbox("Día de la semana solicitado:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])
                horas_solicitadas = st.number_input("Cantidad de horas a descontar:", min_value=0.5, max_value=40.0, value=8.0, step=0.5)
                motivo_libre = st.text_area("Justificación:")
                enviar_libre = st.form_submit_button("Enviar Solicitud")
                if enviar_libre:
                    fecha_libre_str = fecha_libre.strftime("%d/%m/%Y")
                    horas_negativas = -float(horas_solicitadas)
                    cursor.execute("INSERT INTO registro_horas (nombre, fecha, dia, area, cargo, hora_inicio, hora_fin, motivo, total_horas, estado, evidencia, tipo_movimiento) VALUES (?, ?, ?, 'Uso de Tiempo', 'Operario', 'N/A', 'N/A', ?, ?, 'Pendiente', None, 'REDUCCION')", (emp_nombre, fecha_libre_str, dia_libre_semana, motivo_libre, horas_negativas))
                    conn.commit()
                    st.success("🔻 Solicitud de tiempo libre enviada con éxito.")

conn.close()
