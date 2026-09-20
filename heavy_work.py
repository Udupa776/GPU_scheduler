import time
import torch

device = torch.device("cuda")

x = torch.randn(4096, 4096, device=device)
y = torch.randn(4096, 4096, device=device)

print("Starting heavy workload...")

start = time.time()

while time.time() - start < 20:
    z = torch.matmul(x, y)
    torch.cuda.synchronize()

print("Heavy workload completed.")