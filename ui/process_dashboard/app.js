const state = {
  selectedRunId: null,
  runs: [],
  currentRun: null,
  refreshTimer: null,
};

const $ = (id) => document.getElementById(id);

function statusClass(status) {
  const text = String(status || "neutral").toLowerCase();
  if (text.includes("running") || text.includes("started") || text.includes("active")) return "running";
  if (text.includes("complete") || text.includes("finish")) return "completed";
  if (text.includes("fail") || text.includes("error") || text.includes("block")) return "error";
  return "neutral";
}

function shortId(runId) {
  if (!runId) return "-";
  return runId.length > 28 ? `${runId.slice(0, 18)}...${runId.slice(-6)}` : runId;
}

function formatJson(value) {
  return JSON.stringify(value || {}, null, 2);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `HTTP ${response.status}`);
  }
  return payload;
}

function renderRuns() {
  const list = $("runList");
  $("runCount").textContent = String(state.runs.length);
  if (!state.runs.length) {
    list.innerHTML = `<div class="empty">No runs yet. Start one from the main panel.</div>`;
    return;
  }
  list.innerHTML = state.runs
    .map((run) => {
      const runId = run.run_id;
      const status = run.process?.status || run.status || "unknown";
      const metrics = run.metrics || {};
      const active = runId === state.selectedRunId ? "active" : "";
      return `
        <button class="run-item ${active}" data-run-id="${runId}" type="button">
          <span class="run-title">
            <span>${shortId(runId)}</span>
            <span class="status-pill ${statusClass(status)}">${status}</span>
          </span>
          <span class="run-meta">steps ${metrics.steps ?? "-"} · tools ${metrics.tool_calls ?? "-"} · events ${metrics.events ?? "-"}</span>
          <span class="run-meta">${run.finished_at || run.process?.started_at || ""}</span>
        </button>
      `;
    })
    .join("");
  for (const item of list.querySelectorAll("[data-run-id]")) {
    item.addEventListener("click", () => selectRun(item.getAttribute("data-run-id")));
  }
}

function renderMetrics(run) {
  const derived = run?.state || {};
  $("selectedTitle").textContent = run?.run_id ? shortId(run.run_id) : "No run selected";
  $("metricStatus").textContent = derived.status || "-";
  $("metricAgent").textContent = derived.current_agent || "-";
  $("metricStep").textContent = derived.step ?? "-";
  $("metricEvents").textContent = derived.event_count ?? "-";
  $("graphMode").textContent = run?.process?.mode || "event log";
  $("stopBtn").disabled = !(run?.process?.status === "running");
  $("sendDirectiveBtn").disabled = !run?.run_id;
}

function renderGraph(run) {
  const graph = $("agentGraph");
  const agents = run?.state?.agents || [];
  if (!agents.length) {
    graph.innerHTML = `<div class="empty">No agent events yet.</div>`;
    return;
  }
  graph.innerHTML = agents
    .map((agent) => `
      <div class="agent-node ${agent.active ? "active" : ""}">
        <strong>${agent.name}</strong>
        <span class="status-pill ${agent.active ? "running" : "neutral"}">${agent.last_status || "seen"}</span>
        <div class="agent-stats">
          <span>${agent.events} events</span>
          <span>${agent.actions} actions</span>
          <span>${agent.tools} tools</span>
          <span>${agent.errors} errors</span>
        </div>
      </div>
    `)
    .join("");
}

function renderDirectives(run) {
  const target = $("directiveList");
  const directives = [
    ...(run?.state?.directives || []),
    ...(run?.state?.directives_from_files || []),
    ...(run?.state?.ui_directives || []),
  ];
  if (!directives.length) {
    target.innerHTML = `<div class="empty">No directives recorded for this run.</div>`;
    return;
  }
  target.innerHTML = directives
    .slice(-30)
    .reverse()
    .map((directive) => {
      const intent = directive.intent || directive.text || "queued";
      const status = directive.status || "queued";
      const raw = directive.raw_text || directive.text || "";
      return `
        <div class="directive-item">
          <div><span class="status-pill ${statusClass(status)}">${status}</span> <strong>${intent}</strong></div>
          <code>${raw}</code>
        </div>
      `;
    })
    .join("");
}

function renderTimeline(run) {
  const target = $("timeline");
  const filter = $("eventFilter").value.trim().toLowerCase();
  let events = run?.state?.timeline || [];
  if (filter) {
    events = events.filter((event) => JSON.stringify(event).toLowerCase().includes(filter));
  }
  if (!events.length) {
    target.innerHTML = `<div class="empty">No events match the current filter.</div>`;
    return;
  }
  target.innerHTML = events
    .slice()
    .reverse()
    .map((event) => `
      <div class="event-row">
        <div class="event-row-header">
          <span>#${event.sequence ?? "-"} ${event.kind || ""}</span>
          <span>${event.timestamp || ""}</span>
        </div>
        <div>${event.summary || ""}</div>
        <code>${event.status || event.node || event.tool || ""}</code>
      </div>
    `)
    .join("");
}

function renderSelectedRun(run) {
  state.currentRun = run;
  renderMetrics(run);
  renderGraph(run);
  renderDirectives(run);
  renderTimeline(run);
  const statePayload = run?.state
    ? {
        status: run.state.status,
        current_agent: run.state.current_agent,
        step: run.state.step,
        last_action: run.state.last_action,
        last_tool: run.state.last_tool,
        status_counts: run.state.status_counts,
        metrics: run.state.metrics,
        run_dir: run.run_dir,
        control: run.control,
      }
    : {};
  $("stateJson").textContent = formatJson(statePayload);
  $("stdoutView").textContent = run?.stdout || "";
  if (window.lucide) window.lucide.createIcons();
}

async function refreshRuns({ keepSelection = true } = {}) {
  try {
    const payload = await api("/api/runs?limit=80");
    state.runs = payload.runs || [];
    $("connectionStatus").textContent = "Connected";
    $("connectionStatus").className = "status-pill running";
    if (!keepSelection || !state.selectedRunId) {
      state.selectedRunId = state.runs[0]?.run_id || null;
    }
    renderRuns();
    if (state.selectedRunId) {
      await loadRun(state.selectedRunId);
    } else {
      renderSelectedRun(null);
    }
  } catch (error) {
    $("connectionStatus").textContent = "Offline";
    $("connectionStatus").className = "status-pill error";
    console.error(error);
  }
}

async function loadRun(runId) {
  if (!runId) return;
  try {
    const run = await api(`/api/runs/${encodeURIComponent(runId)}`);
    state.selectedRunId = runId;
    renderRuns();
    renderSelectedRun(run);
  } catch (error) {
    console.error(error);
  }
}

function selectRun(runId) {
  state.selectedRunId = runId;
  loadRun(runId);
}

async function startRun(event) {
  event.preventDefault();
  const prompt = $("promptInput").value;
  const mode = $("modeSelect").value;
  const maxSteps = Number($("maxStepsInput").value || 30);
  const button = event.submitter;
  button.disabled = true;
  try {
    const payload = await api("/api/runs", {
      method: "POST",
      body: JSON.stringify({ prompt, mode, max_steps: maxSteps }),
    });
    state.selectedRunId = payload.process.run_id;
    await refreshRuns({ keepSelection: true });
  } catch (error) {
    alert(error.message);
  } finally {
    button.disabled = false;
  }
}

async function sendDirective(event) {
  event.preventDefault();
  if (!state.selectedRunId) return;
  const text = $("directiveInput").value.trim();
  if (!text) return;
  const button = $("sendDirectiveBtn");
  button.disabled = true;
  try {
    await api(`/api/runs/${encodeURIComponent(state.selectedRunId)}/directives`, {
      method: "POST",
      body: JSON.stringify({ text }),
    });
    $("directiveInput").value = "";
    await loadRun(state.selectedRunId);
  } catch (error) {
    alert(error.message);
  } finally {
    button.disabled = false;
  }
}

async function stopRun() {
  if (!state.selectedRunId) return;
  try {
    await api(`/api/runs/${encodeURIComponent(state.selectedRunId)}/stop`, { method: "POST", body: "{}" });
    await refreshRuns({ keepSelection: true });
  } catch (error) {
    alert(error.message);
  }
}

function bindUi() {
  $("startForm").addEventListener("submit", startRun);
  $("directiveForm").addEventListener("submit", sendDirective);
  $("refreshBtn").addEventListener("click", () => refreshRuns({ keepSelection: true }));
  $("stopBtn").addEventListener("click", stopRun);
  $("newRunFocusBtn").addEventListener("click", () => $("promptInput").focus());
  $("eventFilter").addEventListener("input", () => renderTimeline(state.currentRun));
  for (const button of document.querySelectorAll("[data-directive]")) {
    button.addEventListener("click", () => {
      $("directiveInput").value = button.getAttribute("data-directive") || "";
      $("directiveInput").focus();
    });
  }
  if (window.lucide) window.lucide.createIcons();
}

bindUi();
refreshRuns({ keepSelection: false });
state.refreshTimer = setInterval(() => refreshRuns({ keepSelection: true }), 2000);
