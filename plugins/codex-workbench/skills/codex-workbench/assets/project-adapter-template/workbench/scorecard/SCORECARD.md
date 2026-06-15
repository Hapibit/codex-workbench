# {{PROJECT_NAME}} 工作台证据审计卡

scorecard_status: draft
score_confidence: low
calibration_status: draft
semantic_review_status: pending
architecture_review_status: pending
owner: project owner
updated_at: unconfirmed

本文件记录当前项目工作台的 `decision`、参考分、可信度、硬阻塞、人工复核和改进动作。脚本报告来自 `workbench/scorecard/scorecard.py`；业务、产品、UX、架构和 AI 质量判断必须由人工或独立审查补充。

## 当前审计结果

运行：

```bash
python workbench/scorecard/scorecard.py --profile standard --write-report
```

报告位置：

```text
.workbench-validation/scorecard-report.json
```

| 时间 | 档位 | decision | 参考分 | 等级 | 硬阻塞数 | 主要风险 |
| --- | --- | --- | ---: | --- | ---: | --- |
|  | standard |  |  |  |  |  |

## 可信度

参考分必须和 `decision`、可信度一起看。

| 项目 | 当前值 | 证据位置 | 说明 |
| --- | --- | --- | --- |
| score_confidence | low | `.workbench-validation/scorecard-report.json` | high / medium / low |
| calibration_status | draft | `workbench/scorecard/CALIBRATION.md` | draft / reviewed / calibrated / accepted_with_risk |
| 组件参考下限缺口 | pending | `.workbench-validation/scorecard-report.json` | 不能让总分掩盖单项严重短板。 |
| 误报/漏报 | pending | `workbench/scorecard/CALIBRATION.md` | 用于调整参考线和脚本，不用于手工刷分。 |

## 硬阻塞

| 编号 | 来源 | 问题 | 处理状态 | 修复位置 |
| --- | --- | --- | --- | --- |
| B001 | scorecard.py |  | open |  |

## 架构合理性复核

复核重点：

- 质量属性是否明确：可靠性、性能、安全、可维护性、可扩展性、可观测性。
- 模块边界是否清楚，没有把业务、数据访问、AI 调用、UI 状态混在一起。
- 数据流、权限边界、错误路径和回滚策略是否能被验证。
- 重要取舍是否进入 ADR，而不是只留在聊天记录。
- 当前架构是否匹配项目规模和团队能力，没有过度设计或过度简化。

| 项目 | 结论 | 证据位置 | 风险/动作 |
| --- | --- | --- | --- |
| 质量属性 | pending | `workbench/architecture/ARCHITECTURE.md` |  |
| 模块边界 | pending | `workbench/architecture/ARCHITECTURE.md` |  |
| 数据/API/AI 边界 | pending | `workbench/architecture/` |  |
| ADR | pending | `workbench/architecture/adr/` |  |

## 语义质量复核

脚本不能判断业务正确性。以下项目需要人或独立 AI 审查：

| 维度 | 结论 | 证据位置 | 风险/动作 |
| --- | --- | --- | --- |
| 产品目标 | pending | `workbench/product/PRODUCT_BRIEF.md` |  |
| PRD 验收标准 | pending | `workbench/product/PRD.md` |  |
| UX/原型 | pending | `workbench/design/` |  |
| AI eval/安全边界 | pending | `workbench/architecture/AI_DESIGN.md` |  |
| 验证和审查证据 | pending | `workbench/features/<feature-name>/VERIFY.md`、`REVIEW.md` |  |

## 审计解释

- `BLOCKED` 表示存在硬阻塞，不能靠总分通过。
- `PASS_WITH_RISK` 表示没有硬阻塞，但必须人工确认剩余风险。
- `PASS` 表示流程证据较完整，但仍不能替代测试、审查和业务验收。
- 分数高只代表证据链完整，不代表业务一定正确。
- 可信度低时，高分不能作为通过依据。
- 有硬阻塞时不能用高分绕过。
- 有组件参考下限缺口时，先补短板，不要只追总分。
- 没有 `CALIBRATION.md` 的锚定样例和人工抽查时，分数只能作为过程提示。
- 低风险小修可以只跑 `smoke`，但用户可见、跨模块、高风险、AI 自动写入数据、权限或数据库变更必须至少跑 `standard`。
- 发布、PR 或重大改动建议跑 `full`，并补充人工语义复核。

## 改进动作

| 编号 | 触发来源 | 问题类型 | 改进动作 | 自动化目标 | 状态 |
| --- | --- | --- | --- | --- | --- |
| I001 |  | 需求 / 产品 / UX / 架构 / 测试 / 审查 / 工具 / 流程 |  | 测试 / lint / CI / hook / 质量门 / 模板 | open |

## 误报/漏报摘要

详细记录放在 `CALIBRATION.md`。

| 类型 | 数量 | 最近样例 | 处理动作 |
| --- | ---: | --- | --- |
| 误报 | 0 |  |  |
| 漏报 | 0 |  |  |
