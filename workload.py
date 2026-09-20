import argparse
import time

import torch


def run_workload(intensity: float, duration: int):
    device = torch.device("cuda")

    print(f"Starting workload")
    print(f"Target intensity: {intensity}%")
    print(f"Duration: {duration}s")
    print(f"GPU: {torch.cuda.get_device_name(0)}")

    # Fixed-size tensors keep the memory requirement predictable.
    x = torch.randn(1024, 1024, device=device)
    y = torch.randn(1024, 1024, device=device)

    # Convert target intensity into an approximate active/idle cycle.
    intensity = max(1.0, min(100.0, intensity))

    cycle = 0.1
    active_time = cycle * (intensity / 100.0)
    idle_time = cycle - active_time

    start = time.time()

    while time.time() - start < duration:
        active_start = time.time()

        while time.time() - active_start < active_time:
            z = torch.matmul(x, y)

        torch.cuda.synchronize()

        if idle_time > 0:
            time.sleep(idle_time)

    print("Workload completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--intensity",
        type=float,
        required=True,
        help="Target workload intensity from 1 to 100",
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="Workload duration in seconds",
    )

    args = parser.parse_args()

    run_workload(args.intensity, args.duration) 