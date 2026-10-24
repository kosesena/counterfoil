#!/bin/sh
# One evaluation pass on the gateway model, then idle so the platform does not restart the container.
# CF_MODEL picks a gateway model (default: the deploy-time MODEL_DEFAULT); CF_IDS / CF_SPLIT,
# CF_CONDITIONS and CF_REPEATS mirror scripts/run_eval.py. Every result row is echoed as "CFROW <json>"
# so the host can collect it from `ast project logs`.
set -e
[ -f astropods/run.env ] && . astropods/run.env   # baked into the image: ast does not pass .env vars through
export CF_MODEL
OUT=results/astropods-run.jsonl
if [ -n "$CF_IDS" ]; then SEL="--ids $CF_IDS"; else SEL="--split ${CF_SPLIT:-dev}"; fi
python scripts/run_eval.py --model astropods $SEL --conditions "${CF_CONDITIONS:-counterfoil,cap,none}" \
  --repeats "${CF_REPEATS:-1}" --out "$OUT" || echo "CFERROR run_eval exited $?"
sed 's/^/CFROW /' "$OUT"
echo "CFDONE"
exec sleep infinity
