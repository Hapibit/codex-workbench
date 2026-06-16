# Codex Workbench

Codex Workbench 是一个给 Codex 使用的工作台插件。它不是再写一段提示词，而是把项目事实、流程、质量门和复盘证据放进仓库里，让 AI 开发可以长期复查、持续迭代。

安装后，普通用户只需要记住一个入口：

```text
Use Codex Workbench to set up this project's AI workbench.
```

## 它解决什么

AI 写代码快，但真实项目里经常慢在这些地方：

- 需求没确认，AI 先脑补。
- 规则只留在聊天记录里，下一轮又忘。
- 功能写完了，没有验收证据。
- Review 只看代码风格，不看边界、测试和回滚。
- 同类错误反复出现，却没有被沉淀成规则或门禁。

Codex Workbench 的目标，是把这些风险压到仓库文件和确定性检查里，让 AI 更难跳过关键步骤。

## 它会生成什么

在项目仓库里，它会生成一套项目工作台：

```text
AGENTS.md
PROJECT_INTAKE.md
WORKBENCH.md
REVIEW.md
DEVELOPMENT_FLOW.md
PRODUCT_BASELINE.md
FEATURE_WORKFLOW.md
workbench/
├── product/
├── design/
├── architecture/
├── delivery/
├── feature-template/
├── features/
├── quality/
├── runtime/
├── scorecard/
├── review/
└── feedback/
```

常见作用：

- `PROJECT_INTAKE.md`：先确认目标、用户、范围、数据、权限、验收。
- `WORKBENCH.md`：项目怎么走工作台流程。
- `REVIEW.md`：项目审查规则。
- `DEVELOPMENT_FLOW.md`：开发流程契约。
- `PRODUCT_BASELINE.md`：最低产品质量线。
- `FEATURE_WORKFLOW.md`：重要功能的工作包流程。
- `workbench/quality/`：质量门脚本。
- `workbench/feature-template/`：功能工作包模板。
- `workbench/feedback/FAILURE_LOG.md`：失败复盘与升级证据。

## 工作方式

默认流程是：

```text
Project Intake
-> Project Workbench
-> Feature Package
-> Quality Gate
-> Review
-> Feedback Loop
```

但它不是强制所有小改动都走全套。工作台会按风险和影响面决定强度：

- 小改动：轻量处理，直接验证。
- 中等影响：保留必要文档和验证证据。
- 高风险大影响：完整功能工作包、质量门、review。

如果项目已经做了一部分但需求变了，不是直接改代码。先更新对应事实源：

| 变化 | 先更新 |
| --- | --- |
| 项目目标、用户、第一版范围变化 | `PROJECT_INTAKE.md`、产品、UX、架构、交付计划 |
| 当前功能需求变化 | 功能包 `SPEC.md`、`CLARIFY.md` |
| 技术方案变化 | `DESIGN.md`、`DECISIONS.md`、必要时补 ADR |
| 验收标准变化 | `SPEC.md`、`VERIFY.md`、测试和质量门 |
| AI 实现偏离计划 | `IMPLEMENTATION_NOTES.md`、`DECISIONS.md`、`VERIFY.md` |

## 什么时候建功能包

建议创建功能工作包的情况：

- 新功能。
- 跨模块修改。
- 登录、权限、角色、租户、用户数据。
- 数据库 schema、迁移、批量数据修改。
- 公共 API、消息结构、SDK 或第三方集成。
- AI 输出会自动写入核心数据或影响用户权益。
- 生产部署、CI/CD、环境变量、不可逆操作。
- 需求不清但影响范围可能较大。

创建功能工作包：

```text
Use Codex Workbench to create a feature work package named <feature-name>.
```

## 先决条件

这个插件不会替你登录第三方服务，也不会分发作者的私人配置。使用者仍然要自己配置：

- Codex 安装和登录。
- 自己的 `~/.codex/config.toml`。
- MCP servers 和凭证。
- GitHub、Figma、Jenkins、OpenAI、Google 等账号权限。
- Node、Java、Maven、Docker、Python、浏览器、draw.io 等本机工具链。
- 项目的环境变量、API keys 和本地依赖。
- hook 信任、审批策略和权限决策。
- 项目自己的测试、lint、类型检查、构建和 CI 命令。

## 插件与 hook

发布包会携带默认 hook 目录 `hooks/`，用于在支持的 Codex 生命周期上提供本地门禁和阶段提醒。

安装后，使用者仍然需要在自己的 Codex 里 review/trust 这些 hook；插件不会替用户跳过这一步。

Codex 官方文档说明了这一点：

- 插件可以携带 `hooks/hooks.json`。
- 插件 hook 属于非 managed hooks。
- 安装或启用插件不会自动信任它的 hooks。

## 质量门和评分边界

工作台会生成 `workbench/quality/` 和 `workbench/scorecard/`，但它们的职责不同：

| 机制 | 负责什么 | 不负责什么 |
| --- | --- | --- |
| `quality_gate.py` | 调用项目可运行检查，如测试、lint、build、runtime smoke | 代替人工判断业务是否正确 |
| `scorecard.py` | 审计证据是否完整、状态是否一致、是否有硬阻塞 | 给产品质量、架构优劣或 UI 好坏下结论 |
| `REVIEW.md` | 检查 P0/P1/P2 风险、缺失测试、权限和回滚问题 | 代替 CI 或真实验收 |

只看总分是错误用法。工作台按这个顺序判断：

```text
decision
-> blockers
-> confidence
-> component floors
-> reference score
```

如果有 open blocker、质量门失败、高风险未确认，参考分再高也不能当作通过。

## 迭代升级

工作台升级必须从证据开始，不靠感觉改规则。

| 层级 | 触发条件 | 证据位置 | 结果 |
| --- | --- | --- | --- |
| 项目迭代 | 需求变化、功能返工、验证失败、用户反馈 | 项目内 `workbench/features/`、`workbench/feedback/`、`workbench/scorecard/CALIBRATION.md` | 更新项目事实、功能包、测试、review 或质量门 |
| 工作台机制升级 | 同类失败重复出现，说明模板、脚本、质量门或审查规则有缺口 | 插件内 `docs/maintenance/IMPROVEMENT_LOG.md`、`FAILURE_PATTERNS.md` | 修改模板、脚本、质量门、CI、hook 或文档 |
| 插件版本发布 | 升级会影响别人安装后的行为 | `plugin.json`、README、package-check 报告、维护日志 | 发布 patch/minor/major 版本 |

版本规则：

- `PATCH`：修文档、模板文字、脚本 bug，不改变公开工作流。
- `MINOR`：新增向后兼容能力、模板、文档或检查项。
- `MAJOR`：改变公开工作流、生成文件契约、命令行为或兼容性。

## 安装

把仓库添加为 Codex marketplace：

```bash
codex plugin marketplace add Hapibit/codex-workbench --ref main
```

安装插件：

```bash
codex plugin add codex-workbench --marketplace hapibit
```

默认安装 `main`，也就是当前最新版本。只有在复现实验、回滚问题或锁定生产环境时，才建议固定 tag：

```bash
codex plugin marketplace add Hapibit/codex-workbench --ref v1.2.0
codex plugin add codex-workbench --marketplace hapibit
```

## 第一次使用

进入项目根目录，然后对 Codex 说：

```text
Use Codex Workbench to set up this project's AI workbench.
```

它会按项目情况生成或更新这些文件：

```text
AGENTS.md
PROJECT_INTAKE.md
WORKBENCH.md
REVIEW.md
DEVELOPMENT_FLOW.md
PRODUCT_BASELINE.md
FEATURE_WORKFLOW.md
workbench/
```

## 常用入口

检查下一步：

```text
Use Codex Workbench to tell me the next step for this project.
```

审计已有工作台：

```text
Use Codex Workbench to audit this project workbench.
```

创建功能工作包：

```text
Use Codex Workbench to create a feature work package named <feature-name>.
```

## 可选用户工作台

项目工作台默认写进具体项目仓库。用户工作台写进 `~/.codex/`，会影响所有项目，因此必须由使用者显式安装。

预览：

```bash
python skills/codex-workbench/scripts/workbench.py user-workbench
```

确认后写入：

```bash
python skills/codex-workbench/scripts/workbench.py user-workbench --apply
```

如果目标文件已经存在，默认不会覆盖。确实要覆盖时：

```bash
python skills/codex-workbench/scripts/workbench.py user-workbench --apply --force
```

覆盖前会生成 `.bak-时间戳` 备份。说明见 [USER_WORKBENCH.md](docs/USER_WORKBENCH.md)。

## 可选增强能力

Codex Workbench 本身可以独立使用。其他 skill、MCP 或第三方工具只是在具体任务中增强能力，不是入门门槛。

| 任务 | 可选增强 |
| --- | --- |
| UI、Figma、前端还原 | UI/Figma 类 skill |
| ER 图、流程图、架构图、UML | diagram/draw.io 类 skill |
| 单元测试、接口测试、Playwright、AI 对话测试 | testing 类 skill |
| Jenkins、GitHub Actions、CI/CD | CI/Jenkins 类 skill |
| README、Word、论文、PPT、技术文档 | docs 类 skill |
| RAG、Agent、LLM eval、安全治理 | AI governance 类 skill |

查看当前机器有哪些增强包可用：

```bash
python skills/codex-workbench/scripts/check_enhancements.py --query "我要做 UI/Figma 和测试"
```

## 边界

Codex Workbench 不是：

- 业务需求的替代品。
- CI、测试、权限系统或人工验收的替代品。
- 私人账号、MCP 凭证、Figma/Jenkins/GitHub 登录态的分发工具。
- 保证 AI 永不出错的工具。

它的作用是把上下文、流程、质量门和复盘机制放到仓库里，让 AI 更难跳过关键步骤，也让人更容易审查 AI 做过什么。

## 维护者说明

普通使用者可以跳过这一节。

如果你要修改、打包或发布这个插件，再看：

```text
packaging-manifest.json
docs/maintenance/
skills/codex-workbench/
```

发布前至少运行：

```bash
python skills/codex-workbench/scripts/workbench.py package-check --plugin <plugin-root> --expected-version 1.2.0 --write-report
```

发布包应该只暴露一个可见 skill：

```text
codex-workbench
```

机器生成报告放在：

```text
.workbench-validation/
```

`.workbench-validation/` 只放机器报告，不放长期人工维护解释。

## 参考资料

- OpenAI Codex best practices: https://developers.openai.com/codex/learn/best-practices
- OpenAI Codex customization: https://developers.openai.com/codex/concepts/customization
- OpenAI Codex skills: https://developers.openai.com/codex/skills
- OpenAI Codex plugins: https://developers.openai.com/codex/plugins/build
- OpenAI Codex hooks: https://developers.openai.com/codex/hooks
- OpenAI agent improvement loop: https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop
- OpenAI Codex iterative repair loop: https://developers.openai.com/cookbook/examples/codex/build_iterative_repair_loops_with_codex
- SonarQube quality gates: https://docs.sonarsource.com/sonarqube-server/quality-standards-administration/managing-quality-gates/introduction-to-quality-gates
- Google SRE postmortem culture: https://sre.google/workbook/postmortem-culture
- Diataxis: https://diataxis.fr/
- GitHub README: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes
- Rubric design: https://teaching.unl.edu/resources/grading-feedback/design-effective-rubrics
- Semantic Versioning: https://semver.org
- Diataxis: https://diataxis.fr/
- GitHub README: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes
- Rubric design: https://teaching.unl.edu/resources/grading-feedback/design-effective-rubrics
- Semantic Versioning: https://semver.org
