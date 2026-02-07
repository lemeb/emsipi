# Step 4: Creating the Pull Request

**Goal**: Create a PR for the completed feature.

## Prerequisites

- [ ] All tasks from the plan are complete (Step 3 done for all tasks)
- [ ] All commits are pushed to the feature branch
- [ ] Feature branch is rebased on base branch

If tasks remain, go back to Step 3.

## Procedure

1. **Verify readiness**:
   - All tasks committed
   - `/quality` passes on the full branch
   - Branch is up to date with base branch (rebase if needed)

2. **Push the branch** if not already pushed:

   ```bash
   git push -u origin <branch-name>
   ```

3. **Gather lessons learned**:
   - Review any issues encountered during implementation
   - Note patterns that should be documented
   - If you ran `/quality` via sub-agents, check their output for lessons
   - Consider: What would have helped you implement this faster?

4. **Create the PR** with:

   **Title**: Brief, descriptive (under 70 chars)

   **Description** sections:
   - **Summary**: What this PR does (reference the spec)
   - **Changes**: Bullet list of what was added/changed
   - **Testing**: How to verify the changes work
   - **Checklist**: Quality gates passed
   - **References**: Link to issue/spec
   - **Lessons learned**: Anything to add to AGENTS.md or dev/\*.md

5. **Link the PR** per tracker conventions

## PR Description Template

```markdown
## Summary

<1-3 sentences describing what this PR accomplishes>

Closes #<issue-number>

## Changes

- <change 1>
- <change 2>
- ...

## Testing

<How to test these changes>

## Checklist

- [ ] `make check` passes
- [ ] `make check-strict-all` passes
- [ ] `make test-with-coverage` passes (coverage maintained)
- [ ] `make doc` passes
- [ ] Branch rebased on <base-branch>

## Lessons Learned

<Any discoveries that should be added to AGENTS.md or dev/\*.md> <If none, write
"None">
```

<!-- Expand here with repo-specific information. For example:
     - PR template requirements?
     - Issue linking format?
     - Required reviewers?
     - Additional quality gates?
     Do NOT remove this comment. -->

## Completion Criteria

- [ ] PR created with complete description
- [ ] PR linked per tracker conventions
- [ ] CI passing (if applicable)

## Exit

After PR is created:

- Output: `<STEP_COMPLETE>`
- Report the PR URL
- Next: Wait for CI and review (Step 5 handles feedback)

If PR creation blocked (e.g., CI failing, merge conflicts):

- Output: `<BLOCKED reason="...">`
