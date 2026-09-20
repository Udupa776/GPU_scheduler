import time
import torch

device = torch.device("cuda")

print("Starting Workload B...")
print("GPU:", torch.cuda.get_device_name(0))

x = torch.randn(1024, 1024, device=device)
y = torch.randn(1024, 1024, device=device)

start = time.time()

while time.time() - start < 30:
    z = torch.matmul(x, y)
    torch.cuda.synchronize()

    # Slightly longer idle period than Workload A
    time.sleep(0.035)

print("Workload B completed.")