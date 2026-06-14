# Codex Workbench

Codex Workbench 是一个给 Codex 使用的 AI 开发工作台插件。它把项目里的需求澄清、开发流程、质量门、审查规则和验收证据固定下来，让 Codex 不只是“帮你写代码”，而是按一套可复查的项目流程工作。

安装后，你主要只需要记住这一句：

```text
Use Codex Workbench to set up this project's AI workbench.
```

## 30 秒理解

| 你遇到的问题 | Codex Workbench 做什么 |
| --- | --- |
| 需求不清，AI 直接脑补 | 先生成 `PROJECT_INTAKE.md`，把目标、用户、范围、数据、权限和验收说清楚 |
| 每个项目规则都散在聊天里 | 在项目里生成 `AGENTS.md`、`WORKBENCH.md`、`REVIEW.md` |
| AI 写完代码但没有证据 | 用 `VERIFY.md`、质量门脚本和审查清单留下可复查记录 |
| 大功能容易失控 | 用功能工作包把 SPEC、PLAN、TASKS、VERIFY、REVIEW 分阶段管理 |
| 同类错误反复出现 | 把失败沉淀到 `workbench/feedback/FAILURE_LOG.md`、模板、测试或质量门 |

## 快速开始

### 1. 安装插件

当前发布方式是 GitHub marketplace 源。先把这个仓库添加为 Codex marketplace：

```bash
codex plugin marketplace add Hapibit/codex-workbench --ref main
```

然后安装插件：

```bash
codex plugin add codex-workbench --marketplace hapibit
```

如果只是查看源码，可以 clone 仓库：

```bash
git clone https://github.com/Hapibit/codex-workbench.git
```

如果你从 fork 或其他分支安装，把 `Hapibit/codex-workbench` 和 `--ref main` 换成对应仓库和分支。

如果只是本机维护或测试这个插件，使用自己 clone 下来的本地仓库即可，也可以添加本地 marketplace：

```bash
codex plugin marketplace add <本地仓库路径>
```

### 2. 进入你的项目

在项目根目录打开 Codex，然后说：

```text
Use Codex Workbench to set up this project's AI workbench.
```

Codex 会先识别项目，再生成项目本地工作台。生成前如果项目目标不清楚，会先做项目预处理，而不是直接写一堆模板。

### 3. 检查下一步

后续可以直接问：

```text
Use Codex Workbench to tell me the next step for this project.
```

或检查已有工作台：

```text
Use Codex Workbench to audit this project workbench.
```

## 两层工作台

Codex Workbench 区分“用户工作台”和“项目工作台”。

| 层级 | 放在哪里 | 负责什么 | 谁来配置 |
| --- | --- | --- | --- |
| 用户工作台 | 使用者自己的 `~/.codex/` | 默认语言、搜索习惯、需求澄清、skill 路由、全局安全边界 | 使用者自己 |
| 项目工作台 | 每个项目仓库 | 项目事实、技术栈、业务边界、质量门、功能证据 | Codex Workbench 生成后由项目维护 |

项目工作台可以单独使用。用户工作台是可选增强，用来让 Codex 在进入任何项目之前就有统一工作习惯。

这个仓库不会分发作者本人的私人 Codex 配置。私人配置里可能包含本机路径、账号环境、MCP 偏好、hook 信任和权限决策，这些必须由每个使用者自己配置。

## 可选：安装用户工作台模板

如果你还没有自己的全局 Codex 工作台，可以使用本插件提供的通用模板。

先预览，不写文件：

```bash
python skills/codex-workbench/scripts/workbench.py user-workbench
```

确认后写入自己的 Codex 配置目录，默认是 `~/.codex/`：

```bash
python skills/codex-workbench/scripts/workbench.py user-workbench --apply
```

已有文件默认不会覆盖。确实要覆盖时再加：

```bash
python skills/codex-workbench/scripts/workbench.py user-workbench --apply --force
```

模板会生成：

```text
~/.codex/AGENTS.md
~/.codex/WORKBENCH_ROUTING.md
~/.codex/CODE_QUALITY.md
~/.codex/CODE_REVIEW.md
~/.codex/RTK.md
```

详细说明见 `docs/USER_WORKBENCH.md`。

## 项目工作台会生成什么

在目标项目里，Codex Workbench 会生成或升级这些文件：

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

核心文件说明：

| 文件 | 作用 |
| --- | --- |
| `AGENTS.md` | 项目级 AI 入口规则，告诉 Codex 进入项目后先读什么、怎么做 |
| `PROJECT_INTAKE.md` | 项目画像，记录目标用户、范围、数据、权限、AI 边界和验收 |
| `WORKBENCH.md` | 项目工作台说明，记录项目命令、质量门、证据位置和协作方式 |
| `REVIEW.md` | 项目审查规则，规定 P0/P1/P2 风险和必查项 |
| `DEVELOPMENT_FLOW.md` | 项目开发流程契约，避免每次都重新约定流程 |
| `PRODUCT_BASELINE.md` | 最低产品质量线，适合个人开发者也能守住下限 |
| `FEATURE_WORKFLOW.md` | 重要功能的分阶段工作包流程 |
| `workbench/quality/` | 项目质量门脚本 |
| `workbench/feature-template/` | 功能工作包模板 |
| `workbench/feedback/FAILURE_LOG.md` | 重复失败、根因和改进动作记录 |

## 工作流

默认流程是：

```text
Project Intake
  -> Project Workbench
  -> Feature Package
  -> Quality Gate
  -> Review
  -> Feedback Loop
```

意思是：

1. 先确认项目目标、用户、范围、数据、权限和验收。
2. 再生成项目本地规则、工作台说明、审查规则和质量门。
3. 重要功能用工作包记录 SPEC、CLARIFY、PLAN、TASKS、VERIFY、REVIEW。
4. 交付前运行项目质量门、测试、lint、构建或人工验收。
5. 重复失败要沉淀到模板、测试、质量门、CI、hook 或文档。

它不是要求所有改动都走完整流程。工作台会按风险和影响面决定轻重：

| 类型 | 处理方式 |
| --- | --- |
| 小改动 | 轻量处理，直接验证 |
| 中等影响 | 保留必要计划和验证证据 |
| 高风险大影响 | 使用完整功能工作包 |

## 什么时候创建功能工作包

这些情况建议创建功能工作包：

- 新功能。
- 跨模块修改。
- 登录、权限、角色、租户、用户数据。
- 数据库 schema、迁移、批量数据修改。
- 公开 API、消息结构、SDK 或第三方集成。
- AI 输出会自动写入核心数据或影响用户权益。
- 生产部署、CI/CD、环境变量、不可逆操作。
- 需求不清但影响范围可能较大。

创建方式：

```text
Use Codex Workbench to create a feature work package named <feature-name>.
```

生成位置通常是：

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

## 可选增强包

Codex Workbench 本身可以独立使用。其他 skill、MCP 或第三方工具是按任务需要再启用的增强能力，不是入门门槛。

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
python skills/codex-workbench/scripts/check_enhancements.py --query "我要做 UI/Figma 和测试"
```

## 使用者需要自己配置什么

这个插件不会替你登录第三方服务，也不会带走作者的私人配置。你仍然需要自己配置：

- Codex 安装和登录。
- 自己的 `~/.codex/config.toml`。
- MCP servers 和凭证。
- GitHub、Figma、Jenkins、OpenAI、Google 等账号权限。
- Node、Java、Maven、Docker、Python、浏览器、draw.io 等项目工具链。
- 项目的环境变量、API keys 和本地依赖。
- hook 信任、审批策略和权限决策。
- 项目自己的测试、lint、类型检查、构建和 CI 命令。

## 常用脚本

普通使用者通常不需要手动运行这些脚本，直接让 Codex 使用插件即可。维护或排查时可以使用：

```bash
python skills/codex-workbench/scripts/workbench.py inspect --project <repo>
python skills/codex-workbench/scripts/workbench.py generate --project <repo> --name <project-name> --dry-run
python skills/codex-workbench/scripts/workbench.py validate --project <repo>
python skills/codex-workbench/scripts/workbench.py audit --project <repo>
```

## 边界

Codex Workbench 不是：

- 业务需求的替代品。
- CI、测试、权限系统或人工验收的替代品。
- 私人账号、MCP 凭证、Figma/Jenkins/GitHub 登录态的分发工具。
- 保证 AI 永不出错的工具。

它做的是把上下文、流程、质量门和复盘机制放到仓库里，让 AI 更难跳过关键步骤，也让人更容易审查 AI 做过什么。

## 维护者入口

普通使用者可以跳过这一节。

维护、打包和发布规则在：

```text
packaging-manifest.json
docs/maintenance/
skills/codex-workbench/
```

发布前至少运行：

```bash
python skills/codex-workbench/scripts/workbench.py package-check --plugin <plugin-root> --expected-version 1.0.0 --write-report
```

发布包应该只暴露一个可见 skill：

```text
codex-workbench
```
