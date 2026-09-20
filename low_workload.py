import time
import torch

device = torch.device("cuda")

print("Starting LOW workload...")
print("GPU:", torch.cuda.get_device_name(0))

# Small workload
x = torch.randn(1024, 1024, device=device)
y = torch.randn(1024, 1024, device=device)

start = time.time()

while time.time() - start < 30:
    z = torch.matmul(x, y)

    # Leave gaps between GPU operations.
    # This controls how much work we submit over time.
    torch.cuda.synchronize()
    time.sleep(0.02)

print("LOW workload completed.")
