# 发布检查 RELEASE_CHECKLIST

status: draft
owner: project owner
updated_at: unconfirmed

本文件用于发布前检查，不替代 CI、质量门、人工验收或回滚演练。

## 发布范围

- 版本：
- 功能包：
- 变更范围：
- 不发布内容：

## 发布检查

- [ ] `PROJECT_INTAKE.md`、PRD、UX、架构和 release scope 没有冲突。
- [ ] 所有发布功能包 `VERIFY.md` 已通过。
- [ ] 所有发布功能包 `REVIEW.md` 无未解决 P0/P1。
- [ ] `workbench/delivery/TRACEABILITY.md` 没有本次发布相关 `missing` 项。
- [ ] `quality_gate.py --profile standard` 已通过。
- [ ] CI required checks 已通过或记录为 `unverified`。
- [ ] branch protection 已验证或记录为 `unverified`。
- [ ] 回滚步骤已写清。

## 风险确认

| 风险 | 影响 | accepted_risk | 用户确认 | deferred_follow_up |
| --- | --- | --- | --- | --- |
|  |  | false |  |  |

## 回滚

- 回滚触发条件：
- 回滚步骤：
- 数据回滚：
- 配置回滚：
- 验证命令：
