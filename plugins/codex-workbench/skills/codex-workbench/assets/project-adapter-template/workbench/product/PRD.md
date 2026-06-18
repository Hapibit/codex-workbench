# {{PROJECT_NAME}} 产品需求 PRD

status: draft
owner: project owner
updated_at: unconfirmed

本文件定义产品需求、用户故事、验收标准和非目标。AI 写代码前，重要功能必须能追溯到本文件或功能包 `SPEC.md`。

## 产品需求

| 编号 | 需求 | 用户/角色 | 优先级 | 来源 | 状态 |
| --- | --- | --- | --- | --- | --- |
| R001 |  |  | must | PROJECT_INTAKE.md | draft |

## 用户故事

| 编号 | 用户故事 | 验收标准 | 失败路径 | 对应功能包 |
| --- | --- | --- | --- | --- |
| US001 | 作为...我希望...以便... | Given/When/Then 或可测试条件 |  |  |

## 非目标

- 

## 验收标准

- [ ] 主流程可被用户独立完成。
- [ ] 至少一个关键失败路径有反馈。
- [ ] 权限、数据归属和隐私边界有说明。
- [ ] AI 输出的来源、边界、人工确认或回滚规则已定义。

## 变更规则

- 需求变化先改 PRD，再更新 `UX_SPEC.md`、`ARCHITECTURE.md`、`workbench/features/<feature-name>/SPEC.md`。
- 如果需求变化影响已实现功能，必须在对应功能包 `CHANGELOG.md` 和 `VERIFY.md` 记录复测。
- 如果需求无法明确，先更新 `CHANGE_REQUEST.md` 和 `IMPACT_ANALYSIS.md`，必要时向用户确认，不要让 AI 直接实现。
