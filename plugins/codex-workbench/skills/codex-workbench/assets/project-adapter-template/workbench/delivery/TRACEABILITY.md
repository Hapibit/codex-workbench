# 追踪矩阵 TRACEABILITY

本文件只做索引：`ID -> 来源 -> 影响资产 -> 实现位置 -> 验证位置 -> 状态`。不要把 PRD、UX、API、测试报告全文复制进来。

## 状态

- `covered`：已有实现和验证证据。
- `partial`：只覆盖部分路径，必须说明缺口。
- `missing`：应覆盖但未覆盖，不能宣称完成。
- `n/a`：经影响分析确认不适用。

## 矩阵

| ID | 类型 | 来源 | 影响资产 | 实现位置 | 验证位置 | 状态 | 说明 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| REQ-001 | requirement | `workbench/product/PRD.md` |  |  |  | missing |  |
| UX-001 | ux | `workbench/design/UX_SPEC.md` |  |  |  | missing |  |
| API-001 | api | `workbench/architecture/API_DESIGN.md` |  |  |  | missing |  |
| AI-001 | ai | `workbench/architecture/AI_DESIGN.md` |  |  |  | missing |  |

## 更新时机

1. 在 `IMPACT_ANALYSIS.md` 中写预计影响哪些 ID。
2. 在 `VERIFY.md` / quality gate 后，把状态更新为 `covered`、`partial`、`missing` 或 `n/a`。
3. 如果本次不影响矩阵，必须在 `IMPACT_ANALYSIS.md` 写明理由。
