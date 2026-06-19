# {{PROJECT_NAME}} 功能工作包流程

本文件定义单个功能从变更请求到交付复盘的 2.0.0 状态机。目标不是让每个小改动都填满文档，而是让 AI 写代码前知道边界，写完后能拿出证据。

## 状态机

```text
CLASSIFY
-> BASELINE_CHECK
-> CHANGE
-> IMPACT
-> ROUTE
-> PLAN
-> IMPLEMENT
-> VERIFY
-> REVIEW
-> GATE
-> LEARN
-> DONE
```

`FEATURE_STATUS.json` 记录机器状态索引；Markdown 负责解释和证据。不要手写 JSON 来绕过流程，`quality_gate.py` 会用 Markdown、git diff、验证证据和状态 JSON 交叉校验。

## 流程强度

### light

适用：小文案、小样式、小 bug、低风险单文件修改。

要求：

- 可以不创建完整 feature package。
- 必须在 `workbench/delivery/CHANGE_LOG.md` 记录 `change_id`、`scope`、`risk`、`validation`、`evidence`、`reviewer`、`gate_marker`。
- 必须有最小验证证据。
- 不能影响数据、权限、API、AI 输出、发布、依赖或跨模块行为。

### standard

适用：普通功能、单模块改动、用户可见但风险边界清楚的修改。

要求：

- 建立 `workbench/features/<feature-name>/`。
- 必须有 `CHANGE_REQUEST.md`、`IMPACT_ANALYSIS.md`、`PLAN.md`、`TASKS.md`、`VERIFY.md`、`REVIEW.md`。
- `SPEC.md` 和 `DESIGN.md` 用于承接功能级需求和设计，不能替代长期 PRD、UX、ARCH。
- 完成前必须运行可用质量门或说明验证缺口。

### strict

适用：跨模块、数据、权限、公开 API、AI/RAG/Agent、架构、发布、CI/CD、依赖升级、安全/隐私、不可逆操作。

要求：

- 完整 feature package。
- `IMPACT_ANALYSIS.md` 必须说明是否影响 PRD、UX、API、DATA、AI、TEST、RELEASE、TRACEABILITY。
- 必须更新 `workbench/delivery/TRACEABILITY.md`，或明确说明不受影响。
- 必须有验证证据、review 证据和质量门证据。
- UI 任务需要截图、Playwright/a11y 或人工验收证据。
- AI/RAG/Agent 任务需要 eval、失败样例或工具调用证据。
- 如果无法完成自动化验证，不能只写原因，必须有 `accepted_risk`、用户确认、替代验证和 `deferred_follow_up`。

## hard triggers

命中任意一项，最低按 `strict` 处理：

- 数据库 schema、迁移、批量数据修改。
- 登录、认证、授权、角色、租户、权限边界。
- 支付、成绩、订单、核心业务记录、文件归属。
- 用户隐私、敏感数据、密钥、token、cookie、凭证。
- AI 生成内容会自动写入核心数据或影响用户权益。
- RAG 数据源、Agent 工具调用、模型输出策略或安全边界变化。
- 公开 API 合约、SDK、消息队列、事件结构。
- 跨多个模块、多个服务或核心业务流程。
- 生产部署、CI/CD、环境变量、基础设施。
- 依赖升级、feature flag、监控、日志、审计或合规变化。
- 删除、覆盖、不可逆操作。
- 需求不清但影响范围可能较大。

## 工作包目录

```text
workbench/features/<feature-name>/
├── CHANGE_REQUEST.md
├── IMPACT_ANALYSIS.md
├── SPEC.md
├── DESIGN.md
├── PLAN.md
├── TASKS.md
├── DECISIONS.md
├── IMPLEMENTATION_NOTES.md
├── VERIFY.md
├── REVIEW.md
├── CHANGELOG.md
└── FEATURE_STATUS.json
```

模板来源：

```text
workbench/feature-template/
```

## 阶段说明

### CLASSIFY

判断用户请求属于 light、standard 还是 strict。信息不足时先问，不要直接降级。

### BASELINE_CHECK

读取 `PROJECT_INTAKE.md`、`PROJECT_STATE.md`、product/design/architecture/delivery 基线。高风险实现前，关键基线不能是 draft 且不能有 open blocker。

### CHANGE

写 `CHANGE_REQUEST.md`：

- 目标。
- 范围。
- 非目标。
- 验收标准。
- 用户确认或阻塞问题。

### IMPACT

写 `IMPACT_ANALYSIS.md`：

- 是否影响 PRD。
- 是否影响 UX。
- 是否影响 API。
- 是否影响 DATA。
- 是否影响 AI/RAG/Agent。
- 是否影响权限、隐私、发布、测试或 `TRACEABILITY.md`。

第一次影响分析发生在实现前，不要求已有 git diff；实现后由 quality gate 再用 diff 校验影响分析是否准确。

### ROUTE

确认 `workflow_profile`：`light`、`standard` 或 `strict`。如果判断不清，升一级或问用户。

### PLAN

写 `SPEC.md`、`DESIGN.md`、`PLAN.md`、`TASKS.md`。进入实现前必须满足：

- `IMPACT_ANALYSIS.md` 已 ready 或 approved。
- `SPEC.md` 已 `approved_for_plan: true`。
- `DESIGN.md` 已 `approved_for_plan: true`。
- `PLAN.md` 已 `approved_for_implementation: true`。
- `TASKS.md` 已 `ready_for_implementation: true`。

### IMPLEMENT

只改计划覆盖范围。发现计划不对时，先停下更新 `DECISIONS.md`、`PLAN.md` 或 `IMPACT_ANALYSIS.md`，不要边写边扩大范围。

### VERIFY

写 `VERIFY.md`：

- 命令。
- 截图。
- 日志。
- API 响应。
- eval。
- 手工验收。
- 未验证项和风险。

strict 下未验证项必须有 `accepted_risk`、用户确认、替代验证和 `deferred_follow_up`。

### REVIEW

写 `REVIEW.md`：

- 检查 P0/P1。
- 检查是否偏离需求、UX、架构、权限和计划。
- 检查验证证据是否能证明验收，而不是只证明命令跑过。
- 写 `workbench_upgrade_assessment`：`required`、`deferred` 或 `not_required`。

### GATE

运行：

```bash
python workbench/quality/quality_gate.py --profile standard
```

通过后写入 `.workbench-validation/quality-gate-ok.json` 和 `.workbench-validation/quality-workflow-state.json`。runtime gate 的状态另写入 `.workbench-validation/runtime-state.json`；旧 marker 必须绑定当前 git diff，不能跨 diff 复用。

### LEARN

如果出现 AI 跳流程、漏验证、伪造状态、审查漏报、重复失败或 P0/P1，必须判断是否升级：

- 模板。
- 质量门。
- hook。
- CI。
- 测试。
- review prompt。
- `workbench/feedback/FAILURE_LOG.md`。

### DONE

只有验证、review、gate 和必要学习闭环完成后，才能声明完成。

## 追踪矩阵

`workbench/delivery/TRACEABILITY.md` 只做索引：

```text
ID -> 来源 -> 影响资产 -> 实现位置 -> 验证位置 -> 状态
```

更新分两步：

1. 在 `IMPACT_ANALYSIS.md` 写预计影响哪些 ID。
2. 在 `VERIFY.md` / quality gate 后，把矩阵状态更新为 `covered`、`partial`、`missing` 或 `n/a`。

## 防跳过规则

- 不要把 Markdown 当硬门禁。
- `FEATURE_STATUS.json` 不能作为唯一可信事实源。
- `quality_gate.py` 优先看独立事实：git diff、文件 hash、测试/CI 报告、状态 JSON、Markdown。
- 没有 bypass golden test 证明的拦截路径只能标记 `unverified`。
- 用户明确要求的安全删除可以走受控 bypass，但必须记录在 `workbench/runtime/BYPASS_LOG.md`。
