# Codex Workbench 迭代升级机制

本文说明 Codex Workbench 2.0.0 怎么处理项目需求变化、AI 失败、工作台机制升级和插件版本发布。

## 三种迭代不要混在一起

| 类型 | 发生在哪里 | 典型触发 | 结果 |
| --- | --- | --- | --- |
| 项目迭代 | 使用者的项目仓库 | 需求变化、功能返工、验证失败、用户反馈 | 更新项目基线、功能包、测试、review 或项目质量门。 |
| 工作台机制升级 | `codex-workbench` 插件源码 | 同类失败重复出现，模板、脚本、quality gate、hook、scorecard 或文档有缺口 | 修改模板、脚本、文档、CI、hook 或审查规则。 |
| 插件版本发布 | 发布包 | 机制升级会影响别人安装后的行为 | bump 版本、更新 README、跑 package-check、发布 tag。 |

如果只影响一个项目，先在项目里解决；如果多个项目或同类任务重复失败，才说明工作台机制需要升级。

## 项目迭代流程

需求或功能变化时，按 2.0.0 状态机处理：

```text
CHANGE
-> IMPACT
-> ROUTE
-> PLAN
-> IMPLEMENT
-> VERIFY
-> REVIEW
-> GATE
-> LEARN
```

| 变化 | 先改哪里 | 然后做什么 |
| --- | --- | --- |
| 项目目标、用户、第一版范围变化 | `PROJECT_INTAKE.md`、`PROJECT_STATE.md` | 通过 `IMPACT_ANALYSIS.md` 判断 product/design/architecture/delivery 哪些基线要更新。 |
| 当前功能需求变化 | `CHANGE_REQUEST.md`、`IMPACT_ANALYSIS.md`、`SPEC.md` | 同步 `DESIGN.md`、`PLAN.md`、`TASKS.md`、`VERIFY.md`。 |
| 架构、API、数据或 AI 工具边界变化 | `DESIGN.md`、`DECISIONS.md` | 必要时更新 `workbench/architecture/` 或 ADR。 |
| 验收标准变化 | `SPEC.md`、`VERIFY.md` | 补测试、quality gate 或人工验收。 |
| AI 实现偏离计划 | `IMPLEMENTATION_NOTES.md`、`DECISIONS.md` | 复测写入 `VERIFY.md`，必要时进入 `FAILURE_LOG.md`。 |

项目迭代不等于插件升级。项目里能解决的，就留在项目里。

## 失败证据放哪里

| 问题类型 | 证据位置 | 用途 |
| --- | --- | --- |
| 单个功能验证失败 | `workbench/features/<feature>/VERIFY.md` | 记录命令、输出、失败原因、复测结果。 |
| 单个功能审查发现 | `workbench/features/<feature>/REVIEW.md` | 记录 P0/P1/P2、修复状态、剩余风险。 |
| 实现偏离计划 | `workbench/features/<feature>/DECISIONS.md`、`IMPLEMENTATION_NOTES.md` | 记录为什么偏离、影响什么、是否接受。 |
| 需求变化 | `CHANGE_REQUEST.md`、`IMPACT_ANALYSIS.md`、`SPEC.md`、必要时 `PROJECT_INTAKE.md` | 让后续会话知道需求已经变。 |
| 跨功能重复失败 | `workbench/feedback/FAILURE_LOG.md` | 判断是否升级模板、测试、quality gate、hook 或 review。 |
| AI 修改后效果 | `workbench/feedback/AI_EFFECTIVENESS.md` | 判断 AI 工作方式是否变好。 |
| scorecard 误报/漏报 | `workbench/scorecard/CALIBRATION.md` | 调整 rubric、权重、硬阻塞、脚本。 |
| 插件自身升级证据 | `docs/maintenance/IMPROVEMENT_LOG.md` | 记录为什么升级、改了什么、怎么验证。 |

聊天记录不是项目事实源。重要失败必须进入仓库文件。

## 什么时候算需要升级工作台机制

不要把所有不满意都叫升级。先分类：

| 信号 | 说明 | 优先动作 |
| --- | --- | --- |
| 需求变了 | 用户目标、范围、验收或优先级变化 | 更新项目基线和功能包。 |
| AI 做错一次 | 单个功能实现偏离、验证失败或 review 发现问题 | 修当前功能，证据写回功能包。 |
| 同类错误第二次出现 | 同一澄清点、验证缺口、review 漏项重复出现 | 写入 `FAILURE_LOG.md`，考虑升级模板、测试或 gate。 |
| 脚本误判 | 高分低质、低分可用、空文档刷分、伪造状态未拦 | 写入 `CALIBRATION.md` 或维护日志，调整脚本。 |
| 规则经常被跳过 | 用户反复提醒同一流程、搜索或验证规则 | 判断能否变成 runtime gate、quality gate、hook、CI 或更明确状态字段。 |
| 发布包问题 | 缺文件、版本不一致、暴露个人路径、可见 skill 过多 | 修发布包并跑 package-check。 |

## 工作台机制升级流程

```text
1. 收集证据
2. 分类失败
3. 判断影响范围
4. 选择升级位置
5. 小步修改
6. 运行验证
7. 记录维护证据
8. 决定是否发布版本
```

### 1. 收集证据

最低要有一种证据：

- 项目 `VERIFY.md` 里的验证失败。
- 项目 `REVIEW.md` 里的 P0/P1 漏报。
- `FAILURE_LOG.md` 里的重复失败。
- `CALIBRATION.md` 里的 scorecard 误报/漏报。
- `package-check`、`doctor`、`self-test`、`golden-test` 的失败。
- 用户在真实使用中重复提醒同一条规则。

没有证据时，只能记录为想法，不能直接升级硬门禁。

### 2. 分类失败

| 分类 | 表现 | 优先处理 |
| --- | --- | --- |
| 需求失败 | AI 没问清楚目标、范围、验收就实现 | `PROJECT_INTAKE.md`、`CHANGE_REQUEST.md`、`IMPACT_ANALYSIS.md`、澄清规则。 |
| 产品失败 | 功能有代码但用户目标或非目标不清 | `PRODUCT_BRIEF.md`、`PRD.md`、验收标准。 |
| UX 失败 | 页面流程、状态、错误反馈缺失 | `UX_SPEC.md`、`PROTOTYPE.md`、截图/浏览器验证。 |
| 架构失败 | 模块、数据、API、AI 边界混乱 | `ARCHITECTURE.md`、ADR、review 清单。 |
| 验证失败 | 测试、lint、build、runtime smoke 没跑或不可靠 | `quality_gate.py`、CI、pre-commit。 |
| 审查失败 | 权限、数据、回滚、AI 自动生效风险漏掉 | `REVIEW.md`、独立审查提示。 |
| 状态失败 | AI 手写 JSON、旧 marker 复用、阶段和 diff 不一致 | `runtime_gate.py`、`quality_gate.py`、bypass golden test。 |
| scorecard 失败 | 高分低质、低分可用、空文档刷分 | `RUBRIC.md`、`CALIBRATION.md`、scorecard 脚本。 |
| 发布失败 | 发布包缺文件、版本不一致、个人配置泄露 | `packaging-manifest.json`、`plugin.json`、package-check。 |

### 3. 选择升级位置

| 问题 | 不足够的做法 | 更可靠的升级 |
| --- | --- | --- |
| AI 总是不问清楚需求 | README 写提醒 | `PROJECT_INTAKE.md`、`CHANGE_REQUEST.md`、`IMPACT_ANALYSIS.md` 增加必填字段和 blocker。 |
| AI 不跑测试 | 文档里说要跑 | `quality_gate.py`、CI、pre-commit、Stop hook。 |
| review 漏权限 | 提醒 reviewer 小心 | `REVIEW.md` 增加 P0/P1 检查，必要时加测试或 gate。 |
| AI 跳过功能包 | 聊天里提醒 | `FEATURE_STATUS.json`、runtime state、quality gate diff 分类。 |
| 手写状态骗过流程 | 要求 AI 不要手写 | quality gate 用 hash、diff、Markdown、报告交叉校验。 |
| 旧 marker 被复用 | 要求手动重跑 | marker 绑定 `git_head`、`diff_hash`、feature 和证据 hash。 |
| scorecard 被刷分 | 调高总分线 | 增加 blocker、组件下限、关键字段检查、校准样例。 |
| 发布包漏文件 | 手动检查 | `packaging-manifest.json` 和 `package-check` 检查。 |

升级强度按这个顺序：

```text
项目证据
-> 模板或 review 清单
-> 脚本检查
-> quality gate / CI / pre-commit
-> Codex hook
-> 改变公开流程并发布 major
```

## 升级后的验证

| 改动类型 | 最小验证 |
| --- | --- |
| README 或 docs | 关键词检索、旧术语清理、package-check。 |
| 模板字段 | `self-test`、`golden-test`，确认新项目生成文件。 |
| `runtime_gate.py` | 生成 `.workbench-validation/workflow-state.json`，包含 `git_head`、`diff_hash`、source hashes。 |
| `quality_gate.py` | 构造缺 `CHANGE_REQUEST`、缺 `IMPACT_ANALYSIS`、空 `VERIFY`、P0/P1 未解决、旧 marker 等样例。 |
| scorecard/rubric | 构造高分低质、低分可用样例，更新 `CALIBRATION.md`。 |
| hook | 明确哪些路径只做提醒、哪些会阻断；不能把未测试路径写成会拦截。 |
| package manifest | `package-check --expected-version <version> --write-report`。 |

## 怎么证明升级有效

一次升级至少回答五个问题：

1. 这次升级解决哪个真实失败。
2. 失败证据在哪里。
3. 改的是项目个案、模板、脚本、quality gate、CI、hook、review 还是发布包。
4. 什么验证证明这次改动没有破坏现有工作流。
5. 以后如何发现同类问题是否减少。

可接受的证明：

| 证明类型 | 例子 |
| --- | --- |
| 复现样例 | 旧规则会漏掉的问题，新规则能拦住、失败或标记 `unverified`。 |
| 生成验证 | `self-test`、`golden-test` 能生成新模板并通过验证。 |
| 发布验证 | `package-check` P0/P1/P2/P3 为 0。 |
| 项目试水 | 一个真实项目按新流程跑完 feature package、quality gate、review。 |
| 校准记录 | scorecard 误报/漏报被记录，并能解释调整前后差异。 |

没有验证，只能记录为设计想法，不能当作已完成升级。

## 什么时候发版本

Codex Workbench 采用 SemVer：

| 版本类型 | 什么时候用 | 例子 |
| --- | --- | --- |
| `PATCH` | 向后兼容修复，不改变公开工作流 | 修 README、修模板错字、修 package-check 漏检。 |
| `MINOR` | 向后兼容新增能力 | 新增文档、模板、scorecard 维度、可选脚本。 |
| `MAJOR` | 改变公开契约或兼容性 | 改生成目录结构、改默认工作流、移除字段、改变质量门语义。 |

2.0.0 属于 `MAJOR`，因为它把公开工作流从旧的文档流程升级为状态机、变更影响分析、追踪矩阵、机器状态和 gate marker 新鲜度契约。

发布前必须确认：

- `plugin.json` 版本正确。
- README 没有旧版本叙述冲突。
- `packaging-manifest.json` 包含新增文件。
- 个人 skill 和发布包 skill 同步。
- `package-check --expected-version <version> --write-report` 通过。
- `docs/maintenance/IMPROVEMENT_LOG.md` 已记录升级原因、证据来源、变更文件和验证结果。

## 一次升级记录怎么写

维护日志位置：

```text
docs/maintenance/IMPROVEMENT_LOG.md
```

每条记录包含：

```text
问题：
证据来源：
- 用户反馈：
- 架构设计依据：
- 本地失败证据或验证证据：
决策：
变更文件：
验证结果：
后续动作：
```

不要只写“优化了文档”或“升级了工作台”。要能让下一个维护者看懂为什么改、改了哪里、怎么验证、还有什么风险没解决。

## 什么时候不能升级

这些情况不要升级工作台机制：

- 只有一次项目个案，而且可以用项目文档解决。
- 没有真实证据，只是感觉可能会出问题。
- 规则无法被检查，也没有人工确认点。
- 升级会让所有项目变重，但只服务一个特殊项目。
- 新增规则和 Codex skill/plugin/hook 公开边界冲突。

先把问题记录到项目 `FAILURE_LOG.md` 或维护日志草稿，等出现重复证据或高风险证据再升级。

## 参考资料

- OpenAI agent improvement loop: https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop
- OpenAI Codex iterative repair loop: https://developers.openai.com/cookbook/examples/codex/build_iterative_repair_loops_with_codex
- Google SRE postmortem culture: https://sre.google/workbook/postmortem-culture
- Google SRE incident management guide: https://sre.google/resources/practices-and-processes/incident-management-guide
- Semantic Versioning: https://semver.org
