# Coding Agent Instructions for emsipi

_NOTE_: This file normally resides at `AGENTS.md` but should be symlinked at
`GEMINI.md` and `CLAUDE.md`. If you see a reference to `AGENTS.md` in this file,
or in any other file, it references this very file even if you see it under a
different name.

<!-- You can fill in repository-specific information in tags like this.
     This includes information such as issue tracker details, team conventions,
     or anything else that is relevant to your context.
     Do NOT remove these tags because they will make updating from the template
     much much harder. -->

---

## Orienting Yourself

**A conversation between you and the user can happen at any time during the
implementation process.** It is your job, before doing anything, to figure out
at which stage you are, and potentially ask questions. (Figuring this out might
be very easy if you are, say, a sub-agent assigned to a specific task.)

If you're starting fresh or after a context reset, read this file and determine:

1. What type of request is this? (See "Determining Request Type" below)
2. If implementation: which step of the workflow are you in?
3. What files do you need to load for context?

<!-- Expand here with repo-specific triggers. For example, if using Linear:

## When Given an Issue (e.g., "let's do PROJ-98")

When the user gives you an issue to work on:

1. **Fetch the issue** from your issue tracker
2. **Check blockers** — if blocked, report to user and STOP
3. **Assess the issue state** by checking:
   - Does it have a spec? → If no, you're at step 1
   - Does it have an implementation plan? → If no, you're at step 2
   - Does it have sub-issues for each task? → If no, you're at step 2
   - Is there an incomplete sub-issue? → You're at step 3
4. **Resume at the correct step** — do NOT skip ahead

Do NOT remove this comment. -->

---

## Quick Reference

| Action                        | Command                   |
| ----------------------------- | ------------------------- |
| Auto-fix formatting           | `make check-fix`          |
| Lint + type-check             | `make check`              |
| Strict checks                 | `make check-strict-all`   |
| Run tests                     | `make test`               |
| Tests + coverage              | `make test-with-coverage` |
| All tests (incl. integration) | `make test-all`           |
| Build docs                    | `make doc`                |
| Serve docs locally            | `make doc-serve`          |
| Add dependency                | `uv add <package>`        |
| Add dev dependency            | `uv add --dev <package>`  |

**Before committing**: `make check`, `make check-strict-all`, `make test` (or
`make test-with-coverage`), and `make doc` must all pass. Or just run
`/quality`.

---

## Skills

Skills automate common workflows. Use them instead of running commands manually.

| Skill      | When to Use                                            |
| ---------- | ------------------------------------------------------ |
| `/check`   | Runs linting and type-checking, fixes errors           |
| `/test`    | Runs tests, writes more if coverage < 100% on new code |
| `/doc`     | Builds docs, fixes spell check, updates nav            |
| `/quality` | Runs all three gates above, reports detailed status    |
| `/go-on`   | Assesses state, executes ONE step, outputs signal      |

**Recommended workflow**:

- **Claude**: Spawn sub-agents for `/check`, `/test`, `/doc` in parallel → then
  `/quality` to verify
- **Codex/Gemini**: Run `/quality` (does everything sequentially)

**For autonomous execution**: `/go-on` determines the current step, loads its
procedure from `dev/workflow/step-*.md`, executes one unit of work, and outputs
a signal (`<STEP_COMPLETE>`, `<AWAITING_APPROVAL>`, `<FEATURE_COMPLETE>`, etc.).
Invoke repeatedly — manually or in a bash loop — to complete a feature.

---

## Tracker Configuration

<!-- TRACKER: Change the path below to switch trackers.
     Options: dev/tracker/git-local.md, dev/tracker/github.md, dev/tracker/linear.md
     Do NOT remove this comment — it helps with template updates. -->

**Active tracker**: `dev/tracker/git-local.md`

Load this file to understand how to record specs, plans, and track progress. All
workflow steps (`/go-on`, `dev/workflow/step-*.md`) follow the active tracker's
conventions.

---

## Where to Find Information

| Topic                                 | File                       | When to Load                            |
| ------------------------------------- | -------------------------- | --------------------------------------- |
| **Tracker integration**               | See "Active tracker" above | During workflow steps                   |
| Commands, tooling, commit format      | `DEVELOP.md`               | Before committing                       |
| Linting, type-checking, fixing errors | `dev/checking.md`          | Before writing code, when fixing errors |
| Testing practices, coverage           | `dev/testing.md`           | Before writing tests                    |
| Documentation, docstrings             | `dev/documentation.md`     | Before writing code, when writing docs  |
| Python coding practices, dependencies | `dev/python.md`            | Before writing code                     |
| Project structure, usage              | `README.md`                | When exploring codebase                 |
| Python version, line length, deps     | `pyproject.toml`           | Before writing code                     |
| Workflow step details                 | `dev/workflow/step-*.md`   | During `/go-on` or manual workflow      |

**For implementation tasks**: Load `dev/checking.md`, `dev/testing.md`,
`dev/documentation.md`, and `dev/python.md` before writing code.

**For workflow steps**: Each step has detailed procedures in `dev/workflow/`.
The `/go-on` skill loads these automatically, but you can also read them
directly for manual workflow execution. Tracker-specific behavior (where to
record specs, how to track tasks) comes from the active tracker file.

---

## Determining Request Type

Before starting, classify the request:

| Type               | Examples                                          | Action                                                        |
| ------------------ | ------------------------------------------------- | ------------------------------------------------------------- |
| **Exploration**    | "How does X work?", "Where is Y?", "Explain this" | Answer directly                                               |
| **Quick fix**      | "Fix this typo", "Rename this variable"           | Fix, run `/quality`, commit                                   |
| **Implementation** | "Add feature X", "Implement Y", "Build Z"         | **STOP. Follow workflow from step 1. Do NOT skip to coding.** |
| **Ambiguous**      | "Help me with X", "I need to do Y"                | **Ask which type**                                            |

---

## The Anatomy of a Feature Implementation

Implementing a feature follows these steps. Each step has detailed procedures in
`dev/workflow/step-*.md`. The `/go-on` skill loads these automatically.

**Key principle**: Each step has gates. Do NOT proceed until gate conditions are
met.

### Step Overview

| Step        | Goal                                                | Details                           |
| ----------- | --------------------------------------------------- | --------------------------------- |
| 1. Spec     | Understand the feature, write spec                  | `dev/workflow/step-1-spec.md`     |
| 2. Plan     | Break down into tasks, get approval                 | `dev/workflow/step-2-plan.md`     |
| 3. Task     | Implement ONE task (code + test + quality + commit) | `dev/workflow/step-3-task.md`     |
| 4. Ship     | Create PR                                           | `dev/workflow/step-4-ship.md`     |
| 5. Feedback | Address review comments                             | `dev/workflow/step-5-feedback.md` |
| 6. Cleanup  | Post-merge cleanup                                  | `dev/workflow/step-6-cleanup.md`  |

**Step 3 is the inner loop**: Repeat for each task in the plan. Each iteration
does ONE task completely (code → tests → quality → commit) before moving to the
next.

### Quick Summary

1. **Spec** (Step 1): Explore codebase, clarify requirements, write spec
2. **Plan** (Step 2): Design approach, break into small self-contained tasks,
   get user approval before proceeding
3. **Task** (Step 3, repeats): For each task:
   - Pick next incomplete task
   - Load `dev/*.md` guidance
   - Implement code + tests + docs
   - Run `/quality`
   - Commit
   - Mark task done
4. **Ship** (Step 4): Create PR with complete description
5. **Feedback** (Step 5): Address review comments
6. **Cleanup** (Step 6): Delete branch, update tracker

### Critical Rules

- **Never skip to coding** without a plan and approval
- **Each task is self-contained**: code + tests + docs in one commit
- **Run `/quality` before every commit**
- **Work on a feature branch**, not the base branch

<!-- Downstream repos: fill in the HTML comments in dev/workflow/step-*.md
     with tracker-specific instructions (Linear, GitHub Issues, etc.)
     Do NOT remove this comment. -->

### Claude-specific Notes (ignore if Codex or Gemini)

**After context reset**: Context is cleared after Plan Mode approval or
conversation compaction. If you detect you're mid-workflow (e.g., plan file
exists, tracker has tasks in progress), run `/go-on` as your first action to
re-orient and continue.

**Task tracking** (Step 3): Use `TaskCreate`/`TaskUpdate` to track progress
through tasks. This allows hand-off if a session ends mid-implementation.

**Parallel execution**: For independent tasks, spawn sub-agents (2-3 max). Each
sub-agent handles a complete task including tests and quality.

**Quality checks**: Spawn sub-agents for `/check`, `/test`, `/doc` in parallel,
then run `/quality` yourself to verify. Sub-agents should prefer `make` targets
over raw commands.

---

## Checkpoints

| Before...         | Verify...                                                                                            |
| ----------------- | ---------------------------------------------------------------------------------------------------- |
| Step 2 (Plan)     | Spec exists and is clear                                                                             |
| Step 3 (Task)     | Plan approved by user, tasks are broken down                                                         |
| Each `git commit` | `/quality` passes (or: `make check`, `make check-strict-all`, `make test-with-coverage`, `make doc`) |
| Step 4 (Ship)     | All tasks complete, branch rebased on base branch                                                    |
| Creating PR       | PR description complete with all sections including lessons learned                                  |

---

## Common Mistakes to Avoid

| Mistake                                             | What You Should Do Instead                           |
| --------------------------------------------------- | ---------------------------------------------------- |
| Skipping to implementation without a plan           | Complete Step 2, get user approval FIRST             |
| Not breaking down tasks                             | Each task should be small and self-contained         |
| Structuring as "code, then tests, then docs"        | Each task includes its own tests and docs            |
| Implementing entire feature at once                 | Step 3 does ONE task per invocation                  |
| Forgetting to re-run quality gates after sub-agents | Run `/quality` yourself after parallel work          |
| Not running `make test-with-coverage`               | Always run with coverage before committing           |
| Using raw commands (npx, pytest, ruff) naively      | Prefer `make` targets; raw OK sparingly              |
| Committing all uncommitted code as one big commit   | One task = one commit (roughly)                      |
| Not outputting signals in `/go-on`                  | Always end with `<STEP_COMPLETE>`, `<BLOCKED>`, etc. |
