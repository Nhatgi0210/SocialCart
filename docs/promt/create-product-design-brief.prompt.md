# P4.1 — Create the product design brief

> - **Role:** PRIMARY
> - **Skills:** `$brainstorm` (required: clarify experience trade-offs), `$frontend-expert` (supporting: make states and accessibility concrete)
> - **Interaction mode:** plan-then-approve
> - **Output mode:** interactive draft → approved artifact
> - **Approval gate:** approve the interaction contract before saving
> - **Canonical output:** `chapter-04-ai-for-product-design/docs/product-design-brief.md`
> - **Sample correspondence:** [product-design-brief.md](../docs/product-design-brief.md)
> - **Run context:** fresh session; attach or provide every input below.

## Use this when

Accepted product behavior exists and you need a reviewable design contract before exploring visual directions.

## Inputs

- Product requirements: [product-requirements.md](../../chapter-03-ai-for-requirements-product-analysis/docs/product-requirements.md)
- Feature specification: [feature-specification.md](../../chapter-03-ai-for-requirements-product-analysis/docs/feature-specification.md)
- Human visual references, material references, and directly inspected interaction patterns.

If a named visual reference cannot be inspected, report the gap and ask for a usable file, URL, or description.

## Task

Use `$brainstorm` to challenge the user journey before choosing visual treatment. Draft a design brief covering the user struggle, login/register and session entry, ticket contract, four-status board, lane/global creation, centered create/edit modal, status fallback, direct movement, empty lanes, recovery, accessibility, responsive behavior, exclusions, and review gate.

Use `$frontend-expert` to identify required loading, empty, error, disabled, focus, keyboard, touch, narrow-view, and reduced-motion states. Present the draft and wait for approval.

## Constraints and source precedence

1. Human-approved product decisions.
2. Product requirements and feature specification.
3. Directly inspected references.
4. AI suggestions.

- References inform interaction and material patterns only; do not copy branding, layouts, or assets.
- Keep ticket terminology, four fixed statuses, title, optional description, and tags.
- Preserve keyboard/touch status control, direct drag with rollback/retry, and a backend-free prototype boundary.
- Exclude password reset, SSO, social login, dashboards, and unsupported controls.

## Expected output

An approved design brief that a concept explorer and prototype builder can follow without guessing core interaction behavior.

## Save or update

After approval, write `chapter-04-ai-for-product-design/docs/product-design-brief.md`; otherwise return complete Markdown for manual saving.

## Human review required

Approve behavior and recovery expectations before visual style. Resolve conflicts between a supplied reference and accepted product behavior explicitly.

## Validation checklist

- The proposal begins with user work, not visual style.
- Main, failure, and recovery states are observable.
- Accessibility and narrow-view behavior are explicit.
- Exclusions match product artifacts.
