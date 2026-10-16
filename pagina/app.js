/**
 * ANONYMOUS // TACTICAL HUD CONTROLLER
 * Lógica interactiva para el boceto web, radar holográfico, terminal y enlace con la API.
 */

// Estado Global de la Aplicación en Navegador
const AppState = {
  mode: 'normal',
  target: '127.0.0.1',
  localIp: '10.0.5.49',
  serverPort: 8080,
  safeMode: true,
  commandHistory: [],
  historyIndex: -1,
  pendingAction: null,
  radarNodes: [
    { angle: 0.4, dist: 0.35, label: 'TCP/8080 (Web)', color: '#00f0ff' },
    { angle: 1.8, dist: 0.65, label: 'TCP/22 (SSH)', color: '#ffae57' },
    { angle: 3.5, dist: 0.45, label: 'AgentShield HITL', color: '#00f985' },
    { angle: 5.1, dist: 0.75, label: 'SQLite Memory', color: '#bd83ff' }
  ],
  radarAngle: 0,
  ragCategory: 'owasp',
  findings: [],
  pttTree: []
};

// Datos RAG por defecto (fallback autónomo y rápido)
const DEFAULT_RAG_DATA = {
  owasp: [
    {
      id: "A01:2021",
      title: "Broken Access Control (Control de Acceso)",
      risk: "Crítico",
      category: "OWASP Top 10",
      desc: "Falla donde los usuarios pueden actuar fuera de sus permisos previstos.",
      remediation: "Denegar por defecto, forzar autorización en APIs y validar ownership en cada consulta."
    },
    {
      id: "A02:2021",
      title: "Cryptographic Failures (Fallas Criptográficas)",
      risk: "Alto",
      category: "OWASP Top 10",
      desc: "Transmisión o almacenamiento de datos sensibles sin cifrado robusto.",
      remediation: "Imponer TLS 1.3, rechazar algoritmos viejos (MD5/SHA1) y hashear claves con Argon2id."
    },
    {
      id: "A03:2021",
      title: "Injection (Inyecciones SQL / Comandos OS)",
      risk: "Crítico",
      category: "OWASP Top 10",
      desc: "Datos no confiables interpretados como comandos ejecutables por un motor.",
      remediation: "Usar sentencias parametrizadas (Prepared Statements) y validación estricta de tipos."
    },
    {
      id: "A05:2021",
      title: "Security Misconfiguration (Mala Configuración)",
      risk: "Medio-Alto",
      category: "OWASP Top 10",
      desc: "Cuentas por defecto activas, encabezados HTTP ausentes o puertos de debug expuestos.",
      remediation: "Auditar periódicamente, cerrar puertos innecesarios e implementar cabeceras CSP/HSTS."
    }
  ],
  mitre: [
    {
      id: "T1046",
      title: "Network Service Discovery",
      risk: "Discovery",
      category: "MITRE ATT&CK",
      desc: "El adversario sondea hosts y puertos para mapear servicios vulnerables accesibles.",
      remediation: "Segmentación de red, firewalls locales por host y detección de escaneos TCP anómalos."
    },
    {
      id: "T1190",
      title: "Exploit Public-Facing Application",
      risk: "Initial Access",
      category: "MITRE ATT&CK",
      desc: "Aprovechamiento de vulnerabilidades en software expuesto a Internet o Wi-Fi.",
      remediation: "Escaneos de vulnerabilidades periódicos con PTT, parches inmediatos y WAF perimetral."
    },
    {
      id: "T1059",
      title: "Command and Scripting Interpreter",
      risk: "Execution",
      category: "MITRE ATT&CK",
      desc: "Abuso de intérpretes de comandos nativos (PowerShell, Bash) para ejecutar cargas.",
      remediation: "Habilitar registro de bloques de script (EID 4104) y modo de lenguaje restringido."
    }
  ],
  cis: [
    {
      id: "CIS-01",
      title: "Inventario y Control de Activos Empresariales",
      risk: "Control Fundamental",
      category: "CIS Controls v8",
      desc: "Monitorear activamente todos los activos de computación conectados a la infraestructura.",
      remediation: "Utilizar herramientas de descubrimiento pasivo y activo en subredes locales y Wi-Fi."
    },
    {
      id: "CIS-04",
      title: "Configuración Segura de Servidores y Clientes",
      risk: "Control Fundamental",
      category: "CIS Controls v8",
      desc: "Mantener configuraciones de hardware y software según estándares de endurecimiento (CIS Benchmarks).",
      remediation: "Deshabilitar servicios innecesarios, reforzar contraseñas y desactivar protocolos inseguros."
    }
  ]
};

// Datos PTT por defecto
const DEFAULT_PTT_TREE = [
  {
    id: "T1",
    phase: "Reconocimiento",
    title: "Descubrimiento de Interfaces y Sockets",
    status: "completed",
    details: "Host local mapeado y enlace Wi-Fi verificado en subred."
  },
  {
    id: "T2",
    phase: "Escaneo",
    title: "Mapeo de Puertos TCP Críticos",
    status: "in_progress",
    details: "Sondeo de puertos estándar con motor de sockets concurrentes."
  },
  {
    id: "T3",
    phase: "Enumeración",
    title: "Identificación de Versiones y Servicios",
    status: "pending",
    details: "Captura de banners HTTP/SSH y metadatos de servicios."
  },
  {
    id: "T4",
    phase: "Evaluación Defensiva",
    title: "Cotejo Normativo RAG",
    status: "pending",
    details: "Comparación de hallazgos contra marcos OWASP y MITRE."
  },
  {
    id: "T5",
    phase: "Reporte",
    title: "Sugerencias de Mitigación e Informe",
    status: "pending",
    details: "Consolidación de bitácora y exportación para Obsidian."
  }
];

// Hallazgos iniciales
const DEFAULT_FINDINGS = [
  {
    id: 1,
    title: "Puerto 8080 HTTP Abierto",
    target: "127.0.0.1",
    severity: "INFO",
    description: "Servidor táctico web de Anonymous activo y transmitiendo en la red local.",
    timestamp: "12:10:00"
  },
  {
    id: 2,
    title: "AgentShield HITL Activo",
    target: "127.0.0.1",
    severity: "LOW",
    description: "Supervisión humana obligatoria habilitada para objetivos remotos.",
    timestamp: "12:11:15"
  }
];

// =====================================================================
// INICIALIZACIÓN
// =====================================================================
document.addEventListener('DOMContentLoaded', () => {
  initClock();
  initCanvasRadar();
  initEventListeners();
  loadInitialData();
  fetchServerStatus();
});

// Reloj en tiempo real
function initClock() {
  const clockEl = document.getElementById('header-clock');
  function update() {
    const now = new Date();
    clockEl.textContent = now.toTimeString().split(' ')[0] + ' UTC';
  }
  update();
  setInterval(update, 1000);
}

// Carga inicial de datos
function loadInitialData() {
  AppState.pttTree = [...DEFAULT_PTT_TREE];
  AppState.findings = [...DEFAULT_FINDINGS];
  renderPTT();
  renderFindings();
  renderRAG(AppState.ragCategory);
}

// =====================================================================
// RADAR HOLOGRÁFICO EN CANVAS (ANIMACIÓN 60 FPS)
// =====================================================================
function initCanvasRadar() {
  const canvas = document.getElementById('holo-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  function resizeCanvas() {
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
  }
  window.addEventListener('resize', resizeCanvas);
  resizeCanvas();

  function drawRadar() {
    const w = canvas.width / window.devicePixelRatio;
    const h = canvas.height / window.devicePixelRatio;
    const cx = w / 2;
    const cy = h / 2;
    const maxRadius = Math.min(cx, cy) * 0.88;

    ctx.clearRect(0, 0, w, h);

    // Color del acento según el modo
    const accentColor = getComputedStyle(document.body).getPropertyValue('--accent').trim() || '#00f0ff';

    // Círculos concéntricos
    ctx.lineWidth = 1;
    for (let r = 0.25; r <= 1.0; r += 0.25) {
      ctx.beginPath();
      ctx.arc(cx, cy, maxRadius * r, 0, Math.PI * 2);
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
      ctx.stroke();
    }

    // Líneas cardinales de la retícula
    ctx.beginPath();
    ctx.moveTo(cx - maxRadius, cy);
    ctx.lineTo(cx + maxRadius, cy);
    ctx.moveTo(cx, cy - maxRadius);
    ctx.lineTo(cx, cy + maxRadius);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
    ctx.stroke();

    // Barrido giratorio del radar
    AppState.radarAngle += 0.025;
    if (AppState.radarAngle > Math.PI * 2) AppState.radarAngle -= Math.PI * 2;

    const sweepGrad = ctx.createConicGradient(AppState.radarAngle, cx, cy);
    sweepGrad.addColorStop(0, accentColor);
    sweepGrad.addColorStop(0.15, 'transparent');
    sweepGrad.addColorStop(1, 'transparent');

    ctx.fillStyle = sweepGrad;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, maxRadius, AppState.radarAngle, AppState.radarAngle + 0.35);
    ctx.fill();

    // Línea líder del barrido
    const lx = cx + Math.cos(AppState.radarAngle) * maxRadius;
    const ly = cy + Math.sin(AppState.radarAngle) * maxRadius;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(lx, ly);
    ctx.strokeStyle = accentColor;
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Dibujar nodos detectados
    AppState.radarNodes.forEach((node, i) => {
      const nx = cx + Math.cos(node.angle) * (maxRadius * node.dist);
      const ny = cy + Math.sin(node.angle) * (maxRadius * node.dist);

      // Calcular proximidad con el barrido para encendido brillante
      let diff = Math.abs(AppState.radarAngle - node.angle);
      if (diff > Math.PI) diff = Math.PI * 2 - diff;
      const isLit = diff < 0.25;

      ctx.beginPath();
      ctx.arc(nx, ny, isLit ? 5 : 3.5, 0, Math.PI * 2);
      ctx.fillStyle = isLit ? '#ffffff' : (node.color || accentColor);
      ctx.shadowBlur = isLit ? 12 : 6;
      ctx.shadowColor = node.color || accentColor;
      ctx.fill();
      ctx.shadowBlur = 0;

      // Etiqueta del nodo
      ctx.font = '9px JetBrains Mono, monospace';
      ctx.fillStyle = isLit ? '#ffffff' : 'rgba(226, 241, 245, 0.6)';
      ctx.fillText(node.label, nx + 8, ny + 3);
    });

    requestAnimationFrame(drawRadar);
  }

  requestAnimationFrame(drawRadar);
}

// =====================================================================
// CONEXIÓN CON EL SERVIDOR HTTP TÁCTICO (/api)
// =====================================================================
async function fetchServerStatus() {
  try {
    const res = await fetch('/api/status');
    if (res.ok) {
      const data = await res.json();
      if (data.local_ip) {
        AppState.localIp = data.local_ip;
        AppState.serverPort = data.port || 8080;
        updateWifiChip();
      }
      if (data.findings_count) {
        fetchFindings();
      }
      printTermLine(`[ENLACE SERVIDOR] Conectado exitosamente al daemon de Anonymous (${data.local_ip}:${data.port}).`, 'success');
    }
  } catch (err) {
    // Si no está corriendo el backend, el boceto interactúa en modo cliente autónomo
    console.info('Servidor API en modo local/standalone:', err.message);
    updateWifiChip();
  }
}

async function fetchFindings() {
  try {
    const res = await fetch('/api/findings');
    if (res.ok) {
      const data = await res.json();
      if (data.findings && data.findings.length > 0) {
        AppState.findings = data.findings;
        renderFindings();
      }
    }
  } catch (e) {}
}

function updateWifiChip() {
  const el = document.getElementById('wifi-display-text');
  if (el) {
    el.textContent = `WI-FI: http://${AppState.localIp}:${AppState.serverPort}`;
  }
}

function copyWifiLink() {
  const url = `http://${AppState.localIp}:${AppState.serverPort}`;
  navigator.clipboard.writeText(url).then(() => {
    showToast(`✓ Enlace Wi-Fi copiado: ${url}`);
  }).catch(() => {
    showToast(`URL: ${url}`);
  });
}

// =====================================================================
// SELECTOR DE MODOS TÁCTICOS
// =====================================================================
function switchMode(newMode) {
  AppState.mode = newMode;
  document.body.setAttribute('data-mode', newMode);

  // Actualizar botones activos
  document.querySelectorAll('.mode-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-mode') === newMode);
  });

  const radarModeEl = document.getElementById('radar-mode-val');
  if (radarModeEl) {
    radarModeEl.textContent = `MODO ${newMode.toUpperCase()}`;
  }

  // Notificar al servidor si está activo
  fetch('/api/mode', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode: newMode })
  }).catch(() => {});

  printTermLine(`[SISTEMA] Modo táctico conmutado a: ${newMode.toUpperCase()}`, 'alert');
  showToast(`Modo cambiado: ${newMode.toUpperCase()}`);
}

// =====================================================================
// MOTOR DE ESCANEO DE PUERTOS (RED TEAM)
// =====================================================================
function initEventListeners() {
  // Toggle de etiquetas de puertos
  document.querySelectorAll('#port-selector-container .port-tag').forEach(tag => {
    tag.addEventListener('click', () => {
      tag.classList.toggle('active');
    });
  });

  // Enter en el input de la terminal
  const termInput = document.getElementById('terminal-input');
  if (termInput) {
    termInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        sendTerminalCommand();
      } else if (e.key === 'ArrowUp') {
        navigateHistory(-1);
      } else if (e.key === 'ArrowDown') {
        navigateHistory(1);
      }
    });
  }

  // Enter en el buscador RAG
  const ragInput = document.getElementById('rag-search-input');
  if (ragInput) {
    ragInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') searchRAG();
    });
  }

  // Checkbox de modo seguro
  const safeToggle = document.getElementById('safe-mode-toggle');
  if (safeToggle) {
    safeToggle.addEventListener('change', (e) => {
      AppState.safeMode = e.target.checked;
      showToast(AppState.safeMode ? 'AgentShield: HITL Activado' : 'AgentShield: HITL Desactivado');
    });
  }
}

function getSelectedPorts() {
  const activeTags = document.querySelectorAll('#port-selector-container .port-tag.active');
  const ports = [];
  activeTags.forEach(tag => {
    ports.push(parseInt(tag.getAttribute('data-port'), 10));
  });
  return ports.length > 0 ? ports : [80, 443, 8080];
}

async function triggerScan() {
  const targetInput = document.getElementById('target-ip-input');
  const target = targetInput ? targetInput.value.trim() : '127.0.0.1';
  AppState.target = target;
  document.getElementById('radar-target-val').textContent = target;

  const ports = getSelectedPorts();

  // Verificación AgentShield (HITL) para IPs no locales
  const isLocal = (target === '127.0.0.1' || target === 'localhost' || target === AppState.localIp);
  if (AppState.safeMode && !isLocal) {
    triggerHitlModal(target, () => doExecuteScan(target, ports));
    return;
  }

  doExecuteScan(target, ports);
}

async function doExecuteScan(target, ports) {
  printTermLine(`[RECON] Iniciando escaneo TCP de sockets sobre ${target} (${ports.length} puertos)...`, 'alert');
  
  const progBar = document.getElementById('scan-progress-bar');
  const progFill = document.getElementById('scan-progress-fill');
  if (progBar) progBar.style.display = 'block';
  if (progFill) progFill.style.width = '30%';

  try {
    const res = await fetch('/api/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target, ports })
    });

    if (progFill) progFill.style.width = '80%';

    if (res.ok) {
      const data = await res.json();
      if (progFill) progFill.style.width = '100%';
      setTimeout(() => { if (progBar) progBar.style.display = 'none'; }, 400);

      const openPorts = data.open_ports || [];
      if (openPorts.length > 0) {
        printTermLine(`[RESULTADO] ${target}: ${openPorts.length} puertos abiertos detectados:`, 'success');
        openPorts.forEach(p => {
          printTermLine(`  -> TCP/${p.port} (${p.service || 'servicio'}) - ${p.latency_ms}ms`, 'success');
          // Agregar al radar dinámicamente
          AppState.radarNodes.push({
            angle: Math.random() * Math.PI * 2,
            dist: 0.3 + Math.random() * 0.5,
            label: `TCP/${p.port}`,
            color: '#00f985'
          });
        });
      } else {
        printTermLine(`[RESULTADO] No se detectaron puertos abiertos en ${target} para los puertos seleccionados.`, 'error');
      }

      // Refrescar hallazgos
      fetchFindings();
      advancePTTToScanDone();
      return;
    }
  } catch (e) {
    // Modo simulación cliente si no hay backend activo
  }

  // Fallback simulado autónomo
  setTimeout(() => {
    if (progFill) progFill.style.width = '100%';
    setTimeout(() => { if (progBar) progBar.style.display = 'none'; }, 400);

    printTermLine(`[EMULADOR] Escaneo de socket finalizado en ${target}.`, 'success');
    printTermLine(`  -> TCP/8080 (http-alt / Tactical Server) - 0.4ms`, 'success');
    
    // Registrar hallazgo
    AppState.findings.unshift({
      id: AppState.findings.length + 1,
      title: `Puerto TCP/8080 Abierto en ${target}`,
      target: target,
      severity: "INFO",
      description: "Servicio detectado disponible para conexiones locales y Wi-Fi.",
      timestamp: new Date().toTimeString().split(' ')[0]
    });
    renderFindings();
    advancePTTToScanDone();
  }, 600);
}

function advancePTTToScanDone() {
  AppState.pttTree.forEach(node => {
    if (node.id === 'T2') node.status = 'completed';
    if (node.id === 'T3') node.status = 'in_progress';
  });
  renderPTT();
}

// =====================================================================
// AGENTSHIELD HITL MODAL
// =====================================================================
function triggerHitlModal(target, onConfirm) {
  AppState.pendingAction = onConfirm;
  const modal = document.getElementById('hitl-modal');
  const targetDisplay = document.getElementById('modal-target-display');
  if (targetDisplay) targetDisplay.textContent = target;
  if (modal) modal.classList.add('open');
}

function cancelHitlAction() {
  AppState.pendingAction = null;
  const modal = document.getElementById('hitl-modal');
  if (modal) modal.classList.remove('open');
  printTermLine('[AgentShield HITL] Operación cancelada por el usuario.', 'alert');
  showToast('Acción cancelada');
}

function confirmHitlAction() {
  const modal = document.getElementById('hitl-modal');
  if (modal) modal.classList.remove('open');
  if (typeof AppState.pendingAction === 'function') {
    const action = AppState.pendingAction;
    AppState.pendingAction = null;
    printTermLine('[AgentShield HITL] Autorización confirmada manualmente por el operador.', 'success');
    showToast('✓ Operación autorizada');
    action();
  }
}

// =====================================================================
// ÁRBOL PTT (PENTEST TASK TREE)
// =====================================================================
function renderPTT() {
  const container = document.getElementById('ptt-tree-container');
  if (!container) return;

  container.innerHTML = AppState.pttTree.map(item => {
    let badgeClass = 'wait';
    let badgeText = 'PENDIENTE';

    if (item.status === 'completed') {
      badgeClass = 'ok';
      badgeText = 'COMPLETADO';
    } else if (item.status === 'in_progress') {
      badgeClass = 'running';
      badgeText = 'EN PROGRESO';
    }

    return `
      <div class="ptt-node ${item.status}" onclick="inspectPTTNode('${item.id}')">
        <div class="ptt-node-header">
          <span>${item.id} - ${item.phase}: ${item.title}</span>
          <span class="ptt-badge ${badgeClass}">${badgeText}</span>
        </div>
        <div class="ptt-node-desc">${item.details}</div>
      </div>
    `;
  }).join('');
}

function inspectPTTNode(id) {
  const node = AppState.pttTree.find(n => n.id === id);
  if (!node) return;
  printTermLine(`[PTT ${node.id}] Fase: ${node.phase} | Estado: ${node.status.toUpperCase()}`, 'alert');
  printTermLine(`Detalles: ${node.details}`, 'term-output');
}

function resetPTT() {
  AppState.pttTree = [
    { id: "T1", phase: "Reconocimiento", title: "Descubrimiento de Interfaces y Sockets", status: "completed", details: "Host local mapeado y enlace Wi-Fi verificado en subred." },
    { id: "T2", phase: "Escaneo", title: "Mapeo de Puertos TCP Críticos", status: "in_progress", details: "Sondeo de puertos estándar con motor de sockets concurrentes." },
    { id: "T3", phase: "Enumeración", title: "Identificación de Versiones y Servicios", status: "pending", details: "Captura de banners HTTP/SSH y metadatos de servicios." },
    { id: "T4", phase: "Evaluación Defensiva", title: "Cotejo Normativo RAG", status: "pending", details: "Comparación de hallazgos contra marcos OWASP y MITRE." },
    { id: "T5", phase: "Reporte", title: "Sugerencias de Mitigación e Informe", status: "pending", details: "Consolidación de bitácora y exportación para Obsidian." }
  ];
  renderPTT();
  printTermLine('[PTT] Árbol de tareas reiniciado al estado inicial.', 'alert');
  showToast('Árbol PTT reiniciado');
}

// =====================================================================
// HALLAZGOS (FINDINGS)
// =====================================================================
function renderFindings() {
  const container = document.getElementById('findings-container');
  const counter = document.getElementById('findings-counter');
  if (!container) return;

  if (counter) counter.textContent = `${AppState.findings.length} EVENTOS`;

  container.innerHTML = AppState.findings.map(f => `
    <div class="finding-item">
      <div class="finding-header">
        <strong style="color: var(--text-bright);">${f.title}</strong>
        <span class="finding-sev ${f.severity}">${f.severity}</span>
      </div>
      <div style="font-size: 11px; color: var(--text-muted);">${f.description}</div>
      <div style="font-size: 10px; color: var(--accent); font-family: var(--font-mono);">${f.target} • ${f.timestamp}</div>
    </div>
  `).join('');
}

// =====================================================================
// TERMINAL TÁCTICA & CLI
// =====================================================================
function printTermLine(text, styleClass = '') {
  const screen = document.getElementById('term-screen');
  if (!screen) return;

  const line = document.createElement('div');
  line.className = `term-line ${styleClass}`;
  line.textContent = text;
  screen.appendChild(line);
  screen.scrollTop = screen.scrollHeight;
}

function executeQuickCommand(cmd) {
  const input = document.getElementById('terminal-input');
  if (input) input.value = cmd;
  sendTerminalCommand();
}

async function sendTerminalCommand() {
  const input = document.getElementById('terminal-input');
  if (!input) return;
  const raw = input.value.trim();
  if (!raw) return;

  input.value = '';
  AppState.commandHistory.push(raw);
  AppState.historyIndex = AppState.commandHistory.length;

  printTermLine(`anonymous@tactical:~$ ${raw}`, 'term-prompt');

  // Procesar comandos locales rápidos
  const parts = raw.split(' ');
  const verb = parts[0].toLowerCase();

  if (verb === 'clear') {
    const screen = document.getElementById('term-screen');
    if (screen) screen.innerHTML = '';
    return;
  }

  if (verb === 'help') {
    printTermLine('Comandos tácticos disponibles:', 'alert');
    printTermLine('  • status         - Muestra telemetría del sistema e IP Wi-Fi');
    printTermLine('  • scan <ip>      - Ejecuta escaneo TCP con sockets nativos');
    printTermLine('  • ping <ip>      - Prueba conectividad rápida a socket');
    printTermLine('  • rag <norma>    - Consulta normativas OWASP, MITRE o CIS');
    printTermLine('  • ptt            - Muestra estado del árbol de tareas');
    printTermLine('  • findings       - Lista eventos registrados en la sesión');
    printTermLine('  • mode <modo>    - Cambia modo (attack, defense, normal)');
    printTermLine('  • clear          - Limpia la pantalla de la terminal');
    return;
  }

  if (verb === 'mode') {
    const m = parts[1] ? parts[1].toLowerCase() : 'normal';
    switchMode(m);
    return;
  }

  // Enviar comando al servidor backend
  try {
    const res = await fetch('/api/command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: raw, confirmed: !AppState.safeMode })
    });

    if (res.ok) {
      const data = await res.json();
      const r = data.result || {};

      if (r.type === 'agentshield_alert') {
        printTermLine(r.message, 'error');
        triggerHitlModal(r.target, () => {
          fetch('/api/command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: raw, confirmed: true })
          }).then(res2 => res2.json()).then(d2 => {
            printTermLine(d2.result.message || JSON.stringify(d2.result), 'success');
          });
        });
        return;
      }

      printTermLine(r.message || JSON.stringify(r), 'term-output');
      return;
    }
  } catch (e) {
    // Si la API falla, responder localmente
  }

  // Fallback local
  if (verb === 'status') {
    printTermLine(`ANONYMOUS TACTICAL ONLINE // IP Wi-Fi: ${AppState.localIp} // Puerto: ${AppState.serverPort}`, 'success');
  } else if (verb === 'scan') {
    const target = parts[1] || '127.0.0.1';
    doExecuteScan(target, getSelectedPorts());
  } else if (verb === 'rag') {
    filterRAG(parts[1] || 'owasp');
    printTermLine(`Mostrando normativas para '${parts[1] || 'owasp'}' en el panel Blue Team.`, 'success');
  } else if (verb === 'ptt') {
    printTermLine(`Árbol PTT cargado con ${AppState.pttTree.length} fases.`, 'alert');
  } else if (verb === 'findings') {
    printTermLine(`${AppState.findings.length} hallazgos registrados.`, 'success');
  } else {
    printTermLine(`Comando '${raw}' procesado. Escribe 'help' para ver la lista de comandos.`, 'term-output');
  }
}

function navigateHistory(direction) {
  if (AppState.commandHistory.length === 0) return;
  AppState.historyIndex += direction;
  if (AppState.historyIndex < 0) AppState.historyIndex = 0;
  if (AppState.historyIndex >= AppState.commandHistory.length) {
    AppState.historyIndex = AppState.commandHistory.length;
    document.getElementById('terminal-input').value = '';
    return;
  }
  document.getElementById('terminal-input').value = AppState.commandHistory[AppState.historyIndex];
}

// =====================================================================
// MOTOR BLUE TEAM: ASESOR NORMATIVO RAG
// =====================================================================
function filterRAG(category) {
  AppState.ragCategory = category;
  ['owasp', 'mitre', 'cis'].forEach(cat => {
    const btn = document.getElementById(`btn-rag-${cat}`);
    if (btn) btn.classList.toggle('active', cat === category);
  });
  renderRAG(category);
}

function searchRAG() {
  const query = document.getElementById('rag-search-input').value.toLowerCase().trim();
  if (!query) {
    renderRAG(AppState.ragCategory);
    return;
  }

  const container = document.getElementById('rag-container');
  if (!container) return;

  const allItems = [...DEFAULT_RAG_DATA.owasp, ...DEFAULT_RAG_DATA.mitre, ...DEFAULT_RAG_DATA.cis];
  const filtered = allItems.filter(item => 
    item.title.toLowerCase().includes(query) ||
    item.id.toLowerCase().includes(query) ||
    (item.desc && item.desc.toLowerCase().includes(query)) ||
    (item.remediation && item.remediation.toLowerCase().includes(query))
  );

  if (filtered.length === 0) {
    container.innerHTML = `<div style="font-size: 11px; color: var(--text-muted); padding: 10px;">No se encontraron normativas para "${query}".</div>`;
    return;
  }

  renderRAGList(filtered);
}

function renderRAG(category) {
  const items = DEFAULT_RAG_DATA[category] || DEFAULT_RAG_DATA.owasp;
  renderRAGList(items);
}

function renderRAGList(items) {
  const container = document.getElementById('rag-container');
  if (!container) return;

  container.innerHTML = items.map(item => `
    <div class="rag-card-item">
      <div class="rag-card-header">
        <span class="rag-id">${item.id}: ${item.title}</span>
        <span class="rag-cat">${item.category}</span>
      </div>
      <div class="rag-desc">${item.desc}</div>
      <div class="rag-rem">
        <strong>🛡️ Mitigación:</strong> ${item.remediation}
      </div>
    </div>
  `).join('');
}

// =====================================================================
// NOTIFICACIONES HUD (TOASTS)
// =====================================================================
function showToast(msg) {
  const shelf = document.getElementById('toast-shelf');
  if (!shelf) return;

  const toast = document.createElement('div');
  toast.className = 'hud-toast';
  toast.textContent = msg;
  shelf.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.4s ease';
    setTimeout(() => toast.remove(), 400);
  }, 3200);
}
