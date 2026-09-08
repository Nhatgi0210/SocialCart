# P3.1 — Create product requirements

> - **Role:** PRIMARY
> - **Skills:** `$prd-generator` (required), `$brainstorm` (conditional: scope or success criteria remain unclear)
> - **Interaction mode:** plan-then-approve
> - **Output mode:** interactive draft → approved artifact
> - **Approval gate:** approve the PRD before saving
> - **Canonical output:** `chapter-03-ai-for-requirements-product-analysis/docs/product-requirements.md`
> - **Sample correspondence:** [product-requirements.md](../docs/product-requirements.md)
> - **Run context:** fresh session; attach or provide every input below.

## Use this when

The project brief and portable context are approved, and you need a small, testable product boundary.

## Inputs

- Project brief: [project-brief.md](../../chapter-01-ai-in-software-engineering/docs/project-brief.md)
- Project context: [project-context.md](../../chapter-02-prompt-engineering/docs/project-context.md)
- Any newer human-approved product decision.

If a linked artifact is unavailable, ask for it. Do not infer product scope from the filename.

## Task

Use `$prd-generator` to draft a focused PRD. Include product goal, users, registration/login, success signals, scope, functional requirements, user stories, observable acceptance criteria, non-functional expectations, assumptions, and exclusions.

Use `$brainstorm` before drafting only when an unresolved choice materially changes scope. Present the PRD as a draft and wait for human approval; do not save a canonical PRD during the first response.

## Constraints and source precedence

1. Newer human-approved decisions.
2. Project context.
3. Project brief.
4. AI suggestions.

- Describe product behavior, not implementation tasks.
- Use `FR-*` and `US-*` identifiers only where they improve traceability.
- Keep authentication errors safe and resource isolation observable.
- Exclude MCP and unsupported enhancements.
- Report missing or conflicting source information instead of inventing it.

## Expected output

A concise draft PRD that product, design, engineering, and testing can review.

## Save or update

After human approval, write `chapter-03-ai-for-requirements-product-analysis/docs/product-requirements.md`; otherwise return complete Markdown for manual saving.

## Human review required

Approve scope, exclusions, success signals, and every requirement that would cause design or implementation work.

## Validation checklist

- Each requirement serves the core Kanban journey.
- Acceptance criteria are observable.
- Authentication, persistence, and authorization are explicit.
- Exclusions prevent feature expansion.
