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

### FP-016 - 完整 light JSON 仍可能降级高风险路径

失败模式：

即使 `CHANGE_LOG.md` fenced JSON 字段完整，如果质量门只看 `workflow_profile=light`、scope 覆盖当前 diff 和非空证据，AI 仍可能把 API、数据库、权限、架构、quality gate、runtime、release 等高风险路径伪装成 light 变更，绕过 feature package、影响分析和 review。

证据位置：

- 多 agent 质量门复查指出 `has_valid_light_change_record()` 没有路径级 hard trigger。
- `CHANGE_LOG.md` 自身规则已经说影响 PRD/UX/API/DATA/AI/权限/发布不能走 light，但脚本需要同步强制。

工作台处理层：

- 质量门层：新增 `is_light_allowed_path()`，禁止高风险受控路径和权限/安全/发布类命名走 light。
- 测试层：`quality-gate-contract` golden test 覆盖 wildcard `scope:["*"]` 失败和高风险 `workbench/architecture/API_DESIGN.md` light 降级失败。
- 模板层：`CHANGE_LOG.md` 明确必填字段、显式 scope 和 light 禁止路径。

自动化状态：

- 已自动化：wildcard scope、高风险路径 light 降级会失败。
- 仍需人工/CI：路径名无法完全识别业务风险；不确定时必须升级为 standard/strict 或走 feature package。

### FP-015 - strict accepted risk 和 traceability 可以被旧证据伪通过

失败模式：

strict 功能如果只检查 `TRACEABILITY.md` 里存在一些 covered 行，可能用旧矩阵覆盖新功能；如果 `VERIFY.md` 的未验证项只要写 `accepted_risk=true` 就通过，可能没有用户确认、替代验证和 follow-up。最终会把带风险交付伪装成 clean pass。

证据位置：

- 多 agent 质量门复查指出 strict traceability 未绑定 `IMPACT_ANALYSIS.md` 的预计影响 ID。
- 多 agent 复查指出 `accepted_risk` 空值或 true 但缺确认信息的行可能漏过。

工作台处理层：

- 质量门层：`require_traceability_evidence()` 解析 `IMPACT_ANALYSIS.md` 的预计影响 ID，要求每个 ID 在矩阵里有非 missing 状态和验证位置。
- 质量门层：strict 未验证项必须有明确 `accepted_risk=true/false`；true 时必须有用户确认、替代验证和 `deferred_follow_up`。
- marker 层：只要存在 accepted risk，`quality-gate-ok.json` 写 `passed_with_risk` 和 `accepted_risk_features`。
- 测试层：`quality-evidence-contract` 覆盖旧矩阵伪通过失败、不完整 accepted risk 失败、完整 accepted risk 只能 `passed_with_risk`。

自动化状态：

- 已自动化：impact ID 缺矩阵、缺验证位置、未接受或不完整接受风险会失败。
- 仍需人工/CI：用户确认是否真实、替代验证是否足够、traceability 是否覆盖完整业务宇宙仍需 review/CI/人工验收。

### FP-014 - 发布同步和 hook 只读豁免可能形成假安全

失败模式：

doctor/package-check 如果找不到个人 skill 镜像时回退到当前脚本目录，会把插件包自己和自己比较，形成同步假阳性。hook 如果只看命令前缀，把“只读搜索 + 后续破坏性命令”的复合命令当作只读命令，会让危险动作绕过 destructive 检查。`hooks.json` matcher 如果只覆盖旧工具名，也可能漏掉当前 `functions.shell_command` / `functions.apply_patch`。

证据位置：

- 多 agent 发布/hook 复查指出 personal/plugin sync 自比自、只读快路径覆盖复合命令、matcher 未覆盖当前工具命名。
- 当前本地 `package-check` 在插件脚本改动后报告 personal/plugin drift，说明发布前必须同步个人镜像并重跑检查。

工作台处理层：

- 脚本层：`doctor_workbench()` 默认检查 `~/.codex/skills/codex-workbench`；不存在时报 P1，不再 fallback 到插件 skill。
- 发布层：`package-check` 输出 materialized manifest file list hash，并扫描核心 `workbench.py` 的 secret/path 风险。
- hook 层：只读豁免要求单一命令且无 shell 控制符；复合命令继续做危险命令扫描。
- hook 配置：`hooks.json` matcher 覆盖 `functions.*`、`shell_command` 和 `multi_tool_use.*`。
- 测试层：`plugin-hook-hard-gate` 覆盖单一只读搜索不 deny、只读前缀加后续危险动作会 deny。

自动化状态：

- 已自动化：个人 skill 缺失/漂移会导致 doctor/package-check P1；复合只读加危险动作会被 hook deny。
- 仍需人工：真正发布前仍需确认使用 manifest 产物，不把 `.workbench-validation/` 直接压进包。

### FP-012 - 状态已通过但证据表仍为空或阻塞项仍存在

失败模式：

AI 可以把 `VERIFY.md status: passed`、`REVIEW.md status: passed` 或 `FEATURE_STATUS.json delivery_allowed: true` 写成通过状态，但实际证据表仍为空、review 仍勾选 blocking P0/P1，或 strict 功能没有清掉 `TRACEABILITY.md` 的 `missing` 行。这样下一层如果只检查 status 字段，就会把“流程文字完成”误判成“证据链完成”。

证据位置：

- 多 agent quality-gate 复检指出 `VERIFY.md`、`REVIEW.md` 和 strict `TRACEABILITY.md` 仍偏状态字段检查。
- 架构稿第 18 节要求空 `VERIFY`、未解决 P0/P1、strict traceability missing 这类绕过路径必须有 golden test。
- NASA Software Engineering Handbook 强调 traceability 要连接需求、设计、代码和测试，并支持变更影响分析。
- W3C WAI 明确自动化无障碍工具只能辅助判断，不能单独决定 accessibility。

工作台处理层：

- 质量门层：生成型 `quality_gate.py` 新增 `require_verify_evidence`、`require_review_evidence` 和 `require_traceability_evidence`，检查 passed 状态与证据形态、blocking P0/P1、strict traceability 状态是否冲突。
- 测试层：`golden-test` 新增 `quality-evidence-contract`，证明空 `VERIFY.md`、blocking `REVIEW.md` 和 strict `TRACEABILITY.md missing` 会失败。
- 文档层：README 和架构稿明确这些只是证据形态和一致性检查，不能证明证据真实性、review 未漏判、UI/a11y/eval 充分。

自动化状态：

- 已自动化：`quality-evidence-contract` 覆盖三条绕过路径。
- 仍需人工/CI：证据内容是否真实、P0/P1 是否被审查遗漏、traceability 是否覆盖完整需求宇宙、UI/a11y/eval 是否充分，仍必须由真实测试报告、CI artifact、独立 review 或人工验收支撑。

### FP-013 - 发布扫描漏掉 JSON 转义个人路径或同步残留

失败模式：

发布包检查只匹配未转义的 Windows 绝对路径，可能漏掉 JSON 文件里被双反斜杠转义的 Windows 用户目录；同时如果本地同步残留如 `assets/assets`、`references/references`、`scripts/scripts` 没被 manifest 和扫描规则同时覆盖，按本地目录打包时可能带出不该发布的文件。

证据位置：

- 多 agent docs/release 复检指出 `.workbench-validation/package-check-report.json` 中出现 JSON escaped Windows 路径，但 package-check 没报错。
- `packaging-manifest.json` 已经把 `.workbench-validation/**` 标为排除项，但脚本层需要同时要求 nested sync residue 排除项。

工作台处理层：

- 脚本层：个人路径正则支持一个或多个反斜杠，能匹配 JSON escaped Windows path。
- 发布层：`PACKAGING_MANIFEST_REQUIRED_EXCLUDES` 要求排除 `.workbench-validation/**` 和 nested sync residue；`scan_publish_tree` 跳过 `.workbench-validation` 生成报告目录，避免 `package-check --write-report` 自毁，但仍扫描实际发布树和 manifest。
- 文档层：manifest longDescription 增加 hook trust、project generation 和 CI/branch protection 边界。

自动化状态：

- 已自动化：`doctor`、`package-check` 会检查 manifest 排除项、个人路径和发布残留。
- 仍需人工：如果用户绕过 manifest 直接压缩整个本地目录，仍要遵守 README 的发布边界；`.workbench-validation/` 不应进入发布包。

### FP-011 - 防跳过门禁只看当前目录或旧 marker

失败模式：

AI 或脚本实际触碰 nested repo、绝对路径、patch 新增配置或受控代码 diff，但 hook / quality gate 只看当前 `cwd`、marker mtime 或软 Markdown 状态，导致“跳过流程、绕过审批、漏跑质量门”可能没有被下一层发现。

证据位置：

- 多 agent 审查指出 Stop 只看 `hook.cwd`、marker 只看 mtime、patch 不扫描 bypass 配置、受控代码 diff 没有强制 feature/light 记录。
- 手工模拟发现 `approval_policy = 'never'` 这类空格加引号写法需要正则兜底。
- Git 官方文档说明 `pre-commit` / `commit-msg` 可被 `--no-verify` 绕过；GitHub protected branches / required checks 才适合承担远程合并门禁。

工作台处理层：

- hook 层：从 patch headers、命令路径和 `cwd` 归因 touched repo；Stop 遍历 touched repo；patch 新增绕过配置直接 deny；异常分支按事件 fail-closed。
- 质量门层：受控 diff 必须有关联 feature package 或机器可读 light `CHANGE_LOG`；marker 校验 schema、status、`git_head`、`diff_hash`、`checks_run`、scorecard 风险字段。
- 文档层：README 降级“质量门证明语义正确”的表述，明确证据真实性、P0/P1 语义、strict traceability、UI/a11y/eval 仍需 review/CI/人工判断。

自动化状态：

- 已加入 `golden-test` 的 `quality-gate-contract`。
- Hook 关键路径已沉淀为 `plugin-hook-hard-gate` golden case。

### FP-010 - hook 把明确授权的普通目录删除误判为危险命令

失败模式：

工作台硬门禁为了阻止破坏性命令，把所有 `Remove-Item -Recurse -Force` 都当作高风险操作阻断。这样能防止误删，但也会误杀用户明确要求、AI 已经解析并校验过绝对路径的普通项目目录删除，例如清理不属于工作台结构的根目录 `docs\`。

证据位置：

- 用户明确要求删除 `E:\ai-edu-agent\docs`，但 `PreToolUse` hook 仍然阻断。
- 旧规则只用正则 `Remove-Item.*-Recurse.*-Force` 判断，没有区分 `-LiteralPath`、路径根、仓库根、工作台核心目录和普通项目目录。
- 只读搜索命令里出现危险命令样例时，也可能被 destructive 检查误伤。

工作台处理层：

- hook 层：新增 `Test-AllowedExplicitRecursiveDelete`、`Test-ProtectedDeletionPath` 和 `Get-LiteralPathsFromCommandSegment`，允许明确绝对路径且非保护目录的 `Remove-Item -LiteralPath ... -Recurse -Force`。
- hook 层：继续阻止盘符根、用户目录、`.codex`、仓库根、`.git`、`workbench` 核心目录、工作台规则文件和 `workbench/docs`。
- 脚本层：`package-check` 检查插件 hook 是否包含显式递归删除、保护路径和只读搜索识别逻辑。

自动化状态：

- 已自动化：发布包 hook 和个人 hook 同步修正；发布检查会检查关键防护函数是否存在。
- 仍需人工：真正执行递归删除前，仍要由用户明确指定目标；AI 不能自行扩大删除范围，也不能把路径变量、通配符或相对路径当作安全目标。

### FP-008 - AI 跳过阶段门或发明工作台目录层

失败模式：

当用户给出“开始、继续、规划、复查”等短指令时，AI 可能按工程直觉直接推进实现，而不是先读取项目画像、开发流程、功能包状态和验证证据。另一个表现是 AI 把根目录 `docs/` 或自己生成的 `workbench/docs/` 解释成新的工作台阶段，导致项目结构和工作台契约不一致。

证据位置：

- 用户在真实会话中指出 AI 没有按工作台规则来，并要求回顾为什么跳过规则。
- 会话复盘显示：AI 没有把工作台当成状态机使用，没有先读当前阶段和功能包状态，还把 `docs/` 解释成“交付阅读层”。
- `assets/project-adapter-template/` 已有阶段说明，但旧 `validate/audit` 没有检查工作台顶层目录契约。

工作台处理层：

- 模板层：`AGENTS.md` 和 `WORKBENCH.md` 增加 `执行门禁`、`目录契约` 和 `偏离复盘`。
- 脚本层：`validate`、`audit` 和生成的 `quality_gate.py` 检查 `workbench/` 顶层目录契约；`workbench/docs/` 这类未声明目录会成为 P1 或质量门失败。
- 回归层：`golden-test` 增加 guardrails 用例，确认未声明 `workbench/docs/` 会失败，根目录 `docs/` 只触发分类警告。
- 维护层：重复偏离必须进入 `FAILURE_LOG.md`，并判断应升级模板、脚本、质量门、hook、CI、review prompt 还是回归测试。

自动化状态：

- 已自动化：新项目模板包含门禁说明；`validate/audit` 和质量门检查目录契约；`golden-test` 覆盖目录误用。
- 仍需人工：会话职责、搜索优先级和业务语义判断不能完全靠脚本判断；需要 AI 在执行前做状态自检，发现偏离时先复盘。

### FP-009 - 插件有 hook 但没有说明仍需用户信任

失败模式：

发布包可以携带 hooks/hooks.json 和 hook 脚本，但如果 README 没有明确说明“安装后仍需每个使用者自己在 Codex 里 review/trust”，用户可能误以为安装插件就自动获得了系统级硬门禁。这样会把可审查的本地 guardrail 误读成自动可信的全局策略。

证据位置：

- 官方 hooks 文档说明：非 managed command hooks 需要 review 和 trust；插件可以携带 hook，但不会自动跳过 trust。
- 本地 README 早期只说明了 skill、模板和维护证据，没有说明插件 hook 的 trust 边界。
- 发布包最初没有 hooks/ 目录，导致“装了插件就有门禁”的预期和现实不一致。

工作台处理层：

- 说明层：README 增加“插件带 hook，但安装后仍需 trust”的说明。
- 发布层：`packaging-manifest.json` 允许并显式记录 `hooks/**`。
- 脚本层：`package-check` 检查 hook JSON、hook 脚本和关键防护词，避免发布包漏掉本地门禁。

自动化状态：

- 已自动化：发布包会检查 hook 文件是否存在、是否可解析、是否调用门禁脚本。
- 仍需人工：每个使用者仍要在自己的 Codex 里 review/trust hook，这是官方机制要求，不能被插件替代。

### FP-007 - scorecard 高分可能被当成质量证明

失败模式：

如果 scorecard 只输出总分，AI 或使用者可能通过补空文档、改状态字段、忽略语义复核来获得高分。这样分数会退化成形式指标，掩盖业务错误、架构风险、验证不足或 AI eval 漏洞。

证据位置：

- 用户明确担心“打分的问题”，要求减少 AI 幻觉和虚假高分。
- `workbench/scorecard/RUBRIC.md` 原先只说明总分、阈值、硬阻塞和语义复核，没有独立校准文件。
- `scorecard.py` 原先没有 `confidence`、`calibration`、`componentFloorViolations`，`full` 档也没有强制校准和语义/架构复核。

工作台处理层：

- 模板层：新增 `workbench/scorecard/CALIBRATION.md`，记录锚定样例、人工抽查、误报、漏报和阈值调整。
- 脚本层：`scorecard.py` 输出可信度、校准状态、组件下限缺口和 profile 规则；`standard/full` 不允许用总分掩盖组件短板；`full` 要求校准和语义/架构复核。
- 审计层：检查 scorecard 脚本是否包含可信度/校准字段，检查 `SCORECARD.md` 和 `CALIBRATION.md` 是否有必要字段。
- 说明层：`RUBRIC.md`、`WORKBENCH.md` 和 references 明确分数不是业务正确性证明，低可信度高分不能通过。

自动化状态：

- 已自动化：生成、validate、audit、golden-test 和 package-check 都会覆盖 `CALIBRATION.md` 和新版 scorecard 字段。
- 仍需人工：锚定样例、人工抽查、误报/漏报归因和业务语义判断必须由项目负责人、审查人或独立 AI 复核补充。

### FP-006 - 没有严格打分导致流程完成度不可见

失败模式：

工作台有很多文档、功能包和质量门，但没有统一 scorecard 时，用户只能凭感觉判断当前项目是否准备好继续开发或交付。相反，如果只引入一个总分，AI 又可能拿高分绕过 open blocker、架构风险、语义复核和真实验收。

证据位置：

- `assets/project-adapter-template/` 曾没有 `workbench/scorecard/`。
- `quality_gate.py` 曾只检查项目画像、功能包状态和项目命令，没有独立证据成熟度分数。
- `audit` 曾不能发现质量门是否跳过 scorecard。

工作台处理层：

- 模板层：新增 `workbench/scorecard/RUBRIC.md` 和 `SCORECARD.md`。
- 脚本层：新增生成式 `scorecard.py`，并由 `quality_gate.py` 调用。
- 审计层：新增 `scorecard-not-enforced`、`invalid-scorecard-script`、`missing-semantic-score-fields` 等检查。
- 说明层：在 AGENTS、WORKBENCH、REVIEW、PRODUCT_BASELINE 和 references 说明分数边界。

自动化状态：

- 已自动化：新项目生成 scorecard；quality gate 调用 scorecard；golden-test 检查 scorecard 文件和质量门调用。
- 未完全自动化：业务目标、UX、架构合理性、安全/隐私和 AI eval 质量仍需要人工或独立 AI 语义复核。

### FP-005 - 项目工作台缺少产品/UX/架构前置层

失败模式：

工作台能约束 AI 写代码和审查代码，但新项目从 0 到 1 时，AI 可能在没有产品简报、PRD、UX、原型、架构、交付计划的情况下直接进入功能实现。结果是代码质量门通过了，但产品方向、交互路径、架构边界或后续迭代依据仍不清楚。

证据位置：

- `assets/project-adapter-template/` 曾只包含 `PROJECT_INTAKE.md`、`PRODUCT_BASELINE.md`、`DEVELOPMENT_FLOW.md`、`FEATURE_WORKFLOW.md` 和功能包模板。
- 功能包曾缺少 `DESIGN.md`，导致从 CLARIFY 到 PLAN 之间没有独立承接 UX/架构/API/AI 设计的阶段。
- 缺少 `AI_EFFECTIVENESS.md` 和 `ITERATION_LOG.md`，AI 修改后的效果和需求变化没有稳定归档位置。

工作台处理层：

- 模板层：新增 `workbench/product/`、`workbench/design/`、`workbench/architecture/`、`workbench/delivery/`、`workbench/feedback/AI_EFFECTIVENESS.md` 和 `ITERATION_LOG.md`。
- 功能包层：新增 `DESIGN.md`、`IMPLEMENTATION_NOTES.md`、`CHANGELOG.md`。
- 脚本层：`REQUIRED_ADAPTER_FILES`、`FEATURE_PACKAGE_FILES`、`validate`、`audit`、`quality_gate.py`、`golden-test` 都纳入新增文件和 DESIGN 阶段。

自动化状态：

- 已自动化：缺少新增文件会导致 validate/audit 失败；功能包进入 PLAN 前必须通过 DESIGN；package-check 确认个人 skill 和发布包 skill 同步。

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

### FP-004 - 把 scorecard 误当成质量裁判

失败模式：

AI 或用户看到高分后，误以为产品目标、架构合理性、UX、AI eval、安全和代码质量都已经通过。实际上脚本只能检查证据是否存在、状态是否一致、质量门是否接入，不能证明业务判断正确。

证据位置：

- `quality_gate.py` 曾在写入 `.workbench-validation/quality-gate-ok.json` 前调用 scorecard，scorecard 又检查该标记，导致当前运行和历史证据边界不清。
- 模板中曾使用“严格打分”“阈值通过”等措辞，容易让新用户把参考分当成硬质量证明。

工作台处理层：

- 脚本层：`scorecard.py` 输出 `decision`，并支持 `--called-from-quality-gate` 和 `--enforce-blockers`；质量门只因硬阻塞失败。
- 说明层：`RUBRIC.md`、`SCORECARD.md`、`WORKBENCH.md` 改为“证据审计”，明确参考分和组件下限只是风险信号。
- 复核层：产品、UX、架构、AI eval、安全和业务验收必须写入 `SCORECARD.md` 的人工或独立审查结论。

自动化状态：

- 已加入 `self-test`、`golden-test`、`doctor`、`package-check` 验证。后续如果真实项目中继续出现“高分低质量”，应把对应误报记录到 `CALIBRATION.md`，并优先改模板、质量门、CI、hook 或 review 检查。
