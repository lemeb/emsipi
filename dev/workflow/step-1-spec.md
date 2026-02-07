# Step 1: Understanding the Feature

**Goal**: Produce a clear spec that captures what needs to be built.

The level of detail required depends on the team and codebase. Some teams want
formal specs; others want a few bullet points.

## Iron Laws

1. **NO coding until spec is recorded** — Even if you "know what to do," write
   it down first. This catches misunderstandings early.

2. **Acceptance criteria must be testable** — Not "works correctly" but "returns
   200 OK with JSON body containing `user_id`."

3. **Ask about edge cases the user hasn't considered** — Your job is to surface
   hidden assumptions while changes are cheap.

## Prerequisites

- You have a feature request (from user, issue tracker, or conversation)
- You have access to the codebase

## Procedure

1. **Explore the codebase** to understand:
   - Current architecture and patterns
   - Related existing functionality
   - Potential impact areas

2. **Clarify requirements** through dialogue:
   - Probe edge cases, error handling, performance needs
   - Understand integration points and dependencies
   - Confirm user experience expectations

   **Optional: Structured Interview Approach**

   For complex features, consider using `/interview` (if available) or the
   "mutual interview" technique where the agent systematically questions the
   user before writing any code:
   - Probe failure modes, tradeoffs, and hidden assumptions
   - Ask about edge cases the user may not have considered
   - Surface design decisions while they're cheap to change

3. **Research** if needed:
   - Third-party libraries or APIs
   - Similar implementations in other projects
   - Documentation or RFCs

4. **Write the spec** (adapt to team standards):
   - **Problem statement**: What problem does this solve?
   - **Proposed solution**: High-level approach
   - **Acceptance criteria**: How do we know it's done?
   - **Non-goals** (optional): What this intentionally doesn't do

5. **Record the spec** per the active tracker's conventions

## Completion Criteria

- [ ] Codebase explored sufficiently to understand impact
- [ ] All critical questions answered (or escalated)
- [ ] Spec written with acceptance criteria
- [ ] Spec recorded per tracker conventions

## Exit

When spec is complete and recorded:

- Output: `<STEP_COMPLETE>`
- Next: Step 2 (Planning)

If waiting for user input on critical questions:

- **Interactive mode**: Wait for user response
- **Headless mode**: Record state, output `<AWAITING_INPUT reason="...">`
