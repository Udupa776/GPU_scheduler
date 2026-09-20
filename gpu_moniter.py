import subprocess


def get_gpu_state():
    command = [
        "nvidia-smi",
        "--query-gpu=utilization.gpu,utilization.memory,memory.used,memory.total,power.draw,temperature.gpu",
        "--format=csv,noheader,nounits",
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
    )

    values = [value.strip() for value in result.stdout.strip().split(",")]

    return {
        "compute_utilization": float(values[0]),
        "memory_utilization": float(values[1]),
        "vram_used_mb": float(values[2]),
        "vram_total_mb": float(values[3]),
        "power_w": float(values[4]),
        "temperature_c": float(values[5]),
    }


if __name__ == "__main__":
    state = get_gpu_state()

    print("Current GPU state:")
    for key, value in state.items():
        print(f"{key}: {value}")