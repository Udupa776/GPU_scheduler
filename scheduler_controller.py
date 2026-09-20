from scheduler import MEDIUM, SchedulerConfig, can_admit
from job_registry import JobRegistry
from job_manager import JobManager
from job_queue import JobQueue
import time
from benchmark import Benchmark

class SchedulerController:
    def __init__(self, mode="smart"):
        self.job_metrics = {}   
        self.mode = mode
        self.benchmark = Benchmark()
        self.queue = JobQueue()
        self.config = SchedulerConfig()
        self.registry = JobRegistry()
        self.job_manager = JobManager()

    def submit_job(self, job_id, script, profile):
        submit_time = time.time()
        self.job_metrics[job_id] = {
    "submit_time": submit_time,
}
        if self.mode == "baseline" and self.registry.get_running_jobs():
            self.queue.add_job(
                job_id=job_id,
                script=script,
                profile=profile,
            )

            print(f"\n[{job_id}] Baseline scheduler: GPU is busy.")
            print(f"[{job_id}] Status: QUEUED")

            return False

        usage = self.registry.get_resource_usage()

        decision = can_admit(
            current_compute=usage["compute"],
            current_memory=usage["memory"],
            current_vram_mb=usage["vram_mb"],
            workload=profile,
            config=self.config,
        )

        print(f"\n[{job_id}] Scheduler decision:")
        print(decision)

        if decision["decision"] == "ADMIT":
            self.registry.add_job(job_id, profile)

            self.job_manager.start_job(
                job_id,
                script,
            )
            self.job_metrics[job_id]["start_time"] = time.time()

            print(f"[{job_id}] Status: RUNNING")

            return True

        self.queue.add_job(
            job_id=job_id,
            script=script,
            profile=profile,
        )

        print(f"[{job_id}] Status: QUEUED")

        return False

    def update_jobs(self):
        completed_jobs = []

        # Check which running jobs have completed
        for job in self.registry.get_running_jobs():
            if not self.job_manager.is_running(job.job_id):
                completed_jobs.append(job.job_id)

        # Remove completed jobs from the registry
        for job_id in completed_jobs:
            completed_time = time.time()

            self.job_metrics[job_id]["end_time"] = completed_time

            submit_time = self.job_metrics[job_id]["submit_time"]
            start_time = self.job_metrics[job_id]["start_time"]

            wait_time = start_time - submit_time
            runtime = completed_time - start_time

            self.job_metrics[job_id]["wait_time"] = wait_time
            self.job_metrics[job_id]["runtime"] = runtime

            self.benchmark.add_job_result(
    job_id,
    self.job_metrics[job_id],
)

            self.registry.remove_job(job_id)

            print(f"[{job_id}] Status: COMPLETED")
            print(f"[{job_id}] Wait time: {wait_time:.2f} seconds")
            print(f"[{job_id}] Runtime: {runtime:.2f} seconds")
        # Check queued jobs after resources are released
        for queued_job in self.queue.get_jobs():
            usage = self.registry.get_resource_usage()

            decision = can_admit(
                current_compute=usage["compute"],
                current_memory=usage["memory"],
                current_vram_mb=usage["vram_mb"],
                workload=queued_job.profile,
                config=self.config,
            )

            if decision["decision"] == "ADMIT":
                print(f"\n[{queued_job.job_id}] Queued job can now run.")

                self.registry.add_job(
                    queued_job.job_id,
                    queued_job.profile,
                )

                self.job_manager.start_job(
                    queued_job.job_id,
                    queued_job.script,
                )
                self.job_metrics[queued_job.job_id]["start_time"] = time.time()

                self.queue.remove_job(queued_job.job_id)

                print(f"[{queued_job.job_id}] Status: RUNNING")


    def print_benchmark_summary(self):
        self.benchmark.print_summary()