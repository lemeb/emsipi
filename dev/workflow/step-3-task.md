# Step 3: Implementing a Task

**Goal**: Implement ONE task completely (code + tests + quality + commit).

This step repeats for each task in your plan. Each invocation handles exactly
one task.

## Iron Laws

These are non-negotiable constraints. Do NOT rationalize exceptions.

1. **NO code changes without running `/quality` afterward** — Every change gets
   verified before commit. No "I'll run it later" or "this is just a small fix."

2. **NO completion claims without fresh verification evidence** — Before saying
   "done" or "fixed," execute the command that proves it and show the output.

3. **If 3+ attempts to fix the same error fail, STOP** — Output
   `<BLOCKED reason="...">` and reconsider the approach. Don't keep trying
   variations of the same fix.

4. **Each task is self-contained** — Code + tests + docs in one commit. Don't
   structure as "implement everything, then write all tests, then fix docs."

## Prerequisites

- [ ] Implementation plan exists and is approved (Step 2 complete)
- [ ] Tasks are tracked per the active tracker's conventions
- [ ] You are on a feature branch (not main/master/base branch)
- [ ] Previous task (if any) is committed

If not on a feature branch, create one first.

## Procedure

### 3a. Verify feature branch

**BEFORE doing anything else**, verify you are on the correct feature branch:

1. Run `git branch --show-current`
2. If on `main`/`master`/base branch, create and checkout a feature branch
3. Branch name should match the issue (e.g., `feat/PROJ-123-user-auth`)

Do NOT proceed on the base branch.

### 3b. Ensure tasks are recorded in tracker

Verify you are on the feature branch (step 3a), then verify tasks exist in the
tracker. If not (e.g., Plan Mode cleared context):

1. Read the tracker file (`dev/tracker/*.md`) for recording instructions
2. Read the approved plan (local file or issue description)
3. Create task entries per the tracker file (e.g., Linear sub-issues with
   dependencies)
4. **[Claude only]** Create Task entries for ALL tasks using `TaskCreate`. Set
   up the full dependency graph using `addBlockedBy`. This mirrors the tracker
   and provides visibility for the entire implementation.

Only proceed once tasks are recorded in the tracker.

### 3c. Pick the next task

1. **Identify the next incomplete task** from your plan/tracker
2. **Verify it's unblocked** (dependencies completed)
3. **Mark it as in-progress** per tracker conventions
4. **[Claude only]** Mark the Task as `in_progress` with `TaskUpdate`

### 3d. Implement

1. **Load coding guidance** before writing code:
   - `dev/checking.md` — linting & type-checking
   - `dev/testing.md` — testing practices
   - `dev/documentation.md` — docstrings & docs
   - `dev/python.md` — coding style

2. **Write the code** for this task only
   - Follow existing patterns in the codebase
   - Keep changes focused on this task

3. **Write tests** for the code you just wrote
   - Aim for 100% coverage on new code
   - Include edge cases from the spec

4. **Update documentation** if needed
   - Docstrings for new public APIs
   - Update docs/ if user-facing
   - Add terms to `project-words.txt`

### 3e. Quality gate

Run `/quality` (or the manual commands below). ALL must pass before proceeding:

| Gate          | Command                   | Criteria         |
| ------------- | ------------------------- | ---------------- |
| Linting       | `make check`              | Exit code 0      |
| Strict checks | `make check-strict-all`   | Exit code 0      |
| Tests         | `make test-all`           | All tests pass   |
| Coverage      | `make test-with-coverage` | 100% on new code |
| Documentation | `make doc`                | No warnings      |

Additionally: **All acceptance criteria in the spec must have corresponding
tests.**

- **If passing**: Proceed to commit
- **If failing**: Fix issues and re-run until passing
- **If stuck after 3 attempts on the same error**: Output
  `<BLOCKED reason="...">`

### 3f. Commit

1. **Stage the changes** for this task
2. **Write a commit message** following the project's conventions:
   - Check `DEVELOP.md` for commit message format
   - Look at recent commits (`git log -5`) for style reference
3. **Commit** (unless user asked to review first)
4. **Mark task complete** per tracker conventions
5. **[Claude only]** Mark the Task complete with `TaskUpdate`

## Claude-specific Notes (ignore if Codex or Gemini)

**Task tracking**: Use `TaskCreate`/`TaskUpdate` to track progress through tasks
within a session:

- Create tasks with clear subjects and descriptions
- Use `addBlockedBy` to represent the DAG of dependencies from your plan
- Mark tasks `in_progress` when starting, `completed` when done
- This provides visibility and allows hand-off if the session ends

**Parallel execution**: If multiple tasks are independent (no dependencies
between them), you can spawn sub-agents to work on them in parallel:

- Keep it reasonable (2-3 parallel tasks max)
- Each sub-agent handles a complete task including tests and quality
- Tell sub-agents: "Running in headless mode" if applicable

**Quality checks**: To preserve context, spawn sub-agents for `/check`, `/test`,
`/doc` in parallel rather than running make commands directly. After sub-agents
complete, run `/quality` yourself to verify nothing was missed.

<!-- Expand here with repo-specific information. For example:
     - Branch naming conventions?
     - Specific patterns or conventions to follow?
     - How to track progress (e.g., mark sub-issues done as you complete them)?
     Do NOT remove this comment. -->

## Completion Criteria (per task)

- [ ] Code written and follows project patterns
- [ ] Tests written — 100% coverage on new code
- [ ] All acceptance criteria have corresponding tests
- [ ] `/quality` passes (all gates green)
- [ ] Changes committed
- [ ] Task marked complete per tracker conventions

## Exit

After completing ONE task:

- Output: `<STEP_COMPLETE>`
- If more tasks remain: Next invocation continues with next task
- If all tasks done: Next step is Step 4 (Ship)

If blocked (e.g., need clarification, dependency not ready):

- Output: `<BLOCKED reason="...">`
