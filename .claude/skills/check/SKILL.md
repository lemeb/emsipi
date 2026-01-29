---
name: check
description:
  Run linting and type-checking quality gates, fixing any errors found. Use
  after writing code, before committing.
---

# Linting and Type-Checking

Load `dev/checking.md` for detailed guidance on fixing errors.

## Procedure

1. Run `make check-fix` (auto-fixes formatting and simple issues)
2. Run `make check` - must pass
3. Run `make check-strict-all` - must pass
4. If errors occur, fix them using guidance from `dev/checking.md`
5. Repeat until both check commands pass

## Exit Conditions

- **Success**: Both `make check` and `make check-strict-all` pass
- **Failure**: Report remaining errors clearly
