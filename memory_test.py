import torch

device = torch.device("cuda")

x = torch.randn(4096, 4096, device=device)
y = torch.randn(4096, 4096, device=device)

torch.cuda.synchronize()

print("Allocated GPU memory:",
      torch.cuda.memory_allocated() / 1024**2, "MiB")

print("Reserved GPU memory:",
      torch.cuda.memory_reserved() / 1024**2, "MiB")

input("Press Enter to release GPU memory...")