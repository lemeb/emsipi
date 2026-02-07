# Documentation

> **TL;DR**: Run `make doc`. New modules need entries in `docs/api/` and
> `mkdocs.yml`. Add new terms to `project-words.txt` (do NOT sort it).

---

## General Documentation Rules

### Markdown Formatting

- **Blank line before lists**: In markdown and docstrings, always insert a blank
  line between a paragraph and a list. Without it, the list may not render
  correctly. (This doesn't apply to `Raises:` or `Args:` sections in docstrings,
  where the list is part of the same section.)

  ```markdown
  <!-- Correct -->

  List header:

  - first element
  - second element

  <!-- Incorrect - no blank line -->

  List header:

  - first element
  - second element
  ```

- **Two newlines between paragraphs**: Separate paragraphs with two newlines
  (i.e., a blank line). A single newline will render as one continuous
  paragraph.

### Code References and Backticks

Whenever possible, any references to a file or library (or really any piece of
code) should be surrounded with backticks. Don't say "we detect uv.lock", say
"we detect `uv.lock`".

The purpose of backticks is twofold:

1. Visual distinction: code references stand out from prose
2. Semantic meaning: readers know this is a literal file/function/variable name

### Cross-References

Use the format ``[`function`][module.function]`` to create clickable links in
the generated documentation. Example:

```markdown
Uses [`lru_cache`][functools.lru_cache] to ensure...
```

Yes, this means using _both_ backticks and square brackets. This is so that the
generated documentation shows the function name in a code font while linking to
the right place.

This works for:

- The standard library
- This library's own modules
- External libraries configured in inventories (see mkdocs section below)

If you reference something that is not in an inventory, you can still use
backticks, but don't use the square brackets.

**Exception**: You don't need cross-references in `Args:`, `Returns:`, or
`Raises:` sections of docstrings - griffe handles those automatically.

---

## mkdocs-Specific Rules

### Commands

| Command          | Purpose                                                    |
| ---------------- | ---------------------------------------------------------- |
| `make doc`       | Build docs + spell check. **Must pass before committing.** |
| `make doc-serve` | Live preview at localhost:8000                             |

### New Modules

If you create a new module, you MUST:

1. Create a corresponding file in `docs/api/`
2. Update the `nav` section in `mkdocs.yml` to include it

### Spell Check

- Run `make doc` to verify spell check passes
- Add any new technical terms to `project-words.txt`
- Do NOT use `sort` on `project-words.txt`

### Inventories

Available inventories are configured in `mkdocs.yml` under `inventories`. Add
new ones as needed (e.g., `https://example.com/objects.inv`).

Only use cross-references if either:

1. The function or object is part of the standard library
2. The function or object is part of the current library
3. Is part of an external library but the inventory is in the `inventories`
   section of `mkdocs.yml` or another plugin takes care of it (like a
   `griffe-pydantic` plugin for Pydantic objects)

### Guides and Tutorials

Documentation in `docs/` is not limited to API docs. If you think documentation
would be improved by adding things like tutorials, guides, etc., please propose
them to the user. If you see that one of the existing guides or tutorials needs
to be updated, please do so proactively and properly.

For large user-facing features, consider whether a guide would help users
understand how to use the feature.

---

## Docstring-Specific Rules

We use Google style docstrings.

### Basic Format

```python
def example(param1: str, param2: int) -> bool:
    """Short description of the function.

    Longer description if needed. Use blank lines between paragraphs.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value. Continuation lines must be
            indented like this to show they belong to the same
            return description.

    Raises:
        ValueError: When something is wrong.
    """
```

### Critical Docstring Rules

- **IMPORTANT!** Don't hesitate to over-document. Please ensure that when you
  modify a function, you also update the docstring. If you add a new parameter,
  please document it. Don't forget to put "args", "returns", and "raises" in the
  docstring. THIS IS ONE VERY COMMON LINTING MISTAKE! The exception here are
  helper functions that are private to a module and are self-explanatory.

- **1:1 correspondence for Raises**: Make sure there is an exact 1:1
  correspondence between the errors EXPLICITLY raised in the body of the
  function and the errors listed in the `Raises:` section of the docstring. If
  an error is raised but not documented, or documented but not raised, fix the
  docstring or the code accordingly.

- **Returns section**: Always strive to include a `Returns:` section in
  docstrings of functions that return a value. (Don't bother for abstract
  methods or functions that only return `None`, or for "stub functions":
  functions where the body only consists of `pass`, `...`,
  `raise NotImplementedError`, or similar)

- **Return continuation lines**: In `Returns:` sections, continuation lines must
  be indented to show they belong to the same return description. For example:

  ```python
  Returns:
      The URL with async driver if it was a postgres URL,
          otherwise the original value unchanged.
  ```

- **Don't state the obvious**: If a class explicitly subclasses something (e.g.,
  `class A(B, C):`), don't write "Inherits from B and C" in the docstring - the
  auto-generated documentation already shows this.

---

## Lessons Learned

<!-- This section should be updated over time with quirks discovered during
     development. After fixing documentation errors, consider whether the fix
     reveals something that should be documented here for future reference. -->
