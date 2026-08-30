# Compute

**You do not need your own GPU to take part.**

This particular reproduction does not need a GPU at all — it runs on CPU. It is
just slow: on 8 CPU cores, 500 episodes takes several hours. A modest cloud GPU
turns that into well under an hour.

## Places to run it

None of these are endorsements, and none of them guarantee free capacity.
Colab's resources are dynamic and not guaranteed; Kaggle's GPU availability
depends on quota and demand. Check current terms yourself before relying on any
of them.

| Platform | Fits | Notes |
|---|---|---|
| **Google Colab** | 🌱 Explorer | Easiest start. Hosted notebook, GPU/TPU runtimes available. Sessions are ephemeral — save your results out. |
| **Kaggle** | 🌱 Explorer | Notebook with GPU runtime, weekly quota. Good for a benchmark you run once. |
| **Beam Cloud** | 🔧 Contributor | Cloud GPU, billed for run time only. Better for longer jobs. |
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
