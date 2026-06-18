# {{PROJECT_NAME}} 开发流程契约

status: draft
owner: project owner
confirmed_at: unconfirmed
scope: project-specific changes
verification_commands:
{{QUALITY_COMMANDS}}

## 作用

本文件定义本项目自己的开发作业流程。它不是全局通用流程，也不是个人 Codex 配置。

默认状态是 `draft`。在项目负责人确认前，AI 只能把它作为检查清单；涉及功能开发、公开接口、数据库、权限、生产发布、用户数据或 AI 自动生效逻辑时，必须先确认。

确认本流程前，先确认 `PROJECT_INTAKE.md`。项目画像仍是 `status: draft` 或存在 open 阻塞问题时，本文件不能升级为 `confirmed`。

## 状态规则

- `draft`：流程尚未确认。允许用于低风险阅读、分析、文档整理和小范围建议；不应直接作为功能开发硬流程。
- `confirmed`：流程已由项目负责人确认。AI 应按本文件执行项目开发，除非用户给出更新的项目级指令。
- 如果本文件与代码、README、CI、测试、产品要求或用户明确指令冲突，先停止并确认。

## 默认流程

1. 读取 `AGENTS.md`、`PROJECT_INTAKE.md`、`WORKBENCH.md`、`REVIEW.md`、`PRODUCT_BASELINE.md`、`FEATURE_WORKFLOW.md` 和本文件。
2. 先用 `PROJECT_INTAKE.md` 明确项目目标、第一版范围、用户角色、数据所有权、权限边界、AI 使用边界和验收下限。
3. 明确当前任务的目标、范围、验收标准、环境要求和回滚要求。
4. 新功能、跨模块或高风险改动按 `FEATURE_WORKFLOW.md` 建立功能工作包，并先完成 CHANGE_REQUEST/IMPACT_ANALYSIS/SPEC/DESIGN/PLAN/TASKS。
5. 先检查现有实现、测试、脚本、CI 和相关文档，再规划代码改动。
6. 按项目已有结构和命名做最小可验证改动。
7. 先跑最小可靠验证；跨模块、高风险或用户要求时扩大验证。
8. 按 `REVIEW.md` 和功能包 `REVIEW.md` 复查 diff；敏感或大范围改动使用独立审查。
9. 最终说明改了什么、运行了什么验证、哪些没验证、剩余风险是什么。

## 需求不清时

不要静默猜测会改变实现路线的问题。先读仓库能回答的信息；仍不清楚时只问必要问题。

必须确认的缺口：

- 用户可见验收标准不清楚。
- 影响页面、接口、模块、数据库表、模型或业务流程不清楚。
- 角色、权限、租户、组织、课程、用户、文件或其他数据归属边界不清楚。
- 涉及删除、迁移、批量修改、发布、回滚、凭证或不可逆行为。
- AI 生成内容是否自动生效、是否需要人工确认、来源和 eval 标准不清楚。

## 按改动类型执行

- Bugfix：先复现或定位失败行为；能自动化时补回归检查，再修复。
- Feature：确认验收标准和影响面；至少覆盖主流程和一个关键失败/边界路径。
- Feature package：新功能或高风险改动优先创建 `workbench/features/<feature-name>/`，填写 CHANGE_REQUEST/IMPACT_ANALYSIS/SPEC/DESIGN/PLAN/TASKS/DECISIONS/VERIFY/REVIEW/FEATURE_STATUS。
- AI/RAG/Agent：定义输入样例、期望行为、禁止行为、允许来源/工具、评分标准、日志和隐私边界。
- UI：实际浏览器检查桌面和移动端布局、控制台错误、横向溢出、文字裁切和核心交互。
- Backend/API：检查契约兼容、授权和数据归属、错误响应、幂等性、持久化边界。
- Docs-only：检查链接、命令、示例和描述是否符合项目真实行为。

## 人工确认清单

把 `status` 改成 `confirmed` 前，项目负责人至少确认：

- `PROJECT_INTAKE.md` 已经确认项目目标、第一版范围、用户角色、数据权限、AI 边界和关键验收。
- `PROJECT_INTAKE.md` 没有 open 阻塞问题；无法关闭的问题已明确为什么不阻塞。
- 本流程符合团队真实工作方式。
- `verification_commands` 是本项目真实可运行命令。
- 高风险审批边界准确。
- 必须不能跳过的检查已经进入质量门、测试、lint、pre-commit、CI 或 hook。
- docs-only、小 bugfix、feature、AI feature、UI 和 backend 路径都适合本项目。
- `PRODUCT_BASELINE.md` 的产品下限符合项目实际目标。
- `FEATURE_WORKFLOW.md` 的功能工作包流程不会给小改动制造不必要负担。

## 维护规则

同类问题重复出现时，先判断应该改哪里：

- 人工判断规则：更新本文件或 `REVIEW.md`。
- 可自动化检查：优先进入测试、lint、pre-commit、CI 或 `workbench/quality/quality_gate.py`。
- 工具能力缺口：更新 `WORKBENCH.md` 或补充 workbench 脚本。
