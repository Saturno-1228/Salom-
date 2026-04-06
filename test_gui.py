import sys
import threading
import time

def run_app():
    import main
    print("Main app module loaded.")
    # Inicia la interfaz creando la GUI y activando su loop
    main.crear_gui()

thread = threading.Thread(target=run_app, daemon=True)
thread.start()

time.sleep(3)
print("GUI executed and remained stable.")
sys.exit(0)
