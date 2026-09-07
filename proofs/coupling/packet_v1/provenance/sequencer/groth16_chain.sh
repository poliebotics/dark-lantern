#!/usr/bin/env bash
# BOSUN-worker Groth16 chain: continue the frozen coupling-proof stage overnight.
# Success-only chaining. The core stage's success sentinel is
# results/core/proof_sha256.txt — run_core_attempt2.sh writes it only after
# every frozen check (proof non-empty, typed root, exact score, self-verify,
# tamper rejection) has passed. A stage that ends WITHOUT its sentinel is
# logged once and never retried (Sol review 2026-08-23 22:40: capture a
# core/backtrace and reduce RAYON_NUM_THREADS before another attempt).
# Idempotent, marker-guarded, cron-driven. Markers live on durable NFS.
set -u
: "${XDG_RUNTIME_DIR:?set XDG_RUNTIME_DIR}"
: "${DBUS_SESSION_BUS_ADDRESS:?set DBUS_SESSION_BUS_ADDRESS}"

STAGE=<box path redacted>
RUNNER=<box path redacted>
M=[machine path redacted]
CORE_OK=$STAGE/results/core/proof_sha256.txt
G16_OK=$STAGE/results/groth16/proof_sha256.txt

exec 8>"$M/groth16_chain.lock"
flock -n 8 || exit 0
log() { echo "$(date -u +%FT%TZ) $*" >> "$M/groth16_chain.log"; }

# --- stage 1: wait on the core STARK ---
if [ ! -s "$CORE_OK" ]; then
  systemctl --user is-active --quiet zeebeam-r32-core-a2-20260823 && exit 0
  pgrep -f 'run_core_attempt2.sh core' >/dev/null && exit 0
  if [ ! -f "$M/core_a2_failed" ]; then
    touch "$M/core_a2_failed"
    log "core attempt 2 ended without its success sentinel; chain halted, no retry"
    log "core attempt 2 failed; manual diagnosis required"
  fi
  exit 0
fi

# --- stage 2: core passed -> launch Groth16 exactly once (memory-gated) ---
if [ ! -f "$M/groth16_launched" ]; then
  # bosun-desk 02:2x option 3: the frozen 1200G wrap cap must never squeeze the
  # uncapped trainer. Refuse to fire below 1400 GiB available; retry next tick.
  MIN_AVAIL_KIB=1468006400
  AVAIL_KIB=$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)
  if [ "${AVAIL_KIB:-0}" -lt "$MIN_AVAIL_KIB" ]; then
    log "groth16 deferred: MemAvailable ${AVAIL_KIB:-unknown} KiB < $MIN_AVAIL_KIB KiB"
    exit 0
  fi
  touch "$M/groth16_launched"
  CORESHA=$(cut -d' ' -f1 "$CORE_OK")
  log "core sentinel present (proof sha256 $CORESHA); launching groth16 stage"
  log "core passed; launching Groth16"
  setsid nohup "$RUNNER" groth16 >> "$M/groth16_chain_runner.log" 2>&1 &
  exit 0
fi

# --- stage 3: watch Groth16 ---
if [ ! -s "$G16_OK" ]; then
  systemctl --user is-active --quiet zeebeam-r32-groth16-a2-20260823 && exit 0
  pgrep -f 'run_core_attempt2.sh groth16' >/dev/null && exit 0
  if [ ! -f "$M/groth16_a2_failed" ]; then
    touch "$M/groth16_a2_failed"
    log "groth16 stage ended without its success sentinel; chain halted, no retry"
    log "Groth16 failed; manual diagnosis required"
  fi
  exit 0
fi

# --- stage 4: both proofs passed -> freeze the run manifest exactly once ---
if [ ! -e "$STAGE/RUN_SHA256SUMS" ] && [ ! -f "$M/freeze_done" ]; then
  if "$RUNNER" freeze >> "$M/groth16_chain_runner.log" 2>&1; then
    touch "$M/freeze_done"
    RSHA=$(sha256sum "$STAGE/RUN_SHA256SUMS" | cut -d' ' -f1)
    log "freeze complete; RUN_SHA256SUMS sha256 $RSHA"
    log "Groth16 passed; freeze complete"
  else
    log "freeze FAILED; see groth16_chain_runner.log"
  fi
fi
