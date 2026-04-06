import windows_tools
import recordatorios
import organizador

def ejecutar_herramienta(nombre_herramienta, argumentos):
    """
    Despachador central y seguro de herramientas.
    Solo permite ejecutar funciones explícitamente permitidas.
    """

    herramientas_permitidas = {
        "vaciar_papelera": windows_tools.vaciar_papelera,
        "cerrar_programa": windows_tools.cerrar_programa,
        "gestionar_notificaciones": windows_tools.gestionar_notificaciones,
        "buscar_en_brave": windows_tools.buscar_en_brave,
        "abrir_youtube": windows_tools.abrir_youtube,
        "crear_recordatorio_minutos": recordatorios.crear_recordatorio_minutos,
        "crear_recordatorio_hora": recordatorios.crear_recordatorio_hora,
        "silenciar_pc": windows_tools.silenciar_pc,
        "mostrar_estado_bot": windows_tools.mostrar_estado_bot,
        "abrir_panel_control": windows_tools.abrir_panel_control,
        "apagar_pc_tiempo": windows_tools.apagar_pc_tiempo,
        "limpiar_escritorio": organizador.limpiar_escritorio,
        "organizar_archivos": organizador.organizar_archivos_existentes_manual,
        "obtener_reporte_salud": windows_tools.obtener_reporte_salud,
        "listar_procesos_pesados": windows_tools.listar_procesos_pesados,
        "actualizar_bot": windows_tools.actualizar_bot,
        "buscar_y_resumir": windows_tools.buscar_y_resumir,
        "modo_panico": windows_tools.modo_panico,
        "crear_nota_rapida": organizador.crear_nota_rapida,
    }

    if nombre_herramienta not in herramientas_permitidas:
        return f"Error: La herramienta '{nombre_herramienta}' no existe o no está permitida por seguridad."

    funcion = herramientas_permitidas[nombre_herramienta]

    try:
        # Desempaquetamos los argumentos dict al llamar a la función
        return funcion(**argumentos)
    except TypeError as e:
         return f"Error en los argumentos para {nombre_herramienta}: {e}"
    except Exception as e:
        return f"Error al ejecutar {nombre_herramienta}: {e}"
