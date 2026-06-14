# Workbench Failure Patterns

本文件记录 `codex-workbench` 自身反复出现的失败模式，以及这些失败最后落到了哪一层处理。它不是普通复盘流水账；只有会影响后续工作台质量的模式才写进来。

## 分类规则

- 需求问题：用户目标、范围、验收、权限或数据边界没有澄清。
- 规则问题：Markdown 规则太长、太软、太分散，导致模型跳过或误读。
- 工具问题：skill、MCP、hook、脚本、质量门或发布检查没有被正确调用。
- 模板问题：生成给项目的新文件缺字段、缺状态、缺证据位置。
- 发布问题：插件包包含个人路径、缓存、内部备份、未声明的增强 skill 或缺少接收者边界。
- 验证问题：只说验证，没有真实运行脚本、测试、doctor、package-check 或独立审查。

## 处理层

- 说明层：放在 `README.md`、`SKILL.md` 或 `references/`，只用于解释。
- 模板层：放进 `assets/project-adapter-template/`，让新项目自动获得规则。
- 脚本层：放进 `scripts/`，用 `validate`、`audit`、`doctor`、`package-check` 检查。
- hook/CI 层：需要强制阻断时放到 hook、pre-commit、CI、测试或质量门。
- ADR 层：长期架构边界或发布策略，放到 `docs/maintenance/adr/`。

## 失败模式

### FP-004 - 模板有流程但缺少可复查证据

失败模式：

工作台生成了 SPEC、PLAN、TASKS、VERIFY、REVIEW 等文件，但模板只要求“写计划、跑验证、做审查”，没有明确要求事实来源、验收用例、输入输出、证据位置、复测结果、需求变更同步和计划偏离记录。结果是 AI 可能表面完成流程，后续复查时仍不知道依据是什么、证明在哪里、哪些风险没验证。

证据位置：

- `assets/project-adapter-template/workbench/feature-template/SPEC.md` 曾缺少事实源、来源依据和变更记录。
- `assets/project-adapter-template/workbench/feature-template/PLAN.md` 曾缺少备选方案、回滚和未知项。
- `assets/project-adapter-template/workbench/feature-template/TASKS.md` 曾缺少输入、输出、预计文件、证据位置和回滚要求。
- `assets/project-adapter-template/workbench/feature-template/VERIFY.md` 曾偏命令记录，验收证据字段不够完整。
- `assets/project-adapter-template/workbench/feature-template/REVIEW.md` 曾缺少 SPEC 符合性和验证证据充分性检查。

工作台处理层：

- 模板层：强化 PROJECT_INTAKE、SPEC、CLARIFY、PLAN、TASKS、DECISIONS、CHECKLIST、VERIFY、REVIEW 和 FAILURE_LOG。
- 说明层：WORKBENCH 和 REVIEW 增加需求变更、事实源、证据充分性和复查规则。
- 脚本层：暂不新增强校验，避免让模板变脆；先通过自检、golden-test、doctor 和 package-check 保障结构。

自动化状态：

- 已加入模板。后续如果真实项目重复出现“只写命令没有验收证据”，再升级为 `quality_gate.py` 或 `audit` 检查。

### FP-001 - 工作台自身升级证据没有版本化

失败模式：

工作台升级依据只存在于对话和临时报告中，缺少随插件发布的维护证据。后果是后续复查时不知道为什么改、参考了什么资料、哪些问题已经被脚本或模板解决。

证据位置：

- `.workbench-validation/package-check-report.json` 只保存机器报告，不适合人工维护证据。
- 插件根目录曾缺少 `docs/maintenance/IMPROVEMENT_LOG.md` 和 `docs/maintenance/FAILURE_PATTERNS.md`。

工作台处理层：

- 说明层：README 解释 `.workbench-validation/` 与 `docs/maintenance/` 的边界。
- 脚本层：`package-check` 和 `doctor` 检查维护证据文件。
- ADR 层：`docs/maintenance/adr/README.md` 规定需要 ADR 的场景。

自动化状态：

- 已加入发布检查：缺维护证据为 P1，内容过薄或缺关键字段为 P2。

### FP-002 - 软规则容易被跳过

失败模式：

只把“必须搜索、必须澄清、必须验证、必须记录证据”写在 Markdown 中，模型在长会话、短指令或上下文压力下仍可能跳过。

证据位置：

- 全局规则已指出 Markdown 不是硬约束。
- 项目适配器已经加入质量门、状态字段和失败日志，但插件发布检查之前没有覆盖维护证据。

工作台处理层：

- 说明层：保留短规则和路由说明。
- 脚本层：能检查的发布要求放到 `doctor`、`package-check`、项目 `quality_gate.py`。
- hook/CI 层：危险命令、绕过审批、绕过验证等必须由 hook、CI 或项目质量门阻断。

自动化状态：

- 部分已自动化。后续每发现一个“AI 又跳过”的高频问题，都要判断能否提升为脚本、hook、CI 或测试。

### FP-003 - 新用户学习成本过高

失败模式：

如果把第三方 skill、MCP、Figma、draw.io、Jenkins、文档工具全部当成必装项，新用户会误以为必须先配置一堆东西才能用工作台。

证据位置：

- `SKILL.md` 已定义 `codex-workbench` 是唯一公开入口。
- `references/enhancement-packs.md` 和 `assets/enhancements.json` 管理可选增强包。

工作台处理层：

- 说明层：README 和接收者边界说明“基础工作台可单独运行，增强包按任务推荐”。
- 脚本层：`check_enhancements.py` 用于按任务检测可用增强包。

自动化状态：

- 已部分自动化。发布检查要求 visible skill 只能是 `codex-workbench`。
