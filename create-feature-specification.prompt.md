# P3.3 — Create feature specification

> - **Role:** PRIMARY
> - **Skills:** `$prd-generator` (required), `$brainstorm` (conditional: behavior conflict or ambiguity)
> - **Interaction mode:** plan-then-approve
> - **Output mode:** interactive draft → approved artifact
> - **Approval gate:** approve behavior before saving
> - **Canonical output:** `chapter-03-ai-for-requirements-product-analysis/docs/feature-specification.md`
> - **Sample correspondence:** [feature-specification.md](../docs/feature-specification.md)
> - **Run context:** fresh session; attach or provide every input below.

## Use this when

The PRD has passed review and designers or developers need detailed behavior without guessing core rules.

## Inputs

- Accepted product requirements: [product-requirements.md](../docs/product-requirements.md)
- Project context: [project-context.md](../../chapter-02-prompt-engineering/docs/project-context.md)
- Any newer human-approved decision.

## Task

Use `$prd-generator` to specify registration/login, protected access, feature boundaries, business rules, the four-status lifecycle, main, alternative, and error flows, validation, persistent data, and required UI states. Reference `FR-*` and `US-*` identifiers where they clarify traceability.

Use `$brainstorm` only if behavior conflicts or an unresolved choice would alter the contract. Present a draft first and wait for human approval.

## Constraints and source precedence

1. Newer human-approved decisions.
2. Accepted PRD.
3. Project context.
4. AI suggestions.

- Stay solution-light except where an accepted product decision fixes behavior.
- Include direct movement with a status-control fallback.
- Exclude password reset, email verification, SSO, social login, and board-sharing UI/API.
- Report contradictions rather than resolving them silently.

## Expected output

A design- and implementation-ready feature specification.

## Save or update

After human approval, write `chapter-03-ai-for-requirements-product-analysis/docs/feature-specification.md`; otherwise return complete Markdown for manual saving.

## Human review required

Confirm success, failure, recovery, persistence, authorization, and destructive-action behavior before accepting the artifact.

## Validation checklist

- Every primary action has success and failure behavior.
- Destructive actions require intentional confirmation.
- Data survives reload.
- Unauthorized users cannot access unrelated boards or tickets.
