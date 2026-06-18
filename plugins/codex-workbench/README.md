# Codex Workbench

Codex Workbench 是一个给 Codex 使用的 AI 开发工作台插件。2.0.0 的核心不是再写一段提示词，也不是堆更多 Markdown，而是把 AI coding 管成一个可检查的工程状态机：项目基线、变更影响分析、追踪矩阵、验证证据、质量门、审查和失败学习都放进仓库。

普通使用者只需要记住一个入口：

```text
Use Codex Workbench to set up this project's AI workbench.
```

## 为什么要做

AI 写代码的问题通常不是“不会生成代码”，而是这些工程风险没有被固定下来：

- 需求没确认，AI 先脑补。
- 聊天里的规则下一轮又被忘掉。
- 需求、UX、架构和代码之间没有追踪关系。
- AI 写完后只说“完成了”，没有命令、截图、日志、测试、eval 或 review 证据。
- 同类错误反复出现，却没有沉淀成模板、测试、质量门、hook 或 CI。

Codex Workbench 2.0.0 的目标是：不能保证 AI 永远一次写对，但要让受控范围内的跳流程、漏验证、乱改范围、证据缺失和重复失败被本地 gate、CI 或 branch protection 暴露出来；没有自动化验证证明会失败的路径，只能标记为 `unverified`，不能宣传成“已拦截”。

## 2.0.0 架构

2.0.0 是“五层架构 + 贯穿式控制面”：

| 层 | 作用 | 典型文件 |
| --- | --- | --- |
| Agent Control | 防止 AI 把流程当背景说明，控制当前能不能进入下一步 | `AGENTS.md`、`WORKBENCH.md`、`.workbench-validation/workflow-state.json`、hook、quality gate |
| 基础约束层 | 保存长期项目事实，约束目标、范围、UX、架构、权限和 AI 边界 | `PROJECT_INTAKE.md`、`PROJECT_STATE.md`、`workbench/product/`、`workbench/design/`、`workbench/architecture/` |
| 追踪矩阵层 | 连接需求、设计、实现和验证，发现断链 | `workbench/delivery/TRACEABILITY.md` |
| 变更执行层 | 每次 meaningful change 从变更请求和影响分析开始 | `workbench/features/<feature>/`、`CHANGE_REQUEST.md`、`IMPACT_ANALYSIS.md` |
| 质量证据层 | 用真实证据判断能不能继续，不靠 AI 自评 | `workbench/quality/`、`workbench/runtime/`、`VERIFY.md`、`REVIEW.md`、`.workbench-validation/` |
| 学习升级层 | 把重复失败沉淀成模板、测试、质量门、hook、CI 或文档升级 | `workbench/feedback/`、`docs/maintenance/` |

`Agent Control` 不是一个新目录，而是控制面。它贯穿所有阶段。

## 生成目录

在项目仓库里，插件会生成或升级这套结构：

```text
AGENTS.md
PROJECT_INTAKE.md
PROJECT_STATE.md
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
├── feedback/
└── archive/
```

关键文件：

| 文件 | 作用 |
| --- | --- |
| `PROJECT_INTAKE.md` | 确认项目目标、用户、范围、数据、权限、AI 边界和验收。 |
| `PROJECT_STATE.md` | 当前项目事实索引：阶段、active feature、关键命令、约束和风险。 |
| `workbench/delivery/TRACEABILITY.md` | 需求、UX、API、AI、实现和验证的追踪矩阵。 |
| `workbench/delivery/CHANGE_LOG.md` | `light` 变更的机器可读索引。 |
| `workbench/runtime/WORKFLOW_STATE.schema.json` | 运行时状态 schema；实际状态由脚本生成到 `.workbench-validation/workflow-state.json`。 |
| `workbench/features/<feature>/FEATURE_STATUS.json` | 功能包机器状态索引；不能只靠 AI 手写后直接信任，质量门会交叉校验。 |
| `workbench/quality/quality_gate.py` | 本地硬判定入口，检查 diff、状态、证据、review 和 marker 新鲜度。 |
| `.workbench-validation/` | 当前机器生成报告区，不是长期人工维护日志。 |
| `workbench/feedback/FAILURE_LOG.md` | 重复失败、review 漏检、质量门缺口的项目级复盘位置。 |

明确不新增 `workbench/docs/` 作为工作台阶段目录。根目录 `docs/` 可以是普通项目文档，但不是工作台标准阶段。

## 工作流

2.0.0 的主流程是状态机：

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

含义：

| 阶段 | 必须回答 |
| --- | --- |
| `CLASSIFY` | 这是什么任务、风险多高、该走 `light`、`standard` 还是 `strict`。 |
| `BASELINE_CHECK` | 项目 intake、产品、UX、架构、交付基线是否足够支撑本次变更。 |
| `CHANGE` | 为什么改、改什么、不改什么、做到什么算完成。 |
| `IMPACT` | 是否影响 PRD、UX、API、数据、AI、权限、测试、发布和追踪矩阵。 |
| `ROUTE` | 按风险和影响面选流程强度。 |
| `PLAN` | 计划改哪些文件、怎么验证、风险和回滚是什么。 |
| `IMPLEMENT` | 只实现计划覆盖范围。 |
| `VERIFY` | 留下命令、截图、日志、测试、eval、CI 或人工验收证据。 |
| `REVIEW` | 检查 P0/P1、需求偏移、权限、安全、架构、测试和回滚风险。 |
| `GATE` | 运行质量门，写入绑定当前 diff 的 marker。 |
| `LEARN` | 如果出现失败或重复问题，判断是否升级模板、测试、质量门、hook 或 CI。 |

## 流程强度

不是所有改动都走全套。2.0.0 用三个 profile 控制负担：

| Profile | 场景 | 最低证据 |
| --- | --- | --- |
| `light` | 小文案、小样式、低风险单点 bug | `workbench/delivery/CHANGE_LOG.md` 中有机器可读记录，并有最小验证证据。 |
| `standard` | 普通功能、单模块业务改动 | 功能包包含 `CHANGE_REQUEST.md`、`IMPACT_ANALYSIS.md`、`PLAN.md`、`TASKS.md`、`VERIFY.md`、`REVIEW.md`、`FEATURE_STATUS.json`。 |
| `strict` | 跨模块、数据、权限、API、AI/RAG/Agent、架构、发布、生产风险 | 完整功能包、追踪矩阵更新或豁免、质量门、独立审查或 CI 证据。 |

硬触发 `strict` 的例子：

- 数据结构、迁移、批量数据修改。
- 登录、认证、授权、角色、租户、隐私、密钥。
- API 合约、SDK、消息结构、外部集成。
- AI 输出影响用户权益，RAG 数据源变化，Agent 工具调用变化。
- CI/CD、部署、环境变量、基础设施、生产发布。
- 不可逆删除、覆盖或安全风险。

## 需求变更怎么处理

项目已经写了一部分时，需求变化不要求全量重写所有文档。先做 `IMPACT_ANALYSIS.md`，只更新受影响的基线。

| 变化 | 优先更新 |
| --- | --- |
| 项目目标、用户、第一版范围变化 | `PROJECT_INTAKE.md`、`PROJECT_STATE.md`、product/design/architecture/delivery 中受影响文件 |
| 当前功能需求变化 | 功能包 `CHANGE_REQUEST.md`、`IMPACT_ANALYSIS.md`、`SPEC.md` |
| UX 或原型变化 | `workbench/design/` 或功能级 `DESIGN.md` |
| API、数据、AI 工具边界变化 | `workbench/architecture/`、功能级 `DESIGN.md`、ADR |
| 验收标准变化 | `SPEC.md`、`VERIFY.md`、测试、quality gate |
| 实现偏离计划 | `DECISIONS.md`、`IMPLEMENTATION_NOTES.md`、`VERIFY.md`、必要时 `FAILURE_LOG.md` |

## 质量门和 marker

`quality_gate.py` 不是评分器。它的第一职责是阻断不合格状态。

它至少检查：

- `PROJECT_INTAKE.md` 不是 draft，且无 open blocker。
- 有受控代码或受控资产 diff 时，存在关联功能包或有效 `light` 变更记录。
- `standard` / `strict` 有 `IMPACT_ANALYSIS.md`。
- 未通过 `PLAN.md` / `TASKS.md` 时不能进入实现。
- `VERIFY.md` 有真实验证证据。
- `REVIEW.md` 没有未解决 P0/P1。
- `strict` 更新 `TRACEABILITY.md`，或明确说明不受影响。
- `FEATURE_STATUS.json`、Markdown、git diff、证据文件互相一致。
- 旧 `quality-gate-ok.json` 在 diff、active feature、证据或关键基线变化后失效。

通过后写入：

```text
.workbench-validation/quality-gate-ok.json
.workbench-validation/workflow-state.json
```

marker 必须绑定 `git_head`、`diff_hash`、`feature_id`、`commands_run`、`created_at` 和 `branch_protection` 状态。`branch_protection` 只有通过 GitHub API、`gh` 或 CI 环境确认后才能写 `verified`；否则只能写 `unverified`。

## Scorecard 边界

`scorecard` 是证据审计，不是质量裁判。

| 机制 | 用途 | 是否能单独放行 |
| --- | --- | --- |
| `quality_gate.py` | 检查 blocker、状态、diff、证据和 marker | 可以作为本地 gate |
| CI status check | 合并前远程门禁 | 可以作为远程 gate |
| `SCORECARD.md` / `scorecard.py` | 发现证据成熟度、趋势和校准问题 | 不能单独放行 |
| 人工或独立 review | 判断产品、UX、架构、安全和 AI eval 的语义质量 | 高风险时必须参与 |

正确顺序是：

```text
先看 blocker
-> 再看验证证据
-> 再看 review P0/P1
-> 再看 gate / CI
-> 最后才看 scorecard 趋势
```

## Hook 边界

插件会携带默认 `hooks/` 目录，用于会话提醒、危险操作粗拦截和收尾检查。使用者仍然需要在自己的 Codex 环境中 review/trust hooks；插件不会替用户跳过信任步骤。

Hook 只能作为前置护栏，不能承诺覆盖所有路径。最终硬判定必须落到 `runtime_gate.py`、`quality_gate.py`、pre-commit、CI 或 branch protection。

用户明确要求安全删除时，不应被永久阻断；应走路径解析、范围确认、`BYPASS_LOG.md` 记录、过期时间和 follow-up。

## 安装

添加 marketplace：

```bash
codex plugin marketplace add Hapibit/codex-workbench --ref main
```

安装插件：

```bash
codex plugin add codex-workbench --marketplace hapibit
```

默认安装 `main`，也就是仓库当前最新版本。只有复现实验、回滚问题或锁定环境时才建议固定 tag：

```bash
codex plugin marketplace add Hapibit/codex-workbench --ref v2.0.0
codex plugin add codex-workbench --marketplace hapibit
```

## 第一次使用

进入项目根目录，对 Codex 说：

```text
Use Codex Workbench to set up this project's AI workbench.
```

检查下一步：

```text
Use Codex Workbench to tell me the next step for this project.
```

创建功能包：

```text
Use Codex Workbench to create a feature work package named <feature-name>.
```

审计工作台：

```text
Use Codex Workbench to audit this project workbench.
```

## 使用者需要自己配置什么

插件不会分发作者的私人环境。使用者仍然要自己配置：

- Codex 安装和登录。
- 自己的 `~/.codex/config.toml`。
- MCP servers、API keys 和凭证。
- GitHub、Figma、Jenkins、OpenAI 等账号权限。
- Node、Java、Maven、Docker、Python、浏览器、draw.io 等本机工具链。
- 项目的环境变量、本地依赖、测试、lint、build 和 CI 命令。
- hook trust、审批策略和权限决策。

## 可选用户工作台

项目工作台默认写进具体项目仓库。用户工作台写进 `~/.codex/`，会影响所有项目，必须由使用者显式安装。

预览：

```bash
python skills/codex-workbench/scripts/workbench.py user-workbench
```

确认后写入：

```bash
python skills/codex-workbench/scripts/workbench.py user-workbench --apply
```

覆盖已有用户配置需要显式 `--force`，并会生成备份：

```bash
python skills/codex-workbench/scripts/workbench.py user-workbench --apply --force
```

说明见 [USER_WORKBENCH.md](docs/USER_WORKBENCH.md)。

## 可选增强能力

Codex Workbench 本身可以独立使用。其他 skill、MCP 或第三方工具只是增强包，不是入门前置条件。

| 任务 | 可选增强 |
| --- | --- |
| UI、Figma、前端还原 | UI/Figma 类 skill |
| ER 图、流程图、架构图、UML | diagram/draw.io 类 skill |
| 单元测试、接口测试、Playwright、AI 对话测试 | testing 类 skill |
| Jenkins、GitHub Actions、CI/CD | CI/Jenkins 类 skill |
| README、Word、论文、PPT、技术文档 | docs 类 skill |
| RAG、Agent、LLM eval、安全治理 | AI governance 类 skill |

查看本机增强包：

```bash
python skills/codex-workbench/scripts/check_enhancements.py --query "我要做 UI/Figma 和测试"
```

## 维护和发布

普通使用者可以跳过本节。

发布前至少运行：

```bash
python skills/codex-workbench/scripts/workbench.py self-test
python skills/codex-workbench/scripts/workbench.py golden-test
python skills/codex-workbench/scripts/workbench.py package-check --plugin <plugin-root> --expected-version 2.0.0 --write-report
```

发布候选必须满足：

- `.codex-plugin/plugin.json` 版本是 `2.0.0`。
- 只暴露一个可见 skill：`codex-workbench`。
- 新增模板、schema、runtime、quality、docs 都被打包。
- `.workbench-validation/`、cache、`__pycache__`、个人路径和内部备份不进入发布包。
- 维护证据写入 `docs/maintenance/IMPROVEMENT_LOG.md`，机器报告写入 `.workbench-validation/`。

## 参考资料

- OpenAI Codex customization: https://developers.openai.com/codex/concepts/customization
- OpenAI Codex skills: https://developers.openai.com/codex/skills
- OpenAI Codex plugins: https://developers.openai.com/codex/plugins/build
- OpenAI Codex hooks: https://developers.openai.com/codex/hooks
- OpenAI Codex iterative repair loop: https://developers.openai.com/cookbook/examples/codex/build_iterative_repair_loops_with_codex
- GitHub Spec Kit: https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit
- Git hooks: https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks
- GitHub protected branches: https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- GitHub status checks: https://docs.github.com/articles/about-status-checks
- NASA Requirements Management: https://www.nasa.gov/reference/6-2-requirements-management/
- Semantic Versioning: https://semver.org
