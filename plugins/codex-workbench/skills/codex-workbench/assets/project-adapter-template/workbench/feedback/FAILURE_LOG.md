# AI 失败与改进日志

本文件记录跨功能、重复出现、值得沉淀到工作台规则或自动化检查里的问题。单个功能的证据先写在对应功能包内，本文件只记录需要复用的经验。

## 记录规则

出现以下情况必须记录：

- AI 重复犯同类错误。
- 质量门失败后发现模板、规则或脚本需要改。
- 审查漏掉 P0/P1/P2 问题。
- 需求澄清不足导致返工。
- 验证不足导致问题交付后才发现。
- 用户指出工作台流程、分级、证据归档或工具路由不合理。

不要把普通聊天记录、临时想法或无法复用的个人偏好写进来。

升级规则：

- 第一次出现：优先在对应功能包 `VERIFY.md`、`REVIEW.md`、`DECISIONS.md` 记录。
- 每次功能审查结束前，必须在功能 `REVIEW.md` 的 `workbench_upgrade_assessment` 写明是否需要升级工作台；不能只在最终回复里口头说明。
- 同类问题第二次出现：写入本文件，并判断是否需要改模板、审查清单或质量门。
- 同类问题第三次出现，或一次就造成 P0/P1：必须优先考虑脚本、测试、CI、hook 或质量门，不再只加 Markdown 规则。
- 如果暂时不能自动化，必须说明原因和人工复查位置。

## 证据归档位置

单个功能的问题证据放在：

```text
workbench/features/<feature-name>/VERIFY.md
workbench/features/<feature-name>/REVIEW.md
workbench/features/<feature-name>/DECISIONS.md
```

放置规则：

- `VERIFY.md`：放失败命令、失败场景、未验证项、复测结果和剩余风险。
- `REVIEW.md`：放审查发现、严重级别、触发场景、修复方向和是否仍阻塞交付。
- `DECISIONS.md`：放为什么改变方案、为什么偏离计划、为什么新增规则或自动化。
- 本文件：只记录这个问题是否应该变成规则、测试、质量门、CI、hook 或模板改进。

## 失败记录模板

### YYYY-MM-DD 问题标题

- 来源功能包：`workbench/features/<feature-name>/`
- 问题类型：需求 / 实现 / 测试 / 审查 / 工具 / 规则 / 流程
- 严重级别：P0 / P1 / P2 / P3
- 触发次数：1 / 2 / 3+
- 现象：
- 根因：
- 已修复位置：
- 复现方式：
- 防复发证据：
- 对应功能 `REVIEW.md` 的 `workbench_upgrade_assessment`：
- 应沉淀为：
  - [ ] 需求澄清问题
  - [ ] SPEC/PLAN/TASKS 模板
  - [ ] VERIFY/REVIEW 清单
  - [ ] 单元/接口/E2E/AI eval 测试
  - [ ] `workbench/quality/quality_gate.py`
  - [ ] CI/pre-commit/hook
  - [ ] `AGENTS.md` / `WORKBENCH.md` / `REVIEW.md`
- 自动化状态：未处理 / 已加入待办 / 已实现 / 不适合自动化
- 不适合自动化的原因：
- 复查结果：