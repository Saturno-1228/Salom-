import os
import tkinter as tk
from pynput import keyboard
import threading
# import audio_manager  # Sus oídos (Desactivado temporalmente por errores, se usa texto en su lugar)
import organizador    # Sus manos automáticas
import agente         # Su nuevo cerebro

# NOTA: Se ha desactivado la opción de voz temporalmente por errores.
# En su lugar, se ha implementado una interfaz gráfica (GUI) de texto para comunicarse con Salomé.
# El código original de audio está comentado abajo como referencia futura.

'''
def procesar_orden():
    archivo = audio_manager.detener_grabacion()
    if not archivo:
        return
    texto = audio_manager.transcribir_voz(archivo)
    if texto:
        print(f"\nUsted dijo: {texto}")
        # Usar el nuevo agente que maneja memoria y herramientas
        agente.procesar_mensaje(texto)
'''

# --- VARIABLES GLOBALES PARA LA GUI ---
root = None
gui_visible = False

def procesar_orden_texto(texto):
    if texto.strip():
        print(f"\nAmo dice: {texto}")
        # Usar el agente para procesar el comando de texto
        agente.procesar_mensaje(texto)

def toggle_gui():
    global gui_visible, root
    if root is None:
        return

    if gui_visible:
        root.withdraw()
        gui_visible = False
    else:
        root.deiconify()
        root.focus_force()
        # Enfocar en la entrada de texto si la encontramos
        for widget in root.winfo_children():
            if isinstance(widget, tk.Entry):
                widget.focus_set()
                break
        gui_visible = True

def crear_gui():
    global root, gui_visible
    root = tk.Tk()
    root.title("Salomé - Interfaz de Control")
    root.geometry("450x150")

    # Estética limpia, profesional y roja
    color_fondo = "#1a0000"
    color_acento = "#ff3333"
    color_secundario = "#4d0000"
    color_texto = "#ffffff"

    root.configure(bg=color_fondo)
    root.resizable(False, False)

    # Quitar la barra de título si se desea algo más emergente, pero la dejamos para poder moverla.
    # root.overrideredirect(True)

    # Ocultar por defecto
    root.withdraw()
    gui_visible = False

    # Asegurar que se cierra bien al salir (Esc)
    root.protocol("WM_DELETE_WINDOW", lambda: root.withdraw())

    lbl = tk.Label(root, text="Órdenes para Salomé (Esc para ocultar):", bg=color_fondo, fg=color_acento, font=("Segoe UI", 10, "bold"))
    lbl.pack(pady=(10, 5))

    entrada = tk.Entry(root, font=("Segoe UI", 11), bg=color_secundario, fg=color_texto, insertbackground=color_texto, relief="flat")
    entrada.pack(fill="x", padx=20, pady=5, ipady=5)

    def on_enter(event=None):
        texto = entrada.get()
        if texto:
            entrada.delete(0, tk.END)
            # Ejecutamos en un hilo separado para no bloquear la GUI
            threading.Thread(target=procesar_orden_texto, args=(texto,), daemon=True).start()
            toggle_gui() # Ocultar tras enviar

    entrada.bind("<Return>", on_enter)

    # Si presionan Esc en la ventana, se oculta
    root.bind("<Escape>", lambda e: toggle_gui() if gui_visible else None)

    frame_btns = tk.Frame(root, bg=color_fondo)
    frame_btns.pack(pady=5)

    comandos_rapidos = ["Vaciar papelera", "Silenciar", "Notificaciones on", "Limpiar escritorio"]
    for cmd in comandos_rapidos:
        btn = tk.Button(frame_btns, text=cmd, bg=color_secundario, fg=color_texto,
                        activebackground=color_acento, activeforeground=color_texto,
                        relief="flat", font=("Segoe UI", 8),
                        command=lambda c=cmd: [entrada.delete(0, tk.END), entrada.insert(0, c), on_enter()])
        btn.pack(side="left", padx=5)

    root.mainloop()

# --- INICIO DEL SISTEMA ---
if __name__ == "__main__":
    print("--- Salomé está despertando (Modo Texto) ---")
    
    # 1. Activamos la vigilancia automática de archivos
    observador = organizador.iniciar_vigilancia()
    
    # 2. Activamos la escucha de teclado
    print("--- Listo. Presione F4 para abrir/cerrar la consola de texto de Salomé. ---")
    print("--- Presione Ctrl+C en esta terminal para apagar el sistema completamente. ---")

    tecla_f4_presionada = False

    def on_press(key):
        global tecla_f4_presionada, root
        if key == keyboard.Key.f4:
            if not tecla_f4_presionada:
                tecla_f4_presionada = True
                if root is not None:
                    # Llamar a toggle_gui desde el hilo principal de Tkinter de forma segura
                    root.after(0, toggle_gui)

    def on_release(key):
        global tecla_f4_presionada
        if key == keyboard.Key.f4:
            tecla_f4_presionada = False

    # Iniciar el listener de pynput en segundo plano
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    # Iniciar la GUI en el hilo principal (Tkinter requiere estar en el hilo principal)
    try:
        crear_gui()
    except KeyboardInterrupt:
        pass
    finally:
        print("\nApagando a Salomé...")
        observador.stop()
        listener.stop()