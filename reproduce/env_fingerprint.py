#!/usr/bin/env python3
"""Environment fingerprint — the part of a reproduction that is usually missing.

In this study the environment IS the finding. The same command produces
65.4%, 0%, or does not start at all, depending on which versions are
installed. A success rate reported without the stack that produced it
cannot be compared against anything.

So this is written to run BEFORE the evaluation, and to be committed
alongside the result. It records nothing that identifies the machine's
owner -- no hostname, no username, no paths.

    python reproduce/env_fingerprint.py > results/<name>.env.json
"""
from __future__ import annotations

import json
import platform
import subprocess
import sys

# Only the packages that have been observed to change the outcome. A full
# `pip freeze` is also captured below; this shorter list is what a reader
# compares at a glance.
WATCHED = [
    "lerobot",
    "torch",
    "torchvision",
    "gymnasium",
    "gym-pusht",
    "numpy",
    "diffusers",
    "draccus",
    "huggingface-hub",
]


def _versions() -> dict[str, str | None]:
    from importlib.metadata import PackageNotFoundError, version

    out: dict[str, str | None] = {}
    for name in WATCHED:
        try:
            out[name] = version(name)
        except PackageNotFoundError:
            out[name] = None          # absent is a finding too, not an error
    return out


def _cpu() -> str:
    """Model name from /proc/cpuinfo. Falls back to the platform string."""
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "unknown"


def _accelerator() -> dict[str, object]:
    """Whether a GPU was actually used -- not whether one exists.

    `torch.cuda.is_available()` is the honest question here: a machine can
    have a card that this torch build cannot address, and the run would
    still be a CPU run.
    """
    try:
        import torch
    except ImportError:
        return {"torch_present": False}

    info: dict[str, object] = {
        "torch_present": True,
        "cuda_available": torch.cuda.is_available(),
        "torch_build": "cuda" if torch.version.cuda else "cpu",
        "cuda_version": torch.version.cuda,
    }
    if torch.cuda.is_available():
        info["device_name"] = torch.cuda.get_device_name(0)
    return info


def _pip_freeze() -> list[str]:
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pip", "freeze", "--disable-pip-version-check"],
            capture_output=True, text=True, timeout=120,
        )
        return r.stdout.splitlines() if r.returncode == 0 else []
    except (OSError, subprocess.SubprocessError):
        return []


def fingerprint() -> dict[str, object]:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "cpu": _cpu(),
        "accelerator": _accelerator(),
        "watched_versions": _versions(),
        "pip_freeze": _pip_freeze(),
    }


if __name__ == "__main__":
    json.dump(fingerprint(), sys.stdout, indent=2)
    print()
