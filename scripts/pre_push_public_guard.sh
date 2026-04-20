#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
cd "$repo_root"

tmp_input="$(mktemp)"
tmp_output="$(mktemp)"
cleanup() {
  rm -f "$tmp_input" "$tmp_output"
}
trap cleanup EXIT

had_ref=0
payload=""
while IFS=' ' read -r local_ref local_sha remote_ref remote_sha; do
  [[ -z "${local_ref:-}" ]] && continue
  had_ref=1

  if [[ "$local_sha" =~ ^0+$ ]]; then
    continue
  fi

  if [[ "$remote_sha" =~ ^0+$ ]]; then
    range="$local_sha^!"
  else
    range="$remote_sha..$local_sha"
  fi

  if ! git rev-parse --verify "$local_sha" >/dev/null 2>&1; then
    echo "[public-surface-guard] Unable to resolve local ref $local_ref" >&2
    exit 1
  fi

  diff_text="$(git diff --no-color "$range" || true)"
  if [[ -z "$diff_text" ]]; then
    continue
  fi

  payload+=$'\n=== REF ===\n'
  payload+="local_ref: $local_ref\nlocal_sha: $local_sha\nremote_ref: $remote_ref\nremote_sha: $remote_sha\nrange: $range\n"
  payload+=$'\n=== DIFF ===\n'
  payload+="$diff_text"
  payload+=$'\n'
done

if [[ "$had_ref" -eq 0 ]]; then
  echo "[public-surface-guard] No refs supplied; blocking push." >&2
  exit 1
fi

if [[ -z "$payload" ]]; then
  echo "[public-surface-guard] No outgoing diff to review; allowing push."
  exit 0
fi

cat > "$tmp_input" <<EOF
You are reviewing content that is about to be pushed to a PUBLIC remote.

Review the following git diff payload and decide whether it risks exposing private information about Julius Biskopstø, private information about Usable, secrets, credentials, workspace IDs, system prompts, raw internal context, or any other non-public operational detail.

Return ONLY valid JSON with this exact schema:
{
  "allow": true,
  "risk_level": "low",
  "reasons": [],
  "findings": []
}

If uncertain, set allow=false.

BEGIN_DIFF_PAYLOAD
$payload
END_DIFF_PAYLOAD
EOF

if ! public-surface-guard chat -Q -q "$(cat "$tmp_input")" > "$tmp_output" 2>/dev/null; then
  echo "[public-surface-guard] Review agent failed; blocking push." >&2
  exit 1
fi

python3 - "$tmp_output" <<'PY'
import json, sys
from pathlib import Path
text = Path(sys.argv[1]).read_text().strip()
start = text.find('{')
end = text.rfind('}')
if start == -1 or end == -1 or end < start:
    print('[public-surface-guard] Non-JSON output; blocking push.', file=sys.stderr)
    sys.exit(1)
try:
    data = json.loads(text[start:end+1])
except Exception:
    print('[public-surface-guard] Invalid JSON output; blocking push.', file=sys.stderr)
    sys.exit(1)
allow = data.get('allow') is True
risk = data.get('risk_level', 'unknown')
reasons = data.get('reasons', [])
findings = data.get('findings', [])
if allow:
    print(f'[public-surface-guard] PASS risk={risk}')
    sys.exit(0)
print(f'[public-surface-guard] BLOCK risk={risk}', file=sys.stderr)
for item in reasons:
    print(f'  reason: {item}', file=sys.stderr)
for item in findings:
    print(f'  finding: {item}', file=sys.stderr)
sys.exit(1)
PY
