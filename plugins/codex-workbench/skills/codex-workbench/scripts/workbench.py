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
import fnmatch
import hashlib
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


WORKBENCH_VERSION = "2.0.0"

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
    "PROJECT_STATE.md",
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
    "workbench/delivery/CHANGE_LOG.md",
    "workbench/delivery/TRACEABILITY.md",
    "workbench/delivery/ITERATION_PLAN.md",
    "workbench/delivery/RELEASE_PLAN.md",
    "workbench/delivery/RELEASE_CHECKLIST.md",
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
    "workbench/runtime/WORKFLOW_STATE.schema.json",
    "workbench/runtime/BYPASS_LOG.md",
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
    "workbench/feature-template/CHANGE_REQUEST.md",
    "workbench/feature-template/IMPACT_ANALYSIS.md",
    "workbench/feature-template/SPEC.md",
    "workbench/feature-template/DESIGN.md",
    "workbench/feature-template/PLAN.md",
    "workbench/feature-template/TASKS.md",
    "workbench/feature-template/DECISIONS.md",
    "workbench/feature-template/IMPLEMENTATION_NOTES.md",
    "workbench/feature-template/VERIFY.md",
    "workbench/feature-template/REVIEW.md",
    "workbench/feature-template/CHANGELOG.md",
    "workbench/feature-template/FEATURE_STATUS.schema.json",
]

FEATURE_TEMPLATE_FILES = [
    "CHANGE_REQUEST.md",
    "IMPACT_ANALYSIS.md",
    "SPEC.md",
    "DESIGN.md",
    "PLAN.md",
    "TASKS.md",
    "DECISIONS.md",
    "IMPLEMENTATION_NOTES.md",
    "VERIFY.md",
    "REVIEW.md",
    "CHANGELOG.md",
    "FEATURE_STATUS.schema.json",
]

FEATURE_PACKAGE_FILES = [
    "CHANGE_REQUEST.md",
    "IMPACT_ANALYSIS.md",
    "SPEC.md",
    "DESIGN.md",
    "PLAN.md",
    "TASKS.md",
    "DECISIONS.md",
    "IMPLEMENTATION_NOTES.md",
    "VERIFY.md",
    "REVIEW.md",
    "CHANGELOG.md",
    "FEATURE_STATUS.json",
]

REQUIRED_ADAPTER_TEXT_BY_FILE = {
    "AGENTS.md": [
        "需求不清",
        "完成标准",
        "执行门禁",
        "目录契约",
        "偏离复盘",
        "quality_gate.py",
        "PRODUCT_BRIEF.md",
        "PRD.md",
        "UX_SPEC.md",
        "ARCHITECTURE.md",
        "light",
        "standard",
        "strict",
        "hard triggers",
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
    "PROJECT_STATE.md": [
        "当前事实",
        "active_feature",
        "current_stage",
        "验证命令",
        "关键约束",
    ],
    "WORKBENCH.md": [
        "quality_gate.py",
        "接收者配置",
        "工作台审计",
        "标准开发流程",
        "执行门禁",
        "目录契约",
        "偏离复盘",
        "PRODUCT_BRIEF.md",
        "PRD.md",
        "UX_SPEC.md",
        "ARCHITECTURE.md",
        "ITERATION_LOG.md",
        "AI_EFFECTIVENESS.md",
        "light",
        "standard",
        "strict",
        "hard triggers",
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
    "workbench/delivery/CHANGE_LOG.md": [
        "change_id",
        "scope",
        "risk",
        "validation",
        "gate_marker",
    ],
    "workbench/delivery/TRACEABILITY.md": [
        "追踪矩阵",
        "来源",
        "实现位置",
        "验证位置",
        "covered",
    ],
    "workbench/delivery/ITERATION_PLAN.md": [
        "迭代计划",
        "变更",
        "复测结果",
        "下一轮",
    ],
    "workbench/delivery/RELEASE_CHECKLIST.md": [
        "发布检查",
        "回滚",
        "质量门",
        "风险确认",
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
        "状态机",
        "CHANGE_REQUEST.md",
        "IMPACT_ANALYSIS.md",
        "FEATURE_STATUS.json",
        "light",
        "standard",
        "strict",
        "hard triggers",
        "影响分析",
        "SPEC.md",
        "DESIGN.md",
        "PLAN.md",
        "TASKS.md",
        "DECISIONS.md",
        "IMPLEMENTATION_NOTES.md",
        "VERIFY.md",
        "REVIEW.md",
        "CHANGELOG.md",
    ],
    "workbench/feature-template/CHANGE_REQUEST.md": [
        "change_id",
        "目标",
        "范围",
        "非目标",
        "验收标准",
    ],
    "workbench/feature-template/IMPACT_ANALYSIS.md": [
        "影响分析",
        "PRD",
        "UX",
        "API",
        "TRACEABILITY",
    ],
    "workbench/feature-template/SPEC.md": [
        "用户目标",
        "验收标准",
        "范围",
        "approved_for_plan",
        "risk_level",
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
    "workbench/feature-template/VERIFY.md": [
        "status",
        "验证命令",
        "验收记录",
        "workbench_upgrade_assessment",
        "accepted_risk",
        "deferred_follow_up",
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
    "workbench/feature-template/FEATURE_STATUS.schema.json": [
        "current_stage",
        "implementation_allowed",
        "delivery_allowed",
        "required_artifacts",
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
    re.compile(r"[A-Za-z]:(?:\\+)Users(?:\\+)[^\\\s\"']+"),
    re.compile(r"[A-Za-z]:/+Users/+[^/\\\s\"']+"),
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

ALLOWED_WORKBENCH_TOP_LEVEL_DIRS = {
    "product",
    "design",
    "architecture",
    "delivery",
    "feature-template",
    "features",
    "quality",
    "runtime",
    "scorecard",
    "review",
    "feedback",
    "archive",
}

PROJECT_FACING_DOC_FILES = [
    "AGENTS.md",
    "PROJECT_INTAKE.md",
    "WORKBENCH.md",
    "REVIEW.md",
    "DEVELOPMENT_FLOW.md",
    "PRODUCT_BASELINE.md",
    "FEATURE_WORKFLOW.md",
]

PROCESS_STATUSES = {"draft", "confirmed"}
INTAKE_STATUSES = {"draft", "confirmed"}
WORKFLOW_STAGE_ORDER = ["CLASSIFY", "BASELINE_CHECK", "CHANGE", "IMPACT", "ROUTE", "PLAN", "IMPLEMENT", "VERIFY", "REVIEW", "GATE", "LEARN", "DONE", "BLOCKED"]
WORKFLOW_STAGES = set(WORKFLOW_STAGE_ORDER)
FEATURE_STATUSES = {"active", "on_hold", "complete", "blocked", "failed", "repeated_issue"}
WORKFLOW_PROFILES = {"light", "standard", "strict", "unclassified"}
RISK_LEVELS_V2 = {"light", "standard", "strict", "unclassified"}
SPEC_STATUSES = {"draft", "approved", "blocked"}
DESIGN_STATUSES = {"draft", "approved", "blocked"}
PLAN_STATUSES = {"draft", "approved", "blocked"}
TASKS_STATUSES = {"draft", "ready", "blocked"}
VERIFY_STATUSES = {"missing", "partial", "passed", "failed", "blocked"}
REVIEW_STATUSES = {"pending", "passed", "failed", "blocked"}
FEATURE_VERIFICATION_STATUSES = {"not_run", "partial", "passed", "failed", "blocked"}
FEATURE_REVIEW_STATUSES = {"not_reviewed", "passed", "failed", "blocked"}
FEATURE_GATE_STATUSES = {"not_run", "passed", "failed", "stale"}
WORKBENCH_UPGRADE_ASSESSMENTS = {"required", "deferred", "not_required"}
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
    "scripts/workbench_lib/__init__.py",
    "scripts/workbench_lib/generated_scripts.py",
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
    re.compile(r"(?:^|[\\/])\.workbench-validation(?:[\\/]|$)", re.IGNORECASE),
    re.compile(r"(?:^|[\\/])(?:\.pytest_cache|\.mypy_cache|\.ruff_cache|\.cache)(?:[\\/]|$)", re.IGNORECASE),
    re.compile(r"(?:^|[\\/])(?:assets[\\/]assets|references[\\/]references|scripts[\\/]scripts|agents[\\/]agents)(?:[\\/]|$)", re.IGNORECASE),
    re.compile(r"(?:^|[\\/])legacy-skills(?:[\\/]|$)", re.IGNORECASE),
    re.compile(r"(?:^|[\\/])internal(?:[\\/]|$)", re.IGNORECASE),
]

AGENTS_MD_DEFAULT_LIMIT_BYTES = 32 * 1024
AGENTS_MD_NEAR_LIMIT_BYTES = 24 * 1024

PACKAGING_MANIFEST_REQUIRED_INCLUDES = [
    ".codex-plugin/plugin.json",
    ".gitignore",
    "README.md",
    "hooks/**",
    "docs/CODEX_WORKBENCH_2_0_ARCHITECTURE.md",
    "docs/WORKFLOW_AND_SCORECARD.md",
    "docs/ITERATION_UPGRADE.md",
    "docs/USER_WORKBENCH.md",
    "skills/codex-workbench/**",
    "docs/maintenance/**",
]

PACKAGING_MANIFEST_REQUIRED_EXCLUDES = [
    "internal/**",
    "skills/codex-workbench/assets/assets/**",
    "skills/codex-workbench/references/references/**",
    "skills/codex-workbench/scripts/scripts/**",
    "skills/codex-workbench/agents/agents/**",
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
        text = path.read_text(encoding="utf-8")
        if text.startswith("\ufeff"):
            text = text.lstrip("\ufeff")
        return json.loads(text)
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
    from workbench_lib import generated_scripts

    return generated_scripts.generate_quality_gate_py(
        commands,
        FEATURE_PACKAGE_FILES,
        ALLOWED_WORKBENCH_TOP_LEVEL_DIRS,
        WORKBENCH_VERSION,
    )


def generate_scorecard_py() -> str:
    from workbench_lib import generated_scripts

    return generated_scripts.generate_scorecard_py(FEATURE_PACKAGE_FILES, REQUIRED_ADAPTER_FILES)


def generate_py_wrapper(script_name: str) -> str:
    from workbench_lib import generated_scripts

    return generated_scripts.generate_py_wrapper(script_name)


def generate_sh_wrapper(script_name: str) -> str:
    from workbench_lib import generated_scripts

    return generated_scripts.generate_sh_wrapper(script_name)


def generate_runtime_gate_py() -> str:
    from workbench_lib import generated_scripts

    return generated_scripts.generate_runtime_gate_py(WORKBENCH_VERSION)


def generate_api_smoke_py() -> str:
    from workbench_lib import generated_scripts

    return generated_scripts.generate_api_smoke_py()


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
- 当前功能包：`workbench/features/<feature-name>/CHANGE_REQUEST.md`、`IMPACT_ANALYSIS.md`、`SPEC.md`、`DESIGN.md`、`PLAN.md`、`TASKS.md`、`VERIFY.md`、`REVIEW.md`、`FEATURE_STATUS.json`
- 质量和证据审计：`.workbench-validation/`、`workbench/scorecard/SCORECARD.md`、`workbench/scorecard/CALIBRATION.md`

然后检查当前 diff 或用户明确指定的文件。

审查重点：

- 行为是否满足 `PROJECT_INTAKE.md`、PRD、功能 `SPEC.md` 和验收标准。
- 权限、数据所有权、租户/组织/用户/课程/文件等边界是否被破坏。
- API、数据库、前后端契约和外部服务调用是否兼容。
- 测试和质量门是否足以支持本次验收结论；语义正确性仍需结合需求、人工/独立审查和实际验收。
- `scorecard` 是否只被当作证据审计，而不是被误用成质量裁判。
- 是否存在 AI 生成代码常见问题：虚构 API、绕过既有封装、缺少错误处理、只改实现不改验证。
- 是否出现重复失败、审查漏报或质量门缺口，应该沉淀到模板、测试、CI、hook、质量门或 review 规则。

输出 findings 优先，按 `P0/P1/P2/Nit` 排序。每条包含文件路径、行号、风险、触发场景和修复方向。

最后补充：

- 未发现 P0/P1 问题时，明确写“未发现 P0/P1 问题”。
- 列出验证缺口和仍需人工确认的业务/产品/架构判断。
- 给出 `workbench_upgrade_assessment` 建议：`required`、`deferred` 或 `not_required`。
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
    files = {
        "AGENTS.md": render_template("AGENTS.md", variables, generate_agents_md(name, inspection)),
        "PROJECT_INTAKE.md": render_template("PROJECT_INTAKE.md", variables, ""),
        "PROJECT_STATE.md": render_template("PROJECT_STATE.md", variables, ""),
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
        "workbench/delivery/CHANGE_LOG.md": render_template("workbench/delivery/CHANGE_LOG.md", variables, ""),
        "workbench/delivery/TRACEABILITY.md": render_template("workbench/delivery/TRACEABILITY.md", variables, ""),
        "workbench/delivery/RELEASE_PLAN.md": render_template("workbench/delivery/RELEASE_PLAN.md", variables, ""),
        "workbench/delivery/ITERATION_PLAN.md": render_template("workbench/delivery/ITERATION_PLAN.md", variables, ""),
        "workbench/delivery/RELEASE_CHECKLIST.md": render_template("workbench/delivery/RELEASE_CHECKLIST.md", variables, ""),
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
        "workbench/runtime/WORKFLOW_STATE.schema.json": render_template("workbench/runtime/WORKFLOW_STATE.schema.json", variables, ""),
        "workbench/runtime/BYPASS_LOG.md": render_template("workbench/runtime/BYPASS_LOG.md", variables, ""),
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
    }
    for filename in FEATURE_TEMPLATE_FILES:
        rel = f"workbench/feature-template/{filename}"
        files[rel] = render_template(rel, variables, "")
    return files


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


def initial_feature_status(feature_id: str, profile: str = "unclassified") -> dict[str, Any]:
    required_artifacts = [filename for filename in FEATURE_PACKAGE_FILES if filename != "FEATURE_STATUS.json"]
    return {
        "schema": "codex-workbench-feature-status/v2",
        "feature_id": feature_id,
        "feature_status": "active",
        "risk_level": profile,
        "workflow_profile": profile,
        "current_stage": "CHANGE",
        "implementation_allowed": False,
        "delivery_allowed": False,
        "required_artifacts": required_artifacts,
        "verification_status": "not_run",
        "review_status": "not_reviewed",
        "gate_status": "not_run",
        "workbench_upgrade_assessment": "unassessed",
        "source_hashes": {},
    }


def create_feature_package(project: Path, name: str, dry_run: bool, force: bool) -> dict[str, Any]:
    inspection = inspect_project(project)
    variables = template_variables(project.name, inspection)
    slug = slugify_feature_name(name)
    target_root = project / "workbench" / "features" / slug
    actions: dict[str, dict[str, str]] = {}
    for filename in FEATURE_PACKAGE_FILES:
        rel_target = f"workbench/features/{slug}/{filename}"
        if filename == "FEATURE_STATUS.json":
            content = json.dumps(initial_feature_status(slug), ensure_ascii=False, indent=2) + "\n"
        else:
            rel_template = f"workbench/feature-template/{filename}"
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
    directory_contract_report = directory_contract(project)
    directory_errors = directory_contract_report["errors"]
    directory_warnings = directory_contract_report["warnings"]
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
        "directoryErrors": directory_errors,
        "directoryWarnings": directory_warnings,
        "intakeStatus": intake_status,
        "intakeStatusError": intake_status_error,
        "processStatus": process_status,
        "processStatusError": process_status_error,
        "passed": not missing and not placeholders and not python_errors and not feature_errors and not directory_errors and not intake_status_error and not process_status_error,
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


def directory_contract(project: Path) -> dict[str, list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    workbench = project / "workbench"
    if workbench.exists():
        for child in sorted(workbench.iterdir(), key=lambda item: item.name.lower()):
            rel = rel_to(project, child)
            if child.is_dir() and child.name not in ALLOWED_WORKBENCH_TOP_LEVEL_DIRS:
                errors.append(
                    f"{rel}: undeclared workbench top-level directory. Move it under an allowed directory, "
                    "document it in WORKBENCH.md, or update the workbench directory contract."
                )
            elif child.is_file():
                warnings.append(
                    f"{rel}: unexpected file directly under workbench/. Put durable evidence in a declared subdirectory."
                )

    docs_dir = project / "docs"
    if docs_dir.exists() and workbench.exists():
        warnings.append(
            "docs/: root docs directory exists. Treat it as project-owned documentation unless WORKBENCH.md explicitly classifies it; "
            "do not let AI invent it as a workbench stage."
        )

    return {"errors": errors, "warnings": warnings}


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
    spec = texts.get("SPEC.md", "")
    status_json = read_json(package / "FEATURE_STATUS.json") or {}
    return {
        "featureStatus": str(status_json.get("feature_status") or "active").lower(),
        "currentStage": str(status_json.get("current_stage") or "CHANGE").upper(),
        "riskLevel": str(status_json.get("risk_level") or frontmatter_field(spec, "risk_level") or "unclassified").lower(),
        "workflowProfile": str(status_json.get("workflow_profile") or frontmatter_field(spec, "workflow_profile") or "unclassified").lower(),
        "impactScore": frontmatter_int(spec, "impact_score"),
        "uncertaintyScore": frontmatter_int(spec, "uncertainty_score"),
        "rollbackScore": frontmatter_int(spec, "rollback_score"),
        "riskScore": frontmatter_int(spec, "risk_score"),
        "hardTriggers": frontmatter_field(spec, "hard_triggers"),
        "classificationReason": frontmatter_field(spec, "classification_reason"),
        "changeStatus": (frontmatter_field(texts.get("CHANGE_REQUEST.md", ""), "status") or "draft").lower(),
        "impactStatus": (frontmatter_field(texts.get("IMPACT_ANALYSIS.md", ""), "status") or "draft").lower(),
        "specStatus": (frontmatter_field(spec, "status") or "draft").lower(),
        "designStatus": (frontmatter_field(texts.get("DESIGN.md", ""), "status") or "draft").lower(),
        "planStatus": (frontmatter_field(texts.get("PLAN.md", ""), "status") or "draft").lower(),
        "tasksStatus": (frontmatter_field(texts.get("TASKS.md", ""), "status") or "draft").lower(),
        "implementationAllowed": bool(status_json.get("implementation_allowed")),
        "deliveryAllowed": bool(status_json.get("delivery_allowed")),
        "specApprovedForPlan": frontmatter_bool(texts.get("SPEC.md", ""), "approved_for_plan"),
        "designApprovedForPlan": frontmatter_bool(texts.get("DESIGN.md", ""), "approved_for_plan"),
        "planApprovedForTasks": frontmatter_bool(texts.get("PLAN.md", ""), "approved_for_tasks"),
        "planApprovedForImplementation": frontmatter_bool(texts.get("PLAN.md", ""), "approved_for_implementation"),
        "tasksReadyForImplementation": frontmatter_bool(texts.get("TASKS.md", ""), "ready_for_implementation"),
        "verifyStatus": (frontmatter_field(texts.get("VERIFY.md", ""), "status") or "missing").lower(),
        "reviewStatus": (frontmatter_field(texts.get("REVIEW.md", ""), "status") or "pending").lower(),
        "workbenchUpgradeAssessment": (frontmatter_field(texts.get("REVIEW.md", ""), "workbench_upgrade_assessment") or "unassessed").lower(),
        "featureVerificationStatus": str(status_json.get("verification_status") or "not_run").lower(),
        "featureReviewStatus": str(status_json.get("review_status") or "not_reviewed").lower(),
        "featureGateStatus": str(status_json.get("gate_status") or "not_run").lower(),
        "statusUpgradeAssessment": str(status_json.get("workbench_upgrade_assessment") or "unassessed").lower(),
        "requiredArtifacts": status_json.get("required_artifacts") if isinstance(status_json.get("required_artifacts"), list) else [],
        "hasStatusJson": bool(status_json),
        "verifyEmpty": "|  |  |  |" in texts.get("VERIFY.md", "") and "- [ ] 可以交付。" in texts.get("VERIFY.md", ""),
        "hasUncheckedTasks": bool(re.search(r"(?m)^- \[ \]", texts.get("TASKS.md", ""))),
    }


def workflow_stage_index(stage: str) -> int:
    try:
        return WORKFLOW_STAGE_ORDER.index(stage)
    except ValueError:
        return -1


def workflow_stage_reached(state: dict[str, Any], stage: str) -> bool:
    current = workflow_stage_index(state["currentStage"])
    expected = workflow_stage_index(stage)
    return current >= expected and expected >= 0


def feature_state_errors(state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not state["hasStatusJson"]:
        errors.append("missing FEATURE_STATUS.json")
    if state["featureStatus"] not in FEATURE_STATUSES:
        errors.append(f"invalid feature_status '{state['featureStatus']}'")
    if state["currentStage"] not in WORKFLOW_STAGES:
        errors.append(f"invalid current_stage '{state['currentStage']}'")
    if state["featureStatus"] == "on_hold":
        return errors
    if state["riskLevel"] not in RISK_LEVELS_V2:
        errors.append(f"invalid risk_level '{state['riskLevel']}'")
    if state["workflowProfile"] not in WORKFLOW_PROFILES:
        errors.append(f"invalid workflow_profile '{state['workflowProfile']}'")
    if state["featureVerificationStatus"] not in FEATURE_VERIFICATION_STATUSES:
        errors.append(f"invalid verification_status '{state['featureVerificationStatus']}'")
    if state["featureReviewStatus"] not in FEATURE_REVIEW_STATUSES:
        errors.append(f"invalid review_status '{state['featureReviewStatus']}'")
    if state["featureGateStatus"] not in FEATURE_GATE_STATUSES:
        errors.append(f"invalid gate_status '{state['featureGateStatus']}'")
    expected_artifacts = [filename for filename in FEATURE_PACKAGE_FILES if filename != "FEATURE_STATUS.json"]
    missing_required_artifacts = [filename for filename in expected_artifacts if filename not in state["requiredArtifacts"]]
    if missing_required_artifacts:
        errors.append(f"FEATURE_STATUS.json missing required_artifacts entries: {', '.join(missing_required_artifacts)}")
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
        if expected_score >= 6 and state["workflowProfile"] != "strict":
            errors.append("workflow_profile is too low for risk_score >= 6")
        if expected_score >= 3 and state["workflowProfile"] == "light":
            errors.append("workflow_profile is too low for risk_score >= 3")
    if state["specStatus"] not in SPEC_STATUSES:
        errors.append(f"invalid SPEC.md status '{state['specStatus']}'")
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
    if state["statusUpgradeAssessment"] != "unassessed" and state["statusUpgradeAssessment"] not in WORKBENCH_UPGRADE_ASSESSMENTS:
        errors.append(f"invalid FEATURE_STATUS.json workbench_upgrade_assessment '{state['statusUpgradeAssessment']}'")
    if workflow_stage_reached(state, "PLAN") and state["impactStatus"] not in {"ready", "approved"}:
        errors.append("current_stage reached PLAN before IMPACT_ANALYSIS.md was ready")
    if workflow_stage_reached(state, "PLAN") and (state["specStatus"] != "approved" or not state["specApprovedForPlan"]):
        errors.append("current_stage reached plan before SPEC.md was approved_for_plan")
    if workflow_stage_reached(state, "PLAN") and (state["designStatus"] != "approved" or not state["designApprovedForPlan"]):
        errors.append("current_stage reached plan before DESIGN.md was approved_for_plan")
    if workflow_stage_reached(state, "IMPLEMENT") and (state["planStatus"] != "approved" or not state["planApprovedForTasks"]):
        errors.append("current_stage reached tasks before PLAN.md was approved_for_tasks")
    if workflow_stage_reached(state, "IMPLEMENT") and (not state["planApprovedForImplementation"] or state["tasksStatus"] != "ready" or not state["tasksReadyForImplementation"]):
        errors.append("current_stage reached implement before PLAN/TASKS allowed implementation")
    if workflow_stage_reached(state, "REVIEW") and state["verifyStatus"] != "passed":
        errors.append("current_stage reached review before VERIFY.md passed")
    if state["currentStage"] == "DONE" and state["reviewStatus"] != "passed":
        errors.append("current_stage is complete before REVIEW.md passed")
    if state["implementationAllowed"] and (not state["planApprovedForImplementation"] or not state["tasksReadyForImplementation"]):
        errors.append("FEATURE_STATUS.json allows implementation before PLAN/TASKS allow it")
    if state["deliveryAllowed"] and (state["verifyStatus"] != "passed" or state["reviewStatus"] != "passed"):
        errors.append("FEATURE_STATUS.json allows delivery before VERIFY/REVIEW pass")
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
    for error in validation.get("directoryErrors", []):
        rel = error.split(":", 1)[0]
        findings.append(issue("P1", "directory-contract-violation", error, rel))
    for warning in validation.get("directoryWarnings", []):
        rel = warning.split(":", 1)[0] if ":" in warning else None
        code = "root-docs-needs-classification" if warning.startswith("docs/:") else "directory-contract-warning"
        findings.append(issue("P2", code, warning, rel))
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
                findings.append(issue("P1", "invalid-feature-state-field", error, f"{rel_package}/FEATURE_STATUS.json"))
            for error in stage_order_errors:
                findings.append(issue("P1", "invalid-feature-stage-order", error, f"{rel_package}/FEATURE_STATUS.json"))
            if invalid_state_errors:
                continue
            if state["featureStatus"] == "on_hold":
                continue
            if state["featureStatus"] == "active":
                findings.append(issue("P2", "active-feature-not-complete", "Feature package is active but not complete. Finish the state-machine stages before delivery, or set feature_status to on_hold if this is parked work.", f"{rel_package}/FEATURE_STATUS.json"))
            if not state["specApprovedForPlan"]:
                findings.append(issue("P2", "spec-not-approved", "SPEC.md is not approved for planning.", f"{rel_package}/SPEC.md"))
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
            if not state["implementationAllowed"] or not state["deliveryAllowed"] or state["hasUncheckedTasks"]:
                findings.append(issue("P2", "feature-stage-gates-incomplete", "Feature package still has incomplete state gates or unchecked tasks.", f"{rel_package}/FEATURE_STATUS.json"))

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
    for required in ("controlled_changed_paths", "has_valid_light_change_record", "quality_profile", "scorecard_decision", "passed_with_risk", "require_verify_evidence", "require_review_evidence", "require_traceability_evidence"):
        if quality_gate.exists() and required not in quality_gate_text:
            findings.append(issue("P1", "weak-quality-gate-contract", f"Quality gate is missing current hard-gate contract term: {required}", "workbench/quality/quality_gate.py"))
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
    status_path = root / "workbench" / "features" / slug / "FEATURE_STATUS.json"
    data = json.loads(status_path.read_text(encoding="utf-8"))
    data["feature_status"] = "on_hold"
    data["current_stage"] = "BLOCKED"
    status_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_command_capture(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=str(cwd), text=True, capture_output=True)


def find_powershell_command() -> list[str] | None:
    for executable in ("pwsh", "powershell", "powershell.exe"):
        resolved = shutil.which(executable)
        if not resolved:
            continue
        if executable == "pwsh":
            return [resolved, "-NoProfile", "-File"]
        return [resolved, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File"]
    return None


def find_plugin_root_for_hook_golden() -> Path | None:
    current = Path(__file__).resolve()
    for ancestor in current.parents:
        if (ancestor / "hooks" / "workbench-hard-gate.ps1").exists():
            return ancestor
    plugin = default_plugin_root()
    if plugin and (plugin / "hooks" / "workbench-hard-gate.ps1").exists():
        return plugin
    home_nested = Path.home() / "plugins" / "codex-workbench" / "plugins" / "codex-workbench"
    if (home_nested / "hooks" / "workbench-hard-gate.ps1").exists():
        return home_nested
    return None


def invoke_workbench_hook(plugin_root: Path, plugin_data: Path, payload: dict[str, Any]) -> dict[str, Any]:
    powershell = find_powershell_command()
    if not powershell:
        return {
            "returncode": 127,
            "stdout": "",
            "stderr": "PowerShell executable was not found",
            "json": {},
        }
    hook_script = plugin_root / "hooks" / "workbench-hard-gate.ps1"
    env = os.environ.copy()
    env["PLUGIN_ROOT"] = str(plugin_root)
    env["PLUGIN_DATA"] = str(plugin_data)
    result = subprocess.run(
        powershell + [str(hook_script)],
        input=json.dumps(payload, ensure_ascii=True).encode("utf-8"),
        cwd=str(plugin_root),
        capture_output=True,
        env=env,
    )
    stdout = result.stdout.decode("utf-8-sig", errors="replace").strip()
    stderr = result.stderr.decode("utf-8-sig", errors="replace").strip()
    try:
        parsed = json.loads(stdout) if stdout else {}
    except Exception:
        parsed = {}
    return {
        "returncode": result.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "json": parsed,
    }


def hook_pretooluse_permission_decision(result: dict[str, Any]) -> str:
    parsed = result.get("json")
    if not isinstance(parsed, dict):
        return ""
    output = parsed.get("hookSpecificOutput")
    if not isinstance(output, dict):
        return ""
    return str(output.get("permissionDecision") or "")


def run_generated_adapter_smoke(
    root: Path,
    label: str,
    failures: list[str],
    wrapper_expectations: tuple[tuple[str, str], ...] | None = None,
) -> dict[str, int | str]:
    results: dict[str, int | str] = {}

    def assert_wrapper(rel: str, script_name: str) -> None:
        path = root / rel
        if not path.exists():
            failures.append(f"{label}: generated wrapper is missing: {rel}")
            return
        text = path.read_text(encoding="utf-8")
        assert_condition(script_name in text, f"{label}: {rel} does not delegate to {script_name}", failures)

    def run(label_suffix: str, command: list[str]) -> None:
        result = run_command_capture(command, root)
        results[label_suffix] = result.returncode
        assert_condition(
            result.returncode == 0,
            f"{label}: generated script smoke failed for {label_suffix}: {result.stderr or result.stdout}",
            failures,
        )

    run("runtime_gate.py --write-state", [sys.executable, "workbench/runtime/runtime_gate.py", "--write-state"])
    assert_condition((root / ".workbench-validation" / "runtime-state.json").exists(), f"{label}: runtime_gate.py did not write runtime-state.json", failures)
    run("api_smoke.py --help", [sys.executable, "workbench/runtime/api_smoke.py", "--help"])
    run("quality_gate.py --help", [sys.executable, "workbench/quality/quality_gate.py", "--help"])
    run("scorecard.py --help", [sys.executable, "workbench/scorecard/scorecard.py", "--help"])
    expectations = wrapper_expectations or (
        ("workbench/runtime/runtime-gate.ps1", "runtime_gate.py"),
        ("workbench/runtime/api-smoke.ps1", "api_smoke.py"),
        ("workbench/quality/quality-gate.ps1", "quality_gate.py"),
        ("workbench/scorecard/scorecard.ps1", "scorecard.py"),
        ("workbench/runtime/runtime-gate.sh", "runtime_gate.py"),
        ("workbench/runtime/api-smoke.sh", "api_smoke.py"),
        ("workbench/quality/quality-gate.sh", "quality_gate.py"),
        ("workbench/scorecard/scorecard.sh", "scorecard.py"),
    )
    for rel, script_name in expectations:
        assert_wrapper(rel, script_name)

    powershell = find_powershell_command()
    if powershell:
        run("runtime-gate.ps1 --write-state", powershell + ["workbench/runtime/runtime-gate.ps1", "--write-state"])
        run("api-smoke.ps1 --help", powershell + ["workbench/runtime/api-smoke.ps1", "--help"])
        run("quality-gate.ps1 --help", powershell + ["workbench/quality/quality-gate.ps1", "--help"])
        run("scorecard.ps1 --help", powershell + ["workbench/scorecard/scorecard.ps1", "--help"])
    else:
        results["powershell_wrappers"] = "skipped"

    sh = shutil.which("sh")
    if sh:
        run("runtime-gate.sh --write-state", [sh, "workbench/runtime/runtime-gate.sh", "--write-state"])
        run("api-smoke.sh --help", [sh, "workbench/runtime/api-smoke.sh", "--help"])
        run("quality-gate.sh --help", [sh, "workbench/quality/quality-gate.sh", "--help"])
        run("scorecard.sh --help", [sh, "workbench/scorecard/scorecard.sh", "--help"])
    else:
        results["sh_wrappers"] = "skipped"

    return results


def setup_local_git(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=str(root), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    subprocess.run(["git", "config", "user.email", "audit@example.local"], cwd=str(root), check=True)
    subprocess.run(["git", "config", "user.name", "Workbench Audit"], cwd=str(root), check=True)


def commit_all(root: Path, message: str) -> None:
    subprocess.run(["git", "add", "."], cwd=str(root), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=str(root), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def fixture_command_output(root: Path, command: list[str]) -> str:
    try:
        result = subprocess.run(command, cwd=str(root), text=True, capture_output=True, timeout=20)
    except Exception:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.rstrip("\r\n")


def fixture_git_head(root: Path) -> str:
    return fixture_command_output(root, ["git", "rev-parse", "HEAD"]) or "unavailable"


def fixture_diff_hash(root: Path) -> str:
    try:
        result = subprocess.run(["git", "diff", "--binary", "HEAD"], cwd=str(root), capture_output=True, timeout=30)
        payload = result.stdout if result.returncode == 0 else b""
    except Exception:
        payload = b""
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def fixture_text_sha256(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


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
        assert_condition((root / "PROJECT_STATE.md").exists(), f"{name}: PROJECT_STATE.md was not generated", failures)
        assert_condition((root / "workbench" / "delivery" / "CHANGE_LOG.md").exists(), f"{name}: CHANGE_LOG.md was not generated", failures)
        assert_condition((root / "workbench" / "delivery" / "TRACEABILITY.md").exists(), f"{name}: TRACEABILITY.md was not generated", failures)
        assert_condition((root / "workbench" / "runtime" / "WORKFLOW_STATE.schema.json").exists(), f"{name}: WORKFLOW_STATE schema was not generated", failures)
        assert_condition((root / "workbench" / "runtime" / "BYPASS_LOG.md").exists(), f"{name}: BYPASS_LOG.md was not generated", failures)
        assert_condition((root / "workbench" / "feature-template" / "CHANGE_REQUEST.md").exists(), f"{name}: feature CHANGE_REQUEST template was not generated", failures)
        assert_condition((root / "workbench" / "feature-template" / "IMPACT_ANALYSIS.md").exists(), f"{name}: feature IMPACT_ANALYSIS template was not generated", failures)
        assert_condition((root / "workbench" / "feature-template" / "SPEC.md").exists(), f"{name}: feature SPEC template was not generated", failures)
        assert_condition((root / "workbench" / "feature-template" / "DESIGN.md").exists(), f"{name}: feature DESIGN template was not generated", failures)
        assert_condition((root / "workbench" / "feature-template" / "DECISIONS.md").exists(), f"{name}: feature DECISIONS template was not generated", failures)
        assert_condition((root / "workbench" / "feature-template" / "IMPLEMENTATION_NOTES.md").exists(), f"{name}: feature IMPLEMENTATION_NOTES template was not generated", failures)
        assert_condition((root / "workbench" / "feature-template" / "FEATURE_STATUS.schema.json").exists(), f"{name}: feature status schema was not generated", failures)
        assert_condition((root / "workbench" / "feature-template" / "VERIFY.md").exists(), f"{name}: feature VERIFY template was not generated", failures)
        assert_condition((root / "workbench" / "feature-template" / "CHANGELOG.md").exists(), f"{name}: feature CHANGELOG template was not generated", failures)
        feature_preview = create_feature_package(root, "User Login", dry_run=True, force=False)
        assert_condition(feature_preview["featureSlug"] == "user-login", f"{name}: feature slug was not normalized", failures)
        feature = create_feature_package(root, "User Login", dry_run=False, force=False)
        assert_condition((root / "workbench" / "features" / "user-login" / "CHANGE_REQUEST.md").exists(), f"{name}: feature package CHANGE_REQUEST was not created", failures)
        assert_condition((root / "workbench" / "features" / "user-login" / "IMPACT_ANALYSIS.md").exists(), f"{name}: feature package IMPACT_ANALYSIS was not created", failures)
        assert_condition((root / "workbench" / "features" / "user-login" / "SPEC.md").exists(), f"{name}: feature package SPEC was not created", failures)
        assert_condition((root / "workbench" / "features" / "user-login" / "DESIGN.md").exists(), f"{name}: feature package DESIGN was not created", failures)
        assert_condition((root / "workbench" / "features" / "user-login" / "DECISIONS.md").exists(), f"{name}: feature package DECISIONS was not created", failures)
        assert_condition((root / "workbench" / "features" / "user-login" / "CHANGELOG.md").exists(), f"{name}: feature package CHANGELOG was not created", failures)
        assert_condition((root / "workbench" / "features" / "user-login" / "FEATURE_STATUS.json").exists(), f"{name}: feature package FEATURE_STATUS was not created", failures)
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
        script_smoke = run_generated_adapter_smoke(root, name, failures)
        return {
            "name": name,
            "passed": not failures,
            "failures": failures,
            "qualityCommandCount": len(inspection["qualityCommands"]),
            "generatedFileCount": len(generation["files"]),
            "featureFileCount": len(feature["files"]),
            "auditSummary": audit_after_hold["summary"],
            "scriptSmoke": script_smoke,
        }


def run_upgrade_golden_case() -> dict[str, Any]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="codex-workbench-golden-old-workbench-") as tmp:
        root = Path(tmp)
        write_sample_old_workbench(root)
        preview = upgrade_adapter(root, "old-workbench", dry_run=True, replace_docs=False, refresh_generated=False)
        assert_condition(preview["files"]["AGENTS.md"]["action"] == "keep-existing-doc", "upgrade should preserve existing AGENTS.md by default", failures)
        assert_condition(preview["files"]["PROJECT_INTAKE.md"]["action"] == "write-missing", "upgrade should add missing PROJECT_INTAKE.md", failures)
        assert_condition(preview["files"]["PROJECT_STATE.md"]["action"] == "write-missing", "upgrade should add missing PROJECT_STATE.md", failures)
        assert_condition(preview["files"]["DEVELOPMENT_FLOW.md"]["action"] == "write-missing", "upgrade should add missing DEVELOPMENT_FLOW.md", failures)
        assert_condition(preview["files"]["PRODUCT_BASELINE.md"]["action"] == "write-missing", "upgrade should add missing PRODUCT_BASELINE.md", failures)
        assert_condition(preview["files"]["FEATURE_WORKFLOW.md"]["action"] == "write-missing", "upgrade should add missing FEATURE_WORKFLOW.md", failures)
        assert_condition(preview["files"]["workbench/product/PRODUCT_BRIEF.md"]["action"] == "write-missing", "upgrade should add missing PRODUCT_BRIEF.md", failures)
        assert_condition(preview["files"]["workbench/design/UX_SPEC.md"]["action"] == "write-missing", "upgrade should add missing UX_SPEC.md", failures)
        assert_condition(preview["files"]["workbench/architecture/ARCHITECTURE.md"]["action"] == "write-missing", "upgrade should add missing ARCHITECTURE.md", failures)
        assert_condition(preview["files"]["workbench/delivery/TRACEABILITY.md"]["action"] == "write-missing", "upgrade should add missing TRACEABILITY.md", failures)
        assert_condition(preview["files"]["workbench/delivery/CHANGE_LOG.md"]["action"] == "write-missing", "upgrade should add missing CHANGE_LOG.md", failures)
        assert_condition(preview["files"]["workbench/scorecard/RUBRIC.md"]["action"] == "write-missing", "upgrade should add missing scorecard RUBRIC.md", failures)
        assert_condition(preview["files"]["workbench/scorecard/CALIBRATION.md"]["action"] == "write-missing", "upgrade should add missing scorecard CALIBRATION.md", failures)
        assert_condition(preview["files"]["workbench/scorecard/scorecard.py"]["action"] == "write-missing", "upgrade should add missing scorecard.py", failures)
        assert_condition(preview["files"]["workbench/quality/quality_gate.py"]["action"] == "write-missing", "upgrade should add missing Python quality gate", failures)
        assert_condition(preview["files"]["workbench/runtime/runtime_gate.py"]["action"] == "write-missing", "upgrade should add missing runtime_gate.py", failures)
        assert_condition(preview["files"]["workbench/runtime/api_smoke.py"]["action"] == "write-missing", "upgrade should add missing api_smoke.py", failures)
        assert_condition(preview["files"]["workbench/runtime/runtime-gate.ps1"]["action"] == "write-missing", "upgrade should add missing runtime-gate.ps1", failures)
        assert_condition(preview["files"]["workbench/runtime/api-smoke.ps1"]["action"] == "write-missing", "upgrade should add missing api-smoke.ps1", failures)
        assert_condition(preview["files"]["workbench/runtime/runtime-gate.sh"]["action"] == "write-missing", "upgrade should add missing runtime-gate.sh", failures)
        assert_condition(preview["files"]["workbench/runtime/api-smoke.sh"]["action"] == "write-missing", "upgrade should add missing api-smoke.sh", failures)
        applied = upgrade_adapter(root, "old-workbench", dry_run=False, replace_docs=False, refresh_generated=False)
        validation = validate_adapter(root)
        audit = audit_adapter(root)
        assert_condition((root / "AGENTS.md").read_text(encoding="utf-8").startswith("# Old Rules"), "upgrade overwrote existing AGENTS.md", failures)
        assert_condition((root / "PROJECT_INTAKE.md").exists(), "upgrade did not write missing PROJECT_INTAKE.md", failures)
        assert_condition((root / "PROJECT_STATE.md").exists(), "upgrade did not write missing PROJECT_STATE.md", failures)
        assert_condition((root / "DEVELOPMENT_FLOW.md").exists(), "upgrade did not write missing DEVELOPMENT_FLOW.md", failures)
        assert_condition((root / "PRODUCT_BASELINE.md").exists(), "upgrade did not write missing PRODUCT_BASELINE.md", failures)
        assert_condition((root / "FEATURE_WORKFLOW.md").exists(), "upgrade did not write missing FEATURE_WORKFLOW.md", failures)
        assert_condition((root / "workbench" / "product" / "PRODUCT_BRIEF.md").exists(), "upgrade did not write missing PRODUCT_BRIEF.md", failures)
        assert_condition((root / "workbench" / "design" / "UX_SPEC.md").exists(), "upgrade did not write missing UX_SPEC.md", failures)
        assert_condition((root / "workbench" / "architecture" / "ARCHITECTURE.md").exists(), "upgrade did not write missing ARCHITECTURE.md", failures)
        assert_condition((root / "workbench" / "delivery" / "TRACEABILITY.md").exists(), "upgrade did not write missing TRACEABILITY.md", failures)
        assert_condition((root / "workbench" / "delivery" / "CHANGE_LOG.md").exists(), "upgrade did not write missing CHANGE_LOG.md", failures)
        assert_condition((root / "workbench" / "scorecard" / "RUBRIC.md").exists(), "upgrade did not write scorecard RUBRIC.md", failures)
        assert_condition((root / "workbench" / "scorecard" / "CALIBRATION.md").exists(), "upgrade did not write scorecard CALIBRATION.md", failures)
        assert_condition((root / "workbench" / "scorecard" / "scorecard.py").exists(), "upgrade did not write scorecard.py", failures)
        assert_condition((root / "workbench" / "feature-template" / "CHANGE_REQUEST.md").exists(), "upgrade did not write feature change request template", failures)
        assert_condition((root / "workbench" / "feature-template" / "IMPACT_ANALYSIS.md").exists(), "upgrade did not write feature impact analysis template", failures)
        assert_condition((root / "workbench" / "feature-template" / "TASKS.md").exists(), "upgrade did not write feature task template", failures)
        assert_condition((root / "workbench" / "feature-template" / "DESIGN.md").exists(), "upgrade did not write feature design template", failures)
        assert_condition((root / "workbench" / "feature-template" / "DECISIONS.md").exists(), "upgrade did not write feature decisions template", failures)
        assert_condition((root / "workbench" / "feature-template" / "FEATURE_STATUS.schema.json").exists(), "upgrade did not write feature status schema", failures)
        assert_condition((root / "workbench" / "quality" / "quality_gate.py").exists(), "upgrade did not write missing quality_gate.py", failures)
        assert_condition((root / "workbench" / "runtime" / "runtime_gate.py").exists(), "upgrade did not write runtime_gate.py", failures)
        assert_condition((root / "workbench" / "runtime" / "api_smoke.py").exists(), "upgrade did not write api_smoke.py", failures)
        assert_condition((root / "workbench" / "runtime" / "runtime-gate.ps1").exists(), "upgrade did not write runtime-gate.ps1", failures)
        assert_condition((root / "workbench" / "runtime" / "api-smoke.ps1").exists(), "upgrade did not write api-smoke.ps1", failures)
        assert_condition((root / "workbench" / "runtime" / "runtime-gate.sh").exists(), "upgrade did not write runtime-gate.sh", failures)
        assert_condition((root / "workbench" / "runtime" / "api-smoke.sh").exists(), "upgrade did not write api-smoke.sh", failures)
        assert_condition(validation["passed"], "upgrade validation failed", failures)
        assert_condition(audit["summary"]["P0"] == 0, "upgrade audit has P0 findings", failures)
        upgrade_wrapper_expectations = (
            ("workbench/runtime/runtime-gate.ps1", "runtime_gate.py"),
            ("workbench/runtime/api-smoke.ps1", "api_smoke.py"),
            ("workbench/scorecard/scorecard.ps1", "scorecard.py"),
            ("workbench/runtime/runtime-gate.sh", "runtime_gate.py"),
            ("workbench/runtime/api-smoke.sh", "api_smoke.py"),
            ("workbench/quality/quality-gate.sh", "quality_gate.py"),
            ("workbench/scorecard/scorecard.sh", "scorecard.py"),
        )
        script_smoke = run_generated_adapter_smoke(root, "old-workbench-upgrade", failures, upgrade_wrapper_expectations)
        return {
            "name": "old-workbench-upgrade",
            "passed": not failures,
            "failures": failures,
            "previewActions": preview["files"],
            "appliedFileCount": len(applied["files"]),
            "auditSummary": audit["summary"],
            "scriptSmoke": script_smoke,
        }


def run_workbench_guard_golden_case() -> dict[str, Any]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="codex-workbench-golden-guardrails-") as tmp:
        root = Path(tmp)
        write_sample_node(root)
        generate_adapter(root, "guardrails", force=False, dry_run=False)

        rogue_dir = root / "workbench" / "docs"
        rogue_dir.mkdir(parents=True)
        (rogue_dir / "DELIVERY.md").write_text("# Invented Workbench Docs Layer\n", encoding="utf-8")
        validation = validate_adapter(root)
        audit = audit_adapter(root)
        assert_condition(not validation["passed"], "guardrails: undeclared workbench/docs should fail validation", failures)
        assert_condition(any("workbench/docs" in item for item in validation["directoryErrors"]), "guardrails: missing workbench/docs directory error", failures)
        assert_condition(any(finding["code"] == "directory-contract-violation" for finding in audit["findings"]), "guardrails: audit should report directory contract violation", failures)

        shutil.rmtree(rogue_dir)
        project_docs = root / "docs"
        project_docs.mkdir()
        (project_docs / "README.md").write_text("# Project Docs\n", encoding="utf-8")
        validation_with_root_docs = validate_adapter(root)
        audit_with_root_docs = audit_adapter(root)
        assert_condition(validation_with_root_docs["passed"], "guardrails: project-owned root docs should not fail validation", failures)
        assert_condition(any("root docs directory exists" in item for item in validation_with_root_docs["directoryWarnings"]), "guardrails: root docs should produce classification warning", failures)
        assert_condition(any(finding["code"] == "root-docs-needs-classification" for finding in audit_with_root_docs["findings"]), "guardrails: audit should warn about root docs classification", failures)

        return {
            "name": "workbench-guardrails",
            "passed": not failures,
            "failures": failures,
            "directoryErrors": validation["directoryErrors"],
            "directoryWarnings": validation_with_root_docs["directoryWarnings"],
            "auditSummary": audit_with_root_docs["summary"],
        }


def confirm_project_intake_for_fixture(root: Path) -> None:
    intake = root / "PROJECT_INTAKE.md"
    text = intake.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^status:\s*draft\s*$", "status: confirmed", text)
    text = re.sub(r"(?m)^(\| P\d+ \|[^|\n]+\|[^|\n]+\|)\s*\| open \|$", r"\1 answered | closed |", text)
    intake.write_text(text, encoding="utf-8")
    flow = root / "DEVELOPMENT_FLOW.md"
    flow_text = flow.read_text(encoding="utf-8")
    flow_text = re.sub(r"(?m)^status:\s*draft\s*$", "status: confirmed", flow_text)
    flow.write_text(flow_text, encoding="utf-8")


def replace_frontmatter_field(text: str, field: str, value: str) -> str:
    pattern = rf"(?m)^({re.escape(field)}\s*:\s*).*$"
    replacement = rf"\g<1>{value}"
    if re.search(pattern, text):
        return re.sub(pattern, replacement, text, count=1)
    return f"{field}: {value}\n" + text


def write_frontmatter_field(path: Path, field: str, value: str) -> None:
    path.write_text(replace_frontmatter_field(path.read_text(encoding="utf-8"), field, value), encoding="utf-8")


def set_feature_profile(package: Path, profile: str, traceability_required: bool = False) -> None:
    status_path = package / "FEATURE_STATUS.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    status.update(
        {
            "feature_status": "complete",
            "risk_level": profile,
            "workflow_profile": profile,
            "current_stage": "DONE",
            "implementation_allowed": True,
            "delivery_allowed": True,
            "verification_status": "passed",
            "review_status": "passed",
            "gate_status": "not_run",
            "workbench_upgrade_assessment": "not_required",
        }
    )
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    write_frontmatter_field(package / "CHANGE_REQUEST.md", "status", "ready")
    write_frontmatter_field(package / "CHANGE_REQUEST.md", "workflow_profile", profile)
    write_frontmatter_field(package / "IMPACT_ANALYSIS.md", "status", "ready")
    write_frontmatter_field(package / "IMPACT_ANALYSIS.md", "baseline_update_required", "false")
    write_frontmatter_field(package / "IMPACT_ANALYSIS.md", "traceability_update_required", "true" if traceability_required else "false")
    if traceability_required:
        impact = package / "IMPACT_ANALYSIS.md"
        impact_text = impact.read_text(encoding="utf-8")
        impact_text = re.sub(
            r"\|\s*\|\s*\|\s*update / keep / n/a\s*\|\s*`VERIFY\.md`\s*\|",
            "| REQ-GOLDEN-001 | `workbench/product/PRD.md` | update | `VERIFY.md` |",
            impact_text,
            count=1,
        )
        impact.write_text(impact_text, encoding="utf-8")

    spec = package / "SPEC.md"
    scores = (2, 2, 2) if profile == "strict" else (1, 1, 1)
    spec_text = spec.read_text(encoding="utf-8")
    for field, value in (
        ("status", "approved"),
        ("approved_for_plan", "true"),
        ("risk_level", profile),
        ("workflow_profile", profile),
        ("impact_score", str(scores[0])),
        ("uncertainty_score", str(scores[1])),
        ("rollback_score", str(scores[2])),
        ("risk_score", str(sum(scores))),
        ("hard_triggers", "none" if profile != "strict" else "strict traceability golden test"),
        ("classification_reason", "golden test fixture"),
    ):
        spec_text = replace_frontmatter_field(spec_text, field, value)
    spec.write_text(spec_text, encoding="utf-8")

    for filename in ("DESIGN.md",):
        write_frontmatter_field(package / filename, "status", "approved")
        write_frontmatter_field(package / filename, "approved_for_plan", "true")
    plan = package / "PLAN.md"
    plan_text = plan.read_text(encoding="utf-8")
    for field, value in (
        ("status", "approved"),
        ("approved_for_tasks", "true"),
        ("approved_for_implementation", "true"),
    ):
        plan_text = replace_frontmatter_field(plan_text, field, value)
    plan.write_text(plan_text, encoding="utf-8")

    tasks = package / "TASKS.md"
    tasks_text = tasks.read_text(encoding="utf-8")
    tasks_text = replace_frontmatter_field(tasks_text, "status", "ready")
    tasks_text = replace_frontmatter_field(tasks_text, "ready_for_implementation", "true")
    tasks_text = tasks_text.replace("- [ ]", "- [x]")
    tasks.write_text(tasks_text, encoding="utf-8")


def write_verify_fixture(package: Path, with_evidence: bool) -> None:
    verify = package / "VERIFY.md"
    text = verify.read_text(encoding="utf-8")
    text = replace_frontmatter_field(text, "status", "passed")
    text = replace_frontmatter_field(text, "verified_by", "golden-test")
    text = replace_frontmatter_field(text, "verified_at", "2026-06-19T00:00:00Z")
    if with_evidence:
        evidence_path = package.parents[2] / ".workbench-validation" / "golden-verify-evidence.log"
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text("golden verification evidence\n", encoding="utf-8")
        text = re.sub(
            r"\|\s*\|\s*\|\s*\|\s*\|",
            "| py -B workbench/quality/quality_gate.py --profile standard | passed | .workbench-validation/golden-verify-evidence.log | golden fixture |",
            text,
            count=1,
        )
        text = re.sub(
            r"\| 主成功路径 \|\s*\|\s*\|\s*\|\s*\|",
            "| 主成功路径 | run quality gate | evidence log is written | 通过 | .workbench-validation/golden-verify-evidence.log |",
            text,
            count=1,
        )
        text = text.replace("- [ ] 可以交付。", "- [x] 可以交付。")
    verify.write_text(text, encoding="utf-8")


def write_verify_accepted_risk_fixture(package: Path, complete: bool) -> None:
    verify = package / "VERIFY.md"
    text = verify.read_text(encoding="utf-8")
    if complete:
        replacement = "| external branch protection | local env cannot verify remote branch rule | merge could bypass local gate | true | user-confirmed-golden | CI required check + independent review | track branch protection setup before release |"
    else:
        replacement = "| external branch protection | local env cannot verify remote branch rule | merge could bypass local gate | true |  |  |  |"
    if re.search(r"\|\s*\|\s*\|\s*\|\s*false\s*\|\s*\|\s*\|\s*\|", text):
        text = re.sub(r"\|\s*\|\s*\|\s*\|\s*false\s*\|\s*\|\s*\|\s*\|", replacement, text, count=1)
    elif re.search(r"(?m)^\|\s*external branch protection\s*\|.*\|\s*$", text):
        text = re.sub(r"(?m)^\|\s*external branch protection\s*\|.*\|\s*$", replacement, text)
    else:
        text = text + "\n" + replacement + "\n"
    verify.write_text(text, encoding="utf-8")


def write_review_fixture(package: Path, clean: bool) -> None:
    review = package / "REVIEW.md"
    text = review.read_text(encoding="utf-8")
    text = replace_frontmatter_field(text, "status", "passed")
    text = replace_frontmatter_field(text, "reviewed_by", "golden-test")
    text = replace_frontmatter_field(text, "reviewed_at", "2026-06-19T00:00:00Z")
    text = replace_frontmatter_field(text, "workbench_upgrade_assessment", "not_required")
    if clean:
        text = text.replace("- [ ] 未发现 P0/P1。", "- [x] 未发现 P0/P1。")
        text = text.replace("- [x] 存在 P0/P1，不能交付。", "- [ ] 存在 P0/P1，不能交付。")
        text = re.sub(
            r"(## P0/P1 检查\s*\n)(.*?)(\n## 产品下限检查)",
            lambda match: match.group(1) + match.group(2).replace("- [ ]", "- [x]") + match.group(3),
            text,
            flags=re.S,
        )
        text = re.sub(
            r"```text\s*P1 path/to/file\.ext:123 - 问题标题.*?```",
            "无未解决 P0/P1。",
            text,
            flags=re.S,
        )
        text = re.sub(r"(?m)^P1 path/to/file\.ext:123 - unresolved golden blocker\s*$", "", text)
    else:
        text = text.replace("- [ ] 存在 P0/P1，不能交付。", "- [x] 存在 P0/P1，不能交付。")
        text += "\nP1 path/to/file.ext:123 - unresolved golden blocker\n"
    review.write_text(text, encoding="utf-8")


def mark_traceability_covered(root: Path) -> None:
    path = root / "workbench" / "delivery" / "TRACEABILITY.md"
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r"(?m)^\|\s*REQ-001\s*\|[^\n]*$",
        "| REQ-GOLDEN-001 | requirement | `workbench/product/PRD.md` | golden fixture | src/app.js | workbench/features/evidence-gate/VERIFY.md | covered | golden fixture evidence |",
        text,
        count=1,
    )
    path.write_text(text, encoding="utf-8")


def run_quality_gate_contract_golden_case() -> dict[str, Any]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="codex-workbench-golden-quality-gate-") as tmp:
        root = Path(tmp)
        setup_local_git(root)
        (root / "src").mkdir()
        (root / "src" / "app.js").write_text("console.log('v1')\n", encoding="utf-8")
        commit_all(root, "initial app")
        generate_adapter(root, "quality-gate-contract", force=False, dry_run=False)
        commands = [
            {
                "name": "python noop",
                "group": "python",
                "profiles": ["smoke", "standard", "full"],
                "cwd": ".",
                "command": [sys.executable, "-c", "print('quality-ok')"],
            }
        ]
        (root / "workbench" / "quality" / "quality_gate.py").write_text(generate_quality_gate_py(commands), encoding="utf-8")
        confirm_project_intake_for_fixture(root)
        commit_all(root, "workbench baseline")

        (root / "src" / "app.js").write_text("console.log('v2')\n", encoding="utf-8")
        missing_record = run_command_capture([sys.executable, "workbench/quality/quality_gate.py", "--profile", "standard"], root)
        assert_condition(missing_record.returncode != 0, "quality gate should fail controlled code diff without feature package or light record", failures)
        assert_condition("controlled changes require" in (missing_record.stdout + missing_record.stderr), "quality gate failure should mention missing feature/light evidence", failures)

        change_log = root / "workbench" / "delivery" / "CHANGE_LOG.md"
        change_log.write_text(change_log.read_text(encoding="utf-8") + """

```json
{
  "change_id": "CHG-GOLDEN-PSEUDO",
  "workflow_profile": "light",
  "scope": ["*"],
  "risk": "light",
  "validation": "python noop",
  "evidence": "golden quality gate fixture",
  "reviewer": "golden-test",
  "gate_marker": ".workbench-validation/quality-gate-ok.json",
  "status": "verified"
}
```
""", encoding="utf-8")
        pseudo_light = run_command_capture([sys.executable, "workbench/quality/quality_gate.py", "--profile", "standard"], root)
        assert_condition(pseudo_light.returncode != 0, "quality gate should reject wildcard light CHANGE_LOG scope", failures)

        change_log.write_text(change_log.read_text(encoding="utf-8") + """

```json
{
  "change_id": "CHG-GOLDEN-001",
  "workflow_profile": "light",
  "scope": ["src/app.js", "workbench/delivery/CHANGE_LOG.md"],
  "risk": "light",
  "validation": "python noop",
  "evidence": "golden quality gate fixture",
  "reviewer": "golden-test",
  "gate_marker": ".workbench-validation/quality-gate-ok.json",
  "status": "verified"
}
```
""", encoding="utf-8")
        with_light = run_command_capture([sys.executable, "workbench/quality/quality_gate.py", "--profile", "standard"], root)
        assert_condition(with_light.returncode == 0, f"quality gate should pass with valid light CHANGE_LOG record: {with_light.stderr}", failures)
        marker = read_json(root / ".workbench-validation" / "quality-gate-ok.json") or {}
        state = read_json(root / ".workbench-validation" / "quality-workflow-state.json") or {}
        assert_condition(marker.get("status") in {"passed", "passed_with_risk"}, "quality marker should record pass or pass-with-risk status", failures)
        assert_condition(marker.get("quality_profile") == "standard", "quality marker should use quality_profile=standard", failures)
        assert_condition(marker.get("workflow_profile") == "light", "quality marker should infer workflow_profile=light", failures)
        assert_condition("scorecard_decision" in marker, "quality marker should include scorecard_decision", failures)
        assert_condition("unverified_paths" in marker and "branch_protection" in marker.get("unverified_paths", []), "quality marker should record unverified branch protection", failures)
        assert_condition(state.get("workflow_profile") == "light", "workflow state should keep workflow_profile separate from quality profile", failures)
        assert_condition(state.get("quality_profile") == "standard", "workflow state should include quality_profile", failures)

        api_design = root / "workbench" / "architecture" / "API_DESIGN.md"
        api_design_original = api_design.read_bytes()
        change_log_before_forbidden = change_log.read_text(encoding="utf-8")
        api_design.write_bytes(api_design_original + b"\n\n## Golden forbidden light path change\n")
        change_log.write_text(change_log.read_text(encoding="utf-8") + """

```json
{
  "change_id": "CHG-GOLDEN-FORBIDDEN-LIGHT",
  "workflow_profile": "light",
  "scope": ["src/app.js", "workbench/delivery/CHANGE_LOG.md", "workbench/architecture/API_DESIGN.md"],
  "risk": "light",
  "validation": "python noop",
  "evidence": "golden quality gate fixture",
  "reviewer": "golden-test",
  "gate_marker": ".workbench-validation/quality-gate-ok.json",
  "status": "verified"
}
```
""", encoding="utf-8")
        forbidden_light = run_command_capture([sys.executable, "workbench/quality/quality_gate.py", "--profile", "standard"], root)
        assert_condition(forbidden_light.returncode != 0, "quality gate should reject light CHANGE_LOG for high-risk architecture/API paths", failures)
        api_design.write_bytes(api_design_original)
        change_log.write_text(change_log_before_forbidden, encoding="utf-8")

        smoke = run_command_capture([sys.executable, "workbench/quality/quality_gate.py", "--profile", "smoke"], root)
        assert_condition(smoke.returncode == 0, f"smoke quality gate should pass with valid light record: {smoke.stderr}", failures)
        smoke_state = read_json(root / ".workbench-validation" / "quality-workflow-state-smoke.json") or {}
        smoke_marker = read_json(root / ".workbench-validation" / "quality-gate-smoke-ok.json") or {}
        assert_condition(smoke_state.get("workflow_profile") in {"light", "standard", "strict", "unclassified"}, "smoke run must not write quality profile into workflow_profile", failures)
        assert_condition(smoke_state.get("quality_profile") == "smoke", "smoke run should write quality_profile=smoke", failures)
        assert_condition(smoke_marker.get("quality_profile") == "smoke", "smoke run should write a separate smoke marker", failures)
        marker_after_smoke = read_json(root / ".workbench-validation" / "quality-gate-ok.json") or {}
        assert_condition(marker_after_smoke.get("quality_profile") == "standard", "smoke run must not overwrite the standard quality-gate-ok marker", failures)

        return {
            "name": "quality-gate-contract",
            "passed": not failures,
            "failures": failures,
            "missingRecordExit": missing_record.returncode,
            "pseudoLightExit": pseudo_light.returncode,
            "forbiddenLightExit": forbidden_light.returncode,
            "withLightExit": with_light.returncode,
            "markerStatus": marker.get("status"),
            "workflowProfile": marker.get("workflow_profile"),
            "qualityProfile": marker.get("quality_profile"),
        }


def run_quality_evidence_golden_case() -> dict[str, Any]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="codex-workbench-golden-evidence-") as tmp:
        root = Path(tmp)
        setup_local_git(root)
        write_sample_node(root)
        generate_adapter(root, "evidence-gate", force=False, dry_run=False)
        commands = [
            {
                "name": "python noop",
                "group": "python",
                "profiles": ["smoke", "standard", "full"],
                "cwd": ".",
                "command": [sys.executable, "-c", "print('quality-ok')"],
            }
        ]
        (root / "workbench" / "quality" / "quality_gate.py").write_text(generate_quality_gate_py(commands), encoding="utf-8")
        confirm_project_intake_for_fixture(root)
        commit_all(root, "confirmed workbench baseline")
        create_feature_package(root, "Evidence Gate", dry_run=False, force=False)
        package = root / "workbench" / "features" / "evidence-gate"
        set_feature_profile(package, "standard", traceability_required=False)

        write_verify_fixture(package, with_evidence=False)
        write_review_fixture(package, clean=True)
        empty_verify = run_command_capture([sys.executable, "workbench/quality/quality_gate.py", "--profile", "standard"], root)
        assert_condition(empty_verify.returncode != 0, "evidence gate should fail VERIFY.md marked passed with empty evidence", failures)
        assert_condition("VERIFY.md is marked passed" in (empty_verify.stdout + empty_verify.stderr), "evidence gate failure should mention VERIFY evidence", failures)

        write_verify_fixture(package, with_evidence=True)
        write_review_fixture(package, clean=False)
        unresolved_review = run_command_capture([sys.executable, "workbench/quality/quality_gate.py", "--profile", "standard"], root)
        assert_condition(unresolved_review.returncode != 0, "evidence gate should fail REVIEW.md marked passed with unresolved P0/P1 placeholder", failures)
        assert_condition("REVIEW.md" in (unresolved_review.stdout + unresolved_review.stderr), "evidence gate failure should mention REVIEW.md", failures)

        write_review_fixture(package, clean=True)
        standard_pass = run_command_capture([sys.executable, "workbench/quality/quality_gate.py", "--profile", "standard"], root)
        assert_condition(standard_pass.returncode == 0, f"evidence gate should pass after VERIFY/REVIEW evidence is fixed: {standard_pass.stderr}", failures)

        set_feature_profile(package, "strict", traceability_required=True)
        strict_missing_trace = run_command_capture([sys.executable, "workbench/quality/quality_gate.py", "--profile", "standard"], root)
        assert_condition(strict_missing_trace.returncode != 0, "strict evidence gate should fail while TRACEABILITY.md has missing rows", failures)
        assert_condition("TRACEABILITY" in (strict_missing_trace.stdout + strict_missing_trace.stderr), "strict evidence gate failure should mention TRACEABILITY", failures)

        unrelated_trace = root / "workbench" / "delivery" / "TRACEABILITY.md"
        unrelated_trace.write_text(unrelated_trace.read_text(encoding="utf-8").replace(" | missing |  |", " | covered | unrelated legacy evidence |"), encoding="utf-8")
        strict_unrelated_trace = run_command_capture([sys.executable, "workbench/quality/quality_gate.py", "--profile", "standard"], root)
        assert_condition(strict_unrelated_trace.returncode != 0, "strict evidence gate should fail when TRACEABILITY has only unrelated covered IDs", failures)
        assert_condition("impacted IDs missing" in (strict_unrelated_trace.stdout + strict_unrelated_trace.stderr), "strict traceability failure should mention impacted IDs missing", failures)

        mark_traceability_covered(root)
        write_verify_accepted_risk_fixture(package, complete=False)
        incomplete_risk = run_command_capture([sys.executable, "workbench/quality/quality_gate.py", "--profile", "standard"], root)
        assert_condition(incomplete_risk.returncode != 0, "strict evidence gate should fail accepted_risk=true without user confirmation, alternative verification, and follow-up", failures)
        assert_condition("incomplete verification risk acceptance" in (incomplete_risk.stdout + incomplete_risk.stderr), "strict accepted-risk failure should mention incomplete verification risk acceptance", failures)

        write_verify_accepted_risk_fixture(package, complete=True)
        strict_pass = run_command_capture([sys.executable, "workbench/quality/quality_gate.py", "--profile", "standard"], root)
        assert_condition(strict_pass.returncode == 0, f"strict evidence gate should pass after TRACEABILITY rows and accepted risk are complete: {strict_pass.stderr}", failures)
        strict_marker = read_json(root / ".workbench-validation" / "quality-gate-ok.json") or {}
        assert_condition(strict_marker.get("status") == "passed_with_risk", "strict accepted-risk marker should be passed_with_risk", failures)
        assert_condition(strict_marker.get("accepted_risk_features"), "strict accepted-risk marker should list accepted_risk_features", failures)

        return {
            "name": "quality-evidence-contract",
            "passed": not failures,
            "failures": failures,
            "emptyVerifyExit": empty_verify.returncode,
            "unresolvedReviewExit": unresolved_review.returncode,
            "strictMissingTraceExit": strict_missing_trace.returncode,
            "strictUnrelatedTraceExit": strict_unrelated_trace.returncode,
            "incompleteRiskExit": incomplete_risk.returncode,
            "strictPassExit": strict_pass.returncode,
            "strictMarkerStatus": strict_marker.get("status"),
        }


def run_plugin_hook_golden_case() -> dict[str, Any]:
    failures: list[str] = []
    plugin_root = find_plugin_root_for_hook_golden()
    if plugin_root is None:
        failures.append("hook golden: bundled plugin hook script was not found")
        return {"name": "plugin-hook-hard-gate", "passed": False, "failures": failures}

    with tempfile.TemporaryDirectory(prefix="codex-workbench-golden-hooks-") as tmp:
        root = Path(tmp)
        plugin_data = root / "plugin-data"
        plugin_data.mkdir()

        approval_patch = """*** Begin Patch
*** Add File: config.toml
+approval_policy = 'never'
*** End Patch
"""
        approval_result = invoke_workbench_hook(
            plugin_root,
            plugin_data,
            {
                "hook_event_name": "PreToolUse",
                "session_id": "golden-approval-policy",
                "tool_name": "apply_patch",
                "cwd": str(root),
                "tool_input": {"command": approval_patch},
            },
        )
        assert_condition(approval_result["returncode"] == 0, f"hook golden: approval_policy PreToolUse exited {approval_result['returncode']}: {approval_result['stderr']}", failures)
        assert_condition(hook_pretooluse_permission_decision(approval_result) == "deny", "hook golden: apply_patch adding approval_policy='never' should be denied", failures)

        workbench_docs_patch = """*** Begin Patch
*** Add File: workbench/docs/test.md
+# Test
*** End Patch
"""
        docs_result = invoke_workbench_hook(
            plugin_root,
            plugin_data,
            {
                "hook_event_name": "PreToolUse",
                "session_id": "golden-workbench-docs",
                "tool_name": "apply_patch",
                "cwd": str(root),
                "tool_input": {"command": workbench_docs_patch},
            },
        )
        docs_reason = ""
        docs_output = docs_result.get("json", {}).get("hookSpecificOutput", {}) if isinstance(docs_result.get("json"), dict) else {}
        if isinstance(docs_output, dict):
            docs_reason = str(docs_output.get("permissionDecisionReason") or "")
        assert_condition(docs_result["returncode"] == 0, f"hook golden: workbench/docs PreToolUse exited {docs_result['returncode']}: {docs_result['stderr']}", failures)
        assert_condition(hook_pretooluse_permission_decision(docs_result) == "deny", "hook golden: apply_patch adding workbench/docs/test.md should be denied", failures)
        assert_condition("workbench" in docs_reason and "docs" in docs_reason, "hook golden: workbench/docs denial should name the invalid directory", failures)

        readonly_result = invoke_workbench_hook(
            plugin_root,
            plugin_data,
            {
                "hook_event_name": "PreToolUse",
                "session_id": "golden-readonly-rg",
                "tool_name": "functions.shell_command",
                "cwd": str(root),
                "tool_input": {"command": "rg TODO"},
            },
        )
        assert_condition(readonly_result["returncode"] == 0, f"hook golden: readonly rg PreToolUse exited {readonly_result['returncode']}: {readonly_result['stderr']}", failures)
        assert_condition(hook_pretooluse_permission_decision(readonly_result) != "deny", "hook golden: single readonly rg command should not be denied", failures)

        composite_result = invoke_workbench_hook(
            plugin_root,
            plugin_data,
            {
                "hook_event_name": "PreToolUse",
                "session_id": "golden-composite-destructive",
                "tool_name": "functions.shell_command",
                "cwd": str(root),
                "tool_input": {"command": "rg TODO; " + "Remove" + "-Item -LiteralPath '$env:USERPROFILE\\.codex' -Recurse -Force"},
            },
        )
        assert_condition(composite_result["returncode"] == 0, f"hook golden: composite destructive PreToolUse exited {composite_result['returncode']}: {composite_result['stderr']}", failures)
        assert_condition(hook_pretooluse_permission_decision(composite_result) == "deny", "hook golden: readonly prefix plus destructive command should be denied", failures)

        marker_write_result = invoke_workbench_hook(
            plugin_root,
            plugin_data,
            {
                "hook_event_name": "PreToolUse",
                "session_id": "golden-direct-marker-write",
                "tool_name": "functions.shell_command",
                "cwd": str(root),
                "tool_input": {"command": "Set-Content -LiteralPath '.workbench-validation\\quality-gate-ok.json' -Value '{}'"},
            },
        )
        assert_condition(marker_write_result["returncode"] == 0, f"hook golden: direct marker write PreToolUse exited {marker_write_result['returncode']}: {marker_write_result['stderr']}", failures)
        assert_condition(hook_pretooluse_permission_decision(marker_write_result) == "deny", "hook golden: direct quality-gate marker writes should be denied", failures)

        composite_marker_write_result = invoke_workbench_hook(
            plugin_root,
            plugin_data,
            {
                "hook_event_name": "PreToolUse",
                "session_id": "golden-composite-marker-write",
                "tool_name": "functions.shell_command",
                "cwd": str(root),
                "tool_input": {"command": ".\\workbench\\quality\\quality-gate.ps1; Set-Content -LiteralPath '.workbench-validation\\quality-gate-ok.json' -Value '{}'"},
            },
        )
        assert_condition(composite_marker_write_result["returncode"] == 0, f"hook golden: composite marker write PreToolUse exited {composite_marker_write_result['returncode']}: {composite_marker_write_result['stderr']}", failures)
        assert_condition(hook_pretooluse_permission_decision(composite_marker_write_result) == "deny", "hook golden: quality gate path must not exempt direct marker writes in composite commands", failures)

        validation_dir_text = ".workbench-validation"
        gate_marker_name = "quality-" + "gate-" + "ok.json"
        smoke_marker_name = "quality-" + "gate-" + "smoke-" + "ok.json"
        inline_marker_write_result = invoke_workbench_hook(
            plugin_root,
            plugin_data,
            {
                "hook_event_name": "PreToolUse",
                "session_id": "golden-inline-marker-write",
                "tool_name": "functions.shell_command",
                "cwd": str(root),
                "tool_input": {
                    "command": (
                        "py -c \"from pathlib import Path; "
                        f"Path({validation_dir_text!r}, {gate_marker_name!r}).write_text('{{}}'); "
                        "print('.\\\\workbench\\\\quality\\\\quality-gate.ps1')\""
                    )
                },
            },
        )
        assert_condition(inline_marker_write_result["returncode"] == 0, f"hook golden: inline marker write PreToolUse exited {inline_marker_write_result['returncode']}: {inline_marker_write_result['stderr']}", failures)
        assert_condition(hook_pretooluse_permission_decision(inline_marker_write_result) == "deny", "hook golden: interpreter inline marker writes should be denied even when quality gate text appears", failures)

        smoke_marker_write_result = invoke_workbench_hook(
            plugin_root,
            plugin_data,
            {
                "hook_event_name": "PreToolUse",
                "session_id": "golden-smoke-marker-write",
                "tool_name": "functions.shell_command",
                "cwd": str(root),
                "tool_input": {"command": f"Set-Content -LiteralPath '{validation_dir_text}\\{smoke_marker_name}' -Value '{{}}'"},
            },
        )
        assert_condition(smoke_marker_write_result["returncode"] == 0, f"hook golden: smoke marker write PreToolUse exited {smoke_marker_write_result['returncode']}: {smoke_marker_write_result['stderr']}", failures)
        assert_condition(hook_pretooluse_permission_decision(smoke_marker_write_result) == "deny", "hook golden: direct smoke marker writes should be denied", failures)

        outer = root / "outer"
        nested = outer / "packages" / "nested-app"
        outer.mkdir(parents=True)
        setup_local_git(outer)
        (outer / "README.md").write_text("# Outer\n", encoding="utf-8")
        commit_all(outer, "outer baseline")

        nested.mkdir(parents=True)
        setup_local_git(nested)
        (nested / "src").mkdir()
        (nested / "src" / "app.txt").write_text("v1\n", encoding="utf-8")
        (nested / "workbench" / "quality").mkdir(parents=True)
        (nested / "workbench" / "quality" / "quality-gate.ps1").write_text("Write-Output 'quality ok'\n", encoding="utf-8")
        commit_all(nested, "nested baseline")

        session_id = "golden-nested-stop"
        start_result = invoke_workbench_hook(
            plugin_root,
            plugin_data,
            {
                "hook_event_name": "SessionStart",
                "session_id": session_id,
                "cwd": str(nested),
            },
        )
        assert_condition(start_result["returncode"] == 0, f"hook golden: SessionStart exited {start_result['returncode']}: {start_result['stderr']}", failures)
        (nested / "src" / "app.txt").write_text("v2\n", encoding="utf-8")
        stop_result = invoke_workbench_hook(
            plugin_root,
            plugin_data,
            {
                "hook_event_name": "Stop",
                "session_id": session_id,
                "cwd": str(nested),
                "stop_hook_active": False,
            },
        )
        stop_payload = stop_result.get("json", {}) if isinstance(stop_result.get("json"), dict) else {}
        stop_reason = str(stop_payload.get("reason") or "") if isinstance(stop_payload, dict) else ""
        assert_condition(stop_result["returncode"] == 0, f"hook golden: Stop exited {stop_result['returncode']}: {stop_result['stderr']}", failures)
        assert_condition(stop_payload.get("decision") == "block", "hook golden: Stop should block dirty nested repo without quality-gate marker", failures)
        assert_condition("missing quality-gate-ok.json" in stop_reason, "hook golden: Stop block should mention missing quality-gate-ok.json", failures)
        stop_repo_root = str(stop_payload.get("repoRoot") or "")
        normalized_stop_repo = stop_repo_root.replace("\\", "/").lower()
        normalized_nested = str(nested).replace("\\", "/").lower()
        assert_condition(normalized_stop_repo == normalized_nested or normalized_nested in stop_reason.replace("\\", "/").lower(), "hook golden: Stop block should report the nested repo path", failures)

        marker_dir = nested / ".workbench-validation"
        marker_dir.mkdir(parents=True, exist_ok=True)
        workflow_state = {
            "schema": "codex-workbench-workflow-state/v2",
            "generated_by": "quality_gate.py",
            "git_head": fixture_git_head(nested),
            "diff_hash": fixture_diff_hash(nested),
            "workflow_profile": "light",
            "quality_profile": "standard",
            "last_gate_status": "passed",
            "checks_run": ["forged check"],
        }
        workflow_state_text = json.dumps(workflow_state, ensure_ascii=False, indent=2) + "\n"
        workflow_state_path = marker_dir / "quality-workflow-state.json"
        workflow_state_path.write_text(workflow_state_text, encoding="utf-8")
        forged_marker = {
            "schema": "codex-workbench-quality-gate-marker/v2",
            "status": "passed",
            "created_at": utc_now(),
            "projectRoot": str(nested),
            "git_head": fixture_git_head(nested),
            "diff_hash": fixture_diff_hash(nested),
            "workflow_profile": "light",
            "quality_profile": "standard",
            "commands_run": ["forged check"],
            "skipped_groups": [],
            "allow_empty": False,
            "checks_run": ["forged check"],
            "workflow_state": str(workflow_state_path),
            "workflow_state_hash": fixture_text_sha256(workflow_state_text),
            "branch_protection": "unverified",
            "unverified_paths": ["branch_protection"],
        }
        (marker_dir / "quality-gate-ok.json").write_text(json.dumps(forged_marker, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        split_marker_fake_gate_result = invoke_workbench_hook(
            plugin_root,
            plugin_data,
            {
                "hook_event_name": "PreToolUse",
                "session_id": session_id,
                "tool_name": "functions.shell_command",
                "cwd": str(nested),
                "tool_input": {
                    "command": (
                        "py -c \"from pathlib import Path; "
                        "d='.workbench-'+'validation'; "
                        "m='quality-'+'gate-'+'ok.json'; "
                        "Path(d, m).write_text('{}'); "
                        "print('.\\\\workbench\\\\quality\\\\quality-gate.ps1 ')\""
                    )
                },
            },
        )
        assert_condition(split_marker_fake_gate_result["returncode"] == 0, f"hook golden: split marker fake gate PreToolUse exited {split_marker_fake_gate_result['returncode']}: {split_marker_fake_gate_result['stderr']}", failures)
        assert_condition(hook_pretooluse_permission_decision(split_marker_fake_gate_result) != "deny", "hook golden: split marker fake gate probe should not depend on PreToolUse denial", failures)
        forged_stop_result = invoke_workbench_hook(
            plugin_root,
            plugin_data,
            {
                "hook_event_name": "Stop",
                "session_id": session_id,
                "cwd": str(nested),
                "stop_hook_active": False,
            },
        )
        forged_stop_payload = forged_stop_result.get("json", {}) if isinstance(forged_stop_result.get("json"), dict) else {}
        forged_stop_reason = str(forged_stop_payload.get("reason") or "") if isinstance(forged_stop_payload, dict) else ""
        assert_condition(forged_stop_result["returncode"] == 0, f"hook golden: forged marker Stop exited {forged_stop_result['returncode']}: {forged_stop_result['stderr']}", failures)
        assert_condition(forged_stop_payload.get("decision") == "block", "hook golden: Stop should block a fresh-looking marker when no real quality gate ran this session", failures)
        assert_condition("质量门调用" in forged_stop_reason or "quality" in forged_stop_reason.lower(), "hook golden: forged marker Stop block should mention missing session quality-gate invocation", failures)

        return {
            "name": "plugin-hook-hard-gate",
            "passed": not failures,
            "failures": failures,
            "preToolUseApprovalDecision": hook_pretooluse_permission_decision(approval_result),
            "preToolUseWorkbenchDocsDecision": hook_pretooluse_permission_decision(docs_result),
            "preToolUseReadonlyDecision": hook_pretooluse_permission_decision(readonly_result),
            "preToolUseCompositeDecision": hook_pretooluse_permission_decision(composite_result),
            "preToolUseMarkerWriteDecision": hook_pretooluse_permission_decision(marker_write_result),
            "preToolUseCompositeMarkerWriteDecision": hook_pretooluse_permission_decision(composite_marker_write_result),
            "preToolUseInlineMarkerWriteDecision": hook_pretooluse_permission_decision(inline_marker_write_result),
            "preToolUseSmokeMarkerWriteDecision": hook_pretooluse_permission_decision(smoke_marker_write_result),
            "preToolUseSplitMarkerFakeGateDecision": hook_pretooluse_permission_decision(split_marker_fake_gate_result),
            "stopDecision": stop_payload.get("decision") if isinstance(stop_payload, dict) else None,
            "forgedStopDecision": forged_stop_payload.get("decision") if isinstance(forged_stop_payload, dict) else None,
        }


def run_golden_test() -> dict[str, Any]:
    cases = [
        run_golden_case("node-vite", write_sample_node),
        run_golden_case("maven-basic", write_sample_maven),
        run_golden_case("fullstack-compose", write_sample_fullstack),
        run_upgrade_golden_case(),
        run_workbench_guard_golden_case(),
        run_quality_gate_contract_golden_case(),
        run_quality_evidence_golden_case(),
        run_plugin_hook_golden_case(),
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


def default_personal_skill_root() -> Path:
    return Path.home() / ".codex" / "skills" / "codex-workbench"


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
    for home_candidate in (
        Path.home() / "plugins" / "codex-workbench" / "plugins" / "codex-workbench",
        Path.home() / "plugins" / "codex-workbench",
    ):
        if (home_candidate / ".codex-plugin" / "plugin.json").exists():
            return home_candidate
    return None


def iter_publish_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for current, dirs, filenames in os.walk(root):
        cur = Path(current)
        dirs[:] = [d for d in dirs if d not in {".git", ".hg", ".svn", ".workbench-validation"}]
        for filename in filenames:
            files.append(cur / filename)
    return files


def iter_actual_tree_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for current, dirs, filenames in os.walk(root):
        cur = Path(current)
        dirs[:] = [d for d in dirs if d not in {".git", ".hg", ".svn"}]
        for filename in filenames:
            files.append(cur / filename)
    return files


def is_validation_output_path(rel: str) -> bool:
    normalized = rel.replace("\\", "/")
    return bool(re.search(r"(?:^|/)\.workbench-validation(?:/|$)", normalized, re.IGNORECASE))


def scan_actual_tree_residue(root: Path, label: str, include_publish_residue: bool = True, include_validation_output: bool = True) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path in iter_actual_tree_files(root):
        rel = rel_to(root, path)
        normalized = rel.replace("\\", "/")
        if include_validation_output and is_validation_output_path(normalized):
            findings.append(doctor_issue(
                "P2",
                "generated-validation-output-present",
                f"{label} contains .workbench-validation output. It is excluded from the manifest, but direct directory copies may leak stale local reports.",
                rel,
            ))
            continue
        if not include_publish_residue:
            continue
        for pattern in PUBLISH_BLOCKLIST_PATTERNS:
            if is_validation_output_path(normalized):
                continue
            if pattern.search(normalized):
                findings.append(doctor_issue("P1", "publish-artifact-residue", f"{label} contains cache, legacy, or internal residue.", rel))
                break
    return findings


def scan_publish_tree(root: Path, label: str, check_residue: bool = True) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path in iter_publish_files(root):
        rel = rel_to(root, path)
        normalized = rel.replace("\\", "/")
        if check_residue:
            for pattern in PUBLISH_BLOCKLIST_PATTERNS:
                if pattern.search(normalized):
                    findings.append(doctor_issue("P1", "publish-artifact-residue", f"{label} contains cache, legacy, or internal residue.", rel))
                    break
        if path.suffix.lower() not in {".md", ".py", ".ps1", ".sh", ".json", ".toml", ".yml", ".yaml", ".txt"}:
            continue
        text = read_text_safe(path)
        if path.name == "workbench.py" and path.parent.name == "scripts":
            text = re.sub(r"(?s)PERSONAL_PATH_PATTERNS\s*=\s*\[.*?\]\n\n", "PERSONAL_PATH_PATTERNS = []\n\n", text, count=1)
        for pattern in PERSONAL_PATH_PATTERNS:
            if pattern.search(text):
                findings.append(doctor_issue("P1", "personal-path", f"{label} contains a personal absolute path.", rel))
                break
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(doctor_issue("P0", "possible-secret", f"{label} contains a possible secret or token-like value.", rel))
                break
    return findings


def glob_match(path: str, pattern: str) -> bool:
    normalized_path = path.replace("\\", "/")
    normalized_pattern = pattern.replace("\\", "/")
    if normalized_pattern.endswith("/**"):
        prefix = normalized_pattern[:-3].rstrip("/")
        return normalized_path == prefix or normalized_path.startswith(prefix + "/")
    if normalized_pattern.startswith("**/"):
        tail = normalized_pattern[3:]
        return normalized_path == tail or normalized_path.endswith("/" + tail) or fnmatch.fnmatch(normalized_path, normalized_pattern)
    return fnmatch.fnmatch(normalized_path, normalized_pattern)


def materialize_packaging_manifest(plugin: Path, manifest: dict[str, Any]) -> tuple[list[str], list[dict[str, str]]]:
    findings: list[dict[str, str]] = []
    include = manifest.get("include") if isinstance(manifest.get("include"), list) else []
    exclude = manifest.get("exclude") if isinstance(manifest.get("exclude"), list) else []
    all_files: list[str] = []
    for current, dirs, filenames in os.walk(plugin):
        dirs[:] = [d for d in dirs if d not in {".git", ".hg", ".svn"}]
        cur = Path(current)
        for filename in filenames:
            all_files.append(rel_to(plugin, cur / filename).replace("\\", "/"))
    selected: set[str] = set()
    for pattern in include:
        if not isinstance(pattern, str):
            findings.append(doctor_issue("P1", "packaging-manifest-invalid-include", "Packaging manifest include entries must be strings.", "packaging-manifest.json"))
            continue
        matches = [rel for rel in all_files if glob_match(rel, pattern)]
        if not matches:
            findings.append(doctor_issue("P2", "packaging-manifest-empty-include", f"Packaging manifest include pattern matched no files: {pattern}", "packaging-manifest.json"))
        selected.update(matches)
    for pattern in exclude:
        if not isinstance(pattern, str):
            findings.append(doctor_issue("P1", "packaging-manifest-invalid-exclude", "Packaging manifest exclude entries must be strings.", "packaging-manifest.json"))
            continue
        selected = {rel for rel in selected if not glob_match(rel, pattern)}
    blocked = [rel for rel in sorted(selected) if any(pattern.search(rel) for pattern in PUBLISH_BLOCKLIST_PATTERNS)]
    for rel in blocked[:20]:
        findings.append(doctor_issue("P1", "packaging-manifest-includes-residue", "Materialized package file list includes cache, validation output, legacy, or internal residue.", rel))
    return sorted(selected), findings


def file_list_hash(paths: list[str]) -> str:
    payload = "\n".join(sorted(paths)).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def git_tracked_file_set(root: Path) -> set[str] | None:
    try:
        top_result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(root),
            text=True,
            capture_output=True,
            timeout=20,
        )
    except Exception:
        return None
    if top_result.returncode != 0:
        return None
    repo_root = Path(top_result.stdout.strip()).resolve()
    try:
        files_result = subprocess.run(
            ["git", "ls-files"],
            cwd=str(repo_root),
            text=True,
            capture_output=True,
            timeout=20,
        )
    except Exception:
        return None
    if files_result.returncode != 0:
        return None
    tracked: set[str] = set()
    for line in files_result.stdout.splitlines():
        rel = line.strip()
        if not rel:
            continue
        absolute = (repo_root / rel).resolve()
        try:
            tracked.add(absolute.relative_to(root.resolve()).as_posix())
        except ValueError:
            continue
    return tracked


def validate_manifest_files_tracked(plugin: Path, manifest_files: list[str]) -> list[dict[str, str]]:
    tracked = git_tracked_file_set(plugin)
    if tracked is None:
        return [doctor_issue("P3", "package-git-tracking-unverified", "Package file git tracking could not be verified; run package-check in a git checkout before release.", "packaging-manifest.json")]
    findings: list[dict[str, str]] = []
    for rel in manifest_files:
        normalized = rel.replace("\\", "/")
        if normalized not in tracked:
            findings.append(doctor_issue("P2", "package-file-untracked", "Materialized package file exists locally but is not tracked by git; clean-checkout packaging may omit it.", normalized))
    return findings


def validate_skill_files(root: Path, label: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for rel in REQUIRED_SKILL_FILES:
        if not (root / rel).exists():
            findings.append(doctor_issue("P1", "missing-skill-file", f"{label} is missing a required bundled file.", rel))
    script_root = root / "scripts"
    python_files = sorted(script_root.rglob("*.py")) if script_root.exists() else []
    for path in python_files:
        rel = rel_to(root, path)
        if any(part == "__pycache__" for part in path.parts):
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


def validate_plugin_hooks(plugin: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    hooks_json = plugin / "hooks" / "hooks.json"
    hook_script = plugin / "hooks" / "workbench-hard-gate.ps1"
    if not hooks_json.exists():
        findings.append(doctor_issue("P1", "missing-plugin-hooks-json", "Plugin should bundle hooks/hooks.json for local lifecycle guardrails.", rel_to(plugin, hooks_json)))
    else:
        try:
            hooks = json.loads(hooks_json.read_text(encoding="utf-8"))
        except Exception as exc:
            findings.append(doctor_issue("P1", "invalid-plugin-hooks-json", f"Plugin hooks.json is not valid JSON: {exc}", rel_to(plugin, hooks_json)))
        else:
            if not isinstance(hooks.get("hooks"), dict):
                findings.append(doctor_issue("P1", "invalid-plugin-hooks-shape", "Plugin hooks.json should contain a top-level hooks object.", rel_to(plugin, hooks_json)))
            serialized = json.dumps(hooks, ensure_ascii=False)
            if "workbench-hard-gate.ps1" not in serialized:
                findings.append(doctor_issue("P1", "plugin-hooks-missing-hard-gate", "Plugin hooks should invoke workbench-hard-gate.ps1.", rel_to(plugin, hooks_json)))
            matchers = json.dumps([item.get("matcher") for items in hooks.get("hooks", {}).values() if isinstance(items, list) for item in items if isinstance(item, dict)], ensure_ascii=False)
            if not all(term in matchers for term in ("functions", "shell_command", "multi_tool_use")):
                findings.append(doctor_issue("P1", "plugin-hooks-matcher-gap", "Plugin hooks should match current tool namespaces such as functions.shell_command, functions.apply_patch, and multi_tool_use.", rel_to(plugin, hooks_json)))
    if not hook_script.exists():
        findings.append(doctor_issue("P1", "missing-plugin-hook-script", "Plugin should bundle hooks/workbench-hard-gate.ps1.", rel_to(plugin, hook_script)))
    else:
        text = read_text_safe(hook_script)
        required_terms = [
            "Get-WorkbenchAllowedTopDirs",
            "Test-AllowedExplicitRecursiveDelete",
            "Test-ProtectedDeletionPath",
            "Test-SearchOrReadOnlyCommand",
            "projectMarkers",
            "-LiteralPath",
            "workbench\\docs\\",
            "quality-gate.ps1",
            "bypassPermissions",
        ]
        missing_terms = [term for term in required_terms if term not in text]
        if missing_terms:
            findings.append(doctor_issue("P1", "incomplete-plugin-hook-script", f"Plugin hook script is missing required guardrail terms: {', '.join(missing_terms)}.", rel_to(plugin, hook_script)))
    return findings


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


def doctor_workbench(plugin_path: str | None = None, personal_skill_path: str | None = None) -> dict[str, Any]:
    personal = Path(personal_skill_path).expanduser().resolve() if personal_skill_path else default_personal_skill_root()
    plugin = Path(plugin_path).expanduser().resolve() if plugin_path else default_plugin_root()
    findings: list[dict[str, str]] = []
    checks: list[str] = []

    if not personal.exists():
        findings.append(doctor_issue("P1", "personal-skill-not-found", "Personal skill root was not found.", str(personal)))
    else:
        checks.append("personal skill required files")
        findings.extend(validate_skill_files(personal, "Personal skill"))
        findings.extend(scan_publish_tree(personal, "Personal skill", check_residue=False))
        findings.extend(scan_actual_tree_residue(personal, "Personal skill"))

    plugin_summary: dict[str, Any] | None = None
    if plugin is None:
        findings.append(doctor_issue("P1", "plugin-not-found", "Plugin root was not found. Pass --plugin <path> when checking a package."))
    else:
        checks.append("plugin manifest")
        manifest, manifest_findings = validate_plugin_manifest(plugin)
        findings.extend(manifest_findings)
        checks.append("plugin bundled hooks")
        findings.extend(validate_plugin_hooks(plugin))
        plugin_skill = plugin / "skills" / "codex-workbench"
        if plugin_skill.exists():
            checks.append("plugin skill required files")
            findings.extend(validate_skill_files(plugin_skill, "Plugin skill"))
            findings.extend(scan_publish_tree(plugin, "Plugin package"))
            findings.extend(scan_actual_tree_residue(plugin, "Plugin package", include_publish_residue=False))
            checks.append("maintenance evidence")
            findings.extend(validate_maintenance_evidence(plugin))
            if personal.exists():
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
    if isinstance(manifest, dict):
        _, materialized_findings = materialize_packaging_manifest(plugin, manifest)
        findings.extend(materialized_findings)
    return findings


def packaging_manifest_file_list(plugin: Path) -> tuple[list[str], list[dict[str, str]]]:
    manifest_path = plugin / "packaging-manifest.json"
    if not manifest_path.exists():
        return [], []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return [], []
    if not isinstance(manifest, dict):
        return [], []
    return materialize_packaging_manifest(plugin, manifest)


def package_check_workbench(plugin_path: str | None = None, expected_version: str | None = None, write_report: bool = False, personal_skill_path: str | None = None, strict_release: bool = False) -> dict[str, Any]:
    plugin = Path(plugin_path).expanduser().resolve() if plugin_path else default_plugin_root()
    doctor = doctor_workbench(str(plugin) if plugin else None, personal_skill_path)
    findings = list(doctor["findings"])
    checks = list(doctor["checks"])
    manifest: dict[str, Any] | None = None
    exposed_skills: list[str] = []
    manifest_files: list[str] = []

    if plugin is None:
        findings.append(doctor_issue("P1", "package-plugin-missing", "Package check requires a plugin root. Pass --plugin <path>."))
    else:
        checks.append("release manifest")
        manifest, manifest_findings = validate_plugin_manifest(plugin)
        findings.extend(manifest_findings)
        checks.append("packaging manifest")
        findings.extend(validate_packaging_manifest(plugin))
        manifest_files, _ = packaging_manifest_file_list(plugin)
        checks.append("materialized package file list")
        findings.extend(validate_manifest_files_tracked(plugin, manifest_files))
        checks.append("git tracked package files")
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
    passed = severities["P0"] == 0 and severities["P1"] == 0 and (not strict_release or severities["P2"] == 0)
    report = {
        "schema": "codex-workbench-package-check/v1",
        "timestamp": utc_now(),
        "pluginRoot": str(plugin) if plugin else None,
        "expectedVersion": expected_version,
        "strictRelease": strict_release,
        "manifestVersion": manifest.get("version") if manifest else None,
        "visibleSkills": exposed_skills,
        "manifestFileCount": len(manifest_files),
        "manifestFileListHash": file_list_hash(manifest_files) if manifest_files else None,
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
    p_doctor.add_argument("--personal-skill", default=None, help="Personal skill root to compare. Defaults to ~/.codex/skills/codex-workbench when present.")
    p_doctor.add_argument("--output", default=None)

    p_package = sub.add_parser("package-check")
    p_package.add_argument("--plugin", default=None, help="Plugin root to check. Defaults to ~/plugins/codex-workbench when present.")
    p_package.add_argument("--personal-skill", default=None, help="Personal skill root to compare. Defaults to ~/.codex/skills/codex-workbench when present.")
    p_package.add_argument("--expected-version", default=None)
    p_package.add_argument("--strict-release", action="store_true", help="Fail package-check when P2 findings remain. Intended for release CI.")
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
        report = doctor_workbench(args.plugin, args.personal_skill)
        write_json(report, args.output)
        return 0 if report["passed"] else 1
    if args.command == "package-check":
        report = package_check_workbench(args.plugin, args.expected_version, args.write_report, args.personal_skill, args.strict_release)
        write_json(report, args.output)
        return 0 if report["passed"] else 1
    if args.command == "user-workbench":
        report = install_user_workbench(args.codex_home, args.apply, args.force)
        write_json(report, args.output)
        return 0
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
