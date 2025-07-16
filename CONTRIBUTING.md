# Contributing

## ✨ Getting started

### Prerequisites

- [`uv`](https://docs.astral.sh/uv/)
- [`cruft`](https://cruft.readthedocs.io/en/latest/)

### Installation

```bash
make install-all          # Installs all dependencies, including dev ones
# make install            # Only installs the dependencies for the project
source .venv/bin/activate # Activate the virtual environment
```

### Running Tests

```bash
make check                # Runs the linters
# make check-strict-all   # Runs the linters with strict mode
make test                 # Runs most tests
# make test-all           # Runs all tests, including browser ones
# make test-all-versions  # Runs all tests for all supported Python versions
```

### Updating the project

```bash
cruft update       # Updates the project to the latest version of the template
make update-all    # Updates the dependencies, including dev ones
# make update      # Only updates the dependencies for the project
```

### Building the documentation

```bash
make doc-serve            # Builds and serves the documentation locally for preview
make doc                  # Tests then builds the documentation
```

## 📦 Project Structure

- `src/emsipi/`: Main library code.
- `tests/`: Tests.
- `docs/`: Documentation.
- `scratch/`: Scratchpad directory. Ignored by git.

## 💻 Developer experience

### Dependencies and building

We use [`uv`](https://docs.astral.sh/uv/) for dependency management, running
tasks, and package building. `uv` will be installed automatically by the
`Makefile` if it's not found.

#### Adding dependencies

```bash
uv add <dependency> # Adds a dependency to the project
uv add --dev <dependency> # Adds a dev dependency to the project
```

#### Versioning

Note that the version is declared in the `pyproject.toml` file. Don't forget to
update it when you make a new release. We might move to dynamic versioning in
the future if and when
[`uv_build` supports it](https://github.com/astral-sh/uv/issues/11718#issuecomment-2678446245).

### Documentation

For documentation, we use:

- [`mkdocs`](https://www.mkdocs.org/) as the main tool
- [`mkdocs-material`](https://squidfunk.github.io/mkdocs-material/) as the theme
- [`mkdocstrings`](https://mkdocstrings.github.io/) to automatically generate
  documentation from the docstrings.

You can build the documentation locally with `make doc-serve` and preview it at
`http://localhost:8000`. To test and build the documentation, run `make doc`.

### Testing

We use:

- [`pytest`](https://docs.pytest.org/en/stable/) for unit tests.
- [`coverage.py`](https://coverage.readthedocs.io/en/stable/) for coverage.

#### Coverage settings

The settings of `coverage.py` are such that:

- You should see which tests covered which lines of code.
- Type checking-specific code is excluded from coverage.

### Linting and type-checking

We use:

- [`ruff`](https://docs.astral.sh/ruff/) for linting.
- [`mypy`](https://mypy.readthedocs.io/en/stable/) for type-checking.
- [`basedpyright`](https://github.com/basedpyright/basedpyright) for
  type-checking.

By default:

- We use `ruff` with the strictest settings, and some specific ignores that are
  available in the `pyproject.toml` file.
- We use `mypy` with strict settings but ignoring missing imports.
- We do not use `basedpyright`.

We have a "strict" mode that uses more restrictive settings:

- `ruff` with preview rules (preview-mode specific ignores should be put in the
  `ruff-strict.toml` file)
- `mypy` with strict settings and no missing imports ignored.
- `basedpyright` with strict settings.

### Pre-commit hooks

We use [`pre-commit`](https://pre-commit.com/) to run the linters and
type-checkers before committing.

The configuration is in the `.pre-commit-config.yaml` file. Note that we use
`pyright` and not `basedpyright`.
