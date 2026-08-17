import importlib.metadata
import sys

import torch


def test_python_version() -> None:
    assert sys.version_info[:2] == (3, 12)


def test_torch_cuda_available() -> None:
    assert torch.cuda.is_available() is True


def test_torch_cuda_build_version() -> None:
    assert torch.version.cuda is not None
    assert tuple(int(x) for x in torch.version.cuda.split(".")[:2]) >= (12, 8)


def test_gpu_compute_capability() -> None:
    assert torch.cuda.get_device_capability(0) == (12, 0)


def test_cuda_kernel_execution() -> None:
    x = torch.ones(2, 2, device="cuda")
    y = x + x
    assert y.sum().item() == 8.0


def test_mineru_version() -> None:
    assert importlib.metadata.version("mineru") == "3.4.4"
