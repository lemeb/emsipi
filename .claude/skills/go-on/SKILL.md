---
name: go-on
description:
  Continue the implementation workflow from wherever it was left off. Executes
  ONE atomic unit of work, then exits cleanly. Use to make incremental progress
  on a feature.
---

# Workflow Continuation

Load `AGENTS.md` to understand the full workflow and current project
conventions.

## Procedure

1. **Assess current state** from external sources:
   - Check for spec (issue tracker, conversation, or docs)
   - Check for implementation plan and task breakdown
   - Check git for branch, commits, uncommitted changes
   - Check filesystem for implementation progress

2. **Identify next action** based on state:

   | State                               | Action                                                      |
   | ----------------------------------- | ----------------------------------------------------------- |
   | No spec exists                      | Write spec, update tracking, EXIT                           |
   | No plan/tasks                       | Write plan, present to user, wait for approval, EXIT        |
   | Plan approved but tasks not tracked | Create task entries, EXIT                                   |
   | Incomplete task exists              | Implement ONE task, run `/quality`, commit, mark done, EXIT |
   | Task in progress, quality failing   | Fix errors until `/quality` passes, then commit, EXIT       |
   | Code ready but not committed        | Run `/quality`, commit, mark task done, EXIT                |
   | All tasks done, no PR               | Create PR, EXIT                                             |
   | PR exists                           | Report completion, EXIT                                     |

3. **Execute that ONE action** — do NOT ask for permission, just do it

4. **Update tracking** (issue tracker, git, task list)

5. **Exit with clear status**:

   ```text
   ## /go-on Status

   Previous state: <what was found>
   Action taken: <what was done>
   New state: <what changed>
   Next step: <what should happen next>
   ```

## Key Principles

- **Stateless**: Determines state fresh each time from files/git/tracking
- **One atomic unit**: Does ONE thing per invocation
- **Idempotent**: Safe if interrupted; next invocation re-assesses

## Exit Conditions

- **Success**: Completed one unit of work
- **Blocked**: Cannot proceed (waiting for approval, dependency)
- **Complete**: Feature done, PR created
- **Error**: Something went wrong, needs human intervention
