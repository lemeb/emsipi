# Coding Agent Instructions for emsipi

_NOTE_: This file normally resides at `AGENTS.md` but should be symlinked at
`GEMINI.md` and `CLAUDE.md`. If you see a reference to `AGENTS.md` in this file,
it references this very file even if you see it under a different name.

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
| `/go-on`   | Assesses workflow state and executes ONE next step     |

**Recommended workflow**:

- **Claude**: Spawn sub-agents for `/check`, `/test`, `/doc` in parallel → then
  `/quality` to verify
- **Codex/Gemini**: Run `/quality` (does everything sequentially)

For autonomous/loop execution, `/go-on` determines the current workflow step and
makes incremental progress.

---

## Where to Find Information

| Topic                                 | File                   | When to Load                            |
| ------------------------------------- | ---------------------- | --------------------------------------- |
| Commands, tooling, commit format      | `DEVELOP.md`           | Before committing                       |
| Linting, type-checking, fixing errors | `dev/checking.md`      | Before writing code, when fixing errors |
| Testing practices, coverage           | `dev/testing.md`       | Before writing tests                    |
| Documentation, docstrings             | `dev/documentation.md` | Before writing code, when writing docs  |
| Python coding practices, dependencies | `dev/python.md`        | Before writing code                     |
| Project structure, usage              | `README.md`            | When exploring codebase                 |
| Python version, line length, deps     | `pyproject.toml`       | Before writing code                     |

**For implementation tasks**: Load `dev/checking.md`, `dev/testing.md`,
`dev/documentation.md`, and `dev/python.md` before writing code.

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

Implementing a new feature typically involves the following steps. **Each step
has required outputs and gates. Do NOT proceed to the next step until the gate
conditions are met.**

### 1. Fully understanding the feature

This includes _exploring the current state of the codebase_, _asking questions
to the user to clarify any doubts_, and _researching any relevant information_
(whether third-party libraries, roadmaps, old PRs, etc.) to fully grasp the
feature requirements and constraints. The goal of this step is to produce a
spec.

<!-- Expand here with repo-specific information. For example:
     - Where should specs be recorded? (issue tracker, design doc, etc.)
     - Are there specific templates or formats for specs?

     You can add REQUIRED OUTPUT and GATE markers like this:

     **REQUIRED OUTPUT**: Spec written in the issue description.

     **GATE**: Do NOT proceed to step 2 until the spec is recorded.

     Do NOT remove this comment. -->

### 2. Planning the implementation

This involves _deciding on the architecture and design patterns to use_,
_identifying any potential challenges or dependencies_, and _breaking down the
feature into smaller, manageable tasks_. The goal of this step is to produce a
clear implementation plan. Please check that the spec and the implementation
plan are aligned with each other.

In general, a task should be small enough that it can be implemented, tested,
documented, and committed in one go. **Each task should be self-contained: it
includes writing the code, writing tests for that code, updating documentation
if needed, and running quality gates.** Do NOT structure tasks as "implement
features" followed by "write all tests" followed by "run quality gates" — each
task should include its own tests and pass quality gates independently.

It should also be small enough to be done fully within one agent session. A good
rule of thumb is something like 2 human hours. It can be much smaller, however.
In fact, if your feature demands multiple small tasks that are very similar
(e.g. adding multiple API routes), it is a good idea to keep the first task
small, and then use it as a template for the other tasks. Another reason to keep
tasks small is that it makes it easier to review and test; if you run linting
and type-checking commands on thousands of lines of code, it will make the
context window unmanageable.

If you have to write the description of a task, try to keep it relatively
concise but specific enough so that the implementation is clear and the agent
will not spend an unreasonable amount of time exploring the codebase. For
instance, references to relevant files or modules are very helpful. Don't let
your previous exploration go to waste. Do not hesitate to mention blocking tasks
so that we can represent tasks as a DAG. A good title for the first task of,
say, XYZ-999 could be "XYZ-999(1): `<brief task description>`".

If you have to add dependencies for a feature, try to make adding them a
separate task. This will make it easier to review and test.

### Claude-specific note (ignore if Codex or Gemini)

As a general rule, use Plan Mode for this step.

If the implementation plan needs to be written to an external system (e.g. an
issue tracker), and/or tasks need to be created as sub-issues, make this very
explicitly part of the plan. (The reason is that if the user approves the plan,
context might be cleared for a new conversation.)

<!-- Expand here with repo-specific information. For example:
     - Where should plans/tasks be tracked?
     - Are there specific formats for implementation plans?

     You can add REQUIRED OUTPUTS and GATE markers like this:

     **REQUIRED OUTPUTS**:
     - Implementation plan written in the issue description
     - Sub-issues created for each task

     **GATE**: Do NOT proceed to step 3 until:
     - [ ] Implementation plan is presented to the user
     - [ ] User explicitly approves the plan
     - [ ] Sub-issues exist for each task

     Do NOT remove this comment. -->

### 3. Executing the implementation

**PREREQUISITE CHECK**: Before writing any code, verify:

- [ ] There is a clear implementation plan
- [ ] Tasks are broken down (in your issue tracker or in this conversation)
- [ ] You are implementing ONE specific task, not the whole feature at once
- [ ] That task is self-contained (includes its own tests and docs if needed)

This is the actual coding part. Please follow the best practices and coding
standards specified in your context window; and don't hesitate to look at the
existing codebase for reference. **Load `dev/checking.md`, `dev/testing.md`,
`dev/documentation.md`, and `dev/python.md` before writing code.**

As you implement each task, make sure to (1) write unit tests for that task, (2)
update `.gitignore` if needed, (3) update documentation (both inline and
external) as needed. Then run `/quality` before moving to the next task.

Note that the implementation should be made in a feature branch, not directly in
the base branch. Make sure to rebase the feature branch regularly to keep it up
to date with the base branch. (Rebase is the default strategy; but if specified
otherwise, follow the specified strategy.)

<!-- Expand here with repo-specific information. For example:
     - Branch naming conventions?
     - Any specific patterns or conventions to follow?
     - How to track progress (e.g., mark sub-issues done as you complete them)
     Do NOT remove this comment. -->

### Claude-specific notes (ignore if Codex or Gemini)

**Task tracking**: When working on a feature with multiple tasks, use the Tasks
construct (`TaskCreate`, `TaskUpdate`, `TaskList`) to track your progress:

1. **At the start of step 3**: Create a task for each item in your
   implementation plan using `TaskCreate`. Include a clear subject (imperative
   form, e.g., "Add user authentication endpoint") and description with enough
   context for another agent to pick it up if needed.

2. **Before starting work on a task**: Mark it as `in_progress` using
   `TaskUpdate`.

3. **After completing a task**: Mark it as `completed` using `TaskUpdate`. If
   you discover follow-up work during implementation, create new tasks for it.

4. **Set up dependencies**: Use `TaskUpdate` with `addBlockedBy` to represent
   task dependencies from your implementation plan.

This provides visibility into progress and allows seamless hand-off if a session
ends mid-implementation.

**Parallel task execution**: If multiple tasks have no dependencies between them
(e.g., implementing independent endpoints), you can work on them in parallel by
spawning sub-agents for each task. Keep it reasonable—2-3 parallel tasks is
fine, but don't be overly ambitious. Each sub-agent should handle a complete
task including its tests and quality checks.

**Quality checks during implementation**: When you need to run quality checks
(even mid-implementation), spawn sub-agents for `/check`, `/test`, `/doc` in
parallel rather than running make commands directly. This preserves your context
window for the actual implementation work. See step 4 for details.

### 4. Ensuring code quality before committing

There are three quality gates that MUST be passed before committing any code:

1. _Linting and type-checking_. First, run `make check-fix` to auto-fix any
   formatting issues. Then run `make check` to ensure that there are no linting
   or type-checking errors. For stricter checks, run `make check-strict-all`.
   Both `make check` and `make check-strict-all` MUST pass before committing any
   code, because CI/CD will run the same commands and will fail the build if any
   of them fail.
2. _Unit tests_. Run `make test-with-coverage` to run unit tests and see
   coverage. You should aim for 100% unit test coverage for the new code you
   write. If your feature requires internet access or latency (e.g. because it
   is a LLM call), also run `make test-all` to ensure that all integration tests
   pass. `make test` (or `make test-with-coverage`) HAS to pass before
   committing any code.
3. _Documentation_. If you create a new module, you MUST create a corresponding
   file in `docs/api/` AND update the `nav` section in `mkdocs.yml` to include
   it. Also, if you think documentation would be improved by adding things like
   tutorials, guides, etc, please propose them to the user. If you see that one
   of the existing guides or tutorials needs to be updated, please do so
   proactively and properly. Run `make doc` to ensure that the documentation
   builds correctly and that spell check passes. Add any new technical terms to
   `project-words.txt`. Please do NOT use `sort` on `project-words.txt`.
   `make doc` HAS to pass before committing any code.

#### Claude-specific note on quality gates (ignore if Codex or Gemini)

To preserve context window, spawn three sub-agents (using Sonnet 4.5 for cost
control) to run `/check`, `/test`, and `/doc` in parallel. Each sub-agent will
run checks and fix issues. Tell each sub-agent they are running in parallel, so
they shouldn't be alarmed if files change under their feet.

**Sub-agent command guidance**: Sub-agents should prefer `make` targets over raw
commands (e.g., `make test-with-coverage` not `pytest`), because Makefile
targets include project-specific options that raw commands lack. Raw commands
are OK sparingly for targeted checks (e.g., `pytest tests/test_foo.py` to verify
a single file), but sub-agents should be aware they may encounter permission
issues or produce different results than the full make targets.

After the sub-agents complete, run `/quality` yourself to verify nothing was
missed due to concurrent edits.

<!-- Expand here with repo-specific information. For example:
     - Additional quality gates?
     - Specific coverage requirements?
     Do NOT remove this comment. -->

### 5. Committing and creating a PR

In general, we want git commits to be small and self-contained. As a rule of
thumb, there should be a rough 1:1 correspondence between tasks and git commits.
However, sometimes it makes sense to split a task into multiple commits. Use
your best judgment. The important thing is that each commit should be easy to
review and understand on its own. And ideally, the quality gates should pass for
each commit. Check `DEVELOP.md` for more details on how to write commits.

**Unless the user explicitly says you can commit on your own, do not commit
without asking for user review first.**

Once commits are done and pushed, you should create a PR. The PR description
should include the following sections:

- References to any relevant issues, tasks, or discussions, and ideally the spec
  and implementation plan.
- A clear and concise description of the changes made in the PR.
- Instructions on how to test the changes, if applicable.
- Checklist of the quality gates passed (linting, type-checking, unit tests,
  documentation).
- Any additional context or information that reviewers might find useful.
- **Lessons learned**: If you discovered things that should be added to
  `AGENTS.md` or the `dev/*.md` files, note them here so maintainers can
  incorporate them.

<!-- Expand here with repo-specific information. For example:
     - PR template requirements?
     - Issue linking format?
     - Required reviewers?
     Do NOT remove this comment. -->

### 6. Addressing PR feedback

Feedback about the PR can come from different places and should be addressed in
further commits to the same PR.

<!-- Expand here with repo-specific information. For example:
     - How to handle feedback from different sources?
     - Any specific conventions for addressing feedback?
     Do NOT remove this comment. -->

### 7. Cleaning up after the feature is merged

Once the feature is merged, there might be some cleanup tasks to do, such as
removing any temporary code or branches, updating documentation, etc.

<!-- Expand here with repo-specific information. For example:
     - Post-merge cleanup checklist?
     - Any notifications or updates to make?
     Do NOT remove this comment. -->

---

## Checkpoints

| Before...          | Verify...                                                                                            |
| ------------------ | ---------------------------------------------------------------------------------------------------- |
| Step 2 (Planning)  | Spec exists and is clear                                                                             |
| Step 3 (Execution) | Plan approved by user, tasks are broken down                                                         |
| `git commit`       | `/quality` passes (or: `make check`, `make check-strict-all`, `make test-with-coverage`, `make doc`) |
| `git push`         | All quality gates pass, branch rebased on base branch                                                |
| Creating PR        | PR description complete with all sections including lessons learned                                  |

---

## Common Mistakes to Avoid

| Mistake                                             | What You Should Do Instead                    |
| --------------------------------------------------- | --------------------------------------------- |
| Skipping to implementation without a plan           | Complete step 2, get user approval FIRST      |
| Not breaking down tasks                             | Each task should be small and self-contained  |
| Structuring as "code, then tests, then docs"        | Each task includes its own tests and docs     |
| Implementing entire feature at once                 | Implement ONE task at a time                  |
| Forgetting to re-run quality gates after sub-agents | Run all commands yourself after parallel work |
| Not running `make test-with-coverage`               | Always run with coverage before committing    |
| Using raw commands (npx, pytest, ruff) naively      | Prefer `make` targets; raw OK sparingly       |
| Committing all uncommitted code as one big commit   | Split into logical commits per task, or ask   |
