"""REST backend for the GPU scheduler dashboard.

Run from the repository root with: python backend.py
The frontend never executes nvidia-smi; this process does it through gpu_moniter.py.
"""

import json
import os
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from gpu_moniter import get_gpu_state
from scheduler import HEAVY, LOW, MEDIUM
from scheduler_controller import SchedulerController

HOST = os.environ.get("GPU_SCHEDULER_HOST", "0.0.0.0")
PORT = int(os.environ.get("GPU_SCHEDULER_PORT", "8000"))
ROOT = os.path.dirname(os.path.abspath(__file__))
PROFILES = {"LOW": LOW, "MEDIUM": MEDIUM, "HEAVY": HEAVY}
SCRIPTS = {"LOW": "low_workload.py", "MEDIUM": "medium_work.py", "HEAVY": "heavy_work.py"}

controller = SchedulerController(mode="smart")
known_jobs = {}
last_decision = None
experiment_started = None
lock = threading.RLock()


def profile_json(profile):
    return {
        "name": profile.name,
        "compute_utilization": profile.compute_utilization,
        "memory_utilization": profile.memory_utilization,
        "vram_mb": profile.vram_mb,
        "runtime_seconds": profile.runtime_seconds,
    }


def refresh_jobs():
    with lock:
        controller.update_jobs()
        running = {job.job_id: job for job in controller.registry.get_running_jobs()}
        queued = {job.job_id: job for job in controller.queue.get_jobs()}
        now = time.time()
        result = []
        for job_id, record in known_jobs.items():
            profile = record["profile"]
            metrics = controller.job_metrics.get(job_id, {})
            if job_id in running:
                status = "RUNNING - CO-LOCATED" if len(running) > 1 else "RUNNING"
            elif job_id in queued:
                status = "QUEUED"
            elif "end_time" in metrics:
                status = "COMPLETED"
            else:
                continue
            submit_time = metrics.get("submit_time", record["submitted_at"])
            start_time = metrics.get("start_time")
            end_time = metrics.get("end_time")
            result.append({
                "job_id": job_id,
                "workload": profile.name,
                "status": status,
                "profile": profile_json(profile),
                "wait_time_seconds": metrics.get("wait_time", (start_time or now) - submit_time),
                "runtime_seconds": metrics.get("runtime", (now - start_time) if start_time else profile.runtime_seconds),
                "submitted_at": submit_time,
                "started_at": start_time,
                "completed_at": end_time,
            })
        return result


def gpu_payload():
    state = get_gpu_state()
    state["gpu_name"] = get_gpu_name()
    return state


def get_gpu_name():
    import subprocess

    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip().splitlines()[0]


def json_response(handler, payload, status=200):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(body)


class ApiHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        try:
            if path == "/api/health":
                return json_response(self, {"ok": True, "backend": "python"})
            if path == "/api/gpu/state":
                try:
                    return json_response(self, {"available": True, "state": gpu_payload()})
                except (FileNotFoundError, OSError, ValueError) as error:
                    return json_response(self, {"available": False, "error": str(error), "message": "GPU telemetry unavailable"}, 503)
            if path in ("/api/jobs", "/api/queue"):
                jobs = refresh_jobs()
                if path == "/api/queue":
                    jobs = [job for job in jobs if job["status"] == "QUEUED"]
                return json_response(self, {"available": True, "jobs": jobs})
            if path == "/api/scheduler/status":
                jobs = refresh_jobs()
                usage = controller.registry.get_resource_usage()
                return json_response(self, {"available": True, "mode": controller.mode, "running_jobs": len(controller.registry.get_running_jobs()), "queued_jobs": len(controller.queue.get_jobs()), "predicted_usage": usage, "last_decision": last_decision, "experiment_started_at": experiment_started})
            if path == "/api/benchmark/results":
                return json_response(self, {"available": True, "results": benchmark_payload()})
            if path == "/api/experiment/status":
                return json_response(self, {"available": True, "running": experiment_started is not None, "started_at": experiment_started})
            return super().do_GET()
        except Exception as error:
            json_response(self, {"available": False, "error": str(error)}, 500)

    def do_POST(self):
        global experiment_started, last_decision
        global controller, experiment_started, last_decision
        path = urlparse(self.path).path
        try:
            query = parse_qs(urlparse(self.path).query)
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            payload = json.loads(body or b"{}")
            if path == "/api/experiment/start":
                experiment_started = time.time()
                return json_response(self, {"available": True, "running": True, "started_at": experiment_started})
            if path == "/api/experiment/stop":
                experiment_started = None
                return json_response(self, {"available": True, "running": False})
            if path == "/api/experiment/reset":
                with lock:
                    controller = reset_controller()
                    known_jobs.clear()
                    last_decision = None
                    experiment_started = None
                return json_response(self, {"available": True, "running": False})
            if path == "/api/scheduler/mode":
                mode = payload.get("mode", "smart").lower()
                if mode not in ("baseline", "smart"):
                    return json_response(self, {"error": "mode must be baseline or smart"}, 400)
                controller.mode = mode
                return json_response(self, {"available": True, "mode": mode})
            if path == "/api/jobs":
                workload = payload.get("workload", "").upper()
                if workload not in PROFILES:
                    return json_response(self, {"error": "workload must be LOW, MEDIUM, or HEAVY"}, 400)
                job_id = payload.get("job_id") or f"{workload[0]}-{int(time.time() * 1000)}"
                accepted = controller.submit_job(job_id, SCRIPTS[workload], PROFILES[workload])
                usage = controller.registry.get_resource_usage()
                incoming = PROFILES[workload]
                last_decision = {
                    "job_id": job_id,
                    "decision": "ADMIT" if accepted else "QUEUE",
                    "current_compute": usage["compute"] - incoming.compute_utilization if accepted else usage["compute"],
                    "incoming_compute": incoming.compute_utilization,
                    "predicted_compute": usage["compute"] if accepted else usage["compute"] + incoming.compute_utilization,
                    "configured_limit": controller.config.max_compute_utilization,
                    "reason": "Admitted by configured resource limits." if accepted else "Predicted resource usage exceeds a configured safety limit.",
                }
                known_jobs[job_id] = {"profile": incoming, "submitted_at": time.time()}
                return json_response(self, {"available": True, "accepted": accepted, "decision": last_decision})
            return json_response(self, {"error": "Not found"}, 404)
        except Exception as error:
            json_response(self, {"available": False, "error": str(error)}, 500)

    def log_message(self, format, *args):
        if not self.path.startswith("/api/gpu/state"):
            super().log_message(format, *args)


def reset_controller():
    global controller
    controller = SchedulerController(mode="smart")
    return controller


def benchmark_payload():
    results = controller.benchmark
    if not results.results:
        return None
    return {
        "total_wait_time_seconds": results.get_total_wait_time(),
        "average_wait_time_seconds": results.get_average_wait_time(),
        "makespan_seconds": results.get_makespan(),
        "throughput_jobs_per_second": results.get_throughput(),
        "jobs": results.results,
    }


if __name__ == "__main__":
    print(f"GPU Scheduler API listening on http://{HOST}:{PORT}")
    print("Serving dashboard at /frontend/")
    ThreadingHTTPServer((HOST, PORT), ApiHandler).serve_forever()
