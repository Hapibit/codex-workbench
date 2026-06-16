# {{PROJECT_NAME}} 工作台说明

## 作用

本目录是项目级 AI 工作台适配器，用来让 Codex 和其他编码代理按本项目的规则工作。它不是全局 Codex 安装、账号登录、MCP 凭证、hook 信任或本地工具链的替代品。

## 文件职责

- `AGENTS.md`：项目规则入口，说明 AI 必读内容、完成标准、澄清条件和硬边界。
- `PROJECT_INTAKE.md`：项目预处理画像，用来把模糊需求转成可确认的目标、用户、范围、数据、权限、AI 边界和验收。
- `workbench/product/PRODUCT_BRIEF.md`：产品简报，定义业务目标、成功指标、第一版价值和范围边界。
- `workbench/product/PRD.md`：产品需求，定义用户故事、验收标准、非目标和需求变更规则。
- `workbench/product/ROADMAP.md`：路线图，定义版本范围、优先级、依赖和迭代节奏。
- `workbench/design/UX_SPEC.md`：交互规格，定义页面、流程、状态、错误反馈和可用性要求。
- `workbench/design/PROTOTYPE.md`：原型说明，记录 Figma、图片、HTML 或其他原型位置和验收。
- `workbench/design/USER_FLOW.md`：用户流程，记录入口、成功路径、失败路径和验证方式。
- `workbench/architecture/ARCHITECTURE.md`：架构设计，定义模块、边界、数据流、风险和约束。
- `workbench/architecture/DATA_MODEL.md`：数据模型，定义实体、关系、权限和迁移规则。
- `workbench/architecture/API_DESIGN.md`：API 设计，定义接口契约、错误、权限和兼容性。
- `workbench/architecture/AI_DESIGN.md`：AI 设计，定义 AI 输入输出、工具、数据来源、人工确认和 eval。
- `workbench/architecture/adr/`：ADR 目录，记录重大架构、数据、API、AI、部署和安全决策。
- `workbench/delivery/RELEASE_PLAN.md`：发布计划，记录版本范围、验证和回滚。
- `workbench/delivery/ITERATION_PLAN.md`：迭代计划，记录当前迭代、变更、复测和下一轮动作。
- `workbench/delivery/TASK_BREAKDOWN.md`：任务拆分，承接 PRD/UX/架构，进一步落到功能工作包。
- `workbench/scorecard/RUBRIC.md`：证据审计规则，定义权重、参考线、硬阻塞和语义复核边界。
- `workbench/scorecard/SCORECARD.md`：项目当前证据审计卡，记录决策、参考分、可信度、架构合理性、语义质量复核和改进动作。
- `workbench/scorecard/CALIBRATION.md`：审计口径校准记录，记录锚定样例、人工抽查、误报、漏报和参考线调整依据。
- `workbench/scorecard/scorecard.py`：跨平台证据审计脚本，检查证据成熟度和状态一致性。
- `WORKBENCH.md`：工作台使用说明，说明怎么运行质量门、运行时检查、审计和分享。
- `REVIEW.md`：项目审查标准，要求审查先报风险、再报建议。
- `DEVELOPMENT_FLOW.md`：项目开发流程契约。默认是 `status: draft`，必须由项目负责人确认后才作为功能开发流程。
- `PRODUCT_BASELINE.md`：产品下限标准，防止功能只写完代码但用户不可用。
- `FEATURE_WORKFLOW.md`：单功能 SDD 工作包流程，定义 SPEC、CLARIFY、PLAN、TASKS、DECISIONS、CHECKLIST、VERIFY、REVIEW 的闭环。
- `workbench/quality/quality_gate.py`：跨平台质量门，是本项目的主要确定性检查入口。
- `workbench/quality/quality-gate.ps1`：Windows 包装器，只负责调用 Python 质量门。
- `workbench/quality/quality-gate.sh`：macOS/Linux 包装器，只负责调用 Python 质量门。
- `workbench/runtime/runtime_gate.py`：运行时 smoke 计划和可选 URL 检查。
- `workbench/runtime/api_smoke.py`：轻量 API 可用性检查。
- `workbench/feedback/FAILURE_LOG.md`：AI 失败、返工、审查漏报、质量门缺口和工作台改进证据。
- `workbench/feedback/ITERATION_LOG.md`：需求变化、用户反馈、审查结论和验证结果的迭代记录。
- `workbench/feedback/AI_EFFECTIVENESS.md`：AI 实现、审查、修改后的效果评估。
- `workbench/review/independent-review-prompt.md`：给新 AI 会话使用的只读独立审查提示。
- `workbench/feature-template/`：功能工作包模板，用于复制到 `workbench/features/<feature-name>/`。
- `workbench/features/<feature-name>/`：真实功能工作包目录，每个重要功能一份。

## 标准开发流程

用户只需要把需求交给 Codex Workbench，不需要先判断要调用哪个专业 skill。统一入口是：

```text
Use Codex Workbench to tell me the next step for this project.
```

工作台内部按阶段路由：

| 用户当前想做什么 | 先看/先产出的文件 | 必须产出或停止条件 | 可选增强能力 |
| --- | --- | --- | --- |
| 项目还没讲清楚、需求很散、方向变化 | `PROJECT_INTAKE.md` | 确认目标用户、范围、数据、权限、AI 边界和验收；仍有 open blocker 时停止高风险实现。 | 需求澄清、项目预处理 |
| 要确定为什么做、第一版做什么、不做什么 | `workbench/product/PRODUCT_BRIEF.md`、`PRD.md`、`ROADMAP.md` | 写清业务目标、成功指标、用户故事、验收标准、非目标和版本范围。 | 产品/技术文档 |
| 要设计用户路径、页面状态、原型 | `workbench/design/UX_SPEC.md`、`PROTOTYPE.md`、`USER_FLOW.md` | 写清入口、主流程、失败流程、错误/空/加载/权限状态和原型证据。 | UI/UX、Figma、前端设计 |
| 要确定模块、数据、API、AI、权限边界 | `workbench/architecture/` | 写清模块边界、数据模型、API 合约、AI 工具调用、权限边界、ADR 和回滚约束。 | 架构、企业 AI 生命周期、画图 |
| 要拆版本、迭代和任务 | `workbench/delivery/` | 写清当前迭代范围、任务拆分、验证计划、依赖和回滚路径。 | CI/CD、技术文档 |
| 要开始写某个功能 | `workbench/features/<feature-name>/` | 先建立或更新功能包，解决 `CLARIFY.md` open blocker，再实现约定范围。 | 测试、框架、语言专项能力 |
| 要确认质量或复盘失败 | `workbench/quality/`、`scorecard/`、`review/`、`feedback/` | 运行可用质量门，写验证证据和 review 结论；重复失败进入机制升级判断。 | 测试、CI、安全、AI eval、独立审查 |

如果增强能力不存在，仍然继续走本工作台的核心文件和脚本；增强 skill 不是使用本工作台的前置条件。

每次使用阶段路由后，AI 必须按这个执行契约收尾：

1. 先判断当前阶段和项目状态，不清楚时读取现有工作台文件再问最少阻塞问题。
2. 说明本次选择的阶段、依据、需要读的文件和不会做的范围。
3. 更新对应阶段产物；如果阻塞信息缺失，先写入 blocker 或向用户确认，不用猜测替代。
4. 能验证的运行脚本、质量门、scorecard 或审查；不能验证时写明原因。
5. 最终回复只给本轮结果、证据位置、验证结果、剩余风险和下一步。

本工作台的完整 0 到 1 流程是：

```text
项目发现 -> 产品简报 -> PRD -> UX/原型 -> 架构设计 -> 交付计划 -> 功能包开发 -> 验证审查 -> 迭代复盘
```

对应文件：

| 阶段 | 目标 | 主要产物 |
| --- | --- | --- |
| 项目发现 | 搞清楚项目是什么、给谁用、第一版做什么 | `PROJECT_INTAKE.md` |
| 产品简报 | 明确业务目标、成功指标、范围边界 | `workbench/product/PRODUCT_BRIEF.md` |
| PRD | 明确产品需求、用户故事、验收标准、非目标 | `workbench/product/PRD.md` |
| UX/原型 | 明确用户流程、页面状态、原型和交互 | `workbench/design/UX_SPEC.md`、`PROTOTYPE.md`、`USER_FLOW.md` |
| 架构设计 | 明确模块、数据、API、AI、ADR 和风险 | `workbench/architecture/` |
| 交付计划 | 明确版本、迭代和任务拆分 | `workbench/delivery/` |
| 功能包开发 | 单功能 SPEC、CLARIFY、DESIGN、PLAN、TASKS、实现 | `workbench/features/<feature-name>/` |
| 验证审查 | 测试、质量门、独立审查、剩余风险 | `VERIFY.md`、`REVIEW.md`、质量门 |
| 证据审计 | 证据成熟度、硬阻塞、架构/语义复核 | `workbench/scorecard/` |
| 迭代复盘 | 需求变化、AI 效果、失败模式、自动化改进 | `workbench/feedback/` |

这不是一次性瀑布流程。小改动可以走轻流程；新项目、核心功能、跨模块、高风险或需求不清时，必须先补前置事实源，再让 AI 实现。

## AI 实现后的闭环

AI 可以先写代码，但不能自己宣布质量合格。每次 AI 实现后按以下闭环处理：

1. 对照 `SPEC.md` 和 `DESIGN.md` 检查有没有偏离需求、UX、架构或权限边界。
2. 运行 `VERIFY.md` 里定义的验证和项目质量门。
3. 用 `REVIEW.md` 做功能审查；高风险改动再开独立审查。
4. 发现问题时先判断问题属于 PRD、UX、架构、计划、实现、测试还是审查缺口。
5. 根据归因回到对应文件修改，不要只在代码里补丁式修。
6. 修改后重新验证和审查，并把复测写入 `CHANGELOG.md`、`VERIFY.md` 或 `ITERATION_LOG.md`。
7. 统计 AI 的返工、审查发现和质量门失败，写入 `AI_EFFECTIVENESS.md`，用于升级模板、测试、质量门或 CI。
8. 在功能 `REVIEW.md` 的 `workbench_upgrade_assessment` 写明升级判断。只要出现 failed、blocked、P0、P1、返工、审查漏报或重复问题，就不能保持 `unassessed`。

## 证据审计

运行：

```bash
python workbench/scorecard/scorecard.py --profile standard --write-report
```

审计报告写入：

```text
.workbench-validation/scorecard-report.json
```

审计规则在 `workbench/scorecard/RUBRIC.md`。默认参考线：

- `smoke`：60 分参考线，组件下限 20%，快速判断证据是否足以继续推进。
- `standard`：75 分参考线，组件下限 50%，日常开发默认审计档。
- `full`：85 分参考线，组件下限 60%，发布、PR、跨模块或高风险改动；必须完成校准和语义/架构复核。

审计顺序：

1. 先看硬阻塞；有硬阻塞时总分无效。
2. 再看 `decision`：`BLOCKED` 阻塞，`PASS_WITH_RISK` 需要人工确认风险，`PASS` 才能作为流程证据。
3. 再看总分是否低于当前档位参考线；低分不自动失败，但说明证据不足。
4. 再看组件下限，防止总分掩盖产品、架构、验证等单项短板。
5. 再看 `score_confidence`、`CALIBRATION.md`、`semantic_review_status` 和 `architecture_review_status`。
6. 如果语义或架构复核仍是 `pending`，可以继续开发，但不能宣称业务、产品、UX 或架构已经通过最终验收。

这个分数只代表证据成熟度和流程一致性。产品目标是否正确、架构是否真的合理、AI eval 是否覆盖真实失败样例，仍需要人工或独立 AI 审查写入 `SCORECARD.md`。

`score_confidence` 比总分更重要：

- `high`：没有硬阻塞、组件下限缺口、校准缺口或语义/架构复核缺口。
- `medium`：分数可参考，但需要人工看校准、复核或警告项。
- `low`：分数不能作为通过依据，只能作为问题定位线索。

如果分数和实际质量不一致，把差异写入 `CALIBRATION.md` 的误报/漏报记录，然后调整模板、脚本、质量门、CI、hook 或审查清单。不要为了刷高分而补空文档。

## 质量门

```bash
python workbench/quality/quality_gate.py --profile standard
```

检查档位：

- `smoke`：快速本地检查，适合小改动后先跑一遍。
- `standard`：日常开发默认检查，通常包含构建、测试、lint 或打包。
- `full`：PR、发布、跨服务或高风险改动使用，只有配置了重检查时才运行。

已检测到的检查：

{{QUALITY_COMMANDS}}

如果没有任何检查，质量门会失败，除非显式传入 `--allow-empty`。对代码项目来说，空质量门不能当作真实验证。

质量门先运行确定性检查，再调用 `workbench/scorecard/scorecard.py --called-from-quality-gate --enforce-blockers` 生成证据审计报告。只有硬阻塞会让质量门失败；参考分、组件下限、低可信度和未完成复核必须作为风险说明，不能伪装成质量通过证明。

## 开发流程契约

先看 `PROJECT_INTAKE.md`。它负责回答“这个项目到底要做什么、给谁用、第一版边界是什么、哪些问题没搞清楚”。如果它还是 `status: draft` 或存在 open 阻塞问题，不要把 `DEVELOPMENT_FLOW.md` 改成 confirmed，也不要直接启动高风险功能开发。

`DEVELOPMENT_FLOW.md` 用来描述本项目自己的开发作业流程，不是全局通用流程。

- `status: draft`：AI 只能把它当清单参考；功能开发、接口变更、数据库变更、权限变更、生产发布或 AI 自动生效逻辑前必须先确认。
- `status: confirmed`：AI 可以按它执行，但仍要遵守用户最新指令、项目代码事实和安全边界。
- 不同项目可以有不同流程；不要把一个项目的 `DEVELOPMENT_FLOW.md` 复制到其他项目后直接当成已确认流程。
- 如果流程和代码、CI、测试、README 或产品要求冲突，先停下来确认。

确认流程前至少检查：`owner`、`scope`、`confirmed_at`、`verification_commands`、高风险审批边界、各类型改动的验证要求。

## 产品下限和功能工作包

`PRODUCT_BASELINE.md` 是个人开发的最低质量线。任何用户可见功能都必须满足：用户目标清楚、主流程可用、错误状态可理解、权限和数据归属正确、UI 不破坏使用、验证证据存在。

`PROJECT_INTAKE.md` 中的第一版范围、用户角色、数据权限和 AI 边界应该同步影响 `PRODUCT_BASELINE.md`。如果两者冲突，先修项目画像。

`FEATURE_WORKFLOW.md` 用于新功能、跨模块或高风险改动。推荐复制模板：

```text
workbench/feature-template/
```

到：

```text
workbench/features/<feature-name>/
```

安装 Codex Workbench 插件后，推荐让 Codex 创建真实功能工作包；没有插件时也可以手动复制模板：

```text
Use Codex Workbench to create a feature work package named <feature-name>.
```

先按 `FEATURE_WORKFLOW.md` 的工作量分级门选择流程强度。规则是：先检查硬触发器，再按影响范围、不确定性、回滚难度打分；判断不清楚时自动升一级或先问用户。

- L1 轻量任务：不强制创建完整功能包，但必须记录问题、改动、验证和风险。
- L2 中等任务：创建功能工作包，至少完成 SPEC、CLARIFY、PLAN、VERIFY，按需补 TASKS、DECISIONS、REVIEW。
- L3 重量任务：完整走 SPEC、CLARIFY、PLAN、TASKS、DECISIONS、CHECKLIST、VERIFY、REVIEW。
- L4 紧急/重大任务：可以先做最小止血修复，但事后必须补齐验证、审查、复盘和防复发自动化。

只要命中数据库、权限、用户数据、AI 自动写入核心数据、公开 API、跨模块、生产部署、凭证、不可逆操作等硬触发器，最低按 L3 处理。生产事故、安全漏洞、数据损坏或服务不可用按 L4 处理。

然后按顺序完成：

1. `SPEC.md`：需求、范围、验收标准。
2. `CLARIFY.md`：需求缺口、阻塞问题、默认假设和已确认事实。
3. `PLAN.md`：技术方案、影响文件、风险。
4. `TASKS.md`：小步任务。
5. `DECISIONS.md`：关键取舍和实现偏离记录。
6. `CHECKLIST.md`：阶段门禁。
7. 实现代码。
8. `VERIFY.md`：验证命令、手工验收、剩余风险。
9. `REVIEW.md`：功能级审查和自动化改进项。

小 bugfix 可以简化，但不能跳过产品下限、验证证据和最终风险说明。

需求中途变化时：

1. 先判断变化是否影响 `PROJECT_INTAKE.md` 的项目目标、第一版范围、用户、权限、数据或 AI 边界。
2. 如果影响项目方向，先更新 `PROJECT_INTAKE.md`，再更新相关功能 `SPEC.md`。
3. 如果只影响当前功能，先更新 `SPEC.md`，再同步 `PLAN.md`、`TASKS.md`、`VERIFY.md` 和 `REVIEW.md`。
4. 如果变化提高风险等级，重新按 `FEATURE_WORKFLOW.md` 分级，并补充验证和审查。
5. 不能只在聊天里说“需求改了”，然后直接改代码。

## 工作台审计

安装 Codex Workbench 插件后，让 Codex 对本项目工作台执行审计：

```text
Use Codex Workbench to audit this project workbench.
```

分享本工作台或把它当成硬门禁前，必须修复 `P0` 和 `P1`。

严重级别：

- `P0`：可能造成泄密、权限绕过、生产事故、不可逆数据损坏。
- `P1`：会让工作台不可信，例如缺少质量门、生成文件残缺、可能包含 secret。
- `P2`：影响可维护性或验证强度，例如缺少 smoke/standard 档位。
- `P3`：改进建议，例如缺少本地 pre-commit，但 CI 仍可兜底。

`development-flow-draft` 通常是 `P2`：它不阻止生成工作台，但表示项目流程还没有人工确认，不应该直接用于高风险功能开发。

`project-intake-draft` 和 `open-project-intake-blocker` 通常是 `P2`：它们表示项目信息还没完成预处理。生成工作台可以通过，但后续项目质量门会在 `PROJECT_INTAKE.md` 仍是 draft 或存在 open 阻塞问题时失败。

`scorecard-report-not-generated` 是 `P1`：表示质量门没有生成证据审计报告，硬阻塞和证据缺口可能被跳过，必须修复。

## 运行时检查

Dry-run plan:

```bash
python workbench/runtime/runtime_gate.py
```

Apply URL smoke checks:

```bash
python workbench/runtime/runtime_gate.py --apply --backend-health-url http://localhost:8080/health
```

默认不要启动长时间运行的服务；需要实际运行时使用 `--apply`，并先确认端口、环境变量和依赖服务。

## 独立审查

当改动影响核心业务、权限、数据、AI 输出、支付/成绩/订单/文件等敏感路径时，使用 `workbench/review/independent-review-prompt.md` 开新会话做只读复查。

独立审查只看风险，不负责重写代码。它的输出应该按 `P0/P1/P2/Nit` 排序，并说明文件、行号、触发场景和修复方向。

## 反馈闭环

每次出现返工、质量门失败、审查漏报或 AI 重复犯错时，先判断问题来源：

- 需求不清：补充澄清问题或验收标准。
- 实现偏离：补充项目规则、目录边界或接口契约。
- 测试不足：补单元、接口、集成、E2E 或 AI eval。
- 审查漏报：补 `REVIEW.md` 清单或独立审查提示。
- 工具缺失：补 `workbench/quality/quality_gate.py`、pre-commit、CI 或 hook。

证据必须放到固定位置：

- 单个功能的问题证据放在 `workbench/features/<feature-name>/VERIFY.md`、`REVIEW.md`、`DECISIONS.md`。
- 跨功能、重复出现、需要沉淀成规则或自动化的问题，汇总到 `workbench/feedback/FAILURE_LOG.md`。
- 不能只写在聊天记录、最终回复或临时笔记里。

功能审查必须给出工作台升级判断：

| `workbench_upgrade_assessment` | 含义 |
| --- | --- |
| `not_required` | 本次问题是一次性项目个案，已有项目内修复和验证证据，不需要升级工作台。 |
| `failure_log_updated` | 已写入 `workbench/feedback/FAILURE_LOG.md`，等待后续归纳或自动化。 |
| `template_update_needed` | 需要改 SPEC、CLARIFY、DESIGN、PLAN、VERIFY、REVIEW 或其他模板。 |
| `quality_gate_update_needed` | 需要把问题加入 `workbench/quality/quality_gate.py` 或 scorecard 检查。 |
| `review_rule_update_needed` | 需要改项目 `REVIEW.md`、独立审查提示或 P0/P1 清单。 |
| `ci_or_hook_needed` | 需要接入 CI、pre-commit、hook 或其他硬门禁。 |
| `deferred_with_reason` | 暂不升级，但必须说明原因、风险和后续复查位置。 |

能自动化的问题优先进入脚本、测试、lint、CI 或质量门；无法自动化的业务判断才保留在 Markdown 规则里。

## 证据保留策略

工作台证据不能无脑堆积，也不能为了变干净而删除审计线索。按价值分层处理：

| 证据类型 | 位置 | 保留方式 |
| --- | --- | --- |
| 机器生成报告 | `.workbench-validation/*.json` | 默认保留最近报告；旧报告可归档到 `workbench/archive/validation/`，不作为长期人工说明。 |
| 功能级证据 | `workbench/features/<feature-name>/` | 功能开发、验证、审查和决策证据跟功能包保留；发布后可人工归档到 `workbench/archive/features/`。 |
| 重复失败和跨功能问题 | `workbench/feedback/FAILURE_LOG.md` | 只记录重复问题、P0/P1、审查漏报、质量门缺口或流程缺陷；不要记录每次普通失败。 |
| 长期工作台改进 | `docs/maintenance/` 或项目 ADR | 重大规则、架构和发布边界变化用 ADR 或版本归档；主日志只保留当前索引和最近记录。 |

可以让 Codex Workbench 先预览保留计划：

```text
Use Codex Workbench to preview retention for this project.
```

底层命令：

```bash
python <codex-workbench>/scripts/workbench.py retention --project <repo>
```

只有确认后才允许归档旧机器报告：

```bash
python <codex-workbench>/scripts/workbench.py retention --project <repo> --apply --write-report
```

`retention --apply` 只移动旧机器报告，不删除文件，不重写 `FAILURE_LOG.md`、`IMPROVEMENT_LOG.md`、ADR 或功能包内容。人工维护日志过大时，只给出拆分/归档建议。

## 验证适配器

安装 Codex Workbench 插件后，让 Codex 校验本项目工作台：

```text
Use Codex Workbench to validate this project workbench.
```

## 升级已有工作台

已有 `AGENTS.md`、`WORKBENCH.md` 或 `REVIEW.md` 时，默认不要覆盖。安装 Codex Workbench 插件后，让 Codex 先预览升级计划，再由项目负责人确认是否应用：

```text
Use Codex Workbench to preview an upgrade for this project workbench.
```

只有用户明确同意时才覆盖已有文档或刷新已生成脚本。

## 接收者配置

每个接收者必须自己配置 Codex 登录、MCP 凭证、GitHub/Figma/Jenkins 权限、hook 信任、本地工具链和环境变量。不要分享 API keys、cookies、tokens、个人配置文件或浏览器登录态。

## 不覆盖的内容

- 不保证接收者已经安装 Node、Java、Maven、Docker、Python 或项目依赖。
- 不替代 CI、pre-commit、权限系统、代码所有者审查或人工产品验收。
- 不判断业务规则是否正确；业务规则必须来自项目文档、代码、测试、产品确认或用户确认。
