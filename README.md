# Reproduction 001 — Diffusion Policy on PushT

**Can the published result be reproduced today?**

[`lerobot/diffusion_pusht`](https://huggingface.co/lerobot/diffusion_pusht) is a
released Diffusion Policy checkpoint. Its model card reports:

> **65.4%** success over 500 episodes, average max overlap **0.955**,
> at training step 175,000, on the `PushT` environment from `gym-pusht`.

This repository tries to get that number back, on a machine that is not the one
it was measured on, using software that has moved on since.

---

## Status

| Question | Answer |
|---|---|
| Does the checkpoint load on the current LeRobot (0.6.1)? | **No** — requires a processor migration, and the official migration script crashes |
| Does it load on 0.5.1? | **No** — `policy_preprocessor.json` not found |
| What is the last version that loads it? | **0.3.2** — the processor pipeline arrived in 0.3.3 |
| Does it run on 0.3.2? | **Yes** |
| Does it reach 65.4%? | **Measurement in progress** — pilot below |

### Pilot, n = 10

```
pc_success       60.0 %
avg_max_reward   0.8898
eval_s           933.9 s        (93.4 s per episode, CPU)
```

**This is not a discrepancy.** At n = 10 the binomial standard error around
p = 0.654 is about 15 percentage points; the 5.4-point gap is roughly 0.36 SE.
Ten episodes cannot distinguish 60% from 65.4%, which is exactly why the full
500-episode run is needed. That run is under way and this table will be
replaced by its result.

---

## What broke on the way here

None of these are in the model card or the LeRobot documentation. All were hit
in order, on a clean machine.

### 1. `lerobot[pusht]` is not enough

It installs the environment but not the policy. Diffusion Policy needs
`diffusers`, which lives in a different extra:

```bash
pip install "lerobot[pusht,diffusion]"
```

Without it, evaluation dies at policy construction with an `ImportError` that
does name the fix — this one is at least honest.

### 2. `AsyncVectorEnv` surfaces the wrong error

On LeRobot 0.6.1, running with more than one environment produces:

```
ConnectionResetError: [Errno 104] Connection reset by peer
```

That is a symptom, not the cause. Buried further up the traceback:

```
gymnasium.error.NamespaceNotFound: Namespace gym_pusht not found.
```

`lerobot/envs/configs.py` forces the multiprocessing context to `forkserver`.
A `forkserver` child does not inherit the parent's imports, so the
`importlib.import_module(self.package_name)` that registers `gym_pusht` in the
parent never runs in the workers. The workers die; the parent's pipe resets;
the pipe error is what you see.

Workaround:

```bash
--eval.use_async_envs=false
```

### 3. The published checkpoint predates the published code

From LeRobot 0.3.3 onward, loading a policy requires a `policy_preprocessor.json`
that this checkpoint does not have. See
[`results/version-bisection.md`](results/version-bisection.md) for how that
boundary was located.

On 0.6.1 the error points at a migration script. That script then fails:

```
Exception: Couldn't encode 84
```

and leaves a **zero-byte `config.json`** behind, next to files that did get
written — so a partial failure can look like a partial success. The
freshly-loaded config encodes fine on its own, so the fault is in the state the
migration builds before saving. It has not been isolated further. See
[issue tracker](../../issues).

### 4. Installing CPU torch does not keep CPU torch

Installing `torch` from the CPU index and *then* installing `lerobot` silently
replaces it with a CUDA build, pulling roughly 2.5 GB of `nvidia-*` packages
that a CPU-only machine will never use. Install `lerobot` first, then force the
CPU wheel.

This one is caught by `reproduce/env_fingerprint.py`, which reports
`torch_build` separately from `cuda_available` — a machine can carry a CUDA
build it cannot use.

---

## Reproducing this

```bash
python3 -m venv .venv
.venv/bin/pip install "lerobot[pusht,diffusion]==0.3.2"

# Record the stack BEFORE measuring anything. In this study the
# environment is the finding.
.venv/bin/python reproduce/env_fingerprint.py > my-environment.json

.venv/bin/lerobot-eval \
  --policy.path=lerobot/diffusion_pusht \
  --env.type=pusht \
  --eval.n_episodes=500 \
  --eval.batch_size=20 \
  --seed=1000 \
  --output_dir=my-run
```

On 8 CPU cores this takes several hours. See [`COMPUTE.md`](COMPUTE.md) for
places to run it that are not your own machine.

---

## What we do not know

- Whether 500 episodes on 0.3.2 lands on 65.4%, near it, or somewhere else.
- What the original measurement's stack was. The model card does not say, and
  without it "reproduced" and "not reproduced" are both hard to claim.
- Why the migration script fails.
- Whether the number moves across platforms — different `torch`, different
  `numpy`, different CPU. Nobody has run this anywhere but here yet.

That last one is the most useful thing a contributor can change today.

## Contributing

Read [`CONTRIBUTING.md`](CONTRIBUTING.md). Issues carry a `level:` label so you
can find a starting point; nothing is assigned.

A reproduction that fails is a result. A number that does not match is a
result. Report what happened.

## License

Apache 2.0. Part of [Forenly AI Lab](https://github.com/Forenly-AI-Lab).
