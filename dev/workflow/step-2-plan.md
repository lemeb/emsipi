# Step 2: Planning the Implementation

**Goal**: Break down the feature into small, self-contained tasks and get
approval before coding.

## Iron Laws

1. **NO coding until plan is approved** — Present the plan, wait for explicit
   approval. Don't start "just the setup" or "obvious parts."

2. **Each task must be self-contained** — Includes code + tests + docs for that
   piece. Not "implement features" then "write tests" then "update docs."

3. **Tasks form a DAG, not a list** — Note which tasks block which others.
   Parallel work is possible when dependencies allow.

## Prerequisites

- [ ] Spec exists and is clear (Step 1 complete)
- [ ] You understand the acceptance criteria

If prerequisites not met, go back to Step 1.

## Procedure

0. **[Claude only] Enter Plan Mode**: Use the `EnterPlanMode` tool NOW, before
   doing anything else. Do not explore, do not design — enter plan mode first.
   Skip this step if using Codex or Gemini.

1. **Design the approach**:
   - Identify architectural patterns to use
   - Consider dependencies and integration points
   - Note potential challenges or risks

2. **Break down into tasks**:

   Each task should be:
   - **Self-contained**: Includes code + tests + docs for that piece
   - **Small**: Completable in one agent session (~2 human hours max)
   - **Atomic**: Can be committed independently

   Tasks form a **DAG** (directed acyclic graph) — dependencies can be multiple,
   not just linear. Note which tasks block which others.

   Good task example: "Add `/users` endpoint with validation and tests" Bad task
   example: "Implement all endpoints" or "Write tests for feature"

   ### Subtask vs Issue Granularity

   | Level       | Purpose              | Size                       | Who reviews       |
   | ----------- | -------------------- | -------------------------- | ----------------- |
   | **Issue**   | Unit of human review | One PR, one code review    | Human reviewer    |
   | **Subtask** | Unit of agent work   | One focused coding session | Agent self-checks |

   **Issues** are about human cognitive load — a reviewer should be able to
   understand and review the entire change in one sitting.

   **Subtasks** are about context management — an agent should be able to hold
   the entire subtask in context and complete it without losing track.

   An issue typically contains 3-8 subtasks. If you have more, consider
   splitting into multiple issues.

3. **Write the implementation plan**:
   - List tasks with brief descriptions
   - Note dependencies (what blocks what)
   - Note which files/modules each task touches
   - Include setup tasks (dependencies, config) as separate tasks
   - Reference relevant code locations from your exploration

4. **Present the plan to the user** and wait for approval

5. **After approval**, record tasks per the tracker file in `dev/tracker/`

## Task Naming Convention

If tasks are tracked externally (e.g., as sub-issues), use a consistent naming
pattern: `ISSUE-ID(N): Brief description`

Example for issue XYZ-99:

- XYZ-99(1): Add user model and migrations
- XYZ-99(2): Add /users endpoint with validation (depends on 1)
- XYZ-99(3): Add authentication middleware (depends on 1)
- XYZ-99(4): Add protected routes (depends on 2 and 3)

## Claude-specific Notes (ignore if Codex or Gemini)

**Plan Mode behavior**: Context is cleared after the plan is approved. This
means:

1. Read the tracker file (`dev/tracker/*.md`) for specific recording
   instructions

2. The plan MUST include explicit final steps to:
   - Record the implementation plan per the tracker file
   - Create task entries (e.g., sub-issues) per the tracker file
   - These actions happen during plan execution, not after approval

<!-- Expand here with repo-specific information. For example:
     - Where should plans/tasks be tracked?
     - Are there specific formats for implementation plans?
     - Required outputs for the plan (e.g., sub-issues created)?
     Do NOT remove this comment. -->

## Completion Criteria

- [ ] Implementation plan covers all acceptance criteria
- [ ] Tasks are small and self-contained
- [ ] Dependencies between tasks are noted
- [ ] Plan presented to user
- [ ] User explicitly approved the plan
- [ ] Plan and tasks recorded per tracker conventions

## Exit

**Interactive mode**: Wait for user approval, then output `<STEP_COMPLETE>`

**Headless mode**:

- Record the plan per tracker conventions with `Status: DRAFT`
- Output `<AWAITING_APPROVAL>`
- User approves by changing status to `Status: APPROVED`
- Next invocation checks for explicit `Status: APPROVED` — missing status is
  treated as DRAFT

**Headless mode with `--auto-approve`**:

- Record the plan per tracker conventions (no DRAFT status needed)
- Output the plan for visibility, then immediately output `<STEP_COMPLETE>`
- Proceed to Step 3 without waiting

**If plan is rejected**:

1. Ask user what changes are needed (interactive) or note feedback (headless)
2. Update the plan in place — do not delete and recreate
3. Output `<AWAITING_APPROVAL>` again
4. Repeat until approved
