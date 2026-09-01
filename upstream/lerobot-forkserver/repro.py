#!/usr/bin/env python3
"""Minimal reproduction: AsyncVectorEnv + forkserver loses the env registry.

Deliberately does not import lerobot. The failure is in the interaction
between Gymnasium's registry and the forkserver start method; lerobot only
supplies the conditions.

    python repro.py          # fails
    python repro.py --fix    # passes

The `if __name__ == "__main__"` guard below is load-bearing. Without it the
forkserver re-imports this module in the child and re-forks, which produces
a different failure that looks similar and is not the one being reported.
"""
import argparse
import importlib

import gymnasium as gym

ENV_ID = "gym_pusht/PushT-v0"


def build(with_worker_import: bool):
    # The registration happens here, in the parent -- exactly as lerobot's
    # factory does it, and exactly as any user does it by importing the
    # plugin package before calling gym.make().
    if ENV_ID not in gym.registry:
        importlib.import_module("gym_pusht")

    def _make_one():
        if with_worker_import:
            # The fix: register again inside the worker, which does not
            # inherit the parent's imports under forkserver.
            importlib.import_module("gym_pusht")
        return gym.make(ENV_ID, disable_env_checker=True)

    return gym.vector.AsyncVectorEnv([_make_one, _make_one], context="forkserver")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true")
    args = ap.parse_args()

    envs = build(with_worker_import=args.fix)
    obs, _ = envs.reset(seed=0)
    print(f"OK — obs {obs.shape}")
    envs.close()
