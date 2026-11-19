# Validación TDD: proveedor de IA

## Recorrido

Como usuario, quiero que Anonymous use Ollama con `qwen2.5:3b` de forma predeterminada y me permita elegir Google Gemini, para usar un modelo local o la API de Google.

## Evidencia

| Comportamiento | Prueba | RED | GREEN |
|---|---|---|---|
| Ollama acepta la selección sin una clave de Google y usa `qwen2.5:3b`. | `tests/test_ai_provider.py` | Falló: `GeminiClient` no aceptaba `provider`. | Pasa. |
| La solicitud usa `/api/chat`, incluye instrucciones, historial y modelo, y devuelve el contenido. | `tests/test_ai_provider.py` | Falló: `GeminiClient` no aceptaba `provider`. | Pasa. |
| Las respuestas y errores de Ollama se manejan con respaldo local explícito. | `tests/test_ai_provider.py` | Falló: `GeminiClient` no aceptaba `provider`. | Pasa. |
| El proveedor Google conserva el comportamiento y los respaldos existentes. | `tests/test_gemini_fallback.py` | — (regresión existente). | Pasa. |

## Comandos ejecutados

- RED: `python -m pytest anonymous\tests\test_ai_provider.py -q` — 4 fallos esperados porque aún no existía la opción de proveedor.
- GREEN: `python -m pytest anonymous\tests\test_ai_provider.py anonymous\tests\test_gemini_fallback.py -q` — 11 pruebas aprobadas.
- Suite: `python -m pytest anonymous\tests -q` — 108 pruebas y 25 subtests aprobados.
- Cobertura: no se ejecutó.

Las solicitudes a Ollama se probaron con un servidor HTTP simulado; no se validó una instancia real de Ollama ni credenciales de Gemini.
