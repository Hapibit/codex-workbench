# Workbench Maturity Model

Use this reference when the user asks whether a workbench is high quality, expert-grade, shareable, or worth improving.

## Expert Patterns To Apply

- Keep skills focused on one job with clear inputs and outputs.
- Use `SKILL.md` for procedure, `references/` for details, `assets/` for generated templates, and `scripts/` for deterministic checks.
- Inspect before writing, dry-run before applying, validate after writing, and audit before sharing.
- Ask only for decisions that cannot be discovered from the repo or safely inferred.
- Convert repeated or high-risk Markdown rules into scripts, tests, hooks, pre-commit, or CI.
- Define "done" in terms of behavior and verification, not only file creation.
- Treat every repeated AI mistake, failed gate, or review miss as input for the next workbench improvement.
- Before changing the workbench architecture or publishing a release, compare the design with current Codex official guidance for `AGENTS.md`, skills, plugins, hooks, MCP, and best practices.

## Levels

### L0: Prompt Notes

The workbench is only a loose prompt or Markdown note.

Signals:

- No project-local `AGENTS.md`.
- No quality gate.
- No review standard.
- No audit or validation.

Risk: the model can forget or skip most rules.

### L1: Project Adapter

The repo has project-local `AGENTS.md`, `PROJECT_INTAKE.md`, `WORKBENCH.md`, `REVIEW.md`, `DEVELOPMENT_FLOW.md`, `PRODUCT_BASELINE.md`, `FEATURE_WORKFLOW.md`, and SDD feature work package templates.

Required:

- Project identity and boundaries.
- Project intake that turns vague requirements into project goal, users, first-version scope, data permissions, AI boundaries, blockers, and acceptance evidence.
- Workflow and clarification rules.
- A project-specific development flow contract with `status: draft|confirmed`.
- A product baseline that defines the minimum usable product bar for individual developers.
- A feature workflow that turns larger work into SPEC, CLARIFY, PLAN, TASKS, DECISIONS, CHECKLIST, VERIFY, and REVIEW artifacts.
- Review severity model.
- Commands marked as detected, confirmed, or missing.

Risk: still mostly soft guidance.

### L1.5: Personal Product Floor

The workbench can guide a weaker individual developer through product-quality basics before code is written.

Required:

- `PRODUCT_BASELINE.md` defines user goal, main path, failure states, permissions, UI usability, verification evidence, and delivery notes.
- `PROJECT_INTAKE.md` is checked before confirming the development flow or creating high-risk feature work packages.
- `FEATURE_WORKFLOW.md` explains when to create an SDD feature work package and when small fixes may simplify.
- `FEATURE_WORKFLOW.md` includes a workload gate that checks hard triggers first, then scores impact, uncertainty, and rollback difficulty.
- Feature packages record `risk_level`, component scores, `risk_score`, `hard_triggers`, and `classification_reason`.
- Project workbench includes `workbench/scorecard/RUBRIC.md`, `SCORECARD.md`, and `CALIBRATION.md` to make evidence maturity, confidence, hard blockers, architecture review, semantic review, and score calibration visible.
- Single-feature failure evidence is recorded in the feature package, while repeated or cross-feature AI failures are summarized in `workbench/feedback/FAILURE_LOG.md`.
- `workbench/feature-template/` contains SPEC, CLARIFY, PLAN, TASKS, DECISIONS, CHECKLIST, VERIFY, and REVIEW templates.
- `workbench.py feature --project <repo> --name <feature>` can create `workbench/features/<feature>/` from the templates.

Risk: if feature packages are not used for real work, the baseline remains guidance rather than evidence.

### L1.7: State-Checked SDD Flow

The workbench makes process correctness visible and auditable before code is treated as done.

Required:

- Feature packages contain explicit state fields, not only prose checklists.
- Feature packages contain explicit risk classification fields, not only prose claims that a task is low risk.
- Feature packages contain explicit locations for validation failure, review findings, and AI-error-driven decisions.
- `CHECKLIST.md` has `feature_status`, `current_stage`, `implementation_allowed`, and `delivery_allowed`.
- `SPEC.md`, `CLARIFY.md`, `PLAN.md`, `TASKS.md`, `VERIFY.md`, and `REVIEW.md` each expose fields that show whether the phase is approved, ready, passed, failed, blocked, or still draft.
- Active incomplete feature packages are not silently treated as done.
- Parked work is explicitly marked `feature_status: on_hold`.
- Complete work requires passed verification and passed review evidence.
- Lightweight work is not forced through the full SDD package, but still requires problem/change/verification/risk evidence.

Risk: fields can still be edited dishonestly, so L2 must enforce them through quality gates.

### L2: Deterministic Gates

The repo has runnable `workbench/quality/quality_gate.py` and runtime smoke scripts.

Required:

- `smoke` and `standard` profiles.
- Non-empty checks for code projects.
- The quality gate blocks draft `PROJECT_INTAKE.md` or open project-intake blockers before writing success markers.
- The quality gate blocks active or complete feature packages that have not passed the SDD state checks.
- The quality gate blocks feature packages with missing risk classification evidence or risk scores that are inconsistent with the selected `risk_level`.
- `.workbench-validation/quality-gate-ok.json` written only after success.
- Wrappers for Windows and POSIX that only call the Python engine.
- Quality gate invokes `workbench/scorecard/scorecard.py --called-from-quality-gate --enforce-blockers` after deterministic checks pass and writes `.workbench-validation/scorecard-report.json`.
- Scorecard reports `decision`, `confidence`, calibration status, and component floor violations so total score cannot hide local weaknesses.
- Reference scores and component floors are audit signals; tests, quality-gate checks, hard blockers, CI, and human/independent review remain the actual gates.
- `full` profile requires calibrated scoring evidence and completed semantic/architecture review or explicit accepted risk.

Risk: local-only gates can still be skipped unless paired with hooks or CI.

### L3: Audit And Upgrade Loop

The adapter can validate itself and upgrade safely.

Required:

- `validate` checks required files, placeholders, Python syntax, and incomplete feature packages.
- `audit` detects missing gates, secrets, personal paths, weak validation, missing CI/pre-commit signals, draft or blocked project intake, unconfirmed development flow contracts, and unresolved feature-package clarification blockers.
- `upgrade --dry-run` preserves existing docs by default.
- `golden-test` covers representative project shapes.

Risk: still depends on users choosing the right project-specific quality commands.

### L4: Shareable Workbench Package

The skill and generated adapter can be handed to another developer without leaking personal setup.

Required:

- No personal paths, credentials, login state, cookies, tokens, or private URLs.
- Clear recipient setup boundaries.
- Cross-platform primary implementation.
- Versioned skill folder or reviewed distribution channel.
- Release package check validates plugin manifest, packaging manifest, visible skill surface, cache/internal exclusions, and personal-path/secret absence.
- P0/P1 audit findings fixed before sharing.

Risk: recipient must still configure their own Codex login, MCP auth, local toolchain, environment variables, and hook trust.

### L5: Measured Improvement Loop

The workbench improves from real usage instead of staying as static rules.

Required:

- Repeated failures are classified as requirement, implementation, test, review, tool, or rule gaps.
- Scorecard false positives, false negatives, and suspicious high-score/low-quality cases are recorded and used to adjust templates, reference lines, gates, CI, hooks, or review rules.
- Repeated failures have source feature-package evidence and a summary in `workbench/feedback/FAILURE_LOG.md`.
- Each completed, failed, blocked, or repeated-issue feature package records `workbench_upgrade_assessment` before it is treated as done, so Codex must explicitly decide whether the workbench needs a template, gate, review, CI, hook, or failure-log update.
- Workbench package self-upgrades have maintainer evidence in the plugin repository, not only in chat history or generated reports.
- Plugin maintainer evidence lives under `docs/maintenance/IMPROVEMENT_LOG.md`, `docs/maintenance/FAILURE_PATTERNS.md`, and `docs/maintenance/adr/`.
- `.workbench-validation/` is reserved for generated validation reports such as `package-check-report.json`; do not use it as the long-term human-maintained improvement log.
- Retention policy separates current machine reports, feature evidence, repeated failure summaries, and long-lived decisions so useful evidence is preserved without letting one file grow forever.
- Automatable gaps become tests, lint rules, pre-commit, CI, hooks, or quality-gate checks.
- Non-automatable business judgments stay in concise review rules with clear severity.
- `audit`, `self-test`, and `golden-test` are run before publishing changes to the workbench package.
- `doctor` and `package-check` must verify the maintainer evidence files before publishing a shareable plugin.

Risk: measurement can become ceremony if it does not lead to changed checks or clearer rules.

## Upgrade Priorities

1. If L0, create project adapter docs.
2. If L1, add deterministic quality/runtime/review gates.
3. If L2, add validate/audit/upgrade/golden tests.
4. If L3, remove personal assumptions and document recipient setup.
5. If L4, test the package on at least one clean project and one existing-project upgrade.
6. If L5, keep only the metrics and feedback notes that actually change rules, tests, gates, or review behavior.

## Red Flags

- `AGENTS.md` grows into a long tutorial instead of a compact rule entry.
- `AGENTS.md` approaches or exceeds Codex's default project-instruction discovery limit while detailed guidance could live in referenced docs.
- `PROJECT_INTAKE.md` remains draft while downstream documents are treated as confirmed.
- The generated `DEVELOPMENT_FLOW.md` is treated as confirmed before a project owner reviews it.
- User-visible features are implemented without SPEC/CLARIFY/PLAN/TASKS/VERIFY evidence even when the change is broad or high risk.
- Every small edit is forced through the complete feature package, causing process fatigue and skipped workflow evidence.
- AI can label a task as L1/L2 without recording hard-trigger checks, risk scores, or a classification reason.
- The product baseline describes quality ideals but does not force validation evidence.
- Quality gate exists but has zero checks.
- Review checklist has no severity model or output format.
- Templates contain the author's home directory or private service URLs.
- Generated files mention credentials that recipients cannot have.
- Upgrade overwrites existing project-specific docs by default.
- The final answer claims validation without running `validate`, `audit`, or the generated quality gate.
- Feedback notes accumulate but never become automated checks, clearer rules, or review criteria.
- Scorecard becomes a vanity metric: high totals are used to bypass unresolved blockers, low confidence, missing calibration, component floor violations, missing semantic review, or architecture risk.
- Workbench self-upgrade evidence exists only in `.workbench-validation/` or chat transcripts, so release decisions are not versioned with the plugin.
- Feature reviews close without `workbench_upgrade_assessment`, so AI failures never become workbench improvements.
- Logs and reports grow without retention categories, making agents read noisy evidence and hiding the current source of truth.