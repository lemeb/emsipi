# Tracker: Linear

This tracker uses Linear for specs, task tracking, and collaboration.

## Step 1: Spec

**Where to record**: Linear issue description

Example issue `SUN-42: User Authentication`:

```markdown
## Problem

Users cannot log in to the application. We need a secure authentication system.

## Proposed Solution

Implement JWT-based authentication with email/password login.

## Acceptance Criteria

- [ ] User can register with email and password
- [ ] User can log in and receive a JWT token
- [ ] Protected routes reject requests without valid token
- [ ] Passwords are hashed with bcrypt

## Non-Goals

- Social login (OAuth) — future work
- Password reset — future work
```

## Step 2: Plan

**Where to record**: Linear issue description + sub-issues

1. Update the parent issue description with the implementation plan:

```markdown
---

## Implementation Plan

Status: DRAFT

See sub-issues for task breakdown.

### Notes

- Using PyJWT for tokens
- Token expiry: 24 hours
```

1. Create sub-issues with dependencies:
   - `SUN-42(1): Add User model and migrations`
   - `SUN-42(2): Add password hashing utilities` — blocked by (1)
   - `SUN-42(3): Add /register endpoint` — blocked by (1), (2)
   - `SUN-42(4): Add /login endpoint with JWT` — blocked by (1), (2)
   - `SUN-42(5): Add auth middleware` — blocked by (4)
   - `SUN-42(6): Protect routes with middleware` — blocked by (5)

1. Set Linear's native "Blocked by" relationships between sub-issues

**Approval mechanism**:

- In interactive mode, user approves verbally (agent proceeds immediately)
- In headless mode:
  1. Create plan and sub-issues with `Status: DRAFT` in description
  2. Add comment: "Implementation plan ready for review"
  3. Move parent issue to "Ready for Dev"
  4. Output `<AWAITING_APPROVAL>`
  5. User approves by moving to "In Progress" — agent checks issue status on
     next invocation

## Step 3: Task

**Identifying next task**: Find the first sub-issue in "Todo" status with no
blocking dependencies.

**Tracking progress**:

- Move sub-issue to "In Progress" when starting
- Move to "Done" when complete
- Add commit hash as a comment

Example sub-issue status flow:

- `SUN-42(1)`: Todo → In Progress → Done (commit abc123)
- `SUN-42(2)`: Blocked → Todo → In Progress → Done (commit def456)
- `SUN-42(3)`: Blocked → Todo ← current

## Step 4: Ship

**PR reference**:

- Add PR URL as a comment on the parent issue
- Move parent issue to "In Review"

## Step 5: Feedback

**On BLOCKED**:

- Add a comment explaining the blocker and what decision is needed
- Move issue to "Blocked" status
- Tag relevant stakeholders

## Step 6: Cleanup

**After merge**:

- Move parent issue to "Done"
- Sub-issues should already be "Done"

---

## Local vs Remote: The Hybrid Approach

**Draft locally, publish when done. Track progress remotely.**

| Artifact      | Where to draft          | Where to publish          | Notes                             |
| ------------- | ----------------------- | ------------------------- | --------------------------------- |
| Spec          | `.claude/draft-spec.md` | Linear issue description  | Push when interview/spec complete |
| Plan          | `.claude/draft-plan.md` | Linear issue + sub-issues | Push when plan approved           |
| Task progress | —                       | Linear sub-issue status   | Track ONLY in Linear, not locally |

**Why this approach**:

- Drafting locally allows iteration without spamming issue history
- Git history on drafts is valuable for complex features
- Task progress in Linear = single source of truth for status
- Anyone (human or agent) can check Linear to see current state

**Workflow**:

1. Draft spec locally during `/interview` or Step 1
2. When spec is ready, push to issue description
3. Draft plan locally during Step 2
4. When plan is approved, push to issue + create sub-issues
5. Track task completion ONLY by moving sub-issues in Linear
