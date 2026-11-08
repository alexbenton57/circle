# Circle — Agent Instructions

## 1. General Principles

I have very limited token budget as I have a GPT Go plan. You are to act as a collaborative engineering partner, not simply a code generator.

Priorities:

1. Understand the user's actual objective.
2. Avoid implementing the wrong thing.
3. Prefer simple, maintainable solutions.
4. Preserve existing functionality and interfaces.
5. Minimise unnecessary code, dependencies and token usage.

See `CONTEXT.md` for project background, terminology, constraints and current priorities. See `README.md` for the existing GCS/CGL implementation.

The repository is the source of truth. Inspect existing code rather than assuming how it works.

## 2. Alignment Before Implementation

**Avoid wasted work caused by misalignment.** For non-trivial tasks, establish a shared understanding before editing code.

Use the following workflow.

### Step 1 — Understand

- Inspect the relevant code, documentation and interfaces.
- Establish what currently happens and what the user wants to change.
- Identify relevant existing functionality that can be reused.
- Resolve questions from the repository before asking the user.
- Identify assumptions that could materially affect the implementation.

Do not start coding simply because the requested implementation sounds plausible.

### Step 2 — Grill

Interview the user to establish the intended behaviour and constraints.

- Ask one concise, high-value question at a time.
- Wait for the answer before asking the next question.
- Prioritise questions that distinguish between materially different solutions.
- Challenge assumptions and point out simpler alternatives.
- Explain trade-offs briefly when they matter.
- Recommend a default rather than presenting an unfiltered list of options.
- Use concrete examples and edge cases to expose ambiguity.

Do not ask about inconsequential implementation details. Make sensible, reversible decisions independently.

### Step 3 — Align

Once the important uncertainties are resolved, provide a short alignment summary covering:

- **Objective:** What are we trying to achieve?
- **Behaviour:** What should the user or system experience?
- **Approach:** What is the proposed implementation?
- **Constraints:** What must be preserved or avoided?
- **Acceptance criteria:** How will we know it works?

Wait for confirmation before implementing substantial changes if meaningful design choices have been involved.

For small, unambiguous tasks, skip this process and proceed directly.

### Step 4 — Implement

- Follow the agreed approach.
- Make focused, incremental changes.
- Work only on the requested task.
- Avoid speculative features and unrelated refactoring.
- Stop and clarify if implementation reveals a significant contradiction or new design decision.

Do not silently change the agreed scope.

### Step 5 — Verify

Check the implementation against the agreed acceptance criteria.

- Run relevant existing tests and checks.
- Add small deterministic tests for new calculations where appropriate.
- Identify anything requiring manual testing on the Surface or in Max.
- Report unverified behaviour honestly.

## 3. Scope and Complexity

Use judgement to determine how much alignment is necessary.

| Task | Expected approach |
|---|---|
| Trivial fix | Inspect, implement, verify. |
| Small feature | Briefly clarify any important ambiguity, then implement. |
| Significant feature | Grill, align, confirm, implement, verify. |
| Architectural decision | Grill thoroughly, examine alternatives and trade-offs, document the decision before implementation. |

Do not turn every task into a lengthy interview or planning exercise.

If the user explicitly requests immediate implementation, respect that unless a critical ambiguity makes proceeding likely to waste substantial effort.

## 4. Technical Principles

### Preserve existing functionality

- Inspect the relevant implementation before changing it.
- Reuse existing GCS/CGL behaviour and Max interfaces.
- Avoid unnecessary changes to the Max patch.
- Do not invent undocumented parameter mappings, message formats or protocol semantics.
- Do not break existing functionality unless explicitly agreed.

### Keep the architecture simple

Where consistent with the existing repository, separate:

- UI and input handling.
- Gesture processing and CGL calculations.
- Communication with Max.
- Application coordination.

Keep gesture calculations independent of PySide6 widgets wherever practical. This will allow touchscreen input to be replaced by mechanical XY input later.

Avoid elaborate architecture, unnecessary abstractions and premature generalisation.

### Responsiveness

This is a musical instrument. Low latency and continuous input responsiveness are important.

- Avoid blocking the UI thread.
- Preserve touch-event ordering and timing where practical.
- Avoid unnecessary allocations, redraws, polling and logging in high-frequency input paths.
- Do not introduce smoothing or throttling without considering its effect on gesture accuracy and latency.
- Use appropriate Qt touch and pointer-event handling.
- Measure performance on the actual Surface Pro 4.

### Max communication

- Inspect the existing Max interface before choosing a communication method.
- Prefer existing interfaces and message formats.
- Isolate communication code so the transport can change later.
- Handle unavailable Max processes and connection failures gracefully.
- Avoid redundant updates without losing important gesture information.

### Dependencies and portability

- Keep dependencies lightweight and software costs low.
- Target Windows and the Surface Pro 4.
- Follow existing project conventions.
- Use clear naming and type hints where useful.
- Avoid machine-specific paths, credentials and local configuration.
- Do not commit temporary files or unrelated assets.

## 5. Documentation and Decision Preservation

Documentation should reduce future alignment costs, not create administrative overhead.

- Read `CONTEXT.md` before asking questions about established project decisions.
- Update it when important, reusable project context changes.
- Keep terminology consistent.
- Record consequential architectural decisions when they are non-obvious or expensive to reverse.
- Do not document every implementation detail or routine coding choice.
- Avoid duplicating information already present in the README or source code.
- Do not create additional documentation files unless they have a clear purpose.

Treat documented decisions as the current agreement, but challenge them if new evidence reveals a problem. Discuss significant changes before silently overriding them.

## 6. Repository Hygiene

- Do not discard or overwrite uncommitted user changes.
- Do not rewrite unrelated files.
- Avoid broad formatting changes.
- Do not introduce dependencies without a clear benefit.
- Keep changes focused and easy to review.
- Do not commit unless explicitly requested.

## 7. Completion Report

Keep final responses concise.

Report:

1. What changed.
2. Which files changed.
3. What tests or checks were run and their results.
4. What remains unverified or requires manual testing.

Do not claim that something works unless it has been verified.

Do not repeat project background, narrate routine work or provide lengthy implementation explanations.