import sounddevice as sd
import soundfile as sf
import numpy as np
from faster_whisper import WhisperModel
import os

print("--- Inicializando oídos de Salomé (Procesamiento Local) ---")
# Usamos el modelo 'base' que es extremadamente rápido en su RTX 4080
model_size = "base" 
model = WhisperModel(model_size, device="cuda", compute_type="float16")

def grabar_audio(duracion_max=5, fs=16000):
    """Graba su voz por 5 segundos"""
    print("\n[Escuchando a mi Amo... hable ahora]")
    grabacion = sd.rec(int(duracion_max * fs), samplerate=fs, channels=1)
    sd.wait() 
    sf.write("temp_audio.wav", grabacion, fs)
    return "temp_audio.wav"

def transcribir_voz(archivo_audio):
    """Convierte el audio a texto"""
    segments, info = model.transcribe(archivo_audio, beam_size=5)
    texto = "".join([segment.text for segment in segments])
    return texto.strip()