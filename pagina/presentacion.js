/**
 * Anonymous // Script Interactivo de la Página de Presentación
 * Controla el stepper de flujo, tabs de pilares, FAQ y simulador en vivo.
 */

// Datos de los 7 pasos del flujo interactivo
const FLOW_STEPS = [
  {
    phase: "PASO 01",
    tag: "INICIALIZACIÓN",
    title: "1. Despliegue Nativo y Transmisión Wi-Fi",
    description: "El operador inicia el sistema con un solo comando en terminal o haciendo doble clic en start_server.bat. El servidor HTTP nativo en Python enlaza en 0.0.0.0:8080 sin necesidad de levantar pesados contenedores Docker ni subsistemas WSL2. Inmediatamente detecta la tarjeta de red activa y publica las dos direcciones de acceso.",
    highlights: [
      "<b>URL Localhost:</b> http://localhost:8080 para trabajo directo en la estación de auditoría.",
      "<b>URL Wi-Fi Móvil:</b> Transmisión en tiempo real (ej. http://10.0.5.49:8080) permitiendo auditar o monitorear desde smartphones y tablets.",
      "<b>Presupuesto de RAM:</b> Menos de 60 MB en reposo, garantizando fluidez en laptops estándar (AMD Ryzen 5 / 8 GB)."
    ],
    mockupHeader: "BOOT LOG // SERVER DAEMON",
    mockupHtml: `
      <div style="color: #66e0ff; font-weight: bold; margin-bottom: 8px;">[SYSTEM_BOOT] Anonymous Tactical Web Server v1.0</div>
      <div style="color: #8ca4b0;">[NET] Binding socket to 0.0.0.0:8080 (IPv4 TCP)...</div>
      <div style="color: #00f985;">[NET] Discovered primary interface: Wi-Fi (10.0.5.49)</div>
      <div style="color: #ffffff; margin-top: 6px;">[READY] Localhost Access: <span style="color:#00f0ff;">http://localhost:8080</span></div>
      <div style="color: #ffffff;">[READY] LAN/Wi-Fi Access: <span style="color:#00f0ff;">http://10.0.5.49:8080</span></div>
      <div style="color: #8ca4b0; margin-top: 6px;">[SYS] Memory footprint: 48.2 MB RSS (Docker: OFF)</div>
      <div style="color: #00f985; margin-top: 8px;">>>> LISTENING FOR CLIENT CONNECTIONS (HTTP 1.1)</div>
    `
  },
  {
    phase: "PASO 02",
    tag: "SCOPING & CONFIGURACIÓN",
    title: "2. Scoping y Definición del Objetivo",
    description: "El analista ingresa a la interfaz (desde PC o dispositivo móvil) y define el alcance de la auditoría. Selecciona la dirección IP a auditar (ej. 127.0.0.1 para pruebas locales o 192.168.1.50 para auditoría de red) y activa con un clic los puertos críticos a verificar.",
    highlights: [
      "<b>Puertos preconfigurados:</b> 21 (FTP), 22 (SSH), 80 (HTTP), 443 (HTTPS), 3306 (MySQL), 8080 (Web), entre otros.",
      "<b>Control Granular:</b> Posibilidad de alternar chips de puertos para auditorías quirúrgicas o masivas.",
      "<b>Selector de Modo Táctico:</b> Normal (Exploración), Ataque (Red Team), Defensa (Blue Team)."
    ],
    mockupHeader: "HUD UI // TARGET DEFINITION",
    mockupHtml: `
      <div style="border: 1px solid rgba(0,240,255,0.3); padding: 12px; border-radius: 6px; background: rgba(0,240,255,0.03);">
        <div style="color: #8ca4b0; font-size: 11px;">TARGET SCOPE CONFIGURATION</div>
        <div style="font-size: 14px; color: #fff; margin: 4px 0;">HOST: <b style="color:#00f0ff;">127.0.0.1 (Localhost)</b></div>
        <div style="color: #8ca4b0; font-size: 11px; margin-top: 8px;">PUERTOS ACTIVADOS:</div>
        <div style="display:flex; gap: 4px; flex-wrap: wrap; margin-top: 4px;">
          <span style="background:rgba(0,240,255,0.2); color:#00f0ff; padding:2px 6px; border-radius:3px; font-size:10px;">TCP/21</span>
          <span style="background:rgba(0,240,255,0.2); color:#00f0ff; padding:2px 6px; border-radius:3px; font-size:10px;">TCP/22</span>
          <span style="background:rgba(0,240,255,0.2); color:#00f0ff; padding:2px 6px; border-radius:3px; font-size:10px;">TCP/80</span>
          <span style="background:rgba(0,240,255,0.2); color:#00f0ff; padding:2px 6px; border-radius:3px; font-size:10px;">TCP/443</span>
          <span style="background:rgba(0,240,255,0.2); color:#00f0ff; padding:2px 6px; border-radius:3px; font-size:10px;">TCP/8080</span>
        </div>
      </div>
      <div style="color: #00f985; margin-top: 10px;">[INPUT ACCEPTED] Scope validado bajo marco de pruebas autorizado.</div>
    `
  },
  {
    phase: "PASO 03",
    tag: "GOBERNANZA ÉTICA",
    title: "3. Barrera de Seguridad AgentShield (HITL)",
    description: "Para evitar que la inteligencia artificial o un script descontrolado bombardee servidores no autorizados, el arnés AgentShield evalúa la petición. Si el objetivo no es 127.0.0.1 o la IP propia del equipo y el modo seguro está encendido, el sistema detiene inmediatamente el despacho y despliega el modal de confirmación obligatoria.",
    highlights: [
      "<b>Human-In-The-Loop (HITL):</b> Nada se envía a la red sin el consentimiento explícito del analista.",
      "<b>Mitigación de Responsabilidad Legal:</b> Evita incidentes penales o ataques involuntarios a terceros.",
      "<b>Modal Bloqueante:</b> Exige clic en 'AUTORIZAR Y PROCEDER' o aborta limpiamente la tarea."
    ],
    mockupHeader: "AGENTSHIELD // HITL INTERCEPTOR",
    mockupHtml: `
      <div style="border: 1px solid #ff5263; background: rgba(255,82,99,0.08); padding: 12px; border-radius: 6px;">
        <div style="color: #ff5263; font-weight: bold; display: flex; align-items:center; gap:6px;">
          <span>⚠️</span> INTERCEPCIÓN AGENTSHIELD HITL
        </div>
        <div style="color: #e2f1f5; font-size: 11px; margin-top: 6px;">
          Objetivo fuera del rango de loopback detectado: <b style="color:#ffb03a;">192.168.1.105</b>
        </div>
        <div style="color: #8ca4b0; font-size: 10px; margin-top: 6px;">
          ¿Posee autorización formal por escrito de la entidad propietaria?
        </div>
        <div style="margin-top: 8px; display:flex; gap: 8px;">
          <span style="background: rgba(255,255,255,0.1); padding: 2px 8px; border-radius: 4px; font-size: 10px; color: #fff;">[CANCELAR]</span>
          <span style="background: #00f985; color: #000; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold;">[AUTORIZAR Y PROCEDER]</span>
        </div>
      </div>
      <div style="color: #ffb03a; margin-top: 8px;">[STATUS] En espera de interacción del operador humano...</div>
    `
  },
  {
    phase: "PASO 04",
    tag: "AUDITORÍA OFENSIVA",
    title: "4. Escaneo TCP Concurrente por Sockets",
    description: "Una vez autorizado, el motor Red Team dispara un escaneo multihilo de sockets nativos en Python. No requiere nmap, ni binarios de terceros, ni privilegios de administrador de red. Con un timeout calibrado a 350ms, evalúa los puertos simultáneamente y mide la latencia exacta de cada servicio.",
    highlights: [
      "<b>Velocidad extrema:</b> 10 puertos auditados en menos de 0.45 segundos.",
      "<b>Mapeo de Servicios:</b> Resolución automática del protocolo (HTTP, SSH, MySQL, Flask, Web).",
      "<b>Bajo Ruido:</b> Conexiones SYN controladas que no saturan los registros del objetivo."
    ],
    mockupHeader: "SOCKET ENGINE // RAW TCP THREADS",
    mockupHtml: `
      <div style="color: #8ca4b0;">>>> DISPATCHING TCP SOCKET WORKERS (Timeout: 0.35s)</div>
      <div style="color: #ff5263;">[PORT 21] CLOSED (No response)</div>
      <div style="color: #ff5263;">[PORT 22] CLOSED (RST packet)</div>
      <div style="color: #00f985; font-weight: bold;">[PORT 80] OPEN (HTTP) - Latency: 1.2ms</div>
      <div style="color: #00f985; font-weight: bold;">[PORT 8080] OPEN (Tactical Web HUD) - Latency: 0.4ms</div>
      <div style="color: #ff5263;">[PORT 3306] CLOSED</div>
      <div style="color: #00f0ff; margin-top: 8px;">>>> 2 PUERTOS ACTIVOS DETECTADOS EN 0.38s</div>
    `
  },
  {
    phase: "PASO 05",
    tag: "METODOLOGÍA PTT",
    title: "5. Progresión del Árbol de Tareas (PTT)",
    description: "Heredado de la arquitectura de PentestGPT, Anonymous no deja la auditoría al azar. La metodología de Árbol de Tareas (Pentesting Task Tree) actualiza su estado dinámicamente: la tarea T2 (Escaneo) se marca como completada y desbloquea automáticamente la tarea T3 (Enumeración) y T4 (Cotejo Defensivo).",
    highlights: [
      "<b>T1 Reconocimiento:</b> Interfaces y sockets descubiertos (COMPLETADO).",
      "<b>T2 Escaneo:</b> Mapeo de puertos TCP críticos (COMPLETADO).",
      "<b>T3 Enumeración & T4 Asesoría:</b> Banners de servicios y mapeo normativo (EN PROGRESO).",
      "<b>T5 Reporte:</b> Generación de bitácora consolidada."
    ],
    mockupHeader: "PENTEST TASK TREE // TREE STATE",
    mockupHtml: `
      <div style="display:flex; flex-direction:column; gap:6px;">
        <div style="color: #00f985;">[✔] T1: Descubrimiento de Interfaces (10.0.5.49) [COMPLETADO]</div>
        <div style="color: #00f985;">[✔] T2: Mapeo de Puertos TCP Críticos [COMPLETADO]</div>
        <div style="color: #00f0ff; font-weight:bold;">[⚡] T3: Identificación de Banners y Cabeceras [EN PROGRESO]</div>
        <div style="color: #ffb03a;">[⏳] T4: Cotejo Normativo RAG (OWASP/MITRE) [PENDIENTE]</div>
        <div style="color: #8ca4b0;">[🔒] T5: Generación de Reporte Markdown [BLOQUEADO]</div>
      </div>
      <div style="color:#c084fc; margin-top:8px;">[LOGIC] PTT Tree actualizado según descubrimientos en tiempo real.</div>
    `
  },
  {
    phase: "PASO 06",
    tag: "ASESORÍA DEFENSIVA",
    title: "6. Correlación Defensiva RAG (Blue Team)",
    description: "Aquí se cumple la visión simbiótica de Anonymous: la detección ofensiva se conecta inmediatamente con la defensa. El motor Blue Team consulta la base de conocimiento local estructurada en OWASP Top 10, MITRE ATT&CK y CIS Controls v8, ofreciendo la receta exacta de remediación técnica y código de configuración segura.",
    highlights: [
      "<b>OWASP A01:2021:</b> Remediación de Control de Acceso Roto y cabeceras de seguridad.",
      "<b>OWASP A05:2021:</b> Mala Configuración de Seguridad (deshabilitar puertos no usados, HSTS, CSP).",
      "<b>MITRE ATT&CK T1046:</b> Descubrimiento de servicios y cómo configurar firewalls e IDS perimetrales."
    ],
    mockupHeader: "BLUE TEAM RAG // DEFENSIVE ADVISORY",
    mockupHtml: `
      <div style="border: 1px solid rgba(0,249,133,0.3); background: rgba(0,249,133,0.05); padding: 10px; border-radius: 6px;">
        <div style="color: #00f985; font-weight: bold; font-size: 11px;">OWASP A05:2021 // Security Misconfiguration</div>
        <div style="color: #e2f1f5; font-size: 10px; margin-top: 4px;">Puerto 8080 expuesto sin filtrado perimetral.</div>
        <div style="color: #8cffbd; font-size: 10px; margin-top: 6px;">
          <b>Remediación:</b> Restringir interfaz de escucha a 127.0.0.1 si no requiere acceso Wi-Fi, o aplicar reglas UFW/iptables:
          <code style="display:block; background:#000; padding:4px; margin-top:4px; border-radius:3px; color:#66e0ff;">
            ufw allow from 10.0.5.0/24 to any port 8080 proto tcp
          </code>
        </div>
      </div>
    `
  },
  {
    phase: "PASO 07",
    tag: "CONSOLIDACIÓN",
    title: "7. Telemetría Holográfica y Reporte Final",
    description: "El ciclo culmina con la sincronización holística: los puertos descubiertos brillan como nodos tridimensionales en el radar interactivo HTML5 Canvas a 60 FPS, los eventos quedan grabados en la base de datos de hallazgos SQLite y el analista puede generar un informe ejecutivo en formato Markdown listo para Obsidian.",
    highlights: [
      "<b>Radar Canvas 3D:</b> Barrido continuo a 60 FPS con mapeo espacial de nodos abiertos.",
      "<b>Persistencia de Hallazgos:</b> Tabla estructurada con ID, severidad, descripción y timestamp.",
      "<b>Exportación a Obsidian:</b> Documentación acumulativa bajo el patrón de LLM Wiki para trazabilidad histórica."
    ],
    mockupHeader: "SESSION REPORT // TELEMETRY & PERSISTENCE",
    mockupHtml: `
      <div style="color: #00f985; font-weight:bold;">[SUMMARY] AUDITORÍA CONCLUIDA SATISFACTORIAMENTE</div>
      <div style="color: #8ca4b0; font-size: 11px; margin-top: 4px;">Host: 127.0.0.1 | Hallazgos Registrados: 2</div>
      <div style="display:flex; gap:6px; margin-top:6px;">
        <span style="background:rgba(0,240,255,0.15); color:#00f0ff; padding:2px 6px; border-radius:3px; font-size:10px;">CANVAS 60 FPS: ONLINE</span>
        <span style="background:rgba(0,249,133,0.15); color:#00f985; padding:2px 6px; border-radius:3px; font-size:10px;">SQLITE: SYNCED</span>
      </div>
      <div style="color: #e2f1f5; font-size: 11px; margin-top: 8px;">
        Archivo de reporte generado en: <br>
        <span style="color:#c084fc;">anonymous/reports/session_audit_127_0_0_1.md</span>
      </div>
      <div style="color: #66e0ff; margin-top: 8px;">>>> SISTEMA LISTO PARA SIGUIENTE OPERACIÓN</div>
    `
  }
];

let currentStepIndex = 0;

// Inicialización cuando carga el DOM
document.addEventListener("DOMContentLoaded", () => {
  initStepper();
  initPillarsTabs();
  initFaqAccordion();
  initScrollProgress();
  initModeSwitchers();
  initPlayground();
});

/* =====================================================================
   STEPPER DE FLUJO INTERACTIVO
   ===================================================================== */
function initStepper() {
  const container = document.getElementById("flow-nav-container");
  if (!container) return;

  container.innerHTML = "";
  FLOW_STEPS.forEach((step, idx) => {
    const btn = document.createElement("button");
    btn.className = `step-node-btn ${idx === 0 ? "active" : ""}`;
    btn.id = `step-node-${idx}`;
    btn.onclick = () => renderStep(idx);
    btn.innerHTML = `
      <div class="step-node-bubble">${idx + 1}</div>
      <span class="step-node-label">${step.tag}</span>
    `;
    container.appendChild(btn);
  });

  renderStep(0);
}

function renderStep(idx) {
  currentStepIndex = idx;
  const step = FLOW_STEPS[idx];

  // Actualizar nodos visuales
  FLOW_STEPS.forEach((_, i) => {
    const el = document.getElementById(`step-node-${i}`);
    if (el) el.classList.toggle("active", i === idx);
  });

  // Actualizar textos e información
  const phaseTag = document.getElementById("step-phase-tag");
  const title = document.getElementById("step-title");
  const desc = document.getElementById("step-desc");
  const highlights = document.getElementById("step-highlights");
  const mockupTitle = document.getElementById("step-mockup-title");
  const mockupBody = document.getElementById("step-mockup-body");

  if (phaseTag) phaseTag.textContent = `${step.phase} // ${step.tag}`;
  if (title) title.textContent = step.title;
  if (desc) desc.textContent = step.description;

  if (highlights) {
    highlights.innerHTML = step.highlights
      .map(item => `<li>${item}</li>`)
      .join("");
  }

  if (mockupTitle) mockupTitle.textContent = step.mockupHeader;
  if (mockupBody) mockupBody.innerHTML = step.mockupHtml;

  // Actualizar botones de anterior/siguiente
  const prevBtn = document.getElementById("btn-step-prev");
  const nextBtn = document.getElementById("btn-step-next");

  if (prevBtn) {
    prevBtn.disabled = idx === 0;
    prevBtn.style.opacity = idx === 0 ? "0.4" : "1";
    prevBtn.style.cursor = idx === 0 ? "not-allowed" : "pointer";
  }

  if (nextBtn) {
    if (idx === FLOW_STEPS.length - 1) {
      nextBtn.textContent = "Reiniciar Flujo ↺";
      nextBtn.onclick = () => renderStep(0);
    } else {
      nextBtn.textContent = "Siguiente Paso ➔";
      nextBtn.onclick = () => renderStep(currentStepIndex + 1);
    }
  }
}

function prevStep() {
  if (currentStepIndex > 0) {
    renderStep(currentStepIndex - 1);
  }
}

function nextStep() {
  if (currentStepIndex < FLOW_STEPS.length - 1) {
    renderStep(currentStepIndex + 1);
  } else {
    renderStep(0);
  }
}

/* =====================================================================
   TABS DE LOS 5 PILARES
   ===================================================================== */
function initPillarsTabs() {
  const buttons = document.querySelectorAll(".pillar-tab-btn");
  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      buttons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      const target = btn.getAttribute("data-target");
      document.querySelectorAll(".pillar-content-panel").forEach(panel => {
        panel.classList.remove("active");
      });

      const activePanel = document.getElementById(target);
      if (activePanel) {
        activePanel.classList.add("active");
      }
    });
  });
}

/* =====================================================================
   ACORDEÓN DE PREGUNTAS FRECUENTES (FAQ)
   ===================================================================== */
function initFaqAccordion() {
  const cards = document.querySelectorAll(".faq-card");
  cards.forEach(card => {
    const btn = card.querySelector(".faq-question-btn");
    if (!btn) return;

    btn.addEventListener("click", () => {
      const isOpen = card.classList.contains("open");
      // Cerrar otros
      cards.forEach(c => c.classList.remove("open"));
      if (!isOpen) {
        card.classList.add("open");
      }
    });
  });
}

/* =====================================================================
   BARRA DE PROGRESO DE LECTURA (SCROLL PROGRESS)
   ===================================================================== */
function initScrollProgress() {
  const bar = document.getElementById("scroll-progress");
  if (!bar) return;

  window.addEventListener("scroll", () => {
    const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
    const progress = (window.scrollY / totalHeight) * 100;
    bar.style.width = `${Math.min(100, Math.max(0, progress))}%`;
  });
}

/* =====================================================================
   CAMBIO DINÁMICO DE MODOS VISUALES (THEMES)
   ===================================================================== */
function initModeSwitchers() {
  const pills = document.querySelectorAll(".mode-pill");
  pills.forEach(pill => {
    pill.addEventListener("click", () => {
      const mode = pill.getAttribute("data-mode") || "normal";
      document.body.setAttribute("data-mode", mode);
      pills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
    });
  });
}

function switchMode(mode) {
  document.body.setAttribute("data-mode", mode);
  const pills = document.querySelectorAll(".mode-pill");
  pills.forEach(p => {
    p.classList.toggle("active", p.getAttribute("data-mode") === mode);
  });
}

/* =====================================================================
   PLAYGROUND / SIMULADOR EN VIVO DEL FLUJO
   ===================================================================== */
function initPlayground() {
  const chips = document.querySelectorAll(".sim-port-chip");
  chips.forEach(chip => {
    chip.addEventListener("click", () => {
      chip.classList.toggle("selected");
    });
  });
}

function runSimulator() {
  const targetInput = document.getElementById("sim-target-input");
  const screen = document.getElementById("sim-screen");
  if (!targetInput || !screen) return;

  const target = targetInput.value.trim() || "127.0.0.1";
  const selectedPorts = Array.from(document.querySelectorAll(".sim-port-chip.selected"))
    .map(c => parseInt(c.getAttribute("data-port")));

  if (selectedPorts.length === 0) {
    alert("Por favor selecciona al menos un puerto para simular el escaneo.");
    return;
  }

  screen.innerHTML = `
    <div style="color: #66e0ff;">[SIMULADOR DE FLUJO] Iniciando evaluación para: <b>${target}</b></div>
    <div style="color: #8ca4b0;">[AGENTSHIELD] Verificando rango de red y políticas HITL...</div>
  `;

  // Comprobar política HITL
  const isLocal = target === "127.0.0.1" || target === "localhost";

  setTimeout(() => {
    if (!isLocal) {
      screen.innerHTML += `
        <div style="color: #ffb03a; margin-top: 4px;">
          ⚠️ [HITL TRIGGER] El host ${target} es un destino remoto.
        </div>
        <div style="color: #ff5263;">
          [AGENTSHIELD] Solicitando autorización humana obligatoria para evitar escaneo no ético...
        </div>
        <div style="background: rgba(255,255,255,0.08); padding: 8px; border-radius: 4px; margin-top: 6px;">
          <span>Operador confirma: "AUTORIZADO // PRUEBA DE LABORATORIO" ✔</span>
        </div>
      `;
    } else {
      screen.innerHTML += `
        <div style="color: #00f985; margin-top: 4px;">
          ✔ [HITL BYPASS] Host local detectado (${target}). Procede escaneo de bajo impacto sin riesgo externo.
        </div>
      `;
    }

    setTimeout(() => {
      screen.innerHTML += `
        <div style="color: #66e0ff; margin-top: 6px;">
          [RED_TEAM] Ejecutando escáner concurrente por sockets TCP nativos (Sin Docker)...
        </div>
      `;

      setTimeout(() => {
        let openCount = 0;
        selectedPorts.forEach(port => {
          const isOpen = port === 80 || port === 8080 || port === 22;
          if (isOpen) {
            openCount++;
            const svc = port === 80 ? "HTTP" : (port === 8080 ? "Tactical Web" : "SSH");
            screen.innerHTML += `
              <div style="color: #00f985;">
                • TCP/${port} [ABIERTO] - Servicio: ${svc} (Latencia: 0.3ms)
              </div>
            `;
          } else {
            screen.innerHTML += `
              <div style="color: #546a75;">
                • TCP/${port} [CERRADO]
              </div>
            `;
          }
        });

        setTimeout(() => {
          screen.innerHTML += `
            <div style="color: #c084fc; margin-top: 6px;">
              [PTT_TREE] Tarea T2 (Escaneo) marcada como COMPLETADA. Avanzando a T3 (Enumeración).
            </div>
            <div style="color: #00f985; margin-top: 4px;">
              [BLUE_TEAM_RAG] Correlacionando ${openCount} servicio(s) con OWASP Top 10 (A05:2021) y MITRE ATT&CK (T1046).
            </div>
            <div style="color: #00f0ff; margin-top: 6px; font-weight: bold;">
              ✔ [FLUJO COMPLETADO EXITOSAMENTE]
            </div>
          `;
          screen.scrollTop = screen.scrollHeight;
        }, 350);
      }, 500);
    }, 400);
  }, 300);
}

function resetSimulator() {
  const screen = document.getElementById("sim-screen");
  if (screen) {
    screen.innerHTML = `
      <div style="color: #8ca4b0;">
        Simulador en reposo. Define la IP objetivo, selecciona puertos y presiona 'EJECUTAR SIMULACIÓN DE FLUJO'.
      </div>
    `;
  }
}
