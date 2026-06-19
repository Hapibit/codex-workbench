# Codex Workbench 2.0.0 架构设计

本文是 Codex Workbench 2.0.0 的架构设计稿，用来指导模板、脚本、hook、quality gate、README 和发布包升级。当前发布包可能已经是 2.0.x（例如 2.0.3），实际落地状态以 README、脚本和 `.workbench-validation/package-check-report.json` 为准。它不是 1.2.0 的实现说明，也不代表设计中的所有目标都已经完全落地。

本文的边界：

- 负责定义 2.0.0 的定位、分层、状态机、目录契约、门禁原则和验收口径。
- 不负责给出 `quality_gate.py`、`runtime_gate.py`、hook 脚本或 CI workflow 的完整实现。
- 不负责替代后续模板文档、脚本设计文档、迁移手册、发布清单或 README。
- 第 11、14、15、18 节只保留“架构必须约束到哪些实现”的摘要级契约，详细实现应在对应脚本、模板和交付文档中展开。

2.0.0 的核心目标不是“保证 AI 永远写对”，而是把 AI 开发过程变成可检查、可追踪、可阻断、可复盘的工程流程：

```text
只要触碰受控范围，跳流程、漏验证、乱改范围、证据缺失、重复失败，
必须在已启用的受控入口内由 runtime gate、quality gate、CI 或 branch protection 基于独立证据判定失败；
hook 和 pre-commit 负责前置提醒或粗拦截，不能承诺覆盖所有路径。
没有被自动化绕过场景测试证明会失败的路径，只能标记为 unverified，不能宣称“会拦截”。
```

## 1. 设计结论

Codex Workbench 2.0.0 的定位是：

```text
SDLC 基线
+ AI Agent 状态机
+ 变更影响分析
+ 追踪矩阵
+ 验证证据链
+ 硬门禁
+ 失败学习闭环
+ 可信状态生成与校验
```

一句话定义：

```text
Codex Workbench 2.0.0 是一个面向 AI coding 的状态机工作台：
用基线和追踪矩阵约束需求正确性，
用影响分析约束变更正确性，
用验证证据约束实现正确性，
用 hooks 做前置提醒和粗拦截，用已启用的 runtime gate / quality gate / CI / branch protection 基于独立证据判定跳流程失败，
用失败复盘把 AI 错误沉淀成下一轮硬约束。
```

这里的“正确性”不是 AI 自我打分，而是工程证据：

- 需求是否有来源和验收标准。
- 设计是否覆盖用户路径、异常状态和权限边界。
- 架构是否定义模块、数据、API、AI 工具和回滚边界。
- 代码是否只实现已批准范围。
- 验证是否有命令、截图、日志、测试报告、eval 或人工审查证据。
- 审查是否没有未解决 P0/P1 问题。
- 失败是否沉淀到规则、模板、测试、质量门、hook、CI 或复盘日志。

## 2. 资料依据

2.0.0 的设计不是单纯依赖提示词，而是把公开资料中的工程原则落到文件、状态、脚本和门禁里。

| 资料 | 对 2.0.0 的启发 | 落地机制 |
| --- | --- | --- |
| OpenAI Codex customization | `AGENTS.md` 适合放仓库规则、运行命令和完成标准，但可靠质量仍要配合 linters、typecheckers、pre-commit hooks 等工程工具。 | `AGENTS.md` 只做入口规则；硬要求下沉到 hook、quality gate、CI。 |
| OpenAI Codex skills / plugins | 重复工作流应该沉淀为可分发的 skill / plugin，而不是每个项目重新手写提示词。 | 插件只暴露 `codex-workbench` 一个入口，内部封装模板、脚本和增强路由。 |
| OpenAI Codex hooks | hooks 可以在 Codex 生命周期中运行确定性脚本，用来提醒、阻断或检查工具使用；`PreToolUse` 阻断应使用 `permissionDecision: "deny"`、旧式 `decision: "block"` 或 exit code `2`，不能用 `continue:false` 当作 `PreToolUse` 阻断机制。 | `UserPromptSubmit`、`PreToolUse`、`PermissionRequest`、`Stop` 分别承担会话提醒、粗拦截、权限拦截和收尾检查。 |
| NASA requirements management | 需求要有 baseline、双向 traceability，变更要先做 impact assessment。 | 长期基线文档、`TRACEABILITY.md`、`CHANGE_REQUEST.md`、`IMPACT_ANALYSIS.md`。 |
| NASA Software Engineering Handbook | traceability 应连接需求、设计、代码、测试，并支持影响分析。 | 追踪矩阵只做索引，不复制全文：ID -> 来源 -> 实现 -> 验证 -> 状态。 |
| GitHub Spec Kit | spec-driven workflow 把规格、检查清单、计划、任务和实现分成阶段，避免直接从一句需求跳到代码。 | 状态机：`CLASSIFY -> BASELINE_CHECK -> CHANGE -> IMPACT -> ROUTE -> PLAN -> IMPLEMENT -> VERIFY -> REVIEW -> GATE -> LEARN -> DONE`。 |
| Martin Fowler 对 SDD 工具的分析 | workspace files、模板和 checklist 能改善 AI 协作，但 AI 解释 checklist 不是 100% 保证。 | Markdown 不作为唯一裁判；机器可读状态必须由脚本生成并由 quality gate 交叉校验。 |
| Git hooks 官方文档 | client-side hook 适合本地早发现问题，但不是最终强制策略；`pre-commit` 可以被 `--no-verify` 绕过，强制策略应放到服务端或远程门禁。 | hook 只做前置粗拦截；本地 gate、CI、required checks 和 branch protection 才承担最终放行职责。 |
| GitHub protected branches / status checks | 合并前可以要求状态检查通过，阻止不合格变更进入主分支。 | CI 和 branch protection 是最终合并门禁，不把本地 Markdown 当最终保证。 |

参考链接：

- OpenAI Codex customization: https://developers.openai.com/codex/concepts/customization
- OpenAI Codex skills: https://developers.openai.com/codex/skills
- OpenAI Codex hooks: https://developers.openai.com/codex/hooks
- NASA Requirements Management: https://www.nasa.gov/reference/6-2-requirements-management/
- NASA Software Engineering Handbook traceability: https://swehb.nasa.gov/plugins/viewsource/viewpagesrc.action?pageId=215777306
- GitHub Spec Kit: https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit
- Martin Fowler SDD tools analysis: https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html
- Git hooks: https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks
- GitHub protected branches: https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- GitHub status checks: https://docs.github.com/articles/about-status-checks

## 3. 设计原则

### 3.1 不能只靠软规则

Markdown、提示词、聊天约定只能提升 AI 遵守流程的概率，不能保证 AI 不跳过。2.0.0 必须把关键要求转成可执行检查：

| 规则类型 | 应该放哪里 | 原因 |
| --- | --- | --- |
| 解释性规则 | `AGENTS.md`、`WORKBENCH.md`、`FEATURE_WORKFLOW.md` | 让人和 AI 知道怎么工作。 |
| 阶段状态 | 由脚本生成的 JSON | 让工具能判断当前能否进入下一步。 |
| 前置护栏 | hook、pre-commit | 尽早提醒或粗拦截，但不能当最终保证。 |
| 硬判定规则 | runtime gate、quality gate、CI、branch protection | 基于独立证据判定失败或标记 `unverified`。 |
| 合并规则 | GitHub status checks、branch protection | 防止未验证代码进入主分支。 |

### 3.2 文档不是越多越好

1.2.0 暴露的问题之一是流程可能偏重。2.0.0 不应变成更多模板堆积，而应做到：

- 长期基线稳定：PRD、UX、架构、API、数据、AI 设计只在受影响时更新。
- 每次变更轻量：先用 `IMPACT_ANALYSIS.md` 判断影响哪些基线，不要求每次重写所有文档。
- 流程按风险分级：小改动走 light，普通功能走 standard，高风险走 strict。
- 证据必须真实：`VERIFY.md` 不能只写“已验证”，必须有命令、截图、报告、日志或人工确认。

### 3.3 机器状态不能由 AI 手写后直接信任

AI 可以写 Markdown 解释，但可信状态必须由脚本在当前 git 状态下生成。原因是：

- AI 可能忘记更新 JSON。
- AI 可能手写一个看似通过的状态。
- 旧的 `quality-gate-ok.json` 可能对应上一轮 diff。
- 文件内容变化后，之前的验证证据可能已经失效。

因此：

```text
Markdown = 解释、上下文、人工审查证据
JSON = 机器状态索引
quality_gate.py = 当前 git 状态下的可信裁判
CI / branch protection = 最终合并门禁
```

### 3.4 分层兜底必须可证明

“下一层会不会发现并拦截”不能停留在设计愿望。2.0.0 的验收口径是：

```text
每个关键跳流程场景，都必须有自动化绕过场景测试证明至少一层 gate 会失败。
没有测试证明的兜底链路，状态只能是 unverified。
```

每一层不能信任上一层的自述，必须检查独立信号：

- `git diff` 和受控资产路径。
- `diff_hash`、`git_head`、证据文件 hash。
- feature package 文件是否存在且状态一致。
- `CHANGE_REQUEST.md`、`IMPACT_ANALYSIS.md`、`PLAN.md`、`TASKS.md`、`VERIFY.md`、`REVIEW.md` 的必要字段。
- 测试、lint、typecheck、截图、eval、日志或 CI 报告。
- `TRACEABILITY.md` 覆盖状态。
- branch protection / required checks 的远程配置状态。

兜底关系按下表作为最小验收基线：

| 跳过场景 | 首层拦截 | 兜底拦截 | 验收测试 |
| --- | --- | --- | --- |
| 没有会话职责自检 | `UserPromptSubmit` 提醒 | `quality_gate.py` 检查 feature / change 证据 | `bypass-no-session-boundary` |
| 未建 `CHANGE_REQUEST.md` 就改受控代码 | `PreToolUse` 粗拦截 | `quality_gate.py` 基于 diff 失败 | `bypass-missing-change-request` |
| standard / strict 缺 `IMPACT_ANALYSIS.md` | runtime gate | `quality_gate.py` 失败 | `bypass-missing-impact-analysis` |
| 未到 `IMPLEMENT` 就写业务代码 | `PreToolUse` | `quality_gate.py` 检查阶段和 diff 不一致 | `bypass-implement-before-plan` |
| 手写或篡改 `FEATURE_STATUS.json` | runtime gate hash 校验 | `quality_gate.py` 交叉校验 Markdown / diff / hash | `bypass-forged-feature-status` |
| 旧 `quality-gate-ok.json` 继续复用 | `Stop` | `quality_gate.py` 检查 `diff_hash` 失效 | `bypass-stale-gate-marker` |
| `VERIFY.md` 只有“已验证”无证据 | `Stop` | `quality_gate.py` 检查无真实命令/报告/截图/eval | `bypass-empty-verify` |
| `REVIEW.md` 有未解决 P0/P1 | `Stop` | `quality_gate.py` / CI required check 失败 | `bypass-open-p0-p1` |
| 本地 hook / pre-commit 被绕过 | pre-commit 可能失效 | CI / branch protection 失败 | `bypass-no-verify-commit` |
| CI 或 branch protection 未配置 | audit 报告 `unverified` | 不能宣称远程合并受保护 | `audit-branch-protection-unverified` |

这些测试应进入 `golden test` 或 `self-test`，并在发布前运行。只有对应测试通过，文档、README、审计报告才能使用“会拦截”“会失败”这类确定性表述；否则只能说“设计要求拦截，但当前未验证”。

## 4. 顶层架构

2.0.0 是“五层架构 + 一个贯穿式控制面”。

```text
0. Agent Control / 防跳过控制面
1. 基础约束层
2. 追踪矩阵层
3. 变更执行层
4. 质量证据层
5. 学习升级层
```

`Agent Control` 不是普通第六层，也不应该新增 `workbench/agent-control/`。它是贯穿所有阶段的控制面，负责判断 AI 当前能做什么、不能做什么、何时必须停下。

### 4.1 Agent Control / 防跳过控制面

目标：防止 AI 把流程当背景说明。

组成：

- `AGENTS.md`：会话入口、职责边界、常驻规则。
- `WORKBENCH.md`：项目工作台规则。
- `PROJECT_STATE.md`：当前项目事实索引。
- `workbench/runtime/WORKFLOW_STATE.schema.json`：状态结构。
- `.workbench-validation/quality-workflow-state.json`：quality gate 生成的当前质量门状态。
- `.workbench-validation/runtime-state.json`：runtime gate 生成的运行时检查状态。
- hooks：对高风险工具行为做粗拦截。
- `quality_gate.py`：对 git diff、状态、证据做最终本地判定。
- CI / branch protection：对合并做最终门禁。

控制面只做两件事：

1. 判断当前阶段能不能进入下一步。
2. 发现跳流程、缺证据或越权改动时，前置护栏尽早提醒，硬判定层基于独立证据失败或标记 `unverified`。

### 4.2 基础约束层

目标：用长期基线约束 AI 行为，并让偏离项目目标、用户、范围、UX、架构、权限或 AI 边界的变更被影响分析、review 或 gate 暴露。

长期基线文件：

- `PROJECT_INTAKE.md`
- `PROJECT_STATE.md`
- `workbench/product/PRODUCT_BRIEF.md`
- `workbench/product/PRD.md`
- `workbench/product/ROADMAP.md`
- `workbench/design/UX_SPEC.md`
- `workbench/design/USER_FLOW.md`
- `workbench/design/PROTOTYPE.md`
- `workbench/architecture/ARCHITECTURE.md`
- `workbench/architecture/API_DESIGN.md`
- `workbench/architecture/DATA_MODEL.md`
- `workbench/architecture/AI_DESIGN.md`
- `workbench/architecture/adr/`

这些文件不是每次都要重写，而是作为“长期事实源”。如果变更影响它们，必须通过 `IMPACT_ANALYSIS.md` 指出需要更新的文件。

### 4.3 追踪矩阵层

目标：用可检查索引发现需求、设计、实现和验证之间的断链。

核心文件：

- `workbench/delivery/TRACEABILITY.md`

推荐只做索引，不复制详细内容：

| ID | 来源 | 影响文件 | 实现位置 | 验证位置 | 状态 |
| --- | --- | --- | --- | --- | --- |
| `REQ-001` | `PRD.md` | `API_DESIGN.md` | `src/...` | `VERIFY.md` | `covered` |
| `UX-003` | `UX_SPEC.md` | `PROTOTYPE.md` | `components/...` | screenshot / Playwright | `partial` |
| `AI-002` | `AI_DESIGN.md` | eval dataset | `agent/...` | eval report | `missing` |

状态建议：

- `covered`：已有实现和验证证据。
- `partial`：只覆盖部分路径，必须说明缺口。
- `missing`：应覆盖但未覆盖，不能宣称完成。
- `n/a`：经影响分析确认不适用。

### 4.4 变更执行层

目标：让任意修改都从“变更请求”开始，而不是从代码开始。

普通功能包：

```text
workbench/features/<feature-name>/
  CHANGE_REQUEST.md
  IMPACT_ANALYSIS.md
  SPEC.md
  DESIGN.md
  PLAN.md
  TASKS.md
  DECISIONS.md
  IMPLEMENTATION_NOTES.md
  VERIFY.md
  REVIEW.md
  CHANGELOG.md
  FEATURE_STATUS.json
```

注意：

- `SPEC.md` / `DESIGN.md` 是功能级增量说明，不能替代长期 `PRD.md` / `UX_SPEC.md` / `ARCHITECTURE.md`。
- `CHANGE_REQUEST.md` 说明为什么改、改什么、不改什么、验收标准。
- `IMPACT_ANALYSIS.md` 判断影响哪些长期基线、代码、测试、部署、AI 行为和追踪矩阵。
- `PLAN.md` 和 `TASKS.md` 通过后才能进入实现。
- `VERIFY.md` 和 `REVIEW.md` 通过后才能进入完成声明。

### 4.5 质量证据层

目标：不让 AI 用“我认为完成了”替代验证。

组成：

- `workbench/quality/quality_gate.py`
- `workbench/quality/quality-gate.ps1`
- `workbench/quality/quality-gate.sh`
- `workbench/runtime/runtime_gate.py`
- `workbench/scorecard/RUBRIC.md`
- `workbench/scorecard/SCORECARD.md`
- `workbench/scorecard/CALIBRATION.md`
- `workbench/review/independent-review-prompt.md`
- `.workbench-validation/`

质量证据层不追求一个漂亮总分。它优先回答：

- 有没有阻塞项。
- 哪些验证实际跑过。
- 哪些风险没有验证。
- 是否有 P0/P1 未解决问题。
- 当前 gate 结果是否对应当前 diff。

### 4.6 学习升级层

目标：让同类 AI 失误不只靠用户反复提醒。

组成：

- `workbench/feedback/FAILURE_LOG.md`
- `workbench/feedback/ITERATION_LOG.md`
- `workbench/feedback/AI_EFFECTIVENESS.md`
- `workbench/scorecard/CALIBRATION.md`
- 插件维护证据：`docs/maintenance/`
- 当前机器生成报告：`.workbench-validation/`

注意：`.workbench-validation/` 不是插件自身的长期学习升级层。它只适合保存当前机器、当前 git 状态下生成的检查报告、迁移报告和 gate marker。长期维护证据、失败模式、改进记录和 ADR 应放在 `docs/maintenance/`，避免把可删除的机器报告当成版本化知识库。

每个 `REVIEW.md` 必须包含：

```yaml
workbench_upgrade_assessment: required | deferred | not_required | unassessed
```

规则：

- `unassessed` 只允许出现在未完成阶段。
- `completed` / `failed` / `blocked` / `repeated-issue` 不能保持 `unassessed`。
- `required` 必须落到至少一个机制：规则、模板、质量门、hook、测试、CI、失败日志。
- `deferred` 必须有 owner、复查时间、风险说明和 failure log 记录。
- `not_required` 必须有理由和验证证据。

## 5. 目录契约

推荐 2.0.0 目录结构：

```text
AGENTS.md
WORKBENCH.md
PROJECT_INTAKE.md
PROJECT_STATE.md
REVIEW.md
DEVELOPMENT_FLOW.md
PRODUCT_BASELINE.md
FEATURE_WORKFLOW.md

workbench/
  product/
    PRODUCT_BRIEF.md
    PRD.md
    ROADMAP.md

  design/
    UX_SPEC.md
    USER_FLOW.md
    PROTOTYPE.md

  architecture/
    ARCHITECTURE.md
    API_DESIGN.md
    DATA_MODEL.md
    AI_DESIGN.md
    adr/

  delivery/
    CHANGE_LOG.md
    TRACEABILITY.md
    ITERATION_PLAN.md
    RELEASE_PLAN.md
    RELEASE_CHECKLIST.md
    TASK_BREAKDOWN.md

  feature-template/
    CHANGE_REQUEST.md
    IMPACT_ANALYSIS.md
    SPEC.md
    DESIGN.md
    PLAN.md
    TASKS.md
    DECISIONS.md
    IMPLEMENTATION_NOTES.md
    VERIFY.md
    REVIEW.md
    CHANGELOG.md
    FEATURE_STATUS.schema.json

  features/
    <feature-name>/
      CHANGE_REQUEST.md
      IMPACT_ANALYSIS.md
      SPEC.md
      DESIGN.md
      PLAN.md
      TASKS.md
      DECISIONS.md
      IMPLEMENTATION_NOTES.md
      VERIFY.md
      REVIEW.md
      CHANGELOG.md
      FEATURE_STATUS.json

  quality/
    quality_gate.py
    quality-gate.ps1
    quality-gate.sh

  runtime/
    WORKFLOW_STATE.schema.json
    BYPASS_LOG.md
    runtime_gate.py
    runtime-gate.ps1
    runtime-gate.sh

  scorecard/
    RUBRIC.md
    SCORECARD.md
    CALIBRATION.md
    scorecard.py

  review/
    independent-review-prompt.md

  feedback/
    FAILURE_LOG.md
    ITERATION_LOG.md
    AI_EFFECTIVENESS.md

  archive/
```

明确禁止：

- 不新增 `workbench/docs/` 作为工作台阶段目录。
- 根目录 `docs/` 可以作为普通项目文档，但不是工作台标准阶段。
- 不允许 AI 临时发明新的 workbench 顶层目录，除非同步升级模板、脚本、quality gate、hook 和回归测试。

## 6. 核心状态机

2.0.0 的工作流不是“先写一堆文档”，而是状态机：

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

| 阶段 | 输入 | 退出条件 |
| --- | --- | --- |
| `CLASSIFY` | 用户请求、当前会话职责、项目路径 | 得到 `task_type`、`risk_level`、`workflow_profile`。 |
| `BASELINE_CHECK` | `PROJECT_INTAKE.md`、`PROJECT_STATE.md`、product/design/architecture/delivery | 高风险实现前，关键基线不是 draft 且没有 open blocker。 |
| `CHANGE` | 用户目标、问题、变更原因 | `CHANGE_REQUEST.md` 写清目标、范围、非目标和验收标准。 |
| `IMPACT` | 变更请求、长期基线文件、当前项目状态 | `IMPACT_ANALYSIS.md` 判断预计影响 PRD、UX、API、DATA、AI、TEST、RELEASE、TRACEABILITY；实现后由 quality gate 再用 git diff 校验影响分析是否准确。 |
| `ROUTE` | 风险和影响面 | 选择 `light`、`standard` 或 `strict`。 |
| `PLAN` | 影响分析、项目结构 | `PLAN.md` / `TASKS.md` ready，且没有阻塞问题。 |
| `IMPLEMENT` | 通过的计划 | 只改计划覆盖范围，不顺手扩大范围。 |
| `VERIFY` | 实际改动 | `VERIFY.md` 记录命令、截图、测试、日志、eval 或人工验收。 |
| `REVIEW` | diff、验证证据、需求链路 | `REVIEW.md` 无未解决 P0/P1。 |
| `GATE` | 当前 git 状态、feature 状态、证据文件 | quality gate 通过并写入新鲜 marker。 |
| `LEARN` | review、失败、重复问题 | 完成 `workbench_upgrade_assessment`。 |
| `DONE` | gate marker、review、学习评估 | 可以声明完成。 |

## 7. 流程强度分级

流程强度按风险和影响面选择，避免每个小改动都走完整 SDD。

### 7.1 light

适用：

- 小文案。
- 小样式。
- 低风险 bug。
- 不影响 API、数据、权限、AI 行为和发布。

要求：

- 可以不建完整 feature package。
- 必须记录到 `workbench/delivery/CHANGE_LOG.md`。
- 必须有最小验证证据，记录在 `CHANGE_LOG.md` 的验证字段，或记录到轻量 `VERIFY` 条目中。

light 不是无流程，也不是免审通道。它只是把完整功能包压缩为“变更记录 + 最小验证证据”。如果 light 变更后来扩大到行为、接口、数据、权限、AI 或发布影响，必须升级为 `standard` 或 `strict`。

`CHANGE_LOG.md` 的 light 记录必须机器可读，最小字段：

```yaml
change_id:
scope:
risk:
validation:
evidence:
reviewer:
gate_marker:
```

没有这些字段，quality gate 只能把 light 记录当作普通说明文本，不能可靠判断它是否覆盖变更和验证。

### 7.2 standard

适用：

- 普通功能。
- 单模块行为变化。
- 影响用户路径但不涉及高风险边界。

要求：

- `CHANGE_REQUEST.md`
- `IMPACT_ANALYSIS.md`
- `PLAN.md`
- `TASKS.md`
- `VERIFY.md`
- `REVIEW.md`

### 7.3 strict

适用：

- 跨模块。
- 数据结构变化。
- 权限、认证、密钥、安全。
- API 合约变化。
- AI / RAG / Agent 行为变化。
- Agent 工具调用变化。
- RAG 数据源变化。
- 外部集成。
- 依赖升级。
- CI/CD 或部署配置变化。
- feature flag 变化。
- 监控、日志、审计变化。
- 合规、法律、隐私。
- 生产发布。
- 跨前后端或跨服务。
- 不可逆删除、迁移或数据清理。

要求：

- 完整 feature package。
- `TRACEABILITY.md` 更新或明确豁免。
- quality gate。
- 独立 review。
- CI 或等价验证。
- 高风险 AI 任务必须有 eval、失败样例或工具调用证据。
- UI 任务必须有截图、Playwright、a11y 或人工验收证据。
- strict 下不能仅靠“无法验证原因”放行；如果某项验证确实暂时无法完成，必须同时提供 `accepted_risk`、用户确认、替代验证和 `deferred follow-up`。

## 8. 受控资产

2.0.0 不只控制源码。以下文件变化也必须走 `CHANGE_REQUEST + IMPACT_ANALYSIS`：

```text
PROJECT_INTAKE.md
PROJECT_STATE.md
workbench/product/PRD.md
workbench/design/UX_SPEC.md
workbench/architecture/API_DESIGN.md
workbench/architecture/DATA_MODEL.md
workbench/architecture/AI_DESIGN.md
workbench/delivery/RELEASE_PLAN.md
workbench/delivery/TRACEABILITY.md
.github/workflows/*
Dockerfile
package.json
pyproject.toml
pom.xml
build.gradle
```

原因：

- 改 PRD 会改变需求真相源。
- 改 UX 会改变用户验收标准。
- 改 API / DATA 会影响调用方和迁移。
- 改 AI_DESIGN 会影响模型、提示词、工具、安全和评测。
- 改 CI/CD / Docker / 依赖文件会影响构建、部署和供应链。

## 9. Markdown + JSON 双轨

### 9.1 Markdown 的职责

Markdown 负责：

- 解释上下文。
- 记录人类决策。
- 说明验收标准。
- 保存验证证据。
- 写清风险、非目标和权衡。

Markdown 不负责：

- 充当可信状态数据库。
- 直接决定是否能合并。
- 作为唯一质量裁判。

### 9.2 JSON 的职责

JSON 负责给脚本和 CI 读取：

- 当前 active feature。
- 当前阶段。
- 当前 git 状态。
- diff hash。
- 证据文件 hash。
- gate 结果。
- 是否允许实现或交付。

关键修正：

```text
不要长期信任 `workbench/runtime/WORKFLOW_STATE.json`。
`workbench/runtime/` 只保留 `WORKFLOW_STATE.schema.json` 这类 schema / 脚本契约，
实际状态写入 `.workbench-validation/quality-workflow-state.json` 或 `.workbench-validation/runtime-state.json`，并由对应脚本生成或校验。
```

示例：

```json
{
  "git_head": "abc123",
  "diff_hash": "sha256:...",
  "feature_id": "FEATURE-001",
  "current_stage": "VERIFY",
  "implementation_allowed": false,
  "delivery_allowed": false,
  "source_hashes": {
    "CHANGE_REQUEST.md": "sha256:...",
    "IMPACT_ANALYSIS.md": "sha256:...",
    "PLAN.md": "sha256:...",
    "TASKS.md": "sha256:...",
    "VERIFY.md": "sha256:..."
  },
  "created_at": "2026-06-17T00:00:00Z"
}
```

`quality-gate-ok.json` 必须绑定当前 git 状态：

```json
{
  "git_head": "abc123",
  "diff_hash": "sha256:...",
  "feature_id": "FEATURE-001",
  "profile": "standard",
  "commands_run": ["npm test", "npm run lint"],
  "report_id": "qg-20260617-000001",
  "created_at": "2026-06-17T00:00:00Z"
}
```

以下任一变化都会让旧 marker 失效：

- git diff 变化。
- active feature 变化。
- `VERIFY.md` 变化。
- `REVIEW.md` 变化。
- `FEATURE_STATUS.json` 变化。
- 关键基线文件变化。

## 10. 防跳过控制面

防跳过不是一个目录，而是一组贯穿式控制。

### 10.1 `UserPromptSubmit`

作用：

- 注入会话职责。
- 提醒当前是工作台配置、业务开发、资料搜索、文档写作、代码审查还是发布维护。
- 用户短指令如“开始”“继续”“优化”“发布”默认沿用当前职责。

限制：

- 只能提醒，不能可靠阻断全部行为。

### 10.2 `PreToolUse`

作用：

- 粗拦截危险命令。
- 粗拦截未进入 `IMPLEMENT` 就改业务代码。
- 粗拦截未声明的 workbench 顶层目录。

不能做：

- 不能只靠固定路径判断所有业务代码。
- 不能阻止用户明确要求的安全删除。
- 不能替代 `quality_gate.py`。
- 不能用 `continue:false` 当作 `PreToolUse` 阻断机制；正确阻断方式是返回 `permissionDecision: "deny"`、旧式 `decision: "block"`，或 exit code `2`。

建议保护范围不仅包括 `src/`，还包括：

```text
app/
apps/
backend/
frontend/
lib/
components/
packages/
infra/
config/
.github/workflows/
Dockerfile
package.json
pyproject.toml
pom.xml
build.gradle
```

### 10.3 `PermissionRequest`

作用：

- 拦截 Codex 即将发起审批的权限请求。
- 对需要审批的 sandbox、权限提升、网络或高风险操作做 allow / deny / no decision。
- 记录被允许的高风险审批原因、范围和后续验证。

原则：

- `PermissionRequest` 只覆盖会触发审批的请求，不能替代 `PreToolUse`、`quality_gate.py` 或 CI。
- 用户明确确认可以放行，但必须记录原因、范围和后续验证。

### 10.4 `Stop`

作用：

- 如果本轮有受控改动但没有新鲜 quality gate marker，触发继续收尾，要求补跑 gate 或说明无法验证原因。
- 如果有 P0/P1 review 未解决，禁止声明 `DONE`，要求继续修复或标记 blocked。
- 如果 `workbench_upgrade_assessment` 缺失，触发继续补齐。
- `Stop` 不能撤销已经发生的文件改动，它的职责是阻止草率结束、驱动补验证和禁止错误完成声明。

### 10.5 `quality_gate.py`

作用：

- 基于当前 git diff 做最终本地分类。
- 检查功能包、基线、追踪矩阵、验证证据、review、状态 JSON。
- 只有通过后才写 `.workbench-validation/quality-gate-ok.json`。

## 11. Quality Gate 契约摘要

本节只定义 `quality_gate.py` 必须承担的架构级职责和最小失败条件，不展开具体 Python 实现、解析器设计、报告 schema 或 CI workflow。详细实现应放到 `workbench/quality/` 的脚本和测试中。

2.0.0 的 `quality_gate.py` 至少检查：

1. `PROJECT_INTAKE.md` 不得是 draft，且无 open blocker。
2. 有业务代码或受控资产 diff 时，必须存在关联 feature package 或 light 变更记录。
3. `standard` / `strict` 必须有 `IMPACT_ANALYSIS.md`。
4. 进入 `IMPLEMENT` 前，`PLAN.md` / `TASKS.md` 必须 ready。
5. `VERIFY.md` 必须包含真实命令、截图、日志、测试、eval、CI 或人工验收证据；如果无法验证，必须写明原因、风险、替代验证和后续补偿动作。
6. `REVIEW.md` 不得有未解决 P0/P1。
7. `strict` 必须更新 `TRACEABILITY.md`，或明确说明不受影响。
8. UI 任务必须有截图、Playwright、a11y 或人工验收证据；strict 下缺失自动化验证时，必须有 `accepted_risk`、用户确认、替代验证和 `deferred follow-up`。
9. AI / RAG / Agent 任务必须有 eval、失败样例或工具调用证据；strict 下缺失 eval 时，必须有 `accepted_risk`、用户确认、替代验证和 `deferred follow-up`。
10. completed / failed / blocked / repeated issue 功能包必须完成 `workbench_upgrade_assessment`。
11. JSON 状态必须和 Markdown、git diff、证据报告交叉校验。
12. 旧 `.workbench-validation/quality-gate-ok.json` 必须在 git diff、active feature、证据文件或关键基线变化后失效。
13. `CHANGE_LOG.md` 的 light 记录必须机器可读，否则不能作为受控改动的有效证据。
14. 每个声明“会拦截”的跳流程路径必须有对应 bypass golden test；没有测试覆盖时，gate / audit 只能输出 `unverified`。
15. 通过后才写 `.workbench-validation/quality-gate-ok.json`。

质量门不是“评分器”。它的第一职责是阻断不合格状态。

`quality_gate.py` 的判定必须优先使用独立事实，而不是 AI 自述：

```text
git diff > 文件 hash > 测试/CI 报告 > feature 状态 JSON > Markdown 说明
```

如果 Markdown 与 diff、hash、测试报告或 CI 状态冲突，以独立事实为准。触发硬失败条件时 gate 必须失败；只有用户已接受风险、替代验证和 follow-up 已记录，且冲突不涉及伪造状态、缺关键证据或 P0/P1 未解决时，audit 才能输出 `PASS_WITH_RISK`。不能让 AI 手写说明覆盖机器证据。

quality gate / audit 报告还应记录远程合并保护状态：

```yaml
branch_protection: verified | unverified | not_applicable
```

只有通过 GitHub API、`gh` 或 CI 环境明确确认 required checks / branch protection 已启用时，才能写 `verified`。未验证时只能写 `unverified`，并把它表述为“建议配置”，不能宣称远程合并已被保护。

## 12. 评分机制的边界

2.0.0 不建议把“总分”作为是否完成的裁判。

更合理的定位：

- `scorecard` 用于辅助审计和趋势观察。
- `quality_gate.py` 用于硬判定。
- P0/P1 blocker 直接失败，不允许用高分抵消。
- 评分必须有校准记录，不能让 AI 自评后直接通过。

推荐原则：

| 机制 | 用途 | 是否能单独放行 |
| --- | --- | --- |
| `RUBRIC.md` | 说明审计维度 | 否 |
| `SCORECARD.md` | 记录本次审计结果 | 否 |
| `CALIBRATION.md` | 记录评分偏差和校准案例 | 否 |
| `quality_gate.py` | 检查 blocker、证据、状态和 diff | 可以作为本地放行依据 |
| CI status check | 合并前硬门禁 | 可以作为远程放行依据 |

因此，2.0.0 的策略不是“打高分证明质量好”，而是：

```text
先看是否有 blocker；
再看证据是否覆盖验收；
再看 review 是否无 P0/P1；
最后才用 scorecard 辅助发现质量趋势和校准问题。
```

## 13. 追踪矩阵与影响分析

需求、UX、架构、实现、测试之间要有可追踪关系，但不能让追踪矩阵变成复制粘贴的大文档。

### 13.1 `IMPACT_ANALYSIS.md`

每次 meaningful change 都要回答：

- 是否影响 PRD。
- 是否影响 UX。
- 是否影响 API。
- 是否影响 DATA。
- 是否影响 AI / RAG / Agent。
- 是否影响权限或隐私。
- 是否影响测试。
- 是否影响发布或回滚。
- 是否影响 `TRACEABILITY.md`。

### 13.2 `TRACEABILITY.md`

追踪矩阵只记录索引：

```text
ID -> 来源 -> 影响资产 -> 实现位置 -> 验证位置 -> 状态
```

不要把 PRD、UX、API、测试报告全文复制进矩阵。详细内容仍保留在原文件。

### 13.3 更新时机

两阶段更新：

1. 在 `IMPACT_ANALYSIS.md` 中写“预计影响哪些 ID”。
2. 在 `VERIFY.md` / quality gate 后，把 `TRACEABILITY.md` 状态更新为 `covered`、`partial`、`missing` 或 `n/a`。

这样可以减少反复修改需求文件导致的同步负担。

## 14. Bypass 治理契约

本节只定义绕过行为的治理边界。具体 hook 交互、审批提示、日志格式校验和过期清理逻辑，应在 runtime gate / hook 脚本和模板中实现。

绕过不能由 AI 自己决定。`BYPASS_LOG.md` 必须有固定字段：

```text
reason:
scope:
risk:
user_confirmation / approver:
expires_at:
follow_up:
```

原则：

- 用户明确要求的安全删除不应被永久阻断，但要做路径校验和范围确认。
- AI 不能用 bypass 逃避 feature package、验证或 review。
- bypass 必须有过期时间和后续补偿动作。
- 高风险 bypass 后必须进入 `LEARN`，判断是否需要升级 hook 或质量门。

## 15. 迁移策略摘要

本节只定义 1.2.0 -> 2.0.0 的安全迁移原则。完整迁移命令、冲突处理、备份格式和报告 schema，应在升级脚本和迁移手册中展开。

1.2.0 升级到 2.0.0 不能直接覆盖用户项目文档。

推荐迁移命令行为：

```text
upgrade --dry-run
safe add
script refresh
doc replace
migration-report.json
```

### 15.1 `upgrade --dry-run`

默认只预览：

- 将新增哪些文件。
- 将修改哪些文件。
- 哪些文件冲突。
- 哪些目录不符合契约。
- 哪些旧 marker 或旧状态需要迁移。

### 15.2 safe add

只新增缺失的非冲突文件，例如：

- `PROJECT_STATE.md`
- `TRACEABILITY.md`
- `CHANGE_LOG.md`
- schema 文件
- 新 feature-template 文件

### 15.3 script refresh

刷新机器生成脚本，例如：

- `quality_gate.py`
- `runtime_gate.py`
- `scorecard.py`

必须经过用户确认，因为脚本会影响门禁行为。

### 15.4 doc replace

替换已有项目文档风险最高，默认不执行。

只有用户明确确认后，才允许：

- 替换项目 `AGENTS.md`。
- 替换 `WORKBENCH.md`。
- 替换 `FEATURE_WORKFLOW.md`。
- 替换已有 product/design/architecture/delivery 文档。

### 15.5 migration report

迁移后写入：

```text
.workbench-validation/migration-report.json
```

至少包含：

- 迁移前版本。
- 迁移后目标版本。
- 新增文件。
- 修改文件。
- 跳过文件。
- 冲突文件。
- 用户确认项。
- 剩余风险。

## 16. 真实使用流程

### 16.1 从 0 到 1 新项目

```text
用户自然语言提出项目
-> CLASSIFY
-> PROJECT_INTAKE.md
-> product / design / architecture / delivery 基线
-> TRACEABILITY.md 初始索引
-> 第一个 feature package
-> PLAN / TASKS
-> IMPLEMENT
-> VERIFY
-> REVIEW
-> quality gate
-> LEARN
```

用户不需要一开始懂所有文档。工作台默认由 AI 内部路由到对应阶段。

### 16.2 项目已开始，需求变了

```text
用户提出变更
-> CHANGE_REQUEST.md
-> IMPACT_ANALYSIS.md
-> 判断影响哪些长期基线
-> 只更新受影响文件
-> 更新或豁免 TRACEABILITY.md
-> 重新计划、实现、验证、审查
```

这解决“需求文件反复改，所有文件都要同步改”的问题：不是全量同步，而是影响分析驱动的局部同步。

### 16.3 AI 做错了

```text
发现错误
-> REVIEW.md 标记问题等级
-> VERIFY.md 补充失败证据
-> 修复功能包
-> 判断 workbench_upgrade_assessment
-> 如果 required，升级规则、模板、测试、质量门、hook、CI 或失败日志
```

一次错误优先修项目；重复错误或高风险漏检才升级工作台机制。

### 16.4 UI 任务

UI 任务不能只看代码。

至少需要：

- `UX_SPEC.md` 或功能级 `DESIGN.md`。
- 用户流程、页面状态、错误/空/加载/权限状态。
- 截图或 Figma 原型证据。
- Playwright 或人工检查记录。
- a11y 检查或无法检查原因。

### 16.5 AI / RAG / Agent 任务

AI 任务不能只看“能回答”。

至少需要：

- `AI_DESIGN.md` 或功能级 AI 设计。
- 工具调用边界。
- 数据源和权限边界。
- eval 或测试样例。
- 失败样例。
- prompt injection / 数据泄露等风险说明。

## 17. 2.0.0 相对 1.2.0 要解决的问题

| 1.2.0 暴露的问题 | 2.0.0 修正方向 |
| --- | --- |
| AI 会把工作台规则当背景说明，直接推进代码。 | 引入状态机、hook 前置护栏、runtime gate、quality gate、CI 和 branch protection 分层判定；未验证路径标记 `unverified`。 |
| 当前状态靠 Markdown，容易漏读或后补。 | 引入脚本生成的 `.workbench-validation/quality-workflow-state.json` 和 `.workbench-validation/runtime-state.json`，并避免两类状态互相覆盖。 |
| 需求变更后，多份文档容易同步负担过重。 | 用 `IMPACT_ANALYSIS.md` 判断只更新受影响基线。 |
| 文档完整不等于代码正确。 | `VERIFY.md`、`REVIEW.md`、quality gate、CI 要求真实证据。 |
| scorecard 容易被误解成质量裁判。 | scorecard 只做辅助审计，quality gate 才做硬判定。 |
| 失败复盘偏软。 | `workbench_upgrade_assessment` 必须落到机制或写明 deferred / not_required。 |
| hook 有时拦截过粗，用户明确删除也被挡。 | bypass 走受控确认、范围校验、过期和 follow-up，不让绕过变逃生口。 |

## 18. 落地路线图

本节是从架构稿拆分到模板、脚本、hook、CI、测试和发布材料的路线图，不是当前版本已完成清单，也不是具体实现规范。

### 18.0 2.0.3 实现状态说明

下面是发布包 `2.0.3` 相对本设计稿的实现状态映射。它用于避免把历史设计 backlog 误读为当前实现缺口；最终状态仍以 README、脚本、golden-test、doctor 和 package-check 输出为准。

| 设计项 | 2.0.3 状态 | 证据 |
| --- | --- | --- |
| 工作台目录契约，禁止 AI 发明 `workbench/docs/` 等未声明层。 | 已实现确定性检查。 | `workbench-guardrails` golden case；`validate/audit` directory contract。 |
| 受控 diff 必须有关联功能包或机器可读 light 变更记录。 | 已实现确定性检查。 | `quality-gate-contract` golden case。 |
| `quality-gate-ok.json` 绑定 schema、status、`git_head`、`diff_hash` 和 `checks_run`。 | 已实现确定性检查。 | `quality-gate-contract` golden case；生成 marker v2。 |
| hook 对绕过配置、非法工作台目录和 nested repo 缺 marker 做粗拦截。 | 已实现并有 bypass golden test。 | `plugin-hook-hard-gate` golden case。 |
| 空 `VERIFY.md`、blocking `REVIEW.md`、strict `TRACEABILITY.md missing` 不能通过。 | 已实现证据形态和状态一致性检查。 | `quality-evidence-contract` golden case。 |
| `VERIFY.md` 证据真实性、review 是否漏掉 P0/P1、traceability 是否覆盖完整需求宇宙。 | 仍需 review、CI 或人工判断。 | README 标记为语义质量边界；不能宣称完全自动证明。 |
| UI/a11y/eval 证据充分性。 | 仍部分 `unverified`。 | W3C WAI 明确自动化工具只能辅助，无障碍仍需人工判断；AI eval 仍需样例质量和人工/独立复核。 |
| 远程合并保护。 | 未经 GitHub API、`gh` 或 CI 环境确认时只能写 `unverified`。 | GitHub required checks / protected branches 是远程门禁来源。 |

2.0.0 落地应按这个顺序做，避免局部优化破坏整体架构。

### 阶段 A：设计冻结

- [ ] 确认本文为 2.0.0 架构基线。
- [ ] 明确 2.0.0 不兼容点和迁移策略。
- [ ] 确认目录契约。
- [ ] 确认状态机和流程强度。
- [ ] 确认 quality gate 最小规则。
- [ ] 确认“会拦截”只能用于已有 bypass golden test 证明的路径。
- [ ] 未验证的远程合并保护、hook 覆盖和兜底链路必须标记为 `unverified`。

### 阶段 B：模板升级

- [ ] 更新 project adapter template。
- [ ] 更新 feature-template。
- [ ] 增加 `PROJECT_STATE.md`。
- [ ] 增加 `TRACEABILITY.md`。
- [ ] 增加 `CHANGE_LOG.md`。
- [ ] 增加 schema 文件。

### 阶段 C：脚本升级

- [ ] `workbench.py upgrade --dry-run` 支持 1.2.0 -> 2.0.0 预览。
- [ ] `runtime_gate.py` 生成 workflow state。
- [ ] `quality_gate.py` 交叉校验 Markdown、JSON、git diff、证据文件。
- [ ] `quality_gate.py` 检查旧 gate marker 在 diff、feature、证据或关键基线变化后失效。
- [ ] `quality_gate.py` 对缺 `CHANGE_REQUEST`、缺 `IMPACT_ANALYSIS`、缺 `PLAN/TASKS`、空 `VERIFY`、未解决 P0/P1、伪造 JSON、旧 marker 等场景输出失败。
- [ ] `quality_gate.py` 对未被 golden test 覆盖的拦截声明输出 `unverified`。
- [ ] `scorecard.py` 不作为硬放行条件。
- [ ] retention 策略避免 `.workbench-validation/` 无限堆积。

### 阶段 D：hook 升级

- [ ] `UserPromptSubmit` 注入会话职责和状态机提醒。
- [ ] `PreToolUse` 只做粗拦截，不替代 quality gate。
- [ ] `PreToolUse` 使用 `permissionDecision: "deny"`、旧式 `decision: "block"` 或 exit code `2` 阻断，不使用 `continue:false`。
- [ ] `PermissionRequest` 只处理会触发审批的权限请求，并记录 allow / deny / no decision。
- [ ] `Stop` 检查受控改动是否有新鲜 gate marker；缺失时触发继续收尾，不能撤销已发生改动。
- [ ] `BYPASS_LOG.md` 支持用户确认、安全删除和 follow-up。

### 阶段 E：验证与发布

- [ ] golden test 覆盖新项目、已有项目升级、light / standard / strict 三种路径。
- [ ] bypass golden tests 覆盖：缺 `CHANGE_REQUEST`、缺 `IMPACT_ANALYSIS`、未计划先实现、伪造 `FEATURE_STATUS.json`、旧 gate marker、空 `VERIFY.md`、未解决 P0/P1、本地 `--no-verify` 绕过、branch protection 未验证。
- [ ] 每个 bypass golden test 都断言至少一层 gate 返回失败或 audit 输出 `unverified`。
- [ ] audit/report 输出 `branch_protection: verified | unverified | not_applicable`。
- [ ] package-check 检查发布包文件、版本、可见 skill、个人路径泄漏。
- [ ] README 说明最新版本安装、工作流、质量机制和迁移策略。
- [ ] 发布 tag。
- [ ] 确认别人安装时拿到 2.0.0，而不是旧缓存版本。

## 19. 风险与边界

2.0.0 不能承诺：

- AI 永远不会犯错。
- AI 永远不会试图跳流程。
- 文档存在就代表代码正确。
- 有截图就代表 UI 合格。
- 有测试就代表没有 bug。
- 有 scorecard 高分就可以合并。

2.0.0 能承诺的工程目标：

- 受控范围内的变更必须有入口。
- 高风险变更必须有影响分析。
- 实现必须绑定计划。
- 完成声明必须有验证证据。
- review 的 P0/P1 不能被总分抵消。
- gate marker 必须绑定当前 git 状态。
- 在已实现并启用的受控入口内，跳流程、漏验证、乱改范围必须由本地 gate 或 CI / branch protection 基于独立证据判定失败；hook 只能作为前置粗拦截，不能承诺覆盖所有路径。
- 没有 bypass golden test 证明的拦截路径，不能承诺“会拦截”，只能记录为 `unverified`。
- CI / branch protection 没有通过 GitHub API、`gh`、CI 环境或审计报告确认时，不能承诺远程合并保护有效。
- 重复失败会进入学习升级闭环，而不是只靠用户下次再提醒。

## 20. 最终判断

Codex Workbench 2.0.0 不要继续堆更多“开发流程文档”，而要升级为：

```text
变更驱动的 AI coding 状态机
+ 基线约束
+ 追踪矩阵
+ 可信状态生成
+ 质量证据链
+ 硬门禁
+ 失败学习闭环
```

这条路线比单纯提示词、单纯 SDD 文档或单纯评分更适合 AI coding，因为它承认 AI 会漏读、会误判、会后补证据，所以把关键判断下沉到脚本、hook、CI 和可复查证据里。

2.0.0 的最终验收不以“文档写了这些规则”为准，而以这些自动化证据为准：

```text
bypass golden tests 通过
quality_gate.py 能独立发现跳流程和伪造状态
runtime_gate.py 能生成可信 workflow state
Stop hook 能发现未收尾验证并触发继续收尾
CI required checks 能跑 quality gate
branch protection audit 能确认远程门禁状态
```

只有这些证据存在时，才能从“架构要求会拦截”升级为“当前实现会拦截”。

下一步不是继续扩大本文篇幅，而是按边界把本文拆分为可执行资产：

- 模板文件：`workbench/feature-template/` 和项目适配器模板。
- schema：`workbench/runtime/WORKFLOW_STATE.schema.json`、`FEATURE_STATUS.schema.json` 和验证报告 schema。
- runtime gate：`workbench/runtime/runtime_gate.py` 及 hook 集成。
- quality gate：`workbench/quality/quality_gate.py`、shell wrapper 和 bypass golden tests。
- hook 行为：用户级 / 项目级 hooks 配置和脚本。
- CI / audit：required checks、branch protection audit 和报告输出。
- 发布材料：README、迁移手册、package-check 和 release checklist。
