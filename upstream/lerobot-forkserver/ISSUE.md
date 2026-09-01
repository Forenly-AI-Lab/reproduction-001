# `make_env(..., use_async_envs=True)` fails: forkserver workers never import the env package

**Status: draft. Not submitted.** See `../README.md`.

**Target:** `huggingface/lerobot`
**Affected:** confirmed on `0.6.1`; the code path is unchanged back to `0.3.2`
**Component:** `lerobot/envs/configs.py` → `EnvConfig.create_envs`

## Summary

`create_envs` registers the environment package in the **parent** process, then
builds an `AsyncVectorEnv` with `context="forkserver"`. Forkserver workers start
from a clean interpreter and do not inherit the parent's imports, so `gym.make`
in the worker raises `NameNotFound`. The worker dies before it can send that
error back, and the parent surfaces `ConnectionResetError: [Errno 104]` instead
— which points at multiprocessing rather than at the missing registration.

Anyone using `use_async_envs=True` with `n_envs > 1` hits this. It is not the
default (`use_async_envs=False`), which is presumably why it has gone unnoticed.

## Reproduction

Through LeRobot's own API:

```python
from lerobot.envs.factory import make_env, make_env_config

if __name__ == "__main__":
    cfg = make_env_config("pusht")
    envs = make_env(cfg, n_envs=2, use_async_envs=True)
    envs["pusht"][0].reset(seed=0)
```

```
ConnectionResetError: [Errno 104] Connection reset by peer
```

`repro.py` in this directory reduces it further — 45 lines, no lerobot import —
and takes `--fix` to show the same script passing.

```
$ python repro.py
ConnectionResetError: [Errno 104] Connection reset by peer
$ python repro.py --fix
OK — obs (2, 5)
```

The `if __name__ == "__main__"` guard in that script is load-bearing. Without
it the forkserver re-imports the module and re-forks, producing a different
failure that resembles this one and is not it.

## Expected vs actual

| | |
|---|---|
| Expected | The vector env builds, or fails with an error naming the unregistered env |
| Actual | `ConnectionResetError: [Errno 104] Connection reset by peer` from `multiprocessing/connection.py` |

The second complaint is as important as the first: the error names the wrong
layer. The real exception, `gym.error.NameNotFound`, is raised in a worker that
dies before the pipe carries it.

## Mechanism

In `lerobot/envs/configs.py` (0.6.1):

- **L95–107** — registration happens here, in the parent:
  ```python
  if self.gym_id not in gym_registry:
      importlib.import_module(self.package_name)
  ```
- **L110–111** — the worker factory does *not* import the package:
  ```python
  def _make_one():
      return gym.make(self.gym_id, disable_env_checker=..., **self.gym_kwargs)
  ```
- **L114–115** — the start method is forced to forkserver:
  ```python
  if env_cls is gym.vector.AsyncVectorEnv:
      extra_kwargs["context"] = "forkserver"
  ```

Under `fork`, the child would inherit the populated registry and this would
work. Under `forkserver` it cannot: the server process is spawned from a clean
interpreter state, so the parent's `importlib.import_module` never reaches it.

## Proposed fix

One line, inside `_make_one`, so registration happens wherever the factory
actually runs:

```diff
     def _make_one():
+        importlib.import_module(self.package_name)
         return gym.make(self.gym_id, disable_env_checker=self.disable_env_checker, **self.gym_kwargs)
```

`import_module` is a cached no-op after the first call in a process, so the
parent and the synchronous path pay nothing measurable. Verified against the
real `create_envs` code path on 0.6.1: `FIX OK — keys: ['agent_pos', 'pixels']`.

## Not investigated

`lerobot/envs/utils.py:287` sets `context="forkserver"` at a second site. It
looks like the same class of problem, but we have not reproduced it and are not
claiming it here.

## Where this came from

Found while running an independent reproduction of the published
`lerobot/diffusion_pusht` baseline:
https://github.com/Forenly-AI-Lab/reproduction-001
