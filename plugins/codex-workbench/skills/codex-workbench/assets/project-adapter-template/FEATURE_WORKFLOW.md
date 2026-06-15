# {{PROJECT_NAME}} 功能工作包流程

本文件定义单个功能从需求到交付的 SDD 工作包流程。目标是让个人开发者也能按“规格驱动开发”的方式做出可验证、可审查、可维护的功能。

本项目工作台采用两层结构：

- 外层工作台：`AGENTS.md`、`WORKBENCH.md`、`REVIEW.md`、质量门、运行时检查和审计，负责项目治理。
- 内层 SDD：`workbench/features/<feature-name>/`，负责单个功能的 SPEC → CLARIFY → DESIGN → PLAN → TASKS → IMPLEMENT → VERIFY → REVIEW → ITERATE 闭环。

在两层之前还有预处理层：`PROJECT_INTAKE.md`。它负责把模糊项目需求整理成项目画像。功能工作包的 `SPEC.md` 应继承项目画像里的第一版范围、用户角色、权限边界、数据类型和 AI 边界。

核心原则：

- SPEC 是单功能事实源；DESIGN、PLAN、TASKS、实现、VERIFY 和 REVIEW 都必须能追溯到 SPEC。
- 需求变化时先改 SPEC，再同步 DESIGN、PLAN、TASKS、VERIFY、REVIEW 和 CHANGELOG；不要只在聊天记录里说明变化。
- 每个阶段都要留下能复查的证据：来源、判断、命令、结果、剩余风险。
- 能用脚本、测试、CI、hook 或质量门检查的问题，不只停留在 Markdown。

## 工作量分级门

不要所有任务都强制走完整 SDD。先检查硬触发器，再按影响范围、不确定性和回滚难度打分，最后选择流程强度。判断不清楚时自动升一级或先问用户，不能按低风险处理。

### 硬触发器

命中任意一项，最低按 L3 重量任务处理；如果已经是生产事故、安全漏洞、数据损坏或服务不可用，按 L4 紧急/重大任务处理。

- 数据库 schema、迁移、批量数据修改。
- 登录、认证、授权、角色、租户、权限边界。
- 支付、成绩、订单、核心业务记录、文件归属。
- 用户隐私、敏感数据、密钥、token、cookie、凭证。
- AI 生成内容会自动写入核心数据或影响用户权益。
- 公开 API 合约、SDK、消息队列、事件结构。
- 跨多个模块、多个服务或核心业务流程。
- 生产部署、CI/CD、环境变量、基础设施。
- 删除、覆盖、不可逆操作。
- 需求不清但影响范围可能较大。

### 风险打分

没有命中硬触发器时，再按三项打分。每项只能是 0、1、2、3 分。

| 维度 | 0 分 | 1 分 | 2 分 | 3 分 |
| --- | --- | --- | --- | --- |
| 影响范围 | 文档/注释 | 单文件 | 单模块 | 跨模块/核心流程 |
| 不确定性 | 需求清楚 | 少量假设 | 有未确认点 | 需求模糊 |
| 回滚难度 | 很容易 | 可手动回滚 | 回滚麻烦 | 不可逆/涉及数据 |

分级结果：

- 0-2 分：L1 轻量任务。
- 3-5 分：L2 中等任务。
- 6 分以上：L3 重量任务。
- 生产事故、安全漏洞、数据损坏、服务不可用：L4 紧急/重大任务。

### 分级证据

创建功能工作包时，必须在 `SPEC.md` 顶部填写：

- `risk_level: l1|l2|l3|l4`
- `impact_score: 0|1|2|3`
- `uncertainty_score: 0|1|2|3`
- `rollback_score: 0|1|2|3`
- `risk_score: 0-9`
- `hard_triggers: none` 或命中的触发器列表
- `classification_reason: ...`

AI 不能只写“这是轻量任务”。必须写出没有命中哪些硬触发器、为什么这个分数成立、为什么没有升级。

### L1 轻量任务

适用：

- 文案、样式、注释、README 小修。
- 单文件或极少文件的低风险 bugfix。
- 不改变公开 API、数据库、权限、AI 输出、支付/成绩/核心记录。

流程：

1. 说明问题是什么。
2. 说明改了哪里。
3. 运行最小可靠验证。
4. 说明剩余风险。

轻量任务可以不创建完整功能包，但不能跳过验证证据和风险说明。

### L2 中等任务

适用：

- 新增普通用户可见能力。
- 修改一个模块内的业务流程。
- 影响接口、页面、状态或测试，但风险边界清楚。

流程：

1. 建立 `workbench/features/<feature-name>/`。
2. 至少完成 `SPEC.md`、`CLARIFY.md`、`PLAN.md`、`VERIFY.md`。
3. `TASKS.md` 可简化为少量任务；`DECISIONS.md` 只记录真实取舍。
4. 通过质量门和必要审查后交付。

L2 不要求填满每个模板，但必须留下足够证据让下一个 AI 或人能复现：需求依据、实施计划、验证结果、未验证风险。

### L3 重量任务

适用：

- 新功能。
- 跨模块修改。
- 命中硬触发器的权限、数据、接口、数据库、AI 输出、支付/成绩/文件等高风险改动。
- UI 流程、后端接口、AI/RAG/Agent、集成第三方服务。

流程：

必须完整使用 `SPEC.md`、`CLARIFY.md`、`PLAN.md`、`TASKS.md`、`DECISIONS.md`、`CHECKLIST.md`、`VERIFY.md`、`REVIEW.md`。

### L4 紧急/重大任务

适用：

- 生产事故。
- 安全漏洞。
- 数据损坏或数据泄露。
- 服务不可用。
- 需要立即止血的高影响缺陷。

流程：

可以先做最小止血修复，但不能免除记录。事后必须补齐影响范围、修复说明、验证证据、审查结果、复盘结论和防复发自动化。

低风险小修可以简化，但仍要满足 `PRODUCT_BASELINE.md` 的产品下限。任务升级信号包括：需求不清、影响范围扩大、验证无法运行、出现 P0/P1 审查问题、同类 bug 重复出现。

## 适用范围

本流程处理需要留下规格、计划、验证或审查证据的功能工作。是否创建完整功能包由上面的工作量分级门决定。

## 工作包目录

每个重要功能建议复制模板：

```text
workbench/features/<feature-name>/
├── SPEC.md
├── CLARIFY.md
├── DESIGN.md
├── PLAN.md
├── TASKS.md
├── DECISIONS.md
├── IMPLEMENTATION_NOTES.md
├── CHECKLIST.md
├── VERIFY.md
├── REVIEW.md
└── CHANGELOG.md
```

模板来源：

```text
workbench/feature-template/
```

## 状态字段

功能工作包不是普通笔记。模板顶部的状态字段会被质量门和审计读取：

- `CHECKLIST.md` 的 `feature_status` 控制功能包是否参与交付门禁。
- `active` 表示正在推进，不能作为最终交付通过质量门。
- `on_hold` 表示暂停或暂存，质量门只检查结构，不要求完成。
- `complete` 表示准备交付，必须满足 SPEC、CLARIFY、PLAN、TASKS、VERIFY、REVIEW 的通过状态。
- `current_stage` 表示当前阶段，只能是 `spec`、`clarify`、`design`、`plan`、`tasks`、`implement`、`verify`、`review`、`complete`。
- 各阶段文档也有 `status`：`SPEC.md` 用 `draft|approved|blocked`，`CLARIFY.md` 用 `blocked|ready|deferred`，`PLAN.md` 用 `draft|approved|blocked`，`TASKS.md` 用 `draft|ready|blocked`，`VERIFY.md` 用 `missing|partial|passed|failed|blocked`，`REVIEW.md` 用 `pending|passed|failed|blocked`。
- `implementation_allowed` 和 `delivery_allowed` 只有在有证据时才能改成 `true`。

不要为了通过质量门直接改状态。状态变化必须有对应的 SPEC、澄清、计划、任务、验证和审查证据。

状态顺序由质量门和审计检查：

- 进入 `plan` 前，`SPEC.md` 必须 `status: approved` 且 `approved_for_plan: true`，`CLARIFY.md` 必须 `status: ready|deferred` 且 `ready_for_plan: true`，`DESIGN.md` 必须 `status: approved` 且 `approved_for_plan: true`。
- 进入 `tasks` 前，`PLAN.md` 必须 `status: approved` 且 `approved_for_tasks: true`。
- 进入 `implement` 前，`PLAN.md` 必须 `approved_for_implementation: true`，`TASKS.md` 必须 `status: ready` 且 `ready_for_implementation: true`。
- 进入 `review` 前，`VERIFY.md` 必须 `status: passed`。
- 进入 `complete` 前，`REVIEW.md` 必须 `status: passed`。

## 阶段 1：SPEC

先写 `SPEC.md`，不要直接写代码。

写 SPEC 前先检查 `PROJECT_INTAKE.md`：

- 如果项目画像是 draft，先补齐项目目标、第一版范围、用户和权限。
- 如果有 open 阻塞问题，先关闭或说明为什么当前功能不受影响。
- 如果需求变更影响项目方向，先更新项目画像，再更新功能 SPEC。

必须明确：

- 用户目标。
- 范围内和范围外。
- 输入、输出、状态变化。
- 角色、权限、数据归属。
- 验收标准。
- 失败场景。
- AI 生成内容是否需要人工确认。

需求不清时先问；不能把猜测当规格。

完成后，只有验收标准、边界和失败路径清楚时，才能把 `approved_for_plan` 改成 `true`。

## 阶段 2：CLARIFY

用 `CLARIFY.md` 处理需求缺口。

必须分类：

- 阻塞问题：不回答会改变实现路线、权限、数据、验收或风险。
- 可默认问题：可以按项目惯例先假设，但要写明假设。
- 已确认答案：用户、代码、测试、README、CI 或产品文档能证明的事实。

仍存在阻塞问题时，不进入 `PLAN.md`。

没有阻塞问题并且结论有证据后，才能把 `ready_for_plan` 改成 `true`。

## 阶段 3：DESIGN

用 `DESIGN.md` 把需求转成可计划的产品、交互、架构和验证设计。

必须明确：

- 对应 PRD、UX、原型、架构、数据、API、AI 设计。
- 页面、组件、流程、状态、失败路径和权限不足状态。
- 模块、数据模型、接口、权限、AI 输入输出和日志边界。
- 设计风险、人工确认点、ADR 需要。

如果没有 UI、API、数据或 AI 影响，也要明确写“确认不涉及”，不能留空。

设计通过后，才能把 `approved_for_plan` 改成 `true`。

## 阶段 4：PLAN

再写 `PLAN.md`。

必须明确：

- 技术方案。
- 影响文件和模块。
- 数据结构、接口、状态或页面变化。
- 风险和回滚策略。
- 验证方式。

高风险计划应先让人确认。

计划经过确认后，才能把 `approved_for_tasks` 和 `approved_for_implementation` 改成 `true`。

## 阶段 5：TASKS

把 `PLAN.md` 拆成 `TASKS.md`。

任务必须小、可执行、可验证。避免“完成整个系统”这种大任务。

推荐任务粒度：

- 更新数据模型或类型。
- 更新服务/接口。
- 更新 UI。
- 增加测试或 smoke。
- 更新文档。
- 运行验证和审查。

任务可逐项执行和验证后，才能把 `ready_for_implementation` 改成 `true`。

## 阶段 6：DECISIONS

用 `DECISIONS.md` 记录关键设计取舍。

需要记录：

- 架构、数据模型、API、权限、AI/RAG、UI 交互、依赖或部署决策。
- 为什么选这个方案。
- 放弃了什么替代方案。
- 对测试、回滚、兼容性和后续维护的影响。
- AI 做错后为什么要改变方案、为什么偏离计划、为什么新增规则或自动化。

如果实现偏离 `DESIGN.md` 或 `PLAN.md`，先更新 `DECISIONS.md`、`DESIGN.md` 和 `PLAN.md`，再继续写代码。

如果用户中途改需求，先判断改动是否影响 `PROJECT_INTAKE.md` 或当前 `SPEC.md`；影响时先更新事实源，再重算风险等级和验证计划。

## 阶段 7：CHECKLIST

用 `CHECKLIST.md` 做阶段门禁。

最低要求：

- SPEC 完整，验收标准可测试。
- CLARIFY 没有阻塞问题。
- DESIGN 覆盖 UX、架构、数据、API、权限和 AI 影响。
- PLAN 覆盖影响面、风险和验证方式。
- TASKS 是小步、可验证、可回滚。
- VERIFY 有真实命令或手工证据。
- REVIEW 没有未处理 P0/P1。

## 阶段 8：IMPLEMENT

按 `TASKS.md` 小步实现。

要求：

- 只改当前任务需要的文件。
- 沿用项目已有结构、组件、服务、异常处理和命名。
- 不提交临时调试、假数据、硬编码密钥或绕过逻辑。
- 每完成一组相关改动就检查 diff 和验证结果。
- 把 AI 主要改动、偏离计划和遇到的问题写入 `IMPLEMENTATION_NOTES.md`。

## 阶段 9：VERIFY

把验证记录写入 `VERIFY.md`。

至少记录：

- 运行的命令。
- 手工检查步骤。
- 浏览器/API/AI eval 证据。
- 失败命令、失败场景和复测结果。
- 未运行的验证和原因。
- 剩余风险。

代码项目没有任何验证证据时，默认不能算完成。

验证通过后，把 `status` 改成 `passed`；验证失败、阻塞或只完成部分验证时，分别使用 `failed`、`blocked` 或 `partial`。

## 阶段 10：REVIEW

用 `REVIEW.md` 和功能包内 `REVIEW.md` 复查。

重点看：

- 是否满足 SPEC。
- 是否越权或破坏数据归属。
- 是否破坏旧功能、接口或数据。
- 测试是否能在行为坏掉时失败。
- 是否有 AI 幻觉 API、字段、组件或配置。
- 是否需要把问题沉淀进质量门、测试、CI 或工作台规则。
- AI 做错时，记录审查发现、严重级别、触发场景、修复方向和是否仍阻塞交付。

审查通过且没有未处理 P0/P1 后，把 `status` 改成 `passed`。最终交付前，`CHECKLIST.md` 的 `delivery_allowed` 必须为 `true`。

## 阶段 11：ITERATE

如果 AI 写完后出现问题，不要只改代码。先归因：

- 需求错：改 `SPEC.md` 和 `CHANGELOG.md`。
- 交互错：改 `DESIGN.md`、`UX_SPEC.md` 或 `PROTOTYPE.md`。
- 架构错：改 `DESIGN.md`、`ARCHITECTURE.md`、`DECISIONS.md` 或 ADR。
- 计划错：改 `PLAN.md` 和 `TASKS.md`。
- 实现错：改代码并补 `IMPLEMENTATION_NOTES.md`。
- 验证错：改 `VERIFY.md`、测试或质量门。
- 审查漏：改 `REVIEW.md` 或独立审查提示。

修改后必须复测，并把结果写入 `CHANGELOG.md`、`VERIFY.md` 和 `REVIEW.md`。跨功能重复问题再汇总到 `workbench/feedback/AI_EFFECTIVENESS.md` 或 `FAILURE_LOG.md`。

## 失败证据归档

某个功能 AI 做错时，证据必须放回对应功能包：

- `VERIFY.md`：失败命令、失败场景、未验证项、复测结果和剩余风险。
- `REVIEW.md`：审查发现、严重级别、触发场景、修复方向和是否仍阻塞交付。
- `DECISIONS.md`：为什么改变方案、为什么偏离计划、为什么新增规则或自动化。

如果这个问题跨功能重复出现，或者应该沉淀成规则、测试、质量门、CI、hook 或模板改进，再把摘要写入 `workbench/feedback/FAILURE_LOG.md`。不要只把证据留在聊天记录或最终回复里。

## 人工确认点

必须人工确认的点：

- SPEC 不清楚。
- PLAN 涉及数据库、公开 API、权限、生产部署、凭证、用户数据或不可逆行为。
- AI 输出会自动影响核心数据。
- 验证无法运行但仍想交付。
- 审查发现 P0/P1。

## 简化规则

小 bugfix 可以不创建完整功能包，但最终仍要回答：

- 问题是什么。
- 改了哪里。
- 怎么验证。
- 还有什么风险。

如果同类 bug 重复出现，下一次必须升级为完整功能包流程。
