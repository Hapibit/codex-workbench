# Quality Gate Patterns

Use this reference when creating or reviewing `workbench/` scripts for Codex Workbench 2.0.0.

## Principle

Markdown rules are guidance, not enforcement. Anything that must not be skipped should become one of:

- a deterministic script in `workbench/`;
- a package-manager script such as `test`, `lint`, `typecheck`, or `build`;
- a pre-commit or local hook;
- a CI job;
- a Codex hook that blocks supported high-risk behavior;
- branch protection / required status checks.

Codex hooks are useful early guardrails, but they are not a complete enforcement boundary. Keep mandatory acceptance in runtime gates, quality gates, tests, CI, and branch protection.

## Directory Layout

```text
workbench/
  quality/
    quality_gate.py
    quality-gate.ps1
    quality-gate.sh
  runtime/
    WORKFLOW_STATE.schema.json
    BYPASS_LOG.md
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
- Stop on hard failures.
- Check `PROJECT_INTAKE.md` for draft status and open project-intake blockers before success.
- Classify current `git diff` and controlled assets.
- Require an associated feature package for `standard` / `strict` controlled changes, or a valid machine-readable `workbench/delivery/CHANGE_LOG.md` entry for `light`.
- Check existing `workbench/features/<feature-name>/` packages for required 2.0.0 files and valid `FEATURE_STATUS.json`.
- Require `IMPACT_ANALYSIS.md` for `standard` and `strict`.
- Block implementation before `PLAN.md` / `TASKS.md` are ready.
- Require `VERIFY.md` to contain real evidence: command, report, screenshot, log, eval, CI, or human acceptance. For `strict`, an unverified path needs accepted risk, user confirmation, alternative verification, and follow-up.
- Block unresolved P0/P1 in `REVIEW.md`.
- Require `TRACEABILITY.md` update or explicit non-impact rationale for `strict`.
- Block completed, failed, blocked, or repeated-issue feature packages whose `REVIEW.md` still has `workbench_upgrade_assessment: unassessed`.
- Reject unknown `workbench_upgrade_assessment` values.
- Cross-check `FEATURE_STATUS.json`, Markdown status fields, git diff, and evidence files.
- Invalidate old `.workbench-validation/quality-gate-ok.json` when diff, active feature, verification evidence, review evidence, feature status, or critical baselines changed.
- Invoke `workbench/scorecard/scorecard.py --called-from-quality-gate --enforce-blockers` after deterministic checks pass when scorecard exists.
- Treat scorecard hard blockers and full-profile calibration/semantic-review blockers as failures.
- Treat reference score, component floor violations, low confidence, and incomplete semantic/architecture review as risk evidence unless the current profile explicitly promotes them to blockers.
- Create `.workbench-validation/`.
- Write `.workbench-validation/quality-gate-ok.json` only after all checks pass.
- Marker JSON should include `workbench_version`, timestamp, project root, selected profile, `git_head`, `diff_hash`, feature id, commands run, report id, `branch_protection`, and unverified paths.
- Treat `.workbench-validation/` as generated current-state evidence, not a long-term human-maintained log.
- Print each command before running it.
- Return non-zero on failed checks, missing configured commands, forged/stale status, or an empty code-project gate.

Profile intent:

- `smoke`: cheap local checks such as syntax, config, lint, or runtime gate.
- `standard`: normal day-to-day build/test/package validation.
- `full`: heavier e2e, integration, release, branch protection, or cross-service checks when configured.

If a code project has no checks for `smoke` or `standard`, `audit` should report it as a readiness issue.

Common checks by stack:

- Node frontend: package manager install already done, `npm run build`, `npm run lint`, `npm run test` only if scripts exist.
- pnpm frontend: `pnpm build`, `pnpm lint`, `pnpm test` only if scripts exist.
- Maven backend: `mvn test` or `mvn -DskipTests package`, depending on repo convention.
- Gradle backend: `gradlew test` or `gradlew build`.
- Python: `pytest`, `ruff`, `mypy` only if config/dependencies exist.

## `runtime_gate.py`

Required behavior:

- Default to dry-run plan.
- Generate or validate `.workbench-validation/workflow-state.json`.
- Include `git_head`, `diff_hash`, active feature, current stage, allowed actions, source hashes, and creation timestamp.
- Do not trust long-lived `workbench/runtime/WORKFLOW_STATE.json` as state.
- Require `--apply` before starting long-running services or writing generated state.
- Show commands and expected URLs.
- Avoid destructive cleanup unless explicitly requested.

## Wrappers

- `quality-gate.ps1` and `quality-gate.sh` should only locate Python and invoke `quality_gate.py`.
- `runtime-gate.ps1` and `runtime-gate.sh` should only locate Python and invoke `runtime_gate.py`.
- Do not duplicate gate logic across wrapper scripts.

## Audit

`workbench.py audit --project <repo>` must check:

- required adapter files exist;
- generated placeholders are resolved;
- generated Python scripts compile;
- `AGENTS.md` is not close to Codex's default project-instruction discovery limit;
- personal absolute paths are not embedded in shareable files;
- possible secrets or token-like values are absent;
- quality gate has non-empty checks for useful profiles;
- runtime schema and feature status schema exist;
- generation report exists;
- project intake is present, has valid status, and does not contradict a confirmed development flow;
- scorecard files are present and the quality gate invokes scorecard in advisory mode;
- `CALIBRATION.md` exists and has fields for anchor examples, human spot checks, false positives, false negatives, and reference-line changes;
- local pre-commit/hook framework and CI signals are present or explicitly absent;
- branch protection is `verified`, `unverified`, or `not_applicable`, not silently assumed.

Treat `P0` and `P1` audit findings as blockers before sharing the adapter.

Audit should not pretend a Markdown checklist is a hard gate. If the project has source code but no runnable checks, report a readiness issue and ask whether to add tests, linting, or CI.

## Bypass Tests

Any claim that a jump-flow path “will be blocked” needs a bypass golden test or equivalent verification.

Minimum scenarios:

- Missing `CHANGE_REQUEST.md`.
- Missing `IMPACT_ANALYSIS.md`.
- Implementation before plan.
- Forged `FEATURE_STATUS.json`.
- Stale gate marker.
- Empty `VERIFY.md`.
- Unresolved P0/P1.
- Local `--no-verify` path, covered by CI / branch protection or marked `unverified`.
- Branch protection not verified.

Without a passing test, reports should use `unverified` instead of claiming enforcement.

## `independent-review-prompt.md`

Include:

- Scope of changed files.
- Project rules to read.
- Review-only instruction.
- Severity format.
- Requirement to report missing tests, stale marker, unverified behavior, traceability gaps, and accepted-risk misuse.
