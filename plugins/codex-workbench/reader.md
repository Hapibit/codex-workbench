# Codex Workbench Reader

本文给第一次打开发布包的人看。完整说明见 `README.md`，架构细节见 `docs/CODEX_WORKBENCH_2_0_ARCHITECTURE.md`。

## 这是什么

Codex Workbench 是给 Codex 使用的 AI 开发工作台插件。当前发布版是 `2.0.3`，基于 `2.0.0` 架构基线。

它的目标不是保证 AI 永远写对，而是让受控项目里的需求、变更、影响分析、验证证据、review、质量门和失败复盘都有可检查记录。

## 快速开始

安装后，进入目标项目根目录，对 Codex 说：

```text
Use Codex Workbench to set up this project's AI workbench.
```

查看下一步：

```text
Use Codex Workbench to tell me the next step for this project.
```

创建功能包：

```text
Use Codex Workbench to create a feature work package named <feature-name>.
```

## 使用边界

- 项目工作台写进目标项目仓库。
- 用户工作台写进 `~/.codex/`，会影响所有项目，必须显式安装。
- hooks 需要使用者 review 和 trust；插件不会替用户跳过信任步骤。
- 本地 gate 只能判断可检查证据和状态；高风险语义质量仍需要 CI、独立 review 或人工验收。

## 发布检查

维护者发布前至少运行：

```powershell
py -B skills/codex-workbench/scripts/workbench.py self-test
py -B skills/codex-workbench/scripts/workbench.py golden-test
py -B skills/codex-workbench/scripts/workbench.py package-check --plugin <plugin-root> --expected-version 2.0.3 --write-report
```

严格发布还应运行：

```powershell
py -B skills/codex-workbench/scripts/workbench.py package-check --plugin <plugin-root> --expected-version 2.0.3 --strict-release
```
