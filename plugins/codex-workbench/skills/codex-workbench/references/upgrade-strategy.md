# Upgrade Strategy

Use this reference when a repository already has workbench files and needs a safe upgrade to Codex Workbench 2.0.0.

## Default Policy

- Prefer `upgrade --dry-run` before writing anything.
- Preserve existing `AGENTS.md`, `PROJECT_INTAKE.md`, `WORKBENCH.md`, `REVIEW.md`, `DEVELOPMENT_FLOW.md`, `PRODUCT_BASELINE.md`, and `FEATURE_WORKFLOW.md` by default.
- Add missing 2.0.0 files without replacing project-specific docs.
- Do not refresh existing generated scripts unless the user asks for `--refresh-generated`.
- Do not replace project documentation unless the user asks for `--replace-docs`.
- Treat `--replace-docs` as high risk because project-specific rules may be lost even when backups exist.
- Content improvements should normally be proposed as a patch plan first. Apply them only when the user accepts replacing or editing project docs.

## 2.0.0 Upgrade Goals

Upgrade should move the project toward:

- `PROJECT_STATE.md` as a concise current fact index.
- `workbench/delivery/TRACEABILITY.md` for requirement/design/API/AI to verification mapping.
- `workbench/delivery/CHANGE_LOG.md` for machine-readable `light` changes.
- `workbench/delivery/RELEASE_CHECKLIST.md` for release readiness.
- `workbench/runtime/WORKFLOW_STATE.schema.json`, generated `.workbench-validation/runtime-state.json`, and quality gate `.workbench-validation/quality-workflow-state.json`.
- `workbench/runtime/BYPASS_LOG.md` for controlled bypass records.
- Feature packages with `CHANGE_REQUEST.md`, `IMPACT_ANALYSIS.md`, `FEATURE_STATUS.json`, and no reliance on old checklist-only state.
- Quality gate markers that bind `git_head`, `diff_hash`, feature, evidence, commands, and branch protection state.

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
- whether 2.0.0 files were added: `PROJECT_STATE.md`, `TRACEABILITY.md`, `CHANGE_LOG.md`, `RELEASE_CHECKLIST.md`, `WORKFLOW_STATE.schema.json`, `BYPASS_LOG.md`, `CHANGE_REQUEST.md`, `IMPACT_ANALYSIS.md`, `FEATURE_STATUS.schema.json`;
- whether `PROJECT_INTAKE.md` is still `draft`, has open blockers, or has been confirmed by the project owner;
- whether `DEVELOPMENT_FLOW.md` is still `draft` or has been confirmed by the project owner;
- whether generated scripts were refreshed;
- whether existing feature packages need migration to `FEATURE_STATUS.json`;
- whether the adapter still has `P0` or `P1` audit findings;
- whether the adapter moved closer to the requested maturity target.

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

- `AGENTS.md` has a concise read-first workflow, session boundary, clarification rule, done criteria, quality gate rule, and hard boundaries.
- `PROJECT_INTAKE.md` captures project goal, users, first-version scope, data permissions, AI boundaries, blockers, assumptions, and downstream update checklist.
- `PROJECT_STATE.md` is concise and does not duplicate PRD, UX, architecture, or delivery docs.
- `WORKBENCH.md` explains 2.0.0 layers, state machine, profiles, traceability, marker freshness, audit severities, runtime checks, independent review, recipient setup, and what is not covered.
- `REVIEW.md` has severity levels, business/domain boundary checks, security/data checks, AI-generated-code checks, forged-state checks, and concrete findings format.
- `DEVELOPMENT_FLOW.md` has status, owner, scope, confirmation timestamp, verification commands, clarification rules, change-type flows, and human confirmation checklist.
- `PRODUCT_BASELINE.md` defines the minimum usable product bar and disqualifying signals.
- `FEATURE_WORKFLOW.md` explains `light` / `standard` / `strict`, strict triggers, feature work packages, and confirmation points.
- `workbench/feature-template/` includes `CHANGE_REQUEST.md`, `IMPACT_ANALYSIS.md`, `SPEC.md`, `DESIGN.md`, `PLAN.md`, `TASKS.md`, `DECISIONS.md`, `IMPLEMENTATION_NOTES.md`, `VERIFY.md`, `REVIEW.md`, `CHANGELOG.md`, and `FEATURE_STATUS.schema.json`.
- Any rule that must not be skipped has a corresponding script, test, hook, pre-commit, CI job, or explicit quality-gate gap.

## Safety Rules

- Do not delete old project evidence during upgrade unless the user explicitly confirms the exact path and intent.
- Do not turn a project-specific decision into a global plugin rule after one example.
- Do not claim CI or branch protection is enabled unless verified through GitHub API, `gh`, or CI environment.
- Do not treat `.workbench-validation/` as long-term maintainer evidence.
