import threading
import time
import schedule
from plyer import notification
import uuid

# Diccionario para mantener registro de las tareas programadas
_tareas_programadas = {}

def _mostrar_notificacion(mensaje, titulo="Salomé - Recordatorio"):
    """Muestra una notificación emergente en Windows."""
    try:
        notification.notify(
            title=titulo,
            message=mensaje,
            app_name="Salomé",
            timeout=10  # segundos que dura la notificación
        )
        print(f"\n[Recordatorio Mostrado]: {mensaje}")
    except Exception as e:
        print(f"Error al mostrar notificación: {e}")

def _ejecutar_y_cancelar(id_tarea, mensaje):
    """Ejecuta la notificación y luego cancela la tarea para que no se repita si era de un solo uso."""
    _mostrar_notificacion(mensaje)
    if id_tarea in _tareas_programadas:
        schedule.cancel_job(_tareas_programadas[id_tarea])
        del _tareas_programadas[id_tarea]

def crear_recordatorio_minutos(mensaje, minutos):
    """Crea un recordatorio en X minutos."""
    try:
        minutos = int(minutos)
        if minutos <= 0:
            return "Los minutos deben ser mayores a 0."

        tarea_id = str(uuid.uuid4())

        # Programar la tarea
        job = schedule.every(minutos).minutes.do(_ejecutar_y_cancelar, id_tarea=tarea_id, mensaje=mensaje)
        _tareas_programadas[tarea_id] = job

        return f"Recordatorio creado. Te avisaré en {minutos} minutos."
    except Exception as e:
        return f"Error al crear recordatorio: {e}"

def crear_recordatorio_hora(mensaje, hora_str):
    """Crea un recordatorio a una hora específica (formato HH:MM, 24 horas)."""
    try:
        tarea_id = str(uuid.uuid4())
        job = schedule.every().day.at(hora_str).do(_ejecutar_y_cancelar, id_tarea=tarea_id, mensaje=mensaje)
        _tareas_programadas[tarea_id] = job

        return f"Recordatorio creado. Te avisaré a las {hora_str}."
    except schedule.ScheduleValueError:
        return "Formato de hora inválido. Usa HH:MM en formato 24 horas."
    except Exception as e:
        return f"Error al crear recordatorio: {e}"


def _correr_scheduler():
    """Hilo en segundo plano que revisa las tareas programadas continuamente."""
    while True:
        schedule.run_pending()
        time.sleep(1)

# Iniciamos el hilo del scheduler al importar este módulo
_hilo_scheduler = threading.Thread(target=_correr_scheduler, daemon=True)
_hilo_scheduler.start()
print("--- Sistema de recordatorios de Salomé iniciado ---")
