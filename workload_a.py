import time
import torch

device = torch.device("cuda")

print("Starting Workload A...")
print("GPU:", torch.cuda.get_device_name(0))

x = torch.randn(4096, 4096, device=device)
y = torch.randn(4096, 4096, device=device)

start = time.time()

while time.time() - start < 30:
    z = torch.matmul(x, y)
    torch.cuda.synchronize()

print("Workload A completed.")