# Workbench Improvement Log

本文件记录 `codex-workbench` 自身为什么升级、参考了什么证据、改了哪些文件、跑了哪些验证。它是长期维护证据，应该随插件源码一起版本化；不要把它放进 `.workbench-validation/`，后者只保存机器生成的临时报告。

## 使用规则

- 每次升级工作台规则、模板、脚本、门禁或发布结构，都新增一条记录。
- 记录要能回答：问题是什么、证据来源是什么、为什么这样改、改了哪些文件、验证结果是什么、还有什么后续动作。
- 如果某个决策会长期影响架构或发布边界，同时补一条 ADR。
- 如果同类失败重复出现，同时更新 `FAILURE_PATTERNS.md`。

## 记录模板

```text
### YYYY-MM-DD - 标题

问题：

证据来源：
- 用户反馈：
- 官方/外部资料：
- 本地失败证据：

决策：

变更文件：

验证结果：

后续动作：
```

## 记录

### 2026-06-14 - 强化功能工作包的可执行证据

问题：

工作台架构已经具备项目画像、产品下限、功能工作包、质量门和维护证据，但部分模板内容仍偏流程说明。真实开发时，AI 可能只按清单往下走，却没有把需求变更、验收证据、计划偏离、复测结果和审查结论写成可复查材料。

证据来源：

- 用户反馈：要求这次优化注重内容，不再只调整架构，并要求升级后经过复查。
- 官方/外部资料：
  - OpenAI Codex Best Practices: `https://developers.openai.com/codex/learn/best-practices`
  - OpenAI Codex Skills: `https://developers.openai.com/codex/skills`
  - OpenAI Codex ExecPlans: `https://developers.openai.com/cookbook/articles/codex_exec_plans`
  - Addy Osmani, How to write a good spec for AI agents: `https://addyosmani.com/blog/good-spec`
  - Jama Software, Spec-Driven Development for AI-Powered Engineering: `https://www.jamasoftware.com/blog/what-is-spec-driven-development-sdd-for-ai-powered-engineering`
  - AI agent code quality gates article: `https://dev.to/teppana88/how-i-validate-quality-when-ai-agents-write-my-code-481c`
- 本地失败证据：模板已有 SDD 文件和状态字段，但 SPEC 缺少事实源与变更同步要求，PLAN 缺少备选方案、回滚和未知项，TASKS 缺少输入输出证据位置，VERIFY/REVIEW 对验收证据和需求符合性的约束不够具体。

决策：

不改变工作台架构，不新增公开 skill，也不强制所有任务走完整 SDD。只强化模板内容，让项目画像和 SPEC 成为事实源，让 PLAN/TASKS/VERIFY/REVIEW 能回答“依据是什么、怎么证明、出了错怎么复测、重复失败沉淀到哪里”。

变更文件：

- `skills/codex-workbench/assets/PROJECT_INTAKE.template.md`
- `skills/codex-workbench/assets/project-adapter-template/PROJECT_INTAKE.md`
- `skills/codex-workbench/assets/project-adapter-template/PRODUCT_BASELINE.md`
- `skills/codex-workbench/assets/project-adapter-template/FEATURE_WORKFLOW.md`
- `skills/codex-workbench/assets/project-adapter-template/WORKBENCH.md`
- `skills/codex-workbench/assets/project-adapter-template/REVIEW.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feature-template/SPEC.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feature-template/CLARIFY.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feature-template/PLAN.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feature-template/TASKS.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feature-template/DECISIONS.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feature-template/CHECKLIST.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feature-template/VERIFY.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feature-template/REVIEW.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feedback/FAILURE_LOG.md`

验证结果：

- `self-test`：通过，生成 26 个项目工作台文件，验证通过，审计无 P0/P1。
- `golden-test`：通过，覆盖 node-vite、maven-basic、fullstack-compose、old-workbench-upgrade 四个用例，所有用例 passed。
- `doctor --plugin <plugin-root>`：通过，P0/P1/P2/P3 均为 0，确认个人 skill 与插件 skill 同步。
- `package-check --plugin <plugin-root> --expected-version 1.0.0 --write-report`：通过，P0/P1/P2/P3 均为 0，报告写入 `.workbench-validation/package-check-report.json`。
- 复查结论：模板未新增个人路径、密钥或私有 URL；新增内容集中在证据、变更同步、验证和审查，不改变工作台架构。Markdown 规则仍按“指导层”处理，未声称替代脚本、CI、hook 或质量门。
- Python 运行时仍输出 `Could not find platform independent libraries <prefix>`，但上述命令退出码均为 0。

后续动作：

- 如果复查发现模板太重，优先删减说明文本，不动质量门状态字段。
- 如果真实项目中再次出现“验证只写命令、没有验收证据”，考虑把 `VERIFY.md` 的证据表变成质量门检查。

### 2026-06-14 - 分离机器报告和工作台维护证据

问题：

之前只在发布检查后生成 `.workbench-validation/package-check-report.json`，但没有正式目录记录“工作台自身为什么升级、参考了什么资料、失败模式如何沉淀”。这会导致升级依据只停留在对话里，后续发布、复查或交给别人维护时无法追溯。

证据来源：

- 用户反馈：要求明确“工作台自身升级的证据放在哪里”，并质疑 `.workbench-validation/improvement-log.md`、`failure-patterns.md` 是否适配真实工作流。
- 官方/外部资料：
  - OpenAI Codex Skills: `https://developers.openai.com/codex/skills`
  - OpenAI Codex Customization: `https://developers.openai.com/codex/concepts/customization`
  - OpenAI Codex Build plugins: `https://developers.openai.com/codex/plugins/build`
  - Martin Fowler ADR: `https://martinfowler.com/bliki/ArchitectureDecisionRecord.html`
  - Google SRE Postmortem Practices: `https://sre.google/workbook/postmortem-culture/`
  - Datadog Incident Postmortem Practices: `https://www.datadoghq.com/blog/incident-postmortem-process-best-practices`
- 本地失败证据：插件根目录只有 `.workbench-validation/package-check-report.json`，缺少长期维护证据文件；`package-check` 也没有把维护证据列入发布前检查。

决策：

`.workbench-validation/` 只保存机器生成报告，例如 `package-check-report.json`。长期维护证据放在插件根目录 `docs/maintenance/`，包括 `IMPROVEMENT_LOG.md`、`FAILURE_PATTERNS.md` 和 `adr/`。发布检查必须验证这些文件存在，避免“证据驱动升级”再次退化成口头规则。

变更文件：

- `docs/maintenance/IMPROVEMENT_LOG.md`
- `docs/maintenance/FAILURE_PATTERNS.md`
- `docs/maintenance/adr/README.md`
- `packaging-manifest.json`
- `skills/codex-workbench/scripts/workbench.py`
- `skills/codex-workbench/references/workbench-maturity.md`
- `README.md`

验证结果：

- `doctor --plugin <plugin-root>`：通过，P0/P1/P2/P3 均为 0。
- `package-check --plugin <plugin-root> --expected-version 1.0.0 --write-report`：通过，报告写入 `.workbench-validation/package-check-report.json`，并列出 `maintenanceEvidence`。
- `self-test`：通过，生成 26 个项目工作台文件，验证通过，审计无 P0/P1。
- `golden-test`：通过，覆盖 node-vite、maven-basic、fullstack-compose、old-workbench-upgrade 四个用例。
- Python 运行时仍输出 `Could not find platform independent libraries <prefix>`，但上述命令退出码均为 0。

后续动作：

- 如果后续发现维护日志只写不改门禁，应把对应失败模式提升为 `package-check` 或 `doctor` 检查。
- 发布前复查 `docs/maintenance/**` 不包含个人路径、token、cookie、登录态或私有配置。
