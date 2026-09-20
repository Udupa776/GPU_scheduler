# Resource-Aware GPU Scheduler for AI Workloads

A resource-aware GPU scheduling system designed for **AI data centers and shared GPU infrastructure**.

Instead of treating a GPU as simply **"busy" or "free"**, the scheduler analyzes the current GPU state and the resource requirements of incoming AI workloads. Based on the predicted resource demand, it decides whether a workload should **RUN, CO-LOCATE, or QUEUE**.

## 🚀 Problem

AI data centers run many GPU-intensive workloads such as:

- Model training
- Deep learning inference
- Image and video processing
- Data processing
- AI/ML experimentation

Traditional scheduling approaches can be conservative and may make a workload wait whenever a GPU is already occupied, even when the GPU still has available resources.

On the other hand, running too many workloads together can cause resource contention and overload.

This creates a scheduling problem:

> **How can we safely run more AI workloads on shared GPUs while reducing unnecessary waiting?**

## 💡 Our Approach

We developed a **resource-aware GPU scheduler** that evaluates GPU resources before admitting a new workload.

The scheduler considers:

- GPU compute utilization
- GPU memory utilization
- VRAM usage
- Configurable resource limits
- Resource requirements of the incoming workload
- Currently running workloads

It then makes one of three decisions:

```text
                    New Workload
                         |
                         v
              Analyze GPU Resources
                         |
                         v
              Predict Resource Demand
                         |
             +-----------+-----------+
             |           |           |
          Within      Capacity     Exceeds
          limits      available     limits
             |           |           |
             v           v           v
           RUN       CO-LOCATE     QUEUE
```
