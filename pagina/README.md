# WEP-SER-IP — Monitor Web y Página Táctica de Anonymous

Esta carpeta contiene la implementación completa de la interfaz web, boceto interactivo y servidor HTTP local con transmisión por red Wi-Fi para el proyecto **Anonymous** (Plataforma Híbrida de Ciberseguridad).

---

* **`presentacion.html`**: Página web de presentación ejecutiva y académica que detalla:
  * El **contexto completo del proyecto**, ideas clave y fusión de los 5 pilares (PentestGPT, Cybersecurity-RAG, OpenJarvis, Jarvis, ECC AgentShield).
  * Los **problemas reales** que resuelve (fragmentación, hardware 8 GB sin Docker, contención ética HITL y brecha Red/Blue).
  * El **flujo de interacción de usuario** paso a paso con stepper interactivo y simulador en vivo.
* **`presentacion.css`**: Hoja de estilos de vanguardia con estética cyberpunk glassmorphic, variables CSS reactivas y diseño responsivo.
* **`presentacion.js`**: Controlador interactivo para el stepper de 7 pasos, pestañas de arquitectura, preguntas frecuentes (FAQ) y playground de simulación.
* **`index.html`**: Centro de control y panel táctico interactivo (Stark HUD / Red Team & Blue Team).
* **`styles.css`**: Hoja de estilos Cyberpunk / Glassmorphic con soporte multitema en tiempo real (Normal, Ataque, Defensa, Éxito, Error).
* **`app.js`**: Controlador interactivo del cliente, visualizador radar en Canvas HTML5, emulador de terminal interactivo, árbol PTT y conector API REST.
* **`server.py`**: Servidor HTTP Python nativo sin dependencias externas que escucha en `0.0.0.0:8080`, transmitiendo tanto en localhost como por la red Wi-Fi.
* **`start_server.bat`**: Script de inicio rápido con doble clic para Windows.

---

## 🚀 Cómo Iniciar el Servidor

### Opción 1: Con el archivo `.bat` (Recomendado en Windows)
Haz doble clic sobre `start_server.bat`. La consola WEP-SER-IP se mantiene abierta y actualiza el estado cada 2 segundos.

### Opción 2: Desde la Terminal (PowerShell / CMD)
```powershell
cd C:\Users\maxgu\Documents\anonimus\pagina
python server.py --port 8080
```

---

## 🌐 Cómo Acceder desde Otros Dispositivos (Wi-Fi)

1. Asegúrate de que tu teléfono, tablet u otra laptop esté conectada a la **misma red Wi-Fi**.
2. En el dispositivo remoto, abre el navegador web e ingresa la dirección IP de tu máquina en el puerto `8080`:
   ```text
   http://10.0.5.49:8080
   ```
3. Desde tu propia computadora puedes ingresar mediante:
   ```text
   http://localhost:8080
   ```

## 👥 Ver visitantes y dispositivos desde la terminal

La terminal del servidor mantiene una pantalla en vivo con las direcciones IP de quienes abrieron la página y siguen activos (actividad en los últimos 20 segundos), además de los equipos que figuran en la caché ARP del sistema. La página envía una señal de actividad cada 5 segundos mientras está abierta.

Para hacer una consulta puntual desde otra consola:

```powershell
cd C:\Users\maxgu\Documents\anonimus\pagina
python server.py --devices
```

Si iniciaste el servidor en otro puerto, indícalo también, por ejemplo `python server.py --devices --port 8081`. La lista de visitantes solo se puede consultar desde la misma computadora donde corre el servidor. La lista de red es pasiva: lee la caché ARP del sistema, por lo que puede no incluir todos los dispositivos conectados; no realiza sondeos de la red.

---

## ⚡ Funcionalidades Integradas en el Boceto

1. **Escaneo TCP de Sockets:** Permite auditar puertos de red estándar (`21, 22, 80, 443, 3306, 8080`) directamente sin herramientas externas pesadas.
2. **Visualizador PTT (Pentesting Task Tree):** Árbol jerárquico de fases de auditoría (`Reconocimiento -> Escaneo -> Enumeración -> Evaluación Defensiva -> Reporte`).
3. **Asesor Normativo RAG (Blue Team):** Motor de búsqueda integrado de normativas de seguridad `OWASP Top 10`, `MITRE ATT&CK` y `CIS Controls v8`.
4. **AgentShield HITL (Human-In-The-Loop):** Arnés de contención y barrera de autorización para prevenir escaneos a objetivos no autorizados.
5. **Terminal Interactiva:** Soporte de comandos en tiempo real (`status`, `scan <ip>`, `ping <ip>`, `rag <norma>`, `ptt`, `findings`, `mode <modo>`, `help`).
6. **Radar Holográfico 3D Canvas:** Renderizado dinámico a 60 FPS con mapeo de nodos descubiertos.
7. **Glyph Stream:** Estela ligera de glifos cian que sigue el cursor, salpica al hacer clic y respeta la preferencia de movimiento reducido.
