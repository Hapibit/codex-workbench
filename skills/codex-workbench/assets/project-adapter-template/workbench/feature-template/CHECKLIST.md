# 阶段门禁 CHECKLIST

feature_status: active
current_stage: spec
implementation_allowed: false
delivery_allowed: false

本文件是 SDD 功能工作包的阶段门禁。只有勾选项有证据时才勾选。

状态说明：

- `feature_status: active`：当前功能正在推进，质量门会检查阶段状态。
- `feature_status: on_hold`：暂存或暂停的功能包，质量门只检查文件结构，不要求交付完成。
- `feature_status: complete`：功能包准备交付，必须满足 SPEC/CLARIFY/PLAN/TASKS/VERIFY/REVIEW 状态要求。
- `current_stage` 只能是 `spec`、`clarify`、`plan`、`tasks`、`implement`、`verify`、`review`、`complete`。
- 阶段不能倒挂：进入 `plan` 前 SPEC 和 CLARIFY 必须可计划；进入 `tasks` 前 PLAN 必须可拆解；进入 `implement` 前 PLAN/TASKS 必须允许实现；进入 `review` 前 VERIFY 必须通过；进入 `complete` 前 REVIEW 必须通过。

## 分级门禁

- [ ] `SPEC.md` 已填写 `risk_level`，只能是 `l1`、`l2`、`l3` 或 `l4`。
- [ ] `SPEC.md` 已填写 `impact_score`、`uncertainty_score`、`rollback_score` 和 `risk_score`。
- [ ] 已检查硬触发器，`hard_triggers` 不是 `unclassified`。
- [ ] 已写明 `classification_reason`。
- [ ] 判断不清楚时已自动升一级或提出澄清问题。
- [ ] L3/L4 改动没有被降级成 L1/L2。

## SPEC 门禁

- [ ] 用户目标明确。
- [ ] SPEC 能追溯到 `PROJECT_INTAKE.md`、用户确认或项目文件证据。
- [ ] 范围内和范围外明确。
- [ ] 验收标准可测试。
- [ ] 失败和边界场景已列出。
- [ ] 权限、数据归属或隐私边界已说明。

## CLARIFY 门禁

- [ ] `CLARIFY.md` 没有未解决的阻塞问题。
- [ ] 默认假设都有依据和后续确认方式。
- [ ] 用户、代码、README、测试或 CI 能证明的事实已记录。

## PLAN 门禁

- [ ] 技术方案沿用项目现有结构和约定。
- [ ] 影响文件、接口、数据、UI 或 AI/RAG 变化已列出。
- [ ] 已说明备选方案、放弃原因、回滚步骤和未知项。
- [ ] 高风险点有人工确认或回滚策略。
- [ ] 验证计划覆盖主成功路径和至少一个关键失败路径。

## TASKS 门禁

- [ ] 任务足够小，可以逐项实现和验证。
- [ ] 每个任务都能追溯到 SPEC 或 PLAN。
- [ ] 每个任务有输入、输出、预计文件、验证和回滚说明。
- [ ] 高风险任务前有确认点。

## IMPLEMENT 门禁

- [ ] 实现没有越过 SPEC 范围。
- [ ] 实现偏离 PLAN 时，已更新 `DECISIONS.md`、`PLAN.md` 和 `TASKS.md`。
- [ ] 没有提交 secrets、个人路径、临时调试或绕过逻辑。

## VERIFY 门禁

- [ ] `VERIFY.md` 有真实命令、手工步骤、浏览器/API/AI eval 或合理未验证说明。
- [ ] 验证记录包含环境、输入、期望结果、实际结果和证据位置。
- [ ] 质量门已运行，或说明无法运行的原因。
- [ ] 剩余风险已写明。

## REVIEW 门禁

- [ ] `REVIEW.md` 已完成。
- [ ] 审查已核对 SPEC 符合性、验证证据充分性和需求变更同步。
- [ ] 没有未处理 P0/P1。
- [ ] 可自动化的问题已列入测试、lint、CI、hook 或质量门改进项。
