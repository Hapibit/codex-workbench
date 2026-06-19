# {{PROJECT_NAME}} 当前项目状态

status: draft
updated_at: unconfirmed
current_stage: CLASSIFY
active_feature: none
workflow_profile: unclassified
implementation_allowed: false
delivery_allowed: false

本文件是当前项目事实索引，不是长篇 PRD 或聊天记录。详细内容仍以 `PROJECT_INTAKE.md`、`workbench/product/`、`workbench/design/`、`workbench/architecture/` 和 `workbench/delivery/` 为准。

## 当前事实

- 项目目标：
- 第一版范围：
- 当前迭代：
- 当前功能包：
- 当前阻塞：

## 技术栈和运行方式

- 前端：
- 后端：
- 数据库：
- AI/RAG/Agent：
- 运行命令：
- 验证命令：

## 关键约束

- 用户/角色：
- 数据和权限：
- AI 输出边界：
- 发布和回滚：
- 不允许修改：

## 状态更新规则

- 每轮开始先读本文件和 `.workbench-validation/quality-workflow-state.json`；runtime 检查状态在 `.workbench-validation/runtime-state.json`。
- 本文件可以由 AI 建议更新，但不能替代 `quality_gate.py` 的判定。
- 当前阶段变化、active feature 变化、关键命令变化或风险变化后更新本文件。
- 如果本文件和 git diff、质量门报告、feature package 冲突，以独立证据为准。
