# Coding agent instructions for `emsipi`

## Good coding practices

- **Step-by-step**:
  - When coding a feature, try to break it down into smaller steps. This will
    help you focus on one thing at a time, and will make it easier to debug
    issues.
  - In practice, it means that you should operate roughly thusly:
    1. Create the directory and files needed for the feature (and ONLY
       those files.) Maybe update `.gitignore` if needed.
    2. Add the dependencies needed for the feature (and ONLY those
       dependencies.)
    3. Write the code for the feature (and ONLY that code.)
    4. Run the tests with `make test-all` and make sure they pass.
    5. Run `make test-with-coverage` to see which parts of the code are not
       covered by unit tests (without overwriting `make test-all` coverage).
       Then...
    5. Write the tests for the feature (and ONLY those tests.) As a general
       rule, we want 100% coverage WITHOUT any internet / latency request. These
       tests should be triggered with `make test`. HOWEVER, if the feature
       actually requires internet access or latency (e.g. because it is a
       LLM call), then add a test in the `tests/integration` folder that will be
       triggered with `make test-all`. In this case, you should still aim for
       two tests: one that mocks the internet / latency request (so that it can
       be run with `make test`), and one that actually does the internet /
       latency request (so that it can be run with `make test-all`.)
    6. Run the tests and make sure they pass. Note that, for now, `make test`
       does not run coverage; use `make test-with-coverage` to track unit test
       coverage without rerunning integration tests.
    7. Run again `make test-with-coverage` until you reach 100% coverage. If you
       want to make an exception to that rule, you HAVE to ask the user.
    8. Run `make check-strict-all` to make sure there are no linting or
       type-checking errors.
    9. Document the feature (and ONLY that documentation, although you might
       to update / refactor other documentation as needed.)
    10. Propose a git commit with a clear message explaining what you did. DO
        NOT COMMIT directly. Oftentimes, it makes sense to split the work into
        multiple commits. In this case, propose multiple commits with clear
        messages.
  - This is only a guideline, not a strict rule. Use your best judgment. But in
    general, we want git commits to be clean and self-contained.

## Good Python practices

- **Adding dependencies**:
  - Always add new dependencies using `uv add <package>`. This will ensure
    proper locking of the dependencies.
  - If you need to add a dev dependency, use `uv add --dev <package>`.
  - Corollary: never modify `pyproject.toml` or `uv.lock` directly. Always use
    `uv` commands.
  - Only add dependencies that are strictly necessary. Yes, you might think
    that some packages will need to be added later. Well, wait until later then.

- **Checking code**:
  - Use `uv run ruff format . && uv run ruff check . --fix`, then
    `make check-strict-all` to check your code. Please refer to the earlier
    instructions on what is appropriate when.
  - One quirk of `make check-strict-all` is that it will run `ruff`'s preview
    rules. If you want to comment such rule out, you cannot do it in the file;
    it will be removed by `ruff format`. Instead, you should update the
    `ruff-strict.toml` file where these exceptions are documented. YOU SHOULD
    DOCUMENT THE RULE PER FILE, NOT FOR THE ENTIRE CODEBASE. And every exception
    should be documented with a comment explaining why the rule is not applied
    in that file.
  - If you're wondering if a rule is in preview: if it appears during
    `make check-strict-all`, but not during `make check`, then it is a preview
    rule. This means that you need to comment it out in `ruff-strict.toml` if
    you want to ignore it.
  - Be **really** weary before adding any `# type: ignore`, `# pyright: ignore`,
    or `# noqa` comments. These should be used only as last resort, when no
    better solution is available. Don't hesitate to ask questions to the user on
    whether further code changes are made to avoid these comments, or whether
    the ignore comments are acceptable.

- **Code practices**:
  - Check `pyproject.toml` to know what is the minimum Python version that is
    supported. Write constructs accordingly (e.g. no `Union` if Python 3.10+ is
    supported).
  - Try not to use `print` statements. Use your best judgment instead: if it's
    for logging, use `logging`. If it's for user-facing interaction, use the
    `rich` library (such as `print` or `Console`).
  - You can use `# type: ignore[error-code]` (`mypy`),
    `# pyright: ignore[ErrorCode]` (`pyright`), and `# noqa: <ERROR_CODE>`
    (`ruff`). If multiple go on the same line, they should go with `mypy` first.
    Use them only as last resort, when no better solution is available. (An
    example where this is warranted is if `Any` is really the only type that
    works, or if you need to use a third-party library that is not typed.) Some
    pointers on which errors to just comment out are specified below.
  - IMPORTANT! Don't hesitate to over-document. Please ensure that when you
    modify a function, you also update the docstring. If you add a new
    parameter, please document it. Don't forget to put "args", "returns", and
    "raises" in the docstring. THIS IS ONE VERY COMMON LINTING MISTAKE!
  - Check `pyproject.toml` for the max line length. It's probably 80. Yes, the
    formatter will sometimes just reformat the code, but some lines (e.g.
    docstrings) will need to be modified accordingly.
  - The right way to pass a message to an exception is to define a `msg`
    variable, and then pass it to the exception.
  - Put `@final` whenever needed. Helps for type-checking.
  - Put `@override` whenever needed (and it's generally more often than you
    think). Helps for type-checking.
  - Any time you define an empty list, try to type-hint it (e.g.
    `my_list: list[str] = []`).
  - Be mindful of class methods that don't use the `self` parameter. If you
    don't use it, you should make it static.

- **Documentation practices**:
  - Whenever possible, any references to a file or library (or really any piece
    of code) should be surrounded with backticks. Don't say ("we detect
    uv.lock", say "we detect `uv.lock`").

- **Handling linting and type-checking errors** (these are misc notes):
  - In general, if we're dealing with operations that inherently deal with `Any`
    or `Unknown` (e.g. because you're parsing JSON, because you're dealing with
    a third-party library that is not typed, etc.), you can safely put ignore
    comments for: `reportUnknownArgumentType`, `reportUnknownMemberType`,
    `reportUnknownVariableType`, `reportUnknownParameterType`,
    `reportUnknownType`, `reportAny`, `reportExplicitAny`, etc. (`pyright`), and
    `ANN401` (`ruff`).
  - In some cases, you can put `object` as the type, but this is not
    recommended. If you do so, please document why you did it.
