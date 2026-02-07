#!/bin/bash
# Remind agents that scratch/ is gitignored and has no effect on CI/CD.

FILE_PATH=$(jq -r '.tool_input.file_path // empty')

if [[ "$FILE_PATH" == *"/scratch/"* || "$FILE_PATH" == scratch/* ]]; then
  cat >&2 <<'MSG'
Friendly reminder: the scratch/ directory is gitignored. Files here are NOT
tracked by git and will have NO influence on CI/CD. If you intended to make
a change that persists, edit the appropriate project file instead.
MSG
fi
