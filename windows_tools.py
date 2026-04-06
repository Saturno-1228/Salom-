import os
import subprocess
import webbrowser
import psutil
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import requests
import datetime

def obtener_reporte_salud():
    """Devuelve el uso de CPU y RAM."""
    try:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        return f"CPU: {cpu}% - RAM: {ram.percent}% usada ({ram.used / (1024**3):.2f} GB / {ram.total / (1024**3):.2f} GB)."
    except Exception as e:
        return f"Error al obtener salud del PC: {e}"

def listar_procesos_pesados():
    """Lista los 5 procesos que consumen más memoria RAM."""
    try:
        procesos = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                if proc.info['memory_info'] is not None:
                    procesos.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Ordenar por uso de memoria (rss)
        procesos = sorted(procesos, key=lambda p: p['memory_info'].rss, reverse=True)[:5]

        resultado = "Top 5 procesos más pesados:\n"
        for p in procesos:
            mb = p['memory_info'].rss / (1024 * 1024)
            resultado += f"- {p['name']} (PID: {p['pid']}): {mb:.2f} MB\n"
        return resultado
    except Exception as e:
        return f"Error al listar procesos: {e}"

def actualizar_bot():
    """Realiza un git pull y muestra el resultado."""
    try:
        # Asumiendo que el repositorio es local al script
        result = subprocess.run(["git", "pull"], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        if result.returncode == 0:
             return f"Git pull exitoso:\n{result.stdout}\n(Por favor reinicie la aplicación para aplicar todos los cambios)"
        else:
             return f"Error en git pull:\n{result.stderr}"
    except Exception as e:
        return f"Error al actualizar bot: {e}"

def buscar_y_resumir(consulta):
    """Busca en DuckDuckGo, obtiene el texto de los primeros links y lo resume localmente o lo pasa al agente (en este caso devuelve el texto crudo resumido)."""
    try:
        results = DDGS().text(consulta, max_results=3)
        if not results:
            return f"No encontré resultados para '{consulta}'."

        resumen_texto = f"Resultados para '{consulta}':\n\n"
        for r in results:
            resumen_texto += f"TÍTULO: {r.get('title')}\nENLACE: {r.get('href')}\nRESUMEN: {r.get('body')}\n\n"

        # Opcionalmente se podría raspar el enlace, pero DDGS body ya es un buen resumen corto.
        return resumen_texto
    except Exception as e:
        return f"Error al buscar y resumir: {e}"

def modo_panico():
    """Cierra los navegadores más comunes y silencia el PC de inmediato."""
    silenciar_pc()
    navegadores = ["chrome.exe", "firefox.exe", "msedge.exe", "brave.exe"]
    cerrados = []

    if os.name == 'nt':
        for nav in navegadores:
            # Silently kill
            res = subprocess.run(['taskkill', '/F', '/IM', nav], capture_output=True, text=True)
            if res.returncode == 0:
                cerrados.append(nav)

    return f"Modo Pánico Activado. PC Silenciado. Navegadores cerrados: {', '.join(cerrados) if cerrados else 'Ninguno'}."

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
