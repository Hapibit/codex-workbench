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

### 2026-06-15 - 重写 README 的论证结构并补强评分/迭代解释

问题：

用户指出当前 README 仍然“不行”，尤其是为什么要这样搭建、每个流程靠什么保证、评分机制为什么这样设计、权重为什么这样分配、迭代升级什么时候发生和怎么升级，都没有讲清楚。原 README 虽然列出了流程和权重，但更像功能清单，缺少“依据 -> 机制 -> 证据 -> 校准 -> 发布”的论证链。

证据来源：

- 用户反馈：明确要求重新搜索相关资料进行优化，并指出文档结构、评分依据和迭代升级说明不足。
- 官方/外部资料：
  - OpenAI Codex best practices：稳定规则放进 `AGENTS.md`，复杂任务先规划，写清构建/测试/验证命令，重复流程沉淀为 skill/plugin。
  - OpenAI Codex customization：构建顺序是 `AGENTS.md`、plugin/skill、MCP、subagents；不要把所有事情混在一个提示词里。
  - OpenAI Codex skills/plugins：skill 是可复用流程，plugin 是分发单元；本工作台应只暴露一个用户入口。
  - OpenAI agent improvement loop：改进要来自 trace、反馈、eval 和可验证变更。
  - OpenAI Codex iterative repair loop：review、repair、validation 分离，验证失败成为下一轮修复输入。
  - SonarQube quality gates：质量门是明确条件的 pass/fail，不能被总分替代。
  - Rubric 设计资料：评分要有明确 criteria、公开权重、校准样例、误报/漏报记录，减少主观性和偏差。
  - Google SRE postmortem：失败复盘要记录事实、影响、根因、行动项和可验证完成标准。
  - Diataxis 与 GitHub README：README 负责快速理解和开始使用，长解释应放入独立文档。
- 本地失败证据：
  - README 中“评分和证据审计”“迭代升级怎么做”过短，不能说明评分合理性和升级触发机制。
  - `WORKFLOW_AND_SCORECARD.md` 解释了权重，但没有明确把公开资料原则映射到工作台机制。
  - `ITERATION_UPGRADE.md` 有流程，但缺少“什么时候算需要迭代”“怎么证明升级有效”“发布前检查口径”。

决策：

重写根 README 和发布包 README，把入口文档改成使用者能读懂的设计说明：先讲问题和依据，再讲生成内容、流程强度、每个流程靠什么保证、评分机制边界、权重分配、迭代升级和安装使用。补强 `WORKFLOW_AND_SCORECARD.md` 中的资料到机制映射、scorecard 保留但不当裁判的理由、评分可信度责任边界。补强 `ITERATION_UPGRADE.md` 中的升级信号、升级强度、升级有效性证明和发布前检查口径。

变更文件：

- 根仓库 `README.md`
- `plugins/codex-workbench/README.md`
- `plugins/codex-workbench/docs/WORKFLOW_AND_SCORECARD.md`
- `plugins/codex-workbench/docs/ITERATION_UPGRADE.md`
- `plugins/codex-workbench/docs/maintenance/IMPROVEMENT_LOG.md`

验证结果：

- README、workflow、iteration 文档关键词复检通过，确认包含设计依据、评分机制、默认参考权重、迭代升级、升级有效性证明和主要外部参考链接。
- `doctor --plugin <plugin-root>`：通过，P0/P1/P2/P3 均为 0。
- `self-test`：通过，生成 51 个项目工作台文件，验证通过；审计无 P0/P1。
- `golden-test`：通过，覆盖 node-vite、maven-basic、fullstack-compose、old-workbench-upgrade 四个用例。
- `package-check --plugin <plugin-root> --expected-version 1.1.0 --write-report`：通过，manifestVersion 为 `1.1.0`，可见 skill 只有 `codex-workbench`，P0/P1/P2/P3 均为 0。
- Python 运行时仍输出 `Could not find platform independent libraries <prefix>`，但上述命令退出码均为 0。

后续动作：

- 用真实项目试水时，重点观察两件事：用户是否仍把 scorecard 当质量证明；AI 是否仍跳过项目发现、需求澄清、验证和复盘。
- 如果仍出现误解，把相关说明升级为模板字段、质量门检查或 review blocker，而不是继续加长 README。

### 2026-06-15 - 补强迭代升级机制说明

问题：

README 和 `WORKFLOW_AND_SCORECARD.md` 已经提到反馈闭环和“什么情况必须升级工作台”，但没有把迭代升级作为独立机制讲清楚。用户指出“为什么没有讲述迭代升级那块”，并要求重新搜索资料优化。缺口主要是：项目迭代、工作台机制升级、插件版本发布三件事没有分开；也缺少升级证据、升级位置、验证方式和版本号判断。

证据来源：

- 用户反馈：明确指出迭代升级部分不足，要求搜索相关资料后优化。
- 官方/外部资料：
  - OpenAI agent improvement loop：traces、human feedback、evals 和 Codex 修改形成改进飞轮。
  - OpenAI Codex iterative repair loop：review、repair、validation 分离，每轮保存结构化记录，剩余 delta 成为下一轮输入。
  - Google SRE postmortem：失败复盘要有事实、根因、影响、具体 action item、owner、优先级和可验证完成标准。
  - Google SRE incident management：复盘 action items 进入 backlog，按可靠性和业务工作平衡优先级。
  - PDCA：Plan、Do、Check、Act，用小范围实验验证改进，再标准化。
  - Semantic Versioning：用 major/minor/patch 表达变更影响。
- 本地失败证据：
  - README 只有一句“反馈闭环”和一个三层表，没有形成完整升级流程。
  - `WORKFLOW_AND_SCORECARD.md` 只有升级触发条件和升级顺序，没有项目迭代、插件机制升级和版本发布的分层。
  - 发布清单没有专门的迭代升级说明文档。

决策：

新增 `docs/ITERATION_UPGRADE.md` 作为专门文档，明确三层迭代：项目迭代、工作台机制升级、插件版本发布。README 增加入口摘要，`WORKFLOW_AND_SCORECARD.md` 增加正式闭环并链接到专门文档，`packaging-manifest.json` 将新文档纳入发布包。

变更文件：

- 根仓库 `README.md`
- `plugins/codex-workbench/README.md`
- `plugins/codex-workbench/docs/WORKFLOW_AND_SCORECARD.md`
- `plugins/codex-workbench/docs/ITERATION_UPGRADE.md`
- `plugins/codex-workbench/packaging-manifest.json`
- `plugins/codex-workbench/docs/maintenance/IMPROVEMENT_LOG.md`

验证结果：

- 待运行 `package-check --expected-version 1.1.0 --write-report`。

后续动作：

- 后续真实项目试水时，按 `ITERATION_UPGRADE.md` 记录至少一次从失败证据到模板/质量门/scorecard 改进的完整闭环。

### 2026-06-15 - 重构 README 和 scorecard 权重解释

问题：

README 同时承载安装、工作流、评分、维护、发布和长篇设计依据，结构混杂；scorecard 权重只列出分值，缺少“为什么这样分配、为什么不是平均分、为什么验证只占 10 但仍是硬门禁、什么时候调权重、如何校准”的完整说明。用户明确指出文档结构和评分解释都不够科学。

证据来源：

- 用户反馈：要求搜索资料后优化整个文档结构，并重点解释评分机制和参考权重的合理性。
- 官方/外部资料：
  - GitHub README 文档：README 应说明项目做什么、为什么有用、如何开始，长文档应放到其他文档。
  - Diataxis：文档应按用户需求拆分为 tutorial、how-to、reference、explanation。
  - OpenAI Codex best practices：复杂/模糊任务先规划，规则沉淀到 `AGENTS.md` 或 skill，重复流程再自动化。
  - OpenAI Codex skills：skill 使用渐进披露，插件是可分发单元。
  - OpenAI / Anthropic eval 指南：分数不能单独代表质量，成功标准要具体、可测量，并结合人工校准。
  - SonarQube quality gates：质量门用明确条件给出 pass/fail，不靠一个总分替代门禁。
  - Brown University rubric guidance：rubric 要公开标准和权重，并通过样例、复核和校准降低偏差。
- 本地失败证据：
  - 根 README 和发布包 README 重复且过长，混合了用户入口、设计解释和维护说明。
  - `RUBRIC.md` 有权重表，但没有完整解释权重分配依据和校准方式。

决策：

按 README 入口、工作流解释、用户工作台说明、维护证据四类拆分文档。README 保留快速开始、生成内容、评分边界和关键权重说明；新增 `docs/WORKFLOW_AND_SCORECARD.md` 承载完整流程、评分、权重、校准和迭代解释；同步更新项目模板 `RUBRIC.md`，让生成到用户项目里的评分规则也具备同样解释。

变更文件：

- 根仓库 `README.md`
- `plugins/codex-workbench/README.md`
- `plugins/codex-workbench/docs/WORKFLOW_AND_SCORECARD.md`
- `plugins/codex-workbench/packaging-manifest.json`
- `skills/codex-workbench/assets/project-adapter-template/workbench/scorecard/RUBRIC.md`
- `docs/maintenance/IMPROVEMENT_LOG.md`

验证结果：

- 待运行 `package-check --expected-version 1.1.0 --write-report`。

后续动作：

- 用真实项目试水，观察用户是否仍会把 scorecard 当质量证明。
- 如果出现高分低质或低分可用，记录到 `CALIBRATION.md` 并调整权重、硬阻塞或脚本。

### 2026-06-15 - 发布版本提升到 1.1.0

问题：

工作台内容已经完成 0 到 1 流程、功能工作包、证据审计和质量门相关升级，但插件 manifest 仍停留在 `1.0.0`。这会让“本地内容已经升级”和“对外发布版本”不一致，后续安装、缓存和发布说明也容易混淆。

决策：

将发布插件 manifest 升级为 `1.1.0`，并同步 README 中固定版本安装和发布前 `package-check` 命令。历史维护日志中已经发生过的 `1.0.0` 验证记录保持不改，脚本测试样例 Maven 项目的 `<version>1.0.0</version>` 也保持不改，因为它不是插件版本。

变更文件：

- `.codex-plugin/plugin.json`
- `README.md`
- 根仓库 `README.md`
- `.workbench-validation/package-check-report.json`

验证结果：

- `package-check --plugin <plugin-root> --expected-version 1.1.0 --write-report`：通过，P0/P1/P2/P3 均为 0。
- 报告写入 `.workbench-validation/package-check-report.json`，其中 `expectedVersion` 和 `manifestVersion` 均为 `1.1.0`。
- Python 运行时仍输出 `Could not find platform independent libraries <prefix>`，但命令退出码为 0。

后续动作：

- 发布 Git tag 时使用 `v1.1.0`。
- 推送远程前再次确认发布包只暴露 `codex-workbench` 一个可见 skill。

### 2026-06-15 - 防止 scorecard 虚假高分

问题：

用户真正担心的是打分机制本身：如果 AI 能靠补空文档、改状态字段或忽略语义复核拿到高分，scorecard 就会制造幻觉式质量证明。工作台需要保留评分带来的可见性，但不能让分数变成可刷的目标。

证据来源：

- 用户反馈：要求“看一下能不能优化，搜索相关资料”，重点担心打分合理性和 AI 幻觉。
- 官方/外部资料：
  - Anthropic Agent Evals：`https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents`
  - SonarSource Quality Gate：`https://www.sonarsource.com/resources/library/quality-gate`
  - OWASP Risk Rating Methodology：`https://owasp.org/www-community/OWASP_Risk_Rating_Methodology`
  - Goodhart's Law in software metrics：`https://lawsofsoftwareengineering.com/laws/goodharts-law`
  - Rubric reliability / inter-rater reliability references from rubric-design searches.
- 本地失败证据：
  - `scorecard.py` 原先只输出总分、等级、硬阻塞和 warning，没有可信度、校准状态或组件下限。
  - `RUBRIC.md` 和 `SCORECARD.md` 原先没有独立的锚定样例、人工抽查、误报/漏报和阈值调整记录位置。
  - `full` 档原先没有强制校准和语义/架构复核通过。

决策：

不把分数做复杂，也不让 AI 给业务质量打分。scorecard 继续只评估“证据成熟度和流程一致性”，但新增可信度、校准状态和组件下限。`full` 档必须完成校准和语义/架构复核；`standard/full` 不能用总分掩盖单项严重短板。误报、漏报和被刷分案例进入 `CALIBRATION.md`，再反向改模板、脚本、质量门、CI、hook 或审查规则。

变更文件：

- `skills/codex-workbench/scripts/workbench.py`
- `skills/codex-workbench/assets/project-adapter-template/workbench/scorecard/RUBRIC.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/scorecard/SCORECARD.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/scorecard/CALIBRATION.md`
- `skills/codex-workbench/assets/project-adapter-template/WORKBENCH.md`
- `skills/codex-workbench/references/project-adapter-template.md`
- `skills/codex-workbench/references/quality-gate-patterns.md`
- `skills/codex-workbench/references/workbench-maturity.md`
- `docs/maintenance/FAILURE_PATTERNS.md`

验证结果：

- 待运行 `self-test`、`golden-test`、`doctor` 和 `package-check`。

后续动作：

- 用真实项目试水时记录 scorecard 误报/漏报。
- 如果分数被用户或 AI 当成“质量证明”，继续降低总分权重表达，强化 confidence 和 calibration 的展示。

### 2026-06-15 - 引入严格 scorecard 打分机制

问题：

工作台已经有项目预处理、0 到 1 产品/UX/架构层、功能工作包、质量门和审查规则，但缺少统一评分机制。没有分数时，用户很难判断当前项目工作台是“可继续开发、只能原型、还是不能交付”；但如果只做一个总分，又容易让 AI 用高分绕过硬阻塞、业务语义审查和架构合理性判断。

证据来源：

- 用户反馈：要求“引入严格的打分机制”，同时要求搜索资料并评估设计架构是否合理。
- 官方/外部资料：
  - CMU SEI ATAM：`https://www.sei.cmu.edu/library/architecture-tradeoff-analysis-method-collection`
  - JetBrains/Qodana quality gates：`https://www.jetbrains.com/pages/static-code-analysis-guide/quality-gates-in-software-development`
  - Anthropic agent evals：`https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents`
  - OWASP Risk Rating Methodology：`https://owasp.org/www-community/OWASP_Risk_Rating_Methodology`
  - ProductPlan PRD：`https://www.productplan.com/glossary/product-requirements-document`
  - Jama PRD guide：`https://www.jamasoftware.com/requirements-management-guide/writing-requirements/how-to-write-an-effective-product-requirements-document`
  - OpenAI Codex customization：`https://developers.openai.com/codex/concepts/customization#next-step`
  - OpenAI Codex skills：`https://developers.openai.com/codex/skills`
  - OpenAI Codex plugin structure：`https://developers.openai.com/codex/plugins/build#plugin-structure`
- 本地失败证据：项目模板没有 `workbench/scorecard/`，质量门无法检查“证据成熟度分数”，审计也不能发现 scorecard 是否被质量门跳过。

决策：

新增 `workbench/scorecard/` 层，但不把它做成新的公开 skill，保持插件只有 `codex-workbench` 一个入口。scorecard 只做可脚本判断的证据成熟度和状态一致性检查；产品目标、UX、架构合理性、AI eval 和安全/隐私等语义判断必须写入 `SCORECARD.md`，不能由脚本假装判断。质量门必须调用 scorecard，审计发现没有调用时给 `P1 scorecard-not-enforced`。

变更文件：

- `skills/codex-workbench/SKILL.md`
- `skills/codex-workbench/scripts/workbench.py`
- `skills/codex-workbench/references/project-adapter-template.md`
- `skills/codex-workbench/references/quality-gate-patterns.md`
- `skills/codex-workbench/references/workbench-maturity.md`
- `skills/codex-workbench/assets/project-adapter-template/AGENTS.md`
- `skills/codex-workbench/assets/project-adapter-template/WORKBENCH.md`
- `skills/codex-workbench/assets/project-adapter-template/REVIEW.md`
- `skills/codex-workbench/assets/project-adapter-template/PRODUCT_BASELINE.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/scorecard/RUBRIC.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/scorecard/SCORECARD.md`
- `packaging-manifest.json`

验证结果：

- 个人 skill `self-test`：通过，生成 50 个项目工作台文件，验证通过，审计无 P0/P1。
- 个人 skill `golden-test`：通过，覆盖 node-vite、maven-basic、fullstack-compose、old-workbench-upgrade 四个用例，确认 scorecard 文件生成且质量门调用 scorecard。
- 发布包待完成最终 `self-test`、`golden-test`、`doctor` 和 `package-check` 复检。
- Python 运行时仍输出 `Could not find platform independent libraries <prefix>`，但个人 skill 验证命令退出码为 0。

后续动作：

- 在真实项目试水时观察 scorecard 阈值是否过严或过松。
- 如果用户把分数当成业务正确性证明，需要强化 `SCORECARD.md` 的语义/架构复核提示或审查规则。
- 如果本机同步残留目录仍存在，发布时必须按 `packaging-manifest.json` 排除 `assets/assets/**`、`references/references/**` 和 `scripts/scripts/**`。

### 2026-06-15 - 升级为可迭代 AI 产品开发工作台

问题：

项目工作台已有项目预处理、功能工作包、质量门和审查规则，但 0 到 1 项目缺少标准产品开发前置层。用户指出业务规划、架构设计、原型设计、AI 写完后的审查、修改后的效果评估都需要流程化；原先只补 `BUSINESS_PLAN.md`、`UX_FLOW.md` 这类文件名不够标准，也没有形成可迭代闭环。

证据来源：

- 用户反馈：指出 `PROJECT_INTAKE.md`、`BUSINESS_PLAN.md`、`PRD.md`、`ARCHITECTURE.md`、`UX_FLOW.md`、`PROTOTYPE.md` 不符合标准开发流程，并要求可迭代版本。
- 官方/外部资料：
  - GitHub Spec Kit quickstart: `https://github.github.com/spec-kit/quickstart.html`
  - GitHub Spec Kit SDD concepts: `https://github.github.com/spec-kit/concepts/sdd.html`
  - Kiro specs: `https://kiro.dev/docs/specs`
  - BMAD getting started: `https://github.com/bmad-code-org/BMAD-METHOD/blob/main/docs/tutorials/getting-started.md`
  - Martin Fowler on SDD tools: `https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html`
- 本地失败证据：`assets/project-adapter-template/` 只生成根级 PROJECT_INTAKE、PRODUCT_BASELINE、FEATURE_WORKFLOW 和功能包模板；没有 `workbench/product/`、`workbench/design/`、`workbench/architecture/`、`workbench/delivery/`；功能包也没有 `DESIGN.md`、`IMPLEMENTATION_NOTES.md`、`CHANGELOG.md`。

决策：

保留一个公开 skill 入口，不引入强制第三方工具。把项目工作台升级为标准 0 到 1 流程：项目发现 -> 产品简报 -> PRD -> UX/原型 -> 架构设计 -> 交付计划 -> 功能包开发 -> 验证审查 -> 迭代复盘。根级文件保持兼容，新增标准目录作为项目内长期事实源。功能包流程从 SPEC -> CLARIFY -> PLAN 改为 SPEC -> CLARIFY -> DESIGN -> PLAN，并记录 AI 实现、修改后效果和需求变化。

变更文件：

- `skills/codex-workbench/SKILL.md`
- `skills/codex-workbench/scripts/workbench.py`
- `skills/codex-workbench/references/project-adapter-template.md`
- `skills/codex-workbench/assets/project-adapter-template/AGENTS.md`
- `skills/codex-workbench/assets/project-adapter-template/WORKBENCH.md`
- `skills/codex-workbench/assets/project-adapter-template/PROJECT_INTAKE.md`
- `skills/codex-workbench/assets/project-adapter-template/PRODUCT_BASELINE.md`
- `skills/codex-workbench/assets/project-adapter-template/FEATURE_WORKFLOW.md`
- `skills/codex-workbench/assets/project-adapter-template/REVIEW.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/product/*`
- `skills/codex-workbench/assets/project-adapter-template/workbench/design/*`
- `skills/codex-workbench/assets/project-adapter-template/workbench/architecture/*`
- `skills/codex-workbench/assets/project-adapter-template/workbench/delivery/*`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feature-template/DESIGN.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feature-template/IMPLEMENTATION_NOTES.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feature-template/CHANGELOG.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feedback/ITERATION_LOG.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feedback/AI_EFFECTIVENESS.md`

验证结果：

- 个人 skill `self-test`：通过，生成 45 个项目工作台文件，验证通过，审计无 P0/P1。
- 个人 skill `golden-test`：通过，覆盖 node-vite、maven-basic、fullstack-compose、old-workbench-upgrade 四个用例。
- 发布包 skill `self-test`：通过，生成 45 个项目工作台文件，验证通过，审计无 P0/P1。
- 发布包 skill `golden-test`：通过，覆盖四个用例，所有用例 passed。
- `doctor --plugin <plugin-root>`：通过，P0/P1/P2/P3 均为 0，确认个人 skill 与插件 skill 同步。
- `package-check --plugin <plugin-root> --expected-version 1.0.0 --write-report`：通过，P0/P1/P2/P3 均为 0，报告写入 `.workbench-validation/package-check-report.json`。
- Python 运行时仍输出 `Could not find platform independent libraries <prefix>`，但上述命令退出码均为 0。

后续动作：

- 用一个真实 0 到 1 项目试水，观察新增产品/UX/架构层是否过重。
- 如果真实使用中发现模板太重，优先调整 L1/L2/L3/L4 分级和生成说明，不删除质量门状态字段。
- 如果 AI 修改后仍没有记录效果，把 `AI_EFFECTIVENESS.md` 的关键字段提升为 audit 或质量门检查。

### 2026-06-15 - 把用户工作台模板纳入发布包

问题：

发布包已经能生成项目工作台，但没有把“接收者自己的用户工作台”作为可安装模板交付。结果是别人安装 `codex-workbench` 后，只能得到项目级规则、质量门和功能工作包；如果他没有自己的全局 `AGENTS.md`、工具路由、搜索/澄清习惯和审查规则，项目工作台仍然能用，但启动层约束不足，容易误以为插件会自动修改用户全局配置。

证据来源：

- 用户反馈：指出“发布整个你没有修改用户工作台”，要求本地发布包先修正。
- 本地失败证据：`README.md` 只解释用户工作台和项目工作台的关系，没有提供可复制模板或脚本入口；`packaging-manifest.json` 也未把用户工作台说明纳入发布文件。

决策：

不在插件安装时自动覆盖接收者的 `~/.codex/`，因为用户工作台会影响所有项目，并且可能涉及个人账号、MCP、hook 信任和本机路径。改为发布一套通用用户工作台模板，并提供 `user-workbench` 命令：默认只预览，只有用户明确加 `--apply` 才写入，已有文件默认跳过，`--force` 才备份后覆盖。

变更文件：

- `README.md`
- `docs/USER_WORKBENCH.md`
- `packaging-manifest.json`
- `skills/codex-workbench/SKILL.md`
- `skills/codex-workbench/scripts/workbench.py`
- `skills/codex-workbench/assets/user-workbench-template/AGENTS.md`
- `skills/codex-workbench/assets/user-workbench-template/WORKBENCH_ROUTING.md`
- `skills/codex-workbench/assets/user-workbench-template/CODE_QUALITY.md`
- `skills/codex-workbench/assets/user-workbench-template/CODE_REVIEW.md`
- `skills/codex-workbench/assets/user-workbench-template/RTK.md`

验证结果：

- `user-workbench` 预览：通过，默认返回 `would-write`，不写入目标目录。
- `user-workbench --apply` 写入临时目录：通过，生成 5 个用户工作台文件。
- 脚本语法检查：通过。
- 发布包扫描：未发现作者个人绝对路径、邮箱或真实密钥；只出现安全说明中的 `token`、`cookie` 等普通词。

后续动作：

- 重新运行 `package-check --expected-version 1.0.0 --write-report`，确认删除 Python cache 后发布门禁通过。
- 如果用户后续要求真正发布到 GitHub，再处理本地/远端分支差异并由用户确认后推送。

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

### 2026-06-15 - 将 scorecard 从质量裁判重构为证据审计

问题：

工作台曾把 `scorecard.py` 表述为“严格打分”入口，并让质量门在写入 `.workbench-validation/quality-gate-ok.json` 前调用 scorecard。这样有两个风险：第一，用户或 AI 容易把高分误解为代码、产品、架构或 AI eval 已经真实合格；第二，scorecard 又检查质量门成功标记时，会和当前质量门运行形成循环依赖，第一次运行容易被“缺少历史标记”误导。

证据来源：

- 用户反馈：质疑“脚本打分怎么保证合理、怎么减少 AI 幻觉、整体流程是否有问题”。
- 官方/外部资料：
  - OpenAI Codex Best Practices: `https://developers.openai.com/codex/learn/best-practices`
  - OpenAI Codex Skills: `https://developers.openai.com/codex/skills`
  - GitHub Spec Kit: `https://github.github.com/spec-kit/`
  - Kiro Specs Best Practices: `https://kiro.dev/docs/specs/best-practices/`
  - Anthropic Agent Evals: `https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents`
- 本地证据：`quality_gate.py` 先调用 scorecard，scorecard 又检查 `.workbench-validation/quality-gate-ok.json`；模板文档存在“严格打分”“阈值通过”等容易被误读为质量裁判的表述。

决策：

保留 scorecard，但降权为证据审计报告。质量判断改为分层：确定性检查、质量门、CI、review 和人工/独立复核是门禁；scorecard 只输出 `decision`、参考分、可信度、硬阻塞、校准状态和证据缺口。`BLOCKED` 才阻塞质量门，`PASS_WITH_RISK` 必须人工确认风险，参考分和组件下限只作为风险信号。

变更文件：

- `skills/codex-workbench/scripts/workbench.py`
- `skills/codex-workbench/assets/project-adapter-template/AGENTS.md`
- `skills/codex-workbench/assets/project-adapter-template/WORKBENCH.md`
- `skills/codex-workbench/assets/project-adapter-template/PRODUCT_BASELINE.md`
- `skills/codex-workbench/assets/project-adapter-template/REVIEW.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/scorecard/RUBRIC.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/scorecard/SCORECARD.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/scorecard/CALIBRATION.md`
- `skills/codex-workbench/references/quality-gate-patterns.md`
- `skills/codex-workbench/references/project-adapter-template.md`
- `skills/codex-workbench/references/workbench-maturity.md`

验证结果：

- `self-test`：通过，生成 51 个项目工作台文件，验证通过，审计无 P0/P1。
- `golden-test`：通过，覆盖 node-vite、maven-basic、fullstack-compose、old-workbench-upgrade 四个用例。
- `doctor --plugin <plugin-root>`：通过，P0/P1/P2/P3 均为 0。
- `package-check --plugin <plugin-root> --expected-version 1.0.0 --write-report`：通过，P0/P1/P2/P3 均为 0。
- `py -m py_compile skills/codex-workbench/scripts/workbench.py`：通过。
- Python 运行时仍输出 `Could not find platform independent libraries <prefix>`，但上述命令退出码均为 0。

后续动作：

- 在真实项目试水时观察 `PASS_WITH_RISK` 是否被用户或 AI 误当成通过；如果出现，提升为质量门或 review 检查。
- 如果 scorecard 仍出现高分低质量，优先调整模板、参考线、硬阻塞、质量门或审查清单，不手工改报告结果。
