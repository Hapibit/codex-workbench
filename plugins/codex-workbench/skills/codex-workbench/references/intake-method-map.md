# Intake Method Map

Use this reference when comparing project intake with public AI development workflows.

## What To Borrow

### Spec Kit

Borrow:

- define what and why before code,
- use specs as source of truth,
- split work into spec, plan, tasks, and implementation,
- use templates and scripts for consistency,
- keep artifacts in the project, not only in chat.

Map to `PROJECT_INTAKE.md`:

- one-sentence goal,
- users and success criteria,
- first-version scope,
- explicit non-goals,
- downstream feature SPEC and PLAN.

### Kiro-style Spec Workflow

Borrow:

- requirements before design,
- design before tasks,
- tasks before implementation,
- checkpoint each phase,
- use hooks or gates to validate changes.

Map to `PROJECT_INTAKE.md`:

- acceptance evidence,
- human confirmation points,
- blocker rows,
- quality gate requirement.

### BMAD

Borrow:

- analysis or product brief before PRD,
- PRD before architecture,
- architecture before stories,
- story files as focused implementation context,
- QA traces implementation back to requirements.

Map to `PROJECT_INTAKE.md`:

- project brief fields,
- first-version scope,
- business flow,
- architecture constraints,
- downstream feature package and review evidence.

### Enterprise AI Lifecycle

Borrow:

- business owner and system owner,
- intended and prohibited use,
- input data classes and output consumers,
- AI actions and approval requirements,
- risk, eval, logging, privacy, rollback, and monitoring.

Map to `PROJECT_INTAKE.md`:

- AI usage boundary,
- data and permissions,
- eval standard,
- human review point,
- release and rollback constraints.

## What Not To Borrow

- Do not require users to install every external workflow.
- Do not turn small bug fixes into large planning rituals.
- Do not generate PRD, architecture, and story files when a lightweight intake is enough.
- Do not mark project intake as confirmed without user or project evidence.
- Do not let chat history be the only source of truth.

## Recommended Routing

- Vague one-line idea: run the bundled intake flow first.
- Need full planning docs: finish intake, then optionally use a planning/architecture specialist skill if installed.
- AI/RAG/Agent app: finish intake, then optionally use an enterprise AI lifecycle specialist skill if installed.
- Existing workbench generation: use intake first, then run the bundled workbench generation or upgrade flow.
- Specific feature: use project intake first, then feature work package flow.
