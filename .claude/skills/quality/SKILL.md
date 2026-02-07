---
name: quality
description:
  Run all quality gates and report detailed status. Use as final verification
  after parallel sub-agents, or as all-in-one check.
---

# All Quality Gates

## When to Use

This skill serves TWO purposes:

1. **All-in-one check** (Codex, Gemini, or simple tasks): Run all quality gates
   sequentially in a single invocation.

2. **Final verification** (Claude with parallel agents): After spawning
   `/check`, `/test`, `/doc` in parallel, run `/quality` to verify nothing was
   missed due to concurrent edits.

**Either approach works.** Don't do both — that's redundant. For Claude on
complex tasks: spawn parallel sub-agents → then `/quality` as final check. For
simpler tasks or other agents: just run `/quality` directly.

## Procedure

1. Run all quality gate commands sequentially:

   ```bash
   make check-fix
   make check
   make check-strict-all
   make test-with-coverage
   make doc
   ```

2. If any fail, fix the issues and re-run from step 1

3. Report detailed status summary:

   ```text
   ## Quality Gates Summary

   ### Linting & Type-Checking
   - `make check`: PASS/FAIL
   - `make check-strict-all`: PASS/FAIL
   - Errors fixed: <count> (list briefly if any)
   - Remaining warnings: <count or "none">

   ### Tests
   - `make test-with-coverage`: PASS/FAIL
   - Tests: <passed>/<total>
   - Coverage (overall): <X>%
   - Coverage (new code): <X>% [list uncovered files/lines if < 100%]
   - Integration tests (`make test-all`): PASS/FAIL/SKIPPED

   ### Documentation
   - `make doc`: PASS/FAIL
   - New terms added to project-words.txt: <list or "none">
   - New modules documented: <list or "none">

   ### Overall: PASS/FAIL

   ### Lessons Learned
   <Patterns discovered while fixing issues that should be documented>
   <If none, write "None">
   ```

## Lessons Learned

**Always include a "Lessons Learned" section**, even if empty. This is critical
when running as a sub-agent — the main agent needs this information for the PR
description.

Examples of lessons learned (things that should go in AGENTS.md or dev/\*.md):

- "Discovered that `mypy` requires explicit type annotations for class
  variables"
- "Tests using `freezegun` must import it before the module under test"
- "The `--strict` flag requires `Optional[]` for all nullable parameters"

If you fixed issues, ask: "Would knowing this earlier have helped?" Note it in
the lessons learned output. The main agent will include it in the PR description
under "Lessons Learned", and the human maintainer will decide whether to update
`AGENTS.md` or `dev/*.md`.

## Exit Conditions

- **Success**: All gates pass
- **Failure**: Report which gates failed with specific errors/uncovered lines
