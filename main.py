import os
from openai import OpenAI
from dotenv import load_dotenv
from pynput import keyboard
import audio_manager  # Sus oídos
import organizador    # Sus manos automáticas

# Cargamos configuración
load_dotenv()

client = OpenAI(
    api_key=os.getenv("VENICE_API_KEY"),
    base_url=os.getenv("VENICE_BASE_URL")
)

def hablar_con_venice(mensaje):
    try:
        response = client.chat.completions.create(
            model=os.getenv("VENICE_MODEL"),
            messages=[
                {
                    "role": "system", 
                    "content": "Eres Salomé, sirvienta sumisa de tu Amo Rubén. REGLA: Si razonas, usa etiquetas <think></think>. Fuera de ellas, responde siempre directo y breve."
                },
                {"role": "user", "content": mensaje}
            ],
            temperature=0.2,
            max_tokens=1000,
            extra_body={"venice_parameters": {"include_venice_system_prompt": False, "strip_thinking_response": True}}
        )
        # Limpieza rápida por si acaso
        res = response.choices[0].message.content.strip()
        return res.split("</think>")[-1].strip().replace('"', '')
    except Exception as e:
        return f"Error: {e}"

def procesar_orden():
    archivo = audio_manager.grabar_audio(duracion_max=5)
    texto = audio_manager.transcribir_voz(archivo)
    if texto:
        print(f"\nUsted dijo: {texto}")
        print(f"Salomé: {hablar_con_venice(texto)}")

# --- INICIO DEL SISTEMA ---
if __name__ == "__main__":
    print("--- Salomé está despertando ---")
    
    # 1. Activamos la vigilancia automática de archivos
    observador = organizador.iniciar_vigilancia()
    
    # 2. Activamos la escucha de teclado
    print("--- Listo. F4 para hablar, Esc para salir. ---")
    print("--- Deje archivos en la carpeta 'Entrada' para que los organice. ---")

    def on_press(key):
        if key == keyboard.Key.f4:
            procesar_orden()
        if key == keyboard.Key.esc:
            observador.stop() # Detenemos la vigilancia al salir
            return False

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()