#!/bin/bash
# go-on-loop.sh — Autonomous loop wrapper for /go-on
#
# Usage:
#   ./dev/go-on-loop.sh ISSUE-123              # Run until blocked/complete
#   ./dev/go-on-loop.sh ISSUE-123 50           # Max 50 iterations
#   ./dev/go-on-loop.sh ISSUE-123 50 900       # Wait 15min (900s) after PR
#
# The loop continues on <STEP_COMPLETE> and stops on other signals.
# After submitting a PR (<AWAITING_REVIEW>), it waits for CI/review before
# checking for feedback.
#
# Exit codes:
#   0 - Feature complete or awaiting human action
#   1 - Blocked (needs intervention)
#   2 - Max iterations reached
#
# Future enhancement: "work queue" mode where the loop picks the next
# unblocked issue from a list when the current one is blocked.

set -euo pipefail

ISSUE="${1:-}"
MAX_ITERATIONS="${2:-50}"
POST_PR_WAIT="${3:-900}"  # Default: wait 15 minutes after PR for CI/review
MAX_BLOCKED="${4:-3}"     # Stop after this many BLOCKED signals
AUTO_APPROVE="${5:-}"     # Set to "true" to skip approval gates
LOG_FILE=".go-on-loop-$(date +%Y%m%d-%H%M%S).log"
blocked_count=0

if [ -z "$ISSUE" ]; then
  echo "Usage: $0 <issue-id> [max-iterations] [post-pr-wait-seconds] [max-blocked] [auto-approve]"
  echo ""
  echo "Examples:"
  echo "  $0 SUN-199                    # Run with defaults (stops at approval)"
  echo "  $0 SUN-199 30                 # Max 30 iterations"
  echo "  $0 SUN-199 50 1800            # Wait 30min after PR submission"
  echo "  $0 SUN-199 50 0               # Don't wait after PR (for testing)"
  echo "  $0 SUN-199 50 900 3 true      # Full autonomy (skip approvals)"
  exit 1
fi

# Build the flags
GO_ON_FLAGS="--headless"
if [ "$AUTO_APPROVE" = "true" ]; then
  GO_ON_FLAGS="$GO_ON_FLAGS --auto-approve"
fi

echo "Starting /go-on loop for $ISSUE"
echo "  Max iterations: $MAX_ITERATIONS"
echo "  Post-PR wait: ${POST_PR_WAIT}s"
echo "  Max blocked: $MAX_BLOCKED"
echo "  Auto-approve: ${AUTO_APPROVE:-false}"
echo "  Log file: $LOG_FILE"
echo ""

for i in $(seq 1 "$MAX_ITERATIONS"); do
  echo "=== Iteration $i at $(date) ===" | tee -a "$LOG_FILE"

  # Run /go-on and capture output
  OUTPUT=$(claude -p "/go-on $GO_ON_FLAGS $ISSUE" 2>&1) || true
  echo "$OUTPUT" | tee -a "$LOG_FILE"
  echo "" | tee -a "$LOG_FILE"

  # Feature complete
  if echo "$OUTPUT" | grep -q "<FEATURE_COMPLETE>"; then
    echo "Feature complete at iteration $i"
    exit 0
  fi

  # Waiting for human approval (plan, etc.)
  if echo "$OUTPUT" | grep -q "<AWAITING_APPROVAL>"; then
    echo "Paused: awaiting approval"
    echo "Re-run this script after approving to continue"
    exit 0
  fi

  # Waiting for human input
  if echo "$OUTPUT" | grep -q "<AWAITING_INPUT"; then
    echo "Paused: awaiting input"
    echo "Provide the requested input, then re-run"
    exit 0
  fi

  # PR submitted, waiting for CI/review
  if echo "$OUTPUT" | grep -q "<AWAITING_REVIEW>"; then
    if [ "$POST_PR_WAIT" -gt 0 ]; then
      echo "PR submitted. Waiting ${POST_PR_WAIT}s for CI and initial review..."
      sleep "$POST_PR_WAIT"
      echo "Resuming to check for feedback..."
      # Continue the loop to check for feedback
    else
      echo "PR submitted, awaiting review"
      echo "Re-run this script after review to address feedback"
      exit 0
    fi
  fi

  # Blocked
  if echo "$OUTPUT" | grep -q "<BLOCKED"; then
    blocked_count=$((blocked_count + 1))
    echo "Blocked ($blocked_count/$MAX_BLOCKED) — checking if we should stop"

    if [ "$blocked_count" -ge "$MAX_BLOCKED" ]; then
      echo "Reached max blocked count ($MAX_BLOCKED). Stopping."
      echo "Check the log for details: $LOG_FILE"
      exit 1
    fi

    echo "Retrying... (sometimes a fresh invocation helps)"
    sleep 5
    continue
  fi

  # Reset blocked count on successful progress
  blocked_count=0

  # <STEP_COMPLETE> or unrecognized: continue
  echo "Step complete, continuing..."
  sleep 2
done

echo "Reached max iterations ($MAX_ITERATIONS)"
exit 2
