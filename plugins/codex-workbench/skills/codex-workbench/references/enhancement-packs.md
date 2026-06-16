# Enhancement Packs

Use this reference when a task needs capabilities beyond the core project workbench.

## Principle

Keep Codex Workbench as the single public entrypoint. Treat specialist skills as optional enhancement packs.

Do not make users pick specialist skills at the start. The public entrypoint is always:

```text
Use Codex Workbench ...
```

Codex Workbench should route the phase internally, then use optional enhancement packs only when they clearly improve the current step.

Do not bundle every specialist workflow into the core skill. Instead:

1. Detect what the task needs.
2. Prefer the core workbench path for intake, adapter generation, feature packages, quality gates, and review.
3. Use an installed specialist skill only when it directly improves the current task.
4. If the specialist skill is missing, continue with the core path and recommend the missing enhancement by category.

## Stage Routing

| Stage | Core artifact | Optional enhancement |
| --- | --- | --- |
| Project discovery | `PROJECT_INTAKE.md` | project-intake / clarification skills |
| Product planning | `workbench/product/` | technical documentation or project architecture skills |
| UX and prototype | `workbench/design/` | UI/UX, Figma, frontend design skills |
| Architecture | `workbench/architecture/` | architecture, enterprise AI, diagram skills |
| Delivery | `workbench/delivery/` | CI/CD or documentation skills |
| Feature work | `workbench/features/<feature-name>/` | language/framework/test skills |
| Verification and review | `workbench/quality/`, `scorecard/`, `review/`, `feedback/` | testing, CI, security, AI eval, review skills |

The user should not need to know these skill names. They describe the task; Codex Workbench decides the route.

## Categories

### UI And Design

Use for Figma, UI/UX, frontend visual design, design systems, component fidelity, or page polish.

Recommended skills when installed:

- `figma`
- `figma-use`
- `figma-implement-design`
- `figma-generate-design`
- `figma-generate-library`
- `frontend-design`
- `ui-ux-pro-max`

### Diagrams

Use for ER diagrams, architecture diagrams, sequence diagrams, flowcharts, UML, mind maps, and system visualizations.

Recommended skills when installed:

- `drawio-skill`

### Testing And CI

Use for unit tests, API tests, Playwright tests, AI system tests, Jenkinsfile, GitHub Actions, test planning, and CI quality gates.

Recommended skills when installed:

- `unit-testing`
- `api-testing`
- `playwright-automation`
- `ai-test-generation`
- `ai-system-testing`
- `ai-qa-review`
- `test-planning`
- `ci-cd-integration`
- `jenkinsfile-generator`
- `jenkinsfile-validator`

### Documentation And Writing

Use for README files, architecture docs, technical docs, Word documents, PDFs, PPTs, papers, and final delivery cleanup.

Recommended skills when installed:

- `technical-doc-writer`
- `docx`
- `docx-win`
- `pdf`
- `pptpro`
- `research-paper-writing`
- `checkpro`
- `final-delivery-clean`

### Enterprise AI Governance

Use for RAG, AI agents, model/tool workflows, evals, safety, OWASP LLM risks, NIST AI RMF, and enterprise release gates.

Recommended skills when installed:

- `enterprise-ai-app-lifecycle`
- `eval-driven-dev`
- `owasp-llm-top10`
- `nist-ai-rmf`
- `security-threat-model`
- `security-best-practices`

### Project Planning And Architecture

Use for deep project blueprints, architecture audits, tech debt, codebase reconnaissance, and structured planning.

Recommended skills when installed:

- `project-architect`
- `codebase-recon`
- `brooks-audit`
- `brooks-health`
- `brooks-debt`

## Recommendation Policy

Recommend enhancement packs only after a real task indicates a need.

Do not tell new users to install all packs. Use this wording:

```text
Codex Workbench can run by itself. For this task, the useful optional enhancement is: <category>.
```

If multiple categories apply, recommend the smallest set needed for the next step.