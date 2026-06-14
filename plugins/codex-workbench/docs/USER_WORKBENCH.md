# 用户工作台接入说明

Codex Workbench 发布包包含两类东西：

- 项目工作台：写进具体项目仓库，用来记录项目事实、开发流程、质量门和功能证据。
- 用户工作台模板：写进使用者自己的 Codex 配置目录，用来规定 AI 的默认工作方式。

项目工作台是默认能力；用户工作台必须由使用者明确安装或手动复制，插件不会在安装时自动覆盖全局配置。

## 推荐位置

默认 Codex 用户配置目录：

```text
~/.codex/
```

推荐放置：

```text
~/.codex/
├── AGENTS.md
├── WORKBENCH_ROUTING.md
├── CODE_QUALITY.md
├── CODE_REVIEW.md
└── RTK.md
```

这些文件影响使用者打开的所有项目，所以不能带作者的私有路径、账号、MCP 登录态、hook 信任或本机工具配置。

## 快速预览

从插件目录运行：

```bash
python skills/codex-workbench/scripts/workbench.py user-workbench
```

这只会预览要写入哪些文件，不会修改 `~/.codex/`。

## 安装到自己的 Codex 配置

确认后再执行：

```bash
python skills/codex-workbench/scripts/workbench.py user-workbench --apply
```

如果目标文件已经存在，默认不会覆盖。需要覆盖时再加：

```bash
python skills/codex-workbench/scripts/workbench.py user-workbench --apply --force
```

覆盖前脚本会为已有文件生成 `.bak-时间戳` 备份。

## 这些文件负责什么

| 文件 | 作用 |
| --- | --- |
| `AGENTS.md` | 全局入口规则，规定默认语言、需求澄清、搜索、skill 路由、项目规则读取和硬门禁意识。 |
| `WORKBENCH_ROUTING.md` | 按任务类型选择增强 skill、MCP 或外部工具，避免让用户记一堆 skill 名称。 |
| `CODE_QUALITY.md` | 代码实现、测试、验证、AI/RAG、前端和文档同步的最低质量线。 |
| `CODE_REVIEW.md` | 代码审查输出格式、严重级别和必须检查的风险点。 |
| `RTK.md` | 低信号 shell 输出压缩规则；不是所有命令都必须套用。 |

## 和项目工作台怎么配合

用户工作台先决定“AI 应该怎么工作”：

- 需求不清先澄清。
- 当前事实先搜索。
- 先读取项目规则。
- 代码改完要验证。
- 不绕过审批、hook、sandbox、CI。

项目工作台再决定“这个项目具体怎么做”：

- 项目技术栈。
- 构建、测试、运行命令。
- 业务边界。
- 功能工作包。
- 质量门。
- 审查清单。

缺少用户工作台时，项目工作台仍然有用；但用户工作台可以让 Codex 在进入任何项目之前就有统一的工作习惯。

## 不能自动分发的内容

不要把这些内容放进发布包或用户工作台模板：

- API key、token、cookie、账号登录态。
- GitHub、Figma、Jenkins、OpenAI、Google 等凭证。
- 个人绝对路径。
- 私有 MCP 配置。
- hook 信任状态和审批状态。
- 只在作者机器存在的脚本或工具路径。

这些必须由每个接收者在自己的机器上配置。
