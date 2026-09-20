from dataclasses import dataclass
from scheduler import ResourceProfile


@dataclass
class QueuedJob:
    job_id: str
    script: str
    profile: ResourceProfile


class JobQueue:
    def __init__(self):
        self.jobs = []

    def add_job(
        self,
        job_id: str,
        script: str,
        profile: ResourceProfile,
    ):
        self.jobs.append(
            QueuedJob(
                job_id=job_id,
                script=script,
                profile=profile,
            )
        )

    def remove_job(self, job_id: str):
        self.jobs = [
            job
            for job in self.jobs
            if job.job_id != job_id
        ]

    def get_jobs(self):
        return self.jobs

    def is_empty(self):
        return len(self.jobs) == 0