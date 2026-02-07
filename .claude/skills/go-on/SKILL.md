---
name: go-on
description:
  Assess workflow state, execute ONE step, then exit with a signal. Designed for
  incremental progress — invoke repeatedly (manually or in a loop) to complete a
  feature.
---

# Workflow Continuation

## Arguments

```text
/go-on [--headless] [--auto-approve] [ISSUE-REF]
```

- `--headless`: Running in autonomous loop (no user interaction available)
- `--auto-approve`: Skip approval gates for spec and plan (use with caution)
- `ISSUE-REF`: Issue reference (e.g., `SUN-199`, `#42`, `specs/feature.md`)

**Issue resolution**:

- **Interactive mode**: If no ISSUE-REF, infer from conversation context or git
  branch
- **Headless mode**: ISSUE-REF is **required** — fail fast with
  `<BLOCKED reason="No ISSUE-REF provided in headless mode">` if missing

**Note on `--auto-approve`**: By default, headless mode stops at plan approval
(`<AWAITING_APPROVAL>`). With `--auto-approve`, the agent proceeds without
waiting. Use this only when the issue is well-defined and you trust the agent's
plan. The agent will still output the plan before proceeding.

## Quick Reference

| Signal                          | Meaning                                          |
| ------------------------------- | ------------------------------------------------ |
| `<STEP_COMPLETE>`               | One unit done, invoke again for next             |
| `<AWAITING_APPROVAL>`           | Plan presented, waiting for user (headless only) |
| `<AWAITING_INPUT reason="...">` | Need clarification (headless only)               |
| `<AWAITING_REVIEW>`             | PR submitted, waiting for review                 |
| `<FEATURE_COMPLETE>`            | All done                                         |
| `<BLOCKED reason="...">`        | Cannot proceed                                   |

## Procedure

1. **Load the active tracker file** (specified in AGENTS.md under "Tracker
   Configuration") for how to record specs, plans, and track progress

2. **Assess current state** by checking:
   - Tracker (per active tracker file) for spec and plan status
   - Git: branch, commits, uncommitted changes, PR status
   - Filesystem: implementation progress

3. **Determine current step and load its procedure**:

   | State                               | Step | File to Load                                                                 |
   | ----------------------------------- | ---- | ---------------------------------------------------------------------------- |
   | No spec exists                      | 1    | `dev/workflow/step-1-spec.md`                                                |
   | Spec exists, no plan                | 2    | `dev/workflow/step-2-plan.md`                                                |
   | Plan exists, no `Status:` field     | 2    | `dev/workflow/step-2-plan.md` (treat as DRAFT, output `<AWAITING_APPROVAL>`) |
   | Plan exists with `Status: DRAFT`    | 2    | `dev/workflow/step-2-plan.md` (output `<AWAITING_APPROVAL>`)                 |
   | Plan exists with `Status: APPROVED` | 3    | `dev/workflow/step-3-task.md`                                                |
   | Tasks remain incomplete             | 3    | `dev/workflow/step-3-task.md`                                                |
   | All tasks done, no PR               | 4    | `dev/workflow/step-4-ship.md`                                                |
   | PR open, CI pending                 | 5    | `dev/workflow/step-5-feedback.md` (output `<AWAITING_REVIEW>`)               |
   | PR open, has feedback               | 5    | `dev/workflow/step-5-feedback.md`                                            |
   | PR merged                           | 6    | `dev/workflow/step-6-cleanup.md`                                             |
   | PR closed without merge             | —    | Output `<BLOCKED reason="PR rejected">`                                      |

4. **Execute ONE unit of work** per the step file's procedure
   - Follow the active tracker's conventions for recording state
   - If `--headless`, output `<AWAITING_*>` signals instead of waiting

5. **Output status**:

   ```text
   ## /go-on Status

   Mode: <interactive|headless>
   Step: <N - name>
   State before: <what was found>
   Action taken: <what was done>
   Result: <outcome>

   <SIGNAL>

   Next: <what happens on next invocation>
   ```

## Key Principles

- **Stateless**: Determine state fresh each invocation from external sources
- **Atomic**: Do ONE thing, then exit
- **Idempotent**: Safe if interrupted; next invocation re-assesses
- **Signal-driven**: Always output exactly one signal for loop detection
- **Tracker-aware**: Follow the active tracker's conventions

## State Authority Order

When determining state, trust sources in this order (higher = more
authoritative):

1. **Git** (commits, branches, PR status) — ground truth
2. **Filesystem** (actual code, test results)
3. **Tracker files** (IMPLEMENTATION_PLAN.md, specs/)

If sources conflict, update tracker to match Git/filesystem reality.

## Session Cleanup

At the end of each step, ensure state is persisted to the tracker so the next
session (possibly a different agent) can continue. The tracker IS the session
handoff mechanism.

## Headless Mode

When `--headless` is passed:

- Output `<AWAITING_APPROVAL>` instead of waiting for user response
- Output `<AWAITING_INPUT>` instead of asking questions
- Record state to tracker before exiting (so next invocation can continue)
- When spawning sub-agents, tell them: "Running in headless mode"

## For Autonomous Loops

**Recommended**: Use the Python wrapper with circuit breaker:

```bash
# Install dependencies first: uv sync
python .claude/scripts/go_on_loop.py SUN-199
python .claude/scripts/go_on_loop.py SUN-199 --auto-approve
python .claude/scripts/go_on_loop.py SUN-199 --max-no-progress 5
```

The wrapper tracks loop metadata (iterations, circuit breaker state) and stops
when progress stalls. Workflow state still lives in tracker/git — the wrapper
doesn't duplicate it.

**Alternative**: Simple bash loop (no circuit breaker):

```bash
while :; do
  OUTPUT=$(claude -p "/go-on --headless ISSUE-123" 2>&1)
  echo "$OUTPUT"

  # Stop on any signal except STEP_COMPLETE
  grep -q "<FEATURE_COMPLETE>" <<< "$OUTPUT" && exit 0
  grep -q "<AWAITING_APPROVAL>" <<< "$OUTPUT" && exit 0
  grep -q "<AWAITING_INPUT" <<< "$OUTPUT" && exit 0
  grep -q "<AWAITING_REVIEW>" <<< "$OUTPUT" && exit 0
  grep -q "<BLOCKED" <<< "$OUTPUT" && exit 1

  sleep 2
done
```
