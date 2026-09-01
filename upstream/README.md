# upstream/

Findings from this reproduction that appear to be defects in LeRobot rather
than in our setup, prepared for reporting upstream.

**Nothing here has been submitted.** No issue is open, no PR is filed. These
are drafts held until someone decides to send them.

| # | Finding | Evidence | State |
|---|---|---|---|
| 1 | [`AsyncVectorEnv` + forkserver loses the env registry](lerobot-forkserver/) | complete | **ready to submit** |
| 2 | Published checkpoint will not load from 0.3.3 onward | partial | TODO |
| 3 | `migrate_policy_normalization.py` crashes | partial | TODO |

Findings 2 and 3 are recorded in this repository's issues
([#5](https://github.com/Forenly-AI-Lab/reproduction-001/issues/5)) and in
[`../results/version-bisection.md`](../results/version-bisection.md). They are
deliberately **not** being investigated further right now; the notes below say
what is missing so that whoever picks them up does not start from nothing.

---

## Finding 1 — ready

`lerobot-forkserver/` holds the issue text, a standalone 45-line reproduction,
the proposed one-line fix, and the PR description. The mechanism is identified,
the fix is verified on the real code path in 0.6.1, and a search of the LeRobot
tracker found nothing already reporting it.

Before submitting, still to do: read LeRobot's `CONTRIBUTING.md` for DCO or CLA
requirements, and decide which GitHub account files it.

## Finding 2 — TODO: checkpoint will not load from 0.3.3 onward

**What we observed.** `lerobot/diffusion_pusht` loads on 0.3.2 and on no later
version. 0.5.1 reports `policy_preprocessor.json` not found; 0.6.1 raises
`ProcessorMigrationError`. The processor pipeline arrived in 0.3.3, and the
published checkpoint predates the format.

**Why this is not yet reportable.** We have not established whether this is a
defect or an intended, documented break. A released checkpoint on the Hub that
the current library cannot load is a real problem for users either way, but the
issue has to say which one it is, and we cannot yet.

**Missing evidence:**

- Fresh, verbatim error output from 0.5.1 and 0.6.1, captured in clean
  environments. What we have is summarised in `../results/version-bisection.md`,
  not quoted.
- Whether the 0.3.3 release notes or migration docs state that pre-0.3.3
  checkpoints require migration.
- Whether other published checkpoints are affected, or only this one. A
  one-checkpoint problem is a Hub-asset issue; a general one is a library issue,
  and they go to different places.

## Finding 3 — TODO: migration script crashes

**What we observed.** `migrate_policy_normalization.py`, the script 0.6.1's
error message points to, fails with `Couldn't encode 84` and leaves a
zero-byte `config.json` behind.

**Why this is not yet reportable.** The root cause was never isolated. We do
not know what "84" refers to, whether the failure is specific to this
checkpoint, or whether our invocation was correct. Filing it in this state
would hand a maintainer a symptom and no lead.

**Missing evidence:**

- A clean re-run from a fresh clone with the exact command line recorded, to
  rule out our own environment.
- The full traceback, not just the message.
- What the script was encoding when it failed — whether 84 is a byte, an index,
  or a tensor dimension.
- Whether the zero-byte `config.json` is written before or after the crash;
  if before, the script is destructive on failure, which is the more serious
  half of the report.
