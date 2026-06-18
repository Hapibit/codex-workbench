# 绕过记录 BYPASS_LOG

绕过不能由 AI 自己决定。本文件只记录用户明确确认的临时绕过、受控删除或高风险审批结果。

## 固定字段

每条记录必须包含：

- `reason`
- `scope`
- `risk`
- `user_confirmation` / `approver`
- `expires_at`
- `follow_up`

## 记录

| 日期 | reason | scope | risk | user_confirmation / approver | expires_at | follow_up | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  | draft |

## 规则

- 用户明确要求的安全删除可以放行，但必须先做路径校验和范围确认。
- AI 不能用 bypass 逃避 feature package、验证或 review。
- 高风险绕过后必须进入 `LEARN`，判断是否要升级 hook、quality gate、CI 或模板。
