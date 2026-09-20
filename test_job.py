import time

from job_manager import JobManager


manager = JobManager()

manager.start_job("A", "workload_a.py")

print("Job A running:", manager.is_running("A"))

while manager.is_running("A"):
    print(
        f"Job A runtime: "
        f"{manager.get_runtime('A'):.2f} seconds"
    )

    time.sleep(2)

manager.wait_for_job("A")

print("Job manager test completed.")