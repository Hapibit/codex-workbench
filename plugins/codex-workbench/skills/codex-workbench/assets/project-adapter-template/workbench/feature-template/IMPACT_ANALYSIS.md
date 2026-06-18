# 影响分析 IMPACT_ANALYSIS

status: draft
analysis_updated_at: unconfirmed
baseline_update_required: unclassified
traceability_update_required: unclassified

本文件发生在实现前。输入是变更请求、长期基线文件和当前项目状态；实现后由 `quality_gate.py` 再用 git diff 校验影响分析是否准确。

## 影响摘要

- 影响结论：
- 风险等级：light / standard / strict / unclassified
- 是否需要人工确认：

## 基线影响

| 资产 | 是否影响 | 需要更新 | 说明 |
| --- | --- | --- | --- |
| `PROJECT_INTAKE.md` | unknown | unknown |  |
| `workbench/product/PRODUCT_BRIEF.md` | unknown | unknown |  |
| `workbench/product/PRD.md` | unknown | unknown |  |
| `workbench/design/UX_SPEC.md` | unknown | unknown |  |
| `workbench/design/USER_FLOW.md` | unknown | unknown |  |
| `workbench/design/PROTOTYPE.md` | unknown | unknown |  |
| `workbench/architecture/ARCHITECTURE.md` | unknown | unknown |  |
| `workbench/architecture/API_DESIGN.md` | unknown | unknown |  |
| `workbench/architecture/DATA_MODEL.md` | unknown | unknown |  |
| `workbench/architecture/AI_DESIGN.md` | unknown | unknown |  |
| `workbench/delivery/TRACEABILITY.md` | unknown | unknown |  |
| `workbench/delivery/RELEASE_PLAN.md` | unknown | unknown |  |

## 预计影响 ID

| ID | 来源 | 预计动作 | 验证位置 |
| --- | --- | --- | --- |
|  |  | update / keep / n/a | `VERIFY.md` |

## 代码和工程影响

- 受控代码：
- 测试：
- CI/CD：
- 配置：
- 依赖：
- 数据迁移：
- 权限：
- AI/RAG/Agent：

## 路由结论

- `workflow_profile`：
- 选择理由：
- strict 触发器：
- 降级理由：

## 后续同步

- 需要更新的基线文件：
- 需要更新的测试或 eval：
- 需要更新的 release / rollback：
- 不需要更新的理由：
