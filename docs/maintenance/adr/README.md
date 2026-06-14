# ADR Guide

本目录保存 `codex-workbench` 自身的 Architecture Decision Records。ADR 只记录会长期影响工作台架构、发布边界、插件结构、硬门禁策略或新用户使用路径的决策；普通小修放在 `IMPROVEMENT_LOG.md`。

## 什么时候写 ADR

- 改变公开入口，例如从多个 skill 改成只暴露 `codex-workbench`。
- 改变发布包结构，例如新增或移除 `hooks/`、`.mcp.json`、`docs/maintenance/`。
- 改变硬门禁策略，例如把某个检查从 Markdown 升级为 hook、CI 或 package-check。
- 改变接收者边界，例如决定哪些配置必须由用户自己完成。
- 改变项目工作台流程，例如 SDD 强度分级、项目预处理、功能工作包状态机。

## 文件命名

```text
0001-short-decision-title.md
0002-short-decision-title.md
```

编号单调递增。被替代的 ADR 不直接改写结论，应新增 ADR 并在旧 ADR 标记 `Status: superseded`。

## 模板

```markdown
# ADR-0000: Title

Status: proposed | accepted | superseded
Date: YYYY-MM-DD

## Context

为什么需要这个决策。包括用户反馈、官方资料、失败证据、替代方案。

## Decision

选择什么方案，以及不选择什么方案。

## Consequences

正面影响、代价、风险、迁移要求和验证方式。
```
