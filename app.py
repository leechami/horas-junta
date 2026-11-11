import streamlit as st
import pandas as pd
import os
from datetime import datetime
import base64

# CONFIGURACIÓN DEL ARCHIVO EXCEL COMO BASE DE DATOS EN GITHUB
EXCEL_FILE = "base_datos_horas.xlsx"

def conectar_db_excel():
    if not os.path.exists(EXCEL_FILE):
        df = pd.DataFrame(columns=[
            "id", "nombre", "fecha", "dia", "area", "cargo", 
            "hora_inicio", "hora_fin", "motivo", "total_horas", "estado", "evidencia", "tipo_movimiento"
        ])
        df.to_excel(EXCEL_FILE, index=False)
    try:
        return pd.read_excel(EXCEL_FILE)
    except:
        return pd.DataFrame(columns=[
            "id", "nombre", "fecha", "dia", "area", "cargo", 
            "hora_inicio", "hora_fin", "motivo", "total_horas", "estado", "evidencia", "tipo_movimiento"
        ])

def guardar_db_excel(df):
    df.to_excel(EXCEL_FILE, index=False)

st.set_page_config(page_title="Portal de Horas - Junta Comunal", layout="wide")
st.title("🏛️ Sistema de Control de Horas Extras y Compensatorios")
st.markdown("### Junta Comunal de Ancón — Almacenamiento Seguro en Excel")

menu = st.sidebar.selectbox("Seleccione el Módulo", [
    "✍ * Reportar Horas Extras (Suma)", 
    "🔻 Solicitar Día Compensatorio (Resta)",
    "🔐 Panel de Control (Administrador)"
])

df_horas = conectar_db_excel()

# -------------------------------------------------------------------------
# MÓDULO 1: REPORTAR HORAS EXTRAS (Para sumar horas)
# -------------------------------------------------------------------------
if menu == "✍ * Reportar Horas Extras (Suma)":
    st.header("✍ * Formulario para Reportar Horas Extras")
    st.info("Utilice este formulario si realizó labores extraordinarias y desea que se sumen a su saldo.")
    
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
            
        st.markdown("#### 📷 Evidencia Física")
        foto_adjunta = st.file_uploader("Adjuntar foto de la nota firmada o comprobante:", type=["png", "jpg", "jpeg"])
            
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
                
                foto_base64 = ""
                if foto_adjunta is not None:
                    foto_base64 = base64.b64encode(foto_adjunta.read()).decode()
                
                nuevo_id = len(df_horas) + 1
                nueva_fila = {
                    "id": nuevo_id, "nombre": nombre, "fecha": fecha_str, "dia": dia_semana, 
                    "area": area, "cargo": cargo, "hora_inicio": str(hora_inicio), "hora_fin": str(hora_fin), 
                    "motivo": motivo, "total_horas": total_horas_calculadas, "estado": "Pendiente", 
                    "evidencia": foto_base64, "tipo_movimiento": "INGRESO"
                }
                
                df_horas = pd.concat([df_horas, pd.DataFrame([nueva_fila])], ignore_index=True)
                guardar_db_excel(df_horas)
                st.success(f"✔ * Solicitud de horas extras enviada al jefe. Total calculado: {total_horas_calculadas} hrs.")

# -------------------------------------------------------------------------
# MÓDULO 2: SOLICITAR DÍA COMPENSATORIO (Para restar horas)
# -------------------------------------------------------------------------
elif menu == "🔻 Solicitar Día Compensatorio (Resta)":
    st.header("🔻 Formulario de Solicitud de Tiempo Libre / Día Compensatorio")
    st.info("Utilice este formulario si desea solicitar libre un día o unas horas usando su saldo acumulado.")
    
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
                st.error("❌ Por favor, rellene su nombre y el motivo de la ausencia.")
            else:
                fecha_libre_str = fecha_libre.strftime("%d/%m/%Y")
                horas_negativas = -float(horas_solicitadas)
                
                nuevo_id = len(df_horas) + 1
                nueva_fila = {
                    "id": nuevo_id, "nombre": nombre_libre, "fecha": fecha_libre_str, "dia": dia_libre_semana, 
                    "area": "Uso de Tiempo", "cargo": cargo_libre, "hora_inicio": "N/A", "hora_fin": "N/A", 
                    "motivo": motivo_libre, "total_horas": horas_negativas, "estado": "Pendiente", 
                    "evidencia": "", "tipo_movimiento": "REDUCCION"
                }
                
                df_horas = pd.concat([df_horas, pd.DataFrame([nueva_fila])], ignore_index=True)
                guardar_db_excel(df_horas)
                st.success(f"🔻 Solicitud enviada. Esperando aprobación del jefe para descontar {horas_solicitadas} hrs el día {dia_libre_semana}.")

# -------------------------------------------------------------------------
# MÓDULO 3: PANEL DE CONTROL ADMINISTRATIVO (PRIVADO)
# -------------------------------------------------------------------------
elif menu == "🔐 Panel de Control (Administrador)":
    st.header("🔐 Acceso Restringido - Panel del Jefe / Encargado")
    
    with st.form("login_admin"):
        usuario = st.text_input("Usuario Administrador:")
        contrasena = st.text_input("Contraseña de Acceso:", type="password")
        boton_login = st.form_submit_button("Ingresar al Panel")
    
    if boton_login:
        if usuario == "admin_ancon" and contrasena == "Ancon2026*":
            st.session_state["autenticado"] = True
            st.success("🔓 Acceso concedido de forma correcta.")
        else:
            st.error("❌ Usuario o contraseña incorrectos.")
            st.session_state["autenticado"] = False

    if st.session_state.get("autenticado", False):
        st.markdown("---")
        
        # 1. Bolsa Acumulativa General (PRIVADA)
        st.subheader("📊 Bolsa Acumulativa de Horas Reales Disponibles (Privado)")
        
        df_aprobados = df_horas[df_horas["estado"] == "Aprobado"]
        if not df_aprobados.empty:
            resumen = df_aprobados.groupby("nombre")["total_horas"].sum().reset_index()
            resumen.columns = ["Empleado", "Saldo de Horas Disponibles"]
            st.dataframe(resumen, use_container_width=True, hide_index=True)
        else:
            st.warning("No hay horas aprobadas ni saldos consolidados en este periodo.")
            
        # 2. BANDEJA DE ENTRADA UNIFICADA DE PENDIENTES CON VISOR DE FOTOS
        st.subheader("📥 Solicitudes Pendientes por Aprobar o Rechazar")
        df_pendientes = df_horas[df_horas["estado"] == "Pendiente"]
        
        if not df_pendientes.empty:
            for index, fila in df_pendientes.iterrows():
                tipo = fila['tipo_movimiento']
                if tipo == 'INGRESO':
                    color_tipo = f"🟢 SOLICITUD DE HORAS EXTRAS (+) — Laboró el día: {fila['dia']}"
                else:
                    color_tipo = f"🔴 SOLICITUD DE DÍA LIBRE (-) — Solicita libre el día: {fila['dia']}"
                
                with st.expander(f"{color_tipo} | Empleado: {fila['nombre']} — Fecha: {fila['fecha']}"):
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.markdown(f"**Cargo:** {fila['cargo']} | **Área:** {fila['area']}")
                        if tipo == 'INGRESO':
                            st.markdown(f"**Horas a sumar:** {fila['total_horas']} hrs")
                            st.markdown(f"**Horario:** {fila['hora_inicio']} a {fila['hora_fin']}")
                        else:
