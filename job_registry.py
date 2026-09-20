from dataclasses import dataclass
from scheduler import ResourceProfile


@dataclass
class RunningJob:
    job_id: str
    profile: ResourceProfile


class JobRegistry:
    def __init__(self):
        self.running_jobs = []

    def add_job(self, job_id: str, profile: ResourceProfile):
        job = RunningJob(
            job_id=job_id,
            profile=profile,
        )

        self.running_jobs.append(job)

    def remove_job(self, job_id: str):
        self.running_jobs = [
            job
            for job in self.running_jobs
            if job.job_id != job_id
        ]

    def get_resource_usage(self):
        compute = sum(
            job.profile.compute_utilization
            for job in self.running_jobs
        )

        memory = sum(
            job.profile.memory_utilization
            for job in self.running_jobs
        )

        vram = sum(
            job.profile.vram_mb
            for job in self.running_jobs
        )

        return {
            "compute": compute,
            "memory": memory,
            "vram_mb": vram,
        }

    def get_running_jobs(self):
        return self.running_jobs