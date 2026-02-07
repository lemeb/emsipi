# Step 5: Addressing PR Feedback

**Goal**: Address review feedback. The human decides when to merge.

## Prerequisites

- [ ] PR exists (Step 4 complete)
- [ ] Feedback has been received (comments, review requests, CI results)

If no feedback yet (CI still running, reviewers haven't looked):

- Output: `<AWAITING_REVIEW>`
- In autonomous loops, this is a natural pause point

## Procedure

1. **Read all feedback** carefully:
   - Review comments from humans
   - CI failures and automated check results
   - AI-powered review feedback (if any)

2. **For each piece of feedback**:

   a. **Understand** what's being asked b. **Implement** the fix or improvement
   c. **Run `/quality`** to verify d. **Commit** the fix (small, focused
   commits) e. **Reply** to the comment explaining what was done

3. **Push the updates**:

   ```bash
   git push
   ```

4. **Re-request review** if needed

## Handling Different Feedback Types

| Feedback Type        | Action                                                 |
| -------------------- | ------------------------------------------------------ |
| Bug/error found      | Fix it, add test to prevent regression                 |
| Style/convention     | Fix it; note in PR if it's a pattern worth documenting |
| Architecture concern | Discuss with reviewer, may need larger changes         |
| Documentation gap    | Add the missing docs                                   |
| Test coverage        | Add the missing tests                                  |

**Lessons learned**: If feedback reveals a pattern that future agents should
know about, add it to the PR description under "Lessons Learned". The human
maintainer will decide whether to incorporate it into `AGENTS.md` or `dev/*.md`.

<!-- Expand here with repo-specific information. For example:
     - How to handle feedback from different sources (bot comments, human reviewers)?
     - Any specific conventions for addressing feedback?
     - How to handle conflicting feedback?
     Do NOT remove this comment. -->

## Completion Criteria

- [ ] All feedback addressed
- [ ] All conversations resolved
- [ ] CI passing

Note: **Merge is a human decision.** This step is complete when feedback is
addressed, not when the PR is merged.

## Exit

After addressing all current feedback:

- Output: `<STEP_COMPLETE>`
- The human will decide when to merge
- If more feedback comes later: Re-run this step

If waiting for initial review (no feedback yet):

- Output: `<AWAITING_REVIEW>`

If blocked (e.g., disagreement with reviewer, architectural decision needed):

- Output: `<BLOCKED reason="...">`
