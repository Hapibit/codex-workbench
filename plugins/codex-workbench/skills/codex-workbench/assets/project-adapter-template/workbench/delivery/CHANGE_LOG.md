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

## 变更记录

| change_id | 日期 | scope | risk | validation | evidence | reviewer | gate_marker | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  | light/standard/strict |  |  |  | `.workbench-validation/quality-gate-ok.json` 或 n/a | draft |

## 使用规则

- light 变更可以只写本文件和最小验证证据。
- 只要影响 PRD、UX、API、DATA、AI、权限、发布或跨模块，就不能只靠本文件，必须进入 feature package。
- `quality_gate.py` 可以检查本文件是否有固定字段，但不能把空记录当成有效证据。
