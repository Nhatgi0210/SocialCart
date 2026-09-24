# P4.4 — Build the interactive prototype

> - **Role:** PRIMARY
> - **Skills:** `$frontend-expert` (required), `$brainstorm` (conditional: an approved interaction conflicts with implementation constraints)
> - **Interaction mode:** plan-then-approve
> - **Output mode:** code change
> - **Approval gate:** confirm the selected direction and any conflict before changing the prototype
> - **Canonical output:** `chapter-04-ai-for-product-design/prototype/`
> - **Run context:** fresh session; attach or provide every input below.

## Use this when

The human has selected a design direction and you need a disposable static prototype for interaction review.

## Inputs

- Accepted design brief: [product-design-brief.md](../docs/product-design-brief.md)
- Accepted direction: [product-design.md](../docs/product-design.md)
- User flow: [user-flow.mmd](../design/user-flow.mmd)
- Selected concept and human review notes.

## Task

Use `$frontend-expert` to build Login/Register and the ticket board with labelled auth fields, validation, loading, simulated auth, four statuses, lane/global ticket creation, a centered ticket modal, keyboard/touch status control, direct movement, compact empty lanes, and retry behavior for simulated failures.

Inspect the existing prototype before changing it. If an accepted interaction cannot be represented without a material compromise, use `$brainstorm` with the human and wait for a decision.

## Constraints and source precedence

1. Human-approved interaction decisions.
2. Accepted design artifacts.
3. Selected concept.
4. AI implementation preferences.

- Keep the prototype dependency-free and backend-free; reset state on reload.
- Preserve approved material, contrast, focus, narrow-lane, and reduced-motion rules.
- Do not copy reference assets or add unsupported behavior.

## Expected output

Updated `prototype/index.html`, `prototype/styles.css`, `prototype/mock-data.js`, and `prototype/app.js`.

## Save or update

Modify only the prototype files named above. Record design decisions separately through the review gate; do not silently redesign accepted behavior.

## Human review required

The human reviews the runnable prototype before it is treated as the accepted design implementation.

## Validation checklist

- Required interactions work without a backend.
- Failure states retain user input and offer a next action.
- Empty lanes, keyboard status selection, drag state, narrow view, and reduced motion are reviewable.
