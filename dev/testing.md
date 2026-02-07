# Testing

> **TL;DR**: Run `make test`. Aim for 100% coverage on new code.

---

## Commands

| Command                   | Purpose                                          |
| ------------------------- | ------------------------------------------------ |
| `make test`               | Run unit tests. **Must pass before committing.** |
| `make test-all`           | Run all tests including integration tests.       |
| `make test-with-coverage` | Unit tests + coverage report.                    |
| `make test-all-versions`  | Tests across all supported Python versions.      |

## Procedure

1. Run `make test`
2. If failures, fix and re-run
3. Check coverage with `make test-with-coverage`
4. For new code, aim for 100% coverage
5. If your feature requires internet access or latency (e.g., because it is an
   LLM call), also run `make test-all` to ensure that all integration tests pass

## Writing Tests

- Place tests in `tests/` mirroring the `src/` structure
- Use `pytest` fixtures for setup/teardown
- For mocking, prefer `unittest.mock` or `pytest-mock`

### Test Files and Type Checking

Test files often need file-level pyright configuration when they use mocks and
JSON responses that inherently involve `Any` types. Add at the top of the file:

```python
# pyright: reportAny=false, reportExplicitAny=false
```

Add `reportPrivateUsage=false` if tests need to access private module state. Add
`reportUnknownArgumentType=false` for JSON parsing.

See `dev/checking.md` for more details on handling type-checking in tests.

---

## Lessons Learned

<!-- This section should be updated over time with quirks discovered during
     development. After fixing test issues, consider whether the fix reveals
     something that should be documented here for future reference. -->
