# Compute

**You do not need your own GPU to take part.**

This particular reproduction does not need a GPU at all — it runs on CPU. It is
just slow. Both figures below are measured, not estimated:

| | Hardware | Seconds per episode | 500 episodes |
|---|---|---|---|
| CPU | Intel Xeon 8581C, 8 vCPU | 54.8 | ~7.6 h (projected from 80 episodes) |
| GPU | NVIDIA RTX 4090 (Beam serverless) | **2.53** | **21.6 min** |

That is a **21.7×** speed-up, and it cost $0.24 of GPU time.

**The result itself did not change.** Both arms ran `seed=1000`, so the CPU
run's 80 episodes are the same 80 the GPU run started with — 66.2% against
67.5%, a difference of one episode. The GPU buys you time, not a different
answer. If you only have a CPU, run fewer episodes and say how many; that is a
smaller measurement, not a worse one.

## Places to run it

None of these are endorsements, and none of them guarantee free capacity.
Colab's resources are dynamic and not guaranteed; Kaggle's GPU availability
depends on quota and demand. Check current terms yourself before relying on any
of them.

| Platform | Fits | Notes |
|---|---|---|
| **Google Colab** | 🌱 Explorer | Easiest start. Hosted notebook, GPU/TPU runtimes available. Sessions are ephemeral — save your results out. |
| **Kaggle** | 🌱 Explorer | Notebook with GPU runtime, weekly quota. Good for a benchmark you run once. |
| **Beam Cloud** | 🔧 Contributor | Cloud GPU, billed per second of run time. This study's 500-episode run was done here on an RTX 4090: 21.6 min, $0.24. Serverless containers stop by themselves when the job returns. |
| **Modal** | 🔧 Contributor / 🧪 Research | Cloud GPU, scripted and batchable. Suits repeated or parallel runs. |

Use whatever can run the stated environment. Your own laptop counts.

## Known friction on hosted notebooks

Colab and Kaggle ship their own pinned `torch` and `numpy`. Installing
`lerobot==0.3.2` on top of them can conflict, and the failure is usually a
version-resolution error rather than anything to do with this study. Expect to
spend a few minutes on it, and **if you hit it, report it** — that is itself a
finding, and it belongs in an issue rather than in your private notes.

## What makes a reproduction valid here

Not the hardware. The record.

Report all of:

- **GPU** (model, or "CPU only")
- **CUDA** version, if any
- **Python** version
- **Package versions** — `lerobot`, `torch`, `gymnasium`, `gym-pusht`, `numpy`, `diffusers`
- **Runtime** — wall clock
- **Results** — `pc_success`, `avg_max_reward`, number of episodes, seed

`reproduce/env_fingerprint.py` collects everything except the results. Run it
before you measure, and commit its output next to your numbers.

## Platform diversity is data, not noise

This is worth stating plainly, because it is the opposite of the usual advice.

This study is about whether a published number survives changes in the software
around it. So a run on Colab's stack, a run on Kaggle's stack and a run on your
own laptop are **three data points, not one good one and two contaminated
ones**. If your environment differs from the one in the README, your result is
more interesting, not less.

The only thing that makes a run useless is not recording what it ran on.

## One trap we hit, so you don't

Beam's base image carries apt-installed Python packages that `pip` refuses to
uninstall, so a system-wide `pip install lerobot` fails at image-build time with
`Cannot uninstall blinker 1.4 — it is a distutils installed project`. The fix is
not `--ignore-installed`; it is to build a clean virtualenv inside the container
and install into that. `reproduce/beam_job.py` does this, and verifies the
install during the build rather than at run time:

```
python3.12 -m venv /opt/repro
/opt/repro/bin/pip install 'lerobot[pusht,diffusion]==0.3.2'
/opt/repro/bin/python -c 'import lerobot, gym_pusht, torch'
```

Two more things worth knowing there. `gym-pusht` pulls OpenCV, which opens
`libGL` on import even when nothing is drawn, so the image needs `libgl1` and
`libglib2.0-0`. And Beam does not read `.gitignore` — without a `.beamignore`,
local virtualenvs are uploaded on every run. Ours were 20 GB. Excluding them
took the sync from 20 GB to 43 kB.

## A note on counting cores

`env_fingerprint.py` records `os.cpu_count()`, the scheduler affinity and the
cgroup quota separately, because in a container they disagree. On Beam all three
report 255 while the job requested 8 — the sandbox reports the host's cores, not
the allocation. Treat a container's core count as unknown unless the platform
tells you directly. It is recorded anyway: an unreliable number, labelled as
such, is more useful than a confident wrong one.
