# Workbench Maturity Model

Use this reference when the user asks whether a workbench is high quality, expert-grade, shareable, or worth improving.

## Expert Patterns

- Keep one visible skill entrypoint and hide internal complexity.
- Use `SKILL.md` for procedure, `references/` for details, `assets/` for generated templates, and `scripts/` for deterministic checks.
- Inspect before writing, dry-run before applying, validate after writing, and audit before sharing.
- Convert repeated or high-risk Markdown rules into scripts, tests, hooks, pre-commit, CI, or branch protection.
- Define done in terms of behavior and evidence, not file creation.
- Treat every repeated AI mistake, failed gate, stale marker, forged state, or review miss as input for the next workbench improvement.
- Before changing the architecture or publishing a release, compare the design with current Codex guidance for `AGENTS.md`, skills, plugins, hooks, MCP, and best practices.

## Levels

### M0: Prompt Notes

The workbench is only a loose prompt or Markdown note.

Signals:

- No project-local `AGENTS.md`.
- No quality gate.
- No review standard.
- No audit or validation.

Risk: the model can forget or skip most rules.

### M1: Project Adapter

The repo has project-local rules and basic workbench files.

Required:

- `AGENTS.md`, `PROJECT_INTAKE.md`, `WORKBENCH.md`, `REVIEW.md`, `DEVELOPMENT_FLOW.md`, `PRODUCT_BASELINE.md`, `FEATURE_WORKFLOW.md`.
- Project identity and boundaries.
- Project intake that captures project goal, users, first-version scope, data permissions, AI boundaries, blockers, and acceptance evidence.
- Review severity model.
- Commands marked as detected, confirmed, or missing.

Risk: still mostly soft guidance.

### M2: Baseline And Change State Machine

The workbench implements the 2.0.0 state-machine artifacts.

Required:

- `PROJECT_STATE.md`.
- Product, UX, architecture, and delivery baselines.
- `TRACEABILITY.md`.
- `CHANGE_LOG.md`.
- Feature template with `CHANGE_REQUEST.md`, `IMPACT_ANALYSIS.md`, `SPEC.md`, `DESIGN.md`, `PLAN.md`, `TASKS.md`, `DECISIONS.md`, `IMPLEMENTATION_NOTES.md`, `VERIFY.md`, `REVIEW.md`, `CHANGELOG.md`, and `FEATURE_STATUS.schema.json`.
- Generated feature packages include `FEATURE_STATUS.json`.
- `FEATURE_WORKFLOW.md` explains `CLASSIFY -> BASELINE_CHECK -> CHANGE -> IMPACT -> ROUTE -> PLAN -> IMPLEMENT -> VERIFY -> REVIEW -> GATE -> LEARN -> DONE`.
- `light`, `standard`, and `strict` profiles are defined.

Risk: state can still be edited dishonestly unless gates cross-check it.

### M3: Deterministic Gates

The repo has runnable quality/runtime gates.

Required:

- `workbench/runtime/WORKFLOW_STATE.schema.json`.
- `runtime_gate.py` generates `.workbench-validation/workflow-state.json`.
- `quality_gate.py` checks current git diff, feature status, Markdown evidence, traceability, review, and marker freshness.
- `.workbench-validation/quality-gate-ok.json` is written only after success and includes `git_head`, `diff_hash`, `feature_id`, `commands_run`, `created_at`, and branch protection status.
- Scorecard is invoked as advisory evidence audit and cannot override hard failures.
- Wrappers for Windows and POSIX only call the Python engine.

Risk: local-only gates can still be skipped unless paired with hooks or CI.

### M4: Control Plane And Remote Gates

The workbench adds local lifecycle controls and remote merge protection.

Required:

- `UserPromptSubmit` reminds session boundary and state machine.
- `PreToolUse` does coarse blocking for dangerous commands or obvious out-of-stage edits, using supported hook blocking behavior.
- `PermissionRequest` records risky approvals.
- `Stop` detects controlled edits without a fresh gate marker.
- `BYPASS_LOG.md` records reason, scope, risk, user confirmation, expiry, and follow-up.
- CI runs quality gate.
- Branch protection / required checks are verified or reported as `unverified`.
- Bypass golden tests prove specific jump-flow paths fail or become `unverified`.

Risk: hook coverage is not complete; final enforcement must remain in quality gate, CI, and branch protection.

### M5: Shareable Package And Measured Improvement

The workbench can be handed to another developer and improves from real usage.

Required:

- No personal paths, credentials, login state, cookies, tokens, or private URLs.
- Clear recipient setup boundaries.
- Release package check validates plugin manifest, packaging manifest, visible skill surface, cache/internal exclusions, and personal-path/secret absence.
- Only `codex-workbench` is visible as public skill.
- Repeated failures are classified as requirement, implementation, test, review, tool, state, gate, or rule gaps.
- Scorecard false positives, false negatives, and suspicious high-score/low-quality cases are recorded and used to adjust templates, gates, CI, hooks, or review rules.
- Each completed, failed, blocked, or repeated-issue feature package records `workbench_upgrade_assessment`.
- Maintainer evidence lives under `docs/maintenance/IMPROVEMENT_LOG.md`, `docs/maintenance/FAILURE_PATTERNS.md`, and `docs/maintenance/adr/`.
- `.workbench-validation/` is reserved for generated validation reports.
- Retention policy separates current machine reports, feature evidence, repeated failure summaries, and long-lived decisions.
- `audit`, `self-test`, `golden-test`, and `package-check` are run before publishing changes.

Risk: measurement can become ceremony if it does not lead to changed checks or clearer rules.

## Upgrade Priorities

1. If M0, create project adapter docs.
2. If M1, add 2.0.0 baseline, traceability, change request, impact analysis, and feature status.
3. If M2, add runtime/quality gates and marker freshness checks.
4. If M3, add hooks, CI, branch protection audit, and bypass tests.
5. If M4, remove personal assumptions and harden release packaging.
6. If M5, keep only metrics and feedback notes that actually change rules, tests, gates, or review behavior.

## Red Flags

- `AGENTS.md` grows into a long tutorial instead of a compact rule entry.
- `PROJECT_INTAKE.md` remains draft while downstream documents are treated as confirmed.
- `PROJECT_STATE.md` becomes a duplicate encyclopedia instead of a short current fact index.
- User-visible features are implemented without `CHANGE_REQUEST.md`, `IMPACT_ANALYSIS.md`, plan, verification, and review evidence when the change is broad or high risk.
- Every small edit is forced through the complete feature package, causing process fatigue.
- AI can label a task as `light` without a machine-readable `CHANGE_LOG.md` record.
- AI can hand-write `FEATURE_STATUS.json` and bypass quality-gate cross-checks.
- Old `.workbench-validation/quality-gate-ok.json` is reused after diff or evidence changed.
- The final answer claims validation without running `validate`, `audit`, or the generated quality gate.
- Scorecard becomes a vanity metric and is used to bypass unresolved blockers.
- Workbench self-upgrade evidence exists only in `.workbench-validation/` or chat transcripts.
- Feature reviews close without `workbench_upgrade_assessment`.
- Logs and reports grow without retention categories, hiding the current source of truth.
