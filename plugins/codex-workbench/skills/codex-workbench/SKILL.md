---
name: codex-workbench
description: One low-friction entrypoint for using the Codex project workbench. Use when a user wants to set up, run, explain, audit, share, or improve a Codex workbench without learning multiple underlying skills. Contains its own project-intake and workbench-generation scripts; optional specialist skills are used only when installed and clearly useful.
---

# Codex Workbench

Use this as the single user-facing entrypoint. The user should not need to know which internal skill to call, install, or configure.

## Prompt Language Policy

Use a bilingual split instead of making every prompt either English or Chinese:

- Keep this `SKILL.md`, plugin metadata, command names, file names, status fields, and script interfaces in English for stable triggering and distribution.
- Keep generated project-facing instructions in the user's language when the project template is localized. The bundled default project adapter is Chinese.
- Never translate file names, command names, status values, JSON keys, script flags, or quality-gate decisions.
- When a user asks in Chinese, explain workbench behavior in Chinese while preserving technical identifiers such as `PROJECT_INTAKE.md`, `PASS_WITH_RISK`, `quality_gate.py`, and `workbench_upgrade_assessment`.

## Mental Model

The workbench has one simple path. Keep the public path stable even if the internal skills or tools change:

```text
1. Understand the project
2. Establish product, UX, architecture, and delivery facts when the project is 0-to-1 or materially changing
3. Create or update the project workbench
4. Use feature work packages for meaningful changes
5. Run scorecard, quality gates, and review
6. Feed requirement changes, AI failures, and review misses back into specs, templates, tests, gates, scorecards, or automation
```

## Internal Engine

This skill is self-contained for the core workbench flow. Prefer its bundled scripts before calling other skills:

- Project intake: `scripts/intake.py`.
- Workbench generation, upgrade, feature package creation, validation, audit, self-test, and golden-test: `scripts/workbench.py`.
- Optional recipient user-workbench template install: `scripts/workbench.py user-workbench`.

Use the smallest route that fits:

- Vague project, new project, changed requirements, unclear users/scope/permissions/AI boundaries:
  use the bundled project intake script and `assets/PROJECT_INTAKE.template.md`.
- Need to generate, upgrade, validate, audit, or package a repository-local workbench:
  use the bundled workbench script and `assets/project-adapter-template/`.
- Need a full planning blueprint after intake:
  use `project-architect` only if installed and needed.
- AI/RAG/Agent project with data, risk, eval, security, or release gates:
  use `enterprise-ai-app-lifecycle` only if installed and needed.
- Need diagrams, UI, CI, Jenkins, tests, docs, or security:
  read `references/enhancement-packs.md`, then use the relevant specialist skill only when the task clearly requires it.

If an optional specialist skill is missing, continue with the built-in workbench path and tell the user that the specialist enhancement is unavailable. Do not block the workbench setup because a third-party or specialist skill is absent.

## Unified Stage Router

Keep `codex-workbench` as the only public entrypoint. Do not ask the user to choose between intake, product, UX, architecture, testing, or documentation skills before the workbench has routed the task.

When the user gives a project or workbench request, route internally:

| User need | Core workbench route | Required output or stop condition | Optional enhancement, only if installed and clearly useful |
| --- | --- | --- | --- |
| Project discovery, vague requirements, changed direction, unclear users/scope/data/permissions/AI boundaries | `scripts/intake.py`, `PROJECT_INTAKE.md`, `assets/PROJECT_INTAKE.template.md` | Confirm project facts or list blocker questions; do not start high-risk implementation while `PROJECT_INTAKE.md` is draft or has open blockers. | `project-intake-preflight`, `ask-questions-if-underspecified` |
| Product planning, PRD, first-version scope, user stories, acceptance criteria, roadmap | `workbench/product/PRODUCT_BRIEF.md`, `PRD.md`, `ROADMAP.md` | Produce or update product facts, acceptance criteria, non-goals, and version scope before feature work. | `technical-doc-writer`, `project-architect` |
| UX, prototype, user flow, page states, error/empty/loading/permission states | `workbench/design/UX_SPEC.md`, `PROTOTYPE.md`, `USER_FLOW.md` | Produce user flow, UI states, error/empty/loading behavior, and prototype evidence before user-visible implementation. | `ui-ux-pro-max`, `frontend-design`, `figma`, `figma-use`, `figma-generate-design` |
| Architecture, data model, API design, AI/tool boundaries, ADR | `workbench/architecture/ARCHITECTURE.md`, `DATA_MODEL.md`, `API_DESIGN.md`, `AI_DESIGN.md`, `adr/` | Produce module, data, API, AI-tool, permission, and rollback boundaries before cross-module or high-risk work. | `project-architect`, `enterprise-ai-app-lifecycle`, `drawio-skill` |
| Delivery planning, iteration plan, task breakdown, rollback | `workbench/delivery/RELEASE_PLAN.md`, `ITERATION_PLAN.md`, `TASK_BREAKDOWN.md` | Produce iteration scope, task split, validation plan, and rollback notes before scheduling meaningful implementation. | `technical-doc-writer`, `ci-cd-integration` |
| Feature implementation | `scripts/workbench.py feature`, `workbench/features/<feature-name>/` | Create or update the feature package, resolve open blockers, then implement only the agreed scope. | language/framework/test specialist skills as needed |
| Verification, review, scorecard, failure loop | `workbench/quality/`, `workbench/runtime/`, `workbench/scorecard/`, `workbench/review/`, `workbench/feedback/` | Run deterministic checks when available, write verification evidence, review risks, and record repeated failures for mechanism upgrades. | review, testing, CI, security, AI eval skills as needed |

Routing rules:

- The user should be able to say only "Use Codex Workbench..." or describe the phase in plain language.
- The assistant chooses the internal route and reads the necessary project files.
- If the current phase is unclear, inspect existing workbench files first, then ask the minimum blocker questions.
- If an enhancement skill is missing, continue with the core workbench artifact and mention the missing enhancement only as optional.
- Do not expose enhancement skills as setup prerequisites for new users.
- Do not start implementation while project discovery, product scope, UX/architecture boundaries, or high-risk blockers remain unresolved.

## Execution Contract

For every workbench task, follow this loop:

1. Identify the active project path and current session boundary. If the user says this session is for workbench configuration, keep that boundary for later short commands such as "start", "continue", "plan", "optimize", "install", "publish", or "review"; do not advance business-project code unless the user explicitly switches scope.
2. Inspect existing workbench state before choosing a stage: `PROJECT_INTAKE.md`, `AGENTS.md`, `WORKBENCH.md`, `FEATURE_WORKFLOW.md`, `workbench/features/`, `workbench/scorecard/`, and `.workbench-validation/` when present.
3. Select exactly one primary stage from the router table. Load only the reference files needed for that stage.
4. State blockers before edits. If users, scope, acceptance, data, permission, AI boundaries, or environment are unclear and materially affect the route, ask the minimum blocker questions.
5. Produce or update the stage artifact, then validate with the bundled script or project quality gate when available.
6. Report the next concrete step and any validation gap. Do not claim the workbench is a hard gate unless a script, hook, CI job, test, or quality gate enforces it.
7. If the user points out skipped rules, stage mismatch, or invented workbench layers, pause and perform deviation review before continuing.

Keep `SKILL.md` lean. Move detailed explanations to `references/`, deterministic behavior to `scripts/`, and reusable files to `assets/`.

## Decoupling Contract

Separate public workbench concepts from internal implementation tools:

- Public concepts: project intake, project workbench, feature work package, quality gate, runtime check, independent review, audit.
- 0-to-1 concepts: product brief, PRD, UX spec, prototype, user flow, architecture, data model, API design, AI design, delivery plan, scorecard, iteration log, AI effectiveness.
- Internal tools: bundled scripts, templates, references, optional specialist skills, MCP servers.
- Generated project files should mostly describe public concepts and project-local commands, not require users to know internal skill names.
- If an internal tool name is needed, keep it in plugin/skill docs or maintainer instructions, not as a prerequisite in project-local docs.
- The generated project workbench must keep a declared directory contract; invented layers such as `workbench/docs/` are invalid unless promoted through the template, script, and regression tests.
- The project workbench must remain usable as plain repository files plus local scripts.

## Default User Flow

When the user asks whether the plugin also configures the user's personal/global workbench:

1. Explain that the project workbench is default and safe to generate inside a repo.
2. Explain that user/global workbench files affect all projects and require explicit opt-in.
3. Offer the bundled generic template under `assets/user-workbench-template/`.
4. Preview with `python scripts/workbench.py user-workbench` before writing.
5. Use `--apply` only after explicit confirmation; use `--force` only when the user accepts replacing existing user config with backups.

When the user says "set up the workbench" or similar:

1. Identify the project path.
2. If project intent is unclear, run intake first.
3. Preview with `--dry-run` before writes when the command supports it.
4. Validate and audit.
5. Explain only the next action the user needs, not every internal skill.

When the user asks "what should I do next":

1. Check whether `PROJECT_INTAKE.md` exists and is confirmed.
2. Check whether the project adapter exists.
3. Check whether there are open feature packages.
4. Recommend one next step.

## What To Hide From New Users

Do not make new users learn:

- every installed skill name,
- Spec Kit, BMAD, or Kiro terminology,
- internal script details unless they ask,
- global Codex config details,
- optional MCP credentials.

Expose simple commands and artifacts:

- project intake,
- product/UX/architecture/delivery facts,
- project workbench,
- feature work package,
- quality gate,
- scorecard,
- review.

## Third-Party Skill Policy

Treat other people's skills as optional enhancement packs integrated through this workbench.

- Do not present third-party skills as required setup.
- Do not ask a new user to install a large skill list before the workbench can work.
- Recommend specialist skills only after the project workbench has identified a real need.
- When recommending optional skills, group them by purpose: design, diagrams, tests, CI, docs, security, AI eval.
- Prefer one sentence: "This project can run with Codex Workbench alone; these optional skills only improve specific tasks."
- To check local availability, run `python scripts/check_enhancements.py --query "<task text>"` from this skill folder.

## Required Boundaries

- This workbench does not configure private credentials, MCP auth, GitHub/Figma/Jenkins login, or local toolchains for recipients.
- Do not promise that installed rules are hard gates unless a script, hook, CI job, test, or quality gate enforces them.
- Do not start business project implementation from this skill unless the user explicitly changes session scope.
- If the user says this session is for workbench configuration, only handle rules, skills, MCP, hooks, templates, quality gates, plugins, package structure, release maintenance, and workbench documentation.
- Treat short follow-up commands as belonging to the current session boundary. If the boundary is ambiguous and the next action could touch business-project code, ask for the target scope before editing.

## Optional Skill Policy

Optional specialist skills are accelerators, not prerequisites.

The published plugin should expose only:

- `codex-workbench`

Everything else is optional.

## Bundled Script Commands

Run from this skill folder when direct script execution is useful:

```bash
python scripts/intake.py init --project <repo> --name <project-name> --dry-run
python scripts/intake.py audit --project <repo> --write-report
python scripts/workbench.py inspect --project <repo>
python scripts/workbench.py generate --project <repo> --name <project-name> --dry-run
python scripts/workbench.py upgrade --project <repo> --dry-run
python scripts/workbench.py feature --project <repo> --name <feature-name> --dry-run
python scripts/workbench.py validate --project <repo>
python scripts/workbench.py audit --project <repo>
python scripts/workbench.py retention --project <repo>
python scripts/workbench.py retention --project <repo> --apply --write-report
python scripts/workbench.py self-test
python scripts/workbench.py golden-test
python scripts/workbench.py doctor --plugin <plugin-root>
python scripts/workbench.py package-check --plugin <plugin-root> --expected-version <version> --write-report
python scripts/workbench.py user-workbench
python scripts/workbench.py user-workbench --apply
python scripts/check_enhancements.py --query "<task text>"
```

Use write-enabling or overwrite flags only after explicit user confirmation:

- `generate` and `feature` write by default; use `--dry-run` first when previewing.
- `upgrade` previews by default; use `--apply` to write after review.
- `retention` previews by default. With `--apply`, it only archives older machine-generated reports from `.workbench-validation/`; it does not delete or rewrite human-maintained evidence logs.
- Use `--force`, `--replace-docs`, or `--refresh-generated` only when the user explicitly accepts overwrite or refresh risk.
- `user-workbench` previews by default; use `--apply` only after explicit user confirmation because it writes to the recipient's global Codex config.

## Bundled References

Read only the relevant reference:

- `references/project-adapter-template.md`: adapter wording, required sections, and generated-doc quality rules.
- `references/project-intake-integration.md`: preprocessing layer and external method mapping.
- `references/quality-gate-patterns.md`: quality gate behavior and audit expectations.
- `references/recipient-setup-boundaries.md`: what recipients must configure themselves.
- `references/upgrade-strategy.md`: safe upgrade policy for existing projects.
- `references/workbench-maturity.md`: maturity model and expert-grade upgrade priorities.
- `references/intake-method-map.md`: comparison with Spec Kit, Kiro, BMAD, PRD flows, or "大神/别人怎么做".
- `references/enhancement-packs.md`: optional enhancement pack categories for UI/Figma, diagrams, testing/CI, docs, enterprise AI, and architecture.
