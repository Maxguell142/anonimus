/**
 * Anonymous Glyph Stream
 * Canvas implementation of a liquid glyph cursor trail for the static HUD.
 * The canvas never captures input, so the dashboard remains fully interactive.
 */
(() => {
  const canvas = document.getElementById("glyph-stream-canvas");
  if (!canvas || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  const context = canvas.getContext("2d", { alpha: true });
  if (!context) return;

  const cellSize = 13;
  const cellGap = 2;
  const spacing = cellSize + cellGap;
  const trailSeconds = 0.78;
  const glyphs = "ANONYMOUS0123456789ABCDEF<>/{}[]#";
  const cells = new Map();
  const pointer = { x: 0, y: 0, active: false, lastX: 0, lastY: 0, lastAt: 0 };
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  let width = 0;
  let height = 0;
  let pixelRatio = 1;
  let accent = "#00f0ff";
  let tail = "#008f99";
  let lastPaletteRead = 0;
  let previousFrame = 0;
  let animationFrame = 0;
  let lastMoveAt = 0;

  function resize() {
    pixelRatio = Math.min(window.devicePixelRatio || 1, 1.75);
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = Math.round(width * pixelRatio);
    canvas.height = Math.round(height * pixelRatio);
    context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
  }

  function readPalette(now) {
    if (now - lastPaletteRead < 450) return;
    const style = getComputedStyle(document.body);
    accent = style.getPropertyValue("--accent").trim() || accent;
    tail = style.getPropertyValue("--accent-dim").trim() || tail;
    lastPaletteRead = now;
  }

  function randomGlyph() {
    return glyphs[Math.floor(Math.random() * glyphs.length)];
  }

  function addCell(x, y, vx = 0, vy = 0, lifetime = trailSeconds) {
    const column = Math.floor(x / spacing);
    const row = Math.floor(y / spacing);
    const key = `${column}:${row}`;
    const now = performance.now();
    const old = cells.get(key);
    cells.set(key, {
      x: column * spacing + cellGap / 2,
      y: row * spacing + cellGap / 2,
      vx,
      vy,
      born: now,
      lifetime,
      glyph: randomGlyph(),
      scrambledAt: now,
      salt: Math.random(),
      splash: Boolean(old && old.splash),
    });
  }

  function pourSegment(x1, y1, x2, y2, speed) {
    const distance = Math.hypot(x2 - x1, y2 - y1);
    const steps = Math.max(1, Math.ceil(distance / (spacing * 0.42)));
    const push = Math.min(speed * 0.018, 1.4);
    const vx = distance ? ((x1 - x2) / distance) * push : 0;
    const vy = distance ? ((y1 - y2) / distance) * push : 0;

    for (let step = 0; step <= steps; step += 1) {
      const progress = step / steps;
      addCell(x1 + (x2 - x1) * progress, y1 + (y2 - y1) * progress, vx, vy);
    }
  }

  function splash(x, y) {
    const count = 24;
    for (let i = 0; i < count; i += 1) {
      const angle = (Math.PI * 2 * i) / count + (Math.random() - 0.5) * 0.24;
      const speed = 38 + Math.random() * 112;
      const vx = Math.cos(angle) * speed;
      const vy = Math.sin(angle) * speed - 22;
      const lifetime = 0.42 + Math.random() * 0.55;
      const column = Math.floor((x + Math.cos(angle) * (8 + Math.random() * 30)) / spacing);
      const row = Math.floor((y + Math.sin(angle) * (8 + Math.random() * 30)) / spacing);
      const key = `${column}:${row}`;
      const now = performance.now();
      cells.set(key, {
        x: column * spacing + cellGap / 2,
        y: row * spacing + cellGap / 2,
        vx,
        vy,
        born: now,
        lifetime,
        glyph: randomGlyph(),
        scrambledAt: now,
        salt: Math.random(),
        splash: true,
      });
    }
  }

  function onPointerMove(event) {
    const now = performance.now();
    const x = event.clientX;
    const y = event.clientY;
    if (!pointer.active) {
      pointer.active = true;
      pointer.x = pointer.lastX = x;
      pointer.y = pointer.lastY = y;
      pointer.lastAt = now;
      return;
    }

    const elapsed = Math.max((now - pointer.lastAt) / 1000, 1 / 240);
    const speed = Math.hypot(x - pointer.x, y - pointer.y) / elapsed;
    pourSegment(pointer.x, pointer.y, x, y, speed);
    pointer.lastX = pointer.x;
    pointer.lastY = pointer.y;
    pointer.x = x;
    pointer.y = y;
    pointer.lastAt = now;
    lastMoveAt = now;
  }

  function draw(now) {
    animationFrame = requestAnimationFrame(draw);
    if (document.hidden || reducedMotion.matches || now - previousFrame < 30) return;
    previousFrame = now;
    readPalette(now);
    context.clearRect(0, 0, width, height);

    if (pointer.active && now - lastMoveAt > 80 && now - pointer.lastAt > 80) {
      const elapsed = Math.min((now - pointer.lastAt) / 1000, 0.06);
      for (const cell of cells.values()) {
        if (!cell.splash && now - cell.born < 100) {
          cell.vx += ((pointer.x - cell.x) * 0.0004 - cell.vx) * elapsed;
          cell.vy += ((pointer.y - cell.y) * 0.0004 - cell.vy) * elapsed;
        }
      }
      pointer.lastAt = now;
    }

    for (const [key, cell] of cells) {
      const age = (now - cell.born) / 1000;
      const life = age / cell.lifetime;
      if (life >= 1) {
        cells.delete(key);
        continue;
      }

      const delta = Math.min((now - (cell.updatedAt || cell.born)) / 1000, 0.05);
      cell.updatedAt = now;
      cell.x += cell.vx * delta;
      cell.y += cell.vy * delta;
      if (cell.splash) cell.vy += 105 * delta;
      else {
        cell.vx *= 0.985;
        cell.vy *= 0.985;
      }

      if (now - cell.scrambledAt > 125 && life < 0.36) {
        cell.glyph = randomGlyph();
        cell.scrambledAt = now;
      }

      const fade = Math.pow(1 - life, 1.45);
      context.globalAlpha = fade * (0.17 + (1 - life) * 0.25);
      context.fillStyle = life < 0.3 ? accent : tail;
      context.beginPath();
      context.roundRect(cell.x, cell.y, cellSize, cellSize, 2);
      context.fill();

      context.globalAlpha = fade * (0.34 + (1 - life) * 0.5);
      context.fillStyle = "#e2f1f5";
      context.font = `600 ${Math.round(cellSize * 0.56)}px "JetBrains Mono", monospace`;
      context.textAlign = "center";
      context.textBaseline = "middle";
      context.fillText(cell.glyph, cell.x + cellSize / 2, cell.y + cellSize / 2 + 0.5);
    }
    context.globalAlpha = 1;

    if (now - lastMoveAt > 1800) pointer.active = false;
  }

  reducedMotion.addEventListener("change", (event) => {
    if (event.matches) {
      cancelAnimationFrame(animationFrame);
      context.clearRect(0, 0, width, height);
      cells.clear();
    } else {
      previousFrame = 0;
      animationFrame = requestAnimationFrame(draw);
    }
  });

  window.addEventListener("resize", resize, { passive: true });
  window.addEventListener("pointermove", onPointerMove, { passive: true });
  window.addEventListener("pointerdown", (event) => splash(event.clientX, event.clientY), { passive: true });
  window.addEventListener("blur", () => {
    pointer.active = false;
  });
  resize();
  animationFrame = requestAnimationFrame(draw);
})();
