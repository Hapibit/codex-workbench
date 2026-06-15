# Codex Workbench 工作流与评分说明

本文解释 Codex Workbench 为什么这样设计、每个流程靠什么保证、scorecard 为什么不能当质量裁判、参考权重为什么这样分配，以及后续应该怎样根据真实失败迭代。

README 只负责让使用者快速开始；本文负责解释原理和判断口径。

## 文档结构为什么这样拆

GitHub 对 README 的建议是：说明项目做什么、为什么有用、怎样开始、哪里获得帮助、谁维护；更长的文档应该放到其他文档里。Diataxis 文档框架也把文档按用户需求拆成 tutorial、how-to、reference、explanation，避免把“怎么用”和“为什么这样设计”塞进一个长文件。

所以 Codex Workbench 采用这个结构：

| 文档 | 类型 | 作用 |
| --- | --- | --- |
| `README.md` | how-to + overview | 快速理解、安装、第一次使用 |
| `docs/WORKFLOW_AND_SCORECARD.md` | explanation + reference | 完整解释流程、评分、权重、校准、迭代 |
| `docs/USER_WORKBENCH.md` | how-to | 解释可选用户工作台模板 |
| `docs/maintenance/` | reference | 维护证据、失败模式、ADR |
| 项目里的 `workbench/**` | project evidence | 每个项目自己的事实、验证和复盘 |

这样做的目标是：新用户先能用，遇到“为什么这样设计”时再读解释文档；维护者修改规则时有证据位置，不把维护理由留在聊天记录里。

## 工作台的核心判断

Codex Workbench 不是为了让 AI “一次写对所有代码”。它是为了解决 AI 开发中的四个工程问题：

| 问题 | 风险 | 工作台做法 |
| --- | --- | --- |
| 项目事实不稳定 | AI 根据聊天片段脑补项目目标、范围、权限和数据边界 | 把项目事实写入 `PROJECT_INTAKE.md`、产品、UX、架构和交付文档 |
| 需求没有被确认 | 用户需求模糊时 AI 直接实现，后面返工 | 用 `CLARIFY.md`、open blocker 和人工确认阻止高风险推进 |
| 验证不可复查 | AI 说“完成了”，但没有命令、结果、截图、报告或人工验收 | 用 `VERIFY.md`、质量门、CI、`.workbench-validation/` 留证据 |
| 失败没有沉淀 | 同类问题反复出现，每次都靠用户重新提醒 | 用 `FAILURE_LOG.md`、`CALIBRATION.md`、模板、测试、CI、hook 做闭环 |

## 设计依据怎么落到机制里

工作台不是把公开资料贴进 README，而是把资料里的原则落成可执行机制。

| 公开原则 | 工作台机制 | 验证方式 |
| --- | --- | --- |
| Codex 需要仓库级稳定规则、运行命令和完成标准 | 生成项目 `AGENTS.md`、`WORKBENCH.md`、`REVIEW.md` | `validate`、`audit` 检查必需文件和占位符 |
| 复杂任务要先规划，不要直接写代码 | `PROJECT_INTAKE.md`、产品/UX/架构/交付文档、功能工作包 | 质量门阻止 draft intake 和 open blocker |
| 重复流程应该沉淀成 skill/plugin | 插件只暴露 `codex-workbench` 一个入口，内部封装脚本、模板和参考资料 | `package-check` 检查可见 skill 和发布清单 |
| 质量门应该是明确条件，不是一个总分 | `quality_gate.py` 先跑确定性检查，再调用 scorecard 审计证据 | 失败返回非 0，成功才写 `quality-gate-ok.json` |
| 评分要可复核、可校准、减少偏差 | `RUBRIC.md`、`CALIBRATION.md`、confidence、component floors、false positive/false negative | `full` 档要求校准和语义/架构复核 |
| agent 改进要来自真实反馈和 eval | `FAILURE_LOG.md`、`AI_EFFECTIVENESS.md`、`ITERATION_LOG.md` | 重复失败必须改模板、测试、质量门、CI、hook 或审查规则 |
| 事故复盘要有行动项和可验证完成标准 | `docs/maintenance/IMPROVEMENT_LOG.md`、`FAILURE_PATTERNS.md`、ADR | 发布前 `package-check` 检查维护证据 |

所以，文档里的每个“应该”都要能找到对应落点：项目文件、功能包、脚本、质量门、review、scorecard、维护日志或发布检查。找不到落点的规则只能算建议，不能宣传成硬门禁。

## 完整工作流

完整 0 到 1 流程是：

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

对应证据：

| 阶段 | 主要文件 | 要防的风险 |
| --- | --- | --- |
| 项目发现 | `PROJECT_INTAKE.md` | 项目目标、用户、范围、数据、权限、AI 边界不清 |
| 产品简报 | `workbench/product/PRODUCT_BRIEF.md` | 技术功能写出来但没有业务价值 |
| PRD | `workbench/product/PRD.md` | 没有用户故事、验收标准和非目标 |
| UX/原型 | `workbench/design/UX_SPEC.md`、`PROTOTYPE.md`、`USER_FLOW.md` | 页面流程、状态、错误反馈和用户路径缺失 |
| 架构设计 | `workbench/architecture/` | 模块、数据、API、AI 边界在代码里临时拼出来 |
| 交付计划 | `workbench/delivery/` | 没有版本范围、任务拆分、验证和回滚 |
| 功能包开发 | `workbench/features/<feature-name>/` | 大功能失控，需求变更无记录 |
| 验证审查 | `VERIFY.md`、`REVIEW.md`、质量门 | AI 自称完成但没有证据 |
| 证据审计 | `workbench/scorecard/` | 文档看似完整但存在硬阻塞或低可信度 |
| 迭代复盘 | `workbench/feedback/` | 同类问题反复发生 |

这不是强制瀑布流程。流程强度按风险决定：

| 等级 | 场景 | 要求 |
| --- | --- | --- |
| L1 轻量 | 文档、小文案、单文件低风险 bugfix | 可不建完整功能包，但要说明改动、验证和风险 |
| L2 中等 | 普通用户可见功能、单模块业务调整 | 建功能包，至少完成 `SPEC`、`CLARIFY`、`PLAN`、`VERIFY` |
| L3 重量 | 跨模块、权限、数据、API、AI 自动生效、数据库、生产发布 | 完整功能包、质量门、审查，必要时独立审查 |
| L4 紧急/重大 | 生产事故、安全漏洞、数据损坏、服务不可用 | 可先止血，事后必须补验证、审查、复盘和防复发自动化 |

命中以下任意条件，最低按 L3：

- 数据库 schema、迁移、批量数据修改。
- 登录、认证、授权、角色、租户、权限边界。
- 用户隐私、敏感数据、密钥、token、cookie、凭证。
- AI 生成内容会自动写入核心数据或影响用户权益。
- 公开 API、SDK、消息队列、事件结构。
- 生产部署、CI/CD、环境变量、基础设施。
- 删除、覆盖、不可逆操作。
- 需求不清但影响范围可能较大。

## 修改已有功能时怎么做

如果项目已经写了一部分，但需求变了，工作台按影响面处理：

| 变化类型 | 先改哪里 | 再改哪里 |
| --- | --- | --- |
| 项目方向、用户、第一版范围变化 | `PROJECT_INTAKE.md` | 产品、UX、架构、交付计划 |
| 当前功能需求变化 | 功能包 `SPEC.md`、`CLARIFY.md` | `DESIGN.md`、`PLAN.md`、`TASKS.md`、`VERIFY.md` |
| 技术方案变化 | `DESIGN.md`、`DECISIONS.md` | 架构文档或 ADR |
| 验收标准变化 | `SPEC.md`、`VERIFY.md` | 测试、质量门、review 清单 |
| AI 实现偏离计划 | `DECISIONS.md`、`IMPLEMENTATION_NOTES.md` | 复测写入 `VERIFY.md`，必要时写 `FAILURE_LOG.md` |

不能只在聊天里说“需求改了”，然后直接改代码。需求变化必须进入项目事实源或功能工作包，否则下一轮 AI 和审查者无法复查。

## 每个流程靠什么保证

| 流程 | 主要保证 | 不能靠什么保证 |
| --- | --- | --- |
| 项目预处理 | 状态字段、open blocker、人工确认 | AI 自己说“我理解了” |
| 产品需求 | 用户故事、验收标准、非目标、变更记录 | 模糊的一句话需求 |
| UX/原型 | 用户流程、页面状态、错误路径、可访问性要求 | 只说“做得好看” |
| 架构设计 | 模块边界、数据流、API/AI 边界、ADR、回滚策略 | 代码写完后再解释 |
| 功能开发 | 功能工作包的阶段证据 | 一次性大改 |
| 验证 | 测试、lint、build、runtime smoke、质量门、人工验收 | 最终回复里的“已测试” |
| 审查 | P0/P1/P2 风险、独立审查、审查证据 | 只看代码风格 |
| 证据审计 | scorecard 的 `decision`、blocker、confidence、校准 | 总分好看 |
| 复盘 | `FAILURE_LOG.md`、`CALIBRATION.md`、模板/测试/CI/hook 改进 | 聊天里口头记住 |

## 质量门、review、scorecard 的关系

这三者不能混成一个东西：

| 机制 | 判断什么 | 输出 | 能否替代其他机制 |
| --- | --- | --- | --- |
| 质量门 | 确定性检查是否通过，例如测试、lint、build、runtime smoke | 返回码、报告、`.workbench-validation/quality-gate-ok.json` | 不能替代业务验收和审查 |
| review | 行为风险、权限、数据、安全、架构、测试缺口 | `REVIEW.md` 或审查报告 | 不能替代可执行测试 |
| scorecard | 证据成熟度、状态一致性、硬阻塞、校准状态 | `scorecard-report.json`、`SCORECARD.md` | 不能证明代码、产品或架构正确 |

正确顺序是：

```text
先跑确定性验证
-> 再看 review 的 P0/P1
-> 再看 scorecard 的 decision/blockers/confidence
-> 最后看参考分
```

## scorecard 的边界

scorecard 只回答一个问题：

```text
当前项目工作台里的证据是否足够完整，状态是否一致，是否存在硬阻塞。
```

它不回答：

- 产品目标是否一定正确。
- 架构是否最优。
- UI 是否足够好。
- AI eval 是否覆盖所有真实失败。
- 代码没有 bug。
- 可以上线。

这些必须通过测试、人工验收、独立审查、真实运行、用户反馈和生产监控来判断。

## 为什么保留 scorecard，但不让它当裁判

完全不要评分，会失去一个好处：项目证据是否成熟、流程是否断裂、哪些阶段没有证据，很难被快速看见。

只保留一个总分，会制造另一个风险：AI 或使用者可能为了分数补空文档，或者用高分绕过测试失败、审查发现和人工确认。

所以工作台采用折中设计：

```text
脚本打分只看可检查证据
硬阻塞优先于分数
confidence 表达可信度
component floors 防止局部短板被总分掩盖
人工/独立审查负责语义质量
CALIBRATION.md 记录误判并反向改规则
```

这意味着 scorecard 的正确用途是发现证据缺口，不是给 AI 生成的代码背书。

## 为什么不是只给一个总分

OpenAI eval 指南强调，分数要和人工判断结合，不能只看数值；Anthropic 评估指南强调成功标准要具体、可测量，并优先选择更可靠的代码级或人工评估；SonarQube 质量门是用明确条件给出 pass/fail，不是让一个总分掩盖 blocker。

因此 Codex Workbench 的 scorecard 采用这个优先级：

```text
decision
-> blockers
-> confidence
-> component floors
-> reference score
```

含义：

| 项 | 作用 |
| --- | --- |
| `decision` | 直接告诉能不能继续、是否带风险 |
| `blockers` | 有硬阻塞时不能靠高分绕过 |
| `confidence` | 表示分数可信度，高分低可信度不能当通过 |
| 组件下限 | 防止总分掩盖产品、架构、验证等单项短板 |
| 参考分 | 只作为证据成熟度信号 |

## 参考权重为什么这样分配

默认权重不是统计结论，也不是永久标准。它是未校准前的启动权重，用来让项目第一次安装工作台后有一个可执行的证据审计口径。

权重设计不是让 AI 自己评价“做得好不好”，而是让审计脚本优先检查高风险证据是否存在。它遵循四条约束：

1. 项目方向和边界错误，会导致系统性返工，所以项目预处理、产品需求、架构设计不能太低。
2. AI 真正改代码发生在功能工作包里，所以功能工作包最高。
3. 验证失败应该直接阻塞，而不是在总分里扣一点，所以验证权重不需要最大。
4. 反馈闭环面向下一轮改进，不能替当前交付补分，所以反馈闭环最低。

设计原则：

1. 先保证方向正确：项目预处理、产品需求、架构设计各占 15。
2. 真实开发证据最高：功能工作包占 20。
3. UX 和交付计划重要，但项目差异较大：各占 10。
4. 验证失败必须走硬阻塞，所以验证硬门禁只占 10，不用软分数表达全部重要性。
5. 反馈闭环用于长期改进，只占 5，避免用“复盘写得好”掩盖当前需求、设计或验证缺口。

默认权重：

| 维度 | 权重 | 设计理由 | 如果缺失会发生什么 |
| --- | ---: | --- | --- |
| 项目预处理 | 15 | 先确认项目目标、用户、第一版范围、数据、权限和 AI 边界 | 项目方向错，后面写得越多返工越大 |
| 产品需求 | 15 | PRD、用户故事、验收标准决定功能是否做对 | 功能实现了，但不是用户真正要的 |
| 交互/原型 | 10 | 用户路径、页面状态、错误反馈决定是否可用 | 用户可见功能容易出现流程断裂和体验缺口 |
| 架构设计 | 15 | 模块、数据、API、AI 边界错误会导致高风险返工 | 权限、数据、扩展性、AI 工具边界容易混乱 |
| 交付计划 | 10 | 版本、任务、验证、回滚决定能否可控交付 | 代码写完但无法判断版本范围和发布风险 |
| 功能工作包 | 20 | AI 真实开发发生在这里，必须追踪规格到验证的证据链 | 大功能失控，改动依据、任务和验证无法复查 |
| 验证硬门禁 | 10 | 验证重要性主要由 blocker 和质量门表达，不靠分数慢慢扣 | 缺测试、缺质量门、缺运行证据 |
| 反馈闭环 | 5 | 反馈是长期改进信号，不能补偿当前交付证据不足 | 同类错误反复发生，但不能用反馈分掩盖当前失败 |

## 为什么不是平均分

平均分的问题是默认每个维度同等重要，但真实开发风险不是平均分布：

- 功能工作包是 AI 实际动手的位置，缺失时风险最高。
- 项目预处理、产品需求和架构设计决定方向和边界，错了会产生系统性返工。
- 验证如果失败，应直接成为 blocker，而不是只扣一点分。
- 反馈闭环很重要，但它面向下一轮改进，不能抵消当前项目证据缺口。

所以工作台采用“加权参考分 + 硬阻塞 + 组件下限”的组合，而不是平均分。

## 为什么验证只占 10 但仍然最重要

验证硬门禁只占 10，不是因为验证不重要，而是因为验证失败不应该靠分数处理。

验证失败时应该直接进入：

```text
BLOCKED
-> 修复验证失败
-> 重新运行质量门
-> 更新 VERIFY.md / REVIEW.md
```

如果把验证权重调到 30 或 40，反而可能让人以为“验证只是在总分里占比很大”，但仍允许其他维度补分。工作台故意把验证拆成两层：

- 质量门和 blocker：决定能不能继续。
- 参考分 10：表示验证证据成熟度。

## 为什么反馈闭环只占 5

反馈闭环很重要，但它是长期改进信号。一个项目不能因为 `FAILURE_LOG.md` 写得好，就掩盖当前 PRD、架构、功能验证不足。

反馈闭环的正确作用是：

```text
真实失败
-> 记录根因
-> 判断能否自动化
-> 改模板/测试/质量门/CI/hook/review
-> 下一次减少同类失败
```

它不能用来给当前交付“补分过关”。

## 什么时候调整权重

默认权重必须根据项目类型和真实误判校准。调整要写入 `workbench/scorecard/CALIBRATION.md`，不能只在聊天里说。

常见调整：

| 项目类型 | 建议调整 |
| --- | --- |
| UI/产品体验重的项目 | 提高交互/原型权重，提高浏览器验证和人工 UX 复核要求 |
| 后端/API/基础设施项目 | 提高架构设计、验证硬门禁、交付计划权重 |
| AI/RAG/Agent 项目 | 提高 AI 设计、eval、工具调用、数据来源、人工确认相关证据要求 |
| 已有成熟项目做小功能 | 降低 0 到 1 文档权重，提高功能包、验证、review、反馈权重 |
| 安全/权限/隐私敏感项目 | 把相关审查和测试提升为 blocker，而不是只调分 |

调整权重前必须回答：

1. 这个项目的主要失败风险是什么。
2. 哪些证据能提前发现这种失败。
3. 这次调整是基于真实误报/漏报，还是只是主观偏好。
4. 调整后如何验证没有制造新的刷分空间。

## 怎么校准评分，减少幻觉

校准记录放在：

```text
workbench/scorecard/CALIBRATION.md
```

校准不是“调高分数”，而是让 scorecard 更接近真实审查结论。

推荐步骤：

1. 选 3-5 个真实功能包作为锚定样例：一个低质量、一个中等、一个可发布、一个高风险。
2. 人工或独立审查先给结论：能不能交付、风险在哪里、缺什么证据。
3. 运行 scorecard，对比脚本结论。
4. 如果脚本高分但人工认为不能交付，记录 false positive。
5. 如果脚本低分但人工确认可继续，记录 false negative。
6. 根据误判调整模板、硬阻塞、组件下限、权重或脚本。
7. 再跑一次验证，记录调整原因。

误判处理：

| 误判 | 说明 | 应该怎么改 |
| --- | --- | --- |
| 高分低质 | 文档结构完整，但业务、架构、验证或权限有严重问题 | 增加 blocker、组件下限、review 清单、测试或质量门 |
| 低分可用 | 脚本要求了不适合当前项目的证据 | 调低对应权重或把要求改成条件触发 |
| 空文档刷分 | 文件存在但没有有效内容 | 增加关键字段检查、状态检查和人工复核 |
| AI 自评过关 | 没有真实命令输出或人工确认 | 要求质量门、CI、日志、截图、报告或验收记录 |

## 谁来判断分数是否可信

分数可信度不能由同一个 AI 在同一轮里自我保证。工作台要求把判断拆开：

| 判断对象 | 主要判断者 | 证据 |
| --- | --- | --- |
| 文件是否存在、状态字段是否合法、是否有 open blocker | 脚本 | `scorecard-report.json` |
| 测试、lint、build、runtime smoke 是否通过 | 项目质量门、CI | 命令输出、报告、`quality-gate-ok.json` |
| 产品、UX、架构、安全、AI eval 是否合理 | 人工或独立 AI review | `SCORECARD.md`、`REVIEW.md`、PR 评论 |
| scorecard 是否误判 | 人工抽查 + 锚定样例 | `CALIBRATION.md` |
| 同类失败是否需要升级工作台 | 维护者 | `FAILURE_LOG.md`、`IMPROVEMENT_LOG.md` |

同一个 AI 可以协助填写材料，但不能只凭自己的结论宣布评分可靠。至少要有可复查证据；高风险交付还要有人或独立审查确认。

## 什么情况必须升级工作台

本节只说明升级触发条件。完整升级闭环、证据位置、版本发布规则见 [ITERATION_UPGRADE.md](ITERATION_UPGRADE.md)。

出现以下情况，不要只补 Markdown，要考虑升级模板、脚本、质量门、CI、hook 或审查规则：

- 同类 bug 第二次出现。
- AI 多次绕过同一个需求澄清点。
- Review 多次漏掉权限、数据归属、AI 自动生效或回滚风险。
- scorecard 多次高分但人工认为不能交付。
- scorecard 多次阻塞但人工确认可以继续。
- 用户每次都要重复提醒同一条规则。

升级顺序：

```text
补充模板字段
-> 补充审查清单
-> 增加脚本检查
-> 接入测试/lint/typecheck/build
-> 接入 pre-commit/CI
-> 必要时加入 Codex hook
```

判断标准：

| 问题 | 优先升级位置 |
| --- | --- |
| 需求总是不清楚 | `PROJECT_INTAKE.md`、`CLARIFY.md` 模板 |
| UI 总是不完整 | `UX_SPEC.md`、`PROTOTYPE.md`、浏览器验证清单 |
| 权限总是漏 | `REVIEW.md`、测试、质量门、CI |
| AI 输出缺少 eval | `AI_DESIGN.md`、AI eval、`VERIFY.md` |
| 测试经常没跑 | `quality_gate.py`、CI、pre-commit |
| 分数误导交付 | `RUBRIC.md`、`CALIBRATION.md`、scorecard 脚本、README 表述 |

## 迭代升级闭环

工作台升级要按证据闭环执行，而不是靠感觉改文档。推荐流程：

```text
收集证据
-> 分类失败
-> 判断升级层级
-> 修改对应机制
-> 运行验证
-> 记录维护证据
-> 决定是否发布版本
```

| 步骤 | 要回答的问题 | 证据位置 |
| --- | --- | --- |
| 收集证据 | 真实发生了什么，影响了哪个项目、功能或使用者 | `VERIFY.md`、`REVIEW.md`、`FAILURE_LOG.md`、`scorecard-report.json` |
| 分类失败 | 是需求、UX、架构、测试、review、质量门、scorecard、skill 路由还是发布问题 | `workbench/feedback/FAILURE_LOG.md` |
| 判断升级层级 | 只改当前项目，还是要改模板/脚本，还是要发插件版本 | 项目反馈 + 插件维护日志 |
| 修改机制 | 应该改 Markdown、模板、脚本、质量门、CI、hook 还是版本说明 | 对应文件 |
| 运行验证 | 怎么证明这次升级没有制造新问题 | `package-check`、`self-test`、`golden-test`、项目质量门 |
| 记录证据 | 为什么升级、参考什么、改了什么、验证结果是什么 | `docs/maintenance/IMPROVEMENT_LOG.md` |
| 决定版本 | patch、minor、major 哪一种 | `plugin.json`、README、发布说明 |

判断升级层级：

| 情况 | 只改项目 | 改工作台模板/脚本 | 发插件版本 |
| --- | --- | --- | --- |
| 单个功能需求变了 | 是 | 否 | 否 |
| 单个项目的特殊架构约束 | 是 | 否，除非常见 | 否 |
| 同类需求澄清问题出现两次以上 | 否 | 是 | 通常是 patch/minor |
| 质量门漏掉关键验证 | 否 | 是 | 通常是 patch/minor |
| scorecard 高分低质 | 否 | 是，改 rubric/calibration/blocker | 通常是 patch |
| 生成文件契约变化 | 否 | 是 | minor 或 major |
| 移除或改变公开流程 | 否 | 是 | major |

这个闭环参考三个公开工程做法：

- Agent improvement loop：从 traces、人工反馈和 eval 生成下一轮改进，而不是凭印象改。
- Iterative repair loop：review、repair、validation 分离，每一轮都保存记录，剩余 delta 成为下一轮输入。
- SRE postmortem：失败复盘必须有事实、根因、影响、具体 action item、owner、优先级和可验证完成标准。

## 证据放哪里

项目证据：

| 证据 | 位置 |
| --- | --- |
| 项目目标、用户、范围、AI 边界 | `PROJECT_INTAKE.md` |
| 产品需求和验收标准 | `workbench/product/PRD.md` |
| UX/原型和用户路径 | `workbench/design/` |
| 架构、数据、API、AI 设计 | `workbench/architecture/` |
| 单功能规格和验证 | `workbench/features/<feature-name>/` |
| 质量门和 scorecard 报告 | `.workbench-validation/` |
| AI 失败和重复问题 | `workbench/feedback/` |
| scorecard 误报/漏报 | `workbench/scorecard/CALIBRATION.md` |

插件自身维护证据：

| 证据 | 位置 |
| --- | --- |
| 为什么升级、参考了什么、改了哪些文件 | `docs/maintenance/IMPROVEMENT_LOG.md` |
| 重复失败模式 | `docs/maintenance/FAILURE_PATTERNS.md` |
| 长期架构或发布决策 | `docs/maintenance/adr/` |
| 机器生成检查报告 | `.workbench-validation/` |

`.workbench-validation/` 是机器生成报告目录，不适合放长期人工维护说明。

## 参考资料

- GitHub README: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes
- Diataxis: https://diataxis.fr/
- OpenAI Codex best practices: https://developers.openai.com/codex/learn/best-practices
- OpenAI Codex skills: https://developers.openai.com/codex/skills
- OpenAI agent improvement loop: https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop
- OpenAI Codex iterative repair loop: https://developers.openai.com/cookbook/examples/codex/build_iterative_repair_loops_with_codex
- OpenAI evaluation best practices: https://developers.openai.com/api/docs/guides/evaluation-best-practices
- Anthropic eval guidance: https://docs.anthropic.com/en/docs/build-with-claude/develop-tests
- GitHub Spec Kit: https://github.com/github/spec-kit
- SonarQube quality gates: https://docs.sonarsource.com/sonarqube-server/quality-standards-administration/managing-quality-gates/introduction-to-quality-gates
- Google SRE postmortem culture: https://sre.google/workbook/postmortem-culture
- Semantic Versioning: https://semver.org
- Brown University rubric guidance: https://sheridan.brown.edu/resources/course-design/feedback-student-learning/grading-criteria-rubrics/designing-grading
