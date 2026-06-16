# Quality Gate Patterns

Use this reference when creating `workbench/` scripts.

## Principle

Markdown rules are guidance, not enforcement. Anything that must not be skipped should become one of:

- a deterministic script in `workbench/`;
- a package-manager script such as `test`, `lint`, `typecheck`, or `build`;
- a pre-commit or local hook;
- a CI job;
- a Codex hook that blocks unsafe behavior.

The quality gate should be cheap enough to run after normal edits and explicit enough to tell the agent what failed.

Codex hooks are useful hard stops for supported lifecycle events and tool calls, but they are not a complete security boundary. Keep mandatory acceptance in project scripts, tests, CI, pre-commit, and quality gates; use hooks as an early warning or local enforcement layer.

## Directory Layout

```text
workbench/
  quality/
    quality_gate.py
    quality-gate.ps1
    quality-gate.sh
  runtime/
    runtime_gate.py
    runtime-gate.ps1
    runtime-gate.sh
  review/
    independent-review-prompt.md
  scorecard/
    scorecard.py
    scorecard.ps1
    scorecard.sh
    RUBRIC.md
    SCORECARD.md
    CALIBRATION.md
```

## `quality_gate.py`

Required behavior:

- Be the primary cross-platform implementation.
- Resolve project root from the script location.
- Run only commands that exist for the repo.
- Support `--profile smoke|standard|full`.
- Stop on first failure.
- Check `PROJECT_INTAKE.md` for draft status and open project-intake blockers before success.
- Check existing `workbench/features/<feature-name>/` packages for required SDD files and unresolved blocking clarifications.
- Block completed, failed, blocked, or repeated-issue feature packages whose `REVIEW.md` still has `workbench_upgrade_assessment: unassessed`.
- Reject unknown `workbench_upgrade_assessment` values so upgrade decisions use the controlled vocabulary in the feature template.
- Invoke `workbench/scorecard/scorecard.py --profile <profile> --write-report --called-from-quality-gate --enforce-blockers` after deterministic project checks pass and before writing the success marker.
- Treat scorecard hard blockers and `full` profile calibration or semantic-review blockers as quality-gate failures.
- Treat reference score, component floor violations, low confidence, and incomplete semantic/architecture review as risk evidence unless the current profile explicitly promotes them to hard blockers.
- Create `.workbench-validation/`.
- Write `.workbench-validation/quality-gate-ok.json` only after all checks pass.
- Include timestamp, project root, selected profile, and checks run in the marker JSON.
- Treat `.workbench-validation/` as generated current-state evidence, not a long-term human-maintained log. Long-term decisions and repeated failure patterns belong in feedback logs, maintenance docs, or ADRs.
- Print each command before running it.
- Return non-zero on failed checks, missing configured commands, or an empty code-project gate.

Profile intent:

- `smoke`: cheap local checks such as Docker Compose config, lint, type-check, and syntax checks.
- `standard`: normal day-to-day build/test/package validation.
- `full`: heavier e2e, integration, release, or cross-service checks when configured.

If a code project has no checks for `smoke` or `standard`, `audit` should report it as a readiness issue.

Common checks by stack:

- Node frontend: package manager install already done, `npm run build`, `npm run lint`, `npm run test` only if scripts exist.
- pnpm frontend: `pnpm build`, `pnpm lint`, `pnpm test` only if scripts exist.
- Maven backend: `mvn test` or `mvn -DskipTests package`, depending on repo convention.
- Gradle backend: `gradlew test` or `gradlew build`.
- Python: `pytest`, `ruff`, `mypy` only if config/dependencies exist.

## Wrappers

- `quality-gate.ps1` should only locate Python and invoke `quality_gate.py`.
- `quality-gate.sh` should only locate Python and invoke `quality_gate.py`.
- Do not duplicate quality-gate logic across wrapper scripts.

## Audit

`workbench.py audit --project <repo>` must check:

- required adapter files exist;
- generated placeholders are resolved;
- generated Python scripts compile;
- `AGENTS.md` is not close to Codex's default project-instruction discovery limit; keep the entry concise and move detail into `WORKBENCH.md` or referenced files;
- personal absolute paths are not embedded in shareable files;
- possible secrets or token-like values are absent;
- quality gate has non-empty checks for useful profiles;
- generation report exists;
- project intake is present, has valid status, and does not contradict a confirmed development flow;
- scorecard files are present and the quality gate invokes `scorecard.py` with `--called-from-quality-gate`;
- scorecard script outputs `decision`, confidence, calibration status, and component floor violations;
- `CALIBRATION.md` exists and has fields for anchor examples, human spot checks, false positives, false negatives, and reference-line changes;
- local pre-commit/hook framework and CI signals are present or explicitly absent.

Treat `P0` and `P1` audit findings as blockers before sharing the adapter.

Audit should not pretend a Markdown checklist is a hard gate. If the project has source code but no runnable checks, report a readiness issue and ask the user whether to add tests, linting, or CI.

## `runtime_gate.py`

Required behavior:

- Default to dry-run plan.
- Require `-Apply` before starting long-running services.
- Show commands and expected URLs.
- Avoid destructive cleanup unless explicitly requested.

Use `--apply` in Python and map PowerShell wrapper arguments to it when needed.

## `independent-review-prompt.md`

Include:

- Scope of changed files.
- Project rules to read.
- Review-only instruction.
- Severity format.
- Requirement to report missing tests or unverified behavior.
