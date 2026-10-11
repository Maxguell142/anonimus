document.addEventListener("DOMContentLoaded", () => {
  const chatHistory = document.getElementById("chat-history");
  const chatInput = document.getElementById("chat-input");
  const btnSend = document.getElementById("btn-send");
  const btnVoice = document.getElementById("btn-voice");
  const pttContainer = document.getElementById("ptt-container");
  const findingsContainer = document.getElementById("findings-container");
  const badgeOs = document.getElementById("badge-os");
  const badgeIp = document.getElementById("badge-ip");

  const btnScan = document.getElementById("btn-scan");
  const btnRag = document.getElementById("btn-rag");
  const btnBriefing = document.getElementById("btn-briefing");
  const btnResetPtt = document.getElementById("btn-reset-ptt");

  // Load Initial Data
  loadStatus();
  loadPtt();
  loadFindings();

  // Polling every 5 seconds for live PTT / findings updates
  setInterval(() => {
    loadPtt();
    loadFindings();
  }, 5000);

  async function loadStatus() {
    try {
      const res = await fetch("/api/status");
      const data = await res.json();
      if (data && data.system_info) {
        badgeOs.textContent = `🖥️ ${data.system_info.os} (${data.system_info.hostname})`;
        badgeIp.textContent = `🌐 IP: ${data.system_info.local_ip}`;
      }
    } catch (e) {
      console.error("Error loading status:", e);
    }
  }

  async function loadPtt() {
    try {
      const res = await fetch("/api/ptt");
      const data = await res.json();
      if (data && data.tasks) {
        renderPtt(data.tasks);
      }
    } catch (e) {
      console.error("Error loading PTT:", e);
    }
  }

  async function loadFindings() {
    try {
      const res = await fetch("/api/findings");
      const data = await res.json();
      if (data && data.findings) {
        renderFindings(data.findings);
      }
    } catch (e) {
      console.error("Error loading findings:", e);
    }
  }

  function renderPtt(tasks) {
    if (!tasks || tasks.length === 0) {
      pttContainer.innerHTML = '<div style="font-size: 0.8rem; color: var(--text-dim);">Sin tareas PTT.</div>';
      return;
    }

    let html = "";
    tasks.forEach(t => {
      const statusClass = `status-${t.status || 'pending'}`;
      html += `
        <div class="ptt-item">
          <div class="ptt-header">
            <strong>${t.name}</strong>
            <span class="badge-status ${statusClass}">${t.status || 'pending'}</span>
          </div>
          <div style="font-size: 0.72rem; color: var(--text-dim);">${t.phase} ${t.details ? '• ' + t.details : ''}</div>
        </div>
      `;
    });
    pttContainer.innerHTML = html;
  }

  function renderFindings(findings) {
    if (!findings || findings.length === 0) {
      findingsContainer.innerHTML = '<div style="font-size: 0.8rem; color: var(--text-dim);">Sin hallazgos registrados.</div>';
      return;
    }

    let html = '<table class="results-table"><thead><tr><th>Objetivo</th><th>Sev</th><th>Título</th></tr></thead><tbody>';
    findings.forEach(f => {
      const color = f.severity === 'HIGH' ? 'var(--accent-red)' : 'var(--accent-yellow)';
      html += `
        <tr>
          <td>${f.target}</td>
          <td style="color: ${color}; font-weight: bold;">${f.severity}</td>
          <td>${f.title}</td>
        </tr>
      `;
    });
    html += '</tbody></table>';
    findingsContainer.innerHTML = html;
  }

  function appendMessage(role, text) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${role}`;
    
    const meta = document.createElement("div");
    meta.className = "message-meta";
    meta.textContent = role === "user" ? "Tú" : "⚡ Anonymous Core";

    const body = document.createElement("div");
    body.className = "message-body";
    body.innerHTML = text.replace(/\n/g, "<br>");

    msgDiv.appendChild(meta);
    msgDiv.appendChild(body);
    chatHistory.appendChild(msgDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
  }

  async function sendInput(text) {
    if (!text.trim()) return;
    appendMessage("user", text);
    chatInput.value = "";

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
      });
      const data = await res.json();
      
      let reply = data.message || "Operación procesada.";
      if (data.type === "scan" && data.data && data.data.ports) {
        reply += "<br><br><strong>Puertos encontrados:</strong><br>";
        data.data.ports.forEach(p => {
          reply += `• Puerto <code>${p.port}</code>: ${p.service} (${p.banner || 'Abierto'})<br>`;
        });
      }

      appendMessage("assistant", reply);
      loadPtt();
      loadFindings();
    } catch (e) {
      appendMessage("assistant", "⚠️ Error al conectar con el servidor local: " + e.message);
    }
  }

  // Event Listeners
  btnSend.addEventListener("click", () => sendInput(chatInput.value));
  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendInput(chatInput.value);
  });

  btnScan.addEventListener("click", () => {
    const target = document.getElementById("scan-target").value.trim() || "127.0.0.1";
    const ports = document.getElementById("scan-ports").value.trim();
    const cmd = ports ? `scan ${target} ${ports}` : `scan ${target}`;
    sendInput(cmd);
  });

  btnRag.addEventListener("click", () => {
    const query = document.getElementById("rag-query").value.trim() || "OWASP";
    sendInput(`rag ${query}`);
  });

  btnBriefing.addEventListener("click", () => sendInput("status"));
  btnResetPtt.addEventListener("click", () => sendInput("ptt reset"));

  // Voice Dictation (Web Speech API)
  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'es-ES';
    recognition.continuous = false;

    btnVoice.addEventListener("click", () => {
      recognition.start();
      btnVoice.style.background = "var(--accent-red)";
      btnVoice.textContent = "🛑";
    });

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      chatInput.value = transcript;
      btnVoice.style.background = "";
      btnVoice.textContent = "🎙️";
    };

    recognition.onerror = () => {
      btnVoice.style.background = "";
      btnVoice.textContent = "🎙️";
    };

    recognition.onend = () => {
      btnVoice.style.background = "";
      btnVoice.textContent = "🎙️";
    };
  } else {
    btnVoice.title = "Dictado por voz no soportado por este navegador.";
  }
});
