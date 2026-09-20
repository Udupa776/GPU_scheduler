const API_BASE = "";
const history = [];
const predictedHistory = [];
const $ = (selector) => document.querySelector(selector);

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok)
    throw new Error(
      payload.message || payload.error || `HTTP ${response.status}`,
    );
  return payload;
}

const api = {
  health: () => request("/api/health"),
  gpu: () => request("/api/gpu/state"),
  jobs: () => request("/api/jobs"),
  queue: () => request("/api/queue"),
  scheduler: () => request("/api/scheduler/status"),
  benchmark: () => request("/api/benchmark/results"),
  experiment: () => request("/api/experiment/status"),
  post: (path, body = {}) =>
    request(path, { method: "POST", body: JSON.stringify(body) }),
};

const formatMb = (mb) =>
  mb == null
    ? "--"
    : mb >= 1024
      ? `${(mb / 1024).toFixed(1)} GB`
      : `${Number(mb).toFixed(0)} MB`;
const statusClass = (status) =>
  status?.startsWith("RUNNING")
    ? "running"
    : status === "QUEUED"
      ? "queued"
      : "completed";
const profile = (job) => job.profile || {};

function renderGpu(payload) {
  if (!payload.available)
    throw new Error(payload.message || "GPU telemetry unavailable");
  const gpu = payload.state;
  const percent = gpu.vram_total_mb
    ? (gpu.vram_used_mb / gpu.vram_total_mb) * 100
    : 0;
  $("#data-source").textContent = "Python backend / nvidia-smi";
  $("#gpu-name").textContent = gpu.gpu_name || "AWS GPU";
  $("#gpu-util").textContent = `${gpu.compute_utilization}%`;
  $("#memory-util").textContent = `${gpu.memory_utilization}%`;
  $("#vram-used").textContent = formatMb(gpu.vram_used_mb);
  $("#vram-total").textContent = `of ${formatMb(gpu.vram_total_mb)}`;
  $("#power").textContent = `${gpu.power_w} W`;
  $("#temperature").textContent = `${gpu.temperature_c} C`;
  $("#gpu-util-bar").style.width = `${gpu.compute_utilization}%`;
  $("#memory-util-bar").style.width = `${gpu.memory_utilization}%`;
  $("#vram-bar").style.width = `${percent}%`;
  $("#vram-percent").textContent = `${percent.toFixed(0)}%`;
  $("#vram-used-side").textContent = formatMb(gpu.vram_used_mb);
  $("#vram-capacity").textContent = formatMb(gpu.vram_total_mb);
  $("#graph-util").textContent = `${gpu.compute_utilization}%`;
  history.push(gpu.compute_utilization);
  if (history.length > 30) history.shift();
}

function renderJobs(payload) {
  if (!payload.available)
    throw new Error(payload.error || "Job data unavailable");
  const jobs = payload.jobs || [];
  $("#job-table").innerHTML = jobs
    .map((job) => {
      const item = profile(job);
      return `<tr><td>${job.job_id}</td><td><span class="job-workload"><span class="job-avatar">${job.workload[0]}</span>${job.workload}</span></td><td><span class="status ${statusClass(job.status)}">${job.status}</span></td><td>${item.compute_utilization}%</td><td>${item.memory_utilization}%</td><td>${item.vram_mb} MB</td><td>${Number(job.runtime_seconds).toFixed(1)}s</td><td>${Number(job.wait_time_seconds).toFixed(1)}s</td></tr>`;
    })
    .join("");
  const running = jobs.filter((job) => job.status.startsWith("RUNNING"));
  $("#running-count").textContent = running.length;
  $("#queued-count").textContent = jobs.filter(
    (job) => job.status === "QUEUED",
  ).length;
  $("#slot-summary").textContent = `${running.length} ACTIVE JOBS`;
  $("#running-list").innerHTML = running
    .map((job) => {
      const item = profile(job);
      return `<div class="running-card"><span class="run-avatar">${job.workload[0]}</span><div><strong>${job.job_id} - ${job.workload}</strong><span>${item.compute_utilization}% compute / ${item.memory_utilization}% memory / ${item.vram_mb} MB VRAM</span></div><span class="resource-pill">${job.status}</span></div>`;
    })
    .join("");
}

function renderQueue(payload) {
  if (!payload.available) throw new Error(payload.error || "Queue data unavailable");
  $("#queued-count").textContent = (payload.jobs || []).length;
}

function renderScheduler(payload) {
  if (!payload.available)
    throw new Error(payload.error || "Scheduler data unavailable");
  document.querySelectorAll(".mode-button").forEach((button) => {
    button.classList.toggle("active", button.dataset.mode === payload.mode);
  });
  const decision = payload.last_decision;
  const predicted = payload.predicted_usage || {};
  $("#predicted-vram").textContent =
    predicted.vram_mb == null ? "--" : formatMb(predicted.vram_mb);
  $("#graph-predicted").textContent = predicted.compute == null ? "--" : `${predicted.compute}%`;
  predictedHistory.push(Number(predicted.compute || 0));
  if (predictedHistory.length > 30) predictedHistory.shift();
  if (!decision) {
    $("#decision-job").textContent = "NO DECISION YET";
    $("#decision-badge").textContent = "--";
    [
      "decision-current",
      "decision-incoming",
      "decision-combined",
      "decision-limit",
    ].forEach((id) => {
      $(`#${id}`).textContent = "--";
    });
    $("#decision-reason").textContent =
      "Submit a workload to receive a live scheduler decision.";
    return;
  }
  $("#decision-badge").textContent = decision.decision;
  $("#decision-job").textContent = `JOB ${decision.job_id}`;
  $("#decision-current").textContent = `${decision.current_compute}%`;
  $("#decision-incoming").textContent = `${decision.incoming_compute}%`;
  $("#decision-combined").textContent = `${decision.predicted_compute}%`;
  $("#decision-limit").textContent = `${decision.configured_limit}%`;
  $("#decision-reason").textContent = decision.reason;
}

function renderBenchmark(payload) {
  const grid = $("#comparison-grid");
  if (!payload.available || !payload.results) {
    grid.innerHTML = `<p class="data-note">Benchmark results unavailable until the backend records completed jobs.</p>`;
    return;
  }
  const result = payload.results;
  const metrics = [
    ["Total wait", "total_wait_time_seconds", "s"],
    ["Average wait", "average_wait_time_seconds", "s"],
    ["Makespan", "makespan_seconds", "s"],
    ["Throughput", "throughput_jobs_per_second", "/s"],
  ];
  grid.innerHTML = `<div class="comparison-card"><h3>ACTIVE EXPERIMENT</h3><div class="comparison-values">${metrics.map(([label, key, unit]) => `<div><span>${label}</span><strong class="smart-value">${Number(result[key]).toFixed(2)}${unit}</strong></div>`).join("")}</div></div><div class="comparison-card"><h3>COMPLETED JOBS</h3><div class="comparison-values"><div><span>Recorded jobs</span><strong>${result.jobs ? Object.keys(result.jobs).length : 0}</strong></div><div><span>Peak GPU</span><strong>Telemetry stream</strong></div><div><span>Peak VRAM</span><strong>Telemetry stream</strong></div><div><span>Co-located</span><strong>Scheduler state</strong></div></div></div>`;
}

function drawChart() {
  const canvas = $("#utilization-chart");
  const ratio = window.devicePixelRatio || 1;
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  canvas.width = width * ratio;
  canvas.height = height * ratio;
  const context = canvas.getContext("2d");
  context.scale(ratio, ratio);
  if (!history.length) return;
  const line = (values, color) => {
    context.beginPath();
    context.strokeStyle = color;
    context.lineWidth = 2;
    values.forEach((value, index) => {
      const x = (index * width) / Math.max(values.length - 1, 1);
      const y = height - (value * height) / 100;
      index ? context.lineTo(x, y) : context.moveTo(x, y);
    });
    context.stroke();
  };
  line(history, "#31d5f3");
  if (predictedHistory.some((value) => value > 0))
    line(predictedHistory, "#ffb45c");
}

function showDisconnected(message = "Backend disconnected") {
  $("#data-source").textContent = message;
  $("#experiment-status").textContent = message;
  $("#gpu-name").textContent = "GPU telemetry unavailable";
  [
    "gpu-util",
    "memory-util",
    "vram-used",
    "vram-total",
    "power",
    "temperature",
    "vram-percent",
    "vram-used-side",
    "vram-capacity",
    "graph-util",
    "graph-predicted",
    "running-count",
    "queued-count",
  ].forEach((id) => {
    if ($(`#${id}`)) $(`#${id}`).textContent = "--";
  });
  $("#job-table").innerHTML =
    `<tr><td colspan="8" class="data-note">Waiting for AWS telemetry and scheduler backend data.</td></tr>`;
  $("#running-list").innerHTML =
    `<p class="data-note">Running workloads unavailable.</p>`;
}

function showGpuUnavailable() {
  $("#experiment-status").textContent = "GPU telemetry unavailable";
  $("#gpu-name").textContent = "GPU telemetry unavailable";
  ["gpu-util", "memory-util", "vram-used", "vram-total", "power", "temperature", "vram-percent", "vram-used-side", "vram-capacity", "graph-util"].forEach((id) => {
    if ($(`#${id}`)) $(`#${id}`).textContent = "--";
  });
  ["gpu-util-bar", "memory-util-bar", "vram-bar"].forEach((id) => { if ($(`#${id}`)) $(`#${id}`).style.width = "0%"; });
}

function setBackendStatus(connected, running = false) {
  $("#data-source").textContent = connected ? "Python backend / nvidia-smi" : "Backend disconnected";
  $("#experiment-status").textContent = connected ? (running ? "Experiment running" : "Backend connected") : "Backend disconnected";
}

async function render() {
  const results = await Promise.allSettled([
    api.health(), api.gpu(), api.jobs(), api.queue(), api.scheduler(), api.benchmark(), api.experiment(),
  ]);
  const [health, gpu, jobs, queue, scheduler, benchmark, experiment] = results;
  const backendConnected = health.status === "fulfilled" && health.value.ok === true;
  setBackendStatus(backendConnected, experiment.status === "fulfilled" && experiment.value.running);
  if (!backendConnected) { $("#last-sync").textContent = "--"; showDisconnected("Backend disconnected"); return; }
  if (gpu.status === "fulfilled" && gpu.value.available) { renderGpu(gpu.value); $("#last-sync").textContent = new Date().toLocaleTimeString(); } else showGpuUnavailable();
  if (jobs.status === "fulfilled") renderJobs(jobs.value);
  if (queue.status === "fulfilled") renderQueue(queue.value);
  if (scheduler.status === "fulfilled") renderScheduler(scheduler.value);
  if (benchmark.status === "fulfilled") renderBenchmark(benchmark.value);
  if (experiment.status === "fulfilled") $("#experiment-status").textContent = experiment.value.running ? "Experiment running" : "Backend connected";
  drawChart();
}

document.querySelectorAll(".mode-button").forEach((button) =>
  button.addEventListener("click", async () => {
    document
      .querySelectorAll(".mode-button")
      .forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    try {
      await api.post("/api/scheduler/mode", { mode: button.dataset.mode });
      await render();
    } catch (error) {
      showDisconnected();
    }
  }),
);
$("#start-experiment").addEventListener("click", async () => {
  try {
    await api.post("/api/experiment/start");
    await render();
  } catch (error) {
    showDisconnected();
  }
});
$("#stop-experiment").addEventListener("click", async () => {
  try {
    await api.post("/api/experiment/stop");
    await render();
  } catch (error) {
    showDisconnected();
  }
});
$("#reset-experiment").addEventListener("click", async () => {
  try {
    await api.post("/api/experiment/reset");
    await render();
  } catch (error) {
    showDisconnected();
  }
});
document.querySelectorAll(".workload-button").forEach((button) =>
  button.addEventListener("click", async () => {
    try {
      await api.post("/api/jobs", { workload: button.dataset.workload });
      await render();
    } catch (error) {
      showDisconnected();
    }
  }),
);
window.addEventListener("resize", drawChart);
render();
setInterval(render, 1500);
