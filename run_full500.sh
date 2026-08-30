#!/usr/bin/env bash
# Full 500-episode evaluation of lerobot/diffusion_pusht on lerobot 0.3.2.
# Detached on purpose: this takes ~10 h and must survive the shell that starts it.
set -u
cd /home/ubuntu/lab/reproduction-001
OUT=results/full500-v032
.venv-032/bin/python reproduce/env_fingerprint.py > $OUT/environment.json 2>/dev/null
START=$(date -Is)
/usr/bin/time -f "WALL=%e s MAXRSS=%M KB" .venv-032/bin/lerobot-eval \
  --policy.path=lerobot/diffusion_pusht \
  --env.type=pusht \
  --eval.n_episodes=500 \
  --eval.batch_size=20 \
  --seed=1000 \
  --output_dir=$OUT/eval > $OUT/run.log 2>&1
CODE=$?
printf '{"started":"%s","finished":"%s","exit_code":%d}\n' "$START" "$(date -Is)" "$CODE" > $OUT/RUN_STATUS.json
