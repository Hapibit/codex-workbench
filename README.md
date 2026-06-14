# Codex Workbench

Codex Workbench 是一个给 Codex 使用的 AI 开发工作台插件。它解决的不是“再写一段提示词”，而是把 AI 开发中容易丢失的规则、流程、质量门和验收证据放进文件里，让一个项目可以长期、可复查地被 AI 协助开发。

安装后，你只需要记住一个入口：

```text
Use Codex Workbench to set up this project's AI workbench.
```

它会在当前项目里生成一套项目工作台。你不需要先记住一堆 skill 名称，也不需要一开始就安装所有增强工具。

## 它适合谁

- 想用 Codex 开发真实项目，但担心 AI 跳过需求分析、测试、审查的人。
- 技术能力还在成长，希望有一套最低开发质量线的人。
- 有多个项目，希望每个项目都有自己的规则、命令、验收证据和复盘机制的人。
- 想把工作台分享给别人，但又不想把自己的账号、路径、MCP、hook 信任一起发出去的人。

## 它解决什么

AI 写代码常见问题：

- 需求不清楚时，AI 直接脑补。
- 项目规则只存在聊天记录里，下一轮又忘。
- 功能写完了，却没有可复查的验收证据。
- Review 只看代码风格，没有检查权限、数据、测试和回滚。
- 同类错误反复出现，每次都重新解释。

Codex Workbench 的做法是把这些要求沉淀成：

- 项目规则文件。
- 项目画像。
- 功能工作包。
- 质量门脚本。
- 独立审查提示。
- 失败复盘记录。

## 两层工作台

这个插件包含两层能力。

| 层级 | 放在哪里 | 负责什么 | 是否默认写入 |
| --- | --- | --- | --- |
| 用户工作台 | 使用者自己的 `~/.codex/` | 默认语言、需求澄清、搜索习惯、skill 路由、全局安全边界 | 否，需要用户明确安装 |
| 项目工作台 | 具体项目仓库 | 项目事实、技术栈、命令、业务边界、质量门、功能证据 | 是，用户要求建立项目工作台时写入 |

项目工作台可以单独使用；但最稳的方式是两层一起用：

```text
用户工作台：先规定 AI 怎么工作。
项目工作台：再规定这个项目怎么开发、验证和审查。
```

这个仓库不会发布作者本人的私人工作台配置。私人配置里通常包含本机路径、账号环境、MCP 偏好、hook 信任和权限决策，这些必须由每个使用者自己配置。

## 安装插件

先把这个仓库添加为 Codex marketplace：

```bash
codex plugin marketplace add Hapibit/codex-workbench --ref main
```

然后安装插件：

```bash
codex plugin add codex-workbench --marketplace hapibit
```

如果要固定 1.0.0 版本：

```bash
codex plugin marketplace add Hapibit/codex-workbench --ref v1.0.0
codex plugin add codex-workbench --marketplace hapibit
```

查看源码或维护插件：

```bash
git clone https://github.com/Hapibit/codex-workbench.git
```

## 第一次使用

进入你的项目根目录，然后对 Codex 说：

```text
Use Codex Workbench to set up this project's AI workbench.
```

Codex 会按项目情况生成或更新这些文件：

```text
AGENTS.md
PROJECT_INTAKE.md
WORKBENCH.md
REVIEW.md
DEVELOPMENT_FLOW.md
PRODUCT_BASELINE.md
FEATURE_WORKFLOW.md
workbench/
```

常见作用：

- `AGENTS.md`：项目级 AI 入口规则。
- `PROJECT_INTAKE.md`：项目画像，先确认目标、用户、范围、数据、权限和验收。
- `WORKBENCH.md`：项目工作台说明，记录命令、质量门和协作方式。
- `REVIEW.md`：项目审查规则。
- `DEVELOPMENT_FLOW.md`：项目开发流程契约。
- `PRODUCT_BASELINE.md`：最低产品质量线。
- `FEATURE_WORKFLOW.md`：重要功能的工作包流程。
- `workbench/quality/`：项目质量门脚本。
- `workbench/feature-template/`：功能工作包模板。
- `workbench/feedback/FAILURE_LOG.md`：重复失败和改进记录。

## 安装用户工作台模板

如果你还没有自己的全局 Codex 工作台，可以使用本插件提供的通用模板。

先预览，不写文件：

```bash
python plugins/codex-workbench/skills/codex-workbench/scripts/workbench.py user-workbench
```

确认后写入自己的 Codex 配置目录，默认是 `~/.codex/`：

```bash
python plugins/codex-workbench/skills/codex-workbench/scripts/workbench.py user-workbench --apply
```

如果目标文件已经存在，默认不会覆盖。确实要覆盖时：

```bash
python plugins/codex-workbench/skills/codex-workbench/scripts/workbench.py user-workbench --apply --force
```

覆盖前会生成 `.bak-时间戳` 备份。

用户工作台模板会生成：

```text
~/.codex/AGENTS.md
~/.codex/WORKBENCH_ROUTING.md
~/.codex/CODE_QUALITY.md
~/.codex/CODE_REVIEW.md
~/.codex/RTK.md
```

详细说明见：

```text
plugins/codex-workbench/docs/USER_WORKBENCH.md
```

## 工作流

Codex Workbench 的默认流程：

```text
1. Project Intake
   先确认项目目标、用户、范围、数据、权限、AI 边界。

2. Project Workbench
   生成项目规则、工作台说明、审查规则和质量门。

3. Feature Package
   重要功能按 SPEC -> CLARIFY -> PLAN -> TASKS -> VERIFY -> REVIEW 留证据。

4. Quality Gate
   交付前运行项目质量门、测试、lint、构建或人工验收。

5. Feedback Loop
   重复失败沉淀成模板、测试、质量门、CI、hook 或文档。
```

它不是要求所有小改动都走完整流程。工作台会按风险和影响面决定轻重：

- 小改动：轻量处理，直接验证。
- 中等影响：保留必要文档和验证证据。
- 高风险大影响：使用完整功能工作包。

## 什么时候需要功能工作包

这些情况建议创建功能工作包：

- 新功能。
- 跨模块修改。
- 登录、权限、角色、租户、用户数据。
- 数据库 schema、迁移、批量数据修改。
- 公开 API、消息结构、SDK 或第三方集成。
- AI 输出会自动写入核心数据或影响用户权益。
- 生产部署、CI/CD、环境变量、不可逆操作。
- 需求不清但影响范围可能较大。

创建功能工作包：

```text
Use Codex Workbench to create a feature work package named <feature-name>.
```

生成后通常会放在：

```text
workbench/features/<feature-name>/
├── SPEC.md
├── CLARIFY.md
├── PLAN.md
├── TASKS.md
├── DECISIONS.md
├── CHECKLIST.md
├── VERIFY.md
└── REVIEW.md
```

## 常用命令

检查项目情况：

```bash
python plugins/codex-workbench/skills/codex-workbench/scripts/workbench.py inspect --project <repo>
```

预览生成项目工作台：

```bash
python plugins/codex-workbench/skills/codex-workbench/scripts/workbench.py generate --project <repo> --name <project-name> --dry-run
```

验证项目工作台：

```bash
python plugins/codex-workbench/skills/codex-workbench/scripts/workbench.py validate --project <repo>
```

审计项目工作台：

```bash
python plugins/codex-workbench/skills/codex-workbench/scripts/workbench.py audit --project <repo>
```

## 可选增强能力

Codex Workbench 本身可以独立使用。其他 skill 和 MCP 是增强包，不是入门门槛。

| 任务 | 可选增强 |
| --- | --- |
| UI、Figma、设计稿、前端还原 | UI/Figma 类 skill |
| ER 图、流程图、架构图、UML | diagram/draw.io 类 skill |
| 单元测试、接口测试、Playwright、AI 对话测试 | testing 类 skill |
| Jenkins、GitHub Actions、CI/CD | CI/Jenkins 类 skill |
| README、Word、论文、PPT、技术文档 | docs 类 skill |
| RAG、Agent、LLM eval、安全治理 | AI governance 类 skill |

查看当前机器有哪些增强包可用：

```bash
python plugins/codex-workbench/skills/codex-workbench/scripts/check_enhancements.py --query "我要做 UI/Figma 和测试"
```

## 仓库结构

这个仓库本身是一个 Codex marketplace 源：

```text
.agents/plugins/marketplace.json
plugins/codex-workbench/
```

真正的插件包在：

```text
plugins/codex-workbench/
├── .codex-plugin/plugin.json
├── README.md
├── docs/
├── packaging-manifest.json
└── skills/codex-workbench/
```

## 使用者仍然要自己配置什么

这个插件不会替你登录第三方服务，也不会分发作者的私人配置。使用者仍然需要自己配置：

- Codex 安装和登录。
- 自己的 `~/.codex/config.toml`。
- MCP servers 和凭证。
- GitHub、Figma、Jenkins、OpenAI、Google 等账号权限。
- Node、Java、Maven、Docker、Python、浏览器、draw.io 等项目工具链。
- 项目的环境变量、API keys 和本地依赖。
- hook 信任、审批策略和权限决策。
- 项目自己的测试、lint、类型检查、构建和 CI 命令。

## 边界

Codex Workbench 不是：

- 业务需求的替代品。
- CI、测试、权限系统或人工验收的替代品。
- 私人账号、MCP 凭证、Figma/Jenkins/GitHub 登录态的分发工具。
- 保证 AI 永不出错的工具。

它的作用是把上下文、流程、质量门和复盘机制放到仓库里，让 AI 更难跳过关键步骤，也让人更容易审查 AI 做过什么。

## 维护者说明

普通使用者不需要看这一节。

如果你要修改、打包或发布这个插件，再看：

```text
plugins/codex-workbench/docs/maintenance/
plugins/codex-workbench/packaging-manifest.json
```

发布前检查：

```bash
python plugins/codex-workbench/skills/codex-workbench/scripts/workbench.py package-check --plugin plugins/codex-workbench --expected-version 1.0.0 --write-report
```

发布包应该只暴露一个可见 skill：

```text
codex-workbench
```
