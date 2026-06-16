# Codex Workbench

Codex Workbench 是给 Codex 使用的 AI 开发工作台插件。它不是一段更长的提示词，而是一套放进项目仓库里的工作方式：先把项目事实、产品需求、UX/原型、架构、交付计划、功能开发、验证审查、证据审计和失败复盘固定下来，再让 Codex 在这个框架里工作。

它要解决的问题很具体：AI 写代码很快，但在真实项目里，风险通常不来自“代码写得慢”，而来自需求没确认、上下文只留在聊天里、测试没有跑、审查没有证据、同类错误反复出现。Codex Workbench 的目标是降低这些风险，让 AI 开发过程有事实源、有流程、有门禁、有证据、有迭代。

安装后，普通用户主要只需要记住一个入口：

```text
Use Codex Workbench to set up this project's AI workbench.
```

## 设计依据

这个工作台按公开工程实践组合，不按个人感觉堆规则。

| 资料依据 | 对工作台的影响 |
| --- | --- |
| OpenAI Codex best practices | 稳定规则放进 `AGENTS.md`；复杂任务先规划；把构建、测试、lint、完成标准写清楚；重复流程沉淀成 skill 或插件。 |
| OpenAI Codex customization | 先用 `AGENTS.md` 固化仓库规则，再用 skill/plugin 复用工作流，MCP 只负责外部系统连接。 |
| OpenAI Codex skills/plugins | skill 负责可复用流程，plugin 是分发单元；所以本插件只暴露一个入口 `codex-workbench`，内部脚本和模板不要求新用户先学习。 |
| OpenAI agent improvement loop | 改进要来自 trace、反馈、eval 和可验证变更，不靠“感觉更好”。 |
| OpenAI Codex iterative repair loop | review、repair、validation 要分离；验证失败要成为下一轮修复输入。 |
| SonarQube quality gates | 质量门应该是明确条件的 pass/fail，不应该让一个总分掩盖 blocker。 |
| Rubric 设计资料 | 评分必须有明确 criteria、公开权重、校准样例、误报/漏报记录，降低主观性和偏差。 |
| Google SRE postmortem | 失败复盘要记录事实、影响、根因、行动项和可验证完成标准。 |
| Diataxis 与 GitHub README 建议 | README 只负责快速理解和开始使用；长解释、评分、维护和升级细节放到独立文档。 |
| Semantic Versioning | 用 patch/minor/major 表达工作台升级对使用者的影响。 |

完整解释见 [WORKFLOW_AND_SCORECARD.md](docs/WORKFLOW_AND_SCORECARD.md) 和 [ITERATION_UPGRADE.md](docs/ITERATION_UPGRADE.md)。

## 这个插件到底做什么

它会在目标项目里生成一套项目工作台：

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

这些文件不是为了“好看”，而是为了让项目开发过程可以被复查。

| 层级 | 负责什么 | 主要产物 |
| --- | --- | --- |
| 项目发现 | 把目标用户、范围、数据、权限、AI 边界和验收先说清楚 | `PROJECT_INTAKE.md` |
| 产品规划 | 说明为什么做、第一版做什么、不做什么、怎么验收 | `PRODUCT_BRIEF.md`、`PRD.md`、`ROADMAP.md` |
| UX/原型 | 说明用户路径、页面状态、错误反馈、原型和可用性要求 | `UX_SPEC.md`、`PROTOTYPE.md`、`USER_FLOW.md` |
| 架构设计 | 说明模块、数据、API、AI 工具调用、权限边界和 ADR | `workbench/architecture/` |
| 交付计划 | 说明版本范围、任务拆分、验证、回滚和发布风险 | `workbench/delivery/` |
| 功能工作包 | 把每个重要功能拆成规格、澄清、设计、计划、任务、验证、审查 | `workbench/features/<feature>/` |
| 质量门 | 把测试、lint、build、runtime smoke、scorecard 接成可运行检查 | `workbench/quality/` |
| 证据审计 | 检查证据是否完整、状态是否一致、是否有硬阻塞 | `workbench/scorecard/` |
| 失败复盘 | 把重复失败沉淀成模板、测试、质量门、CI、hook 或审查规则 | `workbench/feedback/` |

## 推荐工作流

从 0 到 1 的完整流程是：

```text
项目发现
-> 产品简报
-> PRD
-> UX/原型
-> 架构设计
-> 交付计划
-> 功能包开发
-> 验证审查
-> 证据审计
-> 迭代复盘
```

这不是固定瀑布流程。工作台按风险和影响面选择流程强度：

| 场景 | 推荐强度 | 处理方式 |
| --- | --- | --- |
| 文案、低风险单文件修复 | 轻量 | 可以不建完整功能包，但必须说明改动、验证和风险。 |
| 普通用户可见功能 | 中等 | 建功能包，至少完成 `SPEC`、`CLARIFY`、`PLAN`、`VERIFY`。 |
| 跨模块、权限、数据、AI 自动生效、数据库、生产发布 | 重量 | 完整功能包、质量门、review，必要时独立审查。 |
| 事故、安全漏洞、数据损坏 | 紧急 | 可先止血，事后必须补验证、审查、复盘和防复发自动化。 |

如果项目已经写了一部分但需求变了，不是直接改代码。先更新对应事实源：

| 变化 | 先更新 |
| --- | --- |
| 项目目标、用户、第一版范围变化 | `PROJECT_INTAKE.md`、产品、UX、架构、交付计划 |
| 当前功能需求变化 | 功能包 `SPEC.md`、`CLARIFY.md` |
| 技术方案变化 | `DESIGN.md`、`DECISIONS.md`、必要时补 ADR |
| 验收标准变化 | `SPEC.md`、`VERIFY.md`、测试和质量门 |
| AI 实现偏离计划 | `IMPLEMENTATION_NOTES.md`、`DECISIONS.md`、`VERIFY.md` |

## 每个流程靠什么保证

| 流程 | 主要保证 | 不能靠什么保证 |
| --- | --- | --- |
| 项目预处理 | 状态字段、open blocker、人工确认 | AI 说“我理解了” |
| 产品需求 | 用户故事、验收标准、非目标、变更记录 | 一句模糊需求 |
| UX/原型 | 用户路径、页面状态、错误路径、可访问性要求 | 只说“做得好看” |
| 架构设计 | 模块边界、数据流、API/AI 边界、ADR、回滚策略 | 代码写完后再解释 |
| 功能开发 | 功能工作包的阶段证据 | 一次性大改 |
| 验证 | 测试、lint、build、runtime smoke、质量门、人工验收 | 最终回复里的“已测试” |
| 审查 | P0/P1/P2 风险、独立审查、审查证据 | 只看代码风格 |
| 证据审计 | `decision`、blocker、confidence、校准 | 总分好看 |
| 复盘 | `FAILURE_LOG.md`、`CALIBRATION.md`、模板/测试/CI/hook 改进 | 聊天里口头记住 |

Markdown 规则只是说明。真正不能跳过的要求，要尽量落到脚本、测试、pre-commit、CI、Codex hook 或质量门里。

## 评分机制为什么这样设计

`workbench/scorecard/` 不是质量裁判。它只审计：

```text
证据是否完整
状态是否一致
是否存在硬阻塞
评分口径是否经过校准
```

它不证明产品目标正确、架构最优、UI 好用、代码无 bug、AI eval 覆盖充分或可以上线。

结果必须按这个顺序看：

```text
decision
-> blockers
-> confidence
-> component floors
-> reference score
```

只看总分是错误用法。只要有硬阻塞，参考分再高也不能交付。

默认参考权重是未校准前的启动口径，不是统计结论：

| 维度 | 权重 | 为什么这样放 |
| --- | ---: | --- |
| 项目预处理 | 15 | 先防止方向错、用户错、范围错、权限和数据边界错。 |
| 产品需求 | 15 | PRD 和验收标准决定功能是否做对。 |
| 交互/原型 | 10 | 用户路径重要，但不同项目差异大，不能压过需求和架构。 |
| 架构设计 | 15 | 模块、数据、API、AI 边界错误会带来高返工和高风险。 |
| 交付计划 | 10 | 版本、任务、回滚重要，但不是当前质量的唯一证据。 |
| 功能工作包 | 20 | AI 真实开发发生在这里，必须最高权重检查需求到验证的证据链。 |
| 验证硬门禁 | 10 | 验证失败应直接进入 blocker，不靠软分数慢慢扣。 |
| 反馈闭环 | 5 | 反馈用于长期改进，不能弥补当前需求、设计或验证缺口。 |

这个设计的核心是三条：

1. 高风险失败不能靠低风险文档补分。
2. 验证失败不能靠总分绕过。
3. 反馈复盘不能掩盖当前交付证据不足。

减少 AI 幻觉的办法不是“相信分数”，而是四层约束：

| 约束 | 作用 |
| --- | --- |
| 硬阻塞 | open blocker、质量门失败、高风险未确认时直接阻断。 |
| 组件下限 | 防止总分掩盖产品、架构、验证等单项短板。 |
| 可信度 | 高分低可信度必须人工看风险，不能当作通过。 |
| 校准记录 | 用真实功能包记录 false positive、false negative，再调整模板、脚本、权重或 blocker。 |

完整评分规则见 [WORKFLOW_AND_SCORECARD.md](docs/WORKFLOW_AND_SCORECARD.md) 和项目模板里的 `workbench/scorecard/RUBRIC.md`。

## 迭代升级怎么做

工作台升级不是“觉得哪里不顺就改”。升级必须从证据开始。

Codex Workbench 把迭代分成三层：

| 层级 | 什么时候发生 | 证据放哪里 | 结果 |
| --- | --- | --- | --- |
| 项目迭代 | 需求变化、功能返工、验证失败、用户反馈 | 项目内 `workbench/features/`、`workbench/feedback/`、`workbench/scorecard/CALIBRATION.md` | 更新项目事实、功能包、测试、review 或质量门 |
| 工作台机制升级 | 同类失败重复出现，说明模板、脚本、质量门或审查规则有缺口 | 插件内 `docs/maintenance/IMPROVEMENT_LOG.md`、`FAILURE_PATTERNS.md`、ADR | 修改模板、脚本、质量门、CI、hook 或文档 |
| 插件版本发布 | 升级会影响别人安装后的行为 | `plugin.json`、README、package-check 报告、维护日志 | 发布 patch/minor/major 版本 |

升级闭环：

```text
收集证据
-> 分类失败
-> 判断是项目个案还是工作台机制缺陷
-> 修改对应模板、脚本、质量门、CI、hook 或文档
-> 运行验证
-> 写维护日志
-> 判断是否发版本
```

版本规则：

| 类型 | 什么时候用 |
| --- | --- |
| `PATCH` | 修文档、模板文字、脚本 bug，不改变公开工作流。 |
| `MINOR` | 新增向后兼容能力、模板、文档或检查项。 |
| `MAJOR` | 改变公开工作流、生成文件契约、命令行为或兼容性。 |

完整升级规则见 [ITERATION_UPGRADE.md](docs/ITERATION_UPGRADE.md)。

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
codex plugin marketplace add Hapibit/codex-workbench --ref v1.1.1
codex plugin add codex-workbench --marketplace hapibit
```

## 常用入口

在项目根目录打开 Codex，然后说：

```text
Use Codex Workbench to set up this project's AI workbench.
```

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

## 用户还要自己配置什么

这个插件不会替你登录第三方服务，也不会分发作者的私人配置。使用者仍然要自己配置：

- Codex 安装和登录。
- 自己的 `~/.codex/config.toml`。
- MCP servers 和凭证。
- GitHub、Figma、Jenkins、OpenAI、Google 等账号权限。
- Node、Java、Maven、Docker、Python、浏览器、draw.io 等项目工具链。
- 项目的环境变量、API keys 和本地依赖。
- hook 信任、审批策略和权限决策。
- 项目自己的测试、lint、类型检查、构建和 CI 命令。

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

说明见 [USER_WORKBENCH.md](docs/USER_WORKBENCH.md)。

## 可选增强能力

Codex Workbench 本身可以独立使用。其他 skill、MCP 或第三方工具只是在具体任务中增强能力，不是入门门槛。

用户不需要一开始判断“需求分析、产品规划、UX、架构分别用哪个 skill”。统一入口始终是 Codex Workbench；工作台先判断当前阶段，再在内部选择核心模板、脚本和可选增强能力。

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

## 维护与发布

普通使用者可以跳过这一节。

维护、打包和发布规则在：

```text
packaging-manifest.json
docs/maintenance/
skills/codex-workbench/
```

发布前至少运行：

```bash
python skills/codex-workbench/scripts/workbench.py package-check --plugin <plugin-root> --expected-version 1.1.1 --write-report
```

发布包应该只暴露一个可见 skill：

```text
codex-workbench
```

维护证据放在：

```text
docs/maintenance/
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
- OpenAI agent improvement loop: https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop
- OpenAI Codex iterative repair loop: https://developers.openai.com/cookbook/examples/codex/build_iterative_repair_loops_with_codex
- SonarQube quality gates: https://docs.sonarsource.com/sonarqube-server/quality-standards-administration/managing-quality-gates/introduction-to-quality-gates
- Google SRE postmortem culture: https://sre.google/workbook/postmortem-culture
- Diataxis: https://diataxis.fr/
- GitHub README: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes
- Rubric design: https://teaching.unl.edu/resources/grading-feedback/design-effective-rubrics
- Semantic Versioning: https://semver.org
