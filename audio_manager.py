import os

# Solución para Windows Python 3.8+: Cargar las DLLs de CUDA (cublas, cudnn) desde el entorno virtual (venv)
if os.name == 'nt':
    # Obtenemos la ruta base del entorno (site-packages) donde están instalados los paquetes de nvidia
    import site
    import glob

    # site.getsitepackages() nos da la lista de directorios de paquetes (normalmente site-packages)
    # Buscamos todas las carpetas 'nvidia/*/bin' dentro de site-packages para añadir sus DLLs
    for site_package_dir in site.getsitepackages():
        nvidia_bins = glob.glob(os.path.join(site_package_dir, 'nvidia', '*', 'bin'))
        for bin_dir in nvidia_bins:
            try:
                os.add_dll_directory(bin_dir)
            except Exception as e:
                pass # Ignorar si hay algún problema con un directorio específico

import sounddevice as sd
import soundfile as sf
import numpy as np
from faster_whisper import WhisperModel
import queue

print("--- Inicializando oídos de Salomé (Procesamiento Local) ---")
# Usamos el modelo 'base' que es extremadamente rápido.
# El usuario indicó que prefiere CPU para evitar errores con CUDA.
model_size = "base" 
model = WhisperModel(model_size, device="cpu", compute_type="int8")

_q = queue.Queue()
_recording = False
_stream = None
_fs = 16000

def _callback(indata, frames, time, status):
    if status:
        print(status, flush=True)
    _q.put(indata.copy())

def iniciar_grabacion():
    global _recording, _stream, _q, _fs
    if _recording:
        return
    print("\n[Escuchando a mi Amo... hable ahora]")
    # Vaciamos la cola por si hay audios viejos
    _q = queue.Queue()
    _recording = True
    _stream = sd.InputStream(samplerate=_fs, channels=1, callback=_callback)
    _stream.start()

def detener_grabacion():
    global _recording, _stream, _fs
    if not _recording:
        return None

    _stream.stop()
    _stream.close()
    _recording = False

    print("[Procesando audio...]")

    audio_data = []
    while not _q.empty():
        audio_data.append(_q.get())

    if not audio_data:
        return None

    grabacion = np.concatenate(audio_data, axis=0)
    archivo = "temp_audio.wav"
    sf.write(archivo, grabacion, _fs)
    return archivo

def transcribir_voz(archivo_audio):
    """Convierte el audio a texto"""
    if not archivo_audio or not os.path.exists(archivo_audio):
        return ""
    segments, info = model.transcribe(archivo_audio, beam_size=5)
    texto = "".join([segment.text for segment in segments])
    return texto.strip()