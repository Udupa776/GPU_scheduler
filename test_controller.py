import time

from scheduler import LOW, MEDIUM, HEAVY
from scheduler_controller import SchedulerController


controller = SchedulerController(mode="smart")


# Submit A.
controller.submit_job(
    job_id="A",
    script="low_workload.py",
    profile=LOW,
)

time.sleep(2)


# Submit C while A is running.
controller.submit_job(
    job_id="B",
    script="medium_work.py",
    profile=MEDIUM,
)

time.sleep(2)

controller.submit_job(
    job_id="C",
    script="heavy_work.py",
    profile=HEAVY,
)

print("\nCurrent running jobs:")

for job in controller.registry.get_running_jobs():
    print(f"{job.job_id} -> {job.profile.name}")


print("\nCurrent queued jobs:")

for job in controller.queue.get_jobs():
    print(f"{job.job_id} -> {job.profile.name}")


# Wait for A to finish.
while (
    controller.registry.get_running_jobs()
    or not controller.queue.is_empty()
):
    controller.update_jobs()
    time.sleep(2)


print("\nFinal running jobs:")
print(controller.registry.get_running_jobs())

print("\nFinal queued jobs:")

for job in controller.queue.get_jobs():
    print(f"{job.job_id} -> {job.profile.name}")

controller.print_benchmark_summary()