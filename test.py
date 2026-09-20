from scheduler import (
    LOW,
    MEDIUM,
    HEAVY,
    SchedulerConfig,
    can_admit,
)

from job_registry import JobRegistry


config = SchedulerConfig()
registry = JobRegistry()


# Scheduler admits LOW.
registry.add_job("A", LOW)

print("Running jobs after A:")
for job in registry.get_running_jobs():
    print(f"{job.job_id} -> {job.profile.name}")

print("\nResource usage:")
print(registry.get_resource_usage())


# Check whether MEDIUM can join LOW.
usage = registry.get_resource_usage()

result = can_admit(
    current_compute=usage["compute"],
    current_memory=usage["memory"],
    current_vram_mb=usage["vram_mb"],
    workload=MEDIUM,
    config=config,
)

print("\nDecision for MEDIUM:")
print(result)


# Check whether HEAVY can join LOW.
result = can_admit(
    current_compute=usage["compute"],
    current_memory=usage["memory"],
    current_vram_mb=usage["vram_mb"],
    workload=HEAVY,
    config=config,
)

print("\nDecision for HEAVY:")
print(result)