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


def _cpu_count() -> dict[str, int | None]:
    """How many cores the run could actually use.

    PushT evaluation is dominated by environment simulation, not by network
    inference, so this number can matter more than the GPU. `os.cpu_count()`
    reports the host's cores, which in a container is usually a lie -- the
    scheduler affinity and the cgroup quota are the two limits that bind.
    All three are recorded because they disagree, and the disagreement is
    itself worth seeing.
    """
    import os

    out: dict[str, int | None] = {
        "os_cpu_count": os.cpu_count(),
        "sched_affinity": None,
        "cgroup_quota": None,
    }
    try:
        out["sched_affinity"] = len(os.sched_getaffinity(0))
    except (AttributeError, OSError):
        pass
    # cgroup v2 first, then v1; "max" means no quota is set.
    for path, period in (
        ("/sys/fs/cgroup/cpu.max", None),
        ("/sys/fs/cgroup/cpu/cpu.cfs_quota_us", "/sys/fs/cgroup/cpu/cpu.cfs_period_us"),
    ):
        try:
            raw = open(path).read().split()
            quota = raw[0]
            if quota in ("max", "-1"):
                break
            per = int(raw[1]) if period is None else int(open(period).read())
            out["cgroup_quota"] = int(int(quota) / per)
            break
        except (OSError, ValueError, IndexError):
            continue
    return out


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
        "cpu_count": _cpu_count(),
        "accelerator": _accelerator(),
        "watched_versions": _versions(),
        "pip_freeze": _pip_freeze(),
    }


if __name__ == "__main__":
    json.dump(fingerprint(), sys.stdout, indent=2)
    print()
