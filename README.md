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
| Does it reach 65.4%? | **Not quite** — 62.0% over 500 episodes, 1.6 SE below the claim |

### Result, n = 500

Same checkpoint, same seed, same pinned versions, two different machines.

| | CPU · Xeon 8581C, 8 vCPU | GPU · RTX 4090 (Beam) |
|---|---|---|
| Episodes | 80 (run stopped early) | **500** |
| `pc_success` | 66.2 % | **62.0 %** |
| `avg_max_reward` | — | **0.9461** |
| Seconds per episode | 54.8 | **2.53** |
| Wall clock | 1 h 13 m (of a projected 7.6 h) | **21.6 min** |

**On the headline number.** 62.0% over 500 episodes carries a binomial standard
error of 2.2 points, so the 3.4-point gap to the published 65.4% is about
1.6 SE. That is not a significant difference at the 95% level, and we do not
claim the model card is wrong. But it is not a clean confirmation either: our
point estimate sits below the claim, and separating a real 3.4-point gap from
noise would take roughly 1,500 episodes. `avg_max_reward` lands at 0.9461
against a reported 0.955 — the same direction, slightly low.

**On `avg_max_reward`.** Despite the model card's wording, it is not an
average overlap: the reward is coverage rescaled by 0.95 and then clipped, so
all 310 successful episodes report exactly 1.0. What it does and does not
measure is worked through in [`results/metrics.md`](results/metrics.md).

**On hardware.** Because both arms used `seed=1000`, the CPU run's 80 episodes
are the *same* 80 episodes the GPU run began with. They agree to within a
single episode:

```
first 80 episodes, CPU   66.2 %
first 80 episodes, GPU   67.5 %
```

So the hardware does not move the result. What moves the result is `n`:

```
first  20 episodes   80.0 %
first  40 episodes   67.5 %
first  60 episodes   70.0 %
first  80 episodes   67.5 %
all   500 episodes   62.0 %
```

This study made that mistake on itself. An interim note in this repository once
described the 80-episode figure as "converging on the published number." It was
not converging; it was an optimistic window. A partial run is evidence about a
partial run, and nothing more.

### What could explain the 3.4-point gap

Listed in the order we would bet on them, not in the order that flatters us.
None of these is established; the point of writing them down is that the next
run can eliminate one.

**1. Sampling.** The most boring explanation is also the most likely. At n=500
the standard error is 2.2 points and the gap is 1.6 SE. A difference this size
appears about one time in eight by chance alone. Nothing else needs to be true.

**2. A different draw of episodes.** The model card does not state a seed. We
used `seed=1000`. PushT randomises the pusher position, the block position and
the block angle on every reset, so a different seed is a different set of 500
tasks — some sets are simply harder. This is distinguishable from (1) only by
running more seeds, which we have not done.

**3. The software underneath.** We ran the checkpoint on `lerobot 0.3.2` with
`torch 2.13.0`, `numpy 2.5.2` and `gym-pusht 0.1.6` — versions that did not
exist when the number was published. Physics and sampling both flow through
those libraries. This is the hypothesis this repository exists to examine, and
it is the one we can say least about.

### What we can already rule out

**Hardware.** Both arms ran `seed=1000`, so the CPU run's 80 episodes are the
same 80 the GPU run began with, and they agree to within a single episode
(66.2% against 67.5%). Whatever moved the number, it was not the machine.

### The experiment that would settle it

Run the same evaluation across several seeds. If the spread across seeds covers
3.4 points, (1) and (2) are sufficient and (3) needs no invoking. If every seed
lands below 65.4%, the software stack becomes the suspect. That run is
[issue #4](https://github.com/Forenly-AI-Lab/reproduction-001/issues/4), and it
is open on purpose: we would rather someone else's number sat next to ours than
run it a second time ourselves.

Raw output, including all 500 per-episode records and the environment
fingerprint of the machine that produced them:
[`results/beam-rtx4090-eval.json`](results/beam-rtx4090-eval.json).

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
