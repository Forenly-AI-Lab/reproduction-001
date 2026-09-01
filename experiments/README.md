# experiments/

One directory per run, named for who ran it and on what.

A run belongs here when it differs from the baseline in a way worth recording:
a different platform, a different package version, a different seed, a
different episode count.

Each directory should contain:

```
<name>/
├── environment.json   output of reproduce/env_fingerprint.py, taken BEFORE the run
├── command.txt        the exact command line
├── results.json       pc_success, avg_max_reward, n_episodes, seed, wall clock
└── notes.md           what you expected, what happened, what you are unsure about
```

`notes.md` is not optional and not a formality. A number without the story
around it cannot be compared to anything. If the run failed, the notes are the
entire contribution — say where it broke and what you saw.

Before quoting `avg_max_reward` in `results.json`, read
[`../results/metrics.md`](../results/metrics.md). It is not the average
overlap its name suggests, and reporting it as one will mislead whoever
reads your run next.
