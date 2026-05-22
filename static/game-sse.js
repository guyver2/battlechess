/**
 * Live game updates: EventSource for /events, click-to-move, fetch for moves/promotion.
 */
(function () {
  const boot = document.getElementById("game-sse");
  if (!boot) return;

  const uuid = boot.dataset.gameUuid;
  if (!uuid) return;

  let selectedSq = null;

  function moveUrl() {
    return document.querySelector("#move-area [data-move-url]")?.dataset.moveUrl;
  }

  function legalMovesMap() {
    const el = document.querySelector("#move-area [data-legal-moves]");
    if (!el) return {};
    try {
      return JSON.parse(el.dataset.legalMoves || "{}");
    } catch {
      return {};
    }
  }

  function clearMoveTargets() {
    document.querySelectorAll("#board .sq.move-target").forEach((el) => {
      el.classList.remove("move-target");
    });
  }

  function showMoveTargets(fromSq) {
    clearMoveTargets();
    const dests = legalMovesMap()[fromSq];
    if (!dests?.length) return;
    const board = document.getElementById("board");
    if (!board) return;
    for (const sq of dests) {
      board.querySelector(`[data-sq="${sq}"]`)?.classList.add("move-target");
    }
  }

  function clearSelection() {
    selectedSq = null;
    document.querySelectorAll("#board .sq.selected").forEach((el) => {
      el.classList.remove("selected");
    });
    clearMoveTargets();
  }

  function setSelection(sqEl, sq) {
    clearSelection();
    selectedSq = sq;
    sqEl.classList.add("selected");
    showMoveTargets(sq);
  }

  function pieceColorOnSquare(sqEl) {
    const piece = sqEl.querySelector(".piece");
    if (!piece) return null;
    if (piece.classList.contains("white")) return "white";
    if (piece.classList.contains("black")) return "black";
    return null;
  }

  function showMoveError(msg) {
    const status = document.querySelector("#game-status");
    if (!status) return;
    status.querySelectorAll(".move-error").forEach((el) => el.remove());
    const p = document.createElement("p");
    p.className = "move-error";
    p.setAttribute("role", "alert");
    p.textContent = msg;
    status.appendChild(p);
  }

  function runEmbeddedScripts(html) {
    const re = /<script[^>]*>([\s\S]*?)<\/script>/gi;
    let m;
    while ((m = re.exec(html)) !== null) {
      try {
        // Datastar ExecuteScript (e.g. redirect to lobby after quit waiting)
        Function(m[1])();
      } catch (err) {
        console.error(err);
      }
    }
  }

  function applyPatchData(data) {
    let selector = null;
    let mode = "inner";
    const elements = [];
    for (const line of data.split("\n")) {
      if (line.startsWith("selector ")) selector = line.slice(9);
      else if (line.startsWith("mode ")) mode = line.slice(5).trim();
      else if (line.startsWith("elements ")) elements.push(line.slice(9));
    }
    const html = elements.join("\n");
    if (html.includes("<script")) {
      runEmbeddedScripts(html);
      if (mode === "append") return;
    }
    if (!selector) return;
    const target = document.querySelector(selector);
    if (!target) return;
    if (mode === "inner") {
      target.innerHTML = html;
    } else if (mode === "append") {
      const tpl = document.createElement("template");
      tpl.innerHTML = html;
      target.appendChild(tpl.content);
    } else if (mode === "outer") {
      target.outerHTML = html;
    }
    if (selector === "#board") clearSelection();
  }

  function applyPatchEvent(event) {
    applyPatchData(event.data);
  }

  function consumeFetchSse(response) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    function pump() {
      return reader.read().then(({ done, value }) => {
        if (done) return;
        buffer += decoder.decode(value, { stream: true });
        let idx;
        while ((idx = buffer.indexOf("\n\n")) !== -1) {
          const block = buffer.slice(0, idx);
          buffer = buffer.slice(idx + 2);
          const dataLines = block
            .split("\n")
            .filter((l) => l.startsWith("data: "))
            .map((l) => l.slice(6));
          if (dataLines.length) applyPatchData(dataLines.join("\n"));
        }
        return pump();
      });
    }
    return pump();
  }

  function postForm(url, params) {
    return fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        Accept: "text/event-stream",
        "Datastar-Request": "true",
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams(params),
    }).then((resp) => {
      if (!resp.ok) {
        return resp.text().then((t) => showMoveError(t));
      }
      const ct = resp.headers.get("content-type") || "";
      if (ct.includes("text/event-stream")) {
        return consumeFetchSse(resp).then(() => {
          if (url.includes("/cancel")) {
            window.location.href = "/lobby";
          }
        });
      }
      if (resp.redirected) window.location.href = resp.url;
    });
  }

  function submitMove(uci) {
    const url = moveUrl();
    if (!url || uci.length < 4) return;
    clearSelection();
    return postForm(url, { move: uci });
  }

  function handleSquareClick(sqEl) {
    if (!moveUrl()) return;

    const sq = sqEl.dataset.sq;
    const playerColor = document.getElementById("game-root")?.dataset.playerColor;
    const onSquare = pieceColorOnSquare(sqEl);
    const isOwn = onSquare && onSquare === playerColor;

    if (!selectedSq) {
      if (!isOwn) return;
      setSelection(sqEl, sq);
      return;
    }

    if (isOwn) {
      setSelection(sqEl, sq);
      return;
    }

    submitMove(selectedSq + sq);
  }

  function connectEvents() {
    const es = new EventSource(`/games/${uuid}/events`);
    es.addEventListener("datastar-patch-elements", applyPatchEvent);
    es.onerror = () => {
      es.close();
      setTimeout(connectEvents, 1500);
    };
  }

  connectEvents();

  document.getElementById("game-root")?.addEventListener("click", (e) => {
    const sqEl = e.target.closest(".sq");
    if (!sqEl || !sqEl.closest("#board")) return;
    handleSquareClick(sqEl);
  });

  document.getElementById("game-root")?.addEventListener(
    "submit",
    (e) => {
      const form = e.target.closest("form");
      if (!form || !form.closest("#move-area")) return;
      // Quit waiting uses a normal form POST so the browser follows the redirect to /lobby.
      if (form.classList.contains("quit-waiting-form")) return;
      const attr = form.getAttribute("data-on:submit") || "";
      const m = attr.match(/@post\('([^']+)'/);
      if (!m) return;
      e.preventDefault();
      e.stopImmediatePropagation();
      postForm(m[1], Object.fromEntries(new FormData(form)));
    },
    true
  );
})();
