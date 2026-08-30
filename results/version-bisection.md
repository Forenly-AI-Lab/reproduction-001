# Which LeRobot versions can load `lerobot/diffusion_pusht`?

**Method.** Downloaded every `lerobot` distribution on PyPI with
`pip download --no-deps` and checked for the presence of
`lerobot/processor/pipeline.py`. No installation, no dependency
resolution — the file either ships in the distribution or it does not.

**Result.**

| Version | `processor/pipeline.py` |
|---|---|
| 0.1.0 | absent |
| 0.3.2 | absent |
| 0.3.3 | **present** |
| 0.4.0 – 0.4.4 | present |
| 0.5.0, 0.5.1 | present |
| 0.6.0, 0.6.1 | present |

The processor pipeline was introduced in **0.3.3**.

**Why this matters.** The processor pipeline holds the policy's
normalization. From 0.3.3 onward, loading a policy calls
`PolicyProcessorPipeline.from_pretrained`, which requires a
`policy_preprocessor.json` in the checkpoint. The published
`lerobot/diffusion_pusht` checkpoint does not contain that file — it
predates the format.

Confirmed by running, not inferred:

- **0.6.1** → `ProcessorMigrationError`, pointing at a migration script
- **0.5.1** → `FileNotFoundError: Could not find 'policy_preprocessor.json'
  on the HuggingFace Hub at 'lerobot/diffusion_pusht'`

So the reported **65.4% success over 500 episodes** was measured on a
stack no released version can reproduce directly. The last version that
can load the checkpoint without migration is **0.3.2**.

**What this does not say.** It does not say the checkpoint is broken, or
that the reported number is wrong. It says the published artifact and the
published code have drifted apart, and that nothing on PyPI today closes
the gap without an extra step.
