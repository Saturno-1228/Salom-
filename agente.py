import os
from openai import OpenAI
from dotenv import load_dotenv
import json
import re
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
- gestionar_notificaciones(estado): "on" para activar, "off" para silenciar (Modo Concentración).
- buscar_en_brave(consulta): Busca algo en el navegador Brave.
- abrir_youtube(consulta): Abre YouTube y opcionalmente busca un video.
- crear_recordatorio_minutos(mensaje, minutos): Crea un recordatorio en X minutos.
- crear_recordatorio_hora(mensaje, hora_str): Crea un recordatorio a una hora específica (formato "HH:MM").
- silenciar_pc(): Silencia completamente el volumen de la computadora.
- mostrar_estado_bot(): Muestra la información de estado actual del bot.
- abrir_panel_control(): Abre el panel de control de Windows.
- apagar_pc_tiempo(minutos): Programa el apagado del PC en N minutos (ej. 60).
- limpiar_escritorio(): Fuerza la limpieza moviendo los archivos del escritorio.
- organizar_archivos(): Fuerza la organización general de archivos del sistema.

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

- obtener_reporte_salud(): Muestra uso de CPU y RAM.
- listar_procesos_pesados(): Muestra los procesos que consumen más memoria.
- actualizar_bot(): Realiza un pull desde git.
- buscar_y_resumir(consulta): Busca en la web una consulta y devuelve un resumen.
- modo_panico(): Cierra navegadores y silencia el PC de inmediato.
- crear_nota_rapida(texto, titulo): Crea una nota de texto.

NUNCA devuelvas texto fuera del JSON. Si razonas, hazlo mentalmente sin imprimirlo o en un campo "razonamiento" dentro del JSON.
"""

def detectar_intencion_local(mensaje):
    """Analiza palabras clave para ejecutar comandos locales sin usar la IA y ahorrar tokens."""
    texto = mensaje.lower()

    # Comandos directos y sencillos
    if "vaciar" in texto and "papelera" in texto:
        return {"herramienta": "vaciar_papelera", "args": {}, "respuesta": "Sí, Amo. Vaciando la papelera inmediatamente."}
    if "limpiar" in texto and "escritorio" in texto:
        return {"herramienta": "limpiar_escritorio", "args": {}, "respuesta": "Limpiando su escritorio, Amo."}
    if "silenciar" in texto and ("pc" in texto or "computadora" in texto or "ordenador" in texto):
        return {"herramienta": "silenciar_pc", "args": {}, "respuesta": "Silenciando el sistema, Amo."}
    if "modo pánico" in texto or "modo panico" in texto:
        return {"herramienta": "modo_panico", "args": {}, "respuesta": "¡Modo pánico activado! Cerrando navegadores y silenciando el PC."}
    if "reporte de salud" in texto or ("uso" in texto and ("cpu" in texto or "ram" in texto)):
         return {"herramienta": "obtener_reporte_salud", "args": {}, "respuesta": "Consultando los signos vitales del sistema, Amo."}
    if "actualizar bot" in texto or "git pull" in texto:
        return {"herramienta": "actualizar_bot", "args": {}, "respuesta": "Iniciando actualización desde el repositorio, Amo."}

    return None

def limpiar_respuesta_json(respuesta):
    """Extrae y limpia la respuesta JSON de la IA ignorando texto extra como 'thought' y etiquetas markdown."""
    texto = respuesta.strip()

    # Limpiamos etiquetas think y xml genericas si las hay
    texto = re.sub(r'<think>.*?</think>', '', texto, flags=re.DOTALL)

    # Eliminar bloques de codigo markdown completos y solo quedar con el contenido
    texto = re.sub(r'```(?:json)?\n?(.*?)\n?```', r'\1', texto, flags=re.DOTALL)

    # Extraer estrictamente lo que está entre el primer '{' o '[' y el último '}' o ']'
    match = re.search(r'(\{.*\}|\[.*\])', texto, re.DOTALL)
    if match:
        return match.group(1).strip()

    return texto.strip()

def procesar_mensaje(mensaje_usuario):
    global _historial

    # Árbitro: Comprobar intenciones locales primero
    intencion = detectar_intencion_local(mensaje_usuario)
    if intencion:
        print(f"[Árbitro] Intención local detectada: {intencion['herramienta']}")
        respuesta_texto = intencion["respuesta"]
        herramienta = intencion["herramienta"]
        args = intencion["args"]

        print(f"\nSalomé: {respuesta_texto}")
        _historial.append({"role": "user", "content": mensaje_usuario})
        _historial.append({"role": "assistant", "content": json.dumps({"respuesta_texto": respuesta_texto, "herramienta_a_ejecutar": herramienta, "argumentos_herramienta": args})})

        resultado_herramienta = herramientas.ejecutar_herramienta(herramienta, args)
        print(f"[Sistema] Resultado: {resultado_herramienta}")
        _historial.append({"role": "system", "content": f"Resultado de la herramienta {herramienta}: {resultado_herramienta}"})

        # Opcional: si la herramienta devuelve texto útil (ej. reporte de salud), podemos añadirlo a la respuesta
        if herramienta in ["obtener_reporte_salud", "listar_procesos_pesados", "actualizar_bot", "modo_panico", "buscar_y_resumir"]:
            respuesta_texto += f"\n\n[Resultado]: {resultado_herramienta}"

        return respuesta_texto

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