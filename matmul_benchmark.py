import time
import torch

device = torch.device("cuda")

x = torch.randn(4096, 4096, device=device)
y = torch.randn(4096, 4096, device=device)

# Warm up
for _ in range(10):
    torch.matmul(x, y)

torch.cuda.synchronize()

times = []

for _ in range(100):
    start = time.perf_counter()

    z = torch.matmul(x, y)

    torch.cuda.synchronize()
    end = time.perf_counter()

    times.append((end - start) * 1000)

print(f"Average: {sum(times) / len(times):.3f} ms")
print(f"Minimum: {min(times):.3f} ms")
print(f"Maximum: {max(times):.3f} ms")