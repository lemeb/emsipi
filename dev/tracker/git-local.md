# Tracker: Git-Local (Default)

This tracker uses git-tracked files for all state. No external services
required.

## File Structure

```text
specs/                        # Feature specifications
├── {feature-slug}.md        # One file per feature
IMPLEMENTATION_PLAN.md        # Task list for current feature (temporary)
```

---

## Step 1: Spec

**Where to record**: `specs/{feature-slug}.md`

Example `specs/user-auth.md`:

```markdown
# User Authentication

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

---

## Step 2: Plan

**Where to record**: `IMPLEMENTATION_PLAN.md` (root of repo)

Example:

```markdown
# Implementation Plan: User Authentication

Spec: specs/user-auth.md Status: DRAFT

## Tasks

- [ ] 1. Add User model and migrations
- [ ] 2. Add password hashing utilities (depends on 1)
- [ ] 3. Add /register endpoint (depends on 1, 2)
- [ ] 4. Add /login endpoint with JWT (depends on 1, 2)
- [ ] 5. Add auth middleware (depends on 4)
- [ ] 6. Protect routes with middleware (depends on 5)

## Notes

- Using PyJWT for tokens
- Token expiry: 24 hours
```

**Approval mechanism**:

- In interactive mode, user approves verbally (agent proceeds immediately)
- In headless mode:
  1. Create file with `Status: DRAFT`
  2. Output `<AWAITING_APPROVAL>`
  3. User approves by changing to `Status: APPROVED`
  4. Agent checks for **explicit** `Status: APPROVED` — missing status is
     treated as DRAFT

---

## Step 3: Task

**Tracking progress**: Update `IMPLEMENTATION_PLAN.md` as you work:

```markdown
## Tasks

- [x] 1. Add User model and migrations ✓ (commit abc123)
- [x] 2. Add password hashing utilities ✓ (commit def456)
- [ ] 3. Add /register endpoint ← IN PROGRESS
- [ ] 4. Add /login endpoint with JWT
- [ ] 5. Add auth middleware
- [ ] 6. Protect routes with middleware
```

---

## Step 4: Ship

**PR reference**: Include spec path in PR description:

```markdown
## Summary

Implements user authentication with JWT tokens.

See: specs/user-auth.md
```

---

## Step 5: Feedback

**On BLOCKED**: Add a note to `IMPLEMENTATION_PLAN.md`:

```markdown
## Blocked

Waiting for decision on token expiry time. See PR #42 comment.
```

---

## Step 6: Cleanup

**After merge**:

- Keep `specs/user-auth.md` as documentation
- Delete `IMPLEMENTATION_PLAN.md` (it was temporary for this feature)

---

## Draft Files

During `/interview` or Step 1, you may use `.claude/draft-spec.md` for work in
progress. When ready, move content to `specs/{feature-slug}.md`.

This keeps `specs/` clean (only finished specs) while allowing iteration.
