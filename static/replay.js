/**
 * Game replay viewer: step through snaps, toggle fog POV.
 */
(function () {
  const dataEl = document.getElementById("replay-data");
  if (!dataEl) return;

  let data;
  try {
    data = JSON.parse(dataEl.textContent || "{}");
  } catch {
    return;
  }
  if (!data.steps || data.steps.length === 0) return;

  const boardEl = document.getElementById("replay-board");
  const capWhite = document.getElementById("replay-captured-white");
  const capBlack = document.getElementById("replay-captured-black");
  const fogSelect = document.getElementById("fog-mode");
  const traceToggle = document.getElementById("trace-move");
  const counterEl = document.getElementById("replay-counter");
  const moveLabel = document.getElementById("replay-move-label");

  let stepIndex = 0;
  const maxIndex = data.steps.length - 1;

  if (typeof window.__REPLAY_INITIAL_STEP__ === "number") {
    const n = data.steps.findIndex((s) => s.n === window.__REPLAY_INITIAL_STEP__);
    stepIndex = n >= 0 ? n : maxIndex;
  }

  const STARTING = { q: 1, r: 2, b: 2, n: 2, p: 8 };

  function squareIndex(file, rank) {
    return rank * 8 + file;
  }

  function visibleSquares(squares, color) {
    const vis = new Array(64).fill(false);
    for (let i = 0; i < 64; i++) {
      const p = squares[i];
      if (!p || p.color !== color) continue;
      vis[i] = true;
      const rank = Math.floor(i / 8);
      const file = i % 8;
      for (let dr = -1; dr <= 1; dr++) {
        for (let df = -1; df <= 1; df++) {
          const f = file + df;
          const r = rank + dr;
          if (f >= 0 && f < 8 && r >= 0 && r < 8) {
            vis[squareIndex(f, r)] = true;
          }
        }
      }
    }
    return vis;
  }

  function countMaterial(squares, color) {
    const c = { q: 0, r: 0, b: 0, n: 0, p: 0 };
    for (const p of squares) {
      if (!p || p.color !== color) continue;
      const k = (p.kind || "p").toLowerCase();
      if (c[k] !== undefined) c[k]++;
    }
    return c;
  }

  function capturedTray(color, squares) {
    const on = countMaterial(squares, color);
    const order = ["q", "r", "b", "n", "p"];
    const label = color === "white" ? "White takes" : "Black takes";
    const victim = color === "white" ? "black" : "white";
    let html = `<span class="captured-label">${label}</span>`;
    let any = false;
    for (const k of order) {
      const missing = (STARTING[k] || 0) - (on[k] || 0);
      for (let i = 0; i < missing; i++) {
        html += `<span class="captured-piece ${victim}">${k.toUpperCase()}</span>`;
        any = true;
      }
    }
    if (!any) html += '<span class="captured-empty"> —</span>';
    return html;
  }

  function parseUci(uci) {
    if (!uci || uci.length < 4) return null;
    const from = uci.slice(0, 2).toLowerCase();
    const to = uci.slice(2, 4).toLowerCase();
    if (!/^[a-h][1-8]$/.test(from) || !/^[a-h][1-8]$/.test(to)) return null;
    return { from, to };
  }

  function traceForStep(step) {
    if (!traceToggle?.checked) return null;
    const parsed = parseUci(step.uci);
    if (!parsed) return null;
    return {
      from: parsed.from,
      to: parsed.to,
      actual: step.actual_to || null,
    };
  }

  function sqCenter(sq) {
    const file = sq.charCodeAt(0) - 97;
    const rank = parseInt(sq[1], 10) - 1;
    return { x: file + 0.5, y: 7 - rank + 0.5 };
  }

  const mobileMq = window.matchMedia("(max-width: 767px)");

  function arrowStyle() {
    if (mobileMq.matches) {
      return {
        markerW: 6,
        markerH: 6,
        refX: 5,
        refY: 3,
        headPath: "M0,0 L6,3 L0,6 Z",
        strokePlayed: 0.14,
        strokeGhost: 0.12,
        dashGhost: "0.12 0.1",
      };
    }
    return {
      markerW: 3,
      markerH: 3,
      refX: 2.5,
      refY: 1.5,
      headPath: "M0,0 L3,1.5 L0,3 Z",
      strokePlayed: 0.07,
      strokeGhost: 0.06,
      dashGhost: "0.06 0.05",
    };
  }

  function lineEnds(a, b, padStart, padEnd) {
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const len = Math.hypot(dx, dy) || 1;
    return {
      x1: a.x + (dx / len) * padStart,
      y1: a.y + (dy / len) * padStart,
      x2: b.x - (dx / len) * padEnd,
      y2: b.y - (dy / len) * padEnd,
    };
  }

  function moveArrowSvg(trace) {
    const from = sqCenter(trace.from);
    const to = sqCenter(trace.to);
    const truncated = trace.actual && trace.actual !== trace.to;
    const actual = truncated ? sqCenter(trace.actual) : to;
    const a = arrowStyle();

    const defs = `<defs>
      <marker id="replay-arrowhead" markerWidth="${a.markerW}" markerHeight="${a.markerH}" refX="${a.refX}" refY="${a.refY}" orient="auto">
        <path class="move-arrowhead" d="${a.headPath}"/>
      </marker>
      <marker id="replay-arrowhead-ghost" markerWidth="${a.markerW}" markerHeight="${a.markerH}" refX="${a.refX}" refY="${a.refY}" orient="auto">
        <path class="move-arrowhead move-arrowhead-ghost" d="${a.headPath}"/>
      </marker>
    </defs>`;

    let body = "";
    if (truncated) {
      const played = lineEnds(from, actual, 0.22, 0.18);
      const ghost = lineEnds(actual, to, 0.18, 0.22);
      body += `<line class="move-played" x1="${played.x1}" y1="${played.y1}" x2="${played.x2}" y2="${played.y2}"
        stroke-width="${a.strokePlayed}" stroke-linecap="round" marker-end="url(#replay-arrowhead)"/>`;
      body += `<line class="move-ghost" x1="${ghost.x1}" y1="${ghost.y1}" x2="${ghost.x2}" y2="${ghost.y2}"
        stroke-width="${a.strokeGhost}" stroke-linecap="round" stroke-dasharray="${a.dashGhost}"
        marker-end="url(#replay-arrowhead-ghost)"/>`;
    } else {
      const line = lineEnds(from, to, 0.22, 0.22);
      body += `<line class="move-played" x1="${line.x1}" y1="${line.y1}" x2="${line.x2}" y2="${line.y2}"
        stroke-width="${a.strokePlayed}" stroke-linecap="round" marker-end="url(#replay-arrowhead)"/>`;
    }

    return `<svg class="replay-move-arrow" viewBox="0 0 8 8" aria-hidden="true">${defs}${body}</svg>`;
  }

  function sqCoordMarkup(file, rank) {
    let html = "";
    if (file === 0) {
      html += `<span class="sq-coord sq-coord-rank" aria-hidden="true">${rank + 1}</span>`;
    }
    if (rank === 0) {
      html += `<span class="sq-coord sq-coord-file" aria-hidden="true">${String.fromCharCode(97 + file)}</span>`;
    }
    return html;
  }

  function renderBoard(squares, visible, trace) {
    let html = trace ? moveArrowSvg(trace) : "";
    for (let rank = 7; rank >= 0; rank--) {
      html += '<div class="rank">';
      for (let file = 0; file < 8; file++) {
        const idx = squareIndex(file, rank);
        const light = (rank + file) % 2 === 1;
        const sq = String.fromCharCode(97 + file) + (rank + 1);
        const fog = visible[idx] ? "" : " fog";
        html += `<div class="sq ${light ? "light" : "dark"}${fog}" data-sq="${sq}">${sqCoordMarkup(file, rank)}`;
        const p = squares[idx];
        if (p) {
          html += `<span class="piece ${p.color}">${(p.kind || "p").toUpperCase()}</span>`;
        }
        if (!visible[idx]) {
          html += '<span class="fog-overlay" aria-hidden="true"></span>';
        }
        html += "</div>";
      }
      html += "</div>";
    }
    return html;
  }

  function opponentColor(color) {
    return color === "white" ? "black" : "white";
  }

  function fogForStep(step) {
    const mode = fogSelect?.value || "none";
    if (mode === "none") return new Array(64).fill(true);
    const pov =
      mode === "white"
        ? "white"
        : mode === "black"
          ? "black"
          : opponentColor(step.turn || "white");
    return visibleSquares(step.squares, pov);
  }

  function render() {
    const step = data.steps[stepIndex];
    const vis = fogForStep(step);
    const trace = traceForStep(step);
    if (boardEl) boardEl.innerHTML = renderBoard(step.squares, vis, trace);
    if (capWhite) capWhite.innerHTML = capturedTray("white", step.squares);
    if (capBlack) capBlack.innerHTML = capturedTray("black", step.squares);
    if (counterEl) {
      counterEl.textContent = `Move ${step.n} / ${data.steps[maxIndex].n}`;
    }
    if (moveLabel) {
      if (trace) {
        if (trace.actual && trace.actual !== trace.to) {
          moveLabel.textContent = `${step.uci} (asked ${trace.to}, stopped ${trace.actual})`;
        } else {
          moveLabel.textContent = `${step.uci} (${trace.from} → ${trace.to})`;
        }
      } else if (step.uci) {
        moveLabel.textContent = `Last: ${step.uci}`;
      } else {
        moveLabel.textContent = "Starting position";
      }
    }
  }

  function goTo(i) {
    stepIndex = Math.max(0, Math.min(maxIndex, i));
    render();
    updateEdgeNav();
  }

  function updateEdgeNav() {
    const prev = document.getElementById("replay-edge-prev");
    const next = document.getElementById("replay-edge-next");
    if (!prev || !next) return;
    prev.disabled = stepIndex <= 0;
    next.disabled = stepIndex >= maxIndex;
  }

  document.getElementById("replay-first")?.addEventListener("click", () => goTo(0));
  document.getElementById("replay-prev")?.addEventListener("click", () => goTo(stepIndex - 1));
  document.getElementById("replay-next")?.addEventListener("click", () => goTo(stepIndex + 1));
  document.getElementById("replay-last")?.addEventListener("click", () => goTo(maxIndex));
  document.getElementById("replay-edge-prev")?.addEventListener("click", () => goTo(stepIndex - 1));
  document.getElementById("replay-edge-next")?.addEventListener("click", () => goTo(stepIndex + 1));
  fogSelect?.addEventListener("change", render);
  traceToggle?.addEventListener("change", render);

  document.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") goTo(stepIndex - 1);
    if (e.key === "ArrowRight") goTo(stepIndex + 1);
  });

  mobileMq.addEventListener("change", render);

  updateEdgeNav();
  render();
})();
