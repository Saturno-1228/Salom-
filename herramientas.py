import windows_tools
import recordatorios

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
