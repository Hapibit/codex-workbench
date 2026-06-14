# Upgrade Strategy

Use this reference when a repository already has some workbench files.

## Default Policy

- Prefer `upgrade --dry-run` before writing anything.
- Preserve existing `AGENTS.md`, `PROJECT_INTAKE.md`, `WORKBENCH.md`, `REVIEW.md`, `DEVELOPMENT_FLOW.md`, `PRODUCT_BASELINE.md`, and `FEATURE_WORKFLOW.md` by default.
- Add missing generated scripts under `workbench/`.
- Do not refresh existing generated scripts unless the user asks for `--refresh-generated`.
- Do not replace project documentation unless the user asks for `--replace-docs`.
- Treat `--replace-docs` as a high-risk action because project-specific rules may be lost even when backups exist.
- Content improvements should normally be proposed as a patch plan first. Apply them only when the user accepts replacing or editing project docs.

## Command Choices

- New project with no adapter: `generate --dry-run`, then `generate`.
- Existing partial adapter: `upgrade --dry-run`, then `upgrade --apply`.
- Existing stale generated scripts: `upgrade --dry-run --refresh-generated`, then `upgrade --apply --refresh-generated`.
- Full template reset after user approval: `upgrade --apply --replace-docs --refresh-generated`.

## Review Upgrade Reports

The upgrade report is written to `.workbench-validation/workbench-upgrade-report.json` after `--apply`.

Check:

- which existing docs were preserved;
- which missing files were added;
- whether `PROJECT_INTAKE.md` is still `draft`, has open blockers, or has been confirmed by the project owner;
- whether `DEVELOPMENT_FLOW.md` is still `draft` or has been confirmed by the project owner;
- whether product baseline and feature workflow files were added or preserved;
- whether generated scripts were refreshed;
- whether the adapter still has `P0` or `P1` audit findings.
- whether the adapter moved closer to the maturity level requested by the user.

## After Upgrade

Ask Codex Workbench to validate and audit the project workbench:

```text
Use Codex Workbench to validate this project workbench.
Use Codex Workbench to audit this project workbench.
```

If the project dependencies are installed, run:

```bash
python <repo>/workbench/quality/quality_gate.py --profile smoke
python <repo>/workbench/quality/quality_gate.py --profile standard
```

## Content Upgrade Checklist

When upgrading content rather than only files, check that:

- `AGENTS.md` has a concise read-first workflow, clarification rule, done criteria, quality gate rule, and hard boundaries.
- `PROJECT_INTAKE.md` captures project goal, users, first-version scope, data permissions, AI boundaries, blockers, assumptions, and downstream update checklist.
- `WORKBENCH.md` explains profiles, audit severities, runtime checks, independent review, recipient setup, and what is not covered.
- `REVIEW.md` has severity levels, business/domain boundary checks, security/data checks, AI-generated-code checks, and a concrete findings format.
- `DEVELOPMENT_FLOW.md` has status, owner, scope, confirmation timestamp, verification commands, clarification rules, change-type flows, and a human confirmation checklist.
- `PRODUCT_BASELINE.md` defines the minimum usable product bar and disqualifying signals.
- `FEATURE_WORKFLOW.md` explains feature work packages and confirmation points.
- `workbench/feature-template/` includes SPEC, CLARIFY, PLAN, TASKS, DECISIONS, CHECKLIST, VERIFY, and REVIEW templates.
- Any rule that must not be skipped has a corresponding script, test, hook, pre-commit, CI job, or explicit quality-gate gap.
