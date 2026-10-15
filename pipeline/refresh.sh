#!/usr/bin/env bash
# Weekly refresh: pull data for every team in teams.json, rebuild the pages at the repo root.
# Usage (from repo root or pipeline/): bash pipeline/refresh.sh
set -euo pipefail
cd "$(dirname "$0")"
IDS=$(python3 -c "import json;print(' '.join(str(t['id']) for t in json.load(open('teams.json'))['teams']))")
python3 fetch.py --team-id $IDS --out "data_{id}.json"
python3 site.py ..
