import os
import shutil
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Directorio del usuario actual
USUARIO_DIR = os.path.expanduser('~')

# Rutas a vigilar (Descargas, Escritorio, Documentos)
RUTAS_A_VIGILAR = [
    os.path.join(USUARIO_DIR, "Downloads"),
    os.path.join(USUARIO_DIR, "Desktop"),
    os.path.join(USUARIO_DIR, "Documents")
]

# Carpeta principal donde se organizará todo
CARPETA_TRABAJO = os.path.join(USUARIO_DIR, "Carpeta de Trabajo")

def generar_nombre_unico(ruta_destino, nombre_archivo):
    """
    Si el archivo ya existe en el destino, le añade un número para evitar sobrescribirlo.
    Ejemplo: archivo.txt -> archivo(1).txt -> archivo(2).txt
    """
    nombre, extension = os.path.splitext(nombre_archivo)
    contador = 1
    nueva_ruta = os.path.join(ruta_destino, nombre_archivo)

    while os.path.exists(nueva_ruta):
        nuevo_nombre = f"{nombre}({contador}){extension}"
        nueva_ruta = os.path.join(ruta_destino, nuevo_nombre)
        contador += 1
        
    return nueva_ruta

def organizar_archivo(ruta_archivo, es_nuevo=True):
    """
    Lógica principal para mover un archivo a su carpeta correspondiente.
    """
    # Verificamos si la ruta es válida y es un archivo
    if not os.path.exists(ruta_archivo) or not os.path.isfile(ruta_archivo):
        return

    # Evitamos organizar la misma Carpeta de Trabajo o sus contenidos si por alguna razón está dentro de las rutas vigiladas
    if ruta_archivo.startswith(CARPETA_TRABAJO):
        return

    # Si es un archivo nuevo detectado por watchdog, esperamos 1 segundo para asegurar
    # que ha terminado de copiarse o descargarse. Si es un archivo que ya existía, no esperamos.
    if es_nuevo:
        try:
            time.sleep(1)
        except:
            pass

    nombre_archivo = os.path.basename(ruta_archivo)
    _, extension = os.path.splitext(nombre_archivo)
    extension = extension.lower()

    # --------------------------------------------------------------------------
    # GUÍA PARA MEJORAR Y AÑADIR NUEVAS CARPETAS A FUTURO:
    # 1. Agrega las extensiones que desees en una lista.
    # 2. Asigna un nombre a la variable `subcarpeta` en la condición `elif`.
    # Ejemplo:
    # elif extension in ['.mp4', '.avi', '.mkv']:
    #     subcarpeta = "Videos"
    # --------------------------------------------------------------------------

    if extension in ['.jpg', '.png', '.jpeg', '.gif', '.bmp', '.svg', '.webp']:
        subcarpeta = "Imagenes"
    elif extension in ['.pdf', '.docx', '.doc', '.txt', '.xlsx', '.xls', '.pptx', '.ppt', '.csv']:
        subcarpeta = "Textos"
    elif extension in ['.zip', '.rar', '.7z', '.tar', '.gz']:
        subcarpeta = "Comprimidos"
    elif extension in ['.exe', '.msi']:
        subcarpeta = "Ejecutables"
    elif extension in ['.mp3', '.wav', '.flac']:
        subcarpeta = "Audios"
    elif extension in ['.mp4', '.avi', '.mkv', '.mov']:
        subcarpeta = "Videos"
    else:
        # Ignoramos archivos temporales o de sistema que no queramos mover (incluyendo los de desktop.ini)
        if extension in ['.tmp', '.crdownload', '.ini', '.part']:
            return
        # También ignoramos los accesos directos por seguridad, a menos que quieras moverlos.
        if extension in ['.lnk']:
            return
        subcarpeta = "Otros"

    ruta_destino = os.path.join(CARPETA_TRABAJO, subcarpeta)

    # Creamos la subcarpeta si no existe
    if not os.path.exists(ruta_destino):
        try:
            os.makedirs(ruta_destino)
        except Exception as e:
            print(f"Error al crear la carpeta {ruta_destino}: {e}")
            return

    # Generamos un nombre único para evitar sobrescribir
    ruta_final = generar_nombre_unico(ruta_destino, nombre_archivo)

    # Movemos el archivo
    try:
        shutil.move(ruta_archivo, ruta_final)
        print(f"Amo, he movido {nombre_archivo} a {subcarpeta} por usted.")
    except Exception as e:
        print(f"No se pudo mover {nombre_archivo}: {e}")

class ManejadorArchivos(FileSystemEventHandler):
    def on_created(self, event):
        # Solo reaccionamos si es un archivo
        if not event.is_directory:
            organizar_archivo(event.src_path)

    def on_moved(self, event):
        # Para casos en que los navegadores renombran el archivo una vez descargado
        if not event.is_directory:
            organizar_archivo(event.dest_path)

def limpiar_escritorio():
    """
    Fuerza la limpieza del escritorio, moviendo todos los archivos sueltos a la Carpeta de Trabajo.
    """
    escritorio = os.path.join(USUARIO_DIR, "Desktop")
    if os.path.exists(escritorio):
        archivos_movidos = 0
        for item in os.listdir(escritorio):
            ruta_completa = os.path.join(escritorio, item)
            if os.path.isfile(ruta_completa):
                organizar_archivo(ruta_completa, es_nuevo=False)
                archivos_movidos += 1
        return f"Escritorio limpiado. {archivos_movidos} archivos organizados."
    return "No se pudo acceder al escritorio."

def organizar_archivos_existentes_manual():
    """Llamado manual por el usuario para forzar la organización."""
    organizar_archivos_existentes()
    return "Archivos existentes organizados en las carpetas vigiladas."

def crear_nota_rapida(texto, titulo=None):
    """Crea una nota rápida de texto en la Carpeta de Trabajo."""
    if not os.path.exists(CARPETA_TRABAJO):
        os.makedirs(CARPETA_TRABAJO)

    if not titulo:
        import datetime
        titulo = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    if not titulo.endswith(".txt"):
        titulo += ".txt"

    ruta_notas = os.path.join(CARPETA_TRABAJO, "Notas")
    if not os.path.exists(ruta_notas):
         os.makedirs(ruta_notas)

    ruta_archivo = os.path.join(ruta_notas, titulo)

    try:
        with open(ruta_archivo, "w", encoding="utf-8") as f:
            f.write(texto)
        return f"Nota '{titulo}' creada con éxito en {ruta_notas}."
    except Exception as e:
        return f"Error al crear nota: {e}"

def organizar_archivos_existentes():
    """
    Escanea las carpetas especificadas buscando archivos (no subcarpetas)
    que ya estén ahí y los organiza en la Carpeta de Trabajo.
    """
    print("--- Salomé está ordenando los archivos existentes. Esto puede tomar un momento... ---")
    for ruta in RUTAS_A_VIGILAR:
        if os.path.exists(ruta):
            for item in os.listdir(ruta):
                ruta_completa = os.path.join(ruta, item)
                # Solo procesamos si es un archivo directo (ignorando subcarpetas como los juegos en Documentos)
                if os.path.isfile(ruta_completa):
                    # Pasamos es_nuevo=False para que no se pause 1 segundo por cada archivo
                    organizar_archivo(ruta_completa, es_nuevo=False)
    print("--- Organización inicial completada ---")

def iniciar_vigilancia():
    # Nos aseguramos de que la carpeta de trabajo exista
    if not os.path.exists(CARPETA_TRABAJO):
        os.makedirs(CARPETA_TRABAJO)

    observer = Observer()
    event_handler = ManejadorArchivos()

    rutas_vigiladas = []

    for ruta in RUTAS_A_VIGILAR:
        # Aseguramos que el directorio exista antes de vigilarlo
        if not os.path.exists(ruta):
            try:
                os.makedirs(ruta)
            except:
                continue

        # recursive=False es CLAVE para no tocar archivos internos de aplicaciones/juegos
        observer.schedule(event_handler, ruta, recursive=False)
        rutas_vigiladas.append(ruta)

    observer.start()
    print("--- Salomé ahora vigila las siguientes carpetas en automático ---")
    for r in rutas_vigiladas:
        print(f" - {r}")

    return observer
