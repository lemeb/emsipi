# Python Practices

> **TL;DR**: Check `pyproject.toml` for Python version and line length. Use
> `uv add` for dependencies. Document thoroughly.

This file covers general Python practices. For linting/type-checking specific
practices, see `dev/checking.md`. For docstring formatting, see
`dev/documentation.md`.

---

## Adding Dependencies

```bash
uv add <package>       # Runtime dependency
uv add --dev <package> # Dev dependency
```

- Always add new dependencies using `uv add <package>`. This will ensure proper
  locking of the dependencies.
- Corollary: never modify `pyproject.toml` or `uv.lock` directly as far as
  dependencies are concerned. Always use `uv` commands.
- Only add dependencies that are strictly necessary. Yes, you might think that
  some packages will need to be added later. Well, wait until later then.

---

## Before Writing Code

Check `pyproject.toml` for:

- **Minimum Python version**: Don't use syntax/features unavailable in that
  version (e.g., no `Union` type hint if Python 3.10+, use `|` instead).
- **Line length**: Probably 80. Formatter handles most, but docstrings need
  manual wrapping.

---

## Code Style

### Docstrings

IMPORTANT! Don't hesitate to over-document. Please ensure that when you modify a
function, you also update the docstring. If you add a new parameter, please
document it. Don't forget to put "args", "returns", and "raises" in the
docstring. THIS IS ONE VERY COMMON LINTING MISTAKE!

The exception here are helper functions that are private to a module and are
self-explanatory.

See `dev/documentation.md` for detailed docstring formatting rules.

### Type Hints, Methods, Exceptions, Output

See `dev/checking.md` for detailed practices on:

- Type hints (`@final`, `@override`, `cast`, empty collections)
- Methods and parameters (static methods, unused parameters)
- Exception message patterns
- Output (logging vs print vs rich)

---

## Lessons Learned

<!-- This section should be updated over time with quirks discovered during
     development. After fixing issues, consider whether the fix reveals
     something that should be documented here for future reference. -->
