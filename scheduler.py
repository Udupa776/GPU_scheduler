from dataclasses import dataclass


@dataclass
class ResourceProfile:
    name: str
    compute_utilization: float
    memory_utilization: float
    vram_mb: float
    runtime_seconds: float


# Measured profiles from our RTX 3050 experiments.
LOW = ResourceProfile(
    name="LOW",
    compute_utilization=23.0,
    memory_utilization=18.0,
    vram_mb=133.0,
    runtime_seconds=30.0,
)

MEDIUM = ResourceProfile(
    name="MEDIUM",
    compute_utilization=40.0,
    memory_utilization=27.0,
    vram_mb=369.0,
    runtime_seconds=20.0,
)

HEAVY = ResourceProfile(
    name="HEAVY",
    compute_utilization=99.0,
    memory_utilization=43.0,
    vram_mb=369.0,
    runtime_seconds=20.0,
)


@dataclass
class SchedulerConfig:
    max_compute_utilization: float = 100.0
    max_memory_utilization: float = 80.0
    max_vram_utilization: float = 80.0
    vram_total_mb: float = 6144.0


def can_admit(
    current_compute: float,
    current_memory: float,
    current_vram_mb: float,
    workload: ResourceProfile,
    config: SchedulerConfig,
):
    predicted_compute = current_compute + workload.compute_utilization
    predicted_memory = current_memory + workload.memory_utilization
    predicted_vram = current_vram_mb + workload.vram_mb

    max_allowed_vram = (
        config.vram_total_mb
        * config.max_vram_utilization
        / 100
    )

    if predicted_compute > config.max_compute_utilization:
        return {
            "decision": "QUEUE",
            "reason": "Predicted compute utilization exceeds the safety limit.",
            "predicted_compute": predicted_compute,
            "predicted_memory": predicted_memory,
            "predicted_vram_mb": predicted_vram,
        }

    if predicted_memory > config.max_memory_utilization:
        return {
            "decision": "QUEUE",
            "reason": "Predicted memory utilization exceeds the safety limit.",
            "predicted_compute": predicted_compute,
            "predicted_memory": predicted_memory,
            "predicted_vram_mb": predicted_vram,
        }

    if predicted_vram > max_allowed_vram:
        return {
            "decision": "QUEUE",
            "reason": "Predicted VRAM usage exceeds the safety limit.",
            "predicted_compute": predicted_compute,
            "predicted_memory": predicted_memory,
            "predicted_vram_mb": predicted_vram,
        }

    return {
        "decision": "ADMIT",
        "reason": "Predicted resource usage is within all configured limits.",
        "predicted_compute": predicted_compute,
        "predicted_memory": predicted_memory,
        "predicted_vram_mb": predicted_vram,
    }