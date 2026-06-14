# Hapibit Codex Plugins

这是 Hapibit 的 Codex 插件 marketplace 仓库。当前包含一个插件：

```text
codex-workbench
```

`codex-workbench` 是一个给 Codex 使用的 AI 开发工作台插件，用来为项目生成需求预处理、项目规则、功能工作包、质量门和审查规则。

## 安装

先把这个仓库添加为 Codex marketplace：

```bash
codex plugin marketplace add Hapibit/codex-workbench --ref main
```

然后安装插件：

```bash
codex plugin add codex-workbench --marketplace hapibit
```

安装后，在项目根目录对 Codex 说：

```text
Use Codex Workbench to set up this project's AI workbench.
```

## 本地测试

如果你 clone 了这个仓库，也可以把本地路径作为 marketplace 添加：

```bash
codex plugin marketplace add <本地仓库路径>
```

然后安装：

```bash
codex plugin add codex-workbench --marketplace hapibit
```

## 仓库结构

```text
.agents/plugins/marketplace.json
plugins/codex-workbench/
```

插件详情见：

```text
plugins/codex-workbench/README.md
```

## 发布前检查

维护者发布前运行：

```bash
python plugins/codex-workbench/skills/codex-workbench/scripts/workbench.py package-check --plugin plugins/codex-workbench --expected-version 1.0.0 --write-report
```
