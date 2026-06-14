# Project Adapter Template

Use this reference to create repository-local files. Keep generated text concise, operational, and specific to the repo. The generated docs should read like instructions for an AI coding agent, not like a marketing README.

## `AGENTS.md`

Required sections:

- Project identity: name, type, root path, stack.
- Global inheritance: reference the user's global rules if available, but do not hardcode another person's absolute path in shared templates.
- AI read-first entry: `AGENTS.md`, `PROJECT_INTAKE.md`, `WORKBENCH.md`, `REVIEW.md`, `DEVELOPMENT_FLOW.md`, `PRODUCT_BASELINE.md`, `FEATURE_WORKFLOW.md`, then relevant `workbench/` scripts.
- Project intake entry: read `PROJECT_INTAKE.md`; if it is draft or has open blockers, do not treat project direction as confirmed.
- Project flow entry: read `DEVELOPMENT_FLOW.md`; follow it only when `status: confirmed`, and ask before using a `draft` flow for feature or high-risk work.
- Default workflow: clarify, preserve user changes, follow existing patterns, verify, report residual risk.
- Requirements clarification rule: ask when scope, acceptance, permissions, data ownership, environment, or safety boundaries are missing.
- Done criteria: behavior satisfies the request, verification ran or is explained, no secrets/personal paths/debug noise, high-risk changes have rollback or residual-risk notes.
- Feedback loop: repeated failures or review findings should become project rules, tests, lint, pre-commit, CI, hooks, or quality-gate checks.
- Project boundaries: source directories, generated files, forbidden areas, untrusted text sources.
- Quality gate rule: run `python workbench/quality/quality_gate.py --profile standard` after project code changes when available. Mention PowerShell and shell wrappers as convenience only.
- Quality gate profiles: document `smoke`, `standard`, and `full` when the generated gate supports them.

## `WORKBENCH.md`

Required sections:

- What this project workbench contains and what each file owns.
- How `PROJECT_INTAKE.md` preprocesses vague requirements before development-flow confirmation or feature work.
- How to run quality gate on Windows/macOS/Linux.
- How to choose `--profile smoke|standard|full`.
- How to ask Codex Workbench to audit the project workbench when checking shareability or readiness.
- How to interpret audit severities `P0` through `P3`.
- How to run runtime gate and when `--apply` is allowed.
- How to request independent review.
- How `DEVELOPMENT_FLOW.md` is confirmed, what `draft` means, and why different projects may have different flows.
- How `PRODUCT_BASELINE.md` defines the minimum product quality bar for individual developers.
- How `FEATURE_WORKFLOW.md` and `workbench/feature-template/` define an SDD feature work package, with Codex Workbench as an optional automation layer.
- How to choose lightweight, medium, or heavyweight feature workflow so low-risk edits do not carry full SDD overhead.
- How to turn repeated failures into updated rules or automated checks.
- How single-feature failure evidence is stored in feature packages and repeated/cross-feature failures are summarized in `workbench/feedback/FAILURE_LOG.md`.
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
- AI-generated code checklist: hallucinated APIs, bypassed project abstractions, missing validation artifacts, Markdown-only gates.
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

## `FEATURE_WORKFLOW.md`

Required sections:

- When to use the feature work package flow and when small fixes may simplify it.
- A workload classification gate: check hard triggers first, then score impact, uncertainty, and rollback difficulty; unclear classification must escalate or ask.
- L1 lightweight tasks may skip full feature packages but still require problem/change/verification/risk notes; L2 tasks create partial feature evidence; L3 tasks require the full SDD package; L4 emergency/major tasks allow minimal stop-the-bleeding work but require post-fix verification, review, retrospective, and prevention automation.
- Dependency on `PROJECT_INTAKE.md` before writing feature SPEC files.
- Target directory shape: `workbench/features/<feature-name>/`.
- Stage flow: `SPEC.md` → `CLARIFY.md` → `PLAN.md` → `TASKS.md` → `DECISIONS.md` → `CHECKLIST.md` → implementation → `VERIFY.md` → `REVIEW.md`.
- Human confirmation points for unclear requirements, high-risk plans, unverified delivery, and P0/P1 findings.

## `workbench/feature-template/`

Required files:

- `SPEC.md`: risk_level, impact_score, uncertainty_score, rollback_score, risk_score, hard_triggers, classification_reason, user goal, scope, input/output, permissions, acceptance criteria, failures, AI rules, questions.
- `CLARIFY.md`: blocking questions, safe assumptions, confirmed facts, and a gate that prevents planning while blockers remain.
- `PLAN.md`: technical approach, affected files, data/API/UI/AI changes, risks, verification plan.
- `TASKS.md`: small executable tasks with verification notes.
- `DECISIONS.md`: durable architectural/product decisions and implementation deviations from the plan.
- `CHECKLIST.md`: stage gates for risk classification, spec completeness, clarification resolution, plan coverage, task quality, verification, and review.
- `VERIFY.md`: command results, manual checks, browser/API/AI eval evidence, unverified items, residual risks.
- `REVIEW.md`: P0/P1 checks, product baseline checks, code quality checks, findings format, AI error evidence, automation follow-up.

## `workbench/feedback/FAILURE_LOG.md`

Required sections:

- When to record repeated AI mistakes, quality gate failures, review misses, unclear requirements, insufficient verification, or workflow problems.
- Evidence location rule: single-feature evidence goes to `workbench/features/<feature-name>/VERIFY.md`, `REVIEW.md`, and `DECISIONS.md`.
- Cross-feature or repeated problems go to `workbench/feedback/FAILURE_LOG.md`.
- Failure entry template with source feature package, problem type, severity, symptom, root cause, fixed location, automation target, automation status, and review result.

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
- Downstream update checklist for product baseline, development flow, and first feature package.

## Writing Rules

- Use the project's language convention; otherwise use Chinese if the user is Chinese.
- Do not invent commands. Use commands from manifests, CI files, README, or user confirmation.
- If a command is inferred but unverified, mark it as unverified.
- Keep personal/global config separate from project config.
- Prefer portable paths and commands. Avoid writing another user's absolute home directory into shared templates.
- Keep generated project docs decoupled from implementation tools. Mention public workbench concepts and project-local scripts; avoid requiring users to know internal skill names.
- Keep `AGENTS.md` short enough to be reliably followed. Put detailed explanations in `WORKBENCH.md` or references.
- Keep `AGENTS.md` well below Codex's default project-instruction discovery limit. If it grows toward that limit, split rules by scope instead of expanding the entry file.
- If a rule must not be skipped, pair it with a script, quality gate, pre-commit check, CI job, or Codex hook.
- Do not add process ceremony without a verification signal. Every workbench rule should either guide a decision, route to a tool, or create evidence.
- Do not ship a generated process as if it were confirmed by the team. Generated `DEVELOPMENT_FLOW.md` starts as `draft`.
