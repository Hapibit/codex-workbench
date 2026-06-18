# Project Intake Integration

Use this reference when adding or improving the preprocessing layer of a project workbench.

## External Patterns To Integrate

- GitHub Spec Kit: keep specifications as the center of AI-assisted development. Core flow is Spec -> Plan -> Tasks -> Implement, with templates, helper scripts, quality checklists, and cross-artifact analysis.
- Microsoft Spec Kit guidance: good context should be established before code because code is a binding artifact. Make requirements, motivations, technical choices, and assumptions explicit before implementation.
- Kiro-style workflow: use Requirements -> Design -> Task List -> Implementation with developer checkpoints. Requirements should include user stories and acceptance criteria, and hooks can automate quality gates.
- BMAD-style workflow: use progressive artifacts: analysis or product brief -> PRD -> architecture -> epics/stories -> implementation -> QA. Preserve context by passing durable artifacts from one phase to the next.

## Local Interpretation

Do not copy another tool's full process into this skill. The workbench should provide a lightweight, project-local preprocessing artifact that works even when the recipient has not installed Spec Kit, Kiro, or BMAD.

Use:

- `PROJECT_INTAKE.md` as the project-local evidence artifact.
- The bundled `scripts/intake.py` flow for producing, auditing, listing blockers, and confirming `PROJECT_INTAKE.md`.
- Minimal clarification conversations when repo evidence cannot answer blocking questions.
- Optional planning/architecture specialist skills for deep project planning when full specification and implementation docs are needed.
- Optional enterprise AI lifecycle specialist skills for AI/RAG/Agent projects that need risk, data, eval, security, and release gates.
- `FEATURE_WORKFLOW.md` and `workbench/features/<feature-name>/` for 2.0.0 feature work packages after the project image is clear.

## Required Project Intake Content

`PROJECT_INTAKE.md` should capture:

- one-sentence project goal,
- target users and non-users,
- first-version scope and explicit non-goals,
- core business flow and failure paths,
- data classes and permission boundaries,
- AI usage boundaries, human approval, data sources, privacy, and eval criteria,
- technical and delivery constraints,
- acceptance evidence,
- blocking questions,
- safe assumptions,
- downstream update checklist.

## Gate Behavior

Generated adapters may start with `PROJECT_INTAKE.md` as `status: draft`; this should not fail `validate` or make a newly generated adapter unshareable by itself.

However:

- `audit` should warn when project intake is draft, has default owner fields, or has open blockers.
- `audit` should fail with P1 if `DEVELOPMENT_FLOW.md` is confirmed while project intake is not confirmed.
- Generated `quality_gate.py` should fail when `PROJECT_INTAKE.md` is still draft or has open blocker rows.
- `DEVELOPMENT_FLOW.md` should not become confirmed until project intake is confirmed or unresolved blockers are explicitly documented as non-blocking.

## Avoid

- Do not force a full enterprise ceremony onto small bug fixes.
- Do not make recipients install Spec Kit, Kiro, BMAD, or optional planning skills just to use the generated workbench.
- Do not keep intake conclusions only in chat history.
- Do not treat Markdown checkboxes as hard gates unless a script, test, hook, CI job, or quality gate checks them.
