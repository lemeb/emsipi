---
name: doc
description:
  Build documentation and ensure all doc-related checks pass. Use after writing
  code, before committing.
---

# Documentation

Load `dev/documentation.md` for detailed guidance on docstrings and markdown
formatting.

## Procedure

1. Run `make doc`

2. If spell check fails: add new terms to `project-words.txt` (do NOT sort it)

3. If new module was created: ensure `docs/api/` entry AND `mkdocs.yml` nav
   updated

4. Repeat until `make doc` passes

## Output Format

```text
## Documentation Results

- `make doc`: PASS/FAIL
- New terms added to project-words.txt: <list or "none">
- New modules documented: <list or "none">

### Lessons Learned
<Patterns discovered while fixing doc issues — things future agents should know>
<If none, write "None">
```

**Always include Lessons Learned**, even if empty. When running as a sub-agent,
the main agent needs this for the PR description.

Examples of lessons learned:

- "The spell-checker doesn't recognize 'webhook' — added to project-words.txt"
- "New modules need BOTH `docs/api/<module>.md` AND an entry in mkdocs.yml nav"
- "Use `mkdocstrings` syntax `::: module.path` to auto-generate from docstrings"

## Exit Conditions

- **Success**: `make doc` passes
- **Failure**: Report remaining errors clearly
