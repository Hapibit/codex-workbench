# Codex Workbench 迭代升级机制

本文专门说明 Codex Workbench 怎么迭代升级。它回答四个问题：

1. 项目在开发中变了，工作台怎么处理。
2. AI 或工作台犯错了，证据放哪里。
3. 什么情况只改项目，什么情况要升级工作台模板、脚本、质量门或 hook。
4. 什么情况要发插件版本，版本号怎么判断。

## 为什么需要单独的迭代升级机制

AI 工作台如果只在第一次生成时有用，后面需求一变、项目一大、AI 一犯错，就会退化成普通 Markdown 模板。真正有用的工作台必须能从真实使用中变强：

```text
真实项目运行
-> 暴露需求、实现、验证、审查或评分问题
-> 记录证据
-> 判断问题属于项目个案还是工作台机制缺陷
-> 改对应机制
-> 重新验证
-> 必要时发布新版本
```

这个设计参考了：

- OpenAI agent improvement loop：把 traces、人工反馈、eval 和 Codex 修改连接成改进飞轮。
- OpenAI Codex iterative repair loop：review、repair、validation 分离，每轮留下结构化记录。
- Google SRE postmortem：失败要有事实、根因、影响、action item、owner、优先级和可验证完成标准。
- PDCA：Plan、Do、Check、Act，用小范围实验验证改进，再标准化。
- Semantic Versioning：用版本号表达变更影响。

## 三种迭代不要混在一起

| 类型 | 发生在哪里 | 典型触发 | 结果 |
| --- | --- | --- | --- |
| 项目迭代 | 使用者的项目仓库 | 需求变化、功能返工、验证失败、用户反馈 | 更新项目文档、功能包、测试、review、质量门 |
| 工作台机制升级 | `codex-workbench` 插件源码 | 同类失败重复出现，模板、脚本、scorecard、质量门或文档有缺口 | 修改模板、脚本、文档、CI、hook 或审查规则 |
| 插件版本发布 | 发布包 | 机制升级会影响别人安装后的行为 | bump 版本、更新 README、跑 package-check、发布 tag |

如果只影响一个项目，不应该马上改插件。如果多个项目或同类任务重复失败，才说明工作台机制需要升级。

## 什么时候算“需要迭代”

不要把所有不满意都叫升级。先判断问题属于哪一类。

| 信号 | 说明 | 优先动作 |
| --- | --- | --- |
| 需求变了 | 用户目标、范围、验收或优先级变化 | 更新项目事实源和功能包 |
| AI 做错一次 | 单个功能实现偏离、验证失败或 review 发现问题 | 修当前功能，证据写回功能包 |
| 同类错误第二次出现 | 同一个澄清点、验证缺口、review 漏项重复出现 | 写入 `FAILURE_LOG.md`，考虑升级模板或质量门 |
| 脚本误判 | scorecard 高分低质、低分可用、空文档刷分 | 写入 `CALIBRATION.md`，调整 rubric、脚本或 blocker |
| 规则经常被跳过 | 用户反复提醒同一条流程、搜索或验证规则 | 判断能否变成脚本、CI、hook 或更明确的入口规则 |
| 发布包问题 | 缺文件、版本不一致、暴露个人路径、可见 skill 过多 | 修发布包并跑 package-check |

一次性项目个案优先留在项目里。重复问题、高风险问题、可自动检查的问题，才进入工作台机制升级。

## 项目迭代流程

项目中需求或功能变化时，先更新项目事实源，再改代码。

```text
发现变化
-> 判断影响范围
-> 更新事实源或功能包
-> 修改实现
-> 运行验证
-> 更新 review 和反馈
```

| 变化 | 先改哪里 | 然后做什么 |
| --- | --- | --- |
| 项目目标、用户、第一版范围变化 | `PROJECT_INTAKE.md` | 同步产品、UX、架构和交付计划 |
| 当前功能需求变化 | `workbench/features/<feature>/SPEC.md`、`CLARIFY.md` | 同步 `DESIGN.md`、`PLAN.md`、`TASKS.md`、`VERIFY.md` |
| 架构或数据方案变化 | `DESIGN.md`、`DECISIONS.md` | 必要时补 `workbench/architecture/` 或 ADR |
| 验收标准变化 | `SPEC.md`、`VERIFY.md` | 补测试、质量门或人工验收 |
| AI 实现偏离计划 | `IMPLEMENTATION_NOTES.md`、`DECISIONS.md` | 复测写入 `VERIFY.md`，必要时写 `FAILURE_LOG.md` |

项目迭代不等于插件升级。项目里能解决的，就留在项目里。

## 失败证据放哪里

| 问题类型 | 证据位置 | 用途 |
| --- | --- | --- |
| 单个功能验证失败 | `workbench/features/<feature>/VERIFY.md` | 记录命令、输出、失败原因、复测结果 |
| 单个功能审查发现 | `workbench/features/<feature>/REVIEW.md` | 记录 P0/P1/P2、修复状态、剩余风险 |
| 实现偏离计划 | `workbench/features/<feature>/DECISIONS.md` | 记录为什么偏离、影响什么、是否接受 |
| 需求变化 | `SPEC.md`、`CHANGELOG.md`、必要时 `PROJECT_INTAKE.md` | 让后续会话知道需求已经变 |
| 跨功能重复失败 | `workbench/feedback/FAILURE_LOG.md` | 判断是否升级模板、测试、质量门或 review |
| AI 修改后效果 | `workbench/feedback/AI_EFFECTIVENESS.md` | 判断 AI 工作方式是否变好 |
| scorecard 误报/漏报 | `workbench/scorecard/CALIBRATION.md` | 调整 rubric、权重、硬阻塞、脚本 |
| 插件自身升级证据 | `docs/maintenance/IMPROVEMENT_LOG.md` | 记录为什么升级、改了什么、怎么验证 |

不要把失败证据只放在聊天记录里。聊天记录不是可复查的项目事实源。

## 工作台机制升级流程

当问题不是单个项目个案，而是工作台机制缺陷时，按这个流程升级：

```text
1. 收集证据
2. 分类失败
3. 判断是否重复或高风险
4. 选择升级位置
5. 小步修改
6. 运行验证
7. 记录维护证据
8. 决定是否发布版本
```

### 1. 收集证据

最低要有一种真实证据：

- 项目 `VERIFY.md` 里记录的验证失败。
- 项目 `REVIEW.md` 里记录的 P0/P1 漏报。
- `FAILURE_LOG.md` 里的重复失败。
- `CALIBRATION.md` 里的 scorecard 误报/漏报。
- `package-check`、`doctor`、`self-test`、`golden-test` 的失败。
- 用户在真实使用中重复提醒同一条规则。

没有证据时，只能作为想法记录，不能直接升级硬门禁。

### 2. 分类失败

| 分类 | 表现 | 优先处理 |
| --- | --- | --- |
| 需求失败 | AI 没问清楚就实现 | `PROJECT_INTAKE.md`、`CLARIFY.md`、需求澄清规则 |
| 产品失败 | 功能有代码但用户目标不清 | `PRODUCT_BRIEF.md`、`PRD.md`、验收标准 |
| UX 失败 | 页面流程、状态、错误反馈缺失 | `UX_SPEC.md`、`PROTOTYPE.md`、浏览器验证 |
| 架构失败 | 模块、数据、API、AI 边界混乱 | `ARCHITECTURE.md`、ADR、review 清单 |
| 验证失败 | 测试、lint、build、runtime smoke 没跑或不可靠 | `quality_gate.py`、CI、pre-commit |
| 审查失败 | 权限、数据、回滚、AI 自动生效风险漏掉 | `REVIEW.md`、独立审查提示 |
| scorecard 失败 | 高分低质、低分可用、空文档刷分 | `RUBRIC.md`、`CALIBRATION.md`、scorecard 脚本 |
| 发布失败 | 发布包缺文件、版本不一致、个人配置泄露 | `packaging-manifest.json`、`plugin.json`、package-check |

### 3. 判断升级强度

| 情况 | 动作 |
| --- | --- |
| 只影响当前项目 | 修改项目工作台，不改插件 |
| 影响多个项目或重复出现 | 升级插件模板、脚本或文档 |
| 能被脚本可靠判断 | 加入质量门、scorecard、doctor 或 package-check |
| 只能人工判断 | 加入模板字段、review 清单或人工确认点 |
| 涉及安全、数据、权限、生产 | 优先做硬门禁或 P0/P1 review，不只写说明 |

升级强度按这个顺序选择：

```text
先改项目证据
-> 再改模板或 review 清单
-> 再改脚本检查
-> 再接入质量门/CI/pre-commit
-> 最后才加 hook 或改变公开流程
```

原因是越靠后的手段影响越大。能用项目证据解决的，不要把所有项目都变重；能用脚本稳定判断的，不要只写 Markdown；确实会影响所有安装用户的，才进入版本发布。

### 4. 选择升级位置

| 问题 | 不足够的做法 | 更可靠的升级 |
| --- | --- | --- |
| AI 总是不问清楚需求 | README 写提醒 | `PROJECT_INTAKE.md`、`CLARIFY.md` 增加必填字段和 blocker |
| AI 不跑测试 | 文档里说要跑 | `quality_gate.py`、CI、pre-commit、hook |
| review 漏权限 | 提醒 reviewer 小心 | `REVIEW.md` 增加 P0/P1 检查，必要时加测试 |
| scorecard 被刷分 | 调高总分线 | 增加组件下限、硬阻塞、关键字段检查、校准样例 |
| 发布包漏文件 | 手动检查 | `packaging-manifest.json` 和 `package-check` 检查 |

## 升级后的验证

升级后不能只说“改好了”。至少按影响范围验证：

| 改动类型 | 最小验证 |
| --- | --- |
| README 或 docs | 关键词检索、链接存在、package-check |
| 模板字段 | `self-test`、`golden-test`，确认新项目生成文件 |
| scorecard/rubric | 构造高分低质、低分可用样例，更新 `CALIBRATION.md` |
| quality gate | 在至少一个样例项目跑 `quality_gate.py` |
| package manifest | `package-check --expected-version <version> --write-report` |
| skill 入口或脚本 | `doctor`、`self-test`、`golden-test` |

验证证据位置：

```text
.workbench-validation/
docs/maintenance/IMPROVEMENT_LOG.md
```

`.workbench-validation/` 放机器报告；`IMPROVEMENT_LOG.md` 放人工解释和证据摘要。

## 怎么证明升级有效

一次升级至少要回答五个问题：

1. 这次升级解决的是哪个真实失败。
2. 失败证据在哪里。
3. 改的是项目个案、模板、脚本、质量门、CI、hook、review 还是发布包。
4. 什么验证证明这次改动没有破坏现有工作流。
5. 以后如何发现同类问题是否减少。

可接受的证明不是“AI 觉得更合理”，而是：

| 证明类型 | 例子 |
| --- | --- |
| 复现样例 | 旧规则会漏掉的问题，新规则能拦住或提示。 |
| 生成验证 | `self-test`、`golden-test` 能生成新模板并通过验证。 |
| 发布验证 | `package-check` P0/P1/P2/P3 为 0。 |
| 项目试水 | 一个真实项目按新流程跑完 feature package、quality gate、review。 |
| 校准记录 | scorecard 误报/漏报被记录，并能解释调整前后差异。 |

如果没有任何验证，只能记录为设计想法，不能当作已完成升级。

## 什么时候发版本

版本号用于告诉使用者“这次升级影响多大”。Codex Workbench 采用 SemVer 思路：

| 版本类型 | 什么时候用 | 例子 |
| --- | --- | --- |
| PATCH | 向后兼容修复，不改变公开工作流 | 修 README、修模板错字、修 package-check 漏检 |
| MINOR | 向后兼容新增能力 | 新增文档、模板、scorecard 维度、可选脚本 |
| MAJOR | 不兼容或改变公开契约 | 改生成目录结构、改默认命令、移除字段、改变工作流语义 |

发布前必须确认：

- `plugin.json` 版本正确。
- README 没有旧版本叙述冲突。
- `packaging-manifest.json` 包含新增文件。
- 个人 skill 和发布包 skill 同步。
- `package-check --expected-version <version> --write-report` 通过。
- `docs/maintenance/IMPROVEMENT_LOG.md` 已记录升级原因、证据来源、变更文件和验证结果。

## 发布前检查口径

发布前不要只看 README 是否写好。至少检查：

| 检查项 | 目的 |
| --- | --- |
| `plugin.json` 版本 | 使用者安装到的版本和文档一致。 |
| `packaging-manifest.json` | 新增文档、模板、脚本被打包；本机残留和 cache 被排除。 |
| 可见 skill | 发布包只暴露 `codex-workbench`，不把内部 helper 暴露给新用户。 |
| README 链接 | 新用户能从 README 找到 workflow、scorecard、iteration、user workbench。 |
| 维护日志 | 能说明为什么升级、参考什么、改了什么、怎么验证。 |
| `package-check` | P0/P1/P2/P3 为 0 才能作为发布候选。 |

发布版本应该表达“行为契约变化”，不是每次改字都发一个大版本。

## 一次升级记录应该怎么写

维护日志位置：

```text
docs/maintenance/IMPROVEMENT_LOG.md
```

每条记录必须包含：

```text
问题：
证据来源：
- 用户反馈：
- 外部/官方资料：
- 本地失败证据：
决策：
变更文件：
验证结果：
后续动作：
```

不要只写“优化了文档”或“升级了工作台”。要能让下一个维护者看懂：

- 为什么要改。
- 改的是项目流程、模板、脚本、质量门、scorecard、发布包还是 README。
- 这次改动怎么验证。
- 还有什么风险没解决。

## 什么时候不能升级

这些情况不要升级工作台机制：

- 只有一次项目个案，而且可以用项目文档解决。
- 没有真实证据，只是感觉可能会出问题。
- 规则无法被检查，也没有人工确认点。
- 升级会让所有项目变重，但只服务一个特殊项目。
- 新增规则会和 Codex/skill/plugin 的公开边界冲突。

先把问题记录到项目 `FAILURE_LOG.md` 或维护日志草稿，等出现重复证据或高风险证据再升级。

## 参考资料

- OpenAI agent improvement loop: https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop
- OpenAI Codex iterative repair loop: https://developers.openai.com/cookbook/examples/codex/build_iterative_repair_loops_with_codex
- Google SRE postmortem culture: https://sre.google/workbook/postmortem-culture
- Google SRE incident management guide: https://sre.google/resources/practices-and-processes/incident-management-guide
- PDCA continuous improvement: https://theleanway.net/the-continuous-improvement-cycle-pdca
- Semantic Versioning: https://semver.org
