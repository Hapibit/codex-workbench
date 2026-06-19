# Workbench Improvement Log

本文件记录 `codex-workbench` 自身为什么升级、参考了什么证据、改了哪些文件、跑了哪些验证。它是长期维护证据，应该随插件源码一起版本化；不要把它放进 `.workbench-validation/`，后者只保存机器生成的临时报告。

## 使用规则

- 每次升级工作台规则、模板、脚本、门禁或发布结构，都新增一条记录。
- 记录要能回答：问题是什么、证据来源是什么、为什么这样改、改了哪些文件、验证结果是什么、还有什么后续动作。
- 如果某个决策会长期影响架构或发布边界，同时补一条 ADR。
- 如果同类失败重复出现，同时更新 `FAILURE_PATTERNS.md`。

## 记录模板

```text
### YYYY-MM-DD - 标题

问题：

证据来源：
- 用户反馈：
- 官方/外部资料：
- 本地失败证据：

决策：

变更文件：

验证结果：

后续动作：
```

## 记录

### 2026-06-20 - 稳定 Windows CI hook golden-test 路径诊断

问题：

重新推送 `2.0.3` 后，远端 `windows-package-check` 仍在 `plugin-hook-hard-gate` 用例失败，失败断言仍是 `hook golden: Stop block should report the nested repo path`。本地同一用例通过，但 GitHub Actions 日志没有打印 `repoRoot`、期望 nested repo 路径或 hook 原始输出，导致无法判断 CI 中实际返回的是空值、外层 repo，还是路径格式差异。

证据来源：

- GitHub Actions：`windows-package-check / Run workbench golden-test` 失败，`stopDecision=block`、`forgedStopDecision=block`，但 nested repo path 断言失败。
- 本地复现：`golden-test` 通过，Stop hook 返回 `repoRoot` 指向 nested repo；说明阻断语义正常，问题集中在 CI 断言诊断不足或路径规范化差异。

决策：

不改变 hook 阻断语义，不改 2.0.0 整体架构。只在 `golden-test` 中增加路径规范化 helper，并把 `stopRepoRoot`、`expectedNestedRepo`、规范化后的路径、`reason/stdout/stderr` 摘要写入用例结果。这样 CI 再失败时会直接暴露实际路径和值，而不是只给一句断言失败。

变更文件：

- `skills/codex-workbench/scripts/workbench.py`
- 本机个人 skill 镜像中的 `scripts/workbench.py`
- `docs/maintenance/IMPROVEMENT_LOG.md`

验证结果：

- `py -B skills/codex-workbench/scripts/workbench.py golden-test`：通过，`plugin-hook-hard-gate` 输出 `stopRepoRoot`、`expectedNestedRepo` 和规范化路径。
- `py -B skills/codex-workbench/scripts/workbench.py doctor --plugin <plugin-root> --personal-skill <personal-skill>`：通过，P0/P1/P2/P3 均为 0。
- `py -B skills/codex-workbench/scripts/workbench.py package-check --plugin <plugin-root> --personal-skill <personal-skill> --expected-version 2.0.3 --strict-release`：通过，P0/P1/P2/P3 均为 0。

后续动作：

- 提交并推送后观察 GitHub Actions。如果 CI 仍失败，直接依据新增的 `stopRepoRoot` 与 `stopStdoutExcerpt` 判断是 hook 返回路径错误还是断言条件仍不兼容。
- 后续 CI 复查发现 Windows runner 的 Python stdout 使用 `cp1252`，新增中文诊断字段触发 `UnicodeEncodeError`。已进一步修复 `write_json()`，标准输出统一按 UTF-8 bytes 写出；文件输出仍保持 UTF-8。
- 再次 CI 复查发现 `doctor --plugin` 在干净 runner 上误把缺少个人 skill 镜像判为 P1。已调整为：只有显式传入 `--personal-skill` 时才严格要求个人 skill 存在；CI 只做发布包 doctor，个人/插件同步仍由本机显式检查覆盖。

### 2026-06-20 - 发布 2.0.3 并补充 reader.md

问题：

用户要求开始发布，并明确要求同步文件版本、补写 `reader.md`。2.0.2 已经完成第一轮防跳过收紧，但发布包入口仍缺一个短读者指南，README、CI 和 package-check 命令也需要随 patch 发布版本统一。

证据来源：

- 用户反馈：要求“开始发布，对应的文件版本也要改，然后就是 reader.md 文件记得写”。
- 本地发布检查：发布包 manifest、README、CI workflow 和 package-check 命令仍引用 `2.0.2`。

决策：

作为向后兼容 patch 发布 `2.0.3`。不改变 2.0.0 架构基线，不修改生成项目的 `WORKBENCH_VERSION = "2.0.0"`；只同步插件发布版本、发布检查命令、维护日志和读者入口。`reader.md` 定位为快速入口，不复制完整 README。

变更文件：

- `.codex-plugin/plugin.json`
- `README.md`
- `reader.md`
- `packaging-manifest.json`
- `docs/CODEX_WORKBENCH_2_0_ARCHITECTURE.md`
- `docs/maintenance/IMPROVEMENT_LOG.md`
- 外层 `README.md`
- 外层 `.github/workflows/codex-workbench.yml`

验证结果：

- `py -B skills/codex-workbench/scripts/workbench.py self-test`：通过。
- `py -B skills/codex-workbench/scripts/workbench.py golden-test`：通过。
- `py -B skills/codex-workbench/scripts/workbench.py doctor --plugin <plugin-root> --personal-skill <personal-skill>`：通过，P0/P1/P2/P3 均为 0。
- `py -B skills/codex-workbench/scripts/workbench.py package-check --plugin <plugin-root> --personal-skill <personal-skill> --expected-version 2.0.3 --write-report`：通过，manifestVersion 为 `2.0.3`，visibleSkills 为 `codex-workbench`，P0/P1 为 0；首次运行发现未跟踪发布包文件 P2。
- `git add -- .github plugins/codex-workbench/.gitignore plugins/codex-workbench/reader.md plugins/codex-workbench/skills/codex-workbench/scripts/workbench_lib` 后，`package-check --expected-version 2.0.3 --strict-release`：通过，P0/P1/P2/P3 均为 0。

后续动作：

- 发布 tag 前确认 staged 发布包文件会随版本提交一起进入 Git；不要把 `.workbench-validation/` 机器报告提交进发布包。

### 2026-06-20 - 修复 Windows CI golden-test nested repo path 断言

问题：

`v2.0.3` 推送后，GitHub Actions 的 `windows-package-check` 在 `Run workbench golden-test` 阶段失败。失败用例是 `plugin-hook-hard-gate`，具体断言为 `hook golden: Stop block should report the nested repo path`。

证据来源：

- GitHub Actions 截图显示 `plugin-hook-hard-gate` 中 `stopDecision` 已经是 `block`，`forgedStopDecision` 也是 `block`，但 nested repo 路径断言失败。
- 本地代码复查发现 golden-test 只从中文 `reason` 文本里匹配 nested repo 的完整绝对路径。该断言对 Windows CI runner 的路径格式和 PowerShell 输出细节过于敏感。

决策：

保持 Stop hook 的阻断语义不变，给 Stop block payload 增加机器可读的 `repoRoot` 字段；golden-test 优先校验 `repoRoot` 等于 nested repo 路径，同时保留 `reason` 包含 `missing quality-gate-ok.json` 的要求。这样仍能证明 hook 报告了被阻断的项目，但不把测试绑定到中文 reason 的绝对路径格式。

变更文件：

- `hooks/workbench-hard-gate.ps1`
- `skills/codex-workbench/scripts/workbench.py`
- 本机个人 skill 镜像中的 `scripts/workbench.py`

验证结果：

- `py -B skills/codex-workbench/scripts/workbench.py golden-test`：通过，`plugin-hook-hard-gate` 通过。
- `py -B skills/codex-workbench/scripts/workbench.py doctor --plugin <plugin-root> --personal-skill <personal-skill>`：通过，P0/P1/P2/P3 均为 0。
- `py -B skills/codex-workbench/scripts/workbench.py package-check --plugin <plugin-root> --personal-skill <personal-skill> --expected-version 2.0.3 --strict-release`：通过，P0/P1/P2/P3 均为 0。

后续动作：

- 推送修复到 `main` 后观察 GitHub Actions；不移动已经发布的 `v2.0.3` tag，除非决定重新发布 patch tag。

### 2026-06-19 - 三角复查后修复 light 降级、accepted risk、traceability 和发布同步缺口

问题：

再次多 agent 复查发现 2.0.2 仍有几类可操作缺口：`light` 记录虽然已要求字段齐全，但仍可能用完整 JSON 把高风险路径降级；strict 未验证项需要更明确的 `accepted_risk` 语义和 `passed_with_risk` marker；strict traceability 不能只看矩阵里存在旧的 covered 行，必须绑定本功能 `IMPACT_ANALYSIS.md` 的预计影响 ID；runtime gate 与 quality gate 都写同一个 workflow state 文件，存在互相覆盖风险；doctor/package-check 在缺少个人 skill 镜像时不能自比自；hook 的只读命令豁免不能允许复合命令绕过危险命令检查。

证据来源：

- 多 agent 复查：
  - 文档入口 agent 指出生成 `AGENTS.md` / `WORKBENCH.md` 仍暴露过多内部脚本和阅读负担。
  - 质量门 agent 指出 `light CHANGE_LOG` 高风险路径降级、strict accepted risk 空值、traceability 未绑定影响 ID、runtime/quality state 覆盖风险。
  - 发布/hook agent 指出 personal/plugin sync 自比自、`hooks.json` matcher 未覆盖当前工具命名、只读前缀可掩盖复合危险命令、核心脚本扫描被跳过。
- 官方/外部资料：
  - OpenAI Codex hooks/customization：hook 和项目规则需要与确定性检查结合。
  - NASA requirements management / SWEHB：需求变更需要影响分析和 bidirectional traceability。
  - GitHub protected branches：required checks/reviews 才是远程合并硬门禁。
  - W3C WAI：自动化可访问性工具只能辅助，不能单独证明语义正确。

决策：

继续保留 2.0.0 整体架构，不大改目录层级；把发现的绕过路径收敛到脚本、hook 和 golden test。`light` 只用于低风险显式 scope 变更；strict 风险接受必须有用户确认、替代验证和 follow-up；quality gate 状态与 runtime gate 状态拆成不同文件；发布检查默认检查真实个人 skill 镜像，不再自比自；生成文档只做分层读取和边界措辞优化，不重写整体说明。

变更文件：

- `skills/codex-workbench/scripts/workbench.py`
- `hooks/workbench-hard-gate.ps1`
- `hooks/hooks.json`
- `packaging-manifest.json`
- `.gitignore`
- `README.md`
- `skills/codex-workbench/assets/project-adapter-template/AGENTS.md`
- `skills/codex-workbench/assets/project-adapter-template/WORKBENCH.md`
- `skills/codex-workbench/assets/project-adapter-template/FEATURE_WORKFLOW.md`
- `skills/codex-workbench/assets/project-adapter-template/PROJECT_STATE.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/delivery/CHANGE_LOG.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/review/independent-review-prompt.md`

验证结果：

- 待最终复检：`self-test`、`golden-test`、plugin doctor、personal-skill doctor、`package-check --expected-version 2.0.2 --write-report`。

后续动作：

- 继续把 stale marker hash 校验、branch protection 远程验证、UI/a11y/eval 证据充分性放入后续 parser / CI / review 改进；不把本地 parser 夸大成业务语义证明。

### 2026-06-19 - 多 agent 复检后收紧 2.0.2 防跳过门禁

问题：

多 agent 复检发现 2.0.2 的防跳过机制仍有边界缺口：hook 的 Stop 阶段容易只看当前 `cwd`，对 nested repo 或绝对路径写入归因不足；`quality-gate-ok.json` 新鲜度不能只看 mtime，必须校验 schema、status、`git_head`、`diff_hash` 和 `checks_run`；patch 新增内容可能写入 `approval_policy = 'never'`、`danger-full-access` 等绕过配置；README 对 `quality_gate.py` 的语义证明能力描述偏强。后续复检又发现 `VERIFY.md`、`REVIEW.md`、strict `TRACEABILITY.md` 仍偏状态字段检查，`package-check` 对 JSON escaped Windows 个人路径和本地同步残留有假阴性风险，manifest 长描述也需要同步 hook trust / CI 边界。

证据来源：

- 多 agent 审查：hook agent、quality-gate agent、docs agent 分别指出 touched repo 追踪、marker 语义校验、feature/light 记录硬要求、文档边界和 Windows 命令示例问题。
- 多 agent 二次复检：quality-gate agent 指出空 `VERIFY.md`、blocking `REVIEW.md` 和 strict `TRACEABILITY.md missing` 需要确定性 parser / golden test；docs/release agent 指出 package-check 对 JSON escaped personal path 和发布残留目录存在假阴性，manifest 文案边界比 README 更强。
- 官方资料：
  - OpenAI Codex customization: `https://developers.openai.com/codex/concepts/customization`
  - OpenAI Codex hooks: `https://developers.openai.com/codex/hooks`
  - OpenAI eval guidance: `https://developers.openai.com/blog/eval-skills`
  - NASA Software Engineering Handbook traceability: `https://swehb.nasa.gov/plugins/viewsource/viewpagesrc.action?pageId=215777306`
  - W3C WAI accessibility evaluation tools: `https://www.w3.org/WAI/test-evaluate/tools/selecting`
  - Git hooks: `https://git-scm.com/docs/githooks`
  - GitHub protected branches: `https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches`
- 本地复现：hook 模拟验证 `workbench/docs` patch 被 deny、nested repo dirty worktree 被 Stop block、`approval_policy = 'never'` patch 被 deny。

决策：

把“防跳过”从软规则继续下沉到工具层。hook 负责粗拦截和收尾阻断，quality gate 负责确定性证据状态，CI/branch protection 仍是远程最终门禁。新增 `quality-evidence-contract`，把空 `VERIFY.md`、blocking `REVIEW.md`、strict `TRACEABILITY.md missing` 从软提醒升级为生成型质量门检查。文档必须区分“已由脚本确定性检查证据形态和状态冲突”和“仍需 review/CI/人工判断的语义质量”。

变更文件：

- `hooks/workbench-hard-gate.ps1`
- `.codex-plugin/plugin.json`
- `skills/codex-workbench/scripts/workbench.py`
- `skills/codex-workbench/assets/project-adapter-template/workbench/delivery/CHANGE_LOG.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/runtime/WORKFLOW_STATE.schema.json`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feature-template/VERIFY.md`
- `README.md`
- `docs/CODEX_WORKBENCH_2_0_ARCHITECTURE.md`
- `skills/codex-workbench/SKILL.md`

验证结果：

- `py -B skills/codex-workbench/scripts/workbench.py self-test`：通过。
- `py -B skills/codex-workbench/scripts/workbench.py golden-test`：通过，包含 `quality-gate-contract`、`quality-evidence-contract` 和 `plugin-hook-hard-gate`；缺 feature/light 记录的受控 diff 失败，有效 light fenced JSON 通过；空 `VERIFY.md`、blocking `REVIEW.md`、strict `TRACEABILITY.md missing` 均失败；hook 对绕过配置、`workbench/docs` 和 nested repo 缺 marker 均阻断。
- `py -B skills/codex-workbench/scripts/workbench.py doctor --plugin <plugin-root>`：通过，P0/P1/P2/P3 均为 0。
- `py -B skills/codex-workbench/scripts/workbench.py package-check --plugin <plugin-root> --expected-version 2.0.2 --write-report`：通过，P0/P1/P2/P3 均为 0。
- Hook 手工模拟：`approval_policy = 'never'` patch 被 `PreToolUse` deny；`workbench/docs/test.md` patch 被 `PreToolUse` deny；nested repo 缺 `quality-gate-ok.json` 时 `Stop` block。该路径已沉淀为 `plugin-hook-hard-gate` golden case。
- Python 运行时仍输出 `Could not find platform independent libraries <prefix>`，但上述命令退出码均为 0。

后续动作：

- 继续补强 UI/a11y/eval 证据的确定性形态检查；无障碍和 AI eval 充分性仍不能由脚本单独证明，继续标记为需要 review/CI/人工判断。
- 如果后续出现“真实证据造假”或“review 漏掉 P0/P1”，不要把 parser 夸大为语义证明，应升级独立 review、CI artifact 校验或人工验收流程。

### 2026-06-18 - 修复 Windows hook 命令入口仍可能 code 1

问题：

`2.0.1` 已经把 hook 脚本异常改成 fail-closed JSON 输出，但用户在真实 Codex 会话中仍看到 `SessionStart hook (failed)`、`UserPromptSubmit hook (failed)` 和 `PreToolUse hook (failed)`，错误为 `hook exited with code 1`。

证据来源：

- 用户反馈：用户贴出三个 hook 事件仍然 `exited with code 1`。
- 本地失败证据：直接执行 `workbench-hard-gate.ps1` 正常返回 JSON，但 `hooks.json` 里的主 `command` 使用 `pwsh`；当前 Windows 环境没有可用 `pwsh`。如果 Codex 实际执行主 `command` 而不是 `commandWindows`，hook 会在进入脚本前失败。
- 官方资料：OpenAI Codex hooks 文档说明 Codex 会加载 `~/.codex/hooks.json` 和插件 `hooks/hooks.json`，插件 hook 可使用 `PLUGIN_ROOT` / `PLUGIN_DATA`，Windows 可用 `commandWindows` 覆盖命令；`PreToolUse` 应使用 `permissionDecision: "deny"` 表达阻断，而不是依赖脚本异常退出。

决策：

把全局 hook 和插件随包 hook 的 `command` / `commandWindows` 都改成 Windows 稳定入口：

```text
cmd /c powershell -NoProfile -ExecutionPolicy Bypass -File "%...%\workbench-hard-gate.ps1"
```

这样环境变量由 `cmd` 展开，脚本由 Windows 自带 `powershell.exe` 执行，不依赖 PowerShell 7 的 `pwsh`。安全语义不变：危险操作仍由 hook 的 `permissionDecision: deny` 或 block 输出处理，不能用异常退出当门禁。

变更文件：

- `hooks/hooks.json`
- `.codex-plugin/plugin.json`
- `README.md`
- `docs/maintenance/IMPROVEMENT_LOG.md`

验证结果：

- 全局 `hooks.json` JSON 解析通过。
- 插件 `hooks/hooks.json` JSON 解析通过。
- 真实命令入口 `cmd /c powershell ... -File "%USERPROFILE%\.codex\hooks\workbench-hard-gate.ps1"` 测试通过，`SessionStart` 和 `UserPromptSubmit` 均返回结构化 JSON 且退出码为 0。
- 插件缓存入口 `cmd /c powershell ... -File "%PLUGIN_ROOT%\hooks\workbench-hard-gate.ps1"` 测试通过。
- `package-check --expected-version 2.0.1` 在修改前通过，P0/P1/P2/P3 均为 0；版本提升后以 `2.0.2` 重新运行。

后续动作：

- 作为 patch 版本发布 `2.0.2`，让重新安装插件的用户拿到稳定 hook 命令入口。
- 如果后续再出现入口兼容问题，应把 hook 命令模拟测试提升为 `package-check` 的发布前检查。

### 2026-06-18 - 修复 hook 异常时显示 UserPromptSubmit hook failed

问题：

用户在使用 2.0.0 插件后看到 `UserPromptSubmit hook (failed) error: hook exited with code 1`。这类报错会让用户误以为是业务请求被拦截，实际含义是 hook 脚本自身异常退出。对于工作台门禁来说，脚本异常不应该裸露成 `hook failed`，而应该返回结构化上下文，让 Codex 继续显示明确原因。

证据来源：

- 用户反馈：用户明确询问 `UserPromptSubmit hook (failed)` 怎么解决。
- 本地失败证据：
  - 手动复现正常 `UserPromptSubmit` 输入时，全局 hook 和插件 hook 均返回 `exit=0`。
  - 构造异常环境变量后，旧逻辑可能因 `$ErrorActionPreference = "Stop"` 直接退出。

决策：

将 hook 顶层执行包进 `try/catch`。正常危险操作仍由 `block`、`deny` 或质量门逻辑处理；未预期异常则输出结构化 `hookSpecificOutput`，提示 hook 自身异常并按 fail-closed 处理，最后 `exit 0`，避免 Codex 显示不可读的 `hook failed`。

变更文件：

- `hooks/workbench-hard-gate.ps1`
- `.codex-plugin/plugin.json`
- `README.md`
- `docs/maintenance/IMPROVEMENT_LOG.md`

验证结果：

- 正常 `UserPromptSubmit`：返回结构化 JSON，`exit=0`。
- 插件缓存 `UserPromptSubmit`：返回结构化 JSON，`exit=0`。
- 构造异常 `SessionStart`：返回结构化 hook 异常上下文，`exit=0`。

后续动作：

- 作为 patch 版本发布 `2.0.1`，让重新安装插件的用户拿到 fail-closed hook。

### 2026-06-17 - 发布版本提升到 2.0.0，并按架构设计稿重构工作台为状态机

问题：

1.2.x 工作台仍偏向“文档集合 + 软流程提醒”。真实使用中已经暴露出 AI 可能跳过需求分析、后补功能包、复用旧质量门标记、把 scorecard 误当质量裁判、需求变化后多份文档同步负担过重等问题。用户要求以桌面架构设计稿为准，把 2.0.0 做成 AI coding 状态机、证据链和门禁体系。

证据来源：

- 用户反馈：
  - 用户多次指出“工作台规则会被跳过”“怎么保证 AI 写的是对的”“需求会反复修改”“工作台太重”“评分不能靠 AI 自评”。
  - 用户明确指定本机桌面的 `Codex Workbench 2.0.0 架构设计.md` 为本次升级依据。
- 官方/外部资料：
  - 架构设计稿已汇总 OpenAI Codex customization、skills/plugins、hooks、GitHub Spec Kit、NASA requirements management、Git hooks、GitHub protected branches/status checks 等资料依据。
  - 结论是：`AGENTS.md` 和 Markdown 只能作为说明层；硬要求必须落到 runtime gate、quality gate、CI、branch protection 或可验证证据。
- 本地失败证据：
  - 旧模板仍存在 `CLARIFY.md`、`CHECKLIST.md`、L1/L2/L3/L4 等旧流程概念。
  - 发布说明、reference 和 README 对 2.0.0 的状态机、追踪矩阵、影响分析、机器状态、marker 新鲜度描述不一致。
  - `package-check` 首轮发现 Python cache residue，已清理后重跑通过。

决策：

将发布版本升级为 `2.0.0`，这是 major 版本。原因是公开工作流、生成目录契约和质量门语义发生变化：从旧的文档/SDD 模板流程，升级为 `CLASSIFY -> BASELINE_CHECK -> CHANGE -> IMPACT -> ROUTE -> PLAN -> IMPLEMENT -> VERIFY -> REVIEW -> GATE -> LEARN -> DONE` 状态机。保留一个公开 skill：`codex-workbench`；第三方 skill 仍作为可选增强包。

核心设计落地：

- 新增 `PROJECT_STATE.md`。
- 新增 `workbench/delivery/CHANGE_LOG.md`、`TRACEABILITY.md`、`RELEASE_CHECKLIST.md`。
- 新增 `workbench/runtime/WORKFLOW_STATE.schema.json`、`BYPASS_LOG.md`。
- 新增 `CHANGE_REQUEST.md`、`IMPACT_ANALYSIS.md`、`FEATURE_STATUS.schema.json`，生成真实功能包时写入 `FEATURE_STATUS.json`。
- 移除新模板中的 `CLARIFY.md` 和 `CHECKLIST.md`。
- `quality_gate.py` 生成 `.workbench-validation/workflow-state.json` 和绑定 `git_head`、`diff_hash`、feature、commands、branch protection 状态的 `quality-gate-ok.json`。
- `scorecard` 保持证据审计定位，不作为硬放行裁判。
- `.workbench-validation/` 只作为机器报告区，长期维护证据放 `docs/maintenance/`。
- 将桌面架构设计稿同步为 `docs/CODEX_WORKBENCH_2_0_ARCHITECTURE.md` 并纳入 `packaging-manifest.json`。

变更文件：

- `.codex-plugin/plugin.json`
- `README.md`
- `packaging-manifest.json`
- `docs/CODEX_WORKBENCH_2_0_ARCHITECTURE.md`
- `docs/WORKFLOW_AND_SCORECARD.md`
- `docs/ITERATION_UPGRADE.md`
- `docs/maintenance/IMPROVEMENT_LOG.md`
- `skills/codex-workbench/SKILL.md`
- `skills/codex-workbench/scripts/workbench.py`
- `skills/codex-workbench/references/project-adapter-template.md`
- `skills/codex-workbench/references/project-intake-integration.md`
- `skills/codex-workbench/references/quality-gate-patterns.md`
- `skills/codex-workbench/references/upgrade-strategy.md`
- `skills/codex-workbench/references/workbench-maturity.md`
- `skills/codex-workbench/assets/project-adapter-template/**`

验证结果：

- `py -m py_compile skills/codex-workbench/scripts/workbench.py`：通过。
- `py skills/codex-workbench/scripts/workbench.py self-test`：通过。
- `py skills/codex-workbench/scripts/workbench.py golden-test`：通过。
- `py skills/codex-workbench/scripts/workbench.py package-check --plugin <plugin-root> --expected-version 2.0.0 --write-report`：通过，P0/P1/P2/P3 均为 0。
- 本机桌面的 `Codex Workbench 2.0.0 架构设计.md` 与 `docs/CODEX_WORKBENCH_2_0_ARCHITECTURE.md` SHA256 一致。

后续动作：

- 发布前如果继续改 hook、bypass golden tests、CI workflow 或 branch protection audit，需要追加新维护记录并重跑 package-check。
- 当前 2.0.0 已具备模板、脚本、README、架构文档和 package-check 的一致性；实际项目试水时应重点观察 `light` 记录、`FEATURE_STATUS.json`、旧 marker 失效和 `workbench_upgrade_assessment` 是否被正确执行。

### 2026-06-16 - 让 hook 区分明确授权的普通目录删除和工作台核心删除

问题：

用户明确要求删除 `E:\ai-edu-agent\docs`，但旧的 `PreToolUse` 门禁把所有 `Remove-Item -Recurse -Force` 一刀切拦住，连已经用 `-LiteralPath` 且路径已校验的安全删除也不放行；同时它还会把只读搜索命令里的危险字样误判为真实删除命令。

证据来源：

- 用户反馈：明确指出这个 hook 设计有问题，要求允许用户已确认且路径已校验的删除。
- 官方/外部资料：
  - OpenAI Codex hooks 文档说明 `PreToolUse` 是 guardrail，不是绝对边界；可按事件和命令形态做定向阻断。
  - 官方文档还说明 hooks 是命令级生命周期脚本，应该区分 `Bash`、`apply_patch`、`PermissionRequest` 和 `Stop` 的职责。
- 本地失败证据：
  - 旧 hook 用 `Remove-Item.*-Recurse.*-Force` 直接匹配，误伤所有递归删除。
  - 旧 hook 没有识别 `-LiteralPath`、绝对路径和保护路径。
  - 旧 hook 的 destructive 检查会误把搜索命令里的示例文本当作真实命令。

决策：

把门禁从“字符串里看到递归删除就拦”改成“只有当命令真的在删除高风险目标时才拦”。规则分成两层：一层仍阻止根目录、用户目录、`.codex`、仓库根、`.git`、`workbench` 核心目录和工作台规则文件被删；另一层允许用户明确写出的普通绝对路径、并且带 `-LiteralPath` 的递归删除，只要它不是保护路径。这样能保住工作台核心，同时不再误杀普通项目清理。

变更文件：

- `.codex/hooks/workbench-hard-gate.ps1`
- `hooks/workbench-hard-gate.ps1`
- `skills/codex-workbench/scripts/workbench.py`
- `docs/maintenance/IMPROVEMENT_LOG.md`

验证结果：

- 待运行模拟用例：`Remove-Item -LiteralPath 'E:\ai-edu-agent\docs' -Recurse -Force` 应该允许。
- 待运行模拟用例：`Remove-Item -LiteralPath 'E:\ai-edu-agent' -Recurse -Force` 应该拦截。
- 待运行模拟用例：`rg -n "Remove-Item.*-Recurse.*-Force"` 不应再被误判为危险删除。

后续动作：

- 运行 hook 模拟、PowerShell 语法检查、`doctor` 和 `package-check` 复检。
- 如果后续还出现“明确授权但被拦”的场景，再把允许条件收敛到更精确的绝对路径和参数组合。

### 2026-06-16 - 把工作台硬门禁同步到插件 hook 包

问题：

用户确认当前会话里已经加载了个人全局 hook，但发布插件包里还没有一套随包分发的 hook。这样会导致别人安装 `codex-workbench` 后，只能拿到 skill/template/script 层，而拿不到同等的本地拦截和阶段提醒；同时 README 也需要明确“插件带 hook，但每个使用者仍要自己在 Codex 里信任它们”。

证据来源：

- 用户反馈：直接问“有没有改hook？”并要求继续完善工作台门禁。
- 官方/外部资料：
  - OpenAI Codex hooks 文档说明 hooks 是生命周期脚本，只能作为 deterministic guardrails，不是完整安全边界。
  - 官方文档还说明插件可以携带 hooks/hooks.json，安装后仍需用户 review/trust。
  - OpenAI 关于插件的资料强调插件是分发单元，生命周期配置可以和 plugin 一起打包。
- 本地失败证据：
  - 个人全局 hook 已经有门禁，但发布包没有 hooks/ 目录。
  - package-check 之前没有校验插件 hook 文件存在与语法。
  - README 里没有明确说明“插件带 hook，但安装后仍需信任”。

决策：

把随包 hook 作为插件能力的一部分，但不把它伪装成自动可信的系统级门禁。插件包新增 `hooks/hooks.json` 和 `hooks/workbench-hard-gate.ps1`，并把发布检查升级为：插件 hook 必须存在、必须可解析、必须调用 `workbench-hard-gate.ps1`。README 说明安装后仍需用户自己的 Codex `/hooks` 信任流程。这样做能把“流程提醒”和“工具层门禁”一起带给使用者，但不会越过官方 hook trust 边界。

变更文件：

- `hooks/hooks.json`
- `hooks/workbench-hard-gate.ps1`
- `packaging-manifest.json`
- `README.md`
- `skills/codex-workbench/scripts/workbench.py`
- `docs/maintenance/IMPROVEMENT_LOG.md`

验证结果：

- PowerShell 语法检查通过。
- 模拟 `PreToolUse`：`workbench/docs/` 被拒绝。
- 模拟 `PreToolUse`：根目录 `docs/` 被允许。
- 模拟 `Stop`：工作台违规目录会触发阻断。
- 复检发现插件 hook 初版没有 UTF-8 BOM，在 Windows PowerShell 5.1 下中文字符串会被误读并导致解析失败；已改为 UTF-8 BOM 后重新验证通过。
- `package-check --expected-version 1.2.0 --write-report`：通过，P0/P1/P2/P3 均为 0。

后续动作：

- 运行 `package-check`，确认发布包把 hooks 当成正式分发内容。
- 如果后续发现 hook 逻辑和个人全局 hook 继续分叉，再决定是否把部分逻辑抽成共享脚本。

### 2026-06-16 - 发布版本提升到 1.2.0，并把流程偏离转成可检测门禁

问题：

用户在真实会话中发现 AI 会跳过工作台规则：没有先确认会话职责、没有按项目阶段读取状态、把业务项目推进和工作台配置混在一起、把非标准 `docs/` 层解释成工作台阶段，或者在没有搜索资料时声称参考了资料。这个问题不能继续只靠 README 或 AGENTS.md 的软提示解决；需要把能检测的偏离转成脚本、质量门和回归样例。

证据来源：

- 用户反馈：另一个会话明确承认“按工程直觉推进了任务，没有按工作台阶段门推进任务”；用户要求复查并优化，且要求复检时搜索相关资料。
- 官方/外部资料：
  - OpenAI Codex 官方资料把 `AGENTS.md`、skills、plugins、hooks、sandbox/approval、`/review` 和 `/diff` 分成不同职责层，说明持久规则、复用流程、工具生命周期和人工复查应该分层使用。
  - OpenAI Codex best practices 与 customization 资料强调：稳定规则放到仓库指令，重复流程放到 skill/plugin，确定性行为放到脚本或工具，不要把所有东西堆进长提示词。
  - Microsoft Spec-Driven Development 资料强调：先定义 intent、消除歧义、带约束规划、再用 AI 实现并按 spec 验证。
  - Addy Osmani 关于 AI agent spec 的资料强调：spec 应成为版本控制和 CI/CD 里的可执行工件，每个阶段验证后再进入下一步。
  - Martin Fowler 关于 humans and agents loops 的资料强调：人应该维护由规格、质量检查和工作流规则组成的 agent harness，而不是只在最内层逐行盯代码。
  - SonarQube quality gates、Google SRE postmortem 与 agent 改进循环资料共同指向：重复失败要变成明确检查、行动项和可验证完成标准，而不是只留在对话总结里。
- 本地失败证据：
  - 项目模板已有阶段说明，但 `validate/audit` 没有检查工作台顶层目录契约。
  - 生成的 `quality_gate.py` 没有拦截 AI 自己发明的 `workbench/docs/` 等非标准目录。
  - `REQUIRED_ADAPTER_TEXT_BY_FILE` 没有把 `执行门禁`、`目录契约`、`偏离复盘` 作为模板必含文本。
  - 没有 golden-test 复现“AI 发明工作台目录”和“根目录 docs 需要分类但不应直接失败”的差异。

决策：

将本次改动作为 minor 版本 `1.2.0`。原因是它新增了向后兼容的能力：目录契约、偏离复盘、质量门检查和回归样例；没有改变公开命令入口，也没有移除旧模板字段。

本次升级不追求“让 AI 永远不会跳过规则”，而是把可检测问题提前暴露：`workbench/` 只能使用声明过的顶层目录；`workbench/docs/` 这类 AI 发明层会导致 validate/audit/quality gate 失败；根目录 `docs/` 不直接失败，但 audit 会提示必须分类；模板必须包含执行门禁、目录契约和偏离复盘；重复偏离要进入 `FAILURE_LOG.md`、模板、质量门、hook、CI、review prompt 或 golden-test。

变更文件：

- `.codex-plugin/plugin.json`
- `README.md`
- `skills/codex-workbench/assets/project-adapter-template/AGENTS.md`
- `skills/codex-workbench/assets/project-adapter-template/WORKBENCH.md`
- `skills/codex-workbench/scripts/workbench.py`
- `docs/maintenance/IMPROVEMENT_LOG.md`
- `docs/maintenance/FAILURE_PATTERNS.md`

验证结果：

- `py -m py_compile skills/codex-workbench/scripts/workbench.py`：通过，只有环境警告 `Could not find platform independent libraries <prefix>`，但退出码为 0。
- `py .\skills\codex-workbench\scripts\workbench.py self-test`：通过。
- `py .\skills\codex-workbench\scripts\workbench.py golden-test`：通过，`workbench/docs/` 回归用例会失败，根目录 `docs/` 只产生分类警告。
- `py .\skills\codex-workbench\scripts\workbench.py package-check --plugin <plugin-root> --expected-version 1.2.0 --write-report`：通过，P0/P1/P2/P3 均为 0。

后续动作：

- 用真实项目试水时重点观察：AI 是否先执行阶段自检；是否会把根目录 `docs/` 误当工作台阶段；如果用户指出偏离，AI 是否先复盘并判断应升级模板、脚本、质量门、hook、CI、review prompt 还是回归样例。

### 2026-06-16 - 发布版本提升到 1.1.1，并优化工作台提示词路由

问题：

用户指出工作台提示词需要继续优化，并要求先搜索工作台相关提示词优化资料。实际检查发现，工作台已经有统一入口和阶段路由，但提示词仍有三个风险：阶段路由缺少明确的产物/停止条件；独立审查提示只读少量文件，容易只审代码不审需求和证据；本机同时存在发布插件、插件缓存和兼容 skill 副本，旧副本可能让其他会话读到旧规则。

证据来源：

- 用户反馈：另一个会话曾跳过工作台规则；用户要求工作台提示词既要参考资料，又要真正优化。
- 官方/外部资料：
  - OpenAI Codex best practices：重复工作流应该沉淀为 skill，不要依赖长提示词；skill 要有清晰触发描述、输入输出和脚本/资源。
  - OpenAI Codex customization：skill 采用 progressive disclosure，`SKILL.md` 只在触发后加载，详细资料放 `references/`，确定性能力放 `scripts/`，模板放 `assets/`。
  - OpenAI prompt engineering coding guidance：编码代理提示词应定义角色、结构化工具使用、测试验证、Markdown 标准、计划和进度跟踪。
  - Google / Anthropic / Microsoft 提示词资料：清晰说明目标、约束、成功标准、模糊时的处理方式，并通过测试/评估闭环迭代。
- 本地失败证据：
  - 个人兼容 skill 副本与发布源/插件缓存不一致，存在读取旧提示词的风险。
  - `workbench/review/independent-review-prompt.md` 没有要求按影响面读取 `PROJECT_INTAKE.md`、PRD、UX、架构、功能包和 scorecard 证据。
  - `.codex-plugin/plugin.json` 默认入口缺少创建功能包、验证工作台和预览升级等常用任务。

决策：

将本次改动作为 patch 版本 `1.1.1`。提示词采用“机器入口英文、项目规则中文、技术标识不翻译”的双语分工；在 `SKILL.md` 中加入阶段执行契约；在项目模板中加入阶段自检、产物/停止条件和验证要求；增强独立审查提示，让审查覆盖需求、产品、UX、架构、功能包、质量门、scorecard 和工作台升级判断；同步本机兼容 skill 副本，降低读取旧提示词的风险。

变更文件：

- `.codex-plugin/plugin.json`
- `README.md`
- `skills/codex-workbench/SKILL.md`
- `skills/codex-workbench/agents/openai.yaml`
- `skills/codex-workbench/assets/project-adapter-template/AGENTS.md`
- `skills/codex-workbench/assets/project-adapter-template/WORKBENCH.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/review/independent-review-prompt.md`
- `skills/codex-workbench/scripts/workbench.py`
- 个人工作台路由文件中的 `codex-workbench` 路径说明
- 个人兼容 skill 副本

验证结果：

- `py .\skills\codex-workbench\scripts\workbench.py self-test`：通过。
- `py .\skills\codex-workbench\scripts\workbench.py golden-test`：通过。
- `py .\skills\codex-workbench\scripts\workbench.py package-check --plugin <plugin-root> --expected-version 1.1.1 --write-report`：通过，P0/P1/P2/P3 均为 0。

后续动作：

- 发布 Git tag 时使用 `v1.1.1`。
- 用真实项目试水时重点观察：AI 是否先判断阶段、是否在需求不清时停下来、是否把 review/quality gate 缺口写入升级判断。

### 2026-06-15 - 增加证据保留策略，避免日志无限堆积

问题：

用户指出工作台日志如果一直堆积，会让文件越来越大、AI 读取成本变高、当前事实和历史证据混在一起；但如果简单删除，又会破坏工作台的证据链、复盘和发布审计。这个问题不能靠局部清理脚本解决，必须满足工作台“有证据、有门禁、有复盘、有迭代”的整体需求。

证据来源：

- 用户反馈：要求先搜索资料，再优化，并强调不能胡乱局部优化导致整体架构崩坏。
- 官方/外部资料：
  - Cloudflare log retention best practices：日志保留是数据保留策略的一部分，要平衡安全、调试、合规和成本。
  - Groundcover log retention policies：保留策略应自动执行，按诊断价值分层，低价值日志短保留，高价值事件可归档。
  - ADR 官方资料与 AWS ADR process：重大长期决策应该形成 decision log，记录 context、decision、consequences，而不是塞进一个无限增长日志。
  - Google SRE postmortem culture：复盘要有根因、影响、行动项和审查；没有审查和行动项的复盘不会形成学习。
- 本地失败证据：
  - `.workbench-validation/` 已明确是机器报告目录，但没有命令帮助用户把旧报告移出当前报告区。
  - `IMPROVEMENT_LOG.md`、`FAILURE_LOG.md` 等长期证据已有定位，但没有明确“过大时如何归档、不自动删除”的执行边界。

决策：

新增 `workbench.py retention` 命令，默认只预览保留计划。它把证据分为机器报告、功能级证据、重复失败摘要和长期决策四类。`--apply` 只把旧机器报告从 `.workbench-validation/` 移动到 `workbench/archive/validation/YYYY-MM/`，不删除文件，不重写人工维护日志，不移动功能包。人工日志过大时只给出拆分、归档或 ADR 建议，由维护者审查后处理。

变更文件：

- `skills/codex-workbench/SKILL.md`
- `skills/codex-workbench/scripts/workbench.py`
- `skills/codex-workbench/assets/project-adapter-template/WORKBENCH.md`
- `skills/codex-workbench/references/project-adapter-template.md`
- `skills/codex-workbench/references/quality-gate-patterns.md`
- `skills/codex-workbench/references/workbench-maturity.md`
- `docs/maintenance/IMPROVEMENT_LOG.md`

验证结果：

- 待运行 `py -m py_compile`、`self-test`、`golden-test`、`doctor` 和 `package-check --expected-version 1.1.0 --write-report`。

后续动作：

- 真实项目试水时观察 `retention` 报告是否能把当前机器报告、长期人工证据和功能包证据分清。
- 如果用户需要自动归档功能包，必须另行设计引用更新和 release note 检查，不能直接移动目录。

### 2026-06-15 - 让功能审查显式判断是否需要升级工作台

问题：

用户担心 Codex 在写项目代码时只完成当前功能，却不会留意“这次失败、返工、审查漏报或重复问题是否说明工作台本身要升级”。如果只把这件事写在最终回复或普通说明里，模型很容易跳过，后续项目也不会从失败中受益。

证据来源：

- 用户反馈：明确询问“怎么保证 Codex 会留意升级这个东西”，并多次强调软约束会被跳过，必须尽量落到工具层或流程证据里。
- 官方/外部资料：
  - OpenAI Codex 官方资料把 `AGENTS.md`、skill/plugin、MCP、hook 等分为不同职责层：持久规则、可复用流程、工具能力和工具调用/生命周期拦截应分层使用。
  - OpenAI Codex `AGENTS.md` 指南强调项目规则和验证命令应放入仓库可读文件，而不是只依赖对话记忆。
  - 质量门和 postmortem/改进闭环资料都指向同一个原则：重复失败必须变成可追踪证据和可验证行动项，不能只写总结。
- 本地失败证据：
  - 之前模板有 `FAILURE_LOG.md` 和迭代说明，但功能级 `REVIEW.md` 没有强制字段要求 AI 判断“是否升级工作台”。
  - `quality_gate.py` 不能发现已完成、失败或阻塞的功能包是否漏掉工作台升级判断。

决策：

在功能包 `REVIEW.md` 增加 `workbench_upgrade_assessment` 状态字段，并让 `VERIFY.md`、`REVIEW.md`、`FAILURE_LOG.md`、`WORKBENCH.md` 和 `AGENTS.md` 同步说明。脚本层增加受控枚举和质量门检查：当功能已完成、验证失败、审查失败或处于阻塞状态时，如果该字段仍是 `unassessed`，质量门和本地审计必须报错。这样不能保证 AI 永远正确判断，但能把“是否需要升级工作台”从一句软提示变成项目证据和可检查状态。

变更文件：

- `skills/codex-workbench/assets/project-adapter-template/AGENTS.md`
- `skills/codex-workbench/assets/project-adapter-template/WORKBENCH.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feature-template/VERIFY.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feature-template/REVIEW.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feedback/FAILURE_LOG.md`
- `skills/codex-workbench/scripts/workbench.py`
- `skills/codex-workbench/references/project-adapter-template.md`
- `skills/codex-workbench/references/quality-gate-patterns.md`
- `skills/codex-workbench/references/workbench-maturity.md`
- `docs/maintenance/IMPROVEMENT_LOG.md`

验证结果：

- `py -m py_compile skills/codex-workbench/scripts/workbench.py`：通过。
- `self-test`：通过，生成项目工作台文件，验证通过，审计无 P0/P1。
- 待运行 `golden-test`、`doctor` 和 `package-check --expected-version 1.1.0 --write-report`。

后续动作：

- 在真实项目试水时观察 AI 是否能正确选择 `not_required`、`failure_log_updated`、`template_update_needed`、`quality_gate_update_needed`、`review_rule_update_needed`、`ci_or_hook_needed` 或 `deferred_with_reason`。
- 如果 AI 只是机械填写 `not_required`，下一步把“有失败却写 not_required 必须写原因和证据”的规则升级为更严格的 quality gate 或 review blocker。

### 2026-06-15 - 重写 README 的论证结构并补强评分/迭代解释

问题：

用户指出当前 README 仍然“不行”，尤其是为什么要这样搭建、每个流程靠什么保证、评分机制为什么这样设计、权重为什么这样分配、迭代升级什么时候发生和怎么升级，都没有讲清楚。原 README 虽然列出了流程和权重，但更像功能清单，缺少“依据 -> 机制 -> 证据 -> 校准 -> 发布”的论证链。

证据来源：

- 用户反馈：明确要求重新搜索相关资料进行优化，并指出文档结构、评分依据和迭代升级说明不足。
- 官方/外部资料：
  - OpenAI Codex best practices：稳定规则放进 `AGENTS.md`，复杂任务先规划，写清构建/测试/验证命令，重复流程沉淀为 skill/plugin。
  - OpenAI Codex customization：构建顺序是 `AGENTS.md`、plugin/skill、MCP、subagents；不要把所有事情混在一个提示词里。
  - OpenAI Codex skills/plugins：skill 是可复用流程，plugin 是分发单元；本工作台应只暴露一个用户入口。
  - OpenAI agent improvement loop：改进要来自 trace、反馈、eval 和可验证变更。
  - OpenAI Codex iterative repair loop：review、repair、validation 分离，验证失败成为下一轮修复输入。
  - SonarQube quality gates：质量门是明确条件的 pass/fail，不能被总分替代。
  - Rubric 设计资料：评分要有明确 criteria、公开权重、校准样例、误报/漏报记录，减少主观性和偏差。
  - Google SRE postmortem：失败复盘要记录事实、影响、根因、行动项和可验证完成标准。
  - Diataxis 与 GitHub README：README 负责快速理解和开始使用，长解释应放入独立文档。
- 本地失败证据：
  - README 中“评分和证据审计”“迭代升级怎么做”过短，不能说明评分合理性和升级触发机制。
  - `WORKFLOW_AND_SCORECARD.md` 解释了权重，但没有明确把公开资料原则映射到工作台机制。
  - `ITERATION_UPGRADE.md` 有流程，但缺少“什么时候算需要迭代”“怎么证明升级有效”“发布前检查口径”。

决策：

重写根 README 和发布包 README，把入口文档改成使用者能读懂的设计说明：先讲问题和依据，再讲生成内容、流程强度、每个流程靠什么保证、评分机制边界、权重分配、迭代升级和安装使用。补强 `WORKFLOW_AND_SCORECARD.md` 中的资料到机制映射、scorecard 保留但不当裁判的理由、评分可信度责任边界。补强 `ITERATION_UPGRADE.md` 中的升级信号、升级强度、升级有效性证明和发布前检查口径。

变更文件：

- 根仓库 `README.md`
- `plugins/codex-workbench/README.md`
- `plugins/codex-workbench/docs/WORKFLOW_AND_SCORECARD.md`
- `plugins/codex-workbench/docs/ITERATION_UPGRADE.md`
- `plugins/codex-workbench/docs/maintenance/IMPROVEMENT_LOG.md`

验证结果：

- README、workflow、iteration 文档关键词复检通过，确认包含设计依据、评分机制、默认参考权重、迭代升级、升级有效性证明和主要外部参考链接。
- `doctor --plugin <plugin-root>`：通过，P0/P1/P2/P3 均为 0。
- `self-test`：通过，生成 51 个项目工作台文件，验证通过；审计无 P0/P1。
- `golden-test`：通过，覆盖 node-vite、maven-basic、fullstack-compose、old-workbench-upgrade 四个用例。
- `package-check --plugin <plugin-root> --expected-version 1.1.0 --write-report`：通过，manifestVersion 为 `1.1.0`，可见 skill 只有 `codex-workbench`，P0/P1/P2/P3 均为 0。
- Python 运行时仍输出 `Could not find platform independent libraries <prefix>`，但上述命令退出码均为 0。

后续动作：

- 用真实项目试水时，重点观察两件事：用户是否仍把 scorecard 当质量证明；AI 是否仍跳过项目发现、需求澄清、验证和复盘。
- 如果仍出现误解，把相关说明升级为模板字段、质量门检查或 review blocker，而不是继续加长 README。

### 2026-06-15 - 补强迭代升级机制说明

问题：

README 和 `WORKFLOW_AND_SCORECARD.md` 已经提到反馈闭环和“什么情况必须升级工作台”，但没有把迭代升级作为独立机制讲清楚。用户指出“为什么没有讲述迭代升级那块”，并要求重新搜索资料优化。缺口主要是：项目迭代、工作台机制升级、插件版本发布三件事没有分开；也缺少升级证据、升级位置、验证方式和版本号判断。

证据来源：

- 用户反馈：明确指出迭代升级部分不足，要求搜索相关资料后优化。
- 官方/外部资料：
  - OpenAI agent improvement loop：traces、human feedback、evals 和 Codex 修改形成改进飞轮。
  - OpenAI Codex iterative repair loop：review、repair、validation 分离，每轮保存结构化记录，剩余 delta 成为下一轮输入。
  - Google SRE postmortem：失败复盘要有事实、根因、影响、具体 action item、owner、优先级和可验证完成标准。
  - Google SRE incident management：复盘 action items 进入 backlog，按可靠性和业务工作平衡优先级。
  - PDCA：Plan、Do、Check、Act，用小范围实验验证改进，再标准化。
  - Semantic Versioning：用 major/minor/patch 表达变更影响。
- 本地失败证据：
  - README 只有一句“反馈闭环”和一个三层表，没有形成完整升级流程。
  - `WORKFLOW_AND_SCORECARD.md` 只有升级触发条件和升级顺序，没有项目迭代、插件机制升级和版本发布的分层。
  - 发布清单没有专门的迭代升级说明文档。

决策：

新增 `docs/ITERATION_UPGRADE.md` 作为专门文档，明确三层迭代：项目迭代、工作台机制升级、插件版本发布。README 增加入口摘要，`WORKFLOW_AND_SCORECARD.md` 增加正式闭环并链接到专门文档，`packaging-manifest.json` 将新文档纳入发布包。

变更文件：

- 根仓库 `README.md`
- `plugins/codex-workbench/README.md`
- `plugins/codex-workbench/docs/WORKFLOW_AND_SCORECARD.md`
- `plugins/codex-workbench/docs/ITERATION_UPGRADE.md`
- `plugins/codex-workbench/packaging-manifest.json`
- `plugins/codex-workbench/docs/maintenance/IMPROVEMENT_LOG.md`

验证结果：

- 待运行 `package-check --expected-version 1.1.0 --write-report`。

后续动作：

- 后续真实项目试水时，按 `ITERATION_UPGRADE.md` 记录至少一次从失败证据到模板/质量门/scorecard 改进的完整闭环。

### 2026-06-15 - 重构 README 和 scorecard 权重解释

问题：

README 同时承载安装、工作流、评分、维护、发布和长篇设计依据，结构混杂；scorecard 权重只列出分值，缺少“为什么这样分配、为什么不是平均分、为什么验证只占 10 但仍是硬门禁、什么时候调权重、如何校准”的完整说明。用户明确指出文档结构和评分解释都不够科学。

证据来源：

- 用户反馈：要求搜索资料后优化整个文档结构，并重点解释评分机制和参考权重的合理性。
- 官方/外部资料：
  - GitHub README 文档：README 应说明项目做什么、为什么有用、如何开始，长文档应放到其他文档。
  - Diataxis：文档应按用户需求拆分为 tutorial、how-to、reference、explanation。
  - OpenAI Codex best practices：复杂/模糊任务先规划，规则沉淀到 `AGENTS.md` 或 skill，重复流程再自动化。
  - OpenAI Codex skills：skill 使用渐进披露，插件是可分发单元。
  - OpenAI / Anthropic eval 指南：分数不能单独代表质量，成功标准要具体、可测量，并结合人工校准。
  - SonarQube quality gates：质量门用明确条件给出 pass/fail，不靠一个总分替代门禁。
  - Brown University rubric guidance：rubric 要公开标准和权重，并通过样例、复核和校准降低偏差。
- 本地失败证据：
  - 根 README 和发布包 README 重复且过长，混合了用户入口、设计解释和维护说明。
  - `RUBRIC.md` 有权重表，但没有完整解释权重分配依据和校准方式。

决策：

按 README 入口、工作流解释、用户工作台说明、维护证据四类拆分文档。README 保留快速开始、生成内容、评分边界和关键权重说明；新增 `docs/WORKFLOW_AND_SCORECARD.md` 承载完整流程、评分、权重、校准和迭代解释；同步更新项目模板 `RUBRIC.md`，让生成到用户项目里的评分规则也具备同样解释。

变更文件：

- 根仓库 `README.md`
- `plugins/codex-workbench/README.md`
- `plugins/codex-workbench/docs/WORKFLOW_AND_SCORECARD.md`
- `plugins/codex-workbench/packaging-manifest.json`
- `skills/codex-workbench/assets/project-adapter-template/workbench/scorecard/RUBRIC.md`
- `docs/maintenance/IMPROVEMENT_LOG.md`

验证结果：

- 待运行 `package-check --expected-version 1.1.0 --write-report`。

后续动作：

- 用真实项目试水，观察用户是否仍会把 scorecard 当质量证明。
- 如果出现高分低质或低分可用，记录到 `CALIBRATION.md` 并调整权重、硬阻塞或脚本。

### 2026-06-15 - 发布版本提升到 1.1.0

问题：

工作台内容已经完成 0 到 1 流程、功能工作包、证据审计和质量门相关升级，但插件 manifest 仍停留在 `1.0.0`。这会让“本地内容已经升级”和“对外发布版本”不一致，后续安装、缓存和发布说明也容易混淆。

决策：

将发布插件 manifest 升级为 `1.1.0`，并同步 README 中固定版本安装和发布前 `package-check` 命令。历史维护日志中已经发生过的 `1.0.0` 验证记录保持不改，脚本测试样例 Maven 项目的 `<version>1.0.0</version>` 也保持不改，因为它不是插件版本。

变更文件：

- `.codex-plugin/plugin.json`
- `README.md`
- 根仓库 `README.md`
- `.workbench-validation/package-check-report.json`

验证结果：

- `package-check --plugin <plugin-root> --expected-version 1.1.0 --write-report`：通过，P0/P1/P2/P3 均为 0。
- 报告写入 `.workbench-validation/package-check-report.json`，其中 `expectedVersion` 和 `manifestVersion` 均为 `1.1.0`。
- Python 运行时仍输出 `Could not find platform independent libraries <prefix>`，但命令退出码为 0。

后续动作：

- 发布 Git tag 时使用 `v1.1.0`。
- 推送远程前再次确认发布包只暴露 `codex-workbench` 一个可见 skill。

### 2026-06-15 - 防止 scorecard 虚假高分

问题：

用户真正担心的是打分机制本身：如果 AI 能靠补空文档、改状态字段或忽略语义复核拿到高分，scorecard 就会制造幻觉式质量证明。工作台需要保留评分带来的可见性，但不能让分数变成可刷的目标。

证据来源：

- 用户反馈：要求“看一下能不能优化，搜索相关资料”，重点担心打分合理性和 AI 幻觉。
- 官方/外部资料：
  - Anthropic Agent Evals：`https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents`
  - SonarSource Quality Gate：`https://www.sonarsource.com/resources/library/quality-gate`
  - OWASP Risk Rating Methodology：`https://owasp.org/www-community/OWASP_Risk_Rating_Methodology`
  - Goodhart's Law in software metrics：`https://lawsofsoftwareengineering.com/laws/goodharts-law`
  - Rubric reliability / inter-rater reliability references from rubric-design searches.
- 本地失败证据：
  - `scorecard.py` 原先只输出总分、等级、硬阻塞和 warning，没有可信度、校准状态或组件下限。
  - `RUBRIC.md` 和 `SCORECARD.md` 原先没有独立的锚定样例、人工抽查、误报/漏报和阈值调整记录位置。
  - `full` 档原先没有强制校准和语义/架构复核通过。

决策：

不把分数做复杂，也不让 AI 给业务质量打分。scorecard 继续只评估“证据成熟度和流程一致性”，但新增可信度、校准状态和组件下限。`full` 档必须完成校准和语义/架构复核；`standard/full` 不能用总分掩盖单项严重短板。误报、漏报和被刷分案例进入 `CALIBRATION.md`，再反向改模板、脚本、质量门、CI、hook 或审查规则。

变更文件：

- `skills/codex-workbench/scripts/workbench.py`
- `skills/codex-workbench/assets/project-adapter-template/workbench/scorecard/RUBRIC.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/scorecard/SCORECARD.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/scorecard/CALIBRATION.md`
- `skills/codex-workbench/assets/project-adapter-template/WORKBENCH.md`
- `skills/codex-workbench/references/project-adapter-template.md`
- `skills/codex-workbench/references/quality-gate-patterns.md`
- `skills/codex-workbench/references/workbench-maturity.md`
- `docs/maintenance/FAILURE_PATTERNS.md`

验证结果：

- 待运行 `self-test`、`golden-test`、`doctor` 和 `package-check`。

后续动作：

- 用真实项目试水时记录 scorecard 误报/漏报。
- 如果分数被用户或 AI 当成“质量证明”，继续降低总分权重表达，强化 confidence 和 calibration 的展示。

### 2026-06-15 - 引入严格 scorecard 打分机制

问题：

工作台已经有项目预处理、0 到 1 产品/UX/架构层、功能工作包、质量门和审查规则，但缺少统一评分机制。没有分数时，用户很难判断当前项目工作台是“可继续开发、只能原型、还是不能交付”；但如果只做一个总分，又容易让 AI 用高分绕过硬阻塞、业务语义审查和架构合理性判断。

证据来源：

- 用户反馈：要求“引入严格的打分机制”，同时要求搜索资料并评估设计架构是否合理。
- 官方/外部资料：
  - CMU SEI ATAM：`https://www.sei.cmu.edu/library/architecture-tradeoff-analysis-method-collection`
  - JetBrains/Qodana quality gates：`https://www.jetbrains.com/pages/static-code-analysis-guide/quality-gates-in-software-development`
  - Anthropic agent evals：`https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents`
  - OWASP Risk Rating Methodology：`https://owasp.org/www-community/OWASP_Risk_Rating_Methodology`
  - ProductPlan PRD：`https://www.productplan.com/glossary/product-requirements-document`
  - Jama PRD guide：`https://www.jamasoftware.com/requirements-management-guide/writing-requirements/how-to-write-an-effective-product-requirements-document`
  - OpenAI Codex customization：`https://developers.openai.com/codex/concepts/customization#next-step`
  - OpenAI Codex skills：`https://developers.openai.com/codex/skills`
  - OpenAI Codex plugin structure：`https://developers.openai.com/codex/plugins/build#plugin-structure`
- 本地失败证据：项目模板没有 `workbench/scorecard/`，质量门无法检查“证据成熟度分数”，审计也不能发现 scorecard 是否被质量门跳过。

决策：

新增 `workbench/scorecard/` 层，但不把它做成新的公开 skill，保持插件只有 `codex-workbench` 一个入口。scorecard 只做可脚本判断的证据成熟度和状态一致性检查；产品目标、UX、架构合理性、AI eval 和安全/隐私等语义判断必须写入 `SCORECARD.md`，不能由脚本假装判断。质量门必须调用 scorecard，审计发现没有调用时给 `P1 scorecard-not-enforced`。

变更文件：

- `skills/codex-workbench/SKILL.md`
- `skills/codex-workbench/scripts/workbench.py`
- `skills/codex-workbench/references/project-adapter-template.md`
- `skills/codex-workbench/references/quality-gate-patterns.md`
- `skills/codex-workbench/references/workbench-maturity.md`
- `skills/codex-workbench/assets/project-adapter-template/AGENTS.md`
- `skills/codex-workbench/assets/project-adapter-template/WORKBENCH.md`
- `skills/codex-workbench/assets/project-adapter-template/REVIEW.md`
- `skills/codex-workbench/assets/project-adapter-template/PRODUCT_BASELINE.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/scorecard/RUBRIC.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/scorecard/SCORECARD.md`
- `packaging-manifest.json`

验证结果：

- 个人 skill `self-test`：通过，生成 50 个项目工作台文件，验证通过，审计无 P0/P1。
- 个人 skill `golden-test`：通过，覆盖 node-vite、maven-basic、fullstack-compose、old-workbench-upgrade 四个用例，确认 scorecard 文件生成且质量门调用 scorecard。
- 发布包待完成最终 `self-test`、`golden-test`、`doctor` 和 `package-check` 复检。
- Python 运行时仍输出 `Could not find platform independent libraries <prefix>`，但个人 skill 验证命令退出码为 0。

后续动作：

- 在真实项目试水时观察 scorecard 阈值是否过严或过松。
- 如果用户把分数当成业务正确性证明，需要强化 `SCORECARD.md` 的语义/架构复核提示或审查规则。
- 如果本机同步残留目录仍存在，发布时必须按 `packaging-manifest.json` 排除 `assets/assets/**`、`references/references/**` 和 `scripts/scripts/**`。

### 2026-06-15 - 升级为可迭代 AI 产品开发工作台

问题：

项目工作台已有项目预处理、功能工作包、质量门和审查规则，但 0 到 1 项目缺少标准产品开发前置层。用户指出业务规划、架构设计、原型设计、AI 写完后的审查、修改后的效果评估都需要流程化；原先只补 `BUSINESS_PLAN.md`、`UX_FLOW.md` 这类文件名不够标准，也没有形成可迭代闭环。

证据来源：

- 用户反馈：指出 `PROJECT_INTAKE.md`、`BUSINESS_PLAN.md`、`PRD.md`、`ARCHITECTURE.md`、`UX_FLOW.md`、`PROTOTYPE.md` 不符合标准开发流程，并要求可迭代版本。
- 官方/外部资料：
  - GitHub Spec Kit quickstart: `https://github.github.com/spec-kit/quickstart.html`
  - GitHub Spec Kit SDD concepts: `https://github.github.com/spec-kit/concepts/sdd.html`
  - Kiro specs: `https://kiro.dev/docs/specs`
  - BMAD getting started: `https://github.com/bmad-code-org/BMAD-METHOD/blob/main/docs/tutorials/getting-started.md`
  - Martin Fowler on SDD tools: `https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html`
- 本地失败证据：`assets/project-adapter-template/` 只生成根级 PROJECT_INTAKE、PRODUCT_BASELINE、FEATURE_WORKFLOW 和功能包模板；没有 `workbench/product/`、`workbench/design/`、`workbench/architecture/`、`workbench/delivery/`；功能包也没有 `DESIGN.md`、`IMPLEMENTATION_NOTES.md`、`CHANGELOG.md`。

决策：

保留一个公开 skill 入口，不引入强制第三方工具。把项目工作台升级为标准 0 到 1 流程：项目发现 -> 产品简报 -> PRD -> UX/原型 -> 架构设计 -> 交付计划 -> 功能包开发 -> 验证审查 -> 迭代复盘。根级文件保持兼容，新增标准目录作为项目内长期事实源。功能包流程从 SPEC -> CLARIFY -> PLAN 改为 SPEC -> CLARIFY -> DESIGN -> PLAN，并记录 AI 实现、修改后效果和需求变化。

变更文件：

- `skills/codex-workbench/SKILL.md`
- `skills/codex-workbench/scripts/workbench.py`
- `skills/codex-workbench/references/project-adapter-template.md`
- `skills/codex-workbench/assets/project-adapter-template/AGENTS.md`
- `skills/codex-workbench/assets/project-adapter-template/WORKBENCH.md`
- `skills/codex-workbench/assets/project-adapter-template/PROJECT_INTAKE.md`
- `skills/codex-workbench/assets/project-adapter-template/PRODUCT_BASELINE.md`
- `skills/codex-workbench/assets/project-adapter-template/FEATURE_WORKFLOW.md`
- `skills/codex-workbench/assets/project-adapter-template/REVIEW.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/product/*`
- `skills/codex-workbench/assets/project-adapter-template/workbench/design/*`
- `skills/codex-workbench/assets/project-adapter-template/workbench/architecture/*`
- `skills/codex-workbench/assets/project-adapter-template/workbench/delivery/*`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feature-template/DESIGN.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feature-template/IMPLEMENTATION_NOTES.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feature-template/CHANGELOG.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feedback/ITERATION_LOG.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feedback/AI_EFFECTIVENESS.md`

验证结果：

- 个人 skill `self-test`：通过，生成 45 个项目工作台文件，验证通过，审计无 P0/P1。
- 个人 skill `golden-test`：通过，覆盖 node-vite、maven-basic、fullstack-compose、old-workbench-upgrade 四个用例。
- 发布包 skill `self-test`：通过，生成 45 个项目工作台文件，验证通过，审计无 P0/P1。
- 发布包 skill `golden-test`：通过，覆盖四个用例，所有用例 passed。
- `doctor --plugin <plugin-root>`：通过，P0/P1/P2/P3 均为 0，确认个人 skill 与插件 skill 同步。
- `package-check --plugin <plugin-root> --expected-version 1.0.0 --write-report`：通过，P0/P1/P2/P3 均为 0，报告写入 `.workbench-validation/package-check-report.json`。
- Python 运行时仍输出 `Could not find platform independent libraries <prefix>`，但上述命令退出码均为 0。

后续动作：

- 用一个真实 0 到 1 项目试水，观察新增产品/UX/架构层是否过重。
- 如果真实使用中发现模板太重，优先调整 L1/L2/L3/L4 分级和生成说明，不删除质量门状态字段。
- 如果 AI 修改后仍没有记录效果，把 `AI_EFFECTIVENESS.md` 的关键字段提升为 audit 或质量门检查。

### 2026-06-15 - 把用户工作台模板纳入发布包

问题：

发布包已经能生成项目工作台，但没有把“接收者自己的用户工作台”作为可安装模板交付。结果是别人安装 `codex-workbench` 后，只能得到项目级规则、质量门和功能工作包；如果他没有自己的全局 `AGENTS.md`、工具路由、搜索/澄清习惯和审查规则，项目工作台仍然能用，但启动层约束不足，容易误以为插件会自动修改用户全局配置。

证据来源：

- 用户反馈：指出“发布整个你没有修改用户工作台”，要求本地发布包先修正。
- 本地失败证据：`README.md` 只解释用户工作台和项目工作台的关系，没有提供可复制模板或脚本入口；`packaging-manifest.json` 也未把用户工作台说明纳入发布文件。

决策：

不在插件安装时自动覆盖接收者的 `~/.codex/`，因为用户工作台会影响所有项目，并且可能涉及个人账号、MCP、hook 信任和本机路径。改为发布一套通用用户工作台模板，并提供 `user-workbench` 命令：默认只预览，只有用户明确加 `--apply` 才写入，已有文件默认跳过，`--force` 才备份后覆盖。

变更文件：

- `README.md`
- `docs/USER_WORKBENCH.md`
- `packaging-manifest.json`
- `skills/codex-workbench/SKILL.md`
- `skills/codex-workbench/scripts/workbench.py`
- `skills/codex-workbench/assets/user-workbench-template/AGENTS.md`
- `skills/codex-workbench/assets/user-workbench-template/WORKBENCH_ROUTING.md`
- `skills/codex-workbench/assets/user-workbench-template/CODE_QUALITY.md`
- `skills/codex-workbench/assets/user-workbench-template/CODE_REVIEW.md`
- `skills/codex-workbench/assets/user-workbench-template/RTK.md`

验证结果：

- `user-workbench` 预览：通过，默认返回 `would-write`，不写入目标目录。
- `user-workbench --apply` 写入临时目录：通过，生成 5 个用户工作台文件。
- 脚本语法检查：通过。
- 发布包扫描：未发现作者个人绝对路径、邮箱或真实密钥；只出现安全说明中的 `token`、`cookie` 等普通词。

后续动作：

- 重新运行 `package-check --expected-version 1.0.0 --write-report`，确认删除 Python cache 后发布门禁通过。
- 如果用户后续要求真正发布到 GitHub，再处理本地/远端分支差异并由用户确认后推送。

### 2026-06-14 - 强化功能工作包的可执行证据

问题：

工作台架构已经具备项目画像、产品下限、功能工作包、质量门和维护证据，但部分模板内容仍偏流程说明。真实开发时，AI 可能只按清单往下走，却没有把需求变更、验收证据、计划偏离、复测结果和审查结论写成可复查材料。

证据来源：

- 用户反馈：要求这次优化注重内容，不再只调整架构，并要求升级后经过复查。
- 官方/外部资料：
  - OpenAI Codex Best Practices: `https://developers.openai.com/codex/learn/best-practices`
  - OpenAI Codex Skills: `https://developers.openai.com/codex/skills`
  - OpenAI Codex ExecPlans: `https://developers.openai.com/cookbook/articles/codex_exec_plans`
  - Addy Osmani, How to write a good spec for AI agents: `https://addyosmani.com/blog/good-spec`
  - Jama Software, Spec-Driven Development for AI-Powered Engineering: `https://www.jamasoftware.com/blog/what-is-spec-driven-development-sdd-for-ai-powered-engineering`
  - AI agent code quality gates article: `https://dev.to/teppana88/how-i-validate-quality-when-ai-agents-write-my-code-481c`
- 本地失败证据：模板已有 SDD 文件和状态字段，但 SPEC 缺少事实源与变更同步要求，PLAN 缺少备选方案、回滚和未知项，TASKS 缺少输入输出证据位置，VERIFY/REVIEW 对验收证据和需求符合性的约束不够具体。

决策：

不改变工作台架构，不新增公开 skill，也不强制所有任务走完整 SDD。只强化模板内容，让项目画像和 SPEC 成为事实源，让 PLAN/TASKS/VERIFY/REVIEW 能回答“依据是什么、怎么证明、出了错怎么复测、重复失败沉淀到哪里”。

变更文件：

- `skills/codex-workbench/assets/PROJECT_INTAKE.template.md`
- `skills/codex-workbench/assets/project-adapter-template/PROJECT_INTAKE.md`
- `skills/codex-workbench/assets/project-adapter-template/PRODUCT_BASELINE.md`
- `skills/codex-workbench/assets/project-adapter-template/FEATURE_WORKFLOW.md`
- `skills/codex-workbench/assets/project-adapter-template/WORKBENCH.md`
- `skills/codex-workbench/assets/project-adapter-template/REVIEW.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feature-template/SPEC.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feature-template/CLARIFY.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feature-template/PLAN.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feature-template/TASKS.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feature-template/DECISIONS.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feature-template/CHECKLIST.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feature-template/VERIFY.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feature-template/REVIEW.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/feedback/FAILURE_LOG.md`

验证结果：

- `self-test`：通过，生成 26 个项目工作台文件，验证通过，审计无 P0/P1。
- `golden-test`：通过，覆盖 node-vite、maven-basic、fullstack-compose、old-workbench-upgrade 四个用例，所有用例 passed。
- `doctor --plugin <plugin-root>`：通过，P0/P1/P2/P3 均为 0，确认个人 skill 与插件 skill 同步。
- `package-check --plugin <plugin-root> --expected-version 1.0.0 --write-report`：通过，P0/P1/P2/P3 均为 0，报告写入 `.workbench-validation/package-check-report.json`。
- 复查结论：模板未新增个人路径、密钥或私有 URL；新增内容集中在证据、变更同步、验证和审查，不改变工作台架构。Markdown 规则仍按“指导层”处理，未声称替代脚本、CI、hook 或质量门。
- Python 运行时仍输出 `Could not find platform independent libraries <prefix>`，但上述命令退出码均为 0。

后续动作：

- 如果复查发现模板太重，优先删减说明文本，不动质量门状态字段。
- 如果真实项目中再次出现“验证只写命令、没有验收证据”，考虑把 `VERIFY.md` 的证据表变成质量门检查。

### 2026-06-14 - 分离机器报告和工作台维护证据

问题：

之前只在发布检查后生成 `.workbench-validation/package-check-report.json`，但没有正式目录记录“工作台自身为什么升级、参考了什么资料、失败模式如何沉淀”。这会导致升级依据只停留在对话里，后续发布、复查或交给别人维护时无法追溯。

证据来源：

- 用户反馈：要求明确“工作台自身升级的证据放在哪里”，并质疑 `.workbench-validation/improvement-log.md`、`failure-patterns.md` 是否适配真实工作流。
- 官方/外部资料：
  - OpenAI Codex Skills: `https://developers.openai.com/codex/skills`
  - OpenAI Codex Customization: `https://developers.openai.com/codex/concepts/customization`
  - OpenAI Codex Build plugins: `https://developers.openai.com/codex/plugins/build`
  - Martin Fowler ADR: `https://martinfowler.com/bliki/ArchitectureDecisionRecord.html`
  - Google SRE Postmortem Practices: `https://sre.google/workbook/postmortem-culture/`
  - Datadog Incident Postmortem Practices: `https://www.datadoghq.com/blog/incident-postmortem-process-best-practices`
- 本地失败证据：插件根目录只有 `.workbench-validation/package-check-report.json`，缺少长期维护证据文件；`package-check` 也没有把维护证据列入发布前检查。

决策：

`.workbench-validation/` 只保存机器生成报告，例如 `package-check-report.json`。长期维护证据放在插件根目录 `docs/maintenance/`，包括 `IMPROVEMENT_LOG.md`、`FAILURE_PATTERNS.md` 和 `adr/`。发布检查必须验证这些文件存在，避免“证据驱动升级”再次退化成口头规则。

变更文件：

- `docs/maintenance/IMPROVEMENT_LOG.md`
- `docs/maintenance/FAILURE_PATTERNS.md`
- `docs/maintenance/adr/README.md`
- `packaging-manifest.json`
- `skills/codex-workbench/scripts/workbench.py`
- `skills/codex-workbench/references/workbench-maturity.md`
- `README.md`

验证结果：

- `doctor --plugin <plugin-root>`：通过，P0/P1/P2/P3 均为 0。
- `package-check --plugin <plugin-root> --expected-version 1.0.0 --write-report`：通过，报告写入 `.workbench-validation/package-check-report.json`，并列出 `maintenanceEvidence`。
- `self-test`：通过，生成 26 个项目工作台文件，验证通过，审计无 P0/P1。
- `golden-test`：通过，覆盖 node-vite、maven-basic、fullstack-compose、old-workbench-upgrade 四个用例。
- Python 运行时仍输出 `Could not find platform independent libraries <prefix>`，但上述命令退出码均为 0。

后续动作：

- 如果后续发现维护日志只写不改门禁，应把对应失败模式提升为 `package-check` 或 `doctor` 检查。
- 发布前复查 `docs/maintenance/**` 不包含个人路径、token、cookie、登录态或私有配置。

### 2026-06-15 - 将 scorecard 从质量裁判重构为证据审计

问题：

工作台曾把 `scorecard.py` 表述为“严格打分”入口，并让质量门在写入 `.workbench-validation/quality-gate-ok.json` 前调用 scorecard。这样有两个风险：第一，用户或 AI 容易把高分误解为代码、产品、架构或 AI eval 已经真实合格；第二，scorecard 又检查质量门成功标记时，会和当前质量门运行形成循环依赖，第一次运行容易被“缺少历史标记”误导。

证据来源：

- 用户反馈：质疑“脚本打分怎么保证合理、怎么减少 AI 幻觉、整体流程是否有问题”。
- 官方/外部资料：
  - OpenAI Codex Best Practices: `https://developers.openai.com/codex/learn/best-practices`
  - OpenAI Codex Skills: `https://developers.openai.com/codex/skills`
  - GitHub Spec Kit: `https://github.github.com/spec-kit/`
  - Kiro Specs Best Practices: `https://kiro.dev/docs/specs/best-practices/`
  - Anthropic Agent Evals: `https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents`
- 本地证据：`quality_gate.py` 先调用 scorecard，scorecard 又检查 `.workbench-validation/quality-gate-ok.json`；模板文档存在“严格打分”“阈值通过”等容易被误读为质量裁判的表述。

决策：

保留 scorecard，但降权为证据审计报告。质量判断改为分层：确定性检查、质量门、CI、review 和人工/独立复核是门禁；scorecard 只输出 `decision`、参考分、可信度、硬阻塞、校准状态和证据缺口。`BLOCKED` 才阻塞质量门，`PASS_WITH_RISK` 必须人工确认风险，参考分和组件下限只作为风险信号。

变更文件：

- `skills/codex-workbench/scripts/workbench.py`
- `skills/codex-workbench/assets/project-adapter-template/AGENTS.md`
- `skills/codex-workbench/assets/project-adapter-template/WORKBENCH.md`
- `skills/codex-workbench/assets/project-adapter-template/PRODUCT_BASELINE.md`
- `skills/codex-workbench/assets/project-adapter-template/REVIEW.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/scorecard/RUBRIC.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/scorecard/SCORECARD.md`
- `skills/codex-workbench/assets/project-adapter-template/workbench/scorecard/CALIBRATION.md`
- `skills/codex-workbench/references/quality-gate-patterns.md`
- `skills/codex-workbench/references/project-adapter-template.md`
- `skills/codex-workbench/references/workbench-maturity.md`

验证结果：

- `self-test`：通过，生成 51 个项目工作台文件，验证通过，审计无 P0/P1。
- `golden-test`：通过，覆盖 node-vite、maven-basic、fullstack-compose、old-workbench-upgrade 四个用例。
- `doctor --plugin <plugin-root>`：通过，P0/P1/P2/P3 均为 0。
- `package-check --plugin <plugin-root> --expected-version 1.0.0 --write-report`：通过，P0/P1/P2/P3 均为 0。
- `py -m py_compile skills/codex-workbench/scripts/workbench.py`：通过。
- Python 运行时仍输出 `Could not find platform independent libraries <prefix>`，但上述命令退出码均为 0。

后续动作：

- 在真实项目试水时观察 `PASS_WITH_RISK` 是否被用户或 AI 误当成通过；如果出现，提升为质量门或 review 检查。
- 如果 scorecard 仍出现高分低质量，优先调整模板、参考线、硬阻塞、质量门或审查清单，不手工改报告结果。
