import os
import sys
import tkinter as tk
import customtkinter as ctk
from PIL import Image
from pynput import keyboard
import threading
# import audio_manager  # Sus oídos (Desactivado temporalmente por errores, se usa texto en su lugar)
import organizador    # Sus manos automáticas
import agente         # Su nuevo cerebro
import herramientas   # Herramientas locales para comandos directos

# Configuración de CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")  # Tema oscuro por defecto

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
right_sidebar_frame = None
main_content_frame = None
sidebar_expanded = True
right_sidebar_expanded = False
views = {}
icons = {}
terminal_text = None

class StdoutRedirector:
    """Redirige sys.stdout a la caja de texto de terminal de la GUI"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.original_stdout = sys.stdout

    def write(self, string):
        self.original_stdout.write(string)
        if self.text_widget and root:
            # Insertar en la caja de texto de forma segura desde cualquier hilo
            root.after(0, self._append_text, string)

    def _append_text(self, string):
        self.text_widget.configure(state="normal")
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
        self.text_widget.configure(state="disabled")

    def flush(self):
        self.original_stdout.flush()

def load_icons():
    """Carga los iconos para la interfaz"""
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "icons")
    try:
        icons["chat"] = ctk.CTkImage(light_image=Image.open(os.path.join(icon_path, "chat.png")), dark_image=Image.open(os.path.join(icon_path, "chat.png")), size=(20, 20))
        icons["commands"] = ctk.CTkImage(light_image=Image.open(os.path.join(icon_path, "commands.png")), dark_image=Image.open(os.path.join(icon_path, "commands.png")), size=(20, 20))
        icons["admin"] = ctk.CTkImage(light_image=Image.open(os.path.join(icon_path, "admin.png")), dark_image=Image.open(os.path.join(icon_path, "admin.png")), size=(20, 20))
        icons["wellness"] = ctk.CTkImage(light_image=Image.open(os.path.join(icon_path, "wellness.png")), dark_image=Image.open(os.path.join(icon_path, "wellness.png")), size=(20, 20))
        icons["finance"] = ctk.CTkImage(light_image=Image.open(os.path.join(icon_path, "finance.png")), dark_image=Image.open(os.path.join(icon_path, "finance.png")), size=(20, 20))
        icons["send"] = ctk.CTkImage(light_image=Image.open(os.path.join(icon_path, "send.png")), dark_image=Image.open(os.path.join(icon_path, "send.png")), size=(20, 20))
        icons["menu"] = ctk.CTkImage(light_image=Image.open(os.path.join(icon_path, "menu.png")), dark_image=Image.open(os.path.join(icon_path, "menu.png")), size=(24, 24))
        if os.path.exists(os.path.join(icon_path, "plus.png")):
            icons["plus"] = ctk.CTkImage(light_image=Image.open(os.path.join(icon_path, "plus.png")), dark_image=Image.open(os.path.join(icon_path, "plus.png")), size=(24, 24))
    except Exception as e:
        print(f"Error loading icons: {e}")

def update_chat_history(role, text):
    if chat_history_text:
        chat_history_text.configure(state="normal")
        if role == "user":
            chat_history_text.insert(tk.END, f"Tú: {text}\n\n", "user")
        elif role == "bot":
            chat_history_text.insert(tk.END, "Salomé: ", "bot_name")
            chat_history_text.insert(tk.END, f"{text}\n\n", "bot_text")
        elif role == "bot_local":
            chat_history_text.insert(tk.END, "Salomé (Sistema Local): ", "bot_name")
            chat_history_text.insert(tk.END, f"{text}\n\n", "bot_text")
        elif role == "system":
            chat_history_text.insert(tk.END, f"[Sistema]: {text}\n\n", "system")
        chat_history_text.see(tk.END)
        chat_history_text.configure(state="disabled")

def ejecutar_comando_local(texto_usuario, herramienta, args=None):
    """Ejecuta una herramienta localmente sin pasar por la IA para ahorrar tokens y latencia."""
    if args is None:
        args = {}

    # Mostramos lo que el usuario "ordenó" al presionar el botón
    root.after(0, update_chat_history, "user", texto_usuario)

    try:
        resultado = herramientas.ejecutar_herramienta(herramienta, args)
        root.after(0, update_chat_history, "bot_local", f"Comando ejecutado. Resultado: {resultado}")
    except Exception as e:
        root.after(0, update_chat_history, "system", f"Error ejecutando localmente: {e}")

def procesar_orden_texto(texto):
    if texto.strip():
        # Muestra en el historial
        root.after(0, update_chat_history, "user", texto)
        # Usar el agente para procesar el comando de texto
        try:
            respuesta = agente.procesar_mensaje(texto)
            if respuesta:
                root.after(0, update_chat_history, "bot", respuesta)
            else:
                root.after(0, update_chat_history, "bot", "He procesado la orden, pero no tengo una respuesta verbal.")
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
        if hasattr(root, "chat_entry"):
            root.chat_entry.focus_set()
        gui_visible = True

def toggle_sidebar():
    global sidebar_expanded, sidebar_frame
    if sidebar_expanded:
        sidebar_frame.pack_forget()
        sidebar_expanded = False
    else:
        sidebar_frame.pack(side="left", fill="y")
        sidebar_expanded = True

def toggle_right_sidebar():
    global right_sidebar_expanded, right_sidebar_frame
    if right_sidebar_expanded:
        right_sidebar_frame.pack_forget()
        right_sidebar_expanded = False
    else:
        right_sidebar_frame.pack(side="right", fill="y")
        right_sidebar_expanded = True

def toggle_quick_panel():
    if quick_panel_frame.winfo_ismapped():
        quick_panel_frame.pack_forget()
    else:
        quick_panel_frame.pack(fill="x", pady=(0, 10), before=input_frame)

def show_view(view_name):
    for name, frame in views.items():
        if name == view_name:
            frame.pack(fill="both", expand=True)
        else:
            frame.pack_forget()

def crear_gui():
    global root, gui_visible, chat_history_text, sidebar_frame, right_sidebar_frame, main_content_frame, views, terminal_text

    root = ctk.CTk()
    root.title("Salomé - Interfaz de Control")
    root.geometry("1100x750")

    load_icons()

    # Variables de diseño empresarial y oscuro
    color_fondo_main = "#181818"    # Fondo principal minimalista
    color_fondo_sidebar = "#111111" # Fondo lateral más oscuro
    color_acento = "#E91E63"        # Rosa fuerte
    color_acento_hover = "#C2185B"
    color_nombre_bot = "#F48FB1"    # Rosa pastel suave
    color_texto = "#E0E0E0"         # Gris claro para menor fatiga visual
    color_texto_oscuro = "#A0A0A0"
    color_input = "#212121"         # Fondo inputs y cards
    font_base = ("Segoe UI", 18)    # 18pt como solicitaste para máxima legibilidad
    font_bold = ("Segoe UI", 18, "bold")
    font_title = ("Segoe UI", 24, "bold")

    root.configure(fg_color=color_fondo_main)

    # Ocultar por defecto
    root.withdraw()
    gui_visible = False
    root.protocol("WM_DELETE_WINDOW", lambda: root.withdraw())
    root.bind("<Escape>", lambda e: toggle_gui() if gui_visible else None)

    # --- CONTENEDOR PRINCIPAL ---
    main_container = ctk.CTkFrame(root, fg_color="transparent", corner_radius=0)
    main_container.pack(fill="both", expand=True)

    # --- SIDEBAR DERECHA (TERMINAL / LOGS) ---
    right_sidebar_frame = ctk.CTkFrame(main_container, fg_color=color_fondo_sidebar, width=350, corner_radius=0)
    # No la mostramos por defecto (estará oculta hasta usar toggle_right_sidebar)
    right_sidebar_frame.pack_propagate(False)

    lbl_terminal = ctk.CTkLabel(right_sidebar_frame, text="LOGS DEL SISTEMA", font=("Segoe UI", 16, "bold"), text_color=color_acento)
    lbl_terminal.pack(pady=(20, 10))

    terminal_text = ctk.CTkTextbox(
        right_sidebar_frame,
        font=("Consolas", 18),
        fg_color=color_input,
        text_color=color_texto,
        wrap="word"
    )
    terminal_text.pack(fill="both", expand=True, padx=10, pady=(0, 20))
    terminal_text.configure(state="disabled")

    # Redirigir stdout y stderr al terminal_text
    sys.stdout = StdoutRedirector(terminal_text)
    sys.stderr = StdoutRedirector(terminal_text)

    # --- SIDEBAR IZQUIERDA ---
    sidebar_frame = ctk.CTkFrame(main_container, fg_color=color_fondo_sidebar, width=260, corner_radius=0)
    sidebar_frame.pack(side="left", fill="y")
    sidebar_frame.pack_propagate(False)

    # Título Sidebar
    lbl_title = ctk.CTkLabel(sidebar_frame, text="SALOMÉ", font=font_title, text_color=color_nombre_bot)
    lbl_title.pack(pady=(30, 40))

    # Botones de Navegación
    def nav_btn(text, view_name, icon_key=None):
        btn = ctk.CTkButton(
            sidebar_frame,
            text="  " + text,
            font=font_base,
            fg_color="transparent",
            text_color=color_texto,
            hover_color=color_input,
            anchor="w",
            height=45,
            corner_radius=8,
            image=icons.get(icon_key),
            command=lambda: show_view(view_name)
        )
        btn.pack(fill="x", padx=15, pady=5)
        return btn

    nav_btn("Chat / Historial", "chat", "chat")
    nav_btn("Administración", "admin", "admin")

    # Nuevas secciones
    ctk.CTkLabel(sidebar_frame, text="EXTENSIONES", font=("Segoe UI", 12, "bold"), text_color=color_texto_oscuro).pack(anchor="w", padx=25, pady=(20, 5))
    nav_btn("Bienestar", "wellness", "wellness")
    nav_btn("Financiero", "finance", "finance")

    # --- MAIN CONTENT ---
    content_area = ctk.CTkFrame(main_container, fg_color=color_fondo_main, corner_radius=0)
    # Empacar el content area al lado izquierdo (o derecho del sidebar) pero permitiendo que el right_sidebar ocupe su lugar a la derecha.
    # Dado que right_sidebar es empaquetado y desempaquetado con side="right", content_area debe empaquetarse con side="left" para tomar todo el espacio sobrante en medio.
    content_area.pack(side="left", fill="both", expand=True)

    # Top Bar (Botón Toggle Izquierdo y Derecho)
    top_bar = ctk.CTkFrame(content_area, fg_color=color_fondo_main, height=60, corner_radius=0)
    top_bar.pack(side="top", fill="x")

    btn_toggle_left = ctk.CTkButton(
        top_bar,
        text="",
        image=icons.get("menu"),
        width=40,
        height=40,
        fg_color="transparent",
        hover_color=color_input,
        command=toggle_sidebar
    )
    btn_toggle_left.pack(side="left", padx=20, pady=10)

    btn_toggle_right = ctk.CTkButton(
        top_bar,
        text="Terminal / Logs",
        font=font_bold,
        fg_color=color_input,
        hover_color=color_acento,
        text_color=color_texto,
        width=140,
        height=40,
        corner_radius=8,
        command=toggle_right_sidebar
    )
    btn_toggle_right.pack(side="right", padx=20, pady=10)

    # Contenedor de Vistas
    view_container = ctk.CTkFrame(content_area, fg_color="transparent")
    view_container.pack(fill="both", expand=True, padx=30, pady=(0, 30))

    # --- VISTA 1: CHAT (Default) ---
    chat_view = ctk.CTkFrame(view_container, fg_color="transparent")
    views["chat"] = chat_view

    # Historial de Chat
    chat_history_frame = ctk.CTkFrame(chat_view, fg_color=color_input, corner_radius=12)
    chat_history_frame.pack(fill="both", expand=True, pady=(0, 20))

    # Usamos ctk.CTkTextbox que ya tiene scroll integrado
    chat_history_text = ctk.CTkTextbox(
        chat_history_frame,
        font=font_base,
        fg_color="transparent",
        text_color=color_texto,
        wrap="word"
    )
    chat_history_text.pack(fill="both", expand=True, padx=15, pady=15)

    # Tags configurables en CTkTextbox
    # En CustomTkinter no se permite cambiar font via tag_config por compatibilidad de escalado
    chat_history_text.tag_config("user", foreground="#FFFFFF")
    chat_history_text.tag_config("bot_name", foreground=color_nombre_bot)
    chat_history_text.tag_config("bot_text", foreground="#FFFFFF")
    chat_history_text.tag_config("system", foreground=color_texto_oscuro)
    chat_history_text.configure(state="disabled")

    # Mini-Panel de Acceso Rápido (Oculto por defecto)
    global quick_panel_frame
    quick_panel_frame = ctk.CTkFrame(chat_view, fg_color=color_input, corner_radius=12, height=220)

    # Cabecera del panel para título y botón de cierre
    panel_header = ctk.CTkFrame(quick_panel_frame, fg_color="transparent")
    panel_header.pack(fill="x", padx=10, pady=(10, 0))
    ctk.CTkLabel(panel_header, text="Comandos Rápidos", font=("Segoe UI", 16, "bold"), text_color=color_texto).pack(side="left")
    ctk.CTkButton(panel_header, text="X", font=("Segoe UI", 16, "bold"), fg_color="transparent", hover_color="#444444", text_color=color_texto, width=30, height=30, command=toggle_quick_panel).pack(side="right")

    # Pestañas
    tabview_cmds = ctk.CTkTabview(quick_panel_frame, fg_color="transparent", text_color=color_texto, segmented_button_fg_color=color_fondo_main, segmented_button_selected_color=color_acento, segmented_button_selected_hover_color=color_acento_hover)
    tabview_cmds.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    tabview_cmds.add("Limpieza")
    tabview_cmds.add("Administración")
    tabview_cmds.add("Entretenimiento")
    tabview_cmds.add("Bienestar")

    # Función auxiliar para crear botones dentro del tabview
    # Ahora ejecuta los comandos localmente usando las herramientas directas.
    # Para añadir nuevos botones:
    # 1. Asegúrate de que la herramienta exista en herramientas.py (en su diccionario herramientas_permitidas).
    # 2. Pasa los argumentos necesarios como un diccionario en `args`.
    def create_cmd_btn(parent, text, herramienta, args=None):
        if args is None:
            args = {}
        btn = ctk.CTkButton(
            parent,
            text=text,
            font=font_base,
            fg_color=color_fondo_main,
            hover_color=color_acento,
            text_color=color_texto,
            height=40,
            corner_radius=8,
            command=lambda h=herramienta, a=args, t=text: threading.Thread(
                target=ejecutar_comando_local, args=(t, h, a), daemon=True
            ).start()
        )
        return btn

    # Limpieza
    frame_limpieza = ctk.CTkScrollableFrame(tabview_cmds.tab("Limpieza"), fg_color="transparent", orientation="horizontal", height=80)
    frame_limpieza.pack(fill="both", expand=True)
    create_cmd_btn(frame_limpieza, "Vaciar papelera", "vaciar_papelera").pack(side="left", padx=10, pady=10)
    create_cmd_btn(frame_limpieza, "Limpiar escritorio", "limpiar_escritorio").pack(side="left", padx=10, pady=10)

    # Administración
    frame_admin = ctk.CTkScrollableFrame(tabview_cmds.tab("Administración"), fg_color="transparent", orientation="horizontal", height=80)
    frame_admin.pack(fill="both", expand=True)
    create_cmd_btn(frame_admin, "Apagar en 1 hora", "apagar_pc_tiempo", {"minutos": 60}).pack(side="left", padx=10, pady=10)
    create_cmd_btn(frame_admin, "Mostrar Estado", "mostrar_estado_bot").pack(side="left", padx=10, pady=10)

    # Entretenimiento
    frame_ent = ctk.CTkScrollableFrame(tabview_cmds.tab("Entretenimiento"), fg_color="transparent", orientation="horizontal", height=80)
    frame_ent.pack(fill="both", expand=True)
    create_cmd_btn(frame_ent, "Abrir YouTube", "abrir_youtube").pack(side="left", padx=10, pady=10)

    # Bienestar
    frame_bienestar = ctk.CTkScrollableFrame(tabview_cmds.tab("Bienestar"), fg_color="transparent", orientation="horizontal", height=80)
    frame_bienestar.pack(fill="both", expand=True)
    create_cmd_btn(frame_bienestar, "Modo Concentración", "gestionar_notificaciones", {"estado": "off"}).pack(side="left", padx=10, pady=10)
    create_cmd_btn(frame_bienestar, "Silenciar PC", "silenciar_pc").pack(side="left", padx=10, pady=10)

    # Input Box
    global input_frame
    input_frame = ctk.CTkFrame(chat_view, fg_color="transparent")
    input_frame.pack(fill="x")

    btn_quick_actions = ctk.CTkButton(
        input_frame,
        text="+",
        font=("Segoe UI", 24, "bold"),
        fg_color=color_input,
        hover_color=color_acento,
        text_color=color_acento,
        height=50,
        width=50,
        corner_radius=12,
        image=icons.get("plus"),
        command=lambda: toggle_quick_panel()
    )
    btn_quick_actions.pack(side="left", padx=(0, 10))

    chat_entry = ctk.CTkEntry(
        input_frame,
        font=font_base,
        fg_color=color_input,
        text_color="#FFFFFF",
        border_width=1,
        border_color="#333333",
        height=50,
        corner_radius=12,
        placeholder_text="Escribe un comando a Salomé..."
    )
    chat_entry.pack(side="left", fill="x", expand=True, padx=(0, 15))
    root.chat_entry = chat_entry

    def on_enter(event=None):
        texto = chat_entry.get()
        if texto:
            chat_entry.delete(0, tk.END)
            threading.Thread(target=procesar_orden_texto, args=(texto,), daemon=True).start()

    chat_entry.bind("<Return>", on_enter)

    btn_send = ctk.CTkButton(
        input_frame,
        text="Enviar",
        font=font_bold,
        fg_color=color_acento,
        hover_color=color_acento_hover,
        text_color="#FFFFFF",
        height=50,
        width=120,
        corner_radius=12,
        image=icons.get("send"),
        command=on_enter
    )
    btn_send.pack(side="right")


    # --- VISTA 3: ADMINISTRACIÓN ---
    admin_view = ctk.CTkFrame(view_container, fg_color="transparent")
    views["admin"] = admin_view
    lbl_admin = ctk.CTkLabel(admin_view, text="Panel de Administración", font=font_title, text_color=color_texto)
    lbl_admin.pack(pady=(0, 20), anchor="w")

    lbl_admin_info = ctk.CTkLabel(
        admin_view,
        text="Módulo en desarrollo.\nAquí se configurarán parámetros del sistema y del agente.",
        font=font_base,
        text_color=color_texto,
        justify="left"
    )
    lbl_admin_info.pack(anchor="w")

    # --- VISTA 4: BIENESTAR ---
    wellness_view = ctk.CTkFrame(view_container, fg_color="transparent")
    views["wellness"] = wellness_view
    lbl_wellness = ctk.CTkLabel(wellness_view, text="Panel de Bienestar", font=font_title, text_color=color_texto)
    lbl_wellness.pack(pady=(0, 20), anchor="w")

    # Temporizador Pomodoro
    pomodoro_frame = ctk.CTkFrame(wellness_view, fg_color=color_input, corner_radius=15)
    pomodoro_frame.pack(fill="x", pady=10, padx=20)

    ctk.CTkLabel(pomodoro_frame, text="Temporizador Pomodoro", font=font_bold, text_color=color_texto).pack(pady=10)

    lbl_pomodoro_time = ctk.CTkLabel(pomodoro_frame, text="25:00", font=("Segoe UI", 48, "bold"), text_color=color_acento)
    lbl_pomodoro_time.pack(pady=20)

    # Variables de estado del Pomodoro
    pomodoro_running = {"state": False}
    pomodoro_time = {"seconds": 25 * 60} # 25 minutos

    def update_pomodoro():
        if pomodoro_running["state"] and pomodoro_time["seconds"] > 0:
            pomodoro_time["seconds"] -= 1
            mins, secs = divmod(pomodoro_time["seconds"], 60)
            lbl_pomodoro_time.configure(text=f"{mins:02d}:{secs:02d}")
            root.after(1000, update_pomodoro)
        elif pomodoro_time["seconds"] == 0:
            pomodoro_running["state"] = False
            print("¡Tiempo de Pomodoro terminado!")
            # Opcional: mostrar notificación o reproducir sonido
            pomodoro_time["seconds"] = 25 * 60 # Reset

    def start_pomodoro():
        if not pomodoro_running["state"]:
            pomodoro_running["state"] = True
            update_pomodoro()

    def pause_pomodoro():
        pomodoro_running["state"] = False

    def reset_pomodoro():
        pomodoro_running["state"] = False
        pomodoro_time["seconds"] = 25 * 60
        lbl_pomodoro_time.configure(text="25:00")

    btn_frame = ctk.CTkFrame(pomodoro_frame, fg_color="transparent")
    btn_frame.pack(pady=10)
    ctk.CTkButton(btn_frame, text="Iniciar", font=font_base, fg_color=color_acento, hover_color=color_acento_hover, width=100, command=start_pomodoro).pack(side="left", padx=10)
    ctk.CTkButton(btn_frame, text="Pausar", font=font_base, fg_color="#555555", hover_color="#777777", width=100, command=pause_pomodoro).pack(side="left", padx=10)
    ctk.CTkButton(btn_frame, text="Reiniciar", font=font_base, fg_color="#555555", hover_color="#777777", width=100, command=reset_pomodoro).pack(side="left", padx=10)

    # --- VISTA 5: FINANCIERO ---
    finance_view = ctk.CTkFrame(view_container, fg_color="transparent")
    views["finance"] = finance_view
    lbl_finance = ctk.CTkLabel(finance_view, text="Panel Financiero", font=font_title, text_color=color_texto)
    lbl_finance.pack(pady=(0, 20), anchor="w")

    # Placeholder para APIs Crypto
    crypto_frame = ctk.CTkFrame(finance_view, fg_color=color_input, corner_radius=15)
    crypto_frame.pack(fill="both", expand=True, pady=10, padx=20)

    ctk.CTkLabel(crypto_frame, text="Mercado de Criptomonedas", font=font_bold, text_color=color_texto).pack(pady=20)
    ctk.CTkLabel(
        crypto_frame,
        text="[Espacio reservado para integración de APIs de Crypto]\nPróximamente se mostrarán aquí los precios en tiempo real.",
        font=font_base,
        text_color=color_texto_oscuro,
        justify="center"
    ).pack(expand=True)

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
