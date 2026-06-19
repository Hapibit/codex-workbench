# Project Adapter Template

Use this reference to create repository-local files for Codex Workbench 2.0.0. Generated text should be operational, concise, and specific to the repo. It should read like instructions for an AI coding agent, not like a marketing README.

## Adapter Principles

- Public workflow: `CLASSIFY -> BASELINE_CHECK -> CHANGE -> IMPACT -> ROUTE -> PLAN -> IMPLEMENT -> VERIFY -> REVIEW -> GATE -> LEARN -> DONE`.
- Profiles: `light`, `standard`, `strict`.
- Markdown explains context and evidence; generated JSON is a machine-readable state index; `quality_gate.py` is the local hard judge.
- Do not create `workbench/docs/` as a workbench phase directory.
- Do not claim a path is blocked unless a hook, runtime gate, quality gate, CI check, or bypass golden test proves it.

## `AGENTS.md`

Required sections:

- Project identity: name, type, root path, stack.
- Global inheritance: reference the user's global rules if available, but do not hardcode another person's absolute path in shared templates.
- AI read-first entry: `AGENTS.md`, `PROJECT_INTAKE.md`, `PROJECT_STATE.md`, `WORKBENCH.md`, `REVIEW.md`, `DEVELOPMENT_FLOW.md`, `PRODUCT_BASELINE.md`, `FEATURE_WORKFLOW.md`, then relevant `workbench/` scripts.
- Project intake entry: read `PROJECT_INTAKE.md`; if it is draft or has open blockers, do not treat project direction as confirmed.
- State-machine entry: meaningful work starts from `CHANGE_REQUEST.md` or a valid `light` record, then `IMPACT_ANALYSIS.md`, route, plan, implementation, verification, review, gate, learn.
- Requirements clarification rule: ask when scope, acceptance, permissions, data ownership, environment, or safety boundaries are missing.
- Done criteria: behavior satisfies the request, verification ran or is explained with accepted risk, no unresolved P0/P1, high-risk changes have rollback or residual-risk notes.
- Feedback loop: repeated failures or review findings should become project rules, templates, tests, lint, pre-commit, CI, hooks, or quality-gate checks.
- Project boundaries: source directories, generated files, forbidden areas, untrusted text sources.
- Quality gate rule: run `python workbench/quality/quality_gate.py --profile standard` after project code changes when available. Mention PowerShell and shell wrappers as convenience only.
- Marker rule: `.workbench-validation/quality-gate-ok.json` is valid only for the current `git_head`, `diff_hash`, feature, and evidence.

## `WORKBENCH.md`

Required sections:

- What this project workbench contains and what each file owns.
- 2.0.0 five-layer architecture and Agent Control control plane.
- Full state machine and stage entry/exit conditions.
- How `PROJECT_INTAKE.md` preprocesses vague requirements before high-risk work.
- How product, design, architecture, delivery, and feedback folders map to durable facts rather than chat history.
- How `PROJECT_STATE.md` acts as current fact index, not a long knowledge base.
- How `TRACEABILITY.md` maps requirement/design/API/AI IDs to implementation and verification.
- How `CHANGE_REQUEST.md` and `IMPACT_ANALYSIS.md` prevent full-document churn by updating only impacted baselines.
- How to choose `light`, `standard`, or `strict`.
- How to run quality gate on Windows/macOS/Linux.
- How `.workbench-validation/quality-workflow-state.json`, `.workbench-validation/runtime-state.json`, and `.workbench-validation/quality-gate-ok.json` are generated and invalidated.
- How scorecard works as advisory evidence audit, not as a pass/fail judge.
- How audit severities `P0` through `P3` are interpreted.
- How to run runtime gate and when `--apply` is allowed.
- How to request independent review.
- How `DEVELOPMENT_FLOW.md` is confirmed, what `draft` means, and why different projects may have different flows.
- How `PRODUCT_BASELINE.md` defines the minimum product quality bar for individual developers.
- How `FEATURE_WORKFLOW.md` and `workbench/feature-template/` define feature work packages.
- How single-feature failure evidence is stored in feature packages and repeated/cross-feature failures are summarized in `workbench/feedback/FAILURE_LOG.md`.
- How each feature review records `workbench_upgrade_assessment`.
- How evidence retention works: current machine reports stay in `.workbench-validation/`, feature evidence stays with feature packages, and long-lived decisions move to ADR or maintenance archives.
- How to upgrade an existing workbench without replacing project-specific docs.
- What recipient setup is required.
- What is not covered.

## `REVIEW.md`

Required sections:

- Review goal.
- Severity scale.
- Must-check business/domain boundaries.
- Security and data ownership checklist.
- Test and verification checklist.
- AI-generated code checklist: hallucinated APIs, bypassed project abstractions, missing validation artifacts, forged or stale status, Markdown-only gates.
- Review feedback loop: recommend automation when a finding can become a test, lint rule, CI check, hook, or quality gate.
- Output format for review findings.

## `DEVELOPMENT_FLOW.md`

Required sections:

- Metadata fields: `status: draft|confirmed`, `owner`, `confirmed_at`, `scope`, and `verification_commands`.
- Purpose: define this as a project-specific development process contract, not a global process.
- Status rules: `draft` is guidance only; `confirmed` may be followed for project work.
- Project intake dependency: `PROJECT_INTAKE.md` must be confirmed or explicitly marked non-blocking before this file is confirmed.
- Requirement clarification: what must be confirmed before implementation.
- Change-type flows: bugfix, feature, AI/RAG/agent, UI, backend/API, docs-only.
- Human confirmation checklist before changing status to `confirmed`.
- Maintenance rule: automate repeatable checks instead of keeping everything in Markdown.

## `PRODUCT_BASELINE.md`

Required sections:

- Product quality floor for individual developers.
- Dependency on `PROJECT_INTAKE.md` for project-specific users, scope, data, permissions, AI boundaries, and acceptance evidence.
- Minimum user-visible behavior: clear user goal, usable main path, understandable failures, data ownership, UI usability, verification evidence.
- Disqualifying signals: no validation, happy-path-only behavior, unhandled permissions, fake data, hardcoded secrets, Markdown-only gates.
- Acceptance questions that force the developer to reason about users, risks, and proof.
- Delivery floor: changed files, validation evidence, unverified risks, and follow-up workbench improvements.

## `PROJECT_STATE.md`

Required sections:

- Current project goal.
- Current version scope.
- Main modules.
- Technology stack.
- Run and validation commands, marked detected / confirmed / missing.
- Current phase.
- Active feature package.
- Critical constraints.
- Known risks.

Keep this file short. It is an index, not a replacement for PRD, UX, architecture, or delivery documents.

## `workbench/product/`

Required files:

- `PRODUCT_BRIEF.md`: product brief with business goal, target users, success metrics, first-version scope, non-goals, and iteration rule.
- `PRD.md`: product requirements with user stories, acceptance criteria, failure paths, non-goals, and change rule.
- `ROADMAP.md`: version roadmap with priorities, dependencies, and validation evidence.

## `workbench/design/`

Required files:

- `UX_SPEC.md`: interaction spec with user flows, page/component states, error/empty/loading/permission states, accessibility/usability checks, and iteration rule.
- `PROTOTYPE.md`: prototype reference with Figma/image/HTML/design links, page structure, and prototype acceptance.
- `USER_FLOW.md`: user flow map with entry, success path, failure path, and verification method.

## `workbench/architecture/`

Required files:

- `ARCHITECTURE.md`: architecture design with modules, boundaries, data flow, risks, constraints, and ADR reference.
- `DATA_MODEL.md`: entities, relationships, data ownership, permissions, and migration rules.
- `API_DESIGN.md`: API contracts, errors, authz, compatibility, and verification.
- `AI_DESIGN.md`: AI/RAG/agent inputs, outputs, tools, data sources, forbidden behavior, evals, and privacy.
- `adr/README.md`: ADR template with Context, Decision, Alternatives, and Consequences.

## `workbench/delivery/`

Required files:

- `CHANGE_LOG.md`: machine-readable light-change index with `change_id`, `scope`, `risk`, `validation`, `evidence`, `reviewer`, `gate_marker`, and `status`.
- `TRACEABILITY.md`: requirement/design/API/AI to implementation/verification matrix.
- `RELEASE_PLAN.md`: release scope, validation, rollback, and risk.
- `ITERATION_PLAN.md`: current iteration goal, scope, change handling, retest result, and next round.
- `TASK_BREAKDOWN.md`: task pool that traces work back to PRD, UX, architecture, and feature specs.
- `RELEASE_CHECKLIST.md`: release readiness, migration, environment, rollback, validation, and branch protection checks.

## `FEATURE_WORKFLOW.md`

Required sections:

- When to use the feature work package flow and when `light` can use `CHANGE_LOG.md` instead.
- Hard `strict` triggers.
- Dependency on `PROJECT_INTAKE.md` and relevant baselines before high-risk implementation.
- Target directory shape: `workbench/features/<feature-name>/`.
- Stage flow: `CHANGE_REQUEST.md` -> `IMPACT_ANALYSIS.md` -> `SPEC.md` -> `DESIGN.md` -> `PLAN.md` -> `TASKS.md` -> `DECISIONS.md` -> `IMPLEMENTATION_NOTES.md` -> implementation -> `VERIFY.md` -> `REVIEW.md` -> `CHANGELOG.md` -> `FEATURE_STATUS.json`.
- Human confirmation points for unclear requirements, high-risk plans, accepted risk, unverified delivery, and P0/P1 findings.
- Marker freshness rule for `.workbench-validation/quality-gate-ok.json`.

## `workbench/feature-template/`

Required files:

- `CHANGE_REQUEST.md`: target, reason, scope, non-goals, acceptance criteria, requester, and confirmation.
- `IMPACT_ANALYSIS.md`: impact on PRD, UX, API, DATA, AI, permissions, tests, release, rollback, traceability, and baseline updates.
- `SPEC.md`: feature-level incremental requirements, user goal, scope, input/output, permissions, acceptance criteria, failures, AI rules, questions.
- `DESIGN.md`: functional design with UX, architecture, data, API, permission, AI impact, risks, and approval gate before planning.
- `PLAN.md`: technical approach, affected files, data/API/UI/AI changes, risks, verification plan.
- `TASKS.md`: small executable tasks with verification notes.
- `DECISIONS.md`: durable architectural/product decisions and implementation deviations from the plan.
- `IMPLEMENTATION_NOTES.md`: AI implementation notes, deviations, problems, fixes, and retest evidence.
- `VERIFY.md`: command results, manual checks, browser/API/AI eval evidence, unverified items, residual risks.
- `REVIEW.md`: P0/P1 checks, product baseline checks, code quality checks, findings format, AI error evidence, `workbench_upgrade_assessment`, automation follow-up.
- `CHANGELOG.md`: requirement changes, implementation changes, retest results, and downstream file updates.
- `FEATURE_STATUS.schema.json`: schema for machine-readable feature status.

Generated feature packages also include `FEATURE_STATUS.json`.

## `workbench/runtime/`

Required files:

- `WORKFLOW_STATE.schema.json`: schema for generated workflow state.
- `BYPASS_LOG.md`: controlled bypass records with reason, scope, risk, user confirmation, expiry, and follow-up.
- `runtime_gate.py`: generates or checks `.workbench-validation/runtime-state.json`; quality gate writes `.workbench-validation/quality-workflow-state.json`.
- wrappers for Windows and POSIX.

Do not trust a long-lived `workbench/runtime/WORKFLOW_STATE.json` as the source of truth.

## `workbench/quality/`

Required files:

- `quality_gate.py`: deterministic local judge.
- `quality-gate.ps1` and `quality-gate.sh`: wrappers that only invoke the Python engine.

Required behavior:

- Check project intake status and blockers.
- Classify git diff and controlled assets.
- Require feature package or valid `light` record for controlled changes.
- Require `IMPACT_ANALYSIS.md` for `standard` / `strict`.
- Check `PLAN.md`, `TASKS.md`, `VERIFY.md`, `REVIEW.md`, `TRACEABILITY.md`, `FEATURE_STATUS.json`.
- Invalidate stale `quality-gate-ok.json`.
- Write marker only after all checks pass.

## `workbench/scorecard/`

Required files:

- `RUBRIC.md`: evidence-audit rules with weights, reference lines, hard blockers, and semantic-review boundary.
- `SCORECARD.md`: current project evidence-audit card.
- `CALIBRATION.md`: audit calibration record with anchor examples, human spot checks, false positives, false negatives, and reference-line change rationale.
- `scorecard.py`: deterministic evidence-maturity reporter invoked by the quality gate.

Scoring rules:

- Report evidence maturity and process consistency, not business truth.
- Treat hard blockers as failing regardless of total score.
- Output `decision`, confidence, calibration status, component floor violations, and profile rules so a high score cannot hide weak evidence.
- Require human or independent AI review for product correctness, UX quality, architecture reasonableness, AI eval quality, security/privacy judgment, and business acceptance.
- Use false-positive and false-negative records to adjust templates, reference lines, quality gates, CI, hooks, or review criteria.

## `workbench/feedback/`

Required files:

- `FAILURE_LOG.md`: repeated AI mistakes, quality gate failures, review misses, unclear requirements, insufficient verification, or workflow problems.
- `ITERATION_LOG.md`: change source, impacted layer, updated files, retest result, and next step.
- `AI_EFFECTIVENESS.md`: first-pass rate, rework count, review findings, quality gate failures, clarification count, and improvement action.

Single-feature evidence stays in feature package files first. Cross-feature or repeated problems move to `workbench/feedback/FAILURE_LOG.md`.

## `PROJECT_INTAKE.md`

Required sections:

- Metadata fields: `status: draft|confirmed`, `owner`, and `intake_updated_at`.
- One-sentence project goal.
- Users, roles, and non-users.
- First-version scope, non-goals, and later scope.
- Core business flow and failure paths.
- Data classes and permission boundaries.
- AI usage boundary, human approval, data sources, privacy, and eval criteria.
- Technical and delivery constraints.
- Quality and acceptance evidence.
- Blocking questions with `open|closed|deferred` status.
- Safe assumptions.
- Downstream update checklist for project state, product baseline, development flow, traceability, and first feature package.

## Writing Rules

- Use the project's language convention; otherwise use Chinese if the user is Chinese.
- Do not invent commands. Use commands from manifests, CI files, README, or user confirmation.
- If a command is inferred but unverified, mark it as unverified.
- Keep personal/global config separate from project config.
- Prefer portable paths and commands. Avoid writing another user's absolute home directory into shared templates.
- Keep generated project docs decoupled from implementation tools. Mention public workbench concepts and project-local scripts; avoid requiring users to know internal skill names.
- Keep `AGENTS.md` short enough to be reliably followed. Put detailed explanations in `WORKBENCH.md` or references.
- If a rule must not be skipped, pair it with a script, quality gate, pre-commit check, CI job, or Codex hook.
- Do not add process ceremony without a verification signal. Every workbench rule should either guide a decision, route to a tool, or create evidence.
- Do not ship a generated process as if it were confirmed by the team. Generated `DEVELOPMENT_FLOW.md` starts as `draft`.
- Do not rely on final-chat promises for workbench upgrades. Completed, failed, blocked, or repeated-issue feature work must leave `workbench_upgrade_assessment` in `REVIEW.md`.
