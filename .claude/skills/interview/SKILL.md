---
name: interview
description:
  Conduct a structured feature interview to gather requirements before
  implementation. Asks about scope, user experience, technical design, and edge
  cases. Outputs a specification document. Use before /go-on for complex
  features.
---

# Feature Interview

## Purpose

Gather complete requirements through structured questioning before writing any
code. This surfaces hidden assumptions and design decisions when they're cheap
to change.

## When to Use

- Feature idea that needs clarification
- Ambiguous requirements with multiple valid implementations
- Complex features where scope needs definition
- Before `/go-on` for non-trivial work

## Arguments

```text
/interview "feature description"
/interview "feature description" --context path/to/existing-doc.md
/interview "feature description" --quick
/interview "feature description" --first-principles
```

- `--quick`: Lighter interview (5-8 questions), end when basics are covered
- `--first-principles`: Challenge assumptions before detailed spec gathering
- `--context`: Load existing documentation as starting context

## Interview Modes

### Default Mode (Rigorous)

**Behave like a competent, well-meaning, rigorous staff engineer.**

Ask 10-15 questions across phases. Probe for edge cases, challenge vague
answers, and ensure acceptance criteria are specific and testable. Continue
until user explicitly says "done", "finalize", "that's enough", or similar.

Do NOT auto-complete. The user decides when the interview is sufficient.

### Quick Mode (`--quick`)

Lighter interview for well-understood features. Ask 5-8 questions covering the
basics. End when completion criteria are met OR user seems ready to proceed.

Use this for small features where extensive requirements gathering isn't needed.

### First-Principles Mode (`--first-principles`)

Before gathering detailed spec, challenge the approach with 3-5 questions:

1. "What specific problem have you observed that led to this idea?"
2. "What happens if we don't build this at all? What's the cost of inaction?"
3. "What's the absolute simplest thing that might solve this problem?"
4. "What would have to be true for this to be the wrong approach?"
5. "Is there an existing solution we could use instead?"

Only proceed to detailed spec gathering once the approach seems valid.

## Interview Phases

Adapt phases to the project type. Not all phases apply to all features.

### Phase 1: Scope & MVP (2-3 questions)

- What core problem does this solve?
- Who are the primary users/consumers?
- What's explicitly OUT of scope?
- What's the minimum viable version?

### Phase 2: Interface & Behavior (2-3 questions)

Adapt to project type:

- **API/Backend**: What are the endpoints/methods? What data goes in/out?
- **CLI**: What commands and flags? What output format?
- **Library**: What's the public API? How do users import/call it?
- **Frontend**: What are the user journeys? What happens on error?
- **Data pipeline**: What's the input source? Output destination? Transform
  logic?

### Phase 3: Technical Design (2-3 questions)

- What data needs to be persisted or transformed?
- External integrations or dependencies needed?
- Security or authentication concerns?
- Performance constraints or SLAs?

### Phase 4: Edge Cases & Tradeoffs (1-2 questions)

- What scenarios haven't been considered?
- What are the key tradeoffs you're willing to make?
- How does this interact with existing functionality?

## Handling Uncertainty

When the user responds "I don't know" or seems unsure:

- **Offer contextual defaults** based on common patterns in the codebase
- **Record as assumption** in the spec (to be validated during implementation)
- **Only block if architectural** — auth method, data model = must know; UX
  details = can default

## Question Design

1. **Avoid obvious questions** — Don't ask "do you want error handling?" Ask
   "which errors should fail gracefully vs. fail fast?"

2. **Reveal assumptions** — Ask what the user hasn't considered

3. **Provide options** — Offer 2-3 concrete choices when possible

4. **Be specific** — Require measurable outcomes, not vague "works correctly"

## Completion Criteria

End the interview when:

- [ ] Scope boundary is clear (MVP defined)
- [ ] Main interface/behavior is mapped
- [ ] Technical approach is sketched
- [ ] Major edge cases are identified
- [ ] Acceptance criteria are specific and testable (not vague)
- [ ] **User explicitly confirms** — "done", "finalize", "that's enough", etc.

**Important**: In default (rigorous) mode, do NOT end the interview on your own.
Wait for the user to signal completion. Keep asking probing questions until they
do. In `--quick` mode, you may suggest wrapping up when basics are covered.

## Output Format

Generate a spec file (per tracker conventions) with:

```markdown
# Feature: [Name]

## Problem

[What problem does this solve?]

## Proposed Solution

[High-level approach]

## User Stories

- As a [user], I want [goal] so that [benefit]
  - Acceptance: [testable criterion]

## Technical Notes

- Data model considerations
- API design notes
- Integration points

## Acceptance Criteria

- [ ] [Specific, testable criterion]
- [ ] [Another criterion]

## Assumptions

| Assumption            | Risk         | Notes                |
| --------------------- | ------------ | -------------------- |
| [What we're assuming] | Low/Med/High | [Validation needed?] |

## Decision Log

| Question             | Answer          | Implication                          |
| -------------------- | --------------- | ------------------------------------ |
| [Key question asked] | [User's choice] | [What this means for implementation] |

## Out of Scope

- [What this explicitly doesn't do]

## Open Questions

- [Anything deferred to implementation]
```

## Example

**User**: "I want to add user authentication"

**Interview asks**:

- "Email/password only, or also social login (Google, GitHub)?"
- "Should sessions persist across browser restarts?"
- "What happens after 3 failed login attempts?"
- "Do you need password reset, or is that future work?"

**Result**: Clear spec with JWT vs. session decision, lockout policy, and
explicit scope boundaries.

## After Interview

Once you have a spec:

1. Save it per tracker conventions (e.g., `specs/auth.md`)
2. Run `/go-on` to start the implementation workflow

## Maintaining Draft

Update `.claude/draft-spec.md` after every 2-3 questions. This ensures nothing
is lost if the session is interrupted.

When the interview is complete, move the draft to its final location per tracker
conventions (e.g., `specs/{feature-slug}.md` for git-local, or push to the issue
for GitHub/Linear).
