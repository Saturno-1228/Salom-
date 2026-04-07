import os
import sys
import threading
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import logging

import audio_manager  # Sus oídos
import organizador    # Sus manos automáticas
import agente         # Su nuevo cerebro

app = Flask(__name__)
app.config['SECRET_KEY'] = 'salome_secret_key'
socketio = SocketIO(app, async_mode='eventlet')

# Deshabilitar logs de werkzeug para no saturar
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class SocketIORedirector:
    """Redirige sys.stdout a los logs de la Web UI"""
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout

    def write(self, string):
        self.original_stdout.write(string)
        if string.strip():
            socketio.emit('log_message', {'text': string})

    def flush(self):
        self.original_stdout.flush()

# Guardamos el original
original_stdout = sys.stdout
# sys.stdout = SocketIORedirector(original_stdout) # Activamos si queremos logs en la web
# sys.stderr = SocketIORedirector(sys.stderr)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('text_message')
def handle_text_message(data):
    texto = data.get('text', '')
    if texto.strip():
        # Usar el agente para procesar el comando de texto
        def tarea():
            try:
                respuesta = agente.procesar_mensaje(texto)
                if respuesta:
                    socketio.emit('bot_response', {'text': respuesta})
                else:
                    socketio.emit('bot_response', {'text': "He procesado la orden, pero no tengo una respuesta verbal."})
            except Exception as e:
                socketio.emit('system_message', {'text': f"Error procesando: {e}"})

        socketio.start_background_task(tarea)

@socketio.on('start_audio')
def handle_start_audio():
    audio_manager.iniciar_grabacion()

@socketio.on('stop_audio')
def handle_stop_audio():
    def tarea():
        archivo = audio_manager.detener_grabacion()
        if not archivo:
            socketio.emit('system_message', {'text': "No se detectó audio."})
            return

        socketio.emit('system_message', {'text': "Transcribiendo..."})
        texto = audio_manager.transcribir_voz(archivo)
        if texto:
            socketio.emit('system_message', {'text': f"Transcripción: {texto}"})
            # Procesar el texto como si se hubiera escrito
            try:
                respuesta = agente.procesar_mensaje(texto)
                if respuesta:
                    socketio.emit('bot_response', {'text': respuesta})
                else:
                    socketio.emit('bot_response', {'text': "He procesado la orden, pero no tengo una respuesta."})
            except Exception as e:
                socketio.emit('system_message', {'text': f"Error procesando: {e}"})
        else:
            socketio.emit('system_message', {'text': "No pude entender el audio."})

    socketio.start_background_task(tarea)

def iniciar_servidor():
    print("--- Iniciando Gateway Dashboard en http://127.0.0.1:18789 ---")
    # Utilizamos eventlet que es compatible con async de SocketIO y Windows
    socketio.run(app, host='127.0.0.1', port=18789)

# --- INICIO DEL SISTEMA ---
if __name__ == "__main__":
    print("--- Salomé está despertando (Modo Web Gateway) ---")
    
    # 1. Organizamos los archivos existentes primero
    try:
        organizador.organizar_archivos_existentes()
    except Exception as e:
        print(f"Error inicializando organizador: {e}")

    # 2. Activamos la vigilancia automática de archivos
    observador = None
    try:
        observador = organizador.iniciar_vigilancia()
    except Exception as e:
        print(f"Error iniciando vigilancia: {e}")
    
    print("--- Listo. Abra http://127.0.0.1:18789 en su navegador ---")
    print("--- Presione Ctrl+C en esta terminal para apagar el sistema. ---")

    # Iniciar el servidor web
    try:
        iniciar_servidor()
    except KeyboardInterrupt:
        pass
    finally:
        print("\nApagando a Salomé...")
        if observador:
            observador.stop()
