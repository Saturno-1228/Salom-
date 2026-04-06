import os
import sys
import tkinter as tk
import customtkinter as ctk
from PIL import Image
from pynput import keyboard
import threading
import audio_manager  # Sus oídos
import organizador    # Sus manos automáticas
import agente         # Su nuevo cerebro

# Configuración de CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")  # Tema oscuro por defecto

# --- VARIABLES GLOBALES PARA LA GUI ---
root = None
gui_visible = False
chat_history_text = None
icons = {}
terminal_text = None
quick_panel_frame = None
lbl_pomodoro_hud = None

# Variables de estado del Pomodoro
pomodoro_running = {"state": False}
pomodoro_time = {"seconds": 25 * 60} # 25 minutos

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
        # Si no existe mic_icon, usamos un recuadro o lo creamos
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
        elif role == "system":
            chat_history_text.insert(tk.END, f"[Sistema]: {text}\n\n", "system")
        chat_history_text.see(tk.END)
        chat_history_text.configure(state="disabled")

def update_pomodoro_hud():
    if lbl_pomodoro_hud:
        mins, secs = divmod(pomodoro_time["seconds"], 60)
        lbl_pomodoro_hud.configure(text=f"🍅 {mins:02d}:{secs:02d}")

def procesar_orden_audio():
    # Evitar bloqueos en GUI
    def tarea():
        archivo = audio_manager.detener_grabacion()
        if not archivo:
            root.after(0, update_chat_history, "system", "No se detectó audio.")
            return
        texto = audio_manager.transcribir_voz(archivo)
        if texto:
            root.after(0, procesar_orden_texto, texto)
        else:
            root.after(0, update_chat_history, "system", "No pude entender el audio.")

    threading.Thread(target=tarea, daemon=True).start()

def toggle_mic():
    # Asume que si ya estamos grabando, lo detenemos y procesamos
    if audio_manager._recording:
        root.btn_mic.configure(fg_color="#212121") # Color normal
        procesar_orden_audio()
    else:
        root.btn_mic.configure(fg_color="#C2185B") # Color grabando
        audio_manager.iniciar_grabacion()

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

def toggle_quick_panel():
    if quick_panel_frame.winfo_ismapped():
        quick_panel_frame.pack_forget()
    else:
        quick_panel_frame.pack(fill="both", expand=True, pady=(10, 10), before=input_frame)

def crear_gui():
    global root, gui_visible, chat_history_text, terminal_text, lbl_pomodoro_hud

    root = ctk.CTk()
    root.title("Salomé - Interfaz de Control")
    root.geometry("1100x800")

    load_icons()

    # Estética Pastel-Noir
    color_fondo_main = "#101010"    # Fondo Negro Profundo
    color_acento = "#FFD1DC"        # Rosa Pastel Suave
    color_acento_hover = "#F48FB1"
    color_nombre_bot = "#FFD1DC"
    color_texto = "#E0E0E0"
    color_texto_oscuro = "#A0A0A0"
    color_input = "#1A1A1A"         # Gris muy oscuro para cards
    font_base = ("Segoe UI", 18)
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

    # Top Bar con Título y HUD de Pomodoro
    top_bar = ctk.CTkFrame(main_container, fg_color="transparent", height=60, corner_radius=0)
    top_bar.pack(side="top", fill="x", padx=30, pady=(20, 0))

    lbl_title = ctk.CTkLabel(top_bar, text="SALOMÉ", font=("Segoe UI", 28, "bold"), text_color=color_nombre_bot)
    lbl_title.pack(side="left")

    lbl_pomodoro_hud = ctk.CTkLabel(top_bar, text="", font=("Segoe UI", 20, "bold"), text_color=color_acento)
    lbl_pomodoro_hud.pack(side="right")

    # Área Central
    content_area = ctk.CTkFrame(main_container, fg_color="transparent")
    content_area.pack(fill="both", expand=True, padx=30, pady=(10, 30))

    chat_view = ctk.CTkFrame(content_area, fg_color="transparent")
    chat_view.pack(fill="both", expand=True)

    # Historial de Chat
    chat_history_frame = ctk.CTkFrame(chat_view, fg_color=color_input, corner_radius=12)
    chat_history_frame.pack(fill="both", expand=True, pady=(0, 20))

    chat_history_text = ctk.CTkTextbox(
        chat_history_frame,
        font=font_base,
        fg_color="transparent",
        text_color=color_texto,
        wrap="word"
    )
    chat_history_text.pack(fill="both", expand=True, padx=15, pady=15)

    chat_history_text.tag_config("user", foreground="#FFFFFF")
    chat_history_text.tag_config("bot_name", foreground=color_nombre_bot)
    chat_history_text.tag_config("bot_text", foreground="#FFFFFF")
    chat_history_text.tag_config("system", foreground=color_texto_oscuro)
    chat_history_text.configure(state="disabled")

    # Command Drawer (Cajón de Herramientas)
    global quick_panel_frame
    quick_panel_frame = ctk.CTkFrame(chat_view, fg_color=color_input, corner_radius=12, height=350)

    panel_header = ctk.CTkFrame(quick_panel_frame, fg_color="transparent")
    panel_header.pack(fill="x", padx=10, pady=(10, 0))
    ctk.CTkLabel(panel_header, text="Cajón de Herramientas", font=("Segoe UI", 16, "bold"), text_color=color_acento).pack(side="left")
    ctk.CTkButton(panel_header, text="X", font=("Segoe UI", 16, "bold"), fg_color="transparent", hover_color="#333333", text_color=color_texto, width=30, height=30, command=toggle_quick_panel).pack(side="right")

    tabview_cmds = ctk.CTkTabview(quick_panel_frame, fg_color="transparent", text_color=color_texto, segmented_button_fg_color=color_fondo_main, segmented_button_selected_color=color_acento, segmented_button_selected_hover_color=color_acento_hover)
    tabview_cmds.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    tabview_cmds.add("Limpieza")
    tabview_cmds.add("Administración")
    tabview_cmds.add("Bienestar")
    tabview_cmds.add("Terminal (Logs)")

    def create_cmd_btn(parent, text, command_text):
        return ctk.CTkButton(
            parent,
            text=text,
            font=font_base,
            fg_color=color_fondo_main,
            hover_color=color_acento,
            text_color=color_texto,
            height=40,
            corner_radius=8,
            command=lambda c=command_text: [chat_entry.delete(0, tk.END), chat_entry.insert(0, c), on_enter()]
        )

    # Limpieza
    frame_limpieza = ctk.CTkScrollableFrame(tabview_cmds.tab("Limpieza"), fg_color="transparent")
    frame_limpieza.pack(fill="both", expand=True)
    create_cmd_btn(frame_limpieza, "Vaciar papelera", "vaciar papelera").pack(pady=5, padx=10, fill="x")
    create_cmd_btn(frame_limpieza, "Limpiar escritorio", "limpiar escritorio").pack(pady=5, padx=10, fill="x")

    # Administración
    frame_admin = ctk.CTkScrollableFrame(tabview_cmds.tab("Administración"), fg_color="transparent")
    frame_admin.pack(fill="both", expand=True)
    create_cmd_btn(frame_admin, "Reporte de Salud", "reporte de salud").pack(pady=5, padx=10, fill="x")
    create_cmd_btn(frame_admin, "Procesos Pesados", "listar procesos pesados").pack(pady=5, padx=10, fill="x")
    create_cmd_btn(frame_admin, "Actualizar Bot", "actualizar bot").pack(pady=5, padx=10, fill="x")

    # Bienestar y Pomodoro Integrado
    frame_bienestar = ctk.CTkScrollableFrame(tabview_cmds.tab("Bienestar"), fg_color="transparent")
    frame_bienestar.pack(fill="both", expand=True)
    create_cmd_btn(frame_bienestar, "Modo Pánico", "modo pánico").pack(pady=5, padx=10, fill="x")

    pomodoro_frame = ctk.CTkFrame(frame_bienestar, fg_color=color_fondo_main, corner_radius=8)
    pomodoro_frame.pack(fill="x", pady=10, padx=10)
    ctk.CTkLabel(pomodoro_frame, text="Pomodoro", font=font_bold, text_color=color_texto).pack(pady=(10, 0))
    lbl_pomodoro_time = ctk.CTkLabel(pomodoro_frame, text="25:00", font=("Segoe UI", 32, "bold"), text_color=color_acento)
    lbl_pomodoro_time.pack(pady=5)

    def update_pomodoro():
        if pomodoro_running["state"] and pomodoro_time["seconds"] > 0:
            pomodoro_time["seconds"] -= 1
            mins, secs = divmod(pomodoro_time["seconds"], 60)
            lbl_pomodoro_time.configure(text=f"{mins:02d}:{secs:02d}")
            update_pomodoro_hud()
            root.after(1000, update_pomodoro)
        elif pomodoro_time["seconds"] == 0:
            pomodoro_running["state"] = False
            update_pomodoro_hud()

    def start_pomodoro():
        if not pomodoro_running["state"]:
            pomodoro_running["state"] = True
            update_pomodoro()
            update_pomodoro_hud()

    def reset_pomodoro():
        pomodoro_running["state"] = False
        pomodoro_time["seconds"] = 25 * 60
        lbl_pomodoro_time.configure(text="25:00")
        update_pomodoro_hud()

    btn_pomo_frame = ctk.CTkFrame(pomodoro_frame, fg_color="transparent")
    btn_pomo_frame.pack(pady=(0, 10))
    ctk.CTkButton(btn_pomo_frame, text="▶", font=font_bold, width=40, command=start_pomodoro, fg_color=color_acento).pack(side="left", padx=5)
    ctk.CTkButton(btn_pomo_frame, text="⏹", font=font_bold, width=40, command=reset_pomodoro, fg_color="#333").pack(side="left", padx=5)

    # Terminal / Logs
    terminal_text = ctk.CTkTextbox(tabview_cmds.tab("Terminal (Logs)"), font=("Consolas", 14), fg_color=color_fondo_main, text_color=color_texto, wrap="word")
    terminal_text.pack(fill="both", expand=True)
    terminal_text.configure(state="disabled")
    sys.stdout = StdoutRedirector(terminal_text)
    sys.stderr = StdoutRedirector(terminal_text)

    # --- Input Area ---
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
        command=toggle_quick_panel
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
        placeholder_text="Escribe un comando o petición a Salomé..."
    )
    chat_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
    root.chat_entry = chat_entry

    def on_enter(event=None):
        texto = chat_entry.get()
        if texto:
            chat_entry.delete(0, tk.END)
            threading.Thread(target=procesar_orden_texto, args=(texto,), daemon=True).start()

    chat_entry.bind("<Return>", on_enter)

    # Micrófono Button
    root.btn_mic = ctk.CTkButton(
        input_frame,
        text="🎤",
        font=font_bold,
        fg_color=color_input,
        hover_color=color_acento,
        text_color=color_acento,
        height=50,
        width=50,
        corner_radius=12,
        command=toggle_mic
    )
    root.btn_mic.pack(side="left", padx=(0, 10))

    btn_send = ctk.CTkButton(
        input_frame,
        text="Enviar",
        font=font_bold,
        fg_color=color_acento,
        hover_color=color_acento_hover,
        text_color="#101010",
        height=50,
        width=100,
        corner_radius=12,
        command=on_enter
    )
    btn_send.pack(side="right")

    update_chat_history("system", "Amo Rubén, la Refactorización Pastel-Noir ha concluido.\n\nHe añadido el Escudo de Rubén (notificaciones y Pomodoro), nuevas herramientas de administración y búsqueda, e integrado el Command Drawer y mi micrófono.\nEstoy lista para servirle.")

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
