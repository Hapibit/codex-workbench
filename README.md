# Codex Workbench 使用说明

这个插件的目标是降低学习成本：发布包只应该暴露 `codex-workbench` 一个 skill。新用户安装后，只需要对 Codex 说一句：

```text
Use Codex Workbench to set up this project's AI workbench.
```

## 用户需要知道什么

只需要知道五个词：

- 项目预处理：先把项目需求、用户、范围、数据、权限和验收标准弄清楚。
- 项目工作台：在项目里生成 `AGENTS.md`、`WORKBENCH.md`、`REVIEW.md` 和 `workbench/`。
- 功能工作包：每个重要功能单独走 SPEC、PLAN、TASKS、VERIFY、REVIEW。
- 质量门：用脚本、测试、lint、类型检查、CI 或审查拦住低质量输出。
- 复盘改进：重复出错的地方沉淀成规则、脚本或质量门。

## 增强 skill 怎么办

增强 skill 可以整合进工作台，但不应该都塞成必装项。`codex-workbench` 负责统一入口和路由，增强 skill 作为按需能力包：

- 做 UI 或设计稿时，再推荐 Figma/UI 相关 skill。
- 画 ER 图、流程图、架构图时，再推荐 diagram/draw.io 相关 skill。
- 写测试、Jenkins、CI 时，再推荐测试和 CI 相关 skill。
- 写 README、Word、论文、PPT 时，再推荐文档相关 skill。
- 做安全、AI eval、RAG、智能体治理时，再推荐对应专业 skill。

也就是说，基础使用路径仍然是：

```text
装一个插件 -> 看到一个入口 -> 叫 Codex Workbench 建工作台 -> 按项目工作台做需求、开发、验证、审查
```

专业 skill 由工作台按任务推荐，不是入门门槛。可以用内置检测脚本查看当前机器有哪些增强包可用：

```bash
python skills/codex-workbench/scripts/check_enhancements.py --query "我要做 UI/Figma 和测试"
```

## 接收者仍然要自己配置什么

这个插件不会也不应该替别人带走你的私人配置。接收者仍然要自己配置：

- Codex 安装和登录；
- 自己的 MCP、GitHub、Figma、Jenkins、OpenAI、Google 等账号和凭证；
- 项目需要的 Node、Java、Maven、Docker、Python 等本地工具链；
- hook 信任、权限提示和 API key；
- 项目自己的真实测试、lint、类型检查、CI 命令。

## 最小交付标准

发给别人前，至少要保证：

- 插件内 skill 通过 `quick_validate.py`；
- 插件通过 `validate_plugin.py`；
- 工作台生成器的 `self-test` 和 `golden-test` 通过；
- `doctor` 和 `package-check --expected-version <version> --write-report` 通过；
- 生成的项目工作台不包含个人路径、token、cookie、登录态或私有密钥；
- 文档明确说明：可选 skill 是增强，不是必装。
- `skills/` 目录只暴露 `codex-workbench` 一个入口；内部脚本、模板和参考资料放在这个 skill 自己的 `scripts/`、`assets/`、`references/` 里。
- 增强 skill 清单由 `skills/codex-workbench/assets/enhancements.json` 管理，说明由 `skills/codex-workbench/references/enhancement-packs.md` 管理。

## 工作台自身升级证据放哪里

工作台自身升级证据分两类，不要混放：

- `docs/maintenance/`：长期维护证据，随插件源码和发布包一起走。这里记录为什么升级、参考了什么资料、失败模式如何沉淀、哪些决策需要 ADR。
- `.workbench-validation/`：机器生成报告，只保留本机验证结果，例如 `package-check-report.json`。这个目录会被打包清单排除，不作为长期人工维护文档。

目前正式维护证据文件是：

```text
docs/maintenance/
├── IMPROVEMENT_LOG.md
├── FAILURE_PATTERNS.md
└── adr/
    └── README.md
```

发布前 `package-check` 会检查这些文件是否存在。这样升级工作台时不是凭感觉改，而是按“用户反馈/外部资料/本地失败证据 -> 规则、模板、脚本或门禁 -> 验证报告”的闭环处理。

## 发布包注意

正式发布或打包给别人时，发布目录不应包含内部备份、旧 helper skill、Python 缓存或本机临时文件。只发布：

```text
codex-workbench/
├── .codex-plugin/plugin.json
├── README.md
├── docs/
│   └── maintenance/
│       ├── IMPROVEMENT_LOG.md
│       ├── FAILURE_PATTERNS.md
│       └── adr/
│           └── README.md
└── skills/
    └── codex-workbench/
        ├── SKILL.md
        ├── agents/
        ├── scripts/
        ├── assets/
        └── references/
```
