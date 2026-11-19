# ⚡ Anonymous - Hybrid Cybersecurity Platform

Asistente híbrido unificado de ciberseguridad que fusiona:
- **PentestGPT**: Lógica de auditoría ofensiva y Árbol de Tareas de Pentesting (PTT).
- **Asesor defensivo local**: búsqueda en referencias OWASP Top 10, MITRE ATT&CK, CIS Controls v8 y NIST CSF 2.0.
- **Centro de control Anonymous**: monitoreo local del equipo, registro de eventos y comandos desde una interfaz de escritorio.
- **ECC AgentShield**: Arnés de validación de comandos y Human-In-The-Loop para máxima seguridad.
- **Kali forense integrado**: operaciones de análisis permitidas sobre `kali-forensics`, con evidencias en solo lectura.
- **Kali remoto**: el perfil cloud puede conectarse por OpenSSH a la instancia Kali ya existente; no requiere desplegar un MCP ni un API adicional. Docker y VirtualBox conservan sus integraciones MCP. El descubrimiento sigue limitado y requiere confirmación.

---

## 🚀 Cómo ejecutar la Demo

### 0. Instalar dependencias
Desde la carpeta `anonymous`, instala las dependencias en el entorno virtual que vayas a usar:
```bash
python -m pip install -r requirements.txt
```

### 1. Modo Terminal interactivo (CLI en Warp / PowerShell / Bash):
```bash
python run.py
```

### 2. Modo gráfico de escritorio (HUD nativo):
```bash
python run.py --gui
```
Abre un centro de control de escritorio con métricas reales de CPU, memoria, disco y tráfico de red, un flujo Matrix, gráficos animados tipo pipes, registro de eventos, hallazgos y comandos. No muestra el reactor, objetivos ficticios ni contramedidas decorativas.

Los paneles se pueden arrastrar desde su encabezado, cambiar de tamaño desde la esquina inferior derecha y ocultar o volver a mostrar desde `PANELES`. La posición, el tamaño y la visibilidad se guardan en `~/.anonymous/desktop_layout.json`; `RESTABLECER DISTRIBUCIÓN` recupera la disposición inicial. Los botones `NORMAL`, `ATAQUE`, `DEFENSA`, `ÉXITO` y `ERROR` cambian los colores y el estado de la interfaz.

La ventana se implementa con Tkinter y `psutil`; no abre el navegador ni necesita un servidor web.

---

## 🛠️ Comandos Principales en la Terminal

| Comando | Descripción |
| :--- | :--- |
| `status` / `briefing` | Estado del sistema, IP local y resumen de tareas activas. |
| `config` / `configuración` | Configura proveedor de IA, entorno Kali/conexión y nombre del perfil local. |
| `config show` | Muestra los ajustes activos sin revelar claves API. |
| `scan <ip>` | Escáner multihilo de puertos TCP en Python nativo sin depender de nmap ni Docker. |
| `rag <consulta>` | Consulta instantánea a la base de conocimiento defensiva (OWASP, MITRE, CIS). |
| `ptt` | Muestra el árbol de tareas de penetración (Pentest Task Tree). |
| `ptt reset` | Reinicia el árbol de tareas de pentesting. |
| `findings` | Lista de vulnerabilidades y puertos abiertos detectados en la sesión. |
| `report` | Resumen defensivo de hallazgos y avance del PTT. |
| `ping <host>` | Verificación de conectividad agnóstica de sistema operativo. |
| `help` / `comandos` | Ayuda y listado de comandos. |
| `kali status` | Estado del contenedor forense y del MCP opcional. |
| `kali start` / `kali stop` | Inicia o detiene el contenedor forense (pide confirmación). |
| `kali forensic tools` | Lista las operaciones forenses de solo lectura integradas. |
| `kali forensic identify <archivo>` | Identifica el tipo de archivo en `Evidencias`. |
| `kali forensic metadata <archivo>` | Consulta metadatos básicos con ExifTool. |
| `kali forensic hash <archivo>` | Calcula SHA-256/MD5 y guarda un informe en `Resultados`. |
| `kali forensic partitions <imagen>` | Lista la tabla de particiones con Sleuth Kit. |
| `kali forensic ewf-info <archivo.E01>` / `ewf-verify` | Consulta o verifica una evidencia EWF. |
| `kali forensic files <imagen>` | Lista archivos de una imagen con Sleuth Kit. |
| `kali forensic binwalk <archivo>` | Identifica firmas de archivo sin extraer contenido. |
| `kali-start <objetivo>` | Sesión pasiva de evidencias. |
| `kali knowledge <tema>` | Playbooks markdown copiados de kali-mcp. |
| `kali discover <CIDR>` | Descubrimiento de hosts Nmap `-sn` con MCP o SSH, confirmación explícita y límite de 256 IP privadas. |
| `kali-finish` | Cierra la sesión Kali. |

Las operaciones `kali forensic` solo leen archivos directamente dentro de `C:\Kali-Forensics\Evidencias`; solo `hash` escribe su informe en `Resultados`. No admiten rutas arbitrarias ni shell. `kali-audit` y `kali exec` ofensivo **no están habilitados**. El MCP de `:666` es un servicio distinto y opcional; que el contenedor forense esté activo no significa que ese endpoint esté conectado. Catálogo: `../wiki/commands.md`.

### Alcance y límites de Kali forense

En el contenedor actual, `command -v` confirmó instalados `file`, ExifTool, SHA-256/MD5, Sleuth Kit (`mmls`, `fls`), EWF Tools, Binwalk, TestDisk/PhotoRec, Foremost, YARA, Hashdeep, DC3DD y Volatility 3 (`vol`). Que estén instalados no significa que Anonymous los invoque. La lista integrada y permitida es exactamente la de `kali forensic tools`; `identify`, `metadata`, `hash` y `binwalk` se probaron en vivo con archivo sintético, `partitions` con una imagen MBR sintética, `files` con una imagen FAT12 sintética, y `ewf-info`/`ewf-verify` con una imagen EWF sintética cuyo checksum fue correcto. TestDisk/PhotoRec, Foremost y DC3DD pueden escribir o recuperar datos; YARA requiere reglas seleccionadas; Hashdeep requiere un flujo de manifiestos; y Volatility requiere plugins y parámetros definidos por tipo de volcado. No están expuestos desde Anonymous hasta que exista una interfaz acotada y probada para esos casos.

Anonymous comprueba que `/evidencias` apunte al directorio configurado y esté montado como solo lectura antes de declarar Kali conectado o analizar archivos. Las salidas se limitan a 20 000 bytes por canal y las consultas tienen timeout; el exceso de salida se trunca. Los nombres se limitan a archivos directos dentro de `Evidencias`, y no se aceptan rutas ni comandos. La prueba GUI de `tests/test_kali_desktop_e2e.py` usa widgets Tk reales y valida el clic, la confirmación y el resultado del dispatcher; el dispatcher está simulado en esa prueba.

Para repetir la prueba `fls` real contra Docker desde PowerShell, ejecuta esto en la carpeta `anonymous`. Crea y borra únicamente su imagen FAT12 sintética:

```powershell
$env:ANONYMOUS_KALI_LIVE_TESTS = "1"
python -m unittest tests.test_kali_forensics.TestKaliForensicsLive -v
Remove-Item Env:\ANONYMOUS_KALI_LIVE_TESTS
```

En el contenedor observado, Docker reportó cero dispositivos añadidos y ninguna capacidad adicional explícita, pero el usuario del contenedor es root y su sistema de archivos raíz es escribible. `Evidencias` está en solo lectura; otros montajes, como `Configuracion` y `Herramientas`, son escribibles desde el contenedor. Anonymous no invoca herramientas de escritura, pero esto no convierte al contenedor en un entorno inmutable: el root del contenedor y Docker no equivalen a administración de Windows. Docker Desktop/WSL 2 tampoco proporciona por esta integración acceso directo a la RAM física de Windows ni a discos físicos. Para adquirirlos hace falta un procedimiento externo y autorizado; no se habilita aquí.

### RAG con documentos propios

El RAG local busca en las referencias defensivas y en la biblioteca de PDF ubicada en `RAG/documents/Kali Tools Library_/`. Para agregar fuentes, copia archivos PDF con texto, `.txt` o `.md` a `RAG/documents/` (se permiten subcarpetas); el motor detecta cambios y actualiza su índice en la siguiente consulta `rag <tema>`. Las respuestas incluyen el archivo y la página del fragmento encontrado. Los PDF escaneados requieren OCR. La ingesta y búsqueda son locales; la caché se guarda en `~/.anonymous/rag_documents_index.json`.

También se reconocen peticiones como `iniciemos conexión con Kali`, `inicia Kali` y `conectemos con Kali Docker` como inicio del contenedor forense `kali-forensics`; Anonymous pedirá confirmación antes de iniciarlo. Esto no inicia el stack MCP opcional ni habilita comandos arbitrarios. `status`/`briefing` informan los estados por separado; para comprobarlos sin iniciar nada, usa `kali status`.

`kali discover <CIDR>` pertenece al MCP opcional, separado del contenedor forense. Requiere que ese servicio se configure e inicie por separado y que `kali status` lo muestre conectado. Si está disponible, el descubrimiento se limita a redes privadas de hasta 256 direcciones, requiere confirmación explícita y usa Nmap `-sn` (sin escaneo de puertos ni pruebas de explotación). El contenedor forense por sí solo no ofrece esta función.

Después del descubrimiento, Anonymous usa Ollama para interpretar la salida y responder preguntas de seguimiento, incluso si otro proveedor está seleccionado para el chat general. Solo envía la pregunta, el alcance y los datos estructurados; Ollama no puede ejecutar comandos ni lanzar escaneos. Si Ollama no está disponible, presenta un resumen local claramente etiquetado. Las respuestas TCP reset se consideran inciertas —pueden proceder de una puerta de enlace o intermediario— y no se identifican dispositivos desconocidos sin compararlos con el inventario del router.

También se aceptan frases naturales como `mostrame el estado`, `revisá los puertos de localhost`, `comprobá conectividad con 127.0.0.1`, `ver tareas pendientes`, `armá un informe` y preguntas defensivas como `cómo proteger una API contra fuerza bruta`.

La base normativa funciona sin conexión y es una referencia práctica, no un catálogo exhaustivo ni una fuente legal actualizada automáticamente. Para uso operativo, valida las recomendaciones con la versión vigente de cada marco.

---

## ⚙️ Configuración compartida
La CLI y la aplicación gráfica usan los mismos ajustes locales. En la terminal escribe `config` o `config show`; en la GUI abre **CONFIGURACIÓN**. Se guardan en `~/.anonymous/settings.json`. Las claves API no se escriben en ese archivo: al guardar una clave de Gemini se usa el almacén de credenciales del sistema operativo (`keyring`). `.env` y `GEMINI_API_KEY` siguen siendo compatibles como alternativa; nunca se muestran en `config show`.

En **Inteligencia artificial** puedes elegir Ollama o Google Gemini, cambiar URL/modelos y configurar una clave Gemini. Ollama es el proveedor predeterminado y funciona localmente: instala Ollama y ejecuta `ollama run qwen2.5:3b` para descargar e iniciar el modelo. Para Gemini, usa una clave de [Google AI Studio](https://aistudio.google.com/). El chat principal usa el proveedor seleccionado; la interpretación de descubrimientos Kali continúa usando Ollama según el comportamiento existente y toma de aquí su URL y modelo.

En **Entorno Kali y conexión** puedes elegir:

- `native`: motores locales integrados; no conecta un MCP.
- `docker`: conserva el MCP Docker local existente (`http://127.0.0.1:666/mcp`).
- `cloud`: conecta por OpenSSH a la instancia Kali ya configurada en AWS. Introduce el host/IP, usuario (normalmente `kali`), puerto, ruta del archivo de clave privada y archivo `known_hosts` con la host key verificada. Anonymous no crea una API/MCP ni cambia las reglas de AWS.
- `virtualbox`: conserva el MCP Streamable HTTP configurable; Anonymous no crea ni instala ese servidor. Para endpoints remotos se exige HTTPS.

La conexión cloud usa `ssh` en PATH, `BatchMode`, una clave privada local y `StrictHostKeyChecking=yes`; no acepta automáticamente host keys nuevas ni usa la configuración SSH del usuario. Asegúrate de que la host key del servidor se haya verificado por un canal confiable y esté en `known_hosts`. La clave nunca se copia ni se guarda en `settings.json`. El servidor necesita aceptar SSH desde esta máquina y tener Nmap instalado.

La selección cloud solo permite una comprobación fija de conexión y, después de confirmación, Nmap `-sn` sobre redes IPv4 privadas RFC1918 de hasta 256 direcciones. No habilita shell arbitrario, escaneo de puertos ni pruebas de explotación. Docker y VirtualBox continúan usando su MCP, que debe exponer `execute_command` para el descubrimiento. Sin configuración válida, cada backend informa el error y no se redirige silenciosamente a otro entorno.

**Perfil local** permite definir un nombre visible. No crea cuentas, contraseñas ni autenticación. AgentShield y las confirmaciones de seguridad no se pueden desactivar desde estos ajustes. Otras opciones útiles —tema, idioma, nivel de registro o perfiles por proyecto— pueden añadirse después si se necesitan.

Para mantener la configuración actual basada en variables de entorno, copia `.env.example` a `.env`. Puedes volver a Ollama con `ANONYMOUS_AI_PROVIDER=ollama`.

El contexto de conversación se conserva durante la ejecución actual y no mezcla mensajes de ejecuciones anteriores.  
También entendés frases en español. Los escaneos y pings a objetivos no locales piden confirmación HITL tanto en la terminal como en la GUI de escritorio.  
*Nota: Si Ollama no está disponible o no hay una API key válida de Google, Anonymous recurre a sus motores locales integrados.*
