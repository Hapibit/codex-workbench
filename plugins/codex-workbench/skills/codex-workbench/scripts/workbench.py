#!/usr/bin/env python3
"""Cross-platform project workbench adapter tool.

Commands:
  inspect   Detect stack, commands, CI, docs, and existing adapter files.
  generate  Generate repository-local AGENTS/WORKBENCH/REVIEW/workbench files.
  upgrade   Conservatively add missing or outdated workbench adapter pieces.
  validate  Validate that a generated adapter is complete enough to use.
  audit     Audit adapter completeness, shareability, and hard-gate readiness.
  golden-test Run deterministic fixture tests for common project shapes.
  self-test Run a small offline smoke test of inspect/generate/validate/audit.
"""

from __future__ import annotations

import argparse
import ast
import filecmp
import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "node_modules",
    "dist",
    "build",
    "target",
    ".next",
    ".nuxt",
    ".venv",
    "venv",
    "__pycache__",
}

REQUIRED_ADAPTER_FILES = [
    "AGENTS.md",
    "PROJECT_INTAKE.md",
    "WORKBENCH.md",
    "REVIEW.md",
    "DEVELOPMENT_FLOW.md",
    "PRODUCT_BASELINE.md",
    "FEATURE_WORKFLOW.md",
    "workbench/product/PRODUCT_BRIEF.md",
    "workbench/product/PRD.md",
    "workbench/product/ROADMAP.md",
    "workbench/design/UX_SPEC.md",
    "workbench/design/PROTOTYPE.md",
    "workbench/design/USER_FLOW.md",
    "workbench/architecture/ARCHITECTURE.md",
    "workbench/architecture/DATA_MODEL.md",
    "workbench/architecture/API_DESIGN.md",
    "workbench/architecture/AI_DESIGN.md",
    "workbench/architecture/adr/README.md",
    "workbench/delivery/RELEASE_PLAN.md",
    "workbench/delivery/ITERATION_PLAN.md",
    "workbench/delivery/TASK_BREAKDOWN.md",
    "workbench/scorecard/RUBRIC.md",
    "workbench/scorecard/SCORECARD.md",
    "workbench/scorecard/CALIBRATION.md",
    "workbench/scorecard/scorecard.py",
    "workbench/scorecard/scorecard.ps1",
    "workbench/scorecard/scorecard.sh",
    "workbench/quality/quality_gate.py",
    "workbench/quality/quality-gate.ps1",
    "workbench/quality/quality-gate.sh",
    "workbench/runtime/runtime_gate.py",
    "workbench/runtime/runtime-gate.ps1",
    "workbench/runtime/runtime-gate.sh",
    "workbench/runtime/api_smoke.py",
    "workbench/runtime/api-smoke.ps1",
    "workbench/runtime/api-smoke.sh",
    "workbench/feedback/FAILURE_LOG.md",
    "workbench/feedback/ITERATION_LOG.md",
    "workbench/feedback/AI_EFFECTIVENESS.md",
    "workbench/review/independent-review-prompt.md",
    "workbench/feature-template/SPEC.md",
    "workbench/feature-template/CLARIFY.md",
    "workbench/feature-template/DESIGN.md",
    "workbench/feature-template/PLAN.md",
    "workbench/feature-template/TASKS.md",
    "workbench/feature-template/DECISIONS.md",
    "workbench/feature-template/IMPLEMENTATION_NOTES.md",
    "workbench/feature-template/CHECKLIST.md",
    "workbench/feature-template/VERIFY.md",
    "workbench/feature-template/REVIEW.md",
    "workbench/feature-template/CHANGELOG.md",
]

FEATURE_PACKAGE_FILES = [
    "SPEC.md",
    "CLARIFY.md",
    "DESIGN.md",
    "PLAN.md",
    "TASKS.md",
    "DECISIONS.md",
    "IMPLEMENTATION_NOTES.md",
    "CHECKLIST.md",
    "VERIFY.md",
    "REVIEW.md",
    "CHANGELOG.md",
]

REQUIRED_ADAPTER_TEXT_BY_FILE = {
    "AGENTS.md": [
        "需求不清",
        "完成标准",
        "quality_gate.py",
        "PRODUCT_BRIEF.md",
        "PRD.md",
        "UX_SPEC.md",
        "ARCHITECTURE.md",
        "工作量分级门",
        "硬触发器",
        "FAILURE_LOG.md",
        "不要提交",
    ],
    "PROJECT_INTAKE.md": [
        "预处理画像",
        "阻塞问题",
        "第一版范围",
        "AI 使用边界",
        "生成下游文件前检查",
    ],
    "WORKBENCH.md": [
        "quality_gate.py",
        "接收者配置",
        "工作台审计",
        "标准开发流程",
        "PRODUCT_BRIEF.md",
        "PRD.md",
        "UX_SPEC.md",
        "ARCHITECTURE.md",
        "ITERATION_LOG.md",
        "AI_EFFECTIVENESS.md",
        "工作量分级门",
        "硬触发器",
        "scorecard",
        "证据审计",
        "FAILURE_LOG.md",
        "反馈闭环",
        "workbench_upgrade_assessment",
    ],
    "REVIEW.md": [
        "严重级别",
        "必查项",
        "审查闭环",
        "输出格式",
    ],
    "DEVELOPMENT_FLOW.md": [
        "status: draft",
        "confirmed",
        "verification_commands",
        "需求不清",
    ],
    "PRODUCT_BASELINE.md": [
        "产品下限",
        "用户目标",
        "权限",
        "验证证据",
        "scorecard",
    ],
    "workbench/product/PRODUCT_BRIEF.md": [
        "产品简报",
        "业务目标",
        "成功指标",
        "可迭代",
    ],
    "workbench/product/PRD.md": [
        "产品需求",
        "用户故事",
        "验收标准",
        "非目标",
    ],
    "workbench/product/ROADMAP.md": [
        "路线图",
        "版本",
        "优先级",
        "依赖",
    ],
    "workbench/design/UX_SPEC.md": [
        "交互规格",
        "用户流程",
        "状态",
        "可访问性",
    ],
    "workbench/design/PROTOTYPE.md": [
        "原型",
        "页面",
        "状态",
        "验收",
    ],
    "workbench/design/USER_FLOW.md": [
        "用户流程",
        "入口",
        "成功路径",
        "失败路径",
    ],
    "workbench/architecture/ARCHITECTURE.md": [
        "架构设计",
        "模块",
        "边界",
        "风险",
    ],
    "workbench/architecture/DATA_MODEL.md": [
        "数据模型",
        "实体",
        "权限",
        "迁移",
    ],
    "workbench/architecture/API_DESIGN.md": [
        "API 设计",
        "契约",
        "错误",
        "权限",
    ],
    "workbench/architecture/AI_DESIGN.md": [
        "AI 设计",
        "输入",
        "输出",
        "eval",
    ],
    "workbench/architecture/adr/README.md": [
        "ADR",
        "Context",
        "Decision",
        "Consequences",
    ],
    "workbench/delivery/RELEASE_PLAN.md": [
        "发布计划",
        "范围",
        "验证",
        "回滚",
    ],
    "workbench/delivery/ITERATION_PLAN.md": [
        "迭代计划",
        "变更",
        "复测结果",
        "下一轮",
    ],
    "workbench/delivery/TASK_BREAKDOWN.md": [
        "任务拆分",
        "依赖",
        "验证",
        "负责人",
    ],
    "workbench/scorecard/RUBRIC.md": [
        "证据审计",
        "证据成熟度",
        "硬阻塞",
        "参考线",
        "可信度",
        "校准",
    ],
    "workbench/scorecard/SCORECARD.md": [
        "scorecard_status",
        "score_confidence",
        "calibration_status",
        "semantic_review_status",
        "架构合理性",
        "人工复核",
        "误报",
        "漏报",
    ],
    "workbench/scorecard/CALIBRATION.md": [
        "calibration_status",
        "锚定样例",
        "人工抽查",
        "误报",
        "漏报",
        "参考线调整",
    ],
    "FEATURE_WORKFLOW.md": [
        "工作量分级门",
        "硬触发器",
        "风险打分",
        "L1 轻量任务",
        "L2 中等任务",
        "L3 重量任务",
        "L4 紧急/重大任务",
        "SPEC.md",
        "CLARIFY.md",
        "DESIGN.md",
        "PLAN.md",
        "TASKS.md",
        "DECISIONS.md",
        "IMPLEMENTATION_NOTES.md",
        "CHECKLIST.md",
        "VERIFY.md",
        "REVIEW.md",
        "CHANGELOG.md",
    ],
    "workbench/feature-template/SPEC.md": [
        "用户目标",
        "验收标准",
        "范围",
        "approved_for_plan",
        "risk_level",
        "classification_reason",
    ],
    "workbench/feature-template/CLARIFY.md": [
        "需求澄清",
        "阻塞",
        "已确认",
        "ready_for_plan",
    ],
    "workbench/feature-template/DESIGN.md": [
        "功能设计",
        "UX",
        "架构",
        "approved_for_plan",
    ],
    "workbench/feature-template/PLAN.md": [
        "技术方案",
        "影响文件",
        "风险",
        "approved_for_tasks",
    ],
    "workbench/feature-template/TASKS.md": [
        "任务清单",
        "可验证",
        "ready_for_implementation",
    ],
    "workbench/feature-template/DECISIONS.md": [
        "决策记录",
        "原因",
        "影响",
    ],
    "workbench/feature-template/IMPLEMENTATION_NOTES.md": [
        "实现记录",
        "AI 修改",
        "偏离计划",
        "问题",
    ],
    "workbench/feature-template/CHECKLIST.md": [
        "阶段门禁",
        "SPEC",
        "feature_status",
        "current_stage",
        "分级门禁",
        "VERIFY",
    ],
    "workbench/feature-template/VERIFY.md": [
        "status",
        "验证命令",
        "验收记录",
        "workbench_upgrade_assessment",
    ],
    "workbench/feature-template/REVIEW.md": [
        "status",
        "审查结果",
        "P0",
        "P1",
        "workbench_upgrade_assessment",
    ],
    "workbench/feature-template/CHANGELOG.md": [
        "变更记录",
        "需求变化",
        "影响文件",
        "复测",
    ],
    "workbench/feedback/FAILURE_LOG.md": [
        "证据归档位置",
        "workbench/features/<feature-name>/VERIFY.md",
        "workbench_upgrade_assessment",
        "自动化状态",
        "质量门",
    ],
    "workbench/feedback/ITERATION_LOG.md": [
        "迭代记录",
        "变更来源",
        "影响层级",
        "复测结果",
    ],
    "workbench/feedback/AI_EFFECTIVENESS.md": [
        "AI 效果评估",
        "返工",
        "审查发现",
        "改进动作",
    ],
}

PERSONAL_PATH_PATTERNS = [
    re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+"),
    re.compile(r"/Users/[^/\s]+"),
    re.compile(r"/home/[^/\s]+"),
]

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|secret|password|cookie)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"),
    re.compile(r"(?<![A-Za-z0-9])sk-(?=[A-Za-z0-9_\-]{32,})(?=[A-Za-z0-9_\-]*\d)[A-Za-z0-9_\-]{32,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
]

IMPLEMENTATION_LEAK_PATTERNS = [
    re.compile(r"\b(?:codex-workbench-builder|project-intake-preflight|project-architect|enterprise-ai-app-lifecycle)\b"),
    re.compile(r"<skill>/scripts/workbench\.py"),
    re.compile(r"from the .* skill folder", re.IGNORECASE),
]

REPORT_DIR = ".workbench-validation"
ARCHIVE_DIR = "workbench/archive"
DEFAULT_RETENTION_KEEP_REPORTS = 5
MAINTENANCE_LOG_WARN_BYTES = 96 * 1024
MAINTENANCE_LOG_ARCHIVE_BYTES = 160 * 1024

PROCESS_STATUSES = {"draft", "confirmed"}
INTAKE_STATUSES = {"draft", "confirmed"}
FEATURE_STAGE_ORDER = ["spec", "clarify", "design", "plan", "tasks", "implement", "verify", "review", "complete"]
FEATURE_STAGES = set(FEATURE_STAGE_ORDER)
FEATURE_STATUSES = {"active", "on_hold", "complete"}
RISK_LEVELS = {"l1", "l2", "l3", "l4"}
SPEC_STATUSES = {"draft", "approved", "blocked"}
CLARIFY_STATUSES = {"blocked", "ready", "deferred"}
DESIGN_STATUSES = {"draft", "approved", "blocked"}
PLAN_STATUSES = {"draft", "approved", "blocked"}
TASKS_STATUSES = {"draft", "ready", "blocked"}
VERIFY_STATUSES = {"missing", "partial", "passed", "failed", "blocked"}
REVIEW_STATUSES = {"pending", "passed", "failed", "blocked"}
WORKBENCH_UPGRADE_ASSESSMENTS = {
    "not_required",
    "failure_log_updated",
    "template_update_needed",
    "quality_gate_update_needed",
    "review_rule_update_needed",
    "ci_or_hook_needed",
    "deferred_with_reason",
}
RECIPIENT_SETUP_ITEMS = [
    "Codex installation and login",
    "Recipient-owned Codex config",
    "Recipient-owned MCP servers and credentials",
    "GitHub/Figma/Jenkins/OpenAI/Google authentication when needed",
    "Hook trust and permission decisions",
    "Project local toolchain such as Node, Java, Maven, Docker, Python, draw.io, or browsers",
    "Project environment variables and API keys",
]

USER_WORKBENCH_FILES = [
    "AGENTS.md",
    "WORKBENCH_ROUTING.md",
    "CODE_QUALITY.md",
    "CODE_REVIEW.md",
    "RTK.md",
]

REQUIRED_SKILL_FILES = [
    "SKILL.md",
    "scripts/intake.py",
    "scripts/workbench.py",
    "scripts/check_enhancements.py",
    "assets/PROJECT_INTAKE.template.md",
    "assets/user-workbench-template/AGENTS.md",
    "assets/user-workbench-template/WORKBENCH_ROUTING.md",
    "assets/user-workbench-template/CODE_QUALITY.md",
    "assets/user-workbench-template/CODE_REVIEW.md",
    "assets/user-workbench-template/RTK.md",
    "assets/project-adapter-template/AGENTS.md",
    "assets/project-adapter-template/WORKBENCH.md",
    "assets/project-adapter-template/REVIEW.md",
    "assets/project-adapter-template/FEATURE_WORKFLOW.md",
    "assets/project-adapter-template/workbench/scorecard/RUBRIC.md",
    "assets/project-adapter-template/workbench/scorecard/SCORECARD.md",
    "assets/project-adapter-template/workbench/scorecard/CALIBRATION.md",
    "references/project-adapter-template.md",
    "references/quality-gate-patterns.md",
    "references/recipient-setup-boundaries.md",
    "references/workbench-maturity.md",
]

MAINTENANCE_EVIDENCE_FILES = {
    "docs/maintenance/IMPROVEMENT_LOG.md": [
        "证据来源",
        "变更文件",
        "验证结果",
        "后续动作",
    ],
    "docs/maintenance/FAILURE_PATTERNS.md": [
        "失败模式",
        "证据位置",
        "工作台处理层",
        "自动化状态",
    ],
    "docs/maintenance/adr/README.md": [
        "Status",
        "Context",
        "Decision",
        "Consequences",
    ],
}

PUBLISH_BLOCKLIST_PATTERNS = [
    re.compile(r"__pycache__"),
    re.compile(r"\.pyc$"),
    re.compile(r"(?:^|[\\/])legacy-skills(?:[\\/]|$)", re.IGNORECASE),
    re.compile(r"(?:^|[\\/])internal(?:[\\/]|$)", re.IGNORECASE),
]

AGENTS_MD_DEFAULT_LIMIT_BYTES = 32 * 1024
AGENTS_MD_NEAR_LIMIT_BYTES = 24 * 1024

PACKAGING_MANIFEST_REQUIRED_INCLUDES = [
    ".codex-plugin/plugin.json",
    "README.md",
    "docs/USER_WORKBENCH.md",
    "skills/codex-workbench/**",
    "docs/maintenance/**",
]

PACKAGING_MANIFEST_REQUIRED_EXCLUDES = [
    "internal/**",
    "**/__pycache__/**",
    "**/*.pyc",
    ".workbench-validation/**",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def as_posix(path: Path) -> str:
    return path.as_posix()


def resolve_project(path: str | None) -> Path:
    project = Path(path or os.getcwd()).expanduser().resolve()
    if not project.exists():
        raise SystemExit(f"Project path does not exist: {project}")
    if not project.is_dir():
        raise SystemExit(f"Project path is not a directory: {project}")
    return project


def rel_to(root: Path, path: Path) -> str:
    try:
        return as_posix(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def parse_pom(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": None,
        "artifactId": None,
        "packaging": None,
        "modules": [],
        "javaVersion": None,
    }
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except Exception as exc:
        result["error"] = f"Failed to parse pom.xml: {exc}"
        return result

    def strip(tag: str) -> str:
        return tag.rsplit("}", 1)[-1]

    def child_text(parent: ET.Element, name: str) -> str | None:
        for child in list(parent):
            if strip(child.tag) == name and child.text:
                return child.text.strip()
        return None

    def property_text(name: str) -> str | None:
        for child in list(root):
            if strip(child.tag) != "properties":
                continue
            for prop in list(child):
                if strip(prop.tag) == name and prop.text:
                    return prop.text.strip()
        return None

    result["artifactId"] = child_text(root, "artifactId")
    result["packaging"] = child_text(root, "packaging") or "jar"
    result["javaVersion"] = property_text("java.version") or property_text("maven.compiler.release")
    modules: list[str] = []
    for child in root.iter():
        if strip(child.tag) == "module" and child.text:
            modules.append(child.text.strip())
    result["modules"] = modules
    return result


def iter_files(root: Path, filename: str, max_depth: int = 3) -> list[Path]:
    found: list[Path] = []
    root_depth = len(root.parts)
    for current, dirs, files in os.walk(root):
        cur = Path(current)
        depth = len(cur.parts) - root_depth
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and depth < max_depth]
        if filename in files:
            found.append(cur / filename)
    return sorted(found)


def detect_package_manager(directory: Path) -> str:
    if (directory / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (directory / "yarn.lock").exists():
        return "yarn"
    if (directory / "bun.lockb").exists() or (directory / "bun.lock").exists():
        return "bun"
    return "npm"


def package_command(package_manager: str, script: str) -> list[str]:
    if package_manager == "pnpm":
        return ["pnpm", "run", script]
    if package_manager == "yarn":
        return ["yarn", "run", script]
    if package_manager == "bun":
        return ["bun", "run", script]
    return ["npm", "run", script]


def detect_node(root: Path) -> list[dict[str, Any]]:
    projects: list[dict[str, Any]] = []
    for package_path in iter_files(root, "package.json", max_depth=3):
        data = read_json(package_path)
        directory = package_path.parent
        scripts = data.get("scripts", {}) if isinstance(data, dict) else {}
        dependencies = {}
        if isinstance(data, dict):
            for key in ("dependencies", "devDependencies"):
                if isinstance(data.get(key), dict):
                    dependencies.update(data[key])
        framework = "node"
        for name in ("vite", "vue", "react", "next", "nuxt", "svelte", "angular"):
            if name in dependencies or f"@{name}/core" in dependencies:
                framework = name
                break
        projects.append(
            {
                "path": rel_to(root, directory),
                "packageJson": rel_to(root, package_path),
                "packageManager": detect_package_manager(directory),
                "name": data.get("name") if isinstance(data, dict) else None,
                "framework": framework,
                "scripts": scripts if isinstance(scripts, dict) else {},
            }
        )
    return projects


def detect_maven(root: Path) -> list[dict[str, Any]]:
    projects: list[dict[str, Any]] = []
    for pom_path in iter_files(root, "pom.xml", max_depth=4):
        info = parse_pom(pom_path)
        info["path"] = rel_to(root, pom_path.parent)
        info["pom"] = rel_to(root, pom_path)
        projects.append(info)
    return projects


def detect_compose(root: Path) -> list[str]:
    names = ["docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"]
    return [name for name in names if (root / name).exists()]


def detect_ci(root: Path) -> dict[str, Any]:
    workflows_dir = root / ".github" / "workflows"
    workflows: list[str] = []
    if workflows_dir.exists():
        for item in sorted(workflows_dir.iterdir()):
            if item.suffix.lower() in {".yml", ".yaml"}:
                workflows.append(rel_to(root, item))
    return {
        "githubActions": workflows,
        "jenkinsfile": (root / "Jenkinsfile").exists(),
    }


def detect_existing_adapter(root: Path) -> dict[str, bool]:
    return {
        "AGENTS.md": (root / "AGENTS.md").exists(),
        "WORKBENCH.md": (root / "WORKBENCH.md").exists(),
        "REVIEW.md": (root / "REVIEW.md").exists(),
        "workbench": (root / "workbench").exists(),
        "qualityGatePython": (root / "workbench" / "quality" / "quality_gate.py").exists(),
        "qualityGatePowerShell": (root / "workbench" / "quality" / "quality-gate.ps1").exists(),
        "qualityGateShell": (root / "workbench" / "quality" / "quality-gate.sh").exists(),
    }


def build_quality_commands(root: Path, inspection: dict[str, Any]) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    for compose_file in inspection["composeFiles"]:
        commands.append(
            {
                "name": f"docker compose config ({compose_file})",
                "group": "docker",
                "profiles": ["smoke", "standard", "full"],
                "cwd": ".",
                "command": ["docker", "compose", "-f", compose_file, "config", "--quiet"],
            }
        )
    for node in inspection["nodeProjects"]:
        scripts = node.get("scripts") or {}
        pm = node.get("packageManager") or "npm"
        profile_by_script = {
            "lint": ["smoke", "standard", "full"],
            "typecheck": ["smoke", "standard", "full"],
            "type-check": ["smoke", "standard", "full"],
            "build": ["standard", "full"],
            "test": ["standard", "full"],
            "test:e2e": ["full"],
            "e2e": ["full"],
        }
        for script in ("lint", "typecheck", "type-check", "build", "test", "test:e2e", "e2e"):
            if script in scripts:
                commands.append(
                    {
                        "name": f"{node['path']} {script}",
                        "group": "node",
                        "profiles": profile_by_script[script],
                        "cwd": node["path"] or ".",
                        "command": package_command(pm, script),
                    }
                )
    root_maven = [m for m in inspection["mavenProjects"] if m.get("path") in ("", ".")]
    aggregator_maven = [m for m in inspection["mavenProjects"] if m.get("modules")]
    maven_targets = root_maven or sorted(aggregator_maven, key=lambda item: len(str(item.get("path") or "").split("/")))[:1] or inspection["mavenProjects"][:1]
    for maven in maven_targets:
        pom = maven.get("pom") or "pom.xml"
        commands.append(
            {
                "name": f"maven package ({pom})",
                "group": "maven",
                "profiles": ["standard", "full"],
                "cwd": ".",
                "command": ["mvn", "-f", pom, "-DskipTests", "package"],
            }
        )
    return commands


def inspect_project(project: Path) -> dict[str, Any]:
    inspection: dict[str, Any] = {
        "schema": "codex-workbench-inspection/v1",
        "timestamp": utc_now(),
        "projectRoot": str(project),
        "platform": sys.platform,
        "nodeProjects": detect_node(project),
        "mavenProjects": detect_maven(project),
        "composeFiles": detect_compose(project),
        "ci": detect_ci(project),
        "existingAdapter": detect_existing_adapter(project),
    }
    inspection["qualityCommands"] = build_quality_commands(project, inspection)
    inspection["warnings"] = build_inspection_warnings(inspection)
    return inspection


def build_inspection_warnings(inspection: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if not inspection["qualityCommands"]:
        warnings.append("No quality gate commands were detected. Confirm project build/test commands before generating.")
    existing = inspection["existingAdapter"]
    if any(existing.values()):
        warnings.append("Existing workbench files were detected. Use --force only after reviewing backups.")
    return warnings


def write_json(data: dict[str, Any], output: str | None) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if output:
        target = Path(output).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def format_commands(commands: list[dict[str, Any]]) -> str:
    if not commands:
        return "- No commands detected. Configure the quality gate before relying on this adapter."
    lines = []
    for command in commands:
        cwd = command.get("cwd") or "."
        cmd = " ".join(command["command"])
        profiles = ", ".join(command.get("profiles") or ["standard"])
        lines.append(f"- `{cmd}` in `{cwd}` ({command['group']}; profiles: {profiles})")
    return "\n".join(lines)


def generate_agents_md(project_name: str, inspection: dict[str, Any]) -> str:
    commands = format_commands(inspection["qualityCommands"])
    node = inspection["nodeProjects"]
    maven = inspection["mavenProjects"]
    compose = inspection["composeFiles"]
    return f"""# {project_name} Project Workbench

This is a repository-local Codex adapter. It describes this project only. Global Codex preferences, MCP credentials, hooks, and user login state belong in each user's own Codex configuration.

## Project Identity

- Project root: repository root where this `AGENTS.md` file is located.
- Node projects: {', '.join(p['path'] or '.' for p in node) if node else 'none detected'}
- Maven projects: {', '.join(p['pom'] for p in maven) if maven else 'none detected'}
- Compose files: {', '.join(compose) if compose else 'none detected'}

## Required Workflow

1. Read this file, `WORKBENCH.md`, and `REVIEW.md` before editing project code.
2. Clarify unclear requirements before implementation when scope, acceptance, permissions, data ownership, environment, or safety boundaries are ambiguous.
3. Keep changes small and project-local. Do not overwrite unrelated user changes.
4. Use existing frameworks, scripts, components, and conventions before adding new patterns.
5. After project code changes, run the project quality gate when available.

## Quality Gate

Run the cross-platform quality gate:

```bash
python workbench/quality/quality_gate.py
```

Windows wrapper:

```powershell
powershell -NoProfile -File .\\workbench\\quality\\quality-gate.ps1
```

Detected checks:

{commands}

The quality gate writes `.workbench-validation/quality-gate-ok.json` only after all checks pass.

## High-Risk Decisions

Ask before making changes involving credentials, destructive actions, database schema, public API contracts, production deploy behavior, user data, payment/grades/core records, security boundaries, or AI-generated content that takes effect without human review.

## Project Boundaries

- Do not place project-specific commands in global Codex files.
- Do not commit local secrets, tokens, cookies, or personal login state.
- If a rule is repeatedly skipped, move it into a script, test, lint rule, pre-commit hook, CI job, or quality gate.
"""


def generate_workbench_md(project_name: str, inspection: dict[str, Any]) -> str:
    commands = format_commands(inspection["qualityCommands"])
    return f"""# {project_name} Workbench

## Purpose

This directory contains the project adapter for Codex and other coding agents. It is not a replacement for each user's global Codex installation, authentication, MCP setup, or hook trust.

## Files

- `AGENTS.md`: project rules and workflow entry.
- `REVIEW.md`: project-specific review checks.
- `workbench/quality/quality_gate.py`: cross-platform quality gate.
- `workbench/quality/quality-gate.ps1`: Windows wrapper.
- `workbench/quality/quality-gate.sh`: POSIX wrapper.
- `workbench/runtime/runtime_gate.py`: runtime smoke plan and optional URL checks.
- `workbench/review/independent-review-prompt.md`: review-only prompt for a fresh AI pass.

## Quality Gate

```bash
python workbench/quality/quality_gate.py
```

Detected checks:

{commands}

If no checks are configured, the gate fails unless `--allow-empty` is passed. Do not treat an empty gate as real validation for code projects.

## Runtime Gate

Dry-run plan:

```bash
python workbench/runtime/runtime_gate.py
```

Apply URL smoke checks:

```bash
python workbench/runtime/runtime_gate.py --apply --backend-health-url http://localhost:8080/health
```

## Validation

Validate the adapter through Codex Workbench:

```text
Use Codex Workbench to validate this project workbench.
```

## Recipient Setup

Each recipient must configure their own Codex login, MCP credentials, GitHub/Figma/Jenkins access, hook trust, local toolchain, and environment variables. Do not share API keys, cookies, tokens, or personal config files.
"""


def generate_development_flow_md(project_name: str, inspection: dict[str, Any]) -> str:
    commands = format_commands(inspection["qualityCommands"])
    return f"""# {project_name} Development Flow

status: draft
owner: project owner
confirmed_at: unconfirmed
scope: project-specific changes
verification_commands:
{commands}

## Purpose

This file is the project-specific development process contract. It starts as `draft`; use it as guidance only until the project owner confirms or edits it.

## Status Rules

- `draft`: AI may use this as a checklist, but must ask before applying it to feature work, public API changes, schema changes, permission changes, production deploy changes, or AI output that takes effect automatically.
- `confirmed`: AI should follow this flow for project work unless the user gives a newer project-specific instruction.
- If this file conflicts with current code, CI, product requirements, or explicit user instructions, stop and ask.

## Default Flow

1. Read `AGENTS.md`, `WORKBENCH.md`, `REVIEW.md`, and this file.
2. Clarify the goal, scope, acceptance criteria, data ownership, permission boundaries, environment, and rollback needs.
3. Inspect the existing implementation, tests, scripts, CI, and relevant docs before planning code edits.
4. Make the smallest coherent change that follows existing project structure and conventions.
5. Run the smallest reliable verification first, then expand verification for cross-module or high-risk changes.
6. Review the diff against `REVIEW.md`; use independent review for sensitive or broad changes.
7. Report changed files, verification evidence, unverified risks, and any workbench rule or gate that should be improved.

## Requirement Clarification

When requirements are unclear, ask only for information that changes the implementation path. Do not ask for facts that can be discovered safely from the repo.

Must clarify before implementation when the request lacks:

- user-visible acceptance criteria;
- affected page, API, module, database table, model, or workflow;
- role, permission, tenant, organization, course, user, file, or other data-ownership boundary;
- destructive, irreversible, migration, deployment, or credential behavior;
- AI-generated content approval rules, source requirements, or eval criteria.

## Flow By Change Type

- Bugfix: reproduce or identify the failing behavior, add or update a regression check when practical, then fix.
- Feature: confirm acceptance criteria and affected surfaces, add tests or smoke checks for the main path and one relevant failure path.
- AI/RAG/agent feature: define input cases, expected behavior, forbidden behavior, sources/tools allowed, eval rubric, logging and privacy constraints.
- UI change: verify desktop and mobile layout, console errors, overflow, text clipping, and core interaction in a real browser when practical.
- Backend/API change: check contract compatibility, authz/data ownership, error responses, idempotency, and persistence boundaries.
- Docs-only change: verify links, commands, examples, and whether docs describe actual project behavior.

## Human Confirmation Checklist

Before changing `status` to `confirmed`, the project owner should verify:

- the flow matches the team's real workflow;
- quality commands are real and runnable in this repo;
- high-risk decisions and approval boundaries are accurate;
- CI or local quality gates cover the checks that must not be skipped;
- docs-only, small bugfix, feature, AI feature, UI, and backend paths are acceptable.

## Maintenance

When the same failure repeats, update this file only if the fix is a human decision rule. If it can be automated, prefer a test, lint rule, pre-commit hook, CI check, or `workbench/quality/quality_gate.py`.
"""


def generate_review_md(project_name: str) -> str:
    return f"""# {project_name} Review Rules

## Review Goal

Review for behavior, security, data ownership, maintainability, rollback safety, and missing verification. Prefer concrete findings over style opinions.

## Severity

- `P0`: data leak, privilege bypass, production outage, irreversible corruption, or impossible rollback.
- `P1`: clear functional bug, security gap, contract break, missing authorization, or core workflow failure.
- `P2`: edge-case bug, maintainability risk, weak test coverage, performance regression, or observability gap.
- `Nit`: low-risk readability or naming issue. Report only when useful.

## Must Check

- Does the implementation satisfy the requirement instead of only the happy path?
- Are role, resource, tenant, organization, course, user, or other ownership boundaries preserved?
- Are public API contracts, database schema, and frontend/backend expectations compatible?
- Are tests or manual checks strong enough to fail when the behavior breaks?
- Are secrets, tokens, cookies, logs, uploads, and external calls handled safely?
- Does the change avoid unrelated rewrites and user-change rollback?

## Output

List findings first, ordered by severity. Include file path, line, risk, trigger scenario, and fix direction. If no blocking issue is found, say so and list any validation gaps.
"""


def quote_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def render_template(rel_path: str, variables: dict[str, str], fallback: str) -> str:
    template_path = skill_root() / "assets" / "project-adapter-template" / rel_path
    if template_path.exists():
        content = template_path.read_text(encoding="utf-8")
    else:
        content = fallback
    for key, value in variables.items():
        content = content.replace("{{" + key + "}}", value)
    return content


def summarize_list(items: list[str]) -> str:
    return ", ".join(items) if items else "none detected"


def template_variables(project_name: str, inspection: dict[str, Any]) -> dict[str, str]:
    node_projects = [p["path"] or "." for p in inspection["nodeProjects"]]
    maven_projects = [p["pom"] for p in inspection["mavenProjects"]]
    return {
        "PROJECT_NAME": project_name,
        "PROJECT_ROOT": "repository root where this AGENTS.md file is located",
        "NODE_PROJECTS": summarize_list(node_projects),
        "MAVEN_PROJECTS": summarize_list(maven_projects),
        "COMPOSE_FILES": summarize_list(inspection["composeFiles"]),
        "QUALITY_COMMANDS": format_commands(inspection["qualityCommands"]),
    }


def generate_quality_gate_py(commands: list[dict[str, Any]]) -> str:
    command_json = quote_json(commands)
    feature_files_json = quote_json(FEATURE_PACKAGE_FILES)
    return f'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

COMMANDS = {command_json}
FEATURE_PACKAGE_FILES = {feature_files_json}


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run_scorecard(root: Path, profile: str) -> None:
    script = root / "workbench" / "scorecard" / "scorecard.py"
    if not script.exists():
        raise SystemExit("[quality] scorecard.py is missing. Generate or upgrade workbench/scorecard before trusting evidence reporting.")
    command = [sys.executable, str(script), "--profile", profile, "--write-report", "--called-from-quality-gate", "--enforce-blockers"]
    print("[quality] scorecard evidence report")
    result = subprocess.run(command, cwd=str(root), text=True)
    if result.returncode != 0:
        raise SystemExit(f"[quality] scorecard found blocking evidence gaps (exit {{result.returncode}})")


def run_step(root: Path, step: dict) -> None:
    name = step["name"]
    group = step.get("group", "default")
    cwd = root / step.get("cwd", ".")
    command = step["command"]
    exe = command[0]
    if shutil.which(exe) is None:
        raise SystemExit(f"[quality] missing command for {{name}}: {{exe}}")
    print(f"[quality] {{name}}")
    result = subprocess.run(command, cwd=str(cwd), text=True)
    if result.returncode != 0:
        raise SystemExit(f"[quality] failed: {{name}} (exit {{result.returncode}})")


def check_project_intake(root: Path) -> str | None:
    intake = root / "PROJECT_INTAKE.md"
    if not intake.exists():
        return None
    text = intake.read_text(encoding="utf-8", errors="replace")
    if re.search(r"(?im)^\\s*status\\s*:\\s*draft\\s*$", text):
        raise SystemExit("[quality] PROJECT_INTAKE.md is still draft. Confirm project intake before relying on this workbench for feature or high-risk work.")
    if re.search(r"(?im)^\\|\\s*P\\d+\\s*\\|.*\\|\\s*open\\s*\\|\\s*$", text):
        raise SystemExit("[quality] PROJECT_INTAKE.md has open blocking project-intake questions.")
    return str(intake.relative_to(root))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def read_field(text: str, name: str) -> str | None:
    match = re.search(rf"(?im)^\\s*{{re.escape(name)}}\\s*:\\s*(.+?)\\s*$", text)
    return match.group(1).strip() if match else None


def read_bool(text: str, name: str) -> bool:
    return (read_field(text, name) or "").lower() == "true"


def read_int(text: str, name: str) -> int | None:
    value = read_field(text, name)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def is_placeholder_value(value: str | None) -> bool:
    return value is None or value.strip().lower() in {{"", "unclassified", "待填写", "todo", "tbd"}}


def current_stage_index(stage: str) -> int:
    try:
        return ["spec", "clarify", "design", "plan", "tasks", "implement", "verify", "review", "complete"].index(stage)
    except ValueError:
        return -1


def stage_reached(current_stage: str, expected_stage: str) -> bool:
    current = current_stage_index(current_stage)
    expected = current_stage_index(expected_stage)
    return current >= expected and expected >= 0


def require_feature_field(package: Path, filename: str, field: str, expected: str | bool) -> None:
    text = read_text(package / filename)
    value = read_bool(text, field) if isinstance(expected, bool) else (read_field(text, field) or "").lower()
    if value != expected:
        raise SystemExit(f"[quality] feature package {{package.relative_to(project_root())}} is not complete: {{filename}} {{field}} must be {{expected}}")


def require_feature_status(package: Path, filename: str, allowed: set[str]) -> str:
    text = read_text(package / filename)
    status = (read_field(text, "status") or "").lower()
    if status not in allowed:
        raise SystemExit(f"[quality] feature package {{package.relative_to(project_root())}} has invalid {{filename}} status: {{status or 'missing'}}")
    return status


def check_feature_packages(root: Path) -> list[str]:
    feature_root = root / "workbench" / "features"
    if not feature_root.exists():
        return []
    packages = [item for item in sorted(feature_root.iterdir()) if item.is_dir()]
    checked: list[str] = []
    for package in packages:
        missing = [rel for rel in FEATURE_PACKAGE_FILES if not (package / rel).exists()]
        if missing:
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} is missing files: {{', '.join(missing)}}")
        checklist_text = read_text(package / "CHECKLIST.md")
        feature_status = (read_field(checklist_text, "feature_status") or "active").lower()
        current_stage = (read_field(checklist_text, "current_stage") or "unknown").lower()
        if feature_status not in {{"active", "on_hold", "complete"}}:
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} has invalid feature_status: {{feature_status}}")
        if current_stage not in {{"spec", "clarify", "design", "plan", "tasks", "implement", "verify", "review", "complete"}}:
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} has invalid current_stage: {{current_stage}}")
        if feature_status == "on_hold":
            checked.append(str(package.relative_to(root)) + " (on_hold)")
            continue

        spec_text = read_text(package / "SPEC.md")
        clarify_text = read_text(package / "CLARIFY.md")
        design_text = read_text(package / "DESIGN.md")
        plan_text = read_text(package / "PLAN.md")
        tasks_text = read_text(package / "TASKS.md")
        spec_status = require_feature_status(package, "SPEC.md", {{"draft", "approved", "blocked"}})
        clarify_status = require_feature_status(package, "CLARIFY.md", {{"blocked", "ready", "deferred"}})
        design_status = require_feature_status(package, "DESIGN.md", {{"draft", "approved", "blocked"}})
        plan_status = require_feature_status(package, "PLAN.md", {{"draft", "approved", "blocked"}})
        tasks_status = require_feature_status(package, "TASKS.md", {{"draft", "ready", "blocked"}})
        verify_status = require_feature_status(package, "VERIFY.md", {{"missing", "partial", "passed", "failed", "blocked"}})
        review_status = require_feature_status(package, "REVIEW.md", {{"pending", "passed", "failed", "blocked"}})
        review_text = read_text(package / "REVIEW.md")
        workbench_upgrade_assessment = (read_field(review_text, "workbench_upgrade_assessment") or "unassessed").lower()
        accepted_upgrade_assessments = {{
            "not_required",
            "failure_log_updated",
            "template_update_needed",
            "quality_gate_update_needed",
            "review_rule_update_needed",
            "ci_or_hook_needed",
            "deferred_with_reason",
        }}
        if workbench_upgrade_assessment == "unassessed" and (verify_status in {{"failed", "blocked"}} or review_status in {{"failed", "blocked"}} or current_stage == "complete" or feature_status == "complete"):
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} must set REVIEW.md workbench_upgrade_assessment before passing quality gate")
        if workbench_upgrade_assessment != "unassessed" and workbench_upgrade_assessment not in accepted_upgrade_assessments:
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} has invalid workbench_upgrade_assessment: {{workbench_upgrade_assessment}}")
        risk_level = (read_field(spec_text, "risk_level") or "unclassified").lower()
        impact_score = read_int(spec_text, "impact_score")
        uncertainty_score = read_int(spec_text, "uncertainty_score")
        rollback_score = read_int(spec_text, "rollback_score")
        risk_score = read_int(spec_text, "risk_score")
        hard_triggers = read_field(spec_text, "hard_triggers")
        classification_reason = read_field(spec_text, "classification_reason")
        if risk_level not in {{"l1", "l2", "l3", "l4"}}:
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} has invalid risk_level: {{risk_level}}")
        component_scores = [impact_score, uncertainty_score, rollback_score]
        if any(score is None or score < 0 or score > 3 for score in component_scores):
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} has invalid impact/uncertainty/rollback risk scores")
        if risk_score is None or risk_score < 0 or risk_score > 9:
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} has invalid risk_score")
        if risk_score != sum(component_scores):
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} risk_score must equal impact_score + uncertainty_score + rollback_score")
        if is_placeholder_value(hard_triggers) or is_placeholder_value(classification_reason):
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} is missing risk classification evidence in SPEC.md")
        if risk_score >= 6 and risk_level in {{"l1", "l2"}}:
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} risk_level is too low for risk_score >= 6")
        if risk_score >= 3 and risk_level == "l1":
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} risk_level is too low for risk_score >= 3")
        if stage_reached(current_stage, "plan") and (spec_status != "approved" or not read_bool(spec_text, "approved_for_plan")):
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} reached PLAN before SPEC was approved")
        if stage_reached(current_stage, "plan") and (clarify_status not in {{"ready", "deferred"}} or not read_bool(clarify_text, "ready_for_plan")):
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} reached PLAN before CLARIFY was ready")
        if stage_reached(current_stage, "plan") and (design_status != "approved" or not read_bool(design_text, "approved_for_plan")):
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} reached PLAN before DESIGN was approved")
        if stage_reached(current_stage, "tasks") and (plan_status != "approved" or not read_bool(plan_text, "approved_for_tasks")):
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} reached TASKS before PLAN was approved for tasks")
        if stage_reached(current_stage, "implement") and (not read_bool(plan_text, "approved_for_implementation") or tasks_status != "ready" or not read_bool(tasks_text, "ready_for_implementation")):
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} reached IMPLEMENT before PLAN/TASKS allowed implementation")
        if stage_reached(current_stage, "review") and verify_status != "passed":
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} reached REVIEW before VERIFY passed")
        if current_stage == "complete" and review_status != "passed":
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} reached complete before REVIEW passed")

        if re.search(r"(?im)^\\|\\s*C\\d+\\s*\\|.*\\|\\s*open\\s*\\|\\s*$", clarify_text):
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} still has open blocking clarification items in CLARIFY.md")
        if feature_status != "complete":
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} is {{feature_status}}. Set feature_status to on_hold for paused work, or complete it before passing the final quality gate.")
        require_feature_field(package, "SPEC.md", "approved_for_plan", True)
        require_feature_field(package, "CLARIFY.md", "ready_for_plan", True)
        require_feature_field(package, "DESIGN.md", "approved_for_plan", True)
        require_feature_field(package, "PLAN.md", "approved_for_tasks", True)
        require_feature_field(package, "PLAN.md", "approved_for_implementation", True)
        require_feature_field(package, "TASKS.md", "ready_for_implementation", True)
        require_feature_field(package, "VERIFY.md", "status", "passed")
        require_feature_field(package, "REVIEW.md", "status", "passed")
        if not read_bool(checklist_text, "implementation_allowed") or not read_bool(checklist_text, "delivery_allowed"):
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} is complete but CHECKLIST.md has not allowed implementation and delivery")
        if re.search(r"(?m)^- \\[ \\]", checklist_text) or re.search(r"(?m)^- \\[ \\]", read_text(package / "TASKS.md")):
            raise SystemExit(f"[quality] feature package {{package.relative_to(root)}} still has unchecked checklist or task items")
        checked.append(str(package.relative_to(root)))
    return checked


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-empty", action="store_true")
    parser.add_argument("--profile", choices=["smoke", "standard", "full"], default="standard")
    parser.add_argument("--skip", action="append", default=[], help="Skip a command group such as docker, node, or maven.")
    args = parser.parse_args()

    root = project_root()
    selected = [
        cmd
        for cmd in COMMANDS
        if cmd.get("group") not in set(args.skip)
        and args.profile in set(cmd.get("profiles", ["standard"]))
    ]
    print(f"[quality] profile={{args.profile}}")
    checks_run: list[str] = []
    checked_intake = check_project_intake(root)
    if checked_intake:
        print(f"[quality] checked project intake: {{checked_intake}}")
        checks_run.append("project intake blockers")
    checked_features = check_feature_packages(root)
    if checked_features:
        print(f"[quality] checked SDD feature packages: {{', '.join(checked_features)}}")
        checks_run.append("sdd feature package structure")
    if not selected and not args.allow_empty:
        raise SystemExit(f"[quality] no checks configured for profile {{args.profile}}. Update workbench/quality/quality_gate.py or pass --allow-empty only for docs-only projects.")
    for step in selected:
        run_step(root, step)
        checks_run.append(step["name"])
    run_scorecard(root, args.profile)
    checks_run.append("scorecard evidence report")

    marker_dir = root / ".workbench-validation"
    marker_dir.mkdir(parents=True, exist_ok=True)
    marker = marker_dir / "quality-gate-ok.json"
    marker.write_text(json.dumps({{
        "gate": "quality-gate",
        "status": "passed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "projectRoot": str(root),
        "profile": args.profile,
        "checksRun": checks_run,
    }}, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
    print(f"[quality] wrote {{marker}}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def generate_scorecard_py() -> str:
    feature_files_json = quote_json(FEATURE_PACKAGE_FILES)
    required_adapter_files_json = quote_json(REQUIRED_ADAPTER_FILES)
    script = r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

FEATURE_PACKAGE_FILES = __FEATURE_PACKAGE_FILES__
REQUIRED_ADAPTER_FILES = __REQUIRED_ADAPTER_FILES__

WEIGHTS = {
    "intake": 15,
    "product": 15,
    "design": 10,
    "architecture": 15,
    "delivery": 10,
    "features": 20,
    "verification": 10,
    "feedback": 5,
}

PROFILE_RULES = {
    "smoke": {
        "reference_score": 60,
        "max_blockers": 0,
        "min_component_percent": 20,
        "require_calibration": False,
        "require_semantic_review": False,
        "component_floor_is_blocker": False,
        "score_is_gate": False,
    },
    "standard": {
        "reference_score": 75,
        "max_blockers": 0,
        "min_component_percent": 50,
        "require_calibration": False,
        "require_semantic_review": False,
        "component_floor_is_blocker": False,
        "score_is_gate": False,
    },
    "full": {
        "reference_score": 85,
        "max_blockers": 0,
        "min_component_percent": 60,
        "require_calibration": True,
        "require_semantic_review": True,
        "component_floor_is_blocker": False,
        "score_is_gate": False,
    },
}

STATUS_PATTERN = re.compile(r"(?im)^\s*status\s*:\s*([a-zA-Z_-]+)\s*$")
ACCEPTED_REVIEW_STATUSES = {"passed", "accepted_with_risk", "not_required"}
ACCEPTED_CALIBRATION_STATUSES = {"calibrated", "reviewed", "accepted_with_risk"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def field(text: str, name: str) -> str | None:
    match = re.search(rf"(?im)^\s*{re.escape(name)}\s*:\s*(.+?)\s*$", text)
    return match.group(1).strip() if match else None


def status_of(path: Path) -> str | None:
    text = read_text(path)
    match = STATUS_PATTERN.search(text)
    return match.group(1).strip().lower() if match else None


def has_open_blockers(text: str, prefix: str) -> bool:
    return bool(re.search(rf"(?im)^\|\s*{prefix}\d+\s*\|.*\|\s*open\s*\|\s*$", text))


def is_placeholder_cell(cell: str, placeholder_values: set[str]) -> bool:
    normalized = cell.strip()
    if normalized in placeholder_values:
        return True
    if not normalized:
        return True
    if normalized.startswith("`") and normalized.endswith("`"):
        return True
    if normalized.lower() in {"pending", "draft", "open", "unconfirmed", "project owner", "must"}:
        return True
    if re.fullmatch(r"[A-Z]{1,4}\d{3,}", normalized):
        return True
    if re.fullmatch(r"(FP|FN|I|B)\d{3,}", normalized):
        return True
    if normalized.endswith(".md") or normalized.endswith(".json"):
        return True
    if "待补充" in normalized or "作为..." in normalized or "Given/When/Then" in normalized:
        return True
    if "/" in normalized and any(part.strip().lower() in {"low", "medium", "high", "prototype-only", "usable-with-known-risks", "release-ready"} for part in normalized.split("/")):
        return True
    return False


def contains_filled_table_row(text: str) -> bool:
    placeholder_values = {
        "",
        "\u7f16\u53f7", "\u6765\u6e90", "\u95ee\u9898", "\u5904\u7406\u72b6\u6001", "\u4fee\u590d\u4f4d\u7f6e",
        "\u9879\u76ee", "\u7ed3\u8bba", "\u8bc1\u636e\u4f4d\u7f6e", "\u98ce\u9669/\u52a8\u4f5c",
        "\u7ef4\u5ea6", "\u6863\u4f4d", "\u603b\u5206", "\u7b49\u7ea7", "\u786c\u963b\u585e\u6570", "\u4e3b\u8981\u98ce\u9669",
        "\u6837\u4f8b", "\u9884\u671f\u8bc4\u5206", "\u7406\u7531",
        "\u62bd\u67e5\u4eba", "\u6837\u672c", "\u4eba\u5de5\u7ed3\u8bba", "\u811a\u672c\u7ed3\u8bba",
        "\u5dee\u5f02", "\u540e\u7eed\u52a8\u4f5c", "\u65e5\u671f", "\u8c03\u6574", "\u4f9d\u636e",
        "\u9879\u76ee\u72b6\u6001", "\u9884\u671f\u7b49\u7ea7", "\u9884\u671f\u53ef\u4fe1\u5ea6", "\u590d\u6838\u4eba",
        "\u9700\u6c42", "\u7528\u6237/\u89d2\u8272", "\u4f18\u5148\u7ea7", "\u72b6\u6001",
        "\u7528\u6237\u6545\u4e8b", "\u9a8c\u6536\u6807\u51c6", "\u5931\u8d25\u8def\u5f84", "\u5bf9\u5e94\u529f\u80fd\u5305",
    }
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "---" in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        meaningful = [cell for cell in cells if not is_placeholder_cell(cell, placeholder_values)]
        if len(cells) >= 3 and meaningful:
            return True
    return False


def section_between(text: str, heading: str) -> str:
    match = re.search(rf"(?ms)^##\s+{re.escape(heading)}\s*$([\s\S]*?)(?=^##\s+|\Z)", text)
    return match.group(1) if match else ""


def has_unchecked_item(path: Path) -> bool:
    return bool(re.search(r"(?m)^- \[ \]", read_text(path)))


def score_file_status(root: Path, rel: str, accepted: set[str], full_points: int, partial_points: int = 1) -> tuple[int, list[str], list[str]]:
    path = root / rel
    if not path.exists():
        return 0, [f"missing {rel}"], []
    status = status_of(path)
    if status in accepted:
        return full_points, [], []
    if status == "draft":
        return partial_points, [], [f"{rel} is still draft"]
    return 0, [f"{rel} has invalid or missing status"], []


def component_result(name: str, score: int, max_score: int, blockers: list[str], warnings: list[str]) -> dict:
    score = max(0, min(score, max_score))
    return {
        "name": name,
        "score": score,
        "maxScore": max_score,
        "percent": round(score * 100 / max_score, 1) if max_score else 0,
        "blockers": blockers,
        "warnings": warnings,
    }


def profile_rules(profile: str) -> dict:
    return PROFILE_RULES.get(profile, PROFILE_RULES["standard"])


def score_intake(root: Path) -> dict:
    rel = "PROJECT_INTAKE.md"
    text = read_text(root / rel)
    score, blockers, warnings = score_file_status(root, rel, {"confirmed"}, WEIGHTS["intake"], 5)
    required_terms = ["\u9879\u76ee\u76ee\u6807", "\u7b2c\u4e00\u7248\u8303\u56f4", "AI \u4f7f\u7528\u8fb9\u754c", "\u9a8c\u6536", "\u963b\u585e\u95ee\u9898"]
    missing_terms = [term for term in required_terms if term not in text]
    score -= len(missing_terms) * 2
    warnings.extend([f"PROJECT_INTAKE.md missing section cue: {term}" for term in missing_terms])
    if has_open_blockers(text, "P"):
        blockers.append("PROJECT_INTAKE.md has open blocking questions")
    return component_result("intake", score, WEIGHTS["intake"], blockers, warnings)


def score_product(root: Path) -> dict:
    blockers: list[str] = []
    warnings: list[str] = []
    score = 0
    for rel in ("workbench/product/PRODUCT_BRIEF.md", "workbench/product/PRD.md", "workbench/product/ROADMAP.md"):
        part, part_blockers, part_warnings = score_file_status(root, rel, {"approved", "confirmed"}, 4, 1)
        score += part
        blockers.extend(part_blockers)
        warnings.extend(part_warnings)
    prd = read_text(root / "workbench/product/PRD.md")
    if contains_filled_table_row(prd):
        score += 3
    else:
        warnings.append("PRD.md has no filled requirement/story evidence")
    return component_result("product", score, WEIGHTS["product"], blockers, warnings)


def score_design(root: Path) -> dict:
    blockers: list[str] = []
    warnings: list[str] = []
    score = 0
    for rel in ("workbench/design/UX_SPEC.md", "workbench/design/PROTOTYPE.md", "workbench/design/USER_FLOW.md"):
        part, part_blockers, part_warnings = score_file_status(root, rel, {"approved", "confirmed"}, 3, 1)
        score += part
        blockers.extend(part_blockers)
        warnings.extend(part_warnings)
    ux = read_text(root / "workbench/design/UX_SPEC.md")
    if all(term in ux for term in ("\u5931\u8d25", "\u6743\u9650", "\u53ef\u8bbf\u95ee\u6027")):
        score += 1
    else:
        warnings.append("UX_SPEC.md should cover failure, permission, and accessibility states")
    return component_result("design", score, WEIGHTS["design"], blockers, warnings)


def score_architecture(root: Path) -> dict:
    blockers: list[str] = []
    warnings: list[str] = []
    score = 0
    for rel in (
        "workbench/architecture/ARCHITECTURE.md",
        "workbench/architecture/DATA_MODEL.md",
        "workbench/architecture/API_DESIGN.md",
        "workbench/architecture/AI_DESIGN.md",
    ):
        part, part_blockers, part_warnings = score_file_status(root, rel, {"approved", "confirmed"}, 3, 1)
        score += part
        blockers.extend(part_blockers)
        warnings.extend(part_warnings)
    arch = read_text(root / "workbench/architecture/ARCHITECTURE.md")
    if all(term in arch for term in ("\u8d28\u91cf\u5c5e\u6027", "\u98ce\u9669", "\u9a8c\u8bc1\u65b9\u5f0f")):
        score += 3
    else:
        warnings.append("ARCHITECTURE.md should include quality attributes, risks, and verification method")
    return component_result("architecture", score, WEIGHTS["architecture"], blockers, warnings)


def score_delivery(root: Path) -> dict:
    blockers: list[str] = []
    warnings: list[str] = []
    score = 0
    for rel in ("workbench/delivery/RELEASE_PLAN.md", "workbench/delivery/ITERATION_PLAN.md", "workbench/delivery/TASK_BREAKDOWN.md"):
        part, part_blockers, part_warnings = score_file_status(root, rel, {"approved", "confirmed", "active"}, 3, 1)
        score += part
        blockers.extend(part_blockers)
        warnings.extend(part_warnings)
    release = read_text(root / "workbench/delivery/RELEASE_PLAN.md")
    if "\u56de\u6eda" in release:
        score += 1
    else:
        warnings.append("RELEASE_PLAN.md should include rollback evidence")
    return component_result("delivery", score, WEIGHTS["delivery"], blockers, warnings)


def score_features(root: Path) -> dict:
    feature_root = root / "workbench" / "features"
    blockers: list[str] = []
    warnings: list[str] = []
    if not feature_root.exists():
        return component_result("features", 8, WEIGHTS["features"], blockers, ["No feature packages yet; acceptable before feature development"])
    packages = [item for item in sorted(feature_root.iterdir()) if item.is_dir()]
    if not packages:
        return component_result("features", 8, WEIGHTS["features"], blockers, ["workbench/features exists but has no feature package"])
    package_scores: list[int] = []
    for package in packages:
        rel_package = package.relative_to(root).as_posix()
        missing = [filename for filename in FEATURE_PACKAGE_FILES if not (package / filename).exists()]
        if missing:
            blockers.append(f"{rel_package} missing files: {', '.join(missing)}")
            package_scores.append(0)
            continue
        checklist = read_text(package / "CHECKLIST.md")
        feature_status = (field(checklist, "feature_status") or "active").lower()
        if feature_status == "on_hold":
            package_scores.append(12)
            continue
        if feature_status != "complete":
            warnings.append(f"{rel_package} is {feature_status}")
            package_scores.append(8)
            continue
        if not has_unchecked_item(package / "CHECKLIST.md") and not has_unchecked_item(package / "TASKS.md"):
            package_scores.append(20)
        else:
            blockers.append(f"{rel_package} complete but still has unchecked tasks or gates")
            package_scores.append(12)
    score = min(package_scores) if package_scores else 8
    return component_result("features", score, WEIGHTS["features"], blockers, warnings)


def score_verification(root: Path, called_from_quality_gate: bool) -> dict:
    blockers: list[str] = []
    warnings: list[str] = []
    marker = root / ".workbench-validation" / "quality-gate-ok.json"
    score = 0
    if marker.exists():
        score += 4
    elif called_from_quality_gate:
        warnings.append(".workbench-validation/quality-gate-ok.json is not expected yet because scorecard is running inside the current quality gate")
        score += 2
    else:
        warnings.append(".workbench-validation/quality-gate-ok.json is missing; treat this as historical gate evidence, not current proof")
    quality_gate = root / "workbench" / "quality" / "quality_gate.py"
    gate_text = read_text(quality_gate)
    if quality_gate.exists() and "run_scorecard" in gate_text and "--called-from-quality-gate" in gate_text:
        score += 6
    elif quality_gate.exists() and "run_scorecard" in gate_text:
        score += 4
        warnings.append("quality_gate.py calls scorecard.py but does not pass --called-from-quality-gate")
    else:
        blockers.append("quality_gate.py does not call scorecard.py for evidence reporting")
    return component_result("verification", score, WEIGHTS["verification"], blockers, warnings)


def score_feedback(root: Path) -> dict:
    blockers: list[str] = []
    warnings: list[str] = []
    score = 0
    for rel in ("workbench/feedback/FAILURE_LOG.md", "workbench/feedback/ITERATION_LOG.md", "workbench/feedback/AI_EFFECTIVENESS.md"):
        if (root / rel).exists():
            score += 1
        else:
            blockers.append(f"missing {rel}")
    effectiveness = read_text(root / "workbench/feedback/AI_EFFECTIVENESS.md")
    if "\u8fd4\u5de5" in effectiveness and "\u8d28\u91cf\u95e8" in effectiveness:
        score += 2
    else:
        warnings.append("AI_EFFECTIVENESS.md should track rework and quality-gate failures")
    return component_result("feedback", score, WEIGHTS["feedback"], blockers, warnings)


def score_calibration(root: Path) -> tuple[dict, list[str], list[str]]:
    path = root / "workbench" / "scorecard" / "CALIBRATION.md"
    scorecard_path = root / "workbench" / "scorecard" / "SCORECARD.md"
    text = read_text(path)
    scorecard = read_text(scorecard_path)
    blockers: list[str] = []
    warnings: list[str] = []
    status = (field(text, "calibration_status") or field(scorecard, "calibration_status") or "missing").lower()
    has_anchor_examples = contains_filled_table_row(section_between(text, "\u951a\u5b9a\u6837\u4f8b"))
    has_human_spotcheck = contains_filled_table_row(section_between(text, "\u4eba\u5de5\u62bd\u67e5"))
    has_false_positive_record = "\u8bef\u62a5" in text
    has_false_negative_record = "\u6f0f\u62a5" in text
    has_reference_line_change_log = "\u53c2\u8003\u7ebf\u8c03\u6574" in text
    has_threshold_change_log = has_reference_line_change_log or "\u9608\u503c\u8c03\u6574" in text
    if not path.exists():
        blockers.append("CALIBRATION.md is missing")
    if status == "missing":
        warnings.append("CALIBRATION.md missing calibration_status")
    elif status not in ACCEPTED_CALIBRATION_STATUSES:
        warnings.append(f"CALIBRATION.md calibration_status is {status}, not calibrated/reviewed/accepted_with_risk")
    if not has_anchor_examples:
        warnings.append("CALIBRATION.md has no filled anchor-example evidence")
    if not has_human_spotcheck:
        warnings.append("CALIBRATION.md has no filled human spot-check evidence")
    return {
        "status": status,
        "acceptedStatuses": sorted(ACCEPTED_CALIBRATION_STATUSES),
        "hasAnchorExamples": has_anchor_examples,
        "hasHumanSpotcheck": has_human_spotcheck,
        "tracksFalsePositives": has_false_positive_record,
        "tracksFalseNegatives": has_false_negative_record,
        "hasReferenceLineChangeLog": has_reference_line_change_log,
        "hasThresholdChangeLog": has_threshold_change_log,
        "isCalibrated": status in ACCEPTED_CALIBRATION_STATUSES and has_anchor_examples and has_human_spotcheck,
    }, blockers, warnings


def score_semantic_review(root: Path, require_semantic_review: bool) -> tuple[dict, list[str], list[str]]:
    scorecard = read_text(root / "workbench" / "scorecard" / "SCORECARD.md")
    blockers: list[str] = []
    warnings: list[str] = []
    semantic_status = (field(scorecard, "semantic_review_status") or "missing").lower()
    if semantic_status not in ACCEPTED_REVIEW_STATUSES:
        message = "SCORECARD.md semantic_review_status is not passed, accepted_with_risk, or not_required"
        if require_semantic_review:
            blockers.append(message)
        else:
            warnings.append(message)
    architecture_status = (field(scorecard, "architecture_review_status") or "missing").lower()
    if architecture_status not in ACCEPTED_REVIEW_STATUSES:
        message = "SCORECARD.md architecture_review_status is not passed, accepted_with_risk, or not_required"
        if require_semantic_review:
            blockers.append(message)
        else:
            warnings.append(message)
    if "\u786c\u963b\u585e" not in scorecard or "\u67b6\u6784\u5408\u7406\u6027" not in scorecard:
        blockers.append("SCORECARD.md is missing scorecard structure cues")
    return {
        "semanticReviewStatus": semantic_status,
        "architectureReviewStatus": architecture_status,
        "acceptedStatuses": sorted(ACCEPTED_REVIEW_STATUSES),
        "required": require_semantic_review,
    }, blockers, warnings


def component_floor_violations(components: list[dict], min_percent: int) -> list[dict]:
    return [
        {
            "component": component["name"],
            "percent": component["percent"],
            "minPercent": min_percent,
        }
        for component in components
        if component["percent"] < min_percent
    ]


def confidence_level(blockers: list[str], warnings: list[str], calibration: dict, semantic_review: dict, floor_violations: list[dict]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if blockers:
        reasons.append("Blockers exist; the score cannot be used as pass evidence.")
        return "low", reasons
    if floor_violations:
        reasons.append("A component floor violation may hide local risk behind a good total score.")
    if not calibration["isCalibrated"]:
        reasons.append("The scoring rubric has not been calibrated with anchor examples and human spot checks.")
    if semantic_review["semanticReviewStatus"] not in ACCEPTED_REVIEW_STATUSES:
        reasons.append("Semantic review is incomplete or failed.")
    if semantic_review["architectureReviewStatus"] not in ACCEPTED_REVIEW_STATUSES:
        reasons.append("Architecture review is incomplete or failed.")
    if len(warnings) >= 10:
        reasons.append("Too many warnings; manually review score confidence.")
    if not reasons:
        return "high", ["No obvious blockers, component floor gaps, calibration gaps, or semantic-review gaps."]
    if len(reasons) >= 3 or floor_violations:
        return "low", reasons
    return "medium", reasons


def calculate(root: Path, profile: str, called_from_quality_gate: bool = False) -> dict:
    rules = profile_rules(profile)
    components = [
        score_intake(root),
        score_product(root),
        score_design(root),
        score_architecture(root),
        score_delivery(root),
        score_features(root),
        score_verification(root, called_from_quality_gate),
        score_feedback(root),
    ]
    semantic_review, semantic_blockers, semantic_warnings = score_semantic_review(root, rules["require_semantic_review"])
    calibration, calibration_blockers, calibration_warnings = score_calibration(root)
    total = sum(component["score"] for component in components)
    max_total = sum(component["maxScore"] for component in components)
    floor_violations = component_floor_violations(components, rules["min_component_percent"])
    blockers = semantic_blockers[:] + calibration_blockers[:]
    warnings = semantic_warnings[:] + calibration_warnings[:]
    for component in components:
        blockers.extend(component["blockers"])
        warnings.extend(component["warnings"])
    if rules["require_calibration"] and not calibration["isCalibrated"]:
        blockers.append("full profile requires calibrated scorecard evidence in CALIBRATION.md")
    for violation in floor_violations:
        message = f"{violation['component']} component {violation['percent']}% is below {violation['minPercent']}% floor for {profile}"
        if rules["component_floor_is_blocker"]:
            blockers.append(message)
        else:
            warnings.append(message)
    percentage = round(total * 100 / max_total, 1) if max_total else 0
    confidence, confidence_reasons = confidence_level(blockers, warnings, calibration, semantic_review, floor_violations)
    if blockers:
        level = "blocked"
    elif percentage >= 90:
        level = "release-ready"
    elif percentage >= 75:
        level = "usable-with-known-risks"
    elif percentage >= 60:
        level = "prototype-only"
    else:
        level = "not-ready"
    if blockers:
        decision = "BLOCKED"
    elif confidence == "high":
        decision = "PASS"
    else:
        decision = "PASS_WITH_RISK"
    return {
        "schema": "codex-workbench-scorecard/v1",
        "timestamp": utc_now(),
        "projectRoot": str(root),
        "profile": profile,
        "calledFromQualityGate": called_from_quality_gate,
        "profileRules": rules,
        "scoreMeaning": "evidence_maturity_and_process_consistency_only",
        "decision": decision,
        "decisionMeaning": "BLOCKED blocks delivery; PASS_WITH_RISK requires human review of warnings, confidence, calibration, and semantic review before treating the work as done.",
        "totalScore": total,
        "maxScore": max_total,
        "percentage": percentage,
        "level": level,
        "confidence": confidence,
        "confidenceReasons": confidence_reasons,
        "calibration": calibration,
        "semanticReview": semantic_review,
        "componentFloorViolations": floor_violations,
        "components": components,
        "blockers": blockers,
        "warnings": warnings,
        "limitations": [
            "Scorecard does not prove product correctness, architecture suitability, security/privacy acceptance, or AI eval quality.",
            "High scores must not override blockers, low confidence, missing calibration, missing semantic review, or failed quality gates.",
            "Reference scores and component floors are triage signals, not release gates by themselves.",
            "Treat score changes as signals for review and improvement, not as a target to game.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["smoke", "standard", "full"], default="standard")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--called-from-quality-gate", action="store_true")
    parser.add_argument("--enforce-blockers", action="store_true", help="Return non-zero only for hard blockers, not for low evidence score.")
    args = parser.parse_args()
    root = project_root()
    report = calculate(root, args.profile, args.called_from_quality_gate)
    rules = profile_rules(args.profile)
    report["referenceRules"] = rules
    if args.write_report:
        out_dir = root / ".workbench-validation"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "scorecard-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "decision": report["decision"],
        "score": report["totalScore"],
        "maxScore": report["maxScore"],
        "percentage": report["percentage"],
        "level": report["level"],
        "confidence": report["confidence"],
        "blockers": len(report["blockers"]),
        "warnings": len(report["warnings"]),
        "componentFloorViolations": len(report["componentFloorViolations"]),
        "calibrationStatus": report["calibration"]["status"],
    }, ensure_ascii=False))
    if args.enforce_blockers and len(report["blockers"]) > rules["max_blockers"]:
        print("[scorecard] blockers exist", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''
    return script.replace("__FEATURE_PACKAGE_FILES__", feature_files_json).replace("__REQUIRED_ADAPTER_FILES__", required_adapter_files_json)


def generate_py_wrapper(script_name: str) -> str:
    return f'''param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$Args
)

$ErrorActionPreference = "Stop"
$script = Join-Path $PSScriptRoot "{script_name}"

$python = Get-Command py -ErrorAction SilentlyContinue
if ($python) {{
  & $python.Source $script @Args
  exit $LASTEXITCODE
}}

$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {{
  & $python.Source $script @Args
  exit $LASTEXITCODE
}}

$python = Get-Command python3 -ErrorAction SilentlyContinue
if ($python) {{
  & $python.Source $script @Args
  exit $LASTEXITCODE
}}

throw "Python was not found. Install Python 3 and retry."
'''


def generate_sh_wrapper(script_name: str) -> str:
    return f'''#!/usr/bin/env sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$SCRIPT_DIR/{script_name}" "$@"
fi
if command -v python >/dev/null 2>&1; then
  exec python "$SCRIPT_DIR/{script_name}" "$@"
fi
echo "Python 3 was not found. Install Python 3 and retry." >&2
exit 127
'''


def generate_runtime_gate_py() -> str:
    return '''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import urllib.request


def check_url(url: str, name: str) -> None:
    with urllib.request.urlopen(url, timeout=10) as response:
        status = getattr(response, "status", 200)
        if status >= 400:
            raise SystemExit(f"[runtime] {name} returned HTTP {status}: {url}")
        print(f"[runtime] {name} ok: HTTP {status} {url}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Run checks. Without this flag, print the plan only.")
    parser.add_argument("--frontend-url", default="")
    parser.add_argument("--backend-health-url", default="")
    args = parser.parse_args()

    print("[runtime] dry-run by default. Pass --apply to run URL smoke checks.")
    if not args.apply:
        if args.frontend_url:
            print(f"[runtime] planned frontend check: {args.frontend_url}")
        if args.backend_health_url:
            print(f"[runtime] planned backend health check: {args.backend_health_url}")
        if not args.frontend_url and not args.backend_health_url:
            print("[runtime] no URLs configured. Provide --frontend-url or --backend-health-url.")
        return 0

    if args.frontend_url:
        check_url(args.frontend_url, "frontend")
    if args.backend_health_url:
        check_url(args.backend_health_url, "backend")
    if not args.frontend_url and not args.backend_health_url:
        raise SystemExit("[runtime] no URL checks were provided.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def generate_api_smoke_py() -> str:
    return '''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import urllib.request


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Health or smoke URL to request.")
    args = parser.parse_args()
    with urllib.request.urlopen(args.url, timeout=10) as response:
        status = getattr(response, "status", 200)
        if status >= 400:
            raise SystemExit(f"[smoke] HTTP {status}: {args.url}")
        print(f"[smoke] ok: HTTP {status} {args.url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def generate_review_prompt(project_name: str) -> str:
    return f"""# 独立审查提示

你是 {project_name} 仓库的独立审查者。只做审查，不编辑文件。

先读取：

- `AGENTS.md`
- `WORKBENCH.md`
- `REVIEW.md`
- `PROJECT_INTAKE.md`
- `PRODUCT_BASELINE.md`
- `FEATURE_WORKFLOW.md`

然后按本次改动影响面继续读取：

- 产品或验收变化：`workbench/product/PRODUCT_BRIEF.md`、`workbench/product/PRD.md`、`workbench/product/ROADMAP.md`
- 用户可见流程或 UI 变化：`workbench/design/UX_SPEC.md`、`PROTOTYPE.md`、`USER_FLOW.md`
- 模块、数据、API、AI 工具或权限变化：`workbench/architecture/`
- 当前功能包：`workbench/features/<feature-name>/SPEC.md`、`CLARIFY.md`、`DESIGN.md`、`PLAN.md`、`TASKS.md`、`VERIFY.md`、`REVIEW.md`
- 质量和证据审计：`.workbench-validation/`、`workbench/scorecard/SCORECARD.md`、`workbench/scorecard/CALIBRATION.md`

然后检查当前 diff 或用户明确指定的文件。

审查重点：

- 行为是否满足 `PROJECT_INTAKE.md`、PRD、功能 `SPEC.md` 和验收标准。
- 权限、数据所有权、租户/组织/用户/课程/文件等边界是否被破坏。
- API、数据库、前后端契约和外部服务调用是否兼容。
- 测试和质量门是否足以证明改动正确。
- `scorecard` 是否只被当作证据审计，而不是被误用成质量裁判。
- 是否存在 AI 生成代码常见问题：虚构 API、绕过既有封装、缺少错误处理、只改实现不改验证。
- 是否出现重复失败、审查漏报或质量门缺口，应该沉淀到模板、测试、CI、hook、质量门或 review 规则。

输出 findings 优先，按 `P0/P1/P2/Nit` 排序。每条包含文件路径、行号、风险、触发场景和修复方向。

最后补充：

- 未发现 P0/P1 问题时，明确写“未发现 P0/P1 问题”。
- 列出验证缺口和仍需人工确认的业务/产品/架构判断。
- 给出 `workbench_upgrade_assessment` 建议：`not_required`、`failure_log_updated`、`template_update_needed`、`quality_gate_update_needed`、`review_rule_update_needed`、`ci_or_hook_needed` 或 `deferred_with_reason`。
"""


def backup_target(path: Path) -> None:
    if not path.exists():
        return
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.name}.bak-{stamp}")
    if path.is_dir():
        shutil.copytree(path, backup)
    else:
        shutil.copy2(path, backup)


def write_file(path: Path, content: str, force: bool, dry_run: bool) -> str:
    if path.exists() and not force:
        return "skipped-existing"
    if dry_run:
        return "would-write"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and force:
        backup_target(path)
    path.write_text(content, encoding="utf-8", newline="\n")
    if path.suffix == ".sh":
        try:
            path.chmod(path.stat().st_mode | 0o111)
        except OSError:
            pass
    return "written"


def default_codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.home() / ".codex").resolve()


def user_workbench_template_files() -> dict[str, str]:
    template_dir = skill_root() / "assets" / "user-workbench-template"
    files: dict[str, str] = {}
    for filename in USER_WORKBENCH_FILES:
        path = template_dir / filename
        if not path.exists():
            raise SystemExit(f"Missing user workbench template file: {path}")
        files[filename] = path.read_text(encoding="utf-8")
    return files


def install_user_workbench(codex_home: str | None, apply: bool, force: bool) -> dict[str, Any]:
    target_root = Path(codex_home).expanduser().resolve() if codex_home else default_codex_home()
    files = user_workbench_template_files()
    actions: dict[str, dict[str, str]] = {}
    for rel, content in files.items():
        target = target_root / rel
        if target.exists() and not force:
            action = "keep-existing"
        elif target.exists() and force:
            action = "replace-existing"
        else:
            action = "write-missing"
        status = write_file(target, content, force=force, dry_run=not apply)
        actions[rel] = {
            "action": action,
            "status": status,
        }
    return {
        "schema": "codex-workbench-user-workbench/v1",
        "timestamp": utc_now(),
        "codexHome": str(target_root),
        "apply": apply,
        "force": force,
        "files": actions,
        "notes": [
            "This command installs only generic user workbench templates.",
            "It does not configure credentials, MCP servers, hook trust, approval state, or project-specific commands.",
            "Without --apply it is a preview only.",
        ],
    }


def build_adapter_files(name: str, inspection: dict[str, Any]) -> dict[str, str]:
    variables = template_variables(name, inspection)
    return {
        "AGENTS.md": render_template("AGENTS.md", variables, generate_agents_md(name, inspection)),
        "PROJECT_INTAKE.md": render_template("PROJECT_INTAKE.md", variables, ""),
        "WORKBENCH.md": render_template("WORKBENCH.md", variables, generate_workbench_md(name, inspection)),
        "REVIEW.md": render_template("REVIEW.md", variables, generate_review_md(name)),
        "DEVELOPMENT_FLOW.md": render_template("DEVELOPMENT_FLOW.md", variables, generate_development_flow_md(name, inspection)),
        "PRODUCT_BASELINE.md": render_template("PRODUCT_BASELINE.md", variables, ""),
        "FEATURE_WORKFLOW.md": render_template("FEATURE_WORKFLOW.md", variables, ""),
        "workbench/product/PRODUCT_BRIEF.md": render_template("workbench/product/PRODUCT_BRIEF.md", variables, ""),
        "workbench/product/PRD.md": render_template("workbench/product/PRD.md", variables, ""),
        "workbench/product/ROADMAP.md": render_template("workbench/product/ROADMAP.md", variables, ""),
        "workbench/design/UX_SPEC.md": render_template("workbench/design/UX_SPEC.md", variables, ""),
        "workbench/design/PROTOTYPE.md": render_template("workbench/design/PROTOTYPE.md", variables, ""),
        "workbench/design/USER_FLOW.md": render_template("workbench/design/USER_FLOW.md", variables, ""),
        "workbench/architecture/ARCHITECTURE.md": render_template("workbench/architecture/ARCHITECTURE.md", variables, ""),
        "workbench/architecture/DATA_MODEL.md": render_template("workbench/architecture/DATA_MODEL.md", variables, ""),
        "workbench/architecture/API_DESIGN.md": render_template("workbench/architecture/API_DESIGN.md", variables, ""),
        "workbench/architecture/AI_DESIGN.md": render_template("workbench/architecture/AI_DESIGN.md", variables, ""),
        "workbench/architecture/adr/README.md": render_template("workbench/architecture/adr/README.md", variables, ""),
        "workbench/delivery/RELEASE_PLAN.md": render_template("workbench/delivery/RELEASE_PLAN.md", variables, ""),
        "workbench/delivery/ITERATION_PLAN.md": render_template("workbench/delivery/ITERATION_PLAN.md", variables, ""),
        "workbench/delivery/TASK_BREAKDOWN.md": render_template("workbench/delivery/TASK_BREAKDOWN.md", variables, ""),
        "workbench/scorecard/RUBRIC.md": render_template("workbench/scorecard/RUBRIC.md", variables, ""),
        "workbench/scorecard/SCORECARD.md": render_template("workbench/scorecard/SCORECARD.md", variables, ""),
        "workbench/scorecard/CALIBRATION.md": render_template("workbench/scorecard/CALIBRATION.md", variables, ""),
        "workbench/scorecard/scorecard.py": generate_scorecard_py(),
        "workbench/scorecard/scorecard.ps1": generate_py_wrapper("scorecard.py"),
        "workbench/scorecard/scorecard.sh": generate_sh_wrapper("scorecard.py"),
        "workbench/quality/quality_gate.py": generate_quality_gate_py(inspection["qualityCommands"]),
        "workbench/quality/quality-gate.ps1": generate_py_wrapper("quality_gate.py"),
        "workbench/quality/quality-gate.sh": generate_sh_wrapper("quality_gate.py"),
        "workbench/runtime/runtime_gate.py": generate_runtime_gate_py(),
        "workbench/runtime/runtime-gate.ps1": generate_py_wrapper("runtime_gate.py"),
        "workbench/runtime/runtime-gate.sh": generate_sh_wrapper("runtime_gate.py"),
        "workbench/runtime/api_smoke.py": generate_api_smoke_py(),
        "workbench/runtime/api-smoke.ps1": generate_py_wrapper("api_smoke.py"),
        "workbench/runtime/api-smoke.sh": generate_sh_wrapper("api_smoke.py"),
        "workbench/feedback/FAILURE_LOG.md": render_template("workbench/feedback/FAILURE_LOG.md", variables, ""),
        "workbench/feedback/ITERATION_LOG.md": render_template("workbench/feedback/ITERATION_LOG.md", variables, ""),
        "workbench/feedback/AI_EFFECTIVENESS.md": render_template("workbench/feedback/AI_EFFECTIVENESS.md", variables, ""),
        "workbench/review/independent-review-prompt.md": render_template(
            "workbench/review/independent-review-prompt.md",
            variables,
            generate_review_prompt(name),
        ),
        "workbench/feature-template/SPEC.md": render_template("workbench/feature-template/SPEC.md", variables, ""),
        "workbench/feature-template/CLARIFY.md": render_template("workbench/feature-template/CLARIFY.md", variables, ""),
        "workbench/feature-template/DESIGN.md": render_template("workbench/feature-template/DESIGN.md", variables, ""),
        "workbench/feature-template/PLAN.md": render_template("workbench/feature-template/PLAN.md", variables, ""),
        "workbench/feature-template/TASKS.md": render_template("workbench/feature-template/TASKS.md", variables, ""),
        "workbench/feature-template/DECISIONS.md": render_template("workbench/feature-template/DECISIONS.md", variables, ""),
        "workbench/feature-template/IMPLEMENTATION_NOTES.md": render_template("workbench/feature-template/IMPLEMENTATION_NOTES.md", variables, ""),
        "workbench/feature-template/CHECKLIST.md": render_template("workbench/feature-template/CHECKLIST.md", variables, ""),
        "workbench/feature-template/VERIFY.md": render_template("workbench/feature-template/VERIFY.md", variables, ""),
        "workbench/feature-template/REVIEW.md": render_template("workbench/feature-template/REVIEW.md", variables, ""),
        "workbench/feature-template/CHANGELOG.md": render_template("workbench/feature-template/CHANGELOG.md", variables, ""),
    }


def generate_adapter(project: Path, name: str, force: bool, dry_run: bool) -> dict[str, Any]:
    inspection = inspect_project(project)
    files = build_adapter_files(name, inspection)
    results: dict[str, str] = {}
    for rel, content in files.items():
        results[rel] = write_file(project / rel, content, force=force, dry_run=dry_run)

    report = {
        "schema": "codex-workbench-adapter-report/v1",
        "timestamp": utc_now(),
        "projectRoot": str(project),
        "projectName": name,
        "dryRun": dry_run,
        "files": results,
        "inspection": inspection,
    }
    if not dry_run:
        marker_dir = project / ".workbench-validation"
        marker_dir.mkdir(parents=True, exist_ok=True)
        (marker_dir / "workbench-adapter-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return report


def upgrade_action_for(rel: str, path: Path, replace_docs: bool, refresh_generated: bool) -> str:
    if not path.exists():
        return "write-missing"
    if rel in {"AGENTS.md", "PROJECT_INTAKE.md", "WORKBENCH.md", "REVIEW.md", "DEVELOPMENT_FLOW.md", "PRODUCT_BASELINE.md", "FEATURE_WORKFLOW.md"}:
        return "replace-doc" if replace_docs else "keep-existing-doc"
    if rel.startswith("workbench/"):
        return "refresh-generated" if refresh_generated else "keep-existing-generated"
    return "keep-existing"


def upgrade_adapter(
    project: Path,
    name: str,
    dry_run: bool,
    replace_docs: bool,
    refresh_generated: bool,
) -> dict[str, Any]:
    inspection = inspect_project(project)
    files = build_adapter_files(name, inspection)
    actions: dict[str, dict[str, str]] = {}
    for rel, content in files.items():
        target = project / rel
        action = upgrade_action_for(rel, target, replace_docs, refresh_generated)
        status = "skipped"
        if action in {"write-missing", "replace-doc", "refresh-generated"}:
            status = write_file(target, content, force=True, dry_run=dry_run)
        actions[rel] = {
            "action": action,
            "status": status,
        }

    report = {
        "schema": "codex-workbench-upgrade-report/v1",
        "timestamp": utc_now(),
        "projectRoot": str(project),
        "projectName": name,
        "dryRun": dry_run,
        "replaceDocs": replace_docs,
        "refreshGenerated": refresh_generated,
        "files": actions,
        "inspection": inspection,
    }
    if not dry_run:
        marker_dir = project / REPORT_DIR
        marker_dir.mkdir(parents=True, exist_ok=True)
        (marker_dir / "workbench-upgrade-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return report


def slugify_feature_name(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", name.strip().lower()).strip("-._")
    if not slug:
        raise SystemExit("Feature name must contain at least one letter or number.")
    return slug


def feature_action_for(rel: str, path: Path, force: bool) -> str:
    if not path.exists():
        return "write-missing"
    return "replace-existing" if force else "keep-existing"


def create_feature_package(project: Path, name: str, dry_run: bool, force: bool) -> dict[str, Any]:
    inspection = inspect_project(project)
    variables = template_variables(project.name, inspection)
    slug = slugify_feature_name(name)
    target_root = project / "workbench" / "features" / slug
    actions: dict[str, dict[str, str]] = {}
    for filename in FEATURE_PACKAGE_FILES:
        rel_template = f"workbench/feature-template/{filename}"
        rel_target = f"workbench/features/{slug}/{filename}"
        content = render_template(rel_template, variables, "")
        if filename == "SPEC.md":
            content = content.replace("待填写。", name, 1)
        target = project / rel_target
        action = feature_action_for(rel_target, target, force)
        status = "skipped"
        if action in {"write-missing", "replace-existing"}:
            status = write_file(target, content, force=force, dry_run=dry_run)
        actions[rel_target] = {"action": action, "status": status}

    report = {
        "schema": "codex-workbench-feature-package/v1",
        "timestamp": utc_now(),
        "projectRoot": str(project),
        "featureName": name,
        "featureSlug": slug,
        "featureRoot": rel_to(project, target_root),
        "dryRun": dry_run,
        "force": force,
        "files": actions,
    }
    if not dry_run:
        marker_dir = project / REPORT_DIR
        marker_dir.mkdir(parents=True, exist_ok=True)
        (marker_dir / f"feature-{slug}-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return report


def validate_adapter(project: Path) -> dict[str, Any]:
    missing: list[str] = []
    placeholders: list[str] = []
    python_errors: list[str] = []
    feature_errors: list[str] = []
    intake_status: str | None = None
    intake_status_error: str | None = None
    process_status: str | None = None
    process_status_error: str | None = None
    for rel in REQUIRED_ADAPTER_FILES:
        path = project / rel
        if not path.exists():
            missing.append(rel)
            continue
        if path.suffix in {".md", ".py", ".ps1", ".sh"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            if "{{" in text or "}}" in text:
                placeholders.append(rel)
            if rel == "DEVELOPMENT_FLOW.md":
                match = re.search(r"(?im)^\s*status\s*:\s*([a-zA-Z_-]+)\s*$", text)
                if match:
                    process_status = match.group(1).strip().lower()
                    if process_status not in PROCESS_STATUSES:
                        process_status_error = f"DEVELOPMENT_FLOW.md: invalid status '{process_status}'"
                else:
                    process_status_error = "DEVELOPMENT_FLOW.md: missing status field"
            if rel == "PROJECT_INTAKE.md":
                match = re.search(r"(?im)^\s*status\s*:\s*([a-zA-Z_-]+)\s*$", text)
                if match:
                    intake_status = match.group(1).strip().lower()
                    if intake_status not in INTAKE_STATUSES:
                        intake_status_error = f"PROJECT_INTAKE.md: invalid status '{intake_status}'"
                else:
                    intake_status_error = "PROJECT_INTAKE.md: missing status field"
        if path.suffix == ".py":
            try:
                py_compile.compile(str(path), doraise=True)
            except py_compile.PyCompileError as exc:
                python_errors.append(f"{rel}: {exc.msg}")
    feature_dir = project / "workbench" / "features"
    if feature_dir.exists():
        for package in sorted(item for item in feature_dir.iterdir() if item.is_dir()):
            for filename in FEATURE_PACKAGE_FILES:
                if not (package / filename).exists():
                    feature_errors.append(f"{rel_to(project, package)}: missing {filename}")
            if all((package / filename).exists() for filename in FEATURE_PACKAGE_FILES):
                state = feature_package_state(package)
                for error in feature_state_errors(state):
                    feature_errors.append(f"{rel_to(project, package)}: {error}")
    report = {
        "schema": "codex-workbench-validation/v1",
        "timestamp": utc_now(),
        "projectRoot": str(project),
        "missing": missing,
        "placeholders": placeholders,
        "pythonErrors": python_errors,
        "featureErrors": feature_errors,
        "intakeStatus": intake_status,
        "intakeStatusError": intake_status_error,
        "processStatus": process_status,
        "processStatusError": process_status_error,
        "passed": not missing and not placeholders and not python_errors and not feature_errors and not intake_status_error and not process_status_error,
    }
    return report


def file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def retention_action(action: str, rel: str, reason: str, target: str | None = None, size: int | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {"action": action, "path": rel, "reason": reason}
    if target:
        item["target"] = target
    if size is not None:
        item["sizeBytes"] = size
    return item


def archive_target_for_report(project: Path, report: Path) -> Path:
    try:
        stamp = datetime.fromtimestamp(report.stat().st_mtime, timezone.utc)
    except OSError:
        stamp = datetime.now(timezone.utc)
    return project / ARCHIVE_DIR / "validation" / stamp.strftime("%Y-%m") / report.name


def unique_archive_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    index = 2
    while True:
        candidate = parent / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def project_feature_packages(project: Path) -> list[Path]:
    feature_dir = project / "workbench" / "features"
    if not feature_dir.exists():
        return []
    return sorted(item for item in feature_dir.iterdir() if item.is_dir())


def build_retention_plan(project: Path, keep_reports: int = DEFAULT_RETENTION_KEEP_REPORTS) -> dict[str, Any]:
    actions: list[dict[str, Any]] = []
    report_dir = project / REPORT_DIR
    if report_dir.exists():
        reports = sorted(
            (item for item in report_dir.iterdir() if item.is_file()),
            key=lambda item: item.stat().st_mtime if item.exists() else 0,
            reverse=True,
        )
        for index, report in enumerate(reports):
            rel = rel_to(project, report)
            if index < keep_reports:
                actions.append(retention_action("keep-latest-report", rel, f"Keep the newest {keep_reports} machine-generated validation reports.", size=file_size(report)))
                continue
            target = unique_archive_path(archive_target_for_report(project, report))
            actions.append(
                retention_action(
                    "archive-report",
                    rel,
                    "Machine-generated reports should not accumulate in .workbench-validation; archive older reports instead of deleting evidence.",
                    rel_to(project, target),
                    file_size(report),
                )
            )
    else:
        actions.append(retention_action("no-op", REPORT_DIR, "No generated validation report directory exists."))

    maintenance_files = [
        project / "docs" / "maintenance" / "IMPROVEMENT_LOG.md",
        project / "docs" / "maintenance" / "FAILURE_PATTERNS.md",
        project / "workbench" / "feedback" / "FAILURE_LOG.md",
        project / "workbench" / "feedback" / "ITERATION_LOG.md",
        project / "workbench" / "feedback" / "AI_EFFECTIVENESS.md",
    ]
    for path in maintenance_files:
        if not path.exists():
            continue
        size = file_size(path)
        rel = rel_to(project, path)
        if size >= MAINTENANCE_LOG_ARCHIVE_BYTES:
            actions.append(
                retention_action(
                    "recommend-manual-archive",
                    rel,
                    "Long-lived human evidence is too large. Keep an index/current section here and move older versioned records to an archive file or ADR after review.",
                    size=size,
                )
            )
        elif size >= MAINTENANCE_LOG_WARN_BYTES:
            actions.append(
                retention_action(
                    "warn-growing-log",
                    rel,
                    "Human-maintained evidence is growing. Review whether old entries should become an archive file, ADR, or failure-pattern summary.",
                    size=size,
                )
            )
        else:
            actions.append(retention_action("keep-human-evidence", rel, "Human-maintained evidence is within the current size budget.", size=size))

    for package in project_feature_packages(project):
        state = feature_package_state(package) if all((package / filename).exists() for filename in FEATURE_PACKAGE_FILES) else {}
        rel = rel_to(project, package)
        if state.get("featureStatus") == "complete":
            actions.append(
                retention_action(
                    "recommend-feature-archive",
                    rel,
                    "Completed feature evidence may be moved to workbench/archive/features only after release notes and downstream references are updated.",
                )
            )
        elif state:
            actions.append(retention_action("keep-active-feature", rel, "Active or on-hold feature evidence stays in workbench/features."))

    return {
        "schema": "codex-workbench-retention/v1",
        "timestamp": utc_now(),
        "projectRoot": str(project),
        "mode": "preview",
        "policy": {
            "keepLatestValidationReports": keep_reports,
            "machineReports": ".workbench-validation keeps only current generated reports; older reports are archived, not deleted.",
            "humanEvidence": "Maintenance logs, failure logs, and ADRs are reviewed and split manually; the retention command does not rewrite them.",
            "featureEvidence": "Feature packages remain the source evidence. Completed packages can be archived only after references and release notes are updated.",
        },
        "actions": actions,
    }


def apply_retention_plan(project: Path, report: dict[str, Any]) -> dict[str, Any]:
    applied: list[dict[str, Any]] = []
    for action in report["actions"]:
        if action["action"] != "archive-report":
            applied.append({**action, "status": "skipped"})
            continue
        source = project / action["path"]
        target = project / action["target"]
        if not source.exists():
            applied.append({**action, "status": "missing-source"})
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        final_target = unique_archive_path(target)
        shutil.move(str(source), str(final_target))
        applied.append({**action, "target": rel_to(project, final_target), "status": "archived"})
    report = {**report, "mode": "applied", "applied": applied}
    return report


def retention_report(project: Path, keep_reports: int = DEFAULT_RETENTION_KEEP_REPORTS, apply: bool = False, write_report: bool = False) -> dict[str, Any]:
    if keep_reports < 1:
        raise SystemExit("--keep-reports must be at least 1.")
    report = build_retention_plan(project, keep_reports)
    if apply:
        report = apply_retention_plan(project, report)
    if write_report:
        report_dir = project / REPORT_DIR
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "retention-report.json"
        report["reportPath"] = str(report_path)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def issue(severity: str, code: str, message: str, path: str | None = None) -> dict[str, str]:
    item = {"severity": severity, "code": code, "message": message}
    if path:
        item["path"] = path
    return item


def read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def frontmatter_field(text: str, name: str) -> str | None:
    match = re.search(rf"(?im)^\s*{re.escape(name)}\s*:\s*(.+?)\s*$", text)
    return match.group(1).strip() if match else None


def frontmatter_bool(text: str, name: str) -> bool:
    return (frontmatter_field(text, name) or "").lower() == "true"


def frontmatter_int(text: str, name: str) -> int | None:
    value = frontmatter_field(text, name)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def is_placeholder_value(value: str | None) -> bool:
    return value is None or value.strip().lower() in {"", "unclassified", "待填写", "todo", "tbd"}


def feature_package_state(package: Path) -> dict[str, Any]:
    texts = {filename: read_text_safe(package / filename) for filename in FEATURE_PACKAGE_FILES}
    checklist = texts.get("CHECKLIST.md", "")
    spec = texts.get("SPEC.md", "")
    return {
        "featureStatus": (frontmatter_field(checklist, "feature_status") or "active").lower(),
        "currentStage": (frontmatter_field(checklist, "current_stage") or "unknown").lower(),
        "riskLevel": (frontmatter_field(spec, "risk_level") or "unclassified").lower(),
        "impactScore": frontmatter_int(spec, "impact_score"),
        "uncertaintyScore": frontmatter_int(spec, "uncertainty_score"),
        "rollbackScore": frontmatter_int(spec, "rollback_score"),
        "riskScore": frontmatter_int(spec, "risk_score"),
        "hardTriggers": frontmatter_field(spec, "hard_triggers"),
        "classificationReason": frontmatter_field(spec, "classification_reason"),
        "specStatus": (frontmatter_field(spec, "status") or "draft").lower(),
        "clarifyStatus": (frontmatter_field(texts.get("CLARIFY.md", ""), "status") or "blocked").lower(),
        "designStatus": (frontmatter_field(texts.get("DESIGN.md", ""), "status") or "draft").lower(),
        "planStatus": (frontmatter_field(texts.get("PLAN.md", ""), "status") or "draft").lower(),
        "tasksStatus": (frontmatter_field(texts.get("TASKS.md", ""), "status") or "draft").lower(),
        "implementationAllowed": frontmatter_bool(checklist, "implementation_allowed"),
        "deliveryAllowed": frontmatter_bool(checklist, "delivery_allowed"),
        "specApprovedForPlan": frontmatter_bool(texts.get("SPEC.md", ""), "approved_for_plan"),
        "clarifyReadyForPlan": frontmatter_bool(texts.get("CLARIFY.md", ""), "ready_for_plan"),
        "designApprovedForPlan": frontmatter_bool(texts.get("DESIGN.md", ""), "approved_for_plan"),
        "planApprovedForTasks": frontmatter_bool(texts.get("PLAN.md", ""), "approved_for_tasks"),
        "planApprovedForImplementation": frontmatter_bool(texts.get("PLAN.md", ""), "approved_for_implementation"),
        "tasksReadyForImplementation": frontmatter_bool(texts.get("TASKS.md", ""), "ready_for_implementation"),
        "verifyStatus": (frontmatter_field(texts.get("VERIFY.md", ""), "status") or "missing").lower(),
        "reviewStatus": (frontmatter_field(texts.get("REVIEW.md", ""), "status") or "pending").lower(),
        "workbenchUpgradeAssessment": (frontmatter_field(texts.get("REVIEW.md", ""), "workbench_upgrade_assessment") or "unassessed").lower(),
        "hasOpenClarification": bool(re.search(r"(?im)^\|\s*C\d+\s*\|.*\|\s*open\s*\|\s*$", texts.get("CLARIFY.md", ""))),
        "verifyEmpty": "|  |  |  |" in texts.get("VERIFY.md", "") and "- [ ] 可以交付。" in texts.get("VERIFY.md", ""),
        "hasUncheckedChecklist": bool(re.search(r"(?m)^- \[ \]", checklist)),
        "hasUncheckedTasks": bool(re.search(r"(?m)^- \[ \]", texts.get("TASKS.md", ""))),
    }


def feature_stage_index(stage: str) -> int:
    try:
        return FEATURE_STAGE_ORDER.index(stage)
    except ValueError:
        return -1


def feature_stage_reached(state: dict[str, Any], stage: str) -> bool:
    current = feature_stage_index(state["currentStage"])
    expected = feature_stage_index(stage)
    return current >= expected and expected >= 0


def feature_state_errors(state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if state["featureStatus"] not in FEATURE_STATUSES:
        errors.append(f"invalid feature_status '{state['featureStatus']}'")
    if state["currentStage"] not in FEATURE_STAGES:
        errors.append(f"invalid current_stage '{state['currentStage']}'")
    if state["featureStatus"] == "on_hold":
        return errors
    if state["riskLevel"] not in RISK_LEVELS:
        errors.append(f"invalid risk_level '{state['riskLevel']}'")
    for key, label in (
        ("impactScore", "impact_score"),
        ("uncertaintyScore", "uncertainty_score"),
        ("rollbackScore", "rollback_score"),
    ):
        if state[key] is None or state[key] < 0 or state[key] > 3:
            errors.append(f"invalid {label} '{state[key]}'")
    if state["riskScore"] is None or state["riskScore"] < 0 or state["riskScore"] > 9:
        errors.append(f"invalid risk_score '{state['riskScore']}'")
    if is_placeholder_value(state["hardTriggers"]):
        errors.append("hard_triggers is not classified")
    if is_placeholder_value(state["classificationReason"]):
        errors.append("classification_reason is not classified")
    component_scores = [state["impactScore"], state["uncertaintyScore"], state["rollbackScore"]]
    if all(score is not None for score in component_scores) and state["riskScore"] is not None:
        expected_score = sum(component_scores)
        if state["riskScore"] != expected_score:
            errors.append(f"risk_score should equal impact_score + uncertainty_score + rollback_score ({expected_score})")
        if expected_score >= 6 and state["riskLevel"] in {"l1", "l2"}:
            errors.append("risk_level is too low for risk_score >= 6")
        if expected_score >= 3 and state["riskLevel"] == "l1":
            errors.append("risk_level is too low for risk_score >= 3")
    if state["specStatus"] not in SPEC_STATUSES:
        errors.append(f"invalid SPEC.md status '{state['specStatus']}'")
    if state["clarifyStatus"] not in CLARIFY_STATUSES:
        errors.append(f"invalid CLARIFY.md status '{state['clarifyStatus']}'")
    if state["designStatus"] not in DESIGN_STATUSES:
        errors.append(f"invalid DESIGN.md status '{state['designStatus']}'")
    if state["planStatus"] not in PLAN_STATUSES:
        errors.append(f"invalid PLAN.md status '{state['planStatus']}'")
    if state["tasksStatus"] not in TASKS_STATUSES:
        errors.append(f"invalid TASKS.md status '{state['tasksStatus']}'")
    if state["verifyStatus"] not in VERIFY_STATUSES:
        errors.append(f"invalid VERIFY.md status '{state['verifyStatus']}'")
    if state["reviewStatus"] not in REVIEW_STATUSES:
        errors.append(f"invalid REVIEW.md status '{state['reviewStatus']}'")
    if state["workbenchUpgradeAssessment"] == "unassessed" and (state["featureStatus"] == "complete" or state["currentStage"] == "complete" or state["verifyStatus"] in {"failed", "blocked"} or state["reviewStatus"] in {"failed", "blocked"}):
        errors.append("workbench_upgrade_assessment is unassessed after failure, blocked review, or completed feature")
    if state["workbenchUpgradeAssessment"] != "unassessed" and state["workbenchUpgradeAssessment"] not in WORKBENCH_UPGRADE_ASSESSMENTS:
        errors.append(f"invalid workbench_upgrade_assessment '{state['workbenchUpgradeAssessment']}'")
    if feature_stage_reached(state, "plan") and (state["specStatus"] != "approved" or not state["specApprovedForPlan"]):
        errors.append("current_stage reached plan before SPEC.md was approved_for_plan")
    if feature_stage_reached(state, "plan") and (state["clarifyStatus"] not in {"ready", "deferred"} or not state["clarifyReadyForPlan"]):
        errors.append("current_stage reached plan before CLARIFY.md was ready_for_plan")
    if feature_stage_reached(state, "plan") and (state["designStatus"] != "approved" or not state["designApprovedForPlan"]):
        errors.append("current_stage reached plan before DESIGN.md was approved_for_plan")
    if feature_stage_reached(state, "tasks") and (state["planStatus"] != "approved" or not state["planApprovedForTasks"]):
        errors.append("current_stage reached tasks before PLAN.md was approved_for_tasks")
    if feature_stage_reached(state, "implement") and (not state["planApprovedForImplementation"] or state["tasksStatus"] != "ready" or not state["tasksReadyForImplementation"]):
        errors.append("current_stage reached implement before PLAN/TASKS allowed implementation")
    if feature_stage_reached(state, "review") and state["verifyStatus"] != "passed":
        errors.append("current_stage reached review before VERIFY.md passed")
    if state["currentStage"] == "complete" and state["reviewStatus"] != "passed":
        errors.append("current_stage is complete before REVIEW.md passed")
    return errors


def scan_text_files(project: Path) -> list[Path]:
    targets: list[Path] = []
    for rel in REQUIRED_ADAPTER_FILES:
        path = project / rel
        if path.exists() and path.is_file() and path.suffix in {".md", ".py", ".ps1", ".sh", ".json", ".toml", ".yml", ".yaml"}:
            targets.append(path)
    extra = project / REPORT_DIR / "workbench-adapter-report.json"
    if extra.exists():
        targets.append(extra)
    return targets


def python_literal_from_assign(path: Path, name: str) -> Any:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            continue
        try:
            return ast.literal_eval(node.value)
        except Exception:
            return None
    return None


def detect_precommit(project: Path) -> list[str]:
    candidates = [
        ".pre-commit-config.yaml",
        ".pre-commit-config.yml",
        "lefthook.yml",
        "lefthook.yaml",
        "husky",
        ".husky",
    ]
    return [rel for rel in candidates if (project / rel).exists()]


def audit_adapter(project: Path) -> dict[str, Any]:
    validation = validate_adapter(project)
    inspection = inspect_project(project)
    findings: list[dict[str, str]] = []

    for rel in validation["missing"]:
        severity = "P1" if rel in {"AGENTS.md", "WORKBENCH.md", "REVIEW.md", "workbench/quality/quality_gate.py"} else "P2"
        findings.append(issue(severity, "missing-required-file", "Required workbench adapter file is missing.", rel))
    for rel in validation["placeholders"]:
        findings.append(issue("P1", "unresolved-placeholder", "Generated file still contains unresolved template placeholders.", rel))
    for error in validation["pythonErrors"]:
        rel = error.split(":", 1)[0]
        findings.append(issue("P1", "python-syntax-error", error, rel))
    for error in validation.get("featureErrors", []):
        rel = error.split(":", 1)[0]
        findings.append(issue("P1", "incomplete-feature-package", error, rel))
    if validation.get("intakeStatusError"):
        findings.append(issue("P1", "invalid-project-intake-status", validation["intakeStatusError"], "PROJECT_INTAKE.md"))
    if validation.get("processStatusError"):
        findings.append(issue("P1", "invalid-development-flow-status", validation["processStatusError"], "DEVELOPMENT_FLOW.md"))

    agents_path = project / "AGENTS.md"
    if agents_path.exists():
        agents_size = len(agents_path.read_bytes())
        if agents_size >= AGENTS_MD_DEFAULT_LIMIT_BYTES:
            findings.append(issue("P1", "agents-md-over-default-discovery-limit", "AGENTS.md is at or above Codex's default 32 KiB project instruction discovery limit. Split detailed guidance into referenced files or raise project_doc_max_bytes intentionally.", "AGENTS.md"))
        elif agents_size >= AGENTS_MD_NEAR_LIMIT_BYTES:
            findings.append(issue("P2", "agents-md-near-default-discovery-limit", "AGENTS.md is approaching Codex's default 32 KiB project instruction discovery limit. Keep the entry concise and move details into WORKBENCH.md or references.", "AGENTS.md"))

    for rel, required_texts in REQUIRED_ADAPTER_TEXT_BY_FILE.items():
        path = project / rel
        if not path.exists():
            continue
        text = read_text_safe(path)
        for required in required_texts:
            if required not in text:
                findings.append(issue("P2", "missing-guidance-text", f"Expected guidance text is absent: {required}", rel))

    intake_path = project / "PROJECT_INTAKE.md"
    if intake_path.exists():
        intake_text = read_text_safe(intake_path)
        if validation.get("intakeStatus") == "draft":
            findings.append(issue("P2", "project-intake-draft", "Project intake is still draft. Confirm it before generating a confirmed development flow or starting high-risk feature work.", "PROJECT_INTAKE.md"))
        for field in ("owner:", "intake_updated_at:"):
            if field not in intake_text:
                findings.append(issue("P2", "missing-project-intake-field", f"Project intake is missing field: {field}", "PROJECT_INTAKE.md"))
        if "project owner" in intake_text or "unconfirmed" in intake_text:
            findings.append(issue("P2", "unconfirmed-project-intake", "Project intake still contains default ownership or confirmation placeholders.", "PROJECT_INTAKE.md"))
        if re.search(r"(?im)^\|\s*P\d+\s*\|.*\|\s*open\s*\|\s*$", intake_text):
            findings.append(issue("P2", "open-project-intake-blocker", "Project intake has unresolved blocking questions. Close them before confirming the development flow or starting high-risk feature work.", "PROJECT_INTAKE.md"))

    flow_path = project / "DEVELOPMENT_FLOW.md"
    if flow_path.exists():
        flow_text = read_text_safe(flow_path)
        if validation.get("processStatus") == "draft":
            findings.append(issue("P2", "development-flow-draft", "Development flow is still draft. Confirm it with the project owner before relying on it for feature work.", "DEVELOPMENT_FLOW.md"))
        for field in ("owner:", "confirmed_at:", "scope:", "verification_commands:"):
            if field not in flow_text:
                findings.append(issue("P2", "missing-development-flow-field", f"Development flow is missing field: {field}", "DEVELOPMENT_FLOW.md"))
        if "project owner" in flow_text or "unconfirmed" in flow_text:
            findings.append(issue("P2", "unconfirmed-development-flow", "Development flow still contains default ownership or confirmation placeholders.", "DEVELOPMENT_FLOW.md"))
        if validation.get("processStatus") == "confirmed" and validation.get("intakeStatus") != "confirmed":
            findings.append(issue("P1", "confirmed-flow-without-intake", "Development flow is confirmed while PROJECT_INTAKE.md is not confirmed. Confirm the project intake first.", "DEVELOPMENT_FLOW.md"))

    feature_dir = project / "workbench" / "features"
    if not feature_dir.exists():
        findings.append(issue("P3", "no-feature-work-packages", "No feature work package directory exists yet. Create workbench/features/<feature-name>/ from workbench/feature-template/ for new or high-risk features."))
    else:
        for package in sorted(item for item in feature_dir.iterdir() if item.is_dir()):
            rel_package = rel_to(project, package)
            state = feature_package_state(package)
            state_errors = feature_state_errors(state)
            invalid_state_errors = [error for error in state_errors if error.startswith("invalid ")]
            stage_order_errors = [error for error in state_errors if error not in invalid_state_errors]
            for error in invalid_state_errors:
                findings.append(issue("P1", "invalid-feature-state-field", error, f"{rel_package}/CHECKLIST.md"))
            for error in stage_order_errors:
                findings.append(issue("P1", "invalid-feature-stage-order", error, f"{rel_package}/CHECKLIST.md"))
            if invalid_state_errors:
                continue
            if state["featureStatus"] == "on_hold":
                continue
            if state["hasOpenClarification"]:
                findings.append(issue("P1", "open-blocking-clarification", "Feature package has unresolved blocking clarification items.", f"{rel_package}/CLARIFY.md"))
            if state["featureStatus"] == "active":
                findings.append(issue("P2", "active-feature-not-complete", "Feature package is active but not complete. Finish the SDD stages before delivery, or set feature_status to on_hold if this is parked work.", f"{rel_package}/CHECKLIST.md"))
            if not state["specApprovedForPlan"]:
                findings.append(issue("P2", "spec-not-approved", "SPEC.md is not approved for planning.", f"{rel_package}/SPEC.md"))
            if not state["clarifyReadyForPlan"]:
                findings.append(issue("P2", "clarify-not-ready", "CLARIFY.md is not ready for planning.", f"{rel_package}/CLARIFY.md"))
            if not state["designApprovedForPlan"]:
                findings.append(issue("P2", "design-not-approved", "DESIGN.md is not approved for planning.", f"{rel_package}/DESIGN.md"))
            if not state["planApprovedForTasks"] or not state["planApprovedForImplementation"]:
                findings.append(issue("P2", "plan-not-approved", "PLAN.md is not approved for tasks and implementation.", f"{rel_package}/PLAN.md"))
            if not state["tasksReadyForImplementation"]:
                findings.append(issue("P2", "tasks-not-ready", "TASKS.md is not marked ready for implementation.", f"{rel_package}/TASKS.md"))
            if state["verifyStatus"] != "passed" or state["verifyEmpty"]:
                findings.append(issue("P2", "feature-verification-incomplete", "VERIFY.md does not show passed verification evidence.", f"{rel_package}/VERIFY.md"))
            if state["reviewStatus"] != "passed":
                findings.append(issue("P2", "feature-review-incomplete", "REVIEW.md has not passed.", f"{rel_package}/REVIEW.md"))
            if not state["implementationAllowed"] or not state["deliveryAllowed"] or state["hasUncheckedChecklist"] or state["hasUncheckedTasks"]:
                findings.append(issue("P2", "feature-stage-gates-incomplete", "Feature package still has unchecked stage gates or tasks.", f"{rel_package}/CHECKLIST.md"))

    for path in scan_text_files(project):
        rel = rel_to(project, path)
        if rel == f"{REPORT_DIR}/workbench-adapter-report.json":
            continue
        text = read_text_safe(path)
        for pattern in PERSONAL_PATH_PATTERNS:
            if pattern.search(text):
                findings.append(issue("P1", "personal-path", "File contains a personal absolute path. Replace with portable project-relative guidance.", rel))
                break
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(issue("P0", "possible-secret", "File contains a possible secret or token-like value. Remove it before sharing.", rel))
                break
        if rel in {"AGENTS.md", "PROJECT_INTAKE.md", "WORKBENCH.md", "FEATURE_WORKFLOW.md"}:
            for pattern in IMPLEMENTATION_LEAK_PATTERNS:
                if pattern.search(text):
                    findings.append(issue("P2", "implementation-leak", "Project-facing docs mention internal skill names or skill-local paths. Prefer public workbench concepts and project-local commands.", rel))
                    break

    quality_gate = project / "workbench" / "quality" / "quality_gate.py"
    commands = python_literal_from_assign(quality_gate, "COMMANDS") if quality_gate.exists() else None
    quality_gate_text = read_text_safe(quality_gate) if quality_gate.exists() else ""
    if quality_gate.exists() and "run_scorecard" not in quality_gate_text:
        findings.append(issue("P1", "scorecard-report-not-generated", "Quality gate does not call workbench/scorecard/scorecard.py, so evidence reporting can be skipped.", "workbench/quality/quality_gate.py"))
    elif quality_gate.exists() and "--called-from-quality-gate" not in quality_gate_text:
        findings.append(issue("P2", "scorecard-missing-gate-context", "Quality gate calls scorecard.py without --called-from-quality-gate, so current-run quality-gate evidence may be interpreted as missing history.", "workbench/quality/quality_gate.py"))
    if commands == []:
        findings.append(issue("P1", "empty-quality-gate", "Quality gate has zero configured checks. This is not a hard gate for a code project.", "workbench/quality/quality_gate.py"))
    elif isinstance(commands, list):
        profiles = {profile for cmd in commands for profile in cmd.get("profiles", ["standard"])}
        for profile in ("smoke", "standard"):
            if profile not in profiles:
                findings.append(issue("P2", "missing-quality-profile", f"No quality command is assigned to the {profile} profile.", "workbench/quality/quality_gate.py"))

    report_path = project / REPORT_DIR / "workbench-adapter-report.json"
    if not report_path.exists():
        findings.append(issue("P2", "missing-generation-report", "Generation report is missing; regenerate or save an audit trail.", rel_to(project, report_path)))

    scorecard_script = project / "workbench" / "scorecard" / "scorecard.py"
    if scorecard_script.exists():
        scorecard_text = read_text_safe(scorecard_script)
        if "WEIGHTS" not in scorecard_text or "PROFILE_RULES" not in scorecard_text:
            findings.append(issue("P1", "invalid-scorecard-script", "scorecard.py is missing WEIGHTS or PROFILE_RULES.", "workbench/scorecard/scorecard.py"))
        for required in ("decision", "confidence", "calibration", "componentFloorViolations", "PROFILE_RULES", "calledFromQualityGate"):
            if required not in scorecard_text:
                findings.append(issue("P1", "weak-scorecard-script", f"scorecard.py is missing evidence-audit field: {required}", "workbench/scorecard/scorecard.py"))
    scorecard_doc = project / "workbench" / "scorecard" / "SCORECARD.md"
    if scorecard_doc.exists():
        scorecard_text = read_text_safe(scorecard_doc)
        if "semantic_review_status:" not in scorecard_text or "architecture_review_status:" not in scorecard_text:
            findings.append(issue("P2", "missing-semantic-score-fields", "SCORECARD.md should expose semantic_review_status and architecture_review_status.", "workbench/scorecard/SCORECARD.md"))
        for required in ("score_confidence:", "calibration_status:", "误报", "漏报"):
            if required not in scorecard_text:
                findings.append(issue("P2", "missing-scorecard-trust-field", f"SCORECARD.md should expose scoring trust field: {required}", "workbench/scorecard/SCORECARD.md"))
    calibration_doc = project / "workbench" / "scorecard" / "CALIBRATION.md"
    if calibration_doc.exists():
        calibration_text = read_text_safe(calibration_doc)
        for required in ("calibration_status:", "锚定样例", "人工抽查", "误报", "漏报", "参考线调整"):
            if required not in calibration_text:
                findings.append(issue("P2", "missing-scorecard-calibration-field", f"CALIBRATION.md should include calibration field: {required}", "workbench/scorecard/CALIBRATION.md"))

    precommit = detect_precommit(project)
    if not precommit:
        findings.append(issue("P3", "no-local-precommit", "No local pre-commit/hook framework detected. CI can still enforce, but local feedback is weaker."))

    ci = inspection["ci"]
    if not ci.get("githubActions") and not ci.get("jenkinsfile"):
        findings.append(issue("P2", "no-ci-detected", "No GitHub Actions workflow or Jenkinsfile detected. Server-side quality enforcement is unclear."))

    if not inspection["qualityCommands"]:
        findings.append(issue("P1", "no-detected-quality-commands", "Inspection found no build/test/lint candidates. Confirm project commands before using the adapter."))

    severities = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    for item in findings:
        severities[item["severity"]] = severities.get(item["severity"], 0) + 1

    passed = severities["P0"] == 0 and severities["P1"] == 0
    return {
        "schema": "codex-workbench-audit/v1",
        "timestamp": utc_now(),
        "projectRoot": str(project),
        "passed": passed,
        "summary": severities,
        "findings": findings,
        "validation": validation,
        "inspection": inspection,
    }


def run_self_test() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="codex-workbench-self-test-") as tmp:
        root = Path(tmp)
        package = {
            "name": "sample-app",
            "private": True,
            "scripts": {
                "lint": "node -e \"console.log('lint')\"",
                "build": "node -e \"console.log('build')\"",
            },
            "devDependencies": {"vite": "0.0.0"},
        }
        (root / "package.json").write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")
        inspection = inspect_project(root)
        generation = generate_adapter(root, "sample-app", force=False, dry_run=False)
        validation = validate_adapter(root)
        audit = audit_adapter(root)
        return {
            "schema": "codex-workbench-self-test/v1",
            "timestamp": utc_now(),
            "inspectionDetectedCommands": len(inspection["qualityCommands"]),
            "generatedFiles": generation["files"],
            "validation": validation,
            "audit": {
                "passed": audit["passed"],
                "summary": audit["summary"],
                "findings": audit["findings"],
            },
            "passed": validation["passed"] and audit["passed"] and len(inspection["qualityCommands"]) > 0,
        }


def write_sample_node(root: Path) -> None:
    package = {
        "name": "sample-node",
        "private": True,
        "scripts": {
            "lint": "node -e \"console.log('lint')\"",
            "build": "node -e \"console.log('build')\"",
            "test": "node -e \"console.log('test')\"",
        },
        "devDependencies": {"vite": "0.0.0", "vue": "0.0.0"},
    }
    (root / "package.json").write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")


def write_sample_maven(root: Path) -> None:
    (root / "pom.xml").write_text(
        textwrap.dedent(
            """\
            <project xmlns="http://maven.apache.org/POM/4.0.0">
              <modelVersion>4.0.0</modelVersion>
              <groupId>example</groupId>
              <artifactId>sample-maven</artifactId>
              <version>1.0.0</version>
              <properties>
                <java.version>17</java.version>
              </properties>
            </project>
            """
        ),
        encoding="utf-8",
    )


def write_sample_fullstack(root: Path) -> None:
    frontend = root / "frontend"
    backend = root / "backend"
    frontend.mkdir(parents=True)
    backend.mkdir(parents=True)
    (frontend / "package.json").write_text(
        json.dumps(
            {
                "name": "sample-front",
                "scripts": {"typecheck": "node -e \"console.log('typecheck')\"", "build": "node -e \"console.log('build')\""},
                "dependencies": {"react": "0.0.0", "vite": "0.0.0"},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (backend / "pom.xml").write_text(
        textwrap.dedent(
            """\
            <project xmlns="http://maven.apache.org/POM/4.0.0">
              <modelVersion>4.0.0</modelVersion>
              <groupId>example</groupId>
              <artifactId>backend</artifactId>
              <version>1.0.0</version>
            </project>
            """
        ),
        encoding="utf-8",
    )
    (root / "docker-compose.yml").write_text("services:\n  app:\n    image: alpine\n", encoding="utf-8")


def write_sample_old_workbench(root: Path) -> None:
    write_sample_node(root)
    (root / "AGENTS.md").write_text("# Old Rules\n\nKeep this custom project rule.\n", encoding="utf-8")
    (root / "WORKBENCH.md").write_text("# Old Workbench\n", encoding="utf-8")
    (root / "REVIEW.md").write_text("# Old Review\n", encoding="utf-8")
    (root / "workbench" / "quality").mkdir(parents=True)
    (root / "workbench" / "quality" / "quality-gate.ps1").write_text("Write-Output 'old gate'\n", encoding="utf-8")


def mark_feature_on_hold(root: Path, slug: str) -> None:
    checklist = root / "workbench" / "features" / slug / "CHECKLIST.md"
    text = checklist.read_text(encoding="utf-8")
    text = re.sub(r"(?im)^feature_status:\s*active\s*$", "feature_status: on_hold", text)
    checklist.write_text(text, encoding="utf-8")


def assert_condition(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def run_golden_case(name: str, builder: Any) -> dict[str, Any]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix=f"codex-workbench-golden-{name}-") as tmp:
        root = Path(tmp)
        builder(root)
        inspection = inspect_project(root)
        generation = generate_adapter(root, name, force=False, dry_run=False)
        validation = validate_adapter(root)
        audit = audit_adapter(root)
        upgrade_preview = upgrade_adapter(root, name, dry_run=True, replace_docs=False, refresh_generated=False)

        assert_condition(validation["passed"], f"{name}: validation failed", failures)
        assert_condition(audit["summary"]["P0"] == 0, f"{name}: audit has P0 findings", failures)
        assert_condition(audit["summary"]["P1"] == 0, f"{name}: audit has P1 findings", failures)
        assert_condition((root / "PROJECT_INTAKE.md").exists(), f"{name}: PROJECT_INTAKE.md was not generated", failures)
        assert_condition((root / "DEVELOPMENT_FLOW.md").exists(), f"{name}: DEVELOPMENT_FLOW.md was not generated", failures)
        assert_condition((root / "PRODUCT_BASELINE.md").exists(), f"{name}: PRODUCT_BASELINE.md was not generated", failures)
        assert_condition((root / "FEATURE_WORKFLOW.md").exists(), f"{name}: FEATURE_WORKFLOW.md was not generated", failures)
        assert_condition((root / "workbench" / "product" / "PRODUCT_BRIEF.md").exists(), f"{name}: PRODUCT_BRIEF.md was not generated", failures)
        assert_condition((root / "workbench" / "product" / "PRD.md").exists(), f"{name}: PRD.md was not generated", failures)
        assert_condition((root / "workbench" / "design" / "UX_SPEC.md").exists(), f"{name}: UX_SPEC.md was not generated", failures)
        assert_condition((root / "workbench" / "architecture" / "ARCHITECTURE.md").exists(), f"{name}: ARCHITECTURE.md was not generated", failures)
        assert_condition((root / "workbench" / "delivery" / "ITERATION_PLAN.md").exists(), f"{name}: ITERATION_PLAN.md was not generated", failures)
        assert_condition((root / "workbench" / "scorecard" / "RUBRIC.md").exists(), f"{name}: scorecard RUBRIC was not generated", failures)
        assert_condition((root / "workbench" / "scorecard" / "SCORECARD.md").exists(), f"{name}: scorecard SCORECARD was not generated", failures)
        assert_condition((root / "workbench" / "scorecard" / "CALIBRATION.md").exists(), f"{name}: scorecard CALIBRATION was not generated", failures)
        assert_condition((root / "workbench" / "scorecard" / "scorecard.py").exists(), f"{name}: scorecard.py was not generated", failures)
        assert_condition("run_scorecard" in (root / "workbench" / "quality" / "quality_gate.py").read_text(encoding="utf-8"), f"{name}: quality gate does not call scorecard", failures)
        assert_condition((root / "workbench" / "feedback" / "AI_EFFECTIVENESS.md").exists(), f"{name}: AI_EFFECTIVENESS.md was not generated", failures)
        assert_condition((root / "workbench" / "feature-template" / "SPEC.md").exists(), f"{name}: feature SPEC template was not generated", failures)
        assert_condition((root / "workbench" / "feature-template" / "CLARIFY.md").exists(), f"{name}: feature CLARIFY template was not generated", failures)
        assert_condition((root / "workbench" / "feature-template" / "DESIGN.md").exists(), f"{name}: feature DESIGN template was not generated", failures)
        assert_condition((root / "workbench" / "feature-template" / "DECISIONS.md").exists(), f"{name}: feature DECISIONS template was not generated", failures)
        assert_condition((root / "workbench" / "feature-template" / "IMPLEMENTATION_NOTES.md").exists(), f"{name}: feature IMPLEMENTATION_NOTES template was not generated", failures)
        assert_condition((root / "workbench" / "feature-template" / "CHECKLIST.md").exists(), f"{name}: feature CHECKLIST template was not generated", failures)
        assert_condition((root / "workbench" / "feature-template" / "VERIFY.md").exists(), f"{name}: feature VERIFY template was not generated", failures)
        assert_condition((root / "workbench" / "feature-template" / "CHANGELOG.md").exists(), f"{name}: feature CHANGELOG template was not generated", failures)
        feature_preview = create_feature_package(root, "User Login", dry_run=True, force=False)
        assert_condition(feature_preview["featureSlug"] == "user-login", f"{name}: feature slug was not normalized", failures)
        feature = create_feature_package(root, "User Login", dry_run=False, force=False)
        assert_condition((root / "workbench" / "features" / "user-login" / "SPEC.md").exists(), f"{name}: feature package SPEC was not created", failures)
        assert_condition((root / "workbench" / "features" / "user-login" / "CLARIFY.md").exists(), f"{name}: feature package CLARIFY was not created", failures)
        assert_condition((root / "workbench" / "features" / "user-login" / "DESIGN.md").exists(), f"{name}: feature package DESIGN was not created", failures)
        assert_condition((root / "workbench" / "features" / "user-login" / "DECISIONS.md").exists(), f"{name}: feature package DECISIONS was not created", failures)
        assert_condition((root / "workbench" / "features" / "user-login" / "CHANGELOG.md").exists(), f"{name}: feature package CHANGELOG was not created", failures)
        active_audit = audit_adapter(root)
        assert_condition(active_audit["summary"]["P1"] > 0 or active_audit["summary"]["P2"] > 0, f"{name}: active incomplete feature should be audited", failures)
        mark_feature_on_hold(root, "user-login")
        audit_after_hold = audit_adapter(root)
        assert_condition(audit_after_hold["summary"]["P1"] == 0, f"{name}: on-hold feature should not create P1 findings", failures)
        assert_condition(validation["processStatus"] == "draft", f"{name}: development flow should start as draft", failures)
        assert_condition(len(inspection["qualityCommands"]) > 0, f"{name}: no quality commands detected", failures)
        assert_condition(
            all(item["status"] in {"skipped", "skipped-existing"} or item["action"].startswith("keep-") for item in upgrade_preview["files"].values()),
            f"{name}: dry-run upgrade after generation should not plan writes without refresh flags",
            failures,
        )
        return {
            "name": name,
            "passed": not failures,
            "failures": failures,
            "qualityCommandCount": len(inspection["qualityCommands"]),
            "generatedFileCount": len(generation["files"]),
            "featureFileCount": len(feature["files"]),
            "auditSummary": audit_after_hold["summary"],
        }


def run_upgrade_golden_case() -> dict[str, Any]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="codex-workbench-golden-old-workbench-") as tmp:
        root = Path(tmp)
        write_sample_old_workbench(root)
        preview = upgrade_adapter(root, "old-workbench", dry_run=True, replace_docs=False, refresh_generated=False)
        assert_condition(preview["files"]["AGENTS.md"]["action"] == "keep-existing-doc", "upgrade should preserve existing AGENTS.md by default", failures)
        assert_condition(preview["files"]["PROJECT_INTAKE.md"]["action"] == "write-missing", "upgrade should add missing PROJECT_INTAKE.md", failures)
        assert_condition(preview["files"]["DEVELOPMENT_FLOW.md"]["action"] == "write-missing", "upgrade should add missing DEVELOPMENT_FLOW.md", failures)
        assert_condition(preview["files"]["PRODUCT_BASELINE.md"]["action"] == "write-missing", "upgrade should add missing PRODUCT_BASELINE.md", failures)
        assert_condition(preview["files"]["FEATURE_WORKFLOW.md"]["action"] == "write-missing", "upgrade should add missing FEATURE_WORKFLOW.md", failures)
        assert_condition(preview["files"]["workbench/product/PRODUCT_BRIEF.md"]["action"] == "write-missing", "upgrade should add missing PRODUCT_BRIEF.md", failures)
        assert_condition(preview["files"]["workbench/design/UX_SPEC.md"]["action"] == "write-missing", "upgrade should add missing UX_SPEC.md", failures)
        assert_condition(preview["files"]["workbench/architecture/ARCHITECTURE.md"]["action"] == "write-missing", "upgrade should add missing ARCHITECTURE.md", failures)
        assert_condition(preview["files"]["workbench/scorecard/RUBRIC.md"]["action"] == "write-missing", "upgrade should add missing scorecard RUBRIC.md", failures)
        assert_condition(preview["files"]["workbench/scorecard/CALIBRATION.md"]["action"] == "write-missing", "upgrade should add missing scorecard CALIBRATION.md", failures)
        assert_condition(preview["files"]["workbench/scorecard/scorecard.py"]["action"] == "write-missing", "upgrade should add missing scorecard.py", failures)
        assert_condition(preview["files"]["workbench/quality/quality_gate.py"]["action"] == "write-missing", "upgrade should add missing Python quality gate", failures)
        applied = upgrade_adapter(root, "old-workbench", dry_run=False, replace_docs=False, refresh_generated=False)
        validation = validate_adapter(root)
        audit = audit_adapter(root)
        assert_condition((root / "AGENTS.md").read_text(encoding="utf-8").startswith("# Old Rules"), "upgrade overwrote existing AGENTS.md", failures)
        assert_condition((root / "PROJECT_INTAKE.md").exists(), "upgrade did not write missing PROJECT_INTAKE.md", failures)
        assert_condition((root / "DEVELOPMENT_FLOW.md").exists(), "upgrade did not write missing DEVELOPMENT_FLOW.md", failures)
        assert_condition((root / "PRODUCT_BASELINE.md").exists(), "upgrade did not write missing PRODUCT_BASELINE.md", failures)
        assert_condition((root / "FEATURE_WORKFLOW.md").exists(), "upgrade did not write missing FEATURE_WORKFLOW.md", failures)
        assert_condition((root / "workbench" / "product" / "PRODUCT_BRIEF.md").exists(), "upgrade did not write missing PRODUCT_BRIEF.md", failures)
        assert_condition((root / "workbench" / "design" / "UX_SPEC.md").exists(), "upgrade did not write missing UX_SPEC.md", failures)
        assert_condition((root / "workbench" / "architecture" / "ARCHITECTURE.md").exists(), "upgrade did not write missing ARCHITECTURE.md", failures)
        assert_condition((root / "workbench" / "scorecard" / "RUBRIC.md").exists(), "upgrade did not write scorecard RUBRIC.md", failures)
        assert_condition((root / "workbench" / "scorecard" / "CALIBRATION.md").exists(), "upgrade did not write scorecard CALIBRATION.md", failures)
        assert_condition((root / "workbench" / "scorecard" / "scorecard.py").exists(), "upgrade did not write scorecard.py", failures)
        assert_condition((root / "workbench" / "feature-template" / "TASKS.md").exists(), "upgrade did not write feature task template", failures)
        assert_condition((root / "workbench" / "feature-template" / "CLARIFY.md").exists(), "upgrade did not write feature clarify template", failures)
        assert_condition((root / "workbench" / "feature-template" / "DESIGN.md").exists(), "upgrade did not write feature design template", failures)
        assert_condition((root / "workbench" / "feature-template" / "DECISIONS.md").exists(), "upgrade did not write feature decisions template", failures)
        assert_condition((root / "workbench" / "feature-template" / "CHECKLIST.md").exists(), "upgrade did not write feature checklist template", failures)
        assert_condition((root / "workbench" / "quality" / "quality_gate.py").exists(), "upgrade did not write missing quality_gate.py", failures)
        assert_condition(validation["passed"], "upgrade validation failed", failures)
        assert_condition(audit["summary"]["P0"] == 0, "upgrade audit has P0 findings", failures)
        return {
            "name": "old-workbench-upgrade",
            "passed": not failures,
            "failures": failures,
            "previewActions": preview["files"],
            "appliedFileCount": len(applied["files"]),
            "auditSummary": audit["summary"],
        }


def run_golden_test() -> dict[str, Any]:
    cases = [
        run_golden_case("node-vite", write_sample_node),
        run_golden_case("maven-basic", write_sample_maven),
        run_golden_case("fullstack-compose", write_sample_fullstack),
        run_upgrade_golden_case(),
    ]
    return {
        "schema": "codex-workbench-golden-test/v1",
        "timestamp": utc_now(),
        "cases": cases,
        "passed": all(case["passed"] for case in cases),
    }


def doctor_issue(severity: str, code: str, message: str, path: str | None = None) -> dict[str, str]:
    item = {"severity": severity, "code": code, "message": message}
    if path:
        item["path"] = path
    return item


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_plugin_root() -> Path | None:
    root = skill_root()
    parts = list(root.parts)
    try:
        index = parts.index("skills")
    except ValueError:
        return None
    if index >= 1 and root.name == "codex-workbench":
        candidate = Path(*parts[:index])
        if (candidate / ".codex-plugin" / "plugin.json").exists():
            return candidate
    home_candidate = Path.home() / "plugins" / "codex-workbench"
    if (home_candidate / ".codex-plugin" / "plugin.json").exists():
        return home_candidate
    return None


def iter_publish_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for current, dirs, filenames in os.walk(root):
        cur = Path(current)
        dirs[:] = [d for d in dirs if d not in {".git", ".hg", ".svn"}]
        for filename in filenames:
            files.append(cur / filename)
    return files


def scan_publish_tree(root: Path, label: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path in iter_publish_files(root):
        rel = rel_to(root, path)
        normalized = rel.replace("\\", "/")
        for pattern in PUBLISH_BLOCKLIST_PATTERNS:
            if pattern.search(normalized):
                findings.append(doctor_issue("P1", "publish-artifact-residue", f"{label} contains cache, legacy, or internal residue.", rel))
                break
        if path.suffix.lower() not in {".md", ".py", ".ps1", ".sh", ".json", ".toml", ".yml", ".yaml", ".txt"}:
            continue
        if path.name == "workbench.py" and path.parent.name == "scripts":
            continue
        text = read_text_safe(path)
        for pattern in PERSONAL_PATH_PATTERNS:
            if pattern.search(text):
                findings.append(doctor_issue("P1", "personal-path", f"{label} contains a personal absolute path.", rel))
                break
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(doctor_issue("P0", "possible-secret", f"{label} contains a possible secret or token-like value.", rel))
                break
    return findings


def validate_skill_files(root: Path, label: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for rel in REQUIRED_SKILL_FILES:
        if not (root / rel).exists():
            findings.append(doctor_issue("P1", "missing-skill-file", f"{label} is missing a required bundled file.", rel))
    for rel in ("scripts/workbench.py", "scripts/intake.py", "scripts/check_enhancements.py"):
        path = root / rel
        if not path.exists():
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            findings.append(doctor_issue("P1", "python-syntax-error", f"{exc.msg} at line {exc.lineno}", rel))
    return findings


def validate_plugin_manifest(plugin: Path) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    findings: list[dict[str, str]] = []
    manifest_path = plugin / ".codex-plugin" / "plugin.json"
    if not manifest_path.exists():
        findings.append(doctor_issue("P1", "missing-plugin-manifest", "Plugin manifest is missing.", rel_to(plugin, manifest_path)))
        return None, findings
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        findings.append(doctor_issue("P1", "invalid-plugin-manifest-json", f"Plugin manifest is not valid JSON: {exc}", rel_to(plugin, manifest_path)))
        return None, findings
    if manifest.get("name") != "codex-workbench":
        findings.append(doctor_issue("P1", "plugin-name-mismatch", "Plugin name should be codex-workbench.", rel_to(plugin, manifest_path)))
    skills_path = manifest.get("skills")
    if skills_path != "./skills/":
        findings.append(doctor_issue("P2", "plugin-skills-path", "Plugin skills path should be ./skills/.", rel_to(plugin, manifest_path)))
    skill_dir = plugin / "skills" / "codex-workbench"
    if not skill_dir.exists():
        findings.append(doctor_issue("P1", "missing-plugin-skill", "Plugin does not contain skills/codex-workbench.", rel_to(plugin, skill_dir)))
    return manifest, findings


def validate_maintenance_evidence(plugin: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for rel, required_terms in MAINTENANCE_EVIDENCE_FILES.items():
        path = plugin / rel
        if not path.exists():
            findings.append(doctor_issue("P1", "missing-maintenance-evidence", "Workbench package is missing maintainer evidence for measured improvement.", rel))
            continue
        text = read_text_safe(path)
        if len(text.strip()) < 200:
            findings.append(doctor_issue("P2", "thin-maintenance-evidence", "Maintainer evidence file is too thin to support release review.", rel))
        missing_terms = [term for term in required_terms if term not in text]
        if missing_terms:
            findings.append(doctor_issue("P2", "incomplete-maintenance-evidence", f"Maintainer evidence should include: {', '.join(missing_terms)}.", rel))
    return findings


def compare_skill_trees(personal: Path, plugin_skill: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    rels = sorted({rel_to(personal, path) for path in iter_publish_files(personal)} | {rel_to(plugin_skill, path) for path in iter_publish_files(plugin_skill)})
    for rel in rels:
        left = personal / rel
        right = plugin_skill / rel
        if any(pattern.search(rel.replace("\\", "/")) for pattern in PUBLISH_BLOCKLIST_PATTERNS):
            continue
        if not left.exists():
            findings.append(doctor_issue("P1", "plugin-extra-file", "Plugin skill has a file not present in the personal skill.", rel))
            continue
        if not right.exists():
            findings.append(doctor_issue("P1", "plugin-missing-file", "Plugin skill is missing a file from the personal skill.", rel))
            continue
        if left.is_file() and right.is_file() and not filecmp.cmp(left, right, shallow=False):
            findings.append(doctor_issue("P1", "personal-plugin-drift", "Personal skill and plugin skill file differ.", rel))
    return findings


def doctor_workbench(plugin_path: str | None = None) -> dict[str, Any]:
    personal = skill_root()
    plugin = Path(plugin_path).expanduser().resolve() if plugin_path else default_plugin_root()
    findings: list[dict[str, str]] = []
    checks: list[str] = []

    checks.append("personal skill required files")
    findings.extend(validate_skill_files(personal, "Personal skill"))
    findings.extend(scan_publish_tree(personal, "Personal skill"))

    plugin_summary: dict[str, Any] | None = None
    if plugin is None:
        findings.append(doctor_issue("P2", "plugin-not-found", "Plugin root was not found. Pass --plugin <path> when checking a package."))
    else:
        checks.append("plugin manifest")
        manifest, manifest_findings = validate_plugin_manifest(plugin)
        findings.extend(manifest_findings)
        plugin_skill = plugin / "skills" / "codex-workbench"
        if plugin_skill.exists():
            checks.append("plugin skill required files")
            findings.extend(validate_skill_files(plugin_skill, "Plugin skill"))
            findings.extend(scan_publish_tree(plugin, "Plugin package"))
            checks.append("maintenance evidence")
            findings.extend(validate_maintenance_evidence(plugin))
            checks.append("personal/plugin sync")
            findings.extend(compare_skill_trees(personal, plugin_skill))
        plugin_summary = {
            "path": str(plugin),
            "manifestName": manifest.get("name") if manifest else None,
            "version": manifest.get("version") if manifest else None,
        }

    severities = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    for item in findings:
        severities[item["severity"]] = severities.get(item["severity"], 0) + 1
    return {
        "schema": "codex-workbench-doctor/v1",
        "timestamp": utc_now(),
        "personalSkill": str(personal),
        "plugin": plugin_summary,
        "checks": checks,
        "passed": severities["P0"] == 0 and severities["P1"] == 0,
        "summary": severities,
        "findings": findings,
    }


def exposed_plugin_skills(plugin: Path) -> list[str]:
    skills_dir = plugin / "skills"
    if not skills_dir.exists():
        return []
    return sorted(item.name for item in skills_dir.iterdir() if item.is_dir() and (item / "SKILL.md").exists())


def validate_packaging_manifest(plugin: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    manifest_path = plugin / "packaging-manifest.json"
    if not manifest_path.exists():
        findings.append(doctor_issue("P1", "missing-packaging-manifest", "Package should include packaging-manifest.json so release exclusions are explicit.", "packaging-manifest.json"))
        return findings
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        findings.append(doctor_issue("P1", "invalid-packaging-manifest-json", f"packaging-manifest.json is not valid JSON: {exc}", "packaging-manifest.json"))
        return findings
    include = manifest.get("include")
    exclude = manifest.get("exclude")
    visible = manifest.get("visibleSkills")
    if not isinstance(include, list):
        findings.append(doctor_issue("P1", "packaging-manifest-missing-include-list", "Packaging manifest should define an include list.", "packaging-manifest.json"))
        include = []
    for required in PACKAGING_MANIFEST_REQUIRED_INCLUDES:
        if required not in include:
            findings.append(doctor_issue("P1", "packaging-manifest-missing-required-include", f"Packaging manifest should include {required}.", "packaging-manifest.json"))
    if not isinstance(exclude, list):
        findings.append(doctor_issue("P1", "packaging-manifest-missing-exclude-list", "Packaging manifest should define an exclude list.", "packaging-manifest.json"))
        exclude = []
    for required in PACKAGING_MANIFEST_REQUIRED_EXCLUDES:
        if required not in exclude:
            findings.append(doctor_issue("P1", "packaging-manifest-missing-required-exclude", f"Packaging manifest should exclude {required}.", "packaging-manifest.json"))
    if visible != ["codex-workbench"]:
        findings.append(doctor_issue("P1", "packaging-manifest-visible-skill-mismatch", "Packaging manifest should expose only codex-workbench.", "packaging-manifest.json"))
    return findings


def package_check_workbench(plugin_path: str | None = None, expected_version: str | None = None, write_report: bool = False) -> dict[str, Any]:
    plugin = Path(plugin_path).expanduser().resolve() if plugin_path else default_plugin_root()
    doctor = doctor_workbench(str(plugin) if plugin else None)
    findings = list(doctor["findings"])
    checks = list(doctor["checks"])
    manifest: dict[str, Any] | None = None
    exposed_skills: list[str] = []

    if plugin is None:
        findings.append(doctor_issue("P1", "package-plugin-missing", "Package check requires a plugin root. Pass --plugin <path>."))
    else:
        checks.append("release manifest")
        manifest, manifest_findings = validate_plugin_manifest(plugin)
        findings.extend(manifest_findings)
        checks.append("packaging manifest")
        findings.extend(validate_packaging_manifest(plugin))
        exposed_skills = exposed_plugin_skills(plugin)
        checks.append("visible skill surface")
        if exposed_skills != ["codex-workbench"]:
            findings.append(doctor_issue("P1", "unexpected-visible-skills", "Published plugin should expose only codex-workbench.", "skills"))
        if manifest:
            version = manifest.get("version")
            if not isinstance(version, str) or not re.match(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$", version):
                findings.append(doctor_issue("P1", "invalid-version", "Plugin version should be a semantic version string.", ".codex-plugin/plugin.json"))
            if expected_version and version != expected_version:
                findings.append(doctor_issue("P1", "version-mismatch", f"Plugin version is {version}, expected {expected_version}.", ".codex-plugin/plugin.json"))
            interface = manifest.get("interface") or {}
            if not interface.get("displayName") or not interface.get("shortDescription"):
                findings.append(doctor_issue("P2", "incomplete-plugin-interface", "Plugin interface should include displayName and shortDescription.", ".codex-plugin/plugin.json"))
            for forbidden in ("hooks", "mcpServers", "apps"):
                if forbidden in manifest:
                    findings.append(doctor_issue("P1", "unsupported-or-boundary-leaking-manifest-field", f"Plugin manifest should not include {forbidden} unless supported and intentionally bundled.", ".codex-plugin/plugin.json"))

    severities = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    for item in findings:
        severities[item["severity"]] = severities.get(item["severity"], 0) + 1
    passed = severities["P0"] == 0 and severities["P1"] == 0
    report = {
        "schema": "codex-workbench-package-check/v1",
        "timestamp": utc_now(),
        "pluginRoot": str(plugin) if plugin else None,
        "expectedVersion": expected_version,
        "manifestVersion": manifest.get("version") if manifest else None,
        "visibleSkills": exposed_skills,
        "recipientMustConfigure": RECIPIENT_SETUP_ITEMS,
        "maintenanceEvidence": sorted(MAINTENANCE_EVIDENCE_FILES.keys()),
        "checks": checks,
        "passed": passed,
        "summary": severities,
        "findings": findings,
    }
    if write_report and plugin is not None:
        report_dir = plugin / REPORT_DIR
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "package-check-report.json"
        report["reportPath"] = str(report_path)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Codex workbench adapter tool")
    sub = parser.add_subparsers(dest="command", required=True)

    p_inspect = sub.add_parser("inspect")
    p_inspect.add_argument("--project", default=None)
    p_inspect.add_argument("--output", default=None)

    p_generate = sub.add_parser("generate")
    p_generate.add_argument("--project", default=None)
    p_generate.add_argument("--name", default=None)
    p_generate.add_argument("--force", action="store_true")
    p_generate.add_argument("--dry-run", action="store_true")
    p_generate.add_argument("--output", default=None)

    p_upgrade = sub.add_parser("upgrade")
    p_upgrade.add_argument("--project", default=None)
    p_upgrade.add_argument("--name", default=None)
    p_upgrade.add_argument("--dry-run", action="store_true")
    p_upgrade.add_argument("--apply", action="store_true")
    p_upgrade.add_argument("--replace-docs", action="store_true")
    p_upgrade.add_argument("--refresh-generated", action="store_true")
    p_upgrade.add_argument("--output", default=None)

    p_feature = sub.add_parser("feature")
    p_feature.add_argument("--project", default=None)
    p_feature.add_argument("--name", required=True)
    p_feature.add_argument("--force", action="store_true")
    p_feature.add_argument("--dry-run", action="store_true")
    p_feature.add_argument("--output", default=None)

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("--project", default=None)
    p_validate.add_argument("--output", default=None)

    p_audit = sub.add_parser("audit")
    p_audit.add_argument("--project", default=None)
    p_audit.add_argument("--output", default=None)

    p_retention = sub.add_parser("retention")
    p_retention.add_argument("--project", default=None)
    p_retention.add_argument("--keep-reports", type=int, default=DEFAULT_RETENTION_KEEP_REPORTS)
    p_retention.add_argument("--apply", action="store_true", help="Archive older machine-generated reports. Human evidence is never rewritten.")
    p_retention.add_argument("--write-report", action="store_true")
    p_retention.add_argument("--output", default=None)

    p_self = sub.add_parser("self-test")
    p_self.add_argument("--output", default=None)

    p_golden = sub.add_parser("golden-test")
    p_golden.add_argument("--output", default=None)

    p_doctor = sub.add_parser("doctor")
    p_doctor.add_argument("--plugin", default=None, help="Optional plugin root to check. Defaults to ~/plugins/codex-workbench when present.")
    p_doctor.add_argument("--output", default=None)

    p_package = sub.add_parser("package-check")
    p_package.add_argument("--plugin", default=None, help="Plugin root to check. Defaults to ~/plugins/codex-workbench when present.")
    p_package.add_argument("--expected-version", default=None)
    p_package.add_argument("--write-report", action="store_true")
    p_package.add_argument("--output", default=None)

    p_user = sub.add_parser("user-workbench")
    p_user.add_argument("--codex-home", default=None, help="Target Codex user config directory. Defaults to CODEX_HOME or ~/.codex.")
    p_user.add_argument("--apply", action="store_true", help="Write files. Without this flag, preview only.")
    p_user.add_argument("--force", action="store_true", help="Replace existing files after creating backups.")
    p_user.add_argument("--output", default=None)

    args = parser.parse_args(argv)

    if args.command == "inspect":
        project = resolve_project(args.project)
        write_json(inspect_project(project), args.output)
        return 0
    if args.command == "generate":
        project = resolve_project(args.project)
        name = args.name or project.name
        write_json(generate_adapter(project, name, args.force, args.dry_run), args.output)
        return 0
    if args.command == "upgrade":
        project = resolve_project(args.project)
        name = args.name or project.name
        if args.apply and args.dry_run:
            raise SystemExit("Use either --apply or --dry-run, not both.")
        dry_run = not args.apply
        write_json(
            upgrade_adapter(project, name, dry_run, args.replace_docs, args.refresh_generated),
            args.output,
        )
        return 0
    if args.command == "feature":
        project = resolve_project(args.project)
        write_json(create_feature_package(project, args.name, args.dry_run, args.force), args.output)
        return 0
    if args.command == "validate":
        project = resolve_project(args.project)
        report = validate_adapter(project)
        write_json(report, args.output)
        return 0 if report["passed"] else 1
    if args.command == "audit":
        project = resolve_project(args.project)
        report = audit_adapter(project)
        write_json(report, args.output)
        return 0 if report["passed"] else 1
    if args.command == "retention":
        project = resolve_project(args.project)
        report = retention_report(project, args.keep_reports, args.apply, args.write_report)
        write_json(report, args.output)
        return 0
    if args.command == "self-test":
        report = run_self_test()
        write_json(report, args.output)
        return 0 if report["passed"] else 1
    if args.command == "golden-test":
        report = run_golden_test()
        write_json(report, args.output)
        return 0 if report["passed"] else 1
    if args.command == "doctor":
        report = doctor_workbench(args.plugin)
        write_json(report, args.output)
        return 0 if report["passed"] else 1
    if args.command == "package-check":
        report = package_check_workbench(args.plugin, args.expected_version, args.write_report)
        write_json(report, args.output)
        return 0 if report["passed"] else 1
    if args.command == "user-workbench":
        report = install_user_workbench(args.codex_home, args.apply, args.force)
        write_json(report, args.output)
        return 0
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
