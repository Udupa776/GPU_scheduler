import subprocess
import time


class JobManager:
    def __init__(self):
        self.processes = {}
        self.completed_jobs = {}

    def start_job(self, job_id: str, script: str):
        start_time = time.time()

        process = subprocess.Popen(
            ["python", script]
        )

        self.processes[job_id] = {
            "process": process,
            "script": script,
            "start_time": start_time,
            "end_time": None,
        }

        print(f"[{job_id}] Started: {script}")

    def is_running(self, job_id: str):
        if job_id not in self.processes:
            return False

        process = self.processes[job_id]["process"]

        return process.poll() is None

    def get_runtime(self, job_id: str):
        if job_id not in self.processes:
            return None

        return time.time() - self.processes[job_id]["start_time"]

    def get_job_times(self, job_id: str):
        if job_id not in self.processes:
            return None

        return {
            "start_time": self.processes[job_id]["start_time"],
            "end_time": self.processes[job_id]["end_time"],
        }

    def wait_for_job(self, job_id: str):
        if job_id not in self.processes:
            return

        process = self.processes[job_id]["process"]

        process.wait()

        end_time = time.time()
        self.processes[job_id]["end_time"] = end_time

        runtime = time.time() - self.processes[job_id]["start_time"]

        print(f"[{job_id}] Completed in {runtime:.2f} seconds")

        self.completed_jobs[job_id] = {
    "start_time": self.processes[job_id]["start_time"],
    "end_time": end_time,
}

        del self.processes[job_id]

    def get_completed_job_times(self, job_id: str):
        return self.completed_jobs.get(job_id)