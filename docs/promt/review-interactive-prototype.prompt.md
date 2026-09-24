# P4.5 — Review the interactive prototype

> - **Role:** REVIEW GATE
> - **Skills:** `$product-design:audit` (required), `$frontend-expert` (supporting: assess implementation-state gaps)
> - **Interaction mode:** inspect-and-report
> - **Output mode:** review findings
> - **Approval gate:** human accepts corrections before the design record changes
> - **Updates:** `chapter-04-ai-for-product-design/docs/product-design.md` after human review
> - **Run context:** fresh session; attach or provide every input below.

## Use this when

The static prototype runs and you need observable UX, responsive, and accessibility findings before accepting it.

## Inputs

- Accepted design brief: [product-design-brief.md](../docs/product-design-brief.md)
- Selected design: [product-design.md](../docs/product-design.md)
- Running static prototype in [prototype](../prototype/).

## Task

Use `$product-design:audit` to capture and inspect the flow: login/register, validation, loading, keyboard submission, ticket creation from each entry point, editing, tags, status selection, drag, empty lanes, failure recovery, deletion, narrow view, focus order, and reduced motion.

For each confirmed issue, report evidence, impact, affected interaction, and the smallest correction. Use `$frontend-expert` to distinguish a visible defect from a state-handling or responsive implementation gap. Do not change the design record until findings are reviewed.

## Constraints and source precedence

1. Accepted design artifacts and human decisions.
2. Evidence captured in this review run.
3. AI suggestions.

- Do not report a preference as a defect.
- Do not redesign product scope or introduce backend behavior.

## Expected output

A prioritized review with accepted corrections, deferred risks, evidence limits, and explicit `Not run`/`Blocked` checks.

## Save or update

After human review, update `chapter-04-ai-for-product-design/docs/product-design.md` with accepted corrections and deferred risks only.

## Human review required

The human approves corrections and accepts any remaining risk before the prototype is treated as an accepted reference.

## Validation checklist

- Tickets remain scannable and controls remain understandable.
- Keyboard, narrow-view, and reduced-motion paths are usable.
- Failure states preserve user work and state the next action.
