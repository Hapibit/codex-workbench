# Recipient Setup Boundaries

Use this reference when the user asks whether the workbench plugin or skill can be shared with other developers.

## What Can Be Shared

- The `codex-workbench` plugin package.
- The `codex-workbench` entry skill.
- Internal scripts, templates, and references bundled inside the entry skill.
- Maintainer evidence under `docs/maintenance/` that explains why the workbench changed and how repeated failures are handled.
- Project adapter templates.
- Generated project files: `AGENTS.md`, `WORKBENCH.md`, `REVIEW.md`, and `workbench/`.
- Generic quality gate patterns.

## What Each Recipient Must Configure

- Codex installation and login.
- Their own `~/.codex/config.toml`.
- Their own MCP servers and credentials.
- Their own GitHub/Figma/Jenkins/OpenAI/Google authentication.
- Their own hook trust via `/hooks` after installing hooks.
- Their local toolchain: Node, pnpm/npm, Java, Maven, Docker, Python, draw.io, or anything the project needs.
- Environment variables such as API keys or Jenkins tokens.
- Python 3 for the generated cross-platform workbench scripts, or a deliberate project decision to replace those scripts with another portable runtime.
- Trust decisions for hooks and permission prompts. These cannot be safely pre-approved for another person.

## What Not To Share

- Personal access tokens.
- API keys.
- Cookies.
- Login state.
- Private local paths that only exist on the author's machine.
- `auth.json`, browser profiles, or secret-bearing config files.
- Machine-specific Codex approval state or hook trust state.
- `.workbench-validation/` reports unless the recipient explicitly asks for local validation evidence; these are generated artifacts, not reusable configuration.

## Installation Message For Recipients

Tell recipients:

1. Install the `codex-workbench` plugin package.
2. Restart Codex.
3. Open their project.
4. Ask Codex: "Use Codex Workbench to set up this project's AI workbench."
5. Review generated commands and paths before running quality gates.
6. Let Codex run or guide the workbench audit and fix `P0`/`P1` findings before relying on the adapter.
7. Configure optional MCP/auth and specialist skills only when the project actually needs them.
8. Run `python workbench/quality/quality_gate.py --profile standard` from the generated project adapter after installing the project's local toolchain.

## Optional Specialist Skills

Other people's skills are not required for basic workbench use. Treat them as optional capability packs:

- design/UI skills for Figma or frontend design tasks;
- diagram skills for ERD, architecture, sequence, and flow diagrams;
- testing skills for unit, API, Playwright, AI eval, or Jenkins pipelines;
- documentation skills for README, technical docs, Word, PDF, PPT, and papers;
- security skills for threat modeling, OWASP LLM, and secure code review.

The recipient should not need to learn these names up front. Recommend them only after the workbench detects a real project need.

## Shareability Standard

The shared package is only ready when:

- the visible entry skill validates with `quick_validate.py`;
- `workbench.py self-test` and `golden-test` pass;
- `doctor` and `package-check` pass and confirm `docs/maintenance/` exists;
- generated adapters avoid personal paths and secrets;
- recipient setup is documented as boundaries, not embedded credentials;
- project-specific quality commands are detected from the recipient's repo or confirmed by that recipient.
