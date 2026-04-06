import os
import tkinter as tk
from tkinter import ttk
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
chat_history_text = None
sidebar_frame = None
main_content_frame = None
sidebar_expanded = True
views = {}

def update_chat_history(role, text):
    if chat_history_text:
        chat_history_text.config(state="normal")
        if role == "user":
            chat_history_text.insert(tk.END, f"Tú: {text}\n", "user")
        elif role == "bot":
            chat_history_text.insert(tk.END, f"Salomé: {text}\n", "bot")
        elif role == "system":
            chat_history_text.insert(tk.END, f"[Sistema]: {text}\n", "system")
        chat_history_text.see(tk.END)
        chat_history_text.config(state="disabled")

def procesar_orden_texto(texto):
    if texto.strip():
        # print(f"\nAmo dice: {texto}")
        # Muestra en el historial
        root.after(0, update_chat_history, "user", texto)
        # Usar el agente para procesar el comando de texto
        # Redirigimos el print interno temporalmente si quisieramos,
        # pero como el agente hace prints, los enviamos a consola.
        # Idealmente el agente retornaría la respuesta.
        # Por ahora asumimos que el agente responde y registramos el proceso.
        try:
            # TODO: Idealmente agente.procesar_mensaje debería devolver el texto
            # Para mostrarlo en el historial
            agente.procesar_mensaje(texto)
            root.after(0, update_chat_history, "bot", "He procesado la orden. (Ver consola para detalles completos si los hay)")
        except Exception as e:
            root.after(0, update_chat_history, "system", f"Error procesando: {e}")

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
        # Enfocar en la entrada de texto
        for widget in root.winfo_children():
            if hasattr(root, "chat_entry"):
                root.chat_entry.focus_set()
                break
        gui_visible = True

def toggle_sidebar():
    global sidebar_expanded, sidebar_frame
    if sidebar_expanded:
        sidebar_frame.pack_forget()
        sidebar_expanded = False
    else:
        # Repack left
        sidebar_frame.pack(side="left", fill="y")
        sidebar_expanded = True

def show_view(view_name):
    for name, frame in views.items():
        if name == view_name:
            frame.pack(fill="both", expand=True)
        else:
            frame.pack_forget()

def crear_gui():
    global root, gui_visible, chat_history_text, sidebar_frame, main_content_frame, views

    root = tk.Tk()
    root.title("Salomé - Interfaz de Control")
    root.geometry("1000x700") # Tamaño inicial más grande
    root.resizable(True, True)

    # Estética limpia, profesional y roja (modo oscuro)
    color_fondo_main = "#1e1e1e"
    color_fondo_sidebar = "#111111"
    color_acento = "#d32f2f"     # Rojo profesional
    color_acento_hover = "#b71c1c"
    color_texto = "#e0e0e0"
    color_texto_dark = "#ffffff"
    color_input = "#2d2d2d"

    root.configure(bg=color_fondo_main)

    # Ocultar por defecto
    root.withdraw()
    gui_visible = False
    root.protocol("WM_DELETE_WINDOW", lambda: root.withdraw())
    root.bind("<Escape>", lambda e: toggle_gui() if gui_visible else None)

    # Estilos ttk
    style = ttk.Style()
    style.theme_use('clam')

    # Scrollbar style
    style.configure("Vertical.TScrollbar", background=color_fondo_sidebar, bordercolor=color_fondo_main, arrowcolor=color_texto)

    # Contenedor principal
    main_container = tk.Frame(root, bg=color_fondo_main)
    main_container.pack(fill="both", expand=True)

    # --- SIDEBAR ---
    sidebar_frame = tk.Frame(main_container, bg=color_fondo_sidebar, width=250)
    sidebar_frame.pack(side="left", fill="y")
    sidebar_frame.pack_propagate(False) # Keep width

    lbl_title = tk.Label(sidebar_frame, text="SALOMÉ", font=("Segoe UI", 24, "bold"), bg=color_fondo_sidebar, fg=color_acento)
    lbl_title.pack(pady=20)

    def nav_btn(text, view_name):
        btn = tk.Button(sidebar_frame, text=text, font=("Segoe UI", 16), bg=color_fondo_sidebar, fg=color_texto,
                        activebackground=color_input, activeforeground=color_texto_dark, relief="flat", anchor="w", padx=20,
                        command=lambda: show_view(view_name))
        btn.pack(fill="x", pady=5)
        # Efecto hover
        btn.bind("<Enter>", lambda e: btn.config(bg=color_input))
        btn.bind("<Leave>", lambda e: btn.config(bg=color_fondo_sidebar))
        return btn

    nav_btn("Chat / Historial", "chat")
    nav_btn("Comandos Rápidos", "comandos")
    nav_btn("Administración", "admin")

    # --- MAIN CONTENT ---
    content_area = tk.Frame(main_container, bg=color_fondo_main)
    content_area.pack(side="right", fill="both", expand=True)

    # Botón Toggle Sidebar (Hamburger/Toggle)
    top_bar = tk.Frame(content_area, bg=color_fondo_main, height=50)
    top_bar.pack(side="top", fill="x")
    btn_toggle = tk.Button(top_bar, text="☰", font=("Segoe UI", 18), bg=color_fondo_main, fg=color_texto,
                           activebackground=color_input, activeforeground=color_texto_dark, relief="flat",
                           command=toggle_sidebar)
    btn_toggle.pack(side="left", padx=10, pady=10)

    # Contenedor de Vistas
    view_container = tk.Frame(content_area, bg=color_fondo_main)
    view_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    # --- VISTA 1: CHAT (Default) ---
    chat_view = tk.Frame(view_container, bg=color_fondo_main)
    views["chat"] = chat_view

    # Historial
    chat_history_frame = tk.Frame(chat_view, bg=color_fondo_main)
    chat_history_frame.pack(fill="both", expand=True, pady=(0, 10))

    scrollbar = ttk.Scrollbar(chat_history_frame)
    scrollbar.pack(side="right", fill="y")

    chat_history_text = tk.Text(chat_history_frame, font=("Segoe UI", 16), bg=color_fondo_main, fg=color_texto,
                                relief="flat", yscrollcommand=scrollbar.set, wrap="word", state="disabled")
    chat_history_text.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=chat_history_text.yview)

    # Configurar tags de texto
    chat_history_text.tag_config("user", foreground="#ffffff", font=("Segoe UI", 16, "bold"))
    chat_history_text.tag_config("bot", foreground=color_acento)
    chat_history_text.tag_config("system", foreground="#888888", font=("Segoe UI", 14, "italic"))

    # Input
    input_frame = tk.Frame(chat_view, bg=color_input, padx=10, pady=10)
    input_frame.pack(fill="x")

    chat_entry = tk.Entry(input_frame, font=("Segoe UI", 18), bg=color_input, fg=color_texto_dark,
                          insertbackground=color_texto_dark, relief="flat")
    chat_entry.pack(side="left", fill="x", expand=True, ipady=5)
    root.chat_entry = chat_entry # Guardar referencia para enfocar

    def on_enter(event=None):
        texto = chat_entry.get()
        if texto:
            chat_entry.delete(0, tk.END)
            threading.Thread(target=procesar_orden_texto, args=(texto,), daemon=True).start()

    chat_entry.bind("<Return>", on_enter)

    btn_send = tk.Button(input_frame, text="Enviar", font=("Segoe UI", 16, "bold"), bg=color_acento, fg="#ffffff",
                         activebackground=color_acento_hover, activeforeground="#ffffff", relief="flat", padx=15,
                         command=on_enter)
    btn_send.pack(side="right", padx=(10, 0))


    # --- VISTA 2: COMANDOS RÁPIDOS ---
    comandos_view = tk.Frame(view_container, bg=color_fondo_main)
    views["comandos"] = comandos_view

    lbl_cmds = tk.Label(comandos_view, text="Comandos Rápidos", font=("Segoe UI", 20, "bold"), bg=color_fondo_main, fg=color_texto)
    lbl_cmds.pack(pady=(0, 20), anchor="w")

    # Canvas para scroll en botones
    cmd_canvas = tk.Canvas(comandos_view, bg=color_fondo_main, highlightthickness=0)
    cmd_scrollbar = ttk.Scrollbar(comandos_view, orient="vertical", command=cmd_canvas.yview)
    scrollable_cmd_frame = tk.Frame(cmd_canvas, bg=color_fondo_main)

    scrollable_cmd_frame.bind(
        "<Configure>",
        lambda e: cmd_canvas.configure(
            scrollregion=cmd_canvas.bbox("all")
        )
    )

    cmd_canvas.create_window((0, 0), window=scrollable_cmd_frame, anchor="nw")
    cmd_canvas.configure(yscrollcommand=cmd_scrollbar.set)

    cmd_canvas.pack(side="left", fill="both", expand=True)
    cmd_scrollbar.pack(side="right", fill="y")

    comandos_rapidos = [
        "Vaciar papelera", "Silenciar el PC", "Activar notificaciones",
        "Limpiar escritorio", "Organizar Archivos", "Mostrar Estado del Bot",
        "Modo Concentración", "Abrir panel de control", "Apagar en 1 hora"
    ]

    row = 0
    col = 0
    for cmd in comandos_rapidos:
        btn = tk.Button(scrollable_cmd_frame, text=cmd, font=("Segoe UI", 16), bg=color_input, fg=color_texto,
                        activebackground=color_acento, activeforeground="#ffffff", relief="flat", width=20, height=2,
                        command=lambda c=cmd: [show_view("chat"), chat_entry.delete(0, tk.END), chat_entry.insert(0, c), on_enter()])
        btn.grid(row=row, column=col, padx=10, pady=10)
        col += 1
        if col > 2: # 3 columnas
            col = 0
            row += 1

    # --- VISTA 3: ADMINISTRACIÓN ---
    admin_view = tk.Frame(view_container, bg=color_fondo_main)
    views["admin"] = admin_view
    lbl_admin = tk.Label(admin_view, text="Panel de Administración", font=("Segoe UI", 20, "bold"), bg=color_fondo_main, fg=color_texto)
    lbl_admin.pack(pady=(0, 20), anchor="w")

    lbl_admin_info = tk.Label(admin_view, text="Módulo en desarrollo.\nAquí se configurarán parámetros del sistema y del agente.",
                              font=("Segoe UI", 16), bg=color_fondo_main, fg=color_texto, justify="left")
    lbl_admin_info.pack(anchor="w")

    # Mostrar Chat por defecto
    show_view("chat")
    update_chat_history("system", "Salomé iniciada y lista para recibir órdenes.")

    root.mainloop()

# --- INICIO DEL SISTEMA ---
if __name__ == "__main__":
    print("--- Salomé está despertando (Modo Texto/GUI) ---")
    
    # 1. Organizamos los archivos existentes primero
    organizador.organizar_archivos_existentes()

    # 2. Activamos la vigilancia automática de archivos
    observador = organizador.iniciar_vigilancia()
    
    # 3. Activamos la escucha de teclado
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
