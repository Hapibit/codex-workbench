# Codex Workbench

Codex Workbench 是一个给 Codex 使用的项目工作台插件。它只暴露一个入口：`codex-workbench`。

安装后，在项目根目录对 Codex 说：

```text
Use Codex Workbench to set up this project's AI workbench.
```

它会帮你在项目里建立一套 AI 开发工作流：需求预处理、项目规则、功能工作包、质量门和审查规则。

## 适合谁

- 想用 Codex 做项目，但不想一开始学习一堆 skill 名称的人。
- 想把 AI 开发流程固定到每个项目里的人。
- 想让需求、验证、审查和失败复盘有固定位置的人。
- 想把低质量 AI 代码挡在交付前的人。

## 它会生成什么

在目标项目中，工作台会按项目情况生成或升级这些内容：

- `AGENTS.md`：项目级 AI 规则入口。
- `PROJECT_INTAKE.md`：项目预处理画像，先弄清目标、用户、范围、数据、权限和验收。
- `WORKBENCH.md`：项目工作台说明。
- `REVIEW.md`：代码和功能审查标准。
- `DEVELOPMENT_FLOW.md`：项目自己的开发流程契约。
- `PRODUCT_BASELINE.md`：个人开发者也要达到的最低产品质量线。
- `FEATURE_WORKFLOW.md`：单个功能的 SDD 工作包流程。
- `workbench/`：质量门、运行时检查、独立审查提示、功能模板和失败日志。

## 基本用法

新项目或项目需求还不清楚时：

```text
Use Codex Workbench to set up this project's AI workbench.
```

已有项目想检查工作台是否可靠：

```text
Use Codex Workbench to audit this project workbench.
```

想知道下一步做什么：

```text
Use Codex Workbench to tell me the next step for this project.
```

创建一个重要功能的工作包：

```text
Use Codex Workbench to create a feature work package named <feature-name>.
```

## 你只需要理解五个词

- 项目预处理：先把项目需求、用户、范围、数据、权限和验收标准弄清楚。
- 项目工作台：让 AI 每次进项目先读项目规则和验证方式。
- 功能工作包：重要功能单独留下 SPEC、PLAN、TASKS、VERIFY、REVIEW 证据。
- 质量门：用脚本、测试、lint、类型检查、CI 或审查拦住低质量输出。
- 复盘改进：重复出错的地方沉淀成规则、脚本、测试或质量门。

## 可选增强能力

这个插件本身可以独立使用。其他 skill 是按任务推荐的增强包，不是入门门槛：

- UI/Figma 任务：再装 UI 或 Figma 相关 skill。
- ER 图、流程图、架构图：再装 diagram 或 draw.io 相关 skill。
- 测试、Jenkins、CI：再装测试和 CI 相关 skill。
- README、Word、论文、PPT：再装文档相关 skill。
- 安全、AI eval、RAG、智能体治理：再装对应专业 skill。

可以用内置检测脚本查看当前机器有哪些增强包可用：

```bash
python skills/codex-workbench/scripts/check_enhancements.py --query "我要做 UI/Figma 和测试"
```

## 你仍然要自己配置什么

这个插件不会带走作者的私人配置，也不会替你登录第三方服务。你仍然需要自己配置：

- Codex 安装和登录；
- 自己的 MCP、GitHub、Figma、Jenkins、OpenAI、Google 等账号和凭证；
- 项目需要的 Node、Java、Maven、Docker、Python 等本地工具链；
- hook 信任、权限提示和 API key；
- 项目自己的真实测试、lint、类型检查、CI 命令。

## 维护者说明

普通用户不需要关心发布包目录结构。维护、打包和发布规则放在：

```text
packaging-manifest.json
docs/maintenance/
```
