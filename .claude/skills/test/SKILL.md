---
name: test
description:
  Run tests and achieve 100% coverage on new code, writing additional tests if
  needed. Use after writing code, before committing.
---

# Testing

Load `dev/testing.md` for detailed guidance on writing and fixing tests.

## Procedure

1. Run `make test-with-coverage`

2. If failures occur, fix them and re-run

3. Check coverage for new code (files changed in git):
   - Use `git diff --name-only` to identify new/modified files
   - Review coverage report for those files
   - If < 100% coverage on new code, write additional tests to cover uncovered
     lines
   - Re-run `make test-with-coverage`

4. Repeat until tests pass AND new code has 100% coverage

5. If feature requires internet/latency (e.g., LLM calls), also run
   `make test-all`

## Exit Conditions

- **Success**: Tests pass AND 100% coverage on new code
- **Partial**: Tests pass but < 100% coverage - report uncovered lines for
  review
- **Failure**: Report remaining failures
