import os
import sys
import threading
import queue
import customtkinter as ctk
from PIL import Image
from pynput import keyboard
import agente
import audio_manager
import organizador
import recordatorios

# --- COMENTARIO PARA FUTURAS MEJORAS ---
# CustomTkinter es nativo, pero puede ser propenso a bloqueos de UI si hacemos
# llamadas pesadas en el hilo principal. Mantener el uso de .after() y colas
# para cualquier función que interactúe con el Agente (LLM) o el Micrófono.
# La estructura de la GUI es modular, para agregar nuevas ventanas, usar Toplevel().

# Configuración Inicial de Tema (Glamour-Noir)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Configuración de fuente y colores globales
FONT_FAMILY = "Segoe UI"
BG_COLOR_APP = "#0f1115"
BG_COLOR_USER = "#FFD1DC"
FG_COLOR_USER = "#000000"
BG_COLOR_BOT = "#1A1A1A"
FG_COLOR_BOT = "#FFFFFF"

class SalomeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Salomé")
        self.geometry("450x700")
        self.configure(fg_color=BG_COLOR_APP)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Cola para comunicación entre hilos y la UI
        self.ui_queue = queue.Queue()

        self._build_ui()
        self.after(100, self._process_ui_queue)
        self.after(1000, self._start_services)

        # Estado de grabación y listener del teclado
        self.is_recording = False
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.keyboard_listener.start()

    def _build_ui(self):
        # Frame principal que contendrá el chat y la entrada
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Chat (Scrollable Frame)
        self.chat_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.chat_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self.chat_frame.grid_columnconfigure(0, weight=1)

        # Frame de Entrada (Bottom)
        self.input_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=50)
        self.input_frame.grid(row=1, column=0, sticky="ew")
        self.input_frame.grid_columnconfigure(1, weight=1)

        # Botón Drawer (+)
        self.btn_drawer = ctk.CTkButton(
            self.input_frame,
            text="+",
            width=40,
            corner_radius=20,
            fg_color="#374151",
            hover_color="#4b5563",
            font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"),
            command=self.toggle_drawer
        )
        self.btn_drawer.grid(row=0, column=0, padx=(0, 10))

        # Input de texto
        self.entry_var = ctk.StringVar()
        self.entry = ctk.CTkEntry(
            self.input_frame,
            textvariable=self.entry_var,
            placeholder_text="Escribe a Salomé...",
            height=40,
            corner_radius=20,
            border_color="#2d3039",
            fg_color="#16181d",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14)
        )
        self.entry.grid(row=0, column=1, sticky="ew")
        self.entry.bind("<Return>", lambda event: self.send_message())

        # Botón Enviar (Flecha)
        self.btn_send = ctk.CTkButton(
            self.input_frame,
            text="➤",
            width=40,
            height=40,
            corner_radius=20,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            font=ctk.CTkFont(size=20),
            command=self.send_message
        )
        self.btn_send.grid(row=0, column=2, padx=(10, 0))

        # Inicialización del Menú Drawer (oculto por defecto)
        self.drawer_visible = False
        self.drawer_frame = None

        # Saludo inicial
        self.add_message("Conexión establecida. Salomé lista.", is_user=False, is_system=True)

    def toggle_drawer(self):
        if self.drawer_visible:
            if self.drawer_frame:
                self.drawer_frame.place_forget()
            self.drawer_visible = False
        else:
            self._show_drawer()
            self.drawer_visible = True

    def _show_drawer(self):
        if not self.drawer_frame:
            # Crear el drawer flotante sobre la UI
            self.drawer_frame = ctk.CTkFrame(self, fg_color="#16181d", corner_radius=15, border_width=1, border_color="#2d3039")

            # Usar Tabview
            self.tabview = ctk.CTkTabview(self.drawer_frame, fg_color="transparent")
            self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

            self.tabview.add(" Limpieza ")
            self.tabview.add(" Admin ")
            self.tabview.add(" Bienestar ")

            # Limpieza
            ctk.CTkButton(self.tabview.tab(" Limpieza "), text="🗑️ Vaciar Papelera", anchor="w", fg_color="#1f2937", hover_color="#374151", font=ctk.CTkFont(family=FONT_FAMILY, size=14), command=lambda: self._cmd_from_drawer("vaciar papelera")).pack(fill="x", pady=5)
            ctk.CTkButton(self.tabview.tab(" Limpieza "), text="🧹 Limpiar Escritorio", anchor="w", fg_color="#1f2937", hover_color="#374151", font=ctk.CTkFont(family=FONT_FAMILY, size=14), command=lambda: self._cmd_from_drawer("limpiar escritorio")).pack(fill="x", pady=5)

            # Admin
            ctk.CTkButton(self.tabview.tab(" Admin "), text="🩺 Reporte de Salud", anchor="w", fg_color="#1f2937", hover_color="#374151", font=ctk.CTkFont(family=FONT_FAMILY, size=14), command=lambda: self._cmd_from_drawer("reporte de salud")).pack(fill="x", pady=5)
            ctk.CTkButton(self.tabview.tab(" Admin "), text="📊 Procesos Pesados", anchor="w", fg_color="#1f2937", hover_color="#374151", font=ctk.CTkFont(family=FONT_FAMILY, size=14), command=lambda: self._cmd_from_drawer("listar procesos pesados")).pack(fill="x", pady=5)
            ctk.CTkButton(self.tabview.tab(" Admin "), text="🔄 Actualizar Bot", anchor="w", fg_color="#1f2937", hover_color="#374151", font=ctk.CTkFont(family=FONT_FAMILY, size=14), command=lambda: self._cmd_from_drawer("actualizar bot")).pack(fill="x", pady=5)

            # Bienestar
            ctk.CTkButton(self.tabview.tab(" Bienestar "), text="🛑 Modo Pánico", anchor="w", fg_color="#ef4444", hover_color="#dc2626", text_color="white", font=ctk.CTkFont(family=FONT_FAMILY, size=14), command=lambda: self._cmd_from_drawer("modo pánico")).pack(fill="x", pady=5)

        # Posicionar el drawer encima del input frame.
        # Ajustamos `relx`, `rely` para colocarlo arriba del input.
        # place(relx=0.05, rely=0.5, relwidth=0.9, relheight=0.4, anchor="sw")
        # El anchor 'sw' (South-West) significa que la coordenada Y=1.0 es el fondo.
        self.update_idletasks() # Asegurar dimensiones
        self.drawer_frame.configure(height=250)
        self.drawer_frame.place(relx=0.05, rely=0.88, relwidth=0.9, anchor="sw")

    def _cmd_from_drawer(self, cmd):
        self.toggle_drawer() # Cerrar el drawer
        self.entry_var.set(cmd)
        self.send_message()

    def add_message(self, text, is_user=False, is_system=False):
        # Crear contenedor para el mensaje
        msg_container = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        msg_container.pack(fill="x", pady=5)

        if is_system:
            lbl = ctk.CTkLabel(
                msg_container,
                text=text,
                text_color="#9ca3af",
                font=ctk.CTkFont(family=FONT_FAMILY, slant="italic", size=14),
                justify="center"
            )
            lbl.pack(anchor="center")
            return

        # Burbuja de mensaje
        bubble_color = BG_COLOR_USER if is_user else BG_COLOR_BOT
        text_color = FG_COLOR_USER if is_user else FG_COLOR_BOT
        anchor = "e" if is_user else "w"

        bubble = ctk.CTkFrame(msg_container, fg_color=bubble_color, corner_radius=20)
        bubble.pack(anchor=anchor, padx=10)

        # Label dentro de la burbuja. Wraplength asume un ancho maximo aprox.
        lbl = ctk.CTkLabel(
            bubble,
            text=text,
            text_color=text_color,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14),
            justify="left",
            wraplength=280
        )
        lbl.pack(padx=15, pady=10)

        # Auto-scroll
        self.chat_frame._parent_canvas.yview_moveto(1.0)

    def send_message(self):
        text = self.entry_var.get().strip()
        if not text:
            return

        self.add_message(text, is_user=True)
        self.entry_var.set("")

        # Deshabilitar input temporalmente
        self.entry.configure(state="disabled")
        self.btn_send.configure(state="disabled")

        # Procesar en un hilo separado
        threading.Thread(target=self._process_message_thread, args=(text,), daemon=True).start()

    def _process_message_thread(self, text):
        try:
            respuesta = agente.procesar_mensaje(text)
            self.ui_queue.put({"type": "bot_response", "text": respuesta})
        except Exception as e:
            self.ui_queue.put({"type": "system_message", "text": f"Error procesando: {e}"})

    def _process_ui_queue(self):
        try:
            while True:
                msg = self.ui_queue.get_nowait()
                if msg["type"] == "bot_response":
                    self.add_message(msg["text"], is_user=False)
                    self.entry.configure(state="normal")
                    self.btn_send.configure(state="normal")
                    self.entry.focus()
                elif msg["type"] == "system_message":
                    self.add_message(msg["text"], is_system=True)
                elif msg["type"] == "update_mic_state":
                    # Cambiar el color del borde del input para indicar que estamos grabando
                    if msg["active"]:
                        self.entry.configure(border_color="#ef4444") # Rojo
                    else:
                        self.entry.configure(border_color="#2d3039") # Normal
                elif msg["type"] == "send_transcribed_message":
                    # Simular envío de mensaje desde la transcripción
                    self.entry_var.set(msg["text"])
                    self.send_message()
        except queue.Empty:
            pass
        finally:
            self.after(100, self._process_ui_queue)

    def _start_services(self):
        # 1. Organizamos los archivos existentes primero
        try:
            organizador.organizar_archivos_existentes()
        except Exception as e:
            self.add_message(f"Error inicializando organizador: {e}", is_system=True)

        # 2. Activamos la vigilancia automática de archivos
        try:
            self.observador = organizador.iniciar_vigilancia()
        except Exception as e:
            self.add_message(f"Error iniciando vigilancia: {e}", is_system=True)

    def _on_key_press(self, key):
        if key == keyboard.Key.ctrl_r and not self.is_recording:
            self.is_recording = True
            self.ui_queue.put({"type": "system_message", "text": "🎤 Grabando... Hable ahora."})
            self.ui_queue.put({"type": "update_mic_state", "active": True})
            # Iniciar grabación (audio_manager maneja sus propios hilos/estado)
            audio_manager.iniciar_grabacion()

    def _on_key_release(self, key):
        if key == keyboard.Key.ctrl_r and self.is_recording:
            self.is_recording = False
            self.ui_queue.put({"type": "update_mic_state", "active": False})
            self.ui_queue.put({"type": "system_message", "text": "Procesando audio..."})

            # Detener y procesar en un hilo separado para no bloquear UI ni el listener de teclado
            threading.Thread(target=self._process_audio_thread, daemon=True).start()

    def _process_audio_thread(self):
        try:
            archivo = audio_manager.detener_grabacion()
            if not archivo:
                self.ui_queue.put({"type": "system_message", "text": "No se detectó audio."})
                return

            self.ui_queue.put({"type": "system_message", "text": "Transcribiendo..."})
            texto = audio_manager.transcribir_voz(archivo)

            if texto:
                self.ui_queue.put({"type": "system_message", "text": f"Transcripción: {texto}"})
                # Enviar el texto transcrito como si se hubiera escrito
                self.ui_queue.put({"type": "send_transcribed_message", "text": texto})
            else:
                self.ui_queue.put({"type": "system_message", "text": "No pude entender el audio."})
        except Exception as e:
            self.ui_queue.put({"type": "system_message", "text": f"Error procesando audio: {e}"})

    def on_closing(self):
        if hasattr(self, 'observador') and self.observador:
            self.observador.stop()
        if hasattr(self, 'keyboard_listener'):
            self.keyboard_listener.stop()
        self.destroy()

if __name__ == "__main__":
    app = SalomeApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
