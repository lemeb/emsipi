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

## Exit Conditions

- **Success**: `make doc` passes
- **Failure**: Report remaining errors clearly
