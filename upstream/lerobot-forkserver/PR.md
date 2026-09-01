# PR description — draft, not submitted

**Title:** Register the env package inside the worker factory, not only in the parent

## What

One line in `EnvConfig.create_envs`: call `importlib.import_module(self.package_name)`
inside `_make_one`.

## Why

`create_envs` imports the env package in the parent process and then builds the
`AsyncVectorEnv` with `context="forkserver"`. Forkserver workers start from a
clean interpreter and inherit none of the parent's imports, so `gym.make` in the
worker raises `NameNotFound` against an empty registry.

The worker dies before that exception can travel back over the pipe, so the
caller sees `ConnectionResetError: [Errno 104] Connection reset by peer` from
`multiprocessing/connection.py` — an error that points at the transport rather
than at the missing registration, and sends the reader looking in the wrong
place.

This affects every caller passing `use_async_envs=True` with `n_envs > 1`. The
default is `False`, which is likely why it has survived.

## Cost

`importlib.import_module` returns the cached module after the first call in a
process, so the added call is a dict lookup for the parent, the synchronous
path, and every worker after its first env.

## Testing

- `make_env(make_env_config("pusht"), n_envs=2, use_async_envs=True)` followed
  by `.reset(seed=0)` fails on `main` and passes with this change.
- A 45-line standalone reproduction that imports no lerobot shows the same
  bug and the same fix in isolation.

Both are attached to the issue.

## Not addressed here

`lerobot/envs/utils.py:287` sets `context="forkserver"` at a second site and may
have the same defect. It is out of scope for this PR and is not claimed to be
broken.
