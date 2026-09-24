# P4.2 — Explore interface directions

> - **Role:** PRIMARY
> - **Skills:** `$brainstorm` (required: compare distinct design directions), `$frontend-expert` (required: keep concepts functional and comparable)
> - **Interaction mode:** plan-then-approve
> - **Output mode:** code change
> - **Approval gate:** human selects a direction before prototype work
> - **Canonical output:** `chapter-04-ai-for-product-design/design/concepts/`
> - **Run context:** fresh session; attach or provide every input below.

## Use this when

An accepted design brief exists and you need comparable directions before committing to a prototype.

## Inputs

- Accepted design brief: [product-design-brief.md](../docs/product-design-brief.md)
- Directly inspected interaction patterns and supplied visual references.
- Any human decisions about the concepts to compare.

## Task

Use `$brainstorm` to define three genuinely different visual systems while preserving one interaction contract. With `$frontend-expert`, create three self-contained coded concepts under `design/concepts/`; each must explain its rationale, interaction risks, and review notes.

Pause for human selection after the concepts are ready. Do not choose a winning direction yourself.

## Constraints and source precedence

1. Accepted design brief and human decisions.
2. Directly inspected references.
3. AI suggestions.

- Keep auth, ticket, lane, modal, status-control, direct-movement, and empty-lane behavior comparable.
- Do not reuse an earlier concept DOM/CSS structure.
- References are style constraints only; do not copy branding, layouts, or assets.
- Do not add metrics, filters, assignments, dates, AI controls, or unsupported behavior.

## Expected output

Three reviewable, self-contained concepts in `chapter-04-ai-for-product-design/design/concepts/`.

## Save or update

Create or update only concept files. The selected direction is recorded later by P4.3; do not update `product-design.md` before selection.

## Human review required

The human selects or requests revisions to a direction. Visual novelty is not sufficient evidence for selection.

## Validation checklist

- Concepts differ visually, not in product behavior.
- Auth, ticket editing, movement, and empty lanes are comparable.
- Each concept can be reviewed without guessing how it works.
