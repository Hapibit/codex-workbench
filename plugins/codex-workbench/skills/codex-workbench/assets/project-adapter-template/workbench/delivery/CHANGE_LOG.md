# 变更索引 CHANGE_LOG

本文件只记录 light 变更或项目级变更索引，不复制功能包全文。standard / strict 变更的详细证据应放在 `workbench/features/<feature-name>/`。

## 机器可读字段要求

每条记录必须包含：

- `change_id`
- `scope`
- `risk`
- `validation`
- `evidence`
- `reviewer`
- `gate_marker`
- `status`

机器读取以 fenced JSON 记录为准，表格只做人读摘要。light 变更的最小有效记录示例：

```json
{
  "change_id": "CHG-YYYYMMDD-001",
  "workflow_profile": "light",
  "scope": ["src/example.ts"],
  "risk": "light",
  "validation": "npm run build",
  "evidence": "workbench/delivery/CHANGE_LOG.md#CHG-YYYYMMDD-001",
  "reviewer": "self-review",
  "gate_marker": ".workbench-validation/quality-gate-ok.json",
  "status": "verified"
}
```

## 变更记录

| change_id | 日期 | scope | risk | validation | evidence | reviewer | gate_marker | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  | light/standard/strict |  |  |  | `.workbench-validation/quality-gate-ok.json` 或 n/a | draft |

## 使用规则

- light 变更可以只写本文件和最小验证证据。
- 只要影响 PRD、UX、API、DATA、AI、权限、发布或跨模块，就不能只靠本文件，必须进入 feature package。
- `quality_gate.py` 只把 fenced JSON 中 `workflow_profile/risk=light`、`status=ready|verified|passed|complete`、`change_id/scope/risk/validation/evidence/reviewer/gate_marker` 全部非空、`gate_marker` 指向 `.workbench-validation/`、且 `scope` 显式覆盖当前受控 diff 的记录当成有效 light 证据；空表格不是证据。
- `scope` 不能写 `*`、`all` 或 `.`。数据库、迁移、产品/设计/架构基线、质量门、runtime、feature template、feature package、traceability、release、权限、安全、支付、隐私或部署相关路径不能走 light。
