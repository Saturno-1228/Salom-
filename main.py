import os
from pynput import keyboard
import audio_manager  # Sus oídos
import organizador    # Sus manos automáticas
import agente         # Su nuevo cerebro

def procesar_orden():
    archivo = audio_manager.detener_grabacion()
    if not archivo:
        return
    texto = audio_manager.transcribir_voz(archivo)
    if texto:
        print(f"\nUsted dijo: {texto}")
        # Usar el nuevo agente que maneja memoria y herramientas
        agente.procesar_mensaje(texto)

# --- INICIO DEL SISTEMA ---
if __name__ == "__main__":
    print("--- Salomé está despertando ---")
    
    # 1. Activamos la vigilancia automática de archivos
    observador = organizador.iniciar_vigilancia()
    
    # 2. Activamos la escucha de teclado
    print("--- Listo. Mantenga presionada F4 para hablar, Esc para salir. ---")
    print("--- Deje archivos en la carpeta 'Entrada' para que los organice. ---")

    tecla_f4_presionada = False

    def on_press(key):
        global tecla_f4_presionada
        if key == keyboard.Key.f4:
            if not tecla_f4_presionada:
                tecla_f4_presionada = True
                audio_manager.iniciar_grabacion()
        elif key == keyboard.Key.esc:
            observador.stop() # Detenemos la vigilancia al salir
            return False

    def on_release(key):
        global tecla_f4_presionada
        if key == keyboard.Key.f4:
            tecla_f4_presionada = False
            procesar_orden()

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()