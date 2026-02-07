# Checking (Linting & Type-Checking)

> **TL;DR**: Run `make check-fix` first (auto-fixes many issues), then
> `make check` and `make check-strict-all`. Both must pass before committing.

This file should be loaded both when **writing code** (to avoid triggering
errors) and when **fixing errors** (to know how to resolve them).

---

## Commands

| Command                 | Purpose                                                                  |
| ----------------------- | ------------------------------------------------------------------------ |
| `make check-fix`        | Auto-fix formatting, import sorting, simple lint issues. Run this first. |
| `make check`            | Linting + type-checking in parallel. **Must pass.**                      |
| `make check-strict-all` | Strict mode: ruff preview rules, basedpyright. **Must pass.**            |

## Procedure

1. Run `make check-fix` (auto-fixes many issues)
2. Run `make check`
3. Run `make check-strict-all`
4. If either check command fails, fix the issues and go back to step 1
5. Only proceed when both `make check` and `make check-strict-all` pass

---

## Writing Code to Avoid Errors

These practices prevent common linting/type-checking errors.

### Type Hints

- Check `pyproject.toml` for the minimum Python version. Write constructs
  accordingly (e.g., no `Union` if Python 3.10+ is supported; use `|` instead).
- Any time you define an empty list, try to type-hint it (e.g.,
  `my_list: list[str] = []`).
- If you use `cast(...)`, make sure that the name of the new type is put within
  double quotes (e.g., `cast("MyType", obj)`).
- Put `@final` whenever needed. Helps for type-checking.
- Put `@override` whenever needed (and it's generally more often than you
  think). Helps for type-checking.

### Methods and Parameters

- Be mindful of class methods that don't use the `self` parameter. If you don't
  use it, you should make it static.
- **Unused parameters**: Use `_paramname` prefix (e.g., `_request`) for
  intentionally unused parameters. This satisfies both ruff's `ARG001` and
  pyright's `reportUnusedParameter` without needing ignore comments.
- **Unused call results**: For `reportUnusedCallResult` errors, assign the
  result to `_`, e.g., `_ = await db.execute(...)`. **NOTE**: If you import i18n
  in the file, `_` might be shadowed. In this case, you can use something like
  `_unused` or `__` instead.

### Exceptions

The right way to pass a message to an exception is to define a `msg` variable,
and then pass it to the exception.

### Line Length

Check `pyproject.toml` for the max line length. It's probably 80. Yes, the
formatter will sometimes just reformat the code, but some lines (e.g.,
docstrings) will need to be modified accordingly.

### Output

Try not to use `print` statements. Use your best judgment instead: if it's for
logging, use `logging`. If it's for user-facing interaction, use the `rich`
library (such as `print` or `Console`).

### Scratch Directory

Don't bother modifying `scratch/tmp-file-ignore-them/pyproject.toml` - it's not
tracked by git and exists only for local experimentation. The linter might
complain about it but you can ignore those complaints.

---

## Fixing Errors

### Ruff Preview Rules

One quirk of `make check-strict-all` is that it will run `ruff`'s preview rules.
If you want to ignore such a rule, you cannot do it in the file; it will be
removed by `ruff format`. Instead, you should update the `ruff-strict.toml` file
where these exceptions are documented. YOU SHOULD DOCUMENT THE RULE PER FILE,
NOT FOR THE ENTIRE CODEBASE. And every exception should be documented with a
comment explaining why the rule is not applied in that file.

If you're wondering if a rule is in preview: if it appears during
`make check-strict-all`, but not during `make check`, then it is a preview rule.
This means that you need to add it to `ruff-strict.toml` if you want to ignore
it.

### Ignore Comments

You can use `# type: ignore[error-code]` (`mypy`),
`# pyright: ignore[ErrorCode]` (`pyright`), and `# noqa: <ERROR_CODE>` (`ruff`).
If multiple go on the same line, they should go with `mypy` first. Use them only
as last resort, when no better solution is available. (An example where this is
warranted is if `Any` is really the only type that works, or if you need to use
a third-party library that is not typed.)

**Policy for ignore comments:**

- **Line-level ignores**: Use sparingly. Try to find a better solution first
  (see alternatives below). If truly necessary, add a brief comment explaining
  why.
- **File-level ignores**: Avoid in general. When used, you MUST document why.
  Acceptable cases:
  - Test files that inherently need to use `Any` types (e.g., because of
    mocking, JSON parsing, etc.)
  - Test files with regards to private module state access or docstring-related
    issues.
  - Errors or warnings that are really pervasive throughout the file, and
    addressing them individually would be too cumbersome.

### Alternatives to Ignore Comments

| Error Type         | Try This Instead                                  |
| ------------------ | ------------------------------------------------- |
| Unused parameter   | Prefix with `_` (e.g., `_request`)                |
| Unused call result | Assign to `_` (e.g., `_ = await db.execute(...)`) |
| Too many arguments | See below                                         |

**Too many arguments**: If you get an error saying that there are too many
arguments in a method signature, you should consider the following options, in
order of preference:

1. Refactor the code to reduce the number of parameters (e.g., group related
   parameters into a dataclass or dictionary). But if this is not feasible, or
   clearly idiotic, or decreases code readability, then...
2. Use a noqa comment.
3. Really avoid using solutions relying on `kwargs` or `args` unless absolutely
   necessary. We like type-checking!

### Unknown/Any Type Errors

In general, if we're dealing with operations that inherently deal with `Any` or
`Unknown` (e.g., because you're parsing JSON, because you're dealing with a
third-party library that is not typed, etc.), you can safely put ignore comments
for: `reportUnknownArgumentType`, `reportUnknownMemberType`,
`reportUnknownVariableType`, `reportUnknownParameterType`, `reportUnknownType`,
`reportAny`, `reportExplicitAny`, etc. (`pyright`), and `ANN401` (`ruff`).

**However**: If the unknown/any type is NOT from JSON parsing, mocks, or untyped
libraries, make a best effort to actually type the variables and objects
properly before resorting to ignore comments.

In some cases, you can put `object` as the type, but this is not recommended. If
you do so, please document why you did it.

### Pyright-Specific Issues

- **Pyright ignore placement**: The `# pyright: ignore[rule]` comment MUST be on
  the exact line with the error. Putting it on an adjacent line won't work.
- **Comment wording pitfall**: Any comment starting with `# pyright:` is parsed
  as a directive. If explaining why a pyright ignore is needed, start with
  `# Pyright ignore needed...` (capital P) or rephrase to avoid the prefix.

### Test Files and Pyright Strict Mode

Test files often need file-level pyright configuration when they use mocks and
JSON responses that inherently involve `Any` types. Add at the top of the file:

```python
# pyright: reportAny=false, reportExplicitAny=false
```

Add `reportPrivateUsage=false` if tests need to access private module state, and
`reportUnknownArgumentType=false` for JSON parsing.

---

## Lessons Learned

<!-- This section should be updated over time with quirks discovered during
     development. After fixing linting errors, consider whether the fix reveals
     something that should be documented here for future reference. -->

- **Prettier before markdownlint**: Run `prettier-md` (format/fix) before
  `markdownlint` — it fixes table alignment that otherwise triggers false
  positives. `make doc` does this automatically.
- **Pyright vs Ruff string concatenation**: Pyright's
  `reportImplicitStringConcatenation` forbids implicit concatenation; Ruff's
  ISC003 forbids explicit `+`. Use implicit concatenation with
  `# pyright: ignore[reportImplicitStringConcatenation]` inline.
- **DOC502 and delegated exceptions**: This strict ruff preview rule flags
  `Raises` sections when the exception is raised by a called service, not
  explicitly in the function body. For thin route handlers that delegate to
  services, omit `Raises` from docstrings.
- **Pydantic schemas in tests**: Avoid `**dict` unpacking from
  `dict[str, object]` — mypy flags `arg-type` mismatches. Use explicit keyword
  arguments instead.
- **TD002/TD003 TODO format**: Ruff's flake8-todos rules require a specific
  format. Create an issue first, then reference it:

  ```python
  # TODO(author): description of what needs to be done
  # XXX-123
  ```

  Existing non-compliant TODOs pass CI because pre-commit only checks changed
  files.

- **Mypy strictness with StrEnum**: Pydantic coerces strings to `StrEnum` at
  runtime, but mypy flags `Model(field="value")` as a type error. Use the enum
  value directly (e.g., `MyEnum.VALUE`) or `model_validate({"field": "..."})`
  for tests that intentionally pass raw strings.
