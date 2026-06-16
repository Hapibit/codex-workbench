# 功能审查 REVIEW

status: pending
reviewed_by: unconfirmed
reviewed_at: unconfirmed
workbench_upgrade_assessment: unassessed

## 审查依据

- `SPEC.md`：
- `PLAN.md`：
- `TASKS.md`：
- `VERIFY.md`：
- 相关代码/测试/diff：
- 项目 `REVIEW.md`：

## 审查结果

- [ ] 未发现 P0/P1。
- [ ] 存在 P0/P1，不能交付。
- [ ] 仍有未验证风险，需要说明。

## P0/P1 检查

- [ ] 没有数据泄露。
- [ ] 没有权限绕过。
- [ ] 没有破坏核心流程。
- [ ] 没有不可逆数据损坏。
- [ ] 没有硬编码密钥、token、cookie 或个人路径。
- [ ] 没有绕过质量门、测试、CI 或人工确认。
- [ ] 没有把未确认需求当成已确认事实。
- [ ] 没有超出 SPEC 范围的大改动。

## 产品下限检查

- [ ] 满足 `PRODUCT_BASELINE.md` 的主成功路径要求。
- [ ] 失败、空状态、加载、无权限有反馈。
- [ ] UI/API/AI 输出对用户可理解。
- [ ] 旧功能兼容性已考虑。
- [ ] VERIFY 里的证据足以证明验收标准，而不是只证明命令执行过。

## 代码质量检查

- [ ] 改动范围合理，没有无关重构。
- [ ] 沿用项目已有结构和命名。
- [ ] 没有 AI 幻觉出来的 API、字段、组件、配置或依赖。
- [ ] 测试或验证能在行为坏掉时失败。
- [ ] 删除、迁移、权限、数据写入、外部调用等高风险路径有回滚或补救说明。
- [ ] 文档、测试、schema、fixture、mock、eval 和 CI 与实现保持同步。

## 需求符合性检查

| SPEC 验收项 | 实现证据 | 验证证据 | 结论 |
| --- | --- | --- | --- |
|  |  |  |  |

## 审查发现

```text
P1 path/to/file.ext:123 - 问题标题
风险：
触发场景：
修复方向：
```

## AI 错误证据

当 AI 实现错误、漏测、误判风险、绕过流程或生成幻觉 API 时填写：

- 错误类型：需求 / 实现 / 测试 / 审查 / 工具 / 规则 / 流程
- 严重级别：P0 / P1 / P2 / P3
- 触发场景：
- 证据位置：`VERIFY.md` / diff / 测试日志 / 用户反馈
- 修复方向：
- 是否阻塞交付：

## 自动化改进

本次发现中，应该沉淀到测试、lint、CI、hook 或质量门的项：

- 

## 工作台升级判断

`workbench_upgrade_assessment` 必须在审查结束前改成以下之一，不能保持 `unassessed`：

| 值 | 使用场景 | 必填证据 |
| --- | --- | --- |
| `not_required` | 一次性问题，已经在当前功能修复并验证，不需要升级工作台机制。 | 写明原因和验证位置。 |
| `failure_log_updated` | 同类问题重复出现，或需要后续归纳。 | 写明 `workbench/feedback/FAILURE_LOG.md` 条目。 |
| `template_update_needed` | 模板缺字段、缺检查项或容易让 AI 漏掉信息。 | 写明要改的模板。 |
| `quality_gate_update_needed` | 问题可由脚本、scorecard 或质量门稳定发现。 | 写明建议检查规则。 |
| `review_rule_update_needed` | review 漏掉风险或 P0/P1 定义不清。 | 写明要改的审查规则。 |
| `ci_or_hook_needed` | 需要 CI、pre-commit、hook 或其他硬门禁防止绕过。 | 写明建议门禁位置。 |
| `deferred_with_reason` | 暂不升级。 | 写明原因、风险和后续复查点。 |

## 复查结论

- 是否允许交付：
- 阻塞项：
- 未验证风险：
- 需要写入 `FAILURE_LOG.md` 的重复问题：
- 工作台升级判断：
