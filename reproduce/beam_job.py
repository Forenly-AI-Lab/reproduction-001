#!/usr/bin/env python3
"""The GPU arm of the reproduction, on Beam serverless.

This runs the SAME command as `run_full500.sh`, with the same checkpoint,
the same seed and the same pinned versions. The only variable that changes
is the hardware underneath. That is the whole design: if the two arms
disagree, the disagreement is about compute, not about the software stack.

Serverless is deliberate. An on-demand reservation has to be released by
hand, and we have already seen what an unreleased GPU costs. A serverless
container ends when the function returns.

    python reproduce/beam_job.py --probe    # cheap: build image, check env
    python reproduce/beam_job.py            # the real 500-episode run
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import time

from beam import Image, function

REPO = pathlib.Path(__file__).resolve().parent.parent

# Pinned to the one version that runs this checkpoint at all. Versions from
# 0.3.3 onward expect a processor format the published checkpoint predates
# -- see results/version-bisection.md.
LEROBOT_PIN = "lerobot[pusht,diffusion]==0.3.2"

# Installed into a venv rather than the base image's system Python, for the
# same reason the local arm uses one: Beam's base image carries apt-installed
# Python packages (blinker) that pip refuses to uninstall, so a system-wide
# install of lerobot fails outright at build time. A venv also makes the two
# arms structurally identical -- both are a clean python3.12 environment with
# exactly one pinned install in it.
VENV = "/opt/repro"

# gym-pusht pulls opencv, which dlopen()s libGL at import time even when
# nothing is ever drawn. Without these the container fails on `import cv2`,
# several layers below anything that mentions PushT.
IMAGE = (
    Image(python_version="python3.12")
    .add_commands([
        "apt-get update -qq",
        "apt-get install -y -qq libgl1 libglib2.0-0 python3.12-venv",
        f"python3.12 -m venv {VENV}",
        f"{VENV}/bin/pip install -q --upgrade pip",
        f"{VENV}/bin/pip install -q '{LEROBOT_PIN}'",
        f"{VENV}/bin/python -c 'import lerobot, gym_pusht, torch; print(lerobot.__version__)'",
    ])
)

# retries=0 on purpose. The default is 3, and a silently retried run would
# bill three times and could report a number from an attempt we never saw.
COMMON = dict(image=IMAGE, gpu="RTX4090", cpu=8, memory="32Gi", retries=0)


def _fingerprint() -> dict:
    """Run the study's own fingerprint tool, whatever the working dir is."""
    for candidate in (
        pathlib.Path("/mnt/code/reproduce/env_fingerprint.py"),
        pathlib.Path(__file__).resolve().parent / "env_fingerprint.py",
        pathlib.Path("reproduce/env_fingerprint.py"),
    ):
        if candidate.exists():
            # Run it with the venv's interpreter, not the container's system
            # Python -- otherwise it fingerprints an environment that has no
            # lerobot in it and reports every watched package as absent.
            r = subprocess.run(
                [f"{VENV}/bin/python", str(candidate)], capture_output=True, text=True
            )
            if r.returncode == 0:
                return json.loads(r.stdout)
    return {"error": "env_fingerprint.py not found in container"}


@function(timeout=600, **COMMON)
def probe() -> dict:
    """Seconds, not hours: prove the image and the versions before committing."""
    import os

    return {
        "fingerprint": _fingerprint(),
        "cwd": os.getcwd(),
        # Which of the candidate paths actually exist tells us whether the
        # study's own files were synced, and whether the eval CLI is callable.
        "synced": sorted(p for p in ("/mnt/code", "reproduce", "reproduce/env_fingerprint.py")
                         if os.path.exists(p)),
        "eval_cli": os.path.exists(f"{VENV}/bin/lerobot-eval"),
    }


@function(timeout=10800, **COMMON)
def evaluate() -> dict:
    """500 episodes, identical argv to the local CPU arm."""
    out = "/tmp/eval"
    cmd = [
        f"{VENV}/bin/lerobot-eval",
        "--policy.path=lerobot/diffusion_pusht",
        "--env.type=pusht",
        "--eval.n_episodes=500",
        "--eval.batch_size=20",
        "--seed=1000",
        f"--output_dir={out}",
    ]

    fp = _fingerprint()
    started = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True)
    wall = time.time() - started

    info_path = pathlib.Path(out) / "eval_info.json"
    info = json.loads(info_path.read_text()) if info_path.exists() else None

    return {
        "command": " ".join(cmd),
        "exit_code": proc.returncode,
        "wall_seconds": round(wall, 1),
        "seconds_per_episode": round(wall / 500, 3),
        "fingerprint": fp,
        # Aggregated metrics are the answer; the per-episode list is what
        # lets someone else recompute them instead of trusting ours.
        "aggregated": (info or {}).get("aggregated"),
        "per_episode": (info or {}).get("per_episode"),
        # Kept only on failure -- on success this is a progress bar.
        "stderr_tail": None if proc.returncode == 0 else proc.stderr[-4000:],
    }


if __name__ == "__main__":
    is_probe = "--probe" in sys.argv
    fn, name = (probe, "probe") if is_probe else (evaluate, "eval")

    t0 = time.time()
    result = fn.remote()
    print(f"[{name}] returned after {time.time() - t0:.1f}s (includes cold start)")

    # A failed build or a killed container returns None. Writing that as the
    # result would look like a run that produced nothing, rather than a run
    # that never happened -- so say which it was.
    if result is None:
        print(f"[{name}] FAILED: no result returned (see log above)", file=sys.stderr)
        sys.exit(1)

    dest = REPO / "results" / f"beam-rtx4090-{name}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=2) + "\n")
    print(f"[{name}] wrote {dest}")

    if not is_probe:
        agg = (result or {}).get("aggregated") or {}
        print(json.dumps(agg, indent=2))
