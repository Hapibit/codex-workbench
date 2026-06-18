# Codex Workbench 工作流与 Scorecard 说明

本文解释 Codex Workbench 2.0.0 为什么这样设计、完整工作流怎么走、scorecard 为什么不能当质量裁判，以及升级机制应该怎样根据真实证据迭代。

README 负责快速开始；本文负责解释设计口径。

## 核心结论

Codex Workbench 2.0.0 不是为了保证 AI 永远写对，而是把 AI coding 变成可检查的状态机：

```text
基线约束
-> 变更影响分析
-> 追踪矩阵
-> 计划和实现绑定
-> 验证证据
-> 审查
-> 质量门
-> 失败学习闭环
```

它能工程化保证的是：在已启用的受控入口内，跳流程、漏验证、乱改范围、伪造状态、旧 marker 复用和重复失败，应由 `runtime_gate.py`、`quality_gate.py`、CI 或 branch protection 基于独立证据暴露。Hook 是前置护栏，不是完整 enforcement boundary。

## 文档为什么这样拆

工作台文档按读者和用途拆开：

| 文档 | 类型 | 作用 |
| --- | --- | --- |
| `README.md` | overview + how-to | 快速理解、安装、第一次使用 |
| `docs/WORKFLOW_AND_SCORECARD.md` | explanation + reference | 解释工作流、quality gate、scorecard 和校准 |
| `docs/ITERATION_UPGRADE.md` | how-to + reference | 解释项目迭代、机制升级和版本发布 |
| `docs/USER_WORKBENCH.md` | how-to | 解释可选用户工作台模板 |
| `docs/maintenance/` | maintainer evidence | 维护日志、失败模式、ADR |
| 项目内 `workbench/**` | project evidence | 每个项目自己的事实、验证和复盘 |

`.workbench-validation/` 只放当前机器生成报告，不放长期人工解释。

## 2.0.0 完整工作流

状态机：

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

| 阶段 | 主要产物 | 质量口径 |
| --- | --- | --- |
| `CLASSIFY` | task type、risk level、profile | 风险和影响面必须可解释。 |
| `BASELINE_CHECK` | `PROJECT_INTAKE.md`、`PROJECT_STATE.md`、product/design/architecture/delivery 基线 | 高风险实现前不能依赖 draft intake 或 open blocker。 |
| `CHANGE` | `CHANGE_REQUEST.md` 或 `CHANGE_LOG.md` light 记录 | 写清目标、原因、范围、非目标和验收标准。 |
| `IMPACT` | `IMPACT_ANALYSIS.md` | 判断影响 PRD、UX、API、DATA、AI、TEST、RELEASE、TRACEABILITY。 |
| `ROUTE` | `light` / `standard` / `strict` | 命中 strict 触发条件时不能降级。 |
| `PLAN` | `PLAN.md`、`TASKS.md` | 实现范围、验证方式、风险和回滚要明确。 |
| `IMPLEMENT` | 代码或受控资产变更 | 只改计划覆盖范围。 |
| `VERIFY` | `VERIFY.md` | 必须有命令、截图、日志、测试、eval、CI 或人工验收证据。 |
| `REVIEW` | `REVIEW.md` | P0/P1 不能未解决，必须有 `workbench_upgrade_assessment`。 |
| `GATE` | `.workbench-validation/quality-gate-ok.json` | marker 绑定当前 `git_head`、`diff_hash`、feature 和证据。 |
| `LEARN` | `FAILURE_LOG.md`、模板/测试/gate/hook/CI 更新 | 重复失败不能只靠聊天提醒。 |

## Profile 分级

| Profile | 场景 | 最低要求 |
| --- | --- | --- |
| `light` | 小文案、小样式、低风险单文件 bug | `workbench/delivery/CHANGE_LOG.md` 有机器可读字段：`change_id`、`scope`、`risk`、`validation`、`evidence`、`reviewer`、`gate_marker`。 |
| `standard` | 普通功能、单模块业务改动 | 建功能包，至少完成 `CHANGE_REQUEST.md`、`IMPACT_ANALYSIS.md`、`PLAN.md`、`TASKS.md`、`VERIFY.md`、`REVIEW.md`、`FEATURE_STATUS.json`。 |
| `strict` | 跨模块、权限、数据、API、AI/RAG/Agent、架构、发布 | 完整功能包、`TRACEABILITY.md` 更新或豁免、质量门、独立审查或 CI 证据。 |

硬触发 `strict`：

- 数据库 schema、迁移、批量数据修改。
- 登录、认证、授权、角色、租户、权限边界。
- 隐私、敏感数据、密钥、token、cookie、凭证。
- AI 输出自动写入核心数据或影响用户权益。
- RAG 数据源、Agent 工具调用、prompt 安全边界。
- 公开 API、SDK、消息队列、事件结构。
- 生产部署、CI/CD、环境变量、基础设施。
- 删除、覆盖、不可逆操作。

## 修改已有功能时怎么做

需求变了，不是全量重写所有文档，也不是直接改代码。先用 `IMPACT_ANALYSIS.md` 判断影响哪些长期基线。

| 变化类型 | 先改哪里 | 再改哪里 |
| --- | --- | --- |
| 项目方向、用户、第一版范围变化 | `PROJECT_INTAKE.md`、`PROJECT_STATE.md` | 受影响的 product/design/architecture/delivery 文件 |
| 当前功能需求变化 | `CHANGE_REQUEST.md`、`IMPACT_ANALYSIS.md`、`SPEC.md` | `DESIGN.md`、`PLAN.md`、`TASKS.md`、`VERIFY.md` |
| 技术方案变化 | `DESIGN.md`、`DECISIONS.md` | 架构文档或 ADR |
| 验收标准变化 | `SPEC.md`、`VERIFY.md` | 测试、quality gate、review 清单 |
| AI 实现偏离计划 | `DECISIONS.md`、`IMPLEMENTATION_NOTES.md` | 复测写入 `VERIFY.md`，必要时写 `FAILURE_LOG.md` |

## 追踪矩阵

`TRACEABILITY.md` 只做索引，不复制 PRD、UX、API 或测试全文。

推荐结构：

```text
ID -> 来源 -> 影响资产 -> 实现位置 -> 验证位置 -> 状态
```

状态：

- `covered`：有实现和验证证据。
- `partial`：部分覆盖，必须说明缺口。
- `missing`：应覆盖但未覆盖，不能宣称完成。
- `n/a`：经影响分析确认不适用。

两阶段更新：

1. 在 `IMPACT_ANALYSIS.md` 写预计影响哪些 ID。
2. 在 `VERIFY.md` / quality gate 后更新 `TRACEABILITY.md` 状态。

## Quality Gate、Review、Scorecard 的关系

| 机制 | 判断什么 | 输出 | 边界 |
| --- | --- | --- | --- |
| `quality_gate.py` | diff、状态、证据、P0/P1、marker 新鲜度 | 返回码、报告、`.workbench-validation/quality-gate-ok.json` | 不能替代业务验收和人工判断。 |
| review | 行为风险、权限、数据、安全、架构、测试缺口 | `REVIEW.md` 或独立审查报告 | 不能替代可执行测试。 |
| scorecard | 证据成熟度、状态一致性、趋势和校准问题 | `scorecard-report.json`、`SCORECARD.md` | 不能证明代码、产品、UX 或架构正确。 |
| CI / branch protection | 合并前远程门禁 | status check | 未验证时只能标记 `unverified`。 |

正确顺序：

```text
blocker
-> 验证证据
-> review P0/P1
-> local gate / CI
-> scorecard 趋势
```

## Scorecard 为什么保留

完全不要 scorecard，会看不见证据成熟度和流程断点。只看总分，又会让 AI 或使用者用分数掩盖 blocker。

所以 2.0.0 的 scorecard 只做辅助审计：

- 文件是否存在。
- 状态是否一致。
- 证据是否足够。
- 是否有 component floor 低于要求。
- 是否有 false positive / false negative 需要校准。

它不能单独放行。P0/P1、质量门失败、无验证证据、伪造状态、旧 marker 复用，都不能靠高分抵消。

## 默认参考权重

权重是启动口径，不是科学真理，也不是永久标准。它帮助新项目快速发现证据缺口。

| 维度 | 权重 | 原因 |
| --- | ---: | --- |
| 项目预处理 | 15 | 项目目标、用户、范围、数据、权限和 AI 边界错了，会导致系统性返工。 |
| 产品需求 | 15 | PRD、用户故事、验收标准决定功能是否做对。 |
| UX/原型 | 10 | 用户路径、页面状态和错误反馈决定是否可用。 |
| 架构设计 | 15 | 模块、数据、API、AI 工具边界错误会导致高风险返工。 |
| 交付计划 | 10 | 版本范围、验证和回滚决定能否可控交付。 |
| 功能工作包 | 20 | AI 真实动手发生在这里，必须追踪规格到验证的证据链。 |
| 验证硬门禁 | 10 | 验证失败应成为 blocker，不靠分数慢慢扣。 |
| 反馈闭环 | 5 | 面向下一轮改进，不能抵消当前交付证据不足。 |

平均分不适合这里，因为真实开发风险不是平均分布。功能包、项目边界和架构错误的破坏性更大；验证失败应该直接阻断，而不是只扣分。

## 校准方法

校准记录放在：

```text
workbench/scorecard/CALIBRATION.md
```

步骤：

1. 选 3 到 5 个真实功能包作为锚定样例。
2. 人工或独立审查先给结论：能不能交付、风险在哪里、缺什么证据。
3. 运行 scorecard。
4. 如果脚本高分但人工认为不能交付，记录 false positive。
5. 如果脚本低分但人工确认可继续，记录 false negative。
6. 根据误判调整模板、硬阻塞、组件下限、权重或脚本。
7. 再跑验证并记录原因。

同一个 AI 可以辅助填写材料，但不能只凭自己的结论宣布评分可靠。

## 防止 AI 跳流程

2.0.0 不把防跳过写成普通目录，而是贯穿所有层：

| 层 | 能做什么 | 不能承诺什么 |
| --- | --- | --- |
| `AGENTS.md` / `WORKBENCH.md` | 提醒会话职责和流程 | 不能当硬门禁。 |
| `UserPromptSubmit` hook | 注入职责提醒 | 不能可靠阻断全部行为。 |
| `PreToolUse` hook | 粗拦截危险命令和明显越阶段写入 | 不能替代 diff 分类和质量门。 |
| `PermissionRequest` hook | 处理需要审批的权限请求 | 不能覆盖不触发审批的路径。 |
| `Stop` hook | 阻止草率结束，要求补 gate 或说明风险 | 不能撤销已经发生的文件改动。 |
| `runtime_gate.py` | 生成当前 workflow state | 不能信任 AI 手写状态。 |
| `quality_gate.py` | 交叉校验 Markdown、JSON、git diff、证据和 marker | 必须用独立事实，不信 AI 自述。 |
| CI / branch protection | 合并前最终门禁 | 未验证远程配置时只能写 `unverified`。 |

没有 bypass golden test 证明会失败的路径，不能写成“会拦截”。

## 证据放哪里

项目证据：

| 证据 | 位置 |
| --- | --- |
| 项目目标、用户、范围、AI 边界 | `PROJECT_INTAKE.md`、`PROJECT_STATE.md` |
| 产品需求和验收标准 | `workbench/product/PRD.md` |
| UX/原型和用户路径 | `workbench/design/` |
| 架构、数据、API、AI 设计 | `workbench/architecture/` |
| 单功能规格、计划、验证和审查 | `workbench/features/<feature-name>/` |
| 质量门和 scorecard 机器报告 | `.workbench-validation/` |
| AI 失败和重复问题 | `workbench/feedback/` |
| scorecard 误报/漏报 | `workbench/scorecard/CALIBRATION.md` |

插件维护证据：

| 证据 | 位置 |
| --- | --- |
| 为什么升级、参考了什么、改了哪些文件 | `docs/maintenance/IMPROVEMENT_LOG.md` |
| 重复失败模式 | `docs/maintenance/FAILURE_PATTERNS.md` |
| 长期架构或发布决策 | `docs/maintenance/adr/` |
| 当前机器检查报告 | `.workbench-validation/` |

## 参考资料

- OpenAI Codex customization: https://developers.openai.com/codex/concepts/customization
- OpenAI Codex hooks: https://developers.openai.com/codex/hooks
- OpenAI Codex iterative repair loop: https://developers.openai.com/cookbook/examples/codex/build_iterative_repair_loops_with_codex
- GitHub Spec Kit: https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/
- Git hooks: https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks
- GitHub protected branches: https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- NASA Requirements Management: https://www.nasa.gov/reference/6-2-requirements-management/
- Semantic Versioning: https://semver.org
