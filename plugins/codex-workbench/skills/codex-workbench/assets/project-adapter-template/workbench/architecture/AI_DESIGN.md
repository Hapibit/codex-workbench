# {{PROJECT_NAME}} AI 设计

status: draft
owner: project owner
updated_at: unconfirmed

本文件记录 AI/RAG/Agent 的输入、输出、工具、数据来源、人工确认、隐私和 eval。AI 输出影响核心数据或用户权益时最低按 L3 功能处理。

## AI 能力

| 能力 | 输入 | 输出 | 是否自动生效 | 人工确认 | 对应需求 |
| --- | --- | --- | --- | --- | --- |
|  |  |  | no | required |  |

## 数据来源和工具

| 来源/工具 | 用途 | 权限 | 不允许用途 | 日志要求 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## 禁止行为

- 

## Eval 标准

| 维度 | 通过标准 | 数据集/样例 | 失败处理 |
| --- | --- | --- | --- |
| 正确性 |  |  |  |
| 安全性 |  |  |  |
| 可追溯性 |  |  |  |

## 迭代规则

- AI 表现变化、返工、幻觉、工具误用、RAG 错误必须记录到功能包 `VERIFY.md` / `REVIEW.md`。
- 跨功能重复问题汇总到 `workbench/feedback/AI_EFFECTIVENESS.md` 和 `FAILURE_LOG.md`。

