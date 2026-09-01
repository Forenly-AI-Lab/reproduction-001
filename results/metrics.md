# What the reported numbers actually mean

Two numbers come out of `lerobot-eval` and get compared against the model
card. One of them does not mean what its name suggests. This file exists so
that a contributor reading `avg_max_reward` off a results file does not have
to rediscover that.

## `pc_success`

The percentage of episodes in which the block ended up more than 95% inside
the goal zone. This one is unsurprising: `gym_pusht` sets
`success_threshold = 0.95` and reports `is_success = coverage > threshold`
([`pusht.py:181,258`](https://github.com/huggingface/gym-pusht/blob/main/gym_pusht/envs/pusht.py#L181)).

Report it with `n`. A success rate without an episode count is not a
measurement — see the running-rate table in the README, where the same run
reads 80.0% at n=20 and 62.0% at n=500.

## `avg_max_reward` — not the average overlap

The model card describes 0.955 as *"average max overlap."* It is not an
overlap. `gym_pusht` computes reward as:

```python
coverage = self._get_coverage()
reward = np.clip(coverage / self.success_threshold, 0.0, 1.0)
```

[`pusht.py:256-257`](https://github.com/huggingface/gym-pusht/blob/main/gym_pusht/envs/pusht.py#L256)

Two things happen there, and both matter.

**It is rescaled.** Reward is coverage divided by 0.95, so a coverage of
0.855 reports as a reward of 0.90. The reward is always the larger number.

**It is clipped.** Any episode reaching 95% coverage — which is exactly the
success condition — reports a reward of `1.0` regardless of whether it
covered 95% or 100%. The information is discarded at the threshold.

`avg_max_reward` is then the mean, over episodes, of the highest reward seen
at any step of that episode. So it is a mean over a rescaled, ceiling-capped
quantity, and every successful episode contributes the same value to it.

### Confirmed on this study's own data

All 500 per-episode records are in
[`beam-rtx4090-eval.json`](beam-rtx4090-eval.json), so this is checkable
rather than asserted:

| | n | mean `max_reward` |
|---|---|---|
| Successful episodes | 310 | **exactly 1.0** — the only value present |
| Failed episodes | 190 | 0.8581 |
| All episodes | 500 | 0.9461 |

The 310 successes carry a single distinct value between them. `avg_max_reward`
of 0.9461 is therefore mostly a restatement of `pc_success`, moved by how
close the failures came.

### What the coverage actually was

For a failed episode the clip never binds, so coverage can be recovered as
`reward × 0.95`. The failures averaged **81.5%** coverage — they were not
wild misses.

For the run as a whole, coverage can only be bounded, because the successes
are censored at the ceiling:

```
mean coverage >= (310 x 0.95 + 190 x 0.8152) / 500 = 0.899
```

So **mean coverage was at least 89.9%**, and the true figure is higher by
however much the successful episodes exceeded 0.95. That number is not
recoverable from the evaluation output; it would require logging
`info["coverage"]`, which `lerobot-eval` does not retain.

### The practical consequence

`avg_max_reward` is fine for comparing two runs of the same task, which is
what this study uses it for: ours reads 0.9461 against a published 0.955, in
the same direction as the success rate. It is not a coverage figure, and it
should not be quoted as one.

Note also that `gym_pusht`'s own docstring — *"The reward is the coverage of
the block in the goal zone"* ([`pusht.py:69`](https://github.com/huggingface/gym-pusht/blob/main/gym_pusht/envs/pusht.py#L69))
— describes the unscaled, unclipped quantity, not the one the code returns.
