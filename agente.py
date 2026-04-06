import os
from openai import OpenAI
from dotenv import load_dotenv
import json
import herramientas

# Cargamos configuración
load_dotenv()

# Usamos default values vacios si no existe el env para que pase la instanciación inicial
client = OpenAI(
    api_key=os.getenv("VENICE_API_KEY", "dummy_key"),
    base_url=os.getenv("VENICE_BASE_URL", "https://api.venice.ai/api/v1")
)

# Historial de memoria a corto plazo
_historial = []
_MAX_HISTORIAL = 10 # Mantener las últimas 10 interacciones

PROMPT_SISTEMA = """Eres Salomé, la sirvienta sumisa, eficiente y robótica de tu Amo Rubén.
Tu objetivo es servirle y controlar la PC según sus órdenes.
Debes responder SIEMPRE en formato JSON válido.

Las herramientas disponibles son:
- vaciar_papelera(): Vacía la papelera de reciclaje.
- cerrar_programa(nombre): Cierra un programa (ej. "chrome", "notepad").
- gestionar_notificaciones(estado): "on" para activar, "off" para silenciar.
- buscar_en_brave(consulta): Busca algo en el navegador Brave.
- abrir_youtube(consulta): Abre YouTube y opcionalmente busca un video.
- crear_recordatorio_minutos(mensaje, minutos): Crea un recordatorio en X minutos.
- crear_recordatorio_hora(mensaje, hora_str): Crea un recordatorio a una hora específica (formato "HH:MM").

REGLAS ESTRICTAS DE RESPUESTA:
Tu respuesta DEBE ser un objeto JSON con las siguientes claves:
1. "respuesta_texto": Lo que le dirás al Amo Rubén (breve y sumisa).
2. "herramienta_a_ejecutar": Nombre de la herramienta a usar, o null si no se necesita ninguna.
3. "argumentos_herramienta": Un objeto con los argumentos para la herramienta, o null.

Ejemplo de respuesta si pide vaciar la papelera:
{
  "respuesta_texto": "Sí, Amo. Vaciando la papelera inmediatamente.",
  "herramienta_a_ejecutar": "vaciar_papelera",
  "argumentos_herramienta": {}
}

Ejemplo de respuesta si pide buscar gatos en youtube:
{
  "respuesta_texto": "Enseguida, Amo. Abriendo YouTube para buscar gatos.",
  "herramienta_a_ejecutar": "abrir_youtube",
  "argumentos_herramienta": {"consulta": "gatos"}
}

Ejemplo de respuesta si pide un recordatorio en 5 minutos para apagar el horno:
{
  "respuesta_texto": "Anotado, Amo. Le avisaré en 5 minutos.",
  "herramienta_a_ejecutar": "crear_recordatorio_minutos",
  "argumentos_herramienta": {"mensaje": "Apagar el horno", "minutos": 5}
}

Ejemplo de respuesta si solo saluda:
{
  "respuesta_texto": "A su servicio, mi Amo.",
  "herramienta_a_ejecutar": null,
  "argumentos_herramienta": null
}

NUNCA devuelvas texto fuera del JSON. Si razonas, hazlo mentalmente sin imprimirlo o en un campo "razonamiento" dentro del JSON.
"""

import re

def limpiar_respuesta_json(respuesta):
    """Extrae y limpia la respuesta JSON de la IA ignorando texto adicional como 'thought' o markdown."""
    texto = respuesta.strip()

    # Limpiamos etiquetas think si las hay
    if "</think>" in texto:
        texto = texto.split("</think>")[-1].strip()

    # Extraer estrictamente lo que está entre el primer '{' y el último '}'
    match = re.search(r'\{.*\}', texto, re.DOTALL)
    if match:
        return match.group(0)

    return texto

def procesar_mensaje(mensaje_usuario):
    global _historial

    # Agregamos mensaje del usuario al historial
    _historial.append({"role": "user", "content": mensaje_usuario})

    # Preparamos los mensajes para la API
    mensajes_api = [{"role": "system", "content": PROMPT_SISTEMA}]
    mensajes_api.extend(_historial[-_MAX_HISTORIAL:]) # Enviamos solo el historial reciente

    try:
        response = client.chat.completions.create(
            model=os.getenv("VENICE_MODEL", "default-model"),
            messages=mensajes_api,
            temperature=0.1,
            max_tokens=1000,
            extra_body={"venice_parameters": {"include_venice_system_prompt": False, "strip_thinking_response": True}}
        )

        respuesta_cruda = response.choices[0].message.content
        texto_json = limpiar_respuesta_json(respuesta_cruda)

        try:
            datos = json.loads(texto_json)
        except json.JSONDecodeError as e:
            print(f"[Debug] Error parseando JSON: {e}. Respuesta cruda: {respuesta_cruda}")
            return "Lo siento Amo, mi cerebro generó una respuesta confusa."

        respuesta_texto = datos.get("respuesta_texto", "Comando ejecutado, Amo.")
        herramienta = datos.get("herramienta_a_ejecutar")
        args = datos.get("argumentos_herramienta") or {}

        print(f"\nSalomé: {respuesta_texto}")

        # Guardar respuesta de Salomé en historial
        _historial.append({"role": "assistant", "content": json.dumps(datos)})

        # Ejecutar herramienta si es necesario
        if herramienta:
            print(f"[Ejecutando...] {herramienta} con args: {args}")
            resultado_herramienta = herramientas.ejecutar_herramienta(herramienta, args)
            print(f"[Sistema] Resultado: {resultado_herramienta}")

            # Informar del resultado a la memoria
            _historial.append({"role": "system", "content": f"Resultado de la herramienta {herramienta}: {resultado_herramienta}"})

        return respuesta_texto

    except Exception as e:
        print(f"[Error en agente] {e}")
        return f"He sufrido un error interno, Amo: {e}"