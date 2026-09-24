# P4.3 — Critique and select an interface

> - **Role:** REVIEW GATE
> - **Skills:** `$product-design:audit` (required), `$brainstorm` (conditional: decision trade-off needs discussion)
> - **Interaction mode:** inspect-and-report
> - **Output mode:** review findings
> - **Approval gate:** human accepts the selected direction before recording it
> - **Updates:** `chapter-04-ai-for-product-design/docs/product-design.md` after approval
> - **Run context:** fresh session; attach or provide every input below.

## Use this when

You have comparable concepts and need evidence-based selection rather than aesthetic preference.

## Inputs

- Accepted design brief: [product-design-brief.md](../docs/product-design-brief.md)
- Concepts in [design/concepts](../design/concepts/)
- Human review notes or usability observations.

## Task

Use `$product-design:audit` to inspect the concepts and tie findings to observable states or screenshots. Compare auth clarity, error/loading states, scanability, status comprehension, creation, editing, keyboard/touch status control, direct movement, compact empty lanes, contrast, narrow layout, focus, reduced motion, and recovery.

Return findings and a recommendation. Use `$brainstorm` only if the human needs to weigh a real trade-off. Do not record a decision until the human approves it.

## Constraints and source precedence

1. Human observations and approved design brief.
2. Direct audit evidence.
3. AI preference.

- Compare ticket work, not novelty or glass intensity.
- Do not add features or alter behavior to make a concept win.
- Separate confirmed usability risks from taste.

## Expected output

A decision packet: evidence, recommendation, rejected alternatives, risks, mitigations, and open questions.

## Save or update

After approval, record the selected direction and accepted risks in `chapter-04-ai-for-product-design/docs/product-design.md`.

## Human review required

The human chooses the direction and accepts or defers each material risk.

## Validation checklist

- The selected direction supports the full interaction contract.
- Risks have a mitigation or explicit acceptance.
- The decision is understandable without the original conversation.
