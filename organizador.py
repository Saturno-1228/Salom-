import os
import shutil
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ManejadorArchivos(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            self.organizar(event.src_path)

    def organizar(self, ruta_archivo):
        # Esperamos un segundo para que el archivo termine de copiarse
        time.sleep(1)
        nombre, extension = os.path.splitext(ruta_archivo)
        extension = extension.lower()
        
        destino = "Organizado"
        
        # Definimos subcarpetas según su tipo
        if extension in ['.jpg', '.png', '.jpeg']:
            subcarpeta = "Imagenes"
        elif extension in ['.pdf', '.docx', '.txt']:
            subcarpeta = "Documentos"
        else:
            subcarpeta = "Otros"

        ruta_destino = os.path.join(destino, subcarpeta)
        
        # Creamos la carpeta si no existe
        if not os.path.exists(ruta_destino):
            os.makedirs(ruta_destino)

        # Movemos el archivo
        shutil.move(ruta_archivo, os.path.join(ruta_destino, os.path.basename(ruta_archivo)))
        print(f"Amo, he movido {os.path.basename(ruta_archivo)} a {subcarpeta} por usted.")

def iniciar_vigilancia():
    path = "Entrada"
    if not os.path.exists(path): os.makedirs(path)
    
    event_handler = ManejadorArchivos()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    print("--- Salomé ahora vigila su carpeta de Entrada ---")
    return observer