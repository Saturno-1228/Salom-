import os
import subprocess
import webbrowser

def vaciar_papelera():
    """Vacia la papelera de reciclaje de Windows"""
    try:
        import winshell
        winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
        return "Papelera vaciada con éxito."
    except ImportError:
        # Si no estamos en Windows o falta winshell
        if os.name == 'nt':
            try:
                subprocess.run(['PowerShell', '-Command', 'Clear-RecycleBin -Force -ErrorAction SilentlyContinue'], shell=True)
                return "Papelera vaciada usando PowerShell."
            except Exception as e:
                return f"Error al intentar vaciar la papelera con PowerShell: {e}"
        else:
            return "El comando para vaciar la papelera solo es válido en Windows."
    except Exception as e:
        return f"Error al vaciar la papelera: {e}"

def cerrar_programa(nombre):
    """Cierra forzosamente un programa por su nombre."""
    if os.name != 'nt':
        return "El cierre de programas por nombre de esta manera solo está implementado para Windows."

    try:
        if not nombre.endswith('.exe'):
            nombre += '.exe'
        # Usamos taskkill en Windows
        result = subprocess.run(['taskkill', '/F', '/IM', nombre], capture_output=True, text=True)
        if result.returncode == 0:
            return f"Programa {nombre} cerrado con éxito."
        else:
            return f"No se pudo cerrar {nombre}. Tal vez no está abierto."
    except Exception as e:
        return f"Error al cerrar programa: {e}"

def gestionar_notificaciones(estado="on"):
    """
    Intenta activar o desactivar las notificaciones globales de Windows
    modificando el registro para el 'Focus Assist' (Asistente de Concentración).
    estado: 'on' (permitir notificaciones), 'off' (silenciar/activar Focus Assist)
    """
    if os.name != 'nt':
        return "Esta función solo está disponible en Windows."

    try:
        # Estado 0 = Desactivado (Notificaciones normales)
        # Estado 1 o 2 = Activado (Focus Assist on - Silenciar)
        valor = "0" if estado.lower() == "on" else "2"
        comando = f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\PushNotifications" /v ToastEnabled /t REG_DWORD /d {valor} /f'
        subprocess.run(comando, shell=True, capture_output=True)

        # Requiere reiniciar el explorador para tomar efecto, pero lo omitimos por ser muy invasivo.
        # Avisamos al usuario que podría no ser inmediato o requerir configuraciones adicionales.
        accion = "activadas" if estado.lower() == "on" else "silenciadas"
        return f"Notificaciones del sistema {accion}. (Puede requerir reiniciar sesión para aplicar cambios completamente en algunas versiones de Windows)."
    except Exception as e:
        return f"Error al gestionar notificaciones: {e}"

def buscar_en_brave(consulta):
    """Abre Brave y realiza una búsqueda."""
    try:
        # Intentamos registrar Brave si se conoce la ruta común en Windows
        brave_path = "C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe"
        if os.path.exists(brave_path):
            webbrowser.register('brave', None, webbrowser.BackgroundBrowser(brave_path))
            browser = webbrowser.get('brave')
        else:
            # Fallback al navegador por defecto
            browser = webbrowser.get()

        url = f"https://search.brave.com/search?q={consulta}"
        browser.open(url)
        return f"Buscando '{consulta}' en el navegador."
    except Exception as e:
        return f"Error al buscar en el navegador: {e}"

def abrir_youtube(consulta=None):
    """Abre YouTube en el navegador. Si hay consulta, hace la búsqueda."""
    try:
        brave_path = "C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe"
        if os.path.exists(brave_path):
            webbrowser.register('brave', None, webbrowser.BackgroundBrowser(brave_path))
            browser = webbrowser.get('brave')
        else:
            browser = webbrowser.get()

        if consulta:
            url = f"https://www.youtube.com/results?search_query={consulta}"
            browser.open(url)
            return f"Buscando '{consulta}' en YouTube."
        else:
            browser.open("https://www.youtube.com")
            return "Abriendo YouTube."
    except Exception as e:
        return f"Error al abrir YouTube: {e}"

def silenciar_pc():
    """Silencia el volumen general de Windows usando un comando nircmd o un script VBScript."""
    if os.name != 'nt':
        return "El silenciamiento del PC solo está implementado para Windows."

    try:
        # Usamos un script de PowerShell para silenciar (Mute)
        script = "$obj = new-object -com wscript.shell; $obj.SendKeys([char]173)"
        subprocess.run(["powershell", "-Command", script], capture_output=True)
        return "Volumen del PC silenciado (tecla mute presionada de forma virtual)."
    except Exception as e:
        return f"Error al intentar silenciar el PC: {e}"

def mostrar_estado_bot():
    """Devuelve un resumen simple del estado del bot."""
    # Podría extenderse con uso de RAM, CPU, etc.
    return "Estado del bot Salomé: Operativa, sistemas de vigilancia activos, esperando órdenes."

def abrir_panel_control():
    """Abre el panel de control de Windows."""
    if os.name != 'nt':
        return "Esta función solo está disponible en Windows."

    try:
        subprocess.Popen("control", shell=True)
        return "Panel de Control de Windows abierto."
    except Exception as e:
        return f"Error abriendo el panel de control: {e}"

def apagar_pc_tiempo(minutos=60):
    """Programa el apagado del PC en N minutos."""
    if os.name != 'nt':
        return "Esta función solo está disponible en Windows."

    try:
        segundos = int(minutos) * 60
        # shutdown /s (shutdown) /t (time)
        subprocess.run(['shutdown', '/s', '/t', str(segundos)], capture_output=True)
        return f"PC programado para apagarse en {minutos} minutos."
    except Exception as e:
        return f"Error al programar el apagado: {e}"
