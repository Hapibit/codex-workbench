# {{PROJECT_NAME}} 工作台说明

## 作用

本目录是项目级 AI 工作台适配器，用来让 Codex 和其他编码代理按本项目的规则工作。它不是全局 Codex 安装、账号登录、MCP 凭证、hook 信任或本地工具链的替代品。

## 文件职责

- `AGENTS.md`：项目规则入口，说明 AI 必读内容、完成标准、澄清条件和硬边界。
- `PROJECT_INTAKE.md`：项目预处理画像，用来把模糊需求转成可确认的目标、用户、范围、数据、权限、AI 边界和验收。
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
- `workbench/review/independent-review-prompt.md`：给新 AI 会话使用的只读独立审查提示。
- `workbench/feature-template/`：功能工作包模板，用于复制到 `workbench/features/<feature-name>/`。
- `workbench/features/<feature-name>/`：真实功能工作包目录，每个重要功能一份。

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

能自动化的问题优先进入脚本、测试、lint、CI 或质量门；无法自动化的业务判断才保留在 Markdown 规则里。

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
