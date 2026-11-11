________________st.warning(f"⚠️ ¡Cuidado! Si presiona el botón de abajo, se borrará de forma permanente el acceso del colaborador '{user_a_cambiar}'.")
________________if st.button("🗑️ Eliminar Login de Colaborador del Sistema", key="btn_eliminar_user"):
____________________cursor.execute("DELETE FROM usuarios_personal WHERE usuario = ?", (user_a_cambiar,))
____________________conn.commit()
____________________st.success(f"🗑️ El usuario '{user_a_cambiar}' ha sido borrado del sistema con éxito.")
____________________st.rerun()
____________else:
________________st.warning("No hay operarios registrados.")

________elif menu_admin == "📥 Bandeja de Solicitudes Pendientes":
____________st.header("📥 Solicitudes Pendientes por Validar")
____________pendientes = pd.read_sql_query("SELECT * FROM registro_horas WHERE estado = 'Pendiente'", conn)
____________if not pendientes.empty:
________________for index, fila in pendientes.iterrows():
____________________tipo = fila['tipo_movimiento']
____________________label_movimiento = "🟢 HORAS EXTRAS (+)" if tipo == 'INGRESO' else "🔴 DÍA LIBRE (-)"
____________________st.markdown("---")
____________________st.markdown(f"### {label_movimiento} | Empleado: **{fila['nombre']}** — Fecha: {fila['fecha']}")
____________________st.markdown(f"**Cargo:** {fila['cargo']} | **Área:** {fila['area']} | **Horas:** {abs(fila['total_horas'])} hrs")
____________________st.markdown(f"**Motivo registrado:** {fila['motivo']}")
____________________if tipo == 'INGRESO' and fila['evidencia'] is not None:
________________________st.image(fila['evidencia'], width=350)
____________________if st.button(f"🟢 Autorizar Solicitud #{fila['id']}", key=f"ap_{fila['id']}"):
________________________cursor.execute("UPDATE registro_horas SET estado = 'Aprobado' WHERE id = ?", (fila['id'],))
________________________conn.commit()
________________________st.rerun()
____________________if st.button(f"🔴 Denegar Solicitud #{fila['id']}", key=f"re_{fila['id']}"):
________________________cursor.execute("UPDATE registro_horas SET estado = 'Rechazado' WHERE id = ?", (fila['id'],))
________________________conn.commit()
________________________st.rerun()
____________else:
________________st.success("✅ Bandeja limpia. No hay pendientes por procesar.")

________elif menu_admin == "📊 Bolsa Acumulativa General":
____________st.header("📊 Bolsa Acumulativa de Horas Reales Disponibles")
____________resumen = pd.read_sql_query("SELECT nombre as 'Empleado', SUM(total_horas) as 'Saldo Neto de Horas Disponibles' FROM registro_horas WHERE estado = 'Aprobado' GROUP BY nombre", conn)
____________if not resumen.empty:
________________st.dataframe(resumen, use_container_width=True, hide_index=True)
____________else:
________________st.warning("No hay horas aprobadas consolidadas.")

________elif menu_admin == "📚 Historial de Auditoría":
____________st.header("📚 Historial de Transacciones de la Planilla")
____________historial = pd.read_sql_query("SELECT id, nombre, fecha, area, total_horas, estado, tipo_movimiento, motivo FROM registro_horas", conn)
____________st.dataframe(historial, use_container_width=True, hide_index=True)
____________if not historial.empty:
________________output = io.BytesIO()
________________with pd.ExcelWriter(output, engine='openpyxl') as writer:
____________________historial.to_excel(writer, index=False, sheet_name='Bitacora_Horas_Ancon')
________________processed_data = output.getvalue()
________________st.download_button(label="📥 Descargar Libro Completo en Excel (.xlsx)", data=processed_data, file_name="Planilla_Horas_Ancon.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

____elif st.session_state["user_role"] == "PERSONAL":
________emp_nombre = st.session_state["user_fullname"]
________st.sidebar.markdown(f"### 👨‍🔧 Panel de: \n**{emp_nombre}**")
________menu_personal = st.sidebar.selectbox("Acciones Disponibles", ["📊 Mi Panel y Estatus", "✍️ Reportar Horas Extras (+)", "🔻 Solicitar Día Compensatorio (-)"])

________if menu_personal == "📊 Mi Panel y Estatus":
____________st.header(f"👋 ¡Bienvenido, {emp_nombre}!")
____________cursor.execute("SELECT SUM(total_horas) FROM registro_horas WHERE nombre = ? AND estado = 'Aprobado'", (emp_nombre,))
____________saldo_res = cursor.fetchone()
____________saldo_neto = float(saldo_res[0]) if (saldo_res and saldo_res[0] is not None) else 0.0
____________st.metric(label="⌛ Tu Saldo de Horas Disponibles a Favor:", value=f"{saldo_neto} hrs")
____________df_mis_solicitudes = pd.read_sql_query("SELECT fecha as 'Fecha', dia as 'Día', total_horas as 'Horas', estado as 'Estatus del Jefe', motivo as 'Detalle/Motivo' FROM registro_horas WHERE nombre = ? ORDER BY id DESC", conn, params=(emp_nombre,))
____________if not df_mis_solicitudes.empty:
________________st.dataframe(df_mis_solicitudes, use_container_width=True, hide_index=True)
____________else:
________________st.caption("Aún no has enviado ninguna solicitud.")

________elif menu_personal == "✍️ Reportar Horas Extras (+)":
____________st.header("✍️ Reportar Jornada Extraordinaria")
____________with st.form("form_extras_p", clear_on_submit=True):
________________fecha_input = st.date_input("Fecha de la Jornada:")
________________dia_semana = st.selectbox("Día de la Semana:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])
________________hora_inicio = st.time_input("Hora de Inicio:")
________________hora_fin = st.time_input("Hora de Finalización:")
________________motivo = st.text_area("Motivo de la jornada:")
________________foto_adjunta = st.file_uploader("Adjuntar foto de comprobante:", type=["png", "jpg", "jpeg"])
________________enviar = st.form_submit_button("Subir Solicitud")
________________if enviar:
____________________fmt = "%H:%M:%S"
____________________t1 = datetime.strptime(str(hora_inicio), fmt)
____________________t2 = datetime.strptime(str(hora_fin), fmt)
____________________diferencia = (t2 - t1) if t2 >= t1 else (t2 - t1) + pd.Timedelta(days=1)
____________________total_horas_calculadas = round(diferencia.seconds / 3600, 2)
____________________foto_bytes = foto_adjunta.read() if foto_adjunta is not None else None
____________________fecha_str = fecha_input.strftime("%d/%m/%Y")
____________________cursor.execute("INSERT INTO registro_horas (nombre, fecha, dia, area, cargo, hora_inicio, hora_fin, motivo, total_horas, estado, evidencia, tipo_movimiento) VALUES (?, ?, ?, 'Operaciones', 'Operario', ?, ?, ?, ?, 'Pendiente', ?, 'INGRESO')", (emp_nombre, fecha_str, dia_semana, str(hora_inicio), str(hora_fin), motivo, total_horas_calculadas, foto_bytes))
____________________conn.commit()
____________________st.success("✔️ Solicitud registrada con éxito.")

________elif menu_personal == "🔻 Solicitar Día Compensatorio (-)":
____________st.header("🔻 Solicitar Uso de Tiempo Libre / Día Compensatorio")
____________with st.form("form_libres_p", clear_on_submit=True):
________________fecha_libre = st.date_input("Fecha solicitada:")
________________dia_libre_semana = st.selectbox("Día de la semana solicitado:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])
________________horas_solicitadas = st.number_input("Cantidad de horas a descontar:", min_value=0.5, max_value=40.0, value=8.0, step=0.5)
________________motivo_libre = st.text_area("Justificación:")
________________enviar_libre = st.form_submit_button("Enviar Solicitud")
________________if enviar_libre:
____________________fecha_libre_str = fecha_libre.strftime("%d/%m/%Y")
____________________horas_negativas = -float(horas_solicitadas)
____________________cursor.execute("INSERT INTO registro_horas (nombre, fecha, dia, area, cargo, hora_inicio, hora_fin, motivo, total_horas, estado, evidencia, tipo_movimiento) VALUES (?, ?, ?, 'Uso de Tiempo', 'Operario', 'N/A', 'N/A', ?, ?, 'Pendiente', None, 'REDUCCION')", (emp_nombre, fecha_libre_str, dia_libre_semana, motivo_libre, horas_negativas))
____________________conn.commit()
____________________st.success("🔻 Solicitud de tiempo libre enviada con éxito.")

conn.close()
